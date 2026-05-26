# -*- coding: utf-8 -*-
"""
Weighted wager race backend.

Major changes from the previous version:
- Uses Shuffle's weighted wager endpoint instead of the old stats endpoint.
- Ranks users by weightedWagerAmount, not raw wagerAmount.
- Keeps raw wager amount only as admin/audit context when the API provides it.
- Aggregates duplicate rows by username using a configurable mode. Default is sum.
- Removes broad CORS because the frontend is served by the same Flask app.
- Stops writing admin_store.json on every public request.
- Adds login rate limiting, a health endpoint, and CSV export for payout review.

Important deployment note:
Do not commit real Shuffle/Kick/admin secrets. Put them in environment variables.
"""
from __future__ import annotations

import csv
import io
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
from typing import Any, Dict, Iterable, List, Optional, Tuple

import requests
from flask import Flask, abort, jsonify, redirect, render_template, request, session, url_for, g, Response
from werkzeug.middleware.proxy_fix import ProxyFix
from werkzeug.security import check_password_hash, generate_password_hash

# -------------------------
# Settings loader
# -------------------------

SETTINGS_PATH = os.getenv("SETTINGS_PATH", "settings.json")


def load_settings() -> Dict[str, Any]:
    """Load settings.json if it exists. Environment variables still win later."""
    try:
        with open(SETTINGS_PATH, "r", encoding="utf-8") as f:
            data = json.load(f)
        return data if isinstance(data, dict) else {}
    except FileNotFoundError:
        return {}
    except Exception:
        # Keep startup resilient if settings.json is malformed, but log once after app exists.
        return {}


SETTINGS = load_settings()

# -------------------------
# Timezone helpers
# -------------------------
try:
    from zoneinfo import ZoneInfo
    ET = ZoneInfo("America/New_York")
except Exception:
    ET = None


def fmt_et(epoch: int) -> str:
    """Format epoch seconds in Eastern Time. Falls back to UTC if zoneinfo is unavailable."""
    if not epoch:
        return "—"
    try:
        if ET:
            dt = datetime.fromtimestamp(int(epoch), tz=ET)
            return dt.strftime("%b %d, %Y %I:%M:%S %p %Z")
        dt = datetime.utcfromtimestamp(int(epoch))
        return dt.strftime("%b %d, %Y %I:%M:%S %p UTC")
    except Exception:
        return "—"


# -------------------------
# Config helpers
# -------------------------

def _env_str(name: str, default: str = "") -> str:
    val = os.getenv(name)
    if val is None:
        return str(default or "")
    return val.strip()


def _settings_str(name: str, default: str = "") -> str:
    val = SETTINGS.get(name, default)
    return str(val or "").strip()


def _env_or_setting(env_name: str, setting_name: str, default: str = "") -> str:
    return _env_str(env_name) or _settings_str(setting_name, default)


def _env_int(name: str, default: int) -> int:
    val = os.getenv(name, "").strip()
    if val == "":
        return int(default)
    try:
        return int(val)
    except Exception:
        return int(default)


def _env_bool(name: str, default: bool) -> bool:
    v = os.getenv(name, "").strip().lower()
    if v == "":
        return bool(default)
    return v in ("1", "true", "yes", "on")


def _settings_bool(name: str, default: bool) -> bool:
    val = SETTINGS.get(name, default)
    if isinstance(val, bool):
        return val
    return str(val).strip().lower() in ("1", "true", "yes", "on")


PORT = _env_int("PORT", int(SETTINGS.get("port", 8080)))
REFRESH_SECONDS = _env_int("REFRESH_SECONDS", int(SETTINGS.get("refresh_seconds", 60)))

START_TIME = _env_int("START_TIME", int(SETTINGS.get("start_time", 0)))
END_TIME = _env_int("END_TIME", int(SETTINGS.get("end_time", 0)))

# Prefer SHUFFLE_API_KEY, but keep API_KEY for backward compatibility with your old deployment.
API_KEY = _env_str("SHUFFLE_API_KEY") or _env_str("API_KEY") or _settings_str("shuffle_api_key")

# Weighted endpoint by default. Keep this configurable so you can test if Shuffle changes naming.
SHUFFLE_ENDPOINT_KIND = (_env_or_setting("SHUFFLE_ENDPOINT_KIND", "shuffle_endpoint_kind", "wager") or "wager").strip("/")

# Duplicate username handling:
# - sum: safest when the endpoint returns multiple game/transaction rows per user.
# - max: use only if Shuffle returns repeated aggregate rows and sum would double-count.
SHUFFLE_AGGREGATION_MODE = (_env_or_setting("SHUFFLE_AGGREGATION_MODE", "shuffle_aggregation_mode", "sum") or "sum").lower()
if SHUFFLE_AGGREGATION_MODE not in {"sum", "max"}:
    SHUFFLE_AGGREGATION_MODE = "sum"

# A hard guard against silently reverting to raw wager values.
ALLOW_RAW_WAGER_FALLBACK = _env_bool(
    "ALLOW_RAW_WAGER_FALLBACK",
    _settings_bool("allow_raw_wager_fallback", False),
)

# If set, only include matching campaign/referral rows when the API exposes a campaign field.
# If the API does not expose a campaign field, rows are included because the endpoint/key may already scope data.
CAMPAIGN_CODE_FILTER = _env_or_setting("CAMPAIGN_CODE_FILTER", "campaign_code_filter", "Red")

KICK_CHANNEL_SLUG = _env_or_setting("KICK_CHANNEL_SLUG", "kick_channel_slug", "redhunllef")
KICK_CLIENT_ID = _env_or_setting("KICK_CLIENT_ID", "kick_client_id", "")
KICK_CLIENT_SECRET = _env_or_setting("KICK_CLIENT_SECRET", "kick_client_secret", "")

SESSION_COOKIE_SECURE = _env_bool(
    "SESSION_COOKIE_SECURE",
    _settings_bool("session_cookie_secure", False),
)

