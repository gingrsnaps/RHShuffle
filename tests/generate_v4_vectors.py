"""Rebuild synthetic v4 proofs; historical v1–v3 vectors remain untouched."""
import json
from pathlib import Path
import sys
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from fairness import VERSION, commitment, outcome, verify

vectors=[]
settings=[('baccarat',dict(decks=8,side=side)) for side in ('player','banker','tie') for _ in range(48)]
settings += [('dice',dict(chance=50,side='under')),('keno',dict(picks=list(range(1,11)),risk='high')),
             ('plinko',dict(rows=16,risk='high')),('blackjack',dict(decks=6)),('poker',dict(variant='jacks_or_better')),
             ('coinflip',dict(side='heads')),('limbo',dict(target=250))]
for n,(game,options) in enumerate(settings):
    seed=f'{n:064x}'
    receipt=dict(rules_version=VERSION,season='1790114400',game=game,request_id=f'v4-reference-{n}',nonce=n,
                 client_seed='independent-reference',client_salt=f'{n:032x}',wager=12345,options=options,
                 server_seed=seed,commitment=commitment(seed))
    if game=='blackjack':
        receipt['actions']=[]
        if not outcome(seed,receipt)['ended']:receipt['actions']=['stand']
    if game=='poker':receipt['holds']=[0,2,4]
    receipt['result']=outcome(seed,receipt)
    receipt['payout']=receipt['result']['payout']
    receipt['net']=receipt['payout']-receipt['result'].get('total_wager',receipt['wager'])
    assert verify(receipt)
    vectors.append(receipt)
(Path(__file__).parent/'fairness_v4_vectors.json').write_text(json.dumps(vectors,indent=2)+'\n',encoding='utf-8')
print(f'{len(vectors)} v4 proof vectors written')
