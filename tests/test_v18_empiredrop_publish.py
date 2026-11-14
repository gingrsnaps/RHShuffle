import unittest
from pathlib import Path

from empiredrop_features import resolve_reward_save_mode

ROOT = Path(__file__).resolve().parents[1]


class V18EmpireDropPublishTests(unittest.TestCase):
    def test_javascript_override_wins_when_submit_button_is_disabled(self):
        self.assertEqual(
            resolve_reward_save_mode({'save_mode_intent': 'publish'}),
            'publish',
        )

    def test_native_button_remains_no_javascript_fallback(self):
        self.assertEqual(
            resolve_reward_save_mode({'save_mode': 'publish'}),
            'publish',
        )
        self.assertEqual(
            resolve_reward_save_mode({'save_mode': 'draft'}),
            'draft',
        )

    def test_override_has_priority_over_missing_or_stale_button_value(self):
        self.assertEqual(
            resolve_reward_save_mode({
                'save_mode_intent': 'publish',
                'save_mode': 'draft',
            }),
            'publish',
        )

    def test_invalid_intent_is_rejected(self):
        with self.assertRaises(ValueError):
            resolve_reward_save_mode({'save_mode_intent': 'delete'})

    def test_bundled_public_schedule_matches_confirmed_admin_values(self):
        import json
        from empiredrop_features import rewards_public
        state = json.loads((ROOT / 'data' / 'state.json').read_text(encoding='utf-8'))
        rewards = rewards_public(state['admin']['empiredrop_rewards'])
        self.assertTrue(rewards['enabled'])
        self.assertEqual(rewards['currency'], 'USD')
        self.assertEqual(rewards['total'], '$2,000.00')
        self.assertEqual(rewards['formatted']['1'], '$1,000.00')
        self.assertEqual(rewards['formatted']['10'], '$25.00')

    def test_form_contains_durable_publish_intent(self):
        template = (ROOT / 'templates' / 'admin_empiredrop.html').read_text(encoding='utf-8')
        script = (ROOT / 'static' / 'admin-empiredrop.js').read_text(encoding='utf-8')
        backend = (ROOT / 'wager_backend.py').read_text(encoding='utf-8')
        self.assertIn('name="save_mode_intent"', template)
        self.assertIn("intent.value = mode", script)
        self.assertIn('mode = resolve_reward_save_mode(request.form)', backend)


if __name__ == '__main__':
    unittest.main()
