"""Atomic UTF-8 file storage. No database service, SQL runtime, or setup command.

One small JSON document holds current state. A process lock serializes writers,
including a brief local deployment overlap. Writes use fsync + atomic replace;
a failed write never publishes partial state. Keep one App Platform instance.
"""
from contextlib import contextmanager
import copy
import json
import logging
import os
from pathlib import Path
import secrets
import tempfile
import threading
import time

from werkzeug.security import generate_password_hash
from race_support import read_json, clean_snapshots, race_key
from store_schema import upgrade_store
from race import empty
from presentation import valid_marker
from weekly_history import clean_history
from gaming import validate_gaming, migrate_legacy_profiles
from telemetry import Measurements
from spaces_state import SpacesMirror, SpacesError

LOG = logging.getLogger("redhunllef")


class StoreError(RuntimeError):
    pass


class Conflict(StoreError):
    pass


def encode(value):
    return json.dumps(value, separators=(",", ":"), ensure_ascii=False, allow_nan=False)


def atomic_json(path, value):
    """Create the replacement beside its target so rename stays atomic."""
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, temporary = tempfile.mkstemp(prefix=path.name + ".", suffix=".tmp", dir=path.parent)
    try:
        with os.fdopen(fd, "w", encoding="utf-8", newline="\n") as output:
            output.write(encode(value))
            output.flush()
            os.fsync(output.fileno())
        os.replace(temporary, path)
        if os.name != "nt":
            directory = os.open(path.parent, os.O_RDONLY)
            try:
                os.fsync(directory)
            finally:
                os.close(directory)
    finally:
        if os.path.exists(temporary):
            os.unlink(temporary)


