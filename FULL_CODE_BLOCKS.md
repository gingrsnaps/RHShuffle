# RedHunllef V18 complete code reference

Private credentials and mutable JSON state are intentionally omitted from this readable reference; they remain separate files in the private package.

## `admin_navigation.py`

```python
"""Canonical admin navigation contract.

Every visible destination has one stable URL. Legacy query-string and section
links redirect to these paths, so cached older pages cannot create 404s.
"""
from urllib.parse import urlencode

ADMIN_TABS = frozenset({
    "overview", "shuffle", "race", "players", "empiredrop",
    "gaming", "activity", "settings"
})

ADMIN_PATHS = {
    "overview": "/admin",
    "shuffle": "/admin/leaderboards/shuffle",
    "race": "/admin/leaderboards/shuffle/schedule",
    "players": "/admin/leaderboards/shuffle/players",
    "empiredrop": "/admin/leaderboards/empiredrop",
    "gaming": "/admin/gaming",
    "activity": "/admin/activity",
    "settings": "/admin/settings",
}

ADMIN_ANCHORS = {
    "race": frozenset({"raceForm", "prizes", "siteConfiguration"}),
    "players": frozenset({"override"}),
    "empiredrop": frozenset({"empirePlayersHeading", "empireDatesTitle",
        "empireRewards", "empireRaceDetails", "empireBackup", "empireAdvanced"}),
    "gaming": frozenset({"gamingAdminHeading", "gamingFunding"}),
    "settings": frozenset({"accountSecurity", "adminAccounts", "backups",
        "configurationDetails", "accessControls", "recovery"}),
    "activity": frozenset({"adminOperations"}),
}

ADMIN_SECTION_ALIASES = {
    "overview": "overview", "dashboard": "overview",
    "leaderboards": "shuffle", "shuffle": "shuffle",
    "schedule": "race", "race": "race", "prizes": "race", "edit-race": "race",
    "participants": "players", "wagerers": "players", "players": "players",
    "empiredrop": "empiredrop", "empire": "empiredrop",
    "games": "gaming", "gaming": "gaming", "redpoints": "gaming",
    "settings": "settings", "recovery": "settings", "connections": "settings",
    "accounts": "settings", "activity": "activity", "logs": "activity",
}


def admin_link(tab="overview", anchor=None):
    """Return a validated canonical admin URL."""
    if tab not in ADMIN_TABS:
        raise ValueError("Unknown admin tab")
    if anchor is not None and anchor not in ADMIN_ANCHORS.get(tab, frozenset()):
        raise ValueError("Unknown admin section")
    return ADMIN_PATHS[tab] + ("#" + anchor if anchor else "")


def legacy_query(tab):
    """Document the former URL for tests and migration diagnostics."""
    if tab not in ADMIN_TABS:
        raise ValueError("Unknown admin tab")
    return "/admin?" + urlencode({"tab": tab})
```

## `baccarat.py`

```python
"""Eight-deck Punto Banco, replayed only from the committed random stream.

Each round starts a fresh 416-card shoe; there are no burns or side bets.
The draw tableau follows standard commission Baccarat. All returns include
the stake and round down to whole RedPoints, including the 1.95x Banker win.
"""

RETURNS = {'player': 20000, 'banker': 19500, 'tie': 90000}


def card_value(card):
    rank = card % 13 + 1
    return rank if rank < 10 else 0


def total(cards):
    return sum(map(card_value, cards)) % 10


def banker_draws(points, player_third):
    """Called only after both initial naturals have been ruled out."""
    if player_third is None:
        return points <= 5
    if points <= 2:
        return True
    if points == 3:
        return player_third != 8
    if points == 4:
        return 2 <= player_third <= 7
    if points == 5:
        return 4 <= player_third <= 7
    return points == 6 and player_third in (6, 7)


def replay(draw, wager, side):
    if side not in RETURNS:
        raise ValueError('Choose Player, Banker or Tie.')
    shoe = list(range(416))
    cursor = 0

    def card():
        nonlocal cursor
        # Partial Fisher–Yates: sample distinct physical cards without replacement.
        other = cursor + draw.below(len(shoe) - cursor)
        shoe[cursor], shoe[other] = shoe[other], shoe[cursor]
        value = shoe[cursor]
        cursor += 1
        return value

    player, banker = [card()], [card()]
    player.append(card())
    banker.append(card())
    pt, bt = total(player), total(banker)
    natural = pt >= 8 or bt >= 8
    if not natural:
        third = None
        if pt <= 5:
            player.append(card())
            third = card_value(player[-1])
        if banker_draws(bt, third):
            banker.append(card())
    pt, bt = total(player), total(banker)
    winner = 'tie' if pt == bt else 'player' if pt > bt else 'banker'
    won = side == winner
    push = winner == 'tie' and side != 'tie'
    payout = wager * RETURNS[side] // 10000 if won else wager if push else 0
    return dict(player=player, banker=banker, player_total=pt, banker_total=bt,
                natural=natural, winner=winner, won=won, push=push, payout=payout)
```

## `blackjack.py`

```python
"""Pure six-deck Blackjack replay. No storage, HTTP, clock or random source.

The fairness module supplies unbiased draws from the precommitted seed.
Cards are unique IDs 0..311: deck*52 + suit*13 + rank-1 (A=1, K=13).
A fresh six-deck shoe is sampled without replacement for every round.
"""


def total(cards):
    ranks = [card % 13 + 1 for card in cards]
    points = sum(min(rank, 10) for rank in ranks)
    soft = 1 in ranks and points + 10 <= 21
    return points + (10 if soft else 0), soft


def replay(draw, wager, actions):
    """Replay legal player decisions; keep the dealer hole card private upstream."""
    if not isinstance(actions, list) or len(actions) > 32:
        raise ValueError('Invalid Blackjack action history.')
    shoe = list(range(312))
    cursor = 0
    def card():
        nonlocal cursor
        other = cursor + draw.below(len(shoe) - cursor)
        shoe[cursor], shoe[other] = shoe[other], shoe[cursor]
        value = shoe[cursor]
        cursor += 1
        return value
    player, dealer = [card()], [card()]
    player.append(card()); dealer.append(card())
    pt, _ = total(player); dt, _ = total(dealer)
    ended = pt == 21 or dt == 21  # Dealer peeks before any player decision.
    natural = pt == 21 and dt != 21
    stake = wager
    for index, action in enumerate(actions):
        if ended or action not in ('hit', 'stand', 'double'):
            raise ValueError('That Blackjack action is not legal.')
        if action == 'double':
            if index or len(player) != 2:
                raise ValueError('Double is available only on your first two cards.')
            stake = wager * 2
        if action in ('hit', 'double'):
            player.append(card())
        pt, _ = total(player)
        ended = action in ('stand', 'double') or pt >= 21
    if ended and not (len(player) == 2 and (pt == 21 or dt == 21)) and pt <= 21:
        while total(dealer)[0] < 17:  # Stand on hard and soft 17.
            dealer.append(card())
    pt, ps = total(player); dt, ds = total(dealer)
    status, payout = 'playing', 0
    if ended:
        if len(dealer) == 2 and dt == 21:
            status = 'push' if len(player) == 2 and pt == 21 else 'lose'
        elif natural:
            status = 'blackjack'
        elif pt > 21:
            status = 'lose'
        elif dt > 21 or pt > dt:
            status = 'win'
        elif pt == dt:
            status = 'push'
        else:
            status = 'lose'
        payout = wager * 5 // 2 if status == 'blackjack' else stake * 2 if status == 'win' else stake if status == 'push' else 0
    return dict(ended=ended, player=player, dealer=dealer, player_total=pt, dealer_total=dt,
                player_soft=ps, dealer_soft=ds, status=status, total_wager=stake, payout=payout)
```

## `config.py`

```python
"""One configuration path; saved race settings win after the first import."""
import os
import re
import json
import tempfile
import threading
from pathlib import Path

from race_support import DEFAULT_PRIZES, canonical_site, read_json

RELEASE = "2026.11.14-empiredrop-prize-publish-v18"
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
            # A Git deployment commonly omits private/settings.json. Honor an
            # encrypted SHUFFLE_API_KEY environment variable first; otherwise
            # use the bundled server-only fallback requested by the owner.
            # NEVER publish this repository or serve this Python file directly.
            if key == 'shuffle_api_key':
                from shuffle_deploy_key import SHUFFLE_BUNDLED_KEY
                layers.append((SHUFFLE_BUNDLED_KEY, 'server-side bundled Shuffle key'))
            # Optional server-only fallback for Git deployments where private/
            # is excluded by .gitignore. ONLY use a PRIVATE Git repository.
            if key.startswith('empiredrop_'):
                from empiredrop_deploy_keys import EMPIREDROP_KEYS
                layers.append((EMPIREDROP_KEYS.get(key), 'server-side bundled EmpireDrop keys'))
            value, source = next(((str(v).strip(), source) for v, source in layers if v and str(v).strip()), ("", "missing"))
            self.credentials[key], self.sources[key] = value, source
        # This build deliberately uses only local JSON. Old database variables
        # cannot make startup depend on a removed service.
        # The documented EmpireDrop Races routes are implemented separately.
        # Legacy generic wager API settings are retained for compatibility.
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
```

## `empiredrop.py`

```python
"""EmpireDrop-only, read-only affiliate standings.

The modern EmpireDrop Races path follows the user-supplied OpenAPI 2.0.1.
Legacy generic wagering code remains for old configuration compatibility only.
Official races use EmpireDrop's dates; custom/weekly windows opt in to the
deprecated timestamp endpoint. Currency/unit and tied ranks remain authoritative.
"""
from __future__ import annotations

import copy
from datetime import datetime, timedelta, timezone
from decimal import Decimal, InvalidOperation
import hashlib
import json
import logging
import re
import threading
import time
from urllib.parse import urlsplit

import requests

from integrations import ProviderError
from empiredrop_races import (RaceAPI, RACE_DEFAULTS, validate_race_settings,
                              select_race, normalize_race, keys_only,
                              extract_race_rows, time_value, normalize_legacy_window)
from race_support import EASTERN, fmt_et, local_input
from empiredrop_features import (validate_rewards, rewards_public, payout_for_rows, mask_public_username, EMPIRE_PLACES)

LOG = logging.getLogger('redhunllef.empiredrop')
CODE = 'red'
REFERRAL_URL = 'https://empiredrop.com/c/red'
MAX_ROWS = 10000
MAX_PAGES = 20

# These are *placeholders*, not claims about EmpireDrop's official API.
# Never enable a connection until each of them has been verified with the provider.
DEFAULTS = {
    'api_url': '', 'public_header': 'X-Public-Key', 'private_header': 'X-Private-Key',
    'start_param': 'startTime', 'end_param': 'endTime', 'code_param': '',
    'code_field': 'referralCode', 'name_field': 'username', 'user_id_field': '',
    'wager_field': 'totalWagered', 'currency': 'EUR', 'wager_divisor': '1',
    'code_scoped': False, 'record_mode': 'player_total', 'transaction_id_field': '',
    'pagination_mode': 'none', 'cursor_param': 'cursor', 'next_cursor_field': 'nextCursor',
    'verified_contract': False,
    'auth_mode': 'dual_headers', 'http_method': 'GET', 'request_location': 'query',
    'timestamp_format': 'unix_s', 'rows_path': '', 'next_cursor_path': '',
}
EDITABLE = frozenset(DEFAULTS)
FIELD = re.compile(r'^[a-zA-Z][a-zA-Z0-9_-]{0,49}$')
PATH = re.compile(r'^[a-zA-Z][a-zA-Z0-9_-]{0,49}(?:\.[a-zA-Z][a-zA-Z0-9_-]{0,49}){0,7}$')
HEADER = re.compile(r'^[a-zA-Z][a-zA-Z0-9-]{0,49}$')


def current_week(now=None):
    """Tue 18:00 ET to Tue 18:00 ET, including both DST transitions."""
    local = datetime.fromtimestamp(int(time.time() if now is None else now), EASTERN)
    days = (local.weekday() - 1) % 7
    beginning = local.date() - timedelta(days=days)
    start = datetime(beginning.year, beginning.month, beginning.day, 18, tzinfo=EASTERN)
    if local < start:
        beginning -= timedelta(days=7)
        start = datetime(beginning.year, beginning.month, beginning.day, 18, tzinfo=EASTERN)
    end_day = beginning + timedelta(days=7)
    end = datetime(end_day.year, end_day.month, end_day.day, 18, tzinfo=EASTERN)
    return int(start.timestamp()), int(end.timestamp())


def schedule(admin, now=None):
    """EmpireDrop has its OWN race window; Shuffle dates are never consulted."""
    saved = admin.get('empiredrop_race', {})
    if not isinstance(saved, dict):
        saved = {}
    mode = saved.get('mode', 'weekly')
    if mode == 'custom':
        start, end = int(saved.get('start_time', 0)), int(saved.get('end_time', 0))
        if not 0 < start < end <= 4102444799:
            raise ValueError('Invalid saved EmpireDrop schedule.')
    else:
        mode = 'weekly'
        start, end = current_week(now)
    return dict(start_time=start, end_time=end, mode=mode,
                start_et=fmt_et(start), end_et=fmt_et(end),
                start_input=local_input(start), end_input=local_input(end), code=CODE)


def scope_id(site):
    payload = [site['start_time'], site['end_time'], CODE]
    return hashlib.sha256(json.dumps(payload).encode('ascii')).hexdigest()[:24]


def validate_settings(value):
    """Validate a user-approved provider contract without accepting any keys."""
    if not isinstance(value, dict) or set(value) - EDITABLE:
        raise ValueError('Unexpected EmpireDrop configuration field.')
    result = {**DEFAULTS, **value}
    url = str(result['api_url']).strip()
    if url:
        p = urlsplit(url)
        if (p.scheme != 'https' or not p.hostname or p.hostname != 'empiredrop.com'
            and not p.hostname.endswith('.empiredrop.com') or p.username or p.password
            or p.port not in (None, 443) or p.query or p.fragment or not p.path.startswith('/')):
            raise ValueError('Official API URL must use HTTPS on an empiredrop.com host without credentials or query.')
    result['api_url'] = url
    for key in ('public_header', 'private_header'):
        if not HEADER.fullmatch(str(result[key])):
            raise ValueError('Invalid EmpireDrop credential header name.')
    if result['public_header'].casefold() == result['private_header'].casefold():
        raise ValueError('Credential headers must be different.')
    # Never let the configuration overwrite sensitive HTTP control headers.
    prohibited = {'authorization', 'host', 'cookie', 'set-cookie', 'content-length',
                  'connection', 'location', 'transfer-encoding', 'proxy-authorization'}
    if any(result[k].casefold() in prohibited for k in ('public_header', 'private_header')):
        raise ValueError('Use the provider-documented API credential headers.')
    for key in ('start_param', 'end_param', 'cursor_param'):
        if not FIELD.fullmatch(str(result[key])):
            raise ValueError('Invalid EmpireDrop query/response field: ' + key)
    for key in ('code_field', 'name_field', 'wager_field', 'next_cursor_field'):
        if not PATH.fullmatch(str(result[key])):
            raise ValueError('Invalid EmpireDrop JSON field path: ' + key)
    for key in ('code_param',):
        if result[key] and not FIELD.fullmatch(str(result[key])):
            raise ValueError('Invalid EmpireDrop query field: ' + key)
    for key in ('user_id_field', 'transaction_id_field', 'rows_path', 'next_cursor_path'):
        if result[key] and not PATH.fullmatch(str(result[key])):
            raise ValueError('Invalid EmpireDrop JSON path: ' + key)
    if result['auth_mode'] not in ('dual_headers', 'private_header', 'public_header', 'bearer_private', 'basic_pair'):
        raise ValueError('Unsupported API authentication mode.')
    if result['http_method'] not in ('GET', 'POST'):
        raise ValueError('Unsupported read-only API HTTP method.')
    if result['request_location'] not in ('query', 'json'):
        raise ValueError('Unsupported parameter location.')
    if result['http_method'] == 'GET' and result['request_location'] != 'query':
        raise ValueError('GET API requests must use query parameters.')
    if result['timestamp_format'] not in ('unix_s', 'unix_ms', 'iso8601_utc'):
        raise ValueError('Unsupported timestamp format.')
    if len({result['start_param'], result['end_param'], result['code_param'] or '__none__'}) != 3:
        raise ValueError('Date and referral-code query parameters must differ.')
    if result['currency'] not in ('EUR', 'USD'):
        raise ValueError('Currency must be EUR or USD, as documented by the provider.')
    try:
        divisor = Decimal(str(result['wager_divisor']))
        if not divisor.is_finite() or not 0 < divisor <= 10**12:
            raise ValueError
    except (InvalidOperation, ValueError):
        raise ValueError('Wager divisor must be a finite positive number.') from None
    if result['record_mode'] not in ('player_total', 'transactions'):
        raise ValueError('Record mode must be aggregated player totals or individual transactions.')
    if result['record_mode'] == 'transactions' and not result['transaction_id_field']:
        raise ValueError('Transaction responses require a unique transaction identifier field.')
    if result['pagination_mode'] not in ('none', 'cursor'):
        raise ValueError('Choose no pagination or provider-verified cursor pagination.')
    if result['pagination_mode'] == 'cursor' and result['cursor_param'] in (result['start_param'], result['end_param'], result['code_param']):
        raise ValueError('Cursor parameter must not overwrite other query parameters.')
    for key in ('code_scoped', 'verified_contract'):
        result[key] = value.get(key) is True  # never interpret the string "false" as true
    return result


def read_path(value, path):
    """Read explicitly configured dotted JSON fields; never evaluate expressions."""
    if not path:
        return value
    for part in path.split('.'):
        if not isinstance(value, dict):
            return None
        value = value.get(part)
    return value


def format_timestamp(seconds, mode):
    if mode == 'unix_s':
        return int(seconds)
    if mode == 'unix_ms':
        return int(seconds) * 1000
    return datetime.fromtimestamp(int(seconds), timezone.utc).isoformat(timespec='seconds').replace('+00:00', 'Z')


def build_auth_headers(opts, keys):
    mode = opts['auth_mode']
    public, private = keys.get('empiredrop_public_key', ''), keys.get('empiredrop_private_key', '')
    if mode == 'dual_headers':
        if not public or not private:
            raise ProviderError('Both EmpireDrop keys are required for the configured auth mode.', kind='configuration')
        return {opts['public_header']: public, opts['private_header']: private}, None
    if mode in ('private_header', 'bearer_private'):
        if not private:
            raise ProviderError('EmpireDrop private key is missing.', kind='configuration')
        if mode == 'bearer_private':
            return {'Authorization': 'Bearer ' + private}, None
        return {opts['private_header']: private}, None
    if mode == 'public_header':
        if not public:
            raise ProviderError('EmpireDrop public key is missing.', kind='configuration')
        return {opts['public_header']: public}, None
    if not public or not private:
        raise ProviderError('Both EmpireDrop keys are required for Basic authentication.', kind='configuration')
    return {}, (public, private)


def extract_page(payload, *, rows_path=""):
    if rows_path:
        rows = read_path(payload, rows_path)
        if not isinstance(rows, list):
            raise ProviderError("EmpireDrop configured rows path is not an array.", kind="format")
        return rows, payload if isinstance(payload, dict) else None
    """Accept known safe envelope shapes, not arbitrary nested number fields."""
    if isinstance(payload, list):
        return payload, None
    if not isinstance(payload, dict):
        raise ProviderError('EmpireDrop returned an unsupported JSON object.', kind='format')
    rows = None
    for key in ('data', 'results', 'leaderboard', 'users', 'items', 'referrals'):
        candidate = payload.get(key)
        if isinstance(candidate, list):
            rows = candidate; break
        if isinstance(candidate, dict):
            for inner in ('rows', 'users', 'items', 'leaderboard', 'data'):
                if isinstance(candidate.get(inner), list):
                    rows = candidate[inner]; break
        if rows is not None:
            break
    if rows is None and isinstance(payload.get('rows'), list):
        rows = payload['rows']
    if rows is None:
        raise ProviderError('EmpireDrop response lacks a valid list of wager records.', kind='format')
    return rows, payload


def parse_rows(payload, *, settings=None, currency=None, divisor=None):
    """Filter to referral `red` and normalize verified wager amounts.

    Aggregated player totals are deduplicated by maximum value, NOT summed.
    Only proven transaction rows with unique transaction IDs are ever summed.
    """
    opts = {**DEFAULTS, **(settings or {})}
    if currency is not None: opts['currency'] = currency
    if divisor is not None: opts['wager_divisor'] = divisor
    opts = validate_settings(opts)
    rows, _ = extract_page(payload, rows_path=opts['rows_path'])
    if len(rows) > MAX_ROWS:
        raise ProviderError('EmpireDrop returned too many records.', kind='format')
    totals, display_names, seen_transactions = {}, {}, set()
    matched_code, valid = False, 0
    for row in rows:
        if not isinstance(row, dict):
            continue
        code = read_path(row, opts['code_field'])
        if code is None:
            if not opts['code_scoped']:
                continue
        elif not isinstance(code, str) or code.strip().casefold() != CODE:
            continue
        matched_code = True
        name, amount = read_path(row, opts['name_field']), read_path(row, opts['wager_field'])
        if not isinstance(name, str) or not name.strip() or len(name.strip()) > 64 or amount is None or isinstance(amount, bool):
            continue
        try:
            wager = Decimal(str(amount)) / Decimal(str(opts['wager_divisor']))
        except (InvalidOperation, ValueError, TypeError, ZeroDivisionError):
            continue
        if not wager.is_finite() or wager < 0 or wager > Decimal('1e18'):
            continue
        user_id = read_path(row, opts['user_id_field']) if opts['user_id_field'] else None
        identity = str(user_id).strip() if isinstance(user_id, (str, int)) and not isinstance(user_id, bool) and str(user_id).strip() else name.strip().casefold()
        if opts['record_mode'] == 'transactions':
            tx = read_path(row, opts['transaction_id_field'])
            if not isinstance(tx, (str, int)) or isinstance(tx, bool) or not str(tx).strip():
                raise ProviderError('A transaction is missing its unique identifier.', kind='format')
            if str(tx) in seen_transactions:
                continue
            seen_transactions.add(str(tx))
            totals[identity] = totals.get(identity, Decimal(0)) + wager
        else:
            totals[identity] = max(totals.get(identity, Decimal(0)), wager)
        display_names.setdefault(identity, name.strip())
        valid += 1
    if rows and matched_code and not valid:
        raise ProviderError('EmpireDrop red records lack valid username or wager fields.', kind='format')
    if rows and not opts['code_scoped'] and not matched_code and not any(
            isinstance(r, dict) and read_path(r, opts['code_field']) is not None for r in rows):
        raise ProviderError('Referral field missing; do not show unverified referral results.', kind='format')
    symbol = '€' if opts['currency'] == 'EUR' else '$'
    winners = sorted(totals, key=lambda key: (-totals[key], display_names[key].casefold()))[:15]
    return [dict(rank=i, username=display_names[key], wager=symbol + format(totals[key], ',.2f'))
            for i, key in enumerate(winners, 1)]


def meta_is_closed(saved):
    meta = saved.get('race_meta') or {}
    return meta.get('is_active') is False


class EmpireDropBoard:
    def __init__(self, config, store):
        self.config, self.store = config, store
        self.lock, self.stop_event, self.wakeup = threading.RLock(), threading.Event(), threading.Event()
        self.thread, self.interval = None, 300  # Provider example: race.cache_duration=300s
        self.saved = store.live('empiredrop') or {}
        self.last_manual, self.queued_at, self.checking = 0.0, 0, False
        self.next_allowed = 0.0
        self.events = None  # Assigned by the app; no sensitive provider payloads are recorded.

    def _settings(self):
        _, admin = self.store.admin()
        return validate_settings({**self.config.empiredrop, **admin.get('empiredrop_api', {})})

    def _race_settings(self):
        """Read the race-specific, non-secret configuration from administrator JSON."""
        _, admin = self.store.admin()
        return validate_race_settings(admin.get('empiredrop_races', {}))

    def _race_api(self):
        """Keys come from server configuration; they never go to the client."""
        return RaceAPI(self._race_settings(), self.config.credentials)

    def discover_races(self):
        """Safe admin-only race catalog and schema metadata (no private key used)."""
        races, shape = self._race_api().discover()
        return {'races': races, 'response_shape': shape, 'count': len(races)}

    def probe_race(self, slug=''):
        """Inspect sanitized field *names* without publishing unverified totals."""
        api = self._race_api()
        # Direct slug inspection also works for scheduled/finished races, which
        # are intentionally absent from EmpireDrop's running-races listing.
        if slug:
            selected = {'slug': slug, 'name': slug}
        else:
            races, _ = api.discover()
            site = self._schedule()
            selected = select_race(races, api.settings,
                                   preferred_start=site['start_time'],
                                   preferred_end=site['end_time'])
        result = api.probe(selected['slug'])
        result['race'] = selected
        result['fields_verified'] = api.settings['race_verified_fields']
        return result

    def _scope(self, site):
        """A race change invalidates a snapshot even within the same local week."""
        settings = self._race_settings()
        if settings['source_mode'] in ('legacy', 'legacy_window'):
            return scope_id(site) + '-' + settings['source_mode']
        # Provider-managed races must NOT reset just because Shuffle/local
        # Tuesday's week changes. A manual slug change still resets the scope.
        payload = [settings['source_mode'], settings['race_slug'],
                   settings['api_base_url'], settings['race_window_policy']]
        return hashlib.sha256(json.dumps(payload).encode('utf-8')).hexdigest()[:24]

    def _fetch_races(self, site):
        """Read documented list/detail API; let EmpireDrop define the race.

        The list contains running races only. A configured slug is fetched
        directly so admins can inspect historical and scheduled races too.
        """
        api = self._race_api()
        recovered_from = ''
        if api.settings['race_slug']:
            selected = {'slug': api.settings['race_slug']}
            try:
                payload = api.details(selected['slug'])
            except ProviderError as exc:
                # A saved slug can become stale when EmpireDrop creates a new
                # weekly race. Only recover when the admin explicitly enabled
                # auto-selection AND exactly one current WAGER/RANKING race is
                # available. Never silently choose between multiple races.
                if not (exc.kind == 'scope' and exc.status == 404 and
                        api.settings['auto_select']):
                    raise
                catalog, _ = api.discover()
                try:
                    fallback = select_race(catalog, {**api.settings, 'race_slug': ''},
                                           preferred_start=site['start_time'],
                                           preferred_end=site['end_time'])
                except ProviderError as selection_error:
                    raise ProviderError(
                        'Saved EmpireDrop slug is unavailable (404). ' +
                        str(selection_error) + ' Update Race API & selection in Admin.',
                        kind='selection', status=404) from None
                if fallback['slug'] == selected['slug']:
                    # The list acknowledges this slug, yet its detail is
                    # inaccessible: do not treat that as a stale selection.
                    raise ProviderError(
                        'EmpireDrop lists this race but its details return 404. '
                        'Verify partner permissions with EmpireDrop support.',
                        kind='scope', status=404) from None
                recovered_from = selected['slug']
                selected = fallback
                payload = api.details(selected['slug'])
                LOG.warning(
                    'EmpireDrop saved slug returned 404; recovered using the sole '
                    'running wager race. Confirm and save its current slug in Admin.')
        else:
            catalog, _ = api.discover()
            selected = select_race(catalog, api.settings,
                                   preferred_start=site['start_time'],
                                   preferred_end=site['end_time'])
            payload = api.details(selected['slug'])
        race = payload.get('race')
        if not isinstance(race, dict) or race.get('slug') != selected['slug']:
            raise ProviderError('EmpireDrop race detail slug does not match selection.', kind='scope')
        start, end = time_value(race.get('start_date')), time_value(race.get('end_date'))
        if not start or not end or start >= end:
            raise ProviderError('Race has invalid documented start_date/end_date.', kind='format')
        if api.settings['race_window_policy'] == 'local':
            # Local schedule may be contiguous [start,end), while EmpireDrop's
            # end_date is inclusive (23:59:59). Accept the 1s boundary difference.
            if start != site['start_time'] or abs(end - site['end_time']) > 1:
                raise ProviderError('EmpireDrop race dates differ from local Tuesday schedule.', kind='window')
        # The OpenAPI says ranking[] is not available for closed races. Empty
        # rankings are valid initially and must not erase a saved closed race.
        rows = normalize_race(payload, api.settings)
        ttl = race.get('cache_duration')
        if type(ttl) is not int or not 0 < ttl <= 86400:
            raise ProviderError('Invalid race.cache_duration from provider.', kind='format')
        engine, category = race.get('engine'), race.get('type')
        metric = 'Tickets' if engine == 'RAFFLE' else ('Deposited' if category == 'DEPOSIT' else 'Wagered')
        meta = {
            'slug': race['slug'], 'name': str(race.get('name') or race['slug'])[:90],
            # Safe metadata only; keys and unmasked player names are not logged.
            'selection': ('recovered' if recovered_from else
                          'configured' if api.settings['race_slug'] else 'automatic'),
            'start_time': start, 'end_time': end,
            'date_policy': api.settings['race_window_policy'],
            'currency': race['currency'],
            'unit': 'TICKETS' if engine == 'RAFFLE' else race['currency'],
            'engine': engine, 'type': category, 'metric': metric,
            'is_active': race.get('is_active') is True,
            'is_locked': payload.get('is_locked') is True,
            'cache_duration': ttl, 'ranks_limit': race.get('ranks_limit'),
            'prize_count': len(payload.get('prizes', [])) if isinstance(payload.get('prizes'), list) else 0,
            'winners_count': len(payload.get('winners', [])) if isinstance(payload.get('winners'), list) else 0,
        }
        # Do not hammer a provider endpoint while its ranking cache is hot.
        self.interval = min(3600, max(60, ttl))
        return rows, meta

    def _fetch_window(self, site):
        """Explicit date-range mode through the documented *deprecated* API.

        Unlike modern races, this route supports arbitrary Unix UTC windows,
        but EmpireDrop may remove it. A retired endpoint produces a visible
        error while preserving any last verified result for this window.
        """
        start = int(site['start_time'])
        end = min(int(site['end_time']), int(time.time()))
        if end <= start:
            raise ProviderError('Custom EmpireDrop race has not started.',kind='window')
        payload = self._race_api().legacy_window(start,end)
        rows, info = normalize_legacy_window(payload,start,end)
        ttl = info['cache_duration']
        if type(ttl) is not int or not 0 < ttl <= 86400:
            raise ProviderError('Invalid EmpireDrop cache duration.',kind='format')
        self.interval = min(3600,max(60,ttl))
        meta = {'slug':'date-window','name':'Custom EmpireDrop wager race',
                'start_time':start,'end_time':int(site['end_time']),
                'currency':info['currency'],'unit':info['currency'],
                'engine':'RANKING','type':'WAGER','metric':'Wagered',
                'is_active':int(time.time()) < int(site['end_time']),
                'cache_duration':ttl,'ranks_limit':len(rows),
                'legacy_window':True, 'date_policy':'custom'}
        return rows, meta

    def _schedule(self, now=None):
        _, admin = self.store.admin()
        return schedule(admin, now)

    def fetch(self, site):
        opts, keys = self._settings(), self.config.credentials
        url = opts['api_url']
        if not url or not opts['verified_contract']:
            raise ProviderError('Official EmpireDrop wager API contract is not verified; configure and confirm it first.', kind='configuration')
        if not opts['code_param'] and not opts['code_scoped']:
            # Allowed only if the response includes a verified per-row code field.
            pass
        now = int(time.time())
        start, end = int(site['start_time']), min(int(site['end_time']), now)
        if end <= start:
            raise ProviderError('EmpireDrop race has not started.', kind='window')
        headers = {'Accept':'application/json', 'User-Agent':'RedHunllef-EmpireDrop/3.0'}
        auth_headers, basic_auth = build_auth_headers(opts, keys)
        headers.update(auth_headers)
        params = {opts['start_param']:format_timestamp(start, opts['timestamp_format']),
                  opts['end_param']:format_timestamp(end, opts['timestamp_format'])}
        if opts['code_param']:
            params[opts['code_param']] = CODE
        rows, cursor, used = [], None, set()
        for page in range(MAX_PAGES):
            query = dict(params)
            if cursor is not None:
                query[opts['cursor_param']] = cursor
            try:
                # Never forward either credential to a redirect destination.
                kwargs = {'headers': headers, 'timeout': (5,20), 'allow_redirects': False,
                          'stream': True}
                if basic_auth:
                    kwargs['auth'] = basic_auth
                if opts['request_location'] == 'json':
                    kwargs['json'] = query
                else:
                    kwargs['params'] = query
                if opts['http_method'] == 'GET':
                    response_context = requests.get(url, **kwargs)
                else:
                    response_context = requests.post(url, **kwargs)
                with response_context as response:
                    status = response.status_code
                    if status in (301, 302, 303, 307, 308):
                        raise ProviderError('EmpireDrop API redirected; credentials were not forwarded.', kind='http', status=status)
                    if status == 429:
                        raise ProviderError('EmpireDrop rate limited the request.', kind='rate_limit', status=status)
                    if status in (401, 403):
                        raise ProviderError('EmpireDrop rejected authentication or affiliate API permissions.', kind='access', status=status)
                    if status != 200:
                        raise ProviderError('EmpireDrop returned HTTP ' + str(status), kind='http', status=status)
                    body = bytearray()
                    for chunk in response.iter_content(65536):
                        body.extend(chunk)
                        if len(body) > 4*1024*1024:
                            raise ProviderError('EmpireDrop response is larger than 4 MB.', kind='format')
                    try:
                        payload = json.loads(body, parse_float=Decimal)
                    except (ValueError, UnicodeError, TypeError):
                        raise ProviderError('EmpireDrop returned invalid JSON.', kind='format') from None
            except requests.RequestException:
                raise ProviderError('EmpireDrop could not be reached.', kind='connection') from None
            part, envelope = extract_page(payload, rows_path=opts['rows_path'])
            rows.extend(part)
            if len(rows) > MAX_ROWS:
                raise ProviderError('More than 10,000 wager records; verify pagination.', kind='format')
            next_cursor = (read_path(envelope, opts['next_cursor_path']) if opts['next_cursor_path']
                           else read_path(envelope, opts['next_cursor_field'])) if envelope else None
            if next_cursor in (None, '', False):
                return parse_rows(rows, settings={**opts, "rows_path": ""})
            if opts['pagination_mode'] != 'cursor':
                raise ProviderError('EmpireDrop returned additional pages; configure documented cursor pagination before publishing.', kind='format')
            if not isinstance(next_cursor, (str, int)) or len(str(next_cursor)) > 512 or str(next_cursor) in used:
                raise ProviderError('EmpireDrop returned an invalid or repeated page cursor.', kind='format')
            cursor = str(next_cursor)
            used.add(cursor)
        raise ProviderError('EmpireDrop pagination exceeded the configured safety limit.', kind='format')

    def check(self):
        began = time.monotonic()
        now = int(time.time())
        site = self._schedule(now)
        scope = self._scope(site)
        with self.lock:
            self.checking = True
        try:
            previous = self.store.live('empiredrop') or {}
            old = previous
            if old.get('scope') != scope:
                old = {'scope':scope, 'rows':[], 'updated_at':0}
            try:
                race_config = self._race_settings()
                if race_config['source_mode'] == 'races':
                    rows, race_meta = self._fetch_races(site)
                elif race_config['source_mode'] == 'legacy_window':
                    rows, race_meta = self._fetch_window(site)
                else:
                    rows, race_meta = self.fetch(site), {}
            except ProviderError as error:
                next_value = {**old, 'attempt_at':now, 'error':str(error)[:220], 'error_kind':error.kind}
                # 429 signals our poll frequency exceeded the provider's policy.
                if error.kind == 'rate_limit':
                    self.interval = min(3600, max(600, self.interval * 2))
                LOG.warning('EmpireDrop check did not finish (%s).', error.kind)
                if self.events:
                    self.events.record('empiredrop','warning' if error.kind=='rate_limit' else 'error',
                                       'api_rate_limited' if error.kind=='rate_limit' else 'refresh_failed',
                                       http_status=error.status, code=error.kind,
                                       duration_ms=round((time.monotonic()-began)*1000))
            else:
                # A closed race stops returning ranking[]. Keep its last
                # verified standings, avoiding a false blank board at close.
                if (not rows and race_meta and not race_meta.get('is_active', True)
                    and (old.get('race_meta') or {}).get('slug') == race_meta.get('slug')
                    and old.get('rows')):
                    rows = old['rows']
                if self.events:
                    self.events.record('empiredrop','success','refresh_ok',count=len(rows),
                                       http_status=200, duration_ms=round((time.monotonic()-began)*1000))
                next_value = {'scope':scope, 'rows':rows, 'updated_at':now,
                              'attempt_at':now, 'error':'', 'error_kind':'',
                              'race_meta':race_meta, 'rewards':self._rewards()}
            # Do not overwrite a newly changed schedule while HTTP was in flight.
            if self._scope(self._schedule()) != scope:
                return old
            with self.lock:
                # Keep the last four *verified* previous race snapshots locally.
                # Failed or partially mapped responses are never archived.
                if (not next_value.get('error') and previous.get('updated_at') and
                    (previous.get('scope') != next_value.get('scope') or
                     (previous.get('race_meta') or {}).get('slug') !=
                     (next_value.get('race_meta') or {}).get('slug'))):
                    history = self.store.live('empiredrop_history') or []
                    if not isinstance(history, list): history = []
                    # Preserve the payout snapshot from the *previous* race,
                    # not whatever the administrator configured for the new one.
                    entry = {k:copy.deepcopy(previous.get(k)) for k in
                             ('scope', 'rows', 'updated_at', 'race_meta','rewards')}
                    history = [entry] + [v for v in history if
                        isinstance(v, dict) and (v.get('scope'), (v.get('race_meta') or {}).get('slug')) !=
                        (entry['scope'], (entry.get('race_meta') or {}).get('slug'))]
                    self.store.publish('empiredrop_history', history[:4])
                self.store.publish('empiredrop', next_value)
                self.saved = next_value
            return next_value
        finally:
            with self.lock:
                self.checking = False

    def _visible(self, site):
        with self.lock:
            value = copy.deepcopy(self.saved)
        if value.get('scope') != self._scope(site):
            value = {'rows':[], 'updated_at':0, 'attempt_at':0, 'error':'', 'error_kind':''}
        return value

    def _published_reward_settings(self):
        _, admin = self.store.admin()
        return validate_rewards(admin.get('empiredrop_rewards', {}))

    def _draft_reward_settings(self):
        _, admin = self.store.admin()
        return validate_rewards(admin.get('empiredrop_rewards_draft',
                                          admin.get('empiredrop_rewards', {})))

    def _rewards(self):
        return rewards_public(self._published_reward_settings())

    def _next_check_at(self):
        """UTC epoch seconds of the next scheduled provider check, if known.

        The worker uses a monotonic clock, so translate its remaining delay
        into wall time only for display. Never imply that a public page poll
        performs an actual EmpireDrop provider request.
        """
        if not self.thread or not self.thread.is_alive():
            return 0
        with self.lock:
            if self.checking:
                return 0
            remaining = max(0, self.next_allowed - time.monotonic())
        return int(time.time() + remaining + 0.999)

    def public_history(self):
        """Four independent, sanitized, previously verified race snapshots."""
        archive = self.store.live('empiredrop_history') or []
        result = []
        for item in archive[:4] if isinstance(archive,list) else []:
            if not isinstance(item,dict): continue
            meta = item.get('race_meta') or {}
            frozen = item.get('rewards') or {}
            try: rewards = rewards_public(frozen)
            except ValueError: rewards = rewards_public({})
            rows = item.get('rows') or []
            visible = [dict(rank=x['rank'],username=mask_public_username(x['username']),wager=x['wager'])
                       for x in rows[:EMPIRE_PLACES] if isinstance(x,dict) and all(k in x for k in ('rank','username','wager'))]
            result.append({'name':str(meta.get('name') or meta.get('slug') or 'Previous race')[:90],
                           'slug':str(meta.get('slug') or '')[:100],
                           'start_time':meta.get('start_time') or 0,
                           'end_time':meta.get('end_time') or 0,
                           'updated_at':item.get('updated_at') or 0,
                           'rows':list(payout_for_rows(visible,rewards)),
                           'prizes':{'enabled':rewards['enabled'],'total':rewards['total']}})
        return result

    def public(self, unused_shuffle_site=None):
        """Allowlisted public projection: independent prizes and name masking."""
        site = self._schedule()
        saved = self._visible(site)
        rows = saved.get('rows', [])[:EMPIRE_PLACES]
        error = saved.get('error', '')
        label = ('Updates delayed · last verified results' if error and rows else
                 'Race ended · last verified standings (not a payout confirmation)' if rows and meta_is_closed(saved) else
                 'Source unavailable · ' + error if error else
                 'Updated · EmpireDrop race' if saved.get('updated_at') else
                 'Awaiting EmpireDrop race standings')
        race_settings = self._race_settings()
        source = race_settings['source_mode']
        meta = saved.get('race_meta') or {}
        # The selected slug remains authoritative for standings. The independent
        # website schedule controls only the public countdown and presentation,
        # so admins can use the same Eastern calendar workflow as Shuffle. The
        # provider window remains available for comparison and one-click sync.
        display_schedule = {k:site[k] for k in ('start_time','end_time','start_et','end_et','mode')}
        if source == 'races' and race_settings['race_window_policy'] == 'provider':
            valid = bool(meta.get('start_time') and meta.get('end_time'))
            display_schedule.update(
                mode='provider',
                display_mode='local',
                provider_start_time=meta['start_time'] if valid else 0,
                provider_end_time=meta['end_time'] if valid else 0,
                provider_start_et=fmt_et(meta['start_time']) if valid else '',
                provider_end_et=fmt_et(meta['end_time']) if valid else '',
            )
        rewards = self._rewards()
        visible = [dict(rank=r['rank'], username=mask_public_username(r['username']),wager=r['wager']) for r in rows]
        visible = list(payout_for_rows(visible,rewards))
        return {'rows':visible, 'prizes':rewards,
                'label':label[:260], 'updated_at':saved.get('updated_at',0),
                'currency':meta.get('currency',race_settings['race_currency']) if source!='legacy' else self._settings()['currency'],
                'referral_url':REFERRAL_URL, 'race_meta':meta, 'source_mode':source,
                'schedule':display_schedule, 'code':CODE,
                # This is the *actual worker schedule*, not the browser's 60s poll.
                # It updates after provider cache TTL and rate-limit backoff.
                'refresh_interval':self.interval,
                'next_check_at':self._next_check_at(),
                'attempt_at':saved.get('attempt_at',0),
                'history':self.public_history()}

    def private_status(self, unused_shuffle_site=None):
        site, opts = self._schedule(), self._settings()
        snapshot = self._visible(site)
        state = self.public()
        state.update(rows=list(payout_for_rows(
                         [dict(rank=r['rank'], username=r['username'], user_id=r.get('user_id',''), wager=r['wager']) for r in snapshot.get('rows',[])[:EMPIRE_PLACES]],
                         self._rewards())),
                     attempt_at=snapshot.get('attempt_at',0), error=snapshot.get('error',''),
                     error_kind=snapshot.get('error_kind',''), configuration=opts,
                     schedule={**state['schedule'], 'start_input':site['start_input'], 'end_input':site['end_input']},
                     configured={key:{'configured':bool(self.config.credentials.get(key)),
                                      'source':self.config.sources.get(key,'missing'),
                                      'masked':('••••'+self.config.credentials[key][-4:] if self.config.credentials.get(key) else '')}
                                 for key in ('empiredrop_public_key','empiredrop_private_key')},
                     # These were missing in the previous package, even
                     # though the Jinja template required them. A missing
                     # race_configuration caused admin page rendering errors.
                     race_configuration=self._race_settings(),
                     selection_warning=(
                         'The saved race slug returned 404. The worker recovered '
                         'the only running wager race; save its new slug or clear '
                         'the saved slug for future automatic selection.'
                         if (snapshot.get('race_meta') or {}).get('selection') == 'recovered'
                         else ''),
                     race_history=(self.store.live('empiredrop_history') or [])[:4],
                     private_rewards={**rewards_public(self._draft_reward_settings()),
                         'revision': self._draft_reward_settings()['revision'],
                         'updated_at': self._draft_reward_settings()['updated_at'],
                         'updated_by': self._draft_reward_settings()['updated_by'],
                         'published': self._draft_reward_settings() == self._published_reward_settings(),
                         'published_total': self._rewards()['total'],
                         'published_enabled': self._rewards()['enabled']},
                     refresh_interval=self.interval,
                     running=bool(self.thread and self.thread.is_alive()),
                     checking=self.checking, queued_at=self.queued_at)
        return state

    def request_refresh(self):
        with self.lock:
            # A race slug or source-mode change is new data, not a re-poll of
            # the old cached ranking. Allow the worker to fetch the new scope
            # immediately instead of waiting the old race's cache TTL.
            scope_changed = self.saved.get('scope') != self._scope(self._schedule())
            if not scope_changed and time.monotonic() - self.last_manual < 15:
                return False
            if scope_changed:
                self.next_allowed = 0.0
            self.last_manual, self.queued_at = time.monotonic(), int(time.time())
            self.wakeup.set()
            return True

    def _loop(self):
        # Manual refreshes coalesce, and do NOT bypass the provider's cached
        # minimum interval. This prevents repeated API calls with identical data.
        while not self.stop_event.is_set():
            remaining = max(0.0, self.next_allowed - time.monotonic())
            if remaining:
                self.wakeup.wait(min(remaining, 5))
                self.wakeup.clear()
                continue
            try:
                self.check()
            except Exception:
                LOG.exception('EmpireDrop local worker failure (no credential data logged).')
            self.next_allowed = time.monotonic() + max(60,self.interval)
            # A manual wakeup will be processed when the cache interval elapses.
            self.wakeup.wait(min(self.interval,5))
            self.wakeup.clear()

    def start(self):
        with self.lock:
            if self.thread is None or not self.thread.is_alive():
                self.stop_event.clear()
                self.thread = threading.Thread(target=self._loop, name='empiredrop-updates', daemon=True)
                self.thread.start()

    def stop(self):
        self.stop_event.set(); self.wakeup.set()
        if self.thread and self.thread.is_alive():
            self.thread.join(timeout=1)
```

## `empiredrop_deploy_keys.py`

```python
"""SERVER ONLY: EmpireDrop production API keys for PRIVATE Git deployments.

Contains user-supplied production credentials. Never serve/import this module
in browser assets, publish the repository, or print credentials in logs.
Rotate the key pair if the repository has ever been public. Environment
variables (EMPIREDROP_PUBLIC_KEY / EMPIREDROP_PRIVATE_KEY) override these.
"""
EMPIREDROP_KEYS = {'empiredrop_private_key': 'sk_prod_fBy8TMvWoU4d3s4B9SYjrjBtV90jTGQVcgRdSvFp', 'empiredrop_public_key': 'pk_prod_fIjbtQOdrbVqL8TrUrghtiHMRHy1yG1r'}
```

## `empiredrop_features.py`

```python
"""Independent EmpireDrop rewards and public-name presentation.

These are *advertised local prizes*, not confirmed provider payouts or
payment instructions. Shuffle's settings are never copied implicitly.
"""
from collections import Counter, defaultdict
from decimal import Decimal, InvalidOperation
import re

# EmpireDrop advertises ten local payout positions; Shuffle remains Top 15.
EMPIRE_PLACES = 10
DEFAULT_REWARDS = {'currency': 'EUR', 'enabled': False,
                   'prizes': {str(i): '0.00' for i in range(1, EMPIRE_PLACES + 1)},
                   'revision': 1, 'updated_at': 0, 'updated_by': ''}
CURRENCY_SIGNS = {'EUR': '€', 'USD': '$'}
_AMOUNT = re.compile(r'^(?:\d{1,7})(?:\.\d{1,2})?$')


def validate_rewards(value):
    """Reject negative/oversized/ambiguous payouts before saving any state.

    Private revision/audit metadata is validated here but stripped by the public
    projection. Old exports without metadata are upgraded additively.
    """
    if not isinstance(value, dict) or set(value) - {'currency', 'enabled', 'prizes', 'revision', 'updated_at', 'updated_by'}:
        raise ValueError('Invalid EmpireDrop payout settings.')
    currency = value.get('currency', 'EUR')
    if currency not in CURRENCY_SIGNS:
        raise ValueError('Choose EUR or USD for EmpireDrop rewards.')
    prizes = value.get('prizes', DEFAULT_REWARDS['prizes'])
    if not isinstance(prizes, dict) or set(prizes) not in (
        set(DEFAULT_REWARDS['prizes']), {str(i) for i in range(1, 16)}
    ):
        raise ValueError('Provide a payout for every position from 1 to 10.')
    # Accept old 15-place JSON exports but normalize to the new ten places.
    # Old places 11-15 are not advertised and never enter the new prize pool.
    result = {}
    for key in DEFAULT_REWARDS['prizes']:
        val = str(prizes[key]).strip()
        if not _AMOUNT.fullmatch(val):
            raise ValueError('Place ' + key + ': use a non-negative amount with at most two decimal places.')
        amt = Decimal(val)
        if amt > Decimal('1000000'):
            raise ValueError('Place ' + key + ': payout cannot exceed 1,000,000.')
        result[key] = f'{amt:.2f}'
    revision = value.get('revision', 1)
    updated_at = value.get('updated_at', 0)
    updated_by = value.get('updated_by', '')
    if type(revision) is not int or revision < 1 or revision > 2**31-1:
        raise ValueError('Invalid EmpireDrop payout revision.')
    if type(updated_at) is not int or not 0 <= updated_at <= 4102444799:
        raise ValueError('Invalid EmpireDrop payout timestamp.')
    if not isinstance(updated_by, str) or len(updated_by) > 64 or not updated_by.isprintable():
        raise ValueError('Invalid EmpireDrop payout editor.')
    return {'currency': currency, 'enabled': value.get('enabled') is True, 'prizes': result,
            'revision': revision, 'updated_at': updated_at, 'updated_by': updated_by}



def resolve_reward_save_mode(form):
    """Return the administrator's explicit payout action.

    Browsers omit disabled submit buttons from native form serialization. The
    payout UI disables both buttons immediately to prevent double clicks, so
    JavaScript also writes ``save_mode_intent`` before disabling them. Prefer
    that durable intent while retaining the normal submit-button value as the
    no-JavaScript fallback.
    """
    intent = str(form.get('save_mode_intent') or '').strip().lower()
    button = str(form.get('save_mode') or '').strip().lower()
    mode = intent or button or 'draft'
    if mode not in {'draft', 'publish'}:
        raise ValueError('Choose Save draft or Save and publish.')
    return mode

def format_reward(value, currency):
    return CURRENCY_SIGNS[currency] + f'{Decimal(str(value)):,.2f}'


def rewards_public(raw):
    """Only prize amounts and currency are public, never admin metadata."""
    value = validate_rewards(raw if raw else {})
    pool = sum((Decimal(v) for v in value['prizes'].values()), Decimal(0))
    return {'currency': value['currency'], 'enabled': value['enabled'],
            'prizes': value['prizes'], 'total': format_reward(pool, value['currency']),
            'formatted': {k: format_reward(v, value['currency']) for k, v in value['prizes'].items()}}


def payout_for_rows(rows, rewards):
    """Per-player advertised reward by *provider rank*, split evenly on ties.

    EmpireDrop's ranking may skip ranks after ties. We do not renumber its
    official results, and we do not imply that a prize has been paid.
    """
    count = Counter(row.get('rank') for row in rows)
    observed = defaultdict(int)
    for row in rows:
        rank = row.get('rank')
        val = rewards['prizes'].get(str(rank))
        if rewards['enabled'] and val is not None and count[rank] > 0:
            # Divide *integer cents* and distribute any leftover cents in
            # provider order, so displayed shares always sum to the rank prize.
            cents = int(Decimal(val) * 100)
            base, extra = divmod(cents, count[rank])
            share = base + int(observed[rank] < extra)
            observed[rank] += 1
            yield {**row, 'prize': format_reward(Decimal(share) / 100, rewards['currency'])}
        else:
            yield {**row, 'prize': '—'}


def mask_public_username(name):
    """Display exactly two prefix *slots* and six trailing asterisks.

    The partner API anonymizes ``user.name`` before we receive it. The second
    character of ``s********z`` is a provider mask, NOT a known letter. Using
    the raw first two characters would render ``s*******`` (seven asterisks)
    rather than the public board's consistent eight-character display.

    Use a visible bullet for a character the provider has already hidden.
    Example: ``s********z`` -> ``s•******``; ``Re********tie`` -> ``Re******``.
    Never search for visible suffix characters to invent an unmasked prefix.
    Admin keeps the original, provider-masked name for reference.
    """
    clean = str(name or '').strip()
    masked = {'*', '＊', '•', '●', '∙', '·'}
    prefix = []
    for position in (0, 1):
        char = clean[position] if position < len(clean) else ''
        prefix.append('•' if not char or char in masked or not char.isprintable() else char)
    return ''.join(prefix) + '******'
```

## `empiredrop_races.py`

```python
"""Official EmpireDrop Partner Public API v2.0.1.

Source of truth: ``openapi.yaml`` supplied with this release.
Production host: https://api.empiredrop.com
GET /api/v1/affiliate-partner/races         -> currently running races, NO ranking
GET /api/v1/affiliate-partner/races/{slug}  -> race + ranking + prizes/winners

Every current request requires BOTH X-Public-Key and X-Private-Key. The
legacy /api/v1/race/affiliates/{publicKey} route is DEPRECATED and not used.
No browser code should call these endpoints or receive API credentials.
"""
from __future__ import annotations

from datetime import datetime
from decimal import Decimal, InvalidOperation
import json
import logging
import re
import time
from urllib.parse import quote

import requests
from integrations import ProviderError

LOG = logging.getLogger('redhunllef.empiredrop.races')
API_ORIGIN = 'https://api.empiredrop.com'
LIST_PATH = '/api/v1/affiliate-partner/races'
DETAIL_PATH = '/api/v1/affiliate-partner/races/{slug}'
LEGACY_PATH = '/api/v1/race/affiliates/{publicKey}'  # Deprecated: explicit dates only
# Compatibility alias for historical code/tests. Never used as discovery.
DISCOVER_PATH = LIST_PATH
SLUG = re.compile(r'^[A-Za-z0-9][A-Za-z0-9_-]{0,99}$')
ISO_CURRENCY = re.compile(r'^[A-Z]{3}$')

# The former admin settings assumed an undocumented response shape. These
# settings now reflect the exact OpenAPI request/response schema, and old saved
# values are migrated in memory on read (no live JSON account data is erased).
RACE_DEFAULTS = {
    'source_mode': 'races',
    'api_base_url': API_ORIGIN,
    'race_slug': '',
    'auto_select': True,
    'race_auth_mode': 'dual_headers',
    'race_private_header': 'X-Private-Key',
    'race_public_header': 'X-Public-Key',
    'race_rows_path': 'ranking',
    'race_name_field': 'user.name',
    'race_user_id_field': 'user.hash_id',
    'race_wager_field': 'total',
    'race_currency': 'EUR',  # Actual unit comes from race.currency / ranking[].unit.
    'race_wager_divisor': '100',  # Minor units for EUR and USD (not raffle tickets).
    'race_window_policy': 'provider',
    'race_start_field': 'race.start_date',
    'race_end_field': 'race.end_date',
    'race_verified_fields': True,  # Checked against the supplied OpenAPI spec.
}
RACE_EDITABLE = frozenset(RACE_DEFAULTS)
# ISO 4217 minor-unit exceptions used to avoid pretending all currencies have 2 decimals.
# Add currencies only after verifying the provider's supported currency list.
CURRENCY_DECIMALS = {'EUR': 2, 'USD': 2, 'GBP': 2, 'CAD': 2, 'AUD': 2,
                     'JPY': 0, 'KRW': 0, 'KWD': 3, 'BHD': 3}
CURRENCY_SYMBOLS = {'EUR': '€', 'USD': '$', 'GBP': '£', 'CAD': 'CA$', 'AUD': 'A$'}


def validate_race_settings(candidate):
    """Migrate old admin mapping/auth settings to the documented contract.

    The only meaningful race controls are source mode, slug, active-race auto
    selection and reporting-period policy. Old 'none' authentication cannot
    override the mandatory dual-header OpenAPI security scheme.
    """
    if not isinstance(candidate, dict) or set(candidate) - RACE_EDITABLE:
        raise ValueError('Unexpected EmpireDrop race configuration setting.')
    settings = dict(RACE_DEFAULTS)
    for key in ('source_mode', 'race_slug', 'auto_select', 'race_window_policy'):
        if key in candidate:
            settings[key] = candidate[key]
    settings['source_mode'] = str(settings['source_mode']).lower()
    if settings['source_mode'] not in ('races', 'legacy', 'legacy_window'):
        raise ValueError('Choose the official race API or legacy integration.')
    settings['race_slug'] = str(settings['race_slug']).strip()
    if settings['race_slug'] and not SLUG.fullmatch(settings['race_slug']):
        raise ValueError('Race slug contains unsupported characters.')
    settings['auto_select'] = settings['auto_select'] is True
    if settings['race_window_policy'] not in ('provider', 'local'):
        raise ValueError('Choose provider or local date matching.')
    # Current partner races own their reporting window. Local dates remain in
    # the admin record for display/backup, but must not reject valid provider
    # standings or switch the application to the deprecated endpoint.
    if settings['source_mode'] == 'races':
        settings['race_window_policy'] = 'provider'
    return settings


def time_value(value):
    """Convert the documented UTC ISO 8601 race dates into Unix seconds."""
    if not isinstance(value, str):
        return None
    try:
        dt = datetime.fromisoformat(value.replace('Z', '+00:00'))
        return int(dt.timestamp()) if dt.tzinfo else None
    except (ValueError, OverflowError):
        return None


def keys_only(value, depth=0):
    """Describe nested schema without disclosing player values or secrets."""
    if depth >= 5:
        return {'type': type(value).__name__}
    if isinstance(value, list):
        return {'type': 'array', 'items': len(value),
                'first': keys_only(value[0], depth + 1) if value else None}
    if isinstance(value, dict):
        return {'type': 'object', 'fields': {
            str(k)[:70]: keys_only(v, depth + 1)
            for k, v in list(value.items())[:40]}}
    return {'type': type(value).__name__}


def race_catalog(payload):
    """Parse the documented {"races": [Race,...]} *running races* list."""
    if not isinstance(payload, dict) or not isinstance(payload.get('races'), list):
        raise ProviderError('EmpireDrop race list must contain races[].', kind='format')
    items = payload['races']
    if len(items) > 500:
        raise ProviderError('EmpireDrop returned too many races.', kind='format')
    output, slugs = [], set()
    for item in items:
        if not isinstance(item, dict):
            continue
        slug = item.get('slug')
        if not isinstance(slug, str) or not SLUG.fullmatch(slug) or slug in slugs:
            continue
        slugs.add(slug)
        output.append({
            'slug': slug,
            'name': str(item.get('name') or slug)[:90],
            'start_time': time_value(item.get('start_date')),
            'end_time': time_value(item.get('end_date')),
            'is_active': item.get('is_active') is True,
            'type': item.get('type'),
            'engine': item.get('engine'),
            'currency': item.get('currency'),
            'cache_duration': item.get('cache_duration'),
            'ranks_limit': item.get('ranks_limit'),
        })
    if items and not output:
        raise ProviderError('Race list contains no valid race slugs.', kind='format')
    return output


def select_race(races, options, now=None, preferred_start=0, preferred_end=0):
    """Select the intended running wager race without guessing blindly.

    An explicit slug always wins. With automatic selection enabled, a single
    active WAGER/RANKING race is selected immediately. When EmpireDrop returns
    multiple active wager races, prefer the unique race whose provider dates
    match (or are closest to) the saved local November window. This keeps the
    official slug-based rankings working after a redeploy that lost the saved
    slug, while still refusing an ambiguous tie.
    """
    settings = validate_race_settings(options)
    if settings['race_slug']:
        return next((race for race in races if race['slug'] == settings['race_slug']),
                    {'slug': settings['race_slug'], 'name': settings['race_slug']})
    if not settings['auto_select']:
        raise ProviderError('Select an EmpireDrop race slug or enable automatic selection.', kind='selection')
    eligible = [item for item in races if item['is_active'] and
                item['type'] == 'WAGER' and item['engine'] == 'RANKING']
    if not eligible:
        raise ProviderError(
            'No active WAGER/RANKING EmpireDrop races are available. '
            'Check the partner dashboard or select a valid race slug in Admin.',
            kind='selection')
    if len(eligible) == 1:
        return eligible[0]

    start = int(preferred_start or 0)
    end = int(preferred_end or 0)
    if 0 < start < end:
        exact = [race for race in eligible
                 if race.get('start_time') == start and
                 abs(int(race.get('end_time') or 0) - end) <= 1]
        if len(exact) == 1:
            return exact[0]

        scored = []
        for race in eligible:
            race_start = int(race.get('start_time') or 0)
            race_end = int(race.get('end_time') or 0)
            if not (0 < race_start < race_end):
                continue
            overlaps = race_start < end and race_end >= start
            score = (0 if overlaps else 10**12) + abs(race_start - start) + abs(race_end - end)
            scored.append((score, race['slug'], race))
        scored.sort(key=lambda item: (item[0], item[1]))
        if scored and (len(scored) == 1 or scored[0][0] < scored[1][0]):
            return scored[0][2]

    raise ProviderError(
        'Multiple active wager races exist and no unique date match was found; '
        'select the intended slug in Admin.', kind='selection')


def extract_race_rows(payload, unused_path=''):
    """Current API: ranking[] only. Empty lists are legitimate for new/closed races."""
    if not isinstance(payload, dict) or not isinstance(payload.get('ranking'), list):
        raise ProviderError('EmpireDrop race detail must contain ranking[].', kind='format')
    return payload['ranking']


def _amount(value, currency):
    """Convert integer minor units, not a formatted total_value string."""
    if isinstance(value, bool) or not isinstance(value, int) or value < 0 or value > 10**18:
        raise ProviderError('Invalid ranking total: expected nonnegative integer minor units.', kind='format')
    if currency not in CURRENCY_DECIMALS:
        raise ProviderError('Unknown currency minor-unit precision: ' + str(currency)[:8], kind='format')
    places = CURRENCY_DECIMALS[currency]
    val = Decimal(value) / (Decimal(10) ** places)
    symbol = CURRENCY_SYMBOLS.get(currency, currency + ' ')
    return symbol + format(val, ',.' + str(places) + 'f')


def normalize_race(payload, settings=None):
    """Translate the OpenAPI RaceDetail ranking, including provider tie ranks.

    RANKING + WAGER => money wagered; RANKING + DEPOSIT => money deposited;
    RAFFLE => tickets, *not* currency. No invented wager weighting is applied.
    """
    validate_race_settings(settings or {})  # retained as an API compatibility check
    if not isinstance(payload, dict) or not isinstance(payload.get('race'), dict):
        raise ProviderError('EmpireDrop detail is missing race{}.', kind='format')
    race = payload['race']
    engine, category = race.get('engine'), race.get('type')
    currency = race.get('currency')
    if engine not in ('RANKING', 'RAFFLE') or category not in ('WAGER', 'DEPOSIT'):
        raise ProviderError('Unrecognized EmpireDrop race engine/type.', kind='format')
    if not isinstance(currency, str) or not ISO_CURRENCY.fullmatch(currency):
        raise ProviderError('Invalid EmpireDrop race currency.', kind='format')
    rows = extract_race_rows(payload)
    if len(rows) > 10000:
        raise ProviderError('Too many ranked players.', kind='format')
    output, seen = [], set()
    for row in rows:
        if not isinstance(row, dict) or not isinstance(row.get('user'), dict):
            raise ProviderError('Malformed EmpireDrop ranking entry.', kind='format')
        user = row['user']
        user_id, username = user.get('hash_id'), user.get('name')
        rank, total, unit = row.get('rank'), row.get('total'), row.get('unit')
        if not isinstance(username, str) or not username.strip() or len(username) > 100:
            raise ProviderError('Missing EmpireDrop ranked display name.', kind='format')
        if not isinstance(user_id, str) or not user_id.strip():
            raise ProviderError('Missing stable EmpireDrop user.hash_id.', kind='format')
        if type(rank) is not int or rank < 1:
            raise ProviderError('Invalid EmpireDrop rank.', kind='format')
        if user_id in seen:
            raise ProviderError('Repeated EmpireDrop user in ranking.', kind='format')
        seen.add(user_id)
        if engine == 'RAFFLE':
            if unit != 'TICKETS' or type(total) is not int or total < 0:
                raise ProviderError('Expected TICKETS unit and integer ticket total.', kind='format')
            display = f'{total:,} tickets'
        else:
            if unit != currency:
                raise ProviderError('Ranking unit differs from race.currency.', kind='format')
            display = _amount(total, currency)
        # The provider already anonymizes user.name. Never show Steam IDs.
        # Public projections strip user_id; it remains valuable to admins
        # because EmpireDrop anonymizes the name before sending it.
        output.append({'rank': rank, 'username': username.strip(), 'user_id':user_id, 'wager': display})
    limit = race.get('ranks_limit')
    if type(limit) is int and limit >= 0 and len(output) > limit:
        raise ProviderError('Ranking contains more players than race.ranks_limit.', kind='format')
    return output[:15]


class RaceAPI:
    """Read-only HTTP client with mandatory two-key auth and no redirects."""
    def __init__(self, options, credentials, requester=None):
        self.settings = validate_race_settings(options)
        self.credentials = credentials
        self.requester = requester or requests

    def _get(self, suffix, *, params=None, deprecated=False):
        public = str(self.credentials.get('empiredrop_public_key') or '').strip()
        secret = str(self.credentials.get('empiredrop_private_key') or '').strip()
        if not public or not secret:
            raise ProviderError('Both EmpireDrop production keys are required.', kind='configuration')
        headers = {
            'Accept': 'application/json',
            'User-Agent': 'RedHunllef-EmpireDrop-OpenAPI-2.0.1',
            'X-Private-Key': secret,
        }
        # OpenAPI marks the deprecated path as ApiKeyAuth (private header only).
        # The identifier is already in that endpoint's URL path.
        if not deprecated:
            headers['X-Public-Key'] = public
        try:
            # Only hard-coded provider origin and path prefixes can receive keys.
            with self.requester.get(API_ORIGIN + suffix, headers=headers, params=params,
                                    timeout=(5, 20), stream=True,
                                    allow_redirects=False) as response:
                code = response.status_code
                if code in (301, 302, 303, 307, 308):
                    raise ProviderError('EmpireDrop redirected an authenticated request; refused.', kind='redirect', status=code)
                if code == 401:
                    raise ProviderError('EmpireDrop 401: both API keys must be present.', kind='access', status=code)
                if code == 403:
                    raise ProviderError('EmpireDrop 403: invalid key pair or disallowed server outbound IP.', kind='access', status=code)
                if code == 404:
                    raise ProviderError('EmpireDrop 404: race slug not found or not owned by partner.', kind='scope', status=code)
                if code == 429:
                    raise ProviderError('EmpireDrop 429: rate limit; respect race.cache_duration.', kind='rate_limit', status=code)
                if code != 200:
                    raise ProviderError('EmpireDrop race API returned HTTP ' + str(code), kind='http', status=code)
                body = bytearray()
                for block in response.iter_content(65536):
                    body.extend(block)
                    if len(body) > 4 * 1024 * 1024:
                        raise ProviderError('EmpireDrop response exceeds the 4 MB limit.', kind='format')
                try:
                    result = json.loads(body)
                except (ValueError, UnicodeError, TypeError):
                    raise ProviderError('EmpireDrop returned invalid JSON.', kind='format') from None
                if not isinstance(result, dict):
                    raise ProviderError('EmpireDrop returned a non-object JSON response.', kind='format')
                return result
        except requests.RequestException:
            # Do not include exception URLs/headers; they can leak API metadata.
            raise ProviderError('EmpireDrop network connection failed.', kind='connection') from None

    def discover(self):
        payload = self._get(LIST_PATH)
        return race_catalog(payload), keys_only(payload)

    def details(self, slug):
        if not isinstance(slug, str) or not SLUG.fullmatch(slug):
            raise ProviderError('Invalid race slug.', kind='configuration')
        return self._get(DETAIL_PATH.format(slug=quote(slug, safe='')))

    def probe(self, slug):
        payload = self.details(slug)
        rows = extract_race_rows(payload)
        return {
            'race_slug': slug,
            'structure': keys_only(payload),
            'sample_row_fields': keys_only(rows[0]) if rows else None,
            'participant_rows': len(rows),
            'race': keys_only(payload.get('race', {})),
            'mapping_warning': '',
        }

    def legacy_window(self, start, end):
        """Deprecated endpoint: explicitly scoped Unix UTC timestamp window.

        Current slug-based races cannot change their official dates. This is
        provided as an opt-in compatibility path for custom/weekly schedules.
        Do not mistake the returned rankings for official active race results.
        """
        public = str(self.credentials.get('empiredrop_public_key') or '').strip()
        if not public or not 0 < int(start) < int(end):
            raise ProviderError('A public key and valid start/end dates are required.',kind='configuration')
        return self._get(LEGACY_PATH.format(publicKey=quote(public, safe='')),
                         params={'start_timestamp': int(start), 'end_timestamp': int(end)},
                         deprecated=True)


def normalize_legacy_window(payload, start, end):
    """Normalize the documented deprecated ranking[].currency shape.

    rank/total/user are identical to the modern ranking shape, except for
    currency instead of unit. Retain the provider's displayed rank and avoid
    guessing monetary units from total_value (which is formatted text).
    """
    if not isinstance(payload,dict) or not isinstance(payload.get('ranking'),list):
        raise ProviderError('Deprecated race API must return ranking[].',kind='format')
    ranking = payload['ranking']
    units = {r.get('currency') for r in ranking if isinstance(r,dict)}
    if len(units)>1:
        raise ProviderError('Deprecated ranking contains mixed currencies.',kind='format')
    currency = next(iter(units),'EUR')
    if currency not in CURRENCY_DECIMALS:
        raise ProviderError('Unsupported currency in deprecated ranking.',kind='format')
    translated = [{**r,'unit':r.get('currency')} for r in ranking]
    race = {'name':'Custom EmpireDrop wager race','slug':'date-window',
            'engine':'RANKING','type':'WAGER','currency':currency,
            'ranks_limit':max(15,len(translated)),
            'cache_duration':payload.get('cache_duration',300),
            'is_active':True}
    return normalize_race({'race':race,'ranking':translated}),race
```

## `fairness.py`

```python
"""Versioned RedPoints: deterministic games and exact, published payout calculations.

No HTTP, player records or mutable state live here. A one-time server seed is
committed before each bet and revealed with its receipt. The browser verifier
implements this same specification independently with Web Crypto and BigInt.
"""
from fractions import Fraction
from functools import lru_cache
import hashlib
import hmac
import json
from math import comb
import re

VERSION = 'redpoints-v5'
V4_VERSION = 'redpoints-v4'
V2_VERSION = 'redpoints-v2'
V3_VERSION = 'redpoints-v3'
LEGACY_VERSION = 'redpoints-v1'
SUPPORTED_VERSIONS = (LEGACY_VERSION, V2_VERSION, V3_VERSION, V4_VERSION, VERSION)
BLACKJACK_VERSIONS = (V2_VERSION, V3_VERSION, V4_VERSION, VERSION)
POKER_VERSIONS = (V3_VERSION, V4_VERSION, VERSION)
GAMES = ('dice', 'keno', 'plinko', 'blackjack', 'limbo', 'coinflip', 'poker', 'baccarat')
RISKS = ('low', 'medium', 'high')
SCALE = 10000

# Fixed, symmetric v2 Plinko paytables, stored as exact 1/10,000 units.
# The highest edge multiplier is 1000x on the 16-row High board.
# v1 tables remain available below to verify all earlier receipts.
PLINKO_TABLES = {
    8: {
        'low': (56000, 21000, 11000, 10000, 5000, 10000, 11000, 21000, 56000),
        'medium': (130000, 30000, 13000, 7000, 4000, 7000, 13000, 30000, 130000),
        'high': (290000, 40000, 15000, 3000, 2000, 3000, 15000, 40000, 290000),
    },
    12: {
        'low': (100000, 30000, 16000, 14000, 11000, 10000, 5000, 10000, 11000, 14000, 16000, 30000, 100000),
        'medium': (330000, 110000, 40000, 20000, 11000, 6000, 3000, 6000, 11000, 20000, 40000, 110000, 330000),
        'high': (1700000, 240000, 81000, 20000, 7000, 2000, 2000, 2000, 7000, 20000, 81000, 240000, 1700000),
    },
    16: {
        'low': (160000, 90000, 20000, 14000, 14000, 12000, 11000, 10000, 5000, 10000, 11000, 12000, 14000, 14000, 20000, 90000, 160000),
        'medium': (1100000, 410000, 100000, 50000, 30000, 15000, 10000, 5000, 3000, 5000, 10000, 15000, 30000, 50000, 100000, 410000, 1100000),
        'high': (10000000, 1300000, 260000, 90000, 40000, 20000, 2000, 2000, 2000, 2000, 2000, 20000, 40000, 90000, 260000, 1300000, 10000000),
    },
}


def commitment(seed):
    return hashlib.sha256(bytes.fromhex(seed)).hexdigest()


def options_for(game, value):
    if not isinstance(value, dict):
        raise ValueError('Choose valid game settings.')
    if game == 'dice':
        chance, side = value.get('chance'), value.get('side')
        if type(chance) is not int or not 1 <= chance <= 95 or side not in {'under', 'over'}:
            raise ValueError('Choose a win chance from 1 to 95 and Roll under or Roll over.')
        return dict(chance=chance, side=side)
    if game == 'blackjack':
        if type(value.get('decks')) is not int or value['decks'] != 6:
            raise ValueError('Blackjack uses six decks.')
        return dict(decks=6)
    if game == 'baccarat':
        if type(value.get('decks')) is not int or value['decks'] != 8 or value.get('side') not in ('player', 'banker', 'tie'):
            raise ValueError('Choose Player, Banker or Tie. Baccarat uses eight decks.')
        return dict(decks=8, side=value['side'])
    if game == 'limbo':
        target = value.get('target')
        if type(target) is not int or not 101 <= target <= 100_000_000:
            raise ValueError('Choose a Limbo target from 1.01x to 1,000,000.00x, in 0.01 steps.')
        return dict(target=target)  # Hundredths, never binary floating-point money.
    if game == 'coinflip':
        if value.get('side') not in ('heads', 'tails'):
            raise ValueError('Choose Heads or Tails.')
        return dict(side=value['side'])
    if game == 'poker':
        if value.get('variant') == 'jacks_or_better':
            return dict(variant='jacks_or_better')  # Archived hands only.
        if value.get('variant') == 'texas_holdem' and value.get('button') in ('player', 'computer'):
            return dict(variant='texas_holdem', button=value['button'])
        raise ValueError('Choose the current Hold’em table settings.')
    risk = value.get('risk')
    if risk not in RISKS:
        raise ValueError('Choose Low, Medium, or High risk.')
    if game == 'keno':
        picks = value.get('picks')
        if (not isinstance(picks, list) or not 1 <= len(picks) <= 10 or
                any(type(n) is not int or not 1 <= n <= 40 for n in picks) or len(set(picks)) != len(picks)):
            raise ValueError('Pick 1–10 different numbers from 1 to 40.')
        return dict(picks=sorted(picks), risk=risk)
    if game == 'plinko' and type(value.get('rows')) is int and value['rows'] in {8, 12, 16}:
        return dict(risk=risk, rows=value['rows'])
    raise ValueError('Choose a game with valid settings.')


@lru_cache(maxsize=128)
def table(game, size, risk, version=VERSION):
    """Return exact units for the selected version's published paytable.

    V2 Plinko uses fixed tables. Keno and legacy Plinko scale probability
    weights toward 99%; all final payouts round down to whole points.
    """
    if version not in SUPPORTED_VERSIONS:
        raise ValueError('Unknown game rules version.')
    if game == 'plinko' and version != LEGACY_VERSION:
        return PLINKO_TABLES[size][risk]
    power = dict(low=2, medium=4, high=7)[risk]
    if game == 'keno':
        probabilities = [Fraction(comb(size, h)*comb(40-size, 10-h), comb(40, 10)) for h in range(size+1)]
        weights = [Fraction(h**power) for h in range(size+1)]
    elif game == 'plinko':
        probabilities = [Fraction(comb(size, slot), 2**size) for slot in range(size+1)]
        weights = [Fraction(1, 2) + abs(2*slot-size)**power for slot in range(size+1)]
    else:
        raise ValueError('Unsupported payout table.')
    average = sum(p*w for p, w in zip(probabilities, weights))
    values = tuple(int(Fraction(99, 100)*w/average*SCALE) for w in weights)
    return values


def table_info(game, size, risk):
    values = table(game, size, risk)
    probabilities = ([Fraction(comb(size, h)*comb(40-size, 10-h), comb(40, 10)) for h in range(size+1)]
                     if game == 'keno' else [Fraction(comb(size, i), 2**size) for i in range(size+1)])
    rtp = sum(p*Fraction(v, SCALE) for p, v in zip(probabilities, values))
    return dict(multipliers=list(values), rtp_percent=f'{float(rtp)*100:.4f}',
                probabilities=[float(p) for p in probabilities])


@lru_cache(maxsize=1)
def rules():
    from poker import PAYTABLE, LABELS
    from baccarat import RETURNS
    return dict(version=VERSION, scale=SCALE, games=list(GAMES), min_wager=1, max_wager=None,
                dice_rtp_percent='99.0000',
                limbo=dict(min_target=101, max_target=100_000_000, scale=100, outcomes=2**32),
                coinflip=dict(multiplier=19800, win_probability=0.5),
                poker=dict(variant='texas_holdem', policy='redbot-v1', min_buy_in=20,
                           legacy_paytable=PAYTABLE, legacy_labels=LABELS),
                baccarat=dict(decks=8, returns=RETURNS),
                keno={str(k):{risk:table_info('keno', k, risk) for risk in RISKS} for k in range(1,11)},
                plinko={str(k):{risk:table_info('plinko', k, risk) for risk in RISKS} for k in (8,12,16)})


def max_payout(game, wager, opt):
    """Exact upper bound used before reserving a stake or granting more funds."""
    if game == 'blackjack': return wager*4
    if game == 'baccarat':
        from baccarat import RETURNS
        return wager*RETURNS[opt['side']]//SCALE
    if game == 'poker': return wager*(2 if opt['variant'] == 'texas_holdem' else 800)
    if game == 'limbo': return wager*opt['target']//100
    if game == 'coinflip': return wager*198//100
    if game == 'dice': return wager*99//opt['chance']
    return wager*max(table(game, len(opt['picks']) if game == 'keno' else opt['rows'], opt['risk']))//SCALE


class Draw:
    def __init__(self, seed, receipt):
        self.key = bytes.fromhex(seed)
        version = receipt.get('rules_version', VERSION)
        if version not in SUPPORTED_VERSIONS:
            raise ValueError('Unknown game rules version.')
        self.context = [version, receipt['season'], receipt['game'], receipt['client_seed'],
                        receipt['client_salt'], receipt['nonce'], receipt['wager'], receipt['options']]
        self.block, self.buffer = 0, b''

    def below(self, size):
        # Rejection sampling removes modulo bias, including Keno's changing pool.
        boundary = 2**32 - 2**32 % size
        while True:
            if len(self.buffer) < 4:
                message = json.dumps([*self.context, self.block], sort_keys=True, separators=(',', ':'), ensure_ascii=True).encode('ascii')
                self.buffer = hmac.new(self.key, message, hashlib.sha256).digest()
                self.block += 1
            value, self.buffer = int.from_bytes(self.buffer[:4], 'big'), self.buffer[4:]
            if value < boundary:
                return value % size


def outcome(seed, receipt):
    game, opt, wager = receipt['game'], options_for(receipt['game'], receipt['options']), receipt['wager']
    version = receipt.get('rules_version', VERSION)
    if game in ('limbo', 'coinflip', 'poker') and version not in POKER_VERSIONS:
        raise ValueError('This game requires redpoints-v3 or later.')
    draw = Draw(seed, {**receipt, 'options':opt})
    if game == 'baccarat':
        if version not in (V4_VERSION, VERSION):
            raise ValueError('Baccarat requires redpoints-v4 or later.')
        from baccarat import replay
        return replay(draw, wager, opt['side'])
    if game == 'limbo':
        roll = draw.below(2**32)
        multiplier = max(100, 99*2**32//(2**32-roll))
        won = multiplier >= opt['target']
        return dict(roll=roll, multiplier=multiplier, won=won,
                    payout=wager*opt['target']//100 if won else 0)
    if game == 'coinflip':
        side = ('heads', 'tails')[draw.below(2)]
        won = side == opt['side']
        return dict(side=side, won=won, multiplier=19800, payout=wager*198//100 if won else 0)
    if game == 'poker' and opt['variant'] == 'texas_holdem':
        if version != VERSION:
            raise ValueError('Hold’em requires redpoints-v5.')
        from holdem import replay
        return replay(draw, wager, opt, receipt.get('actions', []), receipt.get('ending'))
    if game == 'poker':
        if version not in (V3_VERSION, V4_VERSION):
            raise ValueError('New Poker hands use Texas Hold’em.')
        from poker import replay
        return replay(draw, wager, receipt.get('holds'))
    if game == 'dice':
        roll = draw.below(10000)
        win = roll < opt['chance']*100 if opt['side']=='under' else roll >= 10000-opt['chance']*100
        payout = wager*99//opt['chance'] if win else 0
        return dict(roll=roll, won=win, payout=payout)
    if game == 'keno':
        numbers = list(range(1, 41))
        drawn = []
        for i in range(10):
            j = i + draw.below(40-i)
            numbers[i], numbers[j] = numbers[j], numbers[i]
            drawn.append(numbers[i])
        hits = len(set(drawn) & set(opt['picks']))
        units = table(game, len(opt['picks']), opt['risk'], receipt.get('rules_version', VERSION))[hits]
        return dict(drawn=drawn, hits=hits, multiplier=units, payout=wager*units//SCALE)
    if game == 'blackjack':
        if version not in BLACKJACK_VERSIONS:
            raise ValueError('Blackjack requires redpoints-v2 or later.')
        from blackjack import replay
        return replay(draw, wager, receipt.get('actions', []))
    path = [draw.below(2) for _ in range(opt['rows'])]
    slot = sum(path)
    units = table(game, opt['rows'], opt['risk'], receipt.get('rules_version', VERSION))[slot]
    return dict(path=path, slot=slot, multiplier=units, payout=wager*units//SCALE)


def _verify(receipt, expected_commitment=None):
    """Offline verifier. Compare against the commitment retained before betting."""
    if (not isinstance(receipt, dict) or receipt.get('rules_version') not in SUPPORTED_VERSIONS or
        any(type(receipt.get(k)) is not int or abs(receipt[k]) > 2**53-1 for k in ('nonce', 'wager', 'payout', 'net')) or
        receipt['wager'] < 1 or receipt['nonce'] < 0 or
        not isinstance(receipt.get('season'), str) or not re.fullmatch(r'\d{1,12}', receipt['season']) or
        not isinstance(receipt.get('client_seed'), str) or not re.fullmatch(r'[A-Za-z0-9 _.-]{1,64}', receipt['client_seed']) or
        not isinstance(receipt.get('client_salt'), str) or not re.fullmatch(r'[a-f0-9]{32}', receipt['client_salt']) or
        not isinstance(receipt.get('server_seed'), str) or not re.fullmatch(r'[a-f0-9]{64}', receipt['server_seed'])):
        return False
    if options_for(receipt.get('game'), receipt.get('options')) != receipt['options']:
        return False
    if commitment(receipt['server_seed']) != receipt['commitment']:
        return False
    if expected_commitment is not None and expected_commitment != receipt['commitment']:
        return False
    result = outcome(receipt['server_seed'], receipt)
    if receipt['game'] in ('blackjack', 'poker') and not result['ended']:
        return False
    stake = result['total_wager'] if receipt['game'] == 'blackjack' else receipt['wager']
    return result == receipt['result'] and receipt['payout'] == result['payout'] and receipt['net'] == result['payout']-stake


def verify(receipt, expected_commitment=None):
    """Reject malformed/unverifiable receipts without crashing the verifier."""
    try:
        return _verify(receipt, expected_commitment)
    except (KeyError, TypeError, ValueError, OverflowError):
        return False
```

## `gaming.py`

```python
"""Shared play-point wallets. All debits, outcomes, receipts and ranks commit once.

Uses the existing JSON transaction and signed browser identity. IPs are admin-only metadata. No money, SQL,
Botrix balance integration, daily wager cap, or separate launch process.
"""
import copy
import hashlib
import hmac
import ipaddress
import logging
import re
import secrets
import threading
import time

from fairness import VERSION, BLACKJACK_VERSIONS, POKER_VERSIONS, GAMES, commitment, options_for, outcome, max_payout
from weekly_history import completed_weeks

LOG = logging.getLogger('redhunllef')
START_POINTS = 100000
MAX_NUMBER = 2**53-1
MAX_PLAYERS = 10000
RECEIPTS = 30
MAX_IP_BINDINGS = MAX_PLAYERS * 4
MAX_GRANTS = 100
PUBLIC_LIVE_SECONDS = 120
PUBLIC_NOW_SECONDS = 30
PUBLIC_LEADER_LIMIT = 10
PUBLIC_LIVE_LIMIT = 20


class GamingError(ValueError):
    def __init__(self, message, code='invalid_bet', status=422):
        super().__init__(message)
        self.code, self.status = code, status


def player_name(value):
    """Validate a public Gaming name without depending on the removed Boss module."""
    if not isinstance(value, str):
        raise GamingError('Enter a name of 1–64 printable characters.', 'invalid_name', 422)
    value = value.strip()
    if not 1 <= len(value) <= 64 or not value.isprintable():
        raise GamingError('Enter a name of 1–64 printable characters.', 'invalid_name', 422)
    return value


def migrate_legacy_profiles(gaming, legacy_profiles):
    """Copy recoverable profile metadata when a unique name safely matches.

    The retired profile system and Gaming used different one-way identity hashes, so a profile
    cannot be linked to a wallet by hash. Existing Gaming wallet names/balances are
    already authoritative. A unique exact name match can safely preserve the old
    recovery digest; ambiguous names are deliberately ignored.
    """
    if not isinstance(gaming, dict) or not isinstance(legacy_profiles, dict):
        return 0
    players = gaming.get('players')
    profiles = legacy_profiles.get('profiles')
    if not isinstance(players, dict) or not isinstance(profiles, dict):
        return 0
    by_name = {}
    ambiguous = set()
    for profile in profiles.values():
        if not isinstance(profile, dict):
            continue
        name = profile.get('name')
        digest = profile.get('recovery_hash')
        if not isinstance(name, str) or not isinstance(digest, str) or not re.fullmatch(r'[a-f0-9]{64}', digest):
            continue
        key = name.casefold()
        if key in by_name:
            ambiguous.add(key)
        else:
            by_name[key] = profile
    migrated = 0
    for player in players.values():
        key = str(player.get('name', '')).casefold()
        profile = by_name.get(key)
        if not profile or key in ambiguous or player.get('recovery_hash'):
            continue
        player['recovery_hash'] = profile['recovery_hash']
        player['recovery_at'] = profile.get('recovery_at', 0)
        migrated += 1
    return migrated


def season(now=None):
    # This is the same Tuesday 18:00 America/New_York boundary as race history.
    # It advances even if the host has not yet edited an expired race form.
    from datetime import datetime, timedelta
    from race_support import EASTERN, fmt_et
    end = completed_weeks(now)[0]['end_time']
    following = int((datetime.fromtimestamp(end, EASTERN)+timedelta(days=7)).timestamp())
    return dict(id=str(end), start_time=end, end_time=following, end_et=fmt_et(following))


def player_key(identity):
    return hashlib.sha256(('redpoints-player-v1:'+identity).encode()).hexdigest()


def canonical_ip(address):
    """Normalize aliases; request headers are resolved by the trusted web layer."""
    if not isinstance(address, str) or '%' in address:
        raise ValueError('A valid visitor IP is required.')
    value = ipaddress.ip_address(address)
    if isinstance(value, ipaddress.IPv6Address) and value.ipv4_mapped:
        value = value.ipv4_mapped
    return str(value)


def ip_key(guard, address):
    # Index connections by a stable digest. Canonical addresses are stored separately
    # for the private admin view, never in public wallet responses or bet logs.
    return hmac.new(bytes.fromhex(guard['salt']), canonical_ip(address).encode('ascii'), hashlib.sha256).hexdigest()


def fresh_stats():
    return {game:dict(bets=0, wagered=0, paid=0, net=0, biggest_payout=0) for game in GAMES}


def is_holdem(hand):
    return bool(hand and hand.get('options', {}).get('variant') == 'texas_holdem')


def upgrade_poker_stats(player):
    # One-way, explicit migration: old 'poker' winnings were Video Poker.
    # Keep proof IDs/options untouched; their original HMAC context is immutable.
    if player.get('poker_stats_version', 1) == 1:
        legacy = player['stats'].pop('poker', None)
        if legacy is not None:
            player['stats']['video_poker'] = legacy
        player['poker_stats_version'] = 2
    player['stats'].setdefault('poker', fresh_stats()['poker'])


def validate_gaming(value):
    """Fail closed on malformed recovery, without overwriting existing saves."""
    if value is None:
        return None
    if not isinstance(value, dict) or value.get('version') != 1 or not isinstance(value.get('players'), dict) or len(value['players']) > MAX_PLAYERS:
        raise ValueError('Invalid RedPoints recovery.')
    for key, player in value['players'].items():
        if not re.fullmatch(r'[a-f0-9]{64}', key) or not isinstance(player, dict):
            raise ValueError('Invalid RedPoints player.')
        if not isinstance(player.get('name'), str) or not 1 <= len(player['name']) <= 64:
            raise ValueError('Invalid RedPoints display name.')
        if type(player.get('community_name_confirmed', False)) is not bool:
            raise ValueError('Invalid community-name confirmation.')
        if type(player.get('public_visibility', False)) is not bool:
            raise ValueError('Invalid public Gaming visibility.')
        last_game = player.get('last_game', '')
        if not isinstance(last_game, str) or (last_game and last_game not in GAMES):
            raise ValueError('Invalid recent Gaming activity.')
        for field in ('last_action_at', 'last_round_at'):
            value_at = player.get(field, 0)
            if type(value_at) not in (int, float) or not 0 <= value_at <= 10**12:
                raise ValueError('Invalid recent Gaming timestamp.')
        recovery_hash = player.get('recovery_hash')
        if recovery_hash is not None and (not isinstance(recovery_hash, str) or not re.fullmatch(r'[a-f0-9]{64}', recovery_hash)):
            raise ValueError('Invalid Gaming recovery digest.')
        recovery_at = player.get('recovery_at', 0)
        if type(recovery_at) not in (int, float) or not 0 <= recovery_at <= 10**12:
            raise ValueError('Invalid Gaming recovery timestamp.')
        if not isinstance(player.get('season'), str) or not re.fullmatch(r'\d{1,12}', player['season']):
            raise ValueError('Invalid RedPoints season.')
        if not isinstance(player.get('server_seed'), str) or not re.fullmatch(r'[a-f0-9]{64}', player['server_seed']):
            raise ValueError('Invalid RedPoints fairness seed.')
        for name in ('balance', 'nonce', 'version'):
            if type(player.get(name)) is not int or not 0 <= player[name] <= MAX_NUMBER:
                raise ValueError('Invalid RedPoints wallet counter.')
        if not {'dice', 'keno', 'plinko'} <= set(player.get('stats', {})) <= set(GAMES) | {'video_poker'}:
            raise ValueError('Invalid RedPoints game statistics.')
        if player.get('poker_stats_version', 1) not in (1, 2):
            raise ValueError('Invalid Poker statistics version.')
        if 'video_poker' in player['stats'] and player.get('poker_stats_version') != 2:
            raise ValueError('Video Poker records need their migration marker.')
        for stats in player['stats'].values():
            for name in ('bets','wagered','paid','biggest_payout'):
                if type(stats.get(name)) is not int or not 0 <= stats[name] <= MAX_NUMBER:
                    raise ValueError('Invalid RedPoints winnings.')
            if stats.get('net') != stats['paid']-stats['wagered']:
                raise ValueError('RedPoints winnings do not balance.')
        if player.get('blackjack') is not None and player.get('poker') is not None:
            raise ValueError('A wallet cannot reserve two card hands at once.')
        reserved = 0
        for game in ('blackjack', 'poker'):
            pending = player.get(game)
            if pending is None:
                continue
            try:
                allowed = BLACKJACK_VERSIONS if game == 'blackjack' else POKER_VERSIONS
                if (pending['game'] != game or pending['rules_version'] not in allowed or
                        pending['nonce'] != player['nonce'] or pending['server_seed'] != player['server_seed'] or
                        pending['commitment'] != commitment(player['server_seed']) or pending['season'] != player['season'] or
                        type(pending['wager']) is not int or not 1 <= pending['wager'] <= MAX_NUMBER or
                        not re.fullmatch(r'[A-Za-z0-9_-]{8,64}', pending['request_id']) or
                        not re.fullmatch(r'[a-f0-9]{32}', pending['client_salt']) or
                        not re.fullmatch(r'[A-Za-z0-9 _.-]{1,64}', pending['client_seed']) or
                        options_for(game, pending['options']) != pending['options']):
                    raise ValueError('Invalid reserved hand')
                if game == 'blackjack' or is_holdem(pending):
                    if (len(pending['action_ids']) != len(pending['actions']) or
                            len(set(pending['action_ids'])) != len(pending['action_ids']) or
                            any(not re.fullmatch(r'[A-Za-z0-9_-]{8,64}', item) for item in pending['action_ids'])):
                        raise ValueError('Invalid saved card moves')
                elif pending.get('holds') is not None or 'draw_id' in pending:
                    raise ValueError('A drawn Poker hand must already be settled')
                if outcome(player['server_seed'], pending)['ended']:
                    raise ValueError('A completed hand cannot remain reserved')
                reserved = pending['wager']
            except (KeyError, TypeError, ValueError):
                raise ValueError('Invalid saved card hand.') from None
        # Refresh grants belong to the wallet, never to game winnings/rankings.
        # Older saves have no adjustment and retain their original accounting.
        adjustment = player.get('balance_adjustment', 0)
        if type(adjustment) is not int or abs(adjustment) > MAX_NUMBER:
            raise ValueError('Invalid RedPoints refresh adjustment.')
        if player['balance'] != START_POINTS + adjustment + sum(s['net'] for s in player['stats'].values()) - reserved:
            raise ValueError('RedPoints wallet does not balance.')
        receipts = player.get('receipts')
        if not isinstance(receipts, list) or len(receipts) > RECEIPTS:
            raise ValueError('Invalid RedPoints receipts.')
        seen = set()
        if len(receipts) != min(RECEIPTS, player['nonce']):
            raise ValueError('RedPoints receipt sequence is incomplete.')
        from fairness import verify
        for index, receipt in enumerate(receipts):
            try:
                valid = (isinstance(receipt, dict) and receipt['request_id'] not in seen and
                         type(receipt['nonce']) is int and receipt['nonce'] == player['nonce']-1-index and
                         type(receipt['wager']) is int and 1 <= receipt['wager'] <= MAX_NUMBER and verify(receipt))
                if not valid: raise ValueError('Invalid receipt')
                seen.add(receipt['request_id'])
            except (KeyError, TypeError, ValueError):
                raise ValueError('A saved RedPoints receipt failed verification.') from None
    activity_revision = value.get('activity_revision', 0)
    if type(activity_revision) is not int or not 0 <= activity_revision <= MAX_NUMBER:
        raise ValueError('Invalid public Gaming activity revision.')
    grants = value.get('admin_grants', [])
    if not isinstance(grants, list) or len(grants) > MAX_GRANTS:
        raise ValueError('Invalid RedPoints grant history.')
    grant_ids = set()
    for grant in grants:
        if (not isinstance(grant, dict) or not isinstance(grant.get('request_id'), str) or
                not re.fullmatch(r'[a-f0-9]{32}', grant['request_id']) or grant['request_id'] in grant_ids or
                not isinstance(grant.get('actor'), str) or not 1 <= len(grant['actor']) <= 64 or
                type(grant.get('amount')) is not int or grant['amount'] != START_POINTS or
                type(grant.get('players')) is not int or not 0 <= grant['players'] <= MAX_PLAYERS or
                type(grant.get('at')) is not int or not 0 <= grant['at'] <= MAX_NUMBER or
                not isinstance(grant.get('season'), str) or not re.fullmatch(r'\d{1,12}', grant['season'])):
            raise ValueError('Invalid RedPoints grant record.')
        grant_ids.add(grant['request_id'])
    guard = value.get('ip_guard')
    if guard is not None:
        if (not isinstance(guard, dict) or guard.get('version') not in (1, 2) or
                not isinstance(guard.get('salt'), str) or not re.fullmatch(r'[a-f0-9]{64}', guard['salt']) or
                not isinstance(guard.get('season'), str) or not re.fullmatch(r'\d{1,12}', guard['season']) or
                not isinstance(guard.get('claims'), dict) or len(guard['claims']) > MAX_IP_BINDINGS):
            raise ValueError('Invalid RedPoints IP bindings.')
        links = 0
        for address, owners in guard['claims'].items():
            owners = [owners] if guard['version'] == 1 else owners
            if (not isinstance(address, str) or not re.fullmatch(r'[a-f0-9]{64}', address) or
                    not isinstance(owners, list) or not owners or len(owners) > MAX_PLAYERS or
                    any(not isinstance(key, str) or key not in value['players'] for key in owners) or
                    len(set(owners)) != len(owners)):
                raise ValueError('Invalid RedPoints IP association.')
            links += len(owners)
        if links > MAX_IP_BINDINGS:
            raise ValueError('Too many saved RedPoints IP associations.')
        addresses = guard.get('addresses', {})
        if not isinstance(addresses, dict) or set(addresses)-set(guard['claims']):
            raise ValueError('Invalid private IP directory.')
        for digest, address in addresses.items():
            if canonical_ip(address) != address or ip_key(guard, address) != digest:
                raise ValueError('Invalid private IP address.')
    return value


class Gaming:
    def __init__(self, store):
        self.store = store
        self._public_cache_lock = threading.RLock()
        self._public_cache_key = None
        self._public_cache_value = None
        self._public_cache_expires_at = 0
        with store.connection() as conn:
            validate_gaming(conn.get('gaming'))
        # Adding a game never resets an existing wallet, seed or receipt.
        # Public activity fields are additive and default private for existing
        # players until they explicitly opt in from the Gaming profile.
        with store.connection(transaction=True) as conn:
            if conn.get('gaming') is None:
                conn['gaming'] = dict(version=1, players={}, activity_revision=0)
            data = conn['gaming']
            data.setdefault('activity_revision', 0)
            for player in data.get('players', {}).values():
                upgrade_poker_stats(player)
                for game, stats in fresh_stats().items():
                    player['stats'].setdefault(game, stats)
                player.setdefault('public_visibility', False)
                player.setdefault('last_game', '')
                player.setdefault('last_action_at', 0)
                player.setdefault('last_round_at', 0)
            self._upgrade_networks(data.get('ip_guard'))

    def restart_balances(self, now=None):
        """Run once at server startup, never from a page or automatic poll.

        Restore the playable allowance without erasing names, results, seeds or
        unfinished hands. Normal weekly rollover still starts a fresh leaderboard.
        """
        current = season(now)
        restored = skipped = 0
        with self.store.connection(transaction=True) as conn:
            for player in (conn.get('gaming') or {}).get('players', {}).values():
                try:
                    self._rollover(player, current)
                    if player['balance'] != START_POINTS:
                        self._reset_allowance(player)
                    restored += 1
                except GamingError:
                    # An exceptional numeric/clock record must not take the
                    # entire community offline. Keep that record unchanged.
                    skipped += 1
        LOG.info('GAMING startup restored %s RedPoints for %s wallets; names and game records retained. Shared IPs are allowed.',
                 START_POINTS, restored)
        if skipped:
            LOG.warning('GAMING retained %s wallets unchanged due to their numeric range or future season.', skipped)
        return dict(restored=restored, skipped=skipped)

    @staticmethod
    def _reset_allowance(player):
        # This adjustment is funding, not winnings. Reserved Blackjack stakes
        # remain in the hand and are settled exactly once by the normal ledger.
        adjustment = player.get('balance_adjustment', 0) + START_POINTS - player['balance']
        hand = player.get('blackjack') or player.get('poker')
        room = max_payout(hand['game'], hand['wager'], hand['options']) if hand else 0
        if START_POINTS+room > MAX_NUMBER or abs(adjustment) > MAX_NUMBER or player['version'] >= MAX_NUMBER:
            raise GamingError('This wallet reached its supported numeric range.', 'capacity', 409)
        player.update(balance=START_POINTS, balance_adjustment=adjustment, version=player['version']+1)

    def _player(self, conn, identity, name, now):
        current = season(now)
        if conn.get('gaming') is None:
            conn['gaming'] = dict(version=1, players={}, activity_revision=0)
        conn['gaming'].setdefault('activity_revision', 0)
        players = conn['gaming']['players']
        key = player_key(identity)
        if key not in players:
            if len(players) >= MAX_PLAYERS:
                raise GamingError('The player registry is full. Contact the host.', 'capacity', 409)
            players[key] = dict(name=name, season=current['id'], balance=START_POINTS, stats=fresh_stats(),
                                nonce=0, version=1, poker_stats_version=2, server_seed=secrets.token_hex(32),
                                receipts=[], last_bet_at=0, public_visibility=False, last_game='',
                                last_action_at=0, last_round_at=0)
        player = players[key]
        upgrade_poker_stats(player)
        for game, stats in fresh_stats().items():
            player['stats'].setdefault(game, stats)
        self._rollover(player, current)
        if player['name'] != name:
            player['name'] = name
            player['version'] += 1
        return player, current

    @staticmethod
    def _touch_activity(data, player, game, now, *, round_completed=False):
        """Record only server-confirmed game actions for the public activity feed.

        Page views and five-second wallet polls never call this helper, so they
        cannot make a visitor appear to be actively playing.
        """
        if game not in GAMES:
            return
        stamp = int(now)
        player['last_game'] = game
        player['last_action_at'] = stamp
        if round_completed:
            player['last_round_at'] = stamp
        data['activity_revision'] = min(MAX_NUMBER, int(data.get('activity_revision', 0)) + 1)

    @staticmethod
    def _rollover(player, current):
        """Reuse the same weekly accounting for player visits and bulk grants."""
        if int(player['season']) > int(current['id']):
            raise GamingError('The server clock moved backwards. The saved wallet is protected.', 'clock', 409)
        if player['season'] != current['id']:
            hand = player.get('blackjack') or player.get('poker')
            if hand:
                if hand['game'] == 'blackjack':
                    hand['actions'].append('stand')
                elif is_holdem(hand):
                    # Fold the saved hand at the boundary; do not wager more.
                    pass
                else:
                    # A week boundary keeps all five initial cards, then settles
                    # under the old week before the new allowance is created.
                    hand.update(holds=list(range(5)), draw_id='weekly-reset')
                hand['ending'] = 'weekly_reset'
                Gaming._settle(player, hand, outcome(player['server_seed'], hand))
            player.update(season=current['id'], balance=START_POINTS, balance_adjustment=0,
                          stats=fresh_stats(), version=player['version']+1)

    @staticmethod
    def _upgrade_networks(guard):
        """Turn old exclusive claims into many-player associations, in place."""
        if guard and guard['version'] == 1:
            guard['claims'] = {digest: [owner] for digest, owner in guard['claims'].items()}
            guard['version'] = 2

    @staticmethod
    def _needs_network_record(data, key, address, current):
        """Missing/full tracking data never affects eligibility to play."""
        try:
            address = canonical_ip(address)
        except ValueError:
            return False
        guard = (data or {}).get('ip_guard')
        if not guard or int(guard['season']) < int(current['id']):
            return True
        if int(guard['season']) > int(current['id']):
            return False
        digest = ip_key(guard, address)
        owners = guard['claims'].get(digest, [])
        if isinstance(owners, str):
            owners = [owners]  # Recovery imports may still contain the old format.
        if key in owners:
            return digest not in guard.get('addresses', {})
        links = sum(1 if isinstance(items, str) else len(items) for items in guard['claims'].values())
        return links < MAX_IP_BINDINGS

    def _record_ip(self, data, key, address, current):
        # A household, VPN, mobile carrier or proxy can represent many people.
        # Only the signed browser/recovery identity owns a wallet, never an IP.
        if not self._needs_network_record(data, key, address, current):
            return
        guard = data.get('ip_guard')
        if guard is None:
            guard = data['ip_guard'] = dict(version=2, salt=secrets.token_hex(32), season=current['id'], claims={}, addresses={})
        self._upgrade_networks(guard)
        if guard['season'] != current['id']:
            guard.update(season=current['id'], claims={}, addresses={})
        digest = ip_key(guard, address)
        owners = guard['claims'].setdefault(digest, [])
        if key not in owners:
            owners.append(key)
        guard.setdefault('addresses', {})[digest] = canonical_ip(address)

    @staticmethod
    def _hand_view(player):
        receipt = player.get('blackjack')
        if not receipt:
            return None
        value = outcome(player['server_seed'], receipt)
        # Never expose the unrevealed seed, hole card or remaining shoe.
        from blackjack import total
        value.update(dealer=[value['dealer'][0], None], dealer_total=total(value['dealer'][:1])[0],
                     dealer_soft=False, round_id=receipt['request_id'], step=len(receipt['actions']),
                     wager=receipt['wager'], can_double=not receipt['actions'] and player['balance'] >= receipt['wager'])
        value['bet'] = {k:v for k,v in receipt.items() if k not in {'server_seed', 'actions', 'action_ids'}}
        return value

    @staticmethod
    def _poker_view(player):
        hand = player.get('poker')
        if not hand:
            return None
        value = outcome(player['server_seed'], hand)
        value.update(round_id=hand['request_id'], wager=hand['wager'], step=len(hand.get('actions', [])),
                     bet={k:v for k,v in hand.items() if k not in {'server_seed', 'holds', 'actions', 'action_ids'}})
        return value

    @staticmethod
    def _view(player, current):
        return dict(season=current, name=player['name'], balance=player['balance'], nonce=player['nonce'],
                    version=player['version'], commitment=commitment(player['server_seed']),
                    stats={game:copy.deepcopy(player['stats'].get(game, stats)) for game, stats in fresh_stats().items()},
                    legacy_poker=copy.deepcopy(player['stats'].get('video_poker')),
                    poker_button='player' if player['stats'].get('poker', {}).get('bets', 0) % 2 == 0 else 'computer',
                    receipts=copy.deepcopy(player['receipts']),
                    needs_profile=not player.get('community_name_confirmed', False),
                    public_visibility=bool(player.get('public_visibility', False)),
                    rules_version=VERSION, ip_bound=False, play_blocked=None,
                    blackjack=Gaming._hand_view(player), poker=Gaming._poker_view(player))

    def view(self, identity, name, now=None, *, client_ip=None):
        now = time.time() if now is None else now
        current = season(now)
        key = player_key(identity)
        def preview():
            return dict(season=current, balance=START_POINTS, name=name or '', nonce=0, version=0,
                        commitment='', stats=fresh_stats(), receipts=[], needs_profile=True, public_visibility=False,
                        rules_version=VERSION, ip_bound=False, play_blocked=None, blackjack=None, poker=None,
                        poker_button='player', legacy_poker=None)
        # Routine five-second reads neither copy the complete community save nor
        # rewrite it. Connection metadata is recorded only when it changes.
        with self.store.connection() as conn:
            data = conn.get('gaming') or {}
            player = data.get('players', {}).get(key)
            if player:
                # The wallet owns its name. No retired profile lookup is required.
                name = player['name']
                if player.get('poker_stats_version') == 2 and player['season'] == current['id']:
                    if not self._needs_network_record(data, key, client_ip, current):
                        return self._view(player, current)
            elif not name:
                return preview()
        with self.store.connection(transaction=True) as conn:
            player, current = self._player(conn, identity, name, now)
            self._record_ip(conn['gaming'], key, client_ip, current)
            return self._view(player, current)

    def confirm_community_name(self, identity, name, public_visibility=None, now=None, *, client_ip=None):
        """Activate the shared wallet once, retaining wins, receipts and its owner.

        Names migrated from the retired profile system remain suggestions until confirmed on Gaming. Older
        empty wallets receive the starting allowance here; re-saving a confirmed
        name does not grant more points or erase larger balances/admin credits.
        """
        name = player_name(name)
        now = time.time() if now is None else now
        if public_visibility is not None and type(public_visibility) is not bool:
            raise GamingError('Choose whether your Gaming name appears publicly.', 'invalid_visibility', 422)
        with self.store.connection(transaction=True) as conn:
            if conn.get('gaming') is None:
                conn['gaming'] = dict(version=1, players={}, activity_revision=0)
            data = conn['gaming']
            data.setdefault('activity_revision', 0)
            before_name = (data.get('players', {}).get(player_key(identity)) or {}).get('name')
            before_visibility = (data.get('players', {}).get(player_key(identity)) or {}).get('public_visibility', False)
            player, current = self._player(conn, identity, name, now)
            self._record_ip(data, player_key(identity), client_ip, current)
            if not player.get('community_name_confirmed', False):
                extra = max(0, START_POINTS - player['balance'])
                adjustment = player.get('balance_adjustment', 0) + extra
                if abs(adjustment) > MAX_NUMBER or player['version'] >= MAX_NUMBER:
                    raise GamingError('This wallet reached its supported numeric range.', 'capacity', 409)
                player.update(community_name_confirmed=True, balance=player['balance']+extra,
                              balance_adjustment=adjustment, version=player['version']+1)
            if public_visibility is not None and player.get('public_visibility', False) != public_visibility:
                player['public_visibility'] = public_visibility
                player['version'] += 1
            if before_name != player['name'] or before_visibility != player.get('public_visibility', False):
                data['activity_revision'] = min(MAX_NUMBER, int(data.get('activity_revision', 0)) + 1)
            return self._view(player, current)

    def save_recovery(self, identity, code_hash, now=None):
        """Attach a replaceable recovery digest to this signed Gaming wallet."""
        if not isinstance(code_hash, str) or not re.fullmatch(r'[a-f0-9]{64}', code_hash):
            raise GamingError('Invalid recovery code.', 'invalid_recovery', 422)
        now = time.time() if now is None else now
        with self.store.connection(transaction=True) as conn:
            player = (conn.get('gaming') or {}).get('players', {}).get(player_key(identity))
            if not player or not player.get('community_name_confirmed'):
                raise GamingError('Save your Gaming name before creating a recovery code.', 'profile_required', 409)
            if now - player.get('recovery_at', 0) < 30:
                raise GamingError('Wait 30 seconds before replacing your recovery code.', 'profile_cooldown', 429)
            player['recovery_hash'] = code_hash
            player['recovery_at'] = now
            player['version'] += 1
            return self._view(player, season(now))

    def recover(self, identity, code_hash, now=None, *, client_ip=None):
        """Validate a recovery digest and return the wallet owned by identity."""
        if not isinstance(code_hash, str) or not re.fullmatch(r'[a-f0-9]{64}', code_hash):
            raise GamingError('That recovery code is invalid or was replaced.', 'invalid_recovery', 400)
        now = time.time() if now is None else now
        key = player_key(identity)
        with self.store.connection(transaction=True) as conn:
            data = conn.get('gaming') or {}
            player = data.get('players', {}).get(key)
            if not player or not hmac.compare_digest(str(player.get('recovery_hash', '')), code_hash):
                raise GamingError('That recovery code is invalid or was replaced.', 'invalid_recovery', 400)
            current = season(now)
            self._rollover(player, current)
            self._record_ip(data, key, client_ip, current)
            return self._view(player, current)

    def grant_everyone(self, request_id, actor, now=None):
        """Add 100k per saved wallet in one atomic write; retries cannot double it.

        HTTP authentication/CSRF is enforced by the admin route. Credits are
        separate from game profit, so Top 5 and fairness receipts stay accurate.
        """
        if (not isinstance(request_id, str) or not re.fullmatch(r'[a-f0-9]{32}', request_id) or
                not isinstance(actor, str) or not 1 <= len(actor) <= 64):
            raise GamingError('Reload the admin panel before granting points.', 'invalid_grant', 422)
        now = time.time() if now is None else now
        current = season(now)
        with self.store.connection(transaction=True) as conn:
            if conn.get('gaming') is None:
                conn['gaming'] = dict(version=1, players={})
            data = conn['gaming']
            history = data.setdefault('admin_grants', [])
            prior = next((item for item in history if item['request_id'] == request_id), None)
            if prior:
                return dict(duplicate=True, **copy.deepcopy(prior))
            for player in data['players'].values():
                self._rollover(player, current)
                adjustment = player.get('balance_adjustment', 0) + START_POINTS
                # Reserve room for the largest return on an unfinished card hand.
                hand = player.get('blackjack') or player.get('poker')
                room = max_payout(hand['game'], hand['wager'], hand['options']) if hand else 0
                if (player['balance'] + START_POINTS + room > MAX_NUMBER or
                        abs(adjustment) > MAX_NUMBER or player['version'] >= MAX_NUMBER):
                    raise GamingError('A wallet reached the numeric limit. No points were granted.', 'capacity', 409)
                player.update(balance=player['balance']+START_POINTS, balance_adjustment=adjustment,
                              version=player['version']+1)
            record = dict(request_id=request_id, actor=actor, amount=START_POINTS,
                          players=len(data['players']), at=int(now), season=current['id'])
            data['admin_grants'] = [record] + history[:MAX_GRANTS-1]
        LOG.info('GAMING Admin %r granted +%s RedPoints to %s wallets; game winnings unchanged.',
                 actor, START_POINTS, record['players'])
        return dict(duplicate=False, **record)

    def refresh_balance(self, identity, name, body, now=None, *, client_ip=None):
        """Reset available points on a browser refresh; preserve all game records.

        Reads and automatic polls never call this method. The version check makes
        retries harmless and prevents a stale page from overwriting a newer bet.
        An unfinished Blackjack stake stays reserved; its hand/seed are untouched.
        """
        if not name:
            raise GamingError('Save your player name before refreshing points.', 'username_required', 409)
        if (not isinstance(body, dict) or type(body.get('version')) is not int or
                not 0 <= body['version'] <= MAX_NUMBER or not isinstance(body.get('season'), str) or
                not re.fullmatch(r'\d{1,12}', body['season'])):
            raise GamingError('Reload the page to refresh your RedPoints.')
        now = time.time() if now is None else now
        with self.store.connection(transaction=True) as conn:
            player, current = self._player(conn, identity, name, now)
            self._record_ip(conn['gaming'], player_key(identity), client_ip, current)
            if body['season'] != current['id']:
                # The weekly rollover already supplies the new allowance.
                return dict(ok=True, wallet=self._view(player, current))
            if body['version'] != player['version']:
                raise GamingError('Your balance changed in another request. Reload to refresh the latest wallet.',
                                  'stale_wallet', 409)
            self._reset_allowance(player)
            LOG.info('GAMING browser refresh restored %s RedPoints; game records retained.', START_POINTS)
            return dict(ok=True, wallet=self._view(player, current))

    def bet(self, identity, name, body, now=None, *, client_ip=None):
        if not name:
            raise GamingError('Save your player name before playing.', 'username_required', 409)
        if not isinstance(body, dict):
            raise GamingError('Send a valid wager.')
        game, request_id = body.get('game'), body.get('request_id')
        if game not in GAMES or not isinstance(request_id, str) or not re.fullmatch(r'[A-Za-z0-9_-]{8,64}', request_id):
            raise GamingError('Choose a game and provide a valid bet receipt ID.')
        opt = options_for(game, body.get('options'))
        wager, nonce = body.get('wager'), body.get('nonce')
        # There is no fixed stake cap or timed delay. Keep amounts exact across
        # Python and JavaScript; the wallet balance remains authoritative.
        if type(wager) is not int or not 1 <= wager <= MAX_NUMBER:
            raise GamingError('Enter a positive whole-point wager within the supported exact-integer range.')
        if type(nonce) is not int or nonce < 0:
            raise GamingError('Reload the fairness details before playing.')
        client, salt = body.get('client_seed'), body.get('client_salt')
        if not isinstance(client, str) or not re.fullmatch(r'[A-Za-z0-9 _.-]{1,64}', client):
            raise GamingError('Use 1–64 letters, numbers, spaces, dots, underscores or hyphens for your client seed.')
        if not isinstance(salt, str) or not re.fullmatch(r'[a-f0-9]{32}', salt):
            raise GamingError('Your browser must generate fresh entropy for this bet.')
        now = time.time() if now is None else now
        with self.store.connection(transaction=True) as conn:
            player, current = self._player(conn, identity, name, now)
            duplicate = next((r for r in player['receipts'] if r['request_id']==request_id), None)
            if duplicate:
                return dict(ok=True, duplicate=True, receipt=copy.deepcopy(duplicate), wallet=self._view(player, current))
            # Old receipts remain recoverable; new wagers use the current rules.
            if body.get('rules_version') != VERSION:
                raise GamingError('Game rules changed. Reload before placing another wager.', 'release_mismatch', 409)
            self._record_ip(conn['gaming'], player_key(identity), client_ip, current)
            active = player.get('blackjack') or player.get('poker')
            if active:
                if active['request_id'] == request_id:
                    return dict(ok=True, duplicate=True, receipt=None, wallet=self._view(player, current))
                raise GamingError('Finish your '+active['game'].capitalize()+' hand before starting another game.', 'active_hand', 409)
            if body.get('season') != current['id']:
                raise GamingError('A new wager-race week started. Refresh to use your new 100,000 RedPoints.', 'new_season', 409)
            if nonce != player['nonce'] or body.get('commitment') != commitment(player['server_seed']):
                raise GamingError('Another tab used this seed. Refresh your balance and fairness details.', 'stale_seed', 409)
            if wager > player['balance']:
                raise GamingError('Not enough RedPoints. Lower the wager or refresh the page for 100,000 RedPoints.', 'balance', 409)
            if game == 'poker':
                button = 'player' if player['stats']['poker']['bets'] % 2 == 0 else 'computer'
                if opt != dict(variant='texas_holdem', button=button):
                    raise GamingError('The dealer button changed. Reload the saved table.', 'stale_hand', 409)
            largest = max_payout(game, wager, opt)
            stats = player['stats'][game]
            if max(player['balance']-wager+largest, stats['paid']+largest, stats['wagered']+wager*(2 if game=='blackjack' else 1),
                   player['nonce']+1, player['version']+1) > MAX_NUMBER:
                raise GamingError('This wallet reached its supported numeric range.', 'capacity', 409)
            receipt = dict(rules_version=VERSION, season=current['id'], request_id=request_id, game=game,
                           client_seed=client, client_salt=salt, nonce=nonce, wager=wager, options=opt,
                           commitment=commitment(player['server_seed']), server_seed=player['server_seed'], at=int(now))
            if game == 'blackjack':
                receipt.update(actions=[], action_ids=[])
            elif game == 'poker':
                receipt.update(actions=[], action_ids=[])
            result = outcome(player['server_seed'], receipt)
            player['balance'] -= wager
            if game in ('blackjack', 'poker') and not result['ended']:
                player[game] = receipt
                player['version'] += 1
                self._touch_activity(conn['gaming'], player, game, now, round_completed=False)
                return dict(ok=True, duplicate=False, receipt=None, wallet=self._view(player, current))
            self._settle(player, receipt, result)
            self._touch_activity(conn['gaming'], player, game, now, round_completed=True)
            return dict(ok=True, duplicate=False, receipt=copy.deepcopy(receipt), wallet=self._view(player, current))

    @staticmethod
    def _settle(player, receipt, result):
        """Credit once after the complete stake has been reserved in this transaction."""
        wager = result['total_wager'] if receipt['game'] == 'blackjack' else receipt['wager']
        payout, net = result['payout'], result['payout']-wager
        player.update(balance=player['balance']+payout, nonce=player['nonce']+1,
                      server_seed=secrets.token_hex(32), version=player['version']+1, last_bet_at=receipt['at'])
        player.pop('blackjack', None)
        player.pop('poker', None)
        receipt.update(result=result, payout=payout, net=net, balance_after=player['balance'],
                       next_commitment=commitment(player['server_seed']))
        stat_game = 'video_poker' if receipt['game'] == 'poker' and not is_holdem(receipt) else receipt['game']
        stats = player['stats'].setdefault(stat_game, dict(bets=0, wagered=0, paid=0, net=0, biggest_payout=0))
        # Hold’em credits the entire remaining table stack to the wallet, but
        # only contested chips and pot awards belong in gambling statistics.
        if is_holdem(receipt):
            wager, payout = result['total_wager'], result['returned']
        stats.update(bets=stats['bets']+1, wagered=stats['wagered']+wager, paid=stats['paid']+payout,
                     net=stats['net']+net, biggest_payout=max(stats['biggest_payout'], payout))
        player['receipts'] = [copy.deepcopy(receipt)]+player['receipts'][:RECEIPTS-1]
        LOG.info('GAMING %s settled; nonce=%s wager=%s payout=%s.', receipt['game'], receipt['nonce'], wager, payout)

    def blackjack_action(self, identity, name, body, now=None, *, client_ip=None):
        if not name or not isinstance(body, dict):
            raise GamingError('Restore your player before continuing.', 'username_required', 409)
        action, action_id, round_id, step = (body.get(k) for k in ('action', 'action_id', 'round_id', 'step'))
        if (action not in ('hit', 'stand', 'double') or type(step) is not int or not 0 <= step <= 32 or
                any(not isinstance(v, str) or not re.fullmatch(r'[A-Za-z0-9_-]{8,64}', v) for v in (action_id, round_id))):
            raise GamingError('Send a valid Blackjack move.')
        now = time.time() if now is None else now
        with self.store.connection(transaction=True) as conn:
            player, current = self._player(conn, identity, name, now)
            done = next((r for r in player['receipts'] if r['request_id'] == round_id and r['game']=='blackjack'), None)
            if done:
                return dict(ok=True, duplicate=True, receipt=copy.deepcopy(done), wallet=self._view(player, current))
            self._record_ip(conn['gaming'], player_key(identity), client_ip, current)
            receipt = player.get('blackjack')
            if not receipt or receipt['request_id'] != round_id:
                raise GamingError('This hand is no longer active. Reload your saved result.', 'stale_hand', 409)
            if action_id in receipt['action_ids']:
                return dict(ok=True, duplicate=True, receipt=None, wallet=self._view(player, current))
            if step != len(receipt['actions']):
                raise GamingError('Another tab played a move. Your saved hand has been updated.', 'stale_hand', 409)
            if action == 'double' and player['balance'] < receipt['wager']:
                raise GamingError('Not enough RedPoints to double. Hit or Stand.', 'balance', 409)
            receipt['actions'].append(action)
            receipt['action_ids'].append(action_id)
            result = outcome(player['server_seed'], receipt)  # Illegal moves roll back.
            if action == 'double':
                player['balance'] -= receipt['wager']
            if result['ended']:
                self._settle(player, receipt, result)
                self._touch_activity(conn['gaming'], player, 'blackjack', now, round_completed=True)
                return dict(ok=True, duplicate=False, receipt=copy.deepcopy(receipt), wallet=self._view(player, current))
            player['version'] += 1
            self._touch_activity(conn['gaming'], player, 'blackjack', now, round_completed=False)
            return dict(ok=True, duplicate=False, receipt=None, wallet=self._view(player, current))

    def poker_action(self, identity, name, body, now=None, *, client_ip=None):
        """Commit one hold/draw decision and settle it atomically, once."""
        if isinstance(body, dict) and body.get('variant') == 'texas_holdem':
            return self.holdem_action(identity, name, body, now, client_ip=client_ip)
        from poker import validate_holds
        if not name or not isinstance(body, dict):
            raise GamingError('Restore your player before drawing cards.', 'username_required', 409)
        holds = validate_holds(body.get('holds'))
        action_id, round_id = body.get('action_id'), body.get('round_id')
        if any(not isinstance(value, str) or not re.fullmatch(r'[A-Za-z0-9_-]{8,64}', value) for value in (action_id, round_id)):
            raise GamingError('Send a valid Poker draw.')
        now = time.time() if now is None else now
        with self.store.connection(transaction=True) as conn:
            player, current = self._player(conn, identity, name, now)
            done = next((r for r in player['receipts'] if r['request_id'] == round_id and r['game'] == 'poker'), None)
            if done:
                if is_holdem(done):
                    raise GamingError('This is a saved Hold’em result.', 'stale_hand', 409)
                if done.get('draw_id') != action_id or done['holds'] != holds:
                    raise GamingError('This hand was already drawn. Its saved result has been kept.', 'stale_hand', 409)
                return dict(ok=True, duplicate=True, receipt=copy.deepcopy(done), wallet=self._view(player, current))
            self._record_ip(conn['gaming'], player_key(identity), client_ip, current)
            hand = player.get('poker')
            if not hand or hand['request_id'] != round_id:
                raise GamingError('This Poker hand is no longer active. Reload your saved result.', 'stale_hand', 409)
            if is_holdem(hand):
                raise GamingError('Use the Hold’em action controls.', 'stale_hand', 409)
            hand.update(holds=holds, draw_id=action_id)
            self._settle(player, hand, outcome(player['server_seed'], hand))
            self._touch_activity(conn['gaming'], player, 'poker', now, round_completed=True)
            return dict(ok=True, duplicate=False, receipt=copy.deepcopy(hand), wallet=self._view(player, current))

    def holdem_action(self, identity, name, body, now=None, *, client_ip=None):
        """Replay a saved hand and commit one player decision exactly once."""
        from holdem import validate_action
        if not name or not isinstance(body, dict):
            raise GamingError('Restore your player before continuing.', 'username_required', 409)
        move = validate_action(body.get('move'))
        action_id, round_id, step = (body.get(k) for k in ('action_id', 'round_id', 'step'))
        if (type(step) is not int or not 0 <= step < 4096 or
                any(not isinstance(v, str) or not re.fullmatch(r'[A-Za-z0-9_-]{8,64}', v) for v in (action_id, round_id))):
            raise GamingError('Send a valid Hold’em move.')
        now = time.time() if now is None else now
        with self.store.connection(transaction=True) as conn:
            player, current = self._player(conn, identity, name, now)
            done = next((r for r in player['receipts'] if r['request_id'] == round_id and is_holdem(r)), None)
            hand = done or player.get('poker')
            if not is_holdem(hand) or hand['request_id'] != round_id:
                raise GamingError('This Hold’em hand is no longer active. Reload its saved result.', 'stale_hand', 409)
            # Reusing an ID with a different move is not an idempotent retry.
            if action_id in hand['action_ids']:
                index = hand['action_ids'].index(action_id)
                if index != step or hand['actions'][index] != move:
                    raise GamingError('That move ID already has a different decision.', 'stale_hand', 409)
                return dict(ok=True, duplicate=True, receipt=copy.deepcopy(done), wallet=self._view(player, current))
            if done or step != len(hand['actions']):
                raise GamingError('Another tab moved. Your saved table has been updated.', 'stale_hand', 409)
            self._record_ip(conn['gaming'], player_key(identity), client_ip, current)
            hand['actions'].append(move)
            hand['action_ids'].append(action_id)
            result = outcome(player['server_seed'], hand)  # Illegal actions roll back the transaction.
            if result['ended']:
                self._settle(player, hand, result)
                self._touch_activity(conn['gaming'], player, 'poker', now, round_completed=True)
                return dict(ok=True, duplicate=False, receipt=copy.deepcopy(hand), wallet=self._view(player, current))
            player['version'] += 1
            self._touch_activity(conn['gaming'], player, 'poker', now, round_completed=False)
            return dict(ok=True, duplicate=False, receipt=None, wallet=self._view(player, current))

    @staticmethod
    def _game_label(game):
        return {
            'poker': "Texas Hold’em",
            'video_poker': 'Video Poker',
            'coinflip': 'Coinflip',
        }.get(game, game.capitalize())

    def public_leaderboard(self, now=None):
        """Return a compact, privacy-safe five-second Gaming community feed.

        The projection contains no wallet IDs, IP addresses, balances, recovery
        data, seeds, receipts or funding adjustments. Rankings use settled
        server-side ledger statistics only. Page views and polling never create
        activity; only confirmed game actions call ``_touch_activity``.
        """
        now = time.time() if now is None else now
        current = season(now)
        with self.store.connection() as conn:
            data = conn.get('gaming') or {}
            revision = int(data.get('activity_revision', 0))
            cache_key = (current['id'], revision)
            with self._public_cache_lock:
                if (cache_key == self._public_cache_key and self._public_cache_value is not None and
                        now < self._public_cache_expires_at):
                    return copy.deepcopy(self._public_cache_value)
            players = data.get('players', {})
            game_counts = {game: 0 for game in GAMES}
            live = []
            next_change = None
            leaders = []
            per_game = {game: [] for game in GAMES}
            for player in players.values():
                if player.get('season') != current['id'] or not player.get('community_name_confirmed'):
                    continue
                stats = player.get('stats') or {}
                net = rounds = 0
                visible = bool(player.get('public_visibility', False))
                for game in GAMES:
                    record = stats.get(game) or {}
                    game_net = int(record.get('net', 0))
                    game_rounds = int(record.get('bets', 0))
                    net += game_net
                    rounds += game_rounds
                    if visible and game_rounds:
                        per_game[game].append(dict(name=player['name'], net=game_net, rounds=game_rounds))
                legacy = stats.get('video_poker') or {}
                net += int(legacy.get('net', 0))
                rounds += int(legacy.get('bets', 0))
                if visible and rounds:
                    leaders.append(dict(name=player['name'], net=net, rounds=rounds))
                last_action = float(player.get('last_action_at', 0) or 0)
                age = max(0, now - last_action) if last_action else PUBLIC_LIVE_SECONDS + 1
                recent_game = 'blackjack' if player.get('blackjack') else 'poker' if player.get('poker') else player.get('last_game', '')
                if last_action and age <= PUBLIC_LIVE_SECONDS and recent_game in GAMES:
                    game_counts[recent_game] += 1
                    transition = (last_action + PUBLIC_NOW_SECONDS
                                  if age <= PUBLIC_NOW_SECONDS and not (player.get('blackjack') or player.get('poker'))
                                  else last_action + PUBLIC_LIVE_SECONDS)
                    if transition > now:
                        next_change = transition if next_change is None else min(next_change, transition)
                    if visible:
                        status = 'In a hand' if player.get('blackjack') or player.get('poker') else ('Playing now' if age <= PUBLIC_NOW_SECONDS else 'Recently active')
                        live.append(dict(name=player['name'], game=recent_game, game_label=self._game_label(recent_game),
                                         status=status, last_action_at=int(last_action)))

            def ranked(rows):
                rows.sort(key=lambda row: (-row['net'], -row['rounds'], row['name'].casefold()))
                result = rows[:PUBLIC_LEADER_LIMIT]
                for index, row in enumerate(result, 1):
                    row['rank'] = index
                return result

            leaders = ranked(leaders)
            game_leaders = {game: ranked(rows) for game, rows in per_game.items()}
            live.sort(key=lambda row: (-row['last_action_at'], row['name'].casefold()))
            value = dict(
                generated_at=int(now), season=current, revision=revision,
                live_players=live[:PUBLIC_LIVE_LIMIT], weekly_leaders=leaders,
                game_leaders=game_leaders,
                game_counts={game: count for game, count in game_counts.items() if count},
                active_count=sum(game_counts.values()),
            )
            with self._public_cache_lock:
                self._public_cache_key = cache_key
                self._public_cache_value = copy.deepcopy(value)
                self._public_cache_expires_at = next_change if next_change is not None else float('inf')
            return value

    def leaders(self, now=None):
        """Private rankings from settled ledger totals, never client-reported wins."""
        current = season(now)
        with self.store.connection() as conn:
            data = conn.get('gaming') or {}
            players = data.get('players', {})
            guard = data.get('ip_guard') or {}
            networks = {}
            if guard.get('season') == current['id']:
                for digest, owners in guard['claims'].items():
                    address = guard.get('addresses', {}).get(digest)
                    if address:
                        for key in ([owners] if isinstance(owners, str) else owners):
                            networks.setdefault(key, []).append(address)
            result, counts = {}, {}
            active = {key:p for key,p in players.items() if p['season']==current['id']}
            def game_stats(player, game):
                # A live recovery import may predate startup migration. Keep its
                # Video Poker rankings separate even before that player visits.
                if player.get('poker_stats_version', 1) == 1:
                    if game == 'poker': return {}
                    if game == 'video_poker': return player['stats'].get('poker', {})
                return player['stats'].get(game, {})
            for game in (*GAMES, 'video_poker'):
                rows = [dict(name=p['name'], player_tag=key[:12], ips=sorted(networks.get(key, [])),
                             balance=p['balance'], funding_adjustment=p.get('balance_adjustment', 0),
                             public_visibility=bool(p.get('public_visibility', False)),
                             last_game=p.get('last_game', ''), last_action_at=p.get('last_action_at', 0),
                             **game_stats(p, game)) for key,p in active.items() if game_stats(p, game).get('bets')]
                rows.sort(key=lambda p:(-p['net'], -p['paid'], p['player_tag']))
                # Count the complete ledger before slicing the five leaders.
                counts[game] = dict(players=len(rows), rounds=sum(row['bets'] for row in rows))
                result[game] = rows[:5]
            legacy = result.pop('video_poker')
            legacy_counts = counts.pop('video_poker')
            return dict(season=current, games=result, counts=counts, legacy_poker=legacy, legacy_poker_counts=legacy_counts,
                        completed_rounds=sum(c['rounds'] for c in counts.values())+legacy_counts['rounds'],
                        revision=sum(p['version'] for p in active.values()), player_count=len(active),
                        confirmed_players=sum(bool(p.get('community_name_confirmed')) for p in active.values()),
                        last_grant=copy.deepcopy((data.get('admin_grants') or [None])[0]),
                        ip_count=sum(map(len, networks.values())), active_hands=sum(bool(p.get('blackjack') or p.get('poker')) for p in active.values()))

    def recovery(self):
        with self.store.connection() as conn:
            return copy.deepcopy(conn.get('gaming'))
```

## `holdem.py`

```python
"""Heads-up no-limit Hold'em, RedPoints only, with a reproducible computer seat.

A hand reserves equal table stacks. Only chips actually committed count as wagers.
The deck is fixed before decisions; the opponent receives a deliberately restricted
observation, never the player's cards, unrevealed board, seed, or deck. Keep this
versioned policy stable so archived receipts can always be replayed.
"""
from collections import Counter
from itertools import combinations

VARIANT = 'texas_holdem'
POLICY = 'redbot-v1'
MIN_BUY_IN = 20
MAX_BUY_IN = (2**53-1)//2
LABELS = ('High card', 'One pair', 'Two pair', 'Three of a kind', 'Straight',
          'Flush', 'Full house', 'Four of a kind', 'Straight flush')
STREETS = ('preflop', 'flop', 'turn', 'river')
SEATS = ('player', 'computer')


def rank_five(cards):
    """Lexicographic rank including every relevant kicker; suits never break ties."""
    ranks = sorted((14 if c % 13 == 0 else c % 13+1 for c in cards), reverse=True)
    groups = sorted(((count, rank) for rank, count in Counter(ranks).items()), reverse=True)
    unique = sorted(set(ranks))
    straight = (5 if unique == [2, 3, 4, 5, 14] else
                unique[-1] if len(unique) == 5 and unique[-1]-unique[0] == 4 else 0)
    flush = len({c//13 for c in cards}) == 1
    if straight and flush: return (8, straight)
    if groups[0][0] == 4: return (7, groups[0][1], groups[1][1])
    if [x[0] for x in groups] == [3, 2]: return (6, groups[0][1], groups[1][1])
    if flush: return (5, *ranks)
    if straight: return (4, straight)
    if groups[0][0] == 3: return (3, groups[0][1], *sorted((r for n, r in groups if n == 1), reverse=True))
    pairs = sorted((r for n, r in groups if n == 2), reverse=True)
    if len(pairs) == 2: return (2, *pairs, groups[-1][1])
    if pairs: return (1, pairs[0], *sorted((r for n, r in groups if n == 1), reverse=True))
    return (0, *ranks)


def best_hand(cards):
    if (not isinstance(cards, list) or not 5 <= len(cards) <= 7 or len(set(cards)) != len(cards)
            or any(type(c) is not int or not 0 <= c < 52 for c in cards)):
        raise ValueError('Evaluate five to seven different cards.')
    # Equal-ranked combinations choose the lexicographically smallest card IDs.
    # This makes the five highlighted cards identical in both implementations.
    candidates = sorted(combinations(sorted(cards), 5))
    best = max(candidates, key=rank_five)
    rank = rank_five(best)
    return dict(rank=list(rank), cards=list(best), label=LABELS[rank[0]])


def validate_action(value):
    if not isinstance(value, dict) or set(value) != {'action', 'amount'}:
        raise ValueError('Send an action and a whole-point amount.')
    action, amount = value['action'], value['amount']
    if (action not in ('fold', 'check', 'call', 'bet', 'raise', 'all_in') or
            type(amount) is not int or not 0 <= amount <= MAX_BUY_IN or
            (action not in ('bet', 'raise') and amount != 0)):
        raise ValueError('Choose a legal Hold’em action.')
    return dict(action=action, amount=amount)


def bot_action(observation):
    """Published redbot-v1: a small, deterministic heuristic, not an odds claim.

    Accept only this observation. Do not pass the engine, deck, player hole cards
    or server seed here. Tests change hidden cards and assert identical decisions.
    """
    cards, board, legal = observation['hole'], observation['board'], observation['legal']
    ranks = sorted((14 if c % 13 == 0 else c % 13+1 for c in cards), reverse=True)
    if not board:
        strength = (65+ranks[0]*2 if ranks[0] == ranks[1] else
                    ranks[0]*3+ranks[1] + (8 if cards[0]//13 == cards[1]//13 else 0)
                    + (5 if ranks[0]-ranks[1] == 1 else 0))
    else:
        rank = best_hand(cards+board)['rank']
        strength = (rank[1]*2 if rank[0] == 0 else 40+rank[1]*2 if rank[0] == 1
                    else 75 if rank[0] == 2 else 90 if rank[0] == 3 else 110)
    # Occasional reproducible bluffs use only this seat's cards and public state.
    bluff = (sum(cards)+sum(board)+observation['pot']+observation['street_index']) % 13 == 0
    if legal['can_raise'] and observation['raises'] == 0 and (strength >= 80 or (bluff and not legal['call'])):
        target = max(legal['min_raise_to'], observation['highest']+max(observation['big_blind'], observation['pot']//2))
        target = min(target, legal['max_raise_to'])
        if target >= legal['min_raise_to']:
            return dict(action='bet' if observation['highest'] == 0 else 'raise', amount=target)
    if legal['check']:
        return dict(action='check', amount=0)
    # Integer-only price/strength thresholds. No fabricated equity percentages.
    cheap = legal['call']*4 <= observation['pot']
    medium = legal['call']*2 <= observation['pot']
    call = strength >= 90 or (strength >= 65 and medium) or (strength >= 40 and cheap)
    return dict(action='call' if call else 'fold', amount=0)


class Hand:
    def __init__(self, deck, buy_in, button):
        if type(buy_in) is not int or not MIN_BUY_IN <= buy_in <= MAX_BUY_IN:
            raise ValueError('Hold’em table stacks must be at least 20 whole RedPoints.')
        if button not in SEATS or len(deck) != 52 or set(deck) != set(range(52)):
            raise ValueError('Invalid Hold’em deal.')
        self.buy_in, self.deck, self.button = buy_in, deck, SEATS.index(button)
        self.big = max(2, buy_in//50)
        self.small = max(1, self.big//2)
        first = 1-self.button  # Heads-up big blind receives the first card.
        self.holes = [[], []]
        for i in range(4): self.holes[(first+i)%2].append(deck[i])
        # Burn before flop, turn and river. Every card is fixed before any move.
        self.boards = [[], deck[5:8], deck[5:8]+[deck[9]], deck[5:8]+[deck[9], deck[11]]]
        self.stacks, self.committed, self.bets = [buy_in, buy_in], [0, 0], [0, 0]
        self.acted, self.raises = [False, False], [0, 0]
        self.street, self.actor, self.last_raise = 0, self.button, self.big
        self.ended, self.winner, self.reason = False, None, None
        self.refunds, self.awards, self.hands = [0, 0], [0, 0], [None, None]
        self.pot_at_end = 0
        self.events = []
        self.pay(self.button, self.small)
        self.pay(1-self.button, self.big)
        self.event('deal', seat=None, action='blinds', amount=self.small+self.big)

    def pay(self, seat, amount):
        self.stacks[seat] -= amount
        self.committed[seat] += amount
        self.bets[seat] += amount

    def legal(self, seat):
        if self.ended: return {}
        high = max(self.bets)
        call = min(self.stacks[seat], high-self.bets[seat])
        maximum = self.bets[seat]+self.stacks[seat]
        can_raise = maximum > high and self.stacks[1-seat] > 0
        return dict(fold=True, check=call == 0, call=call,
                    can_raise=can_raise, min_raise_to=high+self.last_raise,
                    max_raise_to=maximum, all_in=self.stacks[seat] > 0 and (can_raise or self.stacks[seat] <= call))

    def snapshot(self):
        reveal = self.ended and self.reason == 'showdown'
        return dict(player=self.holes[0][:], computer=self.holes[1][:] if reveal else [None, None],
                    board=self.boards[self.street][:], stacks=self.stacks[:], bets=self.bets[:],
                    pot=self.pot_at_end if self.ended else sum(self.committed),
                    street=STREETS[self.street], turn=None if self.ended else SEATS[self.actor],
                    ended=self.ended, winner=self.winner, reason=self.reason)

    def event(self, kind, **extra):
        self.events.append(dict(kind=kind, **extra, state=self.snapshot()))

    def observation(self):
        seat = self.actor
        return dict(hole=self.holes[seat][:], board=self.boards[self.street][:],
                    legal=self.legal(seat), pot=sum(self.committed), highest=max(self.bets),
                    big_blind=self.big, street_index=self.street, raises=self.raises[seat])

    def finish(self, winner=None):
        # Return any uncalled portion before awarding the contested pot.
        matched = min(self.committed)
        self.refunds = [amount-matched for amount in self.committed]
        for i in range(2):
            self.stacks[i] += self.refunds[i]
            self.committed[i] -= self.refunds[i]
        self.pot_at_end = sum(self.committed)
        self.reason = 'fold' if winner is not None else 'showdown'
        if winner is None:
            self.hands = [best_hand(hole+self.boards[3]) for hole in self.holes]
            ranks = [tuple(hand['rank']) for hand in self.hands]
            winner = 0 if ranks[0] > ranks[1] else 1 if ranks[1] > ranks[0] else -1
        self.winner = 'split' if winner == -1 else SEATS[winner]
        if winner == -1:
            self.awards = [self.pot_at_end//2]*2
            # With equal whole-point contributions the heads-up pot is even.
            # Retain the standard odd-chip rule for completeness.
            self.awards[1-self.button] += self.pot_at_end % 2
        else:
            self.awards[winner] = self.pot_at_end
        for i in range(2): self.stacks[i] += self.awards[i]
        self.ended = True
        self.event('settle', seat=self.winner, action=self.reason, amount=self.pot_at_end)
        if sum(self.stacks) != self.buy_in*2 or min(self.stacks) < 0:
            raise ValueError('Hold’em chips did not balance.')

    def advance(self):
        if self.street == 3:
            self.finish()
            return
        self.street += 1
        self.bets, self.acted, self.raises = [0, 0], [False, False], [0, 0]
        self.last_raise, self.actor = self.big, 1-self.button
        self.event('street', seat=None, action=STREETS[self.street], amount=0)
        if 0 in self.stacks:
            self.advance()

    def move(self, value):
        value = validate_action(value)
        if self.ended: raise ValueError('This Hold’em hand is already complete.')
        seat, other = self.actor, 1-self.actor
        legal, action, amount = self.legal(seat), value['action'], value['amount']
        if action == 'fold':
            self.event('action', seat=SEATS[seat], action=action, amount=0)
            self.finish(other)
            return
        if action == 'check':
            if not legal['check']: raise ValueError('Call, raise or fold when facing a bet.')
            paid = 0
        elif action == 'call':
            if not legal['call']: raise ValueError('There is no bet to call. Check instead.')
            paid = legal['call']
        else:
            high = max(self.bets)
            if action == 'all_in':
                if not legal['all_in']: raise ValueError('All-in is not available.')
                amount = legal['max_raise_to']
            elif (action == 'bet') != (high == 0):
                raise ValueError('Use Bet to open a street, or Raise to increase an existing bet.')
            if amount <= high:
                if action != 'all_in' or self.stacks[seat] > legal['call']:
                    raise ValueError('A raise must increase the current bet.')
            else:
                if (not legal['can_raise'] or amount > legal['max_raise_to'] or
                        (amount < legal['min_raise_to'] and amount != legal['max_raise_to'])):
                    raise ValueError('Raise by at least the last full raise, or go all-in.')
                increase = amount-high
                if increase >= self.last_raise: self.last_raise = increase
                self.raises[seat] += 1
                self.acted[other] = False
            paid = amount-self.bets[seat]
        if paid < 0 or paid > self.stacks[seat]: raise ValueError('Not enough chips at the table.')
        self.pay(seat, paid)
        self.acted[seat] = True
        self.actor = other
        self.event('action', seat=SEATS[seat], action=action, amount=paid)
        if self.bets[0] == self.bets[1] and (all(self.acted) or 0 in self.stacks):
            self.advance()
        elif self.stacks[other] == 0 and self.bets[seat] >= self.bets[other]:
            # A short all-in call cannot be raised. Return uncalled excess and run out.
            while self.street < 3:
                self.street += 1
                self.event('street', seat=None, action=STREETS[self.street], amount=0)
            self.finish()

    def auto(self):
        while not self.ended and self.actor == 1:
            self.move(bot_action(self.observation()))

    def result(self, actions):
        value = self.snapshot()
        value.update(variant=VARIANT, policy=POLICY, initial=self.holes[0][:], button=SEATS[self.button],
                     small_blind=self.small, big_blind=self.big, buy_in=self.buy_in,
                     legal={} if self.ended else self.legal(0), actions=actions,
                     events=self.events, total_wager=self.committed[0], returned=self.awards[0],
                     refunds=self.refunds[:], best=self.hands[:],
                     payout=self.stacks[0] if self.ended else 0)
        if self.ended: value['computer'] = self.holes[1][:]
        return value


def replay(draw, buy_in, options, actions=None, ending=None):
    if options.get('variant') != VARIANT or set(options) != {'variant', 'button'}:
        raise ValueError('Invalid Hold’em options.')
    if not isinstance(actions, list) or len(actions) > 4096:
        raise ValueError('Invalid Hold’em action history.')
    # A full Fisher–Yates deck is committed once; later choices cannot reshuffle it.
    deck = list(range(52))
    for i in range(51):
        j = i+draw.below(52-i)
        deck[i], deck[j] = deck[j], deck[i]
    hand = Hand(deck, buy_in, options['button'])
    hand.auto()
    moves = []
    for action in actions:
        move = validate_action(action)
        if hand.ended or hand.actor != 0: raise ValueError('Action after the hand ended.')
        hand.move(move)
        moves.append(move)
        hand.auto()
    if ending is not None:
        if ending != 'weekly_reset' or hand.ended:
            raise ValueError('Invalid automatic Hold’em settlement.')
        # An expired week never places another wager on the player's behalf.
        hand.move(dict(action='fold', amount=0))
    return hand.result(moves)
```

## `integrations.py`

```python
"""Official provider requests with bounded waits and secret-free failures."""
from datetime import datetime, timezone
from decimal import Decimal
from email.utils import parsedate_to_datetime
import json
import threading
import time
from urllib.parse import quote

import requests


class ProviderError(RuntimeError):
    def __init__(self, message, *, retry_after=0, status=None, kind="unknown"):
        super().__init__(message)
        self.retry_after, self.status = retry_after, status
        self.kind = kind


def retry_delay(value):
    try:
        return max(0, int(value))
    except (ValueError, TypeError):
        try:
            stamp = parsedate_to_datetime(str(value))
            return max(0, int((stamp - datetime.now(timezone.utc)).total_seconds()))
        except (ValueError, TypeError, OverflowError):
            return 0


def classify_shuffle_bad_request(response):
    """Classify a Shuffle 400 without logging or returning its raw response.

    The API's error body can contain arbitrary user-controlled text. We only
    inspect up to 4 KiB for fixed date parameter names; other HTTP 400s are
    deliberately called bad_request, not misdiagnosed as date errors.
    """
    try:
        fragment = next(iter(response.iter_content(4096)), b'')[:4096]
        # Strings are used ONLY for allowlisted evidence, never displayed.
        content = fragment.decode('utf-8', errors='ignore').lower()
        if any(mark in content for mark in (
                'starttime', 'endtime', 'start_time', 'end_time',
                'timestamp', 'date range', 'date_window', 'invalid date')):
            return 'window'
    except (TypeError, ValueError, RuntimeError):
        pass
    return 'bad_request'


class Providers:
    def __init__(self, config):
        self.config, self.local = config, threading.local()
        self.token, self.token_until = "", 0
        # Shuffle's affiliate endpoint has shown intermittent HTTP 400s when
        # active and historical checks overlap. Serialize only Shuffle calls;
        # Kick and EmpireDrop retain independent workers.
        self.shuffle_lock = threading.Lock()

    def request(self, method, url, service, *, read_timeout=20, **kwargs):
        self.local.http_status = None
        self.local.provider_reason = None
        # Each background thread owns its session; cookies/auth do not cross.
        if not hasattr(self.local, "session"):
            self.local.session = requests.Session()
            self.local.session.headers.update(Accept="application/json", **{"User-Agent":"RedHunllef/16"})
        try:
            # Redirects could leak a key in a URL or Authorization header. Only
            # the configured official endpoint is allowed to handle the request.
            with self.local.session.request(method, url, timeout=(5, read_timeout), allow_redirects=False, stream=True, **kwargs) as response:
                code = response.status_code
                self.local.http_status = code
                if code == 429 or code >= 500:
                    raise ProviderError(f"{service} returned HTTP {code}; retrying automatically.",
                                        retry_after=retry_delay(response.headers.get("Retry-After")), status=code,
                                        kind="rate_limit" if code == 429 else "upstream")
                if code in (401, 403):
                    raise ProviderError(f"{service} rejected the credentials or access permissions (HTTP {code}).", status=code, kind="access")
                if not 200 <= code < 300:
                    if service == "Shuffle" and code == 400:
                        category = classify_shuffle_bad_request(response)
                        self.local.provider_reason = category
                        # Never surface provider response bodies, request URLs,
                        # keys, or user-specific fields in errors or logs.
                        explanation = (
                            "Shuffle rejected the request's date parameters (HTTP 400). Review the saved race window."
                            if category == 'window' else
                            "Shuffle rejected a request parameter (HTTP 400). Check the date range and configured affiliate endpoint."
                        )
                        raise ProviderError(explanation, status=400, kind=category)
                    raise ProviderError(f"{service} returned HTTP {code}.", status=code, kind="http")
                body = bytearray()
                deadline = time.monotonic() + max(30, read_timeout)
                for chunk in response.iter_content(65536):
                    body.extend(chunk)
                    if len(body) > 8 * 1024 * 1024 or time.monotonic() > deadline:
                        raise ProviderError(f"{service} response exceeded its size or time allowance.", kind="response_limit")
                try:
                    return json.loads(body, parse_float=Decimal)
                except (ValueError, UnicodeDecodeError):
                    raise ProviderError(f"{service} returned invalid JSON.", kind="format") from None
        except requests.ConnectTimeout:
            raise ProviderError(f"{service} connection timed out; check outbound connectivity.", kind="connect_timeout") from None
        except requests.Timeout:
            raise ProviderError(f"{service} timed out; previous results are retained and checks continue.", kind="timeout") from None
        except requests.RequestException:
            raise ProviderError(f"{service} could not be reached; check outbound connectivity.", kind="connection") from None

    def shuffle(self, site):
        key = self.config.credentials["shuffle_api_key"]
        if not key:
            raise ProviderError("Shuffle API key is missing. Add SHUFFLE_API_KEY and restart.", kind="credentials")
        start, end = site["start_time"], min(site["end_time"], int(time.time()))
        self.local.request_meta = {
            "method": "GET", "endpoint_kind": str(self.config.endpoint)[:40],
            "start": int(start), "end": int(end), "timestamp_unit": "seconds",
            "query_keys": ["startTime", "endTime"],
        }
        if not 0 < start < end:
            self.local.provider_reason = "window"
            raise ProviderError("The race does not have an active or completed date window.", kind="window")
        with self.shuffle_lock:
            data = self.request("GET", "https://affiliate.shuffle.com/" + self.config.endpoint + "/" + quote(key, safe=""),
                                "Shuffle", params={"startTime": start, "endTime": end},
                                # Completed-week queries may take longer than a live
                                # window. The wait stays bounded and off web threads.
                                read_timeout=45 if site["end_time"] <= int(time.time()) else 20)
        rows = data if isinstance(data, list) else next((data[k] for k in ("data", "results", "leaderboard", "users", "items")
                    if isinstance(data, dict) and isinstance(data.get(k), list)), None)
        if rows is None or len(rows) > 10000:
            raise ProviderError("Shuffle returned an unsupported leaderboard format or over 10,000 source records.", kind="format")
        return rows

    def kick(self, site):
        keys = self.config.credentials
        if not keys["kick_client_id"] or not keys["kick_client_secret"]:
            raise ProviderError("Kick client credentials are missing. Configure them and restart.")
        for attempt in range(2):
            if attempt or not self.token or time.time() >= self.token_until:
                data = self.request("POST", "https://id.kick.com/oauth/token", "Kick authorization",
                                    data={"grant_type":"client_credentials", "client_id":keys["kick_client_id"], "client_secret":keys["kick_client_secret"]})
                if not isinstance(data, dict) or not isinstance(data.get("access_token"), str):
                    raise ProviderError("Kick did not return a valid app access token.")
                self.token = data["access_token"]
                try:
                    self.token_until = time.time() + max(1, int(data.get("expires_in", 3600)) - 60)
                except (TypeError, ValueError):
                    raise ProviderError("Kick returned an invalid token expiry.") from None
            try:
                data = self.request("GET", "https://api.kick.com/public/v1/channels", "Kick",
                                    params={"slug":site["kick_channel_slug"]}, headers={"Authorization":"Bearer " + self.token})
                break
            except ProviderError as exc:
                if exc.status != 401 or attempt:
                    raise
        rows = data.get("data") if isinstance(data, dict) else None
        channel = next((r for r in rows or [] if isinstance(r, dict) and str(r.get("slug", "")).casefold() == site["kick_channel_slug"].casefold()), None)
        if channel is None:
            raise ProviderError("Kick did not return the configured channel.")
        stream = channel.get("stream")
        if not isinstance(stream, dict) or not isinstance(stream.get("is_live"), bool):
            raise ProviderError("Kick did not provide a valid live status.")
        viewers = stream.get("viewer_count")
        return dict(live=stream["is_live"], title=str(channel.get("stream_title") or stream.get("title") or "")[:240],
                    viewers=int(viewers) if isinstance(viewers, (int, Decimal)) and not isinstance(viewers, bool) and viewers > 0 and stream["is_live"] else None,
                    category=str((channel.get("category") or {}).get("name", ""))[:120], channel=site["kick_channel_slug"])

    def close(self):
        if hasattr(self.local, "session"):
            self.local.session.close()

    def last_http_status(self):
        return getattr(self.local, "http_status", None)

    def last_request_meta(self):
        value = getattr(self.local, "request_meta", None)
        return dict(value) if isinstance(value, dict) else {}

    def last_provider_reason(self):
        value = getattr(self.local, "provider_reason", None)
        return value if value in {"window", "bad_request"} else None
```

## `operations_log.py`

```python
"""Small, bounded, structured operational events for RedHunllef admins.

This is intentionally NOT a raw request logger. Payloads, usernames, player
identifiers, passwords, session cookies, API keys, IPs and provider URLs are
never accepted as log fields. A caller may supply only allowlisted event codes
and bounded numeric facts. Logs are process-local and reset on restart.
"""
from collections import Counter, deque
from datetime import datetime, timezone
from threading import RLock
import time

_ALLOWED_SERVICE = {'empiredrop', 'shuffle', 'kick', 'admin', 'system', 'storage'}
_ALLOWED_LEVEL = {'success', 'info', 'warning', 'error'}
_ALLOWED_EVENT = {
    'refresh_ok', 'refresh_failed', 'refresh_queued', 'settings_saved',
    'connection_test', 'backup_export', 'storage_warning', 'server_error',
    'worker_started', 'api_rate_limited', 'data_quality',
    'empire_rewards_draft', 'empire_rewards_published',
    'empire_rewards_save_failed',
}
# Explanatory categories, NOT free-form provider error text.
_ALLOWED_CODE = {
    'access', 'rate_limit', 'format', 'scope', 'selection', 'window', 'bad_request',
    'configuration', 'connection', 'connect_timeout', 'timeout', 'http',
    'upstream', 'response_limit', 'redirect', 'credentials', 'partial',
    'storage', 'unknown', 'empire_settings', 'empire_rewards',
    'empire_schedule', 'shuffle_settings', 'conflict', 'validation', 'none',

}


def _bounded(value, maximum):
    if isinstance(value, bool):
        return None
    try:
        n = int(value)
        return n if 0 <= n <= maximum else None
    except (TypeError, ValueError, OverflowError):
        return None


class ActivityLog:
    def __init__(self, maxlen=300):
        self.events, self.lock, self.sequence = deque(maxlen=maxlen), RLock(), 0

    def record(self, service, level, event, *, duration_ms=None, http_status=None,
               count=None, code=None, received=None, accepted=None, excluded=None,
               unscoped=None):
        if (service not in _ALLOWED_SERVICE or level not in _ALLOWED_LEVEL or
                event not in _ALLOWED_EVENT):
            raise ValueError('Unsupported log event.')
        if code is not None and code not in _ALLOWED_CODE:
            # Never store an exception string masquerading as an error code.
            code = 'unknown'
        with self.lock:
            now = int(time.time())
            status = _bounded(http_status, 599)
            duration = _bounded(duration_ms, 600000)
            numeric = {
                'count': _bounded(count, 100000),
                'received': _bounded(received, 100000),
                'accepted': _bounded(accepted, 100000),
                'excluded': _bounded(excluded, 100000),
                'unscoped': _bounded(unscoped, 100000),
            }
            # Collapse repeated identical warnings rather than presenting a
            # separate alarm every minute. Each event retains its first/last
            # timestamps, latest bounded counters and a repetition count.
            if level in ('warning', 'error') and self.events:
                last = self.events[0]
                if (last['service'], last['level'], last['event'],
                        last['code'], last['http_status']) == (service, level, event, code, status) \
                        and now - last['at'] <= 300:
                    last['at'] = now
                    last['duration_ms'] = duration
                    last.update(numeric)
                    last['occurrences'] = min(100000, last.get('occurrences', 1) + 1)
                    return dict(last)
            self.sequence += 1
            item = {
                'id': self.sequence, 'at': now, 'first_at': now,
                'service': service, 'level': level, 'event': event,
                'code': code, 'duration_ms': duration,
                'http_status': status, **numeric,
                'occurrences': 1,
            }
            self.events.appendleft(item)
            return dict(item)

    def list(self, service='all', level='all', limit=100):
        if service not in _ALLOWED_SERVICE | {'all'} or level not in _ALLOWED_LEVEL | {'all'}:
            raise ValueError('Invalid log filter.')
        try:
            limit = max(1, min(300, int(limit)))
        except (ValueError, TypeError, OverflowError):
            limit = 100
        with self.lock:
            return [dict(x) for x in self.events if
                    (service == 'all' or x['service'] == service) and
                    (level == 'all' or x['level'] == level)][:limit]

    def summary(self, service='all', level='all'):
        """Counters for the currently selected filters, not global totals."""
        rows = self.list(service, level, 300)
        counts = Counter(row['level'] for row in rows)
        failures = [row for row in rows if row['level'] in ('error', 'warning')]
        return {
            'total': len(rows),
            'levels': {name: counts[name] for name in ('success','info','warning','error')},
            'latest_at': rows[0]['at'] if rows else 0,
            'latest_issue_at': failures[0]['at'] if failures else 0,
        }

    def provider_trends(self, sample=20):
        """Small rolling provider reliability summaries for Admin only.

        Occurrences are counted so grouped repeat failures still affect the
        success rate. No provider payload or player information is included.
        """
        try:
            sample = max(1, min(100, int(sample)))
        except (TypeError, ValueError):
            sample = 20
        result = {}
        with self.lock:
            rows = list(self.events)
        for service in ('shuffle', 'empiredrop'):
            checks = []
            for row in rows:
                if row.get('service') != service or row.get('event') not in {'refresh_ok', 'refresh_failed'}:
                    continue
                occurrences = max(1, int(row.get('occurrences') or 1))
                checks.extend([row.get('event') == 'refresh_ok'] * min(occurrences, sample-len(checks)))
                if len(checks) >= sample:
                    break
            successes = sum(1 for ok in checks if ok)
            result[service] = {
                'sample': len(checks), 'successes': successes,
                'failures': len(checks)-successes,
                'success_rate': round((successes/len(checks))*100) if checks else None,
            }
        return result

    def export(self, service='all', level='all'):
        return {
            'format': 'redhunllef-operations-3',
            'generated_at': datetime.now(timezone.utc).isoformat(),
            'retention': 'Last 300 process-local events; clears after restart',
            'summary': self.summary(service,level),
            'provider_trends': self.provider_trends(),
            'events': self.list(service,level,300),
        }
```

## `poker.py`

```python
"""Single-player five-card draw: 9/6 Jacks or Better, one standard deck.

The committed HMAC stream deals without replacement. Holds are a later player
decision: they never reseed or reshuffle the already committed deck. No jokers.
All listed multipliers are total returns, including the original stake.
"""
from collections import Counter

PAYTABLE = {
    'royal_flush': 800, 'straight_flush': 50, 'four_of_a_kind': 25,
    'full_house': 9, 'flush': 6, 'straight': 4, 'three_of_a_kind': 3,
    'two_pair': 2, 'jacks_or_better': 1, 'no_win': 0,
}
LABELS = {
    'royal_flush': 'Royal flush', 'straight_flush': 'Straight flush',
    'four_of_a_kind': 'Four of a kind', 'full_house': 'Full house',
    'flush': 'Flush', 'straight': 'Straight', 'three_of_a_kind': 'Three of a kind',
    'two_pair': 'Two pair', 'jacks_or_better': 'Jacks or better', 'no_win': 'No paying hand',
}


def validate_holds(holds):
    if (not isinstance(holds, list) or len(holds) > 5 or
            any(type(index) is not int or not 0 <= index < 5 for index in holds) or
            len(set(holds)) != len(holds)):
        raise ValueError('Choose which of the five cards to hold.')
    return sorted(holds)


def classify(cards):
    if (not isinstance(cards, list) or len(cards) != 5 or len(set(cards)) != 5 or
            any(type(card) is not int or not 0 <= card < 52 for card in cards)):
        raise ValueError('Poker requires five different standard-deck cards.')
    # Card IDs match Blackjack's display: A,2,...,K within each suit.
    ranks = sorted(14 if card % 13 == 0 else card % 13 + 1 for card in cards)
    counts = Counter(ranks)
    groups = sorted(counts.values(), reverse=True)
    flush = len({card // 13 for card in cards}) == 1
    straight = len(counts) == 5 and (ranks[-1]-ranks[0] == 4 or ranks == [2, 3, 4, 5, 14])
    if flush and ranks == [10, 11, 12, 13, 14]: return 'royal_flush'
    if straight and flush: return 'straight_flush'
    if groups == [4, 1]: return 'four_of_a_kind'
    if groups == [3, 2]: return 'full_house'
    if flush: return 'flush'
    if straight: return 'straight'
    if groups == [3, 1, 1]: return 'three_of_a_kind'
    if groups == [2, 2, 1]: return 'two_pair'
    if groups == [2, 1, 1, 1] and any(rank >= 11 and count == 2 for rank, count in counts.items()):
        return 'jacks_or_better'
    return 'no_win'


def replay(draw, wager, holds=None):
    deck, cursor = list(range(52)), 0

    def card():
        nonlocal cursor
        other = cursor + draw.below(52-cursor)
        deck[cursor], deck[other] = deck[other], deck[cursor]
        value = deck[cursor]
        cursor += 1
        return value

    initial = [card() for _ in range(5)]
    if holds is None:
        return dict(ended=False, initial=initial, cards=initial[:], holds=None,
                    category='playing', multiplier=0, payout=0)
    holds = validate_holds(holds)
    final = [initial[i] if i in holds else card() for i in range(5)]
    category = classify(final)
    multiplier = PAYTABLE[category]
    return dict(ended=True, initial=initial, cards=final, holds=holds,
                category=category, multiplier=multiplier, payout=wager*multiplier)
```

## `presentation.py`

```python
"""Small view models for change review and private recovery status."""
import re

MAX_NUMBER = 2**53 - 1
from race import token
from race_support import fmt_et, money

LABELS = {
    'start_time': 'Starts · Eastern Time', 'end_time': 'Ends · Eastern Time',
    'site_name': 'Website name', 'race_title': 'Race title',
    'race_description': 'Description', 'kick_channel_slug': 'Kick channel',
    'campaign_code_filter': 'Campaign filter', 'stream_url': 'Livestream link',
    'sponsor_name': 'Sponsor name', 'sponsor_url': 'Sponsor link',
    'community_name': 'Community label', 'community_url': 'Community link',
    'responsible_gambling_url': 'Responsible play link',
}


def changes(before, after):
    result = []
    for key, label in LABELS.items():
        old, new = before.get(key), after.get(key)
        if old != new:
            display = fmt_et if key.endswith('_time') else lambda v: str(v or 'Not set')
            result.append(dict(label=label, before=display(old), after=display(new)))
    for rank in range(1, 16):
        old, new = before.get('prizes', {}).get(str(rank), '0'), after.get('prizes', {}).get(str(rank), '0')
        if money(old) != money(new):
            result.append(dict(label=f'Place {rank} prize', before=money(old), after=money(new)))
    return result


def admin_fingerprint(admin):
    # Exclude migration fields and background timestamps. Exporting a checkpoint
    # never increments the settings revision or invalidates an open admin form.
    return token({key: admin.get(key) for key in (
        'users', 'secret_key', 'site_settings', 'overrides', 'race_history', 'banned_ips', 'audit_log')})


def gaming_fingerprint(value):
    return token({key: [p['version'], p['season'], p['name']] for key,p in value['players'].items()}) if value else ''


def export_marker(admin, snapshot, generated_at, gaming=None):
    return dict(generated_at=generated_at, admin_token=admin_fingerprint(admin),
                standings_token=token(snapshot['last_top15']),
                gaming_token=gaming_fingerprint(gaming))


def valid_marker(value):
    """Accept new checkpoints and safely upgrade older checkpoint markers."""
    if not isinstance(value, dict):
        return None
    generated = value.get('generated_at')
    if type(generated) is not int or not 0 <= generated <= 10**12:
        return None
    for key, length in (('admin_token', 20), ('standings_token', 20)):
        if not isinstance(value.get(key), str) or not re.fullmatch(r'[a-f0-9]{%d}' % length, value[key]):
            return None
    result = {key: value[key] for key in ('generated_at', 'admin_token', 'standings_token')}
    token_value = value.get('gaming_token', '')
    if isinstance(token_value, str) and re.fullmatch(r'[a-f0-9]{20}|', token_value):
        result['gaming_token'] = token_value
    return result


def checkpoint_status(marker, admin, rows, gaming=None):
    marker = valid_marker(marker)
    if not marker:
        return dict(generated_at=0, label='No recovery export recorded', changes=True,
                    details='Generate a private recovery file to protect this checkpoint.')
    changed = admin_fingerprint(admin) != marker.get('admin_token')
    standings = token(rows[:15]) != marker.get('standings_token')
    gaming_changed = marker.get('gaming_token', '') != gaming_fingerprint(gaming)
    notes = []
    if changed: notes.append('account or race settings changed')
    if standings: notes.append('standings changed')
    if gaming_changed: notes.append('RedPoints wallets or fairness receipts changed')
    return dict(generated_at=marker.get('generated_at', 0),
                changes=changed or standings or gaming_changed,
                label='Changes since last export' if notes else 'Checkpoint matches current progress',
                details='; '.join(notes) or 'No new saved progress since this export.')
```

## `provider_admin.py`

```python
"""Safe, provider-agnostic data-quality summaries for the administration UI.

This module never calls a remote API. It reads already-verified local snapshots
and emits only operational metadata; names, player IDs and credentials stay out.
Neither provider's amounts are converted, inferred, or combined here.
"""

from race_support import fmt_et
import time

_ERROR_HELP = {
    'access': 'Check the API key pair and the server outbound IP allowlist.',
    'rate_limit': 'Provider rate limit reached. Leave automatic retry enabled.',
    'format': 'The provider response did not match the documented data format.',
    'scope': 'Check that the selected race belongs to this affiliate account.',
    'selection': 'Select a race slug, or enable auto-select for one running race.',
    'window': 'Check the saved race dates and whether the provider accepts this period.',
    'bad_request': 'Shuffle rejected a request parameter. Review race dates and affiliate endpoint settings.',
    'configuration': 'Review the race mode, slug, and API configuration.',
    'connection': 'Check outbound network connectivity from the application.',
    'http': 'Check the provider status and retry later.',
}


def _int(value):
    return value if type(value) is int and 0 <= value <= 10 ** 12 else 0


def _component(health, key):
    return next((x for x in (health or {}).get('components', [])
                 if isinstance(x, dict) and x.get('key') == key), {})


def summarize_providers(status, empire, trends=None):
    """Return two uniform cards with explicit source-quality indicators.

    status: output of Runtime.status() (admin only)
    empire: output of EmpireDropBoard.private_status() (admin only)
    Every displayed field is operational or aggregated, never a credential.
    """
    health = status.get('health') or {}
    jobs = status.get('jobs') or {}
    shuffle = jobs.get('shuffle') or {}
    quality = status.get('diagnostics') or {}
    s_health = _component(health, 'shuffle')
    e_health = _component(health, 'empiredrop')
    received = _int(quality.get('received'))
    accepted = _int(quality.get('accepted'))
    missing = _int(quality.get('missing_campaign'))
    rejected = quality.get('rejected') or {}
    rejected_total = sum(_int(n) for n in rejected.values()) if isinstance(rejected, dict) else 0
    excluded_total = max(0, received - accepted)
    ranked = _int(status.get('count'))
    trends = trends or {}
    s_trend = trends.get('shuffle') or {}
    e_trend = trends.get('empiredrop') or {}
    s_issues = []
    if not _int(shuffle.get('last_success')):
        s_issues.append('No verified Shuffle response yet.')
    if missing:
        s_issues.append(f'{missing:,} source record(s) lack campaign metadata.')
    if excluded_total:
        s_issues.append(f'{excluded_total:,} source record(s) were excluded by validation or campaign filtering.')
    if shuffle.get('error'):
        http_status = shuffle.get('http_status')
        s_issues.append(
            'Latest request returned HTTP 400. Review the saved race window and endpoint; this does not prove the API key is invalid.'
            if http_status == 400 else
            'Latest check failed. Previous verified results are retained.'
        )
    site = status.get('site') or {}
    end_time = _int(site.get('end_time'))
    if end_time and end_time < time.time() - 86400:
        s_issues.append(
            'The saved Shuffle race ended on ' + fmt_et(end_time) +
            '. This is a historical window. Open Schedule & prizes to prepare a current race; changes require confirmation.'
        )
    rows = status.get('rows') or []
    s_card = {
        'key': 'shuffle', 'name': 'Shuffle',
        'state': s_health.get('state', 'warning'),
        'status': s_health.get('status', 'Waiting for source'),
        'last_success': _int(shuffle.get('last_success')),
        'last_attempt': _int(shuffle.get('attempt_at')),
        'refresh_seconds': 60,
        'participants': ranked,
        'loaded': len(rows) if isinstance(rows, list) else 0,
        'metric': 'Weighted wager',
        'scope': ('Shuffle window: ' + str((status.get('site') or {}).get('start_et') or 'Not configured') + ' → ' +
                  str((status.get('site') or {}).get('end_et') or 'Not configured')),
        'quality': (f'{ranked:,} ranked player(s) from {received:,} source record(s) · '
                    f'{accepted:,} accepted · {excluded_total:,} excluded · {missing:,} without campaign metadata'
                    if received else 'Waiting for source records'),
        'trend': s_trend,
        'request_meta': shuffle.get('request_meta') or {},
        'provider_reason': shuffle.get('provider_reason'),
        'issues': s_issues, 'action': '/admin/leaderboards/shuffle',
        'details': '/admin/leaderboards/shuffle/players',
    }
    meta = empire.get('race_meta') or {}
    erows = empire.get('rows') or []
    mode = empire.get('source_mode') or 'races'
    engine, kind = meta.get('engine'), meta.get('type')
    metric = ('Tickets' if engine == 'RAFFLE' else
              'Deposited' if kind == 'DEPOSIT' else 'Wagered')
    e_issues = []
    if not _int(empire.get('updated_at')):
        e_issues.append('No verified EmpireDrop race response yet.')
    kind_error = empire.get('error_kind')
    if kind_error:
        e_issues.append(_ERROR_HELP.get(kind_error, 'Check the selected race and provider connection.'))
    if meta.get('is_active') is False:
        e_issues.append('This race has closed. The provider may return an empty live ranking.')
    if engine == 'RAFFLE':
        e_issues.append('Raffle totals represent tickets, not wagered currency.')
    if kind == 'DEPOSIT' and engine != 'RAFFLE':
        e_issues.append('This race ranks deposits, not wagers.')
    e_card = {
        'key': 'empiredrop', 'name': 'EmpireDrop',
        'state': e_health.get('state', 'warning'),
        'status': e_health.get('status', 'Waiting for source'),
        'last_success': _int(empire.get('updated_at')),
        'last_attempt': _int(empire.get('attempt_at')),
        'refresh_seconds': max(60, min(86400, _int(empire.get('refresh_interval')) or 300)),
        'participants': len(erows) if isinstance(erows, list) else 0,
        'loaded': len(erows) if isinstance(erows, list) else 0,
        'metric': metric,
        'scope': ('Official race: ' + str(meta.get('slug') or 'Not selected')[:100]) if mode == 'races' else
                 ('Custom date window (deprecated API)' if mode == 'legacy_window' else 'Legacy adapter'),
        'quality': (f'{len(erows):,} verified position(s) / provider cap {meta["ranks_limit"]}'
                    if isinstance(erows, list) and type(meta.get('ranks_limit')) is int
                    else 'Awaiting provider ranking confirmation'),
        'trend': e_trend,
        'request_meta': {},
        'provider_reason': empire.get('error_kind'),
        'issues': e_issues, 'action': '/admin/leaderboards/empiredrop',
        'details': '/admin/leaderboards/empiredrop/source',
    }
    return {'shuffle': s_card, 'empiredrop': e_card}
```

## `race.py`

```python
"""Pure race calculations: exact decimal rankings and one public projection."""
from decimal import Decimal, localcontext
import hashlib
import json
import time

from race_support import decimal_amount, money, race_key

NAMES = ("username", "displayName", "userName", "player", "name")
WEIGHTED = ("weightedWagerAmount", "weightedWager", "weightedAmount", "wagerWeighted")
RAW = ("wagerAmount", "totalWagered", "wageredAmount", "rawWagerAmount")
CAMPAIGN = ("campaignCode", "campaign", "code", "referralCode", "affiliateCode")


def first(row, keys):
    return next((row[k] for k in keys if row.get(k) is not None), None)


def phase(site, now=None):
    now = time.time() if now is None else now
    start, end = site["start_time"], site["end_time"]
    return "unconfigured" if not start or end <= start else "upcoming" if now < start else "ended" if now >= end else "active"


def token(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(",", ":")).encode()).hexdigest()[:20]


def normalize(rows, site, raw_fallback=False):
    accepted, red, rejected, missing_campaign = [], [], {}, 0
    for row in rows:
        reason = None
        if not isinstance(row, dict):
            reason = "invalid record"
        else:
            name, weighted, raw, campaign = first(row, NAMES), first(row, WEIGHTED), first(row, RAW), first(row, CAMPAIGN)
            campaign = None if campaign is None else str(campaign).strip().casefold()
            if not isinstance(name, str) or not name.strip() or len(name) > 64:
                reason = "missing or invalid username"
            elif weighted is None and not raw_fallback:
                reason = "missing weighted amount"
            else:
                try:
                    amount = decimal_amount(raw if weighted is None else weighted)
                except ValueError:
                    reason = "invalid weighted amount"
                if reason is None:
                    raw_invalid = False
                    try:
                        raw_amount = None if raw is None else str(decimal_amount(raw))
                    except ValueError:
                        raw_amount, raw_invalid = None, True
                    item = dict(username=name.strip(), weighted=str(amount), raw=raw_amount, raw_invalid=raw_invalid, row_count=1)
                    if campaign == "red":
                        red.append(item)
                    if campaign is None:
                        missing_campaign += 1
                    expected = site.get("campaign_code_filter", "").strip().casefold()
                    if not expected or campaign is None or campaign == expected:
                        accepted.append(item)
                    else:
                        reason = "other campaign"
        if reason:
            rejected[reason] = rejected.get(reason, 0) + 1
    invalid = sum(v for k, v in rejected.items() if k != "other campaign")
    if invalid and not accepted:
        raise ValueError("Shuffle returned no usable race records. Previous results are retained.")
    warning = f"{invalid} incomplete source record(s) skipped; rankings may be incomplete." if invalid else ""
    if any(row["raw_invalid"] for row in accepted):
        warning += " Some raw totals are unavailable; valid weighted totals still update."
    return dict(source=accepted, red_source=red, rejected=rejected, missing_campaign=missing_campaign,
                received=len(rows), accepted=len(accepted), warning=warning.strip())


def aggregate(rows, mode="sum"):
    result = {}
    for row in rows:
        name = row["username"]
        if name not in result:
            result[name] = dict(row)
            continue
        old = result[name]
        old["row_count"] += row.get("row_count", 1)
        old["raw_invalid"] = old.get("raw_invalid", False) or row.get("raw_invalid", False)
        for key in ("weighted", "raw"):
            if row.get(key) is not None:
                with localcontext() as ctx:
                    ctx.prec = 60
                    a, b = decimal_amount(old.get(key) or 0), decimal_amount(row[key])
                    old[key] = str(max(a, b) if mode == "max" else a + b)
    for row in result.values():
        if row.get("raw_invalid"):
            row["raw"] = None
    return result


def rank(source, overrides, mode="sum", limit=300):
    values = aggregate(source, mode)
    for name in overrides:
        values.setdefault(name, dict(username=name, weighted=None, raw=None, row_count=1))
    ordered = sorted(values.values(), key=lambda r: (-decimal_amount(overrides.get(r["username"], r["weighted"]) or 0), r["username"].casefold(), r["username"]))
    ranked, edits, count = [], [], 0
    for row in ordered:
        original = row["weighted"]
        amount = overrides.get(row["username"], original) or "0"
        qualifies = decimal_amount(amount) >= Decimal("0.01")
        count += int(qualifies)
        item = dict(rank=count if qualifies else None, username=row["username"], weighted_wager=amount,
                    wager=money(amount), original_weighted_wager=original, original_weighted_str=money(original),
                    raw_wager=row["raw"], raw_wager_str=money(row["raw"]), row_count=row.get("row_count", 1),
                    source="override" if row["username"] in overrides else "shuffle")
        if qualifies and len(ranked) < limit:
            ranked.append(item)
        if item["source"] == "override":
            edits.append(item)
    return ranked, edits, count


def empty(site):
    return dict(key=race_key(site), source=[], red_source=[], rows=[], edits=[], red=[], red_total=0, count=0,
                updated_at=0, attempt_at=0, ok=None, error="", warning="", received=0, accepted=0,
                rejected={}, missing_campaign=0, previous_top=[], snapshot_only=False)


def calculate(snapshot, admin, config):
    result = dict(snapshot)
    site = admin["site_settings"]
    rows, edits, count = rank(result["source"], admin["overrides"], config.aggregation, config.limit)
    # Code Red includes raw wagerers with zero weighted contribution, too.
    red = aggregate(result.get("red_source", []), config.aggregation)
    red = [r for r in red.values() if max(decimal_amount(r["weighted"]), decimal_amount(r.get("raw") or 0)) >= Decimal("0.01")]
    red.sort(key=lambda r: (-decimal_amount(r["weighted"]), r["username"].casefold(), r["username"]))
    result.update(rows=rows, edits=edits, count=count,
                  red=[dict(username=r["username"], weighted=money(r["weighted"]), raw=money(r["raw"])) for r in red[:100]], red_total=len(red))
    if phase(site) in {"upcoming", "unconfigured"}:
        result.update(rows=[], red=[], red_total=0, count=0)
        result["edits"] = [{**r, "rank": None} for r in edits]
    result["revision"] = token([race_key(site), result["rows"], result["edits"], result["red"], result.get("warning")])
    return result


def freshness(snapshot):
    stamp = snapshot.get("updated_at", 0)
    stale = bool(snapshot.get("snapshot_only") or snapshot.get("error") or (stamp and time.time() - stamp > 180))
    state = "delayed" if stale else "waiting" if not stamp else "partial" if snapshot.get("warning") else "current"
    return dict(state=state, updated_at=stamp, attempt_at=snapshot.get("attempt_at", 0),
                label={"delayed":"Updates delayed", "waiting":"Waiting for source data", "partial":"Updated with incomplete data", "current":"Up to date"}[state],
                warning=snapshot.get("warning", ""), error=snapshot.get("error", ""))
```

## `race_support.py`

```python
"""Pure validation, Eastern Time conversion, and safe JSON file operations.

This module has no Flask state and makes no network requests. Decimal values
remain exact until they are formatted; persistent amounts use decimal strings.
"""
from __future__ import annotations

import hashlib
import json
import re
import time
from datetime import datetime, timezone
from decimal import Decimal, InvalidOperation
from pathlib import Path
from urllib.parse import urlsplit
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

try:
    EASTERN = ZoneInfo("America/New_York")
except ZoneInfoNotFoundError as exc:
    raise RuntimeError("Eastern Time data is missing. Install requirements.txt, including tzdata.") from exc

STORE_VERSION = 7
DEFAULT_PRIZES = dict(enumerate(
    [1800, 1200, 800, 450, 200, 150, 90, 80, 70, 60, 20, 20, 20, 20, 20], 1
))
WEIGHTING_RULES = [
    {"range": "RTP ≤ 98%", "counts": "100% counts"},
    {"range": "98% < RTP < 99%", "counts": "50% counts"},
    {"range": "RTP ≥ 99%", "counts": "10% counts"},
]
TEXT_LIMITS = {
    "site_name": 60, "race_title": 100, "race_description": 240,
    "sponsor_name": 60, "community_name": 60, "campaign_code_filter": 64,
}
URL_FIELDS = ("sponsor_url", "stream_url", "community_url", "responsible_gambling_url")
OPTIONAL_URLS = {"community_url", "responsible_gambling_url"}
DECIMAL_PATTERN = re.compile(r"^\+?(?:\d+(?:\.\d*)?|\.\d+)(?:[eE][+-]?\d+)?$")
MONEY_PATTERN = re.compile(r"^\$?\s*(?:\d+|\d{1,3}(?:,\d{3})+)(?:\.\d{1,2})?$")


def decimal_amount(value, *, limit=Decimal("1000000000000000")) -> Decimal:
    """Reject malformed, negative, non-finite, or excessive API amounts."""
    if isinstance(value, bool) or value is None:
        raise ValueError("An amount must be a non-negative number.")
    text = str(value).strip()
    # Legacy snapshots may contain formatted amounts, but arbitrary text must
    # never be stripped into a seemingly valid financial value.
    if "$" in text or "," in text:
        if not MONEY_PATTERN.fullmatch(text):
            raise ValueError("Invalid formatted amount.")
        text = text.replace("$", "").replace(",", "").strip()
    if not DECIMAL_PATTERN.fullmatch(text):
        raise ValueError("Invalid numeric amount.")
    try:
        amount = Decimal(text)
    except InvalidOperation as exc:
        raise ValueError("Invalid numeric amount.") from exc
    if not amount.is_finite() or amount < 0 or amount > limit:
        raise ValueError("Amount is outside the allowed range.")
    return amount


def money_input(value) -> Decimal:
    text = str(value or "").strip()
    if not MONEY_PATTERN.fullmatch(text):
        raise ValueError("Use a non-negative amount such as 25000 or $25,000.00.")
    return decimal_amount(text, limit=Decimal("1000000000000"))


def money(value) -> str:
    if value is None:
        return "—"
    try:
        return "$" + format(decimal_amount(value), ",.2f")
    except ValueError:
        return "—"


def integer(value, default=0) -> int:
    try:
        if isinstance(value, bool):
            return default
        return int(value)
    except (TypeError, ValueError, OverflowError):
        return default


def valid_url(value, *, allow_blank=False) -> bool:
    text = str(value or "").strip()
    if not text:
        return allow_blank
    if len(text) > 2048 or any(ord(c) < 33 for c in text) or "\\" in text:
        return False
    try:
        parsed = urlsplit(text)
        _ = parsed.port  # Validate malformed/out-of-range ports as well.
        return (parsed.scheme in {"http", "https"} and bool(parsed.hostname)
                and not parsed.username and not parsed.password)
    except ValueError:
        return False


def fmt_et(epoch) -> str:
    if not epoch:
        return "Not configured"
    try:
        return datetime.fromtimestamp(int(epoch), EASTERN).strftime("%b %d, %Y · %I:%M %p %Z")
    except (ValueError, OSError, OverflowError, TypeError):
        return "Invalid date"


def local_input(epoch) -> str:
    return datetime.fromtimestamp(int(epoch), EASTERN).strftime("%Y-%m-%dT%H:%M") if epoch else ""


def eastern_epoch(value) -> int:
    """Reject nonexistent and ambiguous DST times instead of guessing an hour."""
    try:
        naive = datetime.strptime(str(value), "%Y-%m-%dT%H:%M")
    except (ValueError, TypeError) as exc:
        raise ValueError("Choose a valid date and time.") from exc
    if not 1970 <= naive.year <= 2099:
        raise ValueError("Choose a year between 1970 and 2099.")
    candidates = set()
    for fold in (0, 1):
        aware = naive.replace(tzinfo=EASTERN, fold=fold)
        epoch = int(aware.timestamp())
        if datetime.fromtimestamp(epoch, EASTERN).replace(tzinfo=None) == naive:
            candidates.add(epoch)
    if not candidates:
        raise ValueError("This Eastern Time does not exist because the clocks move forward. Choose another time.")
    if len(candidates) > 1:
        raise ValueError("This Eastern Time occurs twice when the clocks move back. Choose a time outside the repeated hour.")
    return candidates.pop()


def race_key(site) -> str:
    """The affiliate window defines a race; cosmetic edits do not."""
    identity = [integer(site.get("start_time")), integer(site.get("end_time")),
                str(site.get("campaign_code_filter") or "").strip().casefold()]
    return hashlib.sha256(json.dumps(identity).encode()).hexdigest()[:24]


def empty_snapshots(key) -> dict:
    return {"race_key": key, "last_top15": [], "prev_top15": [], "updated_at": None}


def validate_site(site) -> dict:
    """Return field errors; reused by normal saves and backup restoration."""
    errors = {}
    for key, maximum in TEXT_LIMITS.items():
        value = site.get(key)
        if not isinstance(value, str) or len(value) > maximum:
            errors[key] = "Use text up to " + str(maximum) + " characters."
    for key in ("site_name", "race_title", "sponsor_name"):
        if not str(site.get(key) or "").strip():
            errors[key] = "This field is required."
    start, end = integer(site.get("start_time"), -1), integer(site.get("end_time"), -1)
    if not ((start == 0 and end == 0) or (0 < start < end <= 4102444799)):
        errors["end_et"] = "The end must be after the start, within the supported date range."
    for key in ("start_time", "end_time"):
        if isinstance(site.get(key), bool) or not isinstance(site.get(key), int):
            errors["end_et"] = "Race timestamps must be whole epoch seconds."
    if integer(site.get("refresh_seconds")) != 60:
        errors["refresh_seconds"] = "Automatic updates run every 60 seconds."
    if not re.fullmatch(r"[a-z0-9_-]{2,25}", str(site.get("kick_channel_slug") or "")):
        errors["kick_channel_slug"] = "Use a Kick channel name of 2–25 letters, numbers, underscores, or hyphens."
    for key in URL_FIELDS:
        if not valid_url(site.get(key), allow_blank=key in OPTIONAL_URLS):
            errors[key] = "Enter a complete http or https link without embedded credentials."
    prizes = site.get("prizes")
    if not isinstance(prizes, dict) or set(prizes) != {str(n) for n in range(1, 16)}:
        errors["prizes"] = "Include all 15 placement prizes."
    else:
        for rank, amount in prizes.items():
            try:
                number = money_input(str(amount))
                if number.as_tuple().exponent < -2:
                    raise ValueError("Use at most two decimal places.")
            except ValueError as exc:
                errors["prize_" + rank] = str(exc)
    return errors


def canonical_site(source, defaults) -> dict:
    """Fill legacy missing fields without changing saved race choices."""
    clean = dict(defaults)
    clean.update({k: source[k] for k in defaults if k in source})
    clean["leaderboard_size"] = 15
    # Old saved intervals migrate to the required cadence; race dates and
    # financial values retain their saved meanings.
    clean["refresh_seconds"] = 60
    raw = clean.get("prizes")
    raw = raw if isinstance(raw, dict) else {}
    clean["prizes"] = {
        str(n): str(decimal_amount(raw.get(str(n), DEFAULT_PRIZES[n])))
        for n in range(1, 16)
    }
    return clean


def clean_snapshots(snapshots, key) -> dict:
    """Validate every restored row before it can reach a cache or template."""
    if not isinstance(snapshots, dict):
        raise ValueError("Leaderboard snapshots must be an object.")
    if snapshots.get("race_key", key) != key:
        raise ValueError("Snapshot race does not match its schedule.")
    result = empty_snapshots(key)
    for field in ("last_top15", "prev_top15"):
        rows = snapshots.get(field, [])
        if not isinstance(rows, list) or len(rows) > 15:
            raise ValueError("Each saved leaderboard must contain at most 15 rows.")
        ranks, names = set(), set()
        for row in rows:
            if not isinstance(row, dict):
                raise ValueError("Every snapshot entry must be an object.")
            rank = row.get("rank")
            username = row.get("username")
            if (isinstance(rank, bool) or not isinstance(rank, int) or not 1 <= rank <= 15
                    or rank in ranks or not isinstance(username, str)
                    or not username.strip() or len(username) > 128 or username in names):
                raise ValueError("Snapshot ranks or usernames are invalid or duplicated.")
            ranks.add(rank)
            names.add(username)
            weighted = decimal_amount(row.get("weighted_wager", row.get("wager")))
            raw = row.get("raw_wager")
            # Older stores did not always retain the API total beneath an
            # override. Unknown is more accurate than inventing an original.
            base = row.get("original_weighted_wager", None if row.get("source") == "override" else weighted)
            original = None if base is None else str(decimal_amount(base))
            clean = {
                "rank": rank, "username": username.strip(),
                "weighted_wager": str(weighted), "wager": money(weighted),
                "original_weighted_wager": original,
                "original_weighted_str": money(original),
                "raw_wager": None if raw is None else str(decimal_amount(raw)),
                "raw_wager_str": money(raw),
                "source": "override" if row.get("source") == "override" else "shuffle",
                "row_count": max(1, integer(row.get("row_count"), 1)),
            }
            result[field].append(clean)
        result[field].sort(key=lambda row: row["rank"])
    updated = snapshots.get("updated_at")
    if updated is not None and (isinstance(updated, bool) or not isinstance(updated, int)
                                or updated < 0 or updated > int(time.time()) + 300):
        raise ValueError("Snapshot update time is invalid.")
    result["updated_at"] = updated
    return result


def clean_overrides(value) -> dict:
    if not isinstance(value, dict) or len(value) > 10000:
        raise ValueError("Overrides must be an object with at most 10,000 entries.")
    result = {}
    for username, amount in value.items():
        if not isinstance(username, str) or not username.strip() or len(username) > 64:
            raise ValueError("An override username is invalid.")
        result[username.strip()] = str(money_input(str(amount)))
    return result


def csv_text(value) -> str:
    """Prevent text cells from being interpreted as formulas by spreadsheet apps."""
    text = str(value or "")
    unsafe = text.lstrip().startswith(("=", "+", "-", "@")) or bool(text and text[0] in "\t\r\n")
    return "'" + text if unsafe else text


def read_json(path: Path) -> dict:
    try:
        with path.open(encoding="utf-8") as handle:
            value = json.load(handle)
        if not isinstance(value, dict):
            raise ValueError("The file must contain a JSON object.")
        return value
    except (OSError, ValueError) as exc:
        raise RuntimeError("Cannot read " + str(path) + ". The original file was left untouched. Restore a verified recovery copy.") from exc
```

## `release_check.py`

```python
"""Check a complete release without loading credentials or starting workers."""
import ast
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import re
import argparse

from jinja2 import Environment, FileSystemLoader, TemplateError, meta


def check_release(root=None, strict=False, check_dependencies=True):
    root = Path(root or Path(__file__).parent)
    problems, warnings = [], []
    required = {'flask':'Flask', 'werkzeug':'Werkzeug', 'requests':'requests', 'waitress':'waitress', 'tzdata':'tzdata'}

    # DigitalOcean Spaces support is optional. The S3 SDK is imported lazily by
    # spaces_state.py only when RH_SPACES_ENABLE is explicitly enabled. Do not
    # fail normal local-JSON deployments merely because boto3/botocore are not
    # installed.
    spaces_enabled = os.getenv('RH_SPACES_ENABLE', '').strip().lower() in {'1', 'true', 'yes', 'on'}
    optional_modules = {'boto3', 'botocore'}

    if check_dependencies:
        for module, package in required.items():
            if importlib.util.find_spec(module) is None:
                problems.append('Missing dependency: '+package+'. Install requirements.txt.')
        if spaces_enabled:
            for module in sorted(optional_modules):
                if importlib.util.find_spec(module) is None:
                    problems.append(
                        'Spaces storage is enabled but '+module+
                        ' is not installed. Install requirements-spaces.txt or add boto3 to requirements.txt.'
                    )

    modules = list(root.glob('*.py'))
    for source in modules:
        try:
            tree = ast.parse(source.read_text(encoding='utf-8'), filename=source.name)
            compile(tree, source.name, 'exec')
            for node in ast.walk(tree):
                if isinstance(node, ast.ImportFrom) and node.module and not node.level:
                    name = node.module.split('.')[0]
                    if name in optional_modules and not spaces_enabled:
                        continue
                    if importlib.util.find_spec(name) is None and not (root/(name+'.py')).is_file():
                        if check_dependencies or name not in required:
                            problems.append(source.name+' imports missing module '+name)
        except (SyntaxError, UnicodeError) as exc:
            problems.append(source.name+': '+type(exc).__name__)
    environment = Environment(loader=FileSystemLoader(root/'templates'))
    for name in environment.list_templates():
        try:
            text = (root/'templates'/name).read_text(encoding='utf-8')
            tree = environment.parse(text)
            for reference in meta.find_referenced_templates(tree):
                if reference and not (root/'templates'/reference).is_file():
                    problems.append(name+' requires missing template '+reference)
            for asset in re.findall(r"filename\s*=\s*['\"]([^'\"]+)['\"]", text):
                if not (root/'static'/asset).is_file():
                    problems.append(name+' requires missing static/'+asset)
        except (UnicodeError, ValueError, TemplateError) as exc:
            problems.append(name+': '+type(exc).__name__)
    manifest = root/'BUILD_MANIFEST.json'
    if manifest.is_file():
        spec = json.loads(manifest.read_text(encoding='utf-8'))
        for name, expected in spec.get('files', {}).items():
            path = root/name
            if not path.is_file():
                problems.append('Missing release file: '+name)
            elif hashlib.sha256(path.read_bytes()).hexdigest() != expected:
                (problems if strict else warnings).append('File differs from packaged release: '+name)
    if not (root/'templates/index.html').is_file() or not (root/'templates/admin.html').is_file():
        problems.append('The templates folder is incomplete.')
    for marker in ('requirements.txt','runtime.txt','wager_backend.py','app.yaml','BUILD_MANIFEST.json'):
        if not (root/marker).is_file():
            problems.append('Missing deployment root file: '+marker)
    return dict(ok=not problems, problems=sorted(set(problems)), warnings=sorted(set(warnings)),
                python_modules=len(modules), templates=len(environment.list_templates()))


def main():
    parser = argparse.ArgumentParser(description='Validate a RedHunllef source release without loading private configuration.')
    parser.add_argument('--root', default=str(Path(__file__).parent))
    parser.add_argument('--strict', action='store_true', help='Treat manifest hash differences as failures.')
    parser.add_argument('--source-only', action='store_true', help='Skip installed dependency checks.')
    args = parser.parse_args()
    result = check_release(args.root, strict=args.strict, check_dependencies=not args.source_only)
    for warning in result['warnings']:
        print('WARNING:', warning)
    for problem in result['problems']:
        print('ERROR:', problem)
    print(('PASS' if result['ok'] else 'FAIL') + f": {result['python_modules']} Python modules, {result['templates']} templates")
    return 0 if result['ok'] else 1


if __name__ == '__main__':
    raise SystemExit(main())
```

## `runtime.py`

```python
"""One runtime, independent live jobs, and cached completed-week history."""
import copy
from decimal import Decimal
import logging
import secrets
import threading
import time

from config import INTERVAL, RELEASE
from integrations import Providers, ProviderError
from storage import Store, StoreError, Conflict
from race import calculate, empty, freshness, normalize, phase, rank, token
from race_support import fmt_et, money, race_key
from weekly_history import WeeklyHistory
from empiredrop import EmpireDropBoard

LOG = logging.getLogger("redhunllef")


class Runtime:
    def __init__(self, config):
        self.config, self.store, self.providers = config, Store(config), Providers(config)
        self.history = WeeklyHistory(config, self.store, self.providers)
        self.empiredrop = EmpireDropBoard(config, self.store)
        self.lock, self.stop_event = threading.RLock(), threading.Event()
        self.revision, self.admin = self.store.admin()
        self.shuffle = self.store.live("shuffle") or empty(self.admin["site_settings"])
        if self.shuffle.get("key") != race_key(self.admin["site_settings"]):
            self.shuffle = empty(self.admin["site_settings"])
        self.restore_edits()
        self.kick = self.store.live("kick") or dict(updated_at=0, attempt_at=0, error="", live=False)
        self.events = {name: threading.Event() for name in ("shuffle", "kick")}
        self.threads, self.started = {}, False
        self.instance_id = secrets.token_hex(8)
        self.activity_log = None  # Injected after construction by Flask.
        self.jobs = {name: dict(state="starting", next_check=0, duration_ms=0, http_status=None,
                               retry_after=0, attempt_at=0, error="", not_before=0,
                               requested=0, completed=0, runs=0, completed_at=0, result="waiting",
                               failure_streak=0, request_meta={}, provider_reason=None,
                               checked_scope="", checked_start=0, checked_end=0, checked_channel="")
                     for name in self.events}

    def restore_edits(self):
        # Imported Top 15 backups may omit the separate overrides view. Keep
        # the saved ranking intact while making every saved edit accessible.
        _, edits, _ = rank(self.shuffle.get("source", []), self.admin["overrides"],
                           self.config.aggregation, self.config.limit)
        if self.shuffle.get("snapshot_only") or phase(self.admin["site_settings"]) in {"upcoming", "unconfigured"}:
            ranks = {row["username"]: row["rank"] for row in self.shuffle["rows"]}
            edits = [{**row, "rank": ranks.get(row["username"])} for row in edits]
        self.shuffle["edits"] = edits

    def sync(self):
        revision, admin = self.store.admin()
        with self.lock:
            if revision != self.revision:
                self.revision, self.admin = revision, admin
                saved = self.store.live("shuffle")
                self.shuffle = saved if saved and saved.get("key") == race_key(admin["site_settings"]) else empty(admin["site_settings"])
                self.restore_edits()
            return self.revision, copy.deepcopy(self.admin)

    def commit(self, admin, expected, *, snapshot=None, reason=None):
        with self.lock:
            revision = self.store.save(admin, expected, snapshot=snapshot, backup_reason=reason)
            self.revision, self.admin = revision, copy.deepcopy(admin)
            if snapshot is not None:
                self.shuffle = copy.deepcopy(snapshot)

    def public(self):
        with self.lock:
            site, value, kick = copy.deepcopy(self.admin["site_settings"]), copy.deepcopy(self.shuffle), copy.deepcopy(self.kick)
        site.update(start_et=fmt_et(site["start_time"]), end_et=fmt_et(site["end_time"]),
                    total_prize=money(sum(Decimal(v) for v in site["prizes"].values())), race_state=phase(site))
        # Projection is an explicit allowlist. Provider source rows, raw totals,
        # admin names, password hashes, and keys cannot reach the public API.
        rows = [dict(rank=r["rank"], username=r["username"][:2] + "******", wager=r["wager"]) for r in value["rows"][:15]]
        if phase(site) in {"upcoming", "unconfigured"}:
            rows = []
        available = bool(kick.get("updated_at") and not kick.get("error") and time.time() - kick["updated_at"] <= 180
                         and kick.get("channel") == site["kick_channel_slug"])
        stream = {k: kick.get(k) for k in ("live", "title", "viewers", "updated_at")}
        stream["available"] = available
        fresh = freshness(value)
        fresh.pop("error", None)
        return dict(release=RELEASE, server_time=int(time.time()), interval=INTERVAL, site=site, rows=rows,
                    empiredrop=self.empiredrop.public(site),
                    leaderboard_message=self.empty_message(site, value),
                    freshness=fresh, stream=stream, revision=token([site, rows, fresh, stream]))

    @staticmethod
    def empty_message(site, snapshot):
        """Explain an empty board without inventing results or exposing records."""
        state = phase(site)
        if state == "unconfigured":
            return "The race schedule has not been configured."
        if state == "upcoming":
            return "This race has not started. Wagers will load after " + fmt_et(site["start_time"]) + "."
        if snapshot["rows"]:
            return ""
        if snapshot.get("error"):
            return "Shuffle updates are delayed. No successful leaderboard is available for this race window yet."
        if not snapshot.get("updated_at"):
            return "Waiting for Shuffle's first successful update for this race window."
        if not snapshot.get("received"):
            return "Shuffle returned no wagers for " + fmt_et(site["start_time"]) + " to " + fmt_et(site["end_time"]) + "."
        if not snapshot.get("accepted"):
            return "None of the returned wagers match this race's saved campaign filter."
        return "No returned wagers currently meet the $0.01 weighted qualification for this race."

    def status(self):
        if self.started:
            self.start()  # Recover a stopped worker without starting jobs in factory-only tests.
        with self.lock:
            data = self.public()
            data["runtime_id"] = self.instance_id
            data.update(rows=copy.deepcopy(self.shuffle["rows"]), edits=copy.deepcopy(self.shuffle.get("edits", [])),
                        red=copy.deepcopy(self.shuffle.get("red", [])), red_total=self.shuffle.get("red_total", 0),
                        count=self.shuffle.get("count", len(self.shuffle["rows"])), snapshot_only=self.shuffle.get("snapshot_only", False),
                        freshness=freshness(self.shuffle), jobs=self.job_status(),
                        diagnostics=dict(release=RELEASE, credentials=self.config.diagnostics(),
                            storage="Local JSON file (automatic)", settings_revision=self.revision,
                            start_et=fmt_et(self.admin["site_settings"]["start_time"]), end_et=fmt_et(self.admin["site_settings"]["end_time"]),
                            received=self.shuffle.get("received", 0), accepted=self.shuffle.get("accepted", 0),
                            rejected=self.shuffle.get("rejected", {}), missing_campaign=self.shuffle.get("missing_campaign", 0)))
            data["diagnostics"].update(race_state=phase(self.admin["site_settings"]),
                campaign_filter=self.admin["site_settings"]["campaign_code_filter"], endpoint_kind=self.config.endpoint,
                aggregation=self.config.aggregation, qualifying_players=data["count"], loaded_players=len(data["rows"]))
            data['history'] = self.history.diagnostics()
            return data

    def job_status(self):
        with self.lock:
            return {name: {**{k: v for k, v in job.items() if k != "not_before"},
                           "pending": self.events[name].is_set(),
                           "worker_alive": bool(self.threads.get(name) and self.threads[name].is_alive()),
                           "changed_at": (self.shuffle if name == "shuffle" else self.kick).get("changed_at", 0),
                           "last_success": (self.shuffle if name == "shuffle" else self.kick).get("updated_at", 0)}
                    for name, job in self.jobs.items()}

    def check(self, name):
        began, now = time.monotonic(), int(time.time())
        with self.lock:
            ticket = self.jobs[name]["requested"]
            self.jobs[name].update(state="checking", attempt_at=now, next_check=0,
                                   runs=self.jobs[name]["runs"]+1)
        error, status, retry, warning, result, revision = "", None, 0, "", "waiting", None
        failure_code, request_meta = None, {}
        try:
            with self.store.job(name) as acquired:
                revision, admin = self.sync()
                site = admin["site_settings"]
                with self.lock:
                    self.jobs[name].update(checked_scope=race_key(site) if name == "shuffle" else site["kick_channel_slug"],
                        checked_start=site["start_time"] if name == "shuffle" else 0,
                        checked_end=min(site["end_time"], now) if name == "shuffle" else 0,
                        checked_channel=site["kick_channel_slug"] if name == "kick" else "")
                if not acquired:
                    saved = self.store.live(name)
                    with self.lock:
                        if saved and (name == "kick" or saved.get("key") == race_key(site)):
                            setattr(self, name, saved)
                    result = "shared"
                    return 0
                if name == "shuffle":
                    with self.lock:
                        previous = copy.deepcopy(self.shuffle)
                    if phase(site) in {"upcoming", "unconfigured"}:
                        value = empty(site)
                        value["attempt_at"] = now
                        result = phase(site)
                    else:
                        LOG.info("SHUFFLE Checking saved window %s -> %s.", fmt_et(site["start_time"]), fmt_et(min(site["end_time"], now)))
                        incoming = normalize(self.providers.shuffle(site), site, self.config.raw_fallback)
                        status = self.providers.last_http_status()
                        request_meta = self.providers.last_request_meta()
                        value = calculate({**empty(site), **incoming, "updated_at":int(time.time()), "attempt_at":now, "ok":True}, admin, self.config)
                        # Warn once when incomplete campaign/amount records change.
                        # Store only counts, never source values or usernames.
                        missing = value.get('missing_campaign', 0)
                        invalid = sum(n for reason, n in value.get('rejected', {}).items()
                                      if reason != 'other campaign')
                        if (self.activity_log and (missing or invalid) and
                            (missing != previous.get('missing_campaign', 0) or
                             invalid != sum(n for reason, n in previous.get('rejected', {}).items()
                                            if reason != 'other campaign'))):
                            self.activity_log.record('shuffle', 'warning', 'data_quality',
                                                     code='partial', count=value.get('count', len(value.get('rows', []))),
                                                     received=value.get('received', 0), accepted=value.get('accepted', 0),
                                                     excluded=max(0, value.get('received', 0)-value.get('accepted', 0)),
                                                     unscoped=missing)
                        value["changed_at"] = value["updated_at"] if previous["rows"] != value["rows"] else previous.get("changed_at", 0)
                        value["previous_top"] = previous["rows"][:15] if previous["rows"][:15] != value["rows"][:15] else previous.get("previous_top", [])
                        warning = value["warning"]
                        result = "empty" if not value["rows"] else "updated" if previous["rows"] != value["rows"] else "unchanged"
                    with self.lock:
                        self.store.publish(name, value, revision)
                        self.shuffle = value
                    LOG.info("SHUFFLE %s; %s accepted / %s received; race %s → %s.",
                             "Updated" if previous["rows"] != value["rows"] else "Confirmed unchanged",
                             value.get("accepted", 0), value.get("received", 0), fmt_et(site["start_time"]), fmt_et(site["end_time"]))
                    if not value["rows"]:
                        LOG.info("SHUFFLE %s", self.empty_message(site, value))
                else:
                    value = {**self.providers.kick(site), "updated_at":int(time.time()), "attempt_at":now, "error":""}
                    fields = ("live", "title", "viewers", "channel")
                    with self.lock:
                        value["changed_at"] = value["updated_at"] if any(value.get(k) != self.kick.get(k) for k in fields) else self.kick.get("changed_at", 0)
                    status, result = self.providers.last_http_status(), "live" if value["live"] else "offline"
                    with self.lock:
                        self.store.publish(name, value, revision)
                        self.kick = value
                    LOG.info("KICK Confirmed %s.", "LIVE" if value["live"] else "OFFLINE")
        except Conflict:
            self.events[name].set()
            result = "superseded"
            LOG.info("%s Settings changed during this check; checking again.", name.upper())
        except Exception as exc:
            error = str(exc) if isinstance(exc, (ProviderError, StoreError, ValueError)) else "Internal check failed (" + type(exc).__name__ + ")."
            status, retry = getattr(exc, "status", None), getattr(exc, "retry_after", 0)
            failure_code = getattr(exc, "kind", "unknown")
            request_meta = self.providers.last_request_meta() if name == "shuffle" else {}
            superseded, result = False, "failed"
            with self.lock:
                superseded = revision is not None and revision != self.revision
                if not superseded:
                    old = copy.deepcopy(getattr(self, name))
                    old.update(error=error, attempt_at=now, ok=False)
                    try:
                        # Failed responses have the same revision guard as
                        # successful ones. An old window cannot poison a new one.
                        self.store.publish(name, old, revision if revision is not None else self.revision)
                    except Conflict:
                        superseded = True
                    except StoreError:
                        setattr(self, name, old)
                    else:
                        setattr(self, name, old)
                if superseded:
                    self.events[name].set()
            if superseded:
                result = "superseded"
                LOG.info("%s Ignored a failed response for superseded settings; the current settings are queued.", name.upper())
                # A provider rate limit still applies across race windows.
                if status != 429 and not retry:
                    error = ""
            if error:
                LOG.warning("%s %s Previous data retained; retry in %ss.", name.upper(), error, max(INTERVAL, retry))
        finally:
            duration = round((time.monotonic() - began) * 1000)
            with self.lock:
                previous_streak = int(self.jobs[name].get("failure_streak", 0) or 0)
                failure_streak = previous_streak + 1 if error else 0
                # Repeated provider failures back off without spawning overlapping
                # checks. A successful response immediately restores normal cadence.
                effective_retry = max(int(retry or 0),
                                      min(480, INTERVAL * (2 ** min(3, max(0, failure_streak - 1))))) if error else 0
                self.jobs[name].update(state="delayed" if error else "scheduled", error=error, http_status=status,
                                       duration_ms=duration, retry_after=effective_retry, result=result,
                                       failure_streak=failure_streak,
                                       request_meta=request_meta if name == "shuffle" else {},
                                       provider_reason=failure_code if error else None,
                                       completed=max(ticket, self.jobs[name]["completed"]), completed_at=int(time.time()))
            if warning:
                LOG.warning("SHUFFLE %s", warning)
            if self.activity_log and (error or result in ('updated','empty') or
                (name=='kick' and result in ('live','offline') and
                 isinstance(value,dict) and value.get('changed_at')==value.get('updated_at'))):
                # Only meaningful changes/failures; no usernames or provider bodies.
                self.activity_log.record(name,'warning' if error else 'success',
                    'refresh_failed' if error else 'refresh_ok',duration_ms=duration,
                    http_status=status,
                    count=len(value.get('rows',[])) if not error and isinstance(value,dict) else None,
                    received=value.get('received') if not error and isinstance(value,dict) else None,
                    accepted=value.get('accepted') if not error and isinstance(value,dict) else None,
                    excluded=(max(0, value.get('received',0)-value.get('accepted',0))
                             if not error and isinstance(value,dict) and name == 'shuffle' else None),
                    unscoped=(value.get('missing_campaign',0)
                             if not error and isinstance(value,dict) and name == 'shuffle' else None),
                    code=failure_code if error else None)
            LOG.info("%s Check took %sms. Automatic checks stay enabled.", name.upper(), duration)
        return effective_retry if error else 0

    def request_refresh(self, name=None):
        if self.started:
            self.start()
        targets = {}
        for service in (name,) if name else self.events:
            with self.lock:
                job = self.jobs[service]
                scope = race_key(self.admin["site_settings"]) if service == "shuffle" else self.admin["site_settings"]["kick_channel_slug"]
                # A new race should not wait on an ordinary error from the old
                # dates. Explicit provider Retry-After/429 limits remain binding.
                if job["checked_scope"] != scope and not job["retry_after"] and job["http_status"] != 429:
                    job["not_before"] = 0
                if not self.events[service].is_set():
                    job["requested"] += 1
                targets[service] = job["requested"]
                if job["state"] != "checking":
                    job["state"] = "queued"
                    job["next_check"] = int(time.time() + max(0, job["not_before"]-time.monotonic()))
                # Even an active check must retain one follow-up request. The
                # event coalesces repeated clicks without concurrent API calls.
                self.events[service].set()
        return dict(runtime_id=self.instance_id, requests=targets)

    def loop(self, name):
        due = time.monotonic()
        try:
            while not self.stop_event.is_set():
                delay = max(due, self.jobs[name]["not_before"]) - time.monotonic()
                with self.lock:
                    self.jobs[name]["next_check"] = int(time.time() + max(0, delay))
                if delay > 0:
                    triggered = self.events[name].wait(min(delay, 1))
                    if not triggered:
                        continue
                    self.events[name].clear()
                    due = time.monotonic()
                    continue
                self.events[name].clear()
                anchor = due
                retry = self.check(name)
                finished = time.monotonic()
                if retry:
                    self.jobs[name]["not_before"] = finished + retry
                    due = finished + retry
                else:
                    self.jobs[name]["not_before"] = 0
                    due = anchor + (int(max(0, finished - anchor) // INTERVAL) + 1) * INTERVAL
                if self.events[name].is_set():
                    due = finished
        finally:
            self.providers.close()
            self.store.close_job()
            with self.lock:
                self.jobs[name]["state"] = "stopped"

    def start(self):
        with self.lock:
            if self.stop_event.is_set():
                return
            initial = not self.started
            self.started = True
            for name in self.events:
                if self.threads.get(name) and self.threads[name].is_alive():
                    continue
                thread = threading.Thread(target=self.loop, args=(name,), daemon=True, name=name + "-updates")
                self.threads[name] = thread
                thread.start()
                if not initial:
                    LOG.warning("%s Restarted a stopped automatic worker.", name.upper())
        if initial:
            LOG.info("LIVE Automatic Shuffle and Kick checks started; cadence=%ss.", INTERVAL)
        self.history.start()
        self.empiredrop.start()

    def stop(self):
        self.stop_event.set()
        self.history.stop()
        self.empiredrop.stop()
        for event in self.events.values():
            event.set()
        for thread in self.threads.values():
            thread.join(timeout=1)
```

## `shuffle_deploy_key.py`

```python
"""PRIVATE REPOSITORY ONLY. Server-side Shuffle credential fallback.

Used only when the private JSON file is ignored by Git and no encrypted
SHUFFLE_API_KEY environment variable is set. Never import in public scripts.
Prefer encrypted App Platform environment variables for future deployments.
"""

SHUFFLE_BUNDLED_KEY = 'f45f746d-b021-494d-b9b6-b47628ee5cc9'
```

## `spaces_state.py`

```python
"""Optional one-writer DigitalOcean Spaces mirror for the JSON state document.

Disabled by default. When enabled, the remote `current.json` becomes authoritative
on boot; writes first upload an immutable revision checkpoint and then `current`.
This is a *single-writer* protocol, not a distributed database: run one App
Platform instance and avoid simultaneous old/new writers during deployments.
Private credentials must be provided as encrypted environment variables.
"""
import hashlib
import json
import os
import tempfile
from pathlib import Path
import re
import time


class SpacesError(RuntimeError):
    """Operational error that deliberately contains no secret settings."""


class SpacesMirror:
    def __init__(self, *, bucket, endpoint, region, prefix, key_id, secret, client=None):
        if not bucket or not endpoint.startswith('https://') or not key_id or not secret:
            raise SpacesError('Spaces mirror needs HTTPS endpoint, bucket and access keys.')
        if not re.fullmatch(r'[A-Za-z0-9/_-]{1,120}', prefix):
            raise SpacesError('Spaces mirror prefix must contain only safe path characters.')
        self.bucket, self.prefix = bucket, prefix.rstrip('/')
        if client is None:
            try:
                import boto3
                from botocore.config import Config as BotoConfig
            except ImportError:
                raise SpacesError('Install requirements-spaces.txt to enable durable Spaces storage.') from None
            client = boto3.client('s3', region_name=region, endpoint_url=endpoint,
                                  aws_access_key_id=key_id, aws_secret_access_key=secret,
                                  config=BotoConfig(retries={'max_attempts': 3, 'mode': 'standard'},
                                                    connect_timeout=5, read_timeout=12))
        self.client = client
        self.last_verified = 0

    @classmethod
    def from_environment(cls, state_key):
        if os.getenv('RH_SPACES_ENABLE', '').strip().lower() not in {'1', 'true'}:
            return None
        prefix = os.getenv('RH_SPACES_PREFIX', f'redhunllef/{state_key}')
        return cls(bucket=os.getenv('RH_SPACES_BUCKET', ''),
                   endpoint=os.getenv('RH_SPACES_ENDPOINT', ''),
                   region=os.getenv('RH_SPACES_REGION', 'nyc3'),
                   prefix=prefix, key_id=os.getenv('RH_SPACES_KEY_ID', ''),
                   secret=os.getenv('RH_SPACES_SECRET', ''))

    def _key(self, suffix):
        return self.prefix + '/' + suffix

    def fetch(self):
        """Return None only for a documented missing object (not for network errors)."""
        try:
            response = self.client.get_object(Bucket=self.bucket, Key=self._key('current.json'))
            payload = response['Body'].read()
            state = json.loads(payload)
            if not isinstance(state, dict) or state.get('format') != 1 or not isinstance(state.get('admin'), dict):
                raise SpacesError('Remote state is invalid; local data was not overwritten.')
            self.last_verified = int(time.time())
            return state
        except SpacesError:
            raise
        except Exception as exc:
            code = getattr(exc, 'response', {}).get('Error', {}).get('Code', '')
            if code in ('NoSuchKey', '404', 'NotFound'):
                return None
            raise SpacesError('Could not read the authoritative Spaces state; refusing to use a stale local snapshot.') from None

    def prepare(self, local_path, *, state_key, bootstrap=False):
        """Hydrate from authoritative remote state before ordinary store bootstrap."""
        remote = self.fetch()
        if remote is None:
            if not bootstrap:
                raise SpacesError('Spaces has no current state. Restore the latest live backup first or explicitly bootstrap a verified local state.')
            if not local_path.is_file():
                raise SpacesError('Cannot bootstrap Spaces without an existing verified local state file.')
            local = json.loads(local_path.read_text(encoding='utf-8'))
            if not isinstance(local, dict) or local.get('format') != 1 or local.get('key') != state_key:
                raise SpacesError('Local state is not a valid matching account snapshot.')
            self.persist(local, expected=None)
            return
        if remote.get('key') != state_key:
            raise SpacesError('Spaces state key does not match the configured website.')
        if local_path.is_file():
            local = json.loads(local_path.read_text(encoding='utf-8'))
            if int(local.get('_mirror_sequence', 0)) > int(remote.get('_mirror_sequence', 0)):
                raise SpacesError('Local state is newer than remote; stop and reconcile before deploying.')
        # Do not depend on the web stack for recovery; hydrate atomically.
        local_path = Path(local_path)
        local_path.parent.mkdir(parents=True, exist_ok=True)
        handle, tmp_name = tempfile.mkstemp(prefix=local_path.name+'.', suffix='.tmp', dir=local_path.parent)
        try:
            with os.fdopen(handle,'w',encoding='utf-8') as output:
                json.dump(remote,output,ensure_ascii=False,allow_nan=False)
                output.flush(); os.fsync(output.fileno())
            os.replace(tmp_name,local_path)
        finally:
            if os.path.exists(tmp_name): os.unlink(tmp_name)

    def persist(self, value, *, expected):
        """Check the prior revision, then write a versioned snapshot and current.

        Does not support concurrent independent writers. Run exactly one instance
        and coordinate deployment cutovers. A network/upload failure aborts the
        local transaction, rather than falsely reporting that data was saved.
        """
        previous = self.fetch()
        if expected is None:
            if previous is not None:
                raise SpacesError('Remote state already exists; refusing a bootstrap overwrite.')
        elif previous is None or previous != expected:
            raise SpacesError('Remote state changed; refusing to overwrite a newer revision.')
        blob = json.dumps(value, ensure_ascii=False, separators=(',', ':'), allow_nan=False).encode('utf-8')
        digest = hashlib.sha256(blob).hexdigest()[:16]
        seq = int(value.get('_mirror_sequence', 0))
        checkpoint = self._key(f'snapshots/{seq:012d}-{time.time_ns()}-{digest}.json')
        try:
            self.client.put_object(Bucket=self.bucket, Key=checkpoint, Body=blob, ContentType='application/json')
            self.client.put_object(Bucket=self.bucket, Key=self._key('current.json'),
                                   Body=blob, ContentType='application/json')
            self.last_verified = int(time.time())
        except Exception:
            raise SpacesError('Spaces state write failed. No local commit was published; retry when storage is reachable.') from None
```

## `storage.py`

```python
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
                # V13 schedule saves could silently switch EmpireDrop to the
                # deprecated timestamp endpoint. Migrate only that retired
                # source choice back to the documented partner-race API while
                # preserving the selected slug, prizes, accounts and all live
                # data. A private recovery record is kept before the change.
                empire_cfg = existing['admin'].get('empiredrop_races')
                if isinstance(empire_cfg, dict) and empire_cfg.get('source_mode') == 'legacy_window':
                    upgraded = copy.deepcopy(existing)
                    previous_cfg = copy.deepcopy(empire_cfg)
                    migrated_cfg = copy.deepcopy(empire_cfg)
                    migrated_cfg['source_mode'] = 'races'
                    migrated_cfg['race_window_policy'] = 'provider'
                    migrated_cfg['auto_select'] = True
                    self.backup_in(upgraded, 'before-empiredrop-official-api-migration', {
                        'empiredrop_races': previous_cfg,
                        'empiredrop_race': copy.deepcopy(upgraded['admin'].get('empiredrop_race')),
                    })
                    upgraded['admin']['empiredrop_races'] = migrated_cfg
                    upgraded['revision'] += 1
                    atomic_json(self.path, upgraded)
                    self._remember(upgraded)
                    existing = upgraded
                    LOG.warning('MIGRATION EmpireDrop deprecated date-window source changed to official partner races; saved slug and other state retained.')
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
```

## `store_schema.py`

```python
"""Non-destructive document validation shared by startup and migration tools."""
from __future__ import annotations
import copy
import secrets
import time
from race_support import STORE_VERSION, canonical_site, clean_overrides, clean_snapshots, integer, race_key, validate_site
from weekly_history import clean_history


def upgrade_store(value, defaults, health_defaults):
    """Upgrade additively and preserve password hashes, settings, and history."""
    if not isinstance(value, dict):
        raise ValueError("The admin store must contain a JSON object.")
    original = copy.deepcopy(value)
    store = copy.deepcopy(value)
    if 'weekly_history' in store:
        store['weekly_history'] = clean_history(store['weekly_history'])
    version = integer(store.get("version"))
    if version > STORE_VERSION:
        raise RuntimeError("This admin store belongs to a newer application version.")
    users = store.setdefault("users", {})
    if not isinstance(users, dict):
        raise RuntimeError("Admin accounts are malformed. Restore a verified recovery copy.")
    seen = set()
    for username, record in users.items():
        if not isinstance(record, dict) or not isinstance(record.get("pw_hash"), str):
            raise RuntimeError("An admin account is malformed. The original store is unchanged.")
        folded = username.casefold()
        if folded in seen:
            raise RuntimeError("Duplicate case-insensitive admin usernames need offline resolution before upgrade.")
        seen.add(folded)
        record.setdefault("auth_version", 1)
    secret = str(store.get("secret_key") or "")
    if version < 3 or len(secret) < 32 or secret.upper().startswith(("REPLACE_", "GENERATED_")):
        store["secret_key"] = secrets.token_hex(32)
    raw_site = store.get("site_settings", {})
    if not isinstance(raw_site, dict):
        raise ValueError("Saved race settings must be an object; they were not replaced with defaults.")
    site = canonical_site(raw_site, defaults)
    errors = validate_site(site)
    if errors:
        raise RuntimeError("Saved race settings need correction: " + "; ".join(errors.values()))
    store["site_settings"] = site
    store.setdefault("settings_revision", 1)
    store.setdefault("data_revision", 1)
    for field in ("settings_revision", "data_revision"):
        if isinstance(store[field], bool) or not isinstance(store[field], int) or store[field] < 1:
            raise ValueError("Saved revision counters must be positive integers.")
    store.setdefault("overrides", {})
    store["overrides"] = clean_overrides(store["overrides"])
    store.setdefault("race_history", [])
    store.setdefault("audit_log", [])
    store.setdefault("banned_ips", [])
    for key in ("race_history", "audit_log", "banned_ips"):
        if not isinstance(store[key], list):
            raise RuntimeError("Saved " + key + " has an invalid format.")
    for entry in store["race_history"]:
        if not isinstance(entry, dict) or not isinstance(entry.get("site_settings"), dict):
            raise ValueError("An archived race has invalid settings.")
        archived_site = canonical_site(entry["site_settings"], defaults)
        if validate_site(archived_site):
            raise ValueError("An archived race has invalid dates, prizes, or links.")
        clean_overrides(entry.get("overrides", {}))
        clean_snapshots(entry.get("leaderboard_snapshots", {}), race_key(archived_site))
    health = store.setdefault("health", {})
    if not isinstance(health, dict):
        raise RuntimeError("Saved health data has an invalid format.")
    for key, default in health_defaults.items():
        health.setdefault(key, default)
    if "http://" in str(health.get("last_error") or "") or "https://" in str(health.get("last_error") or ""):
        health["last_error"] = "Previous external-service error redacted during migration."
    snapshots = store.setdefault("leaderboard_snapshots", {})
    if not isinstance(snapshots, dict):
        raise ValueError("Saved leaderboard snapshots must be an object.")
    snapshots.setdefault("last_top15", snapshots.get("last_top11") or [])
    snapshots.setdefault("prev_top15", snapshots.get("prev_top11") or [])
    snapshots.setdefault("updated_at", None)
    snapshots.setdefault("race_key", race_key(site))
    # Validate a legacy snapshot without discarding any unknown original fields.
    clean_snapshots(snapshots, race_key(site))
    health["last_success"] = health.get("last_success") or snapshots.get("updated_at") or 0
    store.pop("payout_status", None)
    store["version"] = STORE_VERSION
    store.setdefault("updated_at", int(time.time()))
    return store, store != original
```

## `telemetry.py`

```python
"""Bounded, process-local diagnostics. Never record player names or secrets.

Measurements describe this running process, not an external monitoring service.
They deliberately stay out of the community's transactional save file.
"""
from collections import Counter, deque
import math
import threading
import time


def distribution(values):
    values = sorted(values)
    if not values:
        return dict(samples=0, p50_ms=0, p95_ms=0, max_ms=0)
    return dict(samples=len(values), p50_ms=round(values[math.ceil(len(values)*.5)-1], 2),
                p95_ms=round(values[math.ceil(len(values)*.95)-1], 2), max_ms=round(values[-1], 2))


class Measurements:
    """Keep recent samples bounded even on a long-running, busy server."""
    def __init__(self):
        self.lock = threading.Lock()
        self.started = time.monotonic()
        self.requests = deque(maxlen=512)
        self.storage = deque(maxlen=256)
        self.request_count = self.error_count = self.write_count = 0
        self.last_write = self.last_failure = 0
        self.failure_code = ''
        self.bytes = 0

    def request(self, endpoint, status, elapsed):
        with self.lock:
            self.request_count += 1
            self.error_count += status >= 500
            # Endpoint names come from Flask, never a URL/query/body/header.
            self.requests.append((endpoint or 'unmatched', status, elapsed))

    def transaction(self, wait, copy, write, size=0):
        with self.lock:
            self.storage.append((wait, copy, write))
            if size:
                self.bytes = size
            if write is not None:
                self.write_count += 1
                self.last_write = int(time.time())
                self.failure_code = ''

    def failed(self, code):
        with self.lock:
            self.last_failure = int(time.time())
            self.failure_code = code

    def snapshot(self):
        with self.lock:
            return dict(uptime_seconds=int(time.monotonic()-self.started), requests=self.request_count,
                        server_errors=self.error_count, latency=distribution([r[2] for r in self.requests]),
                        slow_endpoints=dict(Counter(r[0] for r in self.requests if r[2] >= 500)),
                        storage=dict(writes=self.write_count, last_write=self.last_write,
                                     last_failure=self.last_failure, failure_code=self.failure_code,
                                     bytes=self.bytes, lock_wait=distribution([r[0] for r in self.storage]),
                                     copy=distribution([r[1] for r in self.storage if r[1] is not None]),
                                     write=distribution([r[2] for r in self.storage if r[2] is not None])))


def health_view(runtime, measurements, status):
    """Allow-listed support report: no arbitrary provider errors or identities."""
    from config import RELEASE
    probe = runtime.store.readiness()
    stats = measurements.snapshot()
    storage = runtime.store.measurements.snapshot()['storage']
    cards = [dict(key='website', label='Website', state='good', status='Serving requests',
                  detail='The application is running. Provider checks are independent.',
                  last_success=int(time.time()), action='')]
    for key, label in [('shuffle', 'Shuffle'), ('kick', 'Kick')]:
        job = status.get('jobs', {}).get(key, {})
        last = job.get('last_success') or 0
        error = bool(job.get('error'))
        stalled = runtime.started and not job.get('worker_alive')
        delayed = bool(last and time.time()-last > 180)
        state = 'warning' if error or stalled or delayed or not last else 'good'
        detail = ('Automatic worker stopped; check runtime logs.' if stalled else
                  'The provider has not confirmed a recent update. Saved data stays visible.' if state == 'warning' else
                  'Automatic checks run every 60 seconds; values may remain unchanged.')
        cards.append(dict(key=key, label=label, state=state,
                          status='Needs attention' if state == 'warning' else 'Connected', detail=detail,
                          last_success=last, last_check=job.get('attempt_at', 0),
                          last_change=job.get('changed_at', 0), next_check=job.get('next_check', 0),
                          action='/admin/settings#configurationDetails'))
    # EmpireDrop is an independent source with provider-controlled cache TTL.
    empire = runtime.empiredrop.private_status()
    age = time.time() - (empire.get('updated_at') or 0) if empire.get('updated_at') else None
    interval = max(60, int(empire.get('refresh_interval') or 300))
    failed = bool(empire.get('error')) or not empire.get('running')
    state = 'warning' if failed or age is None or age > interval*2+60 else 'good'
    cards.append(dict(key='empiredrop',label='EmpireDrop',state=state,
                      status='Connected' if state=='good' else 'Needs attention',
                      detail=('Latest verified ranking is delayed; the last good board stays visible.' if state=='warning'
                              else 'Provider cache respected; automatic race updates running.'),
                      last_success=empire.get('updated_at') or 0,
                      last_check=empire.get('attempt_at') or 0,
                      action='/admin/leaderboards/empiredrop'))
    cards.append(dict(key='games', label='Games', state='good' if probe['ok'] else 'error',
                      status='Ready to save play' if probe['ok'] else 'Saving unavailable',
                      detail='Results are acknowledged after their save completes. Retry receipts prevent duplicate bets.',
                      last_success=storage['last_write'], action='/admin/gaming'))
    cards.append(dict(key='storage', label='Saved data', state='good' if probe['ok'] else 'error',
                      status='Readable and writable' if probe['ok'] else 'Needs attention',
                      detail=probe['message'], last_success=probe['checked_at'], action='/admin/recovery'))
    return dict(release=RELEASE, generated_at=int(time.time()), ready=probe['ok'], components=cards,
                metrics={**stats, 'storage':storage}, retention='Recent 512 requests and 256 store operations; reset on restart.')
```

## `wager_backend.py`

```python
"""RedHunllef's sole launch command: python wager_backend.py.

App construction has no provider requests or hidden worker startup. The main
function binds one production server, then starts the two automatic jobs once.
"""
from collections import deque
import copy
import csv
from datetime import datetime, timezone, timedelta
from decimal import Decimal
from functools import wraps
import io
import hashlib
import hmac
import ipaddress
import json
import logging
import re
import secrets
import signal
import sys
import threading
import time

from flask import Flask, Response, abort, flash, g, jsonify, redirect, render_template, request, session, url_for
from flask.sessions import SecureCookieSessionInterface
from itsdangerous import BadSignature, URLSafeSerializer, URLSafeTimedSerializer
from werkzeug.exceptions import BadRequest, HTTPException
from werkzeug.security import check_password_hash, generate_password_hash

from config import Config, RELEASE
from presentation import changes, checkpoint_status, export_marker
from store_schema import upgrade_store
from race import calculate, empty, phase, token
from race_support import (DEFAULT_PRIZES, WEIGHTING_RULES, TEXT_LIMITS, URL_FIELDS,
                          canonical_site, clean_overrides, clean_snapshots, csv_text,
                          decimal_amount, eastern_epoch, empty_snapshots, fmt_et,
                          local_input, money, money_input, race_key, validate_site)
from runtime import Runtime
from storage import Conflict, StoreError
from fairness import GAMES, SUPPORTED_VERSIONS, rules as gaming_rules
from gaming import Gaming, GamingError, validate_gaming
from empiredrop import validate_settings, EDITABLE, schedule as empire_schedule, CODE as EMPIRE_CODE
from empiredrop_races import RACE_EDITABLE, validate_race_settings
from empiredrop_features import validate_rewards, rewards_public, resolve_reward_save_mode
from operations_log import ActivityLog
from provider_admin import summarize_providers
from integrations import ProviderError
from telemetry import Measurements, health_view
from admin_navigation import admin_link, ADMIN_TABS, ADMIN_SECTION_ALIASES

LOG = logging.getLogger("redhunllef")
TABS = {"overview":"Overview", "shuffle":"Shuffle standings", "race":"Shuffle schedule", "players":"Shuffle players", "empiredrop":"EmpireDrop", "gaming":"Games & RedPoints", "activity":"Activity & logs", "settings":"Settings"}
if frozenset(TABS) != ADMIN_TABS:
    raise RuntimeError("Admin navigation and rendered tabs disagree")


def account(users, name):
    return next(((k, v) for k, v in users.items() if k.casefold() == str(name).casefold()), (None, None))


def filtered(rows, edits, args):
    view, query, order = args.get("view", "all"), args.get("q", "").strip()[:64], args.get("sort", "rank")
    values = edits if view == "overrides" else rows[:15] if view == "top" else rows
    values = [r for r in values if query.casefold() in r["username"].casefold()]
    if order == "name":
        values = sorted(values, key=lambda r: (r["username"].casefold(), r["username"]))
    elif order == "raw":
        values = sorted(values, key=lambda r: (-decimal_amount(r.get("raw_wager") or 0), r["username"].casefold()))
    return values


def create_app(root=None, testing=False):
    config = Config(root)
    runtime = Runtime(config)
    app = Flask(__name__)
    app.config.update(TESTING=testing, SECRET_KEY=config.secret or runtime.admin["secret_key"],
                      MAX_CONTENT_LENGTH=8 * 1024 * 1024, SESSION_COOKIE_HTTPONLY=True,
                      SESSION_COOKIE_SAMESITE="Lax", PERMANENT_SESSION_LIFETIME=timedelta(hours=12))
    app.extensions["runtime"] = runtime
    activity = app.extensions["activity"] = ActivityLog()
    runtime.empiredrop.events = activity
    runtime.activity_log = activity

    def safe_activity(*args, **kwargs):
        """Operational logging must never turn a completed admin write into HTTP 500."""
        try:
            return activity.record(*args, **kwargs)
        except Exception:
            # Arguments are deliberately not logged because they may come from
            # future call sites that contain private operational context.
            LOG.exception('ACTIVITY A structured event could not be recorded.')
            return None
    app.extensions["settings"] = config
    measurements = app.extensions['measurements'] = Measurements()
    gaming = app.extensions['gaming'] = Gaming(runtime.store)
    # One launch restores playable points for everyone, without clearing results.
    # Page requests and automatic status checks never run this bulk reset.
    gaming.restart_balances()
    player_signer = URLSafeTimedSerializer(app.secret_key, salt="redpoints-player-v1")
    legacy_player_signer = URLSafeTimedSerializer(app.secret_key, salt="community-boss-guest-v1")
    recovery_signer = URLSafeSerializer(app.secret_key, salt="redpoints-recovery-v1")
    legacy_recovery_signer = URLSafeSerializer(app.secret_key, salt="community-boss-recovery-v1")
    review_signer = URLSafeTimedSerializer(app.secret_key, salt="race-review-v1")
    failures, previews, access_log = {}, {}, deque(maxlen=150)
    auth_lock = threading.Lock()
    dummy_hash = generate_password_hash(secrets.token_hex(16))
    # Shipped assets are UTF-8. Never use the host's default text encoding:
    # Windows CP1252 cannot decode some Unicode characters in the browser code.
    assets = token([
        (p.name, p.read_text(encoding="utf-8"))
        for p in sorted((config.root / "static").glob("*"))
        if p.suffix in {".css", ".js"}
    ])

    class Cookies(SecureCookieSessionInterface):
        def get_cookie_secure(self, app):
            if config.secure_cookie in {"1", "true", "always"}:
                return True
            if config.secure_cookie in {"0", "false", "never"}:
                return False
            return request.is_secure
    app.session_interface = Cookies()

    def csrf():
        return session.setdefault("csrf", secrets.token_urlsafe(32))

    def wants_json():
        """Keep fetch failures machine-readable; native pages still render HTML."""
        return request.path.startswith("/gaming/api/") or request.accept_mimetypes.best == "application/json" or request.path in {
            "/data", "/public-state", "/history-state", "/config", "/stream", "/admin/status", "/admin/gaming/status", "/admin/empiredrop/status", "/admin/diagnostics", "/admin/health-report", "/admin/operations/events", "/admin/operations/export", "/healthz", "/readyz"
        }

    def json_error(message, status, code=None):
        body = dict(ok=False, error=message, status=status, release=RELEASE,
                    request_id=getattr(g, 'request_id', ''), code=code or 'http_'+str(status))
        return jsonify(body), status

    def require_csrf():
        expected = session.get('csrf')
        supplied = request.headers.get('X-CSRF-Token') or request.form.get('csrf', '')
        # A missing session token must never match a known fallback value.
        # Reject malformed Unicode cleanly before constant-time ASCII comparison.
        if (not isinstance(expected, str) or not expected or not expected.isascii() or
            not isinstance(supplied, str) or not supplied or not supplied.isascii() or
            not secrets.compare_digest(supplied, expected)):
            abort(400, description="This form expired. Reload the page and try again.")

    def protected(fn):
        @wraps(fn)
        def wrapped(*args, **kwargs):
            if not g.user:
                if request.path.endswith(("status", "diagnostics", ".csv", "backup")) or wants_json():
                    return jsonify(error="Your session expired. Sign in again.", login_url=url_for("login")), 401
                return redirect(url_for("login"))
            return fn(*args, **kwargs)
        return wrapped

    @app.before_request
    def before():
        g.began, g.user, g.superadmin = time.perf_counter(), None, False
        g.request_id = secrets.token_hex(8)
        # App Platform supplies the visitor address in DO-Connecting-IP. Never
        # trust this header on a directly exposed/local server.
        address = request.headers.get("DO-Connecting-IP") if config.proxy else request.remote_addr
        try:
            g.client_ip = str(ipaddress.ip_address(address))
        except (ValueError, TypeError):
            g.client_ip = None
        if request.path.startswith("/admin"):
            g.revision, g.admin = runtime.sync()
            name, record = account(g.admin["users"], session.get("user"))
            if name and record.get("auth_version", 1) == session.get("auth_version"):
                g.user = name
                g.superadmin = name.casefold() == g.admin.get("superadmin", config.superadmin).casefold()
            if request.endpoint == 'recovery_preview' and g.superadmin:
                # A complete private recovery export can exceed an ordinary form. Only authenticated Superadmins get this larger limit.
                request.max_content_length = 64 * 1024 * 1024
        if request.path not in {"/healthz", "/readyz"} and g.client_ip in runtime.admin.get("banned_ips", []):
            abort(403, description="Access from this address has been disabled.")

    @app.after_request
    def after(response):
        response.headers['X-Request-ID'] = getattr(g, 'request_id', '')
        if request.path.startswith('/admin'):
            # Admin HTML includes version-specific navigation and private data.
            # Stale CDN/browser HTML caused links to outlive their route version.
            response.headers['Cache-Control'] = 'private, no-store, max-age=0'

        elapsed = (time.perf_counter()-g.began)*1000
        if request.endpoint not in {'static', 'health', 'ready'}:
            measurements.request(request.endpoint, response.status_code, elapsed)
        if response.status_code >= 500:
            safe_activity('system','error','server_error',http_status=response.status_code,
                            duration_ms=round(elapsed))
            LOG.error('REQUEST id=%s route=%s status=%s elapsed_ms=%.1f',
                      g.request_id, request.endpoint or 'unmatched', response.status_code, elapsed)
        response.headers.update({"X-Content-Type-Options":"nosniff", "X-Frame-Options":"DENY",
            "Referrer-Policy":"strict-origin-when-cross-origin", "X-RedHunllef-Release":RELEASE,
            "Content-Security-Policy":"default-src 'self'; script-src 'self'; style-src 'self'; img-src 'self' data:; connect-src 'self'; frame-ancestors 'none'; base-uri 'self'; form-action 'self'",
            "Cache-Control":"public, max-age=31536000, immutable" if request.path.startswith("/static/") and request.args.get("v") == assets else "no-store"})
        if request.is_secure:
            response.headers["Strict-Transport-Security"] = "max-age=31536000"
        if request.path in {"/public-state", "/gaming/api/public-leaderboard"} and response.status_code in {200, 304}:
            response.headers["Cache-Control"] = "public, no-cache"
        if request.path.startswith("/admin"):
            response.headers["X-Robots-Tag"] = "noindex, nofollow"
        if getattr(g, "new_guest", None):
            response.set_cookie("rh_player", player_signer.dumps(g.new_guest), max_age=365*86400,
                                secure=app.session_interface.get_cookie_secure(app), httponly=True, samesite="Lax")
            if request.cookies.get("rh_raider"):
                response.delete_cookie("rh_raider", secure=app.session_interface.get_cookie_secure(app), samesite="Lax")
        if request.path not in {"/data", "/public-state", "/history-state", "/config", "/stream", "/admin/status", "/healthz", "/readyz"} and not request.path.startswith(("/static/", "/gaming/api/")):
            with auth_lock:
                access_log.appendleft(dict(time=int(time.time()), method=request.method, path=request.path[:120], status=response.status_code,
                                           ip=g.client_ip, ms=round((time.perf_counter()-g.began)*1000)))
        return response

    @app.context_processor
    def context():
        return dict(release=RELEASE, asset_version=assets, csrf=csrf, money=money, fmt_et=fmt_et,
                    admin_link=admin_link,
                    local_input=local_input, tabs=TABS, weighting=WEIGHTING_RULES,
                    local_storage=not runtime.store.pg, hosted_local=config.production and not runtime.store.mirror)

    @app.errorhandler(StoreError)
    def storage_error(error):
        LOG.error("STORAGE %s", str(error))
        if wants_json():
            return json_error(str(error), 503)
        return render_template("error.html", title="Connection interrupted", message=str(error)), 503

    @app.errorhandler(HTTPException)
    def page_error(error):
        # A safe route hint makes 404s actionable without logging query strings,
        # API credentials, usernames, private IDs or arbitrary client path data.
        if error.code == 404:
            known_prefix = next((prefix for prefix in ("/admin", "/gaming", "/history", "/static")
                                 if request.path == prefix or request.path.startswith(prefix + "/")), None)
            safe_path = request.path[:100] if known_prefix and re.fullmatch(r"/[A-Za-z0-9/_-]+", request.path) else "unknown-route"
            LOG.warning("HTTP 404 method=%s path=%s request=%s (unregistered destination)",
                        request.method, safe_path, g.request_id)
        else:
            LOG.warning("HTTP %s %s returned %s (%s).", request.method, request.endpoint or "unmatched route", error.code, error.name)
        if wants_json():
            return json_error(error.description, error.code, getattr(error, 'problem_code', None))
        return render_template("error.html", title="Page unavailable" if error.code == 404 else "Request could not be completed",
                               message=error.description), error.code

    @app.errorhandler(500)
    def internal_error(error):
        original = getattr(error, 'original_exception', None)
        if original is not None:
            LOG.error('REQUEST id=%s endpoint=%s failed with %s.',
                      getattr(g, 'request_id', 'unknown'), request.endpoint or 'unmatched',
                      type(original).__name__,
                      exc_info=(type(original), original, original.__traceback__))
        else:
            LOG.error('REQUEST id=%s endpoint=%s returned HTTP 500.',
                      getattr(g, 'request_id', 'unknown'), request.endpoint or 'unmatched')
        if wants_json():
            return json_error("The backend could not complete this request. Check the runtime logs and try again.", 500)
        return render_template("error.html", title="Something interrupted this request", message="Reload and try again. Existing saved data remains in place."), 500

    @app.get("/")
    def index():
        return render_template("index.html", data=public_snapshot())

    @app.get('/history')
    def public_history():
        # This request reads a small saved snapshot; it never calls Shuffle.
        return render_template('history.html', data=runtime.public(),
                               history=runtime.history.public(request.args.get('week')))

    @app.get('/history-state')
    def history_state():
        return jsonify(release=RELEASE, **runtime.history.public(request.args.get('week')))

    @app.post('/admin/history/refresh')
    @protected
    def refresh_history():
        require_csrf()
        runtime.history.request_refresh()
        if runtime.started:
            runtime.history.start()
        LOG.info('HISTORY Admin queued completed-week checks; provider retry windows remain enforced.')
        return admin_saved('History check queued. Saved results stay visible; provider retry times still apply.',
                           'overview', 'historyConnection')

    def public_snapshot():
        return runtime.public()

    @app.get("/public-state")
    def public_state():
        # The representation excludes the moving clock, so its strong ETag
        # really describes identical bytes. Both 200 and 304 carry fresh time.
        value = public_snapshot()
        server_time = value.pop("server_time")
        response = jsonify(value)
        response.set_etag(token(value))
        response.headers["X-Server-Time"] = str(server_time)
        return response.make_conditional(request)

    def guest():
        """Return the signed Gaming identity, migrating the retired player cookie."""
        if not hasattr(g, "guest"):
            value = None
            try:
                value = player_signer.loads(request.cookies.get("rh_player", ""), max_age=365*86400)
            except BadSignature:
                try:
                    value = legacy_player_signer.loads(request.cookies.get("rh_raider", ""), max_age=365*86400)
                    g.new_guest = value  # Reissue under the new cookie/salt.
                except BadSignature:
                    value = g.new_guest = secrets.token_hex(16)
            if not isinstance(value, str) or not re.fullmatch(r"[a-f0-9]{32}", value):
                value = g.new_guest = secrets.token_hex(16)
            g.guest = value
        return g.guest

    def player_csrf():
        """Bind game writes to the signed player independently of admin login."""
        secret = app.secret_key.encode() if isinstance(app.secret_key, str) else app.secret_key
        return hmac.new(secret, ('redpoints-write-v1:' + guest()).encode(), hashlib.sha256).hexdigest()

    def require_player_csrf():
        guest()
        if getattr(g, 'new_guest', None) and not request.cookies.get(('rh_player')) and not request.cookies.get('rh_raider'):
            failure = BadRequest(description='Your browser did not return the player cookie. Open the game directly on its HTTPS site, allow site cookies, then reload. Use http://localhost:8080 for local testing.')
            failure.problem_code = 'player_cookie_required'
            raise failure
        supplied = request.headers.get('X-CSRF-Token') or request.form.get('csrf', '')
        if isinstance(supplied, str) and supplied.isascii() and hmac.compare_digest(supplied, player_csrf()):
            return
        try:
            require_csrf()
        except BadRequest as failure:
            failure.problem_code = 'csrf_expired'
            raise

    def gaming_wallet():
        return gaming.view(guest(), '', client_ip=g.client_ip)

    def gaming_player_name():
        wallet = gaming_wallet()
        if wallet.get('play_blocked'):
            issue = wallet['play_blocked']
            raise GamingError(issue['message'], issue['code'], 409)
        if wallet['needs_profile']:
            raise GamingError('Save your Gaming name before playing.', 'community_name_required', 409)
        return wallet['name']

    @app.get('/gaming')
    def gaming_home():
        return render_template('gaming.html', data=runtime.public(), wallet=gaming_wallet(),
                               community=gaming.public_leaderboard(),
                               game=None, game_rules=gaming_rules(), player_token=player_csrf())

    @app.get('/gaming/fairness')
    def gaming_fairness():
        return render_template('gaming_fairness.html', data=runtime.public())

    @app.get('/gaming/<game>')
    def gaming_game(game):
        if game not in GAMES: abort(404)
        return render_template('gaming.html', data=runtime.public(), wallet=gaming_wallet(),
                               community=gaming.public_leaderboard(),
                               game=game, game_rules=gaming_rules(), player_token=player_csrf())

    @app.get('/gaming/api/state')
    def gaming_state():
        # The Gaming page uses one five-second request for its private wallet and
        # the sanitized public community board. This avoids duplicate polling.
        value = dict(ok=True, wallet=gaming_wallet(), community=gaming.public_leaderboard(),
                     player_csrf=player_csrf(), release=RELEASE)
        response = jsonify(value)
        response.set_etag(token(value))
        return response.make_conditional(request)

    @app.get('/gaming/api/public-leaderboard')
    def gaming_public_leaderboard():
        # Public allowlist only: no wallet IDs, balances, IPs, seeds, receipts,
        # recovery data or admin funding adjustments.
        value = dict(ok=True, **gaming.public_leaderboard(), release=RELEASE)
        response = jsonify(value)
        response.set_etag(token(value))
        response.headers['Cache-Control'] = 'public, no-cache'
        return response.make_conditional(request)

    @app.post('/gaming/api/refresh')
    def gaming_refresh():
        # Reset only the signed player's wallet, with the same CSRF rules as bets.
        require_player_csrf()
        try:
            result = gaming.refresh_balance(guest(), gaming_player_name(),
                                             request.get_json(silent=True), client_ip=g.client_ip)
            return jsonify(**result, player_csrf=player_csrf(), release=RELEASE)
        except ValueError as exc:
            return json_error(str(exc), getattr(exc, 'status', 422), getattr(exc, 'code', 'invalid_refresh'))

    @app.post('/gaming/api/profile')
    def gaming_profile():
        require_player_csrf()
        body = request.get_json(silent=True)
        if not isinstance(body, dict):
            return json_error('Enter a valid player name.', 422)
        try:
            visibility = body.get('public_visibility')
            # Compatibility for an old cached Gaming asset during a rolling
            # deployment: preserve the existing choice when the field is absent.
            if visibility is None:
                visibility = bool(gaming_wallet().get('public_visibility', False))
            if type(visibility) is not bool:
                return json_error('Choose whether your Gaming name appears publicly.', 422, 'invalid_visibility')
            wallet = gaming.confirm_community_name(guest(), body.get('username'), visibility, client_ip=g.client_ip)
            return jsonify(ok=True, wallet=wallet, player_csrf=player_csrf(), release=RELEASE)
        except ValueError as exc:
            return json_error(str(exc), getattr(exc, 'status', 422), getattr(exc, 'code', 'invalid_name'))

    @app.post('/gaming/api/recovery-code')
    def gaming_recovery_code():
        require_player_csrf()
        identity = guest()
        try:
            code = recovery_signer.dumps({'player': identity, 'nonce': secrets.token_hex(16)})
            wallet = gaming.save_recovery(identity, hashlib.sha256(code.encode()).hexdigest())
            return jsonify(ok=True, code=code, wallet=wallet, player_csrf=player_csrf(), release=RELEASE)
        except ValueError as exc:
            return json_error(str(exc), getattr(exc, 'status', 422), getattr(exc, 'code', 'invalid_recovery'))

    @app.post('/gaming/api/recover')
    def gaming_recover():
        require_player_csrf()
        body = request.get_json(silent=True) or {}
        code = body.get('code', '') if isinstance(body, dict) else ''
        if not isinstance(code, str) or not 20 <= len(code) <= 512:
            return json_error('That recovery code is invalid or was replaced.', 400, 'invalid_recovery')
        decoded = None
        for signer in (recovery_signer, legacy_recovery_signer):
            try:
                decoded = signer.loads(code)
                break
            except BadSignature:
                continue
        original = (decoded.get('player') or decoded.get('guest')) if isinstance(decoded, dict) else None
        if not isinstance(original, str) or not re.fullmatch(r'[a-f0-9]{32}', original):
            return json_error('That recovery code is invalid or was replaced.', 400, 'invalid_recovery')
        try:
            wallet = gaming.recover(original, hashlib.sha256(code.encode()).hexdigest(), client_ip=g.client_ip)
            g.guest = g.new_guest = original
            return jsonify(ok=True, wallet=wallet, player_csrf=player_csrf(), release=RELEASE)
        except ValueError as exc:
            return json_error(str(exc), getattr(exc, 'status', 400), getattr(exc, 'code', 'invalid_recovery'))

    @app.post('/gaming/api/bet')
    def gaming_bet():
        require_player_csrf()
        body = request.get_json(silent=True)
        if not isinstance(body, dict) or body.get('rules_version') not in SUPPORTED_VERSIONS:
            return json_error('Reload to use the current game rules.', 409, 'release_mismatch')
        try:
            result = gaming.bet(guest(), gaming_player_name(), body, client_ip=g.client_ip)
            return jsonify(**result, player_csrf=player_csrf(), release=RELEASE)
        except ValueError as exc:
            return json_error(str(exc), getattr(exc, 'status', 422), getattr(exc, 'code', 'invalid_bet'))

    @app.post('/gaming/api/blackjack/action')
    def gaming_blackjack_action():
        require_player_csrf()
        body = request.get_json(silent=True)
        try:
            result = gaming.blackjack_action(guest(), gaming_player_name(),
                                             body, client_ip=g.client_ip)
            return jsonify(**result, player_csrf=player_csrf(), release=RELEASE)
        except ValueError as exc:
            return json_error(str(exc), getattr(exc, 'status', 422), getattr(exc, 'code', 'invalid_move'))

    @app.post('/gaming/api/poker/action')
    def gaming_poker_action():
        require_player_csrf()
        try:
            result = gaming.poker_action(guest(), gaming_player_name(),
                                         request.get_json(silent=True), client_ip=g.client_ip)
            return jsonify(**result, player_csrf=player_csrf(), release=RELEASE)
        except ValueError as exc:
            return json_error(str(exc), getattr(exc, 'status', 422), getattr(exc, 'code', 'invalid_move'))

    @app.get('/gaming/api/receipts')
    def gaming_receipts():
        # Owner's revealed receipts only. Active server seeds never leave storage.
        return Response(json.dumps(gaming_wallet()['receipts'], indent=2), mimetype='application/json',
                        headers={'Content-Disposition':'attachment; filename=redpoints-receipts.json'})

    @app.get('/admin/gaming')
    @protected
    def admin_gaming_page():
        return render_admin('gaming')

    @app.get('/admin/gaming/status')
    @protected
    def admin_gaming_status():
        # Local Gaming statistics only; this endpoint never contacts providers.
        response = jsonify(ok=True, **gaming.leaders(), public_activity=gaming.public_leaderboard(),
                           release=RELEASE, visitor_ip_configured=not config.production or config.proxy)
        response.set_etag(token(response.get_json()))
        return response.make_conditional(request)

    @app.post('/admin/gaming/grant')
    @protected
    def admin_gaming_grant():
        require_csrf()
        body = request.get_json(silent=True) if request.is_json else request.form
        try:
            result = gaming.grant_everyone(body.get('request_id') if body else None, g.user)
            message = (f"{'Already granted' if result['duplicate'] else 'Granted'} +100,000 RedPoints "
                       f"to {result['players']:,} Gaming {'wallet' if result['players'] == 1 else 'wallets'}. Game winnings and records are unchanged.")
            if not result['players']:
                message = 'No Gaming wallets exist yet. Players receive 100,000 when they save their community name.'
            if wants_json():
                return jsonify(ok=True, **gaming.leaders(), grant=result, message=message,
                               next_request_id=secrets.token_hex(16), release=RELEASE)
            flash(message)
            return redirect(url_for('admin_gaming_page', _anchor='gamingFunding'), 303)
        except ValueError as exc:
            if wants_json():
                return json_error(str(exc), getattr(exc, 'status', 422), getattr(exc, 'code', 'invalid_grant'))
            return render_admin('gaming', errors={'gaming':str(exc)}, status=getattr(exc, 'status', 422))

    @app.get("/data")
    def data():
        return jsonify(runtime.public())

    @app.get("/config")
    def public_config():
        return jsonify(runtime.public()["site"])

    @app.get("/stream")
    def stream():
        return jsonify(runtime.public()["stream"])

    @app.get("/healthz")
    def health():
        return jsonify(ok=True, release=RELEASE)

    @app.get("/readyz")
    def ready():
        check = runtime.store.readiness()
        return jsonify(ok=check['ok'], release=RELEASE, checked_at=check['checked_at']), 200 if check['ok'] else 503

    def recovery_status():
        with runtime.lock:
            return checkpoint_status(runtime.store.checkpoint(), runtime.admin, runtime.shuffle["rows"], gaming.recovery())

    def render_admin(tab=None, draft=None, errors=None, confirm_race=False, restore=None, status=200,
                     change_review=None, review_token=None, recovery_review=None, section_focus=None):
        if status >= 400 and wants_json():
            return json_error(' '.join((errors or {}).values()) or 'This change could not be saved.', status)
        tab = tab or request.args.get("tab", "overview")
        if tab not in TABS:
            tab = "overview"
        values = runtime.status()
        values['gaming'] = gaming.leaders()
        values['gaming']['public_activity'] = gaming.public_leaderboard()
        values['health'] = health_view(runtime, measurements, values)
        values["checkpoint"] = recovery_status() if g.superadmin else None
        empire_status = runtime.empiredrop.private_status(g.admin["site_settings"])
        values["providers"] = summarize_providers(values, empire_status, activity.provider_trends())
        values["durability"] = dict(mode='Spaces mirror' if runtime.store.mirror else 'Local JSON',
                                    remote=bool(runtime.store.mirror),
                                    revision=g.revision,
                                    last_mirrored=(runtime.store.mirror.last_verified if runtime.store.mirror else 0))
        visible = filtered(values["rows"], values["edits"], request.args)
        form = copy.deepcopy(g.admin["site_settings"])
        form.update(start_et=local_input(form["start_time"]), end_et=local_input(form["end_time"]))
        form.update({"prize_"+k: v for k, v in form["prizes"].items()})
        if draft:
            form.update(draft)
        receipt = session.pop('admin_receipt', None) if request.method == 'GET' else None
        if receipt and (receipt.get('user') != g.user or receipt.get('tab') != tab or time.time()-receipt.get('at', 0) > 120):
            receipt = None
        return render_template("admin.html", data=values, tab=tab, form=form, errors=errors or {},
                               revision=(draft or {}).get("revision", g.revision), admin=g.admin, user=g.user,
                               superadmin=g.superadmin, participants=visible, confirm_race=confirm_race, restore=restore,
                               access_log=list(access_log), defaults=DEFAULT_PRIZES, limit=config.limit,
                               change_review=change_review, review_token=review_token,
                               recovery_review=recovery_review, admin_receipt=receipt,
                               gaming_grant_id=secrets.token_hex(16),
                               empire_reward_submission_id=secrets.token_urlsafe(18),
                               empire_admin=empire_status, section_focus=section_focus), status

    def admin_saved(message, tab, target):
        """A receipt is created only after the state commit succeeds.

        JSON writes redirect once to the native page; invalid writes stay in the
        original form so the browser can retain drafts and selected upload files.
        Never save passwords or form bodies in a receipt or log.
        """
        session['admin_receipt'] = dict(message=message, user=g.user, tab=tab,
                                        target=target, at=int(time.time()))
        destination = admin_link(tab) + '#feedback-' + target
        if wants_json():
            return jsonify(ok=True, message=message, redirect=destination, release=RELEASE)
        return redirect(destination, 303)

    @app.route("/admin", methods=["GET", "POST"], endpoint="admin_main")
    @app.route("/admin/login", methods=["GET", "POST"])
    def login():
        if request.method == "GET":
            return render_admin() if g.user else render_template("login.html", error="")
        require_csrf()
        name, password = request.form.get("username", "").strip()[:64], request.form.get("password", "")
        key = g.client_ip or request.remote_addr or "unknown"
        with auth_lock:
            cutoff = time.monotonic() - 600
            for ip in list(failures):
                failures[ip] = [t for t in failures[ip] if t > cutoff]
                if not failures[ip]:
                    del failures[ip]
            if len(failures) >= 2000 and key not in failures:
                return render_template("login.html", error="Too many sign-in attempts. Please try again later."), 429
            if len(failures.get(key, [])) >= 5:
                return render_template("login.html", error="Too many sign-in attempts. Wait ten minutes and try again."), 429
            failures.setdefault(key, []).append(time.monotonic())
        canonical, record = account(g.admin["users"], name)
        valid = check_password_hash(record["pw_hash"] if record else dummy_hash, password[:256])
        if not valid or not canonical or len(password) > 256:
            return render_template("login.html", error="The username or password is incorrect."), 401
        with auth_lock:
            failures.pop(key, None)
        session.clear()
        session.update(user=canonical, auth_version=record.get("auth_version", 1), csrf=secrets.token_urlsafe(32))
        session.permanent = True
        LOG.info("ADMIN Sign-in successful.")
        return redirect(admin_link("overview"), 303)

    # Stable V13 workspace routes. Each visible navigation target resolves
    # directly to an authenticated page instead of depending on query parsing.
    def workspace(tab, focus=None):
        return render_admin(tab, section_focus=focus)

    @app.get('/admin/leaderboards/shuffle')
    @protected
    def admin_shuffle_page():
        return workspace('shuffle')

    @app.get('/admin/leaderboards/shuffle/schedule')
    @protected
    def admin_shuffle_schedule_page():
        return workspace('race', 'schedule')

    @app.get('/admin/leaderboards/shuffle/players')
    @protected
    def admin_shuffle_players_page():
        return workspace('players')

    @app.get('/admin/leaderboards/shuffle/prizes')
    @protected
    def admin_shuffle_prizes_page():
        return workspace('race', 'prizes')

    @app.get('/admin/leaderboards/shuffle/source')
    @protected
    def admin_shuffle_source_page():
        return workspace('shuffle', 'shuffleSource')

    @app.get('/admin/leaderboards/empiredrop')
    @protected
    def admin_empiredrop_page():
        return workspace('empiredrop')

    @app.get('/admin/leaderboards/empiredrop/schedule')
    @protected
    def admin_empiredrop_schedule_page():
        return workspace('empiredrop', 'empireDatesTitle')

    @app.get('/admin/leaderboards/empiredrop/payouts')
    @protected
    def admin_empiredrop_payouts_page():
        return workspace('empiredrop', 'empireRewards')

    @app.get('/admin/leaderboards/empiredrop/source')
    @protected
    def admin_empiredrop_source_page():
        return workspace('empiredrop', 'empireRaceDetails')

    @app.get('/admin/settings')
    @protected
    def admin_settings_page():
        return workspace('settings')

    @app.get('/admin/recovery')
    @protected
    def admin_recovery_page():
        return workspace('settings', 'recovery')

    @app.get('/admin/activity')
    @protected
    def admin_activity_page():
        return workspace('activity')

    # Cached V9/V10/V11 links remain safe compatibility aliases.
    @app.get('/admin/section/<section>')
    @protected
    def admin_section_compat(section):
        tab = ADMIN_SECTION_ALIASES.get(section.strip().lower())
        if tab is None:
            abort(404, description="Unknown admin section. Open Control Center and try again.")
        anchor = {'recovery': 'recovery', 'accounts': 'adminAccounts',
                  'connections': 'configurationDetails'}.get(section)
        return redirect(admin_link(tab, anchor) if anchor else admin_link(tab), code=302)

    # Old bookmarked paths redirect to canonical destinations.
    legacy_destinations = {
        '/admin/overview': 'overview', '/admin/leaderboards': 'shuffle',
        '/admin/shuffle': 'shuffle', '/admin/race': 'race',
        '/admin/schedule': 'race', '/admin/players': 'players',
        '/admin/empiredrop': 'empiredrop', '/admin/community': 'gaming',
        '/admin/logs': 'activity',
    }
    for legacy_path, legacy_tab in legacy_destinations.items():
        def legacy_admin_destination(_tab=legacy_tab):
            return redirect(admin_link(_tab), code=302)
        endpoint = 'admin_compat_' + legacy_path.strip('/').replace('/', '_')
        app.add_url_rule(legacy_path, endpoint=endpoint, view_func=protected(legacy_admin_destination), methods=['GET'])

    required_actions = {
        '/admin', '/admin/section/<section>', '/admin/action', '/admin/logout',
        '/admin/leaderboards/shuffle', '/admin/leaderboards/shuffle/schedule',
        '/admin/leaderboards/shuffle/players', '/admin/leaderboards/shuffle/prizes',
        '/admin/leaderboards/shuffle/source', '/admin/leaderboards/empiredrop',
        '/admin/leaderboards/empiredrop/schedule', '/admin/leaderboards/empiredrop/payouts',
        '/admin/leaderboards/empiredrop/source', '/admin/gaming', '/admin/settings',
        '/admin/recovery', '/admin/activity',
        '/admin/empiredrop/refresh', '/admin/empiredrop/schedule',
        '/admin/empiredrop/rewards', '/admin/empiredrop/races/config',
        '/admin/empiredrop/keys'
    }

    @app.get('/admin/navigation-status')
    @protected
    def admin_navigation_status():
        """Safe diagnostic: destinations and methods only, no credentials."""
        return jsonify(ok=True, release=RELEASE, sections={
            name: admin_link(tab) for name, tab in ADMIN_SECTION_ALIASES.items()
        }, registered=[{'path': rule.rule, 'methods': sorted(rule.methods - {'HEAD','OPTIONS'})}
                      for rule in app.url_map.iter_rules()
                      if rule.rule.startswith('/admin') and not '<' in rule.rule])

    @app.post("/admin/logout")
    def logout():
        require_csrf()
        session.clear()
        return redirect(url_for("login"), 303)

    @app.get("/admin/status")
    @protected
    def status():
        value = runtime.status()
        # The dedicated gaming feed owns fast rankings. Older clients still
        # receive them unless they explicitly opt out of this duplicate body.
        if request.args.get('gaming') != '0':
            value['gaming'] = gaming.leaders()
        value['health'] = health_view(runtime, measurements, value)
        value["checkpoint"] = recovery_status() if g.superadmin else None
        value["providers"] = summarize_providers(value, runtime.empiredrop.private_status(g.admin["site_settings"]), activity.provider_trends())
        rows, edits = value.pop("rows"), value.pop("edits")
        # Other tabs have no participant table; keep their minute responses small.
        if request.args.get("tab", "players") == "players":
            value["participants"] = filtered(rows, edits, request.args)
        if request.args.get("code_red") != "1":
            value.pop("red", None)
        return jsonify(value)

    @app.get('/admin/empiredrop/status')
    @protected
    def empire_admin_status():
        """Protected provider diagnostics; a public request can never read names."""
        return jsonify(runtime.empiredrop.private_status(g.admin['site_settings']))

    @app.post('/admin/empiredrop/refresh')
    @protected
    def empire_admin_refresh():
        """Queue an independent worker check; do not claim success when queued."""
        require_csrf()
        if runtime.started:
            queued = runtime.empiredrop.request_refresh()
            if queued: safe_activity('empiredrop','info','refresh_queued')
            message = ('EmpireDrop refresh requested; check status for the confirmed result.' if queued
                       else 'A refresh was requested recently; the 15-second limit is still active.')
        else:
            message = 'The EmpireDrop worker is not running. Launch python wager_backend.py.'
        return admin_saved(message, 'empiredrop', 'empireRefresh')

    @app.post('/admin/empiredrop/test')
    @protected
    def empire_admin_test():
        """Test authenticated access WITHOUT publishing or changing any standings.

        This is a real network test only when the Superadmin has confirmed the
        official provider contract; otherwise it fails safely with an explanation.
        """
        require_csrf()
        if not g.superadmin:
            abort(403)
        try:
            source_mode = runtime.empiredrop._race_settings()['source_mode']
            if source_mode == 'races':
                rows, _ = runtime.empiredrop._fetch_races(empire_schedule(g.admin))
            elif source_mode == 'legacy_window':
                rows, _ = runtime.empiredrop._fetch_window(empire_schedule(g.admin))
            else:
                rows = runtime.empiredrop.fetch(empire_schedule(g.admin))
        except ProviderError as exc:
            # Only our own short safe exception text is exposed; no response body or keys.
            result = {'ok': False, 'kind': exc.kind, 'message': str(exc)[:220]}
            status = 422
        else:
            result = {'ok': True, 'kind': 'verified', 'message': 'Authenticated result validated. No standings were changed.',
                      'qualified_players': len(rows)}
            status = 200
        safe_activity('empiredrop','success' if status==200 else 'warning','connection_test',count=len(rows) if status==200 else None,
                        code=exc.kind if status!=200 and isinstance(exc,ProviderError) else None)
        return jsonify(result), status

    @app.post('/admin/empiredrop/discover')
    @protected
    def empire_admin_discover():
        """Read public-key race catalog; never return credentials or player PII."""
        require_csrf()
        if not g.superadmin: abort(403)
        try:
            return jsonify({'ok':True, **runtime.empiredrop.discover_races()})
        except ProviderError as exc:
            return jsonify({'ok':False, 'kind':exc.kind, 'message':str(exc)[:220]}), 422

    @app.post('/admin/empiredrop/probe')
    @protected
    def empire_admin_probe():
        """Return only JSON field names/types to aid correct field mapping."""
        require_csrf()
        if not g.superadmin: abort(403)
        try:
            # The slug can be left empty to use the uniquely active provider race.
            slug = str((request.get_json(silent=True) or {}).get('slug', '')).strip()
            if len(slug) > 100: raise ValueError('Invalid slug length.')
            return jsonify({'ok':True, **runtime.empiredrop.probe_race(slug)})
        except (ProviderError, ValueError) as exc:
            return jsonify({'ok':False, 'kind':getattr(exc,'kind','input'), 'message':str(exc)[:220]}), 422

    @app.post('/admin/empiredrop/races/config')
    @protected
    def empire_admin_race_config():
        """Persist race API settings independently of Shuffle and legacy mode."""
        require_csrf()
        if not g.superadmin: abort(403)
        try:
            expected = int(request.form.get('revision', '-1'))
            if expected != g.revision: raise Conflict('Settings changed. Reload and try again.')
            # Authentication, endpoint, units and JSON paths are FIXED by the
            # official OpenAPI 2.0.1. Admins only choose which race to display.
            values = {
                'source_mode': request.form.get('source_mode', 'races').strip(),
                'race_slug': request.form.get('race_slug', '').strip(),
                'auto_select': request.form.get('auto_select') == 'yes',
                'race_window_policy': request.form.get('race_window_policy', 'provider').strip(),
            }
            candidate = copy.deepcopy(g.admin)
            candidate['empiredrop_races'] = validate_race_settings(values)
            runtime.commit(candidate, expected)
            runtime.empiredrop.request_refresh()
            safe_activity('admin','info','settings_saved',code='empire_settings')
            return admin_saved('EmpireDrop race API settings saved; a refresh was queued. Verify results before publishing.',
                               'empiredrop', 'empireRaces')
        except (ValueError, Conflict) as exc:
            return render_admin('empiredrop', errors={'empiredrop':str(exc)},
                                status=409 if isinstance(exc, Conflict) else 422)

    @app.post('/admin/empiredrop/schedule')
    @protected
    def empire_admin_schedule():
        """EmpireDrop calendar is never copied from or written into Shuffle."""
        require_csrf()
        if not g.superadmin:
            abort(403)
        try:
            expected = int(request.form.get('revision', '-1'))
            if expected != g.revision:
                raise Conflict('Another administrator saved settings. Reload before editing.')
            mode = request.form.get('mode')
            if mode == 'weekly':
                value = {'mode':'weekly'}
            elif mode == 'custom':
                start = eastern_epoch(request.form.get('start_et'))
                end = eastern_epoch(request.form.get('end_et'))
                if not 0 < start < end <= 4102444799 or end-start > 90*86400:
                    raise ValueError('EmpireDrop custom race must be between 1 minute and 90 days.')
                value = {'mode':'custom', 'start_time':start, 'end_time':end}
            else:
                raise ValueError('Choose a valid EmpireDrop schedule mode.')
            candidate = copy.deepcopy(g.admin)
            candidate['empiredrop_race'] = value
            # Local dates are retained for administration and backup, but the
            # public standings remain on EmpireDrop's documented slug endpoint.
            # Earlier releases silently switched this form to the deprecated
            # timestamp endpoint, which could leave the public board empty.
            race_options = validate_race_settings(candidate.get('empiredrop_races', {}))
            race_options['source_mode'] = 'races'
            race_options['race_window_policy'] = 'provider'
            candidate['empiredrop_races'] = validate_race_settings(race_options)
            runtime.commit(candidate, expected)
            runtime.empiredrop.request_refresh()
            safe_activity('admin','info','settings_saved',code='empire_schedule')
            return admin_saved(
                'EmpireDrop local schedule saved. Official provider standings and dates remain authoritative.',
                'empiredrop', 'empireSchedule')
        except (ValueError, Conflict) as exc:
            return render_admin('empiredrop', errors={'empiredrop':str(exc)},
                                status=409 if isinstance(exc, Conflict) else 422)

    @app.post('/admin/empiredrop/rewards')
    @protected
    def empire_admin_rewards():
        """Idempotently save a draft or publish ten independent rank prizes.

        The payout editor has its own revision and per-form submission token.
        Double-clicks, browser retries and unchanged submissions cannot create
        duplicate state revisions or duplicate publication events.
        """
        require_csrf()
        if not g.superadmin:
            abort(403)
        try:
            expected = int(request.form.get('reward_revision', '0'))
            mode = resolve_reward_save_mode(request.form)
            submission_id = str(request.form.get('submission_id', '')).strip()
            if not re.fullmatch(r'[A-Za-z0-9_-]{16,80}', submission_id):
                raise ValueError('This payout form expired. Reload and try again.')
            duplicate = unchanged = False
            value = None
            with runtime.store.connection(transaction=True) as conn:
                last_submission = str(conn['admin'].get('empiredrop_reward_last_submission') or '')
                if last_submission and hmac.compare_digest(last_submission, submission_id):
                    duplicate = True
                else:
                    published = validate_rewards(conn['admin'].get('empiredrop_rewards', {}))
                    current = validate_rewards(conn['admin'].get('empiredrop_rewards_draft',
                                                                 conn['admin'].get('empiredrop_rewards', {})))
                    if expected != current['revision']:
                        raise Conflict('EmpireDrop prizes changed in another tab. Reload and review the saved values.')
                    payload = dict(
                        currency=request.form.get('currency', 'EUR'),
                        enabled=mode == 'publish',
                        prizes={str(n): request.form.get('prize_' + str(n), '') for n in range(1, 11)},
                        revision=current['revision'] + 1,
                        updated_at=int(time.time()),
                        updated_by=g.user,
                    )
                    value = validate_rewards(payload)
                    target = published if mode == 'publish' else current
                    unchanged = (
                        target.get('currency') == value.get('currency') and
                        target.get('prizes') == value.get('prizes') and
                        bool(target.get('enabled')) == bool(value.get('enabled'))
                    )
                    if not unchanged:
                        runtime.store.backup_in(conn, 'before-empiredrop-payout-change',
                                                {'empiredrop_rewards': published,
                                                 'empiredrop_rewards_draft': current})
                        conn['admin']['empiredrop_rewards_draft'] = copy.deepcopy(value)
                        if mode == 'publish':
                            conn['admin']['empiredrop_rewards'] = copy.deepcopy(value)
                        conn['admin']['empiredrop_reward_last_submission'] = submission_id
                        conn['admin']['settings_revision'] = int(conn['admin'].get('settings_revision', 1)) + 1
                        conn['admin']['updated_at'] = int(time.time())
                        conn['revision'] += 1
            if duplicate or unchanged:
                return admin_saved('No prize changes were detected. The published schedule was left unchanged.',
                                   'empiredrop', 'empireRewards')
            runtime.sync()
            _, persisted_admin = runtime.store.admin()
            persisted = validate_rewards(persisted_admin.get('empiredrop_rewards_draft',
                                                                persisted_admin.get('empiredrop_rewards', {})))
            if persisted != value:
                raise StoreError('The payout write could not be verified. Existing public prizes were not changed.')
            public_prizes = runtime.empiredrop.public().get('prizes', {})
            expected_public = rewards_public(value)
            if mode == 'publish' and public_prizes != expected_public:
                raise StoreError('The payout was saved but the public projection did not refresh. Reload before retrying.')
            safe_activity('admin', 'success', 'empire_rewards_published' if mode == 'publish' else 'empire_rewards_draft',
                          code='empire_rewards', count=10)
            message = (
                'EmpireDrop prizes saved and published on the public Top 10.'
                if mode == 'publish' else
                'EmpireDrop prize draft saved. The public leaderboard still shows the previously published state.'
            )
            return admin_saved(message, 'empiredrop', 'empireRewards')
        except (ValueError, Conflict, StoreError) as exc:
            safe_activity('admin', 'warning', 'empire_rewards_save_failed',
                          code='conflict' if isinstance(exc, Conflict) else 'validation')
            return render_admin('empiredrop', errors={'empiredrop': str(exc)},
                                status=409 if isinstance(exc, Conflict) else 422)

    @app.get('/admin/empiredrop/settings-backup')
    @protected
    def empire_settings_backup():
        """Export ONLY EmpireDrop admin choices. No live keys or player IDs."""
        if not g.superadmin: abort(403)
        _, current = runtime.store.admin()
        document = {
            'format': 'redhunllef-empiredrop-settings-2',
            'empiredrop_races': validate_race_settings(current.get('empiredrop_races', {})),
            'empiredrop_race': copy.deepcopy(current.get('empiredrop_race', {'mode':'weekly'})),
            'empiredrop_rewards': validate_rewards(current.get('empiredrop_rewards', {})),
            'empiredrop_rewards_draft': validate_rewards(current.get('empiredrop_rewards_draft', current.get('empiredrop_rewards', {}))),
        }
        safe_activity('admin','info','backup_export')
        return Response(json.dumps(document,indent=2),mimetype='application/json',
                        headers={'Content-Disposition':'attachment; filename=empiredrop-settings-backup.json'})

    @app.post('/admin/empiredrop/settings-restore')
    @protected
    def empire_settings_restore():
        """Opt-in import of settings ONLY; never replace accounts, games, or keys.

        A successful commit performs the store's ordinary revision-checked save.
        The separate provider worker then refreshes when its cache permits.
        """
        require_csrf()
        if not g.superadmin: abort(403)
        try:
            if request.form.get('confirm') != 'yes':
                raise ValueError('Check the confirmation before importing settings.')
            expected = int(request.form.get('revision','-1'))
            if expected != g.revision:
                raise Conflict('Settings changed. Reload and recheck the import.')
            upload = request.files.get('settings_file')
            if upload is None:
                raise ValueError('Select an EmpireDrop settings JSON file.')
            try:
                incoming = json.load(upload)
            except (ValueError,UnicodeDecodeError):
                raise ValueError('The selected file is not valid JSON.') from None
            if not isinstance(incoming, dict) or incoming.get('format') not in {
                    'redhunllef-empiredrop-settings-1', 'redhunllef-empiredrop-settings-2'}:
                raise ValueError('This is not a supported EmpireDrop settings backup.')
            required = {'format','empiredrop_races','empiredrop_race','empiredrop_rewards'}
            allowed = required | {'empiredrop_rewards_draft'}
            if not required.issubset(incoming) or set(incoming) - allowed:
                raise ValueError('This EmpireDrop settings backup has unexpected fields.')
            race = incoming['empiredrop_race']
            if not isinstance(race,dict) or race.get('mode') not in {'weekly','custom'}:
                raise ValueError('Invalid EmpireDrop race schedule in backup.')
            if race['mode']=='custom':
                start,end = race.get('start_time'),race.get('end_time')
                if type(start) is not int or type(end) is not int or                    not 0 < start < end <= 4102444799 or end-start>90*86400:
                    raise ValueError('Invalid custom race dates in backup.')
                race={'mode':'custom','start_time':start,'end_time':end}
            else:
                race={'mode':'weekly'}
            reward = validate_rewards(incoming['empiredrop_rewards'])
            reward_draft = validate_rewards(incoming.get('empiredrop_rewards_draft', reward))
            opts = validate_race_settings(incoming['empiredrop_races'])
            candidate = copy.deepcopy(g.admin)
            candidate.update(empiredrop_races=opts, empiredrop_race=race,
                             empiredrop_rewards=reward, empiredrop_rewards_draft=reward_draft)
            runtime.commit(candidate,expected,reason='before-empiredrop-settings-restore')
            runtime.empiredrop.request_refresh()
            safe_activity('admin','info','settings_saved')
            return admin_saved('EmpireDrop settings restored. Accounts, games, Shuffle and API keys were not changed.',
                               'empiredrop','empireBackup')
        except (ValueError,Conflict) as exc:
            return render_admin('empiredrop',errors={'empiredrop':str(exc)},
                                status=409 if isinstance(exc,Conflict) else 422)

    @app.post('/admin/empiredrop/keys')
    @protected
    def empire_admin_keys():
        """Update the server-side private file, never store credentials in admin JSON."""
        require_csrf()
        if not g.superadmin:
            abort(403)
        try:
            changed = config.replace_empiredrop_keys(request.form.get('empiredrop_public_key',''),
                                                     request.form.get('empiredrop_private_key',''))
            return admin_saved('EmpireDrop credentials updated in private/settings.json.' if changed
                               else 'No new credential was entered; existing keys remain unchanged.',
                               'empiredrop', 'empireKeys')
        except (ValueError, OSError) as exc:
            return render_admin('empiredrop', errors={'empiredrop':'Credential update failed: ' +
                                ('Check that private settings are writable.' if isinstance(exc,OSError) else str(exc))}, status=422)

    @app.post('/admin/empiredrop/config')
    @protected
    def empire_admin_config():
        require_csrf()
        if not g.superadmin:
            abort(403, description='Only the Superadmin can configure EmpireDrop.')
        try:
            expected = int(request.form.get('revision', '-1'))
            if expected != g.revision:
                raise Conflict('Another administrator changed settings. Reload and try again.')
            fields = {name: request.form.get(name, '').strip() for name in sorted(EDITABLE - {'code_scoped','verified_contract'})}
            fields['code_scoped'] = request.form.get('code_scoped') == 'yes'
            fields['verified_contract'] = request.form.get('verified_contract') == 'yes'
            candidate = copy.deepcopy(g.admin)
            candidate['empiredrop_api'] = validate_settings(fields)
            runtime.commit(candidate, expected)
            # Preserve the last verified result on configuration saves. It is
            # marked stale until a successful provider response replaces it.
            with runtime.empiredrop.lock:
                prior = dict(runtime.empiredrop.saved)
                if prior.get('updated_at'):
                    prior.update(error='API configuration changed; last verified results retained until rechecked.',
                                 error_kind='configuration')
                    runtime.store.publish('empiredrop', prior)
                    runtime.empiredrop.saved = prior
            runtime.empiredrop.request_refresh()
            return admin_saved('EmpireDrop API configuration saved. Last verified results preserved; refresh requested.',
                               'empiredrop', 'empireConfig')
        except (ValueError, Conflict) as exc:
            return render_admin('empiredrop', errors={'empiredrop':str(exc)},
                                status=409 if isinstance(exc, Conflict) else 422)

    @app.get('/admin/operations/events')
    @protected
    def operations_events():
        """Admin-only structured events. No usernames, addresses, keys, or bodies."""
        try:
            result = activity.list(request.args.get('service','all'),
                                   request.args.get('level','all'),request.args.get('limit','100'))
        except ValueError:
            return json_error('Choose valid event filters.',422)
        return jsonify(events=result, summary=activity.summary(request.args.get('service','all'),request.args.get('level','all')),
                       provider_trends=activity.provider_trends(),
                       retention='Last 300 events; reset on server restart')

    @app.get('/admin/operations/export')
    @protected
    def operations_export():
        """Download a minimal, safe operational report, never runtime snapshots."""
        try:
            report = activity.export(request.args.get('service','all'),
                                     request.args.get('level','all'))
        except ValueError:
            return json_error('Choose valid event filters.',422)
        # TXT is convenient when sharing a quick diagnostic excerpt. Both
        # formats are built exclusively from the allowlisted event schema.
        if request.args.get('format') == 'txt':
            lines = ['RedHunllef operational activity (sanitized)',
                     'Generated: '+report['generated_at'], report['retention'], '']
            for event in report['events']:
                lines.append('%s | %-10s | %-7s | %-24s | class=%s | HTTP %s | %s ms | ranked=%s | received=%s | accepted=%s | excluded=%s | unscoped=%s | %sx' % (
                    datetime.fromtimestamp(event['at'], timezone.utc).isoformat(),event['service'],event['level'],event['event'],
                    event.get('code') or '-',
                    event['http_status'] if event['http_status'] is not None else '-',
                    event['duration_ms'] if event['duration_ms'] is not None else '-',
                    event['count'] if event['count'] is not None else '-',
                    event.get('received') if event.get('received') is not None else '-',
                    event.get('accepted') if event.get('accepted') is not None else '-',
                    event.get('excluded') if event.get('excluded') is not None else '-',
                    event.get('unscoped') if event.get('unscoped') is not None else '-',
                    event.get('occurrences', 1)))
            return Response('\n'.join(lines)+'\n',mimetype='text/plain',
                            headers={'Content-Disposition':'attachment; filename=redhunllef-operations.txt'})
        return Response(json.dumps(report,indent=2),mimetype='application/json',
                        headers={'Content-Disposition':'attachment; filename=redhunllef-operations.json'})

    @app.get("/admin/diagnostics")
    @protected
    def diagnostics():
        value = runtime.status()
        safe = dict(diagnostics=value["diagnostics"], jobs=value["jobs"], freshness=value["freshness"],
                    history=value['history'], generated_at=int(time.time()))
        return Response(json.dumps(safe, indent=2), mimetype="application/json",
                        headers={"Content-Disposition":"attachment; filename=redhunllef-diagnostics.json"})

    @app.get('/admin/health-report')
    @protected
    def health_report():
        # All fields are chosen by health_view. Never dump runtime/state objects.
        return jsonify(health_view(runtime, measurements, runtime.status()))

    def safe_backup():
        with runtime.lock:
            saved, current = runtime.shuffle, runtime.admin
            return dict(backup_version=3, generated_at=int(time.time()), site_settings=copy.deepcopy(current["site_settings"]),
                        overrides=copy.deepcopy(current["overrides"]), race_history=copy.deepcopy(current["race_history"]),
                        leaderboard_snapshots=dict(race_key=saved["key"], last_top15=copy.deepcopy(saved["rows"][:15]),
                                                   prev_top15=copy.deepcopy(saved.get("previous_top", [])), updated_at=saved["updated_at"]))

    @app.get("/admin/backup")
    @protected
    def backup():
        safe_activity('admin','info','backup_export')
        return Response(json.dumps(safe_backup(), indent=2), mimetype="application/json",
                        headers={"Content-Disposition":"attachment; filename=redhunllef-race-backup.json"})

    @app.get("/admin/recovery-backup")
    @protected
    def recovery_backup():
        # A full account export is private to the Superadmin. It uses the same
        # validated seed format as startup and is never part of public feeds.
        if not g.superadmin:
            abort(403, description="Only the Superadmin can download private account recovery files.")
        # One transaction captures accounts, game stakes and receipts at the same
        # instant. Separate reads could otherwise straddle a settling game.
        with runtime.lock, runtime.store.connection(transaction=True) as conn:
            value = copy.deepcopy(conn['admin'])
            saved = conn['live']['shuffle']
            value['leaderboard_snapshots'] = dict(race_key=saved['key'], last_top15=copy.deepcopy(saved['rows'][:15]),
                prev_top15=copy.deepcopy(saved.get('previous_top', [])), updated_at=saved['updated_at'])
            value['weekly_history'] = copy.deepcopy(conn['live'].get('weekly_history'))
            value['redpoints'] = copy.deepcopy(conn.get('gaming'))
            marker = export_marker(conn['admin'], value["leaderboard_snapshots"], int(time.time()), value["redpoints"])
            value["recovery_export"] = marker
            conn['checkpoint'] = marker
        return Response(json.dumps(value, indent=2, ensure_ascii=False, allow_nan=False), mimetype="application/json",
                        headers={"Content-Disposition":"attachment; filename=recovery.seed.json"})

    @app.post("/admin/recovery-preview")
    @protected
    def recovery_preview():
        require_csrf()
        if not g.superadmin:
            abort(403)
        try:
            upload = request.files.get("recovery")
            if not upload:
                raise ValueError("Choose a private recovery JSON file.")
            value, _ = upgrade_store(json.load(upload), config.site, {})
            if not value["users"]:
                raise ValueError("The recovery file contains no administrator accounts.")
            # Older recovery files may include retired profile fields; they are
            # ignored rather than restored into the current application.
            redpoints = validate_gaming(value.get('redpoints'))
            review = dict(accounts=len(value["users"]), overrides=len(value["overrides"]),
                          history=len(value["race_history"]), rows=len(value["leaderboard_snapshots"]["last_top15"]),
                          start=fmt_et(value["site_settings"]["start_time"]), end=fmt_et(value["site_settings"]["end_time"]),
                          redpoints=len(redpoints['players']) if redpoints else 0)
            with runtime.store.connection() as conn:
                old_players = (conn.get('gaming') or {}).get('players', {})
                new_players = (redpoints or {}).get('players', {})
                review['comparison'] = dict(
                    accounts_before=len(conn['admin']['users']), wallets_before=len(old_players),
                    accounts_added=sorted(set(value['users'])-set(conn['admin']['users'])),
                    accounts_removed=sorted(set(conn['admin']['users'])-set(value['users'])),
                    accounts_changed=sum(conn['admin']['users'][key] != value['users'][key]
                                         for key in set(value['users']) & set(conn['admin']['users'])),
                    wallets_added=len(set(new_players)-set(old_players)),
                    wallets_removed=len(set(old_players)-set(new_players)),
                    wallets_changed=sum(old_players[key] != new_players[key] for key in set(new_players)&set(old_players)),
                    pending_before=sum(bool(p.get('poker') or p.get('blackjack')) for p in old_players.values()),
                    pending_after=sum(bool(p.get('poker') or p.get('blackjack')) for p in new_players.values()))
            return render_admin("settings", recovery_review=review)
        except (ValueError, RuntimeError, UnicodeDecodeError) as exc:
            return render_admin("settings", errors={"recovery":str(exc)}, status=422)

    @app.get("/admin/export.csv")
    @protected
    def export():
        value = runtime.status()
        rows = filtered(value["rows"], value["edits"], request.args)
        output = io.StringIO(newline="")
        writer = csv.writer(output)
        writer.writerow(["rank", "username", "weighted_wager", "original_weighted_wager", "raw_wager", "prize", "source", "last_source_update_et", "data_state"])
        for row in rows:
            writer.writerow([row["rank"] or "", csv_text(row["username"]), row["weighted_wager"], row["original_weighted_wager"],
                             row["raw_wager"], value["site"]["prizes"].get(str(row["rank"]), ""), row["source"],
                             fmt_et(value["freshness"]["updated_at"]), value["freshness"]["state"]])
        return Response("\ufeff" + output.getvalue(), mimetype="text/csv",
                        headers={"Content-Disposition":"attachment; filename=redhunllef-" + value["freshness"]["state"] + ".csv"})

    def validate_backup(upload):
        try:
            value = json.load(upload)
        except (ValueError, UnicodeDecodeError):
            raise ValueError("Choose a valid JSON backup.") from None
        if not isinstance(value, dict) or value.get("backup_version") not in {1, 2, 3}:
            raise ValueError("This backup version is not supported.")
        if not isinstance(value.get("site_settings"), dict):
            raise ValueError("The backup has no valid race settings.")
        site = canonical_site(value["site_settings"], config.site)
        if validate_site(site):
            raise ValueError("The backup contains invalid dates, prizes, or links.")
        overrides = clean_overrides(value.get("overrides", {}))
        snapshots = clean_snapshots(value.get("leaderboard_snapshots", {}), race_key(site))
        history = value.get("race_history", [])
        if not isinstance(history, list):
            raise ValueError("Race history must be a list.")
        for entry in history:
            if not isinstance(entry, dict) or not isinstance(entry.get("site_settings"), dict):
                raise ValueError("An archived race is invalid.")
            old_site = canonical_site(entry["site_settings"], config.site)
            if validate_site(old_site):
                raise ValueError("An archived race has invalid settings.")
            clean_overrides(entry.get("overrides", {}))
            clean_snapshots(entry.get("leaderboard_snapshots", {}), race_key(old_site))
        return dict(site_settings=site, overrides=overrides, leaderboard_snapshots=snapshots, race_history=history)

    @app.post("/admin/action")
    @protected
    def action():
        require_csrf()
        action_name, tab = request.form.get("action"), request.form.get("tab", "overview")
        if action_name == "refresh":
            name = request.form.get("service") or None
            if name not in {None, "shuffle", "kick"}:
                abort(400)
            receipt = runtime.request_refresh(name)
            LOG.info("REFRESH Check requested for %s; provider retry delays still apply.", name or "Shuffle and Kick")
            if wants_json():
                return jsonify(ok=True, message="Refresh queued. Its progress and result appear below.",
                               **receipt, jobs=runtime.job_status()), 202
            flash("Check requested. Results update automatically.")
            return redirect(admin_link(tab if tab in TABS else "overview"), 303)
        try:
            expected = int(request.form.get("revision", "0"))
            if expected != g.revision:
                raise Conflict("Another administrator changed saved settings. Reload and review your edits.")
            candidate, snapshot, reason, detail = copy.deepcopy(g.admin), None, None, "Changes saved."
            if action_name == "save_race":
                site = copy.deepcopy(candidate["site_settings"])
                site.update({k: request.form.get(k, "").strip() for k in (*TEXT_LIMITS, *URL_FIELDS, "kick_channel_slug")})
                errors = {}
                for key in ("start", "end"):
                    try:
                        site[key + "_time"] = eastern_epoch(request.form.get(key + "_et"))
                    except ValueError as exc:
                        errors[key + "_et"] = str(exc)
                site["prizes"] = {str(n): request.form.get("prize_" + str(n), "") for n in range(1, 16)}
                errors.update(validate_site(site))
                if errors:
                    return render_admin("race", dict(request.form), errors, status=422)
                site["prizes"] = {k: str(money_input(v)) for k, v in site["prizes"].items()}
                changed_race = race_key(site) != race_key(candidate["site_settings"])
                review = changes(candidate["site_settings"], site)
                expected_review = dict(user=g.user, revision=expected, site=site)
                try:
                    confirmed = request.form.get("confirm_race") == "yes" and review_signer.loads(request.form.get("review_token", ""), max_age=900) == expected_review
                except BadSignature:
                    confirmed = False
                if review and not confirmed:
                    return render_admin("race", dict(request.form), confirm_race=True, change_review=review,
                                        review_token=review_signer.dumps(expected_review))
                if changed_race:
                    old = safe_backup()
                    if candidate["site_settings"]["start_time"]:
                        candidate["race_history"].append({k: old[k] for k in ("site_settings", "overrides", "leaderboard_snapshots")} | {"archived_at":int(time.time())})
                    candidate["overrides"], reason = {}, "before-race-change"
                candidate["site_settings"] = site
                snapshot = empty(site) if changed_race else calculate(runtime.shuffle, candidate, config)
                detail = "Race published. A fresh check is queued for the saved dates; watch its progress below."
            elif action_name == "override":
                name, amount = request.form.get("username", "").strip(), request.form.get("amount", "").strip()
                if not name or len(name) > 64:
                    raise ValueError("Enter the exact full username, up to 64 characters.")
                if amount:
                    candidate["overrides"][name] = str(money_input(amount))
                else:
                    candidate["overrides"].pop(name, None)
                snapshot = calculate(runtime.shuffle, candidate, config)
                detail = f"Override saved for {name}: {money(candidate['overrides'][name])}." if amount else f"Override removed for {name}; source weighting restored."
            elif action_name in {"add_account", "remove_account", "reset_password", "password"}:
                if action_name != "password" and not g.superadmin:
                    abort(403)
                name = request.form.get("username", "").strip() if action_name != "password" else g.user
                canonical, record = account(candidate["users"], name)
                if action_name == "remove_account":
                    if not canonical or canonical.casefold() == candidate.get("superadmin", config.superadmin).casefold():
                        raise ValueError("The protected Superadmin account cannot be removed.")
                    del candidate["users"][canonical]
                    reason = "before-account-removal"
                else:
                    password = request.form.get("new_password", "")
                    if not 12 <= len(password) <= 256 or password != request.form.get("confirm_password"):
                        raise ValueError("Use matching passwords with 12–256 characters.")
                    if action_name == "add_account":
                        if canonical or not re.fullmatch(r"[A-Za-z0-9_]{3,32}", name):
                            raise ValueError("Choose an unused username with 3–32 letters, numbers, or underscores.")
                        canonical, record = name, dict(auth_version=0, created_at=int(time.time()))
                    elif not record:
                        raise ValueError("That account does not exist.")
                    if action_name == "password" and not check_password_hash(record["pw_hash"], request.form.get("current_password", "")[:256]):
                        raise ValueError("The current password is incorrect.")
                    record.update(pw_hash=generate_password_hash(password), auth_version=record.get("auth_version", 1) + 1)
                    candidate["users"][canonical] = record
                    reason = "before-password-change" if action_name != "add_account" else None
                detail = f"Account updated: {name}. Removed or reset accounts lose their previous sessions."
            elif action_name == "preview_restore":
                upload = request.files.get("backup")
                if not upload:
                    raise ValueError("Choose a backup file.")
                value = validate_backup(upload)
                identifier = secrets.token_urlsafe(32)
                with auth_lock:
                    for key in list(previews):
                        if previews[key]["expires"] < time.time():
                            del previews[key]
                    if len(previews) >= 20:
                        raise ValueError("Too many pending restores. Wait ten minutes and try again.")
                    previews[identifier] = dict(value=value, user=g.user, expires=time.time()+600, revision=expected)
                return render_admin("settings", restore=dict(token=identifier, start=fmt_et(value["site_settings"]["start_time"]),
                                    end=fmt_et(value["site_settings"]["end_time"]), rows=len(value["leaderboard_snapshots"]["last_top15"]),
                                    overrides=len(value["overrides"]), history=len(value["race_history"]),
                                    changes=changes(g.admin["site_settings"], value["site_settings"])))
            elif action_name == "restore":
                with auth_lock:
                    preview = previews.get(request.form.get("restore_token"))
                    if not preview or preview["expires"] < time.time() or preview["user"] != g.user or preview["revision"] != expected:
                        raise ValueError("Restore preview expired or settings changed. Review the backup again.")
                    value = copy.deepcopy(preview["value"])
                candidate.update({k: value[k] for k in ("site_settings", "overrides", "race_history")})
                saved = value["leaderboard_snapshots"]
                snapshot = empty(candidate["site_settings"])
                snapshot.update(rows=saved["last_top15"], previous_top=saved["prev_top15"], updated_at=saved["updated_at"] or 0,
                                count=len(saved["last_top15"]), snapshot_only=bool(saved["last_top15"]),
                                source=[dict(username=r["username"], weighted=r["original_weighted_wager"], raw=r["raw_wager"], row_count=r["row_count"]) for r in saved["last_top15"]])
                reason, detail = "before-restore", "Backup restored. Accounts preserved; a private recovery copy was saved."
            elif action_name in {"ban_ip", "unban_ip"}:
                ip = str(ipaddress.ip_address(request.form.get("ip", "")))
                if action_name == "ban_ip" and ip == g.client_ip:
                    raise ValueError("You cannot block the address you are using.")
                candidate["banned_ips"] = sorted(set(candidate["banned_ips"]) | {ip}) if action_name == "ban_ip" else [x for x in candidate["banned_ips"] if x != ip]
            elif action_name == "clear_audit":
                if not g.superadmin:
                    abort(403)
                candidate["audit_log"], reason = [], "before-clearing-audit"
            elif action_name == "clear_access":
                with auth_lock:
                    access_log.clear()
            else:
                raise ValueError("This action is not supported.")
            candidate["updated_at"] = int(time.time())
            candidate["audit_log"].append(dict(ts_et=fmt_et(candidate["updated_at"]), admin_user=g.user, action=action_name, detail=detail))
            candidate["audit_log"] = candidate["audit_log"][-250:]
            runtime.commit(candidate, expected, snapshot=snapshot, reason=reason)
            if action_name in {"password", "reset_password"}:
                _, current = account(candidate["users"], g.user)
                session["auth_version"] = current["auth_version"]
            if action_name in {"save_race", "restore"}:
                runtime.request_refresh()
                LOG.info("RACE Published revision %s: %s -> %s; fresh provider checks queued.", runtime.revision,
                         fmt_et(candidate["site_settings"]["start_time"]), fmt_et(candidate["site_settings"]["end_time"]))
            # One sanitized operational event for the control panel. The detailed
            # account/adjustment audit remains in the protected persistent audit.
            if action_name in {'save_race', 'override', 'restore'}:
                safe_activity('admin', 'info', 'settings_saved', code='shuffle_settings')
            LOG.info("ADMIN %s completed.", action_name)
            if action_name == 'save_race':
                detail = f"Race saved: {candidate['site_settings']['race_title']}. {fmt_et(site['start_time'])} → {fmt_et(site['end_time'])}. Fresh source check queued."
            target = {'save_race':'raceForm', 'override':'override', 'password':'accountSecurity',
                      'add_account':'accounts', 'remove_account':'accounts', 'reset_password':'accounts',
                      'restore':'backups'}.get(action_name, 'accessControls')
            return admin_saved(detail, tab if tab in TABS else 'overview', target)
        except (ValueError, Conflict) as exc:
            return render_admin(tab, dict(request.form) if tab == "race" else None,
                                errors={"form":str(exc)}, status=409 if isinstance(exc, Conflict) else 422)

    missing_admin_actions = required_actions - {rule.rule for rule in app.url_map.iter_rules()}
    if missing_admin_actions:
        raise RuntimeError("Missing admin routes: " + ", ".join(sorted(missing_admin_actions)))
    return app


def main():
    boot_started = time.perf_counter()
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
    try:
        from release_check import check_release
        checked = check_release(strict='--check' in sys.argv)
        preflight_seconds = time.perf_counter() - boot_started
        if not checked['ok']:
            raise RuntimeError('Release check failed: '+'; '.join(checked['problems']))
        for warning in checked['warnings']:
            LOG.warning('RELEASE %s', warning)
        if '--check' in sys.argv:
            LOG.info('RELEASE Checked %s Python modules and %s templates. No accounts or game state changed.', checked['python_modules'], checked['templates'])
            return 0
        app = create_app()
        application_seconds = time.perf_counter() - boot_started - preflight_seconds
        config, runtime = app.extensions["settings"], app.extensions["runtime"]
        from waitress import create_server
        options = dict(host="0.0.0.0", port=config.port, threads=6, ident="RedHunllef", expose_tracebacks=False,
                       max_request_body_size=64*1024*1024, channel_timeout=60, clear_untrusted_proxy_headers=True)
        if config.proxy:
            # App Platform is the only trusted ingress. Do not enable this on
            # a directly exposed host. Waitress applies proxy interpretation once.
            options.update(trusted_proxy="*", trusted_proxy_count=1,
                           trusted_proxy_headers={"x-forwarded-proto", "x-forwarded-for"})
        server = create_server(app, **options)
        listener_seconds = time.perf_counter() - boot_started - preflight_seconds - application_seconds
        LOG.info("BOOT stages: preflight=%.3fs application=%.3fs listener=%.3fs",
                 preflight_seconds, application_seconds, listener_seconds)
        LOG.info("START RedHunllef %s listening on 0.0.0.0:%s; storage=%s.", RELEASE, config.port,
                 'JSON + Spaces mirror' if runtime.store.mirror else 'local JSON')
        LOG.info('HEALTH /healthz checks the process; /readyz checks local reads and writes. Provider delays appear separately in Admin Overview.')
        LOG.info("GAMING RedPoints identities, wallets and recovery are handled independently at /gaming.")
        if not runtime.store.pg:
            LOG.info("STORAGE Local file ready; no external database is required.")
            if config.production and not runtime.store.mirror:
                LOG.warning("STORAGE On App Platform, local changes are lost on redeploy/container replacement. Download the private recovery file from Settings after important changes.")
        for key, details in config.diagnostics().items():
            LOG.info("CONFIG %s: %s (%s).", key, "configured" if details["configured"] else "missing", details["source"])
        LOG.info("RACE Saved window: %s → %s. State=%s.", fmt_et(runtime.admin["site_settings"]["start_time"]),
                 fmt_et(runtime.admin["site_settings"]["end_time"]), phase(runtime.admin["site_settings"]))
        def shutdown(*_):
            raise KeyboardInterrupt
        signal.signal(signal.SIGTERM, shutdown)
        runtime.start()
        LOG.info("BOOT ready for HTTP after %.3fs; /healthz is process health, /readyz is storage readiness",
                 time.perf_counter() - boot_started)
        try:
            server.run()
        finally:
            runtime.stop()
            server.close()
            runtime.store.close()
        return 0
    except KeyboardInterrupt:
        return 0
    except (StoreError, ValueError, RuntimeError) as exc:
        LOG.error("STARTUP %s", str(exc))
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
```

## `weekly_history.py`

```python
"""Four completed Eastern-time weeks, cached in the existing JSON save.

Only the automatic worker contacts Shuffle. Page views read the cache, so traffic
cannot multiply provider requests. Unknown historical prizes are never invented.
"""
import copy
from datetime import datetime, timedelta
import logging
import threading
import time

from integrations import ProviderError
from race import normalize, rank, token
from race_support import EASTERN, clean_overrides, decimal_amount, fmt_et, money, race_key

LOG = logging.getLogger('redhunllef')

# Only these application-owned explanations reach logs or browser diagnostics.
# Never echo a response body, URL, API key, or arbitrary exception message.
PROBLEMS = {
    'credentials': 'Shuffle API key is missing. Configure SHUFFLE_API_KEY and restart.',
    'access': 'Shuffle rejected access. Check the affiliate key and its permissions.',
    'rate_limit': 'Shuffle is rate limiting requests. Waiting for its retry window.',
    'upstream': 'Shuffle returned a server error. Retrying automatically.',
    'window': 'Shuffle identified a date validation problem for this completed week.',
    'bad_request': 'Shuffle rejected a request parameter. The cause may be dates or another API parameter; check the configured endpoint.',
    'connect_timeout': 'Could not connect to Shuffle before the timeout. Check outbound connectivity.',
    'timeout': 'Shuffle did not finish this history query within the allowed time.',
    'connection': 'Could not reach Shuffle. Check DNS, outbound HTTPS, and provider availability.',
    'format': 'Shuffle returned data the leaderboard could not validate.',
    'response_limit': 'Shuffle exceeded the response size or time allowance.',
    'http': 'Shuffle returned an unexpected HTTP status.',
    'unknown': 'The history request failed. Check the runtime logs and connection settings.',
}


def problem(exc):
    status = getattr(exc, 'status', None)
    kind = getattr(exc, 'kind', 'format' if isinstance(exc, ValueError) else 'unknown')
    if status in (401, 403): kind = 'access'
    elif status == 429: kind = 'rate_limit'
    elif status and status >= 500: kind = 'upstream'
    elif status == 400 and kind not in {'window', 'bad_request'}: kind = 'bad_request'
    if kind not in PROBLEMS: kind = 'unknown'
    return kind, status


def completed_weeks(now=None):
    """Use calendar weeks, not fixed seconds: DST weeks can be 167/169 hours."""
    local = datetime.fromtimestamp(time.time() if now is None else now, EASTERN)
    end = local.replace(hour=18, minute=0, second=0, microsecond=0)
    end -= timedelta(days=(end.weekday() - 1) % 7)
    if end > local:
        end -= timedelta(days=7)
    result = []
    for _ in range(4):
        start = end - timedelta(days=7)
        result.append(dict(id=end.strftime('%Y-%m-%d'), start_time=int(start.timestamp()),
                           end_time=int(end.timestamp()), label=start.strftime('%b %d') + ' – ' + end.strftime('%b %d, %Y'),
                           start_et=fmt_et(start.timestamp()), end_et=fmt_et(end.timestamp())))
        end = start
    return result


def clean_history(value):
    """Validate the optional cache when importing a private recovery file."""
    if value is None:
        return dict(version=1, weeks=[])
    if not isinstance(value, dict) or value.get('version') != 1 or not isinstance(value.get('weeks'), list) or len(value['weeks']) > 4:
        raise ValueError('Invalid weekly race history cache.')
    result, seen = [], set()
    for row in value['weeks']:
        if not isinstance(row, dict):
            raise ValueError('Invalid weekly race history entry.')
        for key in ('start_time', 'end_time', 'updated_at', 'attempt_at', 'retry_at', 'count'):
            if type(row.get(key)) is not int or not 0 <= row[key] <= 10**12:
                raise ValueError('Invalid weekly race history counter.')
        expected = completed_weeks(row['end_time'])[0]
        if row['start_time'] != expected['start_time'] or row['end_time'] != expected['end_time'] or row.get('id') != expected['id'] or row['id'] in seen:
            raise ValueError('History must contain distinct Tuesday 6 PM Eastern weeks.')
        seen.add(row['id'])
        if not isinstance(row.get('scope'), str) or len(row['scope']) != 20:
            raise ValueError('Invalid history configuration reference.')
        for key in ('error', 'warning'):
            if not isinstance(row.get(key), str) or len(row[key]) > 500:
                raise ValueError('Invalid history status.')
        if row.get('problem', 'unknown') not in PROBLEMS:
            raise ValueError('Invalid history problem code.')
        if row.get('http_status') is not None and (type(row['http_status']) is not int or not 100 <= row['http_status'] <= 599):
            raise ValueError('Invalid history HTTP status.')
        if type(row.get('failures', 0)) is not int or not 0 <= row.get('failures', 0) <= 100:
            raise ValueError('Invalid history retry count.')
        if row.get('origin', 'shuffle') not in {'shuffle', 'snapshot'}:
            raise ValueError('Invalid history result origin.')
        rows = row.get('rows')
        if not isinstance(rows, list) or len(rows) > 25 or row['count'] < len(rows):
            raise ValueError('Invalid historical leaderboard.')
        for n, player in enumerate(rows, 1):
            if (not isinstance(player, dict) or player.get('rank') != n or
                    not isinstance(player.get('username'), str) or not 1 <= len(player['username']) <= 64):
                raise ValueError('Invalid historical player.')
            decimal_amount(player.get('weighted_wager'))
        prizes = row.get('prizes')
        if prizes is not None:
            if not isinstance(prizes, dict) or set(prizes) != {str(n) for n in range(1, 16)}:
                raise ValueError('Invalid historical prizes.')
            for amount in prizes.values():
                decimal_amount(amount)
        result.append(copy.deepcopy(row))
    return dict(version=1, weeks=result)


class WeeklyHistory:
    def __init__(self, config, store, providers):
        self.config, self.store, self.providers = config, store, providers
        self.stop_event, self.thread = threading.Event(), None
        self.wake_event = threading.Event()
        self.force = False
        self.last_request = 0
        self.active_id = None
        self.lock = threading.RLock()
        self.check_lock = threading.Lock()
        clean_history(store.live('weekly_history'))

    def context(self, week, admin):
        # Use the latest saved settings for this exact period. Today's prize
        # pool or current-race overrides must never leak into an earlier week.
        candidates = [admin, *reversed(admin.get('race_history', []))]
        match = next((item for item in candidates if
            item['site_settings']['start_time'] == week['start_time'] and
            item['site_settings']['end_time'] == week['end_time']), None)
        site = copy.deepcopy((match or admin)['site_settings'])
        site.update(start_time=week['start_time'], end_time=week['end_time'])
        overrides = clean_overrides(match.get('overrides', {})) if match else {}
        prizes = copy.deepcopy(site['prizes']) if match else None
        scope = token([site['campaign_code_filter'], self.config.endpoint,
                       self.config.aggregation, self.config.raw_fallback,
                       self.config.credentials['shuffle_api_key'], overrides, prizes])
        return site, overrides, prizes, scope

    def request_refresh(self):
        """Queue a private admin request; do not block HTTP or bypass backoff."""
        with self.lock:
            if time.monotonic() - self.last_request >= 10:
                self.force = True
                self.last_request = time.monotonic()
                self.wake_event.set()

    def saved_result(self, period, admin, site):
        """Rescue exact-window snapshots; never relabel another race as history."""
        choices = []
        live = self.store.live('shuffle')
        if live and live.get('key') == race_key(site) and live.get('updated_at'):
            choices.append((live['updated_at'], live.get('rows', [])))
        for item in [admin, *admin.get('race_history', [])]:
            old_site = item.get('site_settings', {})
            snapshot = item.get('leaderboard_snapshots', {})
            if (race_key(old_site) == race_key(site) and snapshot.get('updated_at') and
                    snapshot.get('race_key', race_key(site)) == race_key(site)):
                choices.append((snapshot['updated_at'], snapshot.get('last_top15', [])))
        if not choices:
            return {}
        at, rows = max(choices, key=lambda item: item[0])
        # Old exports can contain fewer than 25 places and were not necessarily
        # captured after the cutoff. Clearly mark them as provisional snapshots.
        rows = [p for p in rows if isinstance(p.get('username'), str) and len(p['username']) <= 64]
        return dict(updated_at=at, origin='snapshot', count=len(rows),
                    rows=[dict(rank=n, username=p['username'], weighted_wager=str(decimal_amount(p['weighted_wager'])))
                          for n, p in enumerate(rows[:25], 1)],
                    warning='Saved race snapshot; the final top 25 is awaiting confirmation from Shuffle.')

    def diagnostics(self):
        """Admin-only explanations without provider URLs, keys, or player data."""
        public = self.public()
        saved = {w['id']: w for w in clean_history(self.store.live('weekly_history'))['weeks']}
        return dict(worker_alive=bool(self.thread and self.thread.is_alive()),
                    active_week=self.active_id, weeks=[dict(
                        id=w['id'], label=w['label'], status=w['status'],
                        message=PROBLEMS.get(saved.get(w['id'], {}).get('problem'), '') if w['status']=='delayed' else w['message'],
                        http_status=saved.get(w['id'], {}).get('http_status'),
                        updated_at=w['updated_at'], retry_at=w['retry_at'],
                        attempt_at=saved.get(w['id'], {}).get('attempt_at', 0)) for w in public['weeks']])

    def public(self, selected=None, now=None):
        now = int(time.time() if now is None else now)
        _, admin = self.store.admin()
        saved = {row['id']: row for row in clean_history(self.store.live('weekly_history'))['weeks']}
        weeks = []
        for period in completed_weeks(now):
            _, _, _, scope = self.context(period, admin)
            row = saved.get(period['id'], {})
            if row.get('scope') != scope:
                row = {}
            checked = row.get('updated_at', 0)
            status = 'delayed' if row.get('error') else 'partial' if row.get('warning') else 'ready' if checked else 'loading'
            code = row.get('problem', 'unknown')
            waiting = max(0, row.get('retry_at', 0) - now)
            failed_message = ('Shuffle access needs the host’s attention.' if code in {'access', 'credentials'} else
                              'Shuffle is busy; the next check is scheduled.' if code == 'rate_limit' else
                              'Shuffle could not confirm this week yet.')
            if row.get('error'):
                failed_message += (' Showing saved provisional places; final results still need confirmation.'
                                   if checked and row.get('origin') == 'snapshot' else
                                   ' Showing saved results.' if checked else ' No results have been confirmed yet.')
                failed_message += f' Retrying in about {max(1, (waiting + 59)//60)} minute(s).'
            message = (failed_message if row.get('error') else
                       row.get('warning') or ('No qualifying wagers were returned for this week.' if checked and not row.get('rows') else
                       ('Fetching this completed week from Shuffle…' if self.active_id == period['id'] else
                        'This week is queued for its first automatic check.') if not checked else ''))
            weeks.append({**period, 'status':status, 'message':message,
                'updated_at':checked, 'updated_et':fmt_et(checked) if checked else 'Awaiting first result',
                'retry_at':row.get('retry_at', 0), 'origin':row.get('origin', 'shuffle'),
                'count':row.get('count') if checked else None,
                'prizes_known':checked > 0 and row.get('prizes') is not None,
                'rows':[dict(rank=p['rank'], username=p['username'][:2] + '******',
                             wager=money(p['weighted_wager']),
                             prize=money(row['prizes'].get(str(p['rank']), '0')) if row.get('prizes') is not None else '—')
                        for p in row.get('rows', [])]})
        chosen = next((week for week in weeks if week['id'] == selected), weeks[0])
        return dict(weeks=weeks, selected=chosen, server_time=now, interval=60)

    def check(self, now=None):
        """Backfill up to four weeks; retain successes through provider errors."""
        if not self.check_lock.acquire(blocking=False):
            return 60
        try:
            return self._check(int(time.time() if now is None else now))
        finally:
            self.check_lock.release()

    def _check(self, now):
        revision, admin = self.store.admin()
        periods = completed_weeks(now)
        saved = clean_history(self.store.live('weekly_history'))
        cache = {row['id']: row for row in saved['weeks'] if row['id'] in {p['id'] for p in periods}}
        if len(cache) != len(saved['weeks']):
            self.store.publish('weekly_history', dict(version=1, weeks=list(cache.values())), revision)
        with self.lock:
            force, self.force = self.force, False
        # Never let a repeatedly failing recent week starve an untried older one.
        # Shared throttles still stop the batch and delay every pending week.
        periods.sort(key=lambda p: cache.get(p['id'], {}).get('attempt_at', 0))
        for period in periods:
            if self.stop_event.is_set():
                break
            site, overrides, prizes, scope = self.context(period, admin)
            previous = cache.get(period['id'], {})
            if previous.get('scope') != scope:
                previous = {}
            # Newly closed weeks recheck hourly for settlement corrections;
            # older completed weeks recheck daily. No API call per page view.
            refresh = 3600 if now - period['end_time'] < 86400 else 86400
            if previous.get('retry_at', 0) > now or (not force and previous.get('updated_at') and
                    not previous.get('error') and previous.get('origin') != 'snapshot' and now - previous['updated_at'] < refresh):
                continue
            record = {**period, 'scope':scope, 'updated_at':0, 'attempt_at':now,
                      'retry_at':0, 'count':0, 'rows':[], 'prizes':prizes,
                      'error':'', 'warning':'', **previous}
            record['attempt_at'] = now
            if not record['updated_at']:
                record.update(self.saved_result(period, admin, site))
                if record['updated_at']:
                    cache[period['id']] = record
                    self.store.publish('weekly_history', dict(version=1, weeks=list(cache.values())), revision)
            pause, shared = 0, False
            try:
                self.active_id = period['id']
                LOG.info('HISTORY Checking %s → %s via %s.', period['start_et'], period['end_et'], self.config.endpoint)
                incoming = normalize(self.providers.shuffle(site), site, self.config.raw_fallback)
                rows, _, count = rank(incoming['source'], overrides, self.config.aggregation, 25)
                record.update(rows=[dict(rank=p['rank'], username=p['username'], weighted_wager=p['weighted_wager']) for p in rows],
                              count=count, prizes=prizes, updated_at=now, error='', retry_at=0,
                              problem='unknown', http_status=200, failures=0, origin='shuffle',
                              warning=incoming['warning'][:500])
                LOG.info('HISTORY Saved %s to %s; %s qualifying players.', period['start_et'], period['end_et'], count)
            except (ProviderError, ValueError) as exc:
                code, status = problem(exc)
                failures = min(100, record.get('failures', 0) + 1)
                pause = max(min(900, 60 * 2**min(4, failures-1)), min(86400, getattr(exc, 'retry_after', 0)))
                if code in {'credentials', 'access'}:
                    pause = max(pause, 900)
                shared = code in {'credentials', 'access', 'rate_limit', 'upstream'}
                record.update(error=PROBLEMS[code], problem=code, http_status=status,
                              failures=failures, retry_at=now + pause)
                LOG.warning('HISTORY Week %s failed: %s HTTP=%s. %s Retry in %ss; saved rows=%s.',
                            period['id'], code, status or 'none', PROBLEMS[code], pause, len(record['rows']))
            finally:
                self.active_id = None
            cache[period['id']] = record
            if shared:
                # Explain the shared wait for all weeks instead of leaving the
                # untouched three on an endless "loading" message.
                for pending in periods:
                    if pending['id'] == period['id']: continue
                    psite, _, pprizes, pscope = self.context(pending, admin)
                    old = cache.get(pending['id'], {})
                    if old.get('scope') != pscope: old = {}
                    queued = {**pending, 'scope':pscope, 'updated_at':0, 'attempt_at':0,
                              'count':0, 'rows':[], 'prizes':pprizes, 'warning':'', **old}
                    if not queued['updated_at']: queued.update(self.saved_result(pending, admin, psite))
                    queued.update(error=PROBLEMS[code], problem=code, http_status=status,
                                  retry_at=max(queued.get('retry_at', 0), now + pause))
                    cache[pending['id']] = queued
            self.store.publish('weekly_history', clean_history(dict(version=1, weeks=list(cache.values()))), revision)
            if shared:
                return pause
        return 60

    def loop(self):
        try:
            while not self.stop_event.is_set():
                self.wake_event.clear()
                try:
                    delay = self.check()
                except Exception as exc:
                    LOG.warning('HISTORY Check interrupted (%s); retrying in 60s.', type(exc).__name__)
                    delay = 60
                self.wake_event.wait(delay)
                if self.stop_event.is_set():
                    break
        finally:
            self.providers.close()

    def start(self):
        with self.lock:
            if self.stop_event.is_set() or (self.thread and self.thread.is_alive()):
                return
            self.thread = threading.Thread(target=self.loop, daemon=True, name='weekly-history')
            self.thread.start()

    def stop(self):
        self.stop_event.set()
        self.wake_event.set()
        if self.thread:
            self.thread.join(timeout=1)
```

## `templates/admin.html`

```html
{% extends 'base.html' %}
{% from 'macros.html' import form_fields,action_feedback,field,player_rows with context %}
{% set area = 'leaderboards' if tab in ['shuffle','empiredrop','race','players'] else 'gaming' if tab=='gaming' else 'settings' if tab in ['settings','activity'] else 'overview' %}
{% set section_title = {'overview':'Overview','leaderboards':'Leaderboards','gaming':'Games & RedPoints','settings':'Settings'}[area] %}
{% block title %}{{ tabs[tab] }} · RedHunllef Control Center{% endblock %}
{% block attributes %}data-page="admin" data-admin-tab="{{ tab }}" data-admin-area="{{ area }}" data-feed="/admin/status" data-release="{{ release }}" data-bootstrap="{{ {'server_time':data.server_time,'site':data.site}|tojson|forceescape }}"{% endblock %}
{% block styles %}{% if tab=='gaming' %}<link rel="stylesheet" href="{{ url_for('static',filename='gaming.css',v=asset_version) }}">{% endif %}{% endblock %}
{% block final_styles %}<link rel="stylesheet" href="{{ url_for('static',filename='admin-workspace.css',v=asset_version) }}">{% endblock %}
{% block scripts %}
<script src="{{ url_for('static',filename='admin-health.js',v=asset_version) }}" defer></script>
<script src="{{ url_for('static',filename='admin-logs.js',v=asset_version) }}" defer></script>
<script src="{{ url_for('static',filename='admin-providers.js',v=asset_version) }}" defer></script>
{% if tab=='empiredrop' %}<script src="{{ url_for('static',filename='admin-empiredrop.js',v=asset_version) }}" defer></script>{% endif %}
{% if tab=='gaming' %}<script src="{{ url_for('static',filename='admin-gaming.js',v=asset_version) }}" defer></script>{% endif %}
<script src="{{ url_for('static',filename='admin-feedback.js',v=asset_version) }}" defer></script>
<script src="{{ url_for('static',filename='admin-calendar.js',v=asset_version) }}" defer></script>
<script src="{{ url_for('static',filename='admin-workspace.js',v=asset_version) }}" defer></script>
{% endblock %}
{% block content %}
<div class="admin-app" id="adminApp">
  <div class="admin-veil" id="adminVeil" hidden></div>
  <aside class="admin-sidebar" id="adminSidebar" aria-label="Admin navigation">
    <div class="admin-sidebar-head">
      <a class="admin-brand" href="{{ admin_link('overview') }}"><img src="{{ url_for('static',filename='redlogo.png') }}" alt="" width="36" height="36"><span><strong>RedHunllef</strong><small>Control center</small></span></a>
      <button type="button" class="admin-mobile-close" id="adminCloseMenu" aria-label="Close navigation">×</button>
    </div>
    <p class="admin-sidebar-caption">WORKSPACE</p>
    <nav class="admin-primary-nav" aria-label="Primary admin sections">
      <a href="{{ admin_link('overview') }}" {% if area=='overview' %}aria-current="page"{% endif %}><span class="admin-nav-icon" aria-hidden="true">◫</span>Overview</a>
      <a href="{{ admin_link('shuffle') }}" {% if area=='leaderboards' %}aria-current="page"{% endif %}><span class="admin-nav-icon" aria-hidden="true">♛</span>Leaderboards</a>
      <a href="{{ admin_link('gaming') }}" {% if area=='gaming' %}aria-current="page"{% endif %}><span class="admin-nav-icon" aria-hidden="true">◆</span>Games &amp; RedPoints</a>
      <a href="{{ admin_link('settings') }}" {% if area=='settings' %}aria-current="page"{% endif %}><span class="admin-nav-icon" aria-hidden="true">⚙</span>Settings</a>
    </nav>
    <div class="admin-side-status" aria-label="Provider status">
      <p class="admin-sidebar-caption">SOURCES</p>
      {% for key in ['shuffle','empiredrop'] %}{% set source = data.providers[key] %}
      <a href="{{ admin_link(key) }}" class="admin-side-provider"><span class="admin-status-dot" data-provider-indicator="{{ key }}" data-state="{{ source.state }}"></span><span>{{ source.name }}</span><small>{{ source.status }}</small></a>
      {% endfor %}
      <a class="admin-sidebar-log" href="{{ admin_link('activity') }}">◷ &nbsp; Activity &amp; logs</a>
    </div>
    <div class="admin-side-bottom">
      <div class="admin-user-mini"><span class="admin-user-avatar" aria-hidden="true">{{ user[:1]|upper }}</span><div><strong>{{ user }}</strong><small>{{ 'Superadmin' if superadmin else 'Administrator' }}</small></div></div>
      <a class="admin-external" href="/" target="_blank" rel="noopener noreferrer">View public website ↗</a>
      <form action="/admin/logout" method="post"><input type="hidden" name="csrf" value="{{ csrf() }}"><button class="admin-logout" type="submit">Sign out</button></form>
    </div>
  </aside>
  <div class="admin-content">
    <header class="admin-topbar">
      <div class="admin-top-left"><button id="adminOpenMenu" type="button" class="admin-menu-button" aria-label="Open admin navigation" aria-controls="adminSidebar" aria-expanded="false">☰</button><span class="admin-crumb">Control center <span aria-hidden="true">/</span> <strong>{{ section_title }}</strong></span></div>
      <div class="admin-top-actions"><button class="admin-command-button" type="button" id="adminCommandOpen" aria-haspopup="dialog" aria-controls="adminCommandDialog"><span>⌕ &nbsp; Jump to…</span><kbd>Ctrl K</kbd></button><a class="admin-top-activity" href="{{ admin_link('activity') }}">◷ <span>Activity</span></a><a class="admin-top-public" href="/" target="_blank" rel="noopener noreferrer">Website ↗</a></div>
    </header>
    <main id="main" class="admin-workspace shell" data-area="{{ area }}" data-focus="{{ section_focus|default('') }}">
      <div class="admin-page-heading"><div><p class="admin-page-kicker">CONTROL CENTER</p><h1>{{ section_title }}</h1><p class="admin-page-description">{{ {'overview':'The information that needs your attention now.','leaderboards':'Standings, schedules, prizes and source health.','gaming':'Player wallets, game results and RedPoints controls.','settings':'Accounts, integrations, backups and security.'}[area] }}</p></div><div class="admin-heading-actions"><span class="admin-saved-chip" id="adminSaveStatus" data-validation="{{ 'true' if errors or confirm_race or restore or recovery_review else 'false' }}" role="status">{{ 'Review required — not saved' if errors or confirm_race else 'Server confirmed' }}</span></div></div>
      {% if area=='leaderboards' %}
      <nav class="admin-workspace-nav" aria-label="Leaderboard provider"><a href="{{ admin_link('shuffle') }}" class="admin-provider-tab" {% if tab in ['shuffle','race','players'] %}aria-current="page"{% endif %}>Shuffle <span>Top 15</span></a><a href="{{ admin_link('empiredrop') }}" class="admin-provider-tab" {% if tab=='empiredrop' %}aria-current="page"{% endif %}>EmpireDrop <span>Top 10</span></a></nav>
      {% if tab in ['shuffle','race','players'] %}<nav class="admin-subnav" aria-label="Shuffle management"><a href="{{ admin_link('shuffle') }}" {% if tab=='shuffle' and section_focus!='shuffleSource' %}aria-current="page"{% endif %}>Standings</a><a href="{{ admin_link('race') }}" {% if tab=='race' and section_focus!='prizes' %}aria-current="page"{% endif %}>Schedule</a><a href="/admin/leaderboards/shuffle/prizes" {% if section_focus=='prizes' %}aria-current="page"{% endif %}>Prizes</a><a href="{{ admin_link('players') }}" {% if tab=='players' %}aria-current="page"{% endif %}>Players</a><a href="/admin/leaderboards/shuffle/source" {% if section_focus=='shuffleSource' %}aria-current="page"{% endif %}>Source Health</a></nav>
      {% else %}<nav class="admin-subnav" aria-label="EmpireDrop management"><a href="{{ admin_link('empiredrop') }}" {% if not section_focus %}aria-current="page"{% endif %}>Standings</a><a href="/admin/leaderboards/empiredrop/schedule" {% if section_focus=='empireDatesTitle' %}aria-current="page"{% endif %}>Schedule</a><a href="/admin/leaderboards/empiredrop/payouts" {% if section_focus=='empireRewards' %}aria-current="page"{% endif %}>Prizes</a><a href="/admin/leaderboards/empiredrop/source" {% if section_focus=='empireRaceDetails' %}aria-current="page"{% endif %}>Source Health</a></nav>{% endif %}
      {% elif area=='settings' %}<nav class="admin-workspace-nav" aria-label="Settings management"><a class="admin-provider-tab" href="{{ admin_link('settings') }}" {% if tab=='settings' %}aria-current="page"{% endif %}>Configuration</a><a class="admin-provider-tab" href="{{ admin_link('activity') }}" {% if tab=='activity' %}aria-current="page"{% endif %}>Activity &amp; Logs</a></nav>{% endif %}
      {% with messages=get_flashed_messages() %}{% for message in messages %}<p class="notice success" role="status">{{ message }}</p>{% endfor %}{% endwith %}
      {% if admin_receipt %}<p id="feedback-{{ admin_receipt.target }}" class="notice success" role="status"><strong>Saved.</strong> {{ admin_receipt.message }}</p>{% endif %}
      {% if errors %}<div class="notice warning" role="alert"><strong>Nothing was changed.</strong><ul>{% for key,message in errors.items() %}<li>{{ message }}</li>{% endfor %}</ul></div>{% endif %}
      {% if hosted_local and tab=='settings' %}<p class="notice warning">This deployment is using local JSON. Newer changes can be lost when App Platform replaces the container. {% if superadmin %}<a href="#recovery">Download a recovery checkpoint</a>.{% endif %}</p>{% endif %}
      {% if area=='overview' or tab=='activity' %}{% include 'admin_attention.html' %}{% endif %}
      {% if tab in ['overview','race','players'] %}<p id="leaderboardMessage" class="notice" role="status" {% if not data.leaderboard_message %}hidden{% endif %}>{{ data.leaderboard_message }}</p>{% endif %}
      {% if tab in ['overview','race','players'] %}<div id="endedNotice" class="notice ended-notice" {% if data.site.race_state!='ended' %}hidden{% endif %}><div><strong>Saved Shuffle race ended</strong><span>New wagers outside this race window are not included.</span></div><a class="button small" href="{{ admin_link('race') }}">Set next race →</a></div>{% endif %}
      {% include 'admin_' ~ tab ~ '.html' %}
      {% if tab=='overview' %}<details class="admin-detail-diagnostics panel" id="diagnostics"><summary><strong>System diagnostics</strong><span>Service health and request metrics</span></summary><div class="admin-details-pad">{% include 'admin_health.html' %}<a class="button small" href="{{ admin_link('activity') }}">Open full activity log</a></div></details>{% endif %}
      <footer class="admin-bottom"><span id="browserCheck" role="status">Checking release compatibility…</span><span>Release {{ release }}</span></footer>
    </main>
  </div>
  <dialog id="adminCommandDialog" class="admin-command-dialog" aria-labelledby="adminCommandTitle"><div class="admin-command-title"><strong id="adminCommandTitle">Jump to a workspace</strong><button type="button" id="adminCommandClose" aria-label="Close quick navigation">×</button></div><label class="admin-command-label" for="adminCommandSearch">Search admin actions</label><input id="adminCommandSearch" type="search" autocomplete="off" placeholder="Try EmpireDrop, prizes, wallets, backup…"><nav class="admin-command-results" aria-label="Quick navigation results">
  {% set commands = [('Overview',admin_link('overview'),'Service health and recent activity'),('Shuffle standings',admin_link('shuffle'),'Verified wagers'),('Shuffle schedule',admin_link('race'),'Eastern calendar'),('Shuffle prizes','/admin/leaderboards/shuffle/prizes','15-place rewards'),('Shuffle players',admin_link('players'),'Search and adjustments'),('EmpireDrop standings',admin_link('empiredrop'),'Official Top 10'),('EmpireDrop schedule','/admin/leaderboards/empiredrop/schedule','Provider and display calendars'),('EmpireDrop payouts','/admin/leaderboards/empiredrop/payouts','Draft and published prizes'),('Games and RedPoints',admin_link('gaming'),'Wallets, results and grants'),('Settings',admin_link('settings'),'Accounts, integrations and recovery'),('Activity and logs',admin_link('activity'),'Inspect and export diagnostics')] %}
  {% for label,link,description in commands %}<a href="{{ link }}" data-command-link data-search="{{ (label ~ ' ' ~ description)|lower }}"><strong>{{ label }}</strong><small>{{ description }}</small></a>{% endfor %}
</nav><p id="adminCommandEmpty" hidden>No matching actions.</p><small>Esc closes · Ctrl+K opens</small></dialog>
</div>
{% endblock %}
{% block site_footer %}{% endblock %}
```

## `templates/admin_activity.html`

```html
{# The central view is purpose-built for nontechnical admins. No provider calls. #}
<section class="panel form-panel admin-activity-page">
  <div class="section-title"><div><p class="eyebrow">ADMINISTRATION · OPERATIONS</p><h2>Activity &amp; diagnostics</h2><p class="muted">See when sources last worked, what changed, and what needs attention.</p></div>
  <a class="button small" href="/admin/diagnostics">Download source report</a></div>
  <div id="adminOperationsHost" class="admin-operations-host"></div>
  <h3 class="admin-activity-subtitle">System health &amp; performance</h3>
  {% include 'admin_health.html' %}
  <p class="small muted">Reports are server-generated and contain only operational status and counters. Provider payloads, credentials and player names are excluded.</p>
</section>
```

## `templates/admin_attention.html`

```html
{# One actionable summary; detailed errors stay inside Diagnostics. #}
{% set issues = data.health.components|rejectattr('state','equalto','good')|list %}
<section class="admin-attention" id="adminAttention" data-state="{{ 'warning' if issues else 'good' }}" aria-label="Service status">
  <div class="attention-heading"><strong id="attentionSummary">{{ 'Needs attention' if issues else 'Everything is connected' }}</strong><a class="text-link small" href="/admin/activity">View activity &amp; diagnostics →</a></div>
  <ul id="adminIssueList" role="status" aria-live="polite" aria-atomic="true" {% if not issues %}hidden{% endif %}>{% for item in issues %}<li>{{ item.label }}: {{ 'Saving unavailable. Check storage before making changes.' if item.key in ['storage','games'] else 'Updates delayed. Saved results remain visible; retrying automatically.' }}</li>{% endfor %}</ul>
  <p id="networkError" class="notice warning" role="status" hidden></p>
</section>
```

## `templates/admin_empiredrop.html`

```html
{# Shared presentation layer, independent provider behavior. #}
{% set provider = data.providers.empiredrop %}
<section class="panel form-panel provider-panel empire-section empire-source-overview" aria-labelledby="empireAdminTitle">
  {% include 'admin_provider_summary.html' %}
  <div class="provider-actions">
    <form method="post" action="/admin/empiredrop/refresh"><input type="hidden" name="csrf" value="{{ csrf() }}"><button class="button primary" type="submit">Request EmpireDrop refresh</button></form>
    {% if superadmin %}<button type="button" id="testEmpireConnection" class="button" data-csrf="{{ csrf() }}">Test API connection</button>{% endif %}
    <a class="button" href="#empireRaceDetails">Race API &amp; selection</a>
    <a class="button" href="#empireRewards">Schedule &amp; prizes</a>
    <a class="button" href="{{ admin_link('activity') }}">Activity &amp; logs</a>
  </div>
  <p class="small muted">EmpireDrop automatically respects the race's cache duration. Refresh requests do not bypass the provider's cache or rate limits.</p>
  <p id="empireError" class="notice warning" role="status" {% if not empire_admin.error %}hidden{% endif %}>{{ empire_admin.error }}</p>
  {{ action_feedback('empireRefresh') }}
  <p id="empireTestResult" class="small muted" role="status" aria-live="polite"></p>
</section>
<section class="panel form-panel provider-panel empire-section empire-standings" aria-labelledby="empirePlayersHeading">
  <div class="section-title"><div><p class="eyebrow">EMPIREDROP · PROVIDER RANKS</p><h2 id="empirePlayersHeading">Current Top 10</h2><p class="muted">Names are already anonymized by EmpireDrop. Public IDs help identify the same player between updates.</p></div><span class="tag">{{ empire_admin.private_rewards.total if empire_admin.private_rewards.enabled else 'Prizes not announced' }}</span></div>
  <div class="field"><label for="empireAdminSearch">Find a player or public ID</label><input id="empireAdminSearch" data-provider-search="empireAdminRows" type="search" placeholder="Filter the returned rankings" autocomplete="off"><small>Search covers only positions returned by the provider.</small></div>
  <div class="table-scroll" tabindex="0" role="region" aria-label="EmpireDrop ranked players">
    <table><thead><tr><th>Rank</th><th>Player (provider masked)</th><th>Public player ID</th><th class="number">{{ empire_admin.race_meta.get('metric') or 'Race total' }}</th><th class="number">Advertised prize</th></tr></thead>
    <tbody id="empireAdminRows">{% for row in empire_admin.rows[:10] %}<tr><td class="rank">{{ row.rank }}</td><td><strong>{{ row.username }}</strong></td><td class="small">{{ row.user_id or '—' }}</td><td class="number">{{ row.wager }}</td><td class="number">{{ row.prize }}</td></tr>{% else %}<tr><td colspan="5" class="empty">No ranked players returned. This can be normal before a race starts or after it closes.</td></tr>{% endfor %}</tbody></table>
  </div>
  <p class="small muted">Official ranks (including ties) are preserved. Deposit races and raffles are labeled correctly; we never present their totals as wagered currency.</p>
</section>
<section class="panel form-panel empire-section empire-schedule" id="empireSchedule" aria-labelledby="empireDatesTitle">
  <div class="section-title"><div><p class="eyebrow">EMPIREDROP SCHEDULE</p><h2 id="empireDatesTitle">Schedule</h2><p class="muted">EmpireDrop’s selected race controls the official standings window. The website display window can be aligned below.</p></div><span class="badge">Eastern Time</span></div>
  <div class="official-schedule-card" data-official-start="{{ empire_admin.race_meta.get('start_time',0) }}" data-official-end="{{ empire_admin.race_meta.get('end_time',0) }}">
    <div><span class="eyebrow">OFFICIAL PROVIDER RACE</span><strong>{{ empire_admin.race_meta.get('name') or empire_admin.race_meta.get('slug') or 'No race selected' }}</strong><small>{{ fmt_et(empire_admin.race_meta.get('start_time')) if empire_admin.race_meta.get('start_time') else 'Start not returned' }} → {{ fmt_et(empire_admin.race_meta.get('end_time')) if empire_admin.race_meta.get('end_time') else 'End not returned' }}</small></div>
    {% if empire_admin.race_meta.get('slug') %}<span class="tag">{{ empire_admin.race_meta.get('slug') }}</span>{% endif %}
  </div>
  {% if superadmin %}{{ action_feedback('empireSchedule') }}
  <form method="post" action="/admin/empiredrop/schedule" class="stack admin-sticky-form" data-dirty data-calendar-form="empiredrop">
    <input type="hidden" name="csrf" value="{{ csrf() }}"><input type="hidden" name="revision" value="{{ revision }}"><input type="hidden" name="mode" value="custom"><input type="hidden" id="empireStart" name="start_et" value="{{ empire_admin.schedule.start_input }}"><input type="hidden" id="empireEnd" name="end_et" value="{{ empire_admin.schedule.end_input }}">
    <div class="section-title compact"><div><h3>Website display window</h3><p class="small muted">This controls the countdown and local administration only. It does not change the race inside EmpireDrop.</p></div><button class="button small js-only" id="syncEmpireSchedule" type="button">Sync provider dates</button></div>
    <div class="calendar-grid"><div class="calendar-field"><span class="calendar-label">Start</span><label for="empireStartDate">Date</label><input id="empireStartDate" data-calendar-date="start" type="date" value="{{ empire_admin.schedule.start_input[:10] }}" required><label for="empireStartTime">Time</label><input id="empireStartTime" data-calendar-time="start" type="time" value="{{ empire_admin.schedule.start_input[11:16] }}" step="300" required></div><div class="calendar-arrow" aria-hidden="true">→</div><div class="calendar-field"><span class="calendar-label">End</span><label for="empireEndDate">Date</label><input id="empireEndDate" data-calendar-date="end" type="date" value="{{ empire_admin.schedule.end_input[:10] }}" required><label for="empireEndTime">Time</label><input id="empireEndTime" data-calendar-time="end" type="time" value="{{ empire_admin.schedule.end_input[11:16] }}" step="300" required></div></div>
    <div class="calendar-preview"><span>Eastern Time</span><strong data-calendar-preview>Choose a valid start and end.</strong><small data-calendar-utc></small></div><p id="empireScheduleMismatch" class="notice warning" hidden>The website display window does not match the official EmpireDrop race. Sync the dates before publishing public schedule text.</p>
    <div class="admin-save-bar"><div><strong>Website schedule draft</strong><small>Official provider dates remain authoritative for rankings.</small></div><button class="button primary" type="submit">Save display schedule</button></div>
  </form>{% else %}<p class="small muted">Only the Superadmin may change the website display dates.</p>{% endif %}
</section>
<section class="panel form-panel empire-section empire-rewards" id="empireRewards" aria-labelledby="empireRewardsTitle">
  {% set rewards = empire_admin.private_rewards %}
  <div class="section-title"><div><p class="eyebrow">EMPIREDROP · TOP 10</p><h2 id="empireRewardsTitle">Prize schedule</h2><p class="muted">Save a private draft, review the pool, then publish it to the public leaderboard.</p></div><span class="tag" data-state="{{ 'healthy' if rewards.published and rewards.published_enabled else 'warning' }}">{{ 'Published' if rewards.published and rewards.published_enabled else 'Draft' if not rewards.published else 'Not announced' }}</span></div>
  <div class="admin-payout-summary"><div><span class="small muted">Draft pool</span><strong id="empireRewardTotal">{{ rewards.total }}</strong></div><div><span class="small muted">Public pool</span><strong>{{ rewards.published_total if rewards.published_enabled else 'Not announced' }}</strong></div><div><span class="small muted">Last saved</span><strong>{{ fmt_et(rewards.updated_at) if rewards.updated_at else 'Never' }}</strong>{% if rewards.updated_by %}<small>by {{ rewards.updated_by }}</small>{% endif %}</div></div>
  <p class="small muted">These are locally advertised prizes. They do not change or confirm payments on EmpireDrop. Tied players split the prize assigned to their provider rank.</p>
  {% if superadmin %}
  {{ action_feedback('empireRewards') }}
  <form method="post" action="/admin/empiredrop/rewards" class="stack admin-sticky-form" data-dirty>
    <input type="hidden" name="csrf" value="{{ csrf() }}"><input type="hidden" name="reward_revision" value="{{ rewards.revision }}"><input type="hidden" name="submission_id" value="{{ empire_reward_submission_id }}"><input type="hidden" name="save_mode_intent" value="">
    <div class="field compact-field"><label for="empireRewardsCurrency">Prize currency</label><select id="empireRewardsCurrency" name="currency"><option value="EUR" {% if rewards.currency=='EUR' %}selected{% endif %}>EUR (€)</option><option value="USD" {% if rewards.currency=='USD' %}selected{% endif %}>USD ($)</option></select></div>
    <div class="prize-grid">{% for n in range(1,11) %}<div class="field"><label for="empirePrize{{ n }}">Place {{ n }}</label><input id="empirePrize{{ n }}" name="prize_{{ n }}" type="number" inputmode="decimal" min="0" max="1000000" step="0.01" required value="{{ rewards.prizes[n|string] }}"></div>{% endfor %}</div>
    <div class="admin-save-bar"><div><strong id="empireRewardSaveState">No unsaved changes</strong><small>Publishing replaces the public Top 10 prize schedule after the server verifies the write.</small></div><button type="submit" name="save_mode" value="draft" class="button" data-payout-submit>Save draft</button><button type="submit" name="save_mode" value="publish" class="button primary" data-payout-submit>Save &amp; publish</button></div>
  </form>
  {% else %}<p class="small muted">Only the Superadmin can change payout amounts.</p>{% endif %}
</section>
<section class="panel form-panel empire-section empire-source" id="empireBackup" aria-labelledby="empireBackupTitle">
  <p class="eyebrow">SAFE RECOVERY · EMPIREDROP ONLY</p><h2 id="empireBackupTitle">Settings backup</h2>
  <p class="small muted">Export or restore the EmpireDrop race slug, schedule and local prizes. This file contains no API keys or player accounts. To back up saved standings and all accounts, download a full private recovery export under Settings.</p>
  {% if superadmin %}
  {{ action_feedback('empireBackup') }}
  <a class="button" href="/admin/empiredrop/settings-backup">Download EmpireDrop settings</a>
  <form method="post" action="/admin/empiredrop/settings-restore" enctype="multipart/form-data" class="stack" data-dirty>
    <input type="hidden" name="csrf" value="{{ csrf() }}"><input type="hidden" name="revision" value="{{ revision }}">
    <div class="field"><label for="empireRestoreFile">Restore settings from JSON</label><input id="empireRestoreFile" type="file" accept=".json,application/json" name="settings_file" required></div>
    <div class="field"><label><input type="checkbox" name="confirm" value="yes" required> Replace my current EmpireDrop schedule and payout settings</label></div>
    <button class="button" type="submit">Restore EmpireDrop settings</button>
  </form>
  {% else %}<p class="small muted">Only the Superadmin can export or restore these settings.</p>{% endif %}
</section>
<section class="panel form-panel" aria-labelledby="empireKeysTitle">
  <p class="eyebrow">SERVER CONFIGURATION</p><h2 id="empireKeysTitle">Public and private API keys</h2>
  <p class="small muted">Keys are read from the server's private settings file or environment. They are not printed in HTML, public feeds, network status or browser JavaScript.</p>
  <div class="form-grid">
    {% for key,label in [('empiredrop_public_key','Public API key'),('empiredrop_private_key','Private API key')] %}
    <div class="field"><label>{{ label }}</label><p class="small"><strong>{{ empire_admin.configured[key].masked if empire_admin.configured[key].configured else 'Not configured' }}</strong> · {{ empire_admin.configured[key].source }}</p></div>
    {% endfor %}
  </div>
  {% if superadmin %}
  {{ action_feedback('empireKeys') }}
  <form method="post" action="/admin/empiredrop/keys" class="stack" data-dirty autocomplete="off">
    <input type="hidden" name="csrf" value="{{ csrf() }}">
    <div class="form-grid"><div class="field"><label for="empirePublicKey">Replace public key (optional)</label><input id="empirePublicKey" name="empiredrop_public_key" type="password" autocomplete="new-password" placeholder="Leave blank to retain saved key"></div><div class="field"><label for="empirePrivateKey">Replace private key (optional)</label><input id="empirePrivateKey" name="empiredrop_private_key" type="password" autocomplete="new-password" placeholder="Leave blank to retain saved key"></div></div>
    <button class="button" type="submit">Save new server-side credentials</button>
  </form>
  {% else %}<p class="small muted">Credential replacement is Superadmin-only.</p>{% endif %}
</section>
{# Races API: these are two specific documented GET paths, distinct from the legacy wager adapter. #}
<section class="panel form-panel empire-section empire-source" id="empireRaceDetails" aria-labelledby="empireRacesTitle">
  <p class="eyebrow">OFFICIAL DEVELOPER ROUTES · EMPIREDROP</p>
  <h2 id="empireRacesTitle">Race API &amp; selection</h2>
  <p class="small muted">OpenAPI v2.0.1: <code>GET https://api.empiredrop.com/api/v1/affiliate-partner/races</code> lists currently running races; <code>GET /api/v1/affiliate-partner/races/{slug}</code> returns ranking[]. Both use mandatory X-Public-Key and X-Private-Key headers. The old /race/affiliates/{publicKey} endpoint is deprecated.</p>
  <div class="health-grid" aria-label="EmpireDrop race API health">
    <article class="health-card"><span class="eyebrow">DATA SOURCE</span><strong id="empireRaceMode">{{ empire_admin.source_mode|upper }}</strong></article>
    <article class="health-card"><span class="eyebrow">ACTIVE SLUG</span><strong id="empireRaceSlug">{{ (empire_admin.race_meta or {}).get('slug') or 'Not discovered' }}</strong></article>
    <article class="health-card"><span class="eyebrow">DATA WINDOW</span><strong id="empireRaceWindow">{{ 'Provider race' if empire_admin.race_configuration.race_window_policy=='provider' else 'Local schedule' }}</strong></article>
  </div>
  {% if superadmin %}
  {{ action_feedback('empireRaces') }}
  <div class="button-row">
    <button type="button" class="button" id="empireDiscover" data-csrf="{{ csrf() }}">Discover affiliate races</button>
    <button type="button" class="button" id="empireProbe" data-csrf="{{ csrf() }}">Inspect selected race fields</button>
  </div>
  <pre id="empireRaceDiagnostics" class="small muted" style="white-space:pre-wrap;overflow-wrap:anywhere;max-height:340px;overflow:auto" role="status" aria-live="polite">Not tested in this session. Run discovery to see available race slugs.</pre>
  <p id="empireSlugRecovery" class="notice warning" hidden></p>
  <div id="empireDiscoveredSlugs" class="button-row" aria-label="Verified race choices"></div>
  <form method="post" action="/admin/empiredrop/races/config" class="stack" data-dirty>
    <input type="hidden" name="csrf" value="{{ csrf() }}"><input type="hidden" name="revision" value="{{ revision }}">
    {% set rc = empire_admin.race_configuration %}
    <input type="hidden" name="source_mode" value="races">
    <input type="hidden" name="race_window_policy" value="provider">
    <div class="form-grid">
      <div class="field"><label for="empireSourceModeReadonly">Leaderboard source</label><input id="empireSourceModeReadonly" value="Official EmpireDrop partner race API" readonly aria-readonly="true"><small>Uses the documented race slug endpoint and both production API-key headers.</small></div>
      <div class="field"><label for="empireRaceSlugInput">Race slug (optional)</label><input id="empireRaceSlugInput" name="race_slug" maxlength="100" value="{{ rc.race_slug }}" placeholder="Blank = choose the best active wager race"><small>Enter the exact slug to lock the board to one race. Leave blank to match the active WAGER/RANKING race to the saved week.</small></div>
      <div class="field"><label for="empireRacePolicyReadonly">Race reporting period</label><input id="empireRacePolicyReadonly" value="EmpireDrop start_date / end_date" readonly aria-readonly="true"><small>The provider's official race dates control the returned standings.</small></div>
      <div class="field"><label><input type="checkbox" name="auto_select" value="yes" {% if rc.auto_select %}checked{% endif %}> Automatically select the active wager race</label></div>
    </div>
    <p class="small muted">The deprecated timestamp endpoint is no longer selected by ordinary schedule edits. The website displays up to 10 official positions and respects EmpireDrop's race.ranks_limit.</p>
    <button type="submit" class="button primary">Save race API connection</button>
  </form>
  {% else %}<p class="small muted">Race API diagnostics are available to the Superadmin only.</p>{% endif %}
  <h3>Recent verified EmpireDrop races</h3>
  <p class="small muted">The last four completed snapshots are retained in local JSON. The current live race is displayed above. Back up JSON state before deploying; App Platform storage is ephemeral.</p>
  <div class="table-scroll" tabindex="0" role="region" aria-label="Completed EmpireDrop races">
    <table><thead><tr><th>Race slug</th><th>Last confirmed update</th></tr></thead><tbody>
    {% for item in empire_admin.race_history %}{% set history_meta = item.get('race_meta') or {} %}<tr><td>{{ history_meta.get('slug') or 'Legacy race' }}</td><td>{{ fmt_et(item.get('updated_at',0)) if item.get('updated_at',0) else 'Not recorded' }}</td></tr>
    {% else %}<tr><td colspan="2">No completed EmpireDrop snapshots saved yet.</td></tr>{% endfor %}
    </tbody></table>
  </div>
  <p class="small muted">References: <a href="https://developers.empiredrop.com/#tag/Races/paths/~1api~1v1~1race~1affiliates~1%7BpublicKey%7D/get" target="_blank" rel="noopener noreferrer">Deprecated custom-date standings</a> · <a href="https://developers.empiredrop.com/#tag/Races/paths/~1api~1v1~1affiliate-partner~1races~1%7Bslug%7D/get" target="_blank" rel="noopener noreferrer">Race details</a>.</p>
</section>
<section class="panel form-panel" aria-labelledby="empireContractTitle" {% if empire_admin.race_configuration.source_mode != 'legacy' %}hidden{% endif %}>
  <p class="eyebrow">LEGACY ADAPTER · ADVANCED ONLY</p><h2 id="empireContractTitle">Verified API contract</h2>
  <p class="notice warning">This is an older generic adapter that is not used for official races. Prefer the documented partner-races API above. Use these settings only when you have a separately verified provider contract. Developer portal: <a href="https://developers.empiredrop.com/" target="_blank" rel="noopener noreferrer">developers.empiredrop.com</a>.</p>
  {% if superadmin %}
  {{ action_feedback('empireConfig') }}
  <form method="post" action="/admin/empiredrop/config" class="stack" data-dirty>
    <input type="hidden" name="csrf" value="{{ csrf() }}"><input type="hidden" name="revision" value="{{ revision }}">
    <div class="form-grid">
      {% for key,label in [('api_url','Official provider HTTPS endpoint'),('public_header','Public key HTTP header'),('private_header','Private key HTTP header'),('start_param','Start-date query field'),('end_param','End-date query field'),('code_param','Referral code query field (if applicable)'),('name_field','Username field'),('user_id_field','Stable player ID field (if available)'),('wager_field','Wager amount field'),('code_field','Referral code result field'),('wager_divisor','Units divisor'),('transaction_id_field','Unique transaction ID field (transaction mode)'),('cursor_param','Cursor request field'),('next_cursor_field','Next-cursor response field'),('rows_path','JSON array location (e.g. data.players)'),('next_cursor_path','Next-cursor JSON location (e.g. paging.next)')] %}
      <div class="field"><label for="empire-{{ key }}">{{ label }}</label><input id="empire-{{ key }}" name="{{ key }}" value="{{ empire_admin.configuration[key] }}" maxlength="350" {% if key not in ['api_url','code_param','user_id_field','transaction_id_field','rows_path','next_cursor_path'] %}required{% endif %}></div>
      {% endfor %}
      <div class="field"><label for="empireAuthMode">Authentication mode (verify with provider)</label><select id="empireAuthMode" name="auth_mode">{% for value,label in [('dual_headers','Both keys in separate headers'),('private_header','Private key in named header'),('public_header','Public key in named header'),('bearer_private','Bearer private key'),('basic_pair','HTTP Basic public/private pair')] %}<option value="{{ value }}" {% if empire_admin.configuration.auth_mode==value %}selected{% endif %}>{{ label }}</option>{% endfor %}</select></div>
      <div class="field"><label for="empireHttpMethod">Provider API request method</label><select id="empireHttpMethod" name="http_method">{% for v in ['GET','POST'] %}<option value="{{ v }}" {% if empire_admin.configuration.http_method==v %}selected{% endif %}>{{ v }}</option>{% endfor %}</select></div>
      <div class="field"><label for="empireRequestLocation">Parameter placement</label><select id="empireRequestLocation" name="request_location">{% for v in ['query','json'] %}<option value="{{ v }}" {% if empire_admin.configuration.request_location==v %}selected{% endif %}>{{ v }}</option>{% endfor %}</select></div>
      <div class="field"><label for="empireTimestampFormat">Date/time encoding</label><select id="empireTimestampFormat" name="timestamp_format">{% for v,label in [('unix_s','Unix seconds'),('unix_ms','Unix milliseconds'),('iso8601_utc','ISO 8601 UTC')] %}<option value="{{ v }}" {% if empire_admin.configuration.timestamp_format==v %}selected{% endif %}>{{ label }}</option>{% endfor %}</select></div>
      <div class="field"><label for="empireCurrency">Currency</label><select id="empireCurrency" name="currency">{% for value in ['EUR','USD'] %}<option value="{{ value }}" {% if empire_admin.configuration.currency==value %}selected{% endif %}>{{ value }}</option>{% endfor %}</select></div>
      <div class="field"><label for="empireRecordMode">API response mode</label><select id="empireRecordMode" name="record_mode"><option value="player_total" {% if empire_admin.configuration.record_mode=='player_total' %}selected{% endif %}>Already aggregated player totals (deduplicate)</option><option value="transactions" {% if empire_admin.configuration.record_mode=='transactions' %}selected{% endif %}>Individual transactions (sum unique IDs)</option></select></div>
      <div class="field"><label for="empirePages">Pagination mode</label><select id="empirePages" name="pagination_mode"><option value="none" {% if empire_admin.configuration.pagination_mode=='none' %}selected{% endif %}>One complete page</option><option value="cursor" {% if empire_admin.configuration.pagination_mode=='cursor' %}selected{% endif %}>Provider cursor pagination</option></select></div>
      <div class="field"><label><input type="checkbox" name="code_scoped" value="yes" {% if empire_admin.configuration.code_scoped %}checked{% endif %}> Provider guarantees this endpoint is exclusively referral code red</label></div>
      <div class="field"><label><input type="checkbox" name="verified_contract" value="yes" {% if empire_admin.configuration.verified_contract %}checked{% endif %}> I verified URL, auth headers, timestamps, wager fields, units, pagination and referral scoping with EmpireDrop</label></div>
    </div>
    <button class="button primary" type="submit">Save verified connection configuration</button>
  </form>
  {% else %}<p>Only the Superadmin can update the provider API contract.</p>{% endif %}
</section>
```

## `templates/admin_gaming.html`

```html
<section aria-labelledby="gamingAdminHeading" id="gamingAdmin" data-rankings="{{ data.gaming|tojson|forceescape }}">
  <div class="section-title"><div><p class="eyebrow">THIS RACE WEEK · ADMIN ONLY</p><h2 id="gamingAdminHeading">Gaming · top five per game</h2><p class="muted small">Net winnings = returned − wagered. Free points and admin grants do not count.</p></div><a class="button small" href="{{ '/admin/gaming' if tab=='overview' else '/gaming' }}">{{ 'Gaming controls →' if tab=='overview' else 'Open Gaming →' }}</a></div>
  <div class="ranking-toolbar"><p id="gamingAdminSummary" class="small">Players: {{ data.gaming.player_count }} · Rounds: {{ data.gaming.completed_rounds }} · Active hands: {{ data.gaming.active_hands }} · Publicly active: {{ data.gaming.public_activity.active_count }}</p><div><button id="refreshGaming" class="text-button small" type="button">Refresh stats</button><span id="gamingAdminChecked" class="small muted">Updating automatically</span></div></div>
  <div class="panel gaming-admin-live"><div><p class="eyebrow">PUBLIC GAMING FEED</p><h3>Live community activity</h3><p class="small muted">The public page shows only opted-in names, current game, recent activity, weekly net and round count.</p></div><dl><div><dt>Active now</dt><dd id="gamingPublicActive">{{ data.gaming.public_activity.active_count }}</dd></div><div><dt>Visible leaders</dt><dd id="gamingPublicLeadersCount">{{ data.gaming.public_activity.weekly_leaders|length }}</dd></div><div><dt>Feed revision</dt><dd id="gamingPublicRevision">{{ data.gaming.public_activity.revision }}</dd></div></dl></div>
  <p id="gamingNoRecords" class="notice" {% if data.gaming.completed_rounds %}hidden{% endif %}>No completed rounds this week. Players appear after finishing a RedPoints game.</p>
  <p id="gamingAdminSession" class="notice warning" role="alert" hidden>Your admin session has expired. Private rankings are hidden. <a class="text-link" href="/admin/gaming">Sign in again →</a></p>
  <div class="gaming-admin-cards">{% for game,rows in data.gaming.games.items() %}<section class="panel"><div class="ranking-card-heading"><h3>{{ 'Texas Hold’em' if game=='poker' else game|capitalize }}</h3><span class="tag">Top 5</span></div><p id="gamingCount-{{ game }}" class="small muted">Players: {{ data.gaming.counts[game].players }} · Completed rounds: {{ data.gaming.counts[game].rounds }}</p><ol id="gamingLeaders-{{ game }}" class="gaming-leaders">{% for row in rows %}<li data-player-key="{{ game }}:{{ row.player_tag }}" data-tone="{{ 'positive' if row.net>0 else 'negative' if row.net<0 else 'neutral' }}"><details class="player-breakdown"><summary><span class="leader-name"><small>{{ loop.index }}</small><strong>{{ row.name }}</strong></span><b>{{ '{:+,}'.format(row.net) }} <small>RP</small></b></summary><div class="player-record"><small>{{ '{:,}'.format(row.paid) }} returned · {{ '{:,}'.format(row.wagered) }} wagered · {{ row.bets }} rounds</small><small>{{ '{:,}'.format(row.balance) }} available RP · player {{ row.player_tag }}</small><small>IPs: {{ row.ips|join(', ') or 'Not linked this week yet' }}</small><small>Funding adjustments: {{ '{:+,}'.format(row.funding_adjustment) }} RP · excluded from winnings</small><small>Public Gaming name: {{ 'Visible' if row.public_visibility else 'Hidden' }}{% if row.last_game %} · last game {{ 'Hold’em' if row.last_game=='poker' else row.last_game|capitalize }}{% endif %}{% if row.last_action_at %} · {{ fmt_et(row.last_action_at) }}{% endif %}</small></div></details></li>{% else %}<li class="muted">No completed rounds this week.</li>{% endfor %}</ol></section>{% endfor %}</div>
  <details class="panel gaming-tools" id="gamingFunding"><summary><span><strong>Community RedPoints</strong><small>Give every registered player +100,000</small></span><span aria-hidden="true">+</span></summary><div class="details-content"><p class="small muted">Adds to available balances. Saved winnings, names and unfinished hands are kept.</p><form id="grantGamingForm" method="post" action="/admin/gaming/grant"><input type="hidden" name="csrf" value="{{ csrf() }}"><input type="hidden" name="request_id" value="{{ gaming_grant_id }}"><button id="grantGamingButton" class="button primary" type="submit">Give everyone +100,000 RedPoints</button><p id="gamingGrantMessage" class="small" role="status" aria-live="polite"></p></form><p id="gamingLastGrant" class="small muted">{% if data.gaming.last_grant %}Last grant: {{ data.gaming.last_grant.actor }} · +100,000 each · {{ data.gaming.last_grant.players }} wallets · {{ fmt_et(data.gaming.last_grant.at) }}{% else %}No admin points grant has been saved yet.{% endif %}</p></div></details>
  <details class="panel gaming-tools"><summary><span><strong>Player records &amp; reset schedule</strong><small>Identity, funding and connection information</small></span><span aria-hidden="true">+</span></summary><div class="details-content"><p id="gamingAdminReset" class="small muted">Weekly reset: {{ data.gaming.season.end_et }}.</p><p class="small muted">All eight games share each player's name and wallet. Shared Wi-Fi and VPN connections are allowed. Names are player-submitted; IPs do not verify a Shuffle account or restrict play. Full names and IPs are admin-only.</p><p class="small muted">A browser refresh sets that player's available balance to 100,000; a restart sets all saved wallets to 100,000. Funding is excluded from winnings. Pending card hands keep their committed stake. Weekly reset clears rankings.</p><p id="gamingIpWarning" class="notice warning" hidden>Visitor IP forwarding is not configured. Playing still works. On DigitalOcean App Platform set TRUST_APP_PLATFORM=1 to record each visitor's public IP accurately.</p><p class="small muted">Installed gaming release: <strong id="gamingInstalledRelease">{{ release }}</strong></p></div></details>
  <details class="panel gaming-tools" id="gamingLegacyPoker"><summary>Video Poker · legacy records</summary><div class="details-content"><p class="small muted">Previous Jacks or Better results keep their original rules and proofs.</p><p id="gamingCount-video_poker" class="small muted"></p><ol class="gaming-leaders" id="gamingLeaders-video_poker">{% for row in data.gaming.legacy_poker %}<li><strong>{{ row.name }}</strong> · {{ '{:+,}'.format(row.net) }} net RP</li>{% else %}<li class="muted">No legacy rounds this week.</li>{% endfor %}</ol></div></details>
</section>
```

## `templates/admin_health.html`

```html
<section class="panel health-panel" id="systemHealth" data-health="{{ data.health|tojson|forceescape }}" aria-labelledby="systemHealthHeading">
  <div class="section-title"><div><p class="eyebrow">SYSTEM HEALTH</p><h2 id="systemHealthHeading">System health</h2></div><button class="button small" id="copyHealthReport" type="button">Copy support report</button></div>
  <div class="health-grid">{% for item in data.health.components %}<article class="health-card" data-health-card="{{ item.key }}" data-state="{{ item.state }}">
    <span class="eyebrow">{{ item.label }}</span><strong data-health-status>{{ item.status }}</strong>
    <p data-health-detail>{{ item.detail }}</p><small class="muted" data-health-time>{{ 'Checked ' ~ fmt_et(item.last_success) if item.last_success else 'Waiting for first confirmation' }}</small>
    {% if item.action %}<a class="text-link small" href="{{ item.action }}">{{ 'Recovery & storage' if item.key=='storage' else 'View games' if item.key=='games' else 'Connection details' }} →</a>{% endif %}
  </article>{% endfor %}</div>
  <details class="health-measurements"><summary>Recent measurements</summary><div class="health-metrics" id="healthMetrics"></div><p class="small muted">Recent measurements on this server. Request reports contain no player names, IPs, keys or saved game seeds.</p></details>
  <details class="operations-panel" id="adminOperations" {% if tab=='activity' %}open{% endif %}>
    <summary><strong>Operational activity</strong> <span class="small muted">Search, filter and export recent provider events</span></summary>
    <p class="small muted">Recorded events contain only service, time, severity, HTTP status, duration and counts. Logs are held in memory and reset after restart. They are not a permanent audit trail.</p>
    <div class="ops-summary-grid" aria-label="Recent event totals">
      <div><span>All events</span><strong id="opsTotalEvents">0</strong></div>
      <div><span>Successful</span><strong id="opsTotalSuccess">0</strong></div>
      <div><span>Informational</span><strong id="opsTotalInfo">0</strong></div>
      <div><span>Warnings</span><strong id="opsTotalWarning">0</strong></div>
      <div><span>Errors</span><strong id="opsTotalError">0</strong></div>
    </div>
    <div class="ops-filters">
      <div class="field"><label for="opsSource">Service</label><select id="opsSource"><option value="all">All services</option><option value="shuffle">Shuffle</option><option value="empiredrop">EmpireDrop</option><option value="kick">Kick</option><option value="admin">Admin</option><option value="system">System</option><option value="storage">Storage</option></select></div>
      <div class="field"><label for="opsLevel">Severity</label><select id="opsLevel"><option value="all">All levels</option><option value="success">Success</option><option value="info">Information</option><option value="warning">Warnings</option><option value="error">Errors</option></select></div>
      <div class="field"><label for="opsSearch">Search visible events</label><input type="search" id="opsSearch" placeholder="Source, HTTP code or event type" autocomplete="off"></div>
    </div>
    <div class="button-row ops-buttons"><button type="button" class="button small" id="opsReload">Refresh activity</button><a id="opsExport" class="button small" href="/admin/operations/export">Export JSON</a><a id="opsExportTxt" class="button small" href="/admin/operations/export?format=txt">Export TXT</a></div>
    <p id="opsMessage" class="small muted" role="status" aria-live="polite">Open this section to load recent activity.</p>
    <div id="opsEvents" class="operations-events" role="list" aria-label="Recent operational events"></div>
  </details>
  <p id="healthReportFeedback" class="small" role="status" hidden></p>
</section>
```

## `templates/admin_overview.html`

```html
<section class="stat-grid overview-stats" aria-label="Operational overview">
  <article class="panel stat"><div class="row"><span class="eyebrow">SHUFFLE RACE</span><span id="raceBadge" class="badge state-{{ data.site.race_state }}">{{ data.site.race_state|capitalize }}</span></div><strong id="countdown" class="stat-value">{{ data.site.race_state|capitalize }}</strong><p id="raceWindow" class="muted">{{ data.site.start_et }} → {{ data.site.end_et }}</p><a class="text-link" href="{{ admin_link('race') }}">Manage schedule &amp; prizes →</a></article>
  <article class="panel stat"><span class="eyebrow">SHUFFLE STANDINGS</span><strong class="stat-value"><span id="playerCount">{{ data.count }}</span> <small>players</small></strong><p>Prize pool <strong class="accent" id="poolTotal">{{ data.site.total_prize }}</strong> · 15 places</p><small id="sourceTime" class="muted">Last verified {{ fmt_et(data.freshness.updated_at) if data.freshness.updated_at else 'not yet' }}</small><a class="text-link" href="{{ admin_link('players') }}">View participants →</a></article>
  <article class="panel stat"><span class="eyebrow">REDPOINTS</span><strong class="stat-value">{{ data.gaming.player_count|default(0) }} <small>wallets</small></strong><p>Gaming profiles and fairness receipts are independent of the wager races.</p><a class="text-link" href="{{ admin_link('gaming') }}">Manage games &amp; RedPoints →</a></article>
</section>
<div class="admin-overview-actions" aria-label="Common actions"><a class="button primary" href="{{ admin_link('race') }}">Manage Shuffle race</a><a class="button" href="{{ admin_link('empiredrop') }}">Manage EmpireDrop</a>{% if superadmin %}<a class="button" href="/admin/recovery-backup">Download recovery</a>{% endif %}</div>
{% if superadmin %}<aside class="recovery-reminder panel" id="recoveryReminder" {% if not data.checkpoint.changes %}hidden{% endif %}><div><strong>Recovery checkpoint recommended</strong><p id="recoveryReminderDetail">{{ data.checkpoint.details }}</p></div><a class="button small" href="{{ admin_link('settings','recovery') }}">Open recovery →</a></aside>{% endif %}
<section class="panel form-panel" aria-label="Leaderboard sources"><div class="section-title"><div><p class="eyebrow">PROVIDER HEALTH</p><h2>Leaderboards</h2><p class="muted">Each provider keeps its own schedule, standings and prize publication state.</p></div><a class="button small" href="{{ admin_link('activity') }}">Activity &amp; logs</a></div><div class="provider-overview-grid">{% for key in ['shuffle','empiredrop'] %}{% set provider=data.providers[key] %}<a class="provider-overview-tile" href="{{ admin_link(key) }}"><span>{{ provider.name }}</span><span class="provider-state" data-state="{{ provider.state }}">{{ provider.status }}</span><strong>{{ provider.participants }} ranked</strong><small>Last verified: {{ fmt_et(provider.last_success) if provider.last_success else 'Not verified yet' }}</small><small>{{ provider.quality }}</small><small>{% if provider.trend.sample %}Recent checks: {{ provider.trend.successes }} successful · {{ provider.trend.failures }} failed{% else %}Recent checks: waiting{% endif %}</small></a>{% endfor %}</div></section>
<section class="panel form-panel" aria-label="Daily operations"><div class="section-title"><div><p class="eyebrow">DAILY WORK</p><h2>Common tasks</h2><p class="muted">Direct destinations only—no intermediate redirect pages.</p></div></div><div class="admin-settings-shortcuts"><a href="{{ admin_link('shuffle') }}"><strong>Review Shuffle</strong><span>Standings and source status</span></a><a href="{{ admin_link('empiredrop') }}"><strong>Review EmpireDrop</strong><span>Top 10, schedule and payouts</span></a><a href="{{ admin_link('gaming') }}"><strong>Manage RedPoints</strong><span>Wallets, grants and game results</span></a><a href="{{ admin_link('settings') }}"><strong>Open Settings</strong><span>Accounts, integrations and recovery</span></a></div></section>
```

## `templates/admin_players.html`

```html
<section class="panel form-panel"><div class="section-title"><div><p class="eyebrow">YOUR COMMUNITY, UNCENSORED</p><h2>Race participants</h2></div><a id="exportLink" class="button small" href="{{ url_for('export',view=request.args.get('view','all'),q=request.args.get('q',''),sort=request.args.get('sort','rank')) }}">↓ Export this view</a></div>
<form class="filter-bar" method="get" action="{{ url_for('admin_shuffle_players_page') }}"><div class="field grow"><label for="search">Find a player</label><input id="search" name="q" value="{{ request.args.get('q','') }}" placeholder="Search full username"></div><div class="field"><label for="view">Show</label><select id="view" name="view">{% for key,label in [('all','All loaded players'),('top','Top 15'),('overrides','Adjusted players')] %}<option value="{{ key }}" {% if request.args.get('view','all')==key %}selected{% endif %}>{{ label }}</option>{% endfor %}</select></div><div class="field"><label for="sort">Sort by</label><select id="sort" name="sort">{% for key,label in [('rank','Race rank'),('name','Username'),('raw','Raw wager')] %}<option value="{{ key }}" {% if request.args.get('sort','rank')==key %}selected{% endif %}>{{ label }}</option>{% endfor %}</select></div><button class="button" type="submit">Apply</button></form>
<p class="muted small">Up to {{ limit }} qualifying players are loaded. Search and export cover those loaded records. Original race ranks are retained.</p><div class="table-scroll" tabindex="0" role="region" aria-label="Full race participants"><table><thead><tr><th>Rank</th><th>Player</th><th class="number">Effective weighted</th><th class="number">Original weighted</th><th class="number">Raw wager</th><th>Action</th></tr></thead><tbody id="participantsBody">{{ player_rows(participants) }}</tbody></table></div></section>
<section class="panel form-panel" id="override">{{ action_feedback('override') }}<div class="section-title"><div><p class="eyebrow">A CLEAR AUDIT TRAIL</p><h2>Adjust a weighted total</h2></div></div><form action="/admin/action" method="post" class="filter-bar" data-dirty>{{ form_fields('override','players',revision) }}{{ field('username','Exact full username',request.args.get('edit','')) }}{{ field('amount','Replacement weighted total',admin.overrides.get(request.args.get('edit',''),''),help='Leave blank to remove the override.',required=false) }}<button class="button primary" type="submit">Save adjustment</button></form><p class="muted small">Raw and original weighted amounts remain available. An override changes the effective ranking amount.</p></section>
<details class="panel form-panel code-red" id="codeRed" {% if request.args.get('code_red')=='1' %}open{% endif %}><summary><div><span class="eyebrow">CODE RED</span><h2>Community wagerers <span class="tag" id="redCount">{{ data.red|length }} / 100</span></h2></div><span class="expand-icon" aria-hidden="true">+</span></summary><div class="details-content"><p class="muted">The first 100 confirmed Code Red wagerers, sorted by weighted wager. Full usernames are visible only to administrators. Overrides do not change this source list.</p><p id="redMembership" class="muted small">{{ data.diagnostics.missing_campaign }} source rows have no campaign metadata; membership cannot be verified for those rows.</p><div class="field js-only"><label for="redSearch">Search these Code Red users</label><input id="redSearch" type="search" placeholder="Full username"></div><div class="table-scroll" tabindex="0" role="region" aria-label="Code Red wagerers"><table><thead><tr><th>#</th><th>Full username</th><th class="number">Weighted wager</th><th class="number">Raw wager</th></tr></thead><tbody id="redBody">{% for row in data.red %}<tr data-red-name="{{ row.username }}"><td>{{ loop.index }}</td><td><strong>{{ row.username }}</strong><button class="copy-button js-only" type="button" data-copy="{{ row.username }}">⧉</button></td><td class="number accent">{{ row.weighted }}</td><td class="number">{{ row.raw }}</td></tr>{% else %}<tr><td colspan="4" class="empty">No confirmed Code Red wagerers for this window.</td></tr>{% endfor %}</tbody></table></div></div></details>
```

## `templates/admin_provider_summary.html`

```html
{# Provider shared UI: same labels and structure, independent data and actions. #}
<section class="provider-summary" id="{{ provider.key }}Provider" aria-label="{{ provider.name }} source health">
  <div class="provider-summary-heading">
    <div><p class="eyebrow">SOURCE HEALTH · {{ provider.name|upper }}</p>
      <h2 id="{{ 'empireAdminTitle' if provider.key == 'empiredrop' else 'shuffleAdminTitle' }}">{{ provider.name }} leaderboard</h2>
      <p class="muted small">{{ provider.scope }}</p>
    </div>
    <span class="provider-state" data-provider-state="{{ provider.key }}" data-state="{{ provider.state }}" {% if provider.key=='empiredrop' %}id="empireAdminStatus"{% endif %} role="status">{{ provider.status }}</span>
  </div>
  <div class="provider-metrics">
    <article><span>Last verified</span><strong data-provider-field="{{ provider.key }}:last_success" {% if provider.key=='empiredrop' %}id="empireAdminConfirmed"{% endif %}>{{ fmt_et(provider.last_success) if provider.last_success else 'Not verified yet' }}</strong></article>
    <article><span>Last attempted</span><strong data-provider-field="{{ provider.key }}:last_attempt" {% if provider.key=='empiredrop' %}id="empireAdminAttempted"{% endif %}>{{ fmt_et(provider.last_attempt) if provider.last_attempt else 'Not attempted' }}</strong></article>
    <article><span>Ranked players</span><strong data-provider-field="{{ provider.key }}:participants">{{ provider.participants }}</strong></article>
    <article><span>Recent reliability</span><strong>{% if provider.trend.sample %}{{ provider.trend.successes }}/{{ provider.trend.sample }} successful · {{ provider.trend.success_rate }}%{% else %}Waiting for checks{% endif %}</strong></article>
  </div>
  {% if provider.key=='empiredrop' %}<p class="small muted">Worker: <strong id="empireAdminChecking">{{ 'Checking provider' if empire_admin.checking else 'Waiting for next check' }}</strong></p>{% endif %}
  <div class="provider-quality">
    <div><span class="eyebrow">DATA VALIDATION</span><strong data-provider-field="{{ provider.key }}:quality">{{ provider.quality }}</strong></div>
    <div><span class="eyebrow">METRIC</span><strong data-provider-field="{{ provider.key }}:metric">{{ provider.metric }}</strong></div>
  </div>
  {% if provider.key=='shuffle' and provider.request_meta %}<details class="provider-request-fingerprint"><summary>Last sanitized request</summary><dl><div><dt>Method</dt><dd>{{ provider.request_meta.method }}</dd></div><div><dt>Endpoint</dt><dd>{{ provider.request_meta.endpoint_kind }}</dd></div><div><dt>Start</dt><dd>{{ provider.request_meta.start }}</dd></div><div><dt>End</dt><dd>{{ provider.request_meta.end }}</dd></div><div><dt>Timestamp unit</dt><dd>{{ provider.request_meta.timestamp_unit }}</dd></div></dl></details>{% endif %}
  <div class="provider-issues" data-provider-issues="{{ provider.key }}" {% if not provider.issues %}hidden{% endif %}>
    <strong>Things to check</strong>
    <ul>{% for issue in provider.issues %}<li>{{ issue }}</li>{% endfor %}</ul>
  </div>
</section>
```

## `templates/admin_race.html`

```html
<form id="raceForm" method="post" action="/admin/action" class="stack admin-sticky-form" data-dirty data-calendar-form="shuffle">{{ form_fields('save_race','race',revision) }}{{ action_feedback('raceForm') }}
{% if confirm_race %}<input type="hidden" name="review_token" value="{{ review_token }}"><div class="notice warning"><strong>These changes are a draft. Confirm below to publish them.</strong><p>Changing the race window archives its results and resets its overrides. Changes to prizes or text keep the current race participants. Review the changes below.</p><p>The saved race stays active until you choose <strong>Confirm and publish race</strong> in the bottom save bar.</p></div>{% endif %}
{% if change_review %}{% include "change_review.html" %}{% endif %}
<section class="panel form-panel shuffle-schedule-section" id="shuffleSchedule"><div class="section-title"><div><p class="eyebrow">RACE SCHEDULE</p><h2>Schedule</h2><p class="muted">Choose exact Eastern dates and times. The preview shows the range that will be published.</p></div><div class="calendar-presets js-only"><button class="button small" type="button" id="currentWeek" data-calendar-preset="current">Use current week</button><button class="button small" type="button" id="nextRace" data-calendar-preset="next">Next week</button><button class="button small" type="button" id="startNow" data-calendar-preset="today">Start today</button></div></div>
<input type="hidden" id="start_et" name="start_et" value="{{ form.start_et }}"><input type="hidden" id="end_et" name="end_et" value="{{ form.end_et }}">
<div class="calendar-grid"><div class="calendar-field"><span class="calendar-label">Start</span><label for="shuffleStartDate">Date</label><input id="shuffleStartDate" data-calendar-date="start" type="date" value="{{ form.start_et[:10] }}" required><label for="shuffleStartTime">Time</label><input id="shuffleStartTime" data-calendar-time="start" type="time" value="{{ form.start_et[11:16] }}" step="300" required>{% if errors.get('start_et') %}<small class="field-error">{{ errors.get('start_et') }}</small>{% endif %}</div><div class="calendar-arrow" aria-hidden="true">→</div><div class="calendar-field"><span class="calendar-label">End</span><label for="shuffleEndDate">Date</label><input id="shuffleEndDate" data-calendar-date="end" type="date" value="{{ form.end_et[:10] }}" required><label for="shuffleEndTime">Time</label><input id="shuffleEndTime" data-calendar-time="end" type="time" value="{{ form.end_et[11:16] }}" step="300" required>{% if errors.get('end_et') %}<small class="field-error">{{ errors.get('end_et') }}</small>{% endif %}</div></div><div class="calendar-preview"><span>Eastern Time</span><strong data-calendar-preview>Choose a valid start and end.</strong><small data-calendar-utc></small></div><p class="muted small">Daylight saving is calculated using America/New_York. A changed race window is reviewed before it replaces the live schedule.</p>
<div class="form-grid">{{ field('site_name','Website name',form.site_name) }}{{ field('race_title','Race title',form.race_title) }}</div>{{ field('race_description','Short description',form.race_description,'textarea',required=false) }}</section>
<section class="panel form-panel shuffle-prize-section" id="prizes"><div class="section-title"><div><p class="eyebrow">REWARD THE CLIMB</p><h2>Placement prizes</h2></div><span class="badge" id="prizeTotal">{{ data.site.total_prize }} total</span></div><div class="prize-grid">{% for n in range(1,16) %}{{ field('prize_'~n,'Place '~n,form['prize_'~n],error=errors.get('prize_'~n,'')) }}{% endfor %}</div></section>
<details class="panel form-panel shuffle-advanced-section" id="siteConfiguration"><summary><h2>Website links &amp; advanced race options</h2><span aria-hidden="true">+</span></summary><div class="details-content"><div class="form-grid">{% for key,label,type,required in [('kick_channel_slug','Kick channel name','text',true),('campaign_code_filter','Shuffle campaign code','text',false),('stream_url','Livestream link','url',true),('sponsor_name','Sponsor name','text',true),('sponsor_url','Sponsor link','url',true),('community_name','Community link label','text',false),('community_url','Community link','url',false),('responsible_gambling_url','Responsible play link','url',false)] %}{{ field(key,label,form[key],type,error=errors.get(key,''),required=required) }}{% endfor %}</div></div></details>
<div class="save-bar"><div><strong id="saveLabel">{{ 'Confirmation required — not published' if confirm_race else 'Review your draft' if errors else 'All changes saved' }}</strong><span class="muted small">Live updates preserve your unfinished edits.</span></div><div class="button-row"><button class="button js-only" type="reset">Discard edits</button><button class="button primary" type="submit" {% if confirm_race %}name="confirm_race" value="yes"{% endif %}>{{ 'Confirm and publish race' if confirm_race else 'Save race settings' }}</button></div></div></form>
```

## `templates/admin_settings.html`

```html
{# Four plain-language shortcuts; all existing privileged actions remain server protected. #}
<nav class="admin-settings-compactnav" aria-label="Settings categories">
  <a href="#accountSecurity">My account</a>
  {% if superadmin %}<a href="#adminAccounts">Administrators</a>{% endif %}
  <a href="#backups">Backup &amp; recovery</a>
  <a href="#configurationDetails">Integrations</a>
  <a href="#accessControls">Security</a>
</nav>
<aside class="panel admin-state-card" aria-label="Saved state status">
  <div><span class="eyebrow">SAVED WEBSITE STATE</span><strong>{{ data.durability.mode }}</strong>
    <span>Settings revision {{ data.durability.revision }} · {{ 'Remote state is authoritative' if data.durability.remote else 'Container-local changes can be lost on redeploy' }}</span></div>
  <a class="button small" href="/admin/recovery-backup">Download private recovery</a>
</aside>
<section class="panel form-panel" id="accountSecurity"><p class="eyebrow">YOUR ACCESS</p><h2>Account security</h2>{{ action_feedback('accountSecurity') }}<form method="post" action="/admin/action" class="form-grid" data-dirty>{{ form_fields('password','settings',revision) }}{{ field('current_password','Current password',type='password') }}{{ field('new_password','New password',type='password',help='At least 12 characters.') }}{{ field('confirm_password','Confirm new password',type='password') }}<div class="field"><span>&nbsp;</span><button class="button primary" type="submit">Update password</button></div></form></section>
{% if superadmin %}<details class="panel form-panel" id="adminAccounts"><summary><h2>Administrator accounts</h2><span aria-hidden="true">+</span></summary><div class="details-content"><p class="muted">{{ admin.superadmin }} is the protected Superadmin. Existing accounts are retained while their saved storage is available. Use the private recovery file below before redeploying with local storage.</p>{{ action_feedback('accounts') }}<div class="account-list">{% for name,record in admin.users.items() %}<div class="account-row"><div><strong>{{ name }}</strong><span class="tag">{{ 'Superadmin' if name|lower==admin.superadmin|lower else 'Admin' }}</span></div>{% if name|lower!=admin.superadmin|lower %}<form action="/admin/action" method="post" data-confirm="Remove this account and revoke its sessions?">{{ form_fields('remove_account','settings',revision) }}<input type="hidden" name="username" value="{{ name }}"><button class="button small danger" type="submit">Remove</button></form>{% endif %}</div>{% endfor %}</div><h3>Add an administrator</h3><form action="/admin/action" method="post" class="form-grid">{{ form_fields('add_account','settings',revision) }}{{ field('username','New username',prefix='add-') }}{{ field('new_password','Initial password',type='password',help='At least 12 characters.',prefix='add-') }}{{ field('confirm_password','Confirm password',type='password',prefix='add-') }}<div class="field"><span>&nbsp;</span><button class="button" type="submit">Add administrator</button></div></form>
<details class="nested"><summary>Reset an administrator password</summary><form action="/admin/action" method="post" class="form-grid" data-confirm="Reset this password and revoke previous sessions?">{{ form_fields('reset_password','settings',revision) }}<div class="field"><label for="resetUser">Account</label><select name="username" id="resetUser">{% for name in admin.users %}<option>{{ name }}</option>{% endfor %}</select></div>{{ field('new_password','Replacement password',type='password',prefix='reset-') }}{{ field('confirm_password','Confirm replacement',type='password',prefix='reset-') }}<div class="field"><span>&nbsp;</span><button class="button" type="submit">Reset password</button></div></form></details></div></details>{% endif %}
<details class="panel form-panel" id="backups" {% if restore %}open{% endif %}><summary><h2>Backups &amp; race history</h2><span aria-hidden="true">+</span></summary><div class="details-content"><p class="muted">Race backups include settings, results, overrides, and history. Passwords and integration credentials are excluded.</p>{{ action_feedback('backups') }}<a class="button" href="/admin/backup">↓ Download race backup</a><form class="filter-bar" method="post" action="/admin/action" enctype="multipart/form-data">{{ form_fields('preview_restore','settings',revision) }}<div class="field grow"><label for="backupFile">Restore a race backup</label><input id="backupFile" name="backup" type="file" accept=".json,application/json" required></div><button class="button" type="submit">Review backup</button></form>
{% if restore %}<div class="notice warning"><strong>Review this restore</strong><p>{{ restore.start }} → {{ restore.end }} · {{ restore.rows }} saved participants</p><p>{{ restore.overrides }} overrides · {{ restore.history }} archived races. Accounts and RedPoints wallets stay intact.</p>{% if restore.changes %}{% with change_review=restore.changes %}{% include "change_review.html" %}{% endwith %}{% endif %}<p>Current race data will be replaced. Accounts remain intact, and a private recovery copy is created first.</p><form method="post" action="/admin/action">{{ form_fields('restore','settings',revision) }}<input type="hidden" name="restore_token" value="{{ restore.token }}"><button class="button danger" type="submit">Confirm restore</button></form></div>{% endif %}
{% for race in admin.race_history|reverse %}<details class="nested"><summary>{{ fmt_et(race.site_settings.start_time) }} → {{ fmt_et(race.site_settings.end_time) }}</summary><div class="table-scroll"><table><thead><tr><th>Rank</th><th>Username</th><th class="number">Weighted wager</th></tr></thead><tbody>{% for row in race.leaderboard_snapshots.last_top15 %}<tr><td>{{ row.rank }}</td><td>{{ row.username }}</td><td class="number">{{ row.wager }}</td></tr>{% else %}<tr><td colspan="3">No saved participants.</td></tr>{% endfor %}</tbody></table></div></details>{% else %}<p class="muted small">Completed races appear here after you save a new window.</p>{% endfor %}</div></details>
{% if superadmin %}{% include 'recovery_panel.html' %}{% endif %}
<details class="panel form-panel" id="configurationDetails"><summary><h2>Connections &amp; diagnostics</h2><span aria-hidden="true">+</span></summary><div class="details-content"><div class="diagnostic-grid">{% for key,label in [('storage','Storage'),('start_et','Race starts'),('end_et','Race ends'),('received','Source records received'),('accepted','Valid race records'),('missing_campaign','Records without campaign')] %}<div><span class="muted small">{{ label }}</span><strong data-diagnostic="{{ key }}">{{ data.diagnostics[key] }}</strong></div>{% endfor %}{% for key,value in data.diagnostics.credentials.items() %}<div><span class="muted small">{{ key|replace('_',' ')|title }}</span><strong>{{ 'Configured' if value.configured else 'Missing' }}</strong><small class="muted">{{ value.source }}</small></div>{% endfor %}</div>
{% for name in ['shuffle','kick'] %}<div class="notice"><strong>{{ name|capitalize }}</strong><p id="{{ name }}Message">{{ data.jobs[name].error or 'Waiting for first update' }}</p><small id="{{ name }}Timing" class="muted">Automatic updates every 60 seconds</small></div>{% endfor %}<a class="button" href="/admin/diagnostics">↓ Download redacted diagnostics</a><p class="muted small">The report excludes keys, password hashes, provider response bodies, and participant usernames.</p></div></details>
<details class="panel form-panel" id="accessControls"><summary><h2>Access controls &amp; logs</h2><span aria-hidden="true">+</span></summary><div class="details-content"><form method="post" action="/admin/action" class="filter-bar" data-confirm="Block requests from this IP address?">{{ form_fields('ban_ip','settings',revision) }}{{ field('ip','Block an IPv4 or IPv6 address') }}<button class="button danger" type="submit">Block address</button></form><div class="button-row">{% for ip in admin.banned_ips %}<form action="/admin/action" method="post">{{ form_fields('unban_ip','settings',revision) }}<input type="hidden" name="ip" value="{{ ip }}"><button class="button small" type="submit">Unblock {{ ip }}</button></form>{% endfor %}</div>{{ action_feedback('accessControls') }}<h3>Recent access</h3><div class="table-scroll"><table><thead><tr><th>Time</th><th>Address</th><th>Path</th><th>Status</th></tr></thead><tbody>{% for row in access_log %}<tr><td>{{ fmt_et(row.time) }}</td><td>{{ row.ip }}</td><td>{{ row.method }} {{ row.path }}</td><td>{{ row.status }}</td></tr>{% endfor %}</tbody></table></div><form method="post" action="/admin/action" data-confirm="Clear recent access entries?">{{ form_fields('clear_access','settings',revision) }}<button class="button small" type="submit">Clear access log</button></form><h3>Administrator activity</h3><div class="table-scroll"><table><thead><tr><th>Time</th><th>Administrator</th><th>Action</th></tr></thead><tbody>{% for row in admin.audit_log|reverse %}<tr><td>{{ row.ts_et }}</td><td>{{ row.admin_user }}</td><td>{{ row.action }}</td></tr>{% endfor %}</tbody></table></div>{% if superadmin %}<form action="/admin/action" method="post" data-confirm="Clear the audit log after saving a private recovery copy?">{{ form_fields('clear_audit','settings',revision) }}<button class="button small" type="submit">Clear audit log</button></form>{% endif %}</div></details>
```

## `templates/admin_shuffle.html`

```html
{# The two provider tabs intentionally share admin_provider_summary.html. #}
{% set provider = data.providers.shuffle %}
<section class="panel form-panel provider-panel shuffle-summary-section" aria-labelledby="shuffleActionsHeading">
  {% include 'admin_provider_summary.html' %}
  <div class="provider-actions" id="shuffleActionsHeading">
    <form method="post" action="/admin/action" data-refresh>
      {{ form_fields('refresh','shuffle',revision) }}<input type="hidden" name="service" value="shuffle">
      <button class="button primary" type="submit">Request Shuffle refresh</button>
    </form>
    <a class="button" href="{{ admin_link('race') }}">Edit schedule &amp; prizes</a>
    <a class="button" href="{{ admin_link('players') }}">View all participants</a>
    <a class="button" href="{{ admin_link('activity') }}">Activity &amp; logs</a>
  </div>
  <p class="small muted">Shuffle refreshes independently every 60 seconds. A request queues a check; it doesn't confirm new data until the provider responds. For an expired race window or HTTP 400, use <a class="text-link" href="{{ admin_link('race') }}">Schedule &amp; prizes</a> to review the saved dates before requesting another check.</p>
  <p class="notice warning" {% if not data.freshness.warning and not data.jobs.shuffle.error %}hidden{% endif %} role="status">{{ data.freshness.warning or 'Shuffle updates are delayed; the previous verified board is preserved.' }}</p>
</section>
<section class="panel form-panel provider-panel shuffle-standings-section" aria-labelledby="shufflePlayersHeading">
  <div class="section-title"><div><p class="eyebrow">SHUFFLE · VERIFIED RANKINGS</p><h2 id="shufflePlayersHeading">Current Top 15</h2><p class="muted">Full usernames and raw totals are administrator-only. Public names remain masked.</p></div><span class="tag">{{ data.site.total_prize }} prize pool</span></div>
  <div class="field"><label for="shuffleTopSearch">Find a player</label><input type="search" id="shuffleTopSearch" data-provider-search="shuffleAdminRows" placeholder="Filter the visible Top 15" autocomplete="off"></div>
  <div class="table-scroll" tabindex="0" role="region" aria-label="Shuffle verified top fifteen"><table><thead><tr><th>Rank</th><th>Full username</th><th class="number">Weighted</th><th class="number">Raw</th><th class="number">Advertised prize</th></tr></thead><tbody id="shuffleAdminRows">
    {% for row in data.rows[:15] %}<tr><td class="rank">{{ row.rank }}</td><td><strong>{{ row.username }}</strong>{% if row.source=='override' %} <span class="tag">Adjusted</span>{% endif %}</td><td class="number">{{ row.wager }}</td><td class="number">{{ row.raw_wager_str }}</td><td class="number">{{ money(data.site.prizes.get(row.rank|string,0)) }}</td></tr>
    {% else %}<tr><td colspan="5" class="empty">No verified Shuffle results for this race window.</td></tr>{% endfor %}
  </tbody></table></div>
  <p class="small muted">Shuffle's rank calculation includes the configured weighting and administrator adjustments. Open <a class="text-link" href="{{ admin_link('players') }}">Players</a> for source totals, campaign membership and edits.</p>
</section>
<section class="panel form-panel provider-panel shuffle-source-section" id="shuffleSource" aria-labelledby="shuffleQualityHeading">
  <div class="section-title"><div><p class="eyebrow">DATA RECONCILIATION</p><h2 id="shuffleQualityHeading">Source record checks</h2></div><a class="text-link" href="/admin/diagnostics">Download diagnostic summary</a></div>
  <div class="provider-quality-grid">
    <div><span>Records returned</span><strong>{{ data.diagnostics.received }}</strong></div>
    <div><span>Records included</span><strong>{{ data.diagnostics.accepted }}</strong></div>
    <div><span>Campaign unverified</span><strong>{{ data.diagnostics.missing_campaign }}</strong></div>
    <div><span>Ranked players</span><strong>{{ data.count }}</strong></div>
  </div>
  <p class="small muted">The counts refer to source records, not necessarily distinct players. A missing campaign field does not prove referral membership; verify the scope of your Shuffle affiliate feed before using those records for payouts.</p>
  {% if data.diagnostics.rejected %}<details class="provider-advanced"><summary>Excluded source records</summary><ul>{% for reason,number in data.diagnostics.rejected.items() %}<li>{{ reason }}: {{ number }}</li>{% endfor %}</ul></details>{% endif %}
</section>
```

## `templates/base.html`

```html
<!doctype html>
<html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<meta name="theme-color" content="#160e14"><title>{% block title %}RedHunllef · Wager Race{% endblock %}</title>
<link rel="icon" href="{{ url_for('static', filename='redlogo.ico') }}">
<link rel="stylesheet" href="{{ url_for('static',filename='style.css',v=asset_version) }}">{% block styles %}{% endblock %}<link rel="stylesheet" href="{{ url_for('static',filename='experience.css',v=asset_version) }}"><link rel="stylesheet" href="{{ url_for('static',filename='public-control.css',v=asset_version) }}">{% block final_styles %}{% endblock %}<link rel="stylesheet" href="{{ url_for('static',filename='v11-system.css',v=asset_version) }}"><link rel="stylesheet" href="{{ url_for('static',filename='v14-modern.css',v=asset_version) }}"><link rel="stylesheet" href="{{ url_for('static',filename='v15-system.css',v=asset_version) }}"><link rel="stylesheet" href="{{ url_for('static',filename='v16-system.css',v=asset_version) }}"></head>
<body data-release="{{ release }}" {% block attributes %}{% endblock %}>
{# Login and error pages do not receive the public leaderboard data object. #}
{% set public_site = data.site if data is defined and data.site is defined else {} %}
<a class="skip-link" href="#main">Skip to content</a>
<header class="site-header public-site-header" id="publicSiteHeader">
  <div class="shell header-inner public-header-inner">
    <a class="brand public-brand" href="/" aria-label="RedHunllef homepage">
      <img src="{{ url_for('static',filename='redlogo.png') }}" alt="" width="38" height="38">
      <span><strong data-site-text="site_name">{{ public_site.site_name|default('RedHunllef') }}</strong><span class="brand-sub">WAGER RACES · REDPOINTS</span></span>
    </a>
    <button type="button" class="public-mobile-toggle" id="publicMenuToggle" aria-controls="publicPrimaryNav" aria-expanded="false" aria-label="Open site navigation"><span aria-hidden="true">☰</span><span>Menu</span></button>
    <nav class="public-navigation" id="publicPrimaryNav" aria-label="Main navigation">
      {% block navigation %}
      <div class="public-nav-links">
        <a class="section-nav" href="/#leaderboard" {% if request.endpoint=='index' %}aria-current="page"{% endif %}>Leaderboards</a>
        <a class="section-nav" href="/gaming" {% if request.endpoint in ['gaming_home','gaming_game','gaming_fairness'] %}aria-current="page"{% endif %}>RedPoints Games</a>
        <a class="section-nav" href="/history" {% if request.endpoint=='public_history' %}aria-current="page"{% endif %}>History</a>
      </div>
      <div class="public-nav-right">
        <details class="public-more" id="publicMore"><summary>Community <span aria-hidden="true">⌄</span></summary>
          <div class="public-more-panel">
            <a href="https://botrix.live/k/redhunllef/shop" target="_blank" rel="noopener noreferrer">Points Shop <span aria-hidden="true">↗</span></a>
            <a class="community-nav" data-site-text="community_name" data-site-link="community_url" href="{{ public_site.community_url|default('') }}" {% if not public_site.community_url|default('') %}hidden{% endif %} target="_blank" rel="noopener noreferrer">{{ public_site.community_name|default('Community') }}</a>
          </div>
        </details>
        <a class="button small public-watch" data-site-link="stream_url" href="{{ public_site.stream_url|default('') }}" {% if not public_site.stream_url|default('') %}hidden{% endif %} target="_blank" rel="noopener noreferrer">Watch on Kick <span aria-hidden="true">↗</span></a>
      </div>
      {% endblock %}
    </nav>
  </div>
</header>
{% block content %}{% endblock %}
{% block site_footer %}<footer class="shell footer"><span>RedHunllef <span class="muted">· Races and RedPoints.</span></span><span class="muted">{% block footer %}<a data-site-link="responsible_gambling_url" href="{{ public_site.responsible_gambling_url|default('') }}" {% if not public_site.responsible_gambling_url|default('') %}hidden{% endif %} target="_blank" rel="noopener">Play responsibly · 18+</a>{% endblock %}</span></footer>{% endblock %}
<div id="toast" class="toast" role="status" hidden></div>
<script src="{{ url_for('static',filename='app.js',v=asset_version) }}" defer></script>
<script src="{{ url_for('static',filename='experience.js',v=asset_version) }}" defer></script><script src="{{ url_for('static',filename='public-control.js',v=asset_version) }}" defer></script>{% block scripts %}{% endblock %}
</body></html>
```

## `templates/change_review.html`

```html
<section class="panel change-review" aria-labelledby="changeReviewTitle">
<p class="eyebrow">REVIEW BEFORE PUBLISHING</p><h2 id="changeReviewTitle">Here is exactly what changes.</h2>
<div class="table-scroll" tabindex="0" role="region" aria-label="Current and proposed values"><table><thead><tr><th>Setting</th><th>Current</th><th>Proposed</th></tr></thead><tbody>{% for change in change_review %}<tr><th scope="row">{{ change.label }}</th><td>{{ change.before }}</td><td class="accent">{{ change.after }}</td></tr>{% endfor %}</tbody></table></div>
<p class="small muted">Review expires after 15 minutes. Editing a reviewed value requires a fresh preview before publishing.</p>
</section>
```

## `templates/error.html`

```html
{% extends 'base.html' %}
{% block title %}{{ title }} · RedHunllef{% endblock %}
{% block content %}
<main class="shell login-wrap public-interior-page" id="main">
  <section class="panel login-panel" aria-labelledby="errorTitle">
    <p class="eyebrow">REDHUNLLEF / NAVIGATION</p>
    <h1 id="errorTitle">{{ title }}</h1>
    <p class="muted">{{ message }}</p>
    <p class="small muted">If you followed an old admin bookmark, open the Control Center and choose the section again.</p>
    <div class="button-row"><a class="button primary" href="/admin">Admin Control Center →</a><a class="button" href="/">Public homepage</a></div>
    <p class="release">{{ release }}</p>
  </section>
</main>
{% endblock %}
{% block footer %}RedHunllef Wager Race{% endblock %}
```

## `templates/gaming.html`

```html
{% extends 'base.html' %}
{% block title %}{{ ('Texas Hold’em' if game=='poker' else game|capitalize) ~ ' · ' if game else '' }}RedPoints Games · RedHunllef{% endblock %}
{% block styles %}<link rel="stylesheet" href="{{ url_for('static',filename='gaming.css',v=asset_version) }}">{% if game=='poker' %}<link rel="stylesheet" href="{{ url_for('static',filename='holdem.css',v=asset_version) }}">{% endif %}{% endblock %}
{% block content %}
<main id="main" class="shell gaming-page public-interior-page" data-game="{{ game or '' }}" data-wallet="{{ wallet|tojson|forceescape }}" data-rules="{{ game_rules|tojson|forceescape }}" data-csrf="{{ player_token }}" data-community="{{ community|tojson|forceescape }}">
  <header class="gaming-heading gaming-heading-v15">
    <div class="gaming-title-block">
      <p class="eyebrow">REDPOINTS ARCADE</p>
      <h1>{{ 'Texas Hold’em' if game=='poker' else game|capitalize if game else 'RedPoints Games' }}</h1>
      <p class="gaming-subtitle">{{ 'Play with RedPoints. No cash value.' if game else 'Play community games using RedPoints. No cash value.' }}</p>
    </div>
    <div class="gaming-account-card panel">
      <div class="gaming-balance-line"><span id="pointsLabel">{{ 'STARTING BALANCE' if wallet.needs_profile and not wallet.play_blocked else 'YOUR REDPOINTS' }}</span><strong id="pointsBalance">{% if wallet.needs_profile and wallet.play_blocked %}—{% elif wallet.needs_profile %}{{ '{:,}'.format([100000, wallet.balance]|max) }}{% else %}{{ '{:,}'.format(wallet.balance) }}{% endif %}</strong></div>
      <div class="wallet-detail"><span>In play <b id="pointsInPlay">0</b></span><span>Last net <b id="pointsNet">—</b></span></div>
      <div id="gamingIdentity" class="gaming-identity" {% if wallet.needs_profile %}hidden{% endif %}><span>Playing as <strong id="gamingPlayerName">{{ wallet.name }}</strong></span><button class="text-link small" id="editGamingName" type="button">Profile</button><button class="text-link small" id="openGamingRecoveryIdentity" type="button">Recovery</button><small id="gamingChecked" class="muted">Saved</small></div>
      <button id="openGamingProfile" class="button primary small" type="button" {% if not wallet.needs_profile %}hidden{% endif %}>Create Profile</button>
      <small id="pointsReset">{% if wallet.needs_profile and not wallet.play_blocked %}Create a profile to play.{% else %}Resets {{ wallet.season.end_et }}{% endif %}</small>
    </div>
  </header>

  {% if game %}
  <div class="game-toolbar panel">
    <a class="button small" href="/gaming">← All Games</a>
    <div class="game-switcher compact-game-switcher"><label for="gameSelect">Switch game</label><select id="gameSelect" aria-label="Switch game"><option value="/gaming">All Games</option>{% for item in game_rules.games %}<option value="/gaming/{{ item }}" {% if game==item %}selected{% endif %}>{{ 'Texas Hold’em' if item=='poker' else item|capitalize }}</option>{% endfor %}</select></div>
    <a class="text-link" href="/gaming/fairness">Fairness &amp; Rules ↗</a>
    <span id="roundState" class="round-state" role="status">Ready</span>
  </div>
  {% endif %}

  <p id="gamingNetworkNotice" class="notice warning" hidden><span id="gamingNetworkReason"></span></p>
  <p id="pokerResume" class="notice" hidden><strong>Your Hold’em hand is saved.</strong> <a class="button primary small" href="/gaming/poker">Resume hand →</a></p>
  <p id="blackjackResume" class="notice" hidden><strong>Your Blackjack hand is saved.</strong> <a class="button primary small" href="/gaming/blackjack">Resume hand →</a></p>
  <p id="gamingError" class="notice warning" role="alert" hidden></p><button id="retryBet" type="button" class="button" hidden>Recover pending result</button>

  <dialog id="gamingProfile" class="gaming-dialog" data-autostart="{{ 'true' if game and wallet.needs_profile else 'false' }}" aria-labelledby="gamingProfileTitle">
    <form method="dialog" class="gaming-dialog-close"><button type="submit" aria-label="Close profile">×</button></form>
    <div class="gaming-dialog-content"><p class="eyebrow">PLAYER PROFILE</p><h2 id="gamingProfileTitle">{{ 'Confirm your display name' if wallet.name else 'Choose your display name' }}</h2><p class="muted">Your display name is used across every RedPoints game. New players start with 100,000 RedPoints.</p>
    <form id="gamingNameForm" class="stack"><label for="gamingUsername">Display name</label><input id="gamingUsername" name="username" minlength="1" maxlength="64" value="{{ wallet.name or '' }}" autocomplete="nickname" required><label class="gaming-public-choice" for="gamingPublicVisibility"><input id="gamingPublicVisibility" name="public_visibility" type="checkbox" {% if wallet.public_visibility or wallet.needs_profile %}checked{% endif %}><span><strong>Show me on the Community Leaderboard</strong><small>Displays your name, game activity and weekly result. Wallet and recovery information stay private.</small></span></label><button class="button primary" type="submit">{{ 'Save Changes' if wallet.name else 'Create Profile & Play' }}</button></form>
    <button class="text-link small" id="openGamingRecovery" type="button">Recover Profile →</button></div>
  </dialog>

  <dialog id="gamingRecovery" class="gaming-dialog" aria-labelledby="gamingRecoveryTitle">
    <form method="dialog" class="gaming-dialog-close"><button type="submit" aria-label="Close recovery">×</button></form>
    <div class="gaming-dialog-content"><p class="eyebrow">PROFILE RECOVERY</p><h2 id="gamingRecoveryTitle">Recover Profile</h2><p class="small muted">A recovery code restores your display name, balance, active hands and fairness receipts. Treat it like a password.</p><div class="button-row"><button class="button" id="gamingCreateRecovery" type="button" {% if wallet.needs_profile %}disabled{% endif %}>Create recovery code</button><button class="button" id="gamingCopyRecovery" type="button" hidden>Copy code</button></div><label for="gamingRecoveryCode">Recovery code</label><textarea id="gamingRecoveryCode" rows="4" maxlength="512" spellcheck="false" placeholder="Paste a recovery code here"></textarea><button class="button primary" id="gamingRecoverPlayer" type="button">Recover Profile</button><p id="gamingRecoveryMessage" class="small muted" role="status"></p></div>
  </dialog>

{% if not game %}
<section class="gaming-community gaming-community-v15" aria-labelledby="gamingCommunityTitle" aria-label="Live Gaming leaderboard">
  <div class="section-title gaming-community-heading"><div><p class="eyebrow">COMMUNITY LEADERBOARD</p><h2 id="gamingCommunityTitle">Community Leaderboard</h2><p class="small muted">Recent activity and this week’s settled RedPoints results. Players choose whether their display name appears.</p></div><div id="gamingActivityCount" class="gaming-activity-count"><strong>{{ community.active_count }}</strong><span>playing now</span></div></div>
  <div class="gaming-community-tabs" role="tablist" aria-label="Community leaderboard view"><button type="button" class="is-active" data-community-view="live" aria-selected="true">Playing now</button><button type="button" data-community-view="leaders" aria-selected="false">Weekly leaders</button></div>
  <div id="gamingGameFilters" class="gaming-game-counts gaming-filter-bar" role="group" aria-label="Filter community activity">
    <button type="button" class="is-active" data-community-filter="all" aria-pressed="true"><b>{{ community.active_count }}</b> All Games</button>
    {% for key in game_rules.games %}<button type="button" data-community-filter="{{ key }}" aria-pressed="false"><b>{{ community.game_counts.get(key, 0) }}</b> {{ 'Hold’em' if key=='poker' else key|capitalize }}</button>{% endfor %}
  </div>
  <div class="gaming-community-grid gaming-community-grid-v15">
    <section class="panel gaming-live-panel" data-community-panel="live" aria-labelledby="gamingLiveTitle"><div class="gaming-panel-heading"><div><p class="eyebrow">PLAYING NOW</p><h3 id="gamingLiveTitle">Recent activity</h3></div><span class="live-dot" aria-hidden="true"></span></div><div id="gamingLivePlayers" class="gaming-live-list">{% for row in community.live_players %}<article><span class="gaming-live-avatar">{{ row.name[:1]|upper }}</span><div><strong>{{ row.name }}</strong><small>{{ row.game_label }} · {{ row.status }}</small></div></article>{% else %}<p class="empty">No public players are active right now. Start a game to appear here.</p>{% endfor %}</div></section>
    <section class="panel gaming-leader-panel" data-community-panel="leaders" aria-labelledby="gamingWeeklyTitle" hidden><div class="gaming-panel-heading"><div><p class="eyebrow">THIS WEEK</p><h3 id="gamingWeeklyTitle">Weekly leaders</h3></div><span class="tag">Top 10</span></div><ol id="gamingPublicLeaders" class="gaming-public-leaders">{% for row in community.weekly_leaders %}<li><span class="gaming-public-rank">{{ '%02d'|format(row.rank) }}</span><strong>{{ row.name }}</strong><span><b>{{ '{:+,}'.format(row.net) }} RP</b><small>{{ row.rounds }} rounds</small></span></li>{% else %}<li class="empty">No public results yet this week.</li>{% endfor %}</ol></section>
  </div>
</section>
<section class="games-launcher-heading"><div><p class="eyebrow">CHOOSE A GAME</p><h2>RedPoints Games</h2></div><a class="text-link" href="/gaming/fairness">Fairness &amp; Rules ↗</a></section>
<section class="game-cards game-cards-v15" aria-label="Choose a game">
<a href="/gaming/dice" class="panel game-card"><div class="game-art dice-art" aria-hidden="true"><span>⚄</span><span>⚂</span></div><h2>Dice <span>↗</span></h2><span class="button primary">Play Dice</span></a>
<a href="/gaming/keno" class="panel game-card"><div class="game-art mini-keno" aria-hidden="true">{% for n in range(1,13) %}<span class="{{ 'picked' if n in [2,5,8,10] else '' }}">{{ n }}</span>{% endfor %}</div><h2>Keno <span>↗</span></h2><span class="button primary">Play Keno</span></a>
<a href="/gaming/plinko" class="panel game-card"><div class="game-art plinko-art" aria-hidden="true"><span>●</span><div>· · ·<br>· · · · ·<br>· · · · · · ·</div></div><h2>Plinko <span>↗</span></h2><span class="button primary">Play Plinko</span></a>
<a href="/gaming/blackjack" class="panel game-card"><div class="game-art blackjack-art" aria-hidden="true"><span>♠ A</span><span>♥ K</span></div><h2>Blackjack <span>↗</span></h2><span class="button primary">Play Blackjack</span></a>
<a href="/gaming/limbo" class="panel game-card"><div class="game-art limbo-art" aria-hidden="true"><span>2.00×</span><i></i></div><h2>Limbo <span>↗</span></h2><span class="button primary">Play Limbo</span></a>
<a href="/gaming/coinflip" class="panel game-card"><div class="game-art coinflip-art" aria-hidden="true"><span>R</span></div><h2>Coinflip <span>↗</span></h2><span class="button primary">Play Coinflip</span></a>
<a href="/gaming/poker" class="panel game-card"><div class="game-art blackjack-art poker-art" aria-hidden="true"><span>♥ Q</span><span>♠ A</span></div><h2>Texas Hold’em <span>↗</span></h2><span class="button primary">Play Hold’em</span></a>
<a href="/gaming/baccarat" class="panel game-card"><div class="game-art blackjack-art baccarat-art" aria-hidden="true"><span>♠ 9</span><span>♥ 8</span></div><h2>Baccarat <span>↗</span></h2><span class="button primary">Play Baccarat</span></a>
</section>
<section class="panel game-season"><div class="section-title"><div><p class="eyebrow">YOUR RESULTS</p><h2>This week</h2></div></div><div id="gamingStats" class="game-stat-cards">{% for item,stat in wallet.stats.items() %}<article data-tone="{{ 'positive' if stat.net>0 else 'negative' if stat.net<0 else 'neutral' }}"><strong>{{ 'Hold’em' if item=='poker' else item|capitalize }}</strong><b>{{ '{:+,}'.format(stat.net) }}</b><small>{{ stat.bets }} rounds · net RedPoints</small></article>{% endfor %}</div></section>
{% else %}
<section class="game-layout panel" aria-label="{{ game|capitalize }} game">
<form id="betForm" class="bet-controls"><div class="field"><label for="redWager">{{ 'Table stack · RedPoints' if game=='poker' else 'Wager · RedPoints' }}</label><div class="wager-input"><input id="redWager" type="number" inputmode="numeric" min="{{ 20 if game=='poker' else 1 }}" max="{{ wallet.balance }}" step="1" value="{{ 1000 if game=='poker' else 100 }}" required><button type="button" class="button small" data-wager-scale="0.5" aria-label="Halve wager">½</button><button type="button" class="button small" data-wager-scale="2" aria-label="Double wager">2×</button></div></div>
{% if game=='dice' %}<div class="field"><label for="diceChance">Win chance</label><input id="diceChance" type="range" min="1" max="95" value="50"><output id="diceChanceLabel">50%</output></div><div class="field"><label for="diceSide">Target</label><select id="diceSide"><option value="under">Roll under</option><option value="over">Roll over or equal</option></select></div><div class="bet-preview"><span id="diceTarget">Roll below 50.00</span><strong id="dicePayout">198 points returned</strong><small>Includes wager.</small></div>
{% elif game=='limbo' %}
<div class="field"><label for="limboTarget">Target multiplier</label><input id="limboTarget" type="number" inputmode="decimal" min="1.01" max="1000000" step="0.01" value="2.00" required><div class="button-row limbo-targets"><button type="button" class="button small" data-limbo-target="2">2×</button><button type="button" class="button small" data-limbo-target="10">10×</button><button type="button" class="button small" data-limbo-target="100">100×</button></div></div><div class="bet-preview"><span id="limboChance">Win chance</span><strong id="limboPayout">200 points returned</strong><small>Includes wager.</small></div>
{% elif game=='coinflip' %}
<fieldset class="risk-options coin-options"><legend>Side</legend><label><input type="radio" name="coinSide" value="heads" checked><span>Heads</span></label><label><input type="radio" name="coinSide" value="tails"><span>Tails</span></label></fieldset><div class="bet-preview"><span>50% chance on either side</span><strong id="coinPayout">198 points returned on a win</strong></div>
{% elif game=='baccarat' %}
<fieldset class="risk-options baccarat-options"><legend>Bet on</legend>{% for side in ['player','banker','tie'] %}<label><input type="radio" name="baccaratSide" value="{{ side }}" {% if side=='banker' %}checked{% endif %}><span>{{ side|capitalize }}<small>{{ '2×' if side=='player' else '1.95×' if side=='banker' else '9×' }}</small></span></label>{% endfor %}</fieldset><div class="bet-preview"><strong id="baccaratPayout">195 points returned on a win</strong><small>Player / Banker bets push on a tie.</small></div>
{% elif game=='poker' %}<p class="small muted">Heads-up vs RedBot. Unused table chips return after the hand.</p><p id="holdemNextBlinds" class="small muted"></p>
{% elif game=='blackjack' %}<p class="small muted">Blackjack pays 3:2 · Dealer stands on 17.</p>
{% else %}<fieldset class="risk-options"><legend>Risk</legend>{% for risk in ['low','medium','high'] %}<label><input type="radio" name="risk" value="{{ risk }}" {% if risk=='medium' %}checked{% endif %}><span>{{ risk|capitalize }}</span></label>{% endfor %}</fieldset>
{% if game=='keno' %}<p id="kenoSelection" class="small muted">Pick 1–10 numbers on the board.</p><div class="button-row"><button id="kenoAuto" type="button" class="button small">Quick pick 10</button><button id="kenoClear" type="button" class="button small">Clear</button></div>
{% else %}<div class="field"><label for="plinkoRows">Rows</label><select id="plinkoRows"><option value="8">8 rows</option><option value="12">12 rows</option><option value="16" selected>16 rows</option></select></div>{% endif %}{% endif %}
<button id="betButton" type="submit" class="button primary" {% if wallet.needs_profile %}disabled{% endif %}>{{ 'Drop the ball' if game=='plinko' else 'Draw numbers' if game=='keno' else 'Deal hand' if game=='poker' else 'Deal cards' if game in ['blackjack','baccarat'] else 'Play Limbo' if game=='limbo' else 'Flip coin' if game=='coinflip' else 'Roll Dice' }}</button>

</form>
<div class="game-board">
{% if game=='dice' %}<div class="dice-stage"><div class="dice-roll" id="diceRoll">—</div><p id="diceRollLabel">Your next roll</p><div class="dice-track"><input id="diceBoardChance" class="dice-board-slider" type="range" min="0" max="100" step="1" value="50" aria-label="Dice threshold: drag to change win chance" aria-describedby="diceBoardChanceLabel"><span id="diceMarker" hidden></span></div><output id="diceBoardChanceLabel" class="small muted" for="diceBoardChance">50% win chance</output><div class="dice-scale"><span>0.00</span><span>99.99</span></div></div>
{% elif game=='keno' %}<div class="keno-board" aria-label="Choose Keno numbers">{% for n in range(1,41) %}<button type="button" data-keno="{{ n }}" aria-pressed="false">{{ n }}</button>{% endfor %}</div><p class="keno-key small muted"><span>Selected</span> <span>Drawn</span> <span>Matched</span></p>
{% elif game=='limbo' %}
<div class="limbo-stage"><output id="limboResult" class="limbo-multiplier">1.00×</output><p id="limboStatus" class="muted">Ready.</p><div class="limbo-trail" aria-hidden="true"><span id="limboTrail"></span></div><small id="limboTargetLabel" class="muted">Your target · 2.00×</small></div>
{% elif game=='coinflip' %}
<div class="coin-stage"><div class="coin-space"><div id="redCoin" class="red-coin" role="img" aria-label="Ready to flip"><span class="coin-face coin-heads" aria-hidden="true"><b>R</b><small>HEADS</small></span><span class="coin-face coin-tails" aria-hidden="true"><b>✦</b><small>TAILS</small></span></div></div><p id="coinStatus" class="muted">Ready.</p></div>
{% elif game=='poker' %}
{% include 'holdem_table.html' %}
<div id="legacyPokerTable" class="poker-table holdem-legacy" hidden><p class="notice small">Saved Video Poker hand. Finish this draw to start Hold’em. Its result stays in legacy records.</p><div class="section-title"><div><h2>Jacks or Better</h2></div><span class="small muted">9 / 6 paytable</span></div><div id="pokerCards" class="poker-cards" aria-label="Your five Poker cards">{% for n in range(5) %}<button type="button" class="poker-card is-back" disabled aria-label="Card not dealt">R</button>{% endfor %}</div><div class="button-row poker-actions"><button type="button" class="button small" id="pokerHoldAll" disabled>Hold all</button><button type="button" class="button small" id="pokerClear" disabled>Clear holds</button><button type="button" class="button primary" id="pokerDraw" disabled>Draw cards</button></div><p id="pokerStatus" class="small" role="status">Tap cards to hold.</p></div>
{% elif game=='baccarat' %}
<div class="baccarat-table"><div class="baccarat-hands">{% for side in ['player','banker'] %}<section class="baccarat-hand" id="baccarat{{ side|capitalize }}Hand"><div class="row"><h2>{{ side|capitalize }}</h2><output id="baccarat{{ side|capitalize }}Total">—</output></div><div class="playing-cards" id="baccarat{{ side|capitalize }}" aria-label="{{ side|capitalize }} cards"><span class="playing-card is-hidden">◆</span><span class="playing-card is-hidden">◆</span></div></section>{% endfor %}</div><p id="baccaratStatus" class="small" role="status">Closest to 9 wins.</p></div>
{% elif game=='blackjack' %}<div class="blackjack-table"><div class="blackjack-hand"><div class="row"><h3>Dealer</h3><output id="blackjackDealerTotal">—</output></div><div id="blackjackDealer" class="playing-cards" aria-label="Dealer cards"></div></div><p class="blackjack-felt-label">BLACKJACK PAYS 3:2 <span>DEALER STANDS ON ALL 17s</span></p><div class="blackjack-hand"><div class="row"><h3>Your hand</h3><output id="blackjackPlayerTotal">—</output></div><div id="blackjackPlayer" class="playing-cards" aria-label="Your cards"></div></div><div class="button-row blackjack-actions"><button type="button" class="button primary" data-blackjack="hit" disabled>Hit</button><button type="button" class="button" data-blackjack="stand" disabled>Stand</button><button type="button" class="button" data-blackjack="double" disabled>Double</button></div><p id="blackjackStatus" class="small" role="status">Ready.</p></div>
{% else %}<canvas id="plinkoCanvas" width="720" height="510" aria-label="Plinko board. The result is also shown in text below."></canvas><p id="plinkoResult" class="small muted">Ready to drop.</p>{% endif %}
<div id="gameResult" class="game-result" role="status">Ready.</div><small id="betProof" class="muted"></small>
</div></section>
<details class="panel payout-panel"><summary>{{ 'Rules &amp; hand rankings'|safe if game=='poker' else 'Payouts' }}</summary><p id="payoutDescription" class="small muted"></p><div id="payoutTable" class="payout-table"></div>{% if game=='poker' %}<div class="holdem-rules"><p>Two private cards each. Five shared cards: flop (three), turn (one), river (one). Best five-card hand wins; equal hands split the pot. The dealer button alternates. The button posts the small blind and acts first before the flop, last afterward.</p><p>Check when no bet is owed; otherwise Call, Raise or Fold. A raise amount is the total for this betting round. The minimum raise equals the previous full raise; a smaller increase is allowed only all-in. The minimum opening bet is one big blind. Unmatched chips return to their owner. There is no rake or fixed payout multiplier.</p><p>Both seats start with your chosen table stack. Big blind: stack ÷ 50, rounded down, minimum 2. Small blind: half the big blind, rounded down, minimum 1. Minimum table stack: 20 RP. The wallet reserves your stack until the hand ends. Refresh resumes the same hand. At the weekly reset an unfinished hand folds before the new allowance.</p><p>RedBot is a published, deterministic computer strategy. It sees only its own cards, the revealed board and public betting state. It is not a human player. The completed receipt verifies the shuffle, every decision and the pot. <a class="text-link" href="/gaming/fairness#holdem">Full fairness specification →</a></p></div>{% else %}<p class="small muted">Returns include your wager; rounded down to whole points.</p>{% endif %}</details>
<details class="panel fairness-panel"><summary>Fairness</summary><label for="clientSeed">Your client seed</label><input id="clientSeed" maxlength="64" pattern="[A-Za-z0-9 _.\-]+" autocomplete="off"><dl><dt>Next bet number</dt><dd id="fairNonce">{{ wallet.nonce }}</dd><dt>Committed server-seed hash</dt><dd><code id="fairCommitment">{{ wallet.commitment or 'Save your name to prepare a commitment.' }}</code></dd></dl><a class="text-link" href="/gaming/fairness">Rules &amp; receipt verifier →</a></details>
{% endif %}
<section class="panel bet-history"><div class="section-title"><h2>Recent rounds</h2><a class="text-link" href="/gaming/api/receipts">Receipts ↓</a></div><div class="table-scroll" tabindex="0" role="region" aria-label="Recent rounds" id="historyTable"><table><thead><tr><th>Game</th><th>Wager</th><th>Returned</th><th>Net</th><th>Proof</th></tr></thead><tbody id="betHistory"><tr><td colspan="5" class="empty">No rounds yet.</td></tr></tbody></table></div><button id="historyToggle" class="button small history-toggle" type="button" aria-expanded="false" aria-controls="historyTable" hidden>View all rounds</button></section>
<noscript><p class="notice">JavaScript and a secure HTTPS connection (or localhost) are required for local fairness verification and gameplay.</p></noscript>
</main>
{% endblock %}
{% block scripts %}{% if game=='plinko' %}<script src="{{ url_for('static',filename='plinko.js',v=asset_version) }}" defer></script>{% endif %}<script src="{{ url_for('static',filename='holdem-fairness.js',v=asset_version) }}" defer></script>{% if game=='poker' %}<script src="{{ url_for('static',filename='holdem-ui.js',v=asset_version) }}" defer></script>{% endif %}<script src="{{ url_for('static',filename='fairness.js',v=asset_version) }}" defer></script><script src="{{ url_for('static',filename='gaming.js',v=asset_version) }}" defer></script>{% endblock %}
```

## `templates/gaming_fairness.html`

```html
{% extends 'base.html' %}
{% block title %}Fairness &amp; verifier · RedPoints{% endblock %}
{% block styles %}<link rel="stylesheet" href="{{ url_for('static',filename='gaming.css',v=asset_version) }}">{% endblock %}
{% block content %}<main id="main" class="shell gaming-page"><p class="eyebrow">INSPECT EVERY ROUND</p><h1>Provably fair<span class="accent">.</span></h1><a class="button" href="/gaming">← Gaming dashboard</a>
<section class="panel fairness-panel"><h2>A commitment before your wager</h2><ol>
<li>The server generates a random 32-byte seed and publishes its SHA-256 hash before your bet. The active seed stays private.</li>
<li>Choose your client seed. After reading the commitment, your browser generates another fresh 16 random bytes for this bet. The receipt records both inputs, the game, settings, wager, season and sequential bet number.</li>
<li>HMAC-SHA-256 generates the outcome from those inputs. Balance, wager, result and receipt save in one transaction.</li>
<li>The one-time server seed is revealed when the round ends. Blackjack keeps it and the dealer hole card private until the hand is complete. Hold’em keeps its seed, opponent cards and unrevealed community cards private until the hand ends. Your browser checks its earlier commitment and independently reproduces the result and payout before showing “Verified.” A fresh committed seed is used for the next bet.</li>
</ol><p class="small muted">Keep the commitment you saw before playing. A receipt alone proves its calculation is consistent; it does not independently prove when its commitment was first published. This is an inspectable algorithm, not third-party certification, identity verification, a payout guarantee, or a connection to real-money Shuffle games.</p></section>
<section class="panel fairness-panel"><h2>Verify a saved receipt</h2><p class="muted">Runs entirely in your browser. Paste one downloaded receipt, or an array of receipts. Nothing in this form is sent to the server.</p><form id="receiptVerifier" class="verifier-form"><label for="verifyCommitment">Commitment you saved before this bet (optional; single receipt only)</label><input id="verifyCommitment" minlength="64" maxlength="64" pattern="[a-f0-9]{64}"><label for="verifyReceipt">Receipt JSON</label><textarea id="verifyReceipt" required spellcheck="false"></textarea><button class="button primary" type="submit">Verify locally</button><output id="verifyResult" role="status"></output></form></section>
<section class="panel fairness-panel"><h2>The published rules</h2><p><strong>Dice:</strong> An unbiased integer from 0 to 9,999 is displayed as 0.00–99.99. For a win chance of C percent, Under wins below C × 100; Over wins at or above 10,000 − C × 100. A winning bet returns floor(wager × 99 ÷ C) points, including the wager.</p><p><strong>Keno:</strong> Select 1–10 numbers from 1–40. Ten different numbers are drawn using a partial Fisher–Yates shuffle. Your match count selects the published multiplier. The table updates before betting whenever picks or risk change.</p><p><strong>Plinko:</strong> Each of 8, 12 or 16 steps is an unbiased left/right decision. The sum of right steps selects the slot. The animation only illustrates those committed decisions; physics does not decide the result.</p><p><strong>Blackjack:</strong> A fresh six-deck shoe is sampled without replacement each hand. Cards are dealt player, dealer, player, dealer. Aces count as 1 or 11; face cards count as 10. The dealer checks for a natural before player decisions and stands on all 17s. Hit, Stand, and Double on the first two cards are supported. Double adds the original wager and allows one final card. No splitting, insurance, or surrender. A natural pays 3:2 profit; other wins pay 1:1; ties return the stake. Whole-point returns round down. An opening pair of naturals is a push. An active hand reserves its wager and survives reloads. At the weekly cutoff it automatically stands, is settled under the old week, then the new weekly balance is granted.</p><p><strong>Limbo:</strong> Choose a target from 1.01× to 1,000,000× in 0.01 steps. Let N = 2³² and r be the next unbiased integer from 0 through N−1. The result in hundredths is max(100, floor(99 × N ÷ (N−r))). Reach your target or higher to win. A win returns floor(wager × target-hundredths ÷ 100), regardless of how much higher the result goes. For target T in hundredths, the exact win probability is floor(99 × N ÷ T) ÷ N. Expected return is at most 99% before whole-point rounding.</p>
<p><strong>Coinflip:</strong> Choose Heads or Tails. An unbiased bit maps 0 to Heads and 1 to Tails. Each side has a 50% chance. A win returns floor(wager × 198 ÷ 100), including the stake. A loss returns zero. Expected return is 99% before whole-point rounding.</p>
<p><strong>Texas Hold’em:</strong> Two private cards, five community cards, real betting rounds and pot-based returns against the published RedBot computer opponent. <a href="#holdem">Rules, accounting and verifier specification below.</a></p><details><summary>Legacy Video Poker · v3/v4 rules</summary><p><strong>Video Poker:</strong> Single-player five-card draw Video Poker, using a 52-card deck and a 9/6 Jacks or Better paytable. Deal five cards, hold any subset, then draw once from the remaining deck. Discards never return; held cards stay in their original positions. Total returns are: royal flush 800×, straight flush 50×, four of a kind 25×, full house 9×, flush 6×, straight 4×, three of a kind 3×, two pair 2×, and a pair of jacks, queens, kings or aces 1×. All other hands return zero. The 800× royal applies to every valid wager. Aces may be high or low in a straight. Strategy affects returns, so no fixed player RTP is claimed. The original five cards and your selected holds are included in the final verifiable receipt. At the weekly cutoff, an unfinished hand keeps all five initial cards and settles under the old week before the new balance begins.</p></details>
<p><strong>Baccarat:</strong> Eight decks, freshly sampled each round. Bet on Player, Banker or Tie. Ace=1; 2–9 keep their value; 10/J/Q/K=0. Totals use the last digit. Deal Player, Banker, Player, Banker. An initial 8 or 9 in either hand stops all draws. Otherwise Player draws on 0–5. If Player stands, Banker draws on 0–5. If Player draws, Banker draws on 0–2; on 3 except against an 8; on 4 against 2–7; on 5 against 4–7; on 6 against 6–7; never on 7. Higher final total wins. Player returns 2×, Banker 1.95× after 5% commission, Tie 9×. Player/Banker wagers push on a tie. Returns include the stake and round down to whole points. No side bets, burn cards or carried-over shoes.</p>
<p><strong>Returns:</strong> Keno uses probability-weighted tables targeting 99% expected return before rounding. Plinko uses fixed, symmetric tables: 16-row High has a maximum of 1000×, 12-row High 170×, and 8-row High 29×. Its exact expected return depends on the board and risk. All payouts round down to whole points; small wagers can have lower effective returns. Open Payouts before betting for exact multipliers and returns. Outcome probabilities are also available on table entries.</p><p class="small muted">RedPoints are play-only. There are no purchases, cash-outs or Botrix transfers. Your balance is shared across the eight games and resets to 100,000 at Tuesday 6 PM America/New_York, including daylight saving changes. Each signed player has a separate wallet; people sharing an IP can all play. Browser refreshes restore that player’s available balance to 100,000; server restarts restore every saved wallet to 100,000. Game winnings and unfinished hands are kept until the normal weekly rollover. A recovery code restores your own player in another browser; an IP or display name cannot access someone else’s wallet. There is no daily or weekly play-count limit. Duplicate requests cannot settle the same bet twice.</p></section>
<section class="panel fairness-panel"><details><summary>Payout tables and earlier receipts</summary>
<p>Let p = 2 for Low, 4 for Medium, or 7 for High. For Keno with k selected numbers and h matches, use probability P(h) = choose(k,h) × choose(40−k,10−h) ÷ choose(40,10), and weight w(h) = h<sup>p</sup>.</p>
<p>For Plinko with n rows and landing slot s, the probability is P(s) = choose(n,s) ÷ 2<sup>n</sup>. <code>redpoints-v2</code>, <code>redpoints-v3</code>, <code>redpoints-v4</code> and <code>redpoints-v5</code> use the fixed integer tables published in <code>PLINKO_TABLES</code> in both verifier implementations. The exact expected return is Σ P(s) × multiplier(s). Earlier <code>redpoints-v1</code> receipts instead use weight w(s) = ½ + |2s−n|<sup>p</sup> and the weighted formula below. Earlier receipts keep their original outcomes and payouts.</p>
<p>For Keno and legacy v1 Plinko, calculate the probability-weighted mean M = Σ P(i)w(i). Each multiplier in integer units is floor((99 ÷ 100) × w(i) ÷ M × 10,000). Divide units by 10,000 to display the multiplier. For these table games the return is floor(wager × units ÷ 10,000). Blackjack and Poker have no fixed RTP claim: their expectation depends on the chosen rules and player decisions. The admin panel reports actual settled totals, not an estimated house return. The server uses exact fractions and the independent browser verifier uses integer ratios.</p>
<p class="small muted">Whole-point rounding can make small wagers return materially less than the listed expectation; the payout table shows the exact returned points before each wager.</p>
</details></section>
<section class="panel fairness-panel"><h2>Exact versioned byte format</h2><p>Decode the 64-character server-seed hex string into 32 bytes. SHA-256 of those bytes is the commitment. For HMAC, use those bytes as the key. The ASCII message is compact JSON of:</p><pre><code>[rules_version, season, game, client_seed, client_salt,
 nonce, wager, options, block_number]</code></pre><p>Use the receipt’s <code>rules_version</code>: <code>redpoints-v5</code> for new bets. Earlier v1–v4 receipts remain verifiable. Saved Blackjack and Video Poker hands finish under their original rules; the next bet uses v5. Object keys are sorted, with no spaces around separators. Block numbers start at zero. Read the HMAC digest in four-byte big-endian integers. To choose from N outcomes, reject values at or above 2³² − (2³² mod N), then use value mod N. Consume the next four bytes for the next draw; generate the next HMAC block when necessary.</p><p>Blackjack uses options <code>{"decks":6}</code>. Start with card IDs 0–311, where an ID equals deck × 52 + suit × 13 + rank − 1. Suits are spades, hearts, clubs, diamonds; ranks are A=1 through K=13. For each draw at index i, draw j uniformly from i through 311, swap those shoe positions, and consume the card at i. Replay the saved <code>actions</code> in order against this sequence. Actions are not added to the HMAC context, so changing a decision cannot reshuffle the shoe. The completed receipt includes the decisions and total stake (including Double); net winnings equal payout minus that total stake. The browser verifies the full replay after seed reveal.</p><p>Legacy Video Poker uses options <code>{"variant":"jacks_or_better"}</code> and card IDs 0–51 with the same suit/rank encoding. Partially shuffle and consume five cards first. At Draw, iterate positions 0 through 4; retain held positions and replace each other position with the next card sampled from the remaining deck. The sorted <code>holds</code> array contains positions 0–4. Holds are not part of the HMAC context, so choosing cards never reseeds or reshuffles the committed sequence.</p><p>Baccarat uses <code>{"decks":8,"side":"banker"}</code>, where the side is player, banker or tie. Use card IDs 0–415 with the same encoding; partially shuffle by sampling j from i through 415, swap, then consume i. Deal opening cards alternately and any Player third card before Banker's. The receipt includes all cards, totals and the exact payout. Its independent verifier replays the full draw tableau.</p><p>Coinflip uses options <code>{"side":"heads"}</code> or <code>{"side":"tails"}</code>. Limbo uses <code>{"target":200}</code> for a 2.00× target; its result multiplier also uses hundredths. Legacy Video Poker result multipliers use whole units; Hold’em uses pot awards and has no paytable. Keno, Plinko and Coinflip multipliers use 1/10,000 units. Receipts are versioned so each verifier uses the correct scale.</p>
<p class="small muted">The configured package includes <code>fairness.py</code>, the independent browser implementation <code>static/fairness.js</code>, and the optional offline verifier <code>tools/verify_redpoints.py</code>. These games have their own published rules; they do not claim compatibility with another operator's receipts or payout tables.</p></section><section id="holdem" class="panel prose"><h2>Texas Hold’em · redpoints-v5</h2><p>Poker now means heads-up no-limit Texas Hold’em against RedBot, with two equal table stacks and no rake. Archived Jacks or Better hands and receipts above continue to use their original v3/v4 rules. They never become Hold’em results.</p><p>The chosen stack is reserved from the wallet. At settlement, the entire remaining table stack returns. Net is final table stack minus starting stack. Admin wagers count only matched committed chips; returned means pot awards. Uncalled chips are refunded. Equal best five-card hands split the pot; suits never break ties. The best five can use zero, one or two hole cards.</p><p>Options are <code>{"button":"player","variant":"texas_holdem"}</code> or button computer. The button alternates with settled Hold’em hands in this week, beginning with the player. Big blind is floor(stack/50), minimum 2; small blind is floor(big blind/2), minimum 1. Minimum buy-in is 20. Both seats start each hand with the same stack, limiting loss to that stack. No daily or weekly hand limit.</p><p>Use the existing HMAC stream with version redpoints-v5. Full Fisher–Yates shuffle of IDs 0–51: for i=0 through 50, sample j=i+below(52−i), then swap. Deal alternately, big blind first: deck positions 0–3 are hole cards. Burn position 4; flop is 5–7. Burn 8; turn is 9. Burn 10; river is 11. The deck never changes after betting choices. Hole cards remain hidden until showdown; the seed reveals the full deal after any completed hand, including a fold.</p><p>The button is small blind and acts first preflop; big blind acts first after the flop. There is a big-blind option after a preflop call. Opening bet minimum is the big blind; a full raise increases the highest street contribution by at least the last full raise. Smaller increases are allowed only all-in. An all-in opponent cannot face another bet. Unmatched chips return before a showdown or fold is settled.</p><p>Player decisions are recorded as action plus amount. Amount is a total street contribution for bet or raise, zero for check/call/fold/all_in. They are excluded from the shuffle context. The independent verifier reconstructs every legal action, RedBot response, revealed street, pot and final five-card evaluation. At the weekly boundary an unfinished hand folds without spending more points, recorded as weekly_reset.</p><h3>Published opponent: redbot-v1</h3><p>RedBot receives only its two cards, visible community cards, current pot, legal bet sizes, blind size, street and its own raise count. It does not receive your cards, the seed or the remaining deck. Its exact deterministic decision function is published in holdem.py and independently in static/holdem-fairness.js. It uses made-hand strength, price thresholds and an occasional deterministic bluff. Strength scores are heuristics, not claimed win probabilities. It raises at most once per street; a player can still raise legally in response.</p><p>Receipts prove that the committed deck, published opponent policy, recorded choices and accounting agree. They do not prove optimal opponent play or stop a server from refusing a request. Retain your pre-hand commitment and receipt when auditing. <a class="text-link" href="https://www.pokerstars.com/poker/games/texas-holdem/" target="_blank" rel="noopener">Texas Hold’em rules reference ↗</a></p></section></main>{% endblock %}
{% block scripts %}<script src="{{ url_for('static',filename='holdem-fairness.js',v=asset_version) }}" defer></script><script src="{{ url_for('static',filename='fairness.js',v=asset_version) }}" defer></script><script src="{{ url_for('static',filename='receipt-verifier.js',v=asset_version) }}" defer></script>{% endblock %}
```

## `templates/history.html`

```html
{% extends 'base.html' %}
{% block title %}Race History · RedHunllef{% endblock %}
{% block styles %}<link rel="stylesheet" href="{{ url_for('static', filename='history.css', v=asset_version) }}">{% endblock %}
{% block content %}
{% set week = history.selected %}
<main id="main" class="shell history-page public-interior-page" data-selected-week="{{ week.id }}">
  <header class="history-heading">
    <div><p class="eyebrow">THE LAST FOUR WEEKS</p><h1>Race history<span class="accent">.</span></h1>
    <p class="lead">The community's top 25. Every Tuesday at 6 PM Eastern, a new week closes.</p></div>
    <a class="button" href="/#leaderboard">Current leaderboard <span aria-hidden="true">↗</span></a>
  </header>
  <nav id="historyWeeks" class="history-weeks" aria-label="Completed weeks">
    {% for item in history.weeks %}<a href="{{ url_for('public_history', week=item.id) }}" data-week="{{ item.id }}" {% if item.id==week.id %}aria-current="page"{% endif %}>
      <span class="eyebrow">{{ 'LATEST COMPLETED' if loop.first else 'WEEK ' ~ loop.index }}</span><strong>{{ item.label }}</strong><small>Tuesday → Tuesday</small>
    </a>{% endfor %}
  </nav>
  <form action="/history" method="get" class="history-picker" aria-label="Choose a completed week">
    <label for="historyWeekSelect">Completed week · Eastern Time</label>
    <div class="history-picker-row"><select id="historyWeekSelect" name="week">{% for item in history.weeks %}<option value="{{ item.id }}" {% if item.id==week.id %}selected{% endif %}>{{ item.label }}</option>{% endfor %}</select><button class="button" type="submit">View</button></div>
    <div class="history-step-links">{% set ns=namespace(index=0) %}{% for item in history.weeks %}{% if item.id==week.id %}{% set ns.index=loop.index0 %}{% endif %}{% endfor %}
      <a id="historyPrevious" class="button small" {% if ns.index<3 %}href="/history?week={{ history.weeks[ns.index+1].id }}"{% else %}aria-disabled="true"{% endif %}>← Previous week</a>
      <a id="historyNext" class="button small" {% if ns.index>0 %}href="/history?week={{ history.weeks[ns.index-1].id }}"{% else %}aria-disabled="true"{% endif %}>Next week →</a>
    </div>
  </form>
  <section class="panel history-results" aria-labelledby="historyTitle">
    <div class="history-result-heading"><div><p class="eyebrow">TOP 25 · USERNAMES PROTECTED</p><h2 id="historyTitle">{{ week.label }}</h2></div><span id="historyStatus" class="badge">{{ 'Saved standings' if week.origin=='snapshot' else {'ready':'Provider confirmed','partial':'Partial results','delayed':'Update delayed','loading':'Loading results'}[week.status] }}</span></div>
    <p class="muted history-window" id="historyWindow">{{ week.start_et }} → {{ week.end_et }}</p>
    <p id="historyMessage" class="notice" role="status" {% if not week.message %}hidden{% endif %}>{{ week.message }}</p>
    <p id="historyNetwork" class="notice warning" role="status" hidden></p>
    <div class="table-scroll" tabindex="0" role="region" aria-label="Historical top 25 leaderboard">
      <table><thead><tr><th scope="col">Place</th><th scope="col">Player</th><th scope="col" class="number">Weighted wager</th><th scope="col" class="number">Recorded prize</th></tr></thead>
      <tbody id="historyRows">{% for row in week.rows %}<tr><td class="rank">{{ '%02d'|format(row.rank) }}</td><td><strong>{{ row.username }}</strong></td><td class="number">{{ row.wager }}</td><td class="number accent">{{ row.prize }}</td></tr>{% else %}<tr><td colspan="4" class="empty">{{ 'No qualifying wagers returned for this week.' if week.status=='ready' else 'Results are not available yet. This page checks automatically.' }}</td></tr>{% endfor %}</tbody></table>
    </div>
    <div class="history-meta"><span id="historyCount">{{ week.count ~ (' saved places · final top 25 awaiting confirmation' if week.origin == 'snapshot' else ' qualifying players · showing up to 25') if week.count is not none else 'Waiting for the first result' }}</span><span id="historyChecked">Last checked: {{ week.updated_et }}</span></div>
    <p id="historyPrizeNote" class="muted small">{{ 'Prizes use this week’s saved race settings; only the top 15 places are paid.' if week.prizes_known else 'No matching prize schedule was saved for this week. Prizes are shown as —.' }}</p>
  </section>
  <div class="leaderboard-foot"><span>Tuesday 6 PM → Tuesday 6 PM Eastern · daylight saving time included</span><span>Page updates every 60 seconds</span></div>
  <noscript><p class="notice">Select any week above. Reload to see the latest saved results.</p></noscript>
</main>
{% endblock %}
{% block scripts %}<script src="{{ url_for('static', filename='history.js', v=asset_version) }}" defer></script>{% endblock %}
```

## `templates/holdem_table.html`

```html
<div id="holdemTable" class="holdem-table" aria-label="Texas Hold’em table">
  <div class="holdem-topline"><span class="eyebrow">TEXAS HOLD’EM</span><span id="holdemBlinds" class="small muted">Heads-up · No limit</span></div>
  <section class="holdem-seat" aria-label="Computer opponent">
    <div class="holdem-seat-label"><strong>RedBot <small>Computer</small></strong><span id="holdemComputerButton" class="dealer-button" hidden aria-label="Dealer button">D</span><output id="holdemComputerStack">—</output></div>
    <div id="holdemComputerCards" class="playing-cards holdem-hole" aria-label="Computer cards"><span class="playing-card is-hidden">◆</span><span class="playing-card is-hidden">◆</span></div>
    <small id="holdemComputerBet" class="holdem-seat-bet">&nbsp;</small>
  </section>
  <div class="holdem-center">
    <div class="holdem-pot"><small>POT</small><output id="holdemPot">0</output><span id="holdemChip" aria-hidden="true">R</span></div>
    <div id="holdemBoard" class="playing-cards holdem-board" aria-label="Community cards">{% for n in range(5) %}<span class="holdem-card-slot" aria-hidden="true"></span>{% endfor %}</div>
    <span id="holdemStreet" class="holdem-street">Ready to deal</span>
  </div>
  <section class="holdem-seat" aria-label="Your Hold’em seat">
    <small id="holdemPlayerBet" class="holdem-seat-bet">&nbsp;</small>
    <div id="holdemPlayerCards" class="playing-cards holdem-hole" aria-label="Your cards"><span class="playing-card is-hidden">◆</span><span class="playing-card is-hidden">◆</span></div>
    <div class="holdem-seat-label"><strong>You</strong><span id="holdemPlayerButton" class="dealer-button" hidden aria-label="Dealer button">D</span><output id="holdemPlayerStack">—</output></div>
  </section>
  <p id="holdemStatus" class="holdem-status" role="status" aria-live="polite">Choose a table stack. Deal when ready.</p>
  <div id="holdemControls" class="holdem-controls" hidden>
    <div class="button-row holdem-moves">
      <button type="button" class="button" data-holdem="fold">Fold</button>
      <button type="button" class="button primary" data-holdem="check">Check</button>
      <button type="button" class="button primary" data-holdem="call">Call</button>
      <button type="button" class="button" data-holdem="all_in">All-in</button>
    </div>
    <div id="holdemRaiseControls" class="holdem-raise">
      <label for="holdemRaise">Raise to · RedPoints</label>
      <div class="holdem-raise-input"><input id="holdemRaise" type="number" inputmode="numeric" min="1" step="1"><button type="button" class="button primary" id="holdemRaiseButton">Raise</button></div>
      <div class="button-row"><button type="button" class="button small" data-holdem-size="min">Min</button><button type="button" class="button small" data-holdem-size="half">½ pot</button><button type="button" class="button small" data-holdem-size="pot">Pot</button><small id="holdemRaiseCost" class="muted"></small></div>
    </div>
  </div>
  <details class="holdem-log"><summary>Hand history</summary><ol id="holdemLog"></ol></details>
</div>
```

## `templates/icons.html`

```html
{% macro icon(name, size=20) -%}
<svg class="ui-icon" width="{{ size }}" height="{{ size }}" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.7" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true" focusable="false">
{% if name=='blade' %}<path d="m4 3 7 3 10 15-7-3L4 3ZM3 16l5 5m-4 0 4-5"/>
{% elif name=='bow' %}<path d="M5 3c18 0 18 18 0 18V3Zm0 0 12 9-12 9M2 12h20m-4-4 4 4-4 4"/>
{% elif name=='magic' %}<path d="m12 2 3 7 7 3-7 3-3 7-3-7-7-3 7-3 3-7Z"/>
{% elif name=='close' %}<path d="m6 6 12 12M18 6 6 18"/>
{% elif name=='link' %}<path d="m9 15 6-6m-5-3 2-2a5 5 0 0 1 7 7l-2 2M7 11l-2 2a5 5 0 0 0 7 7l2-2"/>
{% endif %}</svg>
{%- endmacro %}
```

## `templates/index.html`

```html
{% extends 'base.html' %}
{% from 'macros.html' import public_race_summary %}
{% block attributes %}data-page="public" data-feed="/public-state" data-bootstrap="{{ data|tojson|forceescape }}"{% endblock %}
{% block content %}
<main id="main" class="shell public-home">
  <section class="race-hero" aria-labelledby="raceTitle">
    <div class="race-hero-copy">
      <p class="eyebrow"><span class="dot"></span> REDHUNLLEF COMMUNITY RACE</p>
      <h1 id="raceTitle">RedHunllef Wager Race</h1>
      <p id="raceDescription" class="lead">Compete in the weekly race and climb the standings.</p>
      <div class="provider-tabs public-provider-tabs" role="tablist" aria-label="Choose a leaderboard provider">
        <button id="shuffleTab" class="button active" type="button" role="tab" aria-selected="true" aria-controls="shuffleBoard">Shuffle · Top 15</button>
        <button id="empireTab" class="button" type="button" role="tab" aria-selected="false" aria-controls="empireBoard" tabindex="-1">EmpireDrop · Top 10</button>
      </div>
      <div class="provider-brand-row" aria-label="Race providers">
        <a id="sponsorLink" class="provider-brand-card is-selected" data-provider-brand="shuffle" href="{{ data.site.sponsor_url }}" target="_blank" rel="noopener noreferrer sponsored">
          <span class="provider-mark" aria-hidden="true">S</span>
          <span><small>Powered By</small><strong id="sponsorName">{{ data.site.sponsor_name }}</strong></span>
          <span aria-hidden="true">↗</span>
        </a>
        <a class="provider-brand-card" data-provider-brand="empiredrop" href="https://empiredrop.com/c/red" target="_blank" rel="noopener noreferrer sponsored">
          <span class="provider-mark" aria-hidden="true">E</span>
          <span><small>Powered By</small><strong>EmpireDrop</strong></span>
          <span aria-hidden="true">↗</span>
        </a>
      </div>
    </div>

    {{ public_race_summary('shuffleRaceClock', 'clockLabel', 'raceBadge', 'state-' ~ data.site.race_state, data.site.race_state|capitalize, 'countdown', 'raceWindow', data.site.start_et ~ ' → ' ~ data.site.end_et, 'poolTotal', data.site.total_prize, 15, false, 'Shuffle race schedule') }}

    {{ public_race_summary('empireRaceClock', 'empireClockLabel', 'empireRaceBadge', 'state-unconfigured', 'Schedule', 'empireCountdown', 'empireRaceWindow', data.empiredrop.schedule.start_et ~ ' → ' ~ data.empiredrop.schedule.end_et, 'empirePoolTotal', data.empiredrop.prizes.total if data.empiredrop.prizes.enabled else 'Not announced', 10, true, 'EmpireDrop race schedule') }}
  </section>

  <section id="leaderboard" class="public-leaderboards" aria-labelledby="leaderboardTitle">
    <div class="section-title leaderboard-heading"><div><p class="eyebrow">WEEKLY STANDINGS</p><h2 id="leaderboardTitle">Weekly standings</h2></div><a id="providerJoinLink" class="button small" href="{{ data.site.sponsor_url }}" target="_blank" rel="noopener noreferrer sponsored">Join the race ↗</a></div>

    <div id="shuffleBoard" role="tabpanel" aria-labelledby="shuffleTab">
      <p id="leaderboardMessage" class="notice public-fallback" role="status" {% if data.rows %}hidden{% endif %}>Standings are temporarily unavailable.</p>
      <p id="networkError" class="notice public-fallback" role="status" hidden>Standings are temporarily unavailable.</p>
      <div class="podium public-podium">{% for n in [2,1,3] %}{% set r=data.rows|selectattr('rank','equalto',n)|first %}<article class="podium-card place-{{ n }}" data-rank="{{ n }}"><div class="podium-top"><span class="placement">{{ '%02d'|format(n) }}</span><span class="eyebrow">{{ 'FIRST PLACE' if n==1 else 'SECOND PLACE' if n==2 else 'THIRD PLACE' }}</span></div><strong class="podium-name" data-name>{{ r.username if r else 'Open position' }}</strong><div class="podium-values"><div><small>WAGERED</small><strong data-wager>{{ r.wager if r else '$0.00' }}</strong></div><div><small>PRIZE</small><strong class="accent" data-prize>{{ money(data.site.prizes[n|string]) }}</strong></div></div></article>{% endfor %}</div>
      <div class="panel public-table table-scroll" tabindex="0" role="region" aria-label="Shuffle leaderboard places four through fifteen"><table><thead><tr><th>Place</th><th>Player</th><th class="number">Wagered</th><th class="number">Prize</th></tr></thead><tbody>{% for n in range(4,16) %}{% set r=data.rows|selectattr('rank','equalto',n)|first %}<tr data-rank="{{ n }}"><td class="rank">{{ '%02d'|format(n) }}</td><td><strong data-name>{{ r.username if r else 'Open position' }}</strong></td><td class="number" data-wager>{{ r.wager if r else '$0.00' }}</td><td class="number accent" data-prize>{{ money(data.site.prizes[n|string]) }}</td></tr>{% endfor %}</tbody></table></div>
      <details class="panel explanation"><summary>How Shuffle wagers are weighted <span aria-hidden="true">+</span></summary><div class="weighting-grid">{% for rule in weighting %}<div><strong>{{ rule.range }}</strong><p>{{ rule.counts }}</p></div>{% endfor %}</div><p class="muted small">Eligible wagers are adjusted by game RTP. Results and prizes may be reviewed or adjusted.</p></details>
    </div>

    {# Server-render verified standings start #}
    <div id="empireBoard" role="tabpanel" aria-labelledby="empireTab" hidden>
      <p id="empireMessage" class="notice public-fallback" role="status" {% if data.empiredrop.rows %}hidden{% endif %}>{{ 'Standings are temporarily unavailable.' if not data.empiredrop.rows else '' }}</p>
      {% set empire_rows = data.empiredrop.rows[:10] %}
      {% set empire_limit = data.empiredrop.race_meta.get('ranks_limit', 10)|int or 10 %}
      <div class="empire-podium podium public-podium" id="empirePodium" aria-label="EmpireDrop top three">
      {% for n in [2,1,3] %}{% set r = empire_rows[n-1] if empire_rows|length >= n else none %}
        <article class="podium-card place-{{ n }}"><div class="podium-top"><span class="placement" data-empire-place="{{ n }}">{{ '%02d'|format(r.rank if r else n) }}</span><span class="eyebrow">{{ 'FIRST PLACE' if n==1 else 'SECOND PLACE' if n==2 else 'THIRD PLACE' }}</span></div><strong class="podium-name" data-empire-name="{{ n }}">{{ r.username if r else ('Unavailable' if n > empire_limit else 'Open position') }}</strong><div class="podium-values"><div><small>WAGERED</small><strong data-empire-wager="{{ n }}">{{ r.wager if r else '—' }}</strong></div><div><small>PRIZE</small><strong class="accent" data-empire-prize="{{ n }}">{{ r.prize if r and r.prize != '—' else (data.empiredrop.prizes.formatted[(r.rank if r else n)|string] if data.empiredrop.prizes.enabled else 'Not announced') }}</strong></div></div></article>
      {% endfor %}
      </div>
      <div class="panel public-table table-scroll" tabindex="0" role="region" aria-label="EmpireDrop leaderboard places four through ten"><table><thead><tr><th>Place</th><th>Player</th><th class="number">Wagered</th><th class="number">Prize</th></tr></thead><tbody id="empireRows">{% for n in range(4,11) %}{% set r = empire_rows[n-1] if empire_rows|length >= n else none %}<tr><td class="rank" data-empire-place="{{ n }}">{{ '%02d'|format(r.rank if r else n) }}</td><td data-empire-row-name="{{ n }}">{{ r.username if r else ('Unavailable' if n > empire_limit else 'Open position') }}</td><td class="number" data-empire-row-wager="{{ n }}">{{ r.wager if r else '—' }}</td><td class="number accent" data-empire-row-prize="{{ n }}">{{ r.prize if r and r.prize != '—' else (data.empiredrop.prizes.formatted[(r.rank if r else n)|string] if data.empiredrop.prizes.enabled else 'Not announced') }}</td></tr>{% endfor %}</tbody></table></div>
      <p id="empireRankingCoverage" class="public-coverage">{% if empire_limit < 10 %}EmpireDrop currently exposes {{ empire_limit }} official positions for this race.{% elif empire_rows|length < 10 %}Open positions will appear when activity is reported.{% endif %}</p>
      <details class="panel explanation" id="empireHistory"><summary>Previous EmpireDrop races <span aria-hidden="true">+</span></summary><div id="empireHistoryList" class="empire-history-list"><p class="small muted">No completed race snapshots saved yet.</p></div></details>
    </div>
    {# Server-render verified standings end #}
    <noscript><p class="notice">Reload to see the latest saved standings.</p></noscript>
  </section>

  <section class="panel public-games-cta" aria-labelledby="gamesCtaTitle"><div><p class="eyebrow">REDPOINTS GAMES</p><h2 id="gamesCtaTitle">Play with the community.</h2><p class="muted">See who is playing and follow the weekly RedPoints leaderboard.</p></div><a class="button primary" href="/gaming">Open RedPoints Games →</a></section>
</main>
{% endblock %}
{% block styles %}<link rel="stylesheet" href="{{ url_for('static',filename='empiredrop.css',v=asset_version) }}">{% endblock %}
{% block scripts %}<script src="{{ url_for('static', filename='empiredrop.js',v=asset_version) }}" defer></script>{% endblock %}
```

## `templates/login.html`

```html
{% extends 'base.html' %}{% block title %}Sign in · RedHunllef{% endblock %}
{% block navigation %}<a href="/">Back to the race ↗</a>{% endblock %}
{% block content %}<main id="main" class="shell login-wrap"><section class="panel login-panel"><div class="eyebrow"><span class="dot"></span> YOUR RACE. YOUR CONTROL.</div><h1>Welcome back<span class="accent">.</span></h1><p class="muted">Sign in to manage the race and your community.</p>
{% if error %}<p class="notice warning" role="alert">{{ error }}</p>{% endif %}
<form action="{{ url_for('login') }}" method="post" class="stack"><input type="hidden" name="csrf" value="{{ csrf() }}"><div class="field"><label for="username">Username</label><input id="username" name="username" autocomplete="username" required autofocus maxlength="64"></div><div class="field"><label for="password">Password</label><input id="password" name="password" type="password" autocomplete="current-password" required maxlength="256"></div><button class="button primary" type="submit">Sign in <span aria-hidden="true">→</span></button></form><p class="muted small">Administration only. Public visitors do not need an account.</p><span class="release">{{ release }}</span></section></main>{% endblock %}
{% block footer %}Private administration{% endblock %}
```

## `templates/macros.html`

```html
{% macro form_fields(action, tab, revision=0) -%}
<input type="hidden" name="csrf" value="{{ csrf() }}"><input type="hidden" name="action" value="{{ action }}"><input type="hidden" name="tab" value="{{ tab }}"><input type="hidden" name="revision" value="{{ revision }}">
{%- endmacro %}
{% macro field(key, label, value='', type='text', help='', error='', required=true, prefix='') -%}
<div class="field"><label for="f-{{ prefix }}{{ key }}">{{ label }}</label>{% if type == 'textarea' %}<textarea id="f-{{ prefix }}{{ key }}" name="{{ key }}" rows="3" {% if required %}required{% endif %} aria-describedby="help-{{ prefix }}{{ key }}">{{ value }}</textarea>{% else %}<input id="f-{{ prefix }}{{ key }}" name="{{ key }}" type="{{ type }}" {% if type=='password' %}autocomplete="{{ 'current-password' if key=='current_password' else 'new-password' }}"{% endif %} value="{{ value }}" {% if required %}required{% endif %} aria-describedby="help-{{ prefix }}{{ key }}" {% if error %}aria-invalid="true"{% endif %}>{% endif %}<small id="help-{{ prefix }}{{ key }}" class="{{ 'field-error' if error else 'muted' }}">{{ error or help }}</small></div>
{%- endmacro %}
{% macro player_rows(rows, tab='players') -%}
{% for row in rows %}<tr data-player="{{ row.username }}"><td class="rank">{{ '%02d'|format(row.rank) if row.rank else '—' }}</td><td><div class="name-cell"><strong>{{ row.username }}</strong><button type="button" class="copy-button js-only" data-copy="{{ row.username }}" aria-label="Copy {{ row.username }}">⧉</button></div>{% if row.source == 'override' %}<span class="tag">Adjusted</span>{% endif %}</td><td class="number accent">{{ row.wager }}</td><td class="number">{{ row.original_weighted_str }}</td><td class="number">{{ row.raw_wager_str }}</td><td><a class="text-link" href="{{ url_for('admin_shuffle_players_page',edit=row.username) }}#override">Edit</a></td></tr>{% else %}<tr><td colspan="6" class="empty">No matching qualifying wagers. Check the race dates and connection status.</td></tr>{% endfor %}
{%- endmacro %}
{% macro action_feedback(target) -%}
{% if admin_receipt and admin_receipt.target==target %}<p id="feedback-{{ target }}" class="notice success form-feedback saved-receipt" role="status" tabindex="-1"><strong>Saved.</strong> {{ admin_receipt.message }} <small>{{ fmt_et(admin_receipt.at) }}</small></p>{% endif %}
{%- endmacro %}
{% macro public_race_summary(container_id, label_id, badge_id, badge_class, badge_text, countdown_id, window_id, window_text, pool_id, pool_text, places, hidden=false, aria_label='Race schedule') -%}
<aside id="{{ container_id }}" class="race-clock panel public-race-summary"{% if hidden %} hidden{% endif %} aria-label="{{ aria_label }}">
  <div class="race-summary-top"><span class="eyebrow" id="{{ label_id }}">RACE SCHEDULE</span><span id="{{ badge_id }}" class="badge {{ badge_class }}">{{ badge_text }}</span></div>
  <div id="{{ countdown_id }}" class="clock race-countdown" aria-live="off">—</div>
  <p id="{{ window_id }}" class="muted race-date-range">{{ window_text }}</p>
  <div class="clock-footer"><span>Prize pool <strong class="accent" id="{{ pool_id }}">{{ pool_text }}</strong></span><span>{{ places }} paid places</span></div>
</aside>
{%- endmacro %}
```

## `templates/recovery_panel.html`

```html
<section class="panel form-panel" id="recovery"><p class="eyebrow">KEEP YOUR COMMUNITY'S PROGRESS</p><h2>Private recovery checkpoint</h2>
<div class="checkpoint-status"><strong id="checkpointLabel">{{ data.checkpoint.label }}</strong><p id="checkpointDetails">{{ data.checkpoint.details }}</p><small id="checkpointTime">{{ 'Last export generated: ' ~ fmt_et(data.checkpoint.generated_at) if data.checkpoint.generated_at else 'No export generated yet.' }}</small></div>
<p class="muted">Includes administrator accounts, password hashes, the signing key, race settings, saved standings, weekly history, RedPoints wallets, active hands, statistics, and fairness receipts. Keep this file private.</p>
<a class="button primary" href="/admin/recovery-backup" data-recovery-download>↓ Download private recovery file</a>
<p class="small muted">“Generated” means the server prepared a download. It does not confirm that you saved it elsewhere. On App Platform, add the latest file as <code>private/recovery.seed.json</code> to your private repository before redeploying. A new instance imports it automatically; existing saved state always wins. Local copies alone do not survive a container replacement.</p>
<details class="nested" {% if recovery_review %}open{% endif %}><summary>Check a recovery file before restoring <span aria-hidden="true">+</span></summary>
<form method="post" action="/admin/recovery-preview" enctype="multipart/form-data" class="filter-bar"><input type="hidden" name="csrf" value="{{ csrf() }}"><div class="field grow"><label for="recoveryFile">Private recovery JSON</label><input id="recoveryFile" name="recovery" type="file" accept=".json,application/json" required></div><button type="submit" class="button">Review recovery file</button></form>
{% if recovery_review %}<div class="recovery-review"><h3>Validated recovery file</h3><dl><dt>Race dates</dt><dd>{{ recovery_review.start }} → {{ recovery_review.end }}</dd><dt>Accounts</dt><dd>{{ recovery_review.accounts }} administrators</dd><dt>Race data</dt><dd>{{ recovery_review.rows }} saved places · {{ recovery_review.overrides }} overrides · {{ recovery_review.history }} archived races</dd><dt>RedPoints</dt><dd>{{ recovery_review.redpoints }} saved wallets, including active hands, fairness seeds and recent receipts</dd></dl>{% if recovery_review.comparison %}{% set c=recovery_review.comparison %}<h3>Compared with the current save</h3><div class="table-scroll"><table><thead><tr><th>Record</th><th>Current</th><th>Recovery file</th></tr></thead><tbody><tr><td>Administrator accounts</td><td>{{ c.accounts_before }}</td><td>{{ recovery_review.accounts }}</td></tr><tr><td>Player wallets</td><td>{{ c.wallets_before }}</td><td>{{ recovery_review.redpoints }}</td></tr><tr><td>Unfinished hands</td><td>{{ c.pending_before }}</td><td>{{ c.pending_after }}</td></tr></tbody></table></div><p>{{ c.wallets_added }} wallets added · {{ c.wallets_changed }} changed · {{ c.wallets_removed }} absent from this file.</p><p>{{ c.accounts_changed }} existing account records differ.{% if c.accounts_added %} Added: {{ c.accounts_added|join(', ') }}.{% endif %}{% if c.accounts_removed %} Absent: {{ c.accounts_removed|join(', ') }}.{% endif %}</p>{% endif %}<p class="small muted">This review changes nothing. To restore on a fresh deployment, place this file in <code>private/recovery.seed.json</code>. Use the separate race-backup restore form for replacing only a live race.</p></div>{% endif %}
</details></section>
```

## `static/admin-calendar.js`

```javascript
(() => {
  "use strict";
  if (document.body.dataset.page !== "admin") return;
  const fmt = new Intl.DateTimeFormat("en-US", {timeZone:"America/New_York", month:"short", day:"numeric", year:"numeric", hour:"numeric", minute:"2-digit", timeZoneName:"short"});
  const utcFmt = new Intl.DateTimeFormat("en-CA", {timeZone:"UTC", year:"numeric", month:"2-digit", day:"2-digit", hour:"2-digit", minute:"2-digit", hourCycle:"h23"});
  function partsAt(date) {
    return Object.fromEntries(new Intl.DateTimeFormat("en-US", {timeZone:"America/New_York", year:"numeric", month:"2-digit", day:"2-digit", hour:"2-digit", minute:"2-digit", second:"2-digit", hourCycle:"h23"}).formatToParts(date).filter(p=>p.type!=="literal").map(p=>[p.type,p.value]));
  }
  function easternToDate(value) {
    if (!/^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}$/.test(value)) return null;
    const [d,t]=value.split("T"), [y,m,day]=d.split("-").map(Number), [h,min]=t.split(":").map(Number);
    let guess=new Date(Date.UTC(y,m-1,day,h,min));
    for(let i=0;i<3;i++){
      const p=partsAt(guess); const represented=Date.UTC(+p.year,+p.month-1,+p.day,+p.hour,+p.minute);
      const wanted=Date.UTC(y,m-1,day,h,min); guess=new Date(guess.getTime()+(wanted-represented));
    }
    return guess;
  }
  function localValue(date) {
    const p=partsAt(date); return `${p.year}-${p.month}-${p.day}T${p.hour}:${p.minute}`;
  }
  function initialize(form) {
    const prefix=form.dataset.calendarForm === "empiredrop" ? "empire" : "shuffle";
    const hiddenStart=document.getElementById(prefix === "empire" ? "empireStart" : "start_et");
    const hiddenEnd=document.getElementById(prefix === "empire" ? "empireEnd" : "end_et");
    const dateStart=form.querySelector('[data-calendar-date="start"]'), timeStart=form.querySelector('[data-calendar-time="start"]');
    const dateEnd=form.querySelector('[data-calendar-date="end"]'), timeEnd=form.querySelector('[data-calendar-time="end"]');
    const preview=form.querySelector('[data-calendar-preview]'), utc=form.querySelector('[data-calendar-utc]');
    const mismatch=document.getElementById("empireScheduleMismatch");
    function sync() {
      const start=`${dateStart.value}T${timeStart.value}`, end=`${dateEnd.value}T${timeEnd.value}`;
      hiddenStart.value=start; hiddenEnd.value=end;
      const a=easternToDate(start), b=easternToDate(end), valid=a&&b&&b>a;
      preview.textContent=valid ? `${fmt.format(a)} → ${fmt.format(b)}` : "Choose an end after the start.";
      utc.textContent=valid ? `UTC: ${utcFmt.format(a)} → ${utcFmt.format(b)}` : "";
      preview.closest('.calendar-preview')?.classList.toggle('is-invalid', !valid);
      if (mismatch && form.dataset.calendarForm === "empiredrop") {
        const official=form.closest('.empire-schedule')?.querySelector('.official-schedule-card');
        const oa=official?.dataset.officialStart ? (/^\d+$/.test(official.dataset.officialStart) ? new Date(Number(official.dataset.officialStart)*1000) : new Date(official.dataset.officialStart)) : null;
        const ob=official?.dataset.officialEnd ? (/^\d+$/.test(official.dataset.officialEnd) ? new Date(Number(official.dataset.officialEnd)*1000) : new Date(official.dataset.officialEnd)) : null;
        mismatch.hidden=!(valid&&oa&&!Number.isNaN(oa.getTime())&&ob&&!Number.isNaN(ob.getTime()) && (Math.abs(a-oa)>60000 || Math.abs(b-ob)>60000));
      }
      return valid;
    }
    for (const node of [dateStart,timeStart,dateEnd,timeEnd]) node?.addEventListener('input',sync);
    form.addEventListener('submit', event => { if(!sync()){event.preventDefault(); preview.focus?.();} });
    form.addEventListener('reset', () => queueMicrotask(sync));
    form.querySelectorAll('[data-calendar-preset]').forEach(button=>button.addEventListener('click',()=>{
      const now=new Date(), p=partsAt(now);
      const weekday={Sun:0,Mon:1,Tue:2,Wed:3,Thu:4,Fri:5,Sat:6}[new Intl.DateTimeFormat('en-US',{timeZone:'America/New_York',weekday:'short'}).format(now)];
      const delta=(weekday-2+7)%7;
      const dayDate=new Date(Date.UTC(+p.year,+p.month-1,+p.day-delta));
      const y=dayDate.getUTCFullYear(), m=String(dayDate.getUTCMonth()+1).padStart(2,'0'), d=String(dayDate.getUTCDate()).padStart(2,'0');
      let start=easternToDate(`${y}-${m}-${d}T18:00`);
      if(button.dataset.calendarPreset==='next') start=new Date(start.getTime()+7*86400000);
      if(button.dataset.calendarPreset==='today') start=now;
      const end=new Date(start.getTime()+7*86400000);
      const sv=localValue(start), ev=localValue(end); dateStart.value=sv.slice(0,10);timeStart.value=sv.slice(11,16);dateEnd.value=ev.slice(0,10);timeEnd.value=ev.slice(11,16);sync();
    }));
    sync();
  }
  document.querySelectorAll('form[data-calendar-form]').forEach(initialize);
  document.getElementById('syncEmpireSchedule')?.addEventListener('click',()=>{
    const card=document.querySelector('.official-schedule-card'); const form=document.querySelector('form[data-calendar-form="empiredrop"]');
    if(!card||!form||!card.dataset.officialStart||!card.dataset.officialEnd) return;
    const startRaw=card.dataset.officialStart, endRaw=card.dataset.officialEnd;
    const a=/^\d+$/.test(startRaw) ? new Date(Number(startRaw)*1000) : new Date(startRaw);
    const b=/^\d+$/.test(endRaw) ? new Date(Number(endRaw)*1000) : new Date(endRaw);
    if(Number.isNaN(a.getTime())||Number.isNaN(b.getTime())) return;
    const av=localValue(a), bv=localValue(b); form.querySelector('[data-calendar-date="start"]').value=av.slice(0,10);form.querySelector('[data-calendar-time="start"]').value=av.slice(11,16);form.querySelector('[data-calendar-date="end"]').value=bv.slice(0,10);form.querySelector('[data-calendar-time="end"]').value=bv.slice(11,16);form.querySelector('[data-calendar-date="start"]').dispatchEvent(new Event('input',{bubbles:true}));
  });
})();
```

## `static/admin-empiredrop.js`

```javascript
/* Protected EmpireDrop-only admin panel. No raw keys are transmitted to the browser. */
(() => {
  'use strict';
  if (!document.getElementById('empireAdminTitle')) return;
  const id = x => document.getElementById(x);
  let pending = false, expired = false;
  const fmt = t => t ? new Intl.DateTimeFormat('en-US', {timeZone:'America/New_York', year:'numeric', month:'short', day:'numeric', hour:'numeric', minute:'2-digit', timeZoneName:'short'}).format(new Date(t*1000)) : 'Not yet verified';
  const render = data => {
    if (expired) return;
    id('empireAdminStatus').textContent = data.label || 'Awaiting verified EmpireDrop data';
    if (id('empireRaceSlug')) id('empireRaceSlug').textContent = data.race_meta?.slug || 'Not discovered';
    if (id('empireRaceMode')) id('empireRaceMode').textContent = (data.source_mode || 'races').toUpperCase();
    id('empireAdminConfirmed').textContent = fmt(data.updated_at);
    id('empireAdminAttempted').textContent = fmt(data.attempt_at);
    id('empireAdminChecking').textContent = data.checking ? 'Checking provider' : data.queued_at > data.attempt_at ? 'Refresh queued' : 'Idle';
    id('empireError').hidden = !data.error;
    id('empireError').textContent = data.error || '';
    // Show the provider's actual active race when automatic recovery occurs.
    const recovery = id('empireSlugRecovery');
    if (recovery) {
      recovery.hidden = !data.selection_warning;
      recovery.textContent = data.selection_warning || '';
    }
    const body = document.createDocumentFragment();
    (Array.isArray(data.rows) ? data.rows.slice(0,10) : []).forEach(r => {
      const tr = document.createElement('tr');
      for (const v of [String(r.rank).padStart(2,'0'), r.username, r.user_id || '—', r.wager, r.prize || '—']) {
        const td = document.createElement('td'); td.textContent = String(v ?? ''); tr.appendChild(td);
      }
      body.appendChild(tr);
    });
    if (!body.childNodes.length) {
      const tr = document.createElement('tr'); const td = document.createElement('td'); td.colSpan = 5;
      td.textContent = 'No ranked players returned for this race. A closed race or a new race may return an empty ranking.'; tr.appendChild(td); body.appendChild(tr);
    }
    id('empireAdminRows').replaceChildren(body);
    filterEmpirePlayers();
  };
  const clear = () => {
    expired = true; id('empireAdminRows').replaceChildren();
    id('empireAdminStatus').textContent = 'Admin session expired. Sign in again.';
    id('empireAdminConfirmed').textContent = 'Private data hidden';
    id('empireAdminAttempted').textContent = 'Private data hidden';
  };
  async function poll() {
    if (pending || document.hidden || expired) return;
    pending = true;
    try {
      const response = await fetch('/admin/empiredrop/status', {credentials:'same-origin', cache:'no-store'});
      if (response.status === 401 || response.status === 403) { clear(); return; }
      if (!response.ok) throw new Error('Status unavailable');
      render(await response.json());
    } catch { if (!expired) id('empireAdminStatus').textContent = 'Status request failed; last known results may be stale.'; }
    finally { pending = false; }
  }
  const test = id('testEmpireConnection');
  if (test) test.addEventListener('click', async () => {
    test.disabled = true;
    id('empireTestResult').textContent = 'Testing official EmpireDrop connection without saving any wagers…';
    try {
      const response = await fetch('/admin/empiredrop/test', {
        method:'POST', credentials:'same-origin', cache:'no-store',
        headers:{'X-CSRF-Token':test.dataset.csrf, 'Accept':'application/json'}
      });
      if (response.status === 401 || response.status === 403) { clear(); return; }
      const value = await response.json();
      id('empireTestResult').textContent = (value.ok ? 'Confirmed: ' : 'Not connected: ') + (value.message || 'No result');
    } catch { id('empireTestResult').textContent = 'Unable to complete the test.'; }
    finally { test.disabled = false; }
  });
  // Diagnostic requests only return race IDs and field *names*, not player values
  // or API credentials. They use the same CSRF/session protections as admin.
  async function inspectRace(buttonId, path, payload = null) {
    const button = id(buttonId), panel = id('empireRaceDiagnostics');
    if (!button || !panel) return;
    button.disabled = true;
    panel.textContent = 'Contacting the EmpireDrop races API…';
    try {
      const response = await fetch(path, {
        method: 'POST', credentials: 'same-origin', cache: 'no-store',
        headers: {'Accept':'application/json', 'Content-Type':'application/json',
                  'X-CSRF-Token': button.dataset.csrf},
        body: JSON.stringify(payload || {})
      });
      if (response.status === 401 || response.status === 403) { clear(); return; }
      const body = await response.json();
      // Never interpolate response data as HTML; textContent prevents injection.
      panel.textContent = JSON.stringify(body, null, 2);
      // Race slugs from the API are offered as a selection helper, never
      // written to settings until the admin clicks Save below.
      const choices = id('empireDiscoveredSlugs');
      if (choices && path.endsWith('/discover')) {
        choices.replaceChildren();
        const races = body.ok && Array.isArray(body.races) ? body.races : [];
        if (races.length) {
          const select = document.createElement('select');
          select.id = 'empireDiscoveredRaceSelect';
          const placeholder = document.createElement('option');
          placeholder.value = ''; placeholder.textContent = 'Choose a race from the verified list';
          select.appendChild(placeholder);
          races.forEach(r => {
            const option = document.createElement('option');
            option.value = r.slug;
            option.textContent = (r.name || r.slug) + ' · ' + r.slug;
            select.appendChild(option);
          });
          const use = document.createElement('button');
          use.type = 'button'; use.className = 'button';
          use.textContent = 'Use selected race (not saved yet)';
          use.addEventListener('click', () => {
            if (!select.value) return;
            id('empireRaceSlugInput').value = select.value;
            id('empireRaceSlugInput').focus();
          });
          choices.append(select, use);
        } else {
          choices.textContent = 'No running races were returned. Finished and scheduled races are intentionally excluded.';
        }
      }
    } catch {
      panel.textContent = 'Race endpoint request failed. See server logs for a safe error classification.';
    } finally { button.disabled = false; }
  }
  id('empireDiscover')?.addEventListener('click', () =>
    inspectRace('empireDiscover', '/admin/empiredrop/discover'));
  id('empireProbe')?.addEventListener('click', () =>
    inspectRace('empireProbe', '/admin/empiredrop/probe',
                {slug: id('empireRaceSlugInput')?.value?.trim() || ''}));
  document.addEventListener('visibilitychange', () => { if (!document.hidden) poll(); });
  window.setInterval(poll, 15000);
})();

/* Prize preview is purely client-side: saving validates all ten amounts server-side. */
(() => {
  const form = document.querySelector('form[action="/admin/empiredrop/rewards"]');
  if (!form) return;
  const output = document.getElementById('empireRewardTotal');
  function preview() {
    let total = 0;
    for (let i=1;i<=10;i++) {
      const input = form.querySelector(`[name="prize_${i}"]`);
      const n = Number(input?.value);
      if (!Number.isFinite(n) || n<0) { output.textContent = 'Check amount for place '+i;return; }
      total += n;
    }
    const currency = form.querySelector('[name="currency"]').value;
    output.textContent = new Intl.NumberFormat('en-US', {style:'currency',currency}).format(total);
  }
  const status = document.getElementById('empireRewardSaveState');
  const original = new FormData(form);
  const baseline = JSON.stringify([...original].filter(([key]) => !['csrf'].includes(key)));
  function state() {
    const current = JSON.stringify([...new FormData(form)].filter(([key]) => !['csrf'].includes(key)));
    if (status) status.textContent = current === baseline ? 'No unsaved changes' : 'Unsaved prize changes';
  }
  form.addEventListener('input',()=>{preview();state();});
  form.addEventListener('change',()=>{preview();state();});
  let submitting = false;
  form.addEventListener('submit',event=>{
    if (submitting) { event.preventDefault(); return; }
    const submitter = event.submitter;
    const mode = submitter?.value === 'publish' ? 'publish' : 'draft';
    // Disabled submit buttons are omitted from native form serialization.
    // Persist the click intent in a hidden field before locking the buttons so
    // Save & publish cannot silently arrive at the server as Save draft.
    const intent = form.querySelector('[name="save_mode_intent"]');
    if (intent) intent.value = mode;
    submitting = true;
    form.setAttribute('aria-busy','true');
    const publish = mode === 'publish';
    if (status) status.textContent = publish ? 'Saving and verifying public prizes…' : 'Saving draft…';
    for (const button of form.querySelectorAll('[data-payout-submit]')) {
      button.disabled = true;
      if (button === submitter) button.textContent = publish ? 'Publishing…' : 'Saving…';
    }
  });
  preview();state();
})();

/* Local search over the admin-only provider names and stable public IDs. */
function filterEmpirePlayers() {
  const input = document.getElementById('empireAdminSearch');
  const body = document.getElementById('empireAdminRows');
  if (!input || !body) return;
  const q = input.value.trim().toLocaleLowerCase();
  for (const tr of body.querySelectorAll('tr')) {
    tr.hidden = q !== '' && !tr.textContent.toLocaleLowerCase().includes(q);
  }
}
// The common admin-providers.js controller attaches the input event.
// filterEmpirePlayers() is still used after each live table refresh.
```

## `static/admin-feedback.js`

```javascript
/* Keep a rejected form and its selected files intact. Native forms still work.
   Preview/review workflows remain native; only a committed write redirects. */
(() => {
  "use strict";
  if (document.body.dataset.page !== "admin") return;
  const receipt = document.querySelector(".saved-receipt");
  if (receipt) {
    for (
      let parent = receipt.parentElement;
      parent;
      parent = parent.parentElement
    )
      if (parent.tagName === "DETAILS") parent.open = true;
    receipt.focus({ preventScroll: true });
    receipt.scrollIntoView?.({ block: "center" });
  }
  for (const form of document.querySelectorAll('form[method="post"]')) {
    const endpoint = form.getAttribute("action");
    if (
      ![
        "/admin/action",
        "/admin/history/refresh",
      ].includes(endpoint) ||
      form.hasAttribute("data-refresh")
    )
      continue;
    const action = form.elements.namedItem("action")?.value;
    if (["save_race", "preview_restore"].includes(action)) continue;
    let busy = false;
    form.addEventListener("submit", async (event) => {
      if (event.defaultPrevented) return; // Respect the existing confirmation.
      event.preventDefault();
      if (busy) return;
      const data = new FormData(form);
      const button =
        event.submitter || form.querySelector('button[type="submit"]');
      if (button?.name) data.set(button.name, button.value);
      const label = button?.textContent.trim() || "Save change";
      let feedback = form.querySelector("[data-form-feedback]");
      if (!feedback) {
        feedback = document.createElement("p");
        feedback.dataset.formFeedback = "";
        feedback.setAttribute("role", "status");
        feedback.tabIndex = -1;
        form.append(feedback);
      }
      feedback.className = "form-feedback notice";
      feedback.textContent = label + ": saving…";
      busy = true;
      const controls = [...form.querySelectorAll('button[type="submit"]')];
      const prior = controls.map((node) => node.disabled);
      controls.forEach((node) => {
        node.disabled = true;
      });
      const controller = new AbortController();
      const timeout = setTimeout(() => controller.abort(), 15000);
      try {
        const response = await fetch(endpoint, {
          method: "POST",
          body: data,
          credentials: "same-origin",
          headers: { Accept: "application/json" },
          signal: controller.signal,
        });
        if (!response.headers.get("content-type")?.includes("application/json"))
          throw Error(
            "Unexpected response. Check the installed release before retrying.",
          );
        const result = await response.json();
        if (!response.ok || !result.ok)
          throw Error(
            (result.error || "The server did not confirm this change.") +
              (result.request_id ? ` Reference: ${result.request_id}.` : ""),
          );
        const next = new URL(result.redirect, location.origin);
        if (
          next.origin !== location.origin ||
          !next.pathname.startsWith("/admin")
        )
          throw Error(
            "Save confirmed, but the return link is invalid. Reload to verify the saved value.",
          );
        feedback.className = "form-feedback notice success";
        feedback.textContent = result.message;
        document.dispatchEvent(
          new CustomEvent("admin:saved", { detail: { form } }),
        );
        if (next.pathname === location.pathname && next.search === location.search) {
          // A fragment-only navigation does not request a new document. Reload
          // after a confirmed save so receipts and edit revisions are current.
          history.replaceState(history.state, "", next.href);
          location.reload();
        } else {
          location.assign(next.href);
        }
      } catch (error) {
        feedback.className = "form-feedback notice warning";
        feedback.textContent =
          label +
          ": " +
          (error.name === "AbortError"
            ? "No confirmation received. Your draft is kept; verify the saved value before retrying."
            : error.message);
        feedback.focus({ preventScroll: true });
      } finally {
        clearTimeout(timeout);
        busy = false;
        controls.forEach((node, index) => {
          node.disabled = prior[index];
        });
      }
    });
  }
})();
```

## `static/admin-gaming.js`

```javascript
/* Admin-only local stats. No calls to Shuffle and no extra provider work. */
(() => {
  "use strict";
  const root = document.getElementById("gamingAdmin");
  if (!root) return;
  const id = (name) => document.getElementById(name),
    fmt = (n) => Number(n).toLocaleString("en-US");
  let timer,
    busy = false,
    etag = "",
    season = 0,
    revision = -1,
    granting = false,
    expired = false;
  const rowKeys = new Map();
  function render(data) {
    if (expired) return;
    if (
      Number(data.season.id) < season ||
      (Number(data.season.id) === season && data.revision < revision)
    )
      return;
    season = Number(data.season.id);
    revision = data.revision;
    id("gamingAdminReset").textContent = `Weekly reset: ${data.season.end_et}.`;
    const publicActivity = data.public_activity || {};
    id("gamingAdminSummary").textContent =
      `Players: ${fmt(data.player_count)} · Rounds: ${fmt(data.completed_rounds)} · Active hands: ${fmt(data.active_hands)} · Publicly active: ${fmt(publicActivity.active_count || 0)}`;
    if (id('gamingPublicActive')) id('gamingPublicActive').textContent = fmt(publicActivity.active_count || 0);
    if (id('gamingPublicLeadersCount')) id('gamingPublicLeadersCount').textContent = fmt((publicActivity.weekly_leaders || []).length);
    if (id('gamingPublicRevision')) id('gamingPublicRevision').textContent = fmt(publicActivity.revision || 0);
    const grant = data.last_grant;
    id("gamingLastGrant").textContent = grant
      ? `Last grant: ${grant.actor} · +${fmt(grant.amount)} each · ${fmt(grant.players)} ${grant.players === 1 ? "wallet" : "wallets"} · ${new Date(grant.at * 1000).toLocaleString()}`
      : "No admin points grant has been saved yet.";
    id("gamingNoRecords").hidden = data.completed_rounds > 0;
    if (typeof data.visitor_ip_configured === "boolean")
      id("gamingIpWarning").hidden = data.visitor_ip_configured;
    for (const [game, rows] of Object.entries({
      ...data.games,
      video_poker: data.legacy_poker || [],
    })) {
      const list = id("gamingLeaders-" + game);
      if (!list) continue;
      const count =
        game === "video_poker" ? data.legacy_poker_counts : data.counts?.[game];
      if (count) {
        id("gamingCount-" + game).textContent =
          `Players: ${fmt(count.players)} · Completed rounds: ${fmt(count.rounds)}`;
      }
      const key = JSON.stringify(rows);
      if (rowKeys.get(game) === key) continue;
      rowKeys.set(game, key);
      // Preserve open records and keyboard focus when a score changes.
      const open = new Set(
        [...list.querySelectorAll("details[open]")].map(
          (node) => node.closest("[data-player-key]").dataset.playerKey,
        ),
      );
      const focused = list.contains(document.activeElement)
        ? document.activeElement.closest("[data-player-key]")?.dataset.playerKey
        : null;
      list.replaceChildren(
        ...(rows.length
          ? rows.map((row, index) => {
              const item = document.createElement("li"),
                detail = document.createElement("details"),
                summary = document.createElement("summary");
              item.dataset.playerKey = game + ":" + row.player_tag;
              item.dataset.tone =
                row.net > 0 ? "positive" : row.net < 0 ? "negative" : "neutral";
              detail.className = "player-breakdown";
              detail.open = open.has(item.dataset.playerKey);
              const name = document.createElement("span"),
                rank = document.createElement("small"),
                label = document.createElement("strong"),
                score = document.createElement("b"),
                unit = document.createElement("small");
              name.className = "leader-name";
              rank.textContent = index + 1;
              label.textContent = row.name;
              name.append(rank, label);
              score.textContent = `${row.net >= 0 ? "+" : ""}${fmt(row.net)} `;
              unit.textContent = "RP";
              score.append(unit);
              summary.append(name, score);
              const record = document.createElement("div");
              record.className = "player-record";
              for (const value of [
                `${fmt(row.paid)} returned · ${fmt(row.wagered)} wagered · ${row.bets} rounds`,
                `${fmt(row.balance)} available RP · player ${row.player_tag}`,
                `IPs: ${row.ips.join(", ") || "Not linked this week yet"}`,
                `Funding adjustments: ${(row.funding_adjustment || 0) >= 0 ? "+" : ""}${fmt(row.funding_adjustment || 0)} RP · excluded from winnings`,
                `Public Gaming name: ${row.public_visibility ? "Visible" : "Hidden"}${row.last_game ? ` · last game ${row.last_game === "poker" ? "Hold’em" : row.last_game}` : ""}${row.last_action_at ? ` · ${new Date(row.last_action_at * 1000).toLocaleString()}` : ""}`,
              ]) {
                const node = document.createElement("small");
                node.textContent = value;
                record.append(node);
              }
              detail.append(summary, record);
              item.append(detail);
              return item;
            })
          : [
              Object.assign(document.createElement("li"), {
                className: "muted",
                textContent: "No completed rounds this week.",
              }),
            ]),
      );
      if (focused)
        [...list.children]
          .find((node) => node.dataset.playerKey === focused)
          ?.querySelector("summary")
          ?.focus({ preventScroll: true });
    }
  }
  function clearPrivateRankings() {
    // A late response from the shared admin feed must not reveal these again.
    expired = true;
    rowKeys.clear();
    etag = "";
    clearTimeout(timer);
    root.removeAttribute("data-rankings");
    root
      .querySelectorAll('[id^="gamingLeaders-"]')
      .forEach((list) => list.replaceChildren());
    root.querySelectorAll('[id^="gamingCount-"]').forEach((node) => {
      node.textContent = "Sign in to view statistics.";
    });
    id("gamingAdminSummary").textContent = "Private player information hidden.";
    id("gamingAdminSession").hidden = false;
    id("gamingNoRecords").hidden = true;
    id("gamingIpWarning").hidden = true;
    id("grantGamingButton").disabled = true;
    id("gamingGrantMessage").textContent = "Sign in again to grant points.";
    id("gamingLastGrant").textContent = "Sign in to view grant history.";
  }
  async function giveEveryone(event) {
    event.preventDefault();
    if (granting || expired) return;
    granting = true;
    const button = id("grantGamingButton"),
      form = event.currentTarget;
    button.disabled = true;
    id("gamingGrantMessage").textContent = "Saving the grant to every wallet…";
    const controller = new AbortController(),
      timeout = setTimeout(() => controller.abort(), 15000);
    try {
      // Keep the same request ID after failures, including a lost response.
      // The server remembers it so retrying cannot credit the grant twice.
      const response = await fetch(form.action, {
        method: "POST",
        body: new FormData(form),
        credentials: "same-origin",
        cache: "no-store",
        headers: { Accept: "application/json" },
        signal: controller.signal,
      });
      if (response.status === 401 || response.status === 403) {
        clearPrivateRankings();
        throw Error("Sign in again to grant points.");
      }
      if (!response.headers.get("content-type")?.includes("application/json"))
        throw Error(
          "Unexpected response. Reload the admin panel and check the last grant.",
        );
      const value = await response.json();
      if (!response.ok || !value.ok)
        throw Error(value.error || "The grant was not saved.");
      if (expired) return;
      if (value.release !== document.body.dataset.release)
        throw Error(
          "The release changed. Reload and check the last grant before continuing.",
        );
      render(value);
      etag = "";
      form.elements.namedItem("request_id").value = value.next_request_id;
      id("gamingGrantMessage").textContent = value.message;
    } catch (error) {
      id("gamingGrantMessage").textContent =
        error.name === "AbortError"
          ? "Response timed out. You can retry this same grant safely; it will not be added twice."
          : error.message;
    } finally {
      clearTimeout(timeout);
      granting = false;
      button.disabled = expired;
    }
  }
  async function refresh() {
    clearTimeout(timer);
    if (busy || expired || document.hidden) return;
    busy = true;
    id("refreshGaming").disabled = true;
    const controller = new AbortController(),
      timeout = setTimeout(() => controller.abort(), 10000);
    try {
      const response = await fetch("/admin/gaming/status", {
        credentials: "same-origin",
        cache: "no-store",
        signal: controller.signal,
        headers: {
          Accept: "application/json",
          ...(etag ? { "If-None-Match": etag } : {}),
        },
      });
      if (response.status === 401 || response.status === 403) {
        clearPrivateRankings();
        throw Error("Sign in again to view gaming statistics.");
      }
      if (response.status !== 304) {
        if (
          !response.ok ||
          !response.headers.get("content-type")?.includes("application/json")
        )
          throw Error("Stats are delayed. Saved rankings remain visible.");
        const value = await response.json();
        if (value.release && value.release !== document.body.dataset.release)
          throw Error(
            "The server release changed. Reload this page to use the matching gaming dashboard.",
          );
        render(value);
        etag = response.headers.get("etag") || "";
      }
      id("gamingAdminChecked").textContent =
        "Updated " + new Date().toLocaleTimeString() + "";
    } catch (error) {
      id("gamingAdminChecked").textContent =
        error.name === "AbortError"
          ? "Update timed out; retrying automatically."
          : error.message;
    } finally {
      clearTimeout(timeout);
      busy = false;
      id("refreshGaming").disabled = expired;
      if (!document.hidden && !expired) timer = setTimeout(refresh, 5000);
    }
  }
  globalThis.RedGamingAdmin = { render };
  document.addEventListener("admin:expired", clearPrivateRankings);
  render(JSON.parse(root.dataset.rankings));
  root.removeAttribute("data-rankings");
  id("refreshGaming").addEventListener("click", refresh);
  id("grantGamingForm").addEventListener("submit", giveEveryone);
  document.addEventListener("visibilitychange", () => {
    clearTimeout(timer);
    if (!document.hidden) void refresh();
  });
  void refresh();
})();
```

## `static/admin-health.js`

```javascript
/* The minute feed owns provider and storage health. No extra provider requests are created here. */
(() => {
  "use strict";
  const root = document.getElementById("systemHealth");
  if (!root) return;
  const id = (name) => document.getElementById(name);
  const put = (node, value) => {
    if (node && node.textContent !== String(value)) node.textContent = value;
  };
  const date = (value) =>
    value ? new Date(value * 1000).toLocaleString() : "Not recorded";
  let health,
    issueKey = "",
    metricsKey = "";
  function attention() {
    const issues = (health?.components || []).filter(
      (item) => item.state !== "good",
    );
    // A failed save is one incident, even though both Games and Saved data report it.
    const shown = issues.filter(
      (item) =>
        item.key !== "games" ||
        !issues.some((other) => other.key === "storage"),
    );
    const key = JSON.stringify(shown.map((item) => [item.key, item.state]));
    const network = id("networkError") && !id("networkError").hidden;
    id("adminAttention").dataset.state =
      network || shown.length ? "warning" : "good";
    put(
      id("attentionSummary"),
      network
        ? "Dashboard updates delayed"
        : shown.length
          ? "Needs attention"
          : "Everything is connected",
    );
    if (key === issueKey) return;
    issueKey = key;
    const list = id("adminIssueList");
    list.hidden = !shown.length;
    list.replaceChildren(
      ...shown.map((item) => {
        const li = document.createElement("li");
        li.textContent =
          item.label +
          ": " +
          (["storage", "games"].includes(item.key)
            ? "Saving unavailable. Check storage before making changes."
            : "Updates delayed. Saved results remain visible; retrying automatically.");
        return li;
      }),
    );
  }
  function render(value) {
    if (!value?.components) return;
    health = value;
    for (const item of value.components) {
      const card = [...root.querySelectorAll("[data-health-card]")].find(
        (node) => node.dataset.healthCard === item.key,
      );
      if (!card) continue;
      card.dataset.state = item.state;
      put(card.querySelector("[data-health-status]"), item.status);
      put(card.querySelector("[data-health-detail]"), item.detail);
      put(
        card.querySelector("[data-health-time]"),
        item.last_success
          ? "Confirmed " + date(item.last_success)
          : "Waiting for first confirmation",
      );
    }
    attention();
    const m = value.metrics,
      s = m.storage;
    const items = [
      [
        "Request p95",
        m.latency.samples ? m.latency.p95_ms + " ms" : "Collecting",
      ],
      ["Save p95", s.write.samples ? s.write.p95_ms + " ms" : "Collecting"],
      ["Lock wait p95", s.lock_wait.p95_ms + " ms"],
      ["State file", (s.bytes / 1048576).toFixed(2) + " MB"],
      ["Server errors", String(m.server_errors)],
      ["Last save", date(s.last_write)],
    ];
    const key = JSON.stringify(items);
    if (key === metricsKey) return;
    metricsKey = key;
    id("healthMetrics").replaceChildren(
      ...items.map(([label, text]) => {
        const node = document.createElement("div"),
          name = document.createElement("span"),
          count = document.createElement("strong");
        name.textContent = label;
        count.textContent = text;
        node.append(name, count);
        return node;
      }),
    );
  }
  globalThis.RedHealth = { render, attention };
  render(JSON.parse(root.dataset.health));
  id("copyHealthReport").addEventListener("click", async (event) => {
    const feedback = id("healthReportFeedback"),
      button = event.currentTarget;
    button.disabled = true;
    try {
      const response = await fetch("/admin/health-report", {
        headers: { Accept: "application/json" },
        credentials: "same-origin",
        cache: "no-store",
        signal: AbortSignal.timeout(10000),
      });
      if ([401, 403].includes(response.status))
        throw Error("Sign in again to get a current report.");
      if (!response.ok) throw Error("Report unavailable. Check runtime logs.");
      const report = JSON.stringify(await response.json(), null, 2);
      try {
        await navigator.clipboard.writeText(report);
        feedback.textContent =
          "Support report copied. No private player data or credentials included.";
      } catch {
        const url = URL.createObjectURL(
          new Blob([report], { type: "application/json" }),
        );
        const link = document.createElement("a");
        link.href = url;
        link.download = "redhunllef-support.json";
        link.click();
        setTimeout(() => URL.revokeObjectURL(url), 1000);
        feedback.textContent =
          "Clipboard unavailable. The support report was downloaded instead.";
      }
    } catch (error) {
      feedback.textContent = error.message;
    } finally {
      button.disabled = false;
      feedback.hidden = false;
    }
  });
})();
```

## `static/admin-logs.js`

```javascript
/* Text-only operational log viewer. Never render provider messages as HTML.
   This calls the local ADMIN endpoint only; provider APIs are not polled here. */
(() => {
  'use strict';
  const wrap=document.getElementById('adminOperations');
  if (!wrap) return;
  const id=name=>document.getElementById(name);
  const names={
    refresh_ok:'Source data confirmed',refresh_failed:'Source refresh failed',
    refresh_queued:'Manual refresh queued',settings_saved:'Settings saved',
    connection_test:'API connection tested',backup_export:'Backup downloaded',
    storage_warning:'State storage warning',server_error:'Server request failed',
    worker_started:'Automatic worker started',api_rate_limited:'Rate limit reached',
    data_quality:'Source data quality warning',
    empire_rewards_draft:'EmpireDrop prize draft saved',
    empire_rewards_published:'EmpireDrop prizes published',
    empire_rewards_save_failed:'EmpireDrop prize update rejected'
  };
  const advice={
    access:'Check credentials and permitted server IP addresses.',
    rate_limit:'The provider is limiting requests; automatic retries are scheduled.',
    format:'The provider response format did not match the expected schema.',
    scope:'The selected race is unavailable to this affiliate account.',
    selection:'Choose a race slug when more than one race is running.',
    window:'The provider identified a date parameter problem. Review the saved race window.',
    bad_request:'Shuffle rejected a request parameter (HTTP 400). Verify the dates and affiliate endpoint.',
    configuration:'Review the provider connection settings.',
    connection:'Check the server’s outgoing network connection.',
    connect_timeout:'The provider connection timed out.',
    timeout:'The provider did not answer before the timeout.',
    http:'The provider returned a non-success status.',
    upstream:'The provider’s service is temporarily unavailable.',
    response_limit:'The provider response exceeded limits.',
    redirect:'The provider redirected the request; credentials were not forwarded.',
    credentials:'A required server credential is missing.',
    partial:'Some source rows were incomplete.',
    storage:'Saved data could not be written.',
    empire_settings:'EmpireDrop race connection settings updated.',
    empire_rewards:'EmpireDrop prizes updated.',
    empire_schedule:'EmpireDrop dates updated.',
    shuffle_settings:'Shuffle configuration updated.',
    conflict:'Another tab saved a newer payout revision. Reload before retrying.',
    validation:'One or more payout values were rejected before saving.',
  };
  const when=value=>new Intl.DateTimeFormat('en-US',{
    timeZone:'America/New_York',month:'short',day:'numeric',hour:'numeric',minute:'2-digit',second:'2-digit',timeZoneName:'short'
  }).format(new Date(Number(value)*1000));
  let busy=false, lastEvents=[], lastSummary=null;
  const select=()=>new URLSearchParams({service:id('opsSource').value,level:id('opsLevel').value,limit:'300'});
  const query=()=>select().toString();
  const downloads=()=>{
    id('opsExport').href='/admin/operations/export?'+query();
    id('opsExportTxt').href='/admin/operations/export?'+query()+'&format=txt';
  };
  function text(node,value){node.textContent=String(value);return node;}
  function make(tag,className,value) {
    const node=document.createElement(tag);
    if(className) node.className=className;
    if(value!==undefined) text(node,value);
    return node;
  }
  function draw(events,summary){
    lastEvents=events;lastSummary=summary;
    for (const level of ['success','info','warning','error'])
      text(id('opsTotal'+level.charAt(0).toUpperCase()+level.slice(1)),summary?.levels?.[level]??0);
    text(id('opsTotalEvents'),summary?.total??events.length);
    const term=id('opsSearch').value.trim().toLocaleLowerCase();
    const rows=events.filter(entry=>!term||[entry.event,entry.service,entry.level,entry.code||'',
      String(entry.http_status||'')].join(' ').toLocaleLowerCase().includes(term));
    const out=id('opsEvents');out.replaceChildren();
    for(const item of rows){
      const article=make('article','operations-entry');article.role='listitem';article.dataset.severity=item.level;
      const severity=make('span','operations-severity',item.level.toUpperCase());
      const body=make('div','operations-entry-main');
      const heading=make('div','operations-entry-heading');
      heading.append(make('strong','',names[item.event]||'Operational activity'),
        make('time','',when(item.at)));
      const extras=[item.service.charAt(0).toUpperCase()+item.service.slice(1)];
      if(item.http_status!=null) extras.push('HTTP '+item.http_status);
      if(item.duration_ms!=null) extras.push(item.duration_ms+' ms');
      if(item.count!=null) extras.push(item.count+' ranked');
      if(item.received!=null) extras.push(item.received+' received');
      if(item.accepted!=null) extras.push(item.accepted+' accepted');
      if(item.excluded!=null) extras.push(item.excluded+' excluded');
      if(item.unscoped!=null) extras.push(item.unscoped+' without campaign');
      if(Number(item.occurrences)>1) {
        extras.push('Repeated '+item.occurrences+' times');
        if(item.first_at && item.first_at !== item.at) extras.push('First '+when(item.first_at));
      }
      body.append(heading,make('small','operations-details',extras.join(' · ')));
      if(item.code&&advice[item.code])body.append(make('p','operations-advice',advice[item.code]));
      article.append(severity,body);out.append(article);
    }
    text(id('opsMessage'),rows.length ? `Showing ${rows.length} of ${events.length} matching stored events.` :
      'No matching events. Try another filter.');
  }
  async function load(){
    if(busy||!wrap.open||document.hidden)return;
    busy=true;downloads();text(id('opsMessage'),'Loading recent events…');
    try{
      const response=await fetch('/admin/operations/events?'+query(),{
        credentials:'same-origin',cache:'no-store',headers:{Accept:'application/json'}
      });
      if([401,403].includes(response.status))throw new Error('Session expired. Sign in again.');
      if(!response.ok)throw new Error('Activity could not be loaded. Check the server status.');
      const payload=await response.json();
      draw(Array.isArray(payload.events)?payload.events:[],payload.summary);
    }catch(err){text(id('opsMessage'),err.message||'Logs are unavailable.');}
    finally{busy=false;}
  }
  wrap.addEventListener('toggle',load);
  for(const el of [id('opsSource'),id('opsLevel')])el.addEventListener('change',load);
  id('opsSearch').addEventListener('input',()=>draw(lastEvents,lastSummary));
  id('opsReload').addEventListener('click',load);
  document.addEventListener('visibilitychange',()=>{if(!document.hidden&&wrap.open)load();});
  window.setInterval(()=>{if(wrap.open&&!document.hidden)load();},30000);
  downloads();if(wrap.open)load();
})();
```

## `static/admin-providers.js`

```javascript
/* Shared admin source cards. Status comes from the existing /admin/status feed;
   this file NEVER makes additional Shuffle or EmpireDrop API requests. */
(() => {
  'use strict';
  const fmt = timestamp => Number(timestamp) > 0
    ? new Intl.DateTimeFormat('en-US', {timeZone:'America/New_York',year:'numeric',month:'short',day:'numeric',hour:'numeric',minute:'2-digit',timeZoneName:'short'}).format(new Date(timestamp*1000))
    : 'Not verified yet';
  const set = (selector, value) => {
    for (const node of document.querySelectorAll(selector)) node.textContent = String(value);
  };
  function render(payload) {
    if (!payload?.providers) return;
    for (const name of ['shuffle','empiredrop']) {
      const item = payload.providers[name];
      if (!item) continue;
      for (const node of document.querySelectorAll(`[data-provider-state="${name}"]`)) {
        node.dataset.state = item.state;
        node.textContent = item.status;
      }
      const fields = {last_success:fmt(item.last_success),last_attempt:item.last_attempt ? fmt(item.last_attempt) : 'Not attempted',
        participants:item.participants,quality:item.quality,metric:item.metric,cadence:`Every ${item.refresh_seconds} seconds`};
      for (const [key,value] of Object.entries(fields))
        set(`[data-provider-field="${name}:${key}"]`, value);
      const wrapper = document.querySelector(`[data-provider-issues="${name}"]`);
      if (wrapper) {
        const issues = Array.isArray(item.issues) ? item.issues : [];
        wrapper.hidden = issues.length === 0;
        const list = wrapper.querySelector('ul');
        if (list) list.replaceChildren(...issues.map(message=>{
          const row=document.createElement('li'); row.textContent=message; return row;
        }));
      }
    }
  }
  // Table searches filter only the visible loaded records, not the entire provider.
  document.querySelectorAll('[data-provider-search]').forEach(input => {
    const body = document.getElementById(input.dataset.providerSearch);
    if (!body) return;
    input.addEventListener('input', () => {
      const query=input.value.trim().toLocaleLowerCase();
      for (const row of body.querySelectorAll('tr'))
        row.hidden = Boolean(query && !row.textContent.toLocaleLowerCase().includes(query));
    });
  });
  globalThis.RedProviderCards = {render};
})();
```

## `static/admin-workspace.css`

```css
/* RedHunllef control center v5 — shared admin-only design system.
   Deliberately scoped to [data-page="admin"] so public gameplay and leaderboards
   retain their tested styles. No remote fonts, frameworks or dependencies. */
body[data-page="admin"] {
  --admin-background:#100f14;
  --admin-sidebar:#15141b;
  --admin-card:#1d1b24;
  --admin-border:#37333e;
  --admin-soft:#bbb3c2;
  --admin-red:#eb4054;
  --admin-redwash:rgba(235,64,84,.11);
  background:var(--admin-background);
  color:#f5f3f7;
}
body[data-page="admin"] .site-header {display:none}
body[data-page="admin"] .admin-app {display:flex;min-height:100svh;width:100%;isolation:isolate}
body[data-page="admin"] .admin-sidebar {
  position:sticky;top:0;flex:0 0 250px;width:250px;height:100svh;display:flex;flex-direction:column;
  padding:24px 13px 15px;background:var(--admin-sidebar);border-right:1px solid var(--admin-border);
  overflow-y:auto;scrollbar-width:thin;z-index:51;
}
body[data-page="admin"] .admin-sidebar-head {display:flex;align-items:center;justify-content:space-between;margin-bottom:31px;padding:0 10px}
body[data-page="admin"] .admin-brand {display:flex;align-items:center;gap:11px;text-decoration:none;color:inherit;min-width:0}
body[data-page="admin"] .admin-brand img {border-radius:9px;object-fit:contain}
body[data-page="admin"] .admin-brand strong {display:block;font-size:1rem;letter-spacing:-.02em}
body[data-page="admin"] .admin-brand small {display:block;font-size:.71rem;color:var(--admin-soft);margin-top:1px;letter-spacing:.03em}
body[data-page="admin"] .admin-sidebar-caption {font-size:.68rem;letter-spacing:.12em;font-weight:760;color:#948d9d;margin:0 12px 10px}
body[data-page="admin"] .admin-primary-nav {display:grid;gap:5px}
body[data-page="admin"] .admin-primary-nav a {display:flex;align-items:center;gap:13px;padding:12px 14px;min-height:48px;border-radius:10px;text-decoration:none;color:#c6c1cb;font-weight:625;border:1px solid transparent;transition:background-color .16s,color .16s}
body[data-page="admin"] .admin-primary-nav a:hover {background:#24212d;color:white}
body[data-page="admin"] .admin-primary-nav a[aria-current="page"] {color:#fff;background:var(--admin-redwash);border-color:#85414c}
body[data-page="admin"] .admin-nav-icon {display:inline-grid;place-items:center;width:22px;font-size:20px;color:inherit;font-weight:500}
body[data-page="admin"] .admin-side-status {margin-top:36px}
body[data-page="admin"] .admin-side-provider {display:flex;align-items:center;gap:9px;min-height:35px;padding:6px 12px;color:#d8d3df;text-decoration:none;font-size:.85rem;border-radius:8px}
body[data-page="admin"] .admin-side-provider:hover {background:#26242d}
body[data-page="admin"] .admin-side-provider small {font-size:.7rem;color:var(--admin-soft);margin-left:auto;text-align:right;max-width:100px;overflow:hidden;text-overflow:ellipsis;white-space:nowrap}
body[data-page="admin"] .admin-status-dot {width:8px;height:8px;background:#99909e;border-radius:50%;flex:none}
body[data-page="admin"] .admin-status-dot[data-state="good"],body[data-page="admin"] .admin-status-dot[data-state="healthy"] {background:#70ce9c}
body[data-page="admin"] .admin-status-dot[data-state="warning"],body[data-page="admin"] .admin-status-dot[data-state="stale"] {background:#e9bc69}
body[data-page="admin"] .admin-status-dot[data-state="error"],body[data-page="admin"] .admin-status-dot[data-state="down"] {background:#f17885}
body[data-page="admin"] .admin-sidebar-log {display:block;margin:14px 6px 0;padding:12px 7px;color:#ccc4d1;text-decoration:none;font-size:.86rem;border-top:1px solid var(--admin-border)}
body[data-page="admin"] .admin-side-bottom {margin-top:auto;padding:18px 9px 0;border-top:1px solid var(--admin-border);display:grid;gap:10px}
body[data-page="admin"] .admin-user-mini {display:flex;align-items:center;gap:10px;font-size:.86rem;min-width:0}
body[data-page="admin"] .admin-user-mini small {display:block;color:var(--admin-soft);font-size:.72rem}
body[data-page="admin"] .admin-user-avatar {display:grid;place-items:center;width:33px;height:33px;border-radius:10px;background:#60313e;color:#ffe4e8;font-weight:800}
body[data-page="admin"] .admin-external,body[data-page="admin"] .admin-logout {text-align:left;font-size:.8rem;color:#c4bbc9;text-decoration:none}
body[data-page="admin"] .admin-logout {border:0;background:none;min-height:29px;padding:3px 0;cursor:pointer}
body[data-page="admin"] .admin-logout:hover,body[data-page="admin"] .admin-external:hover {color:#fff}
body[data-page="admin"] .admin-content {flex:1;min-width:0}
body[data-page="admin"] .admin-topbar {height:70px;padding:0 clamp(18px,3vw,47px);display:flex;align-items:center;justify-content:space-between;gap:16px;border-bottom:1px solid #2b2933;background:#141219;position:sticky;top:0;z-index:40}
body[data-page="admin"] .admin-top-left,body[data-page="admin"] .admin-top-actions {display:flex;align-items:center;gap:16px;min-width:0}
body[data-page="admin"] .admin-crumb {font-size:.82rem;color:#a9a2b2;white-space:nowrap}
body[data-page="admin"] .admin-crumb span {padding:0 8px;color:#797181}
body[data-page="admin"] .admin-crumb strong {color:#f8f6fa}
body[data-page="admin"] .admin-top-actions a {font-size:.82rem;color:#d4cdd7;text-decoration:none;white-space:nowrap}
body[data-page="admin"] .admin-top-actions a:hover {color:white}
body[data-page="admin"] .admin-command-button {background:#211e27;border:1px solid #3b3541;border-radius:9px;color:#c6bfcd;font-size:.81rem;display:flex;align-items:center;gap:24px;min-height:36px;padding:7px 11px}
body[data-page="admin"] kbd {font:inherit;color:#b7a9b5;font-size:.68rem;background:#302b35;padding:4px 6px;border-radius:5px}
body[data-page="admin"] .admin-workspace.shell {width:min(100%,1450px);max-width:1450px;padding:clamp(20px,2.8vw,42px) clamp(18px,3vw,46px) 64px;margin:0 auto}
body[data-page="admin"] .admin-page-heading {display:flex;align-items:center;justify-content:space-between;gap:20px;margin-bottom:26px}
body[data-page="admin"] .admin-page-heading h1 {font-size:clamp(1.8rem,2.6vw,2.4rem);font-weight:760;letter-spacing:-.05em;line-height:1.12;margin:4px 0 9px}
body[data-page="admin"] .admin-page-kicker {margin:0;font-size:.68rem;font-weight:800;letter-spacing:.14em;color:#bb8590}
body[data-page="admin"] .admin-page-description {color:var(--admin-soft);font-size:.89rem;margin:0}
body[data-page="admin"] .admin-heading-actions {display:flex;align-items:center;gap:12px;flex-wrap:wrap}
body[data-page="admin"] .admin-saved-chip {color:#b5d8c3;font-size:.75rem;white-space:nowrap}
body[data-page="admin"] .admin-saved-chip[data-state="dirty"] {color:#f0be79}
body[data-page="admin"] .admin-workspace-nav {display:flex;align-items:center;gap:8px;margin-bottom:0;overflow-x:auto;padding-bottom:14px}
body[data-page="admin"] .admin-provider-tab {border:1px solid var(--admin-border);background:#1c1a23;border-radius:10px;min-height:44px;display:flex;align-items:center;gap:12px;padding:9px 17px;color:#cdc5d0;text-decoration:none;font-size:.9rem;font-weight:650;white-space:nowrap}
body[data-page="admin"] .admin-provider-tab span {font-size:.7rem;color:#b7abbc;font-weight:500}
body[data-page="admin"] .admin-provider-tab[aria-current="page"] {border-color:#b94d60;background:#3e202b;color:#fff}
body[data-page="admin"] .admin-subnav {display:flex;gap:5px;align-items:center;flex-wrap:wrap;border-bottom:1px solid var(--admin-border);margin:0 0 26px;padding:0 0 8px}
body[data-page="admin"] .admin-subnav a {padding:10px 13px;min-height:40px;text-decoration:none;font-size:.82rem;font-weight:600;color:#c3bac8;border-radius:8px}
body[data-page="admin"] .admin-subnav a:hover {background:#24212c;color:#fff}
body[data-page="admin"] .admin-subnav a[aria-current="page"] {background:#30202a;color:#fff}
body[data-page="admin"] .panel {background:var(--admin-card);border:1px solid var(--admin-border);border-radius:13px;box-shadow:none}
body[data-page="admin"] .panel.form-panel {margin-bottom:18px}
body[data-page="admin"] .section-title h2 {font-size:1.21rem;letter-spacing:-.025em}
body[data-page="admin"] .section-title {gap:16px}
body[data-page="admin"] .muted {color:#b5abba}
body[data-page="admin"] .admin-shortcuts,.admin-quick-actions {gap:9px}
body[data-page="admin"] .button {border-radius:9px}
body[data-page="admin"] .admin-attention {border-radius:11px;margin-bottom:18px}
body[data-page="admin"] .admin-bottom {display:flex;justify-content:space-between;flex-wrap:wrap;gap:12px;margin-top:34px;border-top:1px solid #37323a;padding:19px 0;color:#a9a0ad;font-size:.76rem}
body[data-page="admin"] .admin-detail-diagnostics {margin-top:28px}
body[data-page="admin"] .admin-detail-diagnostics >summary {display:flex;align-items:center;justify-content:space-between;gap:15px;cursor:pointer;padding:17px 22px;font-size:.95rem}
body[data-page="admin"] .admin-detail-diagnostics >summary span {font-size:.77rem;color:#aea6b3}
body[data-page="admin"] .admin-details-pad {padding:14px 20px 22px;border-top:1px solid var(--admin-border)}
body[data-page="admin"] .admin-detail-diagnostics .health-panel {margin:0 0 16px;border:0;background:none;padding:0}
body[data-page="admin"] .admin-workspace [id] {scroll-margin-top:100px}
body[data-page="admin"] .admin-settings-shortcuts {display:grid;grid-template-columns:repeat(4,minmax(0,1fr));gap:10px;margin-bottom:20px}
body[data-page="admin"] .admin-settings-shortcuts a {display:flex;flex-direction:column;gap:5px;padding:16px;border:1px solid var(--admin-border);border-radius:11px;text-decoration:none;background:var(--admin-card);color:#efebf0;font-weight:720;font-size:.83rem}
body[data-page="admin"] .admin-settings-shortcuts a:hover {border-color:#a45c6b}
body[data-page="admin"] .admin-settings-shortcuts span {font-size:.72rem;font-weight:400;color:var(--admin-soft)}
body[data-page="admin"] .admin-mobile-close,body[data-page="admin"] .admin-menu-button {display:none}
body[data-page="admin"] .admin-veil {position:fixed;inset:0;background:#050408b8;z-index:50}
body[data-page="admin"] .admin-command-dialog {width:min(540px,calc(100vw - 36px));max-height:min(700px,85dvh);overflow:auto;border:1px solid #554551;border-radius:15px;background:#19161f;color:#f6f1f5;box-shadow:0 20px 80px #000b;padding:17px}
body[data-page="admin"] .admin-command-dialog::backdrop {background:#050407a9;backdrop-filter:blur(3px)}
body[data-page="admin"] .admin-command-title {display:flex;align-items:center;justify-content:space-between;margin-bottom:12px}
body[data-page="admin"] .admin-command-title button {border:0;background:none;color:#fff;font-size:1.4rem;min-height:30px}
body[data-page="admin"] .admin-command-label {font-size:.7rem;color:#bcb2c2;display:block;margin-bottom:7px}
body[data-page="admin"] #adminCommandSearch {width:100%;margin-bottom:9px;background:#24202d}
body[data-page="admin"] .admin-command-results {display:grid;gap:4px;max-height:48dvh;overflow-y:auto}
body[data-page="admin"] .admin-command-results a {padding:12px;border-radius:9px;text-decoration:none;color:#f2ebf3}
body[data-page="admin"] .admin-command-results a:hover,body[data-page="admin"] .admin-command-results a:focus-visible {background:#332632}
body[data-page="admin"] .admin-command-results strong {display:block;font-size:.83rem}
body[data-page="admin"] .admin-command-results small {color:#b8afbd;font-size:.7rem}
body[data-page="admin"] .admin-command-dialog > small {display:block;color:#afa5b3;margin-top:12px}
body[data-page="admin"] .admin-command-results a[hidden] {display:none}
body[data-page="admin"] .admin-advanced-fold {margin:15px 0 18px;border:1px solid var(--admin-border);border-radius:11px;background:#1a1820}
body[data-page="admin"] .admin-advanced-fold >summary {display:flex;flex-wrap:wrap;align-items:center;justify-content:space-between;gap:8px;padding:18px;cursor:pointer;color:#eee8f0;font-weight:710}
body[data-page="admin"] .admin-advanced-fold >summary small {color:#b3a9b8;font-size:.73rem;font-weight:400}
body[data-page="admin"] .admin-advanced-fold > .panel {margin:12px !important}
body[data-page="admin"] .admin-content [data-reveal-panel][hidden]{display:none}
@media(max-width:1130px) {
  body[data-page="admin"] .admin-sidebar {flex-basis:214px;width:214px}
  body[data-page="admin"] .admin-topbar {padding:0 23px}
  body[data-page="admin"] .admin-workspace.shell {padding:26px 24px}
  body[data-page="admin"] .admin-settings-shortcuts {grid-template-columns:repeat(2,minmax(0,1fr))}
}
@media(max-width:790px) {
  body[data-page="admin"] .admin-sidebar {position:fixed;left:0;top:0;bottom:0;max-width:85vw;width:270px;height:100dvh;transform:translateX(-105%);transition:transform .2s ease;box-shadow:18px 0 45px #0008}
  body[data-page="admin"] .admin-app[data-menu-open="true"] .admin-sidebar {transform:translateX(0)}
  body[data-page="admin"] .admin-mobile-close,body[data-page="admin"] .admin-menu-button {display:inline-grid;place-items:center;border:1px solid var(--admin-border);background:#24202b;color:white;border-radius:9px;min-width:38px;min-height:38px;cursor:pointer}
  body[data-page="admin"] .admin-mobile-close {border:0;background:transparent;font-size:1.5rem}
  body[data-page="admin"] .admin-topbar {height:62px;padding:0 14px}
  body[data-page="admin"] .admin-crumb {font-size:.74rem}
  body[data-page="admin"] .admin-top-public,body[data-page="admin"] .admin-top-activity span,body[data-page="admin"] .admin-command-button kbd {display:none}
  body[data-page="admin"] .admin-command-button {gap:2px}
  body[data-page="admin"] .admin-top-actions {gap:10px}
  body[data-page="admin"] .admin-workspace.shell {padding:22px 15px 45px}
  body[data-page="admin"] .admin-page-heading {align-items:flex-start;flex-direction:column}
  body[data-page="admin"] .admin-page-heading h1 {font-size:1.9rem}
  body[data-page="admin"] .admin-provider-tab {flex:1;justify-content:center}
  body[data-page="admin"] .admin-subnav {flex-wrap:nowrap;overflow-x:auto;scrollbar-width:thin}
  body[data-page="admin"] .admin-subnav a {white-space:nowrap}
}
@media(max-width:520px) {
  body[data-page="admin"] .admin-settings-shortcuts {grid-template-columns:1fr 1fr}
  body[data-page="admin"] .admin-settings-shortcuts a {padding:12px}
  body[data-page="admin"] .admin-command-button {font-size:.75rem}
  body[data-page="admin"] .admin-crumb {overflow:hidden;text-overflow:ellipsis;max-width:170px}
  body[data-page="admin"] .panel.form-panel {padding:17px}
  body[data-page="admin"] .admin-workspace table {min-width:570px}
}
@media(prefers-reduced-motion: reduce){body[data-page="admin"] .admin-sidebar {transition:none}}

/* Operations should be the primary content on the Activity screen. */
body[data-page="admin"] .admin-operations-host {margin:0 0 24px}
body[data-page="admin"] .admin-operations-host .operations-panel {border:1px solid var(--admin-border);background:#17151e;border-radius:12px;padding:0 19px}
body[data-page="admin"] .admin-operations-host .operations-panel > summary {padding:17px 3px}
body[data-page="admin"] .admin-activity-subtitle {margin:22px 0 12px;font-size:1.08rem}
body[data-page="admin"] .admin-activity-page .health-panel {background:transparent;box-shadow:none;border:0;padding:0}

body[data-page="admin"] .admin-saved-chip[data-state="warning"] {color:#f0be79}

/* V10 navigation reliability + accessible section targeting. */
body[data-page="admin"] :target {scroll-margin-top:112px}
body[data-page="admin"] .admin-subnav a:focus-visible,
body[data-page="admin"] .admin-primary-nav a:focus-visible,
body[data-page="admin"] .admin-workspace-nav a:focus-visible {outline:3px solid #efa2b0;outline-offset:2px}
body[data-page="admin"] .admin-subnav a:hover,
body[data-page="admin"] .admin-provider-tab:hover {border-color:#96505f;color:#fff}
body[data-page="admin"] .form-panel input:focus-visible,
body[data-page="admin"] .form-panel select:focus-visible {border-color:#dc6172}
body[data-page="admin"] .admin-save-actions {display:flex;align-items:center;gap:12px;flex-wrap:wrap}
body[data-page="admin"] .admin-subnav a[aria-disabled="true"] {pointer-events:none;opacity:.5}
@media(prefers-reduced-motion:reduce) {body[data-page="admin"] * {scroll-behavior:auto}}

/* V12 reliability-first editors */
.admin-payout-summary{display:grid;grid-template-columns:repeat(3,minmax(0,1fr));gap:12px;margin:18px 0}.admin-payout-summary>div{display:flex;flex-direction:column;gap:4px;padding:14px;border:1px solid var(--line,#3b303a);border-radius:12px;background:#17151c}.admin-payout-summary strong{font-size:1.05rem}.admin-payout-summary small{display:block}.admin-sticky-form{padding-bottom:78px}.admin-save-bar{position:sticky;z-index:8;bottom:12px;display:flex;align-items:center;gap:10px;padding:12px 14px;border:1px solid #49343e;border-radius:14px;background:rgba(23,20,27,.97);box-shadow:0 16px 42px #0008;backdrop-filter:blur(14px)}.admin-save-bar>div{min-width:0;flex:1;display:flex;flex-direction:column;gap:2px}.admin-save-bar small{color:var(--muted,#aaa)}.compact-field{max-width:320px}
@media(max-width:760px){.admin-payout-summary{grid-template-columns:1fr}.admin-save-bar{align-items:stretch;flex-wrap:wrap}.admin-save-bar>div{flex-basis:100%}.admin-save-bar .button{flex:1}}

.gaming-admin-live{display:flex;justify-content:space-between;align-items:center;gap:24px;padding:20px;margin:0 0 18px}
.gaming-admin-live h3{margin:4px 0 6px}
.gaming-admin-live p{margin:0}
.gaming-admin-live dl{display:grid;grid-template-columns:repeat(3,minmax(90px,1fr));gap:10px;margin:0}
.gaming-admin-live dl div{padding:12px;border-radius:10px;background:#17151b;border:1px solid #39323b}
.gaming-admin-live dt{font-size:.68rem;color:var(--muted);text-transform:uppercase;letter-spacing:.07em}
.gaming-admin-live dd{margin:5px 0 0;font-size:1.1rem;font-weight:750;font-variant-numeric:tabular-nums}
@media(max-width:780px){.gaming-admin-live{align-items:flex-start;flex-direction:column}.gaming-admin-live dl{width:100%}}
@media(max-width:520px){.gaming-admin-live dl{grid-template-columns:1fr}}
```

## `static/admin-workspace.js`

```javascript
/* RedHunllef admin control center — navigation and presentation only.
 * No provider requests, credential handling, storage writes or new game logic.
 * Existing backend endpoints and CSRF-protected forms remain authoritative. */
(() => {
  'use strict';
  if (document.body.dataset.page !== 'admin') return;
  const get = (name) => document.getElementById(name);
  const app = get('adminApp');
  const menuButton = get('adminOpenMenu');
  const veil = get('adminVeil');
  const dialog = get('adminCommandDialog');
  const search = get('adminCommandSearch');
  const commandLinks = [...document.querySelectorAll('[data-command-link]')];
  let lastMenuFocus = null;
  const sidebar = get('adminSidebar');
  function syncSidebarAccessibility() {
    // Closed off-canvas navigation must not trap keyboard focus.
    if (sidebar) sidebar.inert = window.matchMedia('(max-width: 790px)').matches && app?.dataset.menuOpen !== 'true';
  }

  // Sidebar is a real drawer on mobile and an always-visible rail on desktop.
  function mobileMenu(open) {
    if (!app) return;
    app.dataset.menuOpen = String(open);
    menuButton?.setAttribute('aria-expanded', String(open));
    if (veil) veil.hidden = !open;
    syncSidebarAccessibility();
    if (open) {
      lastMenuFocus = document.activeElement;
      get('adminCloseMenu')?.focus();
    } else if (lastMenuFocus) {
      lastMenuFocus.focus({preventScroll:true});
      lastMenuFocus = null;
    }
  }
  menuButton?.addEventListener('click', () => mobileMenu(true));
  get('adminCloseMenu')?.addEventListener('click', () => mobileMenu(false));
  veil?.addEventListener('click', () => mobileMenu(false));
  window.matchMedia('(min-width: 791px)').addEventListener('change', event => {
    if (event.matches) mobileMenu(false);
    syncSidebarAccessibility();
  });
  syncSidebarAccessibility();

  function filterCommands() {
    const needle = (search?.value || '').trim().toLocaleLowerCase();
    let count = 0;
    for (const link of commandLinks) {
      link.hidden = !link.dataset.search.includes(needle);
      if (!link.hidden) count++;
    }
    if (get('adminCommandEmpty')) get('adminCommandEmpty').hidden = count !== 0;
  }
  function openCommands() {
    if (!dialog || typeof dialog.showModal !== 'function') return;
    mobileMenu(false);
    if (!dialog.open) dialog.showModal();
    search.value = '';
    filterCommands();
    search.focus();
  }
  get('adminCommandOpen')?.addEventListener('click', openCommands);
  get('adminCommandClose')?.addEventListener('click', () => dialog?.close());
  dialog?.addEventListener('click', event => {
    // Clicking the backdrop closes the dialog; clicking its contents does not.
    if (event.target === dialog) dialog.close();
  });
  search?.addEventListener('input', filterCommands);
  search?.addEventListener('keydown', event => {
    if (event.key === 'Enter') {
      const first = commandLinks.find(link => !link.hidden);
      if (first) { event.preventDefault(); first.click(); }
    }
  });
  document.addEventListener('keydown', event => {
    if ((event.ctrlKey || event.metaKey) && event.key.toLocaleLowerCase() === 'k') {
      event.preventDefault();
      if (dialog?.open) dialog.close(); else openCommands();
    }
    if (event.key === 'Escape') mobileMenu(false);
  });

  // Lightweight dirty-state chip. The existing shared app controller protects
  // unsaved drafts on navigation; this is only a human-readable indicator.
  const saveStatus = get('adminSaveStatus');
  const dirtyForms = [...document.querySelectorAll('form[data-dirty]')];
  const snapshots = new Map();
  const snapshot = form => JSON.stringify([...new FormData(form)].map(([key,val]) =>
    [key, typeof val === 'string' ? val : [val.name,val.size,val.lastModified]]));
  for (const form of dirtyForms) snapshots.set(form, snapshot(form));
  function showSaveStatus() {
    if (!saveStatus) return;
    const modified = dirtyForms.some(form => snapshot(form) !== snapshots.get(form));
    const needsReview = saveStatus.dataset.validation === 'true';
    saveStatus.dataset.state = modified ? 'dirty' : needsReview ? 'warning' : 'saved';
    saveStatus.textContent = modified ? '● Unsaved changes' :
      needsReview ? '● Review required — not saved' : '✓ All changes saved';
  }
  for (const form of dirtyForms) {
    form.addEventListener('input', showSaveStatus);
    form.addEventListener('change', showSaveStatus);
    form.addEventListener('reset', () => queueMicrotask(showSaveStatus));
  }
  document.addEventListener('admin:saved', event => {
    const form = event.detail?.form;
    if (form && snapshots.has(form)) snapshots.set(form, snapshot(form));
    showSaveStatus();
  });
  showSaveStatus();

  // The existing minute-long admin status response is the only source of live
  // state. No parallel polling requests are introduced by the new sidebar.
  document.addEventListener('admin:status', event => {
    const providers = event.detail?.providers;
    if (!providers) return;
    for (const name of ['shuffle','empiredrop']) {
      const source = providers[name];
      const indicator = document.querySelector(`[data-provider-indicator="${name}"]`);
      if (!indicator || !source) continue;
      indicator.dataset.state = source.state || 'unknown';
      const label = indicator.closest('.admin-side-provider')?.querySelector('small');
      if (label) label.textContent = source.status || 'Checking';
    }
  });

  // The legacy EmpireDrop page bundled credentials, recovery and API contract
  // settings between everyday controls. Collapse these under one titled drawer.
  // Keep the original DOM nodes/forms so IDs, CSRF actions, and event listeners
  // remain stable. Without JS the original sections remain fully accessible.
  if (document.body.dataset.adminTab === 'empiredrop') {
    const selectors = ['#empireBackupTitle','#empireKeysTitle','#empireContractTitle'];
    const targets = selectors.map(selector => document.querySelector(selector)?.closest('section')).filter(Boolean);
    if (targets.length) {
      const details = document.createElement('details');
      details.className = 'admin-advanced-fold';
      details.id = 'empireAdvanced';
      const summary = document.createElement('summary');
      summary.innerHTML = '<span>Advanced settings &amp; recovery</span><small>Backups, credentials and compatibility controls</small>';
      targets[0].before(details);
      details.append(summary);
      for (const target of targets) details.append(target);
      function honorHash() {
        let id = '';
        try { id = decodeURIComponent(location.hash.slice(1)); } catch { return; }
        const target = get(id);
        if (target && details.contains(target)) details.open = true;
      }
      honorHash();
      window.addEventListener('hashchange', honorHash);
      // On failed save, show the relevant advanced form and its error.
      if (document.querySelector('[role="alert"]') && location.hash.startsWith('#empire')) details.open = true;
    }
  }

  // On the Operations screen, lead with the logs. The health cards remain in
  // the same section beneath them for deeper investigation.
  if (document.body.dataset.adminTab === 'activity') {
    const operations = get('adminOperations');
    const host = get('adminOperationsHost');
    if (operations && host) {
      host.append(operations);
      operations.open = true;
      operations.setAttribute('aria-label','Recent operational activity');
    }
  }
  // Native details elements own their focus and state. When a quick link lands
  // inside a closed details section, reveal only the relevant ancestor panels.
  function revealAnchor() {
    let id = '';
    try { id = decodeURIComponent(location.hash.slice(1)); } catch { return; }
    const target = id ? get(id) : null;
    if (!target) return;
    for (let ancestor = target.parentElement; ancestor; ancestor = ancestor.parentElement) {
      if (ancestor.tagName === 'DETAILS') ancestor.open = true;
    }
  }
  function revealServerFocus() {
    const focus = document.querySelector('.admin-workspace')?.dataset.focus || '';
    if (!focus) return;
    const target = get(focus);
    if (!target) return;
    for (let ancestor = target.parentElement; ancestor; ancestor = ancestor.parentElement) {
      if (ancestor.tagName === 'DETAILS') ancestor.open = true;
    }
    queueMicrotask(() => target.scrollIntoView({block:'start'}));
  }
  revealAnchor();
  revealServerFocus();
  window.addEventListener('hashchange', revealAnchor);
  // Hidden required inputs must be visible when native form validation runs.
  // Otherwise browsers can reject the save with an un-focusable control.
  document.addEventListener('invalid', event => {
    let parent = event.target?.parentElement;
    while (parent) {
      if (parent.tagName === 'DETAILS') parent.open = true;
      parent = parent.parentElement;
    }
  }, true);
})();
```

## `static/app.js`

```javascript
/* Shared page controller. Native navigation/forms work before this file loads. */
(() => {
  "use strict";
  const id = (name) => document.getElementById(name);
  const text = (node, value) => {
    // Only leaf labels can be text destinations. Never erase a page or form.
    if (!node) return;
    if (
      node.childElementCount ||
      ["BODY", "MAIN", "FORM", "HTML"].includes(node.tagName)
    )
      throw new Error("Invalid text destination");
    if (node.textContent !== String(value ?? ""))
      node.textContent = String(value ?? "");
  };
  const notice = (name, value) => {
    const node = id(name);
    if (node) {
      node.hidden = !value;
      text(node, value);
      if (name === "networkError") globalThis.RedHealth?.attention();
    }
  };
  const currency = (value) =>
    new Intl.NumberFormat("en-US", {
      style: "currency",
      currency: "USD",
    }).format(Number(value) || 0);
  const eastern = new Intl.DateTimeFormat("en-US", {
    timeZone: "America/New_York",
    month: "short",
    day: "numeric",
    year: "numeric",
    hour: "numeric",
    minute: "2-digit",
    timeZoneName: "short",
  });
  const date = (value) =>
    value
      ? eastern.format(new Date(value * 1000))
      : "Waiting for first source update";
  document.documentElement.classList.add("js");
  let toastTimer;
  function toast(message) {
    notice("toast", message);
    clearTimeout(toastTimer);
    toastTimer = setTimeout(() => notice("toast", ""), 4000);
  }
  document.addEventListener("click", async (event) => {
    const button = event.target.closest("[data-copy]");
    if (!button) return;
    try {
      await navigator.clipboard.writeText(button.dataset.copy);
      toast("Username copied.");
    } catch {
      toast("Select and copy the username manually.");
    }
  });
  let dirty = false;
  const dirtyForms = new Set();
  document.querySelectorAll("[data-dirty]").forEach((form) => {
    // Files need their own signature; URLSearchParams reduces every File to
    // the same string and would miss a changed avatar selection.
    const signature = () =>
      JSON.stringify(
        [...new FormData(form)].map(([key, value]) => [
          key,
          typeof value === "string"
            ? value
            : [value.name, value.size, value.lastModified],
        ]),
      );
    const initial = signature();
    const update = () => {
      if (signature() !== initial) dirtyForms.add(form);
      else dirtyForms.delete(form);
      dirty = dirtyForms.size > 0;
      text(id("saveLabel"), dirty ? "Unsaved changes" : "All changes saved");
    };
    form.addEventListener("input", update);
    form.addEventListener("change", update);
    form.addEventListener("reset", () => setTimeout(update, 0));
    form.addEventListener("submit", (event) => {
      queueMicrotask(() => {
        if (!event.defaultPrevented) {
          dirtyForms.delete(form);
          dirty = dirtyForms.size > 0;
        }
      });
    });
  });
  document.addEventListener("admin:saved", (event) => {
    dirtyForms.delete(event.detail.form);
    dirty = dirtyForms.size > 0;
  });
  window.addEventListener("beforeunload", (event) => {
    if (dirty) {
      event.preventDefault();
      event.returnValue = "";
    }
  });
  document.querySelectorAll("[data-confirm]").forEach((form) =>
    form.addEventListener("submit", (event) => {
      if (!window.confirm(form.dataset.confirm)) event.preventDefault();
    }),
  );
  id("raceForm")?.addEventListener("input", () => {
    const sum = [...id("raceForm").querySelectorAll('[name^="prize_"]')].reduce(
      (n, input) => n + Number(input.value.replace(/[$,\s]/g, "")),
      0,
    );
    text(
      id("prizeTotal"),
      Number.isFinite(sum) ? currency(sum) + " total" : "Review prize amounts",
    );
  });
  // The date picker stores Eastern local wall time. Server validation handles
  // nonexistent/ambiguous DST times; a shortcut never silently publishes a race.
  function easternInput(stamp) {
    const parts = new Intl.DateTimeFormat("en-US", {
      timeZone: "America/New_York",
      year: "numeric",
      month: "2-digit",
      day: "2-digit",
      hour: "2-digit",
      minute: "2-digit",
      hourCycle: "h23",
    }).formatToParts(new Date(stamp));
    const v = Object.fromEntries(parts.map((p) => [p.type, p.value]));
    return `${v.year}-${v.month}-${v.day}T${v.hour}:${v.minute}`;
  }
  function daysAfter(value, days) {
    const d = new Date(value + "Z");
    d.setUTCDate(d.getUTCDate() + days);
    return d.toISOString().slice(0, 16);
  }
  // Construct the current Tuesday 6 PM -> Tuesday 6 PM window in Eastern
  // *wall time*, not UTC. The Python server resolves EST/EDT at save time,
  // avoiding a one-hour drift when daylight saving changes.
  function currentEasternWeek() {
    const current = new Date(easternInput(Date.now()) + "Z");
    const start = new Date(current);
    const elapsed = (current.getUTCDay() - 2 + 7) % 7;
    start.setUTCDate(start.getUTCDate() - elapsed);
    start.setUTCHours(18, 0, 0, 0);
    if (start > current) start.setUTCDate(start.getUTCDate() - 7);
    const startText = start.toISOString().slice(0, 16);
    return [startText, daysAfter(startText, 7)];
  }
  id("currentWeek")?.addEventListener("click", () => {
    const [start, end] = currentEasternWeek();
    id("f-start_et").value = start;
    id("f-end_et").value = end;
    id("f-start_et").dispatchEvent(new Event("input", { bubbles: true }));
    toast("Current Eastern Time week prepared. Review and confirm before publishing.");
  });
  id("startNow")?.addEventListener("click", () => {
    id("f-start_et").value = easternInput(Date.now());
    id("f-end_et").value = daysAfter(id("f-start_et").value, 7);
    id("f-start_et").dispatchEvent(new Event("input", { bubbles: true }));
  });
  id("nextRace")?.addEventListener("click", () => {
    const start = id("f-start_et"),
      end = id("f-end_et");
    const duration = Math.max(
      1,
      Math.round(
        (new Date(end.value + "Z") - new Date(start.value + "Z")) / 86400000,
      ) || 7,
    );
    const now = easternInput(Date.now());
    if (!end.value || end.value < now) {
      // Avoid generating another already-expired race from an old backup.
      const [, currentEnd] = currentEasternWeek();
      start.value = currentEnd;
    } else {
      start.value = end.value;
    }
    end.value = daysAfter(start.value, duration);
    start.dispatchEvent(new Event("input", { bubbles: true }));
    toast("Draft prepared. Review the dates before saving.");
  });

  if (!document.body.dataset.feed) return;
  const isAdmin = document.body.dataset.page === "admin";
  let site = {},
    offset = 0,
    sourceAt = 0,
    jobs = {},
    busy = false,
    timer,
    next = 0,
    urgentUntil = 0;
  let pollAgain = false,
    lastWork = "",
    receipt = null;
  let publicCache = null,
    publicETag = "",
    lastProviderFailure = "";
  let participantVersion = "",
    redVersion = "",
    historyVersion = "";
  try {
    const boot = JSON.parse(document.body.dataset.bootstrap);
    site = boot.site;
    offset = boot.server_time * 1000 - Date.now();
  } catch {}
  function clock() {
    if (document.hidden) return;
    const now = (Date.now() + offset) / 1000;
    const state =
      !site.start_time || site.end_time <= site.start_time
        ? "unconfigured"
        : now < site.start_time
          ? "upcoming"
          : now >= site.end_time
            ? "ended"
            : "active";
    const badge = id("raceBadge");
    text(badge, state.charAt(0).toUpperCase() + state.slice(1));
    if (badge) badge.className = "badge state-" + state;
    const left = Math.max(
      0,
      Math.ceil((state === "upcoming" ? site.start_time : site.end_time) - now),
    );
    text(
      id("countdown"),
      state === "unconfigured"
        ? "Set the race dates"
        : state === "ended"
          ? "Race complete"
          : `${Math.floor(left / 86400)}d ${String(Math.floor(left / 3600) % 24).padStart(2, "0")}h ${String(Math.floor(left / 60) % 60).padStart(2, "0")}m ${String(left % 60).padStart(2, "0")}s`,
    );
    text(
      id("clockLabel"),
      state === "upcoming"
        ? "STARTS IN"
        : state === "active"
          ? "RACE ENDS IN"
          : "RACE SCHEDULE",
    );
    text(
      id("raceWindow"),
      site.start_time
        ? date(site.start_time) + " → " + date(site.end_time)
        : "Choose the race dates in Race settings.",
    );
    if (id("endedNotice")) id("endedNotice").hidden = state !== "ended";
    if (sourceAt)
      text(
        id("sourceTime"),
        "Updated " + Math.max(0, Math.floor(now - sourceAt)) + "s ago",
      );
    for (const [name, job] of Object.entries(jobs)) {
      const remaining = Math.max(0, Math.ceil(job.next_check - now));
      text(
        id(name + "Freshness"),
        `Last successful check: ${date(job.last_success)} · Content last changed: ${job.changed_at ? date(job.changed_at) : "No recorded change yet"}`,
      );
      text(
        id(name + "Timing"),
        job.state === "checking"
          ? "Checking now…"
          : `${job.duration_ms || 0} ms · ${job.next_check ? "Next check in " + remaining + "s" : "Check queued"} · Last success: ${date(job.last_success)}`,
      );
    }
  }
  function filterRed() {
    const q = (id("redSearch")?.value || "").trim().toLowerCase();
    id("redBody")
      ?.querySelectorAll("[data-red-name]")
      .forEach(
        (row) => (row.hidden = !row.dataset.redName.toLowerCase().includes(q)),
      );
  }
  id("redSearch")?.addEventListener("input", filterRed);
  function checkingSoon(job) {
    const pending =
      job.pending || job.requested > job.completed || job.state === "queued";
    return (
      job.state === "checking" ||
      (pending &&
        (!job.next_check || job.next_check <= (Date.now() + offset) / 1000 + 3))
    );
  }
  function progress(value) {
    for (const name of ["shuffle", "kick"]) {
      const job = jobs[name] || {},
        pending =
          job.pending ||
          job.requested > job.completed ||
          job.state === "queued";
      let message = "Automatic check is starting.";
      if (job.state === "checking")
        message = job.pending
          ? "Checking now; your follow-up refresh is queued."
          : "Checking the provider now…";
      else if (pending) {
        message =
          job.next_check > (Date.now() + offset) / 1000 + 3
            ? "Queued. Retry scheduled for " + date(job.next_check) + "."
            : "Refresh queued; waiting for the worker.";
        if (job.error)
          message +=
            " Last check" +
            (job.http_status ? " (HTTP " + job.http_status + ")" : "") +
            ": " +
            job.error;
      } else if (job.error)
        message =
          "Check failed" +
          (job.http_status ? " (HTTP " + job.http_status + ")" : "") +
          ": " +
          job.error;
      else if (
        name === "shuffle" &&
        ["updated", "unchanged"].includes(job.result)
      )
        message =
          (job.result === "updated" ? "Published " : "Confirmed ") +
          (value.count || 0) +
          " qualifying players. Last check: " +
          date(job.completed_at) +
          ".";
      else if (name === "shuffle" && job.result === "empty")
        message =
          value.leaderboard_message ||
          "Check completed; no qualifying wagers were returned.";
      else if (["upcoming", "unconfigured"].includes(job.result))
        message =
          value.leaderboard_message ||
          "Waiting for the configured race to start.";
      else if (job.result === "superseded")
        message =
          "The old settings were superseded; a check for the current settings is queued.";
      else if (job.result === "shared")
        message = "Another app instance is checking this provider.";
      else if (name === "kick" && ["live", "offline"].includes(job.result))
        message =
          "Confirmed " +
          job.result +
          " on Kick. Last check: " +
          date(job.completed_at) +
          ".";
      text(id(name + "Progress"), message);
      const summary = job.error
        ? "Needs attention"
        : job.state === "checking"
          ? "Checking now"
          : pending
            ? "Queued"
            : name === "kick" && ["live", "offline"].includes(job.result)
              ? job.result === "live"
                ? "Live"
                : "Offline"
              : job.result === "waiting"
                ? "Waiting for data"
                : job.result === "upcoming"
                  ? "Race upcoming"
                  : job.result === "unconfigured"
                    ? "Set race dates"
                    : "Up to date";
      text(
        id(name + "Summary"),
        `${name === "shuffle" ? "Shuffle" : "Kick"} · ${summary}`,
      );
      id(name + "Summary")?.classList.toggle("has-error", Boolean(job.error));
    }
    const failure = JSON.stringify(
      Object.entries(jobs)
        .filter(([, job]) => job.error)
        .map(([name, job]) => [name, job.error, job.http_status]),
    );
    if (
      failure !== "[]" &&
      failure !== lastProviderFailure &&
      id("connectionDetails")
    )
      id("connectionDetails").open = true;
    lastProviderFailure = failure;
    text(
      id("publishedWindow"),
      "Published window: " +
        date(site.start_time) +
        " → " +
        date(site.end_time),
    );
    const work = JSON.stringify([
      value.runtime_id,
      ...Object.values(jobs).map((job) => [job.requested, job.runs, job.state]),
    ]);
    if (work !== lastWork && Object.values(jobs).some(checkingSoon))
      urgentUntil = Date.now() + 60000;
    lastWork = work;
    if (receipt && value.runtime_id) {
      if (receipt.runtime_id !== value.runtime_id) {
        receipt = null;
        toast("The backend restarted. Current update progress is shown below.");
      } else if (
        Object.entries(receipt.requests).every(
          ([name, target]) => jobs[name]?.completed >= target,
        )
      ) {
        const failed = Object.keys(receipt.requests).some(
          (name) => jobs[name]?.error,
        );
        toast(
          failed
            ? "Refresh finished with a provider error. See update progress below."
            : "Refresh finished. See the update result below.",
        );
        receipt = null;
      }
    }
  }
  function cell(value, className = "") {
    const td = document.createElement("td");
    td.textContent = String(value ?? "—");
    td.className = className;
    return td;
  }
  function updateTable(body, rows, red = false) {
    if (!body) return;
    const encoded = JSON.stringify(rows);
    if (encoded === (red ? redVersion : participantVersion)) return;
    if (red) redVersion = encoded;
    else participantVersion = encoded;
    const scroll = body.closest(".table-scroll"),
      top = scroll?.scrollTop,
      left = scroll?.scrollLeft;
    const focused = document.activeElement,
      focusRow = focused?.closest("tr"),
      focusName = focusRow?.dataset.player || focusRow?.dataset.redName;
    const focusCopy = focused?.hasAttribute("data-copy");
    const fragment = document.createDocumentFragment();
    rows.forEach((r, index) => {
      const tr = document.createElement("tr");
      tr.dataset[red ? "redName" : "player"] = r.username;
      tr.append(cell(red ? index + 1 : r.rank, "rank"));
      const name = cell("");
      const strong = document.createElement("strong");
      strong.textContent = r.username;
      name.append(strong);
      const copy = document.createElement("button");
      copy.type = "button";
      copy.className = "copy-button";
      copy.dataset.copy = r.username;
      copy.textContent = "⧉";
      copy.setAttribute("aria-label", "Copy " + r.username);
      name.append(copy);
      if (!red && r.source === "override") {
        const label = document.createElement("span");
        label.className = "tag";
        label.textContent = "Adjusted";
        name.append(label);
      }
      tr.append(name, cell(red ? r.weighted : r.wager, "number accent"));
      if (!red) tr.append(cell(r.original_weighted_str, "number"));
      tr.append(cell(red ? r.raw : r.raw_wager_str, "number"));
      if (!red) {
        const action = cell(""),
          link = document.createElement("a");
        link.href =
          "/admin/leaderboards/shuffle/players?edit=" +
          encodeURIComponent(r.username) +
          "#override";
        link.className = "text-link";
        link.textContent = "Edit";
        action.append(link);
        tr.append(action);
      }
      fragment.append(tr);
    });
    if (!rows.length) {
      const tr = document.createElement("tr"),
        td = cell(
          red
            ? "No confirmed Code Red wagerers for this window."
            : "No matching qualifying wagers.",
          "empty",
        );
      td.colSpan = red ? 4 : 6;
      tr.append(td);
      fragment.append(tr);
    }
    body.replaceChildren(fragment);
    if (scroll) {
      scroll.scrollTop = top;
      scroll.scrollLeft = left;
    }
    if (focusName)
      [...body.rows]
        .find(
          (row) => (row.dataset.player || row.dataset.redName) === focusName,
        )
        ?.querySelector(focusCopy ? "button" : "a")
        ?.focus({ preventScroll: true });
    if (red) filterRed();
  }
  function apply(value, began) {
    if (!value.site || !value.freshness || !Number.isFinite(value.server_time))
      throw new Error("The update response is incomplete.");
    site = value.site;
    offset = value.server_time * 1000 - (began + Date.now()) / 2;
    sourceAt = value.freshness.updated_at;
    text(id("sponsorName"), site.sponsor_name);
    text(id("poolTotal"), site.total_prize);
    text(id("playerCount"), value.count);
    text(id("dataState"), value.freshness.label);
    text(id("sourceTime"), date(sourceAt));
    // Visitors get a single calm availability state. Provider diagnostics and
    // request details remain in the authenticated Admin Control Center.
    notice(
      "leaderboardMessage",
      isAdmin ? value.leaderboard_message || "" : value.rows?.length ? "" : "Standings are temporarily unavailable.",
    );
    notice(
      "sourceWarning",
      [value.freshness.warning, isAdmin ? value.freshness.error : ""]
        .filter(Boolean)
        .join(" "),
    );
    document
      .querySelectorAll("[data-site-text]")
      .forEach((node) => text(node, site[node.dataset.siteText]));
    document.querySelectorAll("[data-site-link]").forEach((a) => {
      const href = site[a.dataset.siteLink];
      a.hidden = !href;
      if (href && /^https?:\/\//.test(href)) a.href = href;
    });
    if (id("sponsorLink") && /^https?:\/\//.test(site.sponsor_url))
      id("sponsorLink").href = site.sponsor_url;
    if (isAdmin) {
      jobs = value.jobs || {};
      // Shared admin sidebar consumes the existing status response; no extra poll.
      document.dispatchEvent(new CustomEvent("admin:status", { detail: value }));
      if (value.health) globalThis.RedHealth?.render(value.health);
      if (value.providers) globalThis.RedProviderCards?.render(value);
      if (value.checkpoint && id("recoveryReminder")) {
        id("recoveryReminder").hidden = !value.checkpoint.changes;
        text(id("recoveryReminderDetail"), value.checkpoint.details);
      }
      if (value.checkpoint) {
        text(id("checkpointLabel"), value.checkpoint.label);
        text(id("checkpointDetails"), value.checkpoint.details);
        text(
          id("checkpointTime"),
          value.checkpoint.generated_at
            ? "Last export generated: " + date(value.checkpoint.generated_at)
            : "No export generated yet.",
        );
        id("checkpointLabel")?.classList.toggle(
          "accent",
          value.checkpoint.changes,
        );
      }
      progress(value);
      if (value.gaming) globalThis.RedGamingAdmin?.render(value.gaming);
      const historyDiagnostics = id("historyDiagnostics");
      const historyKey = JSON.stringify(value.history?.weeks || []);
      if (
        historyDiagnostics &&
        value.history?.weeks &&
        historyKey !== historyVersion
      ) {
        historyVersion = historyKey;
        historyDiagnostics.replaceChildren(
          ...value.history.weeks.map((week) => {
            const article = document.createElement("article");
            for (const [tag, content] of [
              ["strong", week.label],
              [
                "p",
                (week.message || "Results confirmed.") +
                  (week.http_status ? ` HTTP ${week.http_status}.` : ""),
              ],
              [
                "small",
                `Last result: ${date(week.updated_at)}` +
                  (week.retry_at ? ` · Retry: ${date(week.retry_at)}` : ""),
              ],
            ]) {
              const node = document.createElement(tag);
              node.textContent = content;
              article.append(node);
            }
            return article;
          }),
        );
      }
      updateTable(id("participantsBody"), value.participants || []);
      if (id("codeRed")?.open && value.red)
        updateTable(id("redBody"), value.red, true);
      text(id("redCount"), Math.min(100, value.red_total || 0) + " / 100");
      text(
        id("redMembership"),
        (value.diagnostics?.missing_campaign || 0) +
          " source rows have no campaign metadata; membership cannot be verified for those rows.",
      );
      for (const name of ["shuffle", "kick"])
        text(
          id(name + "Message"),
          jobs[name]?.error ||
            (name === "shuffle"
              ? value.freshness.label
              : value.stream?.available
                ? value.stream.live
                  ? "Live on Kick"
                  : "Kick offline"
                : "Kick status unavailable"),
        );
      const stream = value.stream || {};
      text(
        id("streamDetail"),
        stream.available && stream.live
          ? [
              stream.title,
              stream.viewers
                ? stream.viewers.toLocaleString() + " watching"
                : "Viewer count unavailable",
            ]
              .filter(Boolean)
              .join(" · ")
          : "",
      );
      document
        .querySelectorAll("[data-diagnostic]")
        .forEach((node) =>
          text(node, value.diagnostics?.[node.dataset.diagnostic]),
        );
      text(
        id("browserCheck"),
        "Dashboard checked " +
          date(value.server_time) +
          " · next update in 60 seconds",
      );
    } else {
      const rows = new Map((value.rows || []).map((row) => [row.rank, row]));
      document.querySelectorAll("[data-rank]").forEach((node) => {
        const n = Number(node.dataset.rank),
          row = rows.get(n);
        text(
          node.querySelector("[data-name]"),
          row?.username || "Open position",
        );
        text(node.querySelector("[data-wager]"), row?.wager || "$0.00");
        text(node.querySelector("[data-prize]"), currency(site.prizes[n]));
      });
      if (value.empiredrop)
        document.dispatchEvent(new CustomEvent('empiredrop:update', { detail: {...value.empiredrop, shuffle_site: value.site, server_time:value.server_time} }));
      text(
        id("streamStatus"),
        !value.stream?.available
          ? "Kick status unavailable"
          : value.stream.live
            ? "● Live on Kick"
            : "Kick offline",
      );
    }
    clock();
  }
  async function getJSON(url, options = {}) {
    const controller = new AbortController(),
      timeout = setTimeout(() => controller.abort(), 10000);
    try {
      const conditional =
        !isAdmin &&
        !options.method &&
        new URL(url, location.origin).pathname === "/public-state";
      const headers = { Accept: "application/json", ...options.headers };
      if (conditional && publicETag) headers["If-None-Match"] = publicETag;
      const response = await fetch(url, {
        ...options,
        credentials: "same-origin",
        cache: "no-store",
        signal: controller.signal,
        headers,
      });
      const clockHeader = response.headers?.get("X-Server-Time");
      const currentTime =
        clockHeader && Number.isFinite(Number(clockHeader))
          ? Number(clockHeader)
          : null;
      if (conditional && response.status === 304) {
        if (!publicCache)
          throw new Error("The cached update is unavailable. Reload the page.");
        return {
          ...publicCache,
          server_time: currentTime ?? Date.now() / 1000,
        };
      }
      if (isAdmin && [401, 403].includes(response.status)) {
        document.dispatchEvent(new Event("admin:expired"));
        throw new Error(
          "Your session expired. Sign in again to resume updates.",
        );
      }
      if (
        response.redirected &&
        response.url &&
        new URL(response.url, location.origin).pathname === "/admin/login"
      ) {
        throw new Error(
          "Your session expired. Sign in again to resume updates.",
        );
      }
      if (!response.headers.get("content-type")?.includes("application/json")) {
        const hint =
          response.status === 404
            ? "The update endpoint was not found. Reload the page after installing the complete update."
            : response.status >= 500
              ? "Check the backend runtime logs. Previous results are retained."
              : "Reload the page and sign in again if needed.";
        // Never render an HTML error/proxy page into the dashboard.
        throw new Error(
          `Expected JSON but received a non-JSON response (HTTP ${response.status}). ${hint}`,
        );
      }
      let value;
      try {
        value = await response.json();
      } catch {
        throw new Error(
          `The server returned invalid JSON (HTTP ${response.status}). Check the runtime logs.`,
        );
      }
      if (!response.ok)
        throw new Error(
          `${value?.error || "The server could not complete this request."} (HTTP ${response.status})` +
            (response.status >= 500 && value?.request_id
              ? ` Reference: ${value.request_id}.`
              : ""),
        );
      if (conditional) {
        publicCache = value;
        publicETag = response.headers.get("ETag") || "";
        value = {
          ...value,
          server_time: currentTime ?? value.server_time ?? Date.now() / 1000,
        };
      }
      return value;
    } finally {
      clearTimeout(timeout);
    }
  }
  async function poll() {
    if (document.hidden) return;
    if (busy) {
      pollAgain = true;
      return;
    }
    busy = true;
    clearTimeout(timer);
    const began = Date.now();
    try {
      const url = new URL(document.body.dataset.feed, location.origin);
      if (isAdmin) {
        for (const [key, value] of new URLSearchParams(location.search))
          url.searchParams.set(key, value);
        url.searchParams.set(
          "tab",
          document.body.dataset.adminTab ||
            url.searchParams.get("tab") ||
            "overview",
        );
        // Rankings already have a five-second conditional feed. Do not send
        // the same private lists again in the slower provider-status response.
        url.searchParams.set("gaming", "0");
        if (id("codeRed")?.open) url.searchParams.set("code_red", "1");
      }
      const result = await getJSON(url);
      apply(result, began);
      notice("networkError", "");
      if (
        result.release &&
        document.body.dataset.release &&
        result.release !== document.body.dataset.release
      )
        notice(
          "networkError",
          isAdmin ? "A newer version was deployed. Save your draft, then reload." : "Standings are temporarily unavailable.",
        );
    } catch (error) {
      notice(
        "networkError",
        error.name === "AbortError"
          ? "Dashboard request timed out. Previous results are retained; updates will retry."
          : isAdmin
            ? error.message
            : "Connection delayed. Saved standings remain visible; retrying automatically.",
      );
    } finally {
      busy = false;
      if (!next) next = began + 60000;
      else if (next <= began)
        next += 60000 * (Math.floor((began - next) / 60000) + 1);
      if (next <= Date.now())
        next += 60000 * (Math.floor((Date.now() - next) / 60000) + 1);
      const urgent =
        Date.now() < urgentUntil && Object.values(jobs).some(checkingSoon);
      const delay = pollAgain
        ? 50
        : urgent
          ? 2000
          : Math.max(250, next - Date.now());
      pollAgain = false;
      if (!document.hidden) timer = setTimeout(poll, delay);
    }
  }
  document.querySelectorAll("[data-refresh]").forEach((form) =>
    form.addEventListener("submit", async (event) => {
      event.preventDefault();
      const button = form.querySelector("button");
      if (button.disabled) return;
      button.disabled = true;
      try {
        // A hidden input named "action" shadows form.action in real browsers.
        // Read the HTML attribute so every refresh reaches the backend route.
        const value = await getJSON(form.getAttribute("action"), {
          method: "POST",
          body: new FormData(form),
        });
        receipt = value.requests
          ? { runtime_id: value.runtime_id, requests: value.requests }
          : null;
        jobs = value.jobs || jobs;
        toast(value.message);
        urgentUntil = Date.now() + 60000;
        next = 0;
        await poll();
      } catch (error) {
        toast(error.message);
      } finally {
        button.disabled = false;
      }
    }),
  );
  document
    .querySelectorAll("[data-recovery-download]")
    .forEach((link) =>
      link.addEventListener("click", () => setTimeout(() => void poll(), 1000)),
    );
  id("codeRed")?.addEventListener("toggle", () => {
    if (id("codeRed").open) {
      next = 0;
      poll();
    }
  });
  document.addEventListener("visibilitychange", () => {
    clearTimeout(timer);
    if (!document.hidden) {
      next = 0;
      poll();
    }
  });
  window.addEventListener("pageshow", (event) => {
    if (event.persisted) {
      next = 0;
      poll();
    }
  });
  clock();
  setInterval(clock, 1000);
  poll();
})();
```

## `static/empiredrop.css`

```css
/* Keep RedHunllef's established charcoal/red palette, with responsive tabs. */
.provider-tabs { display: flex; flex-wrap: wrap; align-items: center; gap: 10px; margin: 0 0 20px; }
.provider-tabs [role="tab"] { min-height: 44px; border: 1px solid var(--line); background: var(--panel); color: var(--muted); }
.provider-tabs [role="tab"].active { border-color: var(--accent); background: #431c2a; color: var(--text); box-shadow: inset 0 -2px var(--brand); }
.provider-tabs [role="tab"]:focus-visible { outline: 3px solid var(--accent); outline-offset: 3px; }
.empire-sponsor .sponsor-symbol { color: #ffb6bf; background: #361622; }
.empire-podium { margin-top: 20px; }
.empire-podium .podium-values { grid-template-columns: 1fr 1fr; }
.empire-podium .podium-name { min-height: 1.2em; }
#empireBoard .section-title { margin-top: 20px; }
#empireBoard .leaderboard-foot { margin-bottom: 30px; }
#shuffleBoard[hidden], #empireBoard[hidden] { display: none !important; }
@media (max-width: 700px) {
  .provider-tabs { display:grid; grid-template-columns: 1fr 1fr; gap:8px; }
  .provider-tabs .button { font-size:.83rem; white-space: normal; padding: 10px 6px; }
  .empire-sponsor { min-width: 0; }
  #empireBoard > .section-title { flex-wrap:wrap; }
  #empireBoard .public-table table { min-width: 0; }
}
/* Only the selected provider's race schedule is visible. */
#shuffleRaceClock[hidden], #empireRaceClock[hidden] {display:none!important}

/* EmpireDrop now mirrors Shuffle's two-column wager/prize presentation. */
#empireBoard .public-table td:last-child {font-variant-numeric:tabular-nums}
#empireBoard .podium-values small {line-height:1.2}
#empireBoard .podium-values strong {overflow-wrap:anywhere}
@media (max-width:520px){.empire-podium .podium-values{grid-template-columns:1fr 1fr}}

.empire-history-list{display:grid;gap:8px}
.empire-history-row{padding:12px;border:1px solid var(--line);border-radius:10px;display:grid;gap:5px}
.empire-history-row small{color:var(--muted)}

/* Mirror Shuffle's source status; hide the inactive provider status cleanly. */
#shuffleSourceStatus[hidden], #empireSourceStatus[hidden] {display:none!important}
#empireSourceStatus small {font-variant-numeric:tabular-nums}
@media (max-width:700px) { #empireSourceStatus {text-align:left;align-items:flex-start} }
```

## `static/empiredrop.js`

```javascript
/* Uniform public provider switcher. The browser renders only the server's
 * sanitized /public-state projection; credentials never reach this file. */
(() => {
  'use strict';
  const id = value => document.getElementById(value);
  const shuffleTab = id('shuffleTab');
  const empireTab = id('empireTab');
  if (!shuffleTab || !empireTab) return;

  const tabs = [shuffleTab, empireTab];
  let latest = null;
  let serverOffset = 0;
  let countdownTimer = null;
  const isEmpire = () => empireTab.getAttribute('aria-selected') === 'true';
  const date = unix => unix
    ? new Intl.DateTimeFormat('en-US', {timeZone:'America/New_York', dateStyle:'medium', timeStyle:'short'}).format(new Date(unix*1000)) + ' ET'
    : 'Schedule pending';

  function selectedProvider() {
    return isEmpire() ? 'empiredrop' : 'shuffle';
  }

  function rememberProvider(provider) {
    try { localStorage.setItem('rh.public.provider', provider); } catch {}
    try {
      const url = new URL(location.href);
      if (provider === 'empiredrop') url.searchParams.set('provider', 'empiredrop');
      else url.searchParams.delete('provider');
      history.replaceState(null, '', url);
    } catch {}
  }

  function updateProviderChrome() {
    const empire = isEmpire();
    if (id('shuffleRaceClock')) id('shuffleRaceClock').hidden = empire;
    if (id('empireRaceClock')) id('empireRaceClock').hidden = !empire;
    document.querySelectorAll('[data-provider-brand]').forEach(card => {
      card.classList.toggle('is-selected', card.dataset.providerBrand === selectedProvider());
    });
    const join = id('providerJoinLink');
    if (join) {
      join.href = empire ? 'https://empiredrop.com/c/red' : (id('sponsorLink')?.href || '#');
      join.textContent = empire ? 'Join on EmpireDrop ↗' : 'Join on Shuffle ↗';
    }
  }

  function select(tab, focus=false, remember=true) {
    for (const current of tabs) {
      const active = current === tab;
      current.setAttribute('aria-selected', String(active));
      current.tabIndex = active ? 0 : -1;
      current.classList.toggle('active', active);
      const panel = id(current.getAttribute('aria-controls'));
      if (panel) panel.hidden = !active;
    }
    updateProviderChrome();
    updateCountdowns();
    if (remember) rememberProvider(selectedProvider());
    if (focus) tab.focus();
  }

  tabs.forEach((tab, index) => {
    tab.addEventListener('click', () => select(tab));
    tab.addEventListener('keydown', event => {
      if (!['ArrowLeft','ArrowRight','Home','End'].includes(event.key)) return;
      event.preventDefault();
      const next = event.key === 'Home' ? 0 : event.key === 'End' ? tabs.length-1 :
        (index + (event.key === 'ArrowRight' ? 1 : -1) + tabs.length) % tabs.length;
      select(tabs[next], true);
    });
  });

  function renderHistory(board) {
    const history = id('empireHistoryList');
    if (!history) return;
    const snapshots = Array.isArray(board.history) ? board.history.slice(0, 4) : [];
    history.replaceChildren();
    if (!snapshots.length) {
      history.append(Object.assign(document.createElement('p'), {
        className:'small muted', textContent:'No completed race snapshots saved yet.'
      }));
      return;
    }
    for (const item of snapshots) {
      const row = document.createElement('article');
      row.className = 'empire-history-row';
      const name = document.createElement('strong');
      name.textContent = item.name || 'Previous race';
      const info = document.createElement('small');
      info.textContent = `${date(item.updated_at)} · ${item.rows?.length || 0} saved players`;
      row.append(name, info);
      history.append(row);
    }
  }

  function render(board) {
    if (!board || !Array.isArray(board.rows)) return;
    latest = board;
    if (Number.isFinite(Number(board.server_time))) serverOffset = Number(board.server_time) - Date.now()/1000;
    const rows = board.rows.slice(0, 10);
    const rewards = board.prizes || {};
    const configured = rewards.enabled === true;
    const providerLimit = Number(board.race_meta?.ranks_limit);
    const displayLimit = Number.isInteger(providerLimit) && providerLimit > 0 ? Math.min(10, providerLimit) : 10;

    for (let position=1; position<=10; position++) {
      const row = rows[position-1];
      const unreported = !row && position > displayLimit;
      const name = document.querySelector(position <= 3
        ? `[data-empire-name="${position}"]`
        : `[data-empire-row-name="${position}"]`);
      const amount = document.querySelector(position <= 3
        ? `[data-empire-wager="${position}"]`
        : `[data-empire-row-wager="${position}"]`);
      const place = id('empireBoard')?.querySelector(`[data-empire-place="${position}"]`);
      const prize = document.querySelector(position <= 3
        ? `[data-empire-prize="${position}"]`
        : `[data-empire-row-prize="${position}"]`);
      if (name) name.textContent = row?.username || (unreported ? 'Unavailable' : 'Open position');
      if (amount) amount.textContent = row?.wager || '—';
      if (place) place.textContent = String(row?.rank ?? position).padStart(2, '0');
      if (prize) {
        const serverPrize = row?.prize;
        const prizeRank = String(row?.rank ?? position);
        prize.textContent = serverPrize && serverPrize !== '—'
          ? serverPrize
          : configured ? (rewards.formatted?.[prizeRank] || '—') : 'Not announced';
      }
    }

    if (id('empirePoolTotal')) id('empirePoolTotal').textContent = configured ? rewards.total : 'Not announced';
    if (board.schedule && id('empireRaceWindow')) {
      id('empireRaceWindow').textContent = `${board.schedule.start_et || ''} → ${board.schedule.end_et || ''}`;
    }
    const coverage = id('empireRankingCoverage');
    if (coverage) {
      coverage.textContent = providerLimit > 0 && providerLimit < 10
        ? `EmpireDrop currently exposes ${providerLimit} official positions for this race.`
        : rows.length < 10 ? 'Open positions will appear when activity is reported.' : '';
      coverage.hidden = !coverage.textContent;
    }
    const message = id('empireMessage');
    if (message) {
      message.textContent = rows.length ? '' : (board.updated_at ? 'Showing the most recent standings.' : 'Standings are temporarily unavailable.');
      message.hidden = rows.length > 0;
    }
    renderHistory(board);
    updateProviderChrome();
    updateCountdowns();
  }

  function countdownState(start, end, now) {
    if (!Number.isFinite(start) || !Number.isFinite(end) || !start || !end || end <= start)
      return {state:'unconfigured', label:'RACE SCHEDULE', text:'Set the race dates'};
    if (now >= end) return {state:'ended', label:'RACE SCHEDULE', text:'Race complete'};
    const upcoming = now < start;
    let seconds = Math.max(0, Math.ceil((upcoming ? start : end) - now));
    const days = Math.floor(seconds/86400); seconds %= 86400;
    const hours = Math.floor(seconds/3600); seconds %= 3600;
    const minutes = Math.floor(seconds/60); seconds %= 60;
    return {
      state: upcoming ? 'upcoming' : 'active',
      label: upcoming ? 'STARTS IN' : 'RACE ENDS IN',
      text:`${days}d ${String(hours).padStart(2,'0')}h ${String(minutes).padStart(2,'0')}m ${String(seconds).padStart(2,'0')}s`
    };
  }

  function updateCountdowns() {
    if (!latest || !id('empireCountdown')) return;
    const now = Math.floor(Date.now()/1000 + serverOffset);
    const schedule = latest.schedule || {};
    const value = countdownState(Number(schedule.start_time), Number(schedule.end_time), now);
    id('empireCountdown').textContent = value.text;
    if (id('empireClockLabel')) id('empireClockLabel').textContent = value.label;
    if (id('empireRaceBadge')) {
      id('empireRaceBadge').textContent = value.state.charAt(0).toUpperCase()+value.state.slice(1);
      id('empireRaceBadge').className = 'badge state-'+value.state;
    }
  }

  document.addEventListener('empiredrop:update', event => render(event.detail));
  countdownTimer = setInterval(updateCountdowns, 1000);
  globalThis.addEventListener?.('pagehide', () => clearInterval(countdownTimer), {once:true});

  try {
    const bootstrap = JSON.parse(document.body.dataset.bootstrap || '{}');
    render({...bootstrap.empiredrop, server_time:bootstrap.server_time});
  } catch {}

  let requested = '';
  try { requested = new URL(location.href).searchParams.get('provider') || localStorage.getItem('rh.public.provider') || ''; } catch {}
  select(requested === 'empiredrop' ? empireTab : shuffleTab, false, false);
})();
```

## `static/experience.css`

```css
/* Shared visual contract. Game math, cards and saved state live outside CSS. */
:root {
  --bg: #100e12;
  --panel: #1a171e;
  --panel-high: #242029;
  --line: #3a303a;
  --text: #fcf7f8;
  --muted: #c2b4bd;
  --brand: #ff2d2d;
  --accent: #ff858f;
  --action: #c51e35;
  --positive: #95dcc0;
  --negative: #ff9ba8;
  --radius: 14px;
  --motion-fast: 150ms;
  --motion-reveal: 240ms;
  font-size: 16px;
}
body {
  background:
    radial-gradient(ellipse at 85% 0%, #54152229, transparent 42rem), var(--bg);
}
button,
.button,
input:not([type="hidden"]),
select {
  min-height: 44px;
}
.button,
button,
a {
  -webkit-tap-highlight-color: transparent;
}
.button {
  border-radius: 10px;
  font-weight: 650;
  transition:
    background-color var(--motion-fast),
    border-color var(--motion-fast);
}
.button.primary {
  background: var(--action);
  color: #fff;
  border-color: var(--action);
}
.button.primary:hover:not(:disabled) {
  background: #a7192e;
  border-color: #ff6474;
}
button:disabled {
  cursor: default;
}
button[aria-busy="true"] {
  cursor: progress;
}
input,
select,
textarea {
  border-radius: 9px;
  color: var(--text);
  accent-color: var(--brand);
}
input[type="range"] {
  touch-action: pan-y;
}
input:focus-visible,
select:focus-visible,
button:focus-visible,
a:focus-visible,
summary:focus-visible {
  outline: 3px solid #ff9fa8;
  outline-offset: 3px;
}
input[aria-invalid="true"] {
  border-color: var(--negative);
}
.small,
.points-wallet small {
  font-size: 0.875rem;
}
.eyebrow {
  font-size: 0.7rem;
  letter-spacing: 0.12em;
}
.muted {
  color: var(--muted);
}
.panel {
  border-color: var(--line);
  box-shadow: 0 8px 28px #00000018;
}
.section-title h2 {
  margin-bottom: 0;
}
.number,
output,
.stat-value,
.clock {
  font-variant-numeric: tabular-nums;
}
.site-header {
  background: #151118f5;
  border-bottom: 1px solid #492631;
}
.site-header .section-nav {
  min-height: 44px;
  display: inline-flex;
  align-items: center;
  justify-content: center;
}
.site-header [aria-current="page"] {
  background: #ff394014;
  color: #ff9ba8;
  border-bottom-color: var(--brand);
}
.brand-sub {
  letter-spacing: 0.13em;
}
.hero {
  padding-top: 38px;
  padding-bottom: 30px;
}
.hero h1 {
  font-size: clamp(2rem, 4.5vw, 3.4rem);
}
.podium-card.place-1 {
  border-color: #b83a4d;
  background: linear-gradient(160deg, #421c29, #201720);
}
.podium-name {
  overflow-wrap: anywhere;
}
.public-table th,
.bet-history th {
  color: #cfbec7;
}
.public-table td,
.bet-history td {
  border-bottom-color: #332a34;
}
progress {
  accent-color: var(--brand);
}
.game-switcher {
  display: none;
}
.gaming-heading {
  gap: 24px;
  margin-bottom: 20px;
}
.gaming-heading h1 {
  font-size: clamp(2rem, 4vw, 3rem);
}
.points-wallet {
  padding: 16px 20px;
  min-width: 285px;
  background: linear-gradient(135deg, #381b29, #211920);
  border-color: #803047;
  gap: 4px;
}
.points-wallet > strong {
  font-size: 1.9rem;
  line-height: 1.2;
}
.wallet-detail {
  display: flex;
  gap: 20px;
  color: var(--muted);
  font-size: 0.8rem;
}
.wallet-detail b {
  color: var(--text);
  font-weight: 600;
  padding-left: 5px;
}
.points-wallet #pointsReset {
  font-size: 0.75rem;
}
.gaming-identity {
  gap: 8px 16px;
  margin: 14px 0;
  font-size: 0.875rem;
}
.points-note {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 8px;
  margin: 10px 0;
  font-size: 0.8rem;
}
.round-state {
  display: inline-flex;
  align-items: center;
  gap: 6px;
}
.round-state:before {
  content: "";
  width: 6px;
  height: 6px;
  border-radius: 50%;
  background: var(--positive);
}
[data-play-state="submitting"] .round-state:before,
[data-play-state="recovery"] .round-state:before {
  background: var(--warning);
}
[data-play-state="error"] .round-state:before {
  background: var(--negative);
}
#pokerResume,
#blackjackResume {
  display: flex;
  justify-content: space-between;
  align-items: center;
  gap: 16px;
}
.game-card {
  padding: 16px;
  border-radius: var(--radius);
  background: #1a171e;
}
.game-card h2 {
  font-size: 1.2rem;
  margin: 12px 0;
}
.game-card .game-art {
  height: 146px;
  margin: 0;
  background-color: #23121b;
}
.game-card:hover {
  border-color: #d8495f;
  background: #221a23;
  color: var(--text);
}
.game-card .button {
  margin-top: 0;
}
.game-stat-cards article {
  padding: 14px;
}
.game-stat-cards small {
  font-size: 0.8rem;
}
[data-tone="positive"] b,
b[data-tone="positive"],
[data-tone="positive"] td:nth-child(4) {
  color: var(--positive);
}
[data-tone="negative"] b,
b[data-tone="negative"],
[data-tone="negative"] td:nth-child(4) {
  color: var(--negative);
}
[data-tone="neutral"] b,
b[data-tone="neutral"] {
  color: var(--muted);
}
.game-layout {
  border-radius: 18px;
  background: #17131a;
}
.bet-controls {
  background: #221c26;
}
.bet-controls label,
.bet-controls legend {
  color: #eee0e7;
}
.game-board {
  min-width: 0;
}
.game-result {
  min-height: 54px;
  display: grid;
  place-items: center;
  font-variant-numeric: tabular-nums;
}
.game-result.is-win {
  color: var(--positive);
  border-color: #31634c;
  background: #21433433;
}
#betProof {
  display: block;
  min-height: 24px;
  font-size: 0.8rem;
}
.gaming-bet-status {
  min-height: 24px;
  margin-bottom: 8px;
}
.risk-options label span {
  min-height: 44px;
}
.bet-history {
  margin-bottom: 24px;
}
.bet-history td {
  padding-top: 12px;
  padding-bottom: 12px;
}
.bet-history button {
  min-width: 68px;
}
.history-toggle {
  margin-top: 14px;
}
.holdem-controls {
  border-radius: 12px;
  padding: 12px;
  background: #221821;
  border: 1px solid #613046;
}
.holdem-moves {
  gap: 8px;
}
.holdem-raise-input input {
  min-width: 0;
}
.holdem-seat-label small,
.holdem-street {
  color: #d8c4cf;
}
.holdem-card-slot {
  border-color: #71505e;
}
.health-panel {
  padding: 24px;
  margin-bottom: 20px;
}
.health-panel > .section-title {
  margin-bottom: 18px;
}
.health-grid {
  display: grid;
  grid-template-columns: repeat(5, minmax(0, 1fr));
  gap: 10px;
}
.health-card {
  display: flex;
  flex-direction: column;
  align-items: flex-start;
  gap: 8px;
  min-width: 0;
  border: 1px solid var(--line);
  background: #211a24;
  border-radius: 10px;
  padding: 15px;
}
.health-card > strong {
  font-size: 0.95rem;
}
.health-card p {
  font-size: 0.85rem;
  color: var(--muted);
  margin: 0;
  flex: 1;
}
.health-card small {
  font-size: 0.75rem;
}
.health-card[data-state="good"] > strong {
  color: var(--positive);
}
.health-card[data-state="warning"] > strong {
  color: var(--warning);
}
.health-card[data-state="error"] > strong {
  color: var(--negative);
}
.health-measurements {
  margin-top: 18px;
}
.health-measurements summary {
  cursor: pointer;
  padding: 10px 0;
  min-height: 44px;
}
.health-metrics {
  display: grid;
  grid-template-columns: repeat(3, minmax(0, 1fr));
  gap: 12px;
  padding: 14px 0;
}
.health-metrics div {
  display: grid;
  gap: 4px;
}
.health-metrics span {
  color: var(--muted);
  font-size: 0.8rem;
}
.health-metrics strong {
  font-size: 0.95rem;
  overflow-wrap: anywhere;
}
.recovery-reminder {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 20px;
  gap: 20px;
  margin-bottom: 24px;
  border-color: #685434;
}
.recovery-reminder p {
  margin: 4px 0;
  font-size: 0.9rem;
}
.recovery-reminder small {
  color: var(--muted);
}
.recovery-reminder .button {
  flex-shrink: 0;
}
.recovery-review th,
.recovery-review td {
  text-align: left;
}
.history-weeks a {
  border-radius: 12px;
  min-height: 92px;
}
.history-weeks [aria-current="page"] {
  border-color: #c9495d;
  background: #391b28;
}
.history-meta {
  font-size: 0.85rem;
}






.badge-grid {
  gap: 10px;
}
.badge-grid li {
  border-radius: 10px;
  padding: 12px;
}
.badge-grid li.earned {
  border-color: #6c5364;
  background: #34232f;
}
.badge-grid small {
  font-size: 0.8rem;
}
.footer {
  padding-top: 24px;
  padding-bottom: 24px;
}
@media (max-width: 1050px) {
  .health-grid {
    grid-template-columns: repeat(3, minmax(0, 1fr));
  }
  .header-inner {
    gap: 14px;
  }
}
@media (max-width: 680px) {
  .shell {
    padding-left: 16px;
    padding-right: 16px;
  }
  .header-inner {
    gap: 4px;
    padding-top: 7px;
    padding-bottom: 4px;
  }
  .site-header .brand img {
    width: 27px;
    height: 27px;
  }
  .site-header .brand {
    min-height: 30px;
    font-size: 0.9rem;
  }
  .brand-sub {
    display: none;
  }
  .site-header nav {
    gap: 2px 4px;
    grid-template-columns: repeat(3, minmax(0, 1fr));
  }
  .site-header nav a,
  .site-header nav .button {
    min-height: 44px;
    padding: 5px 6px;
    font-size: 0.77rem;
    line-height: 1.2;
  }
  .hero {
    padding-top: 24px;
    padding-bottom: 20px;
    gap: 20px;
  }
  .hero h1 {
    font-size: 2rem;
  }
  .hero .lead {
    font-size: 1rem;
    margin-bottom: 16px;
  }

  .gaming-page {
    padding-top: 18px;
    padding-bottom: 24px;
  }
  .gaming-heading {
    display: block;
    margin-bottom: 12px;
  }
  .gaming-heading .eyebrow {
    margin-bottom: 4px;
  }
  .gaming-heading h1 {
    font-size: 1.75rem;
    margin: 0 0 12px;
  }
  .points-wallet {
    min-width: 0;
    padding: 12px 14px;
    display: grid;
    grid-template-columns: 1fr 1fr;
    column-gap: 8px;
  }
  .points-wallet > .eyebrow {
    font-size: 0.64rem;
    margin: 0;
  }
  .points-wallet > strong {
    grid-column: 1;
    grid-row: 2;
    font-size: 1.55rem;
  }
  .wallet-detail {
    grid-column: 2;
    grid-row: 1/3;
    display: grid;
    align-content: center;
    gap: 3px;
    text-align: right;
    font-size: 0.75rem;
  }
  .points-wallet #pointsReset {
    grid-column: 1/-1;
    font-size: 0.7rem;
  }
  .js .gaming-page .game-nav {
    display: none;
  }
  .js .game-switcher {
    display: flex;
    align-items: center;
    gap: 10px;
    font-size: 0.8rem;
  }
  .game-switcher select {
    flex: 1;
    min-width: 0;
  }
  .game-switcher > label {
    margin: 0;
  }
  .game-switcher a {
    min-height: 44px;
    display: inline-flex;
    align-items: center;
  }
  .gaming-identity {
    font-size: 0.8rem;
    gap: 4px 10px;
    margin: 8px 0 12px;
  }
  .gaming-identity > span {
    flex-basis: 100%;
  }
  .points-note {
    font-size: 0.75rem;
  }
  .game-cards {
    grid-template-columns: repeat(2, minmax(0, 1fr));
    gap: 10px;
  }
  .game-card {
    display: block;
    padding: 10px;
    min-width: 0;
  }
  .game-card .game-art {
    width: 100%;
    height: 110px;
    margin: 0;
  }
  .game-card h2 {
    font-size: 0.98rem;
    min-height: 1.6em;
    margin: 10px 0;
    gap: 4px;
  }
  .game-card .button {
    padding: 8px;
    font-size: 0.8rem;
  }
  .game-card .dice-art {
    font-size: 70px;
    gap: 0;
  }
  .game-card .dice-art span:last-child {
    font-size: 55px;
  }
  .game-card .blackjack-art span {
    font-size: 20px;
    padding: 12px 7px;
  }
  .game-card .mini-keno {
    padding: 9px;
    gap: 4px;
  }
  .game-card .plinko-art {
    padding: 16px 5px;
    font-size: 27px;
  }
  .game-stat-cards {
    grid-template-columns: repeat(2, minmax(0, 1fr));
    gap: 8px;
  }
  .game-stat-cards article {
    padding: 10px;
  }
  .game-layout {
    overflow: visible;
  }
  .game-board {
    padding: 12px;
  }
  .bet-controls {
    padding: 16px;
    border-radius: 0 0 17px 17px;
  }
  .keno-board {
    grid-template-columns: repeat(5, minmax(0, 1fr));
    gap: 7px;
  }
  .keno-board button {
    min-height: 44px;
  }
  .holdem-table {
    padding: 12px 8px;
  }
  .holdem-controls {
    position: sticky;
    bottom: 8px;
    z-index: 5;
    box-shadow: 0 4px 16px #0008;
  }
  .holdem-moves {
    display: grid;
    grid-template-columns: repeat(2, minmax(0, 1fr));
    gap: 6px;
  }
  .holdem-moves .button {
    font-size: 0.8rem;
    padding: 8px 5px;
  }
  .holdem-raise .button {
    font-size: 0.8rem;
  }
  .blackjack-actions {
    position: sticky;
    bottom: 8px;
    z-index: 5;
    background: #221821;
    padding: 8px;
    border-radius: 10px;
  }
  .bet-history,
  .game-season {
    padding: 16px;
  }
  .bet-history th,
  .bet-history td {
    padding-left: 8px;
    padding-right: 8px;
    font-size: 0.78rem;
  }
  .bet-history table {
    width: 100%;
    min-width: 0;
    table-layout: fixed;
  }
  .bet-history th,
  .bet-history td {
    padding: 10px 4px;
    white-space: normal;
    overflow-wrap: anywhere;
  }
  .bet-history th {
    font-size: 0.64rem;
    letter-spacing: 0.02em;
  }
  .bet-history button {
    min-width: 0;
    width: 100%;
    font-size: 0.78rem;
  }
  .bet-history .section-title h2 {
    font-size: 1.25rem;
  }
  .health-panel {
    padding: 16px;
  }
  .health-panel > .section-title {
    align-items: flex-start;
    gap: 14px;
    flex-direction: column;
  }
  .health-grid {
    grid-template-columns: repeat(2, minmax(0, 1fr));
  }
  .health-card {
    padding: 12px;
  }
  .health-card:last-child {
    grid-column: 1/-1;
  }
  .health-metrics {
    grid-template-columns: repeat(2, minmax(0, 1fr));
  }
  .recovery-reminder {
    align-items: flex-start;
    flex-direction: column;
    gap: 12px;
    padding: 16px;
  }
  .history-picker-row select {
    min-width: 0;
  }
  .site-header:has(.section-nav) .header-inner {
    display: grid;
    grid-template-columns: repeat(3, minmax(0, 1fr));
    gap: 3px 4px;
  }
  .site-header:has(.section-nav) .header-inner > .brand {
    grid-column: 1/3;
    grid-row: 1;
  }
  .site-header:has(.section-nav) nav {
    display: contents;
  }
  .site-header:has(.section-nav) nav > .button {
    grid-column: 3;
    grid-row: 1;
  }
}
@media (prefers-reduced-motion: reduce) {
  html {
    scroll-behavior: auto;
  }
  *,
  *::before,
  *::after {
    scroll-behavior: auto !important;
    animation-duration: 0.01ms !important;
    animation-iteration-count: 1 !important;
    transition-duration: 0.01ms !important;
  }
}

/* Community clarity: primary tasks first; optional details stay in native disclosures. */
.visually-hidden {
  position: absolute !important;
  width: 1px;
  height: 1px;
  padding: 0;
  margin: -1px;
  overflow: hidden;
  clip-path: inset(50%);
  white-space: nowrap;
  border: 0;
}
#inviteProgress,
.source-status {
  min-height: 42px;
  font-variant-numeric: tabular-nums;
}
#playerNameResult,
#gamingGrantMessage,
#hitResult {
  min-height: 1.4em;
}
.player-identity {
  align-items: center;
  gap: 12px;
}
.player-identity .text-button {
  min-height: 44px;
  display: inline-flex;
  align-items: center;
}
.admin-heading {
  margin-bottom: 18px;
}
.admin-main .button {
  max-width: 100%;
  white-space: normal;
  overflow-wrap: anywhere;
  text-align: center;
}
.admin-heading h1 {
  font-size: clamp(1.7rem, 3vw, 2.5rem);
}
.admin-attention {
  margin: 18px 0;
  padding: 14px 18px;
  border: 1px solid var(--line);
  border-radius: var(--radius);
  background: #1b1920;
}
.attention-heading {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
}
.attention-heading > strong {
  font-size: 0.9rem;
  color: var(--positive);
}
.admin-attention[data-state="warning"] {
  border-color: #806645;
  background: #30251c66;
}
.admin-attention[data-state="warning"] .attention-heading > strong {
  color: var(--warning);
}
#adminIssueList {
  padding-left: 18px;
  margin: 10px 0 0;
  font-size: 0.85rem;
  color: var(--muted);
}
#adminIssueList li + li {
  margin-top: 5px;
}
.admin-attention #networkError {
  margin: 10px 0 0;
  border: 0;
  padding: 0;
  background: transparent;
}
.overview-stats {
  margin-bottom: 16px;
}
.overview-stats .stat {
  display: flex;
  flex-direction: column;
  gap: 8px;
}
.overview-stats .stat .stat-value {
  font-size: clamp(1.25rem, 2.2vw, 1.7rem);
  margin: 4px 0;
  overflow-wrap: anywhere;
}
.overview-stats .stat p {
  margin: 0;
  font-size: 0.85rem;
}
.overview-stats .stat a {
  margin-top: auto;
  padding-top: 8px;
  min-height: 44px;
}
.overview-stats .stat small {
  font-size: 0.8rem;
  font-weight: 400;
}




.admin-quick-actions {
  display: flex;
  gap: 8px;
  flex-wrap: wrap;
  margin: 0 0 22px;
}
.recovery-reminder {
  padding: 14px 18px;
}
.recovery-reminder strong {
  font-size: 0.9rem;
}
.recovery-reminder p {
  font-size: 0.8rem;
}
.admin-diagnostics {
  margin: 24px 0;
}
.admin-diagnostics > summary,
.gaming-tools > summary {
  display: flex;
  justify-content: space-between;
  align-items: center;
  cursor: pointer;
  padding: 18px 20px;
  gap: 16px;
  min-height: 56px;
}
.admin-diagnostics > summary small,
.gaming-tools > summary small {
  display: block;
  color: var(--muted);
  font-size: 0.8rem;
  font-weight: 400;
  margin-top: 4px;
}
.diagnostics-content {
  padding: 0 20px 20px;
}
.diagnostics-content .health-panel {
  padding: 18px;
}
.diagnostics-content .connection-summary {
  min-height: 60px;
}
.gaming-tools {
  margin: 14px 0;
}
.gaming-tools > .details-content {
  padding: 0 20px 20px;
}
.ranking-toolbar,
.ranking-toolbar > div {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 10px;
  flex-wrap: wrap;
}
.ranking-toolbar {
  margin-bottom: 16px;
}
.ranking-toolbar p {
  margin: 0;
}
.gaming-admin-cards {
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 16px;
}
.gaming-admin-cards > section {
  padding: 18px;
}
.ranking-card-heading {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
}
.ranking-card-heading h3 {
  margin: 0;
}
.gaming-leaders {
  list-style: none;
  padding: 0;
  margin: 8px 0 0;
}
.gaming-admin-cards .gaming-leaders li {
  padding: 0;
}
.player-breakdown > summary {
  display: grid;
  grid-template-columns: minmax(0, 1fr) auto;
  gap: 10px;
  align-items: center;
  cursor: pointer;
  min-height: 54px;
  padding: 9px 0;
  list-style: none;
}
.player-breakdown > summary::-webkit-details-marker {
  display: none;
}
.leader-name {
  display: flex;
  align-items: center;
  gap: 9px;
  min-width: 0;
}
.leader-name > small {
  font-size: 0.75rem;
  min-width: 12px;
  text-align: center;
}
.leader-name > strong {
  font-size: 0.87rem;
  overflow-wrap: anywhere;
}
.player-breakdown summary b {
  font-size: 0.85rem;
  font-variant-numeric: tabular-nums;
  text-align: right;
}
.player-breakdown summary b > small {
  display: inline;
  font-size: 0.7rem;
}
.player-breakdown summary b:after {
  content: "⌄";
  display: inline-block;
  color: var(--muted);
  margin-left: 7px;
}
.player-breakdown[open] summary b:after {
  content: "⌃";
}
.gaming-admin-cards [data-tone="positive"] b {
  color: var(--positive);
}
.gaming-admin-cards [data-tone="negative"] b {
  color: var(--negative);
}
.player-record {
  display: grid;
  gap: 5px;
  padding: 4px 8px 14px 22px;
  color: var(--muted);
  overflow-wrap: anywhere;
}
.player-record small {
  margin: 0;
  font-size: 0.77rem;
  line-height: 1.5;
}














@media (max-width: 900px) {
  .overview-stats {
    grid-template-columns: 1fr;
  }
}
@media (max-width: 680px) {
.admin-attention {
    padding: 12px;
  }
  .attention-heading {
    align-items: flex-start;
    flex-wrap: wrap;
    gap: 4px;
  }
  .admin-quick-actions .button {
    flex-grow: 1;
  }
  .gaming-admin-cards {
    grid-template-columns: 1fr;
  }
  .gaming-admin-cards > section {
    padding: 14px;
  }
  .gaming-tools > summary,
  .admin-diagnostics > summary {
    padding: 16px;
  }
  .diagnostics-content {
    padding: 0 12px 12px;
  }
  .diagnostics-content .health-panel {
    padding: 12px;
  }
  .diagnostics-content .health-grid {
    grid-template-columns: 1fr;
  }
  .player-breakdown summary b {
    font-size: 0.8rem;
  }


}
```

## `static/experience.js`

```javascript
/* Small shared enhancements. Native links and forms still work without JS. */
(() => {
  "use strict";
  document.documentElement.classList.add("js");
  // Deep links to a recovery form or diagnostics must reveal their ancestors.
  function revealAnchor() {
    let key;
    try {
      key = decodeURIComponent(location.hash.slice(1));
    } catch {
      return;
    }
    const target = document.getElementById(key);
    if (!target) return;
    let opened = false;
    for (let node = target; node; node = node.parentElement) {
      if (node.tagName === "DETAILS" && !node.open) {
        node.open = true;
        opened = true;
      }
    }
    if (opened)
      requestAnimationFrame(() => target.scrollIntoView({ block: "start" }));
  }
  addEventListener("hashchange", revealAnchor);
  revealAnchor();
  const select = document.getElementById("gameSelect");
  select?.addEventListener("change", () => {
    // Values are local template-owned routes, never arbitrary redirect inputs.
    if (
      /^\/gaming(?:\/(dice|keno|plinko|blackjack|limbo|coinflip|poker|baccarat))?$/.test(
        select.value,
      )
    )
      location.assign(select.value);
  });
})();
```

## `static/fairness.js`

```javascript
/* Independent RedPoints v1–v5 verifier. Uses Web Crypto and integer arithmetic.
   No API call, wallet mutation, or provider dependency is involved. */
(() => {
  "use strict";
  const VERSION = "redpoints-v5",
    SCALE = 10000n;
  const SUPPORTED_VERSIONS = ["redpoints-v1", "redpoints-v2", "redpoints-v3", "redpoints-v4", VERSION];
  const PLINKO_TABLES = {
    8: {
      low: [56000, 21000, 11000, 10000, 5000, 10000, 11000, 21000, 56000],
      medium: [130000, 30000, 13000, 7000, 4000, 7000, 13000, 30000, 130000],
      high: [290000, 40000, 15000, 3000, 2000, 3000, 15000, 40000, 290000],
    },
    12: {
      low: [
        100000, 30000, 16000, 14000, 11000, 10000, 5000, 10000, 11000, 14000,
        16000, 30000, 100000,
      ],
      medium: [
        330000, 110000, 40000, 20000, 11000, 6000, 3000, 6000, 11000, 20000,
        40000, 110000, 330000,
      ],
      high: [
        1700000, 240000, 81000, 20000, 7000, 2000, 2000, 2000, 7000, 20000,
        81000, 240000, 1700000,
      ],
    },
    16: {
      low: [
        160000, 90000, 20000, 14000, 14000, 12000, 11000, 10000, 5000, 10000,
        11000, 12000, 14000, 14000, 20000, 90000, 160000,
      ],
      medium: [
        1100000, 410000, 100000, 50000, 30000, 15000, 10000, 5000, 3000, 5000,
        10000, 15000, 30000, 50000, 100000, 410000, 1100000,
      ],
      high: [
        10000000, 1300000, 260000, 90000, 40000, 20000, 2000, 2000, 2000, 2000,
        2000, 20000, 40000, 90000, 260000, 1300000, 10000000,
      ],
    },
  };
  const hex = (bytes) =>
    [...new Uint8Array(bytes)]
      .map((n) => n.toString(16).padStart(2, "0"))
      .join("");
  const bytes = (value) => {
    if (!/^[a-f0-9]{64}$/.test(value)) throw Error("Invalid server seed");
    return new Uint8Array(value.match(/../g).map((n) => parseInt(n, 16)));
  };
  const canonical = (value) =>
    JSON.stringify(value, (_, item) =>
      item && typeof item === "object" && !Array.isArray(item)
        ? Object.fromEntries(
            Object.keys(item)
              .sort()
              .map((key) => [key, item[key]]),
          )
        : item,
    );
  function comb(n, k) {
    let out = 1n;
    for (let i = 1; i <= k; i++) out = (out * BigInt(n - i + 1)) / BigInt(i);
    return out;
  }
  function table(game, size, risk, version = VERSION) {
    if (!SUPPORTED_VERSIONS.includes(version))
      throw Error("Unknown game rules version");
    if (game === "plinko" && version !== "redpoints-v1") {
      const values = PLINKO_TABLES[size]?.[risk];
      if (!values) throw Error("Unknown Plinko board");
      return [...values];
    }
    const power = { low: 2n, medium: 4n, high: 7n }[risk];
    if (!power) throw Error("Unknown risk level");
    const denom = game === "keno" ? comb(40, 10) : 2n ** BigInt(size);
    const weights = [],
      probs = [];
    for (let i = 0; i <= size; i++) {
      weights.push(
        game === "keno"
          ? BigInt(i) ** power
          : 1n + 2n * BigInt(Math.abs(2 * i - size)) ** power,
      );
      probs.push(
        game === "keno"
          ? comb(size, i) * comb(40 - size, 10 - i)
          : comb(size, i),
      );
    }
    const sum = weights.reduce((n, w, i) => n + w * probs[i], 0n);
    return weights.map((w) => Number((99n * w * denom * SCALE) / (100n * sum)));
  }
  async function draw(seed, receipt) {
    const key = await crypto.subtle.importKey(
      "raw",
      bytes(seed),
      { name: "HMAC", hash: "SHA-256" },
      false,
      ["sign"],
    );
    let block = 0,
      data = new Uint8Array(0),
      pos = 0;
    const context = [
      receipt.rules_version || VERSION,
      receipt.season,
      receipt.game,
      receipt.client_seed,
      receipt.client_salt,
      receipt.nonce,
      receipt.wager,
      receipt.options,
    ];
    return async (size) => {
      const limit = 4294967296 - (4294967296 % size);
      while (true) {
        if (pos >= data.length) {
          data = new Uint8Array(
            await crypto.subtle.sign(
              "HMAC",
              key,
              new TextEncoder().encode(canonical([...context, block++])),
            ),
          );
          pos = 0;
        }
        const n = new DataView(data.buffer, data.byteOffset + pos, 4).getUint32(
          0,
          false,
        );
        pos += 4;
        if (n < limit) return n % size;
      }
    };
  }
  function handTotal(cards) {
    const ranks = cards.map((card) => (card % 13) + 1);
    const base = ranks.reduce((sum, rank) => sum + Math.min(rank, 10), 0);
    const soft = ranks.includes(1) && base + 10 <= 21;
    return [base + (soft ? 10 : 0), soft];
  }
  async function blackjackOutcome(pick, wager, actions) {
    if (!Array.isArray(actions) || actions.length > 32)
      throw Error("Invalid action history");
    const shoe = Array.from({ length: 312 }, (_, i) => i);
    let cursor = 0;
    async function card() {
      const other = cursor + (await pick(shoe.length - cursor));
      [shoe[cursor], shoe[other]] = [shoe[other], shoe[cursor]];
      return shoe[cursor++];
    }
    const player = [await card()],
      dealer = [await card()];
    player.push(await card());
    dealer.push(await card());
    let [pt] = handTotal(player),
      [dt] = handTotal(dealer);
    let ended = pt === 21 || dt === 21;
    const natural = pt === 21 && dt !== 21;
    let stake = BigInt(wager);
    for (let index = 0; index < actions.length; index++) {
      const action = actions[index];
      if (ended || !["hit", "stand", "double"].includes(action))
        throw Error("Illegal Blackjack move");
      if (action === "double") {
        if (index || player.length !== 2)
          throw Error("Double requires first two cards");
        stake = BigInt(wager) * 2n;
      }
      if (action === "hit" || action === "double") player.push(await card());
      [pt] = handTotal(player);
      ended = action === "stand" || action === "double" || pt >= 21;
    }
    if (
      ended &&
      !(player.length === 2 && (pt === 21 || dt === 21)) &&
      pt <= 21
    ) {
      while (handTotal(dealer)[0] < 17) dealer.push(await card());
    }
    const [player_total, player_soft] = handTotal(player),
      [dealer_total, dealer_soft] = handTotal(dealer);
    let status = "playing",
      payout = 0n;
    if (ended) {
      if (dealer.length === 2 && dealer_total === 21)
        status = player.length === 2 && player_total === 21 ? "push" : "lose";
      else if (natural) status = "blackjack";
      else if (player_total > 21) status = "lose";
      else if (dealer_total > 21 || player_total > dealer_total) status = "win";
      else if (player_total === dealer_total) status = "push";
      else status = "lose";
      payout =
        status === "blackjack"
          ? (BigInt(wager) * 5n) / 2n
          : status === "win"
            ? stake * 2n
            : status === "push"
              ? stake
              : 0n;
    }
    if (
      payout > BigInt(Number.MAX_SAFE_INTEGER) ||
      stake > BigInt(Number.MAX_SAFE_INTEGER)
    )
      throw Error("Points overflow");
    return {
      ended,
      player,
      dealer,
      player_total,
      dealer_total,
      player_soft,
      dealer_soft,
      status,
      total_wager: Number(stake),
      payout: Number(payout),
    };
  }

  const POKER_PAYTABLE = {
    royal_flush: 800, straight_flush: 50, four_of_a_kind: 25, full_house: 9,
    flush: 6, straight: 4, three_of_a_kind: 3, two_pair: 2, jacks_or_better: 1, no_win: 0,
  };
  function pokerCategory(cards) {
    if (cards.length !== 5 || new Set(cards).size !== 5 ||
        cards.some(card => !Number.isInteger(card) || card < 0 || card >= 52))
      throw Error("Invalid Poker cards");
    const ranks = cards.map(card => card % 13 === 0 ? 14 : card % 13 + 1).sort((a, b) => a-b);
    const counts = new Map();
    for (const rank of ranks) counts.set(rank, (counts.get(rank) || 0)+1);
    const groups = [...counts.values()].sort((a, b) => b-a).join(",");
    const flush = new Set(cards.map(card => Math.floor(card / 13))).size === 1;
    const straight = counts.size === 5 && (ranks[4]-ranks[0] === 4 || ranks.join(",") === "2,3,4,5,14");
    if (flush && ranks.join(",") === "10,11,12,13,14") return "royal_flush";
    if (flush && straight) return "straight_flush";
    if (groups === "4,1") return "four_of_a_kind";
    if (groups === "3,2") return "full_house";
    if (flush) return "flush";
    if (straight) return "straight";
    if (groups === "3,1,1") return "three_of_a_kind";
    if (groups === "2,2,1") return "two_pair";
    if (groups === "2,1,1,1" && [...counts].some(([rank, count]) => rank >= 11 && count === 2))
      return "jacks_or_better";
    return "no_win";
  }
  function validHolds(holds) {
    return Array.isArray(holds) && holds.length <= 5 &&
      holds.every((n, i) => Number.isInteger(n) && n >= 0 && n < 5 && (!i || holds[i-1] < n));
  }
  async function pokerOutcome(pick, wager, holds) {
    const deck = Array.from({ length: 52 }, (_, i) => i);
    let cursor = 0;
    async function card() {
      const other = cursor + await pick(52-cursor);
      [deck[cursor], deck[other]] = [deck[other], deck[cursor]];
      return deck[cursor++];
    }
    const initial = [];
    for (let i = 0; i < 5; i++) initial.push(await card());
    if (holds == null) return { ended: false, initial, cards: [...initial], holds: null, category: "playing", multiplier: 0, payout: 0 };
    if (!validHolds(holds)) throw Error("Invalid held cards");
    const cards = [];
    for (let i = 0; i < 5; i++) cards.push(holds.includes(i) ? initial[i] : await card());
    const category = pokerCategory(cards), multiplier = POKER_PAYTABLE[category];
    return { ended: true, initial, cards, holds, category, multiplier, payout: Number(BigInt(wager)*BigInt(multiplier)) };
  }

  async function baccaratOutcome(pick, wager, side) {
    const shoe = Array.from({length:416}, (_, index) => index);
    let cursor = 0;
    async function card() {
      const other = cursor + await pick(416-cursor);
      [shoe[cursor], shoe[other]] = [shoe[other], shoe[cursor]];
      return shoe[cursor++];
    }
    const value = card => (card % 13 + 1) < 10 ? card % 13 + 1 : 0;
    const total = cards => cards.reduce((sum, card) => sum+value(card), 0) % 10;
    const player = [await card()], banker = [await card()];
    player.push(await card()); banker.push(await card());
    const pt = total(player), bt = total(banker), natural = pt >= 8 || bt >= 8;
    if (!natural) {
      let third = null;
      if (pt <= 5) { player.push(await card()); third = value(player[2]); }
      // An explicit independent tableau makes every boundary auditable.
      const drawOn = [[0,1,2,3,4,5,6,7,8,9], [0,1,2,3,4,5,6,7,8,9],
        [0,1,2,3,4,5,6,7,8,9], [0,1,2,3,4,5,6,7,9], [2,3,4,5,6,7],
        [4,5,6,7], [6,7], []];
      if (third === null ? bt <= 5 : drawOn[bt].includes(third)) banker.push(await card());
    }
    const player_total = total(player), banker_total = total(banker);
    const winner = player_total === banker_total ? "tie" : player_total > banker_total ? "player" : "banker";
    const won = side === winner, push = winner === "tie" && side !== "tie";
    const payout = won ? BigInt(wager)*({player:200n,banker:195n,tie:900n}[side])/100n : push ? BigInt(wager) : 0n;
    if (payout > BigInt(Number.MAX_SAFE_INTEGER)) throw Error("Points overflow");
    return {player, banker, player_total, banker_total, natural, winner, won, push, payout:Number(payout)};
  }

  async function outcome(seed, r) {
    const pick = await draw(seed, r),
      o = r.options;
    if (["limbo", "coinflip", "poker"].includes(r.game) && !["redpoints-v3", "redpoints-v4", VERSION].includes(r.rules_version))
      throw Error("This game requires redpoints-v3");
    if (r.game === "baccarat") {
      if (!["redpoints-v4", VERSION].includes(r.rules_version)) throw Error("Baccarat requires redpoints-v4 or later");
      return baccaratOutcome(pick, r.wager, o.side);
    }
    if (r.game === "limbo") {
      const roll = await pick(4294967296);
      const multiplier = Math.max(100, Number(99n*4294967296n/(4294967296n-BigInt(roll))));
      const won = multiplier >= o.target;
      return { roll, multiplier, won, payout: won ? Number(BigInt(r.wager)*BigInt(o.target)/100n) : 0 };
    }
    if (r.game === "coinflip") {
      const side = ["heads", "tails"][await pick(2)], won = side === o.side;
      return { side, won, multiplier: 19800, payout: won ? Number(BigInt(r.wager)*198n/100n) : 0 };
    }
    if (r.game === "poker") {
      if (o.variant === "texas_holdem") {
        if (r.rules_version !== VERSION) throw Error("Hold’em requires redpoints-v5");
        const verifier = globalThis.RedHoldemFair || (typeof require === "function" ? require("./holdem-fairness.js") : null);
        if (!verifier) throw Error("The Hold’em verifier is missing. Reload this release.");
        return verifier.replay(pick, r.wager, o, r.actions, r.ending);
      }
      if (!["redpoints-v3", "redpoints-v4"].includes(r.rules_version) || o.variant !== "jacks_or_better") throw Error("Invalid legacy Poker version");
      return pokerOutcome(pick, r.wager, r.holds);
    }
    if (r.game === "dice") {
      const roll = await pick(10000),
        won =
          o.side === "under"
            ? roll < o.chance * 100
            : roll >= 10000 - o.chance * 100;
      return {
        roll,
        won,
        payout: won ? Number((BigInt(r.wager) * 99n) / BigInt(o.chance)) : 0,
      };
    }
    if (r.game === "keno") {
      const numbers = Array.from({ length: 40 }, (_, i) => i + 1),
        drawn = [];
      for (let i = 0; i < 10; i++) {
        const j = i + (await pick(40 - i));
        [numbers[i], numbers[j]] = [numbers[j], numbers[i]];
        drawn.push(numbers[i]);
      }
      const hits = drawn.filter((n) => o.picks.includes(n)).length,
        multiplier = table(
          "keno",
          o.picks.length,
          o.risk,
          r.rules_version || VERSION,
        )[hits];
      return {
        drawn,
        hits,
        multiplier,
        payout: Number((BigInt(r.wager) * BigInt(multiplier)) / SCALE),
      };
    }
    if (r.game === "blackjack") {
      if (!["redpoints-v2", "redpoints-v3", "redpoints-v4", VERSION].includes(r.rules_version))
        throw Error("Blackjack requires redpoints-v2 or later");
      return blackjackOutcome(pick, r.wager, r.actions || []);
    }
    if (r.game !== "plinko") throw Error("Unknown game");
    const path = [];
    for (let i = 0; i < o.rows; i++) path.push(await pick(2));
    const slot = path.reduce((a, b) => a + b, 0),
      multiplier = table("plinko", o.rows, o.risk, r.rules_version || VERSION)[
        slot
      ];
    return {
      path,
      slot,
      multiplier,
      payout: Number((BigInt(r.wager) * BigInt(multiplier)) / SCALE),
    };
  }
  async function verifyReceipt(r, expectedCommitment) {
    if (
      !r ||
      !SUPPORTED_VERSIONS.includes(r.rules_version) ||
      typeof r.season !== "string" ||
      typeof r.client_seed !== "string" ||
      typeof r.client_salt !== "string" ||
      ![r.nonce, r.wager, r.payout, r.net].every(Number.isSafeInteger) ||
      r.nonce < 0 ||
      r.wager < 1 ||
      !/^[0-9]{1,12}$/.test(r.season) ||
      !/^[a-f0-9]{32}$/.test(r.client_salt) ||
      !/^[A-Za-z0-9 _.\-]{1,64}$/.test(r.client_seed) ||
      !r.options
    )
      return false;
    const o = r.options;
    const keys = {
      dice: ["chance", "side"],
      keno: ["picks", "risk"],
      plinko: ["risk", "rows"],
      blackjack: ["decks"],
      limbo: ["target"],
      coinflip: ["side"],
      poker: o.variant === "texas_holdem" ? ["button", "variant"] : ["variant"],
      baccarat: ["decks", "side"],
    }[r.game];
    if (!keys || canonical(Object.keys(o).sort()) !== canonical(keys))
      return false;
    if (r.game === "dice") {
      if (
        !Number.isInteger(o.chance) ||
        o.chance < 1 ||
        o.chance > 95 ||
        !["under", "over"].includes(o.side)
      )
        return false;
    } else if (r.game === "blackjack") {
      if (
        o.decks !== 6 ||
        !["redpoints-v2", "redpoints-v3", "redpoints-v4", VERSION].includes(r.rules_version) ||
        !Array.isArray(r.actions)
      )
        return false;
    } else if (r.game === "baccarat") {
      if (!["redpoints-v4", VERSION].includes(r.rules_version) || o.decks !== 8 || !["player", "banker", "tie"].includes(o.side)) return false;
    } else if (r.game === "limbo") {
      if (!["redpoints-v3", "redpoints-v4", VERSION].includes(r.rules_version) || !Number.isInteger(o.target) || o.target < 101 || o.target > 100000000)
        return false;
    } else if (r.game === "coinflip") {
      if (!["redpoints-v3", "redpoints-v4", VERSION].includes(r.rules_version) || !["heads", "tails"].includes(o.side)) return false;
    } else if (r.game === "poker") {
      if (o.variant === "texas_holdem") {
        if (r.rules_version !== VERSION || !["player", "computer"].includes(o.button) || !Array.isArray(r.actions)) return false;
      } else if (!["redpoints-v3", "redpoints-v4"].includes(r.rules_version) || o.variant !== "jacks_or_better" || !validHolds(r.holds)) return false;
    } else {
      if (!["low", "medium", "high"].includes(o.risk)) return false;
      if (r.game === "plinko") {
        if (![8, 12, 16].includes(o.rows)) return false;
      } else if (r.game === "keno") {
        if (
          !Array.isArray(o.picks) ||
          !o.picks.length ||
          o.picks.length > 10 ||
          o.picks.some((n) => !Number.isInteger(n) || n < 1 || n > 40) ||
          new Set(o.picks).size !== o.picks.length ||
          o.picks.some((n, i) => i && n < o.picks[i - 1])
        )
          return false;
      } else return false;
    }
    const hash = hex(
      await crypto.subtle.digest("SHA-256", bytes(r.server_seed)),
    );
    if (
      hash !== r.commitment ||
      (expectedCommitment && hash !== expectedCommitment)
    )
      return false;
    const result = await outcome(r.server_seed, r);
    return (
      canonical(result) === canonical(r.result) &&
      r.payout === result.payout &&
      (!["blackjack", "poker"].includes(r.game) || result.ended) &&
      r.net ===
        result.payout - (r.game === "blackjack" ? result.total_wager : r.wager)
    );
  }
  async function verify(r, expectedCommitment) {
    try { return await verifyReceipt(r, expectedCommitment); }
    catch { return false; }
  }
  globalThis.RedFair = {
    VERSION,
    SUPPORTED_VERSIONS,
    canonical,
    table,
    pokerCategory,
    outcome,
    verify,
  };
  if (typeof module !== "undefined") module.exports = globalThis.RedFair;
})();
```

## `static/gaming.css`

```css
.gaming-page {
  padding-top: 30px;
  padding-bottom: 40px;
}
.gaming-heading {
  display: flex;
  justify-content: space-between;
  align-items: center;
  gap: 20px;
  margin-bottom: 20px;
}
.gaming-heading h1 {
  margin: 6px 0;
  font-size: clamp(2rem, 4vw, 3.5rem);
}
.points-wallet {
  min-width: 250px;
  padding: 18px 24px;
  display: grid;
  gap: 5px;
  border-color: #a63246;
  background: linear-gradient(140deg, #411c2a, #21161f);
}
.points-wallet strong {
  color: #fff1f4;
  font-size: 2rem;
  font-variant-numeric: tabular-nums;
}
.points-wallet small {
  color: var(--muted);
  font-size: 0.72rem;
}
.game-nav {
  display: flex;
  align-items: center;
  flex-wrap: wrap;
  gap: 8px;
}
.game-nav [aria-current="page"] {
  border-color: #ff4c67;
  background: #562331;
}
.points-note {
  margin: 12px 0 20px;
}
.gaming-profile {
  padding: 22px;
  margin-bottom: 18px;
}
.gaming-profile form {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  gap: 10px;
  margin: 14px 0;
}
.gaming-profile input {
  flex: 1;
  min-width: 160px;
}
.gaming-identity {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  gap: 8px 18px;
  margin: 12px 0 20px;
}
.game-cards {
  display: grid;
  grid-template-columns: repeat(3, minmax(0, 1fr));
  gap: 18px;
}
.game-card {
  padding: 20px;
  color: var(--text);
  transition: border-color 0.15s;
}
.game-card:hover {
  border-color: #ed4560;
}
.game-card h2 {
  display: flex;
  justify-content: space-between;
  margin: 16px 0 8px;
}
.game-card p {
  color: var(--muted);
  min-height: 48px;
  line-height: 1.6;
}
.game-card .button {
  margin-top: 12px;
  width: 100%;
}
.game-art {
  height: 175px;
  background: radial-gradient(ellipse at 50% 90%, #81152f55, #180e18);
  border-radius: 12px;
  margin-bottom: 20px;
}
.dice-art {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 15px;
  color: #ff4561;
  font-size: 100px;
}
.dice-art span:last-child {
  transform: rotate(20deg);
  font-size: 76px;
}
.mini-keno {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: 7px;
  padding: 20px;
}
.mini-keno span {
  display: grid;
  place-items: center;
  background: #31202d;
  border-radius: 5px;
  font-weight: 700;
  color: #9c8b9a;
}
.mini-keno .picked {
  color: white;
  background: #b62945;
}
.plinko-art {
  text-align: center;
  font-size: 44px;
  line-height: 0.75;
  padding: 22px;
  letter-spacing: 5px;
  color: #f6c3ce;
}
.plinko-art > span {
  display: block;
  color: #ff4561;
  font-size: 19px;
  line-height: 1.5;
}
.game-season,
.bet-history,
.payout-panel,
.fairness-panel {
  padding: 22px;
  margin-top: 20px;
}
.game-season h2,
.bet-history h2,
.payout-panel h2 {
  font-size: 1.2rem;
  margin-top: 0;
}
.game-stat-cards {
  display: grid;
  grid-template-columns: repeat(3, minmax(0, 1fr));
  gap: 14px;
}
.game-stat-cards article {
  display: grid;
  gap: 9px;
  padding: 16px;
  border-radius: 8px;
  background: #271b27;
}
.game-stat-cards b {
  font-size: 1.4rem;
  color: #ff8295;
}
.game-stat-cards small {
  color: var(--muted);
}
.game-layout {
  display: grid;
  grid-template-columns: 285px minmax(0, 1fr);
  overflow: hidden;
}
.bet-controls {
  padding: 22px;
  background: #251b26;
  border-right: 1px solid #48313e;
  display: flex;
  flex-direction: column;
  gap: 18px;
}
.bet-controls .field,
.bet-controls p {
  margin: 0;
}
.bet-controls label,
.bet-controls legend {
  font-size: 0.84rem;
  font-weight: 650;
}
.bet-controls input,
.bet-controls select {
  width: 100%;
}
.wager-input {
  display: flex;
  margin: 7px 0;
  gap: 4px;
}
.wager-input input {
  min-width: 0;
}
.wager-input .button {
  padding: 8px;
  flex: 0 0 36px;
}
.bet-preview {
  display: grid;
  gap: 7px;
  background: #161018;
  padding: 14px;
  border-radius: 8px;
}
.bet-preview small {
  color: var(--muted);
  font-size: 0.72rem;
}
.risk-options {
  display: flex;
  gap: 4px;
  border: 0;
  padding: 0;
  margin: 0;
}
.risk-options legend {
  margin-bottom: 8px;
}
.risk-options label {
  flex: 1;
  position: relative;
}
.risk-options input {
  position: absolute;
  opacity: 0;
  width: 1px;
}
.risk-options span {
  display: block;
  padding: 12px 4px;
  text-align: center;
  background: #382836;
  border: 1px solid transparent;
  border-radius: 7px;
  cursor: pointer;
}
.risk-options input:checked + span {
  background: #ad2843;
  border-color: #ff6a85;
  color: white;
}
.risk-options input:focus-visible + span {
  outline: 2px solid white;
  outline-offset: 2px;
}
.game-board {
  min-width: 0;
  padding: 22px;
  display: flex;
  flex-direction: column;
  justify-content: center;
  background: radial-gradient(ellipse at top, #35202c88, #100e14 80%);
  min-height: 480px;
}
.game-result {
  text-align: center;
  padding: 16px 8px;
  font-weight: 700;
  font-variant-numeric: tabular-nums;
  background: #2a1b26;
  border: 1px solid #593144;
  border-radius: 8px;
  margin-top: 15px;
}
.game-result.is-win {
  color: #b6efca;
  border-color: #377251;
}
#betProof,
#plinkoResult {
  text-align: center;
  margin-top: 8px;
}
.dice-stage {
  padding: 35px 25px;
  text-align: center;
}
.dice-roll {
  color: #fff3f5;
  font-size: clamp(4rem, 8vw, 6rem);
  font-weight: 800;
  font-variant-numeric: tabular-nums;
}
.dice-stage p {
  color: var(--muted);
}
.dice-track {
  height: 10px;
  background: linear-gradient(90deg, #742436, #e54263);
  border-radius: 9px;
  margin: 55px 0 15px;
  position: relative;
}
#diceMarker {
  position: absolute;
  left: 50%;
  transform: translate(-50%, -38%);
  color: white;
  font-size: 28px;
}
.dice-scale {
  display: flex;
  justify-content: space-between;
  font-size: 0.75rem;
  color: var(--muted);
}
.keno-board {
  display: grid;
  grid-template-columns: repeat(8, minmax(0, 1fr));
  gap: 8px;
}
.keno-board button {
  aspect-ratio: 1;
  padding: 0;
  border: 1px solid #4a3441;
  border-radius: 7px;
  background: #312530;
  color: #d8ccd7;
  font-size: clamp(0.8rem, 2vw, 1.1rem);
  font-weight: 750;
  cursor: pointer;
  min-width: 0;
}
.keno-board button.selected {
  background: #8c2540;
  border-color: #f86b8a;
  color: white;
}
.keno-board button.drawn {
  box-shadow: inset 0 0 0 3px #f0cd8c;
}
.keno-board button.matched {
  background: #2d6651;
  border-color: #8de3b3;
}
.keno-key {
  display: flex;
  justify-content: center;
  gap: 18px;
}
.keno-key span:first-child {
  color: #ff8aa4;
}
.keno-key span:nth-child(2) {
  color: #f0cd8c;
}
.keno-key span:last-child {
  color: #8de3b3;
}
#plinkoCanvas {
  width: 100%;
  height: auto;
  display: block;
}
.payout-table {
  display: flex;
  flex-wrap: wrap;
  gap: 6px;
}
.payout-table > div {
  min-width: 76px;
  flex: 1 0 76px;
  padding: 10px;
  text-align: center;
  display: grid;
  gap: 6px;
  background: #2e1d29;
  border: 1px solid #523040;
  border-radius: 7px;
}
.payout-table small {
  color: var(--muted);
  font-size: 0.7rem;
}
.payout-table strong {
  font-size: 0.95rem;
  color: #ffbac9;
}
.fairness-panel summary {
  cursor: pointer;
  font-weight: 700;
  padding: 3px 0;
}
.fairness-panel code {
  white-space: normal;
  overflow-wrap: anywhere;
}
.fairness-panel input {
  width: 100%;
  margin: 10px 0;
}
.fairness-panel dt {
  color: var(--muted);
  margin: 12px 0 5px;
}
.fairness-panel dd {
  margin: 0;
}
.gaming-admin-cards {
  display: grid;
  grid-template-columns: repeat(3, minmax(0, 1fr));
  gap: 16px;
}
.gaming-admin-cards section {
  padding: 18px;
  min-width: 0;
}
.gaming-admin-cards ol {
  list-style: none;
  padding: 0;
}
.gaming-admin-cards li {
  border-top: 1px solid #48313e;
  padding: 12px 0;
  overflow-wrap: anywhere;
}
.gaming-admin-cards li strong,
.gaming-admin-cards li small {
  display: block;
}
.gaming-admin-cards li b {
  color: #ffacbc;
}
.gaming-admin-cards small {
  color: var(--muted);
  font-size: 0.74rem;
  margin-top: 4px;
}
.verifier-form {
  display: grid;
  gap: 14px;
}
.verifier-form textarea {
  min-height: 200px;
  width: 100%;
  font-family: monospace;
}
@media (max-width: 900px) {
  .game-layout {
    grid-template-columns: 240px minmax(0, 1fr);
  }
  .gaming-admin-cards {
    grid-template-columns: 1fr;
  }
}
@media (max-width: 700px) {
  .gaming-page {
    padding-top: 18px;
  }
  .gaming-heading {
    align-items: stretch;
    flex-direction: column;
    gap: 8px;
  }
  .gaming-heading p {
    margin: 4px 0;
  }
  .points-wallet {
    min-width: 0;
    padding: 14px 18px;
  }
  .points-wallet strong {
    font-size: 1.7rem;
  }
  .game-cards {
    grid-template-columns: 1fr;
  }
  .game-card {
    display: grid;
    grid-template-columns: 100px 1fr;
    gap: 4px 16px;
    padding: 16px;
  }
  .game-art {
    grid-row: span 4;
    width: 100px;
    height: 140px;
    margin: 0;
    align-self: center;
  }
  .game-card h2 {
    margin: 6px 0;
  }
  .game-card p {
    font-size: 0.83rem;
    min-height: 0;
    margin: 0;
  }
  .dice-art {
    font-size: 62px;
    gap: 0;
  }
  .dice-art span:last-child {
    display: none;
  }
  .mini-keno {
    padding: 10px;
    grid-template-columns: repeat(3, 1fr);
    gap: 4px;
    font-size: 0.7rem;
  }
  .plinko-art {
    padding: 16px 3px;
    font-size: 27px;
    line-height: 1;
    letter-spacing: 0;
  }
  .game-layout {
    grid-template-columns: 1fr;
  }
  .game-board {
    grid-row: 1;
    min-height: 270px;
    padding: 12px;
  }
  .bet-controls {
    border-right: 0;
    border-top: 1px solid #48313e;
    padding: 18px;
    gap: 14px;
  }
  .dice-stage {
    padding: 5px 20px;
  }
  .dice-track {
    margin-top: 25px;
  }
  .dice-roll {
    font-size: 4rem;
  }
  .keno-board {
    grid-template-columns: repeat(5, minmax(0, 1fr));
    gap: 7px;
  }
  .keno-board button {
    min-height: 44px;
    aspect-ratio: auto;
    font-size: 0.92rem;
  }
  .game-stat-cards {
    grid-template-columns: 1fr;
    gap: 8px;
  }
  .game-stat-cards article {
    grid-template-columns: 1fr 1fr;
  }
  .game-stat-cards small {
    grid-column: span 2;
  }
  .bet-history,
  .payout-panel,
  .fairness-panel,
  .game-season {
    padding: 15px;
  }
  .bet-history th,
  .bet-history td {
    padding: 10px 5px;
    font-size: 0.72rem;
  }
  .bet-history .section-title {
    align-items: start;
    gap: 8px;
    flex-direction: column;
  }
  .game-nav .button {
    min-height: 44px;
  }
  .gaming-profile form {
    flex-direction: column;
    align-items: stretch;
  }
  .gaming-profile input {
    min-width: 0;
  }
}

.payout-table > div {
  flex-basis: 110px;
  min-width: 110px;
  padding: 9px;
}
.payout-table strong {
  font-size: 0.84rem;
  white-space: nowrap;
}
.bet-history button.text-link {
  background: transparent;
  border: 0;
  min-height: 44px;
  padding: 8px 0;
  color: var(--accent);
  cursor: pointer;
  font: inherit;
  text-decoration: underline;
}

/* Give the native slider room for mouse, keyboard and touch input. */
.gaming-page #diceChance {
  appearance: auto;
  min-height: 44px;
  margin: 0;
  padding: 0;
  border: 0;
  background: transparent;
  accent-color: #ff415b;
  cursor: ew-resize;
  touch-action: pan-y;
}
.gaming-page #diceChance:focus-visible {
  outline: 2px solid #ff8295;
  outline-offset: 3px;
}
.gaming-page #diceChance:disabled {
  cursor: not-allowed;
  opacity: 0.55;
}

/* Keep play/recovery feedback beside the control, including on narrow screens. */
.gaming-bet-status {
  min-height: 2.8em;
  color: var(--muted);
  line-height: 1.5;
  overflow-wrap: anywhere;
}
.gaming-bet-status.is-error {
  color: #ffb8ac;
}
#plinkoCanvas {
  aspect-ratio: 720 / 510;
}

/* A blocked action is not a loading state. Only real requests show progress. */
.gaming-page button:disabled {
  cursor: not-allowed;
}
#betButton[aria-busy="true"] {
  cursor: progress;
}
#betButton[aria-disabled="true"] {
  opacity: 0.7;
}
.dice-track {
  --dice-threshold: 50%;
  --dice-left: #ed4362;
  --dice-right: #392937;
  height: 44px;
  margin: 38px 0 5px;
  background: transparent;
}
.dice-track.is-over {
  --dice-left: #392937;
  --dice-right: #ed4362;
}
.dice-track::before {
  content: "";
  position: absolute;
  top: 17px;
  left: 12px;
  right: 12px;
  height: 10px;
  border-radius: 10px;
  background: linear-gradient(
    to right,
    var(--dice-left) var(--dice-threshold),
    var(--dice-right) var(--dice-threshold)
  );
  pointer-events: none;
}
.gaming-page .dice-board-slider {
  appearance: none;
  position: relative;
  display: block;
  width: 100%;
  height: 44px;
  margin: 0;
  padding: 0;
  border: 0;
  background: transparent;
  cursor: ew-resize;
  touch-action: pan-y;
}
.dice-board-slider::-webkit-slider-runnable-track {
  height: 10px;
  background: transparent;
}
.dice-board-slider::-moz-range-track {
  height: 10px;
  background: transparent;
}
.dice-board-slider::-moz-range-progress {
  background: transparent;
}
.dice-board-slider::-webkit-slider-thumb {
  appearance: none;
  box-sizing: border-box;
  width: 24px;
  height: 24px;
  margin-top: -7px;
  border: 3px solid #ff657e;
  border-radius: 50%;
  background: #fff4f6;
  box-shadow: 0 2px 10px #0007;
}
.dice-board-slider::-moz-range-thumb {
  box-sizing: border-box;
  width: 24px;
  height: 24px;
  border: 3px solid #ff657e;
  border-radius: 50%;
  background: #fff4f6;
  box-shadow: 0 2px 10px #0007;
}
.gaming-page .dice-board-slider:focus-visible {
  outline: 2px solid #ff8295;
  outline-offset: 3px;
}
.gaming-page .dice-board-slider:disabled {
  cursor: not-allowed;
  opacity: 0.55;
}
#diceMarker {
  top: -18px;
  transform: translateX(-50%);
  padding: 3px 6px;
  border-radius: 5px;
  background: #fff4f6;
  color: #281923;
  font-size: 0.7rem;
  font-weight: 700;
  pointer-events: none;
}

/* Responsive four-game layout; card movement illustrates the saved hand. */
.game-cards {
  grid-template-columns: repeat(auto-fit, minmax(min(100%, 240px), 1fr));
}
.gaming-admin-cards {
  grid-template-columns: repeat(2, minmax(0, 1fr));
}
@media (max-width: 760px) {
  .gaming-admin-cards {
    grid-template-columns: 1fr;
  }
}
.gaming-admin-cards small {
  overflow-wrap: anywhere;
}
.blackjack-art {
  gap: 8px;
}
.blackjack-art span {
  border-radius: 9px;
  padding: 14px;
  background: #fff5f3;
  color: #291e29;
  transform: rotate(-10deg);
  font-size: 2rem;
}
.blackjack-art span + span {
  color: #c62a47;
  transform: rotate(12deg);
}
.blackjack-table {
  padding: 24px;
  border: 1px solid #79323f;
  border-radius: 20px;
  background: radial-gradient(ellipse at center, #66252e, #291720);
  min-height: 430px;
}
.blackjack-hand .row {
  display: flex;
  align-items: center;
  justify-content: space-between;
}
.blackjack-hand h3 {
  margin: 0 0 12px;
  font-size: 1rem;
}
.playing-cards {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
  min-height: 98px;
}
.playing-card {
  width: 60px;
  height: 86px;
  flex: none;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  border-radius: 8px;
  background: #fff3ed;
  border: 1px solid #ffffff66;
  color: #22161c;
  font-size: 1.4rem;
  font-weight: 700;
  line-height: 1.2;
  box-shadow: 0 4px 10px #0004;
  /* Cards are animated once by the shared presentation helper. */
}
.playing-card.is-red {
  color: #c62540;
}
.playing-card.is-hidden {
  background: repeating-linear-gradient(45deg, #a22b41 0 4px, #70263a 4px 8px);
  border: 3px solid #efc4c8;
  color: #fff;
}
.blackjack-felt-label {
  text-align: center;
  color: #e3a3ac;
  font-size: 0.75rem;
  letter-spacing: 0.1em;
  margin: 18px 0;
}
.blackjack-felt-label span {
  display: block;
  font-size: 0.6rem;
  margin-top: 4px;
}
.blackjack-actions {
  margin-top: 20px;
  flex-wrap: wrap;
}
.blackjack-actions .button {
  min-height: 44px;
  flex: 1;
}
@keyframes deal-card {
  from {
    opacity: 0;
    transform: translate(18px, -12px) rotate(5deg);
  }
  to {
    opacity: 1;
    transform: translate(0, 0) rotate(0);
  }
}
@media (max-width: 600px) {
  .blackjack-table {
    padding: 16px;
  }
  .playing-card {
    width: 48px;
    height: 72px;
  }
  .playing-cards {
    gap: 6px;
    min-height: 78px;
  }
}
@media (prefers-reduced-motion: reduce) {
  .playing-card {
    animation: none;
  }
}
/* Extra games share the same spacing, red palette and native controls. */
.limbo-art { flex-direction:column; gap:14px; }
.limbo-art span { font-size:2.6rem; font-weight:900; letter-spacing:-.06em; color:#ff7186; }
.limbo-art i { width:65%; height:3px; background:linear-gradient(90deg,transparent,#ff4967); transform:rotate(-12deg); }
.coinflip-art span { display:grid; place-items:center; width:88px; height:88px; border-radius:50%; border:6px double #ff7f8f; background:#991632; color:#fff0f1; font-size:3rem; font-weight:900; box-shadow:0 12px 30px #90032644; }
.limbo-stage,.coin-stage { display:flex; flex-direction:column; align-items:center; justify-content:center; min-height:345px; padding:24px 10px; text-align:center; background:radial-gradient(ellipse at 50% 55%,#be224b22,transparent 68%); }
.limbo-multiplier { color:#ff7186; font-size:clamp(2.7rem,7vw,5rem); font-weight:900; line-height:1.2; letter-spacing:-.06em; font-variant-numeric:tabular-nums; overflow-wrap:anywhere; max-width:100%; }
.limbo-stage.is-win .limbo-multiplier { color:#79e7b3; }
.limbo-trail { width:80%; max-width:390px; height:5px; border-radius:9px; background:#ffffff0d; overflow:hidden; margin:18px 0; }
.limbo-trail span { display:block; width:100%; height:100%; background:linear-gradient(90deg,#97102e,#ff6a84); transform-origin:left; transform:scaleX(0); }
.limbo-targets { margin-top:10px; }
.coin-space { width:170px; height:190px; display:grid; place-items:center; perspective:800px; }
.red-coin { width:140px; height:140px; position:relative; transform-style:preserve-3d; }
.coin-face { position:absolute; inset:0; border:7px double #ff99a9; border-radius:50%; background:radial-gradient(circle at 35% 25%,#dc3556,#780a29); display:flex; flex-direction:column; align-items:center; justify-content:center; backface-visibility:hidden; color:#fff4f6; box-shadow:0 12px 34px #c0193838; }
.coin-face b { font-size:3.1rem; line-height:1.15; }
.coin-face small { font-size:.7rem; letter-spacing:.2em; font-weight:800; }
.coin-tails { transform:rotateY(180deg); background:radial-gradient(circle at 35% 25%,#a32c4b,#461325); }
.coin-options { display:flex; gap:8px; }
.coin-options label { flex:1; }
.poker-table { padding:18px; border:1px solid #ffffff0d; border-radius:20px; background:radial-gradient(ellipse at top,#42192888,#160e16); }
.poker-table h2 { font-size:1.4rem; margin:0; }
.poker-cards { display:grid; grid-template-columns:repeat(5,minmax(0,1fr)); gap:10px; margin:22px 0; }
.poker-card { position:relative; width:100%; min-width:0; min-height:125px; padding:12px 5px; border:2px solid #eadde1; border-radius:12px; background:#fff8f5; color:#1c1620; display:flex; flex-direction:column; align-items:center; justify-content:center; gap:8px; box-shadow:0 5px 15px #0003; transform:none; cursor:pointer; transition:border-color .15s,box-shadow .15s; }
.poker-card:hover { transform:none; background:#fff; }
.poker-card:focus-visible { outline:3px solid #ff5878; outline-offset:4px; }
.poker-card b { font-size:clamp(1.1rem,3vw,2rem); line-height:1.2; }
.poker-card small { font-size:.6rem; letter-spacing:.05em; font-weight:900; color:#685763; }
.poker-card.is-red { color:#c42142; }
.poker-card[aria-pressed="true"] { border-color:#fc3157; box-shadow:0 0 0 2px #fc315744,0 5px 15px #0003; }
.poker-card[aria-pressed="true"] small { color:#c42142; }
.poker-card.is-back { color:#ff8b9e; background:repeating-linear-gradient(35deg,#53152a,#53152a 6px,#441322 6px,#441322 12px); border-color:#863049; font-size:2rem; }
.poker-card:disabled { opacity:1; cursor:default; }
.poker-actions { align-items:center; flex-wrap:wrap; }
.poker-actions #pokerDraw { margin-left:auto; }
.poker-paytable { display:grid; grid-template-columns:repeat(auto-fit,minmax(145px,1fr)); gap:8px; }
.poker-paytable > div { display:flex; flex-direction:column; gap:5px; padding:12px; background:#ffffff04; border:1px solid #ffffff0b; border-radius:10px; }
.poker-paytable > div.is-hit { border-color:#ff4768; background:#ff315317; }
.poker-paytable small { color:var(--muted,#c4b5bf); font-size:.7rem; }
@media(max-width:600px) {
  .poker-table { padding:12px 8px; }
  .poker-cards { gap:5px; }
  .poker-card { border-radius:8px; min-height:90px; padding:10px 2px; }
  .poker-card small { font-size:.52rem; }
  .poker-actions { gap:6px; }
  .poker-actions .button { padding:9px; font-size:.75rem; }
  .limbo-stage,.coin-stage { min-height:285px; }
}

/* Center new game artwork after the shared dashboard card rules. */
.game-art.limbo-art,.game-art.coinflip-art {
  display:flex;
  align-items:center;
  justify-content:center;
}
.game-art.limbo-art span { position:static; font-size:2.6rem; }
.game-art.coinflip-art span { position:static; }
@media(min-width:681px) {
  .game-card { display:flex; flex-direction:column; }
  .game-card > .game-art { flex-shrink:0; }
  .game-card > .button { margin-top:auto; text-align:center; }
}

/* Compact screens keep help accessible without competing with the game. */
.gaming-page .payout-panel summary,
.gaming-page .fairness-panel summary { cursor: pointer; font-weight: 650; }
.gaming-page .payout-panel:not([open]),
.gaming-page .fairness-panel:not([open]) { padding-block: 16px; }
.gaming-bet-status { min-height: 0; margin: 0; }
.gaming-bet-status:empty { display: none; }
#gameResult { min-height: 54px; }
#betProof { min-height: 1.5em; }
.keno-board button { transition: background-color .2s, border-color .2s, box-shadow .2s; }
.game-board { overflow: hidden; }
.playing-card, .poker-card { backface-visibility: hidden; }
.baccarat-table { padding: 28px 20px; border: 1px solid #79323f; border-radius: 20px;
  background: radial-gradient(ellipse at center,#66252e,#291720); min-height: 330px;
  display: flex; flex-direction: column; justify-content: center; }
.baccarat-hands { display: grid; grid-template-columns: repeat(2,minmax(0,1fr)); gap: 14px; }
.baccarat-hand { border: 1px solid #a6526444; border-radius: 12px; padding: 14px 10px;
  transition: border-color .3s, background-color .3s; min-width: 0; }
.baccarat-hand.is-winner { border-color: #eeb39a; background: #be30442a; }
.baccarat-hand .row { display: flex; align-items: center; justify-content: space-between; gap: 8px; margin-bottom: 16px; }
.baccarat-hand h2 { margin: 0; font-size: 1rem; }
.baccarat-hand output { border-radius: 8px; background: #130f17; font-size: 1.2rem;
  font-weight: 750; min-width: 32px; text-align: center; padding: 4px; }
.baccarat-hand .playing-cards { flex-wrap: nowrap; gap: 5px; min-height: 88px; }
.baccarat-hand .playing-card { width: clamp(32px,4vw,54px); height: 78px; font-size: 1.15rem; }
.baccarat-options small { display: block; opacity: .85; font-size: .72rem; margin-top: 4px; }
#baccaratStatus { margin: 24px 0 0; text-align: center; min-height: 1.5em; }
@media (max-width: 680px) {
  .gaming-page .gaming-heading { gap: 16px; }
  .game-board { padding: 16px 12px; min-height: 340px; }
  .baccarat-table { min-height: 280px; padding: 18px 10px; }
  .baccarat-hands { gap: 8px; }
  .baccarat-hand { padding: 12px 6px; }
  .baccarat-hand .playing-card { width: 30px; height: 58px; font-size: .88rem; }
  .baccarat-hand .playing-cards { min-height: 60px; }
  .baccarat-hand .row { margin-bottom: 12px; }
}
@media (prefers-reduced-motion: reduce) {
  .gaming-page *, .gaming-page *::before, .gaming-page *::after {
    animation-duration: .001ms !important; transition-duration: .001ms !important;
  }
}

.game-art.blackjack-art { display: flex; align-items: center; justify-content: center; }

.gaming-recovery{margin:14px 0}.gaming-recovery>summary{display:flex;align-items:center;justify-content:space-between;gap:16px;cursor:pointer}.gaming-recovery>summary span{font-size:.78rem;color:var(--muted,#aaa)}.gaming-recovery-content{display:grid;gap:12px;padding-top:16px}.gaming-recovery textarea{width:100%;font-family:ui-monospace,SFMono-Regular,Consolas,monospace;resize:vertical}

/* V14 public community leaderboard. */
.gaming-public-choice {
  flex:1 1 100%;
  display:flex;
  align-items:flex-start;
  gap:10px;
  padding:12px 14px;
  border:1px solid #433743;
  border-radius:10px;
  background:#1b171e;
  cursor:pointer;
}
.gaming-public-choice input {flex:0 0 auto;width:auto;margin-top:3px}
.gaming-public-choice span {display:grid;gap:3px}
.gaming-public-choice strong {font-size:.86rem}
.gaming-public-choice small {color:var(--muted);font-size:.74rem;line-height:1.45}
.gaming-community {margin:24px 0 28px}
.gaming-community-heading {align-items:center}
.gaming-community-heading h2 {margin:4px 0 6px;font-size:clamp(1.7rem,3.2vw,2.5rem)}
.gaming-activity-count {min-width:105px;display:grid;justify-items:end;gap:2px}
.gaming-activity-count strong {font-size:2rem;line-height:1;color:#fff;font-variant-numeric:tabular-nums}
.gaming-activity-count span {font-size:.7rem;color:var(--muted);text-transform:uppercase;letter-spacing:.09em}
.gaming-game-counts {display:flex;flex-wrap:wrap;gap:8px;margin:-4px 0 14px}
.gaming-game-counts span {padding:7px 10px;border:1px solid #3c333e;background:#1d1921;border-radius:999px;color:#bcb2be;font-size:.75rem}
.gaming-game-counts b {color:#fff;font-variant-numeric:tabular-nums}
.gaming-community-grid {display:grid;grid-template-columns:minmax(0,.9fr) minmax(0,1.1fr);gap:16px}
.gaming-live-panel,.gaming-leader-panel {padding:20px;min-width:0}
.gaming-panel-heading {display:flex;align-items:center;justify-content:space-between;gap:12px;margin-bottom:14px}
.gaming-panel-heading h3 {margin:4px 0 0;font-size:1.18rem}
.live-dot {width:9px;height:9px;border-radius:50%;background:#60d99d;box-shadow:0 0 0 5px #60d99d18}
.gaming-live-list {display:grid;gap:8px}
.gaming-live-list article {display:flex;align-items:center;gap:11px;padding:10px;border-radius:10px;background:#18151b;border:1px solid #302a33}
.gaming-live-list article div {min-width:0;display:grid;gap:2px}
.gaming-live-list strong {overflow:hidden;text-overflow:ellipsis;white-space:nowrap;font-size:.88rem}
.gaming-live-list small {color:var(--muted);font-size:.72rem}
.gaming-live-avatar {display:grid;place-items:center;flex:0 0 34px;width:34px;height:34px;border-radius:10px;background:#442531;color:#ff9caf;font-weight:800}
.gaming-public-leaders {list-style:none;margin:0;padding:0;display:grid}
.gaming-public-leaders li {display:grid;grid-template-columns:38px minmax(0,1fr) auto;align-items:center;gap:10px;min-height:47px;padding:8px 4px;border-bottom:1px solid #302a33}
.gaming-public-leaders li:last-child {border-bottom:0}
.gaming-public-leaders li > strong {overflow:hidden;text-overflow:ellipsis;white-space:nowrap;font-size:.88rem}
.gaming-public-leaders li > span:last-child {display:grid;justify-items:end;gap:2px;font-variant-numeric:tabular-nums}
.gaming-public-leaders li > span:last-child b {font-size:.84rem;color:#ff8ea2}
.gaming-public-leaders li > span:last-child small {font-size:.68rem;color:var(--muted)}
.gaming-public-rank {color:#918693;font-size:.75rem;font-variant-numeric:tabular-nums}
.gaming-live-list .empty,.gaming-public-leaders .empty {margin:0;padding:18px;color:var(--muted);font-size:.8rem;border:1px dashed #3a333c;border-radius:10px;background:transparent}
.gaming-public-leaders .empty {display:block;min-height:0}
@media (max-width:820px){.gaming-community-grid{grid-template-columns:1fr}.gaming-activity-count{justify-items:start}.gaming-community-heading{align-items:flex-start}}
@media (max-width:560px){.gaming-community-heading{display:grid}.gaming-public-leaders li{grid-template-columns:32px minmax(0,1fr) auto}.gaming-live-panel,.gaming-leader-panel{padding:16px}}
.gaming-filter-bar {overflow-x:auto;flex-wrap:nowrap;padding-bottom:3px;scrollbar-width:thin}
.gaming-filter-bar button {
  flex:0 0 auto;
  display:inline-flex;
  align-items:center;
  gap:6px;
  padding:8px 11px;
  border:1px solid #3c333e;
  border-radius:999px;
  background:#1d1921;
  color:#bcb2be;
  font:inherit;
  font-size:.75rem;
  cursor:pointer;
  transition:border-color .16s ease,background-color .16s ease,color .16s ease;
}
.gaming-filter-bar button b {color:#fff;font-variant-numeric:tabular-nums}
.gaming-filter-bar button:hover {border-color:#6b4855;color:#fff}
.gaming-filter-bar button.is-active,
.gaming-filter-bar button[aria-pressed="true"] {border-color:#a24d61;background:#422530;color:#fff}
.gaming-filter-bar button:focus-visible {outline:2px solid #ff8299;outline-offset:2px}
.gaming-public-leaders i {font-style:normal;font-size:.72rem;font-weight:800;margin-right:5px}
.gaming-public-leaders .rank-up {color:#6be1a8}
.gaming-public-leaders .rank-down {color:#f2a16f}
```

## `static/gaming.js`

```javascript
/* Server-authoritative play points. Never generate an outcome in the UI.
   Unknown POST results keep their receipt ID so retries cannot debit twice. */
(() => {
  "use strict";
  const root = document.querySelector(".gaming-page");
  if (!root) return;
  const id = (n) => document.getElementById(n),
    game = root.dataset.game,
    rules = JSON.parse(root.dataset.rules);
  const number = (n) =>
      (typeof n === "bigint" ? n : Number(n)).toLocaleString("en-US"),
    points = (n) => (n > 0 ? "+" : "") + number(n);
  let wallet,
    community = null,
    communityFilter = "all",
    communityRanks = new Map(),
    csrf = root.dataset.csrf,
    busy = false,
    refreshing = false,
    fatal = false,
    pending = null,
    pendingAction = null,
    timer,
    polling = false,
    feedback = "",
    holdemTable = null;
  let selections = new Set(),
    pokerHolds = new Set(),
    pokerRound = "",
    walletEtag = "",
    presentationSequence = 0;
  let historyKey = '', statsKey = '', historyExpanded = false, playPhase = 'ready';
  function phase(value, detail = '') {
    playPhase = value;
    root.dataset.playState = value;
    const node = id('roundState');
    if (node) node.textContent = detail || ({ready:'Ready', submitting:'Contacting server…', verifying:'Checking proof…', playing:'Playing', result:'Round complete', recovery:'Recovering saved result', error:'Needs attention'})[value];
  }
  const cardAnimations = new Set();
  const betLabel = id("betButton")?.textContent || "Play";
  const betForm = id("betForm");
  if (betForm) {
    // Handle validation ourselves so a rejected click has an inline reason.
    betForm.noValidate = true;
    const status = document.createElement("p");
    status.id = "betStatus";
    status.className = "small gaming-bet-status";
    id("betButton").before(status);
    id("betButton").setAttribute("aria-describedby", status.id);
    id("betButton").setAttribute("autocomplete", "off");
  }
  const verifierReady = typeof globalThis.RedFair?.verify === "function" &&
    (game !== "poker" || (typeof globalThis.RedHoldemFair?.replay === "function" && typeof globalThis.RedHoldemUI?.create === "function"));
  const secure = Boolean(
    globalThis.crypto?.subtle && globalThis.crypto?.getRandomValues,
  );
  const isHoldem = value => value?.variant === "texas_holdem" || value?.options?.variant === "texas_holdem";
  const secureMessage =
    "Fairness verification requires HTTPS or localhost and a browser with Web Crypto. Wagering is disabled.";
  const randomHex = () =>
    [...crypto.getRandomValues(new Uint8Array(16))]
      .map((n) => n.toString(16).padStart(2, "0"))
      .join("");
  function randomBelow(size) {
    // Quick picks are selections, not outcomes. Sampling the remaining pool
    // guarantees ten distinct picks even if the RNG repeats a value.
    if (!globalThis.crypto?.getRandomValues)
      throw Error(
        "Quick pick needs browser randomness. Select numbers manually.",
      );
    const limit = 4294967296 - (4294967296 % size);
    const word = new Uint32Array(1);
    for (let attempt = 0; attempt < 128; attempt++) {
      crypto.getRandomValues(word);
      if (word[0] < limit) return word[0] % size;
    }
    throw Error("Quick pick could not generate numbers. Please try again.");
  }
  const locked = () => busy || fatal || Boolean(pending);
  const message = (value = "") => {
    if (!value && !secure) value = secureMessage;
    feedback = value;
    id("gamingError").textContent = value;
    id("gamingError").hidden = !value;
    controls();
  };
  try {
    pending = JSON.parse(sessionStorage.getItem("rh.gaming.pending"));
    pendingAction = JSON.parse(sessionStorage.getItem("rh.gaming.action") || sessionStorage.getItem("rh.blackjack.action"));
  } catch {}
  function remember(value) {
    pending = value;
    try {
      value
        ? sessionStorage.setItem("rh.gaming.pending", JSON.stringify(value))
        : sessionStorage.removeItem("rh.gaming.pending");
    } catch {}
    if (id("retryBet")) id("retryBet").hidden = !pending;
  }
  if (id("clientSeed") && secure) {
    let seed = "";
    try {
      seed = localStorage.getItem("rh.gaming.clientSeed") || "";
    } catch {}
    id("clientSeed").value = /^[A-Za-z0-9 _.\-]{1,64}$/.test(seed)
      ? seed
      : randomHex();
    id("clientSeed").addEventListener("change", () => {
      try {
        localStorage.setItem("rh.gaming.clientSeed", id("clientSeed").value);
      } catch {}
    });
  }
  function wagerProblem() {
    if (!id("redWager") || !wallet) return "";
    const wager = Number(id("redWager").value);
    if (!Number.isSafeInteger(wager) || wager < (game === "poker" ? 20 : 1))
      return game === "poker" ? "Choose a table stack of at least 20 whole RedPoints." : "Enter a positive whole-point wager.";
    if (wager > wallet.balance)
      return `Your wager exceeds your ${number(wallet.balance)} RedPoints balance. Lower it to play.`;
    return "";
  }
  function playBlock() {
    if (fatal)
      return "Verification failed. Reload and review your saved receipts before playing.";
    if (!secure) return secureMessage;
    if (!verifierReady || rules.version !== RedFair.VERSION)
      return "Game rules changed or did not load. Reload this page to continue.";
    if (!wallet) return "Loading your balance…";
    if (wallet.play_blocked) return wallet.play_blocked.message;
    if (wallet.needs_profile)
      return "Save your community name to play.";
    if (wallet.blackjack || wallet.poker) {
      if (wallet.play_blocked) return wallet.play_blocked.message;
      if (pendingAction && !wallet.play_blocked) return "";
      if (wallet.poker) return game === "poker"
        ? isHoldem(wallet.poker) ? "Your hand is saved. Use the table controls." : "Choose the cards to hold, then draw once."
        : "Continue your saved Poker hand before starting another game.";
      return game === "blackjack"
        ? "Use Hit, Stand or Double to finish this hand."
        : "Continue your saved Blackjack hand before starting another game.";
    }
    // Recovering an existing receipt remains possible without another debit.
    if (pending && !wallet.needs_profile) return "";
    if (wallet.balance < 1)
      return "Refresh this page to restore 100,000 RedPoints, or wait for the weekly reset.";
    if (game === "limbo" && limboProblem()) return limboProblem();
    if (game === "keno" && !selections.size)
      return "Pick 1–10 numbers to play.";
    return "";
  }
  function controls() {
    const disabled = locked() || Boolean(wallet?.needs_profile);
    const activeHand = Boolean(wallet?.poker || wallet?.blackjack);
    if (betForm) betForm.hidden = activeHand;
    if (id('gameResult')) id('gameResult').hidden = activeHand && playPhase !== 'result';
    if (id('betProof')) id('betProof').hidden = activeHand && playPhase !== 'result';
    root
      .querySelectorAll(
        "#betForm input, #betForm select, #betForm button, [data-keno], #clientSeed, #diceBoardChance",
      )
      .forEach((el) => {
        if (el.id !== "betButton" && el.disabled !== disabled)
          el.disabled = disabled;
      });
    if (id("betButton")) {
      // Only a real in-flight request disables the button. Other blocked
      // states stay clickable so players can see why and how to recover.
      id("betButton").disabled = busy || Boolean(wallet?.needs_profile);
      id("betButton").setAttribute(
        "aria-disabled",
        String(busy || Boolean(playBlock())),
      );
      id("betButton").setAttribute("aria-busy", String(busy));
      id("betButton").textContent = busy
        ? refreshing ? "Restoring points…" : ({submitting:"Submitting…",verifying:"Checking…",playing:"Playing…",recovery:"Recovering…"}[playPhase] || "Playing…")
        : wallet?.needs_profile
          ? "Save your name first"
        : pendingAction
          ? "Recover your move"
          : (wallet?.blackjack || wallet?.poker)
            ? "Hand in progress"
            : pending
              ? "Recover previous round"
              : betLabel;
      let reason = busy
        ? refreshing ? "Restoring balance…" : ({submitting:"Waiting for the server…",verifying:"Checking the saved proof…",playing:"Revealing the result…",recovery:"Checking the saved round…"}[playPhase] || "Saving…")
        : playBlock();
      if (!reason)
        reason =
          feedback ||
          (pending
            ? "Recover the saved round."
            : wagerProblem());
      if (!reason)
        reason =
          game === "plinko"
            ? ""
            : "";
      if (id("betStatus")) {
        id("betStatus").textContent = reason;
        id("betStatus").classList.toggle(
          "is-error",
          Boolean(
            !busy && (feedback || (!(wallet?.blackjack || wallet?.poker) && playBlock()) || (!pending && wagerProblem())),
          ),
        );
      }
      if (wagerProblem()) id("redWager").setAttribute("aria-invalid", "true");
      else id("redWager").removeAttribute("aria-invalid");
    }
    root.querySelectorAll("[data-blackjack]").forEach((button) => {
      button.disabled =
        busy ||
        fatal ||
        !secure ||
        !verifierReady ||
        Boolean(wallet?.needs_profile) ||
        !wallet?.blackjack ||
        Boolean(pendingAction) ||
        Boolean(wallet?.play_blocked) ||
        (button.dataset.blackjack === "double" && !wallet.blackjack.can_double);
    });
    const pokerLocked = busy || fatal || !secure || !verifierReady ||
      !wallet?.poker || Boolean(wallet?.needs_profile) || Boolean(pendingAction);
    root.querySelectorAll("[data-poker-hold],#pokerDraw,#pokerHoldAll,#pokerClear").forEach(button => {
      button.disabled = pokerLocked;
    });
    if (id("pokerDraw")) id("pokerDraw").textContent = busy ? "Saving draw…" :
      pokerHolds.size === 5 ? "Keep all · finish hand" : `Draw ${5-pokerHolds.size} card${pokerHolds.size === 4 ? "" : "s"}`;
    holdemTable?.controls(pokerLocked || !isHoldem(wallet?.poker));
    if (id("retryBet")) {
      id("retryBet").textContent = pendingAction
        ? "Recover your move"
        : "Recover pending result";
      id("retryBet").hidden =
        !pending || Boolean((wallet?.blackjack || wallet?.poker) && !pendingAction);
      id("retryBet").disabled = busy || fatal || !secure || !verifierReady || Boolean(wallet?.needs_profile);
    }
  }
  function gameLabel(value) {
    return value === "poker" ? "Hold’em" : value ? value[0].toUpperCase() + value.slice(1) : "All games";
  }
  function renderCommunity(next) {
    if (!next || !id("gamingPublicLeaders")) return;
    community = next;
    const available = new Set(["all", ...(rules.games || [])]);
    if (!available.has(communityFilter)) communityFilter = "all";
    const count = id("gamingActivityCount");
    if (count) {
      const strong = count.querySelector("strong");
      if (strong) strong.textContent = number(next.active_count || 0);
    }
    id("gamingGameFilters")?.querySelectorAll("[data-community-filter]").forEach(button => {
      const filter = button.dataset.communityFilter;
      const total = filter === "all" ? next.active_count || 0 : next.game_counts?.[filter] || 0;
      const amount = button.querySelector("b");
      if (amount) amount.textContent = number(total);
      const active = filter === communityFilter;
      button.classList.toggle("is-active", active);
      button.setAttribute("aria-pressed", String(active));
    });
    const live = id("gamingLivePlayers");
    if (live) {
      const players = (Array.isArray(next.live_players) ? next.live_players : [])
        .filter(row => communityFilter === "all" || row.game === communityFilter);
      live.replaceChildren(...(players.length ? players.map(row => {
        const article = document.createElement("article");
        const avatar = document.createElement("span");
        avatar.className = "gaming-live-avatar";
        avatar.textContent = (row.name || "?").slice(0, 1).toUpperCase();
        const detail = document.createElement("div");
        const name = document.createElement("strong");
        name.textContent = row.name || "Player";
        const meta = document.createElement("small");
        meta.textContent = `${row.game_label || gameLabel(row.game)} · ${row.status || "Recently active"}`;
        detail.append(name, meta);
        article.append(avatar, detail);
        return article;
      }) : [Object.assign(document.createElement("p"), {
        className: "empty",
        textContent: communityFilter === "all" ? "No public players are active right now." : `No public ${gameLabel(communityFilter)} players are active right now.`,
      })]));
    }
    const title = id("gamingWeeklyTitle");
    if (title) title.textContent = communityFilter === "all" ? "RedPoints leaders" : `${gameLabel(communityFilter)} leaders`;
    const leaders = id("gamingPublicLeaders");
    if (leaders) {
      const source = communityFilter === "all" ? next.weekly_leaders : next.game_leaders?.[communityFilter];
      const rows = Array.isArray(source) ? source : [];
      const nextRanks = new Map(communityRanks);
      leaders.replaceChildren(...(rows.length ? rows.map(row => {
        const item = document.createElement("li");
        const rank = document.createElement("span");
        rank.className = "gaming-public-rank";
        rank.textContent = String(row.rank || 0).padStart(2, "0");
        const name = document.createElement("strong");
        name.textContent = row.name || "Player";
        const result = document.createElement("span");
        const net = document.createElement("b");
        net.textContent = points(row.net || 0);
        const rounds = document.createElement("small");
        rounds.textContent = `${number(row.rounds || 0)} rounds`;
        const rankKey = `${communityFilter}:${row.name || "Player"}`;
        const prior = communityRanks.get(rankKey);
        if (Number.isInteger(prior) && prior !== row.rank) {
          const movement = document.createElement("i");
          movement.className = row.rank < prior ? "rank-up" : "rank-down";
          movement.textContent = row.rank < prior ? "↑" : "↓";
          movement.setAttribute("aria-label", row.rank < prior ? "Moved up" : "Moved down");
          result.append(movement);
        }
        nextRanks.set(rankKey, row.rank);
        result.append(net, rounds);
        item.append(rank, name, result);
        return item;
      }) : [Object.assign(document.createElement("li"), {
        className: "empty",
        textContent: communityFilter === "all" ? "No public results yet this week." : `No public ${gameLabel(communityFilter)} results yet this week.`,
      })]));
      communityRanks = nextRanks;
    }
  }

  document.querySelector(".gaming-community-tabs")?.addEventListener("click", event => {
    const button = event.target.closest("[data-community-view]");
    if (!button) return;
    const view = button.dataset.communityView;
    document.querySelectorAll("[data-community-view]").forEach(node => {
      const active = node === button;
      node.classList.toggle("is-active", active);
      node.setAttribute("aria-selected", String(active));
    });
    document.querySelectorAll("[data-community-panel]").forEach(panel => {
      panel.hidden = panel.dataset.communityPanel !== view;
    });
  });

  id("gamingGameFilters")?.addEventListener("click", event => {
    const button = event.target.closest("[data-community-filter]");
    if (!button) return;
    communityFilter = button.dataset.communityFilter || "all";
    try { localStorage.setItem("rh.gaming.communityFilter", communityFilter); } catch {}
    renderCommunity(community);
  });


  function renderWallet(next) {
    if (
      !next ||
      !Number.isSafeInteger(next.balance) ||
      next.balance < 0 ||
      !next.season
    )
      throw Error("Invalid wallet response");
    if (
      wallet &&
      (Number(next.season.id) < Number(wallet.season.id) ||
        next.version < wallet.version ||
        next.nonce < wallet.nonce)
    )
      return;
    if (!wallet && id("redWager")?.value === "100" && next.balance > 0)
      id("redWager").value = String(Math.min(100, next.balance));
    wallet = next;
    const reserved = next.blackjack?.wager || next.poker?.buy_in || next.poker?.wager || 0;
    if (id('pointsInPlay')) id('pointsInPlay').textContent = number(reserved);
    const recent = next.receipts?.[0];
    if (id('pointsNet')) {
      id('pointsNet').textContent = recent ? points(recent.net) : '—';
      id('pointsNet').dataset.tone = !recent || !recent.net ? 'neutral' : recent.net > 0 ? 'positive' : 'negative';
    }
    if (next.blackjack && !pending) remember(next.blackjack.bet);
    if (id("blackjackResume"))
      id("blackjackResume").hidden = !next.blackjack || game === "blackjack";
    if (next.poker) {
      if (pending?.request_id === next.poker.round_id && pending.initial_cards &&
          RedFair.canonical(pending.initial_cards) !== RedFair.canonical(next.poker.initial)) {
        fatal = true;
        throw Error("The saved initial Poker cards changed. Keep your receipt and reload before playing.");
      }
      if (isHoldem(next.poker)) {
        assertHoldemActions(next.poker, pending);
        if (pendingAction?.variant === "texas_holdem" && pendingAction.round_id === next.poker.round_id && next.poker.step > pendingAction.step) {
          rememberAction(null); // A lost reply is acknowledged by the saved matching action.
          message();
        }
      }
      if (!pending || pending.request_id === next.poker.round_id)
        remember({ ...(pending || next.poker.bet), initial_cards: [...next.poker.initial],
          ...(isHoldem(next.poker) ? {player_actions:next.poker.actions} : {}) });
    }
    if (id("pokerResume")) id("pokerResume").hidden = !next.poker || game === "poker";
    if (!busy && !root.dataset.animating && (next.poker || next.blackjack)) phase("ready", "Your turn");
    renderPoker(next.poker);
    renderBlackjack(next.blackjack);
    // The signed player owns this balance. Connection metadata never blocks play.
    // Label the allowance until the player confirms their community name.
    const unclaimed = next.needs_profile && !next.play_blocked;
    id("pointsBalance").textContent = next.play_blocked && next.needs_profile
      ? "—" : number(unclaimed ? Math.max(100000, next.balance) : next.balance);
    id("pointsLabel").textContent = unclaimed ? "STARTING REDPOINTS" : "AVAILABLE REDPOINTS";
    if (id("redWager")) id("redWager").max = String(next.balance);
    id("pointsReset").textContent = unclaimed
      ? "Save your name to play."
      : "Resets " + next.season.end_et;
    
    const profileDialog = id("gamingProfile");
    if (profileDialog) {
      const shouldPrompt = next.needs_profile && profileDialog.dataset.autostart === "true";
      if (!next.needs_profile && profileDialog.open) profileDialog.close();
      else if (shouldPrompt && !profileDialog.open && typeof profileDialog.showModal === "function") profileDialog.showModal();
    }
    if (id("openGamingProfile")) id("openGamingProfile").hidden = !next.needs_profile;
    if (id("gamingNetworkNotice")) {
      id("gamingNetworkNotice").hidden = !next.play_blocked;
      id("gamingNetworkReason").textContent = next.play_blocked?.message || "";
    }
    if (id("gamingIdentity")) id("gamingIdentity").hidden = next.needs_profile;
    id("gamingPlayerName").textContent = next.name;
    const publicChoice = id('gamingPublicVisibility');
    if (publicChoice && document.activeElement !== publicChoice) publicChoice.checked = Boolean(next.public_visibility || next.needs_profile);
    if (id("gamingCreateRecovery")) id("gamingCreateRecovery").disabled = next.needs_profile;
    if (id("fairCommitment"))
      id("fairCommitment").textContent =
        next.commitment || "Save your name to prepare a commitment.";
    if (id("fairNonce")) id("fairNonce").textContent = next.nonce;
    const nextStatsKey = JSON.stringify(next.stats);
    if (id("gamingStats") && statsKey !== nextStatsKey) {
      statsKey = nextStatsKey;
      id("gamingStats").replaceChildren(
        ...Object.entries(next.stats).map(([name, stat]) => {
          const article = document.createElement("article");
          article.dataset.tone = stat.net > 0 ? "positive" : stat.net < 0 ? "negative" : "neutral";
          for (const [tag, text] of [
            ["strong", name === "poker" ? "Hold’em" : name[0].toUpperCase() + name.slice(1)],
            ["b", points(stat.net)],
            ["small", `${stat.bets} rounds · net RedPoints`],
          ]) {
            const el = document.createElement(tag);
            el.textContent = text;
            article.append(el);
          }
          return article;
        }),
      );
    }
    const nextHistoryKey = next.receipts.map(r => r.request_id+':'+r.rules_version).join('|');
    if (historyKey !== nextHistoryKey || !id('betHistory').dataset.loaded) {
    const focusedReceipt = document.activeElement?.dataset.receipt;
    historyKey = nextHistoryKey;
    id('betHistory').dataset.loaded = 'true';
    id("betHistory").replaceChildren(
      ...(next.receipts.length
        ? next.receipts.map((receipt, index) => {
            const tr = document.createElement("tr");
            tr.dataset.tone = receipt.net > 0 ? 'positive' : receipt.net < 0 ? 'negative' : 'neutral';
            tr.hidden = !historyExpanded && index >= 5;
            for (const text of [
              receipt.game === "poker" ? isHoldem(receipt) ? "Hold’em" : "Video Poker · legacy" : receipt.game,
              number(receipt.result?.total_wager ?? receipt.wager),
              number(isHoldem(receipt) ? receipt.result.returned : receipt.payout),
              points(receipt.net),
            ]) {
              const td = document.createElement("td");
              td.textContent = text;
              tr.append(td);
            }
            const td = document.createElement("td"),
              button = document.createElement("button");
            button.type = "button";
            button.dataset.receipt = receipt.request_id;
            button.className = "text-link";
            button.textContent = "Verify";
            button.addEventListener("click", async () => {
              button.disabled = true; button.textContent = 'Checking…';
              try {
                button.textContent = (await RedFair.verify(receipt))
                  ? "Verified · download"
                  : "Verification failed";
                const blob = new Blob([JSON.stringify(receipt, null, 2)], {
                    type: "application/json",
                  }),
                  url = URL.createObjectURL(blob),
                  a = document.createElement("a");
                a.href = url;
                a.download = `redpoints-${receipt.request_id}.json`;
                a.click();
                setTimeout(() => URL.revokeObjectURL(url), 1000);
              } catch {
                button.textContent = "Verification failed";
              } finally { button.disabled = false; }
            });
            td.append(button);
            tr.append(td);
            return tr;
          })
        : [
            (() => {
              const tr = document.createElement("tr"),
                td = document.createElement("td");
              td.colSpan = 5;
              td.textContent = "No rounds yet.";
              td.className = "empty";
              tr.append(td);
              return tr;
            })(),
          ]),
    );
    if (focusedReceipt) [...id('betHistory').querySelectorAll('[data-receipt]')].find(node => node.dataset.receipt === focusedReceipt)?.focus({preventScroll:true});
    }
    if (id('historyToggle')) {
      id('historyToggle').hidden = next.receipts.length <= 5;
      id('historyToggle').textContent = historyExpanded ? 'Show fewer' : `View all ${next.receipts.length} rounds`;
      id('historyToggle').setAttribute('aria-expanded', String(historyExpanded));
    }
    controls();
  }
  id('historyToggle')?.addEventListener('click', () => {
    historyExpanded = !historyExpanded;
    [...id('betHistory').rows].forEach((row, index) => row.hidden = !historyExpanded && index >= 5);
    renderWallet(wallet);
  });
  async function api(url, body, conditional = false) {
    const controller = new AbortController(),
      timeout = setTimeout(() => controller.abort(), 15000);
    try {
      const response = await fetch(url, {
        method: body ? "POST" : "GET",
        cache: "no-store",
        credentials: "same-origin",
        signal: controller.signal,
        headers: {
          Accept: "application/json",
          ...(conditional && walletEtag ? { "If-None-Match": walletEtag } : {}),
          ...(body
            ? { "Content-Type": "application/json", "X-CSRF-Token": csrf }
            : {}),
        },
        body: body ? JSON.stringify(body) : undefined,
      });
      if (conditional && response.status === 304) return null;
      if (conditional) walletEtag = response.headers.get("etag") || "";
      if (!response.headers.get("content-type")?.includes("application/json"))
        throw Error(
          `The server returned HTTP ${response.status}. Your pending wager is protected; retry to recover it.`,
        );
      const value = await response.json();
      if (!response.ok) {
        const error = Error(
          (value.error || `Request failed (${response.status})`) +
          (response.status >= 500 && value.request_id ? ` Reference: ${value.request_id}.` : ''),
        );
        error.code = value.code || "";
        error.definitive = response.status < 500 && response.status !== 408;
        throw error;
      }
      if (value.release !== document.body.dataset.release)
        throw Error("The app was updated. Reload before continuing.");
      if (value.player_csrf) csrf = value.player_csrf;
      return value;
    } finally {
      clearTimeout(timeout);
    }
  }
  function opt() {
    if (game === "blackjack") return { decks: 6 };
    if (game === "baccarat") return {decks:8, side:root.querySelector('[name="baccaratSide"]:checked').value};
    if (game === "poker") return { variant: "texas_holdem", button:wallet?.poker_button || "player" };
    if (game === "limbo") return { target: Math.round(Number(id("limboTarget").value)*100) };
    if (game === "coinflip") return { side: root.querySelector('[name="coinSide"]:checked').value };
    if (game === "dice") return { chance: Number(id("diceChance").value), side: id("diceSide").value };
    if (game === "keno") return { picks: [...selections].sort((a,b) => a-b), risk: root.querySelector('[name="risk"]:checked').value };
    return { rows: Number(id("plinkoRows").value), risk: root.querySelector('[name="risk"]:checked').value };
  }
  function limboProblem() {
    const value = Number(id("limboTarget")?.value);
    return !Number.isFinite(value) || value < 1.01 || value > 1000000 ||
      Math.abs(value*100-Math.round(value*100)) > 0.000001
      ? "Use a target from 1.01× to 1,000,000× with at most two decimals." : "";
  }
  const multiple = (units) =>
    (units / 10000).toLocaleString("en-US", { maximumFractionDigits: 4 }) + "×";
  function clearResult() {
    presentationSequence++;
    delete root.dataset.animating;
    // Old receipt highlights must never look like the next selection or draw.
    root
      .querySelectorAll("[data-keno]")
      .forEach((el) => el.classList.remove("drawn", "matched"));
    if (id("gameResult")) {
      id("gameResult").textContent = "Ready.";
      id("gameResult").classList.remove("is-win");
      id("betProof").textContent = "";
    }
    if (id("diceRoll")) {
      id("diceRoll").textContent = "—";
      id("diceRollLabel").textContent = "Your next roll";
      id("diceMarker").hidden = true;
    }
    if (id("limboResult")) {
      id("limboResult").textContent = "1.00×";
      id("limboResult").closest(".limbo-stage").classList.remove("is-win");
      id("limboTrail").style.transform = "scaleX(0)";
      id("limboStatus").textContent = "Ready.";
    }
    if (id("redCoin")) {
      id("redCoin").style.transform = "rotateY(0deg)";
      id("redCoin").setAttribute("aria-label", "Ready to flip");
      id("coinStatus").textContent = "Ready.";
    }
    if (id("plinkoResult"))
      id("plinkoResult").textContent =
        "Ready to drop.";
  }
  function settingsChanged() {
    if (locked()) return;
    clearResult();
    message();
    payout();
    controls();
  }
  function payout() {
    if (!game) return;
    const options = opt(),
      wager = Number(id("redWager").value) || 0;
    // Large stakes can overflow Number during multiplication even when the
    // final return is exact. Preview with the same integer math as settlement.
    const amount =
      Number.isSafeInteger(wager) && wager > 0 ? BigInt(wager) : 0n;
    if (game === "dice") {
      id("diceChanceLabel").textContent = options.chance + "%";
      const threshold =
        options.side === "under" ? options.chance : 100 - options.chance;
      if (id("diceBoardChance")) {
        id("diceBoardChance").value = String(threshold);
        id("diceBoardChance").setAttribute(
          "aria-valuetext",
          `${options.chance}% win chance; threshold ${threshold}`,
        );
        id("diceBoardChanceLabel").textContent =
          `${options.chance}% win chance`;
        const track = id("diceBoardChance").closest(".dice-track");
        track.style.setProperty("--dice-threshold", threshold + "%");
        track.classList.toggle("is-over", options.side === "over");
      }
      id("diceTarget").textContent =
        options.side === "under"
          ? `Roll below ${options.chance.toFixed(2)}`
          : `Roll at or above ${(100 - options.chance).toFixed(2)}`;
      id("dicePayout").textContent =
        number((amount * 99n) / BigInt(options.chance)) +
        " points returned on a win";
      id("payoutDescription").textContent =
        `${options.chance}% chance · ${(99 / options.chance).toFixed(4)}× return`;
      return;
    }
    if (game === "blackjack") {
      id("payoutDescription").textContent =
        "Blackjack 2.5× · Win 2× · Push 1× · Loss 0×";
      return;
    }
    if (game === "limbo") {
      const invalid = limboProblem();
      if (invalid) {
        id("payoutDescription").textContent = invalid;
        id("limboPayout").textContent = "Choose a valid target";
        id("limboChance").textContent = "—";
        return;
      }
      const wins = 99n*4294967296n/BigInt(options.target);
      const chance = (Number(wins)*100/4294967296).toLocaleString("en-US", {maximumFractionDigits:7});
      const target = (options.target/100).toLocaleString("en-US",{minimumFractionDigits:2,maximumFractionDigits:2});
      id("limboChance").textContent = `${chance}% win chance`;
      id("limboPayout").textContent = `${number(amount*BigInt(options.target)/100n)} points returned on a win`;
      id("limboTargetLabel").textContent = `Your target · ${target}×`;
      id("payoutDescription").textContent = `${target}× target · ${chance}% chance`;
      return;
    }
    if (game === "coinflip") {
      id("coinPayout").textContent = `${number(amount*198n/100n)} points returned on a win`;
      id("payoutDescription").textContent = "Win 1.98× · Loss 0× · 50% chance";
      return;
    }
    if (game === "poker" && !wallet?.poker?.holds && (!wallet?.poker || isHoldem(wallet.poker))) {
      const stack = Number(id("redWager").value), big = Math.max(2, Math.floor(stack/50));
      id("holdemNextBlinds").textContent = `Blinds ${number(Math.max(1,Math.floor(big/2)))} / ${number(big)} RP`;
      id("payoutDescription").textContent = "Strongest to weakest. Best five of seven wins; suits do not break ties.";
      id("payoutTable").replaceChildren(...[...(globalThis.RedHoldemFair?.labels || [])].reverse().map(label => Object.assign(document.createElement("div"), {textContent:label})));
      return;
    }
    if (game === "poker") {
      id("payoutDescription").textContent = "9/6 Jacks or Better · Total returns";
      id("payoutTable").classList.add("poker-paytable");
      id("payoutTable").replaceChildren(...Object.entries(rules.poker.legacy_paytable).sort((a,b) => b[1]-a[1]).map(([hand, multiplier]) => {
        const cell = document.createElement("div");cell.dataset.hand = hand;
        for (const [tag, text] of [["small", rules.poker.legacy_labels[hand]], ["strong", `${multiplier}×`], ["small", `${number(amount*BigInt(multiplier))} returned`]]) {
          const node = document.createElement(tag);node.textContent = text;cell.append(node);
        }
        return cell;
      }));
      return;
    }
    if (game === "baccarat") {
      id("baccaratPayout").textContent = `${number(amount*BigInt(rules.baccarat.returns[options.side])/10000n)} points returned on a win`;
      id("payoutDescription").textContent = "Player 2× · Banker 1.95× · Tie 9×. Banker includes 5% commission. Player / Banker push on a tie.";
      return;
    }
    const size = game === "keno" ? Math.max(1, selections.size) : options.rows,
      info = rules[game][String(size)][options.risk];
    if (game === "keno") {
      id("kenoSelection").textContent = selections.size
        ? `${selections.size} selected · ${[...selections].sort((a, b) => a - b).join(", ")}`
        : "Pick 1–10 numbers on the board.";
      root.querySelectorAll("[data-keno]").forEach((el) => {
        const selected = selections.has(Number(el.dataset.keno));
        el.classList.toggle("selected", selected);
        el.setAttribute("aria-pressed", String(selected));
      });
      if (!selections.size) {
        id("payoutDescription").textContent =
          "Select 1–10 numbers to see the payout table.";
        id("payoutTable").replaceChildren();
        return;
      }
    }
    id("payoutDescription").textContent =
      `${game === "keno" ? size + " picked number(s) · payout by matches" : "Slot 0 at the left → slot " + size + " at the right"} · ${info.rtp_percent}% RTP`;
    id("payoutTable").replaceChildren(
      ...info.multipliers.map((value, index) => {
        const box = document.createElement("div");
        for (const [tag, text] of [
          [
            "small",
            game === "keno"
              ? `${index} match${index === 1 ? "" : "es"}`
              : `Slot ${index}`,
          ],
          ["strong", multiple(value)],
          ["small", `${number((amount * BigInt(value)) / 10000n)} RP`],
        ]) {
          const el = document.createElement(tag);
          el.textContent = text;
          box.append(el);
        }
        box.title = `Outcome probability: ${(info.probabilities[index] * 100).toFixed(6)}%`;
        return box;
      }),
    );
    if (game === "plinko") plinko.setBoard(options.rows, info.multipliers);
  }
  // One canvas loop for every visible ball. Outcomes come only from verified
  // receipts; the renderer never samples randomness or changes a payout.
  const plinko = game === "plinko" && globalThis.RedPlinko
    ? RedPlinko.create({id, multiple})
    : {setBoard: () => false, drop: (_rows, _values, _result, done) => done?.()};

  // Animation is presentation only: settle and verify first, then reveal the
  // recorded outcome. No fake rolls, re-deals, navigation or wallet mutations.
  const reducedMotion = () => document.hidden || globalThis.matchMedia?.("(prefers-reduced-motion: reduce)").matches;
  function tween(duration, paint) {
    return new Promise(resolve => {
      let frame, timeout, finished = false;
      const start = performance.now();
      const finish = () => {
        if (finished) return;
        finished = true;
        cancelAnimationFrame(frame); clearTimeout(timeout);
        document.removeEventListener("visibilitychange", hidden);
        paint(1); resolve();
      };
      const hidden = () => { if (document.hidden) finish(); };
      const tick = now => {
        const progress = Math.min(1, Math.max(0, (now-start)/duration));
        if (progress === 1) return finish();
        paint(progress); frame = requestAnimationFrame(tick);
      };
      if (reducedMotion() || typeof requestAnimationFrame !== "function") return finish();
      paint(0);
      document.addEventListener("visibilitychange", hidden);
      frame = requestAnimationFrame(tick);
      timeout = setTimeout(finish, duration+120);
    });
  }
  function animateElement(node, frames, duration=380, delay=0) {
    if (!node?.animate || reducedMotion()) return Promise.resolve();
    const animation = node.animate(frames, {duration, delay, easing:"cubic-bezier(.2,.75,.25,1)", fill:"backwards"});
    // Bounded by a wall-clock timer and visibility handling; a suspended RAF
    // can never leave gameplay disabled or display an intermediate outcome.
    return tween(duration+delay, () => {}).finally(() => animation.cancel());
  }
  function dealCard(node, delay=0, flip=false) {
    const task = animateElement(node, flip
      ? [{opacity:.25,transform:"rotateY(90deg)"},{opacity:1,transform:"rotateY(0)"}]
      : [{opacity:0,transform:"translate(24px,-32px) rotate(8deg) scale(.92)"},{opacity:1,transform:"translate(0,0) rotate(0) scale(1)"}], 420, delay);
    cardAnimations.add(task);
    task.finally(() => cardAnimations.delete(task));
  }
  const waitForCards = () => Promise.all([...cardAnimations]);
  function playingCard(card) {
    const node = document.createElement("span");
    node.className = "playing-card";
    node.dataset.card = String(card);
    if (card === null) {
      node.classList.add("is-hidden"); node.textContent = "◆";
      node.setAttribute("aria-label", "Face-down card");
    } else {
      const rank = card % 13+1, suit = Math.floor((card % 52)/13);
      const label = ["","A","2","3","4","5","6","7","8","9","10","J","Q","K"][rank];
      node.textContent = label+["♠","♥","♣","♦"][suit];
      node.classList.toggle("is-red", suit === 1 || suit === 3);
      node.setAttribute("aria-label", `${label} of ${["spades","hearts","clubs","diamonds"][suit]}`);
    }
    return node;
  }
  async function animateBaccarat(result) {
    const revealed = {player:[],banker:[]};
    for (const side of ["player","banker"]) {
      const label = side[0].toUpperCase()+side.slice(1);
      id(`baccarat${label}`).replaceChildren();
      id(`baccarat${label}Total`).textContent = "—";
      id(`baccarat${label}Hand`).classList.remove("is-winner");
    }
    id("baccaratStatus").textContent = "Dealing…";
    const sequence = [["player",0],["banker",0],["player",1],["banker",1]];
    if (result.player.length === 3) sequence.push(["player",2]);
    if (result.banker.length === 3) sequence.push(["banker",2]);
    let shown = 0;
    await tween(sequence.length*190+240, progress => {
      const count = progress === 1 ? sequence.length : Math.min(sequence.length,Math.floor(progress*(sequence.length+1)));
      while (shown < count) {
        const [side,index] = sequence[shown++], card = result[side][index];
        const label = side[0].toUpperCase()+side.slice(1), node = playingCard(card);
        id(`baccarat${label}`).append(node); revealed[side].push(card);
        dealCard(node);
        const total = revealed[side].reduce((sum,c) => sum+(c%13+1 < 10 ? c%13+1 : 0),0)%10;
        id(`baccarat${label}Total`).textContent = total;
      }
    });
    await waitForCards();
    for (const side of ["player","banker"]) {
      const label = side[0].toUpperCase()+side.slice(1);
      id(`baccarat${label}Hand`).classList.toggle("is-winner",result.winner === side || result.winner === "tie");
    }
    id("baccaratStatus").textContent = `${result.winner === "tie" ? "Tie" : result.winner === "player" ? "Player wins" : "Banker wins"}${result.natural ? " · Natural" : ""}`;
  }
  async function showReceipt(receipt) {
    if (!id("gameResult")) return;
    const ticket = ++presentationSequence, r = receipt.result;
    const done = () => {
      if (ticket !== presentationSequence) return;
      delete root.dataset.animating;
      phase("result");
      id("gameResult").textContent = isHoldem(receipt)
        ? `${points(receipt.net)} RP net · ${number(r.payout)} returned to wallet`
        : `${points(receipt.net)} RP · ${number(receipt.payout)} returned`;
      if (receipt.game === "keno") id("gameResult").textContent = `${r.hits} matched · `+id("gameResult").textContent;
      id("gameResult").classList.toggle("is-win",receipt.net > 0);
      id("betProof").textContent = `Verified · #${receipt.nonce}`;
      void animateElement(id("gameResult"), [{opacity:0,transform:"translateY(6px)"},{opacity:1,transform:"translateY(0)"}],240);
    };
    if (receipt.game !== game) { done(); return; }
    root.dataset.animating = game;
    phase("playing"); controls();
    id("gameResult").textContent = "Playing…";
    id("betProof").textContent = "";
    if (game === "plinko") {
      id("plinkoResult").textContent = "Dropping…";
      plinko.drop(receipt.options.rows, RedFair.table("plinko",receipt.options.rows,receipt.options.risk,receipt.rules_version), r, () => {
        if (ticket === presentationSequence) id("plinkoResult").textContent = `Slot ${r.slot} · ${multiple(r.multiplier)}`;
        done();
      });
      return; // Multiple committed balls can share one rendering loop.
    }
    if (game === "dice") {
      id("diceRollLabel").textContent = "Rolling…";
      id("diceMarker").hidden = false;
      await tween(750, progress => {
        const roll = r.roll*(1-(1-progress)**3);
        id("diceRoll").textContent = progress === 1 ? (r.roll/100).toFixed(2) : "···";
        id("diceMarker").textContent = progress === 1 ? (r.roll/100).toFixed(2) : "●";
        id("diceMarker").style.left = `calc(${roll/100}% + ${12-24*roll/10000}px)`;
      });
      id("diceRollLabel").textContent = r.won ? "Target matched" : "Outside target";
    } else if (game === "keno") {
      root.querySelectorAll("[data-keno]").forEach(node => node.classList.remove("drawn","matched"));
      let shown = 0;
      await tween(1600, progress => {
        const count = progress === 1 ? 10 : Math.min(10,Math.floor(progress*10));
        while (shown < count) {
          const n = r.drawn[shown++], node = root.querySelector(`[data-keno="${n}"]`);
          node.classList.add("drawn"); node.classList.toggle("matched",receipt.options.picks.includes(n));
          void animateElement(node,[{transform:"scale(.88)"},{transform:"scale(1.08)",offset:.6},{transform:"scale(1)"}],220);
        }
      });
    } else if (game === "limbo") await animateLimbo(r);
    else if (game === "coinflip") await animateCoin(r);
    else if (game === "baccarat") await animateBaccarat(r);
    else if (game === "poker") { renderPoker({...r, round_id:receipt.request_id, wager:receipt.wager}); await waitForCards(); }
    else if (game === "blackjack") { renderBlackjack({...r, nonce:receipt.nonce, round_id:receipt.request_id}); await waitForCards(); }
    done();
  }
  function assertHoldemActions(value, body) {
    if (!isHoldem(value)) return;
    const actions = value.actions || [], saved = body?.player_actions || [];
    const mismatch = saved.some((move,index) => RedFair.canonical(move) !== RedFair.canonical(actions[index]));
    const pendingMismatch = pendingAction?.variant === "texas_holdem" &&
      pendingAction.round_id === (value.round_id || value.request_id) && value.ending !== "weekly_reset" &&
      (value.ended || value.result || actions.length > pendingAction.step) &&
      RedFair.canonical(actions[pendingAction.step]) !== RedFair.canonical(pendingAction.move);
    if (mismatch || pendingMismatch) {
      fatal = true;
      throw Error("Hold’em action history changed. Your saved proof has been retained.");
    }
  }
  async function verifyReceipt(receipt, body) {
    phase("verifying"); controls();
    assertHoldemActions(receipt, body);
    const fields = [
      "rules_version",
      "request_id",
      "season",
      "game",
      "client_seed",
      "client_salt",
      "nonce",
      "wager",
      "options",
    ];
    if (body.game === "poker" && !isHoldem(body) && pendingAction?.game === "poker" &&
        pendingAction.round_id === receipt.request_id && receipt.ending !== "weekly_reset" &&
        RedFair.canonical(receipt.holds) !== RedFair.canonical(pendingAction.holds)) {
      fatal = true;
      throw Error("Poker hold verification failed. Keep your receipt for review.");
    }
    if (body.game === "poker" && body.initial_cards &&
        RedFair.canonical(body.initial_cards) !== RedFair.canonical(receipt.result?.initial)) {
      fatal = true;
      throw Error("Poker initial-card verification failed. Keep your receipt for review.");
    }
    let timeout;
    const verified = await Promise.race([
      RedFair.verify(receipt, body.commitment),
      new Promise((_, reject) => {
        timeout = setTimeout(
          () =>
            reject(
              Error(
                "Verification timed out. Recover this round before playing again.",
              ),
            ),
          10000,
        );
      }),
    ]).finally(() => clearTimeout(timeout));
    if (
      !fields.every(
        (key) =>
          RedFair.canonical(receipt[key]) === RedFair.canonical(body[key]),
      ) ||
      !verified
    ) {
      fatal = true;
      throw Error(
        "Fairness verification failed. Stop playing and download your receipts for review.",
      );
    }
  }
  async function recoverSavedRound(next) {
    if (!pending || busy || fatal || !secure || !verifierReady) return;
    const body = pending;
    const receipt = next.receipts.find(
      (item) => item.request_id === body.request_id,
    );
    if (!receipt) return;
    busy = true;
    phase("recovery");
    controls();
    try {
      // Read-only recovery: verify the existing receipt against the original
      // commitment before clearing a lost-response marker. Never debit again.
      await verifyReceipt(receipt, body);
      remember(null);
      rememberAction(null);
      message();
      await showReceipt(receipt);
    } catch (error) {
      message(error.message);
    } finally {
      busy = false;
      if (fatal) { phase('error'); if (id('betProof')) id('betProof').textContent = 'Verification failed'; }
      else if (!root.dataset.animating && playPhase !== 'result') phase(pending && !wallet?.poker && !wallet?.blackjack ? 'recovery' : 'ready', wallet?.poker || wallet?.blackjack ? 'Your turn' : '');
      controls();
    }
  }
  async function submit(body) {
    if (busy || fatal || !secure || !verifierReady) return;
    busy = true;
    phase("submitting");
    controls();
    message();
    try {
      const result = await api("/gaming/api/bet", body),
        receipt = result.receipt;
      if (!receipt && (result.wallet?.blackjack || result.wallet?.poker)) {
        phase("playing");
        renderWallet(result.wallet);
        await waitForCards();
        message();
        return;
      }
      await verifyReceipt(receipt, body);
      remember(null);
      rememberAction(null);
      await showReceipt(receipt);
      renderWallet(result.wallet);
    } catch (error) {
      if (error.definitive) {
        remember(null);
        try {
          renderWallet((await api("/gaming/api/state")).wallet);
        } catch {}
      }
      message(
        error.name === "AbortError"
          ? "The response timed out. Recover the pending result before placing another wager."
          : error.message,
      );
    } finally {
      busy = false;
      if (fatal) { phase('error'); if (id('betProof')) id('betProof').textContent = 'Verification failed'; }
      else if (!root.dataset.animating && playPhase !== 'result') phase(pending && !wallet?.poker && !wallet?.blackjack ? 'recovery' : 'ready', wallet?.poker || wallet?.blackjack ? 'Your turn' : '');
      controls();
    }
  }
  function rememberAction(value) {
    pendingAction = value;
    try {
      value
        ? sessionStorage.setItem("rh.gaming.action", JSON.stringify(value))
        : sessionStorage.removeItem("rh.gaming.action");
      sessionStorage.removeItem("rh.blackjack.action");
    } catch {}
  }
  async function animateLimbo(result) {
    const display = id("limboResult"), multiplier = result.multiplier/100;
    display.closest(".limbo-stage").classList.remove("is-win");
    id("limboStatus").textContent = "Climbing…";
    await tween(950, progress => {
      const value = progress === 1 ? multiplier : Math.exp(Math.log(multiplier)*(1-(1-progress)**2));
      display.textContent = value.toLocaleString("en-US",{minimumFractionDigits:2,maximumFractionDigits:2})+"×";
      id("limboTrail").style.transform = `scaleX(${progress})`;
    });
    display.closest(".limbo-stage").classList.toggle("is-win",result.won);
    id("limboStatus").textContent = result.won ? "Target reached" : "Below target";
  }
  async function animateCoin(result) {
    const coin = id("redCoin"), face = result.side === "heads" ? 0 : 180;
    coin.style.transform = `rotateY(${face}deg)`;
    id("coinStatus").textContent = "Flipping…";
    await animateElement(coin,[{transform:"rotateY(0deg) translateY(0)"},
      {transform:`rotateY(${540+face/2}deg) translateY(-28px)`,offset:.5},
      {transform:`rotateY(${1080+face}deg) translateY(0)`}],1050);
    coin.setAttribute("aria-label",result.side === "heads" ? "Heads" : "Tails");
    id("coinStatus").textContent = `${result.side === "heads" ? "Heads" : "Tails"} · ${result.won ? "Correct call" : "Other side"}`;
  }
  holdemTable = globalThis.RedHoldemUI?.create(root, {
    number, playingCard, animateElement, tween, error:message, changed:controls,
    move(move) {
      const hand = wallet?.poker;
      if (!isHoldem(hand) || busy || fatal || pendingAction || !secure || !verifierReady || holdemTable?.isMoving()) return;
      const body = {game:"poker",variant:"texas_holdem",round_id:hand.round_id,step:hand.step,move,action_id:randomHex()};
      rememberAction(body); void submitAction(body);
    },
  });
  function renderPoker(hand) {
    if (!id("pokerCards")) return;
    if (isHoldem(hand) || !hand) {
      if (hand) { id("legacyPokerTable").hidden = true; id("holdemTable").hidden = false; }
      const task = holdemTable?.render(hand);
      if (task) { cardAnimations.add(task); task.finally(() => cardAnimations.delete(task)); }
      return;
    }
    id("legacyPokerTable").hidden = false; id("holdemTable").hidden = true;
    if (pokerRound !== hand.round_id) {
      pokerRound = hand.round_id;
      const saved = pending?.request_id === hand.round_id ? pending.poker_holds : [];
      pokerHolds = new Set(Array.isArray(saved) ? saved.filter(n => Number.isInteger(n) && n >= 0 && n < 5) : []);
    }
    if (hand.ended) pokerHolds = new Set(hand.holds);
    const row = id("pokerCards");
    hand.cards.forEach((card, index) => {
      let button = row.children[index];
      if (button?.dataset.card !== String(card) || button?.dataset.round !== hand.round_id) {
        const rank = card % 13+1, suit = Math.floor(card/13);
        const label = ["","A","2","3","4","5","6","7","8","9","10","J","Q","K"][rank];
        const node = document.createElement("button");node.type = "button";
        node.className = "poker-card"+(suit === 1 || suit === 3 ? " is-red" : "");
        node.dataset.pokerHold = String(index);node.dataset.card = String(card);node.dataset.round = hand.round_id;
        node.setAttribute("aria-label",`${label} of ${["spades","hearts","clubs","diamonds"][suit]}; toggle hold`);
        const value = document.createElement("b");value.textContent = label+["♠","♥","♣","♦"][suit];
        node.append(value,document.createElement("small"));
        node.addEventListener("click",() => {
          if (node.disabled || !wallet?.poker || busy || pendingAction) return;
          pokerHolds.has(index) ? pokerHolds.delete(index) : pokerHolds.add(index);
          savePokerHolds();
        });
        button ? button.replaceWith(node) : row.append(node);
        button = node;
        dealCard(node,index*85,Boolean(hand.ended));
      }
      button.setAttribute("aria-pressed",String(pokerHolds.has(index)));
      button.querySelector("small").textContent = pokerHolds.has(index) ? "HELD" : hand.ended ? "DRAWN" : "HOLD";
    });
    const pokerStatus = () => { id("pokerStatus").textContent = hand.ended
      ? `${rules.poker.legacy_labels[hand.category]} · ${hand.multiplier}× returned`
      : `${pokerHolds.size} held · ${5-pokerHolds.size} to draw`; };
    if (cardAnimations.size) { id("pokerStatus").textContent = "Dealing…"; void waitForCards().then(pokerStatus); }
    else pokerStatus();
    if (!hand.ended) {
      id("gameResult").textContent = "Tap to hold. Then draw.";
      id("betProof").textContent = "Hand saved";
    }
    root.querySelectorAll("[data-hand]").forEach(cell => cell.classList.toggle("is-hit",Boolean(hand.ended && cell.dataset.hand === hand.category)));
    controls();
  }
  function savePokerHolds() {
    if (pending) remember({ ...pending, poker_holds: [...pokerHolds].sort((a,b) => a-b) });
    renderPoker(wallet.poker);
  }
  id("pokerHoldAll")?.addEventListener("click", () => { pokerHolds = new Set([0,1,2,3,4]);savePokerHolds(); });
  id("pokerClear")?.addEventListener("click", () => { pokerHolds.clear();savePokerHolds(); });
  id("pokerDraw")?.addEventListener("click", () => {
    if (busy || fatal || !secure || !verifierReady || pendingAction || !wallet?.poker) return;
    const body = { game:"poker",round_id:wallet.poker.round_id,holds:[...pokerHolds].sort((a,b) => a-b),action_id:randomHex() };
    rememberAction(body);
    void submitAction(body);
  });
  root.querySelectorAll("[data-limbo-target]").forEach(button => button.addEventListener("click", () => {
    if (locked()) return;
    id("limboTarget").value = Number(button.dataset.limboTarget).toFixed(2);
    settingsChanged();
  }));
  function renderBlackjack(hand) {
    if (!id("blackjackPlayer")) return;
    if (!hand) return;
    for (const [target, cards] of [
      ["blackjackPlayer", hand.player],
      ["blackjackDealer", hand.dealer],
    ]) {
      const row = id(target);
      // Retain existing card elements during balance polls and later hits.
      cards.forEach((card, index) => {
        const key = String(card),
          old = row.children[index];
        if (
          old?.dataset.card === key &&
          row.dataset.round === String(hand.round_id || hand.nonce)
        )
          return;
        const node = playingCard(card);
        const fresh = row.dataset.round !== String(hand.round_id || hand.nonce);
        const delay = fresh ? (index*2+(target === "blackjackDealer" ? 1 : 0))*100 : Math.max(0,index-1)*130;
        const flip = old?.dataset.card === "null";
        old ? old.replaceWith(node) : row.append(node);
        dealCard(node,delay,flip);
      });
      while (row.children.length > cards.length) row.lastElementChild.remove();
      row.dataset.round = String(hand.round_id || hand.nonce);
    }
    const totals = () => {
    id("blackjackPlayerTotal").textContent =
      hand.player_total + (hand.player_soft ? " · soft" : "");
    id("blackjackDealerTotal").textContent =
      hand.dealer_total +
      (hand.ended ? (hand.dealer_soft ? " · soft" : "") : " shown");
    id("blackjackStatus").textContent = hand.ended
      ? {
          blackjack: "Blackjack!",
          win: "You win.",
          push: "Push · stake returned",
          lose: "Dealer wins.",
        }[hand.status] || "Hand complete."
      : `${number(hand.wager)} RP in play`;
    };
    if (cardAnimations.size) {
      id("blackjackStatus").textContent = "Dealing…";
      id("blackjackPlayerTotal").textContent = "—";
      id("blackjackDealerTotal").textContent = "—";
      void waitForCards().then(totals);
    } else totals();
  }
  async function submitAction(body) {
    if (busy || fatal || !secure || !verifierReady) return;
    busy = true;
    phase("submitting");
    message();
    controls();
    try {
      const pokerMove = body.game === "poker";
      const result = await api(pokerMove ? "/gaming/api/poker/action" : "/gaming/api/blackjack/action", body);
      if (result.receipt) {
        if (pokerMove && body.variant !== "texas_holdem" && RedFair.canonical(result.receipt.holds) !== RedFair.canonical(body.holds)) {
          fatal = true;
          throw Error("Poker hold verification failed. Your receipt is retained for review.");
        }
        await verifyReceipt(result.receipt, pending || wallet.blackjack?.bet || wallet.poker.bet);
        remember(null);
        rememberAction(null);
        await showReceipt(result.receipt);
        renderWallet(result.wallet);
      } else {
        assertHoldemActions(result.wallet?.poker, pending);
        rememberAction(null);
        phase("playing");
        renderWallet(result.wallet);
        await waitForCards();
      }
    } catch (error) {
      if (error.definitive) {
        rememberAction(null);
        try {
          renderWallet((await api("/gaming/api/state")).wallet);
        } catch {}
      }
      message(
        error.name === "AbortError"
          ? "Move response timed out. Recover your move; it will not be played twice."
          : error.message,
      );
    } finally {
      busy = false;
      if (fatal) { phase('error'); if (id('betProof')) id('betProof').textContent = 'Verification failed'; }
      else if (!root.dataset.animating && playPhase !== 'result') phase(pending && !wallet?.poker && !wallet?.blackjack ? 'recovery' : 'ready', wallet?.poker || wallet?.blackjack ? 'Your turn' : '');
      controls();
    }
  }
  root.querySelectorAll("[data-blackjack]").forEach((button) =>
    button.addEventListener("click", () => {
      const hand = wallet?.blackjack;
      if (
        !hand ||
        busy ||
        fatal ||
        pendingAction ||
        !secure ||
        !verifierReady ||
        wallet.play_blocked
      )
        return;
      const action = button.dataset.blackjack;
      if (action === "double" && !hand.can_double) return;
      const body = {
        round_id: hand.round_id,
        step: hand.step,
        action,
        action_id: randomHex(),
      };
      rememberAction(body);
      void submitAction(body);
    }),
  );

  id("betForm")?.addEventListener("submit", (event) => {
    event.preventDefault();
    if (busy) return;
    const blocked = playBlock();
    if (blocked) {
      message(blocked);
      if (wallet?.needs_profile && !wallet.play_blocked) {
        id("gamingUsername").scrollIntoView({ block: "center" });
        id("gamingUsername").focus({ preventScroll: true });
      }
      return;
    }
    if (pendingAction) {
      void submitAction(pendingAction);
      return;
    }
    if (pending) {
      void (pendingAction ? submitAction(pendingAction) : submit(pending));
      return;
    }
    const options = opt();
    if (game === "keno" && !selections.size)
      return message("Pick at least one Keno number.");
    const client = id("clientSeed").value,
      wager = Number(id("redWager").value);
    if (!/^[A-Za-z0-9 _.\-]{1,64}$/.test(client))
      return message("Use a valid 1–64 character client seed.");
    const invalidWager = wagerProblem();
    if (invalidWager) {
      message(invalidWager);
      id("redWager").focus();
      return;
    }
    const body = {
      rules_version: RedFair.VERSION,
      game,
      request_id: randomHex(),
      season: wallet.season.id,
      nonce: wallet.nonce,
      commitment: wallet.commitment,
      client_seed: client,
      client_salt: randomHex(),
      wager,
      options,
    };
    clearResult();
    payout();
    remember(body);
    void submit(body);
  });
  id("retryBet")?.addEventListener("click", () => {
    if (pending)
      void (pendingAction ? submitAction(pendingAction) : submit(pending));
  });
  id("gamingNameForm").addEventListener("submit", async (event) => {
    event.preventDefault();
    const button = event.currentTarget.querySelector("button");
    button.disabled = true;
    try {
      const value = await api("/gaming/api/profile", {
        username: id("gamingUsername").value,
        public_visibility: Boolean(id('gamingPublicVisibility')?.checked),
      });
      renderWallet(value.wallet);
      if (!value.wallet.needs_profile && id("gamingProfile")?.open) id("gamingProfile").close();
      message();
    } catch (error) {
      message(error.message);
    } finally {
      button.disabled = false;
    }
  });
  function openRecovery() {
    const panel = id("gamingRecovery");
    if (!panel) return;
    if (typeof panel.showModal === "function" && !panel.open) panel.showModal();
    id("gamingRecoveryCode")?.focus();
  }
  function openProfile() {
    const panel = id("gamingProfile");
    if (!panel) return;
    if (typeof panel.showModal === "function" && !panel.open) panel.showModal();
    id("gamingUsername").value = wallet?.name || "";
    id("gamingUsername")?.focus();
  }
  id("openGamingRecovery")?.addEventListener("click", openRecovery);
  id("openGamingRecoveryIdentity")?.addEventListener("click", openRecovery);
  id("openGamingProfile")?.addEventListener("click", openProfile);
  id("editGamingName")?.addEventListener("click", openProfile);
  id("gamingCreateRecovery")?.addEventListener("click", async (event) => {
    const button = event.currentTarget;
    button.disabled = true;
    const status = id("gamingRecoveryMessage");
    try {
      const value = await api("/gaming/api/recovery-code", {});
      renderWallet(value.wallet);
      id("gamingRecoveryCode").value = value.code;
      id("gamingCopyRecovery").hidden = false;
      status.textContent = "New recovery code created. Save it somewhere private; older codes no longer work.";
    } catch (error) {
      status.textContent = error.message;
    } finally {
      button.disabled = Boolean(wallet?.needs_profile);
    }
  });
  id("gamingCopyRecovery")?.addEventListener("click", async () => {
    const code = id("gamingRecoveryCode").value.trim();
    if (!code) return;
    try {
      await navigator.clipboard.writeText(code);
      id("gamingRecoveryMessage").textContent = "Recovery code copied.";
    } catch {
      id("gamingRecoveryCode").select();
      id("gamingRecoveryMessage").textContent = "Copy the selected recovery code.";
    }
  });
  id("gamingRecoverPlayer")?.addEventListener("click", async (event) => {
    const button = event.currentTarget;
    const status = id("gamingRecoveryMessage");
    const code = id("gamingRecoveryCode").value.trim();
    if (!code) { status.textContent = "Paste a recovery code first."; return; }
    button.disabled = true;
    try {
      const value = await api("/gaming/api/recover", { code });
      renderWallet(value.wallet);
      id("gamingRecovery")?.close();
      id("gamingRecoveryCode").value = "";
      id("gamingCopyRecovery").hidden = true;
      message();
      status.textContent = "Player restored on this browser.";
    } catch (error) {
      status.textContent = error.message;
    } finally {
      button.disabled = false;
    }
  });
  root.querySelectorAll("[data-wager-scale]").forEach((button) =>
    button.addEventListener("click", () => {
      if (locked()) return;
      const current = Number(id("redWager").value);
      id("redWager").value = Math.max(
        1,
        Math.min(
          wallet.balance,
          Math.floor(
            (Number.isFinite(current) ? current : 1) *
              Number(button.dataset.wagerScale),
          ),
        ),
      );
      settingsChanged();
    }),
  );
  root.querySelectorAll("[data-keno]").forEach((button) =>
    button.addEventListener("click", () => {
      if (locked()) return;
      const n = Number(button.dataset.keno);
      if (selections.has(n)) selections.delete(n);
      else if (selections.size < 10) selections.add(n);
      else return message("You can pick up to 10 numbers.");
      settingsChanged();
    }),
  );
  id("kenoClear")?.addEventListener("click", () => {
    if (locked()) return;
    selections.clear();
    settingsChanged();
  });
  id("kenoAuto")?.addEventListener("click", () => {
    if (locked()) return;
    try {
      const pool = Array.from({ length: 40 }, (_, index) => index + 1);
      for (let index = 0; index < 10; index++) {
        const other = index + randomBelow(pool.length - index);
        [pool[index], pool[other]] = [pool[other], pool[index]];
      }
      // Replace the selection only after all ten picks were generated.
      selections = new Set(pool.slice(0, 10));
      settingsChanged();
    } catch (error) {
      message(error.message);
    }
  });
  root
    .querySelectorAll("#redWager,#diceChance,#diceSide,#plinkoRows,#limboTarget,[name=risk],[name=coinSide],[name=baccaratSide]")
    .forEach((el) => {
      el.addEventListener("input", settingsChanged);
      el.addEventListener("change", settingsChanged);
    });
  function boardChanceChanged() {
    if (locked()) return;
    const threshold = Number(id("diceBoardChance").value);
    const chance =
      id("diceSide").value === "under" ? threshold : 100 - threshold;
    id("diceChance").value = String(
      Math.max(1, Math.min(95, Math.round(chance))),
    );
    settingsChanged();
  }
  id("diceBoardChance")?.addEventListener("input", boardChanceChanged);
  id("diceBoardChance")?.addEventListener("change", boardChanceChanged);
  for (const name of ["diceChance", "diceBoardChance"]) {
    id(name)?.addEventListener(
      "wheel",
      (event) => {
        if (
          locked() ||
          event.currentTarget.disabled ||
          event.ctrlKey ||
          event.metaKey ||
          !event.deltaY
        )
          return;
        event.preventDefault();
        const slider = id("diceChance"),
          previous = slider.value;
        if (event.deltaY < 0) slider.stepUp();
        else slider.stepDown();
        if (slider.value !== previous)
          slider.dispatchEvent(new Event("input", { bubbles: true }));
      },
      { passive: false },
    );
  }
  async function poll() {
    clearTimeout(timer);
    if (document.hidden || polling) return;
    if (busy) {
      timer = setTimeout(poll, 5000);
      return;
    }
    polling = true;
    try {
      const value = await api("/gaming/api/state", null, true);
      if (value && !busy) {
        renderWallet(value.wallet);
        renderCommunity(value.community);
        await recoverSavedRound(value.wallet);
      }
      id("gamingChecked").textContent =
        "Saved · live";
    } catch (error) {
      id("gamingChecked").textContent = "Reconnecting…";
    } finally {
      ((polling = false), (feedback = ""));
      if (!document.hidden) timer = setTimeout(poll, 5000);
    }
  }
  document.addEventListener("visibilitychange", () => {
    clearTimeout(timer);
    if (!document.hidden) poll();
  });
  try {
    const savedFilter = localStorage.getItem("rh.gaming.communityFilter");
    if (savedFilter) communityFilter = savedFilter;
  } catch {}
  try { renderCommunity(JSON.parse(root.dataset.community || '{}')); } catch {}
  renderWallet(JSON.parse(root.dataset.wallet));
  remember(pending);
  payout();
  if (pending && !wallet.blackjack && !wallet.poker)
    message(
      "An earlier wager needs confirmation. Recover its result before placing another.",
    );
  if (!secure) message(secureMessage);
  async function start() {
    // Recover an uncertain wager before resetting points. Its receipt and any
    // active Blackjack hand must survive a browser reload unchanged.
    await recoverSavedRound(wallet);
    const navigation = globalThis.performance?.getEntriesByType?.("navigation")?.[0];
    const reloaded = navigation?.type === "reload" ||
      (!navigation && globalThis.performance?.navigation?.type === 1);
    // Link navigation and automatic wallet polls must not refill the balance.
    if (reloaded && secure && !fatal && !wallet.needs_profile && !wallet.play_blocked) {
      busy = refreshing = true;
      controls();
      try {
        for (let attempt = 0; attempt < 2; attempt++) {
          try {
            const result = await api("/gaming/api/refresh", {
              season: wallet.season.id,
              version: wallet.version,
            });
            renderWallet(result.wallet);
            break;
          } catch (error) {
            // A restart, admin grant or other tab can race this page load.
            // Read the latest wallet and retry once, retaining the server's
            // version check; never blindly overwrite a concurrent wager.
            if (attempt || error.code !== "stale_wallet") throw error;
            renderWallet((await api("/gaming/api/state")).wallet);
          }
        }
        walletEtag = "";
      } catch (error) {
        message(error.name === "AbortError"
          ? "The refresh response timed out. Checking the saved balance; reload to try again."
          : error.message);
      } finally {
        busy = refreshing = false;
        controls();
      }
    }
    poll();
  }
  void start();
})();
```

## `static/history.css`

```css
/* History shares the site's red palette and works without JavaScript. */
.history-picker {
  display: none;
}
.history-picker-row,
.history-step-links {
  display: flex;
  gap: 10px;
  margin-top: 10px;
}
.history-picker-row select {
  flex: 1;
  min-width: 0;
}
.history-step-links {
  justify-content: space-between;
}
.history-step-links [aria-disabled] {
  opacity: 0.45;
  cursor: default;
}
@media (max-width: 700px) {
  .history-page .history-results table {
    min-width: 0;
  }
  .history-page .history-results th {
    white-space: normal;
    font-size: 0.6rem;
    letter-spacing: 0.01em;
    padding: 10px 4px;
  }
  .history-page .history-results td {
    font-size: 0.72rem;
    padding: 12px 4px;
  }
  .history-page .history-weeks {
    display: none;
  }
  .history-page .history-picker {
    display: block;
    margin: 0 0 24px;
  }
}
.history-page {
  padding-top: 52px;
  padding-bottom: 30px;
}
.history-heading,
.history-result-heading,
.history-meta {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 20px;
}
.history-heading {
  margin-bottom: 28px;
}
.history-heading h1 {
  margin: 8px 0 12px;
  font-size: clamp(2.2rem, 5vw, 3.4rem);
  letter-spacing: -0.05em;
}
.history-heading .lead {
  max-width: 600px;
}
.history-heading > a {
  flex-shrink: 0;
}
.history-weeks {
  display: grid;
  grid-template-columns: repeat(4, minmax(0, 1fr));
  gap: 12px;
  margin-bottom: 24px;
}
.history-weeks a {
  display: grid;
  gap: 10px;
  padding: 18px;
  border: 1px solid var(--line);
  background: var(--panel);
  border-radius: var(--radius);
  text-decoration: none;
}
.history-weeks a:hover {
  border-color: var(--accent);
  background: var(--panel-high);
}
.history-weeks a[aria-current] {
  border-color: var(--brand);
  box-shadow: inset 0 3px 0 var(--brand);
  background: #29171c;
}
.history-weeks small {
  color: var(--muted);
}
.site-header a[aria-current] {
  color: var(--accent);
}
.history-results {
  padding: 26px;
}
.history-result-heading h2 {
  margin: 8px 0 0;
}
.history-window {
  margin: 12px 0 24px;
}
.history-results table {
  min-width: 520px;
}
.history-results th {
  white-space: nowrap;
}
.history-results tbody tr:nth-child(-n + 3) .rank {
  color: var(--accent);
}
.history-meta {
  margin: 18px 0 12px;
  color: var(--muted);
  font-size: 0.82rem;
  flex-wrap: wrap;
}
@media (max-width: 850px) {
  .history-weeks {
    grid-template-columns: repeat(2, minmax(0, 1fr));
  }
  .history-heading {
    align-items: flex-start;
    flex-direction: column;
  }
}
@media (max-width: 520px) {
  .history-page {
    padding-top: 30px;
  }
  .history-results {
    padding: 18px 12px;
  }
  .history-weeks a {
    padding: 14px 12px;
  }
  .history-weeks strong {
    font-size: 0.9rem;
  }
  .history-result-heading {
    align-items: flex-start;
    flex-direction: column;
    gap: 10px;
  }
}
```

## `static/history.js`

```javascript
/* Read the shared cache once a minute. Week links also work without scripts. */
(() => {
  "use strict";
  const main = document.querySelector(".history-page");
  if (!main) return;
  const id = (name) => document.getElementById(name);
  const text = (name, value) => {
    id(name).textContent = value;
  };
  const labels = {
    ready: "Provider confirmed",
    partial: "Partial results",
    delayed: "Update delayed",
    loading: "Loading results",
  };
  let selected = main.dataset.selectedWeek,
    timer,
    busy = false;
  let renderedRows = "";

  function apply(value) {
    const week = value.selected;
    if (
      value.release !== document.body.dataset.release ||
      !week ||
      !Array.isArray(week.rows) ||
      week.rows.length > 25 ||
      value.weeks?.length !== 4
    )
      throw new Error("Release mismatch or incomplete history response");
    // Only rebuild week links at the weekly rollover, preserving keyboard focus.
    const navigation = id("historyWeeks");
    const existing = [...navigation.querySelectorAll("[data-week]")].map(
      (a) => a.dataset.week,
    );
    if (existing.join() !== value.weeks.map((w) => w.id).join()) {
      const focusWeek = document.activeElement?.dataset.week;
      const links = value.weeks.map((item, index) => {
        const link = document.createElement("a");
        link.href = "/history?week=" + encodeURIComponent(item.id);
        link.dataset.week = item.id;
        for (const [tag, content, className] of [
          [
            "span",
            index ? "WEEK " + (index + 1) : "LATEST COMPLETED",
            "eyebrow",
          ],
          ["strong", item.label, ""],
          ["small", "Tuesday → Tuesday", ""],
        ]) {
          const node = document.createElement(tag);
          node.textContent = content;
          node.className = className;
          link.append(node);
        }
        return link;
      });
      navigation.replaceChildren(...links);
      links
        .find((a) => a.dataset.week === focusWeek)
        ?.focus({ preventScroll: true });
    }
    selected = week.id;
    const select = id("historyWeekSelect");
    const incomingIds = value.weeks.map((w) => w.id).join();
    if ([...select.options].map((o) => o.value).join() !== incomingIds) {
      const draft = select.value;
      select.replaceChildren(
        ...value.weeks.map((w) => new Option(w.label, w.id)),
      );
      select.value = value.weeks.some((w) => w.id === draft) ? draft : selected;
    }
    const position = value.weeks.findIndex((w) => w.id === selected);
    for (const [name, target] of [
      ["historyPrevious", value.weeks[position + 1]],
      ["historyNext", value.weeks[position - 1]],
    ]) {
      const link = id(name);
      if (target) {
        link.href = "/history?week=" + encodeURIComponent(target.id);
        link.removeAttribute("aria-disabled");
      } else {
        link.removeAttribute("href");
        link.setAttribute("aria-disabled", "true");
      }
    }
    for (const link of navigation.querySelectorAll("a")) {
      if (link.dataset.week === selected)
        link.setAttribute("aria-current", "page");
      else link.removeAttribute("aria-current");
    }
    text("historyTitle", week.label);
    text("historyWindow", week.start_et + " → " + week.end_et);
    text("historyStatus", week.origin === "snapshot" ? "Saved standings" : labels[week.status] || "Loading results");
    text("historyMessage", week.message || "");
    id("historyMessage").hidden = !week.message;
    text(
      "historyCount",
      week.count === null
        ? "Waiting for the first result"
        : week.count +
            (week.origin === "snapshot"
              ? " saved places · final top 25 awaiting confirmation"
              : " qualifying players · showing up to 25"),
    );
    text("historyChecked", "Last checked: " + week.updated_et);
    text(
      "historyPrizeNote",
      week.prizes_known
        ? "Prizes use this week’s saved race settings; only the top 15 places are paid."
        : "No matching prize schedule was saved for this week. Prizes are shown as —.",
    );
    const encoded = JSON.stringify([week.id, week.rows, week.status]);
    if (encoded !== renderedRows) {
      const rows = week.rows.map((row) => {
        const tr = document.createElement("tr");
        [
          String(row.rank).padStart(2, "0"),
          row.username,
          row.wager,
          row.prize,
        ].forEach((content, index) => {
          const td = document.createElement("td");
          td.className = ["rank", "", "number", "number accent"][index];
          td.textContent = content;
          tr.append(td);
        });
        return tr;
      });
      if (!rows.length) {
        const tr = document.createElement("tr"),
          td = document.createElement("td");
        td.colSpan = 4;
        td.className = "empty";
        td.textContent =
          week.status === "ready"
            ? "No qualifying wagers returned for this week."
            : "Results are not available yet. This page checks automatically.";
        tr.append(td);
        rows.push(tr);
      }
      id("historyRows").replaceChildren(...rows);
      renderedRows = encoded;
    }
  }

  async function poll() {
    clearTimeout(timer);
    if (document.hidden || busy) return;
    busy = true;
    const controller = new AbortController();
    const timeout = setTimeout(() => controller.abort(), 12000);
    try {
      const response = await fetch(
        "/history-state?week=" + encodeURIComponent(selected),
        {
          credentials: "same-origin",
          cache: "no-store",
          signal: controller.signal,
        },
      );
      if (
        !response.ok ||
        !response.headers.get("content-type")?.includes("application/json")
      )
        throw new Error("History unavailable");
      apply(await response.json());
      id("historyNetwork").hidden = true;
    } catch {
      text(
        "historyNetwork",
        "Could not check for updates. Saved results remain visible; retrying in 60 seconds. Reload if you recently installed an update.",
      );
      id("historyNetwork").hidden = false;
    } finally {
      clearTimeout(timeout);
      busy = false;
      if (!document.hidden) timer = setTimeout(poll, 60000);
    }
  }
  document.addEventListener("visibilitychange", () => {
    clearTimeout(timer);
    if (!document.hidden) poll();
  });
  poll();
})();
```

## `static/holdem-fairness.js`

```javascript
/* Independent redpoints-v5 Hold'em replay. No network or wallet access.
   redbot-v1 receives only its own cards and the public betting observation.
   Keep this policy/version immutable so old receipts remain independently checkable. */
(() => {
  "use strict";
  const VARIANT = "texas_holdem", POLICY = "redbot-v1";
  const labels = ["High card", "One pair", "Two pair", "Three of a kind", "Straight", "Flush", "Full house", "Four of a kind", "Straight flush"];
  const streets = ["preflop", "flop", "turn", "river"], seats = ["player", "computer"];
  const copy = value => JSON.parse(JSON.stringify(value));
  function compare(a, b) {
    for (let i = 0; i < Math.min(a.length, b.length); i++) if (a[i] !== b[i]) return a[i] > b[i] ? 1 : -1;
    return a.length - b.length;
  }
  function rankFive(cards) {
    const ranks = cards.map(c => c % 13 === 0 ? 14 : c % 13 + 1).sort((a,b) => b-a);
    const counts = new Map(); for (const rank of ranks) counts.set(rank, (counts.get(rank)||0)+1);
    const groups = [...counts].map(([rank,count]) => [count,rank]).sort((a,b) => compare(b,a));
    const unique = [...counts.keys()].sort((a,b) => a-b);
    const straight = String(unique) === "2,3,4,5,14" ? 5 : unique.length === 5 && unique[4]-unique[0] === 4 ? unique[4] : 0;
    const flush = new Set(cards.map(c => Math.floor(c/13))).size === 1;
    if (straight && flush) return [8,straight];
    if (groups[0][0] === 4) return [7,groups[0][1],groups[1][1]];
    if (String(groups.map(g=>g[0])) === "3,2") return [6,groups[0][1],groups[1][1]];
    if (flush) return [5,...ranks];
    if (straight) return [4,straight];
    const singles = groups.filter(g=>g[0]===1).map(g=>g[1]).sort((a,b)=>b-a);
    if (groups[0][0] === 3) return [3,groups[0][1],...singles];
    const pairs = groups.filter(g=>g[0]===2).map(g=>g[1]).sort((a,b)=>b-a);
    if (pairs.length === 2) return [2,...pairs,...singles];
    if (pairs.length) return [1,pairs[0],...singles];
    return [0,...ranks];
  }
  function bestHand(cards) {
    if (!Array.isArray(cards) || cards.length < 5 || cards.length > 7 || new Set(cards).size !== cards.length || cards.some(c=>!Number.isInteger(c)||c<0||c>=52)) throw Error("Invalid Hold'em cards");
    const sorted = [...cards].sort((a,b)=>a-b);
    let best = null, rank = null;
    function combinations(start, chosen) {
      if (chosen.length === 5) {
        const value = rankFive(chosen);
        if (!rank || compare(value, rank) > 0) { best = [...chosen]; rank = value; }
        return;
      }
      for (let i=start; i<=sorted.length-(5-chosen.length); i++) combinations(i+1, [...chosen, sorted[i]]);
    }
    combinations(0, []);
    return {rank, cards:best, label:labels[rank[0]]};
  }
  function validateAction(value) {
    if (!value || Array.isArray(value) || Object.keys(value).sort().join() !== "action,amount" ||
        !["fold","check","call","bet","raise","all_in"].includes(value.action) || !Number.isSafeInteger(value.amount) ||
        value.amount < 0 || value.amount > Math.floor(Number.MAX_SAFE_INTEGER/2) ||
        (!["bet","raise"].includes(value.action) && value.amount !== 0)) throw Error("Invalid Hold'em action");
    return {action:value.action, amount:value.amount};
  }
  function botAction(o) {
    const {hole:cards, board, legal} = o;
    const ranks = cards.map(c=>c%13===0?14:c%13+1).sort((a,b)=>b-a);
    let strength;
    if (!board.length) strength = ranks[0]===ranks[1] ? 65+ranks[0]*2 : ranks[0]*3+ranks[1]+(Math.floor(cards[0]/13)===Math.floor(cards[1]/13)?8:0)+(ranks[0]-ranks[1]===1?5:0);
    else {
      const rank = bestHand([...cards,...board]).rank;
      strength = rank[0]===0 ? rank[1]*2 : rank[0]===1 ? 40+rank[1]*2 : rank[0]===2 ? 75 : rank[0]===3 ? 90 : 110;
    }
    const sum = [...cards,...board].reduce((a,b)=>a+BigInt(b),BigInt(o.pot)+BigInt(o.street_index));
    const bluff = sum % 13n === 0n;
    if (legal.can_raise && o.raises === 0 && (strength>=80 || (bluff && !legal.call))) {
      const target = Math.min(legal.max_raise_to, Math.max(legal.min_raise_to, o.highest+Math.max(o.big_blind,Math.floor(o.pot/2))));
      if (target >= legal.min_raise_to) return {action:o.highest===0?"bet":"raise",amount:target};
    }
    if (legal.check) return {action:"check",amount:0};
    const cheap = BigInt(legal.call)*4n <= BigInt(o.pot), medium = BigInt(legal.call)*2n <= BigInt(o.pot);
    return {action:strength>=90 || (strength>=65 && medium) || (strength>=40 && cheap)?"call":"fold",amount:0};
  }
  class Hand {
    constructor(deck, buyIn, button) {
      if (!Number.isSafeInteger(buyIn) || buyIn<20 || buyIn>Math.floor(Number.MAX_SAFE_INTEGER/2) || !seats.includes(button) || deck.length!==52 || new Set(deck).size!==52) throw Error("Invalid Hold'em table");
      this.buyIn=buyIn; this.button=seats.indexOf(button);
      this.big=Math.max(2,Math.floor(buyIn/50)); this.small=Math.max(1,Math.floor(this.big/2));
      this.holes=[[],[]]; const first=1-this.button;
      for(let i=0;i<4;i++) this.holes[(first+i)%2].push(deck[i]);
      this.boards=[[],deck.slice(5,8),[...deck.slice(5,8),deck[9]],[...deck.slice(5,8),deck[9],deck[11]]];
      this.stacks=[buyIn,buyIn];this.committed=[0,0];this.bets=[0,0];this.acted=[false,false];this.raises=[0,0];
      this.street=0;this.actor=this.button;this.lastRaise=this.big;this.ended=false;this.winner=null;this.reason=null;
      this.refunds=[0,0];this.awards=[0,0];this.hands=[null,null];this.potAtEnd=0;this.events=[];
      this.pay(this.button,this.small);this.pay(1-this.button,this.big);
      this.event("deal",{seat:null,action:"blinds",amount:this.small+this.big});
    }
    pay(seat,amount) {this.stacks[seat]-=amount;this.committed[seat]+=amount;this.bets[seat]+=amount;}
    legal(seat) {
      if(this.ended)return {};
      const high=Math.max(...this.bets),call=Math.min(this.stacks[seat],high-this.bets[seat]),maximum=this.bets[seat]+this.stacks[seat];
      const canRaise=maximum>high && this.stacks[1-seat]>0;
      return {fold:true,check:call===0,call,can_raise:canRaise,min_raise_to:high+this.lastRaise,max_raise_to:maximum,all_in:this.stacks[seat]>0 && (canRaise || this.stacks[seat]<=call)};
    }
    snapshot() {
      return {player:[...this.holes[0]],computer:this.ended && this.reason==="showdown"?[...this.holes[1]]:[null,null],
        board:[...this.boards[this.street]],stacks:[...this.stacks],bets:[...this.bets],pot:this.ended?this.potAtEnd:this.committed[0]+this.committed[1],
        street:streets[this.street],turn:this.ended?null:seats[this.actor],ended:this.ended,winner:this.winner,reason:this.reason};
    }
    event(kind, extra) {this.events.push({kind,...extra,state:this.snapshot()});}
    observation() { const seat=this.actor;return {hole:[...this.holes[seat]],board:[...this.boards[this.street]],legal:this.legal(seat),pot:this.committed[0]+this.committed[1],highest:Math.max(...this.bets),big_blind:this.big,street_index:this.street,raises:this.raises[seat]}; }
    finish(winner=null) {
      const matched=Math.min(...this.committed);
      this.refunds=this.committed.map(v=>v-matched);
      for(let i=0;i<2;i++){this.stacks[i]+=this.refunds[i];this.committed[i]-=this.refunds[i];}
      this.potAtEnd=this.committed[0]+this.committed[1];this.reason=winner!==null?"fold":"showdown";
      if(winner===null){this.hands=this.holes.map(h=>bestHand([...h,...this.boards[3]]));const comparison=compare(this.hands[0].rank,this.hands[1].rank);winner=comparison>0?0:comparison<0?1:-1;}
      this.winner=winner===-1?"split":seats[winner];
      if(winner===-1){this.awards=[Math.floor(this.potAtEnd/2),Math.floor(this.potAtEnd/2)];this.awards[1-this.button]+=this.potAtEnd%2;}
      else this.awards[winner]=this.potAtEnd;
      for(let i=0;i<2;i++)this.stacks[i]+=this.awards[i];
      this.ended=true;this.event("settle",{seat:this.winner,action:this.reason,amount:this.potAtEnd});
      if(this.stacks[0]+this.stacks[1]!==this.buyIn*2 || Math.min(...this.stacks)<0)throw Error("Hold'em chips did not balance");
    }
    advance() {
      if(this.street===3){this.finish();return;}
      this.street++;this.bets=[0,0];this.acted=[false,false];this.raises=[0,0];this.lastRaise=this.big;this.actor=1-this.button;
      this.event("street",{seat:null,action:streets[this.street],amount:0});
      if(this.stacks.includes(0))this.advance();
    }
    move(value) {
      value=validateAction(value);if(this.ended)throw Error("Action after hand ended");
      const seat=this.actor,other=1-seat,legal=this.legal(seat),action=value.action;
      let amount=value.amount,paid;
      if(action==="fold"){this.event("action",{seat:seats[seat],action,amount:0});this.finish(other);return;}
      if(action==="check"){if(!legal.check)throw Error("Cannot check facing a bet");paid=0;}
      else if(action==="call"){if(!legal.call)throw Error("There is no bet to call");paid=legal.call;}
      else {
        const high=Math.max(...this.bets);
        if(action==="all_in"){if(!legal.all_in)throw Error("All-in unavailable");amount=legal.max_raise_to;}
        else if((action==="bet")!==(high===0))throw Error("Wrong bet/raise action");
        if(amount<=high){if(action!=="all_in" || this.stacks[seat]>legal.call)throw Error("A raise must increase the bet");}
        else {
          if(!legal.can_raise || amount>legal.max_raise_to || (amount<legal.min_raise_to && amount!==legal.max_raise_to))throw Error("Invalid raise size");
          const increase=amount-high;if(increase>=this.lastRaise)this.lastRaise=increase;
          this.raises[seat]++;this.acted[other]=false;
        }
        paid=amount-this.bets[seat];
      }
      if(paid<0 || paid>this.stacks[seat])throw Error("Not enough table chips");
      this.pay(seat,paid);this.acted[seat]=true;this.actor=other;
      this.event("action",{seat:seats[seat],action,amount:paid});
      if(this.bets[0]===this.bets[1] && (this.acted.every(Boolean)||this.stacks.includes(0)))this.advance();
      else if(this.stacks[other]===0 && this.bets[seat]>=this.bets[other]){
        while(this.street<3){this.street++;this.event("street",{seat:null,action:streets[this.street],amount:0});}this.finish();
      }
    }
    auto() {while(!this.ended && this.actor===1)this.move(botAction(this.observation()));}
    result(actions) {
      const value={...this.snapshot(),variant:VARIANT,policy:POLICY,initial:[...this.holes[0]],button:seats[this.button],small_blind:this.small,big_blind:this.big,buy_in:this.buyIn,
        legal:this.ended?{}:this.legal(0),actions:copy(actions),events:copy(this.events),total_wager:this.committed[0],returned:this.awards[0],refunds:[...this.refunds],best:copy(this.hands),payout:this.ended?this.stacks[0]:0};
      if(this.ended)value.computer=[...this.holes[1]];
      return value;
    }
  }
  async function replay(pick,buyIn,options,actions,ending) {
    if(!options || options.variant!==VARIANT || Object.keys(options).sort().join()!=="button,variant" || !Array.isArray(actions) || actions.length>4096)throw Error("Invalid Hold'em history");
    const deck=Array.from({length:52},(_,i)=>i);
    for(let i=0;i<51;i++){const j=i+await pick(52-i);[deck[i],deck[j]]=[deck[j],deck[i]];}
    const hand=new Hand(deck,buyIn,options.button),moves=[];hand.auto();
    for(const action of actions){const move=validateAction(action);if(hand.ended||hand.actor!==0)throw Error("Unexpected player action");hand.move(move);moves.push(move);hand.auto();}
    if(ending!==undefined && ending!==null){if(ending!=="weekly_reset"||hand.ended)throw Error("Invalid automatic settlement");hand.move({action:"fold",amount:0});}
    return hand.result(moves);
  }
  globalThis.RedHoldemFair={VARIANT,POLICY,labels,rankFive,bestHand,validateAction,botAction,Hand,replay};
  if(typeof module!=="undefined")module.exports=globalThis.RedHoldemFair;
})();
```

## `static/holdem-ui.js`

```javascript
/* Present only saved server events. Animation never decides cards, chips or wins. */
(() => {
  "use strict";
  function create(root, hooks) {
    const id = name => root.querySelector("#"+name), table=id("holdemTable");
    if (!table) return null;
    const fmt=hooks.number, reduced=()=>document.hidden || matchMedia("(prefers-reduced-motion: reduce)").matches;
    let hand=null, round="", seen=0, initial=true, moving=false, externalLock=true, queue=Promise.resolve();
    function status(text){id("holdemStatus").textContent=text;}
    const name=seat=>seat==="player"?"You":"RedBot";
    function describe(event) {
      if(event.kind==="deal")return "Blinds posted. Cards dealt.";
      if(event.kind==="street")return event.action[0].toUpperCase()+event.action.slice(1)+" dealt.";
      if(event.kind==="settle")return event.seat==="split"?"Split pot.":`${name(event.seat)} won ${fmt(event.amount)}.`;
      const action={fold:"folded",check:"checked",call:"called",bet:"bet",raise:"raised",all_in:"went all-in"}[event.action];
      return `${name(event.seat)} ${action}${event.amount?" · "+fmt(event.amount):""}.`;
    }
    async function cards(target, values, count, animate, offset=0, spacing=85) {
      const jobs=[];
      for(let i=0;i<count;i++){
        const value=i<values.length?values[i]:undefined, key=value===undefined?"slot":String(value), old=target.children[i];
        if(old?.dataset.card===key)continue;
        const node=value===undefined?Object.assign(document.createElement("span"),{className:"holdem-card-slot"}):hooks.playingCard(value);
        node.dataset.card=key;
        if(old)old.replaceWith(node);else target.append(node);
        if(animate && value!==undefined){
          const flip=old?.dataset.card==="null" && value!==null;
          jobs.push((async()=>{
            await hooks.tween(offset+i*spacing,()=>{});
            await hooks.animateElement(node,flip?[{transform:"rotateY(90deg)",opacity:.3},{transform:"rotateY(0)",opacity:1}]:[{transform:"translateY(-14px) scale(.94)",opacity:0},{transform:"translateY(0) scale(1)",opacity:1}],240);
          })());
        }
      }
      await Promise.all(jobs);
    }
    async function paint(state, animate, event=null) {
      id("holdemComputerStack").textContent=fmt(state.stacks[1])+" RP";
      id("holdemPlayerStack").textContent=fmt(state.stacks[0])+" RP";
      id("holdemPot").textContent=fmt(state.pot);
      id("holdemComputerBet").textContent=state.ended?" ":state.bets[1]?fmt(state.bets[1])+" in this round":" ";
      id("holdemPlayerBet").textContent=state.ended?" ":state.bets[0]?fmt(state.bets[0])+" in this round":" ";
      id("holdemStreet").textContent=state.ended?state.reason==="showdown"?"Showdown":"Hand complete":state.street;
      const dealing=event?.kind==="deal";
      // Opening deal follows the two alternating seats; later streets reveal in order.
      await Promise.all([
        cards(id("holdemComputerCards"),state.computer,2,animate,dealing && hand.button==="computer"?85:0,dealing?170:85),
        cards(id("holdemPlayerCards"),state.player,2,animate,dealing && hand.button==="player"?85:0,dealing?170:85),
        cards(id("holdemBoard"),state.board,5,animate),
      ]);
      if(animate && event?.amount && ["action","settle"].includes(event.kind)){
        const direction=event.seat==="player"?1:-1;
        await hooks.animateElement(id("holdemChip"),[{transform:`translateY(${direction*24}px) scale(.8)`,opacity:.2},{transform:"translateY(0) scale(1)",opacity:1}],200);
      }
    }
    function cost() {
      if(!hand?.legal)return;
      const value=Number(id("holdemRaise").value),valid=Number.isSafeInteger(value) && value>=hand.legal.min_raise_to && value<=hand.legal.max_raise_to;
      id("holdemRaiseCost").textContent=valid?`${fmt(value-hand.bets[0])} more`:"Choose a legal raise.";
      id("holdemRaiseButton").disabled=externalLock||moving||!valid||!hand.legal.can_raise;
    }
    function controls(locked=externalLock) {
      externalLock=locked;
      const active=hand && !hand.ended;
      id("holdemControls").hidden=!active;
      if(!active)return;
      const legal=hand.legal;
      root.querySelectorAll("[data-holdem]").forEach(button=>{
        const action=button.dataset.holdem;
        button.hidden=action==="check"?!legal.check:action==="call"?!legal.call:action==="fold"?legal.check:!legal.all_in;
        button.disabled=locked||moving;
        if(action==="call")button.textContent=`Call ${fmt(legal.call)}`;
        if(action==="all_in")button.textContent=`All-in ${fmt(hand.stacks[0])}`;
      });
      id("holdemRaiseControls").hidden=!legal.can_raise || legal.max_raise_to<legal.min_raise_to;
      root.querySelectorAll("[data-holdem-size],#holdemRaise").forEach(el=>el.disabled=locked||moving);
      cost();
    }
    function tiebreak(winner) {
      const a=hand.best[winner].rank,b=hand.best[1-winner].rank;
      if(a[0]!==b[0])return "";
      const index=a.findIndex((value,i)=>i>0 && value!==b[i]);
      if(index<0)return "";
      const rank=({14:"A",13:"K",12:"Q",11:"J"})[a[index]]||String(a[index]);
      const primary={0:"high card",1:"higher pair",2:"higher pair",3:"higher trips",4:"higher straight",5:"flush high card",6:"higher trips",7:"higher quads",8:"higher straight flush"};
      const label=index===1?primary[a[0]]:a[0]===2 && index===2?"higher second pair":a[0]===6?"higher pair":"kicker";
      return ` · ${rank} ${label}`;
    }
    function finishView() {
      const legal=hand.legal;
      if(!hand.ended){
        id("holdemRaise").min=legal.min_raise_to;id("holdemRaise").max=legal.max_raise_to;
        id("holdemRaise").value=String(Math.min(legal.min_raise_to,legal.max_raise_to));
        const betting=Math.max(...hand.bets)===0;
        id("holdemRaiseButton").textContent=betting?"Bet":"Raise";
        root.querySelector('label[for="holdemRaise"]').textContent=betting?"Bet · RedPoints":"Raise to · RedPoints";
        status(legal.check?"Your turn · check or bet.":`Your turn · ${fmt(legal.call)} to call.`);
      }else{
        const winner=hand.winner,net=hand.payout-hand.buy_in;
        let text=winner==="split"?"Split pot":winner==="player"?"You win":"RedBot wins";
        if(hand.reason==="fold")text+=winner==="player"?" · opponent folded":" · you folded";
        else if(winner==="split")text+=" · "+hand.best[0].label;
        else {const seat=winner==="player"?0:1;text+=" · "+hand.best[seat].label+tiebreak(seat);}
        status(`${text}. ${net>0?"+":""}${fmt(net)} RP net.`);
        const winning=winner==="split"?[0,1]:[winner==="player"?0:1];
        const highlights=new Set(winning.flatMap(i=>hand.best[i]?.cards||[]));
        table.querySelectorAll(".playing-card[data-card]").forEach(node=>node.classList.toggle("is-winning",highlights.has(Number(node.dataset.card))));
      }
      controls();
    }
    function render(next) {
      if(!next){initial=false;return queue;}
      const newRound=round!==next.round_id;
      if(!newRound && next.events.length<=seen){controls();return queue;}
      const animate=!initial;initial=false;
      const start=newRound?0:seen;seen=next.events.length;round=next.round_id;
      moving=true;controls();
      queue=queue.then(async()=>{
        hand=next;
        if(newRound){
          for(const name of ["holdemPlayerCards","holdemComputerCards","holdemBoard"])id(name).replaceChildren();
          table.querySelectorAll(".is-winning").forEach(n=>n.classList.remove("is-winning"));
        }
        id("holdemBlinds").textContent=`Blinds ${fmt(next.small_blind)} / ${fmt(next.big_blind)}`;
        id("holdemPlayerButton").hidden=next.button!=="player";id("holdemComputerButton").hidden=next.button!=="computer";
        const events=next.events.slice(start);
        if(animate){
          for(const event of events){
            if(event.kind==="action" && event.seat==="computer" && !reduced()){
              status("RedBot is thinking…");await hooks.tween(360,()=>{});
            }
            status(describe(event));await paint(event.state,true,event);
            if(!reduced() && event.kind==="street")await hooks.tween(160,()=>{});
          }
        }else await paint(next.events.at(-1).state,false);
        id("holdemLog").replaceChildren(...next.events.map(event=>Object.assign(document.createElement("li"),{textContent:describe(event)})));
        finishView();
      }).catch(error=>{hooks.error(error.message);}).finally(()=>{moving=false;controls();hooks.changed();});
      return queue;
    }
    root.querySelectorAll("[data-holdem]").forEach(button=>button.addEventListener("click",()=>{
      if(externalLock||moving||!hand||hand.ended)return;
      hooks.move({action:button.dataset.holdem,amount:0});
    }));
    id("holdemRaise").addEventListener("input",cost);
    id("holdemRaiseButton").addEventListener("click",()=>{
      if(externalLock||moving||id("holdemRaiseButton").disabled)return;
      hooks.move({action:Math.max(...hand.bets)===0?"bet":"raise",amount:Number(id("holdemRaise").value)});
    });
    root.querySelectorAll("[data-holdem-size]").forEach(button=>button.addEventListener("click",()=>{
      if(!hand||externalLock||moving)return;
      const high=Math.max(...hand.bets),size=button.dataset.holdemSize;
      const desired=size==="min"?hand.legal.min_raise_to:high+Math.max(hand.big_blind,Math.floor((hand.pot+hand.legal.call)/(size==="half"?2:1)));
      id("holdemRaise").value=String(Math.max(hand.legal.min_raise_to,Math.min(hand.legal.max_raise_to,desired)));cost();
    }));
    return {render,controls,isMoving:()=>moving};
  }
  globalThis.RedHoldemUI={create};
})();
```

## `static/holdem.css`

```css
/* The existing red theme, sized for a two-seat table without horizontal scrolling. */
.gaming-page[data-game="poker"] .game-layout{grid-template-columns:minmax(180px,240px) minmax(0,1fr)}
.holdem-table{--card-w:clamp(40px,6.5vw,67px);position:relative;background:radial-gradient(ellipse at 50% 46%,#49242b 0,#24161c 60%,#181117 100%);border:1px solid #72404b;border-radius:26px;padding:20px;box-shadow:inset 0 0 0 6px #ffffff03,0 12px 32px #0003;overflow:hidden}
.holdem-topline{display:flex;justify-content:space-between;align-items:center;gap:8px;margin-bottom:14px;flex-wrap:wrap}
.holdem-seat{display:flex;flex-direction:column;align-items:center;gap:9px;position:relative}
.holdem-seat-label{display:flex;align-items:center;justify-content:center;gap:10px;flex-wrap:wrap;font-size:.9rem}
.holdem-seat-label strong small{font-weight:400;font-size:.72rem;color:#d0adb6;margin-left:4px}
.holdem-seat-label output{font-variant-numeric:tabular-nums;color:#fff;font-weight:700}
.dealer-button{display:inline-grid;place-items:center;width:22px;height:22px;border-radius:50%;background:#f2e8e9;color:#511825;font-size:.65rem;font-weight:900;box-shadow:0 2px 5px #0006}
.holdem-hole,.holdem-board{justify-content:center;gap:7px;min-height:calc(var(--card-w)*1.4);flex-wrap:nowrap}
.holdem-table .playing-card,.holdem-card-slot{width:var(--card-w);min-width:0;height:calc(var(--card-w)*1.4);flex:0 0 var(--card-w);border-radius:8px;font-size:clamp(.9rem,2.3vw,1.35rem);padding:7px;box-sizing:border-box}
.holdem-card-slot{border:1px dashed #b177833d;background:#08070a26}
.holdem-table .playing-card.is-hidden{background:repeating-linear-gradient(45deg,#7e273a,#7e273a 4px,#682033 4px,#682033 8px);border:2px solid #df92a064;color:#ffbeca}
.holdem-table .playing-card.is-winning{outline:3px solid #ff536d;outline-offset:2px;box-shadow:0 0 18px #ff385333}
.holdem-center{margin:10px auto 18px;text-align:center}
.holdem-pot{position:relative;display:inline-flex;align-items:baseline;gap:8px;margin:0 0 13px;min-width:100px;justify-content:center}
.holdem-pot small{font-size:.62rem;letter-spacing:.17em;color:#cb9aa6}
.holdem-pot output{font-size:1.4rem;font-weight:800;font-variant-numeric:tabular-nums}
#holdemChip{position:absolute;display:grid;place-items:center;right:-30px;top:2px;border:2px dashed #ff9baa;background:#a72442;color:#fff;width:25px;height:25px;border-radius:50%;font-size:.65rem;font-weight:900}
.holdem-street{display:inline-block;text-transform:uppercase;letter-spacing:.16em;font-size:.62rem;color:#cfa8b3;margin-top:9px}
.holdem-seat-bet{font-size:.72rem;min-height:1.1em;color:#e6b5c0;font-variant-numeric:tabular-nums}
.holdem-status{min-height:2.8em;margin:16px 0 8px;text-align:center;font-size:.9rem;line-height:1.4;color:#f8e1e7;text-wrap:balance}
.holdem-moves{justify-content:center;display:flex;flex-wrap:wrap;gap:7px}
.holdem-moves .button{min-height:42px;flex:1 1 84px;padding:10px 12px}
.holdem-raise{margin:14px auto 0;max-width:420px;display:grid;gap:8px}
.holdem-raise label{font-size:.75rem;color:#d7b5be}
.holdem-raise-input{display:flex;gap:8px;min-width:0}
.holdem-raise-input input{min-width:0;width:100%;font-variant-numeric:tabular-nums}
.holdem-raise .button-row{display:flex;gap:6px;align-items:center;flex-wrap:wrap}
#holdemRaiseCost{font-size:.72rem;margin-left:auto}
.holdem-log{margin-top:16px;border-top:1px solid #ffffff12;padding-top:10px;font-size:.75rem}
.holdem-log summary{color:#c3a3ad;cursor:pointer}
.holdem-log ol{padding-left:20px;max-height:190px;overflow-y:auto;line-height:1.7;margin-bottom:0}
.holdem-rules{font-size:.87rem;line-height:1.65;max-width:72ch}
.holdem-rules ul{padding-left:22px}
.holdem-legacy{margin-bottom:12px}
.holdem-table [hidden]{display:none!important}
@media(max-width:760px){.gaming-page[data-game="poker"] .game-layout{grid-template-columns:1fr}.gaming-page[data-game="poker"] .bet-controls{padding:15px}.holdem-table{padding:14px 10px;--card-w:clamp(34px,12vw,60px)}.holdem-table .playing-card{padding:5px}.holdem-hole,.holdem-board{gap:5px}.holdem-topline .eyebrow{font-size:.65rem}.holdem-topline .small{font-size:.65rem}.holdem-seat-label{font-size:.8rem}.holdem-moves .button{font-size:.78rem;flex-basis:65px}.holdem-table{border-radius:18px}}
@media(prefers-reduced-motion:reduce){.holdem-table *{animation:none!important;transition:none!important}}
```

## `static/plinko.js`

```javascript
/* Receipt-driven canvas renderer, loaded only on the Plinko page. */
(() => {
  "use strict";
  globalThis.RedPlinko = {create({id, multiple}) {
    const canvas = id("plinkoCanvas");
    const width = 720,
      height = 510,
      pegRadius = 3.5,
      ballRadius = 8;
    let board,
      layer,
      ctx,
      key = "",
      balls = [],
      resting = null;
    let frameId = null,
      timeoutId,
      lastHit = -1,
      warned = false;

    function cancelFrames() {
      if (frameId !== null && typeof cancelAnimationFrame === "function")
        cancelAnimationFrame(frameId);
      frameId = null;
      clearTimeout(timeoutId);
    }

    function unavailable(error) {
      cancelFrames();
      for (const ball of balls) ball.done?.();
      balls = [];
      if (!warned) {
        warned = true;
        console.warn(
          "PLINKO Animation unavailable; verified results and balances are still saved.",
          error,
        );
      }
      return false;
    }

    function slot(context, index, active = false) {
      const x = 360 + (index - board.rows / 2) * board.step;
      context.fillStyle = active
        ? "#fff2b6"
        : index < 2 || index > board.rows - 2
          ? "#a91f36"
          : "#672334";
      context.fillRect(x - board.step * 0.47, 438, board.step * 0.94, 38);
      context.fillStyle = active ? "#1b1020" : "#ffffff";
      const label = multiple(board.values[index]);
      let size = board.rows > 12 ? 10 : 12;
      context.font = `600 ${size}px sans-serif`;
      while (size > 6 && context.measureText(label).width > board.step * 0.84)
        context.font = `600 ${--size}px sans-serif`;
      context.textAlign = "center";
      context.fillText(label, x, 461);
    }

    function setBoard(rows, values) {
      if (!canvas) return false;
      try {
        const scale = Math.max(
          1,
          Math.min(
            2,
            ((canvas.getBoundingClientRect().width || width) / width) *
              (globalThis.devicePixelRatio || 1),
          ),
        );
        const nextKey = `${rows}:${values.join(",")}:${scale.toFixed(2)}`;
        if (key === nextKey && board) return true;
        const changed = board && (board.rows !== rows || board.values.join(',') !== values.join(','));
        // Resizing rebuilds only the cached pixels, preserving ball positions.
        // A genuinely different paytable finishes old presentations first.
        if (changed) {
          for (const ball of balls) ball.done?.();
          balls = []; resting = null; lastHit = -1;
          cancelFrames();
        }
        board = {
          rows,
          values,
          step: 620 / (rows + 1),
          top: 64,
          dy: 332 / (rows - 1),
        };
        canvas.width = Math.round(width * scale);
        canvas.height = Math.round(height * scale);
        ctx = canvas.getContext("2d");
        layer = document.createElement("canvas");
        layer.width = canvas.width;
        layer.height = canvas.height;
        const background = layer.getContext("2d");
        if (!ctx || !background) return unavailable("Canvas context missing");
        ctx.setTransform(scale, 0, 0, scale, 0, 0);
        background.setTransform(scale, 0, 0, scale, 0, 0);
        for (let r = 0; r < rows; r++) {
          for (let c = 0; c <= r; c++) {
            background.beginPath();
            background.arc(
              360 + (c - r / 2) * board.step,
              board.top + r * board.dy,
              pegRadius,
              0,
              2 * Math.PI,
            );
            background.fillStyle = "#e9d9de";
            background.fill();
          }
        }
        values.forEach((_, index) => slot(background, index));
        key = nextKey;
        return paint(performance.now());
      } catch (error) {
        key = "";
        return unavailable(error);
      }
    }

    function trajectory(result, now) {
      const points = [
        { x: 360, y: 18 },
        { x: 360, y: board.top - pegRadius - ballRadius },
      ];
      let right = 0;
      result.path.forEach((bit, row) => {
        right += bit;
        points.push({
          x: 360 + (right - (row + 1) / 2) * board.step,
          y:
            row === board.rows - 1
              ? 427
              : board.top + (row + 1) * board.dy - pegRadius - ballRadius,
        });
      });
      return {
        points,
        slot: result.slot,
        began: now,
        duration: 360 + (board.rows - 1) * 105,
      };
    }

    function sample(ball, now) {
      const elapsed = Math.max(0, Math.min(ball.duration, now - ball.began));
      let segment, t;
      if (elapsed < 180) {
        segment = 0;
        t = elapsed / 180;
      } else {
        const middle = (board.rows - 1) * 105;
        if (elapsed < 180 + middle) {
          segment = 1 + Math.floor((elapsed - 180) / 105);
          t = ((elapsed - 180) % 105) / 105;
        } else {
          segment = board.rows;
          t = Math.min(1, (elapsed - 180 - middle) / 180);
        }
      }
      const a = ball.points[segment],
        b = ball.points[segment + 1];
      const dy = b.y - a.y;
      // Contact points sit above each peg, not inside it. Each verified bit
      // sends the ball to the left/right peg using a short parabolic bounce.
      const rise = Math.min(5, dy * 0.2);
      const launch = 2 * rise + 2 * Math.sqrt(rise * (rise + dy));
      return {
        x: a.x + (b.x - a.x) * t,
        y:
          segment === 0
            ? a.y + dy * t * t
            : a.y - launch * t + (dy + launch) * t * t,
      };
    }

    function paint(now) {
      if (!ctx || !layer) return false;
      try {
        ctx.clearRect(0, 0, width, height);
        ctx.drawImage(layer, 0, 0, width, height);
        if (lastHit >= 0) slot(ctx, lastHit, true);
        const positions = balls.map((ball) => sample(ball, now));
        if (resting && !balls.length) positions.push(resting);
        for (const position of positions) {
          ctx.beginPath();
          ctx.arc(position.x, position.y, ballRadius, 0, 2 * Math.PI);
          ctx.fillStyle = "#ff415b";
          ctx.shadowColor = "#ff415b";
          ctx.shadowBlur = 10;
          ctx.fill();
        }
        ctx.shadowBlur = 0;
        return true;
      } catch (error) {
        return unavailable(error);
      }
    }

    function finish() {
      const last = balls[balls.length - 1];
      if (last) {
        resting = last.points[last.points.length - 1];
        lastHit = last.slot;
      }
      for (const ball of balls) ball.done?.();
      balls = [];
      cancelFrames();
      paint(performance.now());
    }

    function frame() {
      frameId = null;
      try {
        // Use one monotonic clock. Older RAF timestamps and slow frames must
        // never rewind a ball or leave an animation waiting indefinitely.
        const now = performance.now();
        balls = balls.filter((ball) => {
          if (now - ball.began < ball.duration) return true;
          resting = ball.points[ball.points.length - 1];
          lastHit = ball.slot;
          ball.done?.();
          return false;
        });
        if (!paint(now)) return;
        if (balls.length && !document.hidden)
          frameId = requestAnimationFrame(frame);
        else finish();
      } catch (error) {
        unavailable(error);
      }
    }

    function drop(rows, values, result, done) {
      try {
        if (!setBoard(rows, values)) { done?.(); return; }
        const now = performance.now();
        balls.push({...trajectory(result, now), done});
        if (
          document.hidden ||
          globalThis.matchMedia?.("(prefers-reduced-motion: reduce)").matches ||
          typeof requestAnimationFrame !== "function"
        ) {
          finish();
          return;
        }
        if (frameId === null) frameId = requestAnimationFrame(frame);
        clearTimeout(timeoutId);
        timeoutId = setTimeout(finish, balls[balls.length - 1].duration + 400);
      } catch (error) {
        unavailable(error);
        done?.();
      }
    }

    if (canvas) {
      document.addEventListener("visibilitychange", () => {
        if (document.hidden) finish();
      });
      window.addEventListener("pagehide", () => finish());
      let resizeId;
      window.addEventListener("resize", () => {
        clearTimeout(resizeId);
        resizeId = setTimeout(() => {
          if (board) setBoard(board.rows, board.values);
        }, 120);
      });
    }
    return { setBoard, drop };
  
  }};
})();
```

## `static/public-control.css`

```css


body:not([data-page="admin"]) .shell {max-width: 1290px; width: min(100%,1290px); margin-inline: auto; padding-inline: clamp(16px,3vw,42px)}
body:not([data-page="admin"]) .panel {border:1px solid var(--public-line); background: var(--public-card); border-radius: var(--public-radius); box-shadow: 0 14px 40px #00000020}
body:not([data-page="admin"]) .button,
body:not([data-page="admin"]) button {border-radius: 10px}
body:not([data-page="admin"]) :is(a,button,input,textarea,select,summary):focus-visible {outline:3px solid var(--public-ring);outline-offset:3px}
body:not([data-page="admin"]) :is(.table-scroll) {overscroll-behavior-x: contain; scrollbar-color: #665361 transparent; scrollbar-width: thin}
body:not([data-page="admin"]) .small, body:not([data-page="admin"]) .muted {color: var(--public-soft)}
body:not([data-page="admin"]) .eyebrow {color: #e9a0ac;letter-spacing: .13em;font-size:.69rem}
body:not([data-page="admin"]) .section-title {align-items:end;gap:18px;margin-bottom:18px}
body:not([data-page="admin"]) .section-title h2 {font-size:clamp(1.65rem,2.9vw,2.4rem);line-height:1.1;letter-spacing:-.045em}
body:not([data-page="admin"]) .section-title h3 {letter-spacing:-.03em}
body:not([data-page="admin"]) .tag {border-radius: 20px}
/* Header: four first-class destinations. Community links live in one deliberate menu. */
body:not([data-page="admin"]) .public-site-header {position:sticky;top:0;z-index:45;background:#16131bef;backdrop-filter:blur(16px);border-bottom:1px solid #44313a;box-shadow:0 9px 25px #07050b30}
body:not([data-page="admin"]) .site-header .public-header-inner {display:flex;flex-wrap:nowrap;align-items:center;justify-content:space-between;gap:20px;min-height:72px;padding-block:10px}
body:not([data-page="admin"]) .public-brand {display:flex;align-items:center;gap:10px;flex:0 0 auto;text-decoration:none;min-width:unset}
body:not([data-page="admin"]) .public-brand img {width:38px;height:38px;border-radius:9px;object-fit:contain}
body:not([data-page="admin"]) .public-brand > span {display:flex;flex-direction:column;gap:1px;line-height:1.1}
body:not([data-page="admin"]) .public-brand strong {font-size:.96rem;letter-spacing:-.03em;max-width:190px;text-overflow:ellipsis;overflow:hidden;white-space:nowrap}
body:not([data-page="admin"]) .brand-sub {font-size:.58rem;color:#b7a6b4;font-weight:700;letter-spacing:.18em}
body:not([data-page="admin"]) .site-header .public-navigation {display:flex;flex:1;justify-content:flex-end;align-items:center;min-width:0;gap:clamp(10px,2vw,25px);margin:0}
body:not([data-page="admin"]) .public-nav-links, body:not([data-page="admin"]) .public-nav-right {display:flex;align-items:center;gap:clamp(2px,.4vw,10px)}
body:not([data-page="admin"]) .site-header .public-nav-links a {padding:10px 12px;min-height:42px;display:inline-flex;align-items:center;justify-content:center;border-radius:10px;color:#cbc1cd;font-weight:650;white-space:nowrap;font-size:.86rem;border:1px solid transparent;text-decoration:none}
body:not([data-page="admin"]) .site-header .public-nav-links a:is(:hover,:focus-visible),body:not([data-page="admin"]) .site-header .public-nav-links a[aria-current="page"] {background:#3c242e;color:#fff;border-color:#7f4655}
body:not([data-page="admin"]) .site-header .public-nav-links a[aria-current="page"] {border-bottom:1px solid #b85868}
body:not([data-page="admin"]) .public-more {position:relative;margin:0}
body:not([data-page="admin"]) .public-more summary {padding:10px 9px;min-height:42px;display:flex;align-items:center;gap:8px;color:#cfc5d2;cursor:pointer;font-size:.84rem;list-style:none;border-radius:9px;font-weight:650}
body:not([data-page="admin"]) .public-more summary::-webkit-details-marker {display:none}
body:not([data-page="admin"]) .public-more summary:hover {background:#302631}
body:not([data-page="admin"]) .public-more-panel {position:absolute;right:0;top:calc(100% + 10px);display:grid;gap:5px;width:205px;background:#231d29;border:1px solid #574453;padding:8px;border-radius:12px;box-shadow:0 18px 45px #0009;z-index:48}
body:not([data-page="admin"]) .public-more-panel a {padding:11px;border-radius:8px;display:block;font-size:.86rem;color:#f1eaf0;font-weight:600}
body:not([data-page="admin"]) .public-more-panel a:hover {background:#403041}
body:not([data-page="admin"]) .public-nav-right .public-watch {padding:11px 16px;border:1px solid #a93d52;background:#bc2d45;color:white;font-size:.82rem;font-weight:750;white-space:nowrap;line-height:1.35}
body:not([data-page="admin"]) .public-watch:hover {background:#a22139}
body:not([data-page="admin"]) .public-mobile-toggle {display:none}

body:not([data-page="admin"]) .public-hero {padding-block:clamp(30px,4vw,60px) 26px;display:grid;grid-template-columns:minmax(0,1.25fr) minmax(290px,.75fr);column-gap:clamp(22px,4vw,65px);row-gap:16px;align-items:center}
body:not([data-page="admin"]) .public-hero .hero-intro {min-width:0;padding-block:8px}
body:not([data-page="admin"]) .public-hero h1 {font-size:clamp(2.5rem,5.3vw,4.45rem);letter-spacing:-.065em;line-height:1.05;margin:12px 0 17px;max-width:720px;text-wrap:balance}
body:not([data-page="admin"]) .public-hero .lead {font-size:clamp(.98rem,1.4vw,1.12rem);line-height:1.7;max-width:630px;color:#c7bac6;margin-bottom:20px}
body:not([data-page="admin"]) .public-hero .hero-links {display:flex;flex-wrap:wrap;gap:9px;align-items:center}
body:not([data-page="admin"]) .public-hero .sponsor {border-radius:12px;background:#24202a;border:1px solid #50404a;padding:9px 12px;box-shadow:none}
body:not([data-page="admin"]) .public-hero .sponsor:hover {background:#312633;border-color:#ac5968}
body:not([data-page="admin"]) .public-hero .race-clock {width:100%;max-width:none;border-radius:17px;padding:clamp(21px,2.5vw,29px);background:linear-gradient(142deg,#332029,#1b1922 62%);border:1px solid #68414d;box-shadow:0 22px 56px #0000002b}
body:not([data-page="admin"]) .public-hero .clock {font-size:clamp(2rem,4.3vw,3.4rem);font-weight:850;letter-spacing:-.065em;line-height:1.2;margin:13px 0 7px}
body:not([data-page="admin"]) .public-hero .clock-footer {border-top:1px solid #62525c;padding-top:15px;margin-top:17px;display:flex;justify-content:space-between;gap:10px;font-size:.81rem}
body:not([data-page="admin"]) .public-hero #empireRaceClock[hidden],body:not([data-page="admin"]) .public-hero #shuffleRaceClock[hidden] {display:none!important}



body:not([data-page="admin"]) .public-leaderboards {scroll-margin-top:105px;margin-bottom:40px}
body:not([data-page="admin"]) .public-leaderboards > .section-title {margin-bottom:18px}
body:not([data-page="admin"]) .public-board-hint {margin:6px 0 20px;font-size:.8rem;color:#bcb1bd;line-height:1.55}
body:not([data-page="admin"]) .public-provider-tabs {display:inline-flex;align-items:center;padding:5px;gap:5px;background:#221d27;border:1px solid #3c3240;border-radius:13px;margin-bottom:4px}
body:not([data-page="admin"]) .public-provider-tabs .button {min-width:155px;border:0!important;border-radius:9px!important;background:transparent!important;color:#bdb3c0;padding:10px 15px;box-shadow:none!important;font-size:.85rem}
body:not([data-page="admin"]) .public-provider-tabs .button[aria-selected="true"] {background:#512633!important;color:#fff;border:1px solid #b35263!important}
body:not([data-page="admin"]) .source-status {border:1px solid #493944;border-radius:12px;background:#211d27;padding:9px 13px;min-width:185px;font-size:.79rem}
body:not([data-page="admin"]) .source-status small {color:#bfb6c0}
body:not([data-page="admin"]) .public-podium {gap:14px;align-items:stretch;margin-bottom:18px}
body:not([data-page="admin"]) .public-podium .podium-card {border-radius:15px;padding:clamp(16px,2vw,25px);box-shadow:none;border:1px solid #4c3c49;background:#211d26;min-width:0}
body:not([data-page="admin"]) .public-podium .podium-card.place-1 {background:linear-gradient(153deg,#4c2836,#27202d 66%);border-color:#bb6271;box-shadow:0 10px 34px #7a27411a}
body:not([data-page="admin"]) .public-podium .podium-name {overflow-wrap:anywhere;font-size:clamp(1rem,1.65vw,1.36rem);letter-spacing:-.025em}
body:not([data-page="admin"]) .public-podium .podium-top {gap:8px}
body:not([data-page="admin"]) .public-table {overflow:hidden;border-radius:14px}
body:not([data-page="admin"]) .public-table th {font-size:.69rem;letter-spacing:.09em;text-transform:uppercase;background:#25202a;color:#bbb0bd}
body:not([data-page="admin"]) .public-table th,body:not([data-page="admin"]) .public-table td {padding-block:15px}
body:not([data-page="admin"]) .public-table tbody tr:hover {background:#ffffff06}
body:not([data-page="admin"]) .public-table td strong {font-weight:680}
body:not([data-page="admin"]) .leaderboard-foot {color:#bcb1bd;font-size:.76rem;line-height:1.65}
body:not([data-page="admin"]) .explanation {border-radius:13px}
/* Interior templates retain the complete functional DOM and their own CSS. */
body:not([data-page="admin"]) .public-interior-page {padding-top:clamp(25px,3.5vw,48px);padding-bottom:55px}
body:not([data-page="admin"]) .public-interior-intro {display:flex;justify-content:space-between;align-items:center;gap:15px;margin:0 0 25px}
body:not([data-page="admin"]) .public-interior-intro h1 {font-size:clamp(1.85rem,3.8vw,2.7rem);letter-spacing:-.05em;line-height:1.1;margin:6px 0}
body:not([data-page="admin"]) .public-interior-intro p:last-child {color:#bcb1bd;margin:0;font-size:.89rem}
body:not([data-page="admin"]) .public-breadcrumb {display:flex;align-items:center;justify-content:space-between;gap:14px;margin:0 0 16px;font-size:.78rem;color:#b8adba}
body:not([data-page="admin"]) .history-heading h1, body:not([data-page="admin"]) .gaming-heading h1 {letter-spacing:-.05em}
body:not([data-page="admin"]) .history-weeks a,body:not([data-page="admin"]) .game-card {border-radius:14px}
body:not([data-page="admin"]) .history-weeks a:hover,body:not([data-page="admin"]) .game-card:hover {border-color:#c56676}
body:not([data-page="admin"]) .game-cards {gap:15px}
body:not([data-page="admin"]) .game-card h2 {letter-spacing:-.035em}
body:not([data-page="admin"]) .points-wallet {border-color:#61414f;background:linear-gradient(130deg,#31212d,#201b26)}
body:not([data-page="admin"]) .game-nav {padding:6px 0 12px;gap:7px}
body:not([data-page="admin"]) .game-nav a[aria-current="page"] {border-color:#b95566;background:#4b2635;color:#fff}


body:not([data-page="admin"]) .footer {border-top:1px solid #3b313c;margin-top:42px;padding-top:23px;padding-bottom:26px;color:#b8acb9;font-size:.8rem}
/* Mobile menu uses a real button, not horizontal scroll through seven links. */
@media(max-width:980px) {
  body:not([data-page="admin"]) .site-header .public-header-inner {flex-wrap:wrap;min-height:65px}
  body:not([data-page="admin"]) .public-mobile-toggle {display:inline-flex;align-items:center;gap:8px;margin-left:auto;background:#28222c;border:1px solid #5b434d;border-radius:10px;color:#f9f4f7;font-size:.8rem;font-weight:700;padding:9px 13px;min-height:42px}
  body:not([data-page="admin"]) .site-header .public-navigation {display:none;order:3;flex:0 0 100%;width:100%;gap:10px;align-items:stretch;justify-content:stretch;background:#1c1822;border:1px solid #4c3a46;padding:12px;border-radius:13px;margin-bottom:5px}
  body:not([data-page="admin"]) .site-header .public-navigation[data-open="true"] {display:flex;flex-direction:column}
  body:not([data-page="admin"]) .public-nav-links {display:grid;grid-template-columns:repeat(2,minmax(0,1fr));gap:5px}
  body:not([data-page="admin"]) .site-header .public-nav-links a {justify-content:flex-start}
  body:not([data-page="admin"]) .public-nav-right {display:grid;grid-template-columns:1fr 1fr;gap:9px}
  body:not([data-page="admin"]) .public-more-panel {position:absolute;left:0;right:auto;z-index:49}
  body:not([data-page="admin"]) .public-nav-right .public-watch {text-align:center;display:inline-flex;align-items:center;justify-content:center}
  body:not([data-page="admin"]) .public-hero {grid-template-columns:minmax(0,1.05fr) minmax(270px,.95fr)}
}
@media(max-width:760px) {
  body:not([data-page="admin"]) .public-hero {grid-template-columns:1fr;gap:22px;padding-top:28px}
  body:not([data-page="admin"]) .public-hero h1 {font-size:clamp(2.3rem,8vw,3.5rem)}

  body:not([data-page="admin"]) .public-leaderboards > .section-title {align-items:flex-start;flex-direction:column}
  body:not([data-page="admin"]) .source-status {width:100%}
  body:not([data-page="admin"]) .public-podium {display:grid;grid-template-columns:1fr;gap:10px}
  body:not([data-page="admin"]) .public-podium .podium-card {width:100%;min-height:unset;order:unset;transform:none}
  body:not([data-page="admin"]) .public-podium .podium-card.place-1 {order:-1}
  body:not([data-page="admin"]) .public-interior-intro {align-items:flex-start;flex-direction:column}
}
@media(max-width:520px) {
  body:not([data-page="admin"]) .public-provider-tabs {display:flex;width:100%}
  body:not([data-page="admin"]) .public-provider-tabs .button {min-width:0;flex:1;font-size:.77rem;padding:11px 8px}
  body:not([data-page="admin"]) .public-hero .clock-footer {flex-wrap:wrap}
  body:not([data-page="admin"]) .public-table table {min-width:510px}
  body:not([data-page="admin"]) .public-brand strong {max-width:150px}
  body:not([data-page="admin"]) .footer {display:flex;flex-wrap:wrap;gap:12px}
}
@media(prefers-reduced-motion:reduce) {
  body:not([data-page="admin"]) *,body:not([data-page="admin"]) *::before,body:not([data-page="admin"]) *::after {scroll-behavior:auto!important;animation-duration:.01ms!important;transition-duration:.01ms!important}
}
/* No-script mobile fallback: ordinary links remain visible without JS. */
@media(max-width:980px) {
  html:not(.js) body:not([data-page="admin"]) .site-header .public-navigation {display:flex;flex-direction:column}
  html:not(.js) body:not([data-page="admin"]) .public-mobile-toggle {display:none}
}

/* V12 removes duplicate promotional blocks and lets the live standings lead. */
.public-games-cta{display:flex;align-items:center;justify-content:space-between;gap:20px;margin:34px 0;padding:22px 24px}.public-games-cta h2{margin:.25rem 0}.public-games-cta p{margin:0}.public-games-cta .button{flex:0 0 auto}
@media(max-width:680px){.public-games-cta{align-items:flex-start;flex-direction:column}.public-games-cta .button{width:100%}}
```

## `static/public-control.js`

```javascript
/* Navigation UX only: never touches provider data, games or user accounts. */
(() => {
  'use strict';
  const toggle = document.getElementById('publicMenuToggle');
  const nav = document.getElementById('publicPrimaryNav');
  const more = document.getElementById('publicMore');
  if (!toggle || !nav) return;
  const close = (restoreFocus = false) => {
    nav.dataset.open = 'false';
    toggle.setAttribute('aria-expanded', 'false');
    toggle.setAttribute('aria-label', 'Open site navigation');
    if (more) more.open = false;
    if (restoreFocus) toggle.focus({preventScroll: true});
  };
  const open = () => {
    nav.dataset.open = 'true';
    toggle.setAttribute('aria-expanded', 'true');
    toggle.setAttribute('aria-label', 'Close site navigation');
  };
  toggle.addEventListener('click', () => nav.dataset.open === 'true' ? close() : open());
  nav.addEventListener('click', event => {
    if (event.target.closest('a') && window.matchMedia('(max-width: 980px)').matches) close();
  });
  document.addEventListener('keydown', event => {
    if (event.key === 'Escape') {
      if (nav.dataset.open === 'true') close(true);
      else if (more?.open) more.open = false;
    }
  });
  document.addEventListener('click', event => {
    if (more?.open && !more.contains(event.target)) more.open = false;
  });
  window.matchMedia('(min-width: 981px)').addEventListener('change', event => {
    if (event.matches) close();
  });
})();
```

## `static/receipt-verifier.js`

```javascript
/* This verifier never fetches or posts. The seed is already revealed in a receipt. */
document
  .getElementById("receiptVerifier")
  ?.addEventListener("submit", async (event) => {
    event.preventDefault();
    const output = document.getElementById("verifyResult"),
      button = event.currentTarget.querySelector("button");
    button.disabled = true;
    output.textContent = "Verifying…";
    try {
      if (!crypto.subtle)
        throw Error("Use HTTPS or localhost for Web Crypto verification.");
      const raw = document.getElementById("verifyReceipt").value;
      if (raw.length > 2_000_000)
        throw Error("Verify a smaller receipt export (up to 2 MB). ");
      const parsed = JSON.parse(raw),
        list = Array.isArray(parsed) ? parsed : [parsed];
      const expected = document.getElementById("verifyCommitment").value.trim();
      if (!list.length || list.length > 100 || (expected && list.length !== 1))
        throw Error(
          "Provide 1–100 receipts, or one receipt with a saved commitment.",
        );
      let passed = 0;
      for (const receipt of list)
        if (await RedFair.verify(receipt, expected || undefined)) passed++;
      output.textContent =
        passed === list.length
          ? `Verified ${passed} receipt(s): seed hashes, outcomes and payouts match.${expected ? " The earlier commitment matches too." : " Compare against your earlier saved commitment to check pre-commitment."}`
          : `FAILED: ${list.length - passed} receipt(s) did not verify.`;
    } catch (error) {
      output.textContent = "Could not verify: " + error.message;
    } finally {
      button.disabled = false;
    }
  });
```

## `static/style.css`

```css


:root {
  color-scheme: dark;
  --bg: #110e11;
  --panel: #1a1418;
  --panel-high: #231a20;
  --line: #39282f;
  --text: #faf1f3;
  --muted: #b8a8ae;
  --accent: #ff737b;
  --brand: #ff2d2d;
  --action: #d92236;
  --warning: #f3c77a;
  --radius: 16px;
  --shadow: 0 12px 40px #0002;
  font-family:
    Inter,
    ui-sans-serif,
    system-ui,
    -apple-system,
    BlinkMacSystemFont,
    "Segoe UI",
    sans-serif;
  font-size: 15px;
  line-height: 1.5;
}
* {
  box-sizing: border-box;
}
html {
  scroll-behavior: smooth;
  scroll-padding-top: 95px;
}
body {
  margin: 0;
  background: var(--bg);
  color: var(--text);
}
body:before {
  content: "";
  position: absolute;
  z-index: -1;
  inset: 0 0 auto;
  height: 500px;
  background: radial-gradient(ellipse at 90% -15%, #ff2d2d24, transparent 65%);
  pointer-events: none;
}
a {
  color: inherit;
  text-decoration: none;
}
a:hover {
  color: var(--accent);
}
button,
input,
textarea,
select {
  font: inherit;
}
button,
a,
input,
textarea,
select {
  touch-action: manipulation;
}
button {
  cursor: pointer;
}
button:disabled {
  opacity: 0.55;
  cursor: wait;
}
[hidden] {
  display: none !important;
}
.js-only {
  display: none;
}
.js .js-only {
  display: inline-flex;
}
:focus-visible {
  outline: 3px solid var(--accent);
  outline-offset: 4px;
}
.shell {
  max-width: 1200px;
  margin: auto;
  padding: 0 32px;
}
.accent,
.text-link {
  color: var(--accent);
}
.muted {
  color: var(--muted);
}
.small {
  font-size: 0.82rem;
}
.eyebrow {
  font-size: 0.67rem;
  font-weight: 700;
  letter-spacing: 0.16em;
  color: var(--muted);
  display: flex;
  gap: 9px;
  align-items: center;
}
h1,
h2,
h3,
p {
  margin-top: 0;
}
h1 {
  font-size: clamp(2.1rem, 4vw, 3.65rem);
  letter-spacing: -0.055em;
  line-height: 1.08;
  font-weight: 650;
  margin-bottom: 20px;
}
h2 {
  font-size: 1.65rem;
  line-height: 1.2;
  letter-spacing: -0.035em;
  margin-bottom: 12px;
}
h3 {
  font-size: 1.05rem;
  letter-spacing: -0.015em;
  margin-bottom: 9px;
}
p {
  margin-bottom: 16px;
}
.dot {
  display: inline-block;
  width: 7px;
  height: 7px;
  border-radius: 50%;
  background: var(--accent);
  box-shadow: 0 0 12px #ff2d2d50;
}
.panel {
  border: 1px solid var(--line);
  border-radius: var(--radius);
  background: var(--panel);
  box-shadow: var(--shadow);
}
.row,
.section-title,
.button-row {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 16px;
}
.button-row {
  justify-content: flex-start;
  flex-wrap: wrap;
}
.section-title {
  margin-bottom: 22px;
}
.section-title h2 {
  margin-bottom: 0;
}
.section-title .eyebrow {
  margin-bottom: 7px;
}
.button {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  gap: 13px;
  min-height: 42px;
  padding: 10px 17px;
  border: 1px solid #59313c;
  border-radius: 9px;
  background: #351e27;
  color: var(--text);
  font-weight: 600;
  font-size: 0.84rem;
  white-space: nowrap;
  transition:
    background 0.16s,
    transform 0.16s;
}
.button:hover {
  background: #48232f;
  color: #fff;
}
.button.primary {
  background: var(--action);
  color: #fff;
  border-color: var(--action);
}
.button.primary:hover {
  background: #b8182b;
  border-color: #b8182b;
}
.button.small {
  min-height: 36px;
  padding: 7px 13px;
  font-size: 0.76rem;
}
.button.danger {
  border-color: #745047;
  background: #382521;
  color: #ffb6a3;
}
.text-button,
.copy-button {
  border: 0;
  background: transparent;
  color: var(--muted);
  padding: 7px;
}
.copy-button {
  font-size: 1rem;
  min-width: 34px;
  min-height: 34px;
}
.text-button:hover,
.copy-button:hover {
  color: var(--accent);
}
.text-link {
  font-size: 0.82rem;
  font-weight: 600;
}
.badge,
.tag {
  display: inline-flex;
  align-items: center;
  padding: 5px 10px;
  border: 1px solid #57333e;
  border-radius: 7px;
  font-size: 0.71rem;
  color: #edc1ca;
  background: #331e27;
  white-space: nowrap;
}
.tag {
  font-size: 0.64rem;
  padding: 3px 8px;
  margin-left: 6px;
}
.state-active {
  color: var(--accent);
  border-color: #89434f;
  background: #411d28;
}
.state-ended {
  color: var(--warning);
  background: #312a1f;
  border-color: #665330;
}
.state-upcoming {
  color: #b6c9fb;
  background: #222b40;
  border-color: #404e73;
}
.skip-link {
  position: fixed;
  z-index: 20;
  top: -80px;
  left: 16px;
  padding: 12px;
  background: var(--accent);
  color: #111;
}
.skip-link:focus {
  top: 12px;
}
.site-header {
  border-bottom: 1px solid #40252f;
  background: #160e14ed;
  position: sticky;
  top: 0;
  z-index: 5;
  backdrop-filter: blur(10px);
}
.header-inner {
  min-height: 78px;
  display: flex;
  flex-wrap: wrap;
  justify-content: space-between;
  align-items: center;
  gap: 24px;
}
.brand {
  display: flex;
  gap: 12px;
  align-items: center;
  font-size: 0.92rem;
  font-weight: 800;
  letter-spacing: 0.07em;
}
.brand img {
  border-radius: 8px;
  object-fit: contain;
  background: #11080c;
}
.brand-sub {
  display: block;
  color: var(--muted);
  font-size: 0.48rem;
  font-weight: 600;
  letter-spacing: 0.2em;
  margin-top: 3px;
}
.site-header nav {
  display: flex;
  align-items: center;
  gap: 26px;
  font-size: 0.8rem;
  color: #ead7dc;
}
.site-header form {
  margin: 0;
}
.hero {
  display: grid;
  grid-template-columns: 1.2fr 1fr;
  gap: 52px;
  padding: 52px 0 45px;
  align-items: center;
}
.hero h1 {
  max-width: 580px;
  margin-top: 14px;
}
.lead {
  color: var(--muted);
  font-size: 1rem;
  max-width: 440px;
}
.hero-links {
  display: flex;
  align-items: center;
  gap: 24px;
  margin-top: 26px;
  flex-wrap: wrap;
}
.sponsor {
  display: flex;
  align-items: center;
  gap: 13px;
}
.sponsor small {
  display: block;
  font-size: 0.54rem;
  letter-spacing: 0.13em;
  color: var(--muted);
}
.sponsor strong {
  font-size: 0.9rem;
}
.sponsor-symbol {
  display: grid;
  place-items: center;
  background: #29213d;
  color: #d1baff;
  font-size: 1.2rem;
  font-weight: 900;
  width: 39px;
  height: 39px;
  border-radius: 11px;
}
.race-clock {
  padding: 27px 28px;
  background: linear-gradient(125deg, #311b25, #1a1418);
}
.clock {
  font-size: clamp(1.3rem, 2.4vw, 2.2rem);
  letter-spacing: -0.045em;
  font-weight: 600;
  font-variant-numeric: tabular-nums;
  margin: 28px 0 16px;
  white-space: nowrap;
}
.race-clock p {
  font-size: 0.72rem;
}
.clock-footer {
  border-top: 1px solid var(--line);
  display: flex;
  justify-content: space-between;
  padding-top: 15px;
  gap: 14px;
  font-size: 0.71rem;
  color: var(--muted);
}
.clock-footer strong {
  font-size: 1rem;
  display: inline-block;
  margin-left: 7px;
}
.source-status {
  text-align: right;
  font-size: 0.74rem;
  display: flex;
  flex-direction: column;
  gap: 4px;
}
.source-status small {
  color: var(--muted);
  font-size: 0.66rem;
}
.podium {
  display: grid;
  grid-template-columns: 1fr 1.15fr 1fr;
  align-items: end;
  gap: 16px;
  margin: 35px 0 22px;
}
.podium-card {
  padding: 21px;
  border: 1px solid var(--line);
  border-radius: var(--radius);
  background: linear-gradient(160deg, #291b22, #1a1418);
  min-width: 0;
}
.podium-card.place-1 {
  background: linear-gradient(135deg, #461d2b, #211319);
  border-color: #a34755;
  padding-top: 28px;
  box-shadow: 0 6px 35px #ff2d2d14;
}
.podium-top {
  display: flex;
  align-items: center;
  gap: 12px;
}
.placement {
  font-size: 1.05rem;
  font-weight: 600;
  color: var(--muted);
  font-variant-numeric: tabular-nums;
}
.podium-top .eyebrow {
  font-size: 0.56rem;
  letter-spacing: 0.13em;
  flex: 1;
}
.podium-symbol {
  color: var(--accent);
  font-size: 1.3rem;
}
.podium-name {
  display: block;
  font-size: 1.4rem;
  font-weight: 600;
  letter-spacing: -0.03em;
  margin: 24px 0 27px;
  overflow-wrap: anywhere;
}
.place-1 .podium-name {
  font-size: 1.7rem;
  margin-bottom: 30px;
}
.podium-values {
  display: grid;
  grid-template-columns: 1.5fr 1fr;
  gap: 10px;
}
.podium-values small {
  display: block;
  font-size: 0.51rem;
  letter-spacing: 0.12em;
  color: var(--muted);
  margin-bottom: 7px;
}
.podium-values strong {
  font-size: 1rem;
  font-variant-numeric: tabular-nums;
  overflow-wrap: anywhere;
}
.podium-values > div:last-child {
  text-align: right;
}
.public-table {
  padding: 0 20px;
}
table {
  border-collapse: collapse;
  width: 100%;
  font-size: 0.81rem;
}
th {
  text-align: left;
  font-size: 0.64rem;
  letter-spacing: 0.055em;
  text-transform: uppercase;
  font-weight: 600;
  color: var(--muted);
  padding: 16px 14px;
  border-bottom: 1px solid var(--line);
  white-space: nowrap;
}
td {
  padding: 13px 14px;
  border-bottom: 1px solid #36242c;
}
tbody tr:last-child td {
  border-bottom: 0;
}
tbody tr:hover {
  background: #ffffff03;
}
.number {
  text-align: right;
  font-variant-numeric: tabular-nums;
  white-space: nowrap;
}
.rank {
  color: var(--muted);
  font-variant-numeric: tabular-nums;
  width: 65px;
}
.table-scroll {
  overflow: auto;
  max-width: 100%;
  scrollbar-color: #8c4a5b transparent;
}
.leaderboard-foot {
  display: flex;
  justify-content: space-between;
  gap: 16px;
  color: var(--muted);
  font-size: 0.67rem;
  margin: 15px 0 26px;
}
.explanation {
  padding: 0 22px;
  margin-top: 24px;
}
.explanation summary {
  padding: 18px 0;
  font-size: 0.82rem;
}
.weighting-grid {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 22px;
  border-top: 1px solid var(--line);
  padding-top: 20px;
}
.weighting-grid strong {
  font-size: 0.9rem;
}
.weighting-grid p {
  color: var(--muted);
  font-size: 0.79rem;
  margin: 5px 0 22px;
}
.footer {
  display: flex;
  justify-content: space-between;
  gap: 20px;
  padding-top: 36px;
  padding-bottom: 28px;
  font-size: 0.69rem;
  color: #cfb7c0;
}
.footer span:last-child {
  display: flex;
  gap: 22px;
}
.admin-main {
  padding-top: 35px;
}
.admin-heading {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 24px;
  margin-bottom: 25px;
}
.admin-heading h1 {
  font-size: 2.05rem;
  margin: 9px 0 13px;
}
.admin-heading p {
  font-size: 0.8rem;
  margin: 0;
}
.tabs {
  display: flex;
  align-items: center;
  gap: 8px;
  border-bottom: 1px solid var(--line);
  padding-bottom: 15px;
  margin-bottom: 26px;
}
.tabs a {
  color: var(--muted);
  padding: 9px 17px;
  font-size: 0.83rem;
  border-radius: 8px;
}
.tabs a[aria-current] {
  background: #3c1d29;
  color: var(--accent);
}
.tabs a:hover {
  background: #2c1923;
}
.auto-label {
  margin-left: auto;
  font-size: 0.67rem;
  color: var(--muted);
  display: flex;
  gap: 8px;
  align-items: center;
}
.stat-grid {
  display: grid;
  grid-template-columns: 1.5fr 1fr 1fr;
  gap: 18px;
  margin-bottom: 32px;
}
.stat {
  padding: 24px;
  min-width: 0;
}
.stat-value {
  display: block;
  font-size: 2rem;
  line-height: 1.2;
  letter-spacing: -0.035em;
  margin: 24px 0 12px;
  font-variant-numeric: tabular-nums;
}
.stat #countdown {
  font-size: 1.4rem;
  white-space: nowrap;
}
.stat p {
  font-size: 0.77rem;
  margin-bottom: 12px;
}
.stat small {
  font-size: 0.7rem;
}
.connection-grid {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 18px;
}
.connection {
  display: flex;
  align-items: flex-start;
  gap: 16px;
  padding: 23px;
}
.connection > div:nth-child(2) {
  flex: 1;
  min-width: 0;
}
.connection h3 {
  font-size: 0.93rem;
}
.connection p {
  font-size: 0.8rem;
  margin-bottom: 8px;
  overflow-wrap: anywhere;
}
.connection small {
  font-size: 0.64rem;
}
.connection-icon {
  flex-shrink: 0;
  display: grid;
  place-items: center;
  width: 40px;
  height: 40px;
  border-radius: 10px;
  background: #441f2d;
  color: var(--accent);
  font-size: 1.2rem;
  font-weight: 800;
}
.quick-guide {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 25px;
  padding: 25px;
  margin-top: 24px;
  background: linear-gradient(120deg, #311a25, #1a1418);
}
.quick-guide p {
  font-size: 0.81rem;
  margin: 0;
}
.notice {
  padding: 16px 18px;
  border: 1px solid var(--line);
  border-radius: 10px;
  background: #281b23;
  font-size: 0.83rem;
  margin: 0 0 20px;
  overflow-wrap: anywhere;
}
.notice.warning {
  color: #f4d6a8;
  background: #2a241a;
  border-color: #655237;
}
.notice.success {
  color: #d0efae;
  background: #23301d;
  border-color: #4c683b;
}
.notice p:last-child {
  margin-bottom: 0;
}
.notice strong {
  display: block;
  margin-bottom: 6px;
}
.notice ul {
  padding-left: 20px;
  margin: 6px 0;
}
.ended-notice {
  display: flex;
  justify-content: space-between;
  align-items: center;
  gap: 20px;
}
.ended-notice span {
  color: var(--muted);
  font-size: 0.78rem;
}
.stack {
  display: flex;
  flex-direction: column;
  gap: 20px;
}
.form-panel {
  padding: 25px;
  margin-bottom: 20px;
}
.stack .form-panel {
  margin-bottom: 0;
}
.form-panel h2 {
  font-size: 1.4rem;
}
.form-panel h3 {
  margin-top: 24px;
}
.form-grid {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 18px 22px;
  margin-top: 20px;
}
.field {
  display: flex;
  flex-direction: column;
  gap: 7px;
  min-width: 0;
}
.field label {
  font-size: 0.77rem;
  font-weight: 600;
}
.field small {
  font-size: 0.69rem;
  min-height: 1em;
}
.field-error {
  color: #ffbd9f;
}
input,
textarea,
select {
  width: 100%;
  min-height: 42px;
  background: #160f15;
  color: var(--text);
  border: 1px solid #573240;
  border-radius: 8px;
  padding: 10px 12px;
  font-size: 0.83rem;
}
input:focus,
textarea:focus,
select:focus {
  border-color: var(--accent);
  outline: 1px solid var(--accent);
}
input[type="file"] {
  padding: 7px;
}
input::placeholder {
  color: #ab909c;
}
textarea {
  resize: vertical;
}
input[aria-invalid] {
  border-color: var(--warning);
}
.form-panel > .field {
  margin-top: 20px;
}
.prize-grid {
  display: grid;
  grid-template-columns: repeat(5, 1fr);
  gap: 14px;
}
.prize-grid input {
  font-variant-numeric: tabular-nums;
}
.prize-grid .field small:empty {
  display: none;
}
.save-bar {
  display: flex;
  justify-content: space-between;
  align-items: center;
  gap: 20px;
  padding: 17px 20px;
  background: #301923ef;
  border: 1px solid #89505f;
  border-radius: 12px;
  position: sticky;
  bottom: 15px;
  z-index: 4;
  backdrop-filter: blur(10px);
}
.save-bar strong,
.save-bar span {
  display: block;
}
.save-bar strong {
  font-size: 0.86rem;
  margin-bottom: 3px;
}
.filter-bar {
  display: flex;
  align-items: flex-start;
  gap: 14px;
  margin: 22px 0 14px;
  flex-wrap: wrap;
}
.filter-bar .field {
  flex: 1;
  min-width: 150px;
}
.filter-bar .grow {
  flex: 2;
}
.filter-bar > .button {
  margin-top: 26px;
}
.name-cell {
  display: flex;
  align-items: center;
  gap: 6px;
  overflow-wrap: anywhere;
}
.empty {
  text-align: center;
  padding: 35px;
  color: var(--muted);
}
details summary {
  cursor: pointer;
  list-style: none;
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 18px;
  font-weight: 600;
}
details summary::-webkit-details-marker {
  display: none;
}
summary h2 {
  margin: 0;
}
summary .eyebrow {
  display: block;
  margin-bottom: 7px;
}
details[open] > summary {
  margin-bottom: 18px;
}
.explanation[open] > summary {
  margin-bottom: 0;
}
.expand-icon {
  font-size: 1.4rem;
  color: var(--accent);
}
details[open] > summary .expand-icon {
  transform: rotate(45deg);
}
.details-content > .field {
  margin: 22px 0;
}
.nested {
  border-top: 1px solid var(--line);
  margin-top: 22px;
  padding-top: 18px;
}
.nested summary {
  font-size: 0.83rem;
  color: #dac2cc;
}
.account-row {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 12px 0;
  border-bottom: 1px solid var(--line);
}
.account-row strong {
  font-size: 0.85rem;
}
.diagnostic-grid {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 20px;
  margin: 22px 0;
}
.diagnostic-grid strong,
.diagnostic-grid small {
  display: block;
  overflow-wrap: anywhere;
}
.diagnostic-grid strong {
  font-size: 0.82rem;
  margin-top: 5px;
}
.diagnostic-grid small {
  font-size: 0.68rem;
}
.admin-foot {
  display: flex;
  justify-content: space-between;
  gap: 20px;
  font-size: 0.65rem;
  color: #b396a4;
  margin: 30px 0;
}
.login-wrap {
  min-height: 70vh;
  display: grid;
  place-items: center;
  padding-top: 45px;
  padding-bottom: 45px;
}
.login-panel {
  width: 100%;
  max-width: 450px;
  padding: 38px;
}
.login-panel h1 {
  font-size: 2.35rem;
  margin: 22px 0 14px;
}
.login-panel > .muted {
  font-size: 0.82rem;
}
.login-panel .stack {
  margin: 27px 0;
}
.release {
  font-size: 0.64rem;
  color: #b39aa5;
}
.toast {
  position: fixed;
  bottom: 25px;
  left: 50%;
  transform: translateX(-50%);
  z-index: 20;
  padding: 14px 22px;
  border: 1px solid #8a455c;
  border-radius: 10px;
  background: #3b1c2a;
  box-shadow: var(--shadow);
  max-width: calc(100vw - 30px);
  font-size: 0.83rem;
}
@media (min-width: 1600px) {
  .shell {
    max-width: 1330px;
  }
  .hero {
    padding-top: 64px;
  }
}
@media (max-width: 1000px) {
  .shell {
    padding-left: 24px;
    padding-right: 24px;
  }
  .hero {
    gap: 24px;
    grid-template-columns: 1fr 1fr;
  }
  .race-clock {
    padding: 22px;
  }
  .stat-grid {
    grid-template-columns: 1fr 1fr;
  }
  .stat:first-child {
    grid-column: 1/-1;
  }
  .stat:first-child .stat-value {
    font-size: 2rem;
  }
  .connection-grid {
    grid-template-columns: 1fr;
  }
  .podium {
    gap: 12px;
  }
  .podium-card {
    padding: 16px;
  }
  .podium-values strong {
    font-size: 0.83rem;
  }
  .podium-top .eyebrow {
    font-size: 0.5rem;
  }
  .prize-grid {
    grid-template-columns: repeat(3, 1fr);
  }
  .stat #countdown {
    font-size: 1.8rem;
  }
}
@media (max-width: 700px) {
  html {
    scroll-padding-top: 80px;
  }
  .shell {
    padding-left: 18px;
    padding-right: 18px;
  }
  .header-inner {
    min-height: 68px;
    gap: 12px;
    padding-top: 12px;
    padding-bottom: 12px;
  }
  .brand {
    font-size: 0.75rem;
    gap: 8px;
  }
  .brand img {
    width: 30px;
    height: 30px;
  }
  .brand-sub {
    font-size: 0.4rem;
  }
  .site-header nav {
    gap: 12px;
    font-size: 0.72rem;
    flex: 1 0 100%;
    justify-content: space-between;
    flex-wrap: wrap;
  }
  .site-header nav > a:first-child {
    display: inline-flex;
  }
  .site-header .button {
    padding: 8px 11px;
  }
  .hero {
    grid-template-columns: 1fr;
    gap: 27px;
    padding: 34px 0;
  }
  .hero h1 {
    font-size: 2.7rem;
    max-width: 480px;
    margin-top: 15px;
  }
  .hero-links {
    margin-top: 20px;
  }
  .race-clock {
    padding: 22px;
  }
  .clock {
    font-size: 1.9rem;
    margin: 23px 0 14px;
  }
  .clock-footer strong {
    font-size: 1rem;
  }
  .section-title h2 {
    font-size: 1.5rem;
  }
  .section-title {
    align-items: flex-start;
    gap: 12px;
  }
  .source-status {
    font-size: 0.66rem;
    max-width: 155px;
  }
  .source-status small {
    font-size: 0.59rem;
  }
  .podium {
    grid-template-columns: 1fr 1fr;
    margin-top: 24px;
    gap: 12px;
  }
  .podium .place-1 {
    grid-column: 1/-1;
    grid-row: 1;
    padding: 22px;
  }
  .podium .place-1 .podium-name {
    margin: 14px 0 20px;
    font-size: 1.65rem;
  }
  .place-1 .podium-values strong {
    font-size: 1.3rem;
  }
  .podium .place-2,
  .podium .place-3 {
    padding: 16px;
  }
  .podium-top .eyebrow {
    font-size: 0.49rem;
  }
  .podium-name {
    font-size: 1.1rem;
    margin: 17px 0 20px;
  }
  .podium-values {
    grid-template-columns: 1fr;
    gap: 15px;
  }
  .podium-values > div:last-child {
    text-align: left;
  }
  .place-1 .podium-values {
    grid-template-columns: 1fr 1fr;
  }
  .place-1 .podium-values > div:last-child {
    text-align: right;
  }
  .podium-values strong {
    font-size: 1rem;
  }
  .podium-top {
    gap: 8px;
  }
  .podium-symbol {
    font-size: 1rem;
  }
  .public-table {
    padding: 0 5px;
  }
  th {
    font-size: 0.58rem;
    padding: 14px 9px;
  }
  td {
    font-size: 0.74rem;
    padding: 12px 9px;
  }
  .public-table table {
    min-width: 355px;
  }
  .rank {
    width: 45px;
  }
  .leaderboard-foot {
    flex-direction: column;
    gap: 5px;
    font-size: 0.63rem;
  }
  .weighting-grid {
    grid-template-columns: 1fr;
    gap: 0;
  }
  .weighting-grid p {
    margin-bottom: 16px;
  }
  .footer {
    flex-direction: column;
    gap: 12px;
    padding-top: 26px;
  }
  .footer span:last-child {
    gap: 18px;
  }
  .admin-heading {
    align-items: flex-start;
    gap: 12px;
  }
  .admin-heading h1 {
    font-size: 1.75rem;
  }
  .admin-heading > .button,
  .admin-heading form .button {
    font-size: 0.69rem;
    padding: 9px;
  }
  .admin-heading p {
    font-size: 0.72rem;
  }
  .tabs {
    gap: 2px;
    flex-wrap: wrap;
  }
  .tabs a {
    padding: 9px 13px;
    font-size: 0.76rem;
  }
  .auto-label {
    width: 100%;
    margin: 10px 0 0 13px;
    font-size: 0.65rem;
  }
  .stat-grid {
    gap: 12px;
  }
  .stat {
    padding: 18px;
  }
  .stat-value {
    font-size: 1.7rem;
  }
  .stat:first-child .stat-value {
    font-size: 1.65rem;
  }
  .stat .eyebrow {
    font-size: 0.6rem;
  }
  .stat p {
    font-size: 0.7rem;
  }
  .connection {
    padding: 18px;
    gap: 12px;
  }
  .connection-icon {
    width: 32px;
    height: 32px;
  }
  .quick-guide {
    align-items: flex-start;
    flex-direction: column;
    padding: 20px;
  }
  .form-panel {
    padding: 18px;
  }
  .form-panel .section-title {
    flex-direction: column;
  }
  .form-grid {
    grid-template-columns: 1fr;
    gap: 15px;
  }
  .prize-grid {
    grid-template-columns: repeat(3, minmax(0, 1fr));
    gap: 12px;
  }
  .prize-grid input {
    padding: 9px;
    font-size: 0.78rem;
  }
  .prize-grid label {
    font-size: 0.7rem;
  }
  .save-bar {
    bottom: 8px;
    padding: 14px;
    gap: 12px;
    flex-wrap: wrap;
  }
  .save-bar .button {
    min-height: 40px;
  }
  .save-bar .button-row {
    margin-left: auto;
    gap: 8px;
  }
  .filter-bar .field {
    min-width: 130px;
  }
  .ended-notice {
    align-items: flex-start;
    flex-direction: column;
  }
  .diagnostic-grid {
    grid-template-columns: 1fr 1fr;
    gap: 17px;
  }
  .admin-foot {
    flex-direction: column;
    gap: 5px;
  }
  .login-panel {
    padding: 28px 24px;
  }
  .login-panel h1 {
    font-size: 2.1rem;
  }
}
@media (prefers-reduced-motion: reduce) {
  html {
    scroll-behavior: auto;
  }
  *,
  *:before,
  *:after {
    animation: none !important;
    transition: none !important;
  }
}

/* Provider progress stays visible on every admin tab. */
.refresh-progress {
  padding: 21px 24px;
  margin-bottom: 24px;
  border-top: 2px solid var(--brand);
  background: linear-gradient(120deg, #321821, #1a1418);
}
.progress-heading {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 18px;
  margin-bottom: 15px;
}
.progress-heading p {
  margin-bottom: 5px;
}
.progress-heading .text-link {
  white-space: nowrap;
}
.progress-services {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 24px;
  border-top: 1px solid var(--line);
  padding-top: 15px;
}
.progress-services strong {
  font-size: 0.8rem;
  color: var(--accent);
}
.progress-services p {
  margin: 7px 0 0;
  font-size: 0.78rem;
  overflow-wrap: anywhere;
  color: var(--text);
}
@media (max-width: 700px) {
  .refresh-progress {
    padding: 18px;
  }
  .progress-heading {
    flex-direction: column;
    gap: 10px;
  }
  .progress-services {
    grid-template-columns: 1fr;
    gap: 17px;
  }
}






.site-header .play-nav {
  color: var(--accent);
  font-weight: 650;
}
@media (max-width: 900px) {
  .site-header .community-nav {
    display: none;
  }
}
@media (max-width: 700px) {





  .site-header nav {
    gap: 10px;
  }
  .site-header .button {
    font-size: 0.64rem;
  }
  .site-header .play-nav {
    font-size: 0.69rem;
  }
}

/* Community release: tighter hierarchy and readable, consistent controls. */
:root {
  --muted: #c8b8be;
  font-size: 16px;
  --radius: 14px;
}
.hero {
  padding: 32px 0 27px;
  gap: 30px;
}
.hero h1 {
  font-size: clamp(2rem, 3.6vw, 3.1rem);
  margin-bottom: 13px;
}
.hero-links {
  margin-top: 17px;
  gap: 20px;
}
.hero .lead {
  font-size: 0.92rem;
  margin-bottom: 10px;
}
.race-clock {
  padding: 23px;
}
.clock {
  margin: 18px 0 12px;
}
.source-status small,
.leaderboard-foot,
.podium-values small,
.clock-footer,
.race-clock p {
  font-size: 0.74rem;
}
.podium-top .eyebrow {
  font-size: 0.62rem;
}
.field label {
  font-size: 0.85rem;
}
.field small,
.small {
  font-size: 0.8rem;
}
.button {
  min-height: 44px;
}
.button.small {
  min-height: 40px;
}
.ui-icon {
  vertical-align: middle;
  flex-shrink: 0;
}
.connection-summary > span:first-child {
  display: grid;
  gap: 8px;
}
.connection-summary strong {
  font-size: 0.94rem;
}
.connection-chips {
  display: flex;
  flex-wrap: wrap;
  gap: 9px 20px;
  color: var(--muted);
  font-size: 0.76rem;
  font-weight: 450;
}
.connection-chips .has-error {
  color: var(--warning);
}
.refresh-progress {
  padding: 18px 22px;
  margin-bottom: 23px;
}
.refresh-progress > summary {
  font-size: 0.82rem;
}
.connection-details {
  padding-top: 19px;
  border-top: 1px solid var(--line);
  margin-top: 18px;
}
.connection-details .progress-services {
  border: 0;
  padding-top: 4px;
}
.progress-services form {
  margin: 7px 0 0;
}
.progress-services .text-button {
  padding-left: 0;
  color: var(--accent);
}
.admin-shortcuts {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 18px;
}
.admin-shortcuts > a {
  padding: 24px;
  background: linear-gradient(120deg, #291821, var(--panel));
}
.admin-shortcuts h2 {
  font-size: 1.25rem;
  margin: 16px 0 10px;
}
.admin-shortcuts p {
  color: var(--muted);
  font-size: 0.83rem;
  margin: 0;
}
.change-review {
  padding: 22px;
  margin-bottom: 20px;
}
.change-review h2 {
  font-size: 1.35rem;
}
.change-review table {
  table-layout: fixed;
  min-width: 480px;
}
.change-review th,
.change-review td {
  white-space: normal;
  overflow-wrap: anywhere;
  vertical-align: top;
}
.change-review th:first-child {
  width: 26%;
}
.change-review > p:last-child {
  margin: 14px 0 0;
}
.checkpoint-status {
  padding: 16px 18px;
  border: 1px solid #77414c;
  border-radius: 10px;
  background: #341d27;
  margin: 18px 0;
}
.checkpoint-status p {
  margin: 6px 0;
  font-size: 0.85rem;
}
.checkpoint-status small {
  color: var(--muted);
  font-size: 0.75rem;
}
.recovery-review {
  padding: 18px;
  border: 1px solid var(--line);
  border-radius: 10px;
}
.recovery-review dl {
  display: grid;
  grid-template-columns: 120px minmax(0, 1fr);
  gap: 10px;
  font-size: 0.85rem;
}
.recovery-review dt {
  color: var(--muted);
}
.recovery-review dd {
  margin: 0;
  overflow-wrap: anywhere;
}
.admin-foot {
  font-size: 0.74rem;
}
.site-header nav {
  font-size: 0.83rem;
}
@media (max-width: 700px) {
  .hero {
    padding: 26px 0 22px;
    gap: 20px;
  }
  .hero h1 {
    font-size: 2.2rem;
    margin-top: 10px;
  }
  .hero .lead {
    font-size: 0.91rem;
  }
  .race-clock {
    padding: 20px;
  }
  .clock {
    font-size: 1.65rem;
    margin: 14px 0 10px;
  }
  .clock-footer {
    font-size: 0.73rem;
  }




  .podium-values small {
    font-size: 0.67rem;
  }
  .podium-top .eyebrow {
    font-size: 0.59rem;
  }
  .public-table th {
    font-size: 0.68rem;
  }
  .public-table td {
    font-size: 0.83rem;
  }
  .source-status small {
    font-size: 0.72rem;
  }
  .site-header nav {
    gap: 9px;
  }
  .site-header .button {
    font-size: 0.69rem;
  }
  .site-header .play-nav {
    font-size: 0.74rem;
  }
  .brand {
    font-size: 0.75rem;
    letter-spacing: 0.01em;
  }
  .brand-sub {
    font-size: 0.43rem;
  }
  .admin-shortcuts {
    grid-template-columns: 1fr;
  }
  .refresh-progress {
    padding: 17px;
  }
  .connection-chips {
    gap: 7px 14px;
    font-size: 0.73rem;
  }
  .connection-summary {
    align-items: flex-start;
  }
  .connection-summary > span:last-child {
    font-size: 0.69rem;
  }
  .recovery-review dl {
    grid-template-columns: 1fr;
    gap: 5px;
  }
  .recovery-review dd {
    margin-bottom: 10px;
  }
  .change-review {
    padding: 18px;
  }
  .tabs a {
    font-size: 0.78rem;
  }
  .tabs {
    gap: 4px;
  }
}
/* Community GUI: compact summaries, one red action palette, quiet surfaces. */
:root {
  --bg: #101013;
  --panel: #19191f;
  --panel-high: #222129;
  --line: #363039;
  --muted: #c1b9c2;
  --accent: #ff858a;
  --action: #ce263b;
}
.site-header {
  background: #131217f5;
}
.site-header nav .section-nav {
  padding: 10px 12px;
  border-radius: 10px;
  white-space: nowrap;
}
.site-header nav .section-nav[aria-current="page"] {
  background: #ff3c4d17;
  color: #ff9b9f;
  box-shadow: inset 0 -2px #ff4a57;
}
.hero {
  gap: 24px;
  padding: 24px 0;
  grid-template-columns: minmax(0, 1.2fr) minmax(0, 1fr);
}
.hero h1 {
  font-size: clamp(1.75rem, 3.2vw, 2.6rem);
  line-height: 1.12;
  margin: 8px 0;
}
.hero .lead {
  max-width: 600px;
  margin: 10px 0;
  font-size: 0.92rem;
}
.hero-links {
  gap: 18px;
  margin-top: 14px;
}
.race-clock {
  padding: 18px 20px;
  background: var(--panel);
}
.clock {
  margin: 12px 0 10px;
  font-size: clamp(1.3rem, 2.1vw, 1.85rem);
}
.clock-footer {
  padding-top: 10px;
}
.clock-footer strong {
  color: var(--text);
}
.podium-card {
  box-shadow: none;
}
#inviteProgress {
  font-size: 0.77rem;
  color: var(--muted);
  margin: 0;
}


@keyframes confirmed-progress {
  0% {
    border-color: #ff9399;
  }
  100% {
    border-color: #71303e;
  }
}
.form-feedback {
  width: 100%;
  grid-column: 1 / -1;
  margin: 12px 0;
  overflow-wrap: anywhere;
}
.form-feedback small {
  display: block;
  color: var(--muted);
  margin-top: 6px;
}
.saved-receipt {
  scroll-margin-top: 170px;
}

@media (max-width: 900px) {
  .hero {
    gap: 18px;
  }
  .site-header nav {
    gap: 8px;
  }
}
@media (max-width: 700px) {
  html {
    scroll-padding-top: 146px;
  }
  .header-inner {
    gap: 8px;
    padding-top: 10px;
    padding-bottom: 10px;
  }
  .site-header nav {
    gap: 6px;
  }
  .site-header nav .section-nav {
    flex: 1;
    text-align: center;
    justify-content: center;
    min-height: 44px;
    display: inline-flex;
    align-items: center;
    padding: 8px 6px;
    font-size: 0.79rem;
  }
  .site-header nav > .button {
    display: inline-flex;
    position: absolute;
    right: 18px;
    top: 10px;
    min-height: 34px;
    padding: 6px 10px;
  }
  .hero {
    grid-template-columns: 1fr;
    padding: 18px 0;
    gap: 14px;
  }
  .hero h1 {
    font-size: 1.75rem;
  }
  .hero .lead {
    font-size: 0.84rem;
    margin: 6px 0;
  }
  .hero-links {
    margin-top: 10px;
  }
  .race-clock {
    padding: 14px 16px;
  }
  .clock {
    margin: 8px 0;
    font-size: 1.45rem;
  }
.section-title {
    gap: 12px;
  }
}
@media (prefers-reduced-motion: reduce) {


}

/* Keep the first competitor in view on phones, with the full table readable. */
@media (max-width: 700px) {
  .header-inner {
    position: relative;
  }
  .brand {
    max-width: calc(100% - 120px);
  }
  .hero .race-clock p {
    margin: 6px 0;
  }
  .hero .clock {
    margin: 6px 0;
  }
.podium-name {
    margin-top: 12px;
  }
}

/* Small factual updates stay secondary to the health bar and play button. */
.invite-health-notice {
  margin: 7px 0;
  color: #ffd5ac;
}
.history-diagnostics {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 12px;
  margin-bottom: 16px;
}
.history-diagnostics article {
  padding: 12px;
  border: 1px solid var(--line);
  border-radius: 10px;
  overflow-wrap: anywhere;
}
.history-diagnostics p {
  font-size: 0.82rem;
  margin: 6px 0;
}
.history-diagnostics small {
  color: var(--muted);
}
@media (max-width: 600px) {
  .history-diagnostics {
    grid-template-columns: 1fr;
  }
}

/* Every configured public link remains visible at every viewport width. */
.site-header nav > a.section-nav,
.site-header nav .community-nav:not([hidden]) {
  display: inline-flex;
  align-items: center;
  min-height: 44px;
}
.site-header nav {
  flex-wrap: wrap;
}
@media (max-width: 900px) {
  .site-header .header-inner {
    flex-wrap: wrap;
  }
  .site-header .brand {
    max-width: 100%;
  }
  .site-header .header-inner nav {
    width: 100%;
    display: flex;
    flex-wrap: wrap;
    justify-content: flex-start;
    gap: 5px 12px;
  }
  .site-header .header-inner nav > a {
    position: static;
    flex: 0 1 auto;
    min-height: 44px;
    padding: 8px;
    font-size: 0.78rem;
  }
  .site-header .header-inner nav > .button {
    position: static;
    min-height: 44px;
  }
  .tabs {
    flex-wrap: wrap;
    overflow: visible;
  }
}
@media (max-width: 480px) {
  .site-header .header-inner nav {
    display: grid;
    grid-template-columns: repeat(3, minmax(0, 1fr));
    gap: 2px;
  }
  .site-header .header-inner nav > a {
    justify-content: center;
    text-align: center;
    padding: 6px 3px;
    white-space: normal;
  }
  .site-header .header-inner nav > .button {
    padding: 6px 3px;
    font-size: 0.72rem;
  }
  .site-header .header-inner nav > form {
    justify-self: center;
  }
}

/* Keep the leaderboard close on phones even with every navigation link shown. */
@media (max-width: 700px) {
  .hero {
    padding: 12px 0;
    gap: 10px;
  }
  .hero .lead {
    font-size: 0.82rem;
    margin: 4px 0;
  }
  .hero-links {
    margin-top: 10px;
  }
  .race-clock {
    padding: 14px;
  }
  .race-clock .clock {
    font-size: 1.4rem;
  }
  .race-clock #raceWindow {
    font-size: 0.66rem;
  }
  .clock-footer {
    padding-top: 8px;
    margin-top: 8px;
  }
.invite-health-notice {
    font-size: 0.69rem;
    line-height: 1.4;
    margin: 5px 0;
  }
}
/* Accessible, responsive operational event viewer (independent of browser logs). */
.operations-panel{border-top:1px solid var(--line);padding-top:14px;margin-top:20px}
.operations-panel summary{cursor:pointer;padding:9px 0}
.operations-panel .form-grid{margin-top:12px}
.operations-events{display:grid;gap:8px;max-height:460px;overflow:auto;margin:12px 0}
.operations-entry{display:flex;align-items:start;gap:12px;border:1px solid var(--line);background:var(--panel);border-radius:10px;padding:12px}
.operations-entry > div{display:grid;gap:4px;min-width:0}
.operations-entry small{color:var(--muted);line-height:1.4}
.operations-severity{font-size:.67rem;font-weight:750;letter-spacing:.04em;padding:5px 6px;border-radius:6px;background:#293328;color:#8ce6a0}
.operations-entry[data-severity="warning"] .operations-severity{background:#473622;color:#f7c47e}
.operations-entry[data-severity="error"] .operations-severity{background:#4c222b;color:#ff9ea7}
.operations-entry[data-severity="info"] .operations-severity{background:#2d3448;color:#b0c5ff}
@media(max-width:520px){.operations-entry{padding:9px;gap:8px}.operations-panel .form-grid{grid-template-columns:1fr}}

/* 2026-11-10 admin refresh: common, responsive components for BOTH sources.
   The server owns all values; these styles never change rankings or numbers. */
.provider-panel .section-title {gap:16px;align-items:flex-start}
.provider-summary {display:grid;gap:18px}
.provider-summary-heading{display:flex;gap:16px;justify-content:space-between;align-items:flex-start}
.provider-summary-heading h2{font-size:1.55rem;letter-spacing:-.025em;margin:4px 0 8px}
.provider-summary-heading p{margin:0}
.provider-state{display:inline-flex;align-items:center;gap:7px;border:1px solid #577861;background:#192b22;color:#b8ecd0;border-radius:100px;padding:7px 11px;font-size:.72rem;font-weight:750;white-space:nowrap}
.provider-state::before{content:"";display:inline-block;width:7px;height:7px;border-radius:50%;background:currentColor}
.provider-state[data-state="warning"]{border-color:#94704e;background:#382617;color:#ffd096}
.provider-state[data-state="error"]{border-color:#945265;background:#361824;color:#ffbbc5}
.provider-state[data-state="waiting"]{border-color:#626078;background:#252133;color:#c7b9dd}
.provider-metrics{display:grid;grid-template-columns:repeat(4,minmax(0,1fr));gap:10px}
.provider-metrics article,.provider-quality>div,.provider-quality-grid>div{
  border:1px solid var(--line);border-radius:12px;background:linear-gradient(155deg,#24151e,#1a1018);
  padding:15px;display:flex;flex-direction:column;gap:7px;min-width:0
}
.provider-metrics article>span,.provider-quality-grid>div>span{color:var(--muted);font-size:.72rem;font-weight:600}
.provider-metrics article>strong{font-size:.87rem;line-height:1.45;overflow-wrap:anywhere;font-variant-numeric:tabular-nums}
.provider-quality{display:grid;grid-template-columns:2fr 1fr;gap:10px}
.provider-quality strong{font-size:.87rem;line-height:1.45;overflow-wrap:anywhere}
.provider-issues{padding:14px 17px;border:1px solid #91673d;background:rgba(116,67,18,.15);border-radius:12px;color:#ffe1b9}
.provider-issues[hidden]{display:none}
.provider-issues>strong{font-size:.82rem}
.provider-issues ul{margin:9px 0 0;padding-left:21px;font-size:.77rem;line-height:1.65}
.provider-actions{display:flex;align-items:center;flex-wrap:wrap;gap:9px;margin:18px 0 13px}
.provider-actions form{margin:0}
.provider-actions .button{white-space:normal}
.provider-panel .table-scroll{margin-top:12px}
.provider-panel .field{margin:17px 0 0;max-width:560px}
.provider-quality-grid{display:grid;grid-template-columns:repeat(4,minmax(0,1fr));gap:12px;margin:18px 0}
.provider-quality-grid strong{font-size:1.32rem;font-variant-numeric:tabular-nums}
.provider-overview-grid{display:grid;grid-template-columns:repeat(2,minmax(0,1fr));gap:14px}
.provider-overview-tile{color:var(--text);text-decoration:none;background:linear-gradient(150deg,#271720,#1a1019);border:1px solid var(--line);border-radius:14px;padding:18px;display:grid;grid-template-columns:1fr auto;gap:8px 12px;align-content:start;min-width:0}
.provider-overview-tile:hover,.provider-overview-tile:focus-visible{border-color:var(--accent);outline-offset:3px}
.provider-overview-tile>span:first-child{font-size:1rem;font-weight:800}
.provider-overview-tile>strong{grid-column:1/-1;font-size:1.45rem}
.provider-overview-tile>small{grid-column:1/-1;color:var(--muted);overflow-wrap:anywhere}
.provider-advanced{padding:9px 0}
.provider-advanced summary{cursor:pointer;font-weight:700;color:var(--text)}
.admin-activity-page .health-panel{border:0;padding:0;margin:0;background:transparent;box-shadow:none}
.admin-activity-page .section-title{margin-bottom:23px}
.ops-summary-grid{display:grid;grid-template-columns:repeat(5,minmax(0,1fr));gap:9px;margin-top:16px}
.ops-summary-grid>div{display:grid;gap:6px;background:#20141d;border:1px solid var(--line);border-radius:10px;padding:14px}
.ops-summary-grid span{font-size:.69rem;color:var(--muted)}
.ops-summary-grid strong{font-size:1.32rem;font-variant-numeric:tabular-nums}
.ops-filters{display:grid;grid-template-columns:1fr 1fr 1.3fr;gap:12px;align-items:end;margin-top:18px}
.ops-filters .field{min-width:0}
.ops-buttons{margin-top:15px}
.operations-panel{border-top:1px solid var(--line);margin:25px 0 0;padding-top:16px}
.operations-panel[open]>summary{margin-bottom:9px}
.operations-panel summary{display:flex;gap:10px;justify-content:space-between;align-items:center;font-size:.92rem;cursor:pointer}
.operations-entry{display:flex;align-items:flex-start;gap:13px;border:1px solid var(--line);border-radius:12px;padding:15px;background:linear-gradient(145deg,#22141c,#1a1118)}
.operations-entry-main{display:grid;gap:5px;min-width:0;flex:1}
.operations-entry-heading{display:flex;justify-content:space-between;gap:12px;flex-wrap:wrap;align-items:baseline}
.operations-entry-heading strong{font-size:.87rem}
.operations-entry-heading time{font-size:.72rem;color:var(--muted);font-variant-numeric:tabular-nums}
.operations-details{font-size:.74rem;color:var(--muted)}
.operations-advice{font-size:.76rem;line-height:1.5;margin:3px 0 0;color:#f2d2dc}
.operations-severity{font-size:.67rem;font-weight:750;letter-spacing:.03em;padding:6px 8px;border-radius:6px;background:#203329;color:#aee5c0}
.operations-entry[data-severity="warning"] .operations-severity{background:#473622;color:#ffd091}
.operations-entry[data-severity="error"] .operations-severity{background:#4c222b;color:#ffb0c2}
.operations-entry[data-severity="info"] .operations-severity{background:#292d42;color:#b8c7fb}
.operations-events{max-height:620px;overflow:auto;display:grid;gap:9px;margin:15px 0;scrollbar-color:#6c3545 #221721}
.tabs a[aria-current="page"]{font-weight:800}
.admin-main .tabs{scrollbar-width:thin}
@media(max-width:1100px){.provider-metrics{grid-template-columns:repeat(2,minmax(0,1fr))}.provider-quality-grid{grid-template-columns:repeat(2,minmax(0,1fr))}}
@media(max-width:760px){
 .provider-overview-grid,.provider-quality{grid-template-columns:1fr}
 .ops-summary-grid{grid-template-columns:repeat(3,minmax(0,1fr))}
 .ops-filters{grid-template-columns:1fr 1fr}
 .ops-filters .field:last-child{grid-column:1/-1}
 .provider-summary-heading{flex-wrap:wrap}
}
@media(max-width:520px){
 .provider-metrics,.provider-quality-grid{grid-template-columns:1fr 1fr;gap:8px}
 .provider-metrics article,.provider-quality>div,.provider-quality-grid>div{padding:12px}
 .provider-metrics article>strong{font-size:.76rem}
 .provider-summary-heading h2{font-size:1.22rem}
 .ops-summary-grid{grid-template-columns:repeat(2,minmax(0,1fr))}
 .ops-filters{grid-template-columns:1fr}
 .ops-filters .field:last-child{grid-column:auto}
 .operations-entry{flex-direction:column;gap:8px;padding:12px}
 .operations-entry-heading{display:grid;gap:5px}
 .provider-actions .button{width:100%;text-align:center}
 .provider-actions form{width:100%}
}
```

## `static/v11-system.css`

```css
/* REDHUNLLEF V11 — unified, deliberately quiet visual system.
 * Presentation only. Never add wagering, balance or provider logic here.
 * Load last so older page-specific styles cannot produce conflicting borders.
 */
:root {
  --rh-bg:#111116; --rh-surface:#1b1a22; --rh-surface-raised:#21202a;
  --rh-border:#38333e; --rh-text:#f4f0f4; --rh-muted:#bfb5c1;
  --rh-brand:#d83f56; --rh-brand-soft:#452531; --rh-focus:#f2a1ad;
  --rh-radius:12px; --rh-radius-lg:16px; --rh-gap:16px;
}
body {background-color:var(--rh-bg);color:var(--rh-text)}
:where(a, button, input, select, textarea, summary):focus-visible {outline:2px solid var(--rh-focus);outline-offset:3px}
:where(.button,button,input,select,textarea) {font-family:inherit}
:where(.panel, .podium-card, .game-card) {box-shadow:none}
:where(.muted,.small) {line-height:1.55}
/* A single hierarchy: one prominent page heading; restrained secondary copy. */
body[data-page="admin"] {--admin-background:var(--rh-bg);--admin-sidebar:#15141b;--admin-card:var(--rh-surface);--admin-border:var(--rh-border);--admin-soft:var(--rh-muted)}
body[data-page="admin"] .admin-page-heading {margin-bottom:20px}
body[data-page="admin"] .admin-page-heading h1 {font-size:clamp(1.85rem,2.3vw,2.2rem);letter-spacing:-.04em}
body[data-page="admin"] .admin-page-kicker {font-weight:680;color:#aa9eaa;letter-spacing:.1em}
body[data-page="admin"] .admin-page-description {font-size:.86rem;max-width:52ch}
body[data-page="admin"] .admin-workspace.shell {max-width:1300px;padding-top:31px}
body[data-page="admin"] .admin-sidebar {width:226px;flex-basis:226px;background:#15141b;padding-top:21px}
body[data-page="admin"] .admin-sidebar-head {margin-bottom:23px}
body[data-page="admin"] .admin-primary-nav a {min-height:44px;padding:9px 12px;font-size:.87rem;border-radius:10px}
body[data-page="admin"] .admin-primary-nav a[aria-current="page"] {background:#32232c;border-color:#5b3845}
body[data-page="admin"] .admin-side-status {margin-top:25px}
body[data-page="admin"] .admin-topbar {height:62px;background:#15131a}
body[data-page="admin"] .admin-provider-tab {min-height:42px;border-radius:9px;background:#201d25;padding:8px 14px}
body[data-page="admin"] .admin-provider-tab[aria-current="page"] {background:#3a2630;border-color:#8a4554}
body[data-page="admin"] .admin-subnav {margin-bottom:21px;gap:3px}
body[data-page="admin"] .admin-subnav a {min-height:38px;font-size:.81rem;padding:9px 12px}
body[data-page="admin"] .admin-subnav a[aria-current="page"] {background:#302730}
body[data-page="admin"] .panel {border-color:#38333c;border-radius:var(--rh-radius)}
body[data-page="admin"] .panel.form-panel {margin-bottom:15px}
body[data-page="admin"] .section-title h2 {font-size:1.13rem}
body[data-page="admin"] .admin-heading-actions {margin-left:auto}
body[data-page="admin"] .admin-saved-chip {font-size:.73rem}
/* Less competition on Overview: one primary action, one backup action, a dropdown. */
body[data-page="admin"] .admin-overview-actions {display:flex;align-items:center;gap:9px;flex-wrap:wrap;margin:0 0 20px}
body[data-page="admin"] .admin-action-menu {position:relative}
body[data-page="admin"] .admin-action-menu > summary {border:1px solid var(--rh-border);padding:10px 15px;border-radius:9px;min-height:42px;display:flex;align-items:center;cursor:pointer;list-style:none;font-size:.84rem;color:#ede9ef}
body[data-page="admin"] .admin-action-menu > summary::-webkit-details-marker {display:none}
body[data-page="admin"] .admin-action-menu > summary::after {content:'⌄';margin-left:15px;font-size:1rem;color:var(--rh-muted)}
body[data-page="admin"] .admin-action-menu[open] > summary {border-color:#986473}
body[data-page="admin"] .admin-action-menu nav {position:absolute;z-index:22;top:calc(100% + 7px);left:0;min-width:195px;display:grid;gap:3px;background:#24202a;border:1px solid #55414d;padding:8px;border-radius:10px;box-shadow:0 15px 40px #0008}
body[data-page="admin"] .admin-action-menu nav a {padding:11px 10px;color:#eee8ed;text-decoration:none;border-radius:7px;font-size:.84rem;white-space:nowrap}
body[data-page="admin"] .admin-action-menu nav a:hover {background:#3e2d38}
/* Settings is a compact section selector, not four oversized competing cards. */
body[data-page="admin"] .admin-settings-compactnav {display:flex;flex-wrap:wrap;gap:7px;padding:0 0 17px;margin-bottom:17px;border-bottom:1px solid var(--rh-border)}
body[data-page="admin"] .admin-settings-compactnav a {text-decoration:none;color:#d8ceda;background:#221e27;border:1px solid #39323d;padding:9px 11px;min-height:40px;border-radius:8px;font-size:.82rem}
body[data-page="admin"] .admin-settings-compactnav a:hover {background:#362a35;color:white}
body[data-page="admin"] .form-grid {gap:13px}
body[data-page="admin"] .form-panel details > summary {cursor:pointer}
body[data-page="admin"] .save-bar {border-radius:11px}
/* Keep status truthful, but make routine provider details secondary. */
body[data-page="admin"] .notice.warning {border-radius:11px}
body[data-page="admin"] .provider-overview-grid {gap:11px}
body[data-page="admin"] .admin-settings-shortcuts {gap:8px}
body[data-page="admin"] .admin-settings-shortcuts a {padding:13px;border-radius:9px}
body[data-page="admin"] .admin-workspace table {font-variant-numeric:tabular-nums}
body[data-page="admin"] .admin-workspace table td,body[data-page="admin"] .admin-workspace table th {border-color:#35313b}
/* Public homepage: remove redundant links and let each block breathe. */
body:not([data-page="admin"]) .public-home {padding-bottom:46px}
body:not([data-page="admin"]) .public-hero {padding-block:clamp(26px,3.3vw,42px) 21px;gap:27px}
body:not([data-page="admin"]) .public-hero h1 {font-size:clamp(2.1rem,4.2vw,3.55rem);letter-spacing:-.054em;line-height:1.08;max-width:660px;margin:9px 0 13px}
body:not([data-page="admin"]) .public-hero .lead {font-size:1rem;line-height:1.6;margin-bottom:16px;color:#c3b9c6}
body:not([data-page="admin"]) .public-hero .race-clock {background:#211b25;border-color:#4a3b45;box-shadow:none;padding:clamp(20px,2.4vw,27px)}
body:not([data-page="admin"]) .public-hero .clock {font-size:clamp(1.9rem,3.5vw,2.9rem);margin:9px 0}
body:not([data-page="admin"]) .public-hero .sponsor {background:#1e1a24;border-color:#3f343e}



body:not([data-page="admin"]) .public-leaderboards > .section-title {margin-bottom:14px}
body:not([data-page="admin"]) .public-board-hint {display:none}
body:not([data-page="admin"]) .public-provider-tabs {border-color:#3b333e;background:#1a1921}
body:not([data-page="admin"]) .public-provider-tabs .button {min-width:135px}
body:not([data-page="admin"]) .public-provider-tabs .button[aria-selected="true"] {background:#3a2731!important;border-color:#755160!important}
body:not([data-page="admin"]) .source-status {background:#1d1a22;border-color:#39323e}
body:not([data-page="admin"]) .public-podium .podium-card {background:#1e1b25;border:1px solid #3e3642;padding:clamp(15px,2vw,22px)}
body:not([data-page="admin"]) .public-podium .podium-card.place-1 {background:#32222e;border-color:#885062;box-shadow:none}
body:not([data-page="admin"]) .public-podium .podium-card .eyebrow {letter-spacing:.07em}
body:not([data-page="admin"]) .public-table th {background:#211f28;color:#c9bfcc}
body:not([data-page="admin"]) .public-table tbody tr:nth-child(even) {background:#ffffff02}
body:not([data-page="admin"]) .public-table tbody tr:hover {background:#ffffff08}

body:not([data-page="admin"]) :is(.game-card,.history-weeks a):hover {border-color:#9c6271}
body:not([data-page="admin"]) :is(.history-heading,.gaming-heading) h1 {font-size:clamp(1.8rem,3.6vw,2.65rem);letter-spacing:-.04em}
body:not([data-page="admin"]) :is(.game-card,.history-weeks a) {transition:border-color .15s ease,background .15s ease}

body:not([data-page="admin"]) .site-header {border-bottom:1px solid #332c37}
body:not([data-page="admin"]) .public-nav-links a[aria-current="page"] {background:#32222d;border-color:#794454;color:#fff}
body:not([data-page="admin"]) .public-more summary:hover {background:#29212d}
@media(max-width:900px) {
  body[data-page="admin"] .admin-workspace.shell {padding:20px 16px 40px}
  body:not([data-page="admin"]) .public-hero {grid-template-columns:1fr}
}
@media(max-width:790px) {
  body[data-page="admin"] .admin-sidebar {width:270px;flex-basis:auto}
  body[data-page="admin"] .admin-settings-compactnav {flex-wrap:nowrap;overflow-x:auto;padding-bottom:13px}
  body[data-page="admin"] .admin-settings-compactnav a {white-space:nowrap}
}
@media(max-width:550px) {
  body[data-page="admin"] .admin-overview-actions {display:grid;grid-template-columns:repeat(2,minmax(0,1fr))}
  body[data-page="admin"] .admin-action-menu {grid-column:1/-1}
  body[data-page="admin"] .admin-action-menu > summary {justify-content:center}
  body[data-page="admin"] .admin-action-menu nav {width:100%}
  body:not([data-page="admin"]) .public-hero h1 {font-size:2.3rem}
  body:not([data-page="admin"]) .public-podium .podium-card {padding:16px}
}
@media(prefers-reduced-motion:reduce) {
  :where(*, *::before, *::after) {scroll-behavior:auto!important;animation-duration:.01ms!important;transition-duration:.01ms!important}
}

body[data-page="admin"] .admin-state-card {padding:17px 20px;display:flex;align-items:center;justify-content:space-between;gap:15px;margin-bottom:18px;background:#25202b}
body[data-page="admin"] .admin-state-card >div {display:grid;gap:5px}
body[data-page="admin"] .admin-state-card strong {font-size:1.03rem}
body[data-page="admin"] .admin-state-card span:not(.eyebrow) {color:var(--rh-muted);font-size:.79rem}
@media(max-width:600px) {body[data-page="admin"] .admin-state-card {align-items:stretch;flex-direction:column}}
```

## `static/v14-modern.css`

```css
/* V14 public race system: one quiet hierarchy for both providers. */
body:not([data-page="admin"]) {
  --public-card: #1b1820;
  --public-card-raised: #211d27;
  --public-line: #352f3a;
  --public-line-strong: #5c3a46;
  --public-soft: #b8adb9;
  --public-ring: #f06a7f;
  --public-radius: 14px;
}
body:not([data-page="admin"]) .race-hero {
  display:grid;
  grid-template-columns:minmax(0,1.2fr) minmax(310px,.8fr);
  align-items:center;
  gap:clamp(26px,5vw,72px);
  padding:clamp(42px,6vw,82px) 0 34px;
}
body:not([data-page="admin"]) .race-hero-copy {min-width:0}
body:not([data-page="admin"]) .race-hero h1 {
  margin:12px 0 16px;
  font-size:clamp(2.7rem,6.2vw,5.4rem);
  line-height:.98;
  letter-spacing:-.07em;
  text-wrap:balance;
}
body:not([data-page="admin"]) .race-hero .lead {
  max-width:680px;
  margin:0 0 22px;
  color:#c7bdc8;
  font-size:clamp(1rem,1.5vw,1.15rem);
  line-height:1.7;
}
body:not([data-page="admin"]) .provider-brand-row {
  display:grid;
  grid-template-columns:repeat(2,minmax(0,220px));
  gap:10px;
  margin-top:14px;
}
body:not([data-page="admin"]) .provider-brand-card {
  min-height:64px;
  display:grid;
  grid-template-columns:40px 1fr auto;
  align-items:center;
  gap:12px;
  padding:10px 12px;
  color:#d8ced9;
  background:#1b1820;
  border:1px solid #342f39;
  border-radius:12px;
  text-decoration:none;
  transition:background .16s ease,border-color .16s ease,transform .16s ease;
}
body:not([data-page="admin"]) .provider-brand-card:hover {background:#24202a;border-color:#59444f;transform:translateY(-1px)}
body:not([data-page="admin"]) .provider-brand-card.is-selected {background:#2b2027;border-color:#a84d60;color:#fff}
body:not([data-page="admin"]) .provider-brand-card small {display:block;color:#9f95a1;font-size:.66rem;line-height:1.2;letter-spacing:.02em;text-transform:none}
body:not([data-page="admin"]) .provider-brand-card strong {display:block;margin-top:3px;font-size:1rem;line-height:1.2}
body:not([data-page="admin"]) .provider-mark {display:grid;place-items:center;width:40px;height:40px;border-radius:10px;background:#35242d;color:#ff9cac;font-weight:850;font-size:1.08rem}
body:not([data-page="admin"]) .public-race-summary {
  padding:clamp(22px,3vw,32px);
  background:linear-gradient(145deg,#28202a,#17151c 70%);
  border-color:#4a3a44;
  box-shadow:0 24px 70px #0003;
}
body:not([data-page="admin"]) .race-summary-top {display:flex;justify-content:space-between;align-items:center;gap:12px}
body:not([data-page="admin"]) .public-race-summary .clock {
  margin:18px 0 10px;
  white-space:normal;
  font-size:clamp(2rem,4vw,3.2rem);
  font-weight:850;
  line-height:1.08;
  letter-spacing:-.055em;
}
body:not([data-page="admin"]) .public-race-summary .muted {margin:0;line-height:1.55}
body:not([data-page="admin"]) .public-provider-tabs {margin:0;padding:4px;background:#18161c;border-color:#332e37}
body:not([data-page="admin"]) .public-provider-tabs .button {min-width:168px;padding:10px 15px;font-size:.85rem;font-weight:720}
body:not([data-page="admin"]) .public-provider-tabs .button[aria-selected="true"] {background:#44242e!important;border-color:#9e4b5e!important}
body:not([data-page="admin"]) .public-leaderboards {padding-top:28px}
body:not([data-page="admin"]) .leaderboard-heading {margin-bottom:22px}
body:not([data-page="admin"]) .leaderboard-heading h2 {font-size:clamp(2rem,4vw,3.1rem)}
body:not([data-page="admin"]) .public-fallback {max-width:680px;margin:0 0 18px;background:#241f27;border-color:#453a46;color:#ded5de}
body:not([data-page="admin"]) .public-podium {
  grid-template-columns:repeat(3,minmax(0,1fr));
  align-items:stretch;
  gap:14px;
  margin:22px 0 18px;
}
body:not([data-page="admin"]) .public-podium .podium-card,
body:not([data-page="admin"]) .public-podium .podium-card.place-1 {
  min-height:205px;
  padding:22px;
  background:#1d1a22;
  border-color:#38313b;
  box-shadow:none;
}
body:not([data-page="admin"]) .public-podium .podium-card.place-1 {background:linear-gradient(150deg,#38232c,#201b23 72%);border-color:#895061}
body:not([data-page="admin"]) .public-podium .podium-name,
body:not([data-page="admin"]) .public-podium .place-1 .podium-name {
  display:block;
  margin:28px 0 28px;
  font-size:clamp(1.15rem,2vw,1.55rem);
  line-height:1.2;
  white-space:nowrap;
  overflow:hidden;
  text-overflow:ellipsis;
}
body:not([data-page="admin"]) .public-podium .podium-values {grid-template-columns:1fr 1fr;align-items:end}
body:not([data-page="admin"]) .public-podium .podium-values small {font-size:.62rem;letter-spacing:.09em}
body:not([data-page="admin"]) .public-podium .podium-values strong {font-size:clamp(.95rem,1.5vw,1.2rem)}
body:not([data-page="admin"]) .public-table {padding:0;background:#19171d;border-color:#342e37}
body:not([data-page="admin"]) .public-table table {font-size:.88rem}
body:not([data-page="admin"]) .public-table th {padding:16px 18px;background:#201d24;color:#aaa0ac;font-size:.67rem}
body:not([data-page="admin"]) .public-table td {height:56px;padding:13px 18px;border-color:#2c2730}
body:not([data-page="admin"]) .public-table tbody tr:hover {background:#ffffff04}
body:not([data-page="admin"]) .public-coverage {margin:12px 2px 0;color:#9f95a1;font-size:.78rem}
body:not([data-page="admin"]) .public-games-cta {
  display:flex;
  justify-content:space-between;
  align-items:center;
  gap:24px;
  margin:42px 0 12px;
  padding:26px 28px;
  background:linear-gradient(135deg,#211b24,#18161d);
}
body:not([data-page="admin"]) .public-games-cta h2 {margin:4px 0 7px;font-size:clamp(1.35rem,2.8vw,2rem)}
body:not([data-page="admin"]) .public-games-cta p {margin:0}
body:not([data-page="admin"]) .source-status,
body:not([data-page="admin"]) .public-board-hint,
body:not([data-page="admin"]) #streamStatus,
body:not([data-page="admin"]) .leaderboard-foot {display:none!important}

@media (max-width:880px) {
  body:not([data-page="admin"]) .race-hero {grid-template-columns:1fr;padding-top:38px}
  body:not([data-page="admin"]) .public-race-summary {max-width:none}
}
@media (max-width:680px) {
  body:not([data-page="admin"]) .race-hero h1 {font-size:clamp(2.55rem,13vw,4.2rem)}
  body:not([data-page="admin"]) .provider-brand-row {grid-template-columns:1fr 1fr}
  body:not([data-page="admin"]) .provider-brand-card {grid-template-columns:34px 1fr;padding:9px;min-height:58px}
  body:not([data-page="admin"]) .provider-brand-card > span:last-child {display:none}
  body:not([data-page="admin"]) .provider-mark {width:34px;height:34px}
  body:not([data-page="admin"]) .public-provider-tabs {display:grid;grid-template-columns:1fr 1fr;width:100%}
  body:not([data-page="admin"]) .public-provider-tabs .button {min-width:0;padding-inline:8px}
  body:not([data-page="admin"]) .public-podium {grid-template-columns:1fr}
  body:not([data-page="admin"]) .public-podium .podium-card:nth-child(2) {order:-1}
  body:not([data-page="admin"]) .public-podium .podium-card,
  body:not([data-page="admin"]) .public-podium .podium-card.place-1 {min-height:0}
  body:not([data-page="admin"]) .public-podium .podium-name,
  body:not([data-page="admin"]) .public-podium .place-1 .podium-name {margin:18px 0 20px}
  body:not([data-page="admin"]) .public-table table {min-width:580px}
  body:not([data-page="admin"]) .public-games-cta {align-items:flex-start;flex-direction:column}
}
```

## `static/v15-system.css`

```css
:root{
  --rh-bg:#0d0b10;--rh-surface:#17151c;--rh-surface-2:#1d1921;--rh-surface-3:#241d25;
  --rh-border:#332c35;--rh-border-strong:#55404a;--rh-text:#f6f2f5;--rh-muted:#aaa0ad;
  --rh-accent:#e93b58;--rh-accent-soft:#3a2029;--rh-success:#74d6a0;--rh-warning:#efbd61;
  --rh-radius:14px;--rh-shadow:0 18px 55px rgba(0,0,0,.28);
  --rh-page-title:clamp(2.25rem,5vw,4rem);--rh-section-title:clamp(1.55rem,3vw,2rem);
  --rh-body:1rem;--rh-small:.875rem;--rh-meta:.75rem;
}
body:not([data-page="admin"]){background:radial-gradient(circle at 78% -12%,#2d111b 0,transparent 31%),var(--rh-bg);color:var(--rh-text)}
body:not([data-page="admin"]) h1{font-size:var(--rh-page-title);letter-spacing:-.055em;line-height:1.02}
body:not([data-page="admin"]) h2{font-size:var(--rh-section-title);letter-spacing:-.035em}
body:not([data-page="admin"]) .panel{background:var(--rh-surface);border:1px solid var(--rh-border);border-radius:var(--rh-radius);box-shadow:none}
body:not([data-page="admin"]) .button{border-radius:10px}
body:not([data-page="admin"]) .button.primary{background:var(--rh-accent);border-color:var(--rh-accent);color:white}
body:not([data-page="admin"]) .accent{color:#ff758d}
.public-home .race-hero{padding-top:48px}.public-home .race-hero h1{max-width:760px}.public-home .race-hero .lead{max-width:640px}
.provider-brand-row{max-width:470px}.provider-brand-card{height:64px}.provider-brand-card small{font-size:.7rem!important;text-transform:none!important;letter-spacing:.01em!important}.provider-brand-card strong{font-size:1rem!important}
.public-leaderboards .leaderboard-heading h2{font-size:var(--rh-section-title)!important}.public-podium .podium-card{border-radius:var(--rh-radius)!important}.public-podium .podium-card.place-1{transform:translateY(-6px)}
.public-table th,.public-table td{font-variant-numeric:tabular-nums}.public-fallback{font-size:.9rem;padding:13px 15px}

/* RedPoints Games */
.gaming-page{padding-top:44px;padding-bottom:64px}.gaming-heading-v15{display:grid;grid-template-columns:minmax(0,1fr) minmax(280px,380px);align-items:end;gap:28px;margin-bottom:24px}.gaming-title-block h1{margin:7px 0 10px}.gaming-subtitle{margin:0;color:var(--rh-muted);font-size:1.05rem}.gaming-account-card{padding:18px 20px;display:grid;gap:10px}.gaming-balance-line{display:flex;justify-content:space-between;align-items:baseline;gap:12px}.gaming-balance-line span{font-size:.72rem;color:var(--rh-muted);font-weight:750;letter-spacing:.08em}.gaming-balance-line strong{font-size:2rem;font-variant-numeric:tabular-nums}.gaming-account-card .gaming-identity{margin:0;padding:8px 0 0;border-top:1px solid var(--rh-border);display:flex;gap:10px;align-items:center;flex-wrap:wrap}.gaming-account-card .gaming-identity small{margin-left:auto}.game-toolbar{display:flex;align-items:center;gap:12px;padding:12px 14px;margin-bottom:20px}.compact-game-switcher{display:flex;align-items:center;gap:8px;margin-left:auto}.compact-game-switcher label{font-size:.78rem;color:var(--rh-muted)}.compact-game-switcher select{width:auto;min-width:160px}.round-state{margin-left:auto;font-size:.78rem;color:var(--rh-muted)}
.gaming-community-v15{margin:24px 0 34px}.gaming-community-heading{align-items:end}.gaming-community-heading h2{margin:4px 0 8px}.gaming-community-tabs{display:inline-flex;padding:4px;background:#141218;border:1px solid var(--rh-border);border-radius:11px;margin:0 0 12px}.gaming-community-tabs button{border:0;background:transparent;color:var(--rh-muted);padding:9px 14px;border-radius:8px;font-weight:700}.gaming-community-tabs button.is-active{background:var(--rh-accent-soft);color:#fff}.gaming-filter-bar{margin:0 0 16px;display:flex;gap:7px;overflow:auto;padding-bottom:4px}.gaming-filter-bar button{white-space:nowrap}.gaming-community-grid-v15{grid-template-columns:1fr}.gaming-community-grid-v15>section{min-height:330px}.games-launcher-heading{display:flex;align-items:end;justify-content:space-between;margin:38px 0 16px}.games-launcher-heading h2{margin:4px 0 0}.game-cards-v15{grid-template-columns:repeat(4,minmax(0,1fr));gap:14px}.game-cards-v15 .game-card{min-height:220px;padding:18px}.game-season{margin-top:24px}
.gaming-dialog{width:min(600px,calc(100vw - 28px));border:1px solid var(--rh-border-strong);border-radius:18px;background:#17141b;color:var(--rh-text);padding:0;box-shadow:0 30px 100px #000b}.gaming-dialog::backdrop{background:rgba(5,4,7,.78);backdrop-filter:blur(6px)}.gaming-dialog-content{padding:30px}.gaming-dialog-content h2{margin:5px 0 9px}.gaming-dialog-close{position:absolute;right:12px;top:10px}.gaming-dialog-close button{border:0;background:transparent;color:#d6ccd5;font-size:1.6rem;cursor:pointer}.gaming-public-choice{display:grid!important;grid-template-columns:28px 1fr;gap:12px;align-items:start;padding:14px;border:1px solid var(--rh-border);border-radius:12px;background:#131117}.gaming-public-choice input{width:20px;height:20px;margin-top:2px}.gaming-public-choice small{display:block;margin-top:4px;color:var(--rh-muted)}

/* Admin calendar and focused workspaces */
body[data-page="admin"]{--admin-bg:#0e0d12;--admin-panel:#18161e;--admin-panel-2:#201b23;--admin-border:#352e38;--admin-soft:#a9a0ad;background:var(--admin-bg)}
body[data-page="admin"] .admin-page-heading h1{letter-spacing:-.04em}body[data-page="admin"] .panel{border-radius:14px}body[data-page="admin"] .form-panel{padding:22px}
.calendar-presets{display:flex;flex-wrap:wrap;gap:7px}.calendar-grid{display:grid;grid-template-columns:minmax(0,1fr) auto minmax(0,1fr);gap:16px;align-items:center}.calendar-field{display:grid;grid-template-columns:1fr 140px;gap:8px 10px;padding:16px;border:1px solid var(--admin-border);border-radius:13px;background:#15131a}.calendar-field .calendar-label{grid-column:1/-1;font-size:.72rem;font-weight:800;letter-spacing:.09em;color:#d4c8d2;text-transform:uppercase}.calendar-field label{font-size:.72rem;color:var(--admin-soft);align-self:end}.calendar-field input{width:100%}.calendar-arrow{font-size:1.35rem;color:#7f737f}.calendar-preview{display:grid;gap:4px;margin-top:12px;padding:14px 16px;border:1px solid #463840;border-radius:12px;background:#1d171d}.calendar-preview span{font-size:.7rem;letter-spacing:.08em;text-transform:uppercase;color:var(--admin-soft)}.calendar-preview strong{font-size:1rem}.calendar-preview small{color:var(--admin-soft)}.calendar-preview.is-invalid{border-color:#9c563e}.official-schedule-card{display:flex;justify-content:space-between;align-items:center;gap:20px;margin:16px 0;padding:17px;border:1px solid #4b3942;border-radius:13px;background:#1c171d}.official-schedule-card strong,.official-schedule-card small{display:block}.official-schedule-card small{margin-top:5px;color:var(--admin-soft)}.section-title.compact{margin-top:8px}.field-error{color:#ff9b83}
body[data-page="admin"] .admin-subnav{gap:3px}body[data-page="admin"] .admin-subnav a{padding:9px 12px}
.admin-workspace[data-focus="prizes"] .shuffle-schedule-section,.admin-workspace[data-focus="prizes"] .shuffle-advanced-section{display:none}.admin-workspace[data-focus="prizes"] .shuffle-prize-section{display:block}.admin-workspace[data-focus="shuffleSource"] .shuffle-summary-section,.admin-workspace[data-focus="shuffleSource"] .shuffle-standings-section{display:none}.admin-workspace[data-focus="shuffleSource"] .shuffle-source-section{display:block}.admin-workspace[data-focus="empireDatesTitle"] .empire-section:not(.empire-schedule),.admin-workspace[data-focus="empireRewards"] .empire-section:not(.empire-rewards),.admin-workspace[data-focus="empireRaceDetails"] .empire-section:not(.empire-source):not(.empire-source-overview){display:none}.admin-workspace[data-focus="empireDatesTitle"] .empire-schedule,.admin-workspace[data-focus="empireRewards"] .empire-rewards,.admin-workspace[data-focus="empireRaceDetails"] .empire-source,.admin-workspace[data-focus="empireRaceDetails"] .empire-source-overview{display:block}
body[data-page="admin"] .provider-actions{display:flex;gap:8px;flex-wrap:wrap}body[data-page="admin"] .provider-metrics{grid-template-columns:repeat(3,minmax(0,1fr))}body[data-page="admin"] .provider-metrics article:nth-child(4){display:none}

@media(max-width:980px){.gaming-heading-v15{grid-template-columns:1fr}.gaming-account-card{max-width:none}.gaming-community-grid-v15{grid-template-columns:1fr}.game-cards-v15{grid-template-columns:repeat(2,minmax(0,1fr))}.calendar-grid{grid-template-columns:1fr}.calendar-arrow{transform:rotate(90deg);justify-self:center}}
@media(max-width:640px){.gaming-page{padding-top:28px}.gaming-account-card{padding:14px}.gaming-balance-line strong{font-size:1.65rem}.game-toolbar{align-items:stretch;flex-wrap:wrap}.compact-game-switcher{order:3;width:100%;margin:0}.compact-game-switcher select{flex:1}.round-state{margin-left:0}.gaming-community-heading{align-items:start}.gaming-activity-count{min-width:auto}.game-cards-v15{grid-template-columns:repeat(2,minmax(0,1fr));gap:10px}.game-cards-v15 .game-card{min-height:180px;padding:13px}.calendar-field{grid-template-columns:1fr}.calendar-field .calendar-label{grid-column:1}.official-schedule-card{align-items:flex-start;flex-direction:column}.public-podium .podium-card.place-1{transform:none}}
@media(prefers-reduced-motion:reduce){*{scroll-behavior:auto!important;transition-duration:.01ms!important;animation-duration:.01ms!important}}

/* Focused admin task views */
.admin-workspace[data-focus=""] .shuffle-source-section{display:none}
.admin-workspace[data-focus="schedule"] .shuffle-prize-section{display:none}
.admin-workspace[data-focus=""] .empire-schedule,.admin-workspace[data-focus=""] .empire-rewards,.admin-workspace[data-focus=""] .empire-source{display:none}
```

## `static/v16-system.css`

```css
/* V17 timer-card refinement: preserve the V16 shared summary contract while
   restoring the wider, natural-height Shuffle card proportions, stable provider
   switching, compact Admin diagnostics and stable numeric layouts. */
:root{
  --race-countdown-size:clamp(2.05rem,4.25vw,3.45rem);
  --race-countdown-line:1.05;
  --race-summary-card-width:520px;
}
body:not([data-page="admin"]) .public-home .race-hero{
  align-items:center;
}
body:not([data-page="admin"]) .public-race-summary{
  width:min(100%,var(--race-summary-card-width));
  min-height:0!important;
  height:auto;
  justify-self:end;
  display:flex;
  flex-direction:column;
  padding:clamp(20px,2.25vw,27px)!important;
  background:linear-gradient(145deg,#28202a,#17151c 72%)!important;
  border:1px solid #4a3a44!important;
  border-radius:18px!important;
  box-shadow:0 20px 60px rgba(0,0,0,.24)!important;
}
body:not([data-page="admin"]) .public-race-summary .race-countdown,
body:not([data-page="admin"]) #shuffleRaceClock .race-countdown,
body:not([data-page="admin"]) #empireRaceClock .race-countdown{
  font-size:var(--race-countdown-size)!important;
  font-weight:800!important;
  line-height:var(--race-countdown-line)!important;
  letter-spacing:-.055em!important;
  font-variant-numeric:tabular-nums lining-nums;
  white-space:nowrap!important;
  overflow:hidden;
  text-overflow:ellipsis;
  margin:16px 0 9px!important;
  min-height:0;
  display:block;
}
body:not([data-page="admin"]) .public-race-summary .race-date-range{
  margin:0!important;
  min-height:0;
  display:block;
  font-size:.9rem;
  line-height:1.45;
}
body:not([data-page="admin"]) .public-race-summary .clock-footer{
  min-height:0;
  margin-top:16px!important;
  padding-top:14px!important;
  border-top:1px solid var(--rh-border)!important;
  display:flex;
  align-items:center;
  justify-content:space-between;
  gap:16px;
}
body:not([data-page="admin"]) .public-race-summary .clock-footer strong{
  font-size:1.18rem!important;
  font-variant-numeric:tabular-nums lining-nums;
}
body:not([data-page="admin"]) .public-provider-tabs{
  min-height:48px;
}
body:not([data-page="admin"]) [role="tabpanel"]{
  transition:opacity .16s ease;
}
body:not([data-page="admin"]) .provider-brand-card,
body:not([data-page="admin"]) .public-provider-tabs .button{
  transition:background-color .16s ease,border-color .16s ease,color .16s ease,transform .16s ease;
}
body:not([data-page="admin"]) .public-podium .podium-card,
body:not([data-page="admin"]) .public-table{
  font-variant-numeric:tabular-nums lining-nums;
}
body:not([data-page="admin"]) .public-podium .podium-values>div{
  min-width:0;
}
body:not([data-page="admin"]) .public-podium [data-wager],
body:not([data-page="admin"]) .public-podium [data-empire-wager],
body:not([data-page="admin"]) .public-table .number{
  font-variant-numeric:tabular-nums lining-nums;
}

/* Admin: meaningful provider summaries without turning ordinary retries into
   giant warning panels. */
body[data-page="admin"] .provider-request-fingerprint{
  margin-top:14px;
  border:1px solid var(--admin-border);
  border-radius:11px;
  background:#141218;
}
body[data-page="admin"] .provider-request-fingerprint summary{
  cursor:pointer;
  padding:11px 13px;
  color:var(--admin-soft);
  font-weight:700;
}
body[data-page="admin"] .provider-request-fingerprint dl{
  display:grid;
  grid-template-columns:repeat(5,minmax(0,1fr));
  gap:8px;
  margin:0;
  padding:0 13px 13px;
}
body[data-page="admin"] .provider-request-fingerprint dl div{
  min-width:0;
  padding:9px;
  border-radius:8px;
  background:var(--admin-panel-2);
}
body[data-page="admin"] .provider-request-fingerprint dt{
  color:var(--admin-soft);
  font-size:.68rem;
  text-transform:uppercase;
  letter-spacing:.07em;
}
body[data-page="admin"] .provider-request-fingerprint dd{
  margin:5px 0 0;
  overflow-wrap:anywhere;
  font-variant-numeric:tabular-nums;
}
body[data-page="admin"] form[aria-busy="true"]{
  opacity:.86;
}
body[data-page="admin"] form[aria-busy="true"] [data-payout-submit]{
  cursor:wait;
}

@media(max-width:880px){
  body:not([data-page="admin"]) .public-race-summary{
    width:100%;
    max-width:none;
    justify-self:stretch;
  }
}
@media(max-width:820px){
  body:not([data-page="admin"]) .public-race-summary .race-countdown,
  body:not([data-page="admin"]) #shuffleRaceClock .race-countdown,
  body:not([data-page="admin"]) #empireRaceClock .race-countdown{
    font-size:clamp(1.8rem,8.5vw,2.75rem)!important;
  }
  body[data-page="admin"] .provider-request-fingerprint dl{grid-template-columns:repeat(2,minmax(0,1fr))}
}
@media(max-width:480px){
  body:not([data-page="admin"]) .public-race-summary .race-countdown,
  body:not([data-page="admin"]) #shuffleRaceClock .race-countdown,
  body:not([data-page="admin"]) #empireRaceClock .race-countdown{
    font-size:clamp(1.55rem,9vw,2.2rem)!important;
    letter-spacing:-.04em!important;
  }
  body:not([data-page="admin"]) .public-race-summary .clock-footer{align-items:flex-start;flex-direction:column;gap:5px}
  body[data-page="admin"] .provider-request-fingerprint dl{grid-template-columns:1fr}
}
@media(prefers-reduced-motion:reduce){
  body:not([data-page="admin"]) [role="tabpanel"],
  body:not([data-page="admin"]) .provider-brand-card,
  body:not([data-page="admin"]) .public-provider-tabs .button{transition:none!important}
}
```

## `tools/admin_acceptance_v13.py`

```python
#!/usr/bin/env python3
"""Source-level and template acceptance test that does not contact providers."""
import argparse
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--python', default=sys.executable)
    args = parser.parse_args()
    commands = [
        [args.python, '-m', 'unittest', 'tests.test_navigation_v12', 'tests.test_admin_reliability_v13'],
        [args.python, 'wager_backend.py', '--check'],
    ]
    for command in commands:
        print('+', ' '.join(command))
        result = subprocess.run(command, cwd=ROOT)
        if result.returncode:
            return result.returncode
    print('PASS: admin route, template, payout, dates and release checks completed.')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
```

## `tools/deployment_diagnostics.py`

```python
"""Validate the App Platform source layout without printing secrets.

Use `python tools/deployment_diagnostics.py` after extracting the ZIP.
Use `--archive /path/to/file.zip` to check the archive layout before extraction.
No Flask imports or network access are necessary for source validation.
"""
import argparse
import json
from pathlib import Path
import re
import sys
import time
import zipfile
from urllib.request import Request, urlopen
from urllib.error import HTTPError, URLError

ROOT = Path(__file__).resolve().parents[1]
REQUIRED_ROOT = ('wager_backend.py','requirements.txt','runtime.txt','Procfile','BUILD_MANIFEST.json')

def evaluate(root=ROOT):
    root=Path(root)
    errors=[]
    for name in REQUIRED_ROOT:
        if not (root/name).is_file():errors.append('Missing at source root: '+name)
    if not (root/'templates/index.html').is_file():errors.append('Missing templates/index.html')
    if not (root/'static/app.js').is_file():errors.append('Missing static/app.js')
    requirements=(root/'requirements.txt').read_text(encoding='utf-8') if (root/'requirements.txt').is_file() else ''
    if not re.search(r'^Flask==',requirements,re.M):errors.append('Flask must be in root requirements.txt')
    runtime=(root/'runtime.txt').read_text(encoding='utf-8').strip() if (root/'runtime.txt').is_file() else 'missing'
    if not re.fullmatch(r'python-3\.13\.\d+',runtime):errors.append('Python version missing/unexpected: '+runtime)
    spec=(root/'app.yaml').read_text(encoding='utf-8') if (root/'app.yaml').is_file() else ''
    if re.search(r'^\s*build_command\s*:',spec,re.M):errors.append('Custom build_command found; buildpack installs requirements already')
    match=re.search(r'^\s*source_dir:\s*([^\n#]+)',spec,re.M)
    if match and match.group(1).strip() != '/':errors.append('App YAML source_dir must be / for root-flat ZIP')
    if spec and not re.search(r'^\s*run_command:\s*python wager_backend\.py',spec,re.M):errors.append('Incorrect run command')
    m=root/'BUILD_MANIFEST.json'
    if m.is_file():
        try:
            files=json.loads(m.read_text(encoding='utf-8')).get('files',{})
            for entry in files:
                if entry.startswith(('private/','data/','docs/','tests/')):errors.append('Release manifest must not require optional files: '+entry)
                if not (root/entry).is_file():errors.append('Missing manifest source: '+entry)
        except (ValueError,TypeError) as e:errors.append('Invalid release manifest')
    print('Source directory:',root)
    print('Python:',runtime)
    print('Build command: none in app.yaml; also clear existing DigitalOcean dashboard build command')
    print('Configuration:','private files present in ZIP; Git ignores them by default' if (root/'private/settings.json').is_file() else 'private settings absent; configure encrypted App Platform environment variables')
    print('Stored JSON:','included, snapshot may be stale' if (root/'data/state.json').is_file() else 'not bundled; restore live backup if needed')
    if 'YOUR_GITHUB_USER/' in spec:print('Note: app.yaml has an example repo; do not import until you replace it')
    for err in errors:print('ERROR:',err)
    if not errors:print('PASS: source layout is ready for a Python web service')
    return not errors

def check_archive(path):
    errors=[]
    with zipfile.ZipFile(path) as z:
        names=set(z.namelist())
        for expected in REQUIRED_ROOT:
            if expected not in names:errors.append('Archive root missing '+expected)
        if 'redhunllef/requirements.txt' in names:errors.append('Archive has obsolete redhunllef/ wrapper directory')
        bad=z.testzip()
        if bad:errors.append('Corrupt ZIP entry: '+bad)
        print('ZIP members:',len(names))
    for err in errors:print('ERROR:',err)
    if not errors:print('PASS: flat ZIP root; all deployment entry points found')
    return not errors

def probe(url):
    if not (url.startswith('https://') or url.startswith('http://localhost') or url.startswith('http://127.0.0.1')):
        print('ERROR: use HTTPS for a remote website');return False
    ok=True
    for path in ('/healthz','/readyz'):
        start=time.perf_counter()
        try:
            with urlopen(Request(url.rstrip('/')+path,headers={'User-Agent':'RedHunllef-deployment-check'}),timeout=10) as response:
                print(path,response.status,'%.2fs'%(time.perf_counter()-start))
                ok &= response.status==200
        except (HTTPError,URLError,TimeoutError) as exc:
            print(path,'failed:',type(exc).__name__)
            ok=False
    return ok

if __name__=='__main__':
    parser=argparse.ArgumentParser()
    parser.add_argument('--archive',help='ZIP file to inspect for root nesting or corrupt members')
    parser.add_argument('--url',help='HTTPS URL to probe after deployment')
    args=parser.parse_args()
    ok=evaluate(ROOT)
    if args.archive:ok=check_archive(args.archive) and ok
    if args.url:ok=probe(args.url) and ok
    raise SystemExit(0 if ok else 1)
```

## `tools/live_smoke_v12.py`

```python
#!/usr/bin/env python3
"""Read-only post-deployment acceptance checks for RedHunllef V12.

Run from a trusted workstation after deployment. The script authenticates over
HTTPS, follows the same GET destinations exposed in Admin, and never changes
settings or prints credentials, cookies, API keys, player records, or bodies.
"""
from argparse import ArgumentParser
from getpass import getpass
from html.parser import HTMLParser
from urllib.parse import urljoin, urlsplit
import sys
import requests

PUBLIC = ('/', '/gaming', '/history', '/healthz', '/readyz')
ADMIN = (
    '/admin',
    '/admin/leaderboards/shuffle',
    '/admin/leaderboards/shuffle/schedule',
    '/admin/leaderboards/shuffle/players',
    '/admin/leaderboards/empiredrop',
    '/admin/leaderboards/empiredrop/schedule',
    '/admin/leaderboards/empiredrop/payouts',
    '/admin/leaderboards/empiredrop/source',
    '/admin/gaming',
    '/admin/settings',
    '/admin/recovery',
    '/admin/activity',
)
COMPATIBILITY = (
    '/admin/overview', '/admin/shuffle', '/admin/race', '/admin/schedule',
    '/admin/players', '/admin/empiredrop', '/admin/gaming', '/admin/settings',
    '/admin/activity', '/admin/logs',
)


class CSRFParser(HTMLParser):
    def __init__(self):
        super().__init__(); self.value = None
    def handle_starttag(self, tag, attrs):
        if tag == 'input':
            data = dict(attrs)
            if data.get('name') == 'csrf':
                self.value = data.get('value')


def main() -> int:
    parser = ArgumentParser(description='V12 read-only deployment smoke test')
    parser.add_argument('--base-url', required=True, help='Deployed origin, e.g. https://example.com')
    parser.add_argument('--username', required=True)
    parser.add_argument('--allow-http-localhost', action='store_true')
    args = parser.parse_args()
    origin = args.base_url.rstrip('/')
    parts = urlsplit(origin)
    local_http = args.allow_http_localhost and parts.scheme == 'http' and parts.hostname in {'localhost', '127.0.0.1'}
    if parts.scheme != 'https' and not local_http:
        parser.error('An HTTPS origin is required except for an explicitly allowed localhost test.')
    if parts.query or parts.fragment or parts.username or parts.password:
        parser.error('Pass only the origin; do not include credentials, queries, or fragments.')

    session = requests.Session()
    session.headers.update({'User-Agent': 'RedHunllef-V12-ReadOnly-Smoke/1'})
    failures: list[tuple[str, object]] = []

    def get(path: str, expected: int = 200, *, redirects: bool = True):
        try:
            response = session.get(urljoin(origin + '/', path.lstrip('/')), timeout=15,
                                   allow_redirects=redirects)
            ok = response.status_code == expected
            print('PASS' if ok else 'FAIL', path, 'HTTP', response.status_code)
            if not ok:
                failures.append((path, response.status_code))
            return response
        except requests.RequestException as exc:
            print('FAIL', path, type(exc).__name__)
            failures.append((path, 'connection'))
            return None

    for path in PUBLIC:
        get(path)

    login = get('/admin/login')
    if login is None or login.status_code != 200:
        return 2
    csrf = CSRFParser(); csrf.feed(login.text)
    if not csrf.value:
        print('FAIL could not find sign-in CSRF token')
        return 2
    password = getpass('Admin password (not logged): ')
    try:
        auth = session.post(urljoin(origin + '/', 'admin/login'),
                            data={'csrf': csrf.value, 'username': args.username, 'password': password},
                            timeout=15, allow_redirects=False)
    finally:
        password = ''
    if auth.status_code != 303:
        print('FAIL sign-in did not return HTTP 303; got', auth.status_code)
        return 2
    print('PASS authenticated session established')

    for path in ADMIN:
        get(path)
    for path in COMPATIBILITY:
        get(path)

    status = get('/admin/navigation-status')
    if status is not None and status.status_code == 200:
        try:
            if not status.json().get('ok'):
                failures.append(('/admin/navigation-status', 'reported not ok'))
        except ValueError:
            failures.append(('/admin/navigation-status', 'invalid JSON'))

    print('PASS all checks - read only' if not failures else f'FAIL {len(failures)} checks')
    return 0 if not failures else 1


if __name__ == '__main__':
    raise SystemExit(main())
```

## `tools/live_smoke_v13.py`

```python
#!/usr/bin/env python3
"""Read-only post-deployment acceptance checks for RedHunllef V13.

Run from a trusted workstation after deployment. The script authenticates over
HTTPS, follows the same GET destinations exposed in Admin, and never changes
settings or prints credentials, cookies, API keys, player records, or bodies.
"""
from argparse import ArgumentParser
from getpass import getpass
from html.parser import HTMLParser
from urllib.parse import urljoin, urlsplit
import sys
import requests

PUBLIC = ('/', '/gaming', '/history', '/healthz', '/readyz')
ADMIN = (
    '/admin',
    '/admin/leaderboards/shuffle',
    '/admin/leaderboards/shuffle/schedule',
    '/admin/leaderboards/shuffle/players',
    '/admin/leaderboards/empiredrop',
    '/admin/leaderboards/empiredrop/schedule',
    '/admin/leaderboards/empiredrop/payouts',
    '/admin/leaderboards/empiredrop/source',
    '/admin/gaming',
    '/admin/settings',
    '/admin/recovery',
    '/admin/activity',
)
COMPATIBILITY = (
    '/admin/overview', '/admin/shuffle', '/admin/race', '/admin/schedule',
    '/admin/players', '/admin/empiredrop', '/admin/gaming', '/admin/settings',
    '/admin/activity', '/admin/logs',
)


class CSRFParser(HTMLParser):
    def __init__(self):
        super().__init__(); self.value = None
    def handle_starttag(self, tag, attrs):
        if tag == 'input':
            data = dict(attrs)
            if data.get('name') == 'csrf':
                self.value = data.get('value')


def main() -> int:
    parser = ArgumentParser(description='V13 read-only deployment smoke test')
    parser.add_argument('--base-url', required=True, help='Deployed origin, e.g. https://example.com')
    parser.add_argument('--username', required=True)
    parser.add_argument('--allow-http-localhost', action='store_true')
    args = parser.parse_args()
    origin = args.base_url.rstrip('/')
    parts = urlsplit(origin)
    local_http = args.allow_http_localhost and parts.scheme == 'http' and parts.hostname in {'localhost', '127.0.0.1'}
    if parts.scheme != 'https' and not local_http:
        parser.error('An HTTPS origin is required except for an explicitly allowed localhost test.')
    if parts.query or parts.fragment or parts.username or parts.password:
        parser.error('Pass only the origin; do not include credentials, queries, or fragments.')

    session = requests.Session()
    session.headers.update({'User-Agent': 'RedHunllef-V13-ReadOnly-Smoke/1'})
    failures: list[tuple[str, object]] = []

    def get(path: str, expected: int = 200, *, redirects: bool = True):
        try:
            response = session.get(urljoin(origin + '/', path.lstrip('/')), timeout=15,
                                   allow_redirects=redirects)
            ok = response.status_code == expected
            print('PASS' if ok else 'FAIL', path, 'HTTP', response.status_code)
            if not ok:
                failures.append((path, response.status_code))
            return response
        except requests.RequestException as exc:
            print('FAIL', path, type(exc).__name__)
            failures.append((path, 'connection'))
            return None

    for path in PUBLIC:
        get(path)

    login = get('/admin/login')
    if login is None or login.status_code != 200:
        return 2
    csrf = CSRFParser(); csrf.feed(login.text)
    if not csrf.value:
        print('FAIL could not find sign-in CSRF token')
        return 2
    password = getpass('Admin password (not logged): ')
    try:
        auth = session.post(urljoin(origin + '/', 'admin/login'),
                            data={'csrf': csrf.value, 'username': args.username, 'password': password},
                            timeout=15, allow_redirects=False)
    finally:
        password = ''
    if auth.status_code != 303:
        print('FAIL sign-in did not return HTTP 303; got', auth.status_code)
        return 2
    print('PASS authenticated session established')

    for path in ADMIN:
        get(path)
    for path in COMPATIBILITY:
        get(path)

    status = get('/admin/navigation-status')
    if status is not None and status.status_code == 200:
        try:
            if not status.json().get('ok'):
                failures.append(('/admin/navigation-status', 'reported not ok'))
        except ValueError:
            failures.append(('/admin/navigation-status', 'invalid JSON'))

    print('PASS all checks - read only' if not failures else f'FAIL {len(failures)} checks')
    return 0 if not failures else 1


if __name__ == '__main__':
    raise SystemExit(main())
```

## `tools/live_smoke_v14.py`

```python
#!/usr/bin/env python3
"""Read-only post-deployment acceptance checks for RedHunllef V14.

The script validates public pages, the allowlisted Gaming community feed and
all protected administrator destinations. It never changes settings or prints
credentials, cookies, API keys, player records or response bodies.
"""
from argparse import ArgumentParser
from getpass import getpass
from html.parser import HTMLParser
from urllib.parse import urljoin, urlsplit
import requests

PUBLIC = ('/', '/gaming', '/history', '/public-state',
          '/gaming/api/public-leaderboard', '/healthz', '/readyz')
ADMIN = (
    '/admin', '/admin/leaderboards/shuffle',
    '/admin/leaderboards/shuffle/schedule',
    '/admin/leaderboards/shuffle/players',
    '/admin/leaderboards/empiredrop',
    '/admin/leaderboards/empiredrop/schedule',
    '/admin/leaderboards/empiredrop/payouts',
    '/admin/leaderboards/empiredrop/source',
    '/admin/gaming', '/admin/settings', '/admin/recovery', '/admin/activity',
)
FORBIDDEN_PUBLIC_GAMING_KEYS = {
    'wallet', 'player_tag', 'ips', 'ip', 'balance', 'receipts', 'receipt',
    'server_seed', 'recovery_hash', 'funding_adjustment', 'admin_grants',
}


class CSRFParser(HTMLParser):
    def __init__(self):
        super().__init__(); self.value = None
    def handle_starttag(self, tag, attrs):
        if tag == 'input':
            data = dict(attrs)
            if data.get('name') == 'csrf':
                self.value = data.get('value')


def all_keys(value):
    if isinstance(value, dict):
        for key, child in value.items():
            yield str(key)
            yield from all_keys(child)
    elif isinstance(value, list):
        for child in value:
            yield from all_keys(child)


def main() -> int:
    parser = ArgumentParser(description='V14 read-only deployment smoke test')
    parser.add_argument('--base-url', required=True)
    parser.add_argument('--username', required=True)
    parser.add_argument('--allow-http-localhost', action='store_true')
    args = parser.parse_args()
    origin = args.base_url.rstrip('/')
    parts = urlsplit(origin)
    local_http = args.allow_http_localhost and parts.scheme == 'http' and parts.hostname in {'localhost', '127.0.0.1'}
    if parts.scheme != 'https' and not local_http:
        parser.error('An HTTPS origin is required except for an explicitly allowed localhost test.')
    if parts.query or parts.fragment or parts.username or parts.password:
        parser.error('Pass only the origin; do not include credentials, queries, or fragments.')

    session = requests.Session()
    session.headers.update({'User-Agent': 'RedHunllef-V14-ReadOnly-Smoke/1'})
    failures = []

    def get(path, expected=200, redirects=True):
        try:
            response = session.get(urljoin(origin + '/', path.lstrip('/')), timeout=15,
                                   allow_redirects=redirects)
            ok = response.status_code == expected
            print('PASS' if ok else 'FAIL', path, 'HTTP', response.status_code)
            if not ok: failures.append((path, response.status_code))
            return response
        except requests.RequestException as exc:
            print('FAIL', path, type(exc).__name__)
            failures.append((path, 'connection'))
            return None

    results = {path: get(path) for path in PUBLIC}
    home = results.get('/')
    if home is not None and home.status_code == 200:
        if 'RedHunllef Wager Race' not in home.text or home.text.count('Powered By') < 2:
            failures.append(('/', 'uniform race branding missing'))
            print('FAIL / uniform race branding')
        else:
            print('PASS / uniform race branding')

    feed = results.get('/gaming/api/public-leaderboard')
    if feed is not None and feed.status_code == 200:
        try:
            value = feed.json()
            required = {'live_players', 'weekly_leaders', 'game_leaders', 'game_counts', 'active_count'}
            if not required <= set(value):
                raise ValueError('missing public feed fields')
            leaked = FORBIDDEN_PUBLIC_GAMING_KEYS & set(all_keys(value))
            if leaked:
                raise ValueError('private keys: ' + ', '.join(sorted(leaked)))
            print('PASS public Gaming projection allowlist')
        except (ValueError, TypeError) as exc:
            print('FAIL public Gaming projection', str(exc))
            failures.append(('/gaming/api/public-leaderboard', 'invalid projection'))

    login = get('/admin/login')
    if login is None or login.status_code != 200:
        return 2
    csrf = CSRFParser(); csrf.feed(login.text)
    if not csrf.value:
        print('FAIL could not find sign-in CSRF token')
        return 2
    password = getpass('Admin password (not logged): ')
    try:
        auth = session.post(urljoin(origin + '/', 'admin/login'),
                            data={'csrf': csrf.value, 'username': args.username, 'password': password},
                            timeout=15, allow_redirects=False)
    finally:
        password = ''
    if auth.status_code != 303:
        print('FAIL sign-in did not return HTTP 303; got', auth.status_code)
        return 2
    print('PASS authenticated session established')

    for path in ADMIN:
        get(path)
    status = get('/admin/navigation-status')
    if status is not None and status.status_code == 200:
        try:
            if not status.json().get('ok'):
                failures.append(('/admin/navigation-status', 'reported not ok'))
        except ValueError:
            failures.append(('/admin/navigation-status', 'invalid JSON'))

    print('PASS all checks - read only' if not failures else f'FAIL {len(failures)} checks')
    return 0 if not failures else 1


if __name__ == '__main__':
    raise SystemExit(main())
```

## `tools/verify_redpoints.py`

```python
"""Optional offline audit, not a server launcher: python tools/verify_redpoints.py receipts.json"""
import argparse
import json
from pathlib import Path
import sys
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from fairness import verify

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Verify RedPoints receipts without contacting a server.')
    parser.add_argument('file', type=Path)
    parser.add_argument('--commitment', help='Previously saved commitment; for a single receipt.')
    args = parser.parse_args()
    try:
        values = json.loads(args.file.read_text(encoding='utf-8'))
    except (OSError, UnicodeError, json.JSONDecodeError) as exc:
        parser.error(f'Cannot read receipt JSON: {exc}')
    values = values if isinstance(values, list) else [values]
    if not values or args.commitment and len(values) != 1:
        parser.error('Provide receipts, or one receipt when using --commitment.')
    checks = []
    for index, value in enumerate(values, 1):
        try: passed = verify(value, args.commitment)
        except (ValueError, KeyError, TypeError): passed = False
        checks.append(passed)
        label = value.get('request_id', f'receipt-{index}') if isinstance(value, dict) else f'receipt-{index}'
        print(('PASS' if passed else 'FAIL') + ' ' + str(label))
    raise SystemExit(0 if all(checks) else 1)
```

## `tools/visual_acceptance_v16.py`

```python
"""Headless visual contract for the shared public race summary.

Uses an installed Chromium/Chrome binary. It never starts the application,
contacts a provider, or reads private state.
"""
from pathlib import Path
import html, json, re, shutil, subprocess, sys

ROOT = Path(__file__).resolve().parents[1]
FIXTURE = ROOT / 'tests' / 'fixtures' / 'v16_countdown_uniformity.html'
BROWSER = next((shutil.which(name) for name in ('chromium','chromium-browser','google-chrome','chrome') if shutil.which(name)), None)


def run(width, height, screenshot):
    if not BROWSER:
        raise RuntimeError('Chromium or Chrome is required for visual acceptance.')
    uri = FIXTURE.resolve().as_uri()
    common = [BROWSER, '--headless', '--no-sandbox', '--disable-gpu', '--allow-file-access-from-files',
              f'--window-size={width},{height}']
    try:
        subprocess.run(common + [f'--screenshot={screenshot}', uri], check=True, timeout=20, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        dumped = subprocess.check_output(common + ['--dump-dom', uri], text=True, timeout=20, stderr=subprocess.DEVNULL)
    except subprocess.TimeoutExpired as exc:
        raise RuntimeError('Chromium did not complete the visual fixture within 20 seconds. Run this check on a browser-capable CI runner.') from exc
    match = re.search(r'<pre id="result">(.*?)</pre>', dumped, re.S)
    if not match:
        raise RuntimeError('Visual fixture did not return computed measurements.')
    value = json.loads(html.unescape(match.group(1)))
    if value['fontA'] != value['fontB'] or value['lineA'] != value['lineB']:
        raise AssertionError(f'Countdown typography differs: {value}')
    if abs(value['heightA'] - value['heightB']) > 1:
        raise AssertionError(f'Race summary heights differ: {value}')
    return value


if __name__ == '__main__':
    out = ROOT / 'tests' / 'visual-output'
    out.mkdir(exist_ok=True)
    results = {
        'desktop': run(1440, 900, out / 'v16-countdown-desktop.png'),
        'mobile': run(430, 900, out / 'v16-countdown-mobile.png'),
    }
    print(json.dumps(results, indent=2))
```
