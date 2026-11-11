"""Regression tests for separate EmpireDrop date windows, rewards and safe logs."""
import copy
import json
import unittest
from datetime import datetime,timezone
from unittest.mock import patch
from empiredrop_features import (validate_rewards, rewards_public, payout_for_rows,
                                  mask_public_username)
from empiredrop_races import (RaceAPI,normalize_legacy_window,LEGACY_PATH,API_ORIGIN)
from empiredrop import EmpireDropBoard, schedule
from operations_log import ActivityLog
from integrations import ProviderError

KEYS={'empiredrop_public_key':'pk_prod_EXAMPLE_FAKE',
      'empiredrop_private_key':'sk_prod_EXAMPLE_FAKE'}

class FakeResponse:
    status_code=200
    def __init__(self,p):self.payload=json.dumps(p).encode('utf8')
    def __enter__(self):return self
    def __exit__(self,*unused):pass
    def iter_content(self,size):yield self.payload

class FakeRequests:
    def __init__(self,p):self.payload=p;self.last=None
    def get(self,url,**kwargs):self.last=(url,kwargs);return FakeResponse(self.payload)

class Store:
    def __init__(self,settings=None,rewards=None):
        self.admin_value={'empiredrop_races':settings or {},
                          'empiredrop_rewards':rewards or {}}
        self.saved={}
    def admin(self):return 1,self.admin_value
    def live(self,key):return self.saved.get(key)
    def publish(self,key,val):self.saved[key]=copy.deepcopy(val)
class Config:
    empiredrop={}
    credentials=KEYS
    sources={k:'mock' for k in KEYS}

class QOLTests(unittest.TestCase):
    def test_masking(self):
        self.assertEqual(mask_public_username('Ha*********ms'),'Ha******')
        self.assertEqual(mask_public_username('ShuffleFullName'),'Sh******')
        self.assertEqual(mask_public_username('A'),'A******')

    def test_rewards_independent_and_tie_split(self):
        prizes={str(i):'0' for i in range(1,16)}
        prizes['1']='100.00';prizes['2']='75.00';prizes['3']='50.00'
        cfg=validate_rewards(dict(currency='EUR',enabled=True,prizes=prizes))
        self.assertEqual(rewards_public(cfg)['total'],'€225.00')
        rows=[dict(rank=1,username='mask1',wager='€100.00'),
              dict(rank=1,username='mask2',wager='€100.00'),
              dict(rank=3,username='mask3',wager='€30.00')]
        with_payouts=list(payout_for_rows(rows,cfg))
        self.assertEqual([r['prize'] for r in with_payouts],['€50.00','€50.00','€50.00'])
        self.assertEqual(list(payout_for_rows(rows,validate_rewards({})))[0]['prize'],'—')
        self.assertEqual(cfg['prizes']['2'],'75.00')
        thirds=[dict(rank=1,username=str(i),wager='€0') for i in range(3)]
        self.assertEqual([r['prize'] for r in payout_for_rows(thirds,cfg)],['€33.34','€33.33','€33.33'])
        for bad in ('-5','1e6','NaN','1.234','10000000',''):
            wrong=copy.deepcopy(prizes);wrong['4']=bad
            with self.subTest(bad=bad),self.assertRaises(ValueError):
                validate_rewards({'prizes':wrong})

    def test_deprecated_time_window_contract_and_no_private_key_in_output(self):
        fake=FakeRequests({'cache_duration':300,'ranking':[
            {'rank':1,'total':563744,'currency':'EUR','user':{'hash_id':'ref-1','name':'Ha*********ms'}}]})
        start,end=1731000000,1731600000
        api=RaceAPI({},KEYS,requester=fake)
        payload=api.legacy_window(start,end)
        url,kw=fake.last
        self.assertEqual(url,API_ORIGIN+LEGACY_PATH.format(publicKey=KEYS['empiredrop_public_key']))
        self.assertEqual(kw['params'],{'start_timestamp':start,'end_timestamp':end})
        self.assertFalse(kw['allow_redirects'])
        self.assertEqual(kw['headers']['X-Private-Key'],KEYS['empiredrop_private_key'])
        self.assertNotIn('X-Public-Key',kw['headers'])
        rows,meta=normalize_legacy_window(payload,start,end)
        self.assertEqual(rows[0]['wager'],'€5,637.44')
        self.assertEqual(meta['engine'],'RANKING')
        self.assertNotIn(KEYS['empiredrop_private_key'],json.dumps(rows))

    def test_custom_window_scope_changes_and_separate_rewards_persist(self):
        cfg={'source_mode':'legacy_window'}
        store=Store(cfg,{'currency':'USD','enabled':True,
              'prizes':{str(i):'1.00' for i in range(1,16)}})
        store.admin_value['empiredrop_race']={'mode':'custom',
               'start_time':1731000000,'end_time':1731600000}
        board=EmpireDropBoard(Config(),store)
        first=board._scope(schedule(store.admin_value))
        store.admin_value['empiredrop_race']['end_time']+=3600
        self.assertNotEqual(first,board._scope(schedule(store.admin_value)))
        self.assertEqual(board.public()['prizes']['currency'],'USD')

    def test_public_projection_omits_provider_user_ids(self):
        from tests.test_empiredrop_races import FakeRequests, SAMPLE
        store=Store()
        board=EmpireDropBoard(Config(),store)
        remote=FakeRequests()
        with patch('empiredrop_races.requests.get',side_effect=remote.get):
            board.check()
        public=board.public()
        private=board.private_status()
        self.assertEqual(public['rows'][0]['username'],'Ha******')
        self.assertEqual(private['rows'][0]['user_id'],'FAKE_01')
        self.assertNotIn('FAKE_01',json.dumps(public))
        self.assertNotIn(KEYS['empiredrop_private_key'],json.dumps(public))

    def test_activity_log_has_no_arbitrary_message_or_credentials(self):
        log=ActivityLog(3)
        log.record('empiredrop','success','refresh_ok',count=15,duration_ms=210)
        log.record('admin','info','settings_saved')
        with self.assertRaises(ValueError):log.record('admin','info','secret_key',count=1)
        with self.assertRaises(ValueError):log.record('user@example.org','success','refresh_ok')
        val=log.export()
        self.assertEqual(len(val['events']),2)
        self.assertEqual(val['events'][0]['event'],'settings_saved')
        self.assertEqual(len(log.list('empiredrop','success')),1)
        raw=json.dumps(val)
        for sensitive in ['password','secret_key','username','IP address']:
            self.assertNotIn(sensitive,raw)

if __name__=='__main__':unittest.main()
