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
from race_support import EASTERN, clean_overrides, decimal_amount, fmt_et, money

LOG = logging.getLogger('redhunllef')


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
            message = ('Shuffle history is temporarily unavailable. Saved results remain visible; retrying automatically.' if row.get('error') else
                       row.get('warning') or ('No qualifying wagers were returned for this week.' if checked and not row.get('rows') else
                       'Loading this completed week from Shuffle…' if not checked else ''))
            weeks.append({**period, 'status':status, 'message':message,
                'updated_at':checked, 'updated_et':fmt_et(checked) if checked else 'Awaiting first result',
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
            if previous.get('retry_at', 0) > now or (previous.get('updated_at') and
                    not previous.get('error') and now - previous['updated_at'] < refresh):
                continue
            record = {**period, 'scope':scope, 'updated_at':0, 'attempt_at':now,
                      'retry_at':0, 'count':0, 'rows':[], 'prizes':prizes,
                      'error':'', 'warning':'', **previous}
            record['attempt_at'] = now
            pause = 0
            try:
                incoming = normalize(self.providers.shuffle(site), site, self.config.raw_fallback)
                rows, _, count = rank(incoming['source'], overrides, self.config.aggregation, 25)
                record.update(rows=[dict(rank=p['rank'], username=p['username'], weighted_wager=p['weighted_wager']) for p in rows],
                              count=count, prizes=prizes, updated_at=now, error='', retry_at=0,
                              warning=incoming['warning'][:500])
                LOG.info('HISTORY Saved %s to %s; %s qualifying players.', period['start_et'], period['end_et'], count)
            except (ProviderError, ValueError) as exc:
                pause = max(60, min(86400, getattr(exc, 'retry_after', 0)))
                if getattr(exc, 'status', None) in (401, 403):
                    pause = max(pause, 900)
                record.update(error='Provider check failed; retry pending.', retry_at=now + pause)
                LOG.warning('HISTORY Week ending %s unavailable (%s). Previous result retained.', period['id'], type(exc).__name__)
            cache[period['id']] = record
            self.store.publish('weekly_history', clean_history(dict(version=1, weeks=list(cache.values()))), revision)
            # A throttle/access/outage failure stops this batch, preventing four
            # immediate rejected requests against the same affiliate service.
            if pause:
                return pause
        return 60

    def loop(self):
        try:
            while not self.stop_event.is_set():
                try:
                    delay = self.check()
                except Exception as exc:
                    LOG.warning('HISTORY Check interrupted (%s); retrying in 60s.', type(exc).__name__)
                    delay = 60
                if self.stop_event.wait(delay):
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
        if self.thread:
            self.thread.join(timeout=1)