ADMIN_STORE_PATH = os.getenv("ADMIN_STORE_PATH", "admin_store.json")

ACCESS_LOG_MAX = _env_int("ACCESS_LOG_MAX", 300)
AUDIT_LOG_MAX = _env_int("AUDIT_LOG_MAX", 250)
FULL_LEADERBOARD_MAX = _env_int("FULL_LEADERBOARD_MAX", 300)

LOGIN_WINDOW_SECONDS = _env_int("LOGIN_WINDOW_SECONDS", 10 * 60)
LOGIN_MAX_FAILURES = _env_int("LOGIN_MAX_FAILURES", 5)
LOGIN_LOCK_SECONDS = _env_int("LOGIN_LOCK_SECONDS", 15 * 60)

# Admin bootstrap user is now configurable instead of hard-coded.
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

# -------------------------
# Flask app
# -------------------------

app = Flask(__name__)
app.url_map.strict_slashes = False

# Correctly honors HTTPS/proxy headers when deployed behind DigitalOcean/Cloudflare.
app.wsgi_app = ProxyFix(app.wsgi_app, x_for=1, x_proto=1, x_host=1)

app.config.update(
    SESSION_COOKIE_HTTPONLY=True,
    SESSION_COOKIE_SAMESITE="Lax",
    SESSION_COOKIE_SECURE=SESSION_COOKIE_SECURE,
    PERMANENT_SESSION_LIFETIME=timedelta(days=7),
)

logging.basicConfig(level=logging.INFO)
app.logger.setLevel(logging.INFO)

_store_lock = threading.RLock()
_access_log_lock = threading.RLock()
_login_lock = threading.RLock()

# Persistent admin/security store.
STORE: Dict[str, Any] = {}

# Access log is intentionally in memory only. Public /data polling should not hammer disk writes.
ACCESS_LOG: List[dict] = []

# Per-IP login failure tracker for basic brute-force protection.
LOGIN_FAILURES: Dict[str, Dict[str, Any]] = {}

# -------------------------
# Store helpers
# -------------------------


def store_default() -> Dict[str, Any]:
    """Default persistent admin store. Does not seed fake leaderboard data."""
    now = int(time.time())
    users: Dict[str, Any] = {}

    if BOOTSTRAP_PASS:
        users[SUPERADMIN] = {
            "pw_hash": generate_password_hash(BOOTSTRAP_PASS),
            "created_at": now,
            "created_by": "bootstrap",
        }

    return {
        "version": 2,
        "secret_key": secrets.token_hex(32),
        "users": users,
        # Overrides are weighted-wager overrides, not raw wager overrides.
        "overrides": {},
        "audit_log": [],
        "banned_ips": [],
        "health": {
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
        },
        "leaderboard_snapshots": {
            "prev_top11": [],
            "last_top11": [],
            "updated_at": None,
        },
        "updated_at": now,
    }


def store_save(store: Dict[str, Any]) -> None:
    """Atomic write to admin_store.json."""
    tmp = ADMIN_STORE_PATH + ".tmp"
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(store, f, indent=2)
    os.replace(tmp, ADMIN_STORE_PATH)


def store_load_from_disk() -> Dict[str, Any]:
    """Load the persistent admin store or create a default one."""
    if RESET_ADMIN_STORE_ON_START:
        s = store_default()
        if not s.get("users"):
            raise RuntimeError(
                "RESET_ADMIN_STORE_ON_START is enabled, but no ADMIN_BOOTSTRAP_PASS was provided. "
                "Set ADMIN_BOOTSTRAP_PASS before resetting the admin store."
            )
        store_save(s)
        return s

    if not os.path.exists(ADMIN_STORE_PATH):
        s = store_default()
        if not s.get("users"):
            raise RuntimeError(
                "No admin_store.json exists and no ADMIN_BOOTSTRAP_PASS was provided. "
                "Set ADMIN_BOOTSTRAP_USER and ADMIN_BOOTSTRAP_PASS once, start the app, then log in."
            )
        store_save(s)
        return s

    try:
        with open(ADMIN_STORE_PATH, "r", encoding="utf-8") as f:
            s = json.load(f)
        if not isinstance(s, dict):
            raise ValueError("admin_store root is not a dict")
        return s
    except Exception:
        s = store_default()
        if not s.get("users"):
            raise RuntimeError(
                "admin_store.json exists but could not be read, and no ADMIN_BOOTSTRAP_PASS was provided. "
                "Fix the store file or set ADMIN_BOOTSTRAP_PASS to recreate it."
            )
        store_save(s)
        return s


def store_ensure_keys(s: Dict[str, Any]) -> Tuple[Dict[str, Any], bool]:
    """Ensure required keys exist without deleting unknown keys."""
    dirty = False

    def sd(k: str, v: Any) -> None:
        nonlocal dirty
        if k not in s:
            s[k] = v
            dirty = True

    sd("version", 2)
    sd("secret_key", secrets.token_hex(32))
    sd("users", {})
    sd("overrides", {})
    sd("audit_log", [])
    sd("banned_ips", [])
    sd("health", {})
    sd("leaderboard_snapshots", {})
    sd("updated_at", int(time.time()))

    if not isinstance(s.get("users"), dict):
        s["users"] = {}
        dirty = True

    # Only create the bootstrap user if needed and if a password is explicitly provided.
    # The previous version reset the superadmin password every startup. This avoids surprise lockouts.
    users = s["users"]
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

    h = s.get("health")
    if not isinstance(h, dict):
        s["health"] = {}
        h = s["health"]
        dirty = True

    for hk, hv in {
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
    }.items():
        if hk not in h:
            h[hk] = hv
            dirty = True

    snaps = s.get("leaderboard_snapshots")
    if not isinstance(snaps, dict):
        s["leaderboard_snapshots"] = {}
        snaps = s["leaderboard_snapshots"]
        dirty = True

    for sk, sv in {"prev_top11": [], "last_top11": [], "updated_at": None}.items():
        if sk not in snaps:
            snaps[sk] = sv
            dirty = True

    return s, dirty


