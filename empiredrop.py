"""EmpireDrop-only, read-only affiliate standings.

Important: No official EmpireDrop wagering API contract was publicly verified.
The endpoint, authentication headers, fields, scope, units and pagination MUST be
confirmed by EmpireDrop before enabling it. This module never guesses URLs,
sends keys to redirects, scrapes the website, or fabricates results.
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
from race_support import EASTERN, fmt_et, local_input

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


class EmpireDropBoard:
    def __init__(self, config, store):
        self.config, self.store = config, store
        self.lock, self.stop_event, self.wakeup = threading.RLock(), threading.Event(), threading.Event()
        self.thread, self.interval = None, 60
        self.saved = store.live('empiredrop') or {}
        self.last_manual, self.queued_at, self.checking = 0.0, 0, False

    def _settings(self):
        _, admin = self.store.admin()
        return validate_settings({**self.config.empiredrop, **admin.get('empiredrop_api', {})})

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
        now = int(time.time())
        site = self._schedule(now)
        scope = scope_id(site)
        with self.lock:
            self.checking = True
        try:
            old = self.store.live('empiredrop') or {}
            if old.get('scope') != scope:
                old = {'scope':scope, 'rows':[], 'updated_at':0}
            try:
                rows = self.fetch(site)
            except ProviderError as error:
                next_value = {**old, 'attempt_at':now, 'error':str(error)[:220], 'error_kind':error.kind}
                LOG.warning('EmpireDrop check did not finish (%s).', error.kind)
            else:
                next_value = {'scope':scope, 'rows':rows, 'updated_at':now,
                              'attempt_at':now, 'error':'', 'error_kind':''}
            # Do not overwrite a newly changed schedule while HTTP was in flight.
            if scope_id(self._schedule()) != scope:
                return old
            with self.lock:
                self.store.publish('empiredrop', next_value)
                self.saved = next_value
            return next_value
        finally:
            with self.lock:
                self.checking = False

    def _visible(self, site):
        with self.lock:
            value = copy.deepcopy(self.saved)
        if value.get('scope') != scope_id(site):
            value = {'rows':[], 'updated_at':0, 'attempt_at':0, 'error':'', 'error_kind':''}
        return value

    def public(self, unused_shuffle_site=None):
        site = self._schedule()
        saved = self._visible(site)
        rows = saved.get('rows', [])[:15]
        error = saved.get('error', '')
        label = ('Updates delayed · last verified results' if error and rows else
                 'Source unavailable · ' + error if error else
                 'Updated' if saved.get('updated_at') else 'Awaiting verified EmpireDrop data')
        return {'rows':[{'rank':r['rank'], 'username':r['username'][:2]+'******', 'wager':r['wager']} for r in rows],
                'label':label[:260], 'updated_at':saved.get('updated_at',0),
                'currency':self._settings()['currency'], 'referral_url':REFERRAL_URL,
                'schedule':{k:site[k] for k in ('start_time','end_time','start_et','end_et','mode')},
                'code':CODE}

    def private_status(self, unused_shuffle_site=None):
        site, opts = self._schedule(), self._settings()
        snapshot = self._visible(site)
        state = self.public()
        state.update(rows=[{'rank':r['rank'], 'username':r['username'], 'wager':r['wager']} for r in snapshot.get('rows',[])],
                     attempt_at=snapshot.get('attempt_at',0), error=snapshot.get('error',''),
                     error_kind=snapshot.get('error_kind',''), configuration=opts,
                     schedule={**state['schedule'], 'start_input':site['start_input'], 'end_input':site['end_input']},
                     configured={key:{'configured':bool(self.config.credentials.get(key)),
                                      'source':self.config.sources.get(key,'missing'),
                                      'masked':('••••'+self.config.credentials[key][-4:] if self.config.credentials.get(key) else '')}
                                 for key in ('empiredrop_public_key','empiredrop_private_key')},
                     running=bool(self.thread and self.thread.is_alive()),
                     checking=self.checking, queued_at=self.queued_at)
        return state

    def request_refresh(self):
        with self.lock:
            if time.monotonic() - self.last_manual < 15:
                return False
            self.last_manual, self.queued_at = time.monotonic(), int(time.time())
            self.wakeup.set()
            return True

    def _loop(self):
        while not self.stop_event.is_set():
            try:
                self.check()
            except Exception:
                LOG.exception('EmpireDrop local worker failure (no credential data logged).')
            self.wakeup.wait(self.interval)
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
