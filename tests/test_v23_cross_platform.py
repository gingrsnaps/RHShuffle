from pathlib import Path
import unittest

from empiredrop import attach_rank_movement

ROOT = Path(__file__).resolve().parents[1]

class V23CrossPlatformTests(unittest.TestCase):
    def test_public_poll_is_fifteen_seconds_and_v24_provider_intervals_are_split(self):
        js=(ROOT/'static/app.js').read_text(encoding='utf-8')
        cfg=(ROOT/'config.py').read_text(encoding='utf-8')
        self.assertIn('const PUBLIC_POLL_MS = 15000', js)
        self.assertIn('const ADMIN_POLL_MS = 60000', js)
        self.assertIn('SHUFFLE_INTERVAL = 90', cfg)
        self.assertIn('KICK_INTERVAL = 60', cfg)

    def test_movement_is_server_timestamped_with_exact_expiration(self):
        app=(ROOT/'static/app.js').read_text(encoding='utf-8')
        runtime=(ROOT/'runtime.py').read_text(encoding='utf-8')
        empire=(ROOT/'empiredrop.py').read_text(encoding='utf-8')
        self.assertIn('movementWindowSeconds = 45', app)
        self.assertIn('movement_expires_at', runtime)
        self.assertIn('movement_expires_at', empire)
        self.assertIn('movement_at', runtime)
        self.assertIn('attach_rank_movement', empire)
        self.assertIn('movement_at', empire)

    def test_shuffle_unchanged_snapshot_preserves_original_event_time_in_source(self):
        runtime=(ROOT/'runtime.py').read_text(encoding='utf-8')
        self.assertIn('row["movement_at"] = int(old.get("movement_at", 0) or 0)', runtime)
        self.assertIn('if previous is not None and prior_revision == revision', runtime)
        self.assertIn('value["top15_sequence"] = sequence', runtime)

    def test_empiredrop_unchanged_snapshot_preserves_original_event_time(self):
        old={'rows':[{'rank':1,'username':'A','wager':'€10.00'},{'rank':2,'username':'B','wager':'€9.00'}]}
        rows,rev,seq,changed_at=attach_rank_movement(
            [{'rank':1,'username':'B','wager':'€12.00'},{'rank':2,'username':'A','wager':'€11.00'}], old, 200)
        self.assertEqual(rows[0]['movement'],1)
        self.assertEqual(rows[0]['movement_at'],200)
        saved={'rows':rows,'standings_revision':rev,'standings_sequence':seq,'standings_changed_at':changed_at,'updated_at':200}
        same,rev2,seq2,changed_at2=attach_rank_movement(
            [{'rank':1,'username':'B','wager':'€12.00'},{'rank':2,'username':'A','wager':'€11.00'}], saved, 260)
        self.assertEqual(same[0]['movement_at'],200)
        self.assertEqual(seq2,seq)
        self.assertEqual(rev2,rev)
        self.assertEqual(changed_at2,changed_at)

    def test_countdown_cannot_ellipsis(self):
        css=(ROOT/'static/v20-system.css').read_text(encoding='utf-8')
        block=css[css.index('body:not([data-page="admin"]) .public-race-summary .race-countdown'):css.index('body:not([data-page="admin"]) .public-race-summary .race-date-range')]
        self.assertIn('overflow:visible!important', block)
        self.assertIn('text-overflow:clip!important', block)
        self.assertNotIn('text-overflow:ellipsis', block)

    def test_public_snapshot_has_ordering_and_exact_etag_inputs(self):
        runtime=(ROOT/'runtime.py').read_text(encoding='utf-8')
        backend=(ROOT/'wager_backend.py').read_text(encoding='utf-8')
        self.assertIn('snapshot_sequence=sequence', runtime)
        self.assertIn('runtime_id=runtime_id', runtime)
        self.assertIn('signature = token(payload)', runtime)
        self.assertIn('X-Snapshot-Sequence', backend)

    def test_focus_and_visibility_recover_immediately(self):
        app=(ROOT/'static/app.js').read_text(encoding='utf-8')
        empire=(ROOT/'static/empiredrop.js').read_text(encoding='utf-8')
        self.assertIn('window.addEventListener("focus"', app)
        self.assertIn("addEventListener?.('focus'", empire)
        self.assertIn('visibilitychange', app)
        self.assertIn('visibilitychange', empire)

if __name__ == '__main__': unittest.main()