def store_init() -> None:
    """Initialize persistent store and Flask session secret."""
    global STORE
    s = store_load_from_disk()
    s, dirty = store_ensure_keys(s)
    STORE = s
    if dirty:
        store_save(STORE)


store_init()

# SECRET_KEY priority: env > settings > persistent store.
env_secret = _env_str("SECRET_KEY")
settings_secret = _settings_str("secret_key")
if settings_secret.upper().startswith("REPLACE_") or len(settings_secret) < 16:
    settings_secret = ""
app.secret_key = env_secret or settings_secret or str(STORE.get("secret_key") or secrets.token_hex(32))

# -------------------------
# Formatting, parsing, and auth helpers
# -------------------------


def censor_username(u: str) -> str:
    """Public anonymity rule: first 2 chars + ******."""
    u = (u or "").strip()
    return (u[:2] if u else "") + ("*" * 6)


def money(amount: float) -> str:
    """Format a float as $1,234.56."""
    try:
        val = float(amount or 0)
    except Exception:
        val = 0.0
    return f"${val:,.2f}"


def parse_money_to_float(s: Any) -> float:
    """Parse '$25,000.00' or 25000 into a non-negative float."""
    if isinstance(s, (int, float)):
        try:
            val = float(s)
            return val if math.isfinite(val) and val >= 0 else 0.0
        except Exception:
            return 0.0

    raw = str(s or "").strip()
    if not raw:
        return 0.0

    tmp = raw.replace(",", "").replace("$", "").replace(" ", "")
    tmp = re.sub(r"[^0-9.]", "", tmp)

    if tmp.count(".") > 1:
        first, rest = tmp.split(".", 1)
        tmp = first + "." + rest.replace(".", "")

    if not tmp or tmp == ".":
        return 0.0

    try:
        val = float(tmp)
    except Exception:
        return 0.0

    return val if math.isfinite(val) and val >= 0 else 0.0


def csrf_token() -> str:
    tok = session.get("csrf_token")
    if not tok:
        tok = secrets.token_urlsafe(32)
        session["csrf_token"] = tok
    return tok


def require_csrf() -> None:
    sent = (request.form.get("csrf_token") or "").strip()
    if not sent or sent != session.get("csrf_token"):
        abort(400)


def admin_user() -> Optional[str]:
    return session.get("admin_user")


def is_superadmin() -> bool:
    return (admin_user() or "") == SUPERADMIN


def login_required(fn):
    @wraps(fn)
    def wrapper(*args, **kwargs):
        if not admin_user():
            return redirect(url_for("admin"))
        return fn(*args, **kwargs)
    return wrapper


def client_ip() -> str:
    return (request.remote_addr or "unknown").strip() or "unknown"


def _ua_trim(ua: str, n: int = 160) -> str:
    ua = str(ua or "")
    return ua if len(ua) <= n else ua[: n - 1] + "…"


# -------------------------
# Login rate limiting
# -------------------------


def login_locked(ip: str) -> Tuple[bool, int]:
    """Return whether an IP is temporarily locked out from login attempts."""
    now = int(time.time())
    with _login_lock:
        rec = LOGIN_FAILURES.get(ip) or {"failures": [], "locked_until": 0}
        locked_until = int(rec.get("locked_until") or 0)
        if locked_until > now:
            return True, locked_until - now
        return False, 0


def login_record_failure(ip: str) -> None:
    """Record failed login and lock IP if too many recent failures occur."""
    now = int(time.time())
    with _login_lock:
        rec = LOGIN_FAILURES.setdefault(ip, {"failures": [], "locked_until": 0})
        failures = [t for t in rec.get("failures", []) if now - int(t) <= LOGIN_WINDOW_SECONDS]
        failures.append(now)
        rec["failures"] = failures
        if len(failures) >= LOGIN_MAX_FAILURES:
            rec["locked_until"] = now + LOGIN_LOCK_SECONDS
            app.logger.warning(f"[LOGIN_LOCK] ip={ip} seconds={LOGIN_LOCK_SECONDS}")


def login_record_success(ip: str) -> None:
    """Clear login failures after a successful login."""
    with _login_lock:
        LOGIN_FAILURES.pop(ip, None)


# -------------------------
# Observability
# -------------------------


def _append_rolling(lst: List[dict], entry: dict, max_len: int) -> List[dict]:
    lst.append(entry)
    if len(lst) > max_len:
        lst = lst[-max_len:]
    return lst


def audit(action: str, detail: Dict[str, Any]) -> None:
    """Persist admin/security audit events. This is intentionally disk-backed."""
    with _store_lock:
        entry = {
            "ts": int(time.time()),
            "ts_et": fmt_et(int(time.time())),
            "admin_user": admin_user() or "unknown",
            "ip": client_ip(),
            "action": action,
            "detail": detail,
        }
        STORE["audit_log"] = _append_rolling(STORE.get("audit_log") or [], entry, AUDIT_LOG_MAX)
        STORE["updated_at"] = int(time.time())
        store_save(STORE)

    app.logger.info(f"[AUDIT] user={entry['admin_user']} ip={entry['ip']} action={action} detail={detail}")


@app.before_request
def obs_before_request():
    """Start request timer and enforce banned IPs globally."""
    g._t0 = time.time()

    if request.path.startswith("/static/"):
        return

    ip = client_ip()
    with _store_lock:
        banned = set(STORE.get("banned_ips") or [])
    if ip in banned:
        app.logger.warning(f"[BAN] blocked ip={ip} path={request.path}")
        abort(403)


