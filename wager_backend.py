# -*- coding: utf-8 -*-
"""RedHunllef weighted wager race backend.

The public leaderboard ranks users by Shuffle's weighted wager value, masks
usernames, displays the configured Top 15 prizes, and exposes a cached Kick
live-status endpoint. Administrative functions include weighted overrides,
CSV export, health details, IP bans, audit logs, and admin-user management.

Environment variables take priority over settings.json. Credentials may be
loaded from settings.json for simple deployment, but environment variables are
strongly preferred for production.
"""
from __future__ import annotations

import csv
import io
import ipaddress
import json
import logging
import math
import os
import re
import secrets
import threading
import time
from datetime import datetime, timedelta
from functools import wraps
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional, Tuple
from urllib.parse import urlparse

import requests
from itsdangerous import BadSignature, SignatureExpired, URLSafeTimedSerializer
from flask import (
    Flask,
    Response,
    abort,
    flash,
    g,
    jsonify,
    has_request_context,
    redirect,
    render_template,
    request,
    session,
    url_for,
)
from flask.sessions import SecureCookieSessionInterface
from werkzeug.middleware.proxy_fix import ProxyFix
from werkzeug.security import check_password_hash, generate_password_hash

# ---------------------------------------------------------------------------
# Settings
# ---------------------------------------------------------------------------

BASE_DIR = Path(__file__).resolve().parent


def _resolve_app_path(value: Optional[str], default_name: str) -> str:
    """Resolve relative configuration/data paths from the project directory.

    This keeps startup reliable when Python or Gunicorn is launched from a
    different working directory, which is common in VS Code and hosted app
    platforms. Absolute paths are preserved.
    """
    raw = str(value or default_name).strip() or default_name
    path = Path(raw).expanduser()
    if not path.is_absolute():
        path = BASE_DIR / path
    return str(path.resolve())


SETTINGS_PATH = _resolve_app_path(os.getenv("SETTINGS_PATH"), "settings.json")


def load_settings() -> Dict[str, Any]:
    """Load application settings from settings.json when it exists."""
    try:
        with open(SETTINGS_PATH, "r", encoding="utf-8") as handle:
            value = json.load(handle)
        return value if isinstance(value, dict) else {}
    except FileNotFoundError:
        return {}
    except (OSError, json.JSONDecodeError):
        return {}


SETTINGS = load_settings()


def _env_str(name: str, default: str = "") -> str:
    value = os.getenv(name)
    return str(default or "") if value is None else value.strip()


def _settings_str(name: str, default: str = "") -> str:
    return str(SETTINGS.get(name, default) or "").strip()


def _env_or_setting(env_name: str, setting_name: str, default: str = "") -> str:
    return _env_str(env_name) or _settings_str(setting_name, default)


def _coerce_int(value: Any, default: int) -> int:
    try:
        return int(value)
    except (TypeError, ValueError):
        return int(default)


def _env_int(name: str, default: int) -> int:
    value = os.getenv(name)
    return _coerce_int(value, default) if value not in (None, "") else int(default)


def _settings_int(name: str, default: int) -> int:
    return _coerce_int(SETTINGS.get(name, default), default)


def _coerce_bool(value: Any, default: bool) -> bool:
    if value is None:
        return bool(default)
    if isinstance(value, bool):
        return value
    text = str(value).strip().lower()
    if text in {"1", "true", "yes", "on"}:
        return True
    if text in {"0", "false", "no", "off"}:
        return False
    return bool(default)


def _env_bool(name: str, default: bool) -> bool:
    return _coerce_bool(os.getenv(name), default)


def _settings_bool(name: str, default: bool) -> bool:
    return _coerce_bool(SETTINGS.get(name), default)


PORT = _env_int("PORT", _settings_int("port", 8080))
REFRESH_SECONDS = max(15, _env_int("REFRESH_SECONDS", _settings_int("refresh_seconds", 60)))
START_TIME = _env_int("START_TIME", _settings_int("start_time", 0))
END_TIME = _env_int("END_TIME", _settings_int("end_time", 0))
LEADERBOARD_SIZE = max(3, min(50, _env_int("LEADERBOARD_SIZE", _settings_int("leaderboard_size", 15))))
FULL_LEADERBOARD_MAX = max(
    LEADERBOARD_SIZE,
    _env_int("FULL_LEADERBOARD_MAX", _settings_int("full_leaderboard_max", 300)),
)

DEFAULT_PRIZES: Dict[int, float] = {
    1: 1800,
    2: 1200,
    3: 800,
    4: 450,
    5: 200,
    6: 150,
    7: 90,
    8: 80,
    9: 70,
    10: 60,
    11: 20,
    12: 20,
    13: 20,
    14: 20,
    15: 20,
}


def _load_prizes() -> Dict[int, float]:
    raw = SETTINGS.get("prizes")
    if not isinstance(raw, dict):
        return dict(DEFAULT_PRIZES)

    prizes: Dict[int, float] = dict(DEFAULT_PRIZES)
    for key, value in raw.items():
        try:
            rank = int(key)
            amount = float(value)
        except (TypeError, ValueError):
            continue
        if 1 <= rank <= LEADERBOARD_SIZE and math.isfinite(amount) and amount >= 0:
            prizes[rank] = amount
    return prizes


PRIZES = _load_prizes()

SHUFFLE_API_KEY = (
    _env_str("SHUFFLE_API_KEY")
    or _env_str("API_KEY")
    or _settings_str("shuffle_api_key")
)
SHUFFLE_ENDPOINT_KIND = (
    _env_or_setting("SHUFFLE_ENDPOINT_KIND", "shuffle_endpoint_kind", "wager") or "wager"
).strip("/")
SHUFFLE_AGGREGATION_MODE = (
    _env_or_setting("SHUFFLE_AGGREGATION_MODE", "shuffle_aggregation_mode", "sum") or "sum"
).lower()
if SHUFFLE_AGGREGATION_MODE not in {"sum", "max"}:
    SHUFFLE_AGGREGATION_MODE = "sum"

ALLOW_RAW_WAGER_FALLBACK = _env_bool(
    "ALLOW_RAW_WAGER_FALLBACK",
    _settings_bool("allow_raw_wager_fallback", False),
)
CAMPAIGN_CODE_FILTER = _env_or_setting("CAMPAIGN_CODE_FILTER", "campaign_code_filter", "Red")

KICK_CHANNEL_SLUG = _env_or_setting("KICK_CHANNEL_SLUG", "kick_channel_slug", "redhunllef")
KICK_CLIENT_ID = _env_or_setting("KICK_CLIENT_ID", "kick_client_id", "")
KICK_CLIENT_SECRET = _env_or_setting("KICK_CLIENT_SECRET", "kick_client_secret", "")
KICK_STATUS_TTL = max(15, _env_int("KICK_STATUS_TTL", _settings_int("kick_status_ttl", 30)))
KICK_CHANNEL_TTL = max(300, _env_int("KICK_CHANNEL_TTL", _settings_int("kick_channel_ttl", 86400)))

def _cookie_secure_mode() -> str:
    """Return auto, always, or never for the admin session cookie.

    ``auto`` makes local HTTP development work while still adding the Secure
    attribute whenever Flask sees an HTTPS request. ProxyFix is applied before
    the cookie is saved, so hosted HTTPS requests remain protected.
    """
    raw_env = os.getenv("SESSION_COOKIE_SECURE")
    raw = raw_env if raw_env is not None else SETTINGS.get("session_cookie_secure", "auto")
    if isinstance(raw, bool):
        return "always" if raw else "never"
    text = str(raw or "auto").strip().lower()
    if text in {"1", "true", "yes", "on", "always"}:
        return "always"
    if text in {"0", "false", "no", "off", "never"}:
        return "never"
    return "auto"


SESSION_COOKIE_SECURE_MODE = _cookie_secure_mode()
SESSION_COOKIE_SECURE = SESSION_COOKIE_SECURE_MODE == "always"
ADMIN_STORE_PATH = _resolve_app_path(os.getenv("ADMIN_STORE_PATH"), "admin_store.json")
ACCESS_LOG_MAX = max(50, _env_int("ACCESS_LOG_MAX", _settings_int("access_log_max", 300)))
AUDIT_LOG_MAX = max(50, _env_int("AUDIT_LOG_MAX", _settings_int("audit_log_max", 250)))
LOGIN_WINDOW_SECONDS = max(60, _env_int("LOGIN_WINDOW_SECONDS", 10 * 60))
LOGIN_MAX_FAILURES = max(2, _env_int("LOGIN_MAX_FAILURES", 5))
LOGIN_LOCK_SECONDS = max(60, _env_int("LOGIN_LOCK_SECONDS", 15 * 60))
MIN_ADMIN_PASSWORD_LENGTH = max(12, _env_int("MIN_ADMIN_PASSWORD_LENGTH", 12))

SUPERADMIN = (
    _env_or_setting("SUPERADMIN_USER", "superadmin_user", "gingrsnaps") or "gingrsnaps"
).strip()
BOOTSTRAP_USER = (
    _env_or_setting("ADMIN_BOOTSTRAP_USER", "admin_bootstrap_user", SUPERADMIN) or SUPERADMIN
).strip()
BOOTSTRAP_PASS = _env_or_setting("ADMIN_BOOTSTRAP_PASS", "admin_bootstrap_pass", "")
RESET_ADMIN_STORE_ON_START = _env_bool(
    "RESET_ADMIN_STORE_ON_START",
    _settings_bool("reset_admin_store_on_start", False),
)
RESET_BOOTSTRAP_PASSWORD_ON_START = _env_bool(
    "RESET_BOOTSTRAP_PASSWORD_ON_START",
    _settings_bool("reset_bootstrap_password_on_start", False),
)
REPAIR_BOOTSTRAP_LOGIN_ON_UPGRADE = _env_bool(
    "REPAIR_BOOTSTRAP_LOGIN_ON_UPGRADE",
    _settings_bool("repair_bootstrap_login_on_upgrade", True),
)
DISABLE_BACKGROUND_REFRESH = _env_bool("DISABLE_BACKGROUND_REFRESH", False)

PROXY_FIX_X_FOR = max(0, _env_int("PROXY_FIX_X_FOR", _settings_int("proxy_fix_x_for", 1)))
PROXY_FIX_X_PROTO = max(0, _env_int("PROXY_FIX_X_PROTO", _settings_int("proxy_fix_x_proto", 1)))
PROXY_FIX_X_HOST = max(0, _env_int("PROXY_FIX_X_HOST", _settings_int("proxy_fix_x_host", 1)))
PROXY_FIX_X_PORT = max(0, _env_int("PROXY_FIX_X_PORT", _settings_int("proxy_fix_x_port", 1)))
PROXY_FIX_X_PREFIX = max(0, _env_int("PROXY_FIX_X_PREFIX", _settings_int("proxy_fix_x_prefix", 0)))

SITE_NAME = _settings_str("site_name", "RedHunllef") or "RedHunllef"
RACE_TITLE = _settings_str("race_title", "RedHunllef Wager Race") or "RedHunllef Wager Race"
RACE_DESCRIPTION = _settings_str(
    "race_description",
    "Track the top weighted wagerers for RedHunllef's active race.",
)
SPONSOR_NAME = _settings_str("sponsor_name", "Shuffle.com") or "Shuffle.com"
SPONSOR_URL = _settings_str("sponsor_url", "https://shuffle.com/?r=Red")
STREAM_URL = _settings_str("stream_url", f"https://kick.com/{KICK_CHANNEL_SLUG}")
COMMUNITY_NAME = _settings_str("community_name", "Discord") or "Discord"
COMMUNITY_URL = _settings_str("community_url", "https://discord.gg/nhCbCZQEMK")
RESPONSIBLE_GAMBLING_URL = _settings_str(
    "responsible_gambling_url",
    "https://www.ncpgambling.org/responsible-gambling/",
)


def default_site_settings() -> Dict[str, Any]:
    return {
        "site_name": SITE_NAME,
        "race_title": RACE_TITLE,
        "race_description": RACE_DESCRIPTION,
        "start_time": START_TIME,
        "end_time": END_TIME,
        "refresh_seconds": REFRESH_SECONDS,
        "leaderboard_size": LEADERBOARD_SIZE,
        "prizes": {str(rank): float(PRIZES.get(rank, 0)) for rank in range(1, LEADERBOARD_SIZE + 1)},
        "kick_channel_slug": KICK_CHANNEL_SLUG,
        "campaign_code_filter": CAMPAIGN_CODE_FILTER,
        "sponsor_name": SPONSOR_NAME,
        "sponsor_url": SPONSOR_URL,
        "stream_url": STREAM_URL,
        "community_name": COMMUNITY_NAME,
        "community_url": COMMUNITY_URL,
        "responsible_gambling_url": RESPONSIBLE_GAMBLING_URL,
    }


