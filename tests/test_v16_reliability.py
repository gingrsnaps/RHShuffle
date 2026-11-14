from pathlib import Path
import unittest

from operations_log import ActivityLog
from provider_admin import summarize_providers

ROOT = Path(__file__).resolve().parents[1]


class V16ReliabilityTests(unittest.TestCase):
    def text(self, path):
        return (ROOT / path).read_text(encoding='utf-8')

    def test_countdowns_share_component_and_final_css(self):
        page = self.text('templates/index.html')
        macro = self.text('templates/macros.html')
        self.assertGreaterEqual(page.count('public_race_summary('), 2)
        self.assertIn('clock race-countdown', macro)
        css = self.text('static/v16-system.css')
        self.assertIn('--race-countdown-size', css)
        self.assertIn('#empireRaceClock .race-countdown', css)
        self.assertIn('#shuffleRaceClock .race-countdown', css)
        base = self.text('templates/base.html')
        self.assertIn('v16-system.css', base)

    def test_reward_form_has_idempotency_and_submit_lock(self):
        template = self.text('templates/admin_empiredrop.html')
        self.assertIn('name="submission_id"', template)
        self.assertIn('data-payout-submit', template)
        backend = self.text('wager_backend.py')
        self.assertIn('empiredrop_reward_last_submission', backend)
        self.assertIn('No prize changes were detected', backend)
        javascript = self.text('static/admin-empiredrop.js')
        self.assertIn('let submitting = false', javascript)
        self.assertIn("form.setAttribute('aria-busy','true')", javascript)

    def test_activity_log_tracks_quality_and_trends(self):
        log = ActivityLog()
        log.record('shuffle','success','refresh_ok',count=72,received=832,accepted=72,excluded=3)
        log.record('shuffle','warning','refresh_failed',code='bad_request',http_status=400)
        row = log.list()[1]
        self.assertEqual(row['received'], 832)
        self.assertEqual(row['accepted'], 72)
        self.assertEqual(row['excluded'], 3)
        trend = log.provider_trends()['shuffle']
        self.assertEqual(trend['sample'], 2)
        self.assertEqual(trend['successes'], 1)
        self.assertEqual(trend['failures'], 1)

    def test_provider_summary_uses_precise_terms(self):
        status = {
            'health': {'components': []},
            'jobs': {'shuffle': {'last_success': 1, 'attempt_at': 2, 'request_meta': {'method':'GET'}}},
            'diagnostics': {'received':832,'accepted':72,'missing_campaign':2,'rejected':{'invalid':1}},
            'count':72,'rows':[{}],
            'site': {'end_time': 9999999999, 'start_et':'A','end_et':'B'},
        }
        empire = {'rows': [], 'race_meta': {}, 'updated_at': 0}
        result = summarize_providers(status, empire, {'shuffle':{'sample':2,'successes':1,'failures':1,'success_rate':50}})
        self.assertIn('72 ranked player(s) from 832 source record(s)', result['shuffle']['quality'])
        self.assertEqual(result['shuffle']['trend']['success_rate'], 50)
        self.assertEqual(result['shuffle']['request_meta']['method'], 'GET')

    def test_shuffle_requests_are_serialized_and_backed_off(self):
        integrations = self.text('integrations.py')
        self.assertIn('self.shuffle_lock = threading.Lock()', integrations)
        self.assertIn('with self.shuffle_lock:', integrations)
        runtime = self.text('runtime.py')
        self.assertIn('failure_streak', runtime)
        self.assertIn('min(480, INTERVAL * (2 **', runtime)


if __name__ == '__main__':
    unittest.main()
