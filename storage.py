"""Small transactional store: admin state and live snapshots are separate rows.

SQLite is automatic and needs no database service. PostgreSQL remains an
explicit opt-in for existing deployments. App Platform local files are
temporary; private recovery exports can seed a replacement instance.
"""
from contextlib import contextmanager
import copy
import hashlib
import json
import logging
import secrets
import sqlite3
import threading
import time

from werkzeug.security import generate_password_hash
from race_support import read_json, clean_snapshots, race_key, empty_snapshots
from store_schema import upgrade_store
from race import empty
from boss import validate_boss

LOG = logging.getLogger("redhunllef")


class StoreError(RuntimeError):
    pass


class Conflict(StoreError):
    pass


def encode(value):
    return json.dumps(value, separators=(",", ":"), ensure_ascii=False, allow_nan=False)


class Store:
    def __init__(self, config):
        self.config, self.key = config, config.state_key
        self.pg = bool(config.db_url)
        self.lock, self.conn, self.job_local = threading.RLock(), None, threading.local()
        if not self.pg:
            config.db_path.parent.mkdir(parents=True, exist_ok=True)
            if config.ignored_database_url:
                LOG.info("STORAGE Using local storage; DATABASE_URL is ignored because STORAGE_MODE=local.")
        self.initialize()

    def connect(self):
        if self.pg:
            try:
                import psycopg
            except ImportError:
                raise StoreError("Optional PostgreSQL support is not installed. Install requirements-postgres.txt or use STORAGE_MODE=local.") from None
            options = dict(autocommit=True, connect_timeout=8, sslmode=self.config.sslmode,
                           options="-c statement_timeout=8000 -c lock_timeout=5000")
            if self.config.sslrootcert:
                options["sslrootcert"] = self.config.sslrootcert
            return psycopg.connect(self.config.db_url, **options)
        conn = sqlite3.connect(self.config.db_path, check_same_thread=False, isolation_level=None, timeout=8)
        conn.execute("PRAGMA journal_mode=WAL")
        conn.execute("PRAGMA foreign_keys=ON")
        return conn

    @contextmanager
    def connection(self, transaction=False):
        # No network provider call or template rendering occurs inside this lock.
        with self.lock:
            try:
                if self.conn is None or (self.pg and self.conn.closed):
                    self.conn = self.connect()
                if transaction:
                    self.conn.execute("BEGIN" if self.pg else "BEGIN IMMEDIATE")
                yield self.conn
                if transaction:
                    self.conn.execute("COMMIT")
            except BaseException as exc:
                if transaction and self.conn:
                    try:
                        self.conn.execute("ROLLBACK")
                    except Exception:
                        pass
                if isinstance(exc, (Conflict, ValueError, RuntimeError)):
                    raise
                if not isinstance(exc, Exception):
                    raise
                self.close()
                message = "Database operation failed. Check connectivity, TLS, permissions, and runtime settings." if self.pg else "Local storage could not be read or written. Check disk space and the data folder permissions; do not delete your saved file."
                raise StoreError(message) from None

    def query(self, conn, sql, params=()):
        return conn.execute(sql.replace("?", "%s") if self.pg else sql, params)

    def initialize(self):
        with self.connection(transaction=True) as conn:
            if self.pg:
                conn.execute("SELECT pg_advisory_xact_lock(728364092)")
            conn.execute("CREATE TABLE IF NOT EXISTS rh_admin (name TEXT PRIMARY KEY, revision BIGINT NOT NULL, document TEXT NOT NULL)")
            conn.execute("CREATE TABLE IF NOT EXISTS rh_live (name TEXT NOT NULL, service TEXT NOT NULL, document TEXT NOT NULL, PRIMARY KEY(name, service))")
            conn.execute("CREATE TABLE IF NOT EXISTS rh_boss (name TEXT PRIMARY KEY, document TEXT NOT NULL)")
            conn.execute("CREATE TABLE IF NOT EXISTS rh_recovery (id TEXT PRIMARY KEY, name TEXT NOT NULL, reason TEXT NOT NULL, created BIGINT NOT NULL, document TEXT NOT NULL)")
            existing = self.query(conn, "SELECT document FROM rh_admin WHERE name=?", (self.key,)).fetchone()
            if existing:
                # Validate saved state rather than overwriting an unreadable account store.
                upgrade_store(json.loads(existing[0]), self.config.site, {})
                LOG.info("ACCOUNTS Existing accounts and settings retained.")
                return
            legacy = None
            source = "first-run defaults"
            if self.pg and conn.execute("SELECT to_regclass('wager_state')").fetchone()[0]:
                old = self.query(conn, "SELECT payload FROM wager_state WHERE name=?", (self.key,)).fetchone()
                if old:
                    legacy, source = old[0], "previous PostgreSQL state"
            if legacy is None:
                for path in (self.config.recovery, self.config.legacy, self.config.seed):
                    if path.is_file():
                        legacy, source = read_json(path), path.name
                        break
            if legacy is None:
                legacy = dict(version=7, users={self.config.superadmin: dict(
                    pw_hash=generate_password_hash(self.config.bootstrap_password), auth_version=1)},
                    secret_key=secrets.token_hex(32), site_settings=self.config.site)
            value, _ = upgrade_store(legacy, self.config.site, {})
            community_boss = value.pop("community_boss", None)
            if community_boss is not None:
                community_boss = validate_boss(community_boss)
            if not value["users"]:
                raise StoreError("Saved account store contains no accounts. The original was not replaced.")
            self.backup_in(conn, "before-rebuild-import", {"admin": legacy, "source": source})
            snapshots = clean_snapshots(value.pop("leaderboard_snapshots"), race_key(value["site_settings"]))
            value.pop("health", None)
            value["superadmin"] = self.config.superadmin
            self.query(conn, "INSERT INTO rh_admin VALUES (?, ?, ?)", (self.key, 1, encode(value)))
            if community_boss is not None:
                self.query(conn, "INSERT INTO rh_boss VALUES (?, ?)", (self.key, encode(community_boss)))
            saved = empty(value["site_settings"])
            saved.update(rows=snapshots["last_top15"], previous_top=snapshots["prev_top15"],
                         updated_at=snapshots["updated_at"] or 0, snapshot_only=bool(snapshots["last_top15"]),
                         count=len(snapshots["last_top15"]), warning="Only the saved Top 15 is available until Shuffle responds." if snapshots["last_top15"] else "")
            saved["source"] = [dict(username=r["username"], weighted=r["original_weighted_wager"],
                                    raw=r["raw_wager"], row_count=r["row_count"]) for r in saved["rows"]]
            self.live_in(conn, "shuffle", saved)
            LOG.info("MIGRATION Imported %s; original accounts, hashes, and dates preserved. Recovery copy recorded.", source)
        if not self.pg:
            self.config.db_path.chmod(0o600)

    def admin(self):
        with self.connection() as conn:
            row = self.query(conn, "SELECT revision, document FROM rh_admin WHERE name=?", (self.key,)).fetchone()
        if not row:
            raise StoreError("Saved admin state is missing. Restore a verified database backup.")
        return row[0], json.loads(row[1])

    def live(self, service):
        with self.connection() as conn:
            row = self.query(conn, "SELECT document FROM rh_live WHERE name=? AND service=?", (self.key, service)).fetchone()
        return json.loads(row[0]) if row else None

    def live_in(self, conn, service, value):
        self.query(conn, "INSERT INTO rh_live VALUES (?, ?, ?) ON CONFLICT(name,service) DO UPDATE SET document=excluded.document",
                   (self.key, service, encode(value)))

    def publish(self, service, value, expected_revision=None):
        with self.connection(transaction=True) as conn:
            if expected_revision is not None:
                sql = "SELECT revision FROM rh_admin WHERE name=?" + (" FOR UPDATE" if self.pg else "")
                if self.query(conn, sql, (self.key,)).fetchone()[0] != expected_revision:
                    raise Conflict("Race settings changed during the provider check; a new check is queued.")
            self.live_in(conn, service, value)

    def save(self, value, revision, *, snapshot=None, backup_reason=None):
        with self.connection(transaction=True) as conn:
            old = self.query(conn, "SELECT revision, document FROM rh_admin WHERE name=?" + (" FOR UPDATE" if self.pg else ""), (self.key,)).fetchone()
            if not old or old[0] != revision:
                raise Conflict("Another administrator saved changes. Reload and review before saving again.")
            if backup_reason:
                rows = self.query(conn, "SELECT service,document FROM rh_live WHERE name=?", (self.key,)).fetchall()
                self.backup_in(conn, backup_reason, {"admin": json.loads(old[1]), "live": {r[0]: json.loads(r[1]) for r in rows}})
            self.query(conn, "UPDATE rh_admin SET document=?,revision=revision+1 WHERE name=?", (encode(value), self.key))
            if snapshot is not None:
                self.live_in(conn, "shuffle", snapshot)
        return revision + 1

    def backup_in(self, conn, reason, document):
        self.query(conn, "INSERT INTO rh_recovery VALUES (?, ?, ?, ?, ?)",
                   (secrets.token_hex(16), self.key, reason, int(time.time()), encode(document)))

    @contextmanager
    def job(self, service):
        # Reuse one dedicated connection per provider thread. Session locks
        # prevent duplicate provider calls during an overlapping deployment.
        if not self.pg:
            yield True
            return
        conn = getattr(self.job_local, "conn", None)
        try:
            if conn is None or conn.closed:
                conn = self.job_local.conn = self.connect()
            key = int.from_bytes(hashlib.blake2b((self.key + service).encode(), digest_size=8).digest(), "big", signed=True)
            acquired = conn.execute("SELECT pg_try_advisory_lock(%s)", (key,)).fetchone()[0]
        except Exception:
            self.close_job()
            raise StoreError("Provider coordination could not reach PostgreSQL. The next scheduled check will retry.") from None
        try:
            yield acquired
        finally:
            if acquired:
                try:
                    conn.execute("SELECT pg_advisory_unlock(%s)", (key,))
                except Exception:
                    self.close_job()

    def close_job(self):
        conn = getattr(self.job_local, "conn", None)
        if conn:
            conn.close()
        self.job_local.conn = None

    def close(self):
        with self.lock:
            if self.conn:
                self.conn.close()
            self.conn = None