def normalize_site_settings(value: Any) -> Dict[str, Any]:
    source = value if isinstance(value, dict) else {}
    defaults = default_site_settings()
    output = dict(defaults)

    for key in (
        "site_name",
        "race_title",
        "race_description",
        "kick_channel_slug",
        "campaign_code_filter",
        "sponsor_name",
        "sponsor_url",
        "stream_url",
        "community_name",
        "community_url",
        "responsible_gambling_url",
    ):
        if key in source:
            output[key] = str(source.get(key) or "").strip()

    output["start_time"] = max(0, _coerce_int(source.get("start_time"), defaults["start_time"]))
    output["end_time"] = max(0, _coerce_int(source.get("end_time"), defaults["end_time"]))
    output["refresh_seconds"] = max(
        15,
        min(3600, _coerce_int(source.get("refresh_seconds"), defaults["refresh_seconds"])),
    )
    output["leaderboard_size"] = 15

    raw_prizes = source.get("prizes")
    prizes: Dict[str, float] = {}
    for rank in range(1, 16):
        raw = raw_prizes.get(str(rank)) if isinstance(raw_prizes, dict) else defaults["prizes"].get(str(rank))
        try:
            amount = float(raw)
        except (TypeError, ValueError):
            amount = float(DEFAULT_PRIZES.get(rank, 0))
        if not math.isfinite(amount) or amount < 0:
            amount = float(DEFAULT_PRIZES.get(rank, 0))
        prizes[str(rank)] = amount
    output["prizes"] = prizes

    if not output["stream_url"] and output["kick_channel_slug"]:
        output["stream_url"] = f"https://kick.com/{output['kick_channel_slug']}"
    return output


def apply_site_settings(value: Dict[str, Any]) -> None:
    global SITE_NAME, RACE_TITLE, RACE_DESCRIPTION
    global START_TIME, END_TIME, REFRESH_SECONDS, LEADERBOARD_SIZE, PRIZES
    global KICK_CHANNEL_SLUG, CAMPAIGN_CODE_FILTER
    global SPONSOR_NAME, SPONSOR_URL, STREAM_URL
    global COMMUNITY_NAME, COMMUNITY_URL, RESPONSIBLE_GAMBLING_URL

    clean = normalize_site_settings(value)
    SITE_NAME = clean["site_name"] or "RedHunllef"
    RACE_TITLE = clean["race_title"] or f"{SITE_NAME} Wager Race"
    RACE_DESCRIPTION = clean["race_description"]
    START_TIME = int(clean["start_time"])
    END_TIME = int(clean["end_time"])
    REFRESH_SECONDS = int(clean["refresh_seconds"])
    LEADERBOARD_SIZE = 15
    PRIZES = {rank: float(clean["prizes"].get(str(rank), 0)) for rank in range(1, 16)}
    KICK_CHANNEL_SLUG = clean["kick_channel_slug"]
    CAMPAIGN_CODE_FILTER = clean["campaign_code_filter"]
    SPONSOR_NAME = clean["sponsor_name"] or "Sponsor"
    SPONSOR_URL = clean["sponsor_url"]
    STREAM_URL = clean["stream_url"]
    COMMUNITY_NAME = clean["community_name"] or "Community"
    COMMUNITY_URL = clean["community_url"]
    RESPONSIBLE_GAMBLING_URL = clean["responsible_gambling_url"]


# ---------------------------------------------------------------------------
# Time formatting
# ---------------------------------------------------------------------------

try:
    from zoneinfo import ZoneInfo

    ET = ZoneInfo("America/New_York")
except Exception:  # pragma: no cover - only relevant on unusual Python builds
    ET = None


def fmt_et(epoch: int) -> str:
    """Format epoch seconds in Eastern Time, falling back to UTC."""
    if not epoch:
        return "—"
    try:
        if ET:
            value = datetime.fromtimestamp(int(epoch), tz=ET)
            return value.strftime("%b %d, %Y %I:%M:%S %p %Z")
        value = datetime.utcfromtimestamp(int(epoch))
        return value.strftime("%b %d, %Y %I:%M:%S %p UTC")
    except (OverflowError, OSError, TypeError, ValueError):
        return "—"


# ---------------------------------------------------------------------------
# Flask application and locks
# ---------------------------------------------------------------------------


class AdaptiveSecureCookieSessionInterface(SecureCookieSessionInterface):
    """Use Secure cookies for HTTPS without breaking HTTP development.

    A cookie marked ``Secure`` is never returned by browsers over plain HTTP.
    Older deployments could therefore render the login page but lose the CSRF
    session before the form was submitted. The effective flag now follows the
    current request transport. ``SESSION_COOKIE_SECURE=never`` remains an
    explicit opt-out for unusual development environments.
    """

    @staticmethod
    def _request_uses_https() -> bool:
        if not has_request_context():
            return False
        if request.is_secure:
            return True
        # ProxyFix normally turns this into request.is_secure. Keeping this
        # fallback makes the app tolerant of a platform that forwards the
        # header without applying the expected proxy configuration.
        forwarded = str(request.headers.get("X-Forwarded-Proto") or "")
        return forwarded.split(",", 1)[0].strip().lower() == "https"

    def get_cookie_secure(self, app: Flask) -> bool:  # type: ignore[override]
        mode = str(app.config.get("SESSION_COOKIE_SECURE_MODE", "auto")).lower()
        if mode == "never":
            return False
        # Even when "always" was supplied, setting Secure on an HTTP response
        # makes login impossible. Use Secure whenever the request is HTTPS and
        # omit it only when the current request is actually plain HTTP.
        return self._request_uses_https()


app = Flask(__name__)
app.url_map.strict_slashes = False
app.wsgi_app = ProxyFix(
    app.wsgi_app,
    x_for=PROXY_FIX_X_FOR,
    x_proto=PROXY_FIX_X_PROTO,
    x_host=PROXY_FIX_X_HOST,
    x_port=PROXY_FIX_X_PORT,
    x_prefix=PROXY_FIX_X_PREFIX,
)
app.config.update(
    # A versioned name avoids conflicts with an old Secure-only cookie that a
    # browser may refuse to replace from a local HTTP origin.
    SESSION_COOKIE_NAME="redhunllef_admin_v2",
    SESSION_COOKIE_PATH="/",
    SESSION_COOKIE_DOMAIN=None,
    SESSION_COOKIE_HTTPONLY=True,
    SESSION_COOKIE_SAMESITE="Lax",
    SESSION_COOKIE_SECURE=False,
    SESSION_COOKIE_SECURE_MODE=SESSION_COOKIE_SECURE_MODE,
    PERMANENT_SESSION_LIFETIME=timedelta(days=7),
    SESSION_REFRESH_EACH_REQUEST=False,
    MAX_CONTENT_LENGTH=1 * 1024 * 1024,
)
app.session_interface = AdaptiveSecureCookieSessionInterface()

logging.basicConfig(level=logging.INFO)
app.logger.setLevel(logging.INFO)

_store_lock = threading.RLock()
_access_log_lock = threading.RLock()
_login_lock = threading.RLock()
_cache_lock = threading.RLock()
_admin_cache_lock = threading.RLock()
_force_refresh_lock = threading.Lock()
_kick_token_lock = threading.RLock()
_kick_channel_lock = threading.RLock()
_kick_status_lock = threading.RLock()
_background_lock = threading.Lock()

HTTP = requests.Session()
HTTP.headers.update({"User-Agent": "RedHunllef-WagerRace/3.2"})

STORE: Dict[str, Any] = {}
ACCESS_LOG: List[dict] = []
LOGIN_FAILURES: Dict[str, Dict[str, Any]] = {}
DATA_CACHE: Dict[str, Any] = {"podium": [], "others": [], "meta": {}}
ADMIN_CACHE: Dict[str, Any] = {"top": [], "full": [], "last_refresh": 0}

KICK_TOKEN_CACHE: Dict[str, Any] = {"access_token": "", "expires_at": 0}
KICK_CHANNEL_CACHE: Dict[str, Any] = {"slug": "", "broadcaster_user_id": None, "expires_at": 0}
KICK_STATUS_CACHE: Dict[str, Any] = {
    "value": {
        "live": None,
        "available": False,
        "stale": False,
        "title": None,
        "viewers": None,
        "viewer_count_hidden": False,
        "category": None,
        "started_at": None,
        "source": "kick_api",
        "updated": 0,
    },
    "expires_at": 0,
    "last_success": 0,
}
KICK_HEALTH: Dict[str, Any] = {
    "ok": None,
    "last_check_et": None,
    "last_error": None,
    "last_api_ms": None,
    "live": None,
    "source": "kick_api",
}

# ---------------------------------------------------------------------------
# Persistent admin store
# ---------------------------------------------------------------------------


def _default_health() -> Dict[str, Any]:
    return {
        "last_refresh_ok": None,
        "last_refresh_et": None,
        "last_error": None,
        "last_api_ms": None,
        "last_source": None,
        "last_row_count": 0,
        "last_weighted_row_count": 0,
        "last_skipped_missing_weighted": 0,
        "aggregation_mode": SHUFFLE_AGGREGATION_MODE,
        "endpoint_kind": SHUFFLE_ENDPOINT_KIND,
    }


def store_default() -> Dict[str, Any]:
    now = int(time.time())
    users: Dict[str, Any] = {}
    if BOOTSTRAP_PASS:
        users[BOOTSTRAP_USER] = {
            "pw_hash": generate_password_hash(BOOTSTRAP_PASS),
            "created_at": now,
            "created_by": "bootstrap",
        }
    return {
        "version": 6,
        "secret_key": secrets.token_hex(32),
        "users": users,
        "overrides": {},
        "site_settings": default_site_settings(),
        "audit_log": [],
        "banned_ips": [],
        "health": _default_health(),
        "leaderboard_snapshots": {
            "prev_top15": [],
            "last_top15": [],
            "updated_at": None,
        },
        "updated_at": now,
    }


def store_save(store: Dict[str, Any]) -> None:
    """Atomically write admin_store.json and restrict its permissions when possible."""
    directory = os.path.dirname(os.path.abspath(ADMIN_STORE_PATH))
    os.makedirs(directory, exist_ok=True)
    temporary = ADMIN_STORE_PATH + ".tmp"
    with open(temporary, "w", encoding="utf-8") as handle:
        json.dump(store, handle, indent=2)
        handle.flush()
        os.fsync(handle.fileno())
    os.replace(temporary, ADMIN_STORE_PATH)
    try:
        os.chmod(ADMIN_STORE_PATH, 0o600)
    except OSError:
        pass


def store_load_from_disk() -> Dict[str, Any]:
    if RESET_ADMIN_STORE_ON_START:
        value = store_default()
        if not value.get("users"):
            raise RuntimeError(
                "RESET_ADMIN_STORE_ON_START requires ADMIN_BOOTSTRAP_PASS."
            )
        store_save(value)
        return value

    if not os.path.exists(ADMIN_STORE_PATH):
        value = store_default()
        if not value.get("users"):
            raise RuntimeError(
                "No admin store exists. Set ADMIN_BOOTSTRAP_USER and "
                "ADMIN_BOOTSTRAP_PASS for the first startup."
            )
        store_save(value)
        return value

    try:
        with open(ADMIN_STORE_PATH, "r", encoding="utf-8") as handle:
            value = json.load(handle)
        if not isinstance(value, dict):
            raise ValueError("admin store root is not an object")
        return value
    except (OSError, json.JSONDecodeError, ValueError) as exc:
        replacement = store_default()
        if not replacement.get("users"):
            raise RuntimeError(
                "admin_store.json could not be read and no bootstrap password was supplied."
            ) from exc
        store_save(replacement)
        return replacement


