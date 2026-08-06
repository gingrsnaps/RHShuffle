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

import requests
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

SESSION_COOKIE_SECURE = _env_bool(
    "SESSION_COOKIE_SECURE",
    _settings_bool("session_cookie_secure", False),
)
ADMIN_STORE_PATH = _resolve_app_path(os.getenv("ADMIN_STORE_PATH"), "admin_store.json")
ACCESS_LOG_MAX = max(50, _env_int("ACCESS_LOG_MAX", _settings_int("access_log_max", 300)))
AUDIT_LOG_MAX = max(50, _env_int("AUDIT_LOG_MAX", _settings_int("audit_log_max", 250)))
LOGIN_WINDOW_SECONDS = max(60, _env_int("LOGIN_WINDOW_SECONDS", 10 * 60))
LOGIN_MAX_FAILURES = max(2, _env_int("LOGIN_MAX_FAILURES", 5))
LOGIN_LOCK_SECONDS = max(60, _env_int("LOGIN_LOCK_SECONDS", 15 * 60))
MIN_ADMIN_PASSWORD_LENGTH = max(12, _env_int("MIN_ADMIN_PASSWORD_LENGTH", 12))

SUPERADMIN = _env_or_setting("ADMIN_BOOTSTRAP_USER", "admin_bootstrap_user", "admin") or "admin"
BOOTSTRAP_PASS = _env_or_setting("ADMIN_BOOTSTRAP_PASS", "admin_bootstrap_pass", "")
RESET_ADMIN_STORE_ON_START = _env_bool(
    "RESET_ADMIN_STORE_ON_START",
    _settings_bool("reset_admin_store_on_start", False),
)
RESET_BOOTSTRAP_PASSWORD_ON_START = _env_bool(
    "RESET_BOOTSTRAP_PASSWORD_ON_START",
    _settings_bool("reset_bootstrap_password_on_start", False),
)
DISABLE_BACKGROUND_REFRESH = _env_bool("DISABLE_BACKGROUND_REFRESH", False)

