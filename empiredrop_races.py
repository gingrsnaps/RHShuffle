"""EmpireDrop race endpoints documented by the user's two developer-portal URLs.

GET /api/v1/race/affiliates/{publicKey}       (race discovery)
GET /api/v1/affiliate-partner/races/{slug}   (race details)

Only the paths and HTTP methods are established from the references. Their
server origin, authentication, response shapes and wagering units need a
provider-backed verification. The adapter exposes these options to admins and
NEVER turns ambiguous fields into public monetary values.
"""
from __future__ import annotations

from datetime import datetime, timezone
from decimal import Decimal, InvalidOperation
import logging
import re
import time
from urllib.parse import quote, urlsplit

import requests
from integrations import ProviderError

LOG = logging.getLogger('redhunllef.empiredrop.races')
DISCOVER_PATH = '/api/v1/race/affiliates/{publicKey}'
DETAIL_PATH = '/api/v1/affiliate-partner/races/{slug}'
SLUG = re.compile(r'^[A-Za-z0-9][A-Za-z0-9_-]{0,99}$')
JSON_PATH = re.compile(r'^[a-zA-Z][a-zA-Z0-9_-]{0,49}(?:\.[a-zA-Z][a-zA-Z0-9_-]{0,49}){0,7}$')

RACE_DEFAULTS = {
    'source_mode': 'races',  # 'legacy' continues to use the old verified contract.
    'api_base_url': 'https://empiredrop.com',  # Host is configurable; docs links prove paths only.
    'race_slug': '',  # Blank = unique active race only (never choose arbitrarily).
    'auto_select': True,
    'race_auth_mode': 'none',  # No secret sent until authenticated access is documented.
    'race_private_header': 'X-Private-Key',
    'race_public_header': 'X-Public-Key',
    'race_rows_path': '',  # Set after reviewing *sanitized* response structure.
    'race_name_field': 'username',
    'race_user_id_field': '',
    'race_wager_field': 'wagered',
    'race_currency': 'USD',
    'race_wager_divisor': '1',
    'race_window_policy': 'provider',  # Display provider race times when supplied.
    'race_start_field': 'startTime',
    'race_end_field': 'endTime',
    'race_verified_fields': False,  # Explicitly acknowledge units and wager semantics.
}
RACE_EDITABLE = frozenset(RACE_DEFAULTS)


def validate_race_settings(candidate):
    """Whitelisted configuration, including strict outbound HTTP host validation."""
    if not isinstance(candidate, dict) or set(candidate) - RACE_EDITABLE:
        raise ValueError('Unexpected EmpireDrop race configuration setting.')
    settings = {**RACE_DEFAULTS, **candidate}
    settings['source_mode'] = str(settings['source_mode']).lower()
    if settings['source_mode'] not in ('races', 'legacy'):
        raise ValueError('Choose the races API or legacy API.')
    base = str(settings['api_base_url']).strip().rstrip('/')
    parts = urlsplit(base)
    host = (parts.hostname or '').lower()
    if (parts.scheme != 'https' or (host != 'empiredrop.com' and not host.endswith('.empiredrop.com'))
        or parts.username or parts.password or parts.port not in (None, 443)
        or parts.path or parts.query or parts.fragment):
        raise ValueError('EmpireDrop API base must be an HTTPS empiredrop.com host without paths or credentials.')
    settings['api_base_url'] = base
    slug = str(settings['race_slug']).strip()
    if slug and not SLUG.fullmatch(slug):
        raise ValueError('Race slug contains unsupported characters.')
    settings['race_slug'] = slug
    if settings['race_auth_mode'] not in ('none', 'private_header', 'public_header', 'dual_headers', 'bearer_private'):
        raise ValueError('Unknown race API authentication mode.')
    for key in ('race_private_header', 'race_public_header'):
        header = str(settings[key])
        if not re.fullmatch('[A-Za-z][A-Za-z0-9-]{0,49}', header) or header.lower() in (
            'host', 'cookie', 'authorization', 'connection', 'content-length', 'proxy-authorization',
            'transfer-encoding', 'location'):
            raise ValueError('Unsafe credential HTTP header.')
    if settings['race_private_header'].lower() == settings['race_public_header'].lower():
        raise ValueError('Public and private key header names must differ.')
    for key in ('race_rows_path', 'race_user_id_field'):
        if settings[key] and not JSON_PATH.fullmatch(str(settings[key])):
            raise ValueError('Invalid optional JSON path: ' + key)
    for key in ('race_name_field', 'race_wager_field', 'race_start_field', 'race_end_field'):
        if not JSON_PATH.fullmatch(str(settings[key])):
            raise ValueError('Invalid JSON field: ' + key)
    if settings['race_currency'] not in ('EUR', 'USD'):
        raise ValueError('Only a provider-confirmed EUR/USD wager currency is accepted.')
    if settings['race_window_policy'] not in ('provider', 'local'):
        raise ValueError('Choose provider race dates or the local race schedule.')
    try:
        amount = Decimal(str(settings['race_wager_divisor']))
        if not amount.is_finite() or not 0 < amount <= 10**12: raise ValueError
    except (InvalidOperation, ValueError):
        raise ValueError('Invalid race wager divisor.') from None
    for key in ('auto_select', 'race_verified_fields'):
        settings[key] = settings[key] is True
    return settings