def store_ensure_keys(store: Dict[str, Any]) -> Tuple[Dict[str, Any], bool]:
    """Migrate old stores without deleting unknown data."""
    dirty = False
    original_version = _coerce_int(store.get("version"), 0)

    def ensure(key: str, value: Any) -> None:
        nonlocal dirty
        if key not in store:
            store[key] = value
            dirty = True

    ensure("version", 6)
    ensure("secret_key", secrets.token_hex(32))

    persistent_secret = str(store.get("secret_key") or "")
    if (
        original_version < 3
        or persistent_secret.upper().startswith(("GENERATED_", "REPLACE_"))
        or len(persistent_secret) < 32
    ):
        store["secret_key"] = secrets.token_hex(32)
        dirty = True
    ensure("users", {})
    ensure("overrides", {})
    ensure("site_settings", default_site_settings())
    ensure("audit_log", [])
    ensure("banned_ips", [])
    ensure("health", _default_health())
    ensure("leaderboard_snapshots", {})
    ensure("updated_at", int(time.time()))

    if store.get("version") != 6:
        store["version"] = 6
        dirty = True

    if not isinstance(store.get("users"), dict):
        store["users"] = {}
        dirty = True
    if not isinstance(store.get("overrides"), dict):
        store["overrides"] = {}
        dirty = True
    if "payout_status" in store:
        store.pop("payout_status", None)
        dirty = True

    normalized_site = normalize_site_settings(store.get("site_settings"))
    if store.get("site_settings") != normalized_site:
        store["site_settings"] = normalized_site
        dirty = True
    if not isinstance(store.get("audit_log"), list):
        store["audit_log"] = []
        dirty = True
    if not isinstance(store.get("banned_ips"), list):
        store["banned_ips"] = []
        dirty = True

    users = store["users"]
    bootstrap_key = next(
        (key for key in users if str(key).casefold() == BOOTSTRAP_USER.casefold()),
        None,
    )
    if bootstrap_key is None and BOOTSTRAP_PASS:
        users[BOOTSTRAP_USER] = {
            "pw_hash": generate_password_hash(BOOTSTRAP_PASS),
            "created_at": int(time.time()),
            "created_by": "bootstrap",
        }
        bootstrap_key = BOOTSTRAP_USER
        dirty = True
    elif bootstrap_key is not None and BOOTSTRAP_PASS and (
        RESET_BOOTSTRAP_PASSWORD_ON_START
        or (original_version < 6 and REPAIR_BOOTSTRAP_LOGIN_ON_UPGRADE)
    ):
        # Version 6 repairs the configured bootstrap login once. This resolves
        # deployments that retained an older admin_store.json whose hash no
        # longer matches the password supplied in settings/environment. The
        # repair is migration-only unless the explicit reset flag is enabled.
        record = users.get(bootstrap_key)
        if not isinstance(record, dict):
            record = {}
            users[bootstrap_key] = record
        record["pw_hash"] = generate_password_hash(BOOTSTRAP_PASS)
        record["updated_at"] = int(time.time())
        record["password_repaired_by_version"] = 6
        dirty = True

    health = store.get("health")
    if not isinstance(health, dict):
        health = {}
        store["health"] = health
        dirty = True
    for key, value in _default_health().items():
        if key not in health:
            health[key] = value
            dirty = True

    # Older request exceptions could include credential-bearing URLs. Never carry
    # those values into the upgraded store or the admin health panel.
    old_error = str(health.get("last_error") or "")
    if "http://" in old_error.lower() or "https://" in old_error.lower():
        health["last_error"] = "Previous external-service error redacted during migration."
        dirty = True

    snapshots = store.get("leaderboard_snapshots")
    if not isinstance(snapshots, dict):
        snapshots = {}
        store["leaderboard_snapshots"] = snapshots
        dirty = True

    # Preserve the old Top-11 history while moving to Top 15.
    if "prev_top15" not in snapshots:
        snapshots["prev_top15"] = list(snapshots.get("prev_top11") or [])
        dirty = True
    if "last_top15" not in snapshots:
        snapshots["last_top15"] = list(snapshots.get("last_top11") or [])
        dirty = True
    if "updated_at" not in snapshots:
        snapshots["updated_at"] = None
        dirty = True

    return store, dirty


def store_init() -> None:
    global STORE
    value = store_load_from_disk()
    value, dirty = store_ensure_keys(value)
    if not value.get("users"):
        raise RuntimeError(
            "No admin users exist. Set ADMIN_BOOTSTRAP_USER and ADMIN_BOOTSTRAP_PASS, "
            "then restart the application once to create the initial account."
        )
    STORE = value
    if dirty:
        STORE["updated_at"] = int(time.time())
        store_save(STORE)


store_init()
apply_site_settings(dict(STORE.get("site_settings") or {}))

_env_secret = _env_str("SECRET_KEY")
_settings_secret = _settings_str("secret_key")
if _settings_secret.upper().startswith("REPLACE_") or len(_settings_secret) < 32:
    _settings_secret = ""
app.secret_key = _env_secret or _settings_secret or str(STORE.get("secret_key") or secrets.token_hex(32))

# ---------------------------------------------------------------------------
# General helpers, authentication, validation, and audit logging
# ---------------------------------------------------------------------------


def money(amount: float) -> str:
    try:
        value = float(amount or 0)
    except (TypeError, ValueError):
        value = 0.0
    return f"${value:,.2f}"


def parse_money_to_float(value: Any) -> float:
    if isinstance(value, (int, float)):
        try:
            number = float(value)
            return number if math.isfinite(number) and number >= 0 else 0.0
        except (TypeError, ValueError):
            return 0.0

    text = str(value or "").strip()
    if not text:
        return 0.0
    cleaned = text.replace(",", "").replace("$", "").replace(" ", "")
    cleaned = re.sub(r"[^0-9.]", "", cleaned)
    if cleaned.count(".") > 1:
        first, remainder = cleaned.split(".", 1)
        cleaned = first + "." + remainder.replace(".", "")
    if cleaned in {"", "."}:
        return 0.0
    try:
        number = float(cleaned)
    except ValueError:
        return 0.0
    return number if math.isfinite(number) and number >= 0 else 0.0


_MONEY_PATTERN = re.compile(r"^\s*\$?\s*(?:\d+|\d{1,3}(?:,\d{3})+)(?:\.\d{1,2})?\s*$")


def parse_money_strict(value: str) -> Tuple[Optional[float], Optional[str]]:
    text = str(value or "")
    if not _MONEY_PATTERN.fullmatch(text):
        return None, "Use a non-negative amount such as 25000 or $25,000.00."
    number = float(text.replace("$", "").replace(",", "").strip())
    if not math.isfinite(number) or number < 0 or number > 1_000_000_000_000:
        return None, "The amount is outside the allowed range."
    return number, None


def censor_username(username: str) -> str:
    value = str(username or "").strip()
    return (value[:2] if value else "") + ("*" * 6)


def csrf_token() -> str:
    """Return the session-bound token used by authenticated admin actions."""
    token = session.get("csrf_token")
    if not token:
        token = secrets.token_urlsafe(32)
        session["csrf_token"] = token
    return token


def login_csrf_token() -> str:
    """Return a short-lived signed login token that does not require a cookie.

    The login page is the one place where a session cookie may not yet be
    usable. A stateless signed token preserves login-CSRF protection while
    avoiding the previous GET-cookie/POST-cookie dependency.
    """
    serializer = URLSafeTimedSerializer(str(app.secret_key), salt="admin-login-csrf-v2")
    return serializer.dumps({"purpose": "admin-login"})


def validate_login_csrf(value: str, max_age: int = 60 * 60) -> bool:
    token = str(value or "").strip()
    if not token:
        return False
    serializer = URLSafeTimedSerializer(str(app.secret_key), salt="admin-login-csrf-v2")
    try:
        payload = serializer.loads(token, max_age=max_age)
    except (BadSignature, SignatureExpired, TypeError, ValueError):
        return False
    return isinstance(payload, dict) and payload.get("purpose") == "admin-login"


@app.context_processor
def inject_template_helpers() -> Dict[str, Any]:
    return {
        "csrf_token": csrf_token,
        "login_csrf_token": login_csrf_token,
    }


def require_csrf() -> None:
    sent = str(request.form.get("csrf_token") or "").strip()
    expected = str(session.get("csrf_token") or "")
    if not sent or not expected or not secrets.compare_digest(sent, expected):
        abort(400)


def admin_user() -> Optional[str]:
    value = session.get("admin_user")
    return str(value) if value else None


def is_superadmin() -> bool:
    """Only the configured gingrsnaps superadmin account can manage other admins."""
    return (admin_user() or "").casefold() == SUPERADMIN.casefold()


def find_admin_account(username: str) -> Tuple[Optional[str], Optional[Dict[str, Any]]]:
    """Find an admin account without making login capitalization-sensitive."""
    requested = str(username or "").strip().casefold()
    if not requested:
        return None, None
    with _store_lock:
        users = STORE.get("users") or {}
        for stored_username, record in users.items():
            if str(stored_username).casefold() == requested and isinstance(record, dict):
                return str(stored_username), dict(record)
    return None, None


def login_required(function):
    @wraps(function)
    def wrapper(*args, **kwargs):
        if not admin_user():
            return redirect(url_for("admin"))
        return function(*args, **kwargs)

    return wrapper


def client_ip() -> str:
    return str(request.remote_addr or "unknown").strip() or "unknown"


def _trim(value: Any, length: int = 160) -> str:
    text = str(value or "")
    return text if len(text) <= length else text[: length - 1] + "…"


def _append_rolling(values: List[dict], entry: dict, maximum: int) -> List[dict]:
    values.append(entry)
    return values[-maximum:] if len(values) > maximum else values


def audit(action: str, detail: Dict[str, Any]) -> None:
    with _store_lock:
        entry = {
            "ts": int(time.time()),
            "ts_et": fmt_et(int(time.time())),
            "admin_user": admin_user() or "system",
            "ip": client_ip() if has_request_context() else "system",
            "action": action,
            "detail": detail,
        }
        STORE["audit_log"] = _append_rolling(
            list(STORE.get("audit_log") or []),
            entry,
            AUDIT_LOG_MAX,
        )
        STORE["updated_at"] = int(time.time())
        store_save(STORE)
    app.logger.info(
        "[AUDIT] user=%s ip=%s action=%s detail=%s",
        entry["admin_user"],
        entry["ip"],
        action,
        detail,
    )


def login_locked(ip: str) -> Tuple[bool, int]:
    now = int(time.time())
    with _login_lock:
        record = LOGIN_FAILURES.get(ip) or {"failures": [], "locked_until": 0}
        locked_until = int(record.get("locked_until") or 0)
        if locked_until > now:
            return True, locked_until - now
        return False, 0


def login_record_failure(ip: str) -> None:
    now = int(time.time())
    with _login_lock:
        record = LOGIN_FAILURES.setdefault(ip, {"failures": [], "locked_until": 0})
        failures = [
            int(value)
            for value in record.get("failures", [])
            if now - int(value) <= LOGIN_WINDOW_SECONDS
        ]
        failures.append(now)
        record["failures"] = failures
        if len(failures) >= LOGIN_MAX_FAILURES:
            record["locked_until"] = now + LOGIN_LOCK_SECONDS
            app.logger.warning("[LOGIN_LOCK] ip=%s seconds=%s", ip, LOGIN_LOCK_SECONDS)


def login_record_success(ip: str) -> None:
    with _login_lock:
        LOGIN_FAILURES.pop(ip, None)


def _valid_admin_username(username: str) -> bool:
    return bool(re.fullmatch(r"[A-Za-z0-9_]{3,32}", str(username or "").strip()))


def _valid_password(password: str) -> bool:
    return MIN_ADMIN_PASSWORD_LENGTH <= len(password) <= 256


def _normalized_ip(value: str) -> Optional[str]:
    try:
        return str(ipaddress.ip_address(str(value or "").strip()))
    except ValueError:
        return None


def _valid_public_url(value: str, *, allow_blank: bool = False) -> bool:
    text = str(value or "").strip()
    if not text:
        return allow_blank
    try:
        parsed = urlparse(text)
    except ValueError:
        return False
    return parsed.scheme in {"http", "https"} and bool(parsed.netloc)


def epoch_to_datetime_local(epoch: int) -> str:
    if not epoch:
        return ""
    try:
        if ET:
            return datetime.fromtimestamp(int(epoch), tz=ET).strftime("%Y-%m-%dT%H:%M")
        return datetime.utcfromtimestamp(int(epoch)).strftime("%Y-%m-%dT%H:%M")
    except (TypeError, ValueError, OverflowError, OSError):
        return ""


def datetime_local_to_epoch(value: str) -> Tuple[Optional[int], Optional[str]]:
    text = str(value or "").strip()
    if not text:
        return None, "Choose both a race start and end time."
    try:
        parsed = datetime.strptime(text, "%Y-%m-%dT%H:%M")
        if ET:
            parsed = parsed.replace(tzinfo=ET)
        return int(parsed.timestamp()), None
    except ValueError:
        return None, "Use the date and time picker instead of typing a custom date format."


