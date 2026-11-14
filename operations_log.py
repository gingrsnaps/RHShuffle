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
