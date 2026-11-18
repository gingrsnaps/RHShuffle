from pathlib import Path
import unittest

from race import top_snapshot
from provider_admin import summarize_providers

ROOT = Path(__file__).resolve().parents[1]


def row(rank, name, amount):
    return {
        'rank': rank,
        'username': name,
        'weighted_wager': str(amount),
        'wager': f'${amount:,.2f}',
    }


class V22Top15Tests(unittest.TestCase):
    def test_top_snapshot_versions_all_fifteen_and_movements(self):
        previous = [row(i, f'P{i:02d}', 2000-i) for i in range(1, 16)]
        current = [row(1, 'P02', 2500), row(2, 'NEW', 2400), row(3, 'P01', 2300)]
        current += [row(i, f'P{i:02d}', 2000-i) for i in range(4, 16)]
        visible, revision = top_snapshot(current, previous, 15)
        self.assertEqual(len(visible), 15)
        self.assertEqual([r['rank'] for r in visible], list(range(1, 16)))
        self.assertEqual(visible[0]['movement'], 1)
        self.assertTrue(visible[1]['new_entry'])
        self.assertEqual(len(revision), 20)

    def test_first_snapshot_does_not_mark_everyone_new(self):
        visible, _ = top_snapshot([row(i, f'P{i}', 100-i) for i in range(1, 4)], [], 15)
        self.assertTrue(all(not r['new_entry'] for r in visible))

    def test_duplicate_internal_identity_is_rejected(self):
        with self.assertRaises(ValueError):
            top_snapshot([row(1, 'Same', 10), row(2, 'Same', 9)], [], 15)

    def test_admin_summary_exposes_filled_last_change_and_next_check(self):
        status = {
            'health': {'components':[{'key':'shuffle','state':'healthy','status':'Healthy'},
                                     {'key':'empiredrop','state':'healthy','status':'Healthy'}]},
            'jobs': {'shuffle': {'last_success':100, 'attempt_at':110, 'changed_at':95,
                                 'next_check':160, 'request_meta':{}},},
            'diagnostics': {'received': 832, 'accepted':72, 'missing_campaign':2, 'rejected':{'other campaign':760}},
            'count':72,
            'rows':[{}]*15,
            'site': {'start_et':'A','end_et':'B','end_time':9999999999},
        }
        empire = {'rows':[], 'updated_at':0, 'attempt_at':0, 'next_check_at':0, 'refresh_interval':300,
                  'race_meta':{}, 'source_mode':'races'}
        cards = summarize_providers(status, empire, {'shuffle':{},'empiredrop':{}})
        shuffle = cards['shuffle']
        self.assertEqual(shuffle['filled'],15)
        self.assertEqual(shuffle['last_changed'],95)
        self.assertEqual(shuffle['next_check'],160)
        self.assertIn('15/15 public positions filled', shuffle['quality'])
        self.assertIn('72 ranked player(s) from 832 source record(s)', shuffle['quality'])

    def test_frontend_explicitly_renders_ranks_one_through_fifteen(self):
        js = (ROOT/'static/app.js').read_text(encoding='utf-8')
        self.assertIn('function renderShuffleTop15', js)
        self.assertIn('for (let rank = 1; rank <= 15; rank += 1)', js)
        self.assertIn('value.top15', js)
        self.assertIn('shuffle_revision', js)

    def test_runtime_keeps_backoff_but_restores_anchored_provider_cadence_after_success(self):
        source = (ROOT/'runtime.py').read_text(encoding='utf-8')
        self.assertIn('effective_retry = max', source)
        self.assertIn('if error else 0', source)
        self.assertIn('due = anchor + (int(max(0, finished - anchor) // cadence) + 1) * cadence', source)

    def test_verified_history_is_frozen_until_forced(self):
        source = (ROOT/'weekly_history.py').read_text(encoding='utf-8')
        self.assertIn("previous.get('verified')", source)
        self.assertIn("verified=True", source)
        self.assertIn('Only an explicit administrator refresh rechecks it', source)

    def test_public_etag_uses_public_revision(self):
        source = (ROOT/'wager_backend.py').read_text(encoding='utf-8')
        self.assertIn('response.set_etag(str(value.get("revision") or token(value)))', source)


if __name__ == '__main__':
    unittest.main()