def race_state(now: Optional[int] = None) -> str:
    current = int(now or time.time())
    if START_TIME and current < START_TIME:
        return "upcoming"
    if END_TIME and current >= END_TIME:
        return "ended"
    if START_TIME and END_TIME:
        return "active"
    return "unconfigured"


def _human_duration(seconds: int) -> str:
    seconds = max(0, int(seconds))
    days, remainder = divmod(seconds, 86400)
    hours, remainder = divmod(remainder, 3600)
    minutes = remainder // 60
    parts = []
    if days:
        parts.append(f"{days} day{'s' if days != 1 else ''}")
    if hours and len(parts) < 2:
        parts.append(f"{hours} hour{'s' if hours != 1 else ''}")
    if minutes and len(parts) < 2:
        parts.append(f"{minutes} minute{'s' if minutes != 1 else ''}")
    return ", ".join(parts) or "less than a minute"


def admin_race_banner(now: Optional[int] = None) -> Dict[str, str]:
    current = int(time.time()) if now is None else int(now)
    state = race_state(current)
    if state == "unconfigured":
        return {
            "title": "Schedule not configured",
            "detail": "Choose a start and end time in Wager Race Settings.",
        }
    if state == "upcoming":
        return {
            "title": "Upcoming",
            "detail": f"Begins {fmt_et(START_TIME)} · {_human_duration(START_TIME - current)} from now.",
        }
    if state == "active":
        return {
            "title": "Active",
            "detail": f"Ends {fmt_et(END_TIME)} · {_human_duration(END_TIME - current)} remaining.",
        }
    return {
        "title": "Ended",
        "detail": f"Ended {fmt_et(END_TIME)} · the final leaderboard remains available for review.",
    }


def public_site_settings() -> Dict[str, Any]:
    return {
        "site_name": SITE_NAME,
        "race_title": RACE_TITLE,
        "race_description": RACE_DESCRIPTION,
        "sponsor_name": SPONSOR_NAME,
        "sponsor_url": SPONSOR_URL,
        "stream_url": STREAM_URL,
        "community_name": COMMUNITY_NAME,
        "community_url": COMMUNITY_URL,
        "responsible_gambling_url": RESPONSIBLE_GAMBLING_URL,
    }


def reset_kick_caches() -> None:
    with _kick_token_lock:
        KICK_TOKEN_CACHE.update({"access_token": "", "expires_at": 0})
    with _kick_channel_lock:
        KICK_CHANNEL_CACHE.update({"slug": "", "broadcaster_user_id": None, "expires_at": 0})
    with _kick_status_lock:
        KICK_STATUS_CACHE.update({
            "value": {
                "live": None,
                "available": False,
                "stale": False,
                "title": None,
                "viewers": None,
                "viewer_count_hidden": False,
                "category": None,
                "started_at": None,
                "source": "kick_api",
                "updated": 0,
            },
            "expires_at": 0,
            "last_success": 0,
        })


def build_safe_backup() -> Dict[str, Any]:
    with _store_lock:
        return {
            "backup_version": 1,
            "generated_at": int(time.time()),
            "generated_at_et": fmt_et(int(time.time())),
            "site_settings": normalize_site_settings(STORE.get("site_settings")),
            "overrides": dict(STORE.get("overrides") or {}),
            "leaderboard_snapshots": dict(STORE.get("leaderboard_snapshots") or {}),
        }


# ---------------------------------------------------------------------------
# Request observability and security headers
# ---------------------------------------------------------------------------


@app.before_request
def before_request_observability():
    g._request_started = time.perf_counter()
    if request.path.startswith("/static/"):
        return None

    ip = client_ip()
    with _store_lock:
        banned = set(STORE.get("banned_ips") or [])
    if ip in banned:
        app.logger.warning("[BAN] blocked ip=%s path=%s", ip, request.path)
        abort(403)
    return None


@app.after_request
def after_request_security_and_observability(response: Response) -> Response:
    # Security headers. Templates contain no inline JavaScript or CSS.
    response.headers.setdefault(
        "Content-Security-Policy",
        "default-src 'self'; base-uri 'self'; form-action 'self'; "
        "frame-ancestors 'none'; object-src 'none'; img-src 'self' data:; "
        "style-src 'self'; script-src 'self'; connect-src 'self'",
    )
    response.headers.setdefault("X-Content-Type-Options", "nosniff")
    response.headers.setdefault("X-Frame-Options", "DENY")
    response.headers.setdefault("Referrer-Policy", "strict-origin-when-cross-origin")
    response.headers.setdefault(
        "Permissions-Policy",
        "camera=(), microphone=(), geolocation=(), payment=(), usb=()",
    )
    response.headers.setdefault("Cross-Origin-Opener-Policy", "same-origin")
    if request.is_secure:
        response.headers.setdefault(
            "Strict-Transport-Security",
            "max-age=31536000; includeSubDomains",
        )

    if request.path.startswith(("/admin", "/data", "/config", "/stream", "/healthz", "/readyz")):
        response.headers["Cache-Control"] = "no-store, max-age=0"

    if not request.path.startswith("/static/"):
        started = getattr(g, "_request_started", None)
        elapsed_ms = int((time.perf_counter() - started) * 1000) if started else None
        entry = {
            "ts": int(time.time()),
            "ts_et": fmt_et(int(time.time())),
            "ip": client_ip(),
            "method": request.method,
            "path": request.path,
            "status": int(response.status_code or 0),
            "ms": elapsed_ms,
            "ua": _trim(request.headers.get("User-Agent", "")),
        }
        app.logger.info(
            "[ACCESS] %s %s %s -> %s (%sms)",
            entry["ip"],
            entry["method"],
            entry["path"],
            entry["status"],
            entry["ms"],
        )
        with _access_log_lock:
            global ACCESS_LOG
            ACCESS_LOG = _append_rolling(ACCESS_LOG, entry, ACCESS_LOG_MAX)

    return response


# ---------------------------------------------------------------------------
# External HTTP helpers
# ---------------------------------------------------------------------------


class ExternalServiceError(RuntimeError):
    """Safe external-service error that never contains a credential-bearing URL."""


def _request_with_retry(
    method: str,
    url: str,
    service: str,
    *,
    attempts: int = 3,
    retry_statuses: Iterable[int] = (429, 500, 502, 503, 504),
    **kwargs: Any,
) -> requests.Response:
    last_status: Optional[int] = None
    last_exception_name: Optional[str] = None

    for attempt in range(max(1, attempts)):
        try:
            response = HTTP.request(method, url, **kwargs)
            last_status = int(response.status_code)
        except requests.RequestException as exc:
            last_exception_name = type(exc).__name__
            if attempt + 1 < attempts:
                time.sleep(0.4 * (2**attempt))
                continue
            raise ExternalServiceError(
                f"{service} request failed ({last_exception_name})."
            ) from None

        if response.status_code in set(retry_statuses) and attempt + 1 < attempts:
            retry_after = response.headers.get("Retry-After", "")
            try:
                delay = min(5.0, max(0.25, float(retry_after)))
            except ValueError:
                delay = 0.4 * (2**attempt)
            time.sleep(delay)
            continue
        return response

    if last_status is not None:
        raise ExternalServiceError(f"{service} returned HTTP {last_status}.")
    raise ExternalServiceError(f"{service} request failed ({last_exception_name or 'unknown error'}).")


def _response_json(response: requests.Response, service: str) -> Any:
    try:
        return response.json()
    except ValueError:
        raise ExternalServiceError(f"{service} returned an invalid JSON response.") from None


# ---------------------------------------------------------------------------
# Shuffle weighted leaderboard
# ---------------------------------------------------------------------------

SHUFFLE_URL_RANGE = "https://affiliate.shuffle.com/{kind}/{api_key}?startTime={start}&endTime={end}"
SHUFFLE_URL_LIFETIME = "https://affiliate.shuffle.com/{kind}/{api_key}"

WEIGHTING_RULES = [
    {"range": "RTP ≤ 98%", "counts": "100% of wagered amount"},
    {"range": "98% < RTP < 99%", "counts": "50% of wagered amount"},
    {"range": "RTP ≥ 99%", "counts": "10% of wagered amount"},
]
USERNAME_KEYS = ("username", "displayName", "userName", "player", "name")
WEIGHTED_KEYS = ("weightedWagerAmount", "weightedWager", "weightedAmount", "wagerWeighted")
RAW_WAGER_KEYS = ("wagerAmount", "totalWagered", "wageredAmount", "rawWagerAmount")
CAMPAIGN_KEYS = ("campaignCode", "campaign", "code", "referralCode", "affiliateCode")


def sanitize_window() -> Tuple[int, int]:
    now = int(time.time())
    start = int(START_TIME or 0)
    end = int(END_TIME or 0)
    if start <= 0 or end <= 0 or end <= start:
        end = now
        start = max(0, now - 14 * 24 * 3600)
    if end > now:
        end = now
    return start, end


def _extract_rows(payload: Any) -> List[dict]:
    if isinstance(payload, list):
        return [item for item in payload if isinstance(item, dict)]
    if isinstance(payload, dict):
        for key in ("data", "results", "leaderboard", "users", "items"):
            value = payload.get(key)
            if isinstance(value, list):
                return [item for item in value if isinstance(item, dict)]
    return []


def _first_present(row: dict, keys: Iterable[str]) -> Any:
    for key in keys:
        if key in row:
            return row.get(key)
    return None


def _row_campaign(row: dict) -> Optional[str]:
    value = _first_present(row, CAMPAIGN_KEYS)
    return None if value is None else str(value).strip()


def _campaign_allowed(row: dict) -> bool:
    expected = str(CAMPAIGN_CODE_FILTER or "").strip()
    if not expected:
        return True
    actual = _row_campaign(row)
    return True if actual is None else actual.lower() == expected.lower()


def normalize_weighted_row(row: dict) -> Tuple[Optional[dict], Optional[str]]:
    username = str(_first_present(row, USERNAME_KEYS) or "").strip()
    if not username:
        return None, "missing_username"
    if not _campaign_allowed(row):
        return None, "campaign_filtered"

    weighted_raw = _first_present(row, WEIGHTED_KEYS)
    raw_wager_raw = _first_present(row, RAW_WAGER_KEYS)
    weighted = parse_money_to_float(weighted_raw)
    raw_wager = parse_money_to_float(raw_wager_raw)

    if weighted_raw is None:
        if ALLOW_RAW_WAGER_FALLBACK and raw_wager > 0:
            weighted = raw_wager
        else:
            return None, "missing_weightedWagerAmount"

    return {
        "username": username,
        "weightedWagerAmount": weighted,
        "wagerAmount": raw_wager if raw_wager_raw is not None else None,
        "campaignCode": _row_campaign(row),
        "source": "shuffle",
    }, None


def fetch_from_shuffle() -> Tuple[List[dict], Dict[str, Any]]:
    if not SHUFFLE_API_KEY:
        return [], {
            "ok": False,
            "ms": None,
            "error": "Missing SHUFFLE_API_KEY.",
            "source": "none",
            "row_count": 0,
        }

    headers = {"Accept": "application/json"}
    start, end = sanitize_window()
    started = time.perf_counter()

    try:
        range_url = SHUFFLE_URL_RANGE.format(
            kind=SHUFFLE_ENDPOINT_KIND,
            api_key=SHUFFLE_API_KEY,
            start=start,
            end=end,
        )
        response = _request_with_retry(
            "GET",
            range_url,
            "Shuffle",
            timeout=(5, 20),
            headers=headers,
        )
        elapsed_ms = int((time.perf_counter() - started) * 1000)

        if response.status_code == 400:
            lifetime_started = time.perf_counter()
            lifetime_url = SHUFFLE_URL_LIFETIME.format(
                kind=SHUFFLE_ENDPOINT_KIND,
                api_key=SHUFFLE_API_KEY,
            )
            response = _request_with_retry(
                "GET",
                lifetime_url,
                "Shuffle",
                timeout=(5, 20),
                headers=headers,
            )
            elapsed_ms = int((time.perf_counter() - lifetime_started) * 1000)
            if not response.ok:
                raise ExternalServiceError(f"Shuffle returned HTTP {response.status_code}.")
            rows = _extract_rows(_response_json(response, "Shuffle"))
            return rows, {
                "ok": True,
                "ms": elapsed_ms,
                "error": None,
                "source": "weighted_lifetime",
                "row_count": len(rows),
            }

        if not response.ok:
            raise ExternalServiceError(f"Shuffle returned HTTP {response.status_code}.")
        rows = _extract_rows(_response_json(response, "Shuffle"))
        return rows, {
            "ok": True,
            "ms": elapsed_ms,
            "error": None,
            "source": "weighted_range",
            "row_count": len(rows),
        }
    except ExternalServiceError as exc:
        return [], {
            "ok": False,
            "ms": int((time.perf_counter() - started) * 1000),
            "error": str(exc),
            "source": "none",
            "row_count": 0,
        }


