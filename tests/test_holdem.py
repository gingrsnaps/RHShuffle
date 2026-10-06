"""Hold'em rules, accounting, privacy, recovery, and atomic action regressions."""
import copy
from concurrent.futures import ThreadPoolExecutor
import unittest
from unittest.mock import patch

import test_redpoints
from fairness import VERSION, V4_VERSION, commitment, outcome, verify
from gaming import Gaming, GamingError, player_key, validate_gaming
from holdem import Hand, best_hand, bot_action, validate_action
from holdem_vectors import vectors
from storage import StoreError


def cards(ranks, suits):
    return [s*13+(0 if r==14 else r-1) for r,s in zip(ranks,suits)]


class HoldemRulesTests(unittest.TestCase):
    def test_best_five_kickers_wheel_board_tie_and_two_trips(self):
        examples=[([14,13,12,11,10,2,3],[0,0,0,0,0,1,2],[8,14]),
                  ([14,2,3,4,5,8,9],[0,1,2,3,0,1,2],[4,5]),
                  ([14,14,14,13,13,13,2],[0,1,2,0,1,2,3],[6,14,13]),
                  ([9,9,9,9,14,13,2],[0,1,2,3,0,1,2],[7,9,14]),
                  ([14,14,13,13,12,12,11],[0,1,0,1,0,1,0],[2,14,13,12]),
                  ([14,14,13,12,11,9,2],[0,1,2,3,0,1,2],[1,14,13,12,11])]
        for ranks,suits,want in examples:
            self.assertEqual(best_hand(cards(ranks,suits))['rank'],want)
        board=cards([14,13,12,11,10],[0]*5)
        self.assertEqual(best_hand(board+[14,15])['rank'],best_hand(board+[16,17])['rank'])
        self.assertEqual(best_hand(board+[14,15])['cards'],sorted(board))

    def test_heads_up_order_big_blind_option_and_minimum_raise(self):
        hand=Hand(list(range(52)),1000,'player')
        self.assertEqual((hand.small,hand.big,hand.actor),(10,20,0))
        hand.move(dict(action='call',amount=0))
        self.assertEqual(hand.street,0);self.assertEqual(hand.actor,1)
        hand.move(dict(action='check',amount=0))
        self.assertEqual(hand.street,1);self.assertEqual(hand.actor,1)
        hand.move(dict(action='bet',amount=40))
        self.assertEqual(hand.legal(0)['min_raise_to'],80)
        with self.assertRaises(ValueError):hand.move(dict(action='raise',amount=60))
        hand.move(dict(action='raise',amount=100))
        self.assertEqual(hand.legal(1)['min_raise_to'],160)
        self.assertEqual(hand.actor,1)

    def test_fold_refunds_uncalled_blind_and_all_in_deals_all_streets(self):
        hand=Hand(list(range(52)),1000,'player');hand.move(dict(action='fold',amount=0))
        self.assertEqual(hand.refunds,[0,10]);self.assertEqual(hand.stacks,[990,1010])
        self.assertEqual(hand.result([])['total_wager'],10)
        hand=Hand(list(range(52)),1000,'player')
        hand.move(dict(action='all_in',amount=0))
        self.assertFalse(hand.legal(1)['can_raise'])
        hand.move(dict(action='call',amount=0))
        self.assertTrue(hand.ended);self.assertEqual(hand.street,3)
        self.assertEqual(len(hand.result([])['board']),5);self.assertEqual(sum(hand.stacks),2000)

    def test_opponent_observation_has_no_hidden_information(self):
        first=Hand(list(range(52)),1000,'computer')
        other_deck=list(range(52));other_deck[0],other_deck[20]=other_deck[20],other_deck[0]
        other_deck[5],other_deck[30]=other_deck[30],other_deck[5]
        second=Hand(other_deck,1000,'computer')
        self.assertNotEqual(first.holes[0],second.holes[0])
        self.assertEqual(first.observation(),second.observation())
        self.assertEqual(bot_action(first.observation()),bot_action(second.observation()))
        self.assertEqual(set(first.observation()),{'hole','board','legal','pot','highest','big_blind','street_index','raises'})

    def test_illegal_actions_and_buy_in_types_rejected(self):
        for value in (dict(action='check',amount=True),dict(action='call',amount=1),dict(action='win',amount=0),dict(action='raise',amount=-1)):
            with self.assertRaises(ValueError):validate_action(value)
        for value in (True,19,20.0,2**53):
            with self.assertRaises(ValueError):Hand(list(range(52)),value,'player')

    def test_reference_hands_verify_and_tampering_fails(self):
        receipts=vectors()
        for receipt in receipts:
            self.assertTrue(verify(receipt),receipt['request_id'])
            if receipt['game']!='poker':continue
            self.assertEqual(sum(receipt['result']['stacks']),receipt['wager']*2)
            self.assertEqual(receipt['net'],receipt['result']['returned']-receipt['result']['total_wager'])
            changed=copy.deepcopy(receipt);changed['result']['events'][0]['amount']+=1
            self.assertFalse(verify(changed))
            changed=copy.deepcopy(receipt);changed['options']['button']='computer' if changed['options']['button']=='player' else 'player'
            self.assertFalse(verify(changed))


