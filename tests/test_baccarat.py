"""Baccarat tableau, exact accounting, old-hand migration and offline proofs."""
import copy
import json
from pathlib import Path
import time
import unittest
from unittest.mock import patch

from baccarat import banker_draws, card_value, replay, RETURNS
from fairness import VERSION, V3_VERSION, GAMES, commitment, outcome, verify
from gaming import Gaming, player_key, validate_gaming
from storage import StoreError
import test_redpoints


class Cards:
    """Feed selected physical cards through the public unbiased-draw interface."""
    def __init__(self, cards):
        self.cards, self.shoe, self.cursor = iter(cards), list(range(416)), 0

    def below(self, size):
        assert size == 416-self.cursor
        j = self.shoe.index(next(self.cards))
        answer = j-self.cursor
        assert answer >= 0
        self.shoe[self.cursor], self.shoe[j] = self.shoe[j], self.shoe[self.cursor]
        self.cursor += 1
        return answer


def value_id(value, deck):
    return deck*52+(value-1 if value else 9)


class BaccaratRulesTests(unittest.TestCase):
    def test_card_values_and_entire_banker_table(self):
        self.assertEqual([card_value(n) for n in range(13)],[1,2,3,4,5,6,7,8,9,0,0,0,0])
        expected=[set(range(10)),set(range(10)),set(range(10)),{0,1,2,3,4,5,6,7,9},
                  {2,3,4,5,6,7},{4,5,6,7},{6,7},set()]
        for points in range(8):
            self.assertEqual(banker_draws(points,None), points < 6)
            for third in range(10):
                self.assertEqual(banker_draws(points,third),third in expected[points])

    def test_all_initial_totals_and_third_card_values_with_three_bets(self):
        draw_on=[set(range(10)),set(range(10)),set(range(10)),{0,1,2,3,4,5,6,7,9},
                 {2,3,4,5,6,7},{4,5,6,7},{6,7},set(),set(),set()]
        for pt in range(10):
            for bt in range(10):
                for third in range(10):
                    natural = pt >= 8 or bt >= 8
                    pdraw = not natural and pt <= 5
                    bdraw = not natural and (third in draw_on[bt] if pdraw else bt <= 5)
                    initial=[value_id(pt,0),value_id(bt,1),value_id(0,2),value_id(0,3)]
                    cards=initial+([value_id(third,4)] if pdraw else [])+([value_id(7,5)] if bdraw else [])
                    final_p=(pt+(third if pdraw else 0))%10
                    final_b=(bt+(7 if bdraw else 0))%10
                    winner='tie' if final_p==final_b else 'player' if final_p>final_b else 'banker'
                    for side in ('player','banker','tie'):
                        r=replay(Cards(cards),101,side)
                        self.assertEqual((len(r['player']),len(r['banker'])),(2+int(pdraw),2+int(bdraw)))
                        self.assertEqual((r['player_total'],r['banker_total'],r['winner'],r['natural']),(final_p,final_b,winner,natural))
                        expected=101*RETURNS[side]//10000 if winner==side else 101 if winner=='tie' else 0
                        self.assertEqual(r['payout'],expected)
                        self.assertEqual(len(set(r['player']+r['banker'])),len(cards))

    def test_proofs_and_rejection_of_tampering_or_old_baccarat_versions(self):
        vectors=json.loads((Path(__file__).parent/'fairness_v4_vectors.json').read_text(encoding='utf-8'))
        combos=set()
        for receipt in vectors:
            self.assertTrue(verify(receipt,receipt['commitment']))
            changed=copy.deepcopy(receipt);changed['net']+=1
            self.assertFalse(verify(changed))
            if receipt['game']=='baccarat':
                combos.add((receipt['options']['side'],receipt['result']['winner']))
                changed=copy.deepcopy(receipt);changed['result']['player'][0]=(changed['result']['player'][0]+1)%416
                self.assertFalse(verify(changed))
                self.assertFalse(verify({**receipt,'rules_version':V3_VERSION}))
        self.assertEqual(len(combos),9)