def aggregate_by_username(entries: List[dict]) -> Dict[str, dict]:
    output: Dict[str, dict] = {}
    for entry in entries or []:
        username = str(entry.get("username", "")).strip()
        if not username:
            continue
        weighted = parse_money_to_float(entry.get("weightedWagerAmount"))
        raw_value = entry.get("wagerAmount")
        raw = parse_money_to_float(raw_value) if raw_value is not None else None

        previous = output.get(username)
        if previous is None:
            output[username] = {
                "username": username,
                "weightedWagerAmount": weighted,
                "wagerAmount": raw,
                "campaignCode": entry.get("campaignCode"),
                "source": entry.get("source", "shuffle"),
                "row_count": 1,
            }
            continue

        previous["row_count"] = int(previous.get("row_count") or 0) + 1
        if SHUFFLE_AGGREGATION_MODE == "max":
            previous["weightedWagerAmount"] = max(
                parse_money_to_float(previous.get("weightedWagerAmount")),
                weighted,
            )
            if raw is not None:
                old_raw = previous.get("wagerAmount")
                previous["wagerAmount"] = (
                    max(parse_money_to_float(old_raw), raw) if old_raw is not None else raw
                )
        else:
            previous["weightedWagerAmount"] = (
                parse_money_to_float(previous.get("weightedWagerAmount")) + weighted
            )
            if raw is not None:
                old_raw = previous.get("wagerAmount")
                previous["wagerAmount"] = (
                    parse_money_to_float(old_raw) if old_raw is not None else 0.0
                ) + raw
    return output


def _public_payload_from_top(
    top: List[Dict[str, Any]],
    *,
    stale: bool = False,
    updated_at: Optional[int] = None,
) -> Dict[str, Any]:
    podium: List[dict] = []
    others: List[dict] = []
    for row in top[:LEADERBOARD_SIZE]:
        rank = int(row.get("rank") or 0)
        if rank <= 0:
            continue
        public_row = {
            "username": censor_username(str(row.get("username") or "")),
            "wager": str(row.get("wager") or money(row.get("weighted_wager") or 0)),
            "weighted_wager": str(row.get("wager") or money(row.get("weighted_wager") or 0)),
        }
        if rank <= 3:
            podium.append(public_row)
        else:
            others.append({"rank": rank, **public_row})
    return {
        "podium": podium,
        "others": others,
        "meta": {
            "updated_at": int(updated_at or time.time()),
            "label": "Weighted Wager",
            "leaderboard_size": LEADERBOARD_SIZE,
            "stale": stale,
            "race_state": race_state(),
            "has_data": bool(top),
        },
    }

def build_snapshots() -> Tuple[Dict[str, Any], List[Dict[str, Any]], List[Dict[str, Any]], Dict[str, Any]]:
    raw_rows, meta = fetch_from_shuffle()
    normalized: List[dict] = []
    skipped_missing_weighted = 0
    skipped_campaign = 0
    skipped_username = 0

    for row in raw_rows:
        item, reason = normalize_weighted_row(row)
        if item:
            normalized.append(item)
        elif reason == "missing_weightedWagerAmount":
            skipped_missing_weighted += 1
        elif reason == "campaign_filtered":
            skipped_campaign += 1
        elif reason == "missing_username":
            skipped_username += 1

    by_name = aggregate_by_username(normalized)
    with _store_lock:
        overrides = dict(STORE.get("overrides") or {})

    for username, amount in overrides.items():
        clean_username = str(username).strip()
        if not clean_username:
            continue
        by_name[clean_username] = {
            "username": clean_username,
            "weightedWagerAmount": parse_money_to_float(amount),
            "wagerAmount": None,
            "campaignCode": CAMPAIGN_CODE_FILTER or None,
            "source": "override",
            "row_count": 1,
        }

    entries = [
        item
        for item in by_name.values()
        if parse_money_to_float(item.get("weightedWagerAmount")) >= 0.01
    ]
    entries.sort(
        key=lambda item: parse_money_to_float(item.get("weightedWagerAmount")),
        reverse=True,
    )

    admin_full: List[Dict[str, Any]] = []
    for rank, entry in enumerate(entries[:FULL_LEADERBOARD_MAX], start=1):
        weighted = parse_money_to_float(entry.get("weightedWagerAmount"))
        raw_value = entry.get("wagerAmount")
        raw = parse_money_to_float(raw_value) if raw_value is not None else None
        admin_full.append(
            {
                "rank": rank,
                "username": str(entry.get("username") or "Unknown"),
                "weighted_wager": weighted,
                "wager": money(weighted),
                "raw_wager": raw,
                "raw_wager_str": money(raw) if raw is not None else "—",
                "source": entry.get("source", "shuffle"),
                "row_count": int(entry.get("row_count") or 1),
            }
        )

    top = admin_full[:LEADERBOARD_SIZE]
    meta.update(
        {
            "weighted_row_count": len(normalized),
            "skipped_missing_weighted": skipped_missing_weighted,
            "skipped_campaign": skipped_campaign,
            "skipped_username": skipped_username,
            "aggregation_mode": SHUFFLE_AGGREGATION_MODE,
            "endpoint_kind": SHUFFLE_ENDPOINT_KIND,
            "campaign_code_filter": CAMPAIGN_CODE_FILTER,
        }
    )
    return _public_payload_from_top(top), top, admin_full, meta


def seed_cache_from_store() -> None:
    with _store_lock:
        snapshots = STORE.get("leaderboard_snapshots") or {}
        stored_top = list(snapshots.get("last_top15") or [])[:LEADERBOARD_SIZE]
        updated_at = int(snapshots.get("updated_at") or 0)
    if not stored_top:
        return
    with _cache_lock:
        DATA_CACHE.update(_public_payload_from_top(stored_top, stale=True, updated_at=updated_at))
    with _admin_cache_lock:
        ADMIN_CACHE["top"] = stored_top
        ADMIN_CACHE["full"] = stored_top
        ADMIN_CACHE["last_refresh"] = updated_at


def compute_top_deltas() -> List[Dict[str, Any]]:
    with _store_lock:
        snapshots = STORE.get("leaderboard_snapshots") or {}
        current = list(snapshots.get("last_top15") or [])
        previous = list(snapshots.get("prev_top15") or [])
    previous_map = {
        str(entry.get("username") or ""): parse_money_to_float(
            entry.get("weighted_wager", entry.get("wager"))
        )
        for entry in previous
    }
    previous_rank = {
        str(entry.get("username") or ""): int(entry.get("rank") or 0)
        for entry in previous
    }
    output: List[Dict[str, Any]] = []
    for entry in current[:LEADERBOARD_SIZE]:
        username = str(entry.get("username") or "")
        current_value = parse_money_to_float(entry.get("weighted_wager", entry.get("wager")))
        delta = current_value - previous_map.get(username, 0.0)
        current_rank = int(entry.get("rank") or 0)
        old_rank = previous_rank.get(username)
        rank_change = (old_rank - current_rank) if old_rank else None
        enriched = dict(entry)
        raw_value = enriched.get("raw_wager")
        raw_display = str(enriched.get("raw_wager_str") or "").strip()
        enriched["raw_wager_str"] = (
            raw_display
            if raw_display
            else money(raw_value)
            if raw_value is not None
            else "—"
        )
        enriched["delta"] = delta
        enriched["delta_str"] = (
            "+" + money(delta)
            if delta > 0
            else "-" + money(abs(delta))
            if delta < 0
            else "+$0.00"
        )
        enriched["rank_change"] = rank_change
        enriched["rank_change_label"] = (
            "New"
            if old_rank is None
            else f"↑ {rank_change}"
            if rank_change and rank_change > 0
            else f"↓ {abs(rank_change)}"
            if rank_change and rank_change < 0
            else "—"
        )
        enriched["prize"] = money(PRIZES.get(current_rank, 0))
        output.append(enriched)
    return output

def refresh_cache_once(reason: str = "tick") -> None:
    public, top, full, meta = build_snapshots()
    now = int(time.time())
    with _admin_cache_lock:
        had_data = bool(ADMIN_CACHE.get("top"))

    if not top and had_data:
        with _store_lock:
            health = STORE.setdefault("health", _default_health())
            health.update(
                {
                    "last_refresh_ok": False,
                    "last_refresh_et": fmt_et(now),
                    "last_error": meta.get("error") or "Shuffle returned no weighted leaderboard rows.",
                    "last_api_ms": meta.get("ms"),
                    "last_source": meta.get("source"),
                    "last_row_count": meta.get("row_count", 0),
                    "last_weighted_row_count": meta.get("weighted_row_count", 0),
                    "last_skipped_missing_weighted": meta.get("skipped_missing_weighted", 0),
                    "aggregation_mode": SHUFFLE_AGGREGATION_MODE,
                    "endpoint_kind": SHUFFLE_ENDPOINT_KIND,
                }
            )
            STORE["updated_at"] = now
            store_save(STORE)
        app.logger.warning(
            "[REFRESH] failed; retained old cache source=%s ms=%s rows=%s error=%s",
            meta.get("source"),
            meta.get("ms"),
            meta.get("row_count"),
            meta.get("error"),
        )
        return

    with _cache_lock:
        DATA_CACHE.update(public)
    with _admin_cache_lock:
        ADMIN_CACHE["top"] = top
        ADMIN_CACHE["full"] = full
        ADMIN_CACHE["last_refresh"] = now

    with _store_lock:
        health = STORE.setdefault("health", _default_health())
        health.update(
            {
                "last_refresh_ok": bool(meta.get("ok")) and bool(top),
                "last_refresh_et": fmt_et(now),
                "last_error": meta.get("error"),
                "last_api_ms": meta.get("ms"),
                "last_source": meta.get("source"),
                "last_row_count": meta.get("row_count", 0),
                "last_weighted_row_count": meta.get("weighted_row_count", 0),
                "last_skipped_missing_weighted": meta.get("skipped_missing_weighted", 0),
                "aggregation_mode": SHUFFLE_AGGREGATION_MODE,
                "endpoint_kind": SHUFFLE_ENDPOINT_KIND,
            }
        )
        snapshots = STORE.setdefault("leaderboard_snapshots", {})
        snapshots["prev_top15"] = list(snapshots.get("last_top15") or [])
        snapshots["last_top15"] = top
        snapshots["updated_at"] = now
        STORE["updated_at"] = now
        store_save(STORE)

    app.logger.info(
        "[REFRESH] ok=%s reason=%s source=%s ms=%s raw_rows=%s weighted_rows=%s top=%s full=%s",
        meta.get("ok"),
        reason,
        meta.get("source"),
        meta.get("ms"),
        meta.get("row_count"),
        meta.get("weighted_row_count"),
        len(top),
        len(full),
    )


# ---------------------------------------------------------------------------
# Kick OAuth and live status
# ---------------------------------------------------------------------------

KICK_TOKEN_URL = "https://id.kick.com/oauth/token"
KICK_API_BASE = "https://api.kick.com"


def _clear_kick_token() -> None:
    with _kick_token_lock:
        KICK_TOKEN_CACHE.update({"access_token": "", "expires_at": 0})


def get_kick_app_token(force: bool = False) -> str:
    now = int(time.time())
    with _kick_token_lock:
        token = str(KICK_TOKEN_CACHE.get("access_token") or "")
        expires_at = int(KICK_TOKEN_CACHE.get("expires_at") or 0)
        if token and not force and expires_at > now + 30:
            return token

        if not KICK_CLIENT_ID or not KICK_CLIENT_SECRET:
            raise ExternalServiceError("Kick credentials are not configured.")

        response = _request_with_retry(
            "POST",
            KICK_TOKEN_URL,
            "Kick OAuth",
            timeout=(5, 15),
            headers={"Accept": "application/json"},
            data={
                "grant_type": "client_credentials",
                "client_id": KICK_CLIENT_ID,
                "client_secret": KICK_CLIENT_SECRET,
            },
        )
        if not response.ok:
            raise ExternalServiceError(f"Kick OAuth returned HTTP {response.status_code}.")
        payload = _response_json(response, "Kick OAuth")
        if not isinstance(payload, dict) or not payload.get("access_token"):
            raise ExternalServiceError("Kick OAuth returned no access token.")

        token = str(payload["access_token"])
        expires_in = max(60, _coerce_int(payload.get("expires_in"), 3600))
        KICK_TOKEN_CACHE.update(
            {
                "access_token": token,
                "expires_at": now + max(60, expires_in - 60),
            }
        )
        return token