PROXY_FIX_X_FOR = max(0, _env_int("PROXY_FIX_X_FOR", _settings_int("proxy_fix_x_for", 1)))
PROXY_FIX_X_PROTO = max(0, _env_int("PROXY_FIX_X_PROTO", _settings_int("proxy_fix_x_proto", 1)))
PROXY_FIX_X_HOST = max(0, _env_int("PROXY_FIX_X_HOST", _settings_int("proxy_fix_x_host", 1)))
PROXY_FIX_X_PORT = max(0, _env_int("PROXY_FIX_X_PORT", _settings_int("proxy_fix_x_port", 1)))
PROXY_FIX_X_PREFIX = max(0, _env_int("PROXY_FIX_X_PREFIX", _settings_int("proxy_fix_x_prefix", 0)))

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
    SESSION_COOKIE_NAME="redhunllef_admin",
    SESSION_COOKIE_HTTPONLY=True,
    SESSION_COOKIE_SAMESITE="Lax",
    SESSION_COOKIE_SECURE=SESSION_COOKIE_SECURE,
    PERMANENT_SESSION_LIFETIME=timedelta(days=7),
    SESSION_REFRESH_EACH_REQUEST=False,
    MAX_CONTENT_LENGTH=1 * 1024 * 1024,
)

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
HTTP.headers.update({"User-Agent": "RedHunllef-WagerRace/3.1"})

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
        users[SUPERADMIN] = {
            "pw_hash": generate_password_hash(BOOTSTRAP_PASS),
            "created_at": now,
            "created_by": "bootstrap",
        }
    return {
        "version": 3,
        "secret_key": secrets.token_hex(32),
        "users": users,
        "overrides": {},
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

    ensure("version", 3)
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
    ensure("audit_log", [])
    ensure("banned_ips", [])
    ensure("health", _default_health())
    ensure("leaderboard_snapshots", {})
    ensure("updated_at", int(time.time()))

    if store.get("version") != 3:
        store["version"] = 3
        dirty = True

    if not isinstance(store.get("users"), dict):
        store["users"] = {}
        dirty = True
    if not isinstance(store.get("overrides"), dict):
        store["overrides"] = {}
        dirty = True
    if not isinstance(store.get("audit_log"), list):
        store["audit_log"] = []
        dirty = True
    if not isinstance(store.get("banned_ips"), list):
        store["banned_ips"] = []
        dirty = True

    users = store["users"]
    if SUPERADMIN not in users and BOOTSTRAP_PASS:
        users[SUPERADMIN] = {
            "pw_hash": generate_password_hash(BOOTSTRAP_PASS),
            "created_at": int(time.time()),
            "created_by": "bootstrap",
        }
        dirty = True
    elif SUPERADMIN in users and BOOTSTRAP_PASS and RESET_BOOTSTRAP_PASSWORD_ON_START:
        users[SUPERADMIN]["pw_hash"] = generate_password_hash(BOOTSTRAP_PASS)
        users[SUPERADMIN]["updated_at"] = int(time.time())
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
    token = session.get("csrf_token")
    if not token:
        token = secrets.token_urlsafe(32)
        session["csrf_token"] = token
    return token


@app.context_processor
def inject_template_helpers() -> Dict[str, Any]:
    return {"csrf_token": csrf_token}


def require_csrf() -> None:
    sent = str(request.form.get("csrf_token") or "").strip()
    expected = str(session.get("csrf_token") or "")
    if not sent or not expected or not secrets.compare_digest(sent, expected):
        abort(400)


def admin_user() -> Optional[str]:
    value = session.get("admin_user")
    return str(value) if value else None


def is_superadmin() -> bool:
    return (admin_user() or "") == SUPERADMIN


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


def _public_payload_from_top(top: List[Dict[str, Any]], *, stale: bool = False) -> Dict[str, Any]:
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
            "updated_at": int(time.time()),
            "label": "Weighted Wager",
            "leaderboard_size": LEADERBOARD_SIZE,
            "stale": stale,
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

    entries = list(by_name.values())
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
        DATA_CACHE.update(_public_payload_from_top(stored_top, stale=True))
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
    output: List[Dict[str, Any]] = []
    for entry in current[:LEADERBOARD_SIZE]:
        username = str(entry.get("username") or "")
        current_value = parse_money_to_float(entry.get("weighted_wager", entry.get("wager")))
        delta = current_value - previous_map.get(username, 0.0)
        enriched = dict(entry)
        enriched["delta"] = delta
        enriched["delta_str"] = (
            "+" + money(delta)
            if delta > 0
            else "-" + money(abs(delta))
            if delta < 0
            else "+$0.00"
        )
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
    return render_template("index.html", leaderboard_size=LEADERBOARD_SIZE)


@app.route("/data")
def data():
    with _cache_lock:
        payload = {
            "podium": list(DATA_CACHE.get("podium") or []),
            "others": list(DATA_CACHE.get("others") or []),
            "meta": dict(DATA_CACHE.get("meta") or {}),
        }
    return jsonify(payload)


@app.route("/config")
def config():
    return jsonify(
        {
            "start_time": START_TIME,
            "end_time": END_TIME,
            "refresh_seconds": REFRESH_SECONDS,
            "leaderboard_size": LEADERBOARD_SIZE,
            "leaderboard_label": "Weighted Wager",
            "weighting_rules": WEIGHTING_RULES,
            "prizes": {str(rank): money(PRIZES.get(rank, 0)) for rank in range(1, LEADERBOARD_SIZE + 1)},
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
    csrf_token()
    if admin_user():
        return render_admin_panel()

    error = None
    if request.method == "POST":
        require_csrf()
        ip = client_ip()
        locked, remaining = login_locked(ip)
        if locked:
            error = f"Too many failed login attempts. Try again in {max(1, math.ceil(remaining / 60))} minute(s)."
            return render_template("admin_login.html", error=error)

        username = str(request.form.get("username") or "").strip()
        password = str(request.form.get("password") or "")
        with _store_lock:
            record = (STORE.get("users") or {}).get(username)

        if not record or not check_password_hash(str(record.get("pw_hash") or ""), password):
            login_record_failure(ip)
            error = "Invalid username or password."
            app.logger.warning("[LOGIN_FAIL] ip=%s user=%s", ip, username)
        else:
            login_record_success(ip)
            session.clear()
            session.permanent = True
            session["admin_user"] = username
            session["csrf_token"] = secrets.token_urlsafe(32)
            audit("login_ok", {"user": username})
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


def render_admin_panel():
    csrf_token()
    with _store_lock:
        overrides = dict(STORE.get("overrides") or {})
        audit_log = list(reversed(STORE.get("audit_log") or []))
        banned_ips = list(STORE.get("banned_ips") or [])
        health = dict(STORE.get("health") or {})
        admin_users = sorted((STORE.get("users") or {}).keys())
    with _access_log_lock:
        access_log = list(reversed(ACCESS_LOG))
    with _admin_cache_lock:
        top = list(ADMIN_CACHE.get("top") or [])
        full = list(ADMIN_CACHE.get("full") or [])
        last_refresh = int(ADMIN_CACHE.get("last_refresh") or 0)
    with _kick_status_lock:
        kick_health = dict(KICK_HEALTH)

    next_refresh = last_refresh + REFRESH_SECONDS if last_refresh else 0
    return render_template(
        "admin_panel.html",
        admin_user=admin_user(),
        is_superadmin=is_superadmin(),
        superadmin_user=SUPERADMIN,
        refresh_seconds=REFRESH_SECONDS,
        leaderboard_size=LEADERBOARD_SIZE,
        start_et=fmt_et(START_TIME),
        end_et=fmt_et(END_TIME),
        last_refresh_et=fmt_et(last_refresh),
        next_refresh_et=fmt_et(next_refresh),
        endpoint_kind=SHUFFLE_ENDPOINT_KIND,
        aggregation_mode=SHUFFLE_AGGREGATION_MODE,
        campaign_code_filter=CAMPAIGN_CODE_FILTER or "—",
        weighting_rules=WEIGHTING_RULES,
        prizes={rank: money(PRIZES.get(rank, 0)) for rank in range(1, LEADERBOARD_SIZE + 1)},
        overrides=overrides,
        top=top,
        top_with_deltas=compute_top_deltas(),
        full_leaderboard=full,
        access_log=access_log,
        audit_log=audit_log,
        banned_ips=banned_ips,
        health=health,
        kick_health=kick_health,
        admin_users=admin_users,
        min_password_length=MIN_ADMIN_PASSWORD_LENGTH,
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
            "source",
            "row_count",
            "last_refresh_et",
        ]
    )
    for row in rows:
        writer.writerow(
            [
                row.get("rank"),
                row.get("username"),
                f"{parse_money_to_float(row.get('weighted_wager')):.2f}",
                "" if row.get("raw_wager") is None else f"{parse_money_to_float(row.get('raw_wager')):.2f}",
                row.get("source", ""),
                row.get("row_count", 1),
                fmt_et(last_refresh),
            ]
        )
    audit("export_csv", {"rows": len(rows)})
    return Response(
        output.getvalue(),
        mimetype="text/csv",
        headers={"Content-Disposition": "attachment; filename=weighted_leaderboard_export.csv"},
    )


@app.route("/admin/action", methods=["POST"])
@login_required
def admin_action():
    require_csrf()
    action = str(request.form.get("action") or "").strip()

    if action == "set_override":
        username = str(request.form.get("username") or "").strip()
        amount_text = str(request.form.get("amount") or "").strip()
        if not username or len(username) > 64:
            flash("Enter a valid username up to 64 characters.", "error")
            return redirect(url_for("admin"))

        if amount_text == "":
            with _store_lock:
                before = (STORE.get("overrides") or {}).get(username)
                STORE.setdefault("overrides", {}).pop(username, None)
                STORE["updated_at"] = int(time.time())
                store_save(STORE)
            audit("weighted_override_remove", {"username": username, "before": before})
            flash(f"Removed the weighted override for {username}.", "success")
            return redirect(url_for("admin"))

        amount, error = parse_money_strict(amount_text)
        if error or amount is None:
            flash(error or "Invalid override amount.", "error")
            return redirect(url_for("admin"))
        with _store_lock:
            before = (STORE.get("overrides") or {}).get(username)
            STORE.setdefault("overrides", {})[username] = amount
            STORE["updated_at"] = int(time.time())
            store_save(STORE)
        audit(
            "weighted_override_set",
            {"username": username, "before": before, "after": amount},
        )
        flash(f"Set {username}'s weighted override to {money(amount)}.", "success")
        return redirect(url_for("admin"))

    if action == "force_refresh":
        with _force_refresh_lock:
            refresh_cache_once(reason="force_refresh")
            refresh_kick_status(force=True)
        audit("force_refresh", {})
        flash("Leaderboard and Kick status refreshed.", "success")
        return redirect(url_for("admin"))

    if action == "ban_ip":
        normalized = _normalized_ip(str(request.form.get("ip") or ""))
        if not normalized:
            flash("Enter a valid IPv4 or IPv6 address.", "error")
            return redirect(url_for("admin"))
        with _store_lock:
            banned = STORE.setdefault("banned_ips", [])
            if normalized not in banned:
                banned.append(normalized)
            STORE["updated_at"] = int(time.time())
            store_save(STORE)
        audit("ban_ip", {"ip": normalized})
        flash(f"Banned {normalized}.", "success")
        return redirect(url_for("admin"))

    if action == "unban_ip":
        normalized = _normalized_ip(str(request.form.get("ip") or ""))
        if normalized:
            with _store_lock:
                STORE["banned_ips"] = [
                    value for value in STORE.get("banned_ips", []) if value != normalized
                ]
                STORE["updated_at"] = int(time.time())
                store_save(STORE)
            audit("unban_ip", {"ip": normalized})
            flash(f"Unbanned {normalized}.", "success")
        return redirect(url_for("admin"))

    if action == "clear_access_log":
        global ACCESS_LOG
        with _access_log_lock:
            ACCESS_LOG = []
        audit("clear_access_log", {})
        flash("Access log cleared.", "success")
        return redirect(url_for("admin"))

    if action == "clear_audit_log":
        if not is_superadmin():
            abort(403)
        with _store_lock:
            STORE["audit_log"] = []
            STORE["updated_at"] = int(time.time())
            store_save(STORE)
        audit("clear_audit_log", {})
        flash("Audit log cleared.", "success")
        return redirect(url_for("admin"))

    if action in {"add_admin", "remove_admin", "set_admin_password"}:
        if not is_superadmin():
            abort(403)

        if action == "add_admin":
            username = str(request.form.get("new_username") or "").strip()
            password = str(request.form.get("new_password") or "")
            if not _valid_admin_username(username):
                flash("Admin usernames must be 3–32 letters, numbers, or underscores.", "error")
                return redirect(url_for("admin"))
            if not _valid_password(password):
                flash(f"Passwords must be {MIN_ADMIN_PASSWORD_LENGTH}–256 characters.", "error")
                return redirect(url_for("admin"))
            with _store_lock:
                users = STORE.setdefault("users", {})
                if username in users:
                    flash("That admin user already exists.", "error")
                    return redirect(url_for("admin"))
                users[username] = {
                    "pw_hash": generate_password_hash(password),
                    "created_at": int(time.time()),
                    "created_by": admin_user() or SUPERADMIN,
                }
                STORE["updated_at"] = int(time.time())
                store_save(STORE)
            audit("add_admin_ok", {"username": username})
            flash(f"Added admin user {username}.", "success")
            return redirect(url_for("admin"))

        if action == "remove_admin":
            username = str(request.form.get("rm_username") or "").strip()
            if not username or username == SUPERADMIN:
                flash("The configured superadmin cannot be removed.", "error")
                return redirect(url_for("admin"))
            with _store_lock:
                existed = username in (STORE.get("users") or {})
                STORE.setdefault("users", {}).pop(username, None)
                STORE["updated_at"] = int(time.time())
                store_save(STORE)
            audit("remove_admin", {"username": username, "existed": existed})
            flash(f"Removed admin user {username}." if existed else "Admin user was not found.", "success")
            return redirect(url_for("admin"))

        username = str(request.form.get("pw_username") or "").strip()
        password = str(request.form.get("pw_password") or "")
        if not username or not _valid_password(password):
            flash(f"Select an existing user and use a {MIN_ADMIN_PASSWORD_LENGTH}–256 character password.", "error")
            return redirect(url_for("admin"))
        with _store_lock:
            users = STORE.get("users") or {}
            if username not in users:
                flash("That admin user does not exist.", "error")
                return redirect(url_for("admin"))
            users[username]["pw_hash"] = generate_password_hash(password)
            users[username]["updated_at"] = int(time.time())
            STORE["users"] = users
            STORE["updated_at"] = int(time.time())
            store_save(STORE)
        audit("set_admin_password_ok", {"username": username})
        flash(f"Updated the password for {username}.", "success")
        return redirect(url_for("admin"))

    flash("Unknown admin action.", "error")
    return redirect(url_for("admin"))


# ---------------------------------------------------------------------------
# Error handlers
# ---------------------------------------------------------------------------


@app.errorhandler(400)
def bad_request(_error):
    return (
        "Bad Request (400)\n\n"
        "The request was rejected. Refresh the page and try again. "
        "For local HTTP testing, set SESSION_COOKIE_SECURE=0.\n",
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
    return render_template("404.html"), 404


if __name__ == "__main__":
    app.logger.info("Project directory: %s", BASE_DIR)
    app.logger.info("Settings file: %s", SETTINGS_PATH)
    app.logger.info("Admin store: %s", ADMIN_STORE_PATH)
    app.logger.info("Listening on http://0.0.0.0:%s", PORT)
    app.run(host="0.0.0.0", port=PORT)