def path(obj, dotted):
    if not dotted: return obj
    for key in dotted.split('.'):
        if not isinstance(obj, dict): return None
        obj = obj.get(key)
    return obj


def keys_only(value):
    """Shape summary for admin diagnostics: no player values, keys or PII."""
    if isinstance(value, list):
        return {'type': 'array', 'items': len(value), 'first': keys_only(value[0]) if value else None}
    if isinstance(value, dict):
        return {'type': 'object', 'fields': {str(k)[:70]: ('array' if isinstance(v, list) else
                'object' if isinstance(v, dict) else type(v).__name__) for k,v in list(value.items())[:40]}}
    return {'type': type(value).__name__}


def time_value(value):
    """Accept ISO8601, Unix seconds or milliseconds for race period verification."""
    if value is None or isinstance(value, bool): return None
    try:
        if isinstance(value, (int, float)) or (isinstance(value, str) and value.isdigit()):
            v = float(value)
            if v > 1e11: v /= 1000
            return int(v) if 946684800 <= v <= 4102444799 else None
        if isinstance(value, str):
            dt = datetime.fromisoformat(value.replace('Z', '+00:00'))
            if dt.tzinfo is None: return None
            return int(dt.timestamp())
    except (ValueError, OverflowError, TypeError):
        pass
    return None


def race_catalog(payload):
    """Parse race *identifiers*, never player or wager data from discovery."""
    candidates = payload if isinstance(payload, list) else None
    if isinstance(payload, dict):
        for candidate in (path(payload, 'data.races'), path(payload, 'data.items'), payload.get('races'),
                          payload.get('data'), payload.get('results'), payload.get('items')):
            if isinstance(candidate, list): candidates = candidate; break
        if candidates is None and isinstance(payload.get('data'), dict):
            for candidate in (payload['data'].get('results'), payload['data'].get('affiliates')):
                if isinstance(candidate, list): candidates = candidate; break
    if candidates is None:
        raise ProviderError('Race discovery JSON contains no recognized races array. Check response structure.', kind='format')
    if len(candidates) > 500:
        raise ProviderError('Race discovery returned too many entries.', kind='format')
    races, unique = [], set()
    for item in candidates:
        if not isinstance(item, dict): continue
        slug = next((v for v in (path(item, 'slug'), path(item, 'race.slug'), path(item, 'raceSlug'),
                     path(item, 'race_slug')) if isinstance(v, str) and SLUG.fullmatch(v)), None)
        if not slug or slug in unique: continue
        unique.add(slug)
        name = next((v for v in (item.get('name'), item.get('title'), path(item, 'race.name'))
                     if isinstance(v, str) and v.strip()), slug)
        status = str(item.get('status') or path(item, 'race.status') or '').lower()
        start = time_value(next((v for v in (item.get('startTime'), item.get('start_time'), item.get('startAt'),
                item.get('startsAt'), path(item, 'race.startTime')) if v is not None), None))
        end = time_value(next((v for v in (item.get('endTime'), item.get('end_time'), item.get('endAt'),
                item.get('endsAt'), path(item, 'race.endTime')) if v is not None), None))
        races.append(dict(slug=slug, name=name[:90], status=status[:36], start_time=start, end_time=end))
    if candidates and not races:
        raise ProviderError('Races found but none have a recognizable slug. Inspect sanitized field names.', kind='format')
    return races


