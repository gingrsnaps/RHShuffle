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
                          action='/admin?tab=settings#diagnostics'))
    cards.append(dict(key='games', label='Games', state='good' if probe['ok'] else 'error',
                      status='Ready to save play' if probe['ok'] else 'Saving unavailable',
                      detail='Results are acknowledged after their save completes. Retry receipts prevent duplicate bets.',
                      last_success=storage['last_write'], action='/admin/gaming'))
    cards.append(dict(key='storage', label='Saved data', state='good' if probe['ok'] else 'error',
                      status='Readable and writable' if probe['ok'] else 'Needs attention',
                      detail=probe['message'], last_success=probe['checked_at'], action='/admin?tab=settings#recovery'))
    return dict(release=RELEASE, generated_at=int(time.time()), ready=probe['ok'], components=cards,
                metrics={**stats, 'storage':storage}, retention='Recent 512 requests and 256 store operations; reset on restart.')
