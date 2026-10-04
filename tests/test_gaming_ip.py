"""Shared connections, private rankings and backwards-compatible RedPoints saves."""
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

    def test_shared_ip_players_keep_separate_wallets_and_private_records(self):
        game=self.app.extensions['gaming']; ip='198.51.100.1'
        owner=game.view('one','First',client_ip=ip)
        result=game.bet('one','First',self.body(owner),client_ip=ip)
        for name in ('', 'Second'):
            other=game.view('two',name,client_ip=ip)
            self.assertEqual(other['balance'],100000)
            self.assertIsNone(other['play_blocked'])
            self.assertEqual(other['receipts'],[])
            self.assertNotIn('First',json.dumps(other))
        played=game.bet('two','Second',self.body(other),client_ip=ip)
        self.assertTrue(verify(played['receipt']))
        self.assertEqual(game.view('one','First',client_ip=ip),result['wallet'])
        self.assertEqual(len(game.recovery()['players']),2)
        rows=game.leaders()['games']['dice']
        self.assertEqual({row['name'] for row in rows},{'First','Second'})
        self.assertTrue(all(row['ips']==[ip] for row in rows))
        validate_gaming(game.recovery())

    def test_signed_owner_moves_to_another_players_network_without_losing_ledger(self):
        game=self.app.extensions['gaming']
        wallet=game.view('one','First',client_ip='192.0.2.1')
        paid=game.bet('one','First',self.body(wallet),client_ip='192.0.2.1')['wallet']
        self.assertEqual(game.view('one','First',client_ip='192.0.2.2'),paid)
        other=game.view('two','Second',client_ip='192.0.2.3')
        self.assertEqual(game.view('one','First',client_ip='192.0.2.3'),paid)
        self.assertEqual(game.view('two','Second',client_ip='192.0.2.3'),other)
        validate_gaming(game.recovery())

    def test_missing_or_invalid_ip_never_blocks_play(self):
        self.assertEqual(canonical_ip('::ffff:192.0.2.1'),'192.0.2.1')
        self.assertEqual(canonical_ip('2001:0db8::0001'),'2001:db8::1')
        game=self.app.extensions['gaming']
        for n,address in enumerate((None,'unknown','192.0.2.1, 192.0.2.2','fe80::1%eth0','192.0.2.1','::ffff:192.0.2.1')):
            who=str(n);wallet=game.confirm_community_name(who,'Player'+who,client_ip=address)
            self.assertEqual(wallet['balance'],100000)
            self.assertIsNone(wallet['play_blocked'])
            result=game.bet(who,'Player'+who,self.body(wallet),client_ip=address)
            self.assertTrue(verify(result['receipt']))
        self.assertEqual(len(game.recovery()['players']),6)
        with patch('storage.atomic_json',side_effect=AssertionError('Idle write')):
            game.view('0','Player0',client_ip=None)
        validate_gaming(game.recovery())

    def test_one_hundred_players_can_register_and_bet_on_one_ip(self):
        game=self.app.extensions['gaming']
        def play(n):
            who=str(n);name='Player'+who;ip='192.0.2.1'
            wallet=game.confirm_community_name(who,name,client_ip=ip)
            return game.bet(who,name,self.body(wallet),client_ip=ip)
        with ThreadPoolExecutor(max_workers=10) as pool:
            results=list(pool.map(play,range(100)))
        self.assertTrue(all(result['ok'] and verify(result['receipt']) for result in results))
        self.assertEqual(len(game.recovery()['players']),100)
        self.assertEqual(game.leaders()['counts']['dice'],dict(players=100,rounds=100))
        self.assertTrue(all(r['ips']==['192.0.2.1'] for r in game.leaders()['games']['dice']))
        validate_gaming(game.recovery())

    def test_proxy_headers_are_tracking_only_and_only_trusted_when_configured(self):
        game=self.app.extensions['gaming']
        headers={'X-Forwarded-For':'192.0.2.222','DO-Connecting-IP':'192.0.2.223'}
        client=self.app.test_client();client.environ_base['REMOTE_ADDR']='198.51.100.1'
        value=client.get('/gaming/api/state',headers=headers).json
        headers['X-CSRF-Token']=value['player_csrf']
        self.assertEqual(client.post('/gaming/api/profile',headers=headers,json={'username':'Direct'}).status_code,200)
        addresses=game.recovery()['ip_guard']['addresses'].values()
        self.assertIn('198.51.100.1',addresses);self.assertNotIn('192.0.2.223',addresses)
        self.app.extensions['settings'].proxy=True
        for ip in ('192.0.2.10','192.0.2.10',None):
            client=self.app.test_client();headers={'DO-Connecting-IP':ip} if ip else {}
            value=client.get('/gaming/api/state',headers=headers).json
            headers['X-CSRF-Token']=value['player_csrf']
            saved=client.post('/gaming/api/profile',headers=headers,json={'username':'SharedConnection'}).json
            self.assertEqual(saved['wallet']['balance'],100000,saved)
            self.assertIsNone(saved['wallet']['play_blocked'])
            played=client.post('/gaming/api/bet',headers=headers,json=self.body(saved['wallet']))
            self.assertEqual(played.status_code,200,played.text)
        self.assertEqual(len(game.recovery()['players']),4)

    def test_old_exclusive_claims_migrate_and_allow_new_players(self):
        game=self.app.extensions['gaming'];ip='192.0.2.1'
        before=game.confirm_community_name('old','Original',client_ip=ip)
        with game.store.connection(transaction=True) as conn:
            guard=conn['gaming']['ip_guard'];guard['version']=1
            guard['claims']={digest:owners[0] for digest,owners in guard['claims'].items()}
        validate_gaming(game.recovery())
        # Importing an old recovery while running also uses the migration path.
        new=game.confirm_community_name('new','NewPlayer',client_ip=ip)
        self.assertIsNone(new['play_blocked'])
        self.assertEqual(game.view('old','Original',client_ip=ip),before)
        saved=game.recovery();self.assertEqual(saved['ip_guard']['version'],2)
        self.assertEqual(len(next(iter(saved['ip_guard']['claims'].values()))),2)
        validate_gaming(saved)

    def test_full_tracking_directory_does_not_block_wallets_or_idle_polls(self):
        game=self.app.extensions['gaming']
        game.view('one','First',client_ip='192.0.2.1')
        with patch('gaming.MAX_IP_BINDINGS',1):
            other=game.confirm_community_name('two','Second',client_ip='192.0.2.1')
            result=game.bet('two','Second',self.body(other),client_ip='192.0.2.2')
            self.assertTrue(result['ok'])
            with patch('storage.atomic_json',side_effect=AssertionError('Idle write')):
                self.assertIsNone(game.view('two','Second',client_ip='192.0.2.2')['play_blocked'])
        validate_gaming(game.recovery())

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

    def test_new_week_restarts_shared_wallets_and_tracking(self):
        game=self.app.extensions['gaming'];now=time.time();edge=season(now)['end_time']
        game.view('a','First',edge-1,client_ip='192.0.2.1')
        b=game.view('b','Second',edge,client_ip='192.0.2.1')
        self.assertEqual(b['balance'],100000)
        a=game.view('a','First',edge,client_ip='192.0.2.1')
        self.assertIsNone(a['play_blocked']);self.assertEqual(a['balance'],100000)
        self.assertEqual(len(game.recovery()['players']),2)

    def test_app_restart_funds_every_saved_player_and_keeps_names_and_records(self):
        from wager_backend import create_app
        clients=[self.player('Restart'+str(n))[0] for n in range(2)]
        for client in clients:self.play(client,'dice',time.time())
        game=self.app.extensions['gaming']
        with game.store.connection(transaction=True) as conn:
            for player,balance in zip(conn['gaming']['players'].values(),(0,333333)):
                player['balance_adjustment']=balance-100000-sum(s['net'] for s in player['stats'].values())
                player['balance']=balance
        before=game.recovery();validate_gaming(before)
        # Reconstruct the real app against the persisted JSON, as a restart does.
        self.r.store.close()
        restarted=create_app(self.root,testing=True)
        self.addCleanup(restarted.extensions['runtime'].store.close)
        after=restarted.extensions['gaming'].recovery()
        for key,original in before['players'].items():
            saved=after['players'][key];self.assertEqual(saved['balance'],100000)
            for field in ('name','community_name_confirmed','stats','receipts','server_seed','nonce'):
                self.assertEqual(saved[field],original[field],field)
        for client in clients:
            restored=restarted.test_client();restored.set_cookie('rh_raider',client.get_cookie('rh_raider').value)
            state=restored.get('/gaming/api/state').json
            self.assertFalse(state['wallet']['needs_profile'])
            result=restored.post('/gaming/api/bet',json=self.body(state['wallet']),headers={'X-CSRF-Token':state['player_csrf']})
            self.assertEqual(result.status_code,200,result.text)
        validate_gaming(restarted.extensions['gaming'].recovery())

    def test_restart_retains_active_blackjack_and_its_fairness_receipt(self):
        from test_blackjack import BlackjackWalletTests
        game,body,result=BlackjackWalletTests.opened(self)
        original=game.recovery()['players'][player_key('bj')]
        self.assertEqual(game.restart_balances()['restored'],1)
        restored=game.recovery()['players'][player_key('bj')]
        self.assertEqual(restored['balance'],100000)
        for field in ('blackjack','server_seed','stats','receipts','nonce'):
            self.assertEqual(restored[field],original[field])
        hand=result['wallet']['blackjack']
        final=game.blackjack_action('bj','RedCard',dict(round_id=hand['round_id'],step=hand['step'],action='stand',action_id='restart-stand'),client_ip=None)
        self.assertTrue(verify(final['receipt'],body['commitment']))
        validate_gaming(game.recovery())

    def test_shared_ip_refresh_only_changes_own_points_and_keeps_records(self):
        first,_=self.player('One');self.play(first,'dice',time.time())
        before=first.get('/gaming/api/state').json
        other=self.app.test_client();other.environ_base['REMOTE_ADDR']=first.environ_base['REMOTE_ADDR']
        state=other.get('/gaming/api/state').json
        saved=other.post('/gaming/api/profile',json={'username':'Two'},headers={'X-CSRF-Token':state['player_csrf']}).json
        self.play(other,'plinko',time.time())
        state=other.get('/gaming/api/state').json
        body=dict(version=state['wallet']['version'],season=state['wallet']['season']['id'])
        self.assertEqual(other.post('/gaming/api/refresh',json=body).status_code,400)
        response=other.post('/gaming/api/refresh',json=body,headers={'X-CSRF-Token':state['player_csrf']})
        self.assertEqual(response.status_code,200,response.text)
        self.assertEqual(response.json['wallet']['balance'],100000)
        self.assertEqual(response.json['wallet']['stats'],state['wallet']['stats'])
        self.assertEqual(response.json['wallet']['receipts'],state['wallet']['receipts'])
        self.assertEqual(first.get('/gaming/api/state').json['wallet'],before['wallet'])
        validate_gaming(self.app.extensions['gaming'].recovery())

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
        for item in ('dice','keno','plinko','blackjack'):
            self.assertEqual(len(saved['games'][item]),5)
            self.assertEqual(saved['counts'][item],dict(players=7,rounds=7))
            self.assertTrue(all(row['ips'] and row['bets']==1 for row in saved['games'][item]))
        self.assertIn('arcade3',saved['release'])
