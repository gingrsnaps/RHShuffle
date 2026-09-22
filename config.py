"""One configuration path; saved race settings win after the first import."""
import os
import re
from pathlib import Path

from race_support import DEFAULT_PRIZES, canonical_site, read_json

RELEASE = "2026.09.22-boss"
INTERVAL = 60


class Config:
    def __init__(self, root=None):
        self.root = Path(root or Path(__file__).parent).resolve()
        path = lambda name, default: Path(os.getenv(name) or self.root / default)
        self.legacy = path("ADMIN_STORE_PATH", "admin_store.json")
        self.seed = path("ADMIN_SEED_PATH", "private/admin_store.seed.json")
        self.recovery = path("RECOVERY_SEED_PATH", "private/recovery.seed.json")
        self.db_path = path("LOCAL_DATABASE_PATH", "data/redhunllef.sqlite3")
        explicit = os.getenv("SETTINGS_PATH")
        bundled = self.root / "private/settings.json"
        private = read_json(bundled) if bundled.is_file() and not explicit else {}
        settings_path = path("SETTINGS_PATH", "settings.json")
        settings = read_json(settings_path) if settings_path.is_file() else {}
        integration_path = path("INTEGRATIONS_PATH", "integrations.json")
        integrations = read_json(integration_path) if integration_path.is_file() else {}
        defaults = {**private, **settings}
        self.credentials, self.sources = {}, {}
        for key in ("shuffle_api_key", "kick_client_id", "kick_client_secret"):
            layers = [(os.getenv(key.upper()), key.upper())]
            if key == "shuffle_api_key":
                layers.append((os.getenv("API_KEY"), "API_KEY"))
            layers += [(settings.get(key), "settings.json"), (integrations.get(key), "integrations.json"),
                       (private.get(key), "private/settings.json")]
            value, source = next(((str(v).strip(), source) for v, source in layers if v and str(v).strip()), ("", "missing"))
            self.credentials[key], self.sources[key] = value, source
        # Local storage needs no account, service, or connection string. A stale
        # DATABASE_URL from an earlier deployment cannot break this default.
        self.storage_mode = os.getenv("STORAGE_MODE", "local").strip().lower()
        if self.storage_mode not in {"local", "postgres"}:
            raise ValueError("STORAGE_MODE must be local or postgres.")
        supplied_url = os.getenv("DATABASE_URL", "").strip()
        self.db_url = supplied_url if self.storage_mode == "postgres" else ""
        self.ignored_database_url = bool(supplied_url and not self.db_url)
        if self.storage_mode == "postgres" and not self.db_url:
            raise ValueError("STORAGE_MODE=postgres needs DATABASE_URL. Use STORAGE_MODE=local for automatic local storage.")
        self.state_key = os.getenv("APP_STATE_KEY", "redhunllef")
        if not re.fullmatch(r"[A-Za-z0-9_-]{1,64}", self.state_key):
            raise ValueError("APP_STATE_KEY must contain 1–64 letters, numbers, underscores or hyphens.")
        # Storage and web security are independent: local storage on App Platform
        # still uses production cookies, proxy handling, and the normal server.
        mode = os.getenv("APP_ENV", "production" if self.db_url or "PORT" in os.environ else "local")
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
        self.sslmode = os.getenv("DATABASE_SSLMODE", "require")
        if self.db_url and self.sslmode not in {"require", "verify-full", "verify-ca", "disable"}:
            raise ValueError("Unsupported DATABASE_SSLMODE.")
        self.sslrootcert = os.getenv("DATABASE_SSLROOTCERT", "")
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
