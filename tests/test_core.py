import importlib
import os
from pathlib import Path
import tempfile
import time
import unittest
from unittest import mock


class CoreTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.temp_dir = tempfile.TemporaryDirectory()
        os.environ["ADMIN_STORE_PATH"] = os.path.join(cls.temp_dir.name, "admin_store.json")
        os.environ["SUPERADMIN_USER"] = "test_admin"
        os.environ["ADMIN_BOOTSTRAP_USER"] = "test_admin"
        os.environ["ADMIN_BOOTSTRAP_PASS"] = "this-is-a-secure-test-password"
        os.environ["SECRET_KEY"] = "test-secret-key-that-is-long-enough-for-unit-tests-only"
        os.environ["DISABLE_BACKGROUND_REFRESH"] = "1"
        os.environ["SESSION_COOKIE_SECURE"] = "0"
        cls.backend = importlib.import_module("wager_backend")

    @classmethod
    def tearDownClass(cls):
        cls.temp_dir.cleanup()

    def test_configured_superadmin_can_manage_admins(self):
        with self.backend.app.test_request_context("/admin"):
            self.backend.session["admin_user"] = "TEST_ADMIN"
            self.assertTrue(self.backend.is_superadmin())
            self.backend.session["admin_user"] = "ordinary_admin"
            self.assertFalse(self.backend.is_superadmin())

    def test_admin_template_has_admin_management_without_payout_column(self):
        template = (Path(self.backend.BASE_DIR) / "templates" / "admin_panel.html").read_text(encoding="utf-8")
        backend_source = (Path(self.backend.BASE_DIR) / "wager_backend.py").read_text(encoding="utf-8")
        self.assertIn('id="admin-users"', template)
        self.assertIn('name="action" value="add_admin"', template)
        self.assertNotIn('<th>Payout</th>', template)
        self.assertNotIn('name="payout_status"', template)
        self.assertNotIn('"payout_status",\n            "source"', backend_source)
        self.assertNotIn("set_payout_status", backend_source)
        self.assertIn("Wager Race Control Center", template)
        self.assertIn("Save Wager Race Settings", template)
        self.assertIn("Export Leaderboard", template)
        self.assertIn('name="new_password_confirm"', template)

    def test_superadmin_can_add_an_admin(self):
        username = "new_admin_test"
        with self.backend._store_lock:
            self.backend.STORE.setdefault("users", {}).pop(username, None)
            self.backend.store_save(self.backend.STORE)

        with self.backend.app.test_client() as client:
            with client.session_transaction() as session_data:
                session_data["admin_user"] = "test_admin"
                session_data["csrf_token"] = "test-csrf-token"
            response = client.post(
                "/admin/action",
                data={
                    "csrf_token": "test-csrf-token",
                    "action": "add_admin",
                    "new_username": username,
                    "new_password": "a-valid-new-admin-password",
                    "new_password_confirm": "a-valid-new-admin-password",
                },
                follow_redirects=False,
            )
        self.assertEqual(response.status_code, 302)
        with self.backend._store_lock:
            self.assertIn(username, self.backend.STORE.get("users", {}))
            self.backend.STORE["users"].pop(username, None)
            self.backend.store_save(self.backend.STORE)

    def test_prize_schedule_has_fifteen_places(self):
        self.assertEqual(self.backend.LEADERBOARD_SIZE, 15)
        self.assertEqual(len(self.backend.PRIZES), 15)
        self.assertEqual(sum(self.backend.PRIZES.values()), 5000)
        self.assertEqual(self.backend.PRIZES[1], 1800)
        self.assertEqual(self.backend.PRIZES[15], 20)

    def test_username_masking(self):
        self.assertEqual(self.backend.censor_username("ExampleUser"), "Ex******")
        self.assertEqual(self.backend.censor_username("A"), "A******")

    def test_strict_money_parser(self):
        value, error = self.backend.parse_money_strict("$25,000.50")
        self.assertIsNone(error)
        self.assertEqual(value, 25000.50)
        value, error = self.backend.parse_money_strict("25k")
        self.assertIsNone(value)
        self.assertIsNotNone(error)

    def test_public_payload_supports_top_fifteen(self):
        rows = [
            {
                "rank": rank,
                "username": f"Player{rank}",
                "weighted_wager": 1000 - rank,
                "wager": f"${1000 - rank:,.2f}",
            }
            for rank in range(1, 16)
        ]
        payload = self.backend._public_payload_from_top(rows)
        self.assertEqual(len(payload["podium"]), 3)
        self.assertEqual(len(payload["others"]), 12)
        self.assertEqual(payload["others"][-1]["rank"], 15)

    def test_old_store_migrates_and_redacts_url_errors(self):
        old_store = {
            "version": 2,
            "secret_key": "old-secret-that-was-long-enough-but-is-now-rotated",
            "users": {"test_admin": {"pw_hash": "not-used-in-this-test"}},
            "health": {"last_error": "400 for https://affiliate.shuffle.com/wager/secret"},
            "leaderboard_snapshots": {"last_top11": [{"rank": 1}], "prev_top11": []},
        }
        migrated, dirty = self.backend.store_ensure_keys(old_store)
        self.assertTrue(dirty)
        self.assertEqual(migrated["version"], 5)
        self.assertEqual(migrated["leaderboard_snapshots"]["last_top15"], [{"rank": 1}])
        self.assertNotIn("https://", migrated["health"]["last_error"])
        self.assertNotEqual(
            migrated["secret_key"],
            "old-secret-that-was-long-enough-but-is-now-rotated",
        )

    def test_kick_offline_response(self):
        channel = {
            "slug": "redhunllef",
            "broadcaster_user_id": 123,
            "stream_title": "",
            "stream": {"is_live": False, "viewer_count": 0},
        }
        with mock.patch.object(self.backend, "fetch_kick_channel", return_value=channel):
            result = self.backend._fetch_kick_status_uncached()
        self.assertFalse(result["live"])
        self.assertTrue(result["available"])
        self.assertIsNone(result["viewers"])

    def test_kick_hidden_viewer_count(self):
        channel = {
            "slug": "redhunllef",
            "broadcaster_user_id": 123,
            "stream_title": "Test stream",
            "category": {"name": "Just Chatting"},
            "stream": {
                "is_live": True,
                "viewer_count": 0,
                "start_time": "2026-08-05T00:00:00Z",
            },
        }
        with mock.patch.object(self.backend, "fetch_kick_channel", return_value=channel):
            result = self.backend._fetch_kick_status_uncached()
        self.assertTrue(result["live"])
        self.assertTrue(result["viewer_count_hidden"])
        self.assertIsNone(result["viewers"])

    def test_cached_kick_token_is_reused(self):
        previous = dict(self.backend.KICK_TOKEN_CACHE)
        try:
            self.backend.KICK_TOKEN_CACHE.update(
                {"access_token": "cached-token", "expires_at": int(time.time()) + 600}
            )
            with mock.patch.object(self.backend.HTTP, "request") as request_mock:
                token = self.backend.get_kick_app_token()
            self.assertEqual(token, "cached-token")
            request_mock.assert_not_called()
        finally:
            self.backend.KICK_TOKEN_CACHE.clear()
            self.backend.KICK_TOKEN_CACHE.update(previous)

    def test_race_state_transitions(self):
        old_start = self.backend.START_TIME
        old_end = self.backend.END_TIME
        try:
            self.backend.START_TIME = 100
            self.backend.END_TIME = 200
            self.assertEqual(self.backend.race_state(50), "upcoming")
            self.assertEqual(self.backend.race_state(150), "active")
            self.assertEqual(self.backend.race_state(250), "ended")
        finally:
            self.backend.START_TIME = old_start
            self.backend.END_TIME = old_end

    def test_admin_race_banner(self):
        old_start = self.backend.START_TIME
        old_end = self.backend.END_TIME
        try:
            self.backend.START_TIME = 100
            self.backend.END_TIME = 200
            self.assertEqual(self.backend.admin_race_banner(50)["title"], "Upcoming")
            self.assertEqual(self.backend.admin_race_banner(150)["title"], "Active")
            self.assertEqual(self.backend.admin_race_banner(250)["title"], "Ended")
        finally:
            self.backend.START_TIME = old_start
            self.backend.END_TIME = old_end

    def test_public_url_validation(self):
        self.assertTrue(self.backend._valid_public_url("https://kick.com/redhunllef"))
        self.assertFalse(self.backend._valid_public_url("javascript:alert(1)"))
        self.assertTrue(self.backend._valid_public_url("", allow_blank=True))

    def test_safe_backup_excludes_accounts_and_secrets(self):
        backup = self.backend.build_safe_backup()
        self.assertIn("site_settings", backup)
        self.assertNotIn("payout_status", backup)
        self.assertNotIn("users", backup)
        self.assertNotIn("secret_key", backup)


if __name__ == "__main__":
    unittest.main()
