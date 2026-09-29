"""Real HTTP regressions for community access and persistent player names."""
from concurrent.futures import ThreadPoolExecutor
import copy
from pathlib import Path
import tempfile
import unittest

import test_comfort_update as support
from boss import CommunityBoss, validate_boss
from wager_backend import create_app


class PlayerAccessTests(unittest.TestCase):
    setUp = support.ComfortTests.setUp
    player = support.ComfortTests.player
    post = support.ComfortTests.post
    hit = support.ComfortTests.hit
    admin = support.ComfortTests.admin
    action = support.ComfortTests.action

    def test_100_players_share_one_proxy_and_all_attack_without_approvals(self):
        self.app.extensions['settings'].proxy = True
        clients = []
        for i in range(100):
            c = self.app.test_client()
            c.environ_base.update(REMOTE_ADDR='10.0.0.1', HTTP_DO_CONNECTING_IP='192.0.2.1')
            c.get('/play/api/state')
            clients.append(c)
        def register_and_hit(i):
            c = clients[i]
            registered = self.post(c, '/play/api/profile', username=f'CommunityMember{i:03}')
            if registered.status_code != 200: return ('registration', registered.status_code)
            return ('attack', self.hit(c).status_code)
        with ThreadPoolExecutor(max_workers=12) as pool:
            results = list(pool.map(register_and_hit, range(100)))
        self.assertEqual(results, [('attack', 200)] * 100)
        before = self.b.export()
        self.assertEqual(len(before['players']), 100)
        self.assertEqual(before['total_attacks'], 100)
        self.assertEqual(len(before['profiles']), 100)
        self.assertEqual(self.hit(clients[0]).status_code, 429)
        # Everybody gets their own next turn, not a shared connection cooldown.
        self.clock.return_value += 30
        with ThreadPoolExecutor(max_workers=12) as pool:
            self.assertEqual(list(pool.map(lambda c: self.hit(c).status_code, clients)), [200]*100)
        state = self.b.export()
        self.assertEqual(state['total_attacks'], 200)
        self.assertEqual(state['hp'], state['max_hp'] - state['total_damage'])
        self.assertEqual(len(state.get('households', {})), 0)
        validate_boss(state)

    def test_name_survives_ip_changes_refresh_restart_and_new_raid(self):
        c = self.player('StickyName'); self.hit(c)
        saved = self.b.export()
        for ip in ('192.0.2.2', '198.51.100.8', '2001:db8::a', '2001:db8:1::b'):
            c.environ_base['REMOTE_ADDR'] = ip
            current = c.get('/play/api/state').json['state']
            self.assertEqual(current['you']['display_name'], 'StickyName')
            self.assertTrue(current['you']['identity_ready'])
            self.assertIn('StickyName', c.get('/play').text)
            self.assertEqual(self.hit(c).status_code, 429)
        self.assertEqual(self.b.export(), saved)  # Polls do not rewrite a name or reset progress.
        rebuilt = create_app(self.root, testing=True)
        same = rebuilt.test_client()
        same.set_cookie('rh_raider', c.get_cookie('rh_raider').value)
        self.assertEqual(same.get('/play/api/state').json['state']['you']['display_name'], 'StickyName')
        self.assertEqual(rebuilt.extensions['boss'].export(), saved)
        self.clock.return_value += 30
        v = same.get('/play/api/state').json
        hit = same.post('/play/api/attack',json=dict(raid_id=v['state']['raid_id'],style='blade',request_id='retained-cookie-hit'),headers={'X-CSRF-Token':v['csrf']})
        self.assertEqual(hit.status_code, 200)
        rebuilt.extensions['boss'].control('restart', saved['id'])
        self.assertEqual(same.get('/play/api/state').json['state']['you']['display_name'], 'StickyName')
        self.assertTrue(same.get('/play/api/state').json['state']['you']['identity_ready'])

    def test_missing_or_changing_proxy_header_never_discards_a_player(self):
        self.app.extensions['settings'].proxy = True
        a = self.player('NoHeader'); self.assertEqual(self.hit(a).status_code, 200)
        a.environ_base['HTTP_DO_CONNECTING_IP'] = '192.0.2.44'
        self.assertEqual(a.get('/play/api/state').json['state']['you']['display_name'], 'NoHeader')
        a.environ_base['HTTP_DO_CONNECTING_IP'] = 'not-an-ip'
        self.clock.return_value += 30
        self.assertEqual(self.hit(a).status_code, 200)
        # The malformed header still is not trusted as a client IP.
        self.assertNotIn('not-an-ip', str(self.b.export()))

    def test_one_rejecting_browser_cannot_throttle_other_players_on_same_ip(self):
        bad = self.player()
        for _ in range(25): self.post(bad, '/play/api/profile', username='')
        self.assertEqual(self.post(bad, '/play/api/profile', username='BadClient').status_code, 429)
        for i in range(30):
            c = self.player(f'Unaffected{i}')
            self.assertEqual(self.hit(c).status_code, 200)
        self.assertEqual(self.b.export()['total_attacks'], 30)

    def test_valid_recovery_can_use_a_network_with_other_active_players(self):
        a = self.player('RecoverMe', '192.0.2.1'); self.hit(a)
        code = self.post(a, '/play/api/recovery-code').json['code']
        b = self.player('ExistingPlayer', '192.0.2.2'); self.hit(b)
        recovered = self.player(ip='192.0.2.2')
        response = self.post(recovered, '/play/api/recover', code=code)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json['state']['you']['display_name'], 'RecoverMe')
        self.assertEqual(self.hit(recovered).status_code, 429)
        self.clock.return_value += 30
        self.assertEqual(self.hit(recovered).status_code, 200)
        self.assertEqual(self.hit(b).status_code, 200)
        self.assertEqual(len(self.b.export()['players']), 2)

    def test_reloading_never_reissues_the_raider_identity_cookie(self):
        c = self.player('PersistentCookie'); cookie = c.get_cookie('rh_raider').value
        for _ in range(5):
            for path in ('/play', '/play/api/state'):
                response = c.get(path)
                self.assertFalse(any(h.startswith('rh_raider=') for h in response.headers.getlist('Set-Cookie')))
                self.assertEqual(c.get_cookie('rh_raider').value, cookie)
                self.assertIn('PersistentCookie', response.text)

    def test_legacy_network_claims_and_household_limits_do_not_require_a_reset(self):
        a = self.player('Existing'); self.hit(a)
        before = self.b.export()
        profile = next(iter(before['profiles'].values()))
        legacy = copy.deepcopy(before)
        legacy['networks'][profile['network']] = {'last_attack': self.clock.return_value + 300, 'day':0, 'used':500}
        legacy['households'] = {profile['network']:2}
        with self.r.store.connection(transaction=True) as conn: self.b._write(conn, legacy)
        self.b.loaded_at = 0
        current = self.b.export()
        self.assertEqual(current, legacy)
        for i in range(10):
            c = self.player(f'NewMember{i}'); self.assertEqual(self.hit(c).status_code, 200)
        after = self.b.export()
        pk = next(iter(before['profiles']))
        self.assertEqual(after['profiles'][pk], before['profiles'][pk])
        self.assertEqual(after['players'][pk], before['players'][pk])
        self.assertEqual(after['id'], before['id'])
        self.assertEqual(after['total_attacks'], before['total_attacks'] + 10)
        self.assertLess(after['hp'], before['hp'])
        validate_boss(after)

    def test_name_collision_does_not_give_access_to_someone_elses_profile(self):
        a = self.player('ReservedName'); self.hit(a)
        b = self.player()
        self.assertEqual(self.post(b, '/play/api/profile', username='reservedname').status_code, 409)
        self.assertEqual(self.hit(b).status_code, 409)
        self.assertNotIn('ReservedName', b.get('/play/api/state').text)
        self.assertEqual(self.post(b, '/play/api/profile', username='OwnName').status_code, 200)
        self.assertEqual(self.hit(b).status_code, 200)
        self.assertNotEqual(a.get('/play/api/state').json['state']['you']['name'], b.get('/play/api/state').json['state']['you']['name'])


if __name__ == '__main__': unittest.main()
