"""Run against a disposable database supplied as TEST_DATABASE_URL.

These checks never use DATABASE_URL implicitly. CI provisions its own database;
local development skips them unless a dedicated test database is provided.
"""
import copy
import os
from pathlib import Path
import secrets
import sys
import tempfile
import unittest
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from config import Config
from race import empty
from storage import Conflict, Store

TEST_URL = os.getenv("TEST_DATABASE_URL", "")
TEST_SSLMODE = os.getenv("TEST_DATABASE_SSLMODE", "require")


@unittest.skipUnless(TEST_URL, "No dedicated TEST_DATABASE_URL provided")
class PostgreSQLTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.key = "test_" + secrets.token_hex(12)
        self.environment = patch.dict(os.environ, {
            "APP_ENV": "production", "STORAGE_MODE": "postgres", "DATABASE_URL": TEST_URL, "DATABASE_SSLMODE": TEST_SSLMODE,
            "APP_STATE_KEY": self.key, "ADMIN_BOOTSTRAP_PASS": "synthetic-test-password",
        }, clear=True)
        self.environment.start()
        self.addCleanup(self.environment.stop)
        self.config = Config(Path(self.temp.name))
        self.store = Store(self.config)
        self.addCleanup(self.cleanup_database)

    def cleanup_database(self):
        self.store.close_job()
        with self.store.connection(transaction=True) as conn:
            for table in ("rh_live", "rh_boss", "rh_recovery", "rh_admin"):
                conn.execute("DELETE FROM " + table + " WHERE name=%s", (self.key,))
            if conn.execute("SELECT to_regclass('wager_state')").fetchone()[0]:
                conn.execute("DELETE FROM wager_state WHERE name=%s", (self.key,))
        self.store.close()

    def test_admin_conflicts_are_transactional_and_live_updates_keep_revision(self):
        revision, admin = self.store.admin()
        snapshot = empty(admin["site_settings"])
        self.store.publish("shuffle", snapshot, revision)
        self.assertEqual(self.store.admin()[0], revision)
        admin["site_settings"]["race_title"] = "Saved change"
        self.store.save(admin, revision)
        with self.assertRaises(Conflict):
            self.store.save(admin, revision, snapshot={"wrong": True}, backup_reason="must-rollback")
        self.assertEqual(self.store.live("shuffle"), snapshot)
        with self.assertRaises(Conflict):
            self.store.publish("shuffle", {"wrong": True}, revision)
        self.assertEqual(self.store.live("shuffle"), snapshot)

    def test_provider_lock_is_shared_between_connections_and_services_are_independent(self):
        other = Store(self.config)
        try:
            with self.store.job("shuffle") as first, other.job("shuffle") as duplicate:
                self.assertTrue(first)
                self.assertFalse(duplicate)
                with other.job("kick") as kick:
                    self.assertTrue(kick)
            with other.job("shuffle") as released:
                self.assertTrue(released)
        finally:
            other.close_job()
            other.close()

    def test_previous_jsonb_state_imports_once_and_original_table_is_unchanged(self):
        from psycopg.types.json import Jsonb
        _, legacy = self.store.admin()
        legacy["site_settings"]["race_title"] = "Original saved title"
        legacy["custom_preserved_field"] = {"source": "existing deployment"}
        with self.store.connection(transaction=True) as conn:
            conn.execute("CREATE TABLE IF NOT EXISTS wager_state (name TEXT PRIMARY KEY, payload JSONB NOT NULL)")
            conn.execute("INSERT INTO wager_state(name,payload) VALUES (%s,%s)", (self.key, Jsonb(legacy)))
            conn.execute("DELETE FROM rh_admin WHERE name=%s", (self.key,))
        self.store.close()
        self.store = Store(self.config)
        revision, imported = self.store.admin()
        self.assertEqual(imported["users"], legacy["users"])
        self.assertEqual(imported["custom_preserved_field"], legacy["custom_preserved_field"])
        with self.store.connection() as conn:
            self.assertEqual(conn.execute("SELECT payload FROM wager_state WHERE name=%s", (self.key,)).fetchone()[0], legacy)
        imported["site_settings"]["race_title"] = "Newer title wins"
        self.store.save(imported, revision)
        self.store.close()
        self.store = Store(self.config)
        self.assertEqual(self.store.admin()[1]["site_settings"]["race_title"], "Newer title wins")

    def test_invalid_document_rolls_back_private_backup_and_admin_write(self):
        revision, admin = self.store.admin()
        candidate = copy.deepcopy(admin)
        candidate["invalid"] = float("nan")
        with self.store.connection() as conn:
            count = conn.execute("SELECT count(*) FROM rh_recovery WHERE name=%s", (self.key,)).fetchone()[0]
        with self.assertRaises(ValueError):
            self.store.save(candidate, revision, backup_reason="invalid-candidate")
        self.assertEqual(self.store.admin(), (revision, admin))
        with self.store.connection() as conn:
            self.assertEqual(conn.execute("SELECT count(*) FROM rh_recovery WHERE name=%s", (self.key,)).fetchone()[0], count)
