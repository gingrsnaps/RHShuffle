"""Blackjack rules, durable turns, hidden cards and one-time settlements."""
import copy
import time
import unittest
from concurrent.futures import ThreadPoolExecutor
from unittest.mock import patch

import test_app
import test_redpoints as redpoints
from blackjack import replay, total
from fairness import VERSION, outcome, verify
from gaming import Gaming, GamingError, player_key, season, validate_gaming
from storage import StoreError


class Shoe:
    """Choose known card IDs without replacement to exercise exact rule cases."""
    def __init__(self, cards):
        self.cards=iter(cards);self.shoe=list(range(312));self.cursor=0
    def below(self,size):
        card=next(self.cards);j=self.shoe.index(card,self.cursor)
        offset=j-self.cursor
        self.shoe[self.cursor],self.shoe[j]=self.shoe[j],self.shoe[self.cursor]
        self.cursor+=1
        return offset


class BlackjackRulesTests(unittest.TestCase):
    def test_naturals_push_peek_soft17_double_and_bust(self):
        cases=[
          ([0,9,12,8],[], 'blackjack',250,21,19,100),
          ([0,13,9,22],[], 'push',100,21,21,100),
          ([8,0,9,12],[], 'lose',0,19,21,100),
          ([9,0,8,5],['stand'], 'win',200,19,17,100),
          ([5,8,4,7,9],['double'], 'win',400,21,17,200),
          ([9,8,21,7,4],['hit'], 'lose',0,24,17,100),
        ]
        for cards,actions,status,payout,pt,dt,stake in cases:
            with self.subTest(status=status,actions=actions):
                r=replay(Shoe(cards),100,actions)
                self.assertTrue(r['ended']);self.assertEqual(r['status'],status)
                self.assertEqual((r['payout'],r['player_total'],r['dealer_total'],r['total_wager']),(payout,pt,dt,stake))
    def test_aces_rounding_and_illegal_moves(self):
        self.assertEqual(total([0,13,26,5]),(19,True))
        self.assertEqual(total([0,9,8]),(20,False))
        self.assertEqual(replay(Shoe([0,9,12,8]),3,[])['payout'],7)
        with self.assertRaises(ValueError):replay(Shoe([0,9,12,8]),100,['hit'])
        with self.assertRaises(ValueError):replay(Shoe([1,9,2,8,3]),100,['hit','double'])


