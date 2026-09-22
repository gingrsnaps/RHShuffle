"""Render real templates against synthetic data for the optional DOM test suite."""
import json
import os
from pathlib import Path
import sys
import tempfile
import time
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from wager_backend import create_app
from race import calculate, empty, normalize


def render(destination):
    destination.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory() as directory, patch.dict(os.environ, {
        "APP_ENV": "test", "DATABASE_URL": "", "ADMIN_BOOTSTRAP_PASS": "fixture-password-only",
        "SUPERADMIN_USER": "gingrsnaps", "SECRET_KEY": "", "ADMIN_STORE_PATH": directory + "/none.json",
        "ADMIN_SEED_PATH": directory + "/none-seed.json", "LOCAL_DATABASE_PATH": directory + "/test.sqlite3",
        "SETTINGS_PATH": directory + "/none-settings.json",
    }):
        app = create_app(Path(directory), testing=True)
        runtime = app.extensions["runtime"]
        try:
            now = int(time.time())
            admin = runtime.admin
            admin["site_settings"].update(start_time=now-3600, end_time=now+86400)
            admin["overrides"]["ExamplePlayer000"] = "2000"
            source = [{"username": f"ExamplePlayer{i:03}", "weightedWagerAmount": str(1000-i),
                       "wagerAmount": str(3000-i), "campaignCode": "Red"} for i in range(105)]
            source.append({"username": "<img src=x onerror=alert(1)>", "weightedWagerAmount": "99999", "campaignCode": "Red"})
            snapshot = calculate({**empty(admin["site_settings"]), **normalize(source, admin["site_settings"]),
                                  "updated_at": now, "ok": True}, admin, runtime.config)
            runtime.commit(admin, runtime.revision, snapshot=snapshot)
            client = app.test_client()
            for name, url in {"public": "/", "login": "/admin", "error": "/missing", "play": "/play"}.items():
                (destination/(name+".html")).write_text(client.get(url).text, encoding="utf-8")
            with client.session_transaction() as session:
                session.update(user="gingrsnaps", auth_version=1, csrf="fixture-csrf")
            for tab in ("overview", "race", "players", "boss", "settings"):
                (destination/(tab+".html")).write_text(client.get("/admin?tab="+tab).text, encoding="utf-8")
            (destination/"boss.json").write_text(json.dumps(client.get("/play/api/state").json), encoding="utf-8")
            (destination/"public.json").write_text(json.dumps(client.get("/data").json), encoding="utf-8")
            (destination/"admin.json").write_text(json.dumps(client.get("/admin/status?code_red=1").json), encoding="utf-8")
        finally:
            runtime.store.close()


if __name__ == "__main__":
    render(Path(sys.argv[1]))
