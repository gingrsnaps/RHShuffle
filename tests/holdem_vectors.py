"""Reproducible v5 reference receipts, generated instead of shipping a large fixture.

The JS suite reads this program's JSON and independently replays every receipt.
Earlier v1-v4 fixture files remain immutable.
"""
import json
from pathlib import Path
import random
import sys
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from fairness import VERSION, commitment, outcome
from holdem import MAX_BUY_IN


def vectors():
    result=[]
    settings={'dice':dict(chance=50,side='under'),'keno':dict(picks=list(range(1,11)),risk='high'),
              'plinko':dict(rows=16,risk='high'),'blackjack':dict(decks=6),'limbo':dict(target=200),
              'coinflip':dict(side='heads'),'baccarat':dict(decks=8,side='banker')}
    for index in range(88):
        game='poker' if index<74 else list(settings)[(index-74)%7]
        seed=f'{index+809:064x}'
        buy_in=(20,101,1000,20000,MAX_BUY_IN)[index%5] if game=='poker' else 100
        opt=dict(variant='texas_holdem',button='player' if index%2==0 else 'computer') if game=='poker' else settings[game]
        receipt=dict(rules_version=VERSION,game=game,season='1790000000',nonce=index,wager=buy_in,options=opt,
                     client_seed='Holdem-reference',client_salt='7a'*16,server_seed=seed,commitment=commitment(seed),
                     request_id=f'holdem-v5-fixture-{index}',actions=[])
        state=outcome(seed,receipt)
        if game=='blackjack' and not state['ended']:
            receipt['actions']=['stand'];state=outcome(seed,receipt)
        if game=='poker':
            rng=random.Random(index)
            if not state['ended'] and index%13==0:
                receipt['ending']='weekly_reset';state=outcome(seed,receipt)
            while not state['ended']:
                legal=state['legal']
                choices=['check' if legal['check'] else 'call']*5+['fold']
                if legal['all_in']:choices.append('all_in')
                if legal['can_raise'] and legal['min_raise_to']<=legal['max_raise_to']:
                    choices+=['bet' if max(state['bets'])==0 else 'raise']*2
                action=rng.choice(choices)
                amount=legal['min_raise_to'] if action in ('bet','raise') else 0
                receipt['actions'].append(dict(action=action,amount=amount))
                state=outcome(seed,receipt)
        stake=state.get('total_wager',buy_in) if game=='blackjack' else buy_in
        receipt.update(result=state,payout=state['payout'],net=state['payout']-stake)
        result.append(receipt)
    return result


if __name__=='__main__':print(json.dumps(vectors(),separators=(',',':')))
