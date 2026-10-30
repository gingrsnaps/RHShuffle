"""One configuration path; saved race settings win after the first import."""
import os
import re
import json
import tempfile
import threading
from pathlib import Path

from race_support import DEFAULT_PRIZES, canonical_site, read_json

RELEASE = "2026.10.30-empiredrop-contract-adapter3"
INTERVAL = 60


class Config:
    def __init__(self, root=None):
        self.root = Path(root or Path(__file__).parent).resolve()
        self.credential_lock = threading.RLock()
        path = lambda name, default: Path(os.getenv(name) or self.root / default)
        self.legacy = path("ADMIN_STORE_PATH", "admin_store.json")
        self.seed = path("ADMIN_SEED_PATH", "private/admin_store.seed.json")
        self.recovery = path("RECOVERY_SEED_PATH", "private/recovery.seed.json")
        self.db_path = path("LOCAL_DATABASE_PATH", "data/redhunllef.sqlite3")
        self.state_path = path("STATE_FILE", "data/state.json")
        explicit = os.getenv("SETTINGS_PATH")
        bundled = self.root / "private/settings.json"
        private = read_json(bundled) if bundled.is_file() and not explicit else {}
        settings_path = path("SETTINGS_PATH", "settings.json")
        settings = read_json(settings_path) if settings_path.is_file() else {}
        integration_path = path("INTEGRATIONS_PATH", "integrations.json")
        integrations = read_json(integration_path) if integration_path.is_file() else {}
        defaults = {**private, **settings}
        self.credentials, self.sources = {}, {}
        for key in ("shuffle_api_key", "kick_client_id", "kick_client_secret", "empiredrop_public_key", "empiredrop_private_key"):
            layers = [(os.getenv(key.upper()), key.upper())]
            if key == "shuffle_api_key":
                layers.append((os.getenv("API_KEY"), "API_KEY"))
            layers += [(settings.get(key), "settings.json"), (integrations.get(key), "integrations.json"),
                       (private.get(key), "private/settings.json")]
            value, source = next(((str(v).strip(), source) for v, source in layers if v and str(v).strip()), ("", "missing"))
            self.credentials[key], self.sources[key] = value, source
        # This build deliberately uses only local JSON. Old database variables
        # cannot make startup depend on a removed service.
        # EmpireDrop's API contract is not publicly documented. The endpoint,
        # auth header names, wager unit and time parameters are explicit here,
        # never guessed by the application or sent to the browser.
        self.empiredrop = {
            "api_url": str(os.getenv("EMPIREDROP_API_URL", defaults.get("empiredrop_api_url", ""))),
            "public_header": str(defaults.get("empiredrop_public_header", "X-Public-Key")),
            "private_header": str(defaults.get("empiredrop_private_header", "X-Private-Key")),
            "start_param": str(defaults.get("empiredrop_start_param", "startTime")),
            "end_param": str(defaults.get("empiredrop_end_param", "endTime")),
            "currency": str(defaults.get("empiredrop_currency", "EUR")).upper(),
            "wager_divisor": str(defaults.get("empiredrop_wager_divisor", "1")),
            "code_param": str(defaults.get("empiredrop_code_param", "")),
            "code_field": str(defaults.get("empiredrop_code_field", "referralCode")),
            "wager_field": str(defaults.get("empiredrop_wager_field", "totalWagered")),
            "name_field": str(defaults.get("empiredrop_name_field", "username")),
            "code_scoped": str(defaults.get("empiredrop_code_scoped", False)).lower() in ("1", "true"),
            "record_mode": str(defaults.get("empiredrop_record_mode", "player_total")),
            "user_id_field": str(defaults.get("empiredrop_user_id_field", "")),
            "transaction_id_field": str(defaults.get("empiredrop_transaction_id_field", "")),
            "pagination_mode": str(defaults.get("empiredrop_pagination_mode", "none")),
            "cursor_param": str(defaults.get("empiredrop_cursor_param", "cursor")),
            "next_cursor_field": str(defaults.get("empiredrop_next_cursor_field", "nextCursor")),
            "verified_contract": str(defaults.get("empiredrop_verified_contract", False)).lower() in ("1", "true"),
            "auth_mode": str(defaults.get("empiredrop_auth_mode", "dual_headers")),
            "http_method": str(defaults.get("empiredrop_http_method", "GET")),
            "request_location": str(defaults.get("empiredrop_request_location", "query")),
            "timestamp_format": str(defaults.get("empiredrop_timestamp_format", "unix_s")),
            "rows_path": str(defaults.get("empiredrop_rows_path", "")),
            "next_cursor_path": str(defaults.get("empiredrop_next_cursor_path", "")),
        }
        self.storage_mode, self.db_url = "local", ""
        self.ignored_database_url = bool(os.getenv("DATABASE_URL"))
        self.state_key = os.getenv("APP_STATE_KEY", "redhunllef")
        if not re.fullmatch(r"[A-Za-z0-9_-]{1,64}", self.state_key):
            raise ValueError("APP_STATE_KEY must contain 1–64 letters, numbers, underscores or hyphens.")
        # Storage and web security are independent: local storage on App Platform
        # still uses production cookies, proxy handling, and the normal server.
        mode = os.getenv("APP_ENV", "production" if "PORT" in os.environ else "local")
        self.production = mode == "production"
        self.port = int(os.getenv("PORT", "8080"))
        if not 1 <= self.port <= 65535:
            raise ValueError("PORT must be between 1 and 65535.")
        self.proxy = os.getenv("TRUST_APP_PLATFORM", "0") == "1"
        self.secure_cookie = os.getenv("SESSION_COOKIE_SECURE", "always" if self.production else "auto").lower()
        self.secret = os.getenv("SECRET_KEY", "").strip()
        if self.secret and len(self.secret) < 32:
            raise ValueError("SECRET_KEY must have at least 32 characters when set.")
        self.superadmin = os.getenv("SUPERADMIN_USER", defaults.get("superadmin_user", "gingrsnaps"))
        self.bootstrap_password = os.getenv("ADMIN_BOOTSTRAP_PASS", "enok2121")
        self.endpoint = os.getenv("SHUFFLE_ENDPOINT_KIND", defaults.get("shuffle_endpoint_kind", "wager"))
        if not re.fullmatch(r"[A-Za-z0-9_-]+", self.endpoint):
            raise ValueError("SHUFFLE_ENDPOINT_KIND must be one endpoint name.")
        self.aggregation = os.getenv("SHUFFLE_AGGREGATION_MODE", defaults.get("shuffle_aggregation_mode", "sum"))
        if self.aggregation not in {"sum", "max"}:
            raise ValueError("SHUFFLE_AGGREGATION_MODE must be sum or max.")
        self.raw_fallback = str(os.getenv("ALLOW_RAW_WAGER_FALLBACK", defaults.get("allow_raw_wager_fallback", False))).lower() in {"1", "true"}
        self.limit = min(10000, max(100, int(os.getenv("FULL_LEADERBOARD_MAX", "300"))))
        site = dict(site_name="RedHunllef", race_title="RedHunllef Wager Race",
                    race_description="Your wagers. Your place. The race is on.", start_time=0, end_time=0,
                    refresh_seconds=60, leaderboard_size=15, prizes={str(k): str(v) for k, v in DEFAULT_PRIZES.items()},
                    kick_channel_slug="redhunllef", campaign_code_filter="Red", sponsor_name="Shuffle.com",
                    sponsor_url="https://shuffle.com/?r=Red", stream_url="https://kick.com/redhunllef",
                    community_name="Red Community", community_url="", responsible_gambling_url="https://www.ncpgambling.org/")
        for name in ("START_TIME", "END_TIME", "KICK_CHANNEL_SLUG", "CAMPAIGN_CODE_FILTER"):
            if name in os.environ:
                defaults[name.lower()] = int(os.environ[name]) if name.endswith("TIME") else os.environ[name]
        self.site = canonical_site(defaults, site)

    def diagnostics(self):
        return {key: {"configured": bool(value), "source": self.sources[key]} for key, value in self.credentials.items()}

    def replace_empiredrop_keys(self, public='', private=''):
        """Superadmin-only server-side operation. Empty input retains the old key.

        Written to private/settings.json with an atomic replacement and mode 0600.
        Environment-supplied keys deliberately cannot be overridden by this form.
        """
        updates = {}
        for field, value, prefix in (("empiredrop_public_key",public,"pk_prod_"),
                                     ("empiredrop_private_key",private,"sk_prod_")):
            value = str(value or '').strip()
            if not value:
                continue
            if os.getenv(field.upper()):
                raise ValueError('A deployment environment variable overrides ' + field + '. Update it at the host.')
            if not value.startswith(prefix) or not re.fullmatch(r'[A-Za-z0-9_]{24,128}', value):
                raise ValueError('Invalid ' + field + ' format. Enter the provider-issued value.')
            updates[field] = value
        if not updates:
            return False
        with self.credential_lock:
            target = self.root / 'private' / 'settings.json'
            target.parent.mkdir(parents=True, exist_ok=True)
            original = read_json(target) if target.exists() else {}
            if not isinstance(original, dict):
                raise ValueError('Private settings must be a JSON object.')
            content = {**original, **updates}
            fd, temp = tempfile.mkstemp(prefix='.empiredrop-', suffix='.json', dir=target.parent)
            try:
                with os.fdopen(fd, 'w', encoding='utf-8', newline='\n') as file:
                    json.dump(content, file, ensure_ascii=False, indent=2)
                    file.write('\n')
                    file.flush(); os.fsync(file.fileno())
                os.chmod(temp, 0o600)
                os.replace(temp, target)
            finally:
                if os.path.exists(temp):
                    os.unlink(temp)
            for key, value in updates.items():
                self.credentials[key], self.sources[key] = value, 'private/settings.json'
        return True
