"""Bounded, in-memory throttles for rejected requests, separate from gameplay.

Successful eligible attacks are never counted or blocked by this guard. A regular
30-second rhythm is not a reason to flag someone. Records expire; no bans exist.
"""
from collections import deque
import hashlib
import hmac
import threading
import time


class AbuseGuard:
    def __init__(self, secret):
        self.secret = secret.encode()
        self.lock = threading.Lock()
        self.records, self.flags = {}, deque(maxlen=50)

    def key(self, identity, address):
        # Admin diagnostics need a correlation tag, never a raw IP or cookie.
        return hmac.new(self.secret, (identity + ':' + address).encode(), hashlib.sha256).hexdigest()[:16]

    def _entry(self, category, key, now):
        for k, v in list(self.records.items()):
            if now - v['at'] >= 60: del self.records[k]
        pair = (category, key)
        if pair not in self.records:
            if len(self.records) >= 4000:
                self.records.pop(next(iter(self.records)))
            self.records[pair] = dict(at=now, count=0)
        return self.records[pair]

    def retry_after(self, category, key):
        with self.lock:
            now = time.monotonic()
            item = self._entry(category, key, now)
            threshold = 20 if category == 'registration' else 12
            return max(1, int(60 - now + item['at']) + 1) if item['count'] >= threshold else 0

    def rejected(self, category, key, alias):
        with self.lock:
            item = self._entry(category, key, time.monotonic())
            item['count'] += 1
            threshold = 20 if category == 'registration' else 12
            if item['count'] == threshold:
                self.flags.appendleft(dict(at=int(time.time()), category=category, tag=key,
                                           alias=alias[:40], rejected=threshold))

    def status(self):
        with self.lock:
            cutoff = time.time() - 86400
            return [dict(f) for f in self.flags if f['at'] > cutoff]
