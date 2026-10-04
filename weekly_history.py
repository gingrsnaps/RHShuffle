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
    'window': 'Shuffle rejected this completed date range. Check affiliate access to historical wagers.',
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
    elif status == 400: kind = 'window'
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
