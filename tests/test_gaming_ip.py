"""IP ownership, private rankings and backwards-compatible RedPoints saves."""
import copy
import json
import time
import unittest
from concurrent.futures import ThreadPoolExecutor
from unittest.mock import patch
from pathlib import Path

import test_app
import test_redpoints as redpoints
from fairness import VERSION, LEGACY_VERSION, commitment, outcome, verify, table, table_info
from gaming import Gaming, GamingError, canonical_ip, fresh_stats, player_key, season, validate_gaming


class GamingIPTests(unittest.TestCase):
    setUp = test_app.AppTests.setUp
    body = redpoints.RedPointsTests.body
    player = redpoints.RedPointsTests.player
    finish_hand = redpoints.RedPointsTests.finish_hand
    play = redpoints.RedPointsTests.play

    def test_same_ip_cannot_mint_wallet_or_read_another_player(self):
        game=self.app.extensions['gaming']; ip='198.51.100.1'
        owner=game.view('one','First',client_ip=ip)
        result=game.bet('one','First',self.body(owner),client_ip=ip)
        before=copy.deepcopy(game.recovery())
        for name in ('', 'Second'):
            blocked=game.view('two',name,client_ip=ip)
            self.assertEqual(blocked['balance'],0)
            self.assertEqual(blocked['play_blocked']['code'],'ip_wallet_exists')
            self.assertEqual(blocked['receipts'],[])
            self.assertNotIn('First',json.dumps(blocked))
        with self.assertRaises(GamingError) as exc:
            game.bet('two','Second',self.body(owner),client_ip=ip)
        self.assertEqual(exc.exception.code,'ip_wallet_exists')
        self.assertEqual(before,game.recovery())
        self.assertEqual(game.view('one','First',client_ip=ip),result['wallet'])

    def test_signed_owner_moves_network_and_keeps_ledger(self):
        game=self.app.extensions['gaming']
        wallet=game.view('one','First',client_ip='192.0.2.1')
        paid=game.bet('one','First',self.body(wallet),client_ip='192.0.2.1')['wallet']
        self.assertEqual(game.view('one','First',client_ip='192.0.2.2'),paid)
        other=game.view('two','Second',client_ip='192.0.2.3')
        blocked=game.view('one','First',client_ip='192.0.2.3')
        self.assertEqual(blocked['balance'],paid['balance'])
        self.assertEqual(blocked['play_blocked']['code'],'ip_wallet_exists')
        self.assertEqual(game.view('two','Second',client_ip='192.0.2.3'),other)

    def test_ipv4_ipv6_normalization_and_missing_ip_fail_closed(self):
        self.assertEqual(canonical_ip('::ffff:192.0.2.1'),'192.0.2.1')
        self.assertEqual(canonical_ip('2001:0db8::0001'),'2001:db8::1')
        game=self.app.extensions['gaming']
        game.view('a','One',client_ip='192.0.2.1')
        self.assertEqual(game.view('b','Two',client_ip='::ffff:192.0.2.1')['balance'],0)
        for address in (None,'unknown','192.0.2.1, 192.0.2.2','fe80::1%eth0'):
            self.assertEqual(game.view('bad','Bad',client_ip=address)['play_blocked']['code'],'ip_unavailable')
        self.assertEqual(len(game.recovery()['players']),1)

    def test_simultaneous_registration_claims_ip_once(self):
        game=self.app.extensions['gaming']
        with ThreadPoolExecutor(max_workers=10) as pool:
            results=list(pool.map(lambda n:game.view(str(n),'Player'+str(n),client_ip='192.0.2.1'),range(10)))
        self.assertEqual(sum(r['ip_bound'] for r in results),1)
        self.assertEqual(len(game.recovery()['players']),1)

    def test_proxy_header_is_only_used_when_explicitly_trusted(self):
        game=self.app.extensions['gaming']
        owner,_=self.player()
        attacker=self.app.test_client();attacker.environ_base['REMOTE_ADDR']=owner.environ_base['REMOTE_ADDR']
        result=attacker.get('/gaming/api/state',headers={'X-Forwarded-For':'192.0.2.222','DO-Connecting-IP':'192.0.2.223'}).json
        self.assertEqual(result['wallet']['play_blocked']['code'],'ip_wallet_exists')
        self.app.extensions['settings'].proxy=True
        for ip in ('192.0.2.10','192.0.2.11'):
            client=self.app.test_client()
            headers={'DO-Connecting-IP':ip}
            value=client.get('/gaming/api/state',headers=headers).json
            headers['X-CSRF-Token']=value['player_csrf']
            saved=client.post('/gaming/api/profile',headers=headers,json={'username':'Proxy'+ip[-2:]}).json
            self.assertEqual(saved['wallet']['balance'],100000,saved)
            self.assertIsNone(saved['wallet']['play_blocked'])
        missing=self.app.test_client().get('/gaming/api/state').json
        self.assertEqual(missing['wallet']['play_blocked']['code'],'ip_unavailable')
        self.assertEqual(len(game.recovery()['players']),3)

    def test_legacy_save_keeps_all_balances_seeds_receipts(self):
        game=self.app.extensions['gaming']; now=time.time()
        base=game.view('legacy','Legacy',now,client_ip='192.0.2.1')
        old={**self.body(base,'plinko'),'rules_version':LEGACY_VERSION,'server_seed':'a1'*32,'at':int(now)}
        old['commitment']=commitment(old['server_seed']);result=outcome(old['server_seed'],old)
        old.update(result=result,payout=result['payout'],net=result['payout']-old['wager'])
        with game.store.connection(transaction=True) as conn:
            data=conn['gaming'];data.pop('ip_guard')
            player=data['players'][player_key('legacy')]
            player['stats'].pop('blackjack')
            stats=player['stats']['plinko'];stats.update(bets=1,wagered=old['wager'],paid=old['payout'],net=old['net'],biggest_payout=old['payout'])
            player.update(balance=100000+old['net'],nonce=1,receipts=[old])
        before=game.recovery()['players'][player_key('legacy')]
        fresh=Gaming(game.store);after=fresh.view('legacy','Legacy',client_ip='192.0.2.1')
        self.assertEqual(after['balance'],before['balance']);self.assertEqual(after['receipts'],before['receipts'])
        self.assertEqual(after['commitment'],commitment(before['server_seed']))
        duplicate=fresh.bet('legacy','Legacy',old,client_ip='192.0.2.1')
        self.assertTrue(duplicate['duplicate']);self.assertEqual(duplicate['receipt'],old)
        with self.assertRaises(GamingError) as exc:
            fresh.bet('legacy','Legacy',{**self.body(after),'rules_version':LEGACY_VERSION},client_ip='192.0.2.1')
        self.assertEqual(exc.exception.code,'release_mismatch')
        validate_gaming(fresh.recovery())

    def test_admin_full_names_ips_and_rankings_not_in_public_state(self):
        client,_=self.player('PrivateRedName');self.play(client,'plinko',time.time())
        value=self.client.get('/admin/gaming/status').json
        self.assertEqual(value['games']['plinko'][0]['ips'],['198.51.100.1'])
        for tab in ('overview','gaming'):
            text=self.client.get('/admin?tab='+tab).text
            self.assertIn('gamingLeaders-blackjack',text)
            self.assertIn('PrivateRedName',text);self.assertIn('198.51.100.1',text)
        guest=self.app.test_client()
        self.assertEqual(guest.get('/admin/gaming/status').status_code,401)
        for url in ('/gaming','/gaming/api/state','/gaming/api/receipts'):
            text=guest.get(url).text
            self.assertNotIn('PrivateRedName',text);self.assertNotIn('198.51.100.1',text)

    def test_idle_wallet_and_rank_polls_do_not_rewrite_state(self):
        client,_=self.player()
        with patch('storage.atomic_json',side_effect=AssertionError('Idle write')):
            for _ in range(5):
                self.assertEqual(client.get('/gaming/api/state').status_code,200)
                self.assertEqual(self.client.get('/admin/gaming/status').status_code,200)

    def test_new_week_releases_ip_claim_without_resetting_other_players(self):
        game=self.app.extensions['gaming'];now=time.time();edge=season(now)['end_time']
        game.view('a','First',edge-1,client_ip='192.0.2.1')
        b=game.view('b','Second',edge,client_ip='192.0.2.1')
        self.assertEqual(b['balance'],100000)
        a=game.view('a','First',edge,client_ip='192.0.2.1')
        self.assertEqual(a['play_blocked']['code'],'ip_wallet_exists')
        self.assertEqual(len(game.recovery()['players']),2)

    def test_published_v2_plinko_and_v1_reference_receipts(self):
        for receipt in json.loads((Path(__file__).parent/'fairness_vectors.json').read_text()):
            self.assertTrue(verify(receipt),receipt['request_id'])
        for rows in (8,12,16):
            for risk in ('low','medium','high'):
                values=table('plinko',rows,risk)
                self.assertEqual(values,tuple(reversed(values)))
                self.assertEqual(len(values),rows+1)
                self.assertTrue(98.8<float(table_info('plinko',rows,risk)['rtp_percent'])<99.2)
        self.assertEqual(table('plinko',16,'high')[0],10000000)
        self.assertEqual(max(table('plinko',16,'high')),10000000)

    def test_direct_admin_route_and_empty_state_are_rendered_without_javascript(self):
        from config import RELEASE
        for url in ('/admin', '/admin?tab=gaming', '/admin/gaming'):
            response=self.client.get(url)
            self.assertEqual(response.status_code,200,response.text)
            for game in ('dice','keno','plinko','blackjack'):
                self.assertIn('gamingLeaders-'+game,response.text)
                self.assertIn('gamingCount-'+game,response.text)
            self.assertIn('No completed RedPoints rounds are saved',response.text)
            self.assertIn(RELEASE,response.text)
            self.assertIn('href="/admin/gaming">Gaming top 5',response.text)
        self.assertEqual(self.app.test_client().get('/admin/gaming').status_code,302)

    def test_all_players_are_counted_before_slicing_top_five(self):
        game=self.app.extensions['gaming'];now=time.time()
        for n in range(7):
            who='count-'+str(n);name='CountPlayer'+str(n);ip='192.0.2.'+str(n+1)
            for item in ('dice','keno','plinko','blackjack'):
                wallet=game.view(who,name,now,client_ip=ip)
                result=game.bet(who,name,self.body(wallet,item),now,client_ip=ip)
                if not result['receipt']:
                    hand=result['wallet']['blackjack']
                    game.blackjack_action(who,name,dict(round_id=hand['round_id'],step=0,action='stand',action_id='count-stand'),now,client_ip=ip)
        saved=self.client.get('/admin/gaming/status').json
        self.assertEqual(saved['completed_rounds'],28)
        for item in saved['games']:
            self.assertEqual(len(saved['games'][item]),5)
            self.assertEqual(saved['counts'][item],dict(players=7,rounds=7))
            self.assertTrue(all(row['ips'] and row['bets']==1 for row in saved['games'][item]))
        self.assertIn('arcade2',saved['release'])