class HoldemWalletTests(unittest.TestCase):
    setUp=test_redpoints.RedPointsTests.setUp
    player=test_redpoints.RedPointsTests.player
    body=test_redpoints.RedPointsTests.body
    finish_hand=test_redpoints.RedPointsTests.finish_hand

    def opened(self):
        game=self.app.extensions['gaming'];wallet=game.confirm_community_name('holdem-player','Holdem Player')
        body=self.body(wallet,'poker');body['wager']=1000
        result=game.bet('holdem-player','Holdem Player',body,client_ip='192.0.2.40')
        return game,body,result

    @staticmethod
    def move(hand,action='fold',amount=0):
        return dict(variant='texas_holdem',round_id=hand['round_id'],step=hand['step'],action_id='move-test-'+str(hand['step']),move=dict(action=action,amount=amount))

    def test_private_hand_and_duplicate_action_exactly_once(self):
        game,body,result=self.opened();hand=result['wallet']['poker']
        self.assertEqual(hand['computer'],[None,None])
        self.assertTrue(all(e['state']['computer']==[None,None] for e in hand['events']))
        self.assertNotIn('server_seed',str(result));self.assertEqual(result['wallet']['balance'],99000)
        move=self.move(hand)
        with ThreadPoolExecutor(max_workers=6) as pool:
            results=list(pool.map(lambda _:game.poker_action('holdem-player','Holdem Player',move),range(6)))
        self.assertEqual(sum(not r['duplicate'] for r in results),1)
        receipt=results[0]['receipt'];self.assertTrue(verify(receipt,body['commitment']))
        self.assertEqual(receipt['net'],-10);self.assertEqual(receipt['payout'],990)
        self.assertEqual(results[0]['wallet']['stats']['poker']['wagered'],10)
        self.assertEqual(results[0]['wallet']['stats']['poker']['paid'],0)
        with self.assertRaises(GamingError):game.poker_action('holdem-player','Holdem Player',{**move,'move':dict(action='call',amount=0)})
        self.assertEqual(game.leaders()['games']['poker'][0]['name'],'Holdem Player')
        self.assertEqual(game.leaders()['games']['poker'][0]['ips'],['192.0.2.40'])
        self.assertEqual(game.view('holdem-player','Holdem Player')['poker_button'],'computer')
        validate_gaming(game.recovery())

    def test_refresh_restart_weekly_settlement_and_name_persist(self):
        game,body,result=self.opened();wallet=result['wallet'];before=game.recovery()['players'][player_key('holdem-player')]['poker']
        game.refresh_balance('holdem-player','Holdem Player',dict(version=wallet['version'],season=wallet['season']['id']))
        game.grant_everyone('a1'*16,'Admin');game.restart_balances()
        restored=Gaming(game.store)
        self.assertEqual(restored.recovery()['players'][player_key('holdem-player')]['poker'],before)
        self.assertEqual(restored.view('holdem-player','Holdem Player')['balance'],100000)
        rollover=restored.view('holdem-player','Holdem Player',now=wallet['season']['end_time'])
        self.assertEqual(rollover['balance'],100000);self.assertIsNone(rollover['poker'])
        receipt=rollover['receipts'][0];self.assertEqual(receipt['ending'],'weekly_reset');self.assertTrue(verify(receipt))
        self.assertEqual(receipt['net'],-10);self.assertEqual(rollover['stats']['poker']['bets'],0)
        validate_gaming(restored.recovery())

    def test_action_failure_and_other_player_cannot_change_hand(self):
        game,_,result=self.opened();hand=result['wallet']['poker'];before=game.recovery()
        with self.assertRaises(ValueError):game.poker_action('holdem-player','Holdem Player',self.move(hand,'check'))
        self.assertEqual(game.recovery(),before)
        with patch('storage.atomic_json',side_effect=OSError('disk full')):
            with self.assertRaises(StoreError):game.poker_action('holdem-player','Holdem Player',self.move(hand))
        self.assertEqual(game.recovery(),before)
        with self.assertRaises(GamingError):game.poker_action('different','Different',self.move(hand))
        with self.assertRaises(GamingError):game.bet('holdem-player','Holdem Player',{**self.body(result['wallet'],'coinflip'),'request_id':'different-pending-game'})

    def test_legacy_statistics_migrate_once_and_stay_separate(self):
        game,_,result=self.opened();game.poker_action('holdem-player','Holdem Player',self.move(result['wallet']['poker']))
        # Turn this fixture into an old completed Video Poker save with matching accounting.
        with game.store.connection(transaction=True) as conn:
            player=conn['gaming']['players'][player_key('holdem-player')]
            old=self.body(game._view(player,{'id':player['season']}),'poker')
            old.update(rules_version=V4_VERSION,options=dict(variant='jacks_or_better'),server_seed='ef'*32,
                       commitment=commitment('ef'*32),holds=[0,1,2,3,4],nonce=0)
            old['result']=outcome(old['server_seed'],old);old['payout']=old['result']['payout'];old['net']=old['payout']-old['wager']
            player['receipts']=[old];player['stats']['poker']=dict(bets=1,wagered=100,paid=old['payout'],net=old['net'],biggest_payout=old['payout'])
            player['balance']=100000+old['net'];player.pop('poker_stats_version')
        validate_gaming(game.recovery())
        self.assertEqual(game.leaders()['games']['poker'],[])
        self.assertEqual(len(game.leaders()['legacy_poker']),1)
        self.assertEqual(game.view('holdem-player','Holdem Player')['stats']['poker']['bets'],0)
        migrated=Gaming(game.store);again=Gaming(game.store)
        value=again.view('holdem-player','Holdem Player')
        self.assertEqual(value['stats']['poker']['bets'],0);self.assertEqual(value['legacy_poker']['bets'],1)
        self.assertEqual(value['receipts'][0],old);self.assertTrue(verify(old))
        self.assertEqual(again.leaders()['games']['poker'],[]);self.assertEqual(len(again.leaders()['legacy_poker']),1)
        validate_gaming(again.recovery())

    def test_client_cannot_choose_the_button_or_mix_legacy_protocols(self):
        game=self.app.extensions['gaming'];wallet=game.confirm_community_name('seat','Seat Test')
        body=self.body(wallet,'poker');before=game.recovery()
        with self.assertRaises(GamingError):
            game.bet('seat','Seat Test',{**body,'options':dict(variant='texas_holdem',button='computer')})
        self.assertEqual(game.recovery(),before)
        result=game.bet('seat','Seat Test',body);hand=result['wallet']['poker']
        result=game.poker_action('seat','Seat Test',self.move(hand))
        with self.assertRaises(GamingError):
            game.poker_action('seat','Seat Test',dict(round_id=hand['round_id'],holds=[],action_id='wrong-protocol'))
        self.assertTrue(verify(result['receipt']));validate_gaming(game.recovery())

    def test_http_csrf_and_other_wallet_isolation(self):
        client,value=self.player('HTTP Holdem')
        body=self.body(value['wallet'],'poker')
        response=client.post('/gaming/api/bet',json=body,headers={'X-CSRF-Token':value['player_csrf']})
        self.assertEqual(response.status_code,200,response.text)
        hand=response.json['wallet']['poker'];move=self.move(hand)
        self.assertEqual(client.post('/gaming/api/poker/action',json=move).status_code,400)
        other,state=self.player('Other User')
        reply=other.post('/gaming/api/poker/action',json=move,headers={'X-CSRF-Token':state['player_csrf']})
        self.assertEqual(reply.status_code,409)
        response=self.finish_hand(client,response,value['player_csrf'])
        self.assertTrue(verify(response.json['receipt']))
        self.assertEqual(len(response.json['wallet']['stats']),8)
        self.assertEqual(client.get('/gaming/poker').status_code,200)
        self.assertEqual(self.app.test_client().get('/admin/gaming/status').status_code,401)


if __name__=='__main__':unittest.main()
