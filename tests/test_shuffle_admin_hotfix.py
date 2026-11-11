"""Regression tests for the exact November 2026 operations report findings.

No live API requests and no credentials in test output.
"""
import json
from pathlib import Path
import time
import unittest
from unittest.mock import patch

from integrations import classify_shuffle_bad_request, Providers, ProviderError
from operations_log import ActivityLog
from provider_admin import summarize_providers

ROOT=Path(__file__).resolve().parents[1]

class Response:
    def __init__(self, body): self.body=body
    def iter_content(self, _): yield self.body.encode('utf-8')

class HotfixTests(unittest.TestCase):
    def test_shuffle_400_is_not_always_a_date_error(self):
        self.assertEqual(classify_shuffle_bad_request(Response('{"message":"unknown filter type"}')), 'bad_request')
        self.assertEqual(classify_shuffle_bad_request(Response('{"errors":{"startTime":"invalid date"}}')), 'window')
        self.assertEqual(classify_shuffle_bad_request(Response('NO PRIVATE DATA')), 'bad_request')

    def test_historical_shuffle_400_uses_same_classification(self):
        from weekly_history import problem
        self.assertEqual(problem(ProviderError('Request rejected',status=400,kind='bad_request'))[0],'bad_request')
        self.assertEqual(problem(ProviderError('Request rejected',status=400,kind='window'))[0],'window')

    def test_repeated_400_warnings_are_grouped(self):
        log=ActivityLog()
        log.record('shuffle','warning','refresh_failed',code='bad_request',http_status=400)
        log.record('shuffle','warning','refresh_failed',code='bad_request',http_status=400)
        self.assertEqual(log.summary()['total'],1)
        self.assertEqual(log.list()[0]['occurrences'],2)
        self.assertEqual(log.list()[0]['http_status'],400)
        log.record('empiredrop','success','refresh_ok',count=10,http_status=200)
        self.assertEqual(log.summary()['levels']['success'],1)
        self.assertEqual(log.summary()['levels']['warning'],1)
        self.assertNotIn('sk_prod_',json.dumps(log.export()))

    def test_stale_shuffle_dates_produce_actionable_warning_without_changes(self):
        old_end=int(time.time())-100000
        status={'health':{'components':[]},'site':{'start_time':old_end-604800,'end_time':old_end,
                'start_et':'Old week','end_et':'Old week'},'rows':[],
                'jobs':{'shuffle':{'error':'400','http_status':400,'last_success':0,'attempt_at':0}},
                'diagnostics':{'received':0,'accepted':0},'count':0}
        empire={'race_meta':{},'rows':[],'source_mode':'races','updated_at':0}
        result=summarize_providers(status,empire)
        issues=' '.join(result['shuffle']['issues'])
        self.assertIn('HTTP 400',issues)
        self.assertIn('historical window',issues)
        self.assertIn('require confirmation',issues)
        self.assertEqual(result['empiredrop']['participants'],0)

    def test_admin_date_formatter_does_not_use_invalid_intl_combination(self):
        for name in ('admin-providers.js','admin-empiredrop.js'):
            code=(ROOT/'static'/name).read_text(encoding='utf-8')
            self.assertNotIn('dateStyle:',code)
            self.assertIn("timeZoneName:'short'",code)
        app=(ROOT/'static/app.js').read_text(encoding='utf-8')
        self.assertIn('currentEasternWeek()',app)
        self.assertIn('id("currentWeek")',app)
        self.assertIn('Use current week',(ROOT/'templates/admin_race.html').read_text(encoding='utf-8'))

    def test_private_key_fallback_is_not_browser_side(self):
        import config,shuffle_deploy_key
        private=json.loads((ROOT/'private/settings.json').read_text(encoding='utf-8'))
        self.assertEqual(private['shuffle_api_key'],shuffle_deploy_key.SHUFFLE_BUNDLED_KEY)
        config_file=(ROOT/'config.py').read_text(encoding='utf-8')
        self.assertIn('SHUFFLE_BUNDLED_KEY',config_file)
        for file in (ROOT/'static').glob('*.js'):
            self.assertNotIn(private['shuffle_api_key'],file.read_text(encoding='utf-8'))

if __name__=='__main__':unittest.main()