def kick_api_get(path: str, params: List[Tuple[str, Any]]) -> Any:
    for token_attempt in range(2):
        token = get_kick_app_token(force=token_attempt > 0)
        response = _request_with_retry(
            "GET",
            KICK_API_BASE + path,
            "Kick API",
            timeout=(5, 15),
            headers={
                "Accept": "application/json",
                "Authorization": f"Bearer {token}",
            },
            params=params,
        )
        if response.status_code == 401 and token_attempt == 0:
            _clear_kick_token()
            continue
        if not response.ok:
            raise ExternalServiceError(f"Kick API returned HTTP {response.status_code}.")
        return _response_json(response, "Kick API")
    raise ExternalServiceError("Kick API authorization failed.")


def fetch_kick_channel(force: bool = False) -> Dict[str, Any]:
    """Return the configured Kick channel using the documented slug lookup.

    The channel endpoint already includes current stream metadata. Using it as
    the primary source removes an unnecessary second API dependency.
    """
    now = int(time.time())
    slug = KICK_CHANNEL_SLUG.strip().lower()
    if not slug:
        raise ExternalServiceError("KICK_CHANNEL_SLUG is not configured.")

    # The broadcaster ID cache is still useful for the fallback livestream
    # endpoint, but live status itself is intentionally refreshed each TTL.
    payload = kick_api_get("/public/v1/channels", [("slug", slug)])
    data = payload.get("data") if isinstance(payload, dict) else None
    if not isinstance(data, list) or not data:
        raise ExternalServiceError("Kick channel was not found.")

    selected = next(
        (
            item
            for item in data
            if isinstance(item, dict) and str(item.get("slug") or "").lower() == slug
        ),
        data[0] if isinstance(data[0], dict) else None,
    )
    if not isinstance(selected, dict):
        raise ExternalServiceError("Kick returned an invalid channel response.")

    broadcaster_id = selected.get("broadcaster_user_id")
    try:
        broadcaster_id_int = int(broadcaster_id)
    except (TypeError, ValueError):
        broadcaster_id_int = 0

    if broadcaster_id_int:
        with _kick_channel_lock:
            KICK_CHANNEL_CACHE.update(
                {
                    "slug": slug,
                    "broadcaster_user_id": broadcaster_id_int,
                    "expires_at": now + KICK_CHANNEL_TTL,
                }
            )
    return selected


def resolve_kick_broadcaster_id(force: bool = False) -> int:
    now = int(time.time())
    slug = KICK_CHANNEL_SLUG.strip().lower()
    with _kick_channel_lock:
        cached_slug = str(KICK_CHANNEL_CACHE.get("slug") or "")
        cached_id = KICK_CHANNEL_CACHE.get("broadcaster_user_id")
        expires_at = int(KICK_CHANNEL_CACHE.get("expires_at") or 0)
        if cached_id and cached_slug == slug and not force and expires_at > now:
            return int(cached_id)

    channel = fetch_kick_channel(force=force)
    broadcaster_id = channel.get("broadcaster_user_id")
    try:
        return int(broadcaster_id)
    except (TypeError, ValueError):
        raise ExternalServiceError("Kick channel response did not include a broadcaster ID.") from None


