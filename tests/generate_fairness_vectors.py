"""Deterministic reference receipts: synthetic keys only, no saved accounts."""
import json
from pathlib import Path
import sys
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from fairness import LEGACY_VERSION, commitment, outcome

cases=[('dice',dict(chance=c,side=s)) for c in (1,5,50,95) for s in ('under','over')]
cases += [('keno',dict(picks=list(range(1,n+1)),risk=r)) for n in range(1,11) for r in ('low','medium','high')]
cases += [('plinko',dict(rows=n,risk=r)) for n in (8,12,16) for r in ('low','medium','high')]
values=[]
for n,(game,options) in enumerate(cases):
    seed=f'{n+1:064x}'
    receipt=dict(rules_version=LEGACY_VERSION,server_seed=seed,commitment=commitment(seed),season='1790719200',
                 client_seed='reference.seed-1',client_salt=f'{100+n:032x}',nonce=n,wager=(1,100,9999)[n%3],
                 game=game,options=options,request_id='reference-'+str(n))
    result=outcome(seed,receipt)
    receipt.update(result=result,payout=result['payout'],net=result['payout']-receipt['wager'])
    values.append(receipt)
Path(__file__).with_name('fairness_vectors.json').write_text(json.dumps(values,indent=2)+'\n',encoding='utf-8')
print(f'{len(values)} deterministic vectors written.')
