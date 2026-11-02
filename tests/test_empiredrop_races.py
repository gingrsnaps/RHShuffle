"""Offline tests for the two documented EmpireDrop Races GET endpoints.

These fixtures intentionally contain synthetic credentials and fake wagers.
No test connects to EmpireDrop or exposes the real production keys.
"""
import json
import time
import unittest
from unittest.mock import patch

from empiredrop_races import (RaceAPI, race_catalog, select_race, normalize_race,
                              validate_race_settings, DISCOVER_PATH, DETAIL_PATH)
from empiredrop import EmpireDropBoard
from integrations import ProviderError


class FakeResponse:
    def __init__(self, value, code=200):
        self.code = code
        self.payload = json.dumps(value).encode()
    @property
    def status_code(self): return self.code
    def __enter__(self): return self
    def __exit__(self, *args): return False
    def iter_content(self, size): yield self.payload


class FakeRequests:
    def __init__(self, discover, details, detail_status=200):
        self.discover_payload = discover
        self.details_payload = details
        self.detail_status = detail_status
        self.calls = []
    def get(self, url, **kwargs):
        self.calls.append((url,kwargs))
        if '/api/v1/race/affiliates/' in url:
            return FakeResponse(self.discover_payload)
        if '/api/v1/affiliate-partner/races/' in url:
            return FakeResponse(self.details_payload, self.detail_status)
        raise AssertionError('Unexpected endpoint: '+url)


ACTIVE = {'slug':'red-november', 'name':'Red November', 'status':'active'}
CREDS = {'empiredrop_public_key':'pk_prod_EXAMPLE_ONLY',
         'empiredrop_private_key':'sk_prod_EXAMPLE_ONLY'}


class RaceTests(unittest.TestCase):
    def test_documented_paths_are_used_without_credentials_in_response(self):
        remote=FakeRequests({'data':[ACTIVE]}, {'data':{'leaderboard':[{'username':'Alpha','wagered':123}]}})
        api=RaceAPI({},CREDS, requester=remote)
        races,_=api.discover()
        self.assertEqual(races[0]['slug'], 'red-november')
        details=api.details('red-november')
        self.assertEqual(details['data']['leaderboard'][0]['username'], 'Alpha')
        self.assertEqual(len(remote.calls),2)
        self.assertTrue(remote.calls[0][0].endswith(DISCOVER_PATH.format(publicKey=CREDS['empiredrop_public_key'])))
        self.assertTrue(remote.calls[1][0].endswith(DETAIL_PATH.format(slug='red-november')))
        for _,kwargs in remote.calls:
            self.assertFalse(kwargs['allow_redirects'])
            self.assertNotIn(CREDS['empiredrop_private_key'],str(kwargs))

    def test_private_key_sent_only_on_detail_when_configured(self):
        remote=FakeRequests([ACTIVE], {'leaderboard':[]})
        api=RaceAPI({'race_auth_mode':'private_header'},CREDS,requester=remote)
        api.discover();api.details('red-november')
        self.assertNotIn(CREDS['empiredrop_private_key'],str(remote.calls[0]))
        self.assertEqual(remote.calls[1][1]['headers']['X-Private-Key'], CREDS['empiredrop_private_key'])

    def test_invalid_host_slug_and_redirect_rejected(self):
        with self.assertRaises(ValueError): validate_race_settings({'api_base_url':'https://evil.com'})
        with self.assertRaises(ValueError): validate_race_settings({'api_base_url':'https://empiredrop.com@evil.com'})
        with self.assertRaises(ProviderError): RaceAPI({},CREDS).details('../other')
        remote=FakeRequests([ACTIVE],[],302)
        with self.assertRaises(ProviderError) as err: RaceAPI({},CREDS,requester=remote).details('red-november')
        self.assertEqual(err.exception.kind,'redirect')

    def test_discovery_and_unique_active_selection(self):
        races=race_catalog({'data':{'races':[ACTIVE,{'slug':'old','status':'ended'}]}})
        self.assertEqual(select_race(races,validate_race_settings({}))['slug'],'red-november')
        with self.assertRaises(ProviderError):
            select_race(races+[{'slug':'another','status':'active','start_time':None,'end_time':None}],validate_race_settings({}))
        self.assertEqual(select_race(races,validate_race_settings({'race_slug':'old'}))['slug'],'old')

    def test_confirmed_monetary_field_required_and_duplicate_is_not_summed(self):
        payload={'data':{'leaderboard':[
            {'username':'Alpha','wagered':'250.75','id':'abc'},
            {'username':'AlphaRenamed','wagered':'110.00','id':'abc'},
            {'username':'Beta','wagered':99,'id':'def'},
        ]}}
        options={'race_verified_fields':True,'race_user_id_field':'id'}
        self.assertEqual(normalize_race(payload,options), [
            {'rank':1,'username':'Alpha','wager':'€250.75'},
            {'rank':2,'username':'Beta','wager':'€99.00'}])
        with self.assertRaises(ProviderError): normalize_race(payload,{})
        with self.assertRaises(ProviderError): normalize_race({'leaderboard':[{'username':'A','deposits':200}]},options)

    def test_no_credential_values_in_shape_probe(self):
        remote=FakeRequests([ACTIVE], {'data':{'leaderboard':[{'username':'Alpha','wagered':'123','secret':'not-returned'}]}})
        probe=RaceAPI({},CREDS,requester=remote).probe('red-november')
        serialized=json.dumps(probe)
        self.assertIn('username',serialized)
        self.assertNotIn('Alpha',serialized)
        self.assertNotIn('not-returned',serialized)
        self.assertNotIn(CREDS['empiredrop_private_key'],serialized)

    def test_empty_valid_race_is_not_a_transport_error(self):
        self.assertEqual(normalize_race({'leaderboard':[]},{'race_verified_fields':True}),[])

    def test_default_auto_select_is_enabled(self):
        self.assertTrue(validate_race_settings({})['auto_select'])


class FakeStore:
    def __init__(self):
        self.admin_value={'empiredrop_races':{'race_verified_fields':True}}
        self.saved={}
    def admin(self): return (1,self.admin_value)
    def live(self,name): return self.saved.get(name)
    def publish(self,name,value,*args): self.saved[name]=value


class FakeConfig:
    empiredrop={}
    credentials=CREDS
    sources={k:'private/settings.json' for k in CREDS}


class WorkerTests(unittest.TestCase):
    def test_new_worker_uses_race_endpoints_publishes_and_preserves_on_failure(self):
        store=FakeStore(); board=EmpireDropBoard(FakeConfig(),store)
        remote=FakeRequests([ACTIVE], {'leaderboard':[{'username':'Alpha','wagered':'99.5'}]})
        with patch('empiredrop_races.requests.get',side_effect=remote.get):
            board.check()
        self.assertEqual(board.public()['rows'][0]['username'],'Al******')
        self.assertEqual(board.private_status()['race_meta']['slug'],'red-november')
        self.assertEqual(board.private_status()['rows'][0]['wager'],'€99.50')
        self.assertEqual(len(remote.calls),2)
        # Provider failures do not erase a verified prior leaderboard.
        with patch('empiredrop_races.requests.get',side_effect=Exception('broken')):
            # ProviderError is the safe expected transport failure path.
            pass
        with patch('empiredrop_races.requests.get',side_effect=__import__('requests').ConnectionError('offline')):
            board.check()
        self.assertEqual(board.private_status()['rows'][0]['username'],'Alpha')
        self.assertIn('delayed',board.public()['label'])


if __name__ == '__main__': unittest.main()