class BlackjackWalletTests(unittest.TestCase):
    setUp=test_app.AppTests.setUp
    body=redpoints.RedPointsTests.body

    def opened(self,now=None):
        game=self.app.extensions['gaming'];now=time.time() if now is None else now
        wallet=game.view('bj','RedCard',now,client_ip='192.0.2.1')
        # Pick a public, deterministic test seed with a playable opening hand.
        for seed in range(100):
            with game.store.connection(transaction=True) as conn:
                conn['gaming']['players'][player_key('bj')]['server_seed']=f'{seed:064x}'
            wallet=game.view('bj','RedCard',now,client_ip='192.0.2.1')
            body=self.body(wallet,'blackjack')
            result=outcome(f'{seed:064x}',{**body,'actions':[]})
            if not result['ended'] and result['player_total']<18:break
        opened=game.bet('bj','RedCard',body,now,client_ip='192.0.2.1')
        return game,body,opened

    def move(self,game,hand,action='stand',now=None,action_id='blackjack-move-1'):
        body=dict(round_id=hand['round_id'],step=hand['step'],action=action,action_id=action_id)
        return game.blackjack_action('bj','RedCard',body,now,client_ip='192.0.2.1'),body

    def test_reservation_hole_card_privacy_restore_and_idempotent_settlement(self):
        game,body,opened=self.opened();wallet=opened['wallet'];hand=wallet['blackjack']
        self.assertIsNone(opened['receipt']);self.assertEqual(wallet['balance'],99900)
        self.assertEqual(hand['dealer'][1],None)
        private=game.recovery()['players'][player_key('bj')]['server_seed']
        self.assertNotIn(private,str(opened));self.assertNotIn('server_seed',str(opened))
        validate_gaming(game.recovery())
        self.assertEqual(Gaming(game.store).view('bj','RedCard',client_ip='192.0.2.1'),wallet)
        self.assertTrue(game.bet('bj','RedCard',body,client_ip='192.0.2.1')['duplicate'])
        result,move=self.move(game,hand)
        self.assertTrue(verify(result['receipt'],body['commitment']))
        self.assertIsNone(result['wallet']['blackjack'])
        self.assertEqual(result['wallet']['balance'],100000+result['receipt']['net'])
        duplicate=game.blackjack_action('bj','RedCard',move,client_ip='192.0.2.1')
        self.assertTrue(duplicate['duplicate']);self.assertEqual(result['wallet'],duplicate['wallet'])
        self.assertEqual(result['wallet']['stats']['blackjack']['bets'],1)
        validate_gaming(game.recovery())

    def test_two_tabs_cannot_hit_twice_with_same_step_or_request(self):
        game,body,opened=self.opened();hand=opened['wallet']['blackjack']
        move=dict(round_id=hand['round_id'],step=0,action='hit',action_id='concurrent-hit')
        with ThreadPoolExecutor(max_workers=6) as pool:
            replies=list(pool.map(lambda _:game.blackjack_action('bj','RedCard',move,client_ip='192.0.2.1'),range(6)))
        self.assertEqual(sum(not r['duplicate'] for r in replies),1)
        value=game.view('bj','RedCard',client_ip='192.0.2.1')
        hand=value['blackjack']
        if hand:
            self.assertEqual(hand['step'],1);self.assertEqual(len(hand['player']),3)
            with self.assertRaises(GamingError):game.blackjack_action('bj','RedCard',{**move,'action_id':'different-hit'},client_ip='192.0.2.1')
        validate_gaming(game.recovery())

    def test_other_games_and_other_wallets_cannot_use_active_hand(self):
        game,body,opened=self.opened();hand=opened['wallet']['blackjack']
        with self.assertRaises(GamingError) as exc:
            game.bet('bj','RedCard',{**self.body(opened['wallet']),'request_id':'another-game'},client_ip='192.0.2.1')
        self.assertEqual(exc.exception.code,'active_hand')
        game.view('other','Other',client_ip='192.0.2.2')
        with self.assertRaises(GamingError):game.blackjack_action('other','Other',dict(round_id=hand['round_id'],step=0,action='stand',action_id='steal-hand-id'),client_ip='192.0.2.2')
        self.assertEqual(game.view('bj','RedCard',client_ip='192.0.2.1'),opened['wallet'])

    def test_double_uses_real_total_stake_for_profit_and_ranking(self):
        game,body,opened=self.opened()
        result,_=self.move(game,opened['wallet']['blackjack'],'double')
        r=result['receipt'];self.assertEqual(r['result']['total_wager'],200)
        self.assertEqual(r['net'],r['payout']-200)
        self.assertEqual(result['wallet']['balance'],99800+r['payout'])
        self.assertEqual(game.leaders()['games']['blackjack'][0]['wagered'],200)
        self.assertTrue(verify(r,body['commitment']))
        self.assertFalse(verify({**r,'actions':['stand']},body['commitment']))
        validate_gaming(game.recovery())

    def test_move_write_failure_rolls_back_cards_and_money(self):
        game,body,opened=self.opened();before=game.recovery()
        with patch('storage.atomic_json',side_effect=OSError('disk full')):
            with self.assertRaises(StoreError):self.move(game,opened['wallet']['blackjack'],'double')
        self.assertEqual(game.recovery(),before)

    def test_weekly_cutoff_auto_stands_old_hand_once_then_resets(self):
        edge=season()['end_time'];game,body,opened=self.opened(edge-1)
        reset=game.view('bj','RedCard',edge,client_ip='192.0.2.1')
        self.assertEqual(reset['balance'],100000);self.assertIsNone(reset['blackjack'])
        r=reset['receipts'][0];self.assertEqual(r['ending'],'weekly_reset')
        self.assertEqual(r['actions'],['stand']);self.assertTrue(verify(r,body['commitment']))
        self.assertEqual(reset['stats']['blackjack']['bets'],0)
        self.assertEqual(game.view('bj','RedCard',edge+1,client_ip='192.0.2.1'),reset)
        validate_gaming(game.recovery())
