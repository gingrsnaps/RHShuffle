"""Seven-game accounting, commitment compatibility and real Poker decisions."""
import copy
import time
import unittest
from concurrent.futures import ThreadPoolExecutor
from unittest.mock import patch

import test_app
import test_redpoints
from fairness import VERSION, V2_VERSION, commitment, outcome, verify, max_payout
from gaming import Gaming, GamingError, player_key, validate_gaming
from poker import PAYTABLE, classify, replay
from storage import StoreError


class FixedDraw:
    def __init__(self, value): self.value = value
    def below(self, size):
        if not 0 <= self.value < size: raise AssertionError('Test draw outside range')
        return self.value


class ExtraRulesTests(unittest.TestCase):
    def receipt(self, game, options, wager=101):
        return dict(rules_version=VERSION, season='1780000000', game=game,
                    client_seed='reference', client_salt='01'*16, nonce=0, wager=wager, options=options)

    def test_coinflip_is_even_and_whole_point_returns_are_exact(self):
        for picked in ('heads', 'tails'):
            values=[]
            for bit in (0, 1):
                with patch('fairness.Draw',return_value=FixedDraw(bit)):
                    values.append(outcome('00'*32,self.receipt('coinflip',dict(side=picked))))
            self.assertEqual(sum(r['won'] for r in values),1)
            self.assertEqual(sorted(r['payout'] for r in values),[0,199])

    def test_limbo_exact_boundary_at_each_target_and_maximum_roll(self):
        size=2**32
        for target in (101,200,1000,99999999,100000000):
            winning_rolls=99*size//target
            for roll,won in ((size-winning_rolls-1,False),(size-winning_rolls,True),(size-1,True),(0,False)):
                with patch('fairness.Draw',return_value=FixedDraw(roll)):
                    result=outcome('00'*32,self.receipt('limbo',dict(target=target)))
                self.assertEqual(result['won'],won)
                self.assertEqual(result['payout'],101*target//100 if won else 0)
                self.assertGreaterEqual(result['multiplier'],100)
            self.assertLessEqual(winning_rolls*target,99*size)

    def test_all_poker_categories_including_ace_low_straight(self):
        cases={
            'royal_flush':[0,9,10,11,12], 'straight_flush':[0,1,2,3,4],
            'four_of_a_kind':[0,13,26,39,1], 'full_house':[0,13,26,1,14],
            'flush':[0,2,4,6,8], 'straight':[0,14,28,42,4],
            'three_of_a_kind':[0,13,26,1,2], 'two_pair':[0,13,1,14,2],
            'jacks_or_better':[10,23,0,1,2], 'no_win':[1,14,0,3,5],
        }
        for label,cards in cases.items(): self.assertEqual(classify(cards),label)
        self.assertEqual(PAYTABLE['royal_flush'],800)
        self.assertEqual(classify([0,13,1,3,5]),'jacks_or_better')
        self.assertEqual(classify([9,22,0,1,2]),'no_win')

    def test_hold_or_replace_every_subset_without_reusing_a_discard(self):
        for mask in range(32):
            holds=[i for i in range(5) if mask & (1<<i)]
            result=replay(FixedDraw(0),100,holds)
            self.assertEqual(result['initial'],list(range(5)))
            self.assertEqual(len(set(result['cards'])),5)
            for i,card in enumerate(result['cards']):
                if i in holds:self.assertEqual(card,result['initial'][i])
                else:self.assertNotIn(card,result['initial'])
            self.assertEqual(result['payout'],100*PAYTABLE[result['category']])
        self.assertEqual(replay(FixedDraw(0),100,list(range(5)))['payout'],5000)
        for bad in ([0,0],[-1],[5],[True],None):
            if bad is not None:
                with self.assertRaises(ValueError):replay(FixedDraw(0),100,bad)


class ExtraWalletTests(unittest.TestCase):
    setUp=test_app.AppTests.setUp
    body=test_redpoints.RedPointsTests.body
    player=test_redpoints.RedPointsTests.player
    play=test_redpoints.RedPointsTests.play
    finish_hand=test_redpoints.RedPointsTests.finish_hand

    def opened(self, who='poker', name='PokerPlayer'):
        game=self.app.extensions['gaming']
        wallet=game.confirm_community_name(who,name,client_ip='192.0.2.1')
        body=self.body(wallet,'poker')
        result=game.bet(who,name,body,client_ip='192.0.2.1')
        return game,body,result

    def test_eight_games_share_a_profile_wallet_and_private_rankings(self):
        client,_=self.player('SevenGames')
        for name in ('dice','keno','plinko','blackjack','limbo','coinflip','poker','baccarat'):
            self.assertEqual(client.get('/gaming/'+name).status_code,200)
            result,_=self.play(client,name,time.time())
            self.assertTrue(verify(result['receipt']))
        rankings=self.client.get('/admin/gaming/status').json
        self.assertEqual(rankings['completed_rounds'],8)
        self.assertEqual(len(rankings['games']),8)
        self.assertTrue(all(rows[0]['name']=='SevenGames' for rows in rankings['games'].values()))
        self.assertEqual(len({rows[0]['player_tag'] for rows in rankings['games'].values()}),1)
        self.assertNotIn('SevenGames',self.app.test_client().get('/gaming/api/state').text)

    def test_poker_reservation_holds_seed_privacy_and_retry(self):
        game,body,opened=self.opened();hand=opened['wallet']['poker']
        self.assertIsNone(opened['receipt']);self.assertEqual(opened['wallet']['balance'],99900)
        initial=hand['initial'];saved=game.recovery()['players'][player_key('poker')]
        self.assertNotIn(saved['server_seed'],str(opened))
        self.assertNotIn('server_seed',str(opened))
        move=dict(round_id=hand['round_id'],holds=[0,2,4],action_id='poker-test-draw')
        result=game.poker_action('poker','PokerPlayer',move,client_ip=None)
        receipt=result['receipt'];self.assertTrue(verify(receipt,body['commitment']))
        self.assertEqual(receipt['result']['initial'],initial)
        for i in move['holds']:self.assertEqual(receipt['result']['cards'][i],initial[i])
        self.assertEqual(result['wallet']['balance'],99900+receipt['payout'])
        self.assertIsNone(result['wallet']['poker'])
        self.assertEqual(result['wallet']['stats']['poker']['bets'],1)
        again=game.poker_action('poker','PokerPlayer',move)
        self.assertTrue(again['duplicate']);self.assertEqual(again['wallet'],result['wallet'])
        self.assertFalse(verify({**receipt,'holds':[1,3]}))
        self.assertFalse(verify({**receipt,'holds':[0,0]}))
        validate_gaming(game.recovery())

    def test_competing_draws_commit_once_and_other_players_cannot_draw(self):
        game,_,opened=self.opened();hand=opened['wallet']['poker']
        body=dict(round_id=hand['round_id'],holds=[],action_id='same-draw-request')
        with ThreadPoolExecutor(max_workers=6) as pool:
            values=list(pool.map(lambda _:game.poker_action('poker','PokerPlayer',body),range(6)))
        self.assertEqual(sum(not value['duplicate'] for value in values),1)
        with self.assertRaises(GamingError):game.poker_action('poker','PokerPlayer',{**body,'action_id':'other-tab-draw','holds':[0]})
        with self.assertRaises(GamingError):game.poker_action('another','Another',body,client_ip='192.0.2.1')
        validate_gaming(game.recovery())

    def test_refresh_restart_grant_and_weekly_boundary_keep_a_pending_hand_consistent(self):
        game,body,result=self.opened();wallet=result['wallet'];hand=wallet['poker']
        original=copy.deepcopy(game.recovery()['players'][player_key('poker')]['poker'])
        game.refresh_balance('poker','PokerPlayer',dict(version=wallet['version'],season=wallet['season']['id']))
        game.grant_everyone('ab'*16,'Admin');game.restart_balances()
        self.assertEqual(game.recovery()['players'][player_key('poker')]['poker'],original)
        restored=Gaming(game.store).view('poker','PokerPlayer')
        self.assertEqual(restored['poker'],hand);self.assertEqual(restored['balance'],100000)
        new=game.view('poker','PokerPlayer',now=wallet['season']['end_time'])
        self.assertIsNone(new['poker']);self.assertEqual(new['balance'],100000)
        self.assertTrue(verify(new['receipts'][0],body['commitment']))
        self.assertEqual(new['receipts'][0]['holds'],list(range(5)))
        self.assertTrue(all(stats['bets']==0 for stats in new['stats'].values()))
        validate_gaming(game.recovery())

    def test_pending_hand_blocks_other_games_and_failed_draw_rolls_back(self):
        game,_,result=self.opened();before=game.recovery();wallet=result['wallet']
        other={**self.body(wallet,'coinflip'),'request_id':'another-game-while-pending'}
        with self.assertRaises(GamingError):game.bet('poker','PokerPlayer',other)
        hand=wallet['poker'];body=dict(round_id=hand['round_id'],holds=[0,3],action_id='disk-fail-draw')
        with patch('storage.atomic_json',side_effect=OSError('disk full')):
            with self.assertRaises(StoreError):game.poker_action('poker','PokerPlayer',body)
        self.assertEqual(game.recovery(),before)
        client,state=self.player('CSRFPlayer')
        self.assertEqual(client.post('/gaming/api/poker/action',json=body).status_code,400)

    def test_v2_blackjack_hand_and_four_game_save_migrate_without_redealing(self):
        game=self.app.extensions['gaming'];wallet=game.view('old','OldPlayer')
        body=self.body(wallet,'blackjack')
        for seed in range(100):
            private=f'{seed:064x}'
            pending={**body,'rules_version':V2_VERSION,'server_seed':private,
                     'commitment':commitment(private),'actions':[],'action_ids':[],'at':int(time.time())}
            if not outcome(private,pending)['ended']:break
        with game.store.connection(transaction=True) as conn:
            player=conn['gaming']['players'][player_key('old')]
            for new in ('limbo','coinflip','poker','baccarat'):player['stats'].pop(new)
            player.update(server_seed=private,blackjack=pending,balance=99900)
        validate_gaming(game.recovery());migrated=Gaming(game.store)
        migrated.restart_balances()
        saved=migrated.recovery()['players'][player_key('old')]
        self.assertEqual(saved['blackjack'],pending);self.assertEqual(len(saved['stats']),8)
        hand=migrated.view('old','OldPlayer')['blackjack']
        result=migrated.blackjack_action('old','OldPlayer',dict(round_id=hand['round_id'],step=0,action='stand',action_id='finish-old-hand'))
        self.assertEqual(result['receipt']['rules_version'],V2_VERSION)
        self.assertTrue(verify(result['receipt']));validate_gaming(migrated.recovery())


if __name__ == '__main__': unittest.main()
