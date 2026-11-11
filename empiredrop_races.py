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


def select_race(races, options, now=None):
    """Select the sole running race unless an explicit slug is configured.

    The running-races API does *not* list completed/scheduled races, so an
    explicit slug may be fetched directly from the detail endpoint.
    """
    settings = validate_race_settings(options)
    if settings['race_slug']:
        return next((race for race in races if race['slug'] == settings['race_slug']),
                    {'slug': settings['race_slug'], 'name': settings['race_slug']})
    if not settings['auto_select']:
        raise ProviderError('Select an EmpireDrop race slug or enable automatic selection.', kind='selection')
    running = [item for item in races if item['is_active']]
    if len(running) != 1:
        message = ('No running EmpireDrop races are available.' if not running else
                   'Multiple EmpireDrop races are running; select a slug in Admin.')
        raise ProviderError(message, kind='selection')
    return running[0]


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
