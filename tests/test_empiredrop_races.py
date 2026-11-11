"""EmpireDrop OpenAPI v2.0.1 contract regression tests. No live credentials."""
import copy
import json
import time
from pathlib import Path
import unittest
from unittest.mock import patch

from empiredrop_races import (RaceAPI, race_catalog, select_race, normalize_race,
                              validate_race_settings, LIST_PATH, DETAIL_PATH, API_ORIGIN)
from empiredrop import EmpireDropBoard
from integrations import ProviderError

ROOT=Path(__file__).resolve().parents[1]
SAMPLE=json.loads((ROOT/'tests/fixtures/empiredrop_race_success.json').read_text())
LIST={'races':[copy.deepcopy(SAMPLE['race'])]}
KEYS={'empiredrop_public_key':'pk_prod_EXAMPLE_DO_NOT_USE',
      'empiredrop_private_key':'sk_prod_EXAMPLE_DO_NOT_USE'}

class FakeResponse:
    def __init__(self,payload,code=200):
        self.payload=json.dumps(payload).encode('utf-8'); self.status_code=code
    def __enter__(self):return self
    def __exit__(self,*args):return False
    def iter_content(self,size):yield self.payload

class FakeRequests:
    def __init__(self,catalog=None,detail=None,code=200):
        self.catalog=LIST if catalog is None else catalog
        self.detail=SAMPLE if detail is None else detail
        self.code=code
        self.calls=[]
    def get(self,url,**kwargs):
        self.calls.append((url,kwargs))
        if url==API_ORIGIN+LIST_PATH:return FakeResponse(self.catalog,self.code)
        if url==API_ORIGIN+DETAIL_PATH.format(slug=SAMPLE['race']['slug']):
            return FakeResponse(self.detail,self.code)
        raise AssertionError('Unexpected source URL')

class Store:
    def __init__(self,settings=None):
        self.admin_value={'empiredrop_races':settings or {}}
        self.saved={}
    def admin(self):return 1,self.admin_value
    def live(self,key):return self.saved.get(key)
    def publish(self,key,value):self.saved[key]=copy.deepcopy(value)

class Config:
    empiredrop={}
    credentials=KEYS
    sources={k:'mock' for k in KEYS}

class OpenAPITests(unittest.TestCase):
    def test_both_headers_sent_to_both_current_endpoints(self):
        fake=FakeRequests(); api=RaceAPI({},KEYS,requester=fake)
        races,_=api.discover(); result=api.details(races[0]['slug'])
        self.assertEqual(result['race']['slug'],races[0]['slug'])
        self.assertEqual(len(fake.calls),2)
        for url,kw in fake.calls:
            self.assertTrue(url.startswith('https://api.empiredrop.com/api/v1/affiliate-partner/races'))
            self.assertEqual(kw['headers']['X-Public-Key'],KEYS['empiredrop_public_key'])
            self.assertEqual(kw['headers']['X-Private-Key'],KEYS['empiredrop_private_key'])
            self.assertFalse(kw['allow_redirects'])
            self.assertTrue(kw['stream'])
            self.assertNotIn('/race/affiliates/',url)

    def test_old_saved_settings_migrate_to_spec_defaults(self):
        opts=validate_race_settings({'api_base_url':'https://empiredrop.com',
            'race_auth_mode':'none','race_name_field':'username',
            'race_wager_field':'wagered','race_rows_path':'data.leaderboard',
            'race_verified_fields':False,'race_start_field':'startTime'})
        self.assertEqual(opts['api_base_url'],API_ORIGIN)
        self.assertEqual(opts['race_auth_mode'],'dual_headers')
        self.assertEqual(opts['race_rows_path'],'ranking')
        self.assertEqual(opts['race_name_field'],'user.name')
        self.assertEqual(opts['race_wager_field'],'total')
        self.assertEqual(opts['race_wager_divisor'],'100')
        self.assertEqual(opts['race_start_field'],'race.start_date')
        self.assertTrue(opts['race_verified_fields'])
        self.assertEqual(opts['race_private_header'],'X-Private-Key')

    def test_catalog_running_races_and_direct_slug(self):
        result=race_catalog(LIST)
        self.assertEqual(result[0]['slug'],SAMPLE['race']['slug'])
        self.assertTrue(result[0]['is_active'])
        self.assertEqual(result[0]['cache_duration'],300)
        self.assertEqual(select_race(result,{})['slug'],SAMPLE['race']['slug'])
        self.assertEqual(select_race([] ,{'race_slug':'finished-race'})['slug'],'finished-race')
        with self.assertRaises(ProviderError):select_race([], {})
        with self.assertRaises(ProviderError):select_race(result+result,{})

    def test_documented_minor_units_and_tied_ranks(self):
        rows=normalize_race(SAMPLE,{})
        self.assertEqual(rows,[
            {'rank':1,'username':'Ha*********ms','user_id':'FAKE_01','wager':'€5,637.44'},
            {'rank':2,'username':'Us*****2','user_id':'FAKE_02','wager':'€1,002.50'},
            {'rank':2,'username':'Us*****3','user_id':'FAKE_03','wager':'€1,002.50'},
        ])

    def test_deposit_ranking_and_raffle_tickets_are_not_wagers(self):
        deposit=copy.deepcopy(SAMPLE);deposit['race']['type']='DEPOSIT'
        self.assertEqual(normalize_race(deposit)[0]['wager'],'€5,637.44')
        raffle=copy.deepcopy(SAMPLE);raffle['race']['engine']='RAFFLE'
        for row in raffle['ranking']:
            row['unit']='TICKETS';row['total']=17
        self.assertEqual(normalize_race(raffle)[0]['wager'],'17 tickets')
        raffle['ranking'][0]['unit']='EUR'
        with self.assertRaises(ProviderError):normalize_race(raffle)

    def test_bad_response_not_published(self):
        for bad in (None,{'ranking':[]},{'race':SAMPLE['race'],'ranking':[{'rank':1}]},
                    {**SAMPLE,'ranking':[{'rank':1,'total':200,'unit':'EUR',
                       'user':{'name':'masked','hash_id':'fake'}},{'rank':2,'total':200,'unit':'EUR',
                       'user':{'name':'masked2','hash_id':'fake'}}]}):
            with self.subTest(bad=repr(bad)[:20]),self.assertRaises(ProviderError):normalize_race(bad)
        self.assertEqual(normalize_race({**SAMPLE,'ranking':[]}),[])

    def test_http_errors_and_no_redirect(self):
        for status,kind in [(401,'access'),(403,'access'),(404,'scope'),(429,'rate_limit'),(302,'redirect'),(500,'http')]:
            with self.subTest(status=status):
                api=RaceAPI({},KEYS,FakeRequests(code=status))
                with self.assertRaises(ProviderError) as e:api.discover()
                self.assertEqual(e.exception.kind,kind)

    def test_admin_probe_returns_shapes_not_player_values(self):
        fake=FakeRequests();probe=RaceAPI({},KEYS,fake).probe(SAMPLE['race']['slug'])
        serialized=json.dumps(probe)
        self.assertIn('hash_id',serialized)
        self.assertNotIn('Ha*********ms',serialized)
        self.assertNotIn(KEYS['empiredrop_private_key'],serialized)

