"""Regressions for community polish, reviewed publication and recovery metadata."""
import copy
import io
import json
from pathlib import Path
import re
import secrets
import tempfile
import unittest
from unittest.mock import patch

import test_app as support
from boss import CommunityBoss, DAY, fresh_raid, validate_boss
from wager_backend import create_app


class CommunityTests(unittest.TestCase):
    setUp = support.AppTests.setUp
    form = support.AppTests.form
    schedule = support.AppTests.schedule

    def hit(self, guest='community-test', ip='192.0.2.9'):
        boss = self.app.extensions['boss']
        state = boss.status(guest, ip)
        return boss.attack(guest, ip, state['weakness'], state['raid_id'], secrets.token_hex(16))

    def test_conditional_public_snapshot_and_private_cache_boundaries(self):
        first = self.client.get('/public-state')
        self.assertEqual(first.status_code, 200)
        self.assertEqual(first.headers['Cache-Control'], 'public, no-cache')
        self.assertNotIn('server_time', first.json)
        self.assertNotIn('you', first.json['boss'])
        self.assertNotIn('csrf', first.json)
        with patch('runtime.time.time', return_value=float(first.headers['X-Server-Time']) + 1):
            unchanged = self.client.get('/public-state', headers={'If-None-Match': first.headers['ETag']})
        self.assertEqual(unchanged.status_code, 304)
        self.assertEqual(unchanged.data, b'')
        self.assertGreater(float(unchanged.headers['X-Server-Time']), float(first.headers['X-Server-Time']))
        self.hit()
        changed = self.client.get('/public-state', headers={'If-None-Match': first.headers['ETag']})
        self.assertEqual(changed.status_code, 200)
        self.assertNotEqual(first.headers['ETag'], changed.headers['ETag'])
        for url in ('/play/api/state', '/admin/status', '/admin/recovery-backup'):
            response = self.client.get(url)
            self.assertEqual(response.headers['Cache-Control'], 'no-store')
            self.assertNotIn('ETag', response.headers)

    def test_review_signature_requires_the_exact_reviewed_changes(self):
        self.schedule()
        original = copy.deepcopy(self.r.admin)
        revision = self.r.revision
        form = dict(self.form(), csrf='test-token', action='save_race', revision=revision,
                    race_title='The new community race', prize_1='1801', sponsor_url='https://example.test/sponsor')
        preview = self.client.post('/admin/action', data=form)
        self.assertEqual(preview.status_code, 200)
        for label in ('Race title', 'Place 1 prize', 'Sponsor link'):
            self.assertIn(label, preview.text)
        review = re.search('name="review_token" value="([^"]+)"', preview.text).group(1)
        tampered = self.client.post('/admin/action', data={**form, 'confirm_race':'yes', 'review_token':review, 'prize_1':'1901'})
        self.assertEqual(tampered.status_code, 200)
        self.assertEqual(self.r.revision, revision)
        self.assertEqual(self.r.admin, original)
        confirmed = self.client.post('/admin/action', data={**form, 'confirm_race':'yes', 'review_token':review})
        self.assertEqual(confirmed.status_code, 303)
        self.assertEqual(self.r.revision, revision + 1)
        self.assertEqual(self.r.admin['site_settings']['prizes']['1'], '1801')

    def test_badges_reward_real_hits_and_distinct_raid_days(self):
        boss = self.app.extensions['boss']
        with patch('boss.time.time', return_value=1_800_000_000) as clock:
            for hit in range(100):
                clock.return_value = 1_800_000_000 + (hit // 40) * DAY + (hit % 40) * 60
                result = self.hit()
            state = result['state']
            self.assertEqual(state['you']['active_days'], 3)
            self.assertEqual(state['you']['attacks'], 100)
            self.assertTrue(all(badge['earned'] for badge in state['you']['badges']))
            self.assertEqual(state['total_damage'], 16_000)
            self.assertEqual(state['rules']['daily_attacks'], 40)
        validate_boss(boss.export())

    def test_legacy_raid_migration_keeps_progress_and_counts_only_known_days(self):
        boss = self.app.extensions['boss']
        with patch('boss.time.time', return_value=1_800_000_000) as clock:
            self.hit()
            old = boss.export()
            for player in old['players'].values():
                player.pop('active_days')
            with self.r.store.connection(transaction=True) as conn:
                boss._write(conn, old)
            restored = CommunityBoss(self.r.store)
            self.assertEqual(restored.export(), old)
            self.app.extensions['boss'] = restored
            clock.return_value += DAY
            state = self.hit()['state']
            self.assertEqual(state['you']['active_days'], 2)
            self.assertEqual(state['you']['damage'], 300)
            self.assertFalse(next(b for b in state['you']['badges'] if b['id'] == 'loyal')['earned'])

    def test_milestones_and_victory_recap_include_every_contributor(self):
        boss = self.app.extensions['boss']
        raid = fresh_raid(health=1650)
        with self.r.store.connection(transaction=True) as conn:
            boss._write(conn, raid, new_raid=True)
        boss.loaded_at = 0
        url = '/play/api/contributors?raid_id=' + raid['id']
        self.assertEqual(self.client.get(url).status_code, 409)
        for index in range(11):
            state = self.hit(str(index), f'192.0.2.{index + 1}')['state']
            if index == 2:
                self.assertEqual([m['percent'] for m in state['milestones'] if m['reached']], [25])
        self.assertTrue(all(m['reached'] for m in state['milestones']))
        result = self.client.get(url)
        self.assertEqual(result.status_code, 200)
        self.assertEqual(len(result.json['contributors']), 11)
        self.assertTrue(all(set(row) == {'name', 'damage', 'attacks'} for row in result.json['contributors']))
        self.assertEqual(self.client.get('/play/api/contributors?raid_id=old-raid').status_code, 409)

    def test_recovery_export_tracks_changes_without_invalidating_admin_forms(self):
        before = self.r.store.admin()
        recovery = self.client.get('/admin/recovery-backup').json
        self.assertEqual(self.r.store.admin(), before)
        self.assertEqual(self.r.store.checkpoint(), recovery['recovery_export'])
        self.assertFalse(self.client.get('/admin/status').json['checkpoint']['changes'])
        self.hit()
        status = self.client.get('/admin/status').json['checkpoint']
        self.assertEqual(status['attacks'], 1)
        self.assertEqual(status['damage'], 150)
        self.assertTrue(status['changes'])

    def test_private_recovery_review_validates_without_changing_live_state(self):
        self.hit()
        recovery = self.client.get('/admin/recovery-backup').json
        before = self.r.store.admin(), self.app.extensions['boss'].export()
        response = self.client.post('/admin/recovery-preview', data={
            'csrf':'test-token', 'recovery':(io.BytesIO(json.dumps(recovery).encode()), 'recovery.json')})
        self.assertEqual(response.status_code, 200)
        self.assertIn('Validated recovery file', response.text)
        self.assertIn('1 raiders', response.text)
        self.assertNotIn(recovery['users']['gingrsnaps']['pw_hash'], response.text)
        self.assertEqual((self.r.store.admin(), self.app.extensions['boss'].export()), before)
        invalid = self.client.post('/admin/recovery-preview', data={
            'csrf':'test-token', 'recovery':(io.BytesIO(b'{bad json'), 'bad.json')})
        self.assertEqual(invalid.status_code, 422)
        self.assertEqual(self.client.post('/admin/recovery-preview').status_code, 400)
        self.assertEqual(self.app.test_client().post('/admin/recovery-preview').status_code, 302)

    def test_recovered_metadata_survives_import_and_malformed_metadata_is_ignored(self):
        self.hit()
        recovery = self.client.get('/admin/recovery-backup').json
        for malformed in (False, True):
            with self.subTest(malformed=malformed), tempfile.TemporaryDirectory() as directory:
                value = copy.deepcopy(recovery)
                if malformed:
                    value['recovery_export']['attacks'] = 'untrusted number'
                root = Path(directory)
                (root / 'private').mkdir()
                (root / 'private/recovery.seed.json').write_text(json.dumps(value), encoding='utf-8')
                restored = create_app(root, testing=True)
                try:
                    store = restored.extensions['runtime'].store
                    self.assertEqual(restored.extensions['boss'].export(), recovery['community_boss'])
                    self.assertEqual(store.checkpoint(), None if malformed else recovery['recovery_export'])
                finally:
                    restored.extensions['runtime'].store.close()


if __name__ == '__main__':
    unittest.main()
