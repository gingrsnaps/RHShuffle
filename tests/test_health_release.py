"""Readiness, private diagnostics, consistent recovery and community load."""
from concurrent.futures import ThreadPoolExecutor
import copy
import io
import json
from pathlib import Path
import tempfile
import time
import unittest
from unittest.mock import patch

import test_app
from fairness import VERSION, verify
from gaming import player_key, validate_gaming
from release_check import check_release
from storage import StoreError


class HealthTests(unittest.TestCase):
    setUp = test_app.AppTests.setUp

    def test_provider_failure_does_not_fail_readiness_but_storage_failure_does(self):
        self.r.jobs['shuffle']['error'] = 'Upstream unavailable'
        self.r.jobs['kick']['error'] = 'Upstream unavailable'
        self.assertEqual(self.client.get('/readyz').status_code, 200)
        self.r.store._probe_until = 0
        with patch('storage.tempfile.TemporaryFile', side_effect=OSError('read-only')):
            result = self.client.get('/readyz')
        self.assertEqual(result.status_code, 503)
        self.assertFalse(result.json['ok'])
        self.assertEqual(self.client.get('/healthz').status_code, 200)

    def test_health_report_requires_current_admin_and_has_no_private_values(self):
        anonymous = self.app.test_client()
        self.assertEqual(anonymous.get('/admin/health-report').status_code, 401)
        self.r.jobs['shuffle']['error'] = 'DO_NOT_EXPORT_PROVIDER_RESPONSE'
        game = self.app.extensions['gaming']
        game.confirm_community_name('health-player', 'DO_NOT_EXPORT_NAME')
        result = self.client.get('/admin/health-report')
        self.assertEqual(result.status_code, 200)
        for value in ['DO_NOT_EXPORT_NAME', 'DO_NOT_EXPORT_PROVIDER_RESPONSE', self.app.secret_key, 'server_seed', '198.51.100.1']:
            self.assertNotIn(value, result.text)
        self.assertEqual({c['key'] for c in result.json['components']}, {'website','shuffle','kick','games','storage'})
        with self.client.session_transaction() as session:
            session['auth_version'] = 999
        self.assertEqual(self.client.get('/admin/health-report').status_code, 401)

    def test_errors_have_trace_ids_and_storage_measurements_do_not_change_state(self):
        result = self.client.get('/gaming/api/unknown', headers={'Accept':'application/json'})
        self.assertEqual(result.status_code, 404)
        self.assertEqual(result.json['request_id'], result.headers['X-Request-ID'])
        self.assertEqual(result.json['code'], 'http_404')
        self.assertEqual(len(result.headers['X-Request-ID']), 16)
        before = self.r.store.path.read_bytes()
        for _ in range(3):
            self.client.get('/readyz')
            self.client.get('/admin/health-report')
        self.assertEqual(before, self.r.store.path.read_bytes())
        self.assertGreater(self.app.extensions['measurements'].snapshot()['requests'], 0)

    def test_full_export_preserves_pending_hand_and_preview_counts_differences(self):
        game = self.app.extensions['gaming']
        wallet = game.confirm_community_name('export-player', 'Export player')
        body = dict(rules_version=VERSION, game='poker', request_id='export-test-hand',
                    season=wallet['season']['id'], nonce=wallet['nonce'], commitment=wallet['commitment'],
                    wager=1000, client_seed='export', client_salt='ab'*16,
                    options=dict(variant='texas_holdem', button='player'))
        game.bet('export-player', 'Export player', body)
        exported = self.client.get('/admin/recovery-backup')
        self.assertEqual(exported.status_code, 200)
        state = validate_gaming(exported.json['redpoints'])
        self.assertEqual(state['players'][player_key('export-player')]['poker']['request_id'], 'export-test-hand')
        response = self.client.post('/admin/recovery-preview', data={
            'csrf':'test-token', 'recovery':(io.BytesIO(exported.data), 'recovery.json')})
        self.assertEqual(response.status_code, 200)
        self.assertIn('Compared with the current save', response.text)
        self.assertIn('Unfinished hands', response.text)
        self.assertEqual(game.view('export-player','Export player')['balance'], 99000)

    def test_one_hundred_players_can_settle_and_retry_on_same_network(self):
        game = self.app.extensions['gaming']
        jobs = []
        for index in range(100):
            identity, name = 'load-'+str(index), 'Community '+str(index)
            wallet = game.confirm_community_name(identity, name)
            body = dict(rules_version=VERSION, game='coinflip', request_id='load-round-'+str(index),
                        season=wallet['season']['id'], nonce=wallet['nonce'], commitment=wallet['commitment'],
                        wager=100, client_seed='community-load', client_salt='ab'*16, options=dict(side='heads'))
            jobs.append((identity, name, body))
        def play(job):
            identity, name, body = job
            start = time.perf_counter()
            result = game.bet(identity, name, body, client_ip='198.51.100.9')
            return result, (time.perf_counter()-start)*1000
        with ThreadPoolExecutor(max_workers=16) as pool:
            results = list(pool.map(play, jobs+jobs))
        self.assertEqual(sum(not item[0]['duplicate'] for item in results), 100)
        saved = validate_gaming(game.recovery())
        self.assertEqual(len(saved['players']), 100)
        for player in saved['players'].values():
            self.assertEqual(player['stats']['coinflip']['bets'], 1)
            self.assertEqual(player['balance'], 100000+player['receipts'][0]['net'])
            self.assertTrue(verify(player['receipts'][0]))
        from telemetry import distribution
        print('COMMUNITY_LOAD '+json.dumps(dict(players=100, requests=200, threads=16,
              latency=distribution([item[1] for item in results]), storage=self.r.store.measurements.snapshot()['storage'])))


class PackageTests(unittest.TestCase):
    def test_incomplete_asset_is_reported(self):
        with tempfile.TemporaryDirectory() as folder:
            root=Path(folder); (root/'templates').mkdir()
            (root/'templates/index.html').write_text("<script src=\"{{ url_for('static',filename='missing.js') }}\"></script>")
            (root/'templates/admin.html').write_text('admin')
            result=check_release(root)
            self.assertFalse(result['ok'])
            self.assertIn('index.html requires missing static/missing.js', result['problems'])
