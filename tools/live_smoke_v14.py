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
