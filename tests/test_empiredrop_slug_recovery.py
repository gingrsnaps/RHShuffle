"""Provider-contract regression tests for stale EmpireDrop race slugs.

These deliberately use fixture credentials and mocked HTTP responses only.
No third-party API is called and no production keys are exposed.
"""
import copy
import time
import unittest
from unittest.mock import patch

from tests.test_empiredrop_races import (
    SAMPLE, LIST, FakeRequests, FakeResponse, Store, Config, API_ORIGIN,
    LIST_PATH,
)
from empiredrop import EmpireDropBoard
from empiredrop_races import select_race
from integrations import ProviderError

class StaleSlugRemote(FakeRequests):
    def __init__(self, catalog=None):
        super().__init__(catalog=catalog)
    def get(self, url, **kwargs):
        if url == API_ORIGIN + '/api/v1/affiliate-partner/races/stale-week':
            self.calls.append((url, kwargs))
            return FakeResponse({'error':'not found'}, 404)
        return super().get(url, **kwargs)

class SlugRecoveryTests(unittest.TestCase):
    def test_stale_slug_recovers_unique_running_wager_race(self):
        store=Store({'source_mode':'races','race_slug':'stale-week','auto_select':True})
        board=EmpireDropBoard(Config(),store)
        fake=StaleSlugRemote()
        with patch('empiredrop_races.requests.get',side_effect=fake.get):
            result=board.check()
        self.assertEqual(result['error'],'')
        self.assertEqual(result['race_meta']['slug'],SAMPLE['race']['slug'])
        self.assertEqual(result['race_meta']['selection'],'recovered')
        self.assertEqual(len(result['rows']),3)
        self.assertEqual(board.public()['rows'][0]['username'],'Ha******')
        self.assertNotIn('user_id',board.public()['rows'][0])
        self.assertIn('saved race slug returned 404',board.private_status()['selection_warning'].lower())
        self.assertEqual(store.admin_value['empiredrop_races']['race_slug'],'stale-week',
                         'The worker must not rewrite administrator settings itself')
        self.assertEqual(len(fake.calls),3)
        for _,kwargs in fake.calls:
            self.assertIn('X-Private-Key',kwargs['headers'])
            self.assertIn('X-Public-Key',kwargs['headers'])

    def test_stale_slug_does_not_guess_when_multiple_wager_races_exist(self):
        other=copy.deepcopy(SAMPLE['race'])
        other['slug']='second-running-race'
        store=Store({'race_slug':'stale-week','auto_select':True})
        board=EmpireDropBoard(Config(),store)
        fake=StaleSlugRemote({'races':[SAMPLE['race'],other]})
        with patch('empiredrop_races.requests.get',side_effect=fake.get):
            result=board.check()
        self.assertEqual(result['error_kind'],'selection')
        self.assertEqual(result['rows'],[])
        self.assertIn('Multiple',result['error'])
        self.assertEqual(len(fake.calls),2)

    def test_stale_slug_without_auto_select_does_not_discover_or_publish(self):
        store=Store({'race_slug':'stale-week','auto_select':False})
        board=EmpireDropBoard(Config(),store)
        fake=StaleSlugRemote()
        with patch('empiredrop_races.requests.get',side_effect=fake.get):
            result=board.check()
        self.assertEqual(result['error_kind'],'scope')
        self.assertEqual(len(fake.calls),1)
        self.assertFalse(board.public()['rows'])

    def test_auto_selection_never_picks_deposit_or_raffle_race(self):
        wrong=copy.deepcopy(SAMPLE['race'])
        wrong['type']='DEPOSIT'
        with self.assertRaises(ProviderError):
            select_race([dict(slug=wrong['slug'],is_active=True,type='DEPOSIT',engine='RANKING')],{})
        with self.assertRaises(ProviderError):
            select_race([dict(slug=wrong['slug'],is_active=True,type='WAGER',engine='RAFFLE')],{})

    def test_new_admin_scope_can_refresh_without_old_cache_hold(self):
        store=Store({'race_slug':'old-week','auto_select':False})
        board=EmpireDropBoard(Config(),store)
        board.saved={'scope':board._scope(board._schedule()),'updated_at':100}
        board.next_allowed=time.monotonic()+500
        store.admin_value['empiredrop_races']['race_slug']='new-week'
        self.assertTrue(board.request_refresh())
        self.assertEqual(board.next_allowed,0)

if __name__=='__main__': unittest.main()
