"""Anonymous fast updates and server-confirmed admin receipts."""
import unittest
import test_app
from unittest.mock import patch


class GuiUpdateTests(unittest.TestCase):
    setUp = test_app.AppTests.setUp

    def test_summary_is_anonymous_private_fields_absent_and_provider_free(self):
        guest = self.app.test_client()
        with patch.object(self.r.providers, 'shuffle', side_effect=AssertionError('No provider call')):
            response = guest.get('/boss-summary')
        self.assertEqual(response.status_code, 200)
        self.assertNotIn('Set-Cookie', response.headers)
        self.assertIn('no-store', response.headers['Cache-Control'])
        self.assertIn('health_revision', response.json['boss'])
        for key in ('you', 'csrf', 'admin_leaders', 'profiles', 'players', 'username', 'pw_hash'):
            self.assertNotIn(key, response.json['boss'])

    def test_native_override_has_receipt_beside_control_and_exact_accepted_value(self):
        response = self.client.post('/admin/action', data={
            'csrf':'test-token', 'action':'override', 'tab':'players',
            'revision':self.r.revision, 'username':'Example', 'amount':'1234.56'})
        self.assertEqual(response.status_code, 303)
        self.assertTrue(response.location.endswith('#feedback-override'))
        page = self.client.get(response.location).text
        self.assertIn('id="feedback-override"', page)
        self.assertIn('Override saved for Example: $1,234.56', page)
        self.assertNotIn('id="feedback-override"', self.client.get('/admin?tab=players').text)

    def test_json_invalid_write_is_specific_and_does_not_commit(self):
        before = self.r.revision
        response = self.client.post('/admin/action', data={
            'csrf':'test-token', 'action':'override', 'tab':'players',
            'revision':before, 'username':'Example', 'amount':'bad'}, headers={'Accept':'application/json'})
        self.assertEqual(response.status_code, 422)
        self.assertIn('non-negative amount', response.json['error'])
        self.assertEqual(self.r.revision, before)

    def test_json_boss_save_has_confirmed_values_and_native_receipt(self):
        state = self.client.get('/admin/boss/status').json['state']
        response = self.client.post('/admin/boss/action', data={
            'csrf':'test-token', 'action':'settings', 'raid_id':state['raid_id'],
            'settings_revision':state['settings_revision'], 'boss_name':'Ruby <boss>',
            'base_damage':'234', 'weak_damage':'456', 'burst_bonus':'78'}, headers={'Accept':'application/json'})
        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.json['ok'])
        self.assertIn('base: 234', response.json['message'])
        page = self.client.get(response.json['redirect']).text
        self.assertIn('id="feedback-bossSettingsHeading"', page)
        self.assertIn('Ruby &lt;boss&gt;', page)
        self.assertNotIn('Ruby <boss>', page)

    def test_failed_boss_save_is_json_and_preserves_original_state(self):
        state = self.client.get('/admin/boss/status').json['state']
        response = self.client.post('/admin/boss/action', data={
            'csrf':'test-token', 'action':'remaining_health', 'raid_id':state['raid_id'],
            'health_revision':state['health_revision'], 'health':'100'}, headers={'Accept':'application/json'})
        self.assertEqual(response.status_code, 422)
        self.assertIn('Confirm', response.json['error'])
        self.assertEqual(self.client.get('/admin/boss/status').json['state']['hp'], state['hp'])

    def test_masked_latest_hit_and_health_notice_never_expose_admin_identity(self):
        player=self.app.test_client();opening=player.get('/play/api/state').json
        token=opening['player_csrf']
        player.post('/play/api/profile',json={'username':'VisibleToAdminsOnly','raid_id':opening['state']['raid_id']},headers={'X-CSRF-Token':token})
        response=player.post('/play/api/attack',json={'raid_id':opening['state']['raid_id'],'request_id':'test-latest-hit','style':'blade'},headers={'X-CSRF-Token':token})
        self.assertEqual(response.status_code,200)
        boss=self.app.extensions['boss'];current=boss.summary()
        boss.control('remaining_health',current['raid_id'],current['max_hp'],health_revision=current['health_revision'],actor='SecretAdmin')
        public=self.app.test_client().get('/boss-summary')
        self.assertEqual(public.json['boss']['latest_hit']['name'],'Vi******')
        self.assertIsNotNone(public.json['boss']['health_change'])
        self.assertNotIn('VisibleToAdminsOnly',public.text)
        self.assertNotIn('SecretAdmin',public.text)
