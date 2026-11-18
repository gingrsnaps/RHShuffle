import time
import unittest
from pathlib import Path
import sys
import types

# This focused test does not need Werkzeug; stub the one storage import so the
# runtime helper can be exercised in dependency-light CI.
if 'werkzeug.security' not in sys.modules:
    werkzeug = types.ModuleType('werkzeug')
    security = types.ModuleType('werkzeug.security')
    security.generate_password_hash = lambda value: 'test-hash'
    werkzeug.security = security
    sys.modules.setdefault('werkzeug', werkzeug)
    sys.modules.setdefault('werkzeug.security', security)

from config import RELEASE, RANK_MOVEMENT_SECONDS, INTERVAL, KICK_INTERVAL
from movement import public_movement_event
from runtime import Runtime
from empiredrop import attach_rank_movement


def shuffle_row(rank, name, amount):
    return {
        'rank': rank,
        'username': name,
        'wager': f'${amount:.2f}',
        'weighted_wager': str(amount),
        'raw_wager': str(amount),
        'raw_wager_str': f'${amount:.2f}',
        'source': 'provider',
    }


class V25LiveStandingsTests(unittest.TestCase):
    def runtime_stub(self):
        value = Runtime.__new__(Runtime)
        value._movement_events = []
        return value

    def test_release_and_cadences_are_preserved(self):
        self.assertEqual(RELEASE, '2026.11.17-live-standings-v25')
        self.assertEqual(INTERVAL, 90)
        self.assertEqual(KICK_INTERVAL, 60)
        self.assertEqual(RANK_MOVEMENT_SECONDS, 45)

    def test_shuffle_swap_gets_explicit_events_and_independent_sequences(self):
        rt = self.runtime_stub()
        baseline = {'rows':[shuffle_row(1,'Alpha',100), shuffle_row(2,'Bravo',90)], 'updated_at':100}
        rt.ensure_top15(baseline, {'rows':[]})
        self.assertEqual(baseline['top15_movement_sequence'], 0)
        previous = baseline
        current = {'rows':[shuffle_row(1,'Bravo',120), shuffle_row(2,'Alpha',110)], 'updated_at':200}
        rt.ensure_top15(current, previous)
        self.assertEqual(current['top15_sequence'], previous['top15_sequence'] + 1)
        self.assertEqual(current['top15_movement_sequence'], 1)
        self.assertEqual(current['top15_movement_count'], 2)
        bravo, alpha = current['rows'][:2]
        self.assertEqual(bravo['movement'], 1)
        self.assertEqual(alpha['movement'], -1)
        self.assertEqual(bravo['previous_rank'], 2)
        self.assertEqual(alpha['previous_rank'], 1)
        self.assertEqual(bravo['movement_expires_at'], 245)
        event = public_movement_event(bravo)
        self.assertEqual(event['direction'], 'up')
        self.assertEqual(event['places'], 1)
        self.assertEqual(event['previous_rank'], 2)
        self.assertEqual(event['current_rank'], 1)
        self.assertTrue(event['event_id'])

    def test_wager_only_change_advances_standings_not_movement(self):
        rt = self.runtime_stub()
        previous = {'rows':[shuffle_row(1,'Alpha',100), shuffle_row(2,'Bravo',90)], 'updated_at':100}
        rt.ensure_top15(previous, {'rows':[]})
        current = {'rows':[shuffle_row(1,'Alpha',150), shuffle_row(2,'Bravo',95)], 'updated_at':200}
        rt.ensure_top15(current, previous)
        self.assertGreater(current['top15_sequence'], previous['top15_sequence'])
        self.assertEqual(current['top15_movement_sequence'], previous['top15_movement_sequence'])
        self.assertEqual(current['top15_movement_count'], 0)
        self.assertIsNone(public_movement_event(current['rows'][0]))

    def test_identical_confirmation_does_not_restart_event(self):
        rt = self.runtime_stub()
        baseline = {'rows':[shuffle_row(1,'Alpha',100), shuffle_row(2,'Bravo',90)], 'updated_at':100}
        rt.ensure_top15(baseline, {'rows':[]})
        moved = {'rows':[shuffle_row(1,'Bravo',120), shuffle_row(2,'Alpha',110)], 'updated_at':200}
        rt.ensure_top15(moved, baseline)
        event_id = moved['rows'][0]['movement_event_id']
        expires = moved['rows'][0]['movement_expires_at']
        same = {'rows':[shuffle_row(1,'Bravo',120), shuffle_row(2,'Alpha',110)], 'updated_at':230}
        rt.ensure_top15(same, moved)
        self.assertEqual(same['rows'][0]['movement_event_id'], event_id)
        self.assertEqual(same['rows'][0]['movement_expires_at'], expires)
        self.assertEqual(same['top15_movement_sequence'], moved['top15_movement_sequence'])

    def test_empiredrop_explicit_events_use_stable_provider_identity(self):
        old = {'rows':[
            {'rank':1,'username':'Re******','user_id':'p-1','wager':'$10.00'},
            {'rank':2,'username':'Re******','user_id':'p-2','wager':'$9.00'},
        ], 'standings_sequence':3, 'standings_revision':'old'}
        # Let the helper calculate old revision naturally so only the actual swap matters.
        from empiredrop import _standings_revision
        old['standings_revision'] = _standings_revision(old['rows'])
        rows, rev, seq, changed = attach_rank_movement([
            {'rank':1,'username':'Re******','user_id':'p-2','wager':'$12.00'},
            {'rank':2,'username':'Re******','user_id':'p-1','wager':'$11.00'},
        ], old, 500)
        self.assertEqual(seq, 4)
        self.assertEqual(changed, 500)
        self.assertEqual(rows[0]['movement'], 1)
        self.assertEqual(rows[1]['movement'], -1)
        self.assertNotEqual(rows[0]['movement_event_id'], rows[1]['movement_event_id'])
        self.assertEqual(public_movement_event(rows[0])['expires_at'], 545)

    def test_public_standings_contract_is_lightweight_and_five_seconds(self):
        source = Path('runtime.py').read_text(encoding='utf-8')
        self.assertIn('def public_standings(self):', source)
        self.assertIn('"sync_interval_seconds": 5', source)
        self.assertIn('"top15": copy.deepcopy(value.get("top15") or [])', source)
        route = Path('wager_backend.py').read_text(encoding='utf-8')
        self.assertIn('@app.get("/public-standings")', route)
        frontend = Path('static/live-standings.js').read_text(encoding='utf-8')
        self.assertIn('const SYNC_MS = 5000;', frontend)
        self.assertIn("fetch('/public-standings'", frontend)
        self.assertNotIn('shuffle.com', frontend.lower())
        self.assertNotIn('empiredrop.com/api', frontend.lower())


if __name__ == '__main__':
    unittest.main()