@app.after_request
def obs_after_request(resp):
    """Record access logs in memory only. No disk write per request."""
    if request.path.startswith("/static/"):
        return resp

    t0 = getattr(g, "_t0", None)
    ms = int((time.time() - t0) * 1000) if t0 else None

    entry = {
        "ts": int(time.time()),
        "ts_et": fmt_et(int(time.time())),
        "ip": client_ip(),
        "method": request.method,
        "path": request.path,
        "status": int(getattr(resp, "status_code", 0) or 0),
        "ms": ms,
        "ua": _ua_trim(request.headers.get("User-Agent", ""), 160),
    }

    app.logger.info(f"[ACCESS] {entry['ip']} {entry['method']} {entry['path']} -> {entry['status']} ({entry['ms']}ms)")

    with _access_log_lock:
        global ACCESS_LOG
        ACCESS_LOG = _append_rolling(ACCESS_LOG, entry, ACCESS_LOG_MAX)

    return resp


# -------------------------
# Shuffle weighted fetch + cache
# -------------------------

URL_RANGE = "https://affiliate.shuffle.com/{kind}/{api_key}?startTime={start}&endTime={end}"
URL_LIFE = "https://affiliate.shuffle.com/{kind}/{api_key}"

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
    """Ensure end <= now and start < end. If invalid, fall back to the last 14 days."""
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
    """
    Extract row dictionaries from common API response shapes.

    Supports:
    - [ {...}, {...} ]
    - { "data": [ ... ] }
    - { "results": [ ... ] }
    - { "leaderboard": [ ... ] }
    - { "users": [ ... ] }
    """
    if isinstance(payload, list):
        return [x for x in payload if isinstance(x, dict)]

    if isinstance(payload, dict):
        for key in ("data", "results", "leaderboard", "users", "items"):
            val = payload.get(key)
            if isinstance(val, list):
                return [x for x in val if isinstance(x, dict)]

    return []


def _first_present(row: dict, keys: Iterable[str]) -> Any:
    for key in keys:
        if key in row:
            return row.get(key)
    return None


def _row_campaign(row: dict) -> Optional[str]:
    val = _first_present(row, CAMPAIGN_KEYS)
    if val is None:
        return None
    return str(val).strip()


def _campaign_allowed(row: dict) -> bool:
    """
    Apply campaign filter only if the row actually has a campaign-like field.
    If not present, include the row because the endpoint/key may already be scoped.
    """
    wanted = (CAMPAIGN_CODE_FILTER or "").strip()
    if not wanted:
        return True
    campaign = _row_campaign(row)
    if campaign is None:
        return True
    return campaign.lower() == wanted.lower()


def normalize_weighted_row(row: dict) -> Tuple[Optional[dict], Optional[str]]:
    """
    Convert one Shuffle API row into the internal shape used by the app.

    Returns (normalized_row, skip_reason). A row is skipped if it has no username or no
    weighted wager amount. Raw wager fallback is disabled by default on purpose.
    """
    username = str(_first_present(row, USERNAME_KEYS) or "").strip()
    if not username:
        return None, "missing_username"

    if not _campaign_allowed(row):
        return None, "campaign_filtered"

    weighted_raw = _first_present(row, WEIGHTED_KEYS)
    raw_wager_raw = _first_present(row, RAW_WAGER_KEYS)

    weighted = parse_money_to_float(weighted_raw)
    raw_wager = parse_money_to_float(raw_wager_raw)

    has_weighted_key = weighted_raw is not None
    if not has_weighted_key:
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
    """
    Fetch weighted wager rows from Shuffle.

    Returns:
      (rows, meta)

    meta intentionally never includes the API key.
    """
    if not API_KEY:
        return [], {
            "ok": False,
            "ms": None,
            "error": "Missing SHUFFLE_API_KEY/API_KEY.",
            "source": "none",
            "row_count": 0,
        }

    headers = {"User-Agent": "Shuffle-Weighted-WagerRace/AdminPanel"}
    start, end = sanitize_window()

    t0 = time.perf_counter()
    try:
        range_url = URL_RANGE.format(kind=SHUFFLE_ENDPOINT_KIND, api_key=API_KEY, start=start, end=end)
        r = requests.get(range_url, timeout=20, headers=headers)
        ms = int((time.perf_counter() - t0) * 1000)

        # Some Shuffle endpoints may not accept start/end. If so, use the lifetime/current endpoint.
        if r.status_code == 400:
            t1 = time.perf_counter()
            life_url = URL_LIFE.format(kind=SHUFFLE_ENDPOINT_KIND, api_key=API_KEY)
            r2 = requests.get(life_url, timeout=20, headers=headers)
            ms2 = int((time.perf_counter() - t1) * 1000)
            r2.raise_for_status()
            rows = _extract_rows(r2.json())
            return rows, {
                "ok": True,
                "ms": ms2,
                "error": None,
                "source": "weighted_lifetime",
                "row_count": len(rows),
            }

        r.raise_for_status()
        rows = _extract_rows(r.json())
        return rows, {
            "ok": True,
            "ms": ms,
            "error": None,
            "source": "weighted_range",
            "row_count": len(rows),
        }

    except Exception as e:
        ms = int((time.perf_counter() - t0) * 1000)
        return [], {
            "ok": False,
            "ms": ms,
            "error": str(e),
            "source": "none",
            "row_count": 0,
        }


