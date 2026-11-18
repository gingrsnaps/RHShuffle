from pathlib import Path
import unittest
from unittest.mock import patch

from empiredrop import attach_rank_movement, EmpireDropBoard
from race import top_snapshot
from config import (RELEASE, INTERVAL, KICK_INTERVAL, EMPIREDROP_MIN_INTERVAL,
                    RANK_MOVEMENT_SECONDS)

ROOT=Path(__file__).resolve().parents[1]

class V24ProviderCadenceTests(unittest.TestCase):
    def test_release_and_cadence_contract(self):
        self.assertEqual(RELEASE,'2026.11.17-provider-cadence-v24')
        self.assertEqual(INTERVAL,90)
        self.assertEqual(KICK_INTERVAL,60)
        self.assertEqual(EMPIREDROP_MIN_INTERVAL,90)
        self.assertEqual(RANK_MOVEMENT_SECONDS,45)
        app=(ROOT/'static/app.js').read_text(encoding='utf-8')
        self.assertIn('const PUBLIC_POLL_MS = 15000',app)
        self.assertIn('const ADMIN_POLL_MS = 60000',app)

    def test_runtime_uses_independent_anchored_cadences(self):
        source=(ROOT/'runtime.py').read_text(encoding='utf-8')
        self.assertIn('return KICK_INTERVAL if name == "kick" else INTERVAL',source)
        self.assertIn('// cadence) + 1) * cadence',source)
        self.assertIn('min(720, cadence * (2 **',source)

    def test_empiredrop_90_second_floor_respects_longer_provider_ttl(self):
        source=(ROOT/'empiredrop.py').read_text(encoding='utf-8')
        self.assertIn('max(self.minimum_interval, ttl)',source)
        self.assertIn('self.minimum_interval = EMPIREDROP_MIN_INTERVAL',source)
        self.assertNotIn('max(60, ttl)',source)

    def test_empiredrop_movement_expiration_is_45_seconds_and_does_not_restart(self):
        old={'rows':[{'rank':1,'username':'A','wager':'€10.00'}, {'rank':2,'username':'B','wager':'€9.00'}]}
        rows,rev,seq,changed=attach_rank_movement([
            {'rank':1,'username':'B','wager':'€12.00'}, {'rank':2,'username':'A','wager':'€11.00'}], old, 200)
        self.assertEqual(rows[0]['movement'],1)
        self.assertEqual(rows[0]['movement_at'],200)
        self.assertEqual(rows[0]['movement_expires_at'],245)
        saved={'rows':rows,'standings_revision':rev,'standings_sequence':seq,'standings_changed_at':changed,'updated_at':200}
        same,_,_,_=attach_rank_movement([
            {'rank':1,'username':'B','wager':'€12.00'}, {'rank':2,'username':'A','wager':'€11.00'}], saved, 230)
        self.assertEqual(same[0]['movement_at'],200)
        self.assertEqual(same[0]['movement_expires_at'],245)

    def test_same_rank_wager_change_has_no_movement(self):
        old={'rows':[{'rank':1,'username':'A','wager':'€10.00'}], 'standings_revision':'old','standings_sequence':1}
        rows,_,_,_=attach_rank_movement([{'rank':1,'username':'A','wager':'€20.00'}], old, 300)
        self.assertEqual(rows[0]['movement'],0)
        self.assertFalse(rows[0]['new_entry'])
        self.assertEqual(rows[0]['movement_expires_at'],0)

    def test_mask_collision_is_irrelevant_to_backend_identity(self):
        old={'rows':[{'rank':1,'username':'RedOne','user_id':'u1','wager':'€10.00'},
                     {'rank':2,'username':'RedTwo','user_id':'u2','wager':'€9.00'}]}
        rows,_,_,_=attach_rank_movement([
            {'rank':1,'username':'RedTwo','user_id':'u2','wager':'€11.00'},
            {'rank':2,'username':'RedOne','user_id':'u1','wager':'€10.50'}], old, 400)
        self.assertEqual([x['movement'] for x in rows],[1,-1])

    def test_shared_frontend_renderer_is_used_by_both_providers(self):
        shared=(ROOT/'static/rank-movement.js').read_text(encoding='utf-8')
        shuffle=(ROOT/'static/app.js').read_text(encoding='utf-8')
        empire=(ROOT/'static/empiredrop.js').read_text(encoding='utf-8')
        base=(ROOT/'templates/base.html').read_text(encoding='utf-8')
        self.assertIn('DEFAULT_WINDOW_SECONDS = 45',shared)
        self.assertIn('RedRankMovement?.render',shuffle)
        self.assertIn('RedRankMovement?.render',empire)
        self.assertLess(base.index("filename='rank-movement.js'"),base.index("filename='app.js'"))

if __name__=='__main__': unittest.main()
