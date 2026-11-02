"""No live EmpireDrop API calls. Tests use synthetic referral and wager data."""
import copy
import unittest
from unittest.mock import patch

from empiredrop import EmpireDropBoard, parse_rows, validate_settings, schedule, scope_id
from integrations import ProviderError
from wager_backend import create_app


class EmpireDropParsingTests(unittest.TestCase):
    def test_red_only_and_sorted_without_shuffles_weighting(self):
        sample = {'data': [
            {'username': 'NotRed', 'totalWagered': 50000, 'referralCode': 'other'},
            {'username': 'TwoPlayer', 'totalWagered': '150.50', 'referralCode': 'RED'},
            {'username': 'FirstPlayer', 'totalWagered': 300, 'referralCode': 'red'},
            {'username': 'TwoPlayer', 'totalWagered': '50', 'referralCode': 'red'},
        ]}
        rows = parse_rows(sample)
        self.assertEqual([(r['username'], r['wager']) for r in rows],
                         [('FirstPlayer', '€300.00'), ('TwoPlayer', '€150.50')])

    def test_unproved_code_scope_refuses_to_show_users(self):
        with self.assertRaises(ProviderError):
            parse_rows([{'username': 'Test', 'totalWagered': 5}])
        rows = parse_rows([{'username': 'Test', 'totalWagered': 5}],
                          settings={'code_scoped': True})
        self.assertEqual(rows[0]['username'], 'Test')

    def test_unknown_wager_fields_not_converted_from_deposits(self):
        with self.assertRaises(ProviderError):
            parse_rows([{'username': 'Person', 'deposits': 500, 'referralCode': 'red'}])
        with self.assertRaises(ProviderError):
            parse_rows([{'username': 'Person', 'totalWagered': 'NaN', 'referralCode': 'red'}])
        with self.assertRaises(ProviderError):
            parse_rows([{'username': 'Person', 'totalWagered': -1, 'referralCode': 'red'}])

    def test_url_and_header_validation_forbids_credential_redirects(self):
        for value in ('http://api.empiredrop.com/v1',
                      'https://api.empiredrop.com@evil.example/path',
                      'https://evil.example/path',
                      'https://api.empiredrop.com/v1?private_key=secret'):
            with self.subTest(value=value), self.assertRaises(ValueError):
                validate_settings({'api_url': value})
        self.assertEqual(validate_settings({'api_url':'https://api.empiredrop.com/v1'})['api_url'],
                         'https://api.empiredrop.com/v1')


class EmpireDropAppTests(unittest.TestCase):
    def setUp(self):
        import tempfile
        from pathlib import Path
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        with patch.dict('os.environ', {'APP_ENV':'test','ADMIN_BOOTSTRAP_PASS':'test-only-password'}, clear=True):
            self.app = create_app(Path(self.temp.name), testing=True)
        self.addCleanup(self.app.extensions['runtime'].store.close)
        self.client = self.app.test_client()
        with self.client.session_transaction() as session:
            session.update(user='gingrsnaps', auth_version=1, csrf='test-csrf')

    def test_separate_public_and_admin_views_never_share_names_or_keys(self):
        runtime = self.app.extensions['runtime']
        site = runtime.admin['site_settings']
        board = runtime.empiredrop
        with board.lock:
            board.saved = dict(scope=scope_id(schedule(runtime.admin)), rows=[{'rank':1,'username':'RealEmpireName', 'wager':'€500.00'}], updated_at=12345, attempt_at=12345, error='')
        public = board.public(site)
        private = self.client.get('/admin/empiredrop/status')
        self.assertEqual(private.status_code, 200)
        self.assertEqual(private.json['rows'][0]['username'], 'RealEmpireName')
        self.assertEqual(public['rows'][0]['username'], 'Re******')
        self.assertNotIn('RealEmpireName', str(public))
        self.assertNotIn(runtime.config.credentials.get('empiredrop_private_key') or 'KEY_NOT_SET', private.text)
        self.assertNotIn(runtime.config.credentials.get('empiredrop_public_key') or 'KEY_NOT_SET', private.text)
        self.assertNotIn('RealEmpireName', self.app.test_client().get('/public-state').text)
        self.assertEqual(self.app.test_client().get('/admin/empiredrop/status').status_code, 401)

    def test_superadmin_config_isolated_and_csrf_protected(self):
        board = self.app.extensions['runtime'].empiredrop
        original_shuffle = copy.deepcopy(self.app.extensions['runtime'].store.live('shuffle'))
        original = dict(board._settings())
        response = self.client.post('/admin/empiredrop/config', data={'api_url':'https://api.empiredrop.com/v1'})
        self.assertEqual(response.status_code, 400)
        fields = {key:str(value) for key,value in original.items() if key != 'code_scoped'}
        fields.update(csrf='test-csrf', revision='1', api_url='https://api.empiredrop.com/v1')
        response = self.client.post('/admin/empiredrop/config', data=fields)
        self.assertEqual(response.status_code, 303, response.text)
        self.assertEqual(board._settings()['api_url'], 'https://api.empiredrop.com/v1')
        self.assertEqual(self.app.extensions['runtime'].store.live('shuffle'), original_shuffle)

    def test_referral_link_is_present(self):
        html = self.client.get('/').text
        self.assertIn('https://empiredrop.com/c/red', html)
        self.assertIn('empireBoard', html)
        self.assertIn('shuffleBoard', html)
        self.assertIn('EmpireDrop', self.client.get('/admin?tab=empiredrop').text)


if __name__ == '__main__':
    unittest.main()