def aggregate_by_username(entries: List[dict]) -> Dict[str, dict]:
    """
    Aggregate normalized rows by username.

    Default mode is sum, because weighted wager endpoints often return more granular data.
    Switch SHUFFLE_AGGREGATION_MODE=max only if you confirm the endpoint returns duplicate
    aggregate rows that would otherwise double-count.
    """
    out: Dict[str, dict] = {}

    for e in entries or []:
        name = str(e.get("username", "")).strip()
        if not name:
            continue

        weighted = parse_money_to_float(e.get("weightedWagerAmount"))
        raw = e.get("wagerAmount")
        raw_val = parse_money_to_float(raw) if raw is not None else None

        prev = out.get(name)
        if prev is None:
            out[name] = {
                "username": name,
                "weightedWagerAmount": weighted,
                "wagerAmount": raw_val,
                "campaignCode": e.get("campaignCode"),
                "source": e.get("source", "shuffle"),
                "row_count": 1,
            }
            continue

        prev["row_count"] = int(prev.get("row_count") or 0) + 1

        if SHUFFLE_AGGREGATION_MODE == "max":
            if weighted > parse_money_to_float(prev.get("weightedWagerAmount")):
                prev["weightedWagerAmount"] = weighted
            if raw_val is not None:
                old_raw = prev.get("wagerAmount")
                prev["wagerAmount"] = max(parse_money_to_float(old_raw), raw_val) if old_raw is not None else raw_val
        else:
            prev["weightedWagerAmount"] = parse_money_to_float(prev.get("weightedWagerAmount")) + weighted
            if raw_val is not None:
                old_raw = prev.get("wagerAmount")
                prev["wagerAmount"] = (parse_money_to_float(old_raw) if old_raw is not None else 0.0) + raw_val

    return out


_cache_lock = threading.Lock()
_admin_cache_lock = threading.Lock()
_force_refresh_lock = threading.Lock()

# Public cache returned by /data. Keep key name "wager" so old frontend shape still works.
DATA_CACHE: Dict[str, Any] = {"podium": [], "others": [], "meta": {}}

# Admin cache keeps full usernames and optional raw wager values.
ADMIN_CACHE: Dict[str, Any] = {
    "top11": [],
    "full": [],
    "last_refresh": 0,
}


def compute_top11_deltas() -> List[Dict[str, Any]]:
    """Compute Top-11 weighted deltas compared with the previous refresh tick."""
    with _store_lock:
        snaps = STORE.get("leaderboard_snapshots") or {}
        last_top = snaps.get("last_top11") or []
        prev_top = snaps.get("prev_top11") or []

    prev_map: Dict[str, float] = {}
    for e in prev_top:
        u = str(e.get("username", "")).strip()
        prev_map[u] = parse_money_to_float(e.get("weighted_wager", e.get("wager")))

    enriched: List[Dict[str, Any]] = []
    for e in last_top:
        u = str(e.get("username", "")).strip()
        cur = parse_money_to_float(e.get("weighted_wager", e.get("wager")))
        prev = prev_map.get(u, 0.0)
        d = cur - prev

        out = dict(e)
        out["delta"] = d
        if d > 0:
            out["delta_str"] = "+" + money(abs(d))
        elif d < 0:
            out["delta_str"] = "-" + money(abs(d))
        else:
            out["delta_str"] = "+$0.00"
        enriched.append(out)

    return enriched


def build_snapshots() -> Tuple[Dict[str, Any], List[Dict[str, Any]], List[Dict[str, Any]], Dict[str, Any]]:
    """
    Build public and admin leaderboard snapshots from weighted wager data.

    Public:
      - masked usernames
      - weighted wager display only

    Admin:
      - full usernames
      - weighted wager
      - raw wager, if the API provides it
    """
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

    # Apply admin overrides as weighted wager totals.
    with _store_lock:
        overrides = dict(STORE.get("overrides") or {})

    for uname, amt in overrides.items():
        u = str(uname).strip()
        if not u:
            continue
        weighted_override = parse_money_to_float(amt)
        by_name[u] = {
            "username": u,
            "weightedWagerAmount": weighted_override,
            "wagerAmount": None,
            "campaignCode": CAMPAIGN_CODE_FILTER or None,
            "source": "override",
            "row_count": 1,
        }

    entries = list(by_name.values())
    entries.sort(key=lambda e: parse_money_to_float(e.get("weightedWagerAmount")), reverse=True)

    admin_full: List[Dict[str, Any]] = []
    for i, e in enumerate(entries[:FULL_LEADERBOARD_MAX], start=1):
        full = str(e.get("username", "Unknown"))
        weighted = parse_money_to_float(e.get("weightedWagerAmount"))
        raw = e.get("wagerAmount")
        raw_float = parse_money_to_float(raw) if raw is not None else None
        admin_full.append({
            "rank": i,
            "username": full,
            "weighted_wager": weighted,
            # Keep old key as formatted string for template compatibility.
            "wager": money(weighted),
            "raw_wager": raw_float,
            "raw_wager_str": money(raw_float) if raw_float is not None else "—",
            "source": e.get("source", "shuffle"),
            "row_count": int(e.get("row_count") or 1),
        })

    admin_top11 = admin_full[:11]

    podium: List[dict] = []
    others: List[dict] = []
    for row in admin_top11:
        i = int(row["rank"])
        public_row = {
            "username": censor_username(row["username"]),
            "wager": row["wager"],
            "weighted_wager": row["wager"],
        }
        if i <= 3:
            podium.append(public_row)
        else:
            others.append({"rank": i, **public_row})

    meta.update({
        "weighted_row_count": len(normalized),
        "skipped_missing_weighted": skipped_missing_weighted,
        "skipped_campaign": skipped_campaign,
        "skipped_username": skipped_username,
        "aggregation_mode": SHUFFLE_AGGREGATION_MODE,
        "endpoint_kind": SHUFFLE_ENDPOINT_KIND,
        "campaign_code_filter": CAMPAIGN_CODE_FILTER,
    })

    public_payload = {
        "podium": podium,
        "others": others,
        "meta": {
            "updated_at": int(time.time()),
            "label": "Weighted Wager",
        },
    }
    return public_payload, admin_top11, admin_full, meta


