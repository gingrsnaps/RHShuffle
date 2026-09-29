"""Behavioral checks for player recovery, file durability and uncapped fairness."""
import copy
import hashlib
import json
import os
from pathlib import Path
import secrets
import sqlite3
import tempfile
import threading
import unittest
from unittest.mock import patch

from boss import CommunityBoss, BossError, validate_boss
from config import Config
from storage import Store, StoreError
from wager_backend import create_app


class ComfortTests(unittest.TestCase):
    def setUp(self):
        temp = tempfile.TemporaryDirectory(); self.addCleanup(temp.cleanup)
        self.root = Path(temp.name)
        env = patch.dict(os.environ, {'APP_ENV':'test', 'ADMIN_BOOTSTRAP_PASS':'test-password'}, clear=True)
        env.start(); self.addCleanup(env.stop)
        self.app = create_app(self.root, testing=True)
        self.r, self.b = self.app.extensions['runtime'], self.app.extensions['boss']
        clock = patch('boss.time.time', return_value=self.b.export()['created_at'] + 1.25)
        self.clock = clock.start(); self.addCleanup(clock.stop)

    def player(self, name=None, ip='192.0.2.1'):
        c = self.app.test_client(); c.environ_base['REMOTE_ADDR'] = ip
        v = c.get('/play/api/state').json
        if name: self.assertEqual(self.post(c, '/play/api/profile', username=name).status_code, 200)
        return c

    def post(self, c, path, **body):
        v = c.get('/play/api/state').json
        return c.post(path, json={'raid_id': v['state']['raid_id'], **body}, headers={'X-CSRF-Token': v['csrf']})

    def hit(self, c):
        v = c.get('/play/api/state').json
        return self.post(c, '/play/api/attack', style=v['state']['weakness'], request_id=secrets.token_hex(16))

    def admin(self):
        c = self.player(ip='198.51.100.1')
        with c.session_transaction() as s: s.update(user='gingrsnaps', auth_version=1)
        return c

    def action(self, c, action, **fields):
        v = c.get('/play/api/state').json
        return c.post('/admin/boss/action', data={'csrf':v['csrf'], 'raid_id':v['state']['raid_id'], 'action':action, **fields})

    def test_json_is_the_only_active_store_and_survives_restart(self):
        c = self.player('Alice'); self.hit(c)
        value = self.b.export(); before = self.r.store.admin()
        self.assertTrue((self.root/'data/state.json').is_file())
        self.assertFalse(list(self.root.rglob('*.sqlite3')))
        again = Store(Config(self.root))
        self.assertEqual(again.admin(), before)
        self.assertEqual(CommunityBoss(again).export(), value)
        self.assertEqual(json.loads((self.root/'data/state.json').read_text())['boss']['hp'], value['hp'])

    def test_failed_file_replace_rolls_back_in_memory_and_on_disk(self):
        c = self.player('Alice'); before = self.b.export(); disk = (self.root/'data/state.json').read_bytes()
        with patch('storage.os.replace', side_effect=OSError('fixture disk error')):
            response = self.hit(c)
        self.assertEqual(response.status_code, 503)
        self.assertEqual((self.root/'data/state.json').read_bytes(), disk)
        self.assertEqual(self.b.export(), before)
        self.assertFalse(list((self.root/'data').glob('*.tmp')))
        self.assertEqual(self.hit(c).status_code, 200)

    def test_corrupt_saved_json_never_resets_accounts(self):
        path = self.root/'data/state.json'; path.write_text('{broken', encoding='utf-8')
        with self.assertRaises(RuntimeError): Store(Config(self.root))
        self.assertEqual(path.read_text(), '{broken')

    def test_sqlite_migration_preserves_entire_saved_state_and_original_file(self):
        c = self.player('Alice'); self.hit(c)
        old = self.b.export(); admin = self.r.store.admin()
        target = self.root/'old-install'; (target/'data').mkdir(parents=True)
        path = target/'data/redhunllef.sqlite3'
        with sqlite3.connect(path) as db:
            db.execute('CREATE TABLE rh_admin (name TEXT, revision INTEGER, document TEXT)')
            db.execute('CREATE TABLE rh_live (name TEXT, service TEXT, document TEXT)')
            db.execute('CREATE TABLE rh_boss (name TEXT, document TEXT)')
            db.execute('INSERT INTO rh_admin VALUES (?, ?, ?)', ('redhunllef', admin[0], json.dumps(admin[1])))
            db.execute('INSERT INTO rh_live VALUES (?, ?, ?)', ('redhunllef', 'shuffle', json.dumps(self.r.shuffle)))
            db.execute('INSERT INTO rh_boss VALUES (?, ?)', ('redhunllef', json.dumps(old)))
        original = path.read_bytes()
        migrated = Store(Config(target))
        self.assertEqual(migrated.admin(), admin)
        self.assertEqual(CommunityBoss(migrated).export(), old)
        self.assertEqual(migrated.live('shuffle'), self.r.shuffle)
        self.assertEqual(path.read_bytes(), original)
        self.assertTrue((target/'data/state.json').exists())

    def test_two_store_instances_do_not_lose_concurrent_damage(self):
        other = CommunityBoss(Store(Config(self.root)))
        raid = self.b.status()['raid_id']; errors = []
        def attack(i):
            try: (self.b if i % 2 else other).attack(str(i), f'192.0.2.{i+1}', 'blade', raid, secrets.token_hex(16))
            except Exception as exc: errors.append(exc)
        workers = [threading.Thread(target=attack, args=(i,)) for i in range(12)]
        for t in workers: t.start()
        for t in workers: t.join(10)
        self.assertFalse(errors)
        state = self.b.export()
        self.assertEqual(state['total_attacks'], 12)
        validate_boss(state)

    def test_owner_recovery_retains_cookie_identity_receipts_and_badges(self):
        a = self.player('Alice'); hit = self.hit(a).json
        code_response = self.post(a, '/play/api/recovery-code')
        self.assertEqual(code_response.status_code, 200)
        code = code_response.json['code']
        disk = (self.root/'data/state.json').read_text()
        self.assertNotIn(code, disk)
        b = self.player(); recovered = self.post(b, '/play/api/recover', code=code)
        self.assertEqual(recovered.status_code, 200)
        you = recovered.json['state']['you']
        self.assertEqual(you['name'], hit['state']['you']['name'])
        self.assertEqual(you['damage'], hit['hit']['damage'])
        self.assertEqual(you['badges'], hit['state']['you']['badges'])
        self.assertEqual(self.hit(b).status_code, 429)
        self.clock.return_value += 30
        self.assertEqual(self.hit(b).status_code, 200)
        self.assertEqual(len(self.b.export()['players']), 1)
        public = self.player(ip='192.0.2.8').get('/play/api/state').text
        self.assertNotIn('Alice', public); self.assertNotIn('recovery_hash', public)
        with self.assertRaises(BossError): self.b.save_recovery('other', hashlib.sha256(b'bad').hexdigest())

    def test_recovery_rotation_forgery_csrf_and_other_connections(self):
        a = self.player('Alice'); code = self.post(a, '/play/api/recovery-code').json['code']
        self.assertEqual(a.post('/play/api/recovery-code').status_code, 400)
        b = self.player(ip='192.0.2.2')
        self.assertEqual(self.post(b, '/play/api/recover', code=code+'x').status_code, 400)
        self.clock.return_value += 30
        new = self.post(a, '/play/api/recovery-code').json['code']
        self.assertEqual(self.post(b, '/play/api/recover', code=code).status_code, 400)
        self.assertEqual(self.post(b, '/play/api/recover', code=new).status_code, 200)
        self.assertEqual(b.get('/play/api/state').json['state']['you']['display_name'], 'Alice')

    def test_household_approval_is_private_and_retains_per_player_cooldowns(self):
        a = self.player('Alice'); b = self.player(); host = self.admin()
        self.assertEqual(self.post(b, '/play/api/profile', username='Bob').status_code, 409)
        self.assertEqual(self.action(b, 'household', player_name='Alice', slots='2').status_code, 302)
        self.assertEqual(self.action(host, 'household', player_name='Alice', slots='2').status_code, 303)
        self.assertEqual(self.post(b, '/play/api/profile', username='Bob').status_code, 200)
        self.assertEqual(self.hit(a).status_code, 200); self.assertEqual(self.hit(b).status_code, 200)
        self.assertEqual(self.hit(a).status_code, 429); self.assertEqual(self.hit(b).status_code, 429)
        c = self.player(); self.assertEqual(self.post(c, '/play/api/profile', username='Charlie').status_code, 409)
        self.assertEqual(self.action(host, 'household', player_name='Alice', slots='1').status_code, 422)
        validate_boss(self.b.export())
        public = c.get('/play/api/state').text
        for secret in ('Alice', 'Bob', 'households', 'admin_history'): self.assertNotIn(secret, public)
        self.clock.return_value += 30
        self.assertEqual(self.hit(a).status_code, 200); self.assertEqual(self.hit(b).status_code, 200)

    def test_rejected_flood_is_throttled_but_eligible_hits_are_never_capped(self):
        c = self.player('Alice'); self.hit(c)
        for _ in range(13): last = self.hit(c)
        self.assertEqual(last.status_code, 429)
        self.assertEqual(last.json['code'], 'request_throttle')
        host = self.admin(); flags = host.get('/admin/boss/status').json['state']['abuse_flags']
        self.assertEqual(len(flags), 1)
        self.assertEqual(flags[0]['category'], 'attack')
        self.assertNotIn('192.0.2.1', json.dumps(flags))
        self.clock.return_value += 30
        self.assertEqual(self.hit(c).status_code, 200)  # Still inside the abuse window.
        for _ in range(120):
            self.clock.return_value += 30
            self.assertEqual(self.hit(c).status_code, 200)
        self.assertIsNone(c.get('/play/api/state').json['state']['rules']['daily_attacks'])
        self.assertNotIn('abuse_flags', c.get('/play/api/state').text)

    def test_rapid_registration_rejections_throttle_without_banning(self):
        c = self.player()
        for _ in range(21): response = self.post(c, '/play/api/profile', username='')
        self.assertEqual(response.status_code, 429)
        self.assertEqual(response.json['code'], 'request_throttle')
        self.assertEqual(self.r.admin['banned_ips'], [])

    def test_rally_counts_distinct_recent_players_and_changes_no_combat_rules(self):
        raid = self.b.status()['raid_id']; start = self.clock.return_value
        for i in range(14): self.b.attack(str(i), f'192.0.2.{i+1}', 'blade', raid, secrets.token_hex(16))
        self.assertEqual(self.b.status()['rally']['count'], 14)
        self.clock.return_value += 30
        self.b.attack('0', '192.0.2.1', 'blade', raid, secrets.token_hex(16))
        self.assertFalse(self.b.status()['rally']['unlocked'])
        self.b.attack('last', '192.0.2.99', 'blade', raid, secrets.token_hex(16))
        v = self.b.status(); self.assertTrue(v['rally']['unlocked']); hp = v['hp']
        self.clock.return_value = start + 86400
        self.assertTrue(self.b.status()['rally']['unlocked']); self.assertEqual(self.b.status()['hp'], hp)
        self.assertEqual(v['rules']['damage'], 100)
        self.b.control('restart', raid)
        self.assertFalse(self.b.status()['rally']['unlocked'])

    def test_rally_expiry_and_admin_pace_do_not_adjust_health(self):
        raid = self.b.status()['raid_id']
        for i in range(11):
            self.b.attack(str(i), f'192.0.2.{i+1}', 'blade', raid, secrets.token_hex(16))
            self.clock.return_value += 30
        old = self.b.export(); view = self.b.admin_status()
        self.assertTrue(view['balance']['observed'])
        self.assertEqual([p['days'] for p in view['balance']['presets']], [3,5,7])
        self.assertEqual(self.b.export(), old)
        self.clock.return_value += 601
        self.assertEqual(self.b.status()['rally']['count'], 0)
        self.assertEqual(self.b.status()['hp'], old['hp'])

    def test_admin_history_is_atomic_persistent_and_not_public(self):
        host = self.admin(); player = self.player('Alice')
        self.assertEqual(self.action(host, 'settings', settings_revision=0, boss_name='Ruby', base_damage=12, weak_damage=23, burst_bonus=34).status_code, 303)
        self.assertEqual(self.action(host, 'remaining_health', health=12345, health_revision=0, confirm_health='yes').status_code, 303)
        records = self.b.admin_status()['admin_history']
        self.assertEqual(records[0]['actor'], 'gingrsnaps'); self.assertEqual(records[0]['after']['hp'], 12345)
        self.assertEqual(records[1]['after']['name'], 'Ruby')
        self.assertEqual(CommunityBoss(Store(Config(self.root))).admin_status()['admin_history'], records)
        self.assertNotIn('admin_history', player.get('/play/api/state').text)
        self.assertEqual(self.action(player, 'pause').status_code, 302)
        self.assertEqual(self.b.admin_status()['admin_history'], records)
        validate_boss(self.b.export())

    def test_source_checks_and_content_changes_have_separate_times(self):
        from race import empty
        now = int(self.clock.return_value)
        admin = copy.deepcopy(self.r.admin); admin['site_settings'].update(start_time=now-100, end_time=now+10000)
        self.r.commit(admin, self.r.revision, snapshot=empty(admin['site_settings']))
        rows = [dict(username='Test', weightedWagerAmount='100', wagerAmount='150', campaignCode='Red')]
        with patch.object(self.r.providers, 'shuffle', return_value=rows): self.r.check('shuffle')
        first = self.r.job_status()['shuffle']
        self.clock.return_value += 60
        with patch.object(self.r.providers, 'shuffle', return_value=rows): self.r.check('shuffle')
        second = self.r.job_status()['shuffle']
        self.assertGreater(second['last_success'], first['last_success'])
        self.assertEqual(second['changed_at'], first['changed_at'])
        rows[0]['weightedWagerAmount'] = '200'; self.clock.return_value += 60
        with patch.object(self.r.providers, 'shuffle', return_value=rows): self.r.check('shuffle')
        self.assertGreater(self.r.job_status()['shuffle']['changed_at'], first['changed_at'])


if __name__ == '__main__': unittest.main()