def _kick_status_from_channel(channel: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    """Parse live status directly from GET /public/v1/channels when available."""
    stream = channel.get("stream")
    if not isinstance(stream, dict):
        return None

    now = int(time.time())
    live = bool(stream.get("is_live"))
    viewer_count = _coerce_int(stream.get("viewer_count"), 0)
    category = channel.get("category")
    category_name = category.get("name") if isinstance(category, dict) else None

    return {
        "live": live,
        "available": True,
        "stale": False,
        "title": (str(channel.get("stream_title") or "") or None) if live else None,
        "viewers": viewer_count if live and viewer_count > 0 else None,
        "viewer_count_hidden": bool(live and viewer_count == 0),
        "category": (str(category_name or "") or None) if live else None,
        "started_at": (str(stream.get("start_time") or "") or None) if live else None,
        "source": "kick_channels",
        "updated": now,
    }


def _fetch_kick_status_uncached() -> Dict[str, Any]:
    channel = fetch_kick_channel()
    channel_status = _kick_status_from_channel(channel)
    if channel_status is not None:
        return channel_status

    # Compatibility fallback for a channel response that omits the stream
    # object. Kick documents this endpoint for app access tokens and one or
    # more user_id query parameters.
    broadcaster_id = resolve_kick_broadcaster_id()
    payload = kick_api_get(
        "/public/v1/users/livestreams",
        [("user_id", broadcaster_id)],
    )
    data = payload.get("data") if isinstance(payload, dict) else None
    now = int(time.time())
    if not isinstance(data, list) or not data:
        return {
            "live": False,
            "available": True,
            "stale": False,
            "title": None,
            "viewers": None,
            "viewer_count_hidden": False,
            "category": None,
            "started_at": None,
            "source": "kick_livestreams",
            "updated": now,
        }

    stream = data[0] if isinstance(data[0], dict) else {}
    viewer_count = _coerce_int(stream.get("viewer_count"), 0)
    category = stream.get("category")
    category_name = category.get("name") if isinstance(category, dict) else None
    return {
        "live": True,
        "available": True,
        "stale": False,
        "title": str(stream.get("title") or "") or None,
        "viewers": viewer_count if viewer_count > 0 else None,
        "viewer_count_hidden": viewer_count == 0,
        "category": str(category_name or "") or None,
        "started_at": str(stream.get("started_at") or "") or None,
        "source": "kick_livestreams",
        "updated": now,
    }


def refresh_kick_status(force: bool = False) -> Dict[str, Any]:
    now = int(time.time())
    with _kick_status_lock:
        cached = dict(KICK_STATUS_CACHE.get("value") or {})
        expires_at = int(KICK_STATUS_CACHE.get("expires_at") or 0)
        if not force and cached and expires_at > now:
            return cached

        started = time.perf_counter()
        try:
            value = _fetch_kick_status_uncached()
            elapsed_ms = int((time.perf_counter() - started) * 1000)
            KICK_STATUS_CACHE.update(
                {
                    "value": value,
                    "expires_at": now + KICK_STATUS_TTL,
                    "last_success": now,
                }
            )
            KICK_HEALTH.update(
                {
                    "ok": True,
                    "last_check_et": fmt_et(now),
                    "last_error": None,
                    "last_api_ms": elapsed_ms,
                    "live": value.get("live"),
                    "source": "kick_api",
                }
            )
            return dict(value)
        except ExternalServiceError as exc:
            elapsed_ms = int((time.perf_counter() - started) * 1000)
            KICK_HEALTH.update(
                {
                    "ok": False,
                    "last_check_et": fmt_et(now),
                    "last_error": str(exc),
                    "last_api_ms": elapsed_ms,
                    "source": "kick_api",
                }
            )
            last_success = int(KICK_STATUS_CACHE.get("last_success") or 0)
            if cached and last_success:
                cached.update({"available": False, "stale": True, "updated": now})
                KICK_STATUS_CACHE.update(
                    {"value": cached, "expires_at": now + min(15, KICK_STATUS_TTL)}
                )
                return dict(cached)

            unavailable = {
                "live": None,
                "available": False,
                "stale": False,
                "title": None,
                "viewers": None,
                "viewer_count_hidden": False,
                "category": None,
                "started_at": None,
                "source": "kick_api",
                "updated": now,
            }
            KICK_STATUS_CACHE.update(
                {"value": unavailable, "expires_at": now + min(15, KICK_STATUS_TTL)}
            )
            return dict(unavailable)


# ---------------------------------------------------------------------------
# Background refresh
# ---------------------------------------------------------------------------

_background_started = False


def refresh_loop() -> None:
    while True:
        try:
            refresh_cache_once(reason="tick")
        except Exception as exc:  # keep the worker alive on unexpected errors
            app.logger.exception("[REFRESH_LOOP] leaderboard error: %s", exc)
        try:
            refresh_kick_status(force=True)
        except Exception as exc:
            app.logger.exception("[REFRESH_LOOP] Kick error: %s", exc)
        time.sleep(REFRESH_SECONDS)


def start_background_refresh() -> None:
    global _background_started
    if DISABLE_BACKGROUND_REFRESH:
        return
    with _background_lock:
        if _background_started:
            return
        _background_started = True
        # Let the background thread perform the initial refresh so worker startup
        # is not blocked by external API timeouts.
        threading.Thread(
            target=refresh_loop,
            name="wager-race-refresh",
            daemon=True,
        ).start()


seed_cache_from_store()
start_background_refresh()

# ---------------------------------------------------------------------------
# Public routes
# ---------------------------------------------------------------------------


@app.route("/")
def index():
    return render_template(
        "index.html",
        leaderboard_size=LEADERBOARD_SIZE,
        site=public_site_settings(),
        total_prize=money(sum(PRIZES.values())),
        default_prizes={rank: DEFAULT_PRIZES.get(rank, 0) for rank in range(1, LEADERBOARD_SIZE + 1)},
        refresh_seconds=REFRESH_SECONDS,
    )


@app.route("/data")
def data():
    with _cache_lock:
        payload = {
            "podium": list(DATA_CACHE.get("podium") or []),
            "others": list(DATA_CACHE.get("others") or []),
            "meta": dict(DATA_CACHE.get("meta") or {}),
        }
    payload["meta"]["race_state"] = race_state()
    return jsonify(payload)


@app.route("/config")
def config():
    return jsonify(
        {
            "start_time": START_TIME,
            "end_time": END_TIME,
            "server_time": int(time.time()),
            "race_state": race_state(),
            "refresh_seconds": REFRESH_SECONDS,
            "leaderboard_size": LEADERBOARD_SIZE,
            "leaderboard_label": "Weighted Wager",
            "weighting_rules": WEIGHTING_RULES,
            "prizes": {str(rank): money(PRIZES.get(rank, 0)) for rank in range(1, LEADERBOARD_SIZE + 1)},
            "total_prize": money(sum(PRIZES.values())),
        }
    )


@app.route("/stream")
def stream():
    return jsonify(refresh_kick_status(force=False))


@app.route("/healthz")
def healthz():
    """Liveness check for the hosting platform.

    External APIs can be temporarily unavailable without meaning the Flask
    process is dead. This endpoint therefore remains HTTP 200 while reporting
    a degraded status in JSON, preventing endless platform restart loops.
    """
    with _store_lock:
        shuffle_health = dict(STORE.get("health") or {})
    with _admin_cache_lock:
        full_count = len(ADMIN_CACHE.get("full") or [])
        top_count = len(ADMIN_CACHE.get("top") or [])
        last_refresh = int(ADMIN_CACHE.get("last_refresh") or 0)
    with _kick_status_lock:
        kick_health = dict(KICK_HEALTH)

    shuffle_ok = bool(shuffle_health.get("last_refresh_ok")) and top_count > 0
    kick_ok = kick_health.get("ok") is not False
    status = "ok" if shuffle_ok and kick_ok else "degraded"
    return jsonify(
        {
            "ok": True,
            "status": status,
            "process": "running",
            "race_state": race_state(),
            "shuffle": {
                "ok": shuffle_ok,
                "last_refresh_ok": shuffle_health.get("last_refresh_ok"),
                "last_refresh_et": shuffle_health.get("last_refresh_et"),
                "last_source": shuffle_health.get("last_source"),
                "last_error": shuffle_health.get("last_error"),
                "last_api_ms": shuffle_health.get("last_api_ms"),
                "leaderboard_count": full_count,
                "top_count": top_count,
                "last_refresh_epoch": last_refresh,
                "endpoint_kind": SHUFFLE_ENDPOINT_KIND,
                "aggregation_mode": SHUFFLE_AGGREGATION_MODE,
            },
            "kick": kick_health,
        }
    ), 200


@app.route("/readyz")
def readyz():
    """Strict readiness check for manual diagnostics, not platform liveness."""
    with _store_lock:
        shuffle_health = dict(STORE.get("health") or {})
    with _admin_cache_lock:
        top_count = len(ADMIN_CACHE.get("top") or [])
    ready = bool(shuffle_health.get("last_refresh_ok")) and top_count > 0
    return jsonify({"ready": ready, "top_count": top_count}), 200 if ready else 503


# ---------------------------------------------------------------------------
# Admin routes
# ---------------------------------------------------------------------------


@app.route("/admin", methods=["GET", "POST"])
def admin():
    if admin_user():
        return render_admin_panel()

    error = None
    if request.method == "POST":
        # Login uses a stateless signed token because the browser may not have
        # accepted a session cookie yet. Authenticated actions remain protected
        # by the stronger session-bound CSRF token.
        if not validate_login_csrf(request.form.get("login_csrf_token") or ""):
            error = "The login form expired or could not be verified. Please submit it again."
            app.logger.warning("[LOGIN_CSRF_FAIL] ip=%s", client_ip())
            return render_template("admin_login.html", error=error), 200

        ip = client_ip()
        locked, remaining = login_locked(ip)
        if locked:
            error = f"Too many failed login attempts. Try again in {max(1, math.ceil(remaining / 60))} minute(s)."
            return render_template("admin_login.html", error=error)

        username = str(request.form.get("username") or "").strip()
        password = str(request.form.get("password") or "")
        canonical_username, record = find_admin_account(username)
        valid_password = False
        if record:
            try:
                valid_password = check_password_hash(
                    str(record.get("pw_hash") or ""),
                    password,
                )
            except (TypeError, ValueError):
                valid_password = False

        if not canonical_username or not valid_password:
            login_record_failure(ip)
            error = "Invalid username or password."
            app.logger.warning("[LOGIN_FAIL] ip=%s user=%s", ip, username)
        else:
            login_record_success(ip)
            session.clear()
            session.permanent = True
            session["admin_user"] = canonical_username
            session["csrf_token"] = secrets.token_urlsafe(32)
            audit("login_ok", {"user": canonical_username})
            return redirect(url_for("admin"))

    return render_template("admin_login.html", error=error)


@app.route("/admin/logout", methods=["POST"])
@login_required
def admin_logout():
    require_csrf()
    username = admin_user()
    audit("logout", {"user": username})
    session.clear()
    return redirect(url_for("admin"))


def _admin_setup_checklist(
    *,
    health: Dict[str, Any],
    kick_health: Dict[str, Any],
    top_count: int,
    current_user_record: Dict[str, Any],
) -> List[Dict[str, Any]]:
    site = normalize_site_settings(STORE.get("site_settings"))
    dates_ok = bool(site["start_time"] and site["end_time"] and site["end_time"] > site["start_time"])
    prizes_ok = len(site.get("prizes") or {}) == 15 and all(
        parse_money_to_float((site.get("prizes") or {}).get(str(rank))) >= 0
        for rank in range(1, 16)
    )
    links_ok = all(
        _valid_public_url(site.get(key, ""), allow_blank=key in {"community_url", "responsible_gambling_url"})
        for key in ("sponsor_url", "stream_url", "community_url", "responsible_gambling_url")
    )
    password_changed = bool(current_user_record.get("updated_at")) or current_user_record.get("created_by") != "bootstrap"
    return [
        {"label": "Shuffle credentials configured", "ok": bool(SHUFFLE_API_KEY)},
        {"label": "Kick credentials configured", "ok": bool(KICK_CLIENT_ID and KICK_CLIENT_SECRET)},
        {"label": "Wager Race dates configured", "ok": dates_ok},
        {"label": "All 15 prizes configured", "ok": prizes_ok},
        {"label": "Public links are valid", "ok": links_ok},
        {"label": "Shuffle data connected", "ok": bool(health.get("last_refresh_ok")) and top_count > 0},
        {"label": "Kick live status connected", "ok": kick_health.get("ok") is True},
        {"label": "Admin password changed", "ok": password_changed},
    ]


def render_admin_panel():
    csrf_token()
    with _store_lock:
        overrides = dict(STORE.get("overrides") or {})
        audit_log = list(reversed(STORE.get("audit_log") or []))
        banned_ips = list(STORE.get("banned_ips") or [])
        health = dict(STORE.get("health") or {})
        users = dict(STORE.get("users") or {})
        admin_users = sorted(users.keys())
        site_settings = normalize_site_settings(STORE.get("site_settings"))
        current_user_record = dict(users.get(admin_user() or "") or {})
    with _access_log_lock:
        access_log = list(reversed(ACCESS_LOG))
    with _admin_cache_lock:
        top = list(ADMIN_CACHE.get("top") or [])
        full = list(ADMIN_CACHE.get("full") or [])
        last_refresh = int(ADMIN_CACHE.get("last_refresh") or 0)
    with _kick_status_lock:
        kick_health = dict(KICK_HEALTH)

    top_with_deltas = compute_top_deltas()
    full_enriched = []
    for row in full:
        item = dict(row)
        rank = int(item.get("rank") or 0)
        item["prize"] = money(PRIZES.get(rank, 0)) if rank <= LEADERBOARD_SIZE else "—"
        full_enriched.append(item)

    checklist = _admin_setup_checklist(
        health=health,
        kick_health=kick_health,
        top_count=len(top),
        current_user_record=current_user_record,
    )
    next_refresh = last_refresh + REFRESH_SECONDS if last_refresh else 0
    last_refresh_age = max(0, int(time.time()) - last_refresh) if last_refresh else None
    shuffle_connected = bool(health.get("last_refresh_ok")) and bool(top)
    kick_connected = kick_health.get("ok") is True
    public_connected = bool(top) and last_refresh_age is not None and last_refresh_age <= max(180, REFRESH_SECONDS * 3)

    return render_template(
        "admin_panel.html",
        admin_user=admin_user(),
        is_superadmin=is_superadmin(),
        superadmin_user=SUPERADMIN,
        refresh_seconds=REFRESH_SECONDS,
        leaderboard_size=LEADERBOARD_SIZE,
        start_et=fmt_et(START_TIME),
        end_et=fmt_et(END_TIME),
        start_input=epoch_to_datetime_local(START_TIME),
        end_input=epoch_to_datetime_local(END_TIME),
        last_refresh_et=fmt_et(last_refresh),
        next_refresh_et=fmt_et(next_refresh),
        last_refresh_age=last_refresh_age,
        endpoint_kind=SHUFFLE_ENDPOINT_KIND,
        aggregation_mode=SHUFFLE_AGGREGATION_MODE,
        campaign_code_filter=CAMPAIGN_CODE_FILTER or "—",
        weighting_rules=WEIGHTING_RULES,
        prizes={rank: PRIZES.get(rank, 0) for rank in range(1, LEADERBOARD_SIZE + 1)},
        total_prize=money(sum(PRIZES.values())),
        default_prizes={rank: DEFAULT_PRIZES.get(rank, 0) for rank in range(1, LEADERBOARD_SIZE + 1)},
        overrides=overrides,
        top=top,
        top_with_deltas=top_with_deltas,
        full_leaderboard=full_enriched,
        access_log=access_log,
        audit_log=audit_log,
        banned_ips=banned_ips,
        health=health,
        kick_health=kick_health,
        admin_users=admin_users,
        min_password_length=MIN_ADMIN_PASSWORD_LENGTH,
        site_settings=site_settings,
        setup_checklist=checklist,
        setup_complete=all(item["ok"] for item in checklist),
        shuffle_connected=shuffle_connected,
        kick_connected=kick_connected,
        public_connected=public_connected,
        race_state=race_state(),
        race_banner=admin_race_banner(),
        public_url=url_for("index", _external=True),
    )


@app.route("/admin/export.csv")
@login_required
def admin_export_csv():
    with _admin_cache_lock:
        rows = list(ADMIN_CACHE.get("full") or [])
        last_refresh = int(ADMIN_CACHE.get("last_refresh") or 0)
    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(
        [
            "rank",
            "username",
            "weighted_wager",
            "raw_wager",
            "prize",
            "source",
            "row_count",
            "last_refresh_et",
        ]
    )
    for row in rows:
        rank = int(row.get("rank") or 0)
        username = str(row.get("username") or "")
        writer.writerow(
            [
                rank,
                username,
                f"{parse_money_to_float(row.get('weighted_wager')):.2f}",
                "" if row.get("raw_wager") is None else f"{parse_money_to_float(row.get('raw_wager')):.2f}",
                f"{float(PRIZES.get(rank, 0)):.2f}" if rank <= LEADERBOARD_SIZE else "",
                row.get("source", ""),
                row.get("row_count", 1),
                fmt_et(last_refresh),
            ]
        )
    audit("export_csv", {"rows": len(rows)})
    return Response(
        output.getvalue(),
        mimetype="text/csv",
        headers={"Content-Disposition": "attachment; filename=redhunllef_wager_race_leaderboard.csv"},
    )


@app.route("/admin/backup.json")
@login_required
def admin_backup():
    payload = build_safe_backup()
    audit("download_backup", {"backup_version": payload.get("backup_version")})
    stamp = datetime.utcnow().strftime("%Y%m%d-%H%M%S")
    return Response(
        json.dumps(payload, indent=2),
        mimetype="application/json",
        headers={"Content-Disposition": f"attachment; filename=redhunllef-backup-{stamp}.json"},
    )


def _redirect_admin(anchor: str = ""):
    target = url_for("admin")
    if anchor:
        target += f"#{anchor}"
    return redirect(target)


@app.route("/admin/action", methods=["POST"])
@login_required
def admin_action():
    require_csrf()
    action = str(request.form.get("action") or "").strip()

    if action == "save_event_settings":
        start_epoch, start_error = datetime_local_to_epoch(request.form.get("start_et", ""))
        end_epoch, end_error = datetime_local_to_epoch(request.form.get("end_et", ""))
        if start_error or end_error or start_epoch is None or end_epoch is None:
            flash(start_error or end_error or "Choose valid Wager Race dates.", "error")
            return _redirect_admin("wager-race-settings")
        if end_epoch <= start_epoch:
            flash("Wager Race end time must be later than the start time.", "error")
            return _redirect_admin("wager-race-settings")

        refresh = _coerce_int(request.form.get("refresh_seconds"), REFRESH_SECONDS)
        if refresh < 15 or refresh > 3600:
            flash("Refresh frequency must be between 15 and 3,600 seconds.", "error")
            return _redirect_admin("wager-race-settings")

        slug = str(request.form.get("kick_channel_slug") or "").strip().lower()
        if not re.fullmatch(r"[a-z0-9_-]{2,50}", slug):
            flash("Kick channel names may use letters, numbers, underscores, and hyphens.", "error")
            return _redirect_admin("wager-race-settings")

        site_name = _trim(request.form.get("site_name"), 60).strip()
        race_title = _trim(request.form.get("race_title"), 100).strip()
        race_description = _trim(request.form.get("race_description"), 240).strip()
        sponsor_name = _trim(request.form.get("sponsor_name"), 60).strip()
        community_name = _trim(request.form.get("community_name"), 60).strip()
        campaign_filter = _trim(request.form.get("campaign_code_filter"), 64).strip()
        if not all((site_name, race_title, sponsor_name)):
            flash("Site name, race title, and sponsor name are required.", "error")
            return _redirect_admin("wager-race-settings")

        urls = {
            "sponsor_url": str(request.form.get("sponsor_url") or "").strip(),
            "stream_url": str(request.form.get("stream_url") or "").strip(),
            "community_url": str(request.form.get("community_url") or "").strip(),
            "responsible_gambling_url": str(request.form.get("responsible_gambling_url") or "").strip(),
        }
        for key, value in urls.items():
            if not _valid_public_url(value, allow_blank=key in {"community_url", "responsible_gambling_url"}):
                flash(f"Enter a valid http or https URL for {key.replace('_', ' ')}.", "error")
                return _redirect_admin("wager-race-settings")

        prizes: Dict[str, float] = {}
        for rank in range(1, 16):
            amount, error = parse_money_strict(str(request.form.get(f"prize_{rank}") or ""))
            if error or amount is None:
                flash(f"Prize #{rank}: {error or 'Enter a valid amount.'}", "error")
                return _redirect_admin("wager-race-settings")
            prizes[str(rank)] = amount

        new_settings = {
            "site_name": site_name,
            "race_title": race_title,
            "race_description": race_description,
            "start_time": start_epoch,
            "end_time": end_epoch,
            "refresh_seconds": refresh,
            "leaderboard_size": 15,
            "prizes": prizes,
            "kick_channel_slug": slug,
            "campaign_code_filter": campaign_filter,
            "sponsor_name": sponsor_name,
            "sponsor_url": urls["sponsor_url"],
            "stream_url": urls["stream_url"] or f"https://kick.com/{slug}",
            "community_name": community_name or "Community",
            "community_url": urls["community_url"],
            "responsible_gambling_url": urls["responsible_gambling_url"],
        }
        with _store_lock:
            old_slug = str((STORE.get("site_settings") or {}).get("kick_channel_slug") or "")
            STORE["site_settings"] = normalize_site_settings(new_settings)
            STORE["updated_at"] = int(time.time())
            store_save(STORE)
            saved = dict(STORE["site_settings"])
        apply_site_settings(saved)
        if old_slug != KICK_CHANNEL_SLUG:
            reset_kick_caches()

        refresh_messages = []
        with _force_refresh_lock:
            try:
                refresh_cache_once(reason="settings_save")
                refresh_messages.append("leaderboard refreshed")
            except Exception as exc:
                app.logger.exception("[SETTINGS] refresh failed: %s", exc)
                refresh_messages.append("leaderboard refresh needs attention")
            try:
                kick_result = refresh_kick_status(force=True)
                refresh_messages.append("Kick checked" if kick_result.get("available") else "Kick needs attention")
            except Exception as exc:
                app.logger.exception("[SETTINGS] Kick check failed: %s", exc)
                refresh_messages.append("Kick needs attention")
        audit("save_event_settings", {"start_time": start_epoch, "end_time": end_epoch, "prize_total": sum(prizes.values())})
        flash(f"Wager Race settings saved successfully; {', '.join(refresh_messages)}.", "success")
        return _redirect_admin("wager-race-settings")

    if action == "test_shuffle":
        rows, meta = fetch_from_shuffle()
        if meta.get("ok"):
            flash(f"Shuffle connection successful. Received {len(rows)} row(s) from {meta.get('source')} in {meta.get('ms')} ms.", "success")
        else:
            flash(f"Shuffle connection failed: {meta.get('error') or 'Unknown error.'}", "error")
        audit("test_shuffle", {"ok": bool(meta.get("ok")), "rows": len(rows)})
        return _redirect_admin("connections")

    if action == "test_kick":
        result = refresh_kick_status(force=True)
        if result.get("available"):
            state = "live" if result.get("live") else "offline"
            flash(f"Kick connection successful. The channel is currently {state}.", "success")
        else:
            with _kick_status_lock:
                error = KICK_HEALTH.get("last_error")
            flash(f"Kick connection failed: {error or 'Unknown error.'}", "error")
        audit("test_kick", {"available": bool(result.get("available")), "live": result.get("live")})
        return _redirect_admin("connections")

    if action == "set_override":
        username = str(request.form.get("username") or "").strip()
        amount_text = str(request.form.get("amount") or "").strip()
        if not username or len(username) > 64:
            flash("Enter a valid username up to 64 characters.", "error")
            return _redirect_admin("leaderboard-management")

        if amount_text == "":
            with _store_lock:
                before = (STORE.get("overrides") or {}).get(username)
                STORE.setdefault("overrides", {}).pop(username, None)
                STORE["updated_at"] = int(time.time())
                store_save(STORE)
            audit("weighted_override_remove", {"username": username, "before": before})
            flash(f"Removed the weighted override for {username}.", "success")
            return _redirect_admin("leaderboard-management")

        amount, error = parse_money_strict(amount_text)
        if error or amount is None:
            flash(error or "Invalid override amount.", "error")
            return _redirect_admin("leaderboard-management")
        with _store_lock:
            before = (STORE.get("overrides") or {}).get(username)
            STORE.setdefault("overrides", {})[username] = amount
            STORE["updated_at"] = int(time.time())
            store_save(STORE)
        audit("weighted_override_set", {"username": username, "before": before, "after": amount})
        flash(f"Set {username}'s weighted override to {money(amount)}.", "success")
        return _redirect_admin("leaderboard-management")


    if action == "force_refresh":
        with _force_refresh_lock:
            refresh_cache_once(reason="force_refresh")
            refresh_kick_status(force=True)
        audit("force_refresh", {})
        flash("Leaderboard and Kick status refreshed.", "success")
        return _redirect_admin("connections")

    if action == "change_own_password":
        username = admin_user() or ""
        current_password = str(request.form.get("current_password") or "")
        new_password = str(request.form.get("new_password") or "")
        confirm_password = str(request.form.get("confirm_password") or "")
        if new_password != confirm_password:
            flash("The new password and confirmation do not match.", "error")
            return _redirect_admin("account-security")
        if not _valid_password(new_password):
            flash(f"Passwords must be {MIN_ADMIN_PASSWORD_LENGTH}–256 characters.", "error")
            return _redirect_admin("account-security")
        with _store_lock:
            record = (STORE.get("users") or {}).get(username)
            if not record or not check_password_hash(str(record.get("pw_hash") or ""), current_password):
                flash("Current password is incorrect.", "error")
                return _redirect_admin("account-security")
            record["pw_hash"] = generate_password_hash(new_password)
            record["updated_at"] = int(time.time())
            STORE["users"][username] = record
            STORE["updated_at"] = int(time.time())
            store_save(STORE)
        session["csrf_token"] = secrets.token_urlsafe(32)
        audit("change_own_password", {"user": username})
        flash("Your password was changed successfully.", "success")
        return _redirect_admin("account-security")

    if action == "restore_backup":
        uploaded = request.files.get("backup_file")
        if not uploaded or not uploaded.filename:
            flash("Choose a JSON backup file to restore.", "error")
            return _redirect_admin("backup-restore")
        try:
            payload = json.loads(uploaded.read().decode("utf-8"))
        except (UnicodeDecodeError, json.JSONDecodeError):
            flash("The selected file is not a valid JSON backup.", "error")
            return _redirect_admin("backup-restore")
        if not isinstance(payload, dict) or _coerce_int(payload.get("backup_version"), 0) != 1:
            flash("This backup format is not supported.", "error")
            return _redirect_admin("backup-restore")

        site = normalize_site_settings(payload.get("site_settings"))
        raw_overrides = payload.get("overrides") if isinstance(payload.get("overrides"), dict) else {}
        clean_overrides = {
            _trim(username, 64).strip(): parse_money_to_float(amount)
            for username, amount in raw_overrides.items()
            if _trim(username, 64).strip()
        }
        raw_snapshots = payload.get("leaderboard_snapshots")
        clean_snapshots = raw_snapshots if isinstance(raw_snapshots, dict) else {}
        if not isinstance(clean_snapshots.get("last_top15"), list):
            clean_snapshots["last_top15"] = []
        if not isinstance(clean_snapshots.get("prev_top15"), list):
            clean_snapshots["prev_top15"] = []
        clean_snapshots["updated_at"] = _coerce_int(clean_snapshots.get("updated_at"), 0) or None

        with _store_lock:
            STORE["site_settings"] = site
            STORE["overrides"] = clean_overrides
            STORE["leaderboard_snapshots"] = clean_snapshots
            STORE["updated_at"] = int(time.time())
            store_save(STORE)
        apply_site_settings(site)
        reset_kick_caches()
        seed_cache_from_store()
        audit("restore_backup", {"overrides": len(clean_overrides)})
        flash("Backup restored. Admin accounts and passwords were left unchanged.", "success")
        return _redirect_admin("backup-restore")

    if action == "ban_ip":
        normalized = _normalized_ip(str(request.form.get("ip") or ""))
        if not normalized:
            flash("Enter a valid IPv4 or IPv6 address.", "error")
            return _redirect_admin("advanced-administration")
        with _store_lock:
            banned = STORE.setdefault("banned_ips", [])
            if normalized not in banned:
                banned.append(normalized)
            STORE["updated_at"] = int(time.time())
            store_save(STORE)
        audit("ban_ip", {"ip": normalized})
        flash(f"Banned {normalized}.", "success")
        return _redirect_admin("advanced-administration")

    if action == "unban_ip":
        normalized = _normalized_ip(str(request.form.get("ip") or ""))
        if normalized:
            with _store_lock:
                STORE["banned_ips"] = [value for value in STORE.get("banned_ips", []) if value != normalized]
                STORE["updated_at"] = int(time.time())
                store_save(STORE)
            audit("unban_ip", {"ip": normalized})
            flash(f"Unbanned {normalized}.", "success")
        return _redirect_admin("advanced-administration")

    if action == "clear_access_log":
        global ACCESS_LOG
        with _access_log_lock:
            ACCESS_LOG = []
        audit("clear_access_log", {})
        flash("Access log cleared.", "success")
        return _redirect_admin("advanced-administration")

    if action == "clear_audit_log":
        if not is_superadmin():
            abort(403)
        with _store_lock:
            STORE["audit_log"] = []
            STORE["updated_at"] = int(time.time())
            store_save(STORE)
        audit("clear_audit_log", {})
        flash("Audit log cleared.", "success")
        return _redirect_admin("advanced-administration")

    if action in {"add_admin", "remove_admin", "set_admin_password"}:
        if not is_superadmin():
            abort(403)

        if action == "add_admin":
            username = str(request.form.get("new_username") or "").strip()
            password = str(request.form.get("new_password") or "")
            password_confirm = str(request.form.get("new_password_confirm") or "")
            if password != password_confirm:
                flash("The temporary password and confirmation do not match.", "error")
                return _redirect_admin("admin-users")
            if not _valid_admin_username(username):
                flash("Admin usernames must be 3–32 letters, numbers, or underscores.", "error")
                return _redirect_admin("admin-users")
            if not _valid_password(password):
                flash(f"Passwords must be {MIN_ADMIN_PASSWORD_LENGTH}–256 characters.", "error")
                return _redirect_admin("admin-users")
            with _store_lock:
                users = STORE.setdefault("users", {})
                if username in users:
                    flash("That admin user already exists.", "error")
                    return _redirect_admin("admin-users")
                users[username] = {
                    "pw_hash": generate_password_hash(password),
                    "created_at": int(time.time()),
                    "created_by": admin_user() or SUPERADMIN,
                }
                STORE["updated_at"] = int(time.time())
                store_save(STORE)
            audit("add_admin_ok", {"username": username})
            flash(f"Added admin user {username}.", "success")
            return _redirect_admin("admin-users")

        if action == "remove_admin":
            username = str(request.form.get("rm_username") or "").strip()
            if not username or username.casefold() == SUPERADMIN.casefold():
                flash("The configured superadmin cannot be removed.", "error")
                return _redirect_admin("admin-users")
            with _store_lock:
                existed = username in (STORE.get("users") or {})
                STORE.setdefault("users", {}).pop(username, None)
                STORE["updated_at"] = int(time.time())
                store_save(STORE)
            audit("remove_admin", {"username": username, "existed": existed})
            flash(f"Removed admin user {username}." if existed else "Admin user was not found.", "success")
            return _redirect_admin("admin-users")

        username = str(request.form.get("pw_username") or "").strip()
        password = str(request.form.get("pw_password") or "")
        password_confirm = str(request.form.get("pw_password_confirm") or "")
        if password != password_confirm:
            flash("The new password and confirmation do not match.", "error")
            return _redirect_admin("admin-users")
        if not username or not _valid_password(password):
            flash(f"Select an existing user and use a {MIN_ADMIN_PASSWORD_LENGTH}–256 character password.", "error")
            return _redirect_admin("admin-users")
        with _store_lock:
            users = STORE.get("users") or {}
            if username not in users:
                flash("That admin user does not exist.", "error")
                return _redirect_admin("admin-users")
            users[username]["pw_hash"] = generate_password_hash(password)
            users[username]["updated_at"] = int(time.time())
            STORE["users"] = users
            STORE["updated_at"] = int(time.time())
            store_save(STORE)
        audit("set_admin_password_ok", {"username": username})
        flash(f"Updated the password for {username}.", "success")
        return _redirect_admin("admin-users")

    flash("Unknown admin action.", "error")
    return redirect(url_for("admin"))


# ---------------------------------------------------------------------------
# Error handlers
# ---------------------------------------------------------------------------


@app.errorhandler(400)
def bad_request(_error):
    return (
        "Bad Request (400)\n\n"
        "The request could not be verified. Return to the previous page, refresh it, and try again.\n",
        400,
        {"Content-Type": "text/plain; charset=utf-8"},
    )


@app.errorhandler(403)
def forbidden(_error):
    return (
        "Forbidden (403)\n\nYou are not authorized to perform this action.\n",
        403,
        {"Content-Type": "text/plain; charset=utf-8"},
    )


@app.errorhandler(404)
def not_found(_error):
    return render_template("404.html", site=public_site_settings()), 404


if __name__ == "__main__":
    app.logger.info("Project directory: %s", BASE_DIR)
    app.logger.info("Settings file: %s", SETTINGS_PATH)
    app.logger.info("Admin store: %s", ADMIN_STORE_PATH)
    app.logger.info("Session cookie secure mode: %s", SESSION_COOKIE_SECURE_MODE)
    app.logger.info("Listening on http://0.0.0.0:%s", PORT)
    app.run(host="0.0.0.0", port=PORT)