def refresh_cache_once(reason: str = "tick") -> None:
    """
    Refresh caches and update persistent health/snapshots.

    If Shuffle fails temporarily and we already have data, keep the old cache but mark health as failed.
    """
    public, admin_top11, admin_full, meta = build_snapshots()
    now = int(time.time())

    with _admin_cache_lock:
        had_data = bool(ADMIN_CACHE.get("top11"))

    # If refresh returned nothing after we already had data, avoid blanking the public leaderboard.
    if not admin_top11 and had_data:
        with _store_lock:
            STORE["health"]["last_refresh_ok"] = False
            STORE["health"]["last_refresh_et"] = fmt_et(now)
            STORE["health"]["last_error"] = meta.get("error") or "Shuffle returned no weighted leaderboard rows"
            STORE["health"]["last_api_ms"] = meta.get("ms")
            STORE["health"]["last_source"] = meta.get("source")
            STORE["health"]["last_row_count"] = meta.get("row_count", 0)
            STORE["health"]["last_weighted_row_count"] = meta.get("weighted_row_count", 0)
            STORE["health"]["last_skipped_missing_weighted"] = meta.get("skipped_missing_weighted", 0)
            STORE["health"]["aggregation_mode"] = SHUFFLE_AGGREGATION_MODE
            STORE["health"]["endpoint_kind"] = SHUFFLE_ENDPOINT_KIND
            STORE["updated_at"] = now
            store_save(STORE)

        app.logger.warning(
            f"[REFRESH] FAIL kept_old_cache source={meta.get('source')} ms={meta.get('ms')} "
            f"rows={meta.get('row_count')} weighted={meta.get('weighted_row_count')} err={meta.get('error')}"
        )
        return

    with _cache_lock:
        DATA_CACHE.update(public)

    with _admin_cache_lock:
        ADMIN_CACHE["top11"] = admin_top11
        ADMIN_CACHE["full"] = admin_full
        ADMIN_CACHE["last_refresh"] = now

    with _store_lock:
        STORE["health"]["last_refresh_ok"] = bool(meta.get("ok")) and bool(admin_top11)
        STORE["health"]["last_refresh_et"] = fmt_et(now)
        STORE["health"]["last_error"] = meta.get("error")
        STORE["health"]["last_api_ms"] = meta.get("ms")
        STORE["health"]["last_source"] = meta.get("source")
        STORE["health"]["last_row_count"] = meta.get("row_count", 0)
        STORE["health"]["last_weighted_row_count"] = meta.get("weighted_row_count", 0)
        STORE["health"]["last_skipped_missing_weighted"] = meta.get("skipped_missing_weighted", 0)
        STORE["health"]["aggregation_mode"] = SHUFFLE_AGGREGATION_MODE
        STORE["health"]["endpoint_kind"] = SHUFFLE_ENDPOINT_KIND

        snaps = STORE.get("leaderboard_snapshots") or {}
        snaps["prev_top11"] = snaps.get("last_top11", [])
        snaps["last_top11"] = admin_top11
        snaps["updated_at"] = now
        STORE["leaderboard_snapshots"] = snaps

        STORE["updated_at"] = now
        store_save(STORE)

    app.logger.info(
        f"[REFRESH] ok={meta.get('ok')} reason={reason} source={meta.get('source')} "
        f"ms={meta.get('ms')} raw_rows={meta.get('row_count')} weighted_rows={meta.get('weighted_row_count')} "
        f"top11={len(admin_top11)} full={len(admin_full)} aggregation={SHUFFLE_AGGREGATION_MODE}"
    )


def refresh_loop() -> None:
    """Background loop: refresh every REFRESH_SECONDS."""
    while True:
        try:
            refresh_cache_once(reason="tick")
        except Exception as e:
            app.logger.exception(f"[REFRESH_LOOP] unexpected: {e}")
        time.sleep(max(5, int(REFRESH_SECONDS)))


# Initial refresh + background thread. Startup should not fail only because Shuffle is down.
try:
    refresh_cache_once(reason="startup")
except Exception as e:
    app.logger.exception(f"[STARTUP_REFRESH] failed: {e}")
threading.Thread(target=refresh_loop, daemon=True).start()

# -------------------------
# Kick endpoint placeholder
# -------------------------


def get_stream_status() -> Dict[str, Any]:
    """
    Return Kick status.

    Kept as a safe stub because live/viewer count was intentionally removed from the core logic.
    You can expand this later without affecting weighted leaderboard correctness.
    """
    return {"live": False, "title": None, "viewers": None, "source": "disabled", "updated": int(time.time())}


# -------------------------
# Public routes
# -------------------------

@app.route("/")
def index():
    return render_template("index.html")


@app.route("/data")
def data():
    with _cache_lock:
        payload = dict(DATA_CACHE)
    return jsonify(payload)


@app.route("/config")
def config():
    return jsonify({
        "start_time": START_TIME,
        "end_time": END_TIME,
        "refresh_seconds": REFRESH_SECONDS,
        "leaderboard_label": "Weighted Wager",
        "weighting_rules": WEIGHTING_RULES,
    })


@app.route("/stream")
def stream():
    return jsonify(get_stream_status())


@app.route("/healthz")
def healthz():
    """Simple health endpoint for uptime checks and deployment monitoring."""
    with _store_lock:
        health = dict(STORE.get("health") or {})
    with _admin_cache_lock:
        full_count = len(ADMIN_CACHE.get("full") or [])
        top_count = len(ADMIN_CACHE.get("top11") or [])
        last_refresh = int(ADMIN_CACHE.get("last_refresh") or 0)

    ok = bool(health.get("last_refresh_ok")) and top_count > 0
    return jsonify({
        "ok": ok,
        "last_refresh_ok": health.get("last_refresh_ok"),
        "last_refresh_et": health.get("last_refresh_et"),
        "last_source": health.get("last_source"),
        "last_error": health.get("last_error"),
        "last_api_ms": health.get("last_api_ms"),
        "leaderboard_count": full_count,
        "top_count": top_count,
        "last_refresh_epoch": last_refresh,
        "endpoint_kind": SHUFFLE_ENDPOINT_KIND,
        "aggregation_mode": SHUFFLE_AGGREGATION_MODE,
    }), (200 if ok else 503)