def select_race(races, options, now=None):
    """Never silently select a random past or unrelated affiliate race."""
    chosen = options['race_slug']
    if chosen:
        match = next((r for r in races if r['slug'] == chosen), None)
        if match is None:
            raise ProviderError('Configured race slug is absent from this public-key affiliate race list.', kind='scope')
        return match
    if not options['auto_select']:
        raise ProviderError('Select a race slug in EmpireDrop admin or enable unique-active auto selection.', kind='configuration')
    now = int(now or time.time())
    active = [r for r in races if (r['start_time'] is not None and r['end_time'] is not None
        and r['start_time'] <= now < r['end_time']) or r['status'] in ('active', 'ongoing', 'running', 'in_progress')]
    if len(active) != 1:
        raise ProviderError('Unable to uniquely identify an active EmpireDrop race. Select its slug in admin.', kind='selection')
    return active[0]


def extract_race_rows(payload, dotted=''):
    if dotted:
        rows = path(payload, dotted)
        if not isinstance(rows, list):
            raise ProviderError('Configured race rows path does not contain an array.', kind='format')
        return rows
    for key in ('leaderboard', 'participants', 'players', 'rankings', 'entries', 'results', 'users',
                'data.leaderboard', 'data.participants', 'data.players', 'data.rankings',
                'data.entries', 'data.results', 'data.race.leaderboard', 'race.leaderboard'):
        rows = path(payload, key)
        if isinstance(rows, list): return rows
        if isinstance(rows, dict):
            for sub in ('rows', 'players', 'participants', 'entries', 'items', 'data'):
                if isinstance(rows.get(sub), list): return rows[sub]
    raise ProviderError('Race details have no recognized participants array; configure race_rows_path.', kind='format')


def normalize_race(payload, settings):
    """ONLY verified wagers. Never substitute prizes, deposits or box openings."""
    opts = validate_race_settings(settings)
    rows = extract_race_rows(payload, opts['race_rows_path'])
    if len(rows) > 10000: raise ProviderError('Too many race participant entries.', kind='format')
    totals, names = {}, {}
    for item in rows:
        if not isinstance(item, dict): continue
        name = path(item, opts['race_name_field'])
        amount = path(item, opts['race_wager_field'])
        if not isinstance(name, str) or not name.strip() or len(name) > 64 or amount is None or isinstance(amount, bool):
            continue
        try: wager = Decimal(str(amount)) / Decimal(str(opts['race_wager_divisor']))
        except (InvalidOperation, ValueError, TypeError, ZeroDivisionError): continue
        if not wager.is_finite() or not 0 <= wager <= Decimal('1e18'): continue
        ident = path(item, opts['race_user_id_field']) if opts['race_user_id_field'] else None
        ident = str(ident).strip() if isinstance(ident, (str, int)) and not isinstance(ident, bool) else ''
        ident = ident or name.strip().casefold()
        # Race standings are cumulative player totals, NOT individual bets.
        # Repeated pages or duplicated players must not inflate their amount.
        totals[ident] = max(totals.get(ident, Decimal(0)), wager)
        names.setdefault(ident, name.strip())
    if rows and not totals:
        raise ProviderError('Race participants exist, but mapped username/wager fields are invalid.', kind='format')
    if not opts['race_verified_fields']:
        raise ProviderError('Race wager field and units are not verified; preview data and confirm mapping in admin.', kind='verification')
    symbol = '€' if opts['race_currency'] == 'EUR' else '$'
    ordered = sorted(totals, key=lambda k:(-totals[k], names[k].casefold()))[:15]
    return [dict(rank=i, username=names[k], wager=symbol + format(totals[k], ',.2f'))
            for i,k in enumerate(ordered, 1)]