class Store:
    def __init__(self, config):
        self.config, self.key, self.pg = config, config.state_key, False
        self.path = config.state_path
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.lock = threading.RLock()
        self.cached, self.stamp = None, None
        self.measurements = Measurements()
        self._probe, self._probe_until = None, 0
        # Optional remote authority: never treat an old bundled JSON snapshot as
        # current when durable Spaces state has been configured.
        self.mirror = SpacesMirror.from_environment(self.key)
        if self.mirror:
            self.mirror.prepare(self.path, state_key=self.key,
                                bootstrap=os.getenv('RH_SPACES_BOOTSTRAP_LOCAL') == '1')
        self.initialize()

    @contextmanager
    def _file_lock(self):
        # The lock file is separate from the atomically replaced state file.
        with open(str(self.path) + ".lock", "a+b") as handle:
            if os.name == "nt":
                import msvcrt
                handle.seek(0, os.SEEK_END)
                if not handle.tell():
                    handle.write(b"0"); handle.flush()
                handle.seek(0)
                msvcrt.locking(handle.fileno(), msvcrt.LK_LOCK, 1)
            else:
                import fcntl
                fcntl.flock(handle, fcntl.LOCK_EX)
            try:
                yield
            finally:
                if os.name == "nt":
                    handle.seek(0)
                    msvcrt.locking(handle.fileno(), msvcrt.LK_UNLCK, 1)
                else:
                    fcntl.flock(handle, fcntl.LOCK_UN)

    def _remember(self, value):
        # We just committed these exact bytes. Avoid re-parsing them on the next
        # poll while still noticing another process's atomic replacement.
        stat = self.path.stat()
        self.cached = value
        self.stamp = (stat.st_mtime_ns, stat.st_size, stat.st_ino)

    def _disk(self):
        if not self.path.exists():
            if self.cached is not None:
                raise StoreError("The saved state file is missing. Restore it; accounts were not reset.")
            return None
        stat = self.path.stat()
        stamp = (stat.st_mtime_ns, stat.st_size, stat.st_ino)
        if stamp != self.stamp:
            value = read_json(self.path)
            if (not isinstance(value, dict) or value.get("format") != 1 or value.get("key") != self.key
                    or type(value.get("revision")) is not int or value["revision"] < 1
                    or not isinstance(value.get("admin"), dict) or not isinstance(value.get("live"), dict)):
                raise StoreError("The saved state file is invalid. It was not overwritten.")
            self.cached, self.stamp = value, stamp
        return self.cached

    @contextmanager
    def connection(self, transaction=False):
        """Existing call sites use this as a transaction, not a SQL connection."""
        started = time.perf_counter()
        waited, copied, written, size = 0, None, None, 0
        with self.lock:
            try:
                with self._file_lock():
                    waited = (time.perf_counter()-started)*1000
                    current = self._disk()
                    copying = time.perf_counter()
                    value = copy.deepcopy(current) if transaction else current
                    copied = (time.perf_counter()-copying)*1000 if transaction else None
                    yield value
                    if transaction and value != current:
                        writing = time.perf_counter()
                        if self.mirror:
                            # Write the remote authority before acknowledging a save.
                            # Fail closed rather than silently falling back to a
                            # disposable App Platform filesystem.
                            value['_mirror_sequence'] = int(current.get('_mirror_sequence', 0)) + 1
                            self.mirror.persist(value, expected=current)
                        atomic_json(self.path, value)
                        self._remember(value)
                        written = (time.perf_counter()-writing)*1000
                    size = self.stamp[1] if self.stamp else 0
            except (Conflict, ValueError, RuntimeError):
                raise
            except OSError as exc:
                self.measurements.failed('store_io_error')
                self._probe_until = 0
                LOG.error("STORAGE Local file operation failed (%s).", type(exc).__name__)
                raise StoreError("Local storage could not be read or written. Check free space and the data folder permissions; keep your saved file.") from None
            finally:
                self.measurements.transaction(waited, copied, written, size)

    def readiness(self):
        """Probe local state and a tiny temporary write, at most once per 15s.

        Never rewrite community state as a health check. Upstream availability
        does not determine whether this application can serve its users.
        """
        with self.lock:
            if self._probe and time.monotonic() < self._probe_until:
                return dict(self._probe)
            try:
                with self._file_lock():
                    if self._disk() is None:
                        raise StoreError('Missing saved state')
                    with tempfile.TemporaryFile(dir=self.path.parent) as check:
                        check.write(b'ready\n')
                        check.flush()
                        os.fsync(check.fileno())
                ok, message = True, 'Local save checked. Keep a private recovery export outside this server.'
            except (OSError, ValueError, RuntimeError):
                ok, message = False, 'Check data-folder permissions, free disk space and runtime logs. Existing state was not reset.'
                self.measurements.failed('store_probe_failed')
            self._probe = dict(ok=ok, checked_at=int(time.time()), message=message)
            self._probe_until = time.monotonic() + 15
            return dict(self._probe)

    def initialize(self):
        with self.lock, self._file_lock():
            existing = self._disk()
            if existing is not None:
                upgrade_store(existing["admin"], self.config.site, {})
                if not existing['admin'].get('users'):
                    raise StoreError('Saved account store contains no accounts. It was not replaced.')
                validate_gaming(existing.get('gaming'))
                if existing.get('boss') is not None or existing.get('avatar') is not None:
                    upgraded = copy.deepcopy(existing)
                    migrated = migrate_legacy_profiles(upgraded.get('gaming'), upgraded.get('boss'))
                    self.backup_in(upgraded, 'before-retired-profile-removal',
                                   {'boss': upgraded.get('boss'), 'avatar': upgraded.get('avatar')})
                    upgraded.pop('boss', None)
                    upgraded.pop('avatar', None)
                    upgraded['revision'] += 1
                    atomic_json(self.path, upgraded)
                    self._remember(upgraded)
                    existing = upgraded
                    LOG.info('MIGRATION Retired profile data removed; %s Gaming recovery record(s) preserved by unique name match.', migrated)
                LOG.info("ACCOUNTS Existing accounts, settings and RedPoints retained from JSON.")
                return
            # Optional fail-closed guard: deployers who have moved state out of
            # the container can refuse an accidental reset to an ancient seed.
            if self.config.production and os.getenv('RH_REQUIRE_EXISTING_STATE') == '1':
                raise StoreError('No persisted state found; refusing to bootstrap accounts or restore an older race seed.')
            value = self._import_sqlite()
            if value is None:
                legacy, source = None, "first-run defaults"
                for path in (self.config.recovery, self.config.legacy, self.config.seed):
                    if path.is_file():
                        legacy, source = read_json(path), path.name
                        break
                if legacy is None:
                    legacy = dict(version=7, users={self.config.superadmin: dict(
                        pw_hash=generate_password_hash(self.config.bootstrap_password), auth_version=1)},
                        secret_key=secrets.token_hex(32), site_settings=self.config.site)
                admin, _ = upgrade_store(legacy, self.config.site, {})
                weekly = clean_history(admin.pop('weekly_history', None))
                redpoints = validate_gaming(admin.pop('redpoints', None))
                # Retired profile data is intentionally removed. The untouched legacy document
                # is retained in the automatic import recovery file below.
                admin.pop("community_boss", None)
                admin.pop("community_boss_avatar", None)
                marker = valid_marker(admin.pop("recovery_export", None))
                if not admin["users"]:
                    raise StoreError("Saved account store contains no accounts. The original was not replaced.")
                snapshots = clean_snapshots(admin.pop("leaderboard_snapshots"), race_key(admin["site_settings"]))
                admin.pop("health", None)
                admin["superadmin"] = self.config.superadmin
                saved = empty(admin["site_settings"])
                saved.update(rows=snapshots["last_top15"], previous_top=snapshots["prev_top15"],
                             updated_at=snapshots["updated_at"] or 0, snapshot_only=bool(snapshots["last_top15"]),
                             count=len(snapshots["last_top15"]), warning="Only the saved Top 15 is available until Shuffle responds." if snapshots["last_top15"] else "")
                saved["source"] = [dict(username=r["username"], weighted=r["original_weighted_wager"],
                                        raw=r["raw_wager"], row_count=r["row_count"]) for r in saved["rows"]]
                value = dict(format=1, key=self.key, revision=1, admin=admin, live={"shuffle": saved, "weekly_history":weekly},
                             gaming=redpoints, checkpoint=marker, recoveries=[])
                self.backup_in(value, "before-rebuild-import", {"admin": legacy, "source": source})
                LOG.info("MIGRATION Imported %s; original accounts, hashes and dates retained.", source)
            atomic_json(self.path, value)
            self._remember(value)
            LOG.info("STORAGE JSON save ready. No SQL or extra service is used.")

    def _import_sqlite(self):
        """One-time, read-only bridge from the previous release. Never delete it."""
        path = self.config.db_path
        if not path.is_file():
            return None
        import sqlite3  # Standard library, used only for the old-save import.
        try:
            with sqlite3.connect(path.resolve().as_uri() + "?mode=ro", uri=True) as old:
                old.execute("BEGIN")
                row = old.execute("SELECT revision,document FROM rh_admin WHERE name=?", (self.key,)).fetchone()
                if not row:
                    raise StoreError("The previous local save has no matching account record. It was not replaced.")
                admin = json.loads(row[1])
                upgrade_store(admin, self.config.site, {})
                if not admin.get('users'):
                    raise StoreError('The previous local save has no accounts. It was not replaced.')
                tables = {r[0] for r in old.execute("SELECT name FROM sqlite_master WHERE type='table'")}
                value = dict(format=1, key=self.key, revision=row[0], admin=admin,
                             live={r[0]: json.loads(r[1]) for r in old.execute("SELECT service,document FROM rh_live WHERE name=?", (self.key,))},
                             recoveries=[])
                row = old.execute("SELECT document FROM rh_checkpoint WHERE name=?", (self.key,)).fetchone() if 'rh_checkpoint' in tables else None
                value['checkpoint'] = json.loads(row[0]) if row else None
                value['gaming'] = None
                if 'rh_recovery' in tables:
                    for reason, created, document in old.execute("SELECT reason,created,document FROM rh_recovery WHERE name=? ORDER BY created DESC LIMIT 10", (self.key,)):
                        self.backup_in(value, reason, json.loads(document), created=created)
        except (sqlite3.Error, ValueError) as exc:
            raise StoreError("The old local save could not be imported. Keep it intact; no default accounts or state replaced it.") from exc
        LOG.info("MIGRATION Previous SQLite save imported into JSON; old file left intact. New writes use JSON only.")
        return value

    def admin(self):
        with self.connection() as value:
            return value['revision'], copy.deepcopy(value['admin'])

    def checkpoint(self, marker=None):
        if marker is not None:
            marker = valid_marker(marker)
            if marker is None: raise ValueError("Invalid recovery export metadata.")
        with self.connection(transaction=marker is not None) as value:
            if marker is not None: value['checkpoint'] = marker
            return copy.deepcopy(value.get('checkpoint'))

    def live(self, service):
        with self.connection() as value:
            return copy.deepcopy(value['live'].get(service))

    def live_in(self, conn, service, value):
        conn['live'][service] = copy.deepcopy(value)

    def publish(self, service, value, expected_revision=None):
        with self.connection(transaction=True) as conn:
            if expected_revision is not None and conn['revision'] != expected_revision:
                raise Conflict("Race settings changed during the provider check; a new check is queued.")
            self.live_in(conn, service, value)

    def save(self, value, revision, *, snapshot=None, backup_reason=None):
        with self.connection(transaction=True) as conn:
            if conn['revision'] != revision:
                raise Conflict("Another administrator saved changes. Reload and review before saving again.")
            if backup_reason:
                self.backup_in(conn, backup_reason, {'admin': conn['admin'], 'live': conn['live']})
            conn['admin'], conn['revision'] = copy.deepcopy(value), revision + 1
            if snapshot is not None: self.live_in(conn, 'shuffle', snapshot)
        return revision + 1

    def backup_in(self, conn, reason, document, *, created=None):
        # Local recovery copies are bounded and are NOT a remote backup service.
        created = int(time.time()) if created is None else created
        folder = self.path.parent / 'recovery'
        name = f"{created}-{secrets.token_hex(8)}.json"
        atomic_json(folder / name, dict(reason=reason, created=created, document=document))
        records = conn.setdefault('recoveries', [])
        records.append(dict(file=name, reason=reason, created=created))
        conn['recoveries'] = records[-10:]
        # Retain a few additional files so a failed parent commit never deletes
        # a recovery file still referenced by the committed state.
        for path in sorted(folder.glob('*.json'), key=lambda p: p.stat().st_mtime_ns, reverse=True)[20:]:
            path.unlink(missing_ok=True)

    @contextmanager
    def job(self, service):
        yield True

    def close_job(self):
        pass

    def close(self):
        pass
