import importlib
import os
import tempfile
import time
import unittest
from unittest import mock


class CoreTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.temp_dir = tempfile.TemporaryDirectory()
        os.environ["ADMIN_STORE_PATH"] = os.path.join(cls.temp_dir.name, "admin_store.json")
        os.environ["ADMIN_BOOTSTRAP_USER"] = "test_admin"
        os.environ["ADMIN_BOOTSTRAP_PASS"] = "this-is-a-secure-test-password"
        os.environ["SECRET_KEY"] = "test-secret-key-that-is-long-enough-for-unit-tests-only"
        os.environ["DISABLE_BACKGROUND_REFRESH"] = "1"
        os.environ["SESSION_COOKIE_SECURE"] = "0"
        cls.backend = importlib.import_module("wager_backend")

    @classmethod
    def tearDownClass(cls):
        cls.temp_dir.cleanup()

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
        self.assertEqual(migrated["version"], 3)
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


if __name__ == "__main__":
    unittest.main()