class RaceAPI:
    """Read-only transport. Public key is path segment; private key stays server-side."""
    def __init__(self, options, credentials, requester=None):
        self.settings = validate_race_settings(options)
        self.credentials = credentials
        self.requester = requester or requests

    def _get(self, url, use_auth=False):
        opts = self.settings
        headers = {'Accept': 'application/json', 'User-Agent': 'RedHunllef-EmpireDrop-Races/1.0'}
        mode = opts['race_auth_mode'] if use_auth else 'none'
        pub, secret = self.credentials.get('empiredrop_public_key',''), self.credentials.get('empiredrop_private_key','')
        if mode in ('public_header', 'dual_headers'):
            if not pub: raise ProviderError('EmpireDrop public key missing.', kind='configuration')
            headers[opts['race_public_header']] = pub
        if mode in ('private_header', 'dual_headers', 'bearer_private'):
            if not secret: raise ProviderError('EmpireDrop private key missing.', kind='configuration')
            if mode == 'bearer_private': headers['Authorization'] = 'Bearer ' + secret
            else: headers[opts['race_private_header']] = secret
        try:
            with self.requester.get(url, headers=headers, timeout=(5, 18), stream=True, allow_redirects=False) as response:
                status = response.status_code
                if status in (301,302,303,307,308):
                    raise ProviderError('EmpireDrop redirected the API request; credentials were not forwarded.', kind='redirect', status=status)
                if status in (401,403):
                    raise ProviderError('EmpireDrop rejected access. Verify API permissions and authentication.', kind='access', status=status)
                if status == 429:
                    raise ProviderError('EmpireDrop rate limit reached; request frequency must be reduced.', kind='rate_limit', status=status)
                if status != 200:
                    raise ProviderError('EmpireDrop race API returned HTTP ' + str(status), kind='http', status=status)
                raw = bytearray()
                for block in response.iter_content(65536):
                    raw.extend(block)
                    if len(raw) > 4*1024*1024:
                        raise ProviderError('EmpireDrop response larger than 4 MB.', kind='format')
                import json
                from decimal import Decimal
                try: return json.loads(raw, parse_float=Decimal)
                except (UnicodeError, ValueError, TypeError):
                    raise ProviderError('EmpireDrop race API returned invalid JSON.', kind='format') from None
        except requests.RequestException:
            raise ProviderError('EmpireDrop network request failed.', kind='connection') from None

    def discover(self):
        public = self.credentials.get('empiredrop_public_key', '').strip()
        if not public or len(public) > 256:
            raise ProviderError('Configured EmpireDrop public key is missing or invalid.', kind='configuration')
        url = self.settings['api_base_url'] + DISCOVER_PATH.format(publicKey=quote(public, safe=''))
        payload = self._get(url)  # Discovery: never send private key.
        return race_catalog(payload), keys_only(payload)

    def details(self, slug):
        if not SLUG.fullmatch(str(slug)):
            raise ProviderError('Invalid race slug.', kind='configuration')
        url = self.settings['api_base_url'] + DETAIL_PATH.format(slug=quote(slug, safe=''))
        return self._get(url, use_auth=True)

    def probe(self, slug):
        payload = self.details(slug)
        structure = keys_only(payload)
        try:
            rows = extract_race_rows(payload, self.settings['race_rows_path'])
            sample = keys_only(rows[0]) if rows else None
            count = len(rows)
            error = ''
        except ProviderError as exc:
            sample, count, error = None, 0, str(exc)
        return {'race_slug':slug, 'structure': structure, 'sample_row_fields':sample,
                'participant_rows':count, 'mapping_warning':error}
