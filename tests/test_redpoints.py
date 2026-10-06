"""Real wallet/API tests; synthetic seeds and players, never live providers."""
import copy
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime
from fractions import Fraction
import json
from math import comb
from pathlib import Path
import time
import unittest
from unittest.mock import patch

import test_app
from fairness import GAMES, VERSION, LEGACY_VERSION, commitment, outcome, table, verify
from gaming import Gaming, GamingError, season, validate_gaming
from race_support import EASTERN
from storage import StoreError
from wager_backend import create_app


class RedPointsTests(unittest.TestCase):
    setUp = test_app.AppTests.setUp

    def player(self, name='RedPlayer'):
        client=self.app.test_client()
        self.next_ip = getattr(self, 'next_ip', 0) + 1
        client.environ_base['REMOTE_ADDR'] = '198.51.100.' + str(self.next_ip)
        state=client.get('/gaming/api/state').json
        response=client.post('/gaming/api/profile', json={'username':name}, headers={'X-CSRF-Token':state['player_csrf']})
        self.assertEqual(response.status_code,200,response.text)
        return client,response.json

    def body(self, wallet, game='dice', **values):
        options={'dice':dict(chance=50,side='under'),'keno':dict(picks=list(range(1,11)),risk='medium'),'plinko':dict(rows=16,risk='high'),'blackjack':dict(decks=6),'limbo':dict(target=200),'coinflip':dict(side='heads'),'poker':dict(variant='texas_holdem',button=wallet.get('poker_button','player')),'baccarat':dict(decks=8,side='banker')}[game]
        return dict(rules_version=VERSION, game=game, request_id='test-bet-'+str(wallet['nonce']), season=wallet['season']['id'],
                    nonce=wallet['nonce'], commitment=wallet['commitment'], client_seed='player-chosen-seed',
                    client_salt='0123456789abcdef'*2,wager=100,options=options,**values)

    def finish_hand(self, client, response, csrf):
        if response.json.get('receipt') is None and response.json.get('wallet', {}).get('blackjack'):
            hand=response.json['wallet']['blackjack']
            response=client.post('/gaming/api/blackjack/action', json=dict(round_id=hand['round_id'], step=hand['step'], action='stand', action_id='finish-test-hand'), headers={'X-CSRF-Token':csrf})
            self.assertEqual(response.status_code,200,response.text)
        while response.json.get('receipt') is None and response.json.get('wallet', {}).get('poker'):
            hand=response.json['wallet']['poker']
            response=client.post('/gaming/api/poker/action', json=dict(variant='texas_holdem',round_id=hand['round_id'],step=hand['step'],move=dict(action='check' if hand['legal']['check'] else 'call',amount=0),action_id='finish-poker-hand-'+str(hand['step'])), headers={'X-CSRF-Token':csrf})
            self.assertEqual(response.status_code,200,response.text)
        return response

    def play(self, client, game, now):
        value=client.get('/gaming/api/state').json
        body=self.body(value['wallet'],game)
        with patch('gaming.time.time',return_value=now):
            response=client.post('/gaming/api/bet',json=body,headers={'X-CSRF-Token':value['player_csrf']})
        self.assertEqual(response.status_code,200,response.text)
        response = self.finish_hand(client, response, value['player_csrf'])
        self.assertTrue(verify(response.json['receipt'],body['commitment']))
        return response.json,body

    def test_one_balance_across_three_games_refresh_and_name_edits(self):
        client,value=self.player()
        self.assertEqual(value['wallet']['balance'],100000)
        now=time.time()
        expected=100000
        for n,game in enumerate(GAMES):
            result,body=self.play(client,game,now+n*2)
            expected+=result['receipt']['net']
            self.assertEqual(result['wallet']['balance'],expected)
            self.assertNotEqual(result['wallet']['commitment'],body['commitment'])
            self.assertEqual(client.get('/gaming/'+game).status_code,200)
        state=client.get('/gaming/api/state').json
        with patch('gaming.time.time',return_value=now+61):
            renamed=client.post('/gaming/api/profile',json={'username':'NewRedName'},headers={'X-CSRF-Token':state['player_csrf']})
        self.assertEqual(renamed.status_code,200,renamed.text)
        self.assertEqual(renamed.json['wallet']['balance'],expected)
        self.assertEqual(client.get('/gaming/api/state').json['wallet']['nonce'],len(GAMES))
        self.assertEqual(client.get('/play/api/state').json['state']['you']['display_name'],'NewRedName')

    def test_duplicate_response_after_lost_reply_and_concurrent_tabs(self):
        client,value=self.player()
        body=self.body(value['wallet'])
        api=lambda:client.post('/gaming/api/bet',json=body,headers={'X-CSRF-Token':value['player_csrf']})
        first=api().json; again=api().json
        self.assertTrue(again['duplicate']);self.assertEqual(first['receipt'],again['receipt'])
        self.assertEqual(again['wallet']['nonce'],1)
        changed={**body,'request_id':'different-request'}
        self.assertEqual(client.post('/gaming/api/bet',json=changed,headers={'X-CSRF-Token':value['player_csrf']}).status_code,409)

    def test_atomic_concurrent_wallet_debit(self):
        game=self.app.extensions['gaming']; wallet=game.view('parallel','Parallel', client_ip='198.51.100.1')
        body=self.body(wallet)
        with ThreadPoolExecutor(max_workers=5) as pool:
            results=list(pool.map(lambda _:game.bet('parallel','Parallel',body, client_ip='198.51.100.1'),range(5)))
        self.assertEqual(sum(not result['duplicate'] for result in results),1)
        self.assertEqual(game.view('parallel','Parallel', client_ip='198.51.100.1')['nonce'],1)

    def test_tuesday_reset_and_dst_without_reloading_accounts(self):
        cutoff=datetime(2026,11,3,18,tzinfo=EASTERN).timestamp()
        game=self.app.extensions['gaming']; wallet=game.view('weekly','Weekly',cutoff-2, client_ip='198.51.100.1')
        self.assertEqual(wallet['season']['end_time']-wallet['season']['start_time'],169*3600)
        body=self.body(wallet)
        bet=game.bet('weekly','Weekly',body,cutoff-2, client_ip='198.51.100.1')
        reset=game.view('weekly','Weekly',cutoff, client_ip='198.51.100.1')
        self.assertEqual(reset['balance'],100000)
        self.assertTrue(all(row['bets']==0 for row in reset['stats'].values()))
        self.assertEqual(reset['nonce'],1)
        self.assertEqual(reset['receipts'][0],bet['receipt'])
        self.assertTrue(game.bet('weekly','Weekly',body,cutoff+1, client_ip='198.51.100.1')['duplicate'])
        with self.assertRaises(GamingError):game.bet('weekly','Weekly',{**body,'request_id':'a-new-id'},cutoff+2, client_ip='198.51.100.1')

    def test_tampering_overdraft_and_csrf_rejected(self):
        client,value=self.player();body=self.body(value['wallet'])
        for values,status in [({'wager':True},422),({'wager':100001},409),({'wager':2**53},422),({'wager':-5},422),
                              ({'options':{'chance':100,'side':'under'}},422),({'commitment':'a'*64},409),
                              ({'nonce':9},409),({'options':{'chance':50,'side':'bad'}},422),({'client_salt':'bad'},422)]:
            response=client.post('/gaming/api/bet',json={**body,**values},headers={'X-CSRF-Token':value['player_csrf']})
            self.assertEqual(response.status_code,status,response.text)
        other,foreign=self.player('Another')
        self.assertEqual(other.post('/gaming/api/bet',json=self.body(foreign['wallet']),headers={'X-CSRF-Token':value['player_csrf']}).status_code,400)
        self.assertEqual(client.get('/gaming/api/state').json['wallet']['balance'],100000)
        self.assertEqual(client.get('/gaming/api/state').json['wallet']['nonce'],0)

    def test_save_failure_rolls_back_wager_and_seed(self):
        game=self.app.extensions['gaming'];before=game.view('writer','Writer', client_ip='198.51.100.1'); body=self.body(before)
        with patch('storage.atomic_json',side_effect=OSError('disk full')):
            with self.assertRaises(StoreError):game.bet('writer','Writer',body, client_ip='198.51.100.1')
        self.assertEqual(game.view('writer','Writer', client_ip='198.51.100.1'),before)

    def test_top_five_for_each_game_private_and_sorted_by_net(self):
        game=self.app.extensions['gaming'];now=time.time()
        for n in range(7):
            for index,item in enumerate(GAMES):
                wallet=game.view('private'+str(n),'PrivatePlayer'+str(n), client_ip='198.51.100.'+str(n+1))
                result=game.bet('private'+str(n),'PrivatePlayer'+str(n),self.body(wallet,item),now+index*2, client_ip='198.51.100.'+str(n+1))
                if item=='blackjack' and not result['receipt']:
                    hand=result['wallet']['blackjack']
                    game.blackjack_action('private'+str(n),'PrivatePlayer'+str(n),dict(round_id=hand['round_id'],step=hand['step'],action='stand',action_id='top-five-stand'),now+index*2,client_ip='198.51.100.'+str(n+1))
                while item=='poker' and not result['receipt']:
                    hand=result['wallet']['poker']
                    result=game.poker_action('private'+str(n),'PrivatePlayer'+str(n),dict(variant='texas_holdem',round_id=hand['round_id'],step=hand['step'],move=dict(action='check' if hand['legal']['check'] else 'call',amount=0),action_id='top-five-move-'+str(hand['step'])),now+index*2,client_ip='198.51.100.'+str(n+1))
        value=self.client.get('/admin/gaming/status').json
        for item in GAMES:
            rows=value['games'][item]
            self.assertEqual(len(rows),5)
            self.assertEqual([r['net'] for r in rows],sorted((r['net'] for r in rows),reverse=True))
        guest=self.app.test_client()
        self.assertEqual(guest.get('/admin/gaming/status').status_code,401)
        for url in ('/','/history','/gaming','/gaming/api/state','/gaming/api/receipts'):
            self.assertNotIn('PrivatePlayer',guest.get(url).text)
        self.assertIn('PrivatePlayer',self.client.get('/admin').text)

    def test_recovery_retains_wallet_seed_nonce_receipts_and_cookie_identity(self):
        client,_=self.player();self.play(client,'keno',time.time())
        before=client.get('/gaming/api/state').json['wallet']
        backup=self.client.get('/admin/recovery-backup')
        self.assertIn('redpoints',backup.json)
        target=self.root/'restored';(target/'private').mkdir(parents=True)
        (target/'private/recovery.seed.json').write_bytes(backup.data)
        restored=create_app(target,testing=True);self.addCleanup(restored.extensions['runtime'].store.close)
        other=restored.test_client();other.set_cookie('rh_raider',client.get_cookie('rh_raider').value)
        after=other.get('/gaming/api/state').json['wallet']
        self.assertEqual(after['balance'],100000)  # Restoring starts a new server.
        for key in ('name','needs_profile','stats','receipts','nonce','commitment','blackjack'):
            self.assertEqual(after[key],before[key],key)
        state=backup.json['redpoints'];next(iter(state['players'].values()))['balance']+=1
        with self.assertRaises(ValueError):validate_gaming(state)

    def test_one_hundred_distinct_networks_can_all_play(self):
        game=self.app.extensions['gaming']
        for n in range(100):
            wallet=game.view('shared-'+str(n),'Shared'+str(n), client_ip='198.51.100.'+str(n+1))
            self.assertEqual(wallet['balance'],100000)
        self.assertEqual(len(game.recovery()['players']),100)

    def test_live_seed_is_never_returned_and_receipt_tamper_is_detected(self):
        client,value=self.player()
        seed=next(iter(self.app.extensions['gaming'].recovery()['players'].values()))['server_seed']
        self.assertNotIn(seed,client.get('/gaming/api/state').text)
        result,body=self.play(client,'plinko',time.time())
        r=result['receipt'];self.assertEqual(r['server_seed'],seed)
        for key,new in [('payout',r['payout']+1),('nonce',r['nonce']+1),('client_seed','changed')]:
            self.assertFalse(verify({**r,key:new},body['commitment']))

    def test_wallet_poll_reuses_etag_until_a_committed_change(self):
        client, _ = self.player()
        response = client.get('/gaming/api/state')
        etag = response.headers['ETag']
        unchanged = client.get('/gaming/api/state', headers={'If-None-Match': etag})
        self.assertEqual(unchanged.status_code, 304)
        self.assertEqual(unchanged.data, b'')
        self.play(client, 'dice', time.time())
        changed = client.get('/gaming/api/state', headers={'If-None-Match': etag})
        self.assertEqual(changed.status_code, 200)
        self.assertNotEqual(changed.headers['ETag'], etag)

    def test_recovery_checkpoint_notices_wagers_without_marking_idle_polls(self):
        client, _ = self.player()
        self.assertEqual(self.client.get('/admin/recovery-backup').status_code, 200)
        before = self.client.get('/admin/status').json['checkpoint']
        self.assertFalse(before['changes'], before)
        client.get('/gaming/api/state')
        self.assertFalse(self.client.get('/admin/status').json['checkpoint']['changes'])
        self.play(client, 'dice', time.time())
        after = self.client.get('/admin/status').json['checkpoint']
        self.assertTrue(after['changes'])
        self.assertIn('RedPoints wallets or fairness receipts changed', after['details'])

    def test_full_balance_can_be_wagered_in_every_game(self):
        for game in GAMES:
            client, state = self.player('FullBalance' + game)
            body = {**self.body(state['wallet'], game), 'wager':100000}
            response = client.post('/gaming/api/bet', json=body,
                                   headers={'X-CSRF-Token':state['player_csrf']})
            self.assertEqual(response.status_code, 200, response.text)
            response = self.finish_hand(client, response, state['player_csrf'])
            self.assertEqual(response.json['receipt']['wager'], 100000)
            self.assertEqual(response.json['wallet']['balance'], response.json['receipt']['payout'])
            self.assertTrue(verify(response.json['receipt'], body['commitment']))
        validate_gaming(self.app.extensions['gaming'].recovery())

    def test_consecutive_distinct_bets_need_no_clock_advance(self):
        game = self.app.extensions['gaming']
        now = time.time()
        wallet = game.view('no-delay', 'NoDelay', now, client_ip='198.51.100.1')
        for nonce in range(40):
            body = {**self.body(wallet), 'wager':1}
            result = game.bet('no-delay', 'NoDelay', body, now, client_ip='198.51.100.1')
            self.assertEqual(result['receipt']['nonce'], nonce)
            self.assertEqual(result['receipt']['at'], int(now))
            self.assertFalse(result['duplicate'])
            wallet = result['wallet']
        duplicate = game.bet('no-delay', 'NoDelay', body, now, client_ip='198.51.100.1')
        self.assertTrue(duplicate['duplicate'])
        self.assertEqual(duplicate['wallet']['nonce'], 40)
        validate_gaming(game.recovery())

    def test_large_wager_receipt_survives_full_recovery(self):
        client, value = self.player()
        body = {**self.body(value['wallet'], 'keno'), 'wager':75000}
        result = client.post('/gaming/api/bet', json=body,
                             headers={'X-CSRF-Token':value['player_csrf']})
        self.assertEqual(result.status_code, 200, result.text)
        target = self.root / 'large-wager-restore'
        (target/'private').mkdir(parents=True)
        (target/'private/recovery.seed.json').write_bytes(self.client.get('/admin/recovery-backup').data)
        restored = create_app(target, testing=True)
        self.addCleanup(restored.extensions['runtime'].store.close)
        other = restored.test_client()
        other.set_cookie('rh_raider', client.get_cookie('rh_raider').value)
        wallet = other.get('/gaming/api/state').json['wallet']
        self.assertEqual(wallet['balance'], 100000)  # Startup restores the allowance.
        for key in ('name', 'stats', 'nonce', 'commitment', 'receipts', 'blackjack'):
            self.assertEqual(wallet[key], result.json['wallet'][key], key)
        self.assertTrue(verify(wallet['receipts'][0], body['commitment']))