class WorkerTests(unittest.TestCase):
    def test_board_publishes_provider_metadata_and_preserves_shuffle(self):
        store=Store();store.publish('shuffle',{'rows':[{'username':'ShuffleUser'}]})
        board=EmpireDropBoard(Config(),store)
        fake=FakeRequests()
        with patch('empiredrop_races.requests.get',side_effect=fake.get):
            board.check()
        public=board.public();private=board.private_status()
        self.assertEqual(public['rows'][0]['username'],'Ha******')
        self.assertEqual(public['rows'][0]['wager'],'€5,637.44')
        self.assertEqual(public['rows'][1]['rank'],2)
        self.assertEqual(public['rows'][2]['rank'],2)
        self.assertEqual(public['race_meta']['metric'],'Wagered')
        self.assertEqual(public['schedule']['mode'],'provider')
        self.assertEqual(board.interval,300)
        self.assertEqual(private['race_configuration']['api_base_url'],API_ORIGIN)
        self.assertEqual(private['race_history'],[])
        self.assertEqual(store.live('shuffle')['rows'][0]['username'],'ShuffleUser')
        self.assertNotIn(KEYS['empiredrop_private_key'],json.dumps(public))
        self.assertNotIn(KEYS['empiredrop_private_key'],json.dumps(private))

    def test_rate_limit_keeps_last_good_data_and_backs_off(self):
        store=Store();board=EmpireDropBoard(Config(),store);remote=FakeRequests()
        with patch('empiredrop_races.requests.get',side_effect=remote.get):board.check()
        with patch('empiredrop_races.requests.get',side_effect=FakeRequests(code=429).get):board.check()
        self.assertEqual(board.public()['rows'][0]['wager'],'€5,637.44')
        self.assertEqual(board.private_status()['error_kind'],'rate_limit')
        self.assertGreaterEqual(board.interval,600)

    def test_provider_window_not_wiped_by_tuesday_rollover(self):
        store=Store();board=EmpireDropBoard(Config(),store)
        from empiredrop import schedule
        old=board._scope(schedule(store.admin_value,now=1780500000))
        new=board._scope(schedule(store.admin_value,now=1781100000))
        self.assertEqual(old,new)

    def test_closed_race_preserves_last_verified_rows(self):
        store=Store({'race_slug':SAMPLE['race']['slug']});board=EmpireDropBoard(Config(),store)
        with patch('empiredrop_races.requests.get',side_effect=FakeRequests().get):board.check()
        closed=copy.deepcopy(SAMPLE);closed['race']['is_active']=False;closed['ranking']=[]
        with patch('empiredrop_races.requests.get',side_effect=FakeRequests(detail=closed).get):board.check()
        self.assertEqual(board.public()['rows'][0]['wager'],'€5,637.44')
        self.assertFalse(board.public()['race_meta']['is_active'])

if __name__=='__main__':unittest.main()
