"""No Flask, no live provider access: reproducible EmpireDrop isolation tests."""
import copy
from datetime import datetime
from decimal import Decimal
from pathlib import Path
import tempfile
import unittest
import os
import json
from unittest.mock import patch
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from empiredrop import (CODE, EmpireDropBoard, current_week, parse_rows, schedule,
                        scope_id, validate_settings)
from integrations import ProviderError
from race_support import EASTERN


class MockResponse:
    def __init__(self, payload, status=200):
        self.payload, self.status_code = payload, status
    def __enter__(self): return self
    def __exit__(self, *_): return False
    def iter_content(self, size):
        import json
        yield json.dumps(self.payload).encode('utf-8')


class FakeStore:
    def __init__(self):
        self.doc = {'site_settings':{'start_time':1,'end_time':2,'campaign_code_filter':'ShuffleCampaign'}}
        self.live_values = {'shuffle':{'key':'unchanged','rows':[{'username':'ShuffleExample'}]}}
    def admin(self): return 1, copy.deepcopy(self.doc)
    def live(self, service): return copy.deepcopy(self.live_values.get(service))
    def publish(self, service, value): self.live_values[service] = copy.deepcopy(value)


class FakeConfig:
    def __init__(self):
        self.empiredrop = {**validate_settings({}), 'api_url':'https://api.empiredrop.com/v1/example',
                           'verified_contract':True}
        self.credentials = {'empiredrop_public_key':'pk_test-example','empiredrop_private_key':'sk_test-example'}
        self.sources = {'empiredrop_public_key':'test', 'empiredrop_private_key':'test'}