class FairMathTests(unittest.TestCase):
    def test_published_tables_bound_expected_return(self):
        for game,sizes in [('keno',range(1,11)),('plinko',(8,12,16))]:
            for size in sizes:
                for risk in ('low','medium','high'):
                    values=table(game,size,risk,LEGACY_VERSION)
                    probabilities=[Fraction(comb(size,i)*comb(40-size,10-i),comb(40,10)) if game=='keno' else Fraction(comb(size,i),2**size) for i in range(size+1)]
                    self.assertEqual(sum(probabilities),1)
                    rtp=sum(p*Fraction(v,10000) for p,v in zip(probabilities,values))
                    self.assertLessEqual(rtp,Fraction(99,100))
                    self.assertGreaterEqual(rtp,Fraction(9899,10000))
                    if game=='plinko':self.assertEqual(values,tuple(reversed(values)))

    def test_draw_shapes_are_deterministic_without_duplicate_keno_numbers(self):
        for n in range(50):
            base=dict(season='1790719200',client_seed='example',client_salt='a'*32,nonce=n,wager=100)
            for game,opt in [('keno',dict(picks=[1,2,3],risk='low')),('plinko',dict(rows=16,risk='high')),('dice',dict(chance=50,side='over'))]:
                receipt=dict(base,game=game,options=opt)
                result=outcome('ab'*32,receipt)
                self.assertEqual(result,outcome('ab'*32,receipt))
                if game=='keno':self.assertEqual(len(set(result['drawn'])),10)
                elif game=='plinko':self.assertEqual(result['slot'],sum(result['path']))
                else:self.assertTrue(0<=result['roll']<10000)

if __name__=='__main__':unittest.main()
