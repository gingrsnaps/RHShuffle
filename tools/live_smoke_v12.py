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