# -------------------------
# Admin routes
# -------------------------

@app.route("/admin", methods=["GET", "POST"])
def admin():
    """
    GET:
      - logged in: render admin panel
      - logged out: render login form

    POST:
      - login attempt, protected by per-IP rate limiting
    """
    csrf_token()

    if admin_user():
        return render_admin_panel()

    error = None
    if request.method == "POST":
        ip = client_ip()
        locked, remaining = login_locked(ip)
        if locked:
            error = f"Too many failed login attempts. Try again in {max(1, remaining // 60)} minute(s)."
            app.logger.warning(f"[LOGIN_RATE_LIMIT] ip={ip}")
            return render_template("admin_login.html", csrf_token=csrf_token(), error=error)

        username = (request.form.get("username") or "").strip()
        password = request.form.get("password") or ""

        with _store_lock:
            urec = (STORE.get("users") or {}).get(username)

        if not urec or not check_password_hash(urec.get("pw_hash", ""), password):
            login_record_failure(ip)
            error = "Invalid username or password."
            app.logger.warning(f"[LOGIN_FAIL] ip={ip} user={username}")
        else:
            login_record_success(ip)
            session.permanent = True
            session["admin_user"] = username
            session["csrf_token"] = secrets.token_urlsafe(32)
            app.logger.info(f"[LOGIN_OK] ip={ip} user={username}")
            audit("login_ok", {"user": username})
            return redirect(url_for("admin"))

    return render_template("admin_login.html", csrf_token=csrf_token(), error=error)


@app.route("/admin/logout")
def admin_logout():
    if admin_user():
        audit("logout", {"user": admin_user()})
    session.clear()
    return redirect(url_for("admin"))


def render_admin_panel():
    """Render admin panel with weighted leaderboard, logs, and controls."""
    csrf_token()

    with _store_lock:
        overrides = dict(STORE.get("overrides") or {})
        audit_log = list(reversed(STORE.get("audit_log") or []))
        banned_ips = list(STORE.get("banned_ips") or [])
        health = dict(STORE.get("health") or {})
        admin_users = sorted(list((STORE.get("users") or {}).keys()))

    with _access_log_lock:
        access_log = list(reversed(ACCESS_LOG))

    with _admin_cache_lock:
        top11 = list(ADMIN_CACHE.get("top11") or [])
        full = list(ADMIN_CACHE.get("full") or [])
        last_refresh = int(ADMIN_CACHE.get("last_refresh") or 0)

    next_refresh = last_refresh + int(REFRESH_SECONDS) if last_refresh else 0
    top11_with_deltas = compute_top11_deltas()

    return render_template(
        "admin_panel.html",
        csrf_token=csrf_token(),
        admin_user=admin_user(),
        is_superadmin=is_superadmin(),
        superadmin_user=SUPERADMIN,
        refresh_seconds=REFRESH_SECONDS,
        start_et=fmt_et(int(START_TIME)),
        end_et=fmt_et(int(END_TIME)),
        last_refresh_et=fmt_et(last_refresh),
        next_refresh_et=fmt_et(next_refresh),
        endpoint_kind=SHUFFLE_ENDPOINT_KIND,
        aggregation_mode=SHUFFLE_AGGREGATION_MODE,
        campaign_code_filter=CAMPAIGN_CODE_FILTER or "—",
        weighting_rules=WEIGHTING_RULES,
        overrides=overrides,
        top11=top11,
        top11_with_deltas=top11_with_deltas,
        full_leaderboard=full,
        access_log=access_log,
        audit_log=audit_log,
        banned_ips=banned_ips,
        health=health,
        admin_users=admin_users,
    )


def _valid_admin_username(u: str) -> bool:
    """Admin usernames: 3..32 chars, letters/numbers/_ only."""
    u = (u or "").strip()
    return bool(re.fullmatch(r"[A-Za-z0-9_]{3,32}", u))


@app.route("/admin/export.csv")
@login_required
def admin_export_csv():
    """Export current full weighted leaderboard for payout verification."""
    with _admin_cache_lock:
        rows = list(ADMIN_CACHE.get("full") or [])
        last_refresh = int(ADMIN_CACHE.get("last_refresh") or 0)

    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow([
        "rank",
        "username",
        "weighted_wager",
        "raw_wager",
        "source",
        "row_count",
        "last_refresh_et",
    ])
    for row in rows:
        writer.writerow([
            row.get("rank"),
            row.get("username"),
            f"{parse_money_to_float(row.get('weighted_wager')):.2f}",
            "" if row.get("raw_wager") is None else f"{parse_money_to_float(row.get('raw_wager')):.2f}",
            row.get("source", ""),
            row.get("row_count", 1),
            fmt_et(last_refresh),
        ])

    audit("export_csv", {"rows": len(rows)})
    return Response(
        output.getvalue(),
        mimetype="text/csv",
        headers={"Content-Disposition": "attachment; filename=weighted_leaderboard_export.csv"},
    )


