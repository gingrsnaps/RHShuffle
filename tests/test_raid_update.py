"""Requested gameplay changes, identity boundaries and additive save upgrades."""
import copy
import json
import os
from pathlib import Path
import secrets
import tempfile
import unittest
from unittest.mock import patch

from boss import CommunityBoss, DAY, MAX_HP, MAX_DAMAGE, validate_boss
from wager_backend import create_app


class RaidUpdateTests(unittest.TestCase):
    def setUp(self):
        temp = tempfile.TemporaryDirectory(); self.addCleanup(temp.cleanup)
        self.root = Path(temp.name)
        env = patch.dict(os.environ, {'APP_ENV':'test', 'ADMIN_BOOTSTRAP_PASS':'test-password'}, clear=True)
        env.start(); self.addCleanup(env.stop)
        self.app = create_app(self.root, testing=True)
        self.r, self.b = self.app.extensions['runtime'], self.app.extensions['boss']
        self.addCleanup(self.r.store.close)
        clock = patch('boss.time.time', return_value=self.b.export()['created_at'] + 1.25)
        self.clock = clock.start(); self.addCleanup(clock.stop)

    def client(self, ip='192.0.2.1', name=None):
        c = self.app.test_client(); c.environ_base['REMOTE_ADDR'] = ip
        value = c.get('/play/api/state').json
        if name:
            self.assertEqual(self.name(c, name).status_code, 200)
        return c, value

    def name(self, c, name, **extra):
        v = c.get('/play/api/state').json
        return c.post('/play/api/profile', json={'raid_id':v['state']['raid_id'], 'username':name, **extra}, headers={'X-CSRF-Token':v['csrf']})

    def attack(self, c, **extra):
        v = c.get('/play/api/state').json
        return c.post('/play/api/attack', json={'raid_id':v['state']['raid_id'], 'style':v['state']['weakness'],
                      'request_id':secrets.token_hex(16), **extra}, headers={'X-CSRF-Token':v['csrf']})

    def core_hit(self, guest='a', ip='192.0.2.1', style=None):
        v = self.b.status(guest, ip)
        return self.b.attack(guest, ip, style or v['weakness'], v['raid_id'], secrets.token_hex(16))

    def admin(self):
        c, v = self.client('198.51.100.50')
        with c.session_transaction() as session: session.update(user='gingrsnaps', auth_version=1)
        return c, v['csrf']

    def test_username_is_required_on_http_and_cannot_be_forged_in_attack(self):
        c, v = self.client()
        self.assertEqual(self.attack(c, username='Fake', role='admin').status_code, 409)
        self.assertEqual(c.post('/play/api/profile', json={'username':'Fake'}).status_code, 400)
        for invalid in ('', ' ', 'x'*65, 'a\nb', 5, []):
            self.assertEqual(self.name(c, invalid).status_code, 422)
        self.assertEqual(self.name(c, 'Real submitted name').status_code, 200)
        self.assertEqual(self.attack(c).status_code, 200)
        self.assertEqual(self.b.export()['total_attacks'], 1)

    def test_distinct_players_share_ip_and_names_survive_ip_changes(self):
        a, _ = self.client(name='Alice'); b, _ = self.client()
        self.assertEqual(self.name(b, 'Bob').status_code, 200)
        self.assertNotIn('Alice', b.get('/play/api/state').text)
        self.attack(a)
        a.environ_base['REMOTE_ADDR'] = '192.0.2.2'
        self.assertEqual(self.attack(a).status_code, 429)
        self.clock.return_value += 30
        self.assertEqual(a.get('/play/api/state').json['state']['you']['display_name'], 'Alice')
        self.assertTrue(a.get('/play/api/state').json['state']['you']['identity_ready'])
        self.assertEqual(self.attack(a).status_code, 200)
        self.assertEqual(self.name(b, 'Alice').status_code, 200)
        # Reusing a display label never inherits the first player's damage.
        self.assertEqual(b.get('/play/api/state').json['state']['you']['damage'], 0)
        self.assertEqual(a.get('/play/api/state').json['state']['you']['attacks'], 2)

    def test_profile_forgery_cannot_change_another_player_or_game_settings(self):
        a, _ = self.client(name='Alice'); b, _ = self.client('192.0.2.2')
        self.attack(a); before = self.b.export()
        response = self.name(b, 'Bob', guest='forged', player_id=next(iter(before['profiles'])), hp=0, damage=9999, role='admin')
        self.assertEqual(response.status_code, 200)
        after = self.b.export()
        for field in ('hp', 'players', 'total_damage', 'settings', 'networks'):
            self.assertEqual(after[field], before[field])
        self.assertEqual(next(iter(after['profiles'].values()))['name'], 'Alice')
        self.assertEqual(self.name(b, 'Other name').status_code, 429)

    def test_thirty_seconds_exact_and_no_daily_cap(self):
        c, _ = self.client(name='Unlimited')
        beginning = self.clock.return_value
        for i in range(101):
            self.clock.return_value = beginning + i*30
            self.assertEqual(self.attack(c).status_code, 200)
        saved = self.b.export()
        self.clock.return_value += 29.99
        blocked = self.attack(c)
        self.assertEqual(blocked.status_code, 429)
        self.assertEqual(blocked.headers['Retry-After'], '1')
        self.clock.return_value += .01
        self.assertEqual(self.attack(c).status_code, 200)
        self.assertEqual(saved['total_attacks'], 101)
        self.assertIsNone(c.get('/play/api/state').json['state']['rules']['daily_attacks'])

    def test_private_top_five_full_names_and_public_aliases(self):
        names = [f'FullName{i}' for i in range(7)]
        for i, name in enumerate(names):
            guest, ip = str(i), f'192.0.2.{i+1}'
            self.b.register(guest, ip, self.b.status()['raid_id'], name)
            for _ in range(i+1):
                self.core_hit(guest, ip); self.clock.return_value += 30
        anonymous, _ = self.client('198.51.100.1')
        self.assertEqual(anonymous.get('/admin/boss/status').status_code, 401)
        admin, _ = self.admin()
        response = admin.get('/admin/boss/status')
        self.assertEqual(response.headers['Cache-Control'], 'no-store')
        self.assertEqual([r['name'] for r in response.json['state']['admin_leaders']], names[-1:1:-1])
        for url in ('/play/api/state', '/play', '/public-state'):
            for name in names: self.assertNotIn(name, anonymous.get(url).text)
        self.r.admin['users']['helper'] = copy.deepcopy(self.r.admin['users']['gingrsnaps'])
        self.r.commit(self.r.admin, self.r.revision)
        with admin.session_transaction() as session: session['user'] = 'helper'
        self.assertEqual(admin.get('/admin/boss/status').status_code, 200)
        self.r.admin['users'].pop('helper'); self.r.commit(self.r.admin, self.r.revision)
        self.assertEqual(admin.get('/admin/boss/status').status_code, 401)

    def test_extreme_damage_zero_damage_and_explicit_hp_preserve_contributions(self):
        self.core_hit(); saved = self.b.export()
        self.b.control('health', saved['id'], 1, health_revision=0)
        s = self.b.export()
        self.assertEqual((s['hp'], s['max_hp'], s['total_damage']), (0, 1, 150))
        self.assertEqual(s['players'], saved['players'])
        self.b.control('health', s['id'], MAX_HP, health_revision=1)
        self.b.control('remaining_health', s['id'], MAX_HP, health_revision=2)
        self.b.configure(s['id'], dict(name='Flexible', damage=MAX_DAMAGE, weak_damage=0, burst_bonus=0), 0)
        self.clock.return_value += 30
        zero = self.core_hit()
        self.assertEqual(zero['hit']['damage'], 0)
        self.assertEqual(zero['state']['hp'], MAX_HP)
        validate_boss(self.b.export())
        self.b.control('remaining_health', s['id'], 5, health_revision=3)
        self.clock.return_value += 30
        v = self.b.status('a', '192.0.2.1')
        wrong = next(x for x in ('blade','bow','magic') if x != v['weakness'])
        self.assertEqual(self.core_hit(style=wrong)['hit']['damage'], 5)
        validate_boss(self.b.export())
        # Recovery metadata must handle the same numeric range as combat saves.
        self.b.control('restart', s['id'], MAX_HP)
        view = self.b.status('a', '192.0.2.1')
        wrong = next(x for x in ('blade','bow','magic') if x != view['weakness'])
        self.assertEqual(self.core_hit(style=wrong)['hit']['damage'], MAX_HP)
        admin, _ = self.admin()
        exported = admin.get('/admin/recovery-backup')
        self.assertEqual(exported.status_code, 200)
        self.assertEqual(exported.json['recovery_export']['damage'], MAX_HP)
        self.assertFalse(admin.get('/admin/status').json['checkpoint']['changes'])


    def test_random_weakness_is_shared_and_stable_without_writes(self):
        saved = self.b.export(); samples = []
        for i in range(60):
            self.clock.return_value += 600
            first = self.b.status('a', '192.0.2.1')['weakness']
            other = CommunityBoss(self.r.store).status('b', '192.0.2.2')['weakness']
            self.assertEqual(first, other); samples.append(first)
        self.assertEqual(set(samples), {'blade','bow','magic'})
        self.assertTrue(any(a == b for a,b in zip(samples, samples[1:])))
        self.assertEqual(saved, self.b.export())

    def test_eight_achievements_take_a_week_and_survive_new_raids(self):
        start = self.clock.return_value
        self.b.register('a', '192.0.2.1', self.b.status()['raid_id'], 'WeekPlayer')
        for day in range(7):
            if day == 3:
                self.b.control('restart', self.b.status()['raid_id'])
            for hit in range(75):
                self.clock.return_value = start + day*DAY + hit*30
                self.core_hit(style=('blade','bow','magic')[hit%3] if day == 0 else None)
            view = self.b.status('a', '192.0.2.1')
            if day < 6:
                self.assertFalse(next(b for b in view['you']['badges'] if b['id'] == 'week')['earned'])
        self.assertEqual(len(view['you']['badges']), 8)
        self.assertTrue(all(b['earned'] for b in view['you']['badges']))
        before = self.b.export()
        self.assertEqual(CommunityBoss(self.r.store).export(), before)
        self.b.control('restart', view['raid_id'])
        self.assertEqual(self.b.status('a', '192.0.2.1')['you']['badges'], view['you']['badges'])
        self.assertEqual(self.b.status()['total_damage'], 0)

    def test_legacy_save_migrates_additively_without_changing_hp(self):
        self.core_hit(); old = self.b.export()
        old.pop('profiles', None); old.pop('health_adjustment', None)
        for p in old['players'].values(): p['used'] = 40
        for p in old['networks'].values(): p['used'] = 40
        with self.r.store.connection(transaction=True) as conn: self.b._write(conn, old)
        self.b = CommunityBoss(self.r.store)
        self.assertEqual(self.b.export(), old)
        self.b.register('a', '192.0.2.1', old['id'], 'Returning player')
        self.assertEqual(self.b.export()['players'], old['players'])
        self.clock.return_value += 30
        self.assertEqual(self.core_hit()['state']['total_attacks'], 2)
        validate_boss(self.b.export())

    def test_profile_and_health_recovery_are_portable_and_reject_tampering(self):
        c, _ = self.client(name='RecoveryPlayer'); self.attack(c)
        saved = self.b.export()
        self.b.control('remaining_health', saved['id'], 17, health_revision=0)
        admin, _ = self.admin(); recovery = admin.get('/admin/recovery-backup').json
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory); (root/'private').mkdir()
            (root/'private/recovery.seed.json').write_text(json.dumps(recovery), encoding='utf-8')
            restored = create_app(root, testing=True)
            try: self.assertEqual(restored.extensions['boss'].export(), self.b.export())
            finally: restored.extensions['runtime'].store.close()
        bad = self.b.export(); next(iter(bad['profiles'].values()))['weak_hits'] = 99999
        with self.assertRaises(ValueError): validate_boss(bad)

    def test_connection_release_and_remaining_hp_are_admin_only(self):
        player, _ = self.client(name='Claimed')
        current = self.b.status(); admin, csrf = self.admin()
        form = dict(csrf=csrf, raid_id=current['raid_id'], action='release_player', player_name='Claimed', confirm_release='yes')
        self.assertEqual(player.post('/admin/boss/action', data=form).status_code, 302)
        self.assertEqual(admin.post('/admin/boss/action', data={**form,'csrf':'wrong'}).status_code, 400)
        self.assertEqual(admin.post('/admin/boss/action', data=form).status_code, 422)
        replacement, _ = self.client()
        self.assertEqual(self.name(replacement, 'Replacement').status_code, 200)
        self.assertEqual(self.attack(player).status_code, 200)
        hpform = dict(csrf=csrf, raid_id=current['raid_id'], action='remaining_health', health='0', health_revision='0', confirm_health='yes')
        self.assertEqual(admin.post('/admin/boss/action', data=hpform).status_code, 303)
        self.assertEqual(self.b.status()['hp'], 0)
        self.assertEqual(self.b.status()['status'], 'victory')


if __name__ == '__main__': unittest.main()
