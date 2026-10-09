"""Partial boss edits and lean status feeds must preserve existing gameplay."""
import unittest
from unittest.mock import patch
import test_app


class ClarityUpdateTests(unittest.TestCase):
    setUp = test_app.AppTests.setUp

    def edit(self, action, **fields):
        state = self.app.extensions['boss'].status()
        data = dict(action=action, csrf='test-token', raid_id=state['raid_id'],
                    settings_revision=state['settings_revision'], **fields)
        return self.client.post('/admin/boss/action', data=data, headers={'Accept':'application/json'})

    def test_separate_name_and_damage_preserve_hp_and_unrelated_settings(self):
        boss = self.app.extensions['boss']
        state = boss.status()
        boss.control('remaining_health', state['raid_id'], 12345, health_revision=state['health_revision'])
        before = boss.export()
        # Ignore unrelated extra fields: an appearance save cannot smuggle in HP/damage changes.
        response = self.edit('name', boss_name='Ruby Prime', health=1, base_damage=999)
        self.assertEqual(response.status_code, 200)
        self.assertIn('bossNameHeading', response.json['redirect'])
        current = boss.export()
        self.assertEqual(current['settings']['name'], 'Ruby Prime')
        for field in ['damage', 'weak_damage', 'burst_bonus']:
            self.assertEqual(current['settings'][field], before['settings'][field])
        for field in ['hp', 'max_hp', 'total_attacks', 'total_damage', 'players']:
            self.assertEqual(current[field], before[field])
        response = self.edit('damage', base_damage=123, weak_damage=456, burst_bonus=78, boss_name='Ignore me')
        self.assertEqual(response.status_code, 200)
        current = boss.export()
        self.assertEqual(current['settings'], dict(name='Ruby Prime', damage=123, weak_damage=456, burst_bonus=78))
        self.assertEqual(current['hp'], 12345)
        self.assertEqual(current['total_damage'], before['total_damage'])

    def test_stale_invalid_or_unauthorized_partial_edits_do_not_commit(self):
        boss = self.app.extensions['boss']
        old = boss.status()
        self.assertEqual(self.edit('name', boss_name='Saved').status_code, 200)
        before = boss.export()
        body = dict(action='damage', csrf='test-token', raid_id=old['raid_id'],
                    settings_revision=old['settings_revision'], base_damage=8, weak_damage=9, burst_bonus=10)
        response = self.client.post('/admin/boss/action', data=body, headers={'Accept':'application/json'})
        self.assertEqual(response.status_code, 422)
        self.assertIn('Another admin', response.json['error'])
        self.assertEqual(self.edit('name', boss_name=' ').status_code, 422)
        self.assertEqual(self.edit('damage', base_damage=-1, weak_damage=1, burst_bonus=1).status_code, 422)
        anonymous = self.app.test_client()
        self.assertEqual(anonymous.post('/admin/boss/action', data=body, headers={'Accept':'application/json'}).status_code, 401)
        body['csrf'] = 'invalid'
        self.assertEqual(self.client.post('/admin/boss/action', data=body, headers={'Accept':'application/json'}).status_code, 400)
        self.assertEqual(boss.export(), before)

    def test_minute_feed_omits_duplicate_rankings_and_local_feed_is_conditional(self):
        gaming = self.app.extensions['gaming']
        with patch.object(gaming, 'leaders', side_effect=AssertionError('Duplicate rankings read')):
            response = self.client.get('/admin/status?tab=overview&gaming=0')
        self.assertEqual(response.status_code, 200)
        self.assertNotIn('gaming', response.json)
        self.assertNotIn('participants', response.json)
        self.assertIn('boss', response.json)
        full = self.client.get('/admin/status')
        self.assertIn('gaming', full.json)
        response = self.client.get('/admin/gaming/status')
        self.assertIn('boss', response.json)
        cached = self.client.get('/admin/gaming/status', headers={'If-None-Match':response.headers['ETag']})
        self.assertEqual(cached.status_code, 304)
        self.assertEqual(self.app.test_client().get('/admin/gaming/status').status_code, 401)