@app.route("/admin/action", methods=["POST"])
@login_required
def admin_action():
    """CSRF-protected admin actions."""
    require_csrf()
    action = (request.form.get("action") or "").strip()

    if action == "set_override":
        username = (request.form.get("username") or "").strip()
        amount_raw = (request.form.get("amount") or "").strip()
        if not username:
            return redirect(url_for("admin"))

        before = None
        after = None
        removed = False

        with _store_lock:
            STORE.setdefault("overrides", {})

            if amount_raw == "":
                before = STORE["overrides"].get(username)
                STORE["overrides"].pop(username, None)
                STORE["updated_at"] = int(time.time())
                store_save(STORE)
                removed = True
            else:
                new_amt = float(parse_money_to_float(amount_raw))
                before = STORE["overrides"].get(username)
                STORE["overrides"][username] = new_amt
                STORE["updated_at"] = int(time.time())
                store_save(STORE)
                after = new_amt

        if removed:
            audit("weighted_override_remove", {"username": username, "before": before})
        else:
            audit("weighted_override_set", {"username": username, "before": before, "after": after})

        return redirect(url_for("admin"))

    if action == "force_refresh":
        audit("force_refresh", {})
        started = time.time()
        with _force_refresh_lock:
            try:
                refresh_cache_once(reason="force_refresh")
                app.logger.info(f"[ADMIN] force_refresh done in {time.time() - started:.2f}s")
            except Exception as e:
                app.logger.exception(f"[ADMIN] force_refresh failed: {e}")
        return redirect(url_for("admin"))

    if action == "ban_ip":
        ip = (request.form.get("ip") or "").strip()
        if ip:
            with _store_lock:
                STORE.setdefault("banned_ips", [])
                if ip not in STORE["banned_ips"]:
                    STORE["banned_ips"].append(ip)
                STORE["updated_at"] = int(time.time())
                store_save(STORE)
            audit("ban_ip", {"ip": ip})
        return redirect(url_for("admin"))

    if action == "unban_ip":
        ip = (request.form.get("ip") or "").strip()
        if ip:
            with _store_lock:
                STORE.setdefault("banned_ips", [])
                STORE["banned_ips"] = [x for x in STORE["banned_ips"] if x != ip]
                STORE["updated_at"] = int(time.time())
                store_save(STORE)
            audit("unban_ip", {"ip": ip})
        return redirect(url_for("admin"))

    if action == "clear_access_log":
        global ACCESS_LOG
        with _access_log_lock:
            ACCESS_LOG = []
        audit("clear_access_log", {})
        return redirect(url_for("admin"))

    if action == "clear_audit_log":
        with _store_lock:
            STORE["audit_log"] = []
            STORE["updated_at"] = int(time.time())
            store_save(STORE)
        audit("clear_audit_log", {})
        return redirect(url_for("admin"))

    if action in {"add_admin", "remove_admin", "set_admin_password"}:
        if not is_superadmin():
            abort(403)

        if action == "add_admin":
            new_user = (request.form.get("new_username") or "").strip()
            new_pw = request.form.get("new_password") or ""
            if not _valid_admin_username(new_user):
                audit("add_admin_reject", {"reason": "bad_username", "username": new_user})
                return redirect(url_for("admin"))
            if not new_pw:
                audit("add_admin_reject", {"reason": "empty_password", "username": new_user})
                return redirect(url_for("admin"))
            if new_user == SUPERADMIN:
                audit("add_admin_reject", {"reason": "superadmin_reserved", "username": new_user})
                return redirect(url_for("admin"))

            with _store_lock:
                STORE.setdefault("users", {})
                if new_user in STORE["users"]:
                    audit("add_admin_reject", {"reason": "already_exists", "username": new_user})
                    return redirect(url_for("admin"))
                STORE["users"][new_user] = {
                    "pw_hash": generate_password_hash(new_pw),
                    "created_at": int(time.time()),
                    "created_by": admin_user() or SUPERADMIN,
                }
                STORE["updated_at"] = int(time.time())
                store_save(STORE)

            audit("add_admin_ok", {"username": new_user})
            return redirect(url_for("admin"))

        if action == "remove_admin":
            rm_user = (request.form.get("rm_username") or "").strip()
            if not rm_user or rm_user == SUPERADMIN:
                audit("remove_admin_reject", {"reason": "invalid_target", "username": rm_user})
                return redirect(url_for("admin"))

            with _store_lock:
                existed = rm_user in (STORE.get("users") or {})
                (STORE.get("users") or {}).pop(rm_user, None)
                STORE["updated_at"] = int(time.time())
                store_save(STORE)

            audit("remove_admin", {"username": rm_user, "existed": existed})
            return redirect(url_for("admin"))

        if action == "set_admin_password":
            target = (request.form.get("pw_username") or "").strip()
            pw = request.form.get("pw_password") or ""
            if not target or not pw:
                audit("set_admin_password_reject", {"reason": "missing_fields"})
                return redirect(url_for("admin"))
            if target == SUPERADMIN:
                audit("set_admin_password_reject", {"reason": "superadmin_forced"})
                return redirect(url_for("admin"))

            with _store_lock:
                users = STORE.get("users") or {}
                if target not in users:
                    audit("set_admin_password_reject", {"reason": "no_such_user", "username": target})
                    return redirect(url_for("admin"))
                users[target]["pw_hash"] = generate_password_hash(pw)
                users[target]["updated_at"] = int(time.time())
                STORE["users"] = users
                STORE["updated_at"] = int(time.time())
                store_save(STORE)

            audit("set_admin_password_ok", {"username": target})
            return redirect(url_for("admin"))

    return redirect(url_for("admin"))


# -------------------------
# Errors
# -------------------------

@app.errorhandler(400)
def bad_request(_e):
    return (
        "Bad Request (400)\n\n"
        "This is almost always cookies/sessions or CSRF mismatch.\n"
        "Fixes:\n"
        "1) Make sure cookies are enabled.\n"
        "2) If you're using http:// locally, set SESSION_COOKIE_SECURE=0.\n"
        "3) If you're using https:// in production, set SESSION_COOKIE_SECURE=1.\n",
        400,
        {"Content-Type": "text/plain; charset=utf-8"},
    )


@app.errorhandler(403)
def forbidden(_e):
    return (
        "Forbidden (403)\n\n"
        "If your IP was banned, remove it from admin_store.json -> banned_ips.\n",
        403,
        {"Content-Type": "text/plain; charset=utf-8"},
    )


@app.errorhandler(404)
def nf(_e):
    return render_template("404.html"), 404


if __name__ == "__main__":
    app.logger.info(f"Listening on http://0.0.0.0:{PORT}")
    app.run(host="0.0.0.0", port=PORT)