class BaccaratWalletTests(unittest.TestCase):
    setUp=test_redpoints.RedPointsTests.setUp
    player=test_redpoints.RedPointsTests.player
    body=test_redpoints.RedPointsTests.body

    def test_saved_round_deduplicates_and_admin_tracks_exact_net_and_ip(self):
        client,state=self.player('BaccaratPlayer');body=self.body(state['wallet'],'baccarat')
        headers={'X-CSRF-Token':state['player_csrf']}
        self.assertEqual(client.post('/gaming/api/bet',json=body).status_code,400)
        result=client.post('/gaming/api/bet',json=body,headers=headers)
        self.assertEqual(result.status_code,200,result.text)
        receipt=result.json['receipt'];self.assertTrue(verify(receipt,body['commitment']))
        self.assertEqual(result.json['wallet']['balance'],100000+receipt['net'])
        self.assertTrue(client.post('/gaming/api/bet',json=body,headers=headers).json['duplicate'])
        self.assertEqual(client.get('/admin/gaming/status').status_code,401)
        rankings=self.client.get('/admin/gaming/status').json
        # Public game data cannot expose private IP tracking.
        self.assertNotIn('198.51.100.1',json.dumps(result.json))
        self.assertIn('BaccaratPlayer',json.dumps(rankings))
        self.assertIn('198.51.100.1',json.dumps(rankings))
        validate_gaming(self.app.extensions['gaming'].recovery())

    def test_failed_save_does_not_debit_or_rotate_commitment(self):
        game=self.app.extensions['gaming'];wallet=game.view('failure','Failure')
        before=game.recovery();body=self.body(wallet,'baccarat')
        with patch('storage.atomic_json',side_effect=OSError('disk full')):
            with self.assertRaises(StoreError):game.bet('failure','Failure',body)
        self.assertEqual(game.recovery(),before)

    def test_v3_pending_card_hands_keep_seed_cards_and_original_receipt_version(self):
        for card_game in ('blackjack','poker'):
            with self.subTest(card_game=card_game):
                game=self.app.extensions['gaming'];identity='legacy-'+card_game
                wallet=game.view(identity,identity);body=self.body(wallet,card_game)
                if card_game=='poker':body['options']=dict(variant='jacks_or_better')
                for number in range(100):
                    seed=f'{number:064x}'
                    pending={**body,'rules_version':V3_VERSION,'server_seed':seed,'commitment':commitment(seed),
                             'at':int(time.time())}
                    pending.update({'actions':[],'action_ids':[]} if card_game=='blackjack' else {'holds':None})
                    if not outcome(seed,pending)['ended']:break
                with game.store.connection(transaction=True) as conn:
                    player=conn['gaming']['players'][player_key(identity)]
                    player['stats'].pop('baccarat')
                    player.update(server_seed=seed,balance=99900)
                    player[card_game]=pending
                original=outcome(seed,pending)
                migrated=Gaming(game.store);migrated.restart_balances()
                self.assertEqual(migrated.recovery()['players'][player_key(identity)][card_game],pending)
                hand=migrated.view(identity,identity)[card_game]
                if card_game=='poker':
                    result=migrated.poker_action(identity,identity,dict(round_id=hand['round_id'],holds=[0,2,4],action_id='migrate-draw'))
                    self.assertEqual(result['receipt']['result']['initial'],original['initial'])
                else:
                    result=migrated.blackjack_action(identity,identity,dict(round_id=hand['round_id'],step=0,action='stand',action_id='migrate-stand'))
                    self.assertEqual(result['receipt']['result']['player'],original['player'])
                self.assertTrue(verify(result['receipt']));self.assertEqual(result['receipt']['rules_version'],V3_VERSION)
                self.assertEqual(set(result['wallet']['stats']),set(GAMES))
                validate_gaming(migrated.recovery())


if __name__=='__main__': unittest.main()