class EmpireDropContractTests(unittest.TestCase):
    def test_weekly_eastern_calendar_and_dst_boundaries(self):
        for day, hours in [('2026-03-10T18:00',167), ('2026-11-03T18:00',169)]:
            end = int(datetime.fromisoformat(day).replace(tzinfo=EASTERN).timestamp())
            start, calculated_end = current_week(end-60)
            self.assertEqual(calculated_end,end)
            self.assertEqual((end-start)//3600,hours)
        store = FakeStore()
        value = schedule(store.doc, now=1793275200)
        self.assertNotEqual(value['start_time'],store.doc['site_settings']['start_time'])
        store.doc['empiredrop_race']={'mode':'custom','start_time':123456,'end_time':234567}
        self.assertEqual(schedule(store.doc)['start_time'],123456)

    def test_referral_red_filters_others_and_does_not_inherit_shuffles_weighting(self):
        payload=[{'username':'Alice','totalWagered':'50.23','referralCode':'RED'},
                 {'username':'Other','totalWagered':'1000000','referralCode':'other'}]
        self.assertEqual(parse_rows(payload),[{'rank':1,'username':'Alice','wager':'€50.23'}])
        with self.assertRaises(ProviderError):
            parse_rows([{'username':'Not scoped','totalWagered':100}])

    def test_aggregated_duplicates_do_not_double_count(self):
        rows=[{'username':'Alice','userId':'123','totalWagered':100,'referralCode':'red'},
              {'username':'Alice','userId':'123','totalWagered':100,'referralCode':'red'},
              {'username':'Alice','userId':'123','totalWagered':200,'referralCode':'red'}]
        self.assertEqual(parse_rows(rows,settings={'user_id_field':'userId'})[0]['wager'],'€200.00')

    def test_transaction_mode_requires_unique_ids(self):
        sample=[{'username':'A','transaction':'a','totalWagered':100,'referralCode':'red'},
                {'username':'A','transaction':'a','totalWagered':100,'referralCode':'red'},
                {'username':'A','transaction':'b','totalWagered':80,'referralCode':'red'}]
        self.assertEqual(parse_rows(sample,settings={'record_mode':'transactions','transaction_id_field':'transaction'})[0]['wager'],'€180.00')
        with self.assertRaises(ValueError):validate_settings({'record_mode':'transactions'})
        with self.assertRaises(ProviderError):parse_rows([{'username':'A','referralCode':'red','totalWagered':1}],settings={'record_mode':'transactions','transaction_id_field':'transaction'})

    def test_bad_amount_and_unknown_deposits_rejected(self):
        for bad in ('NaN',-1,float('inf'), True):
            with self.assertRaises(ProviderError):parse_rows([{'username':'A','referralCode':'red','totalWagered':bad}])
        with self.assertRaises(ProviderError):parse_rows([{'username':'A','referralCode':'red','deposit':1000}])

    def test_cannot_use_non_empiredrop_hosts_or_redirect_headers(self):
        for url in ('http://api.empiredrop.com/v1', 'https://api.empiredrop.com.evil.test/secret',
                    'https://empiredrop.com:8080/v1', 'https://empiredrop.com/?api_key=abc'):
            with self.assertRaises(ValueError): validate_settings({'api_url':url})
        with self.assertRaises(ValueError): validate_settings({'public_header':'Authorization'})

    def test_keys_never_leave_without_confirmed_contract(self):
        c, db = FakeConfig(), FakeStore()
        c.empiredrop['verified_contract']=False
        board=EmpireDropBoard(c,db)
        with patch('empiredrop.requests.get',side_effect=AssertionError('unexpected network request')):
            with self.assertRaises(ProviderError): board.fetch(schedule(db.doc))

    def test_connection_and_scoped_rows_with_no_secret_exposure(self):
        c, db=FakeConfig(),FakeStore()
        board=EmpireDropBoard(c,db)
        start,end=current_week()
        params=[]
        def request(url,**kw):
            self.assertTrue(url.startswith('https://api.empiredrop.com/'))
            self.assertFalse(kw['allow_redirects'])
            params.append(kw)
            return MockResponse({'data':[{'username':'PublicName', 'referralCode':'red', 'totalWagered':123.45}]})
        with patch('empiredrop.requests.get',side_effect=request):
            board.check()
        self.assertEqual(len(params),1)
        self.assertEqual(db.live('shuffle'),{'key':'unchanged','rows':[{'username':'ShuffleExample'}]})
        public=board.public()
        self.assertEqual(public['rows'][0]['username'],'Pu******')
        self.assertNotIn(c.credentials['empiredrop_private_key'],str(public))
        private=board.private_status()
        self.assertEqual(private['rows'][0]['username'],'PublicName')
        self.assertNotIn(c.credentials['empiredrop_private_key'],str(private))

    def test_pagination_no_partial_board_and_safe_cursor(self):
        c,db=FakeConfig(),FakeStore()
        board=EmpireDropBoard(c,db)
        def part(url,**kwargs): return MockResponse({'data':[{'username':'A','referralCode':'red','totalWagered':1}], 'nextCursor':'more'})
        with patch('empiredrop.requests.get',side_effect=part):
            with self.assertRaises(ProviderError):board.fetch(schedule(db.doc))
        c.empiredrop['pagination_mode']='cursor'
        pages=[]
        def paged(url,**kwargs):
            pages.append(kwargs['params'].get('cursor'))
            if len(pages)==1:
                return MockResponse({'data':[{'username':'A','referralCode':'red','totalWagered':10}], 'nextCursor':'next'})
            return MockResponse({'data':[{'username':'B','referralCode':'red','totalWagered':20}]})
        with patch('empiredrop.requests.get',side_effect=paged): rows=board.fetch(schedule(db.doc))
        self.assertEqual(pages,[None,'next'])
        self.assertEqual([x['username'] for x in rows],['B','A'])

    def test_failure_preserves_last_good_results_and_never_edits_shuffle(self):
        c,db=FakeConfig(),FakeStore()
        board=EmpireDropBoard(c,db)
        with patch.object(board,'fetch',return_value=[{'rank':1,'username':'Saved','wager':'€12.00'}]):board.check()
        before=db.live('empiredrop')
        with patch.object(board,'fetch',side_effect=ProviderError('rate limited',kind='rate_limit')):board.check()
        self.assertEqual(db.live('empiredrop')['rows'],before['rows'])
        self.assertIn('delayed',board.public()['label'])
        self.assertEqual(db.live('shuffle')['rows'][0]['username'],'ShuffleExample')

    def test_provider_errors_have_distinct_safe_categories(self):
        config, store = FakeConfig(), FakeStore()
        board = EmpireDropBoard(config, store)
        for status, kind in [(401,'access'),(403,'access'),(429,'rate_limit'),(302,'http'),(500,'http')]:
            with self.subTest(status=status), patch('empiredrop.requests.get',return_value=MockResponse({},status)):
                with self.assertRaises(ProviderError) as raised:board.fetch(schedule(store.doc))
                self.assertEqual(raised.exception.kind,kind)

    def test_nested_response_paths_and_millisecond_requests(self):
        c, db = FakeConfig(), FakeStore()
        c.empiredrop.update(rows_path='payload.players', name_field='player.display',
                           code_field='meta.code', wager_field='metrics.volume',
                           user_id_field='player.id', timestamp_format='unix_ms',
                           next_cursor_path='paging.next')
        board = EmpireDropBoard(c,db)
        calls=[]
        def request(url, **kw):
            calls.append(kw)
            return MockResponse({'payload':{'players':[{'player':{'id':7,'display':'Nested'},
                       'metrics':{'volume':'12.25'}, 'meta':{'code':'red'}}]},
                       'paging':{'next':None}})
        with patch('empiredrop.requests.get',side_effect=request):
            result = board.fetch(schedule(db.doc))
        self.assertEqual(result[0]['username'],'Nested')
        self.assertEqual(result[0]['wager'],'€12.25')
        self.assertIsInstance(calls[0]['params']['startTime'],int)
        self.assertGreater(calls[0]['params']['startTime'],10**12)

    def test_post_json_bearer_auth_with_iso_dates(self):
        c, db = FakeConfig(), FakeStore()
        c.empiredrop.update(auth_mode='bearer_private',http_method='POST',
                           request_location='json',timestamp_format='iso8601_utc')
        board=EmpireDropBoard(c,db)
        called=[]
        def post(url, **kw):
            called.append(kw)
            return MockResponse([{'username':'Poster','referralCode':'red','totalWagered':5}])
        with patch('empiredrop.requests.post',side_effect=post):
            result=board.fetch(schedule(db.doc))
        self.assertEqual(result[0]['username'],'Poster')
        self.assertTrue(called[0]['headers']['Authorization'].startswith('Bearer '))
        self.assertTrue(called[0]['json']['startTime'].endswith('Z'))
        self.assertNotIn('params',called[0])

    def test_wrong_or_unverified_configuration_never_contacts_provider(self):
        for bad in ({'auth_mode':'unknown'},{'http_method':'DELETE'},
                    {'http_method':'GET','request_location':'json'},
                    {'rows_path':'results.__class__[0]'},
                    {'timestamp_format':'local'}):
            with self.subTest(bad=bad), self.assertRaises(ValueError):
                validate_settings(bad)
        c, db = FakeConfig(), FakeStore()
        c.empiredrop.update(verified_contract=False,auth_mode='bearer_private')
        with patch('empiredrop.requests.post',side_effect=AssertionError('network')), \
             patch('empiredrop.requests.get',side_effect=AssertionError('network')):
            with self.assertRaises(ProviderError):
                EmpireDropBoard(c,db).fetch(schedule(db.doc))

    def test_private_settings_key_replace_is_atomic_and_persistent(self):
        from config import Config
        with tempfile.TemporaryDirectory() as folder, patch.dict(os.environ, {}, clear=True):
            path = Path(folder)/'private'/'settings.json'
            path.parent.mkdir()
            path.write_text(json.dumps({'site_name':'Test','empiredrop_public_key':'pk_prod_initialinitialinitial111',
                                        'empiredrop_private_key':'sk_prod_initialinitialinitial111'}))
            c=Config(folder)
            original=c.credentials['empiredrop_private_key']
            self.assertFalse(c.replace_empiredrop_keys())
            self.assertTrue(c.replace_empiredrop_keys(public='pk_prod_newpublickeyvalue9999999'))
            saved=json.loads(path.read_text())
            self.assertEqual(saved['empiredrop_private_key'], original)
            self.assertEqual(c.credentials['empiredrop_public_key'], 'pk_prod_newpublickeyvalue9999999')
            restarted=Config(folder)
            self.assertEqual(restarted.credentials['empiredrop_public_key'],c.credentials['empiredrop_public_key'])
            self.assertEqual(restarted.credentials['empiredrop_private_key'],original)
            with self.assertRaises(ValueError):c.replace_empiredrop_keys(private='not-a-key')
            self.assertEqual(json.loads(path.read_text()),saved)

    def test_env_credential_overrides_are_not_replaced_by_admin(self):
        from config import Config
        with tempfile.TemporaryDirectory() as folder, patch.dict(os.environ, {'EMPIREDROP_PRIVATE_KEY':'sk_prod_environmentenvironment12345'}, clear=True):
            c=Config(folder)
            with self.assertRaises(ValueError):
                c.replace_empiredrop_keys(private='sk_prod_newprivatekeyvalue1234')
            self.assertFalse((Path(folder)/'private'/'settings.json').exists())



if __name__ == '__main__':unittest.main()
