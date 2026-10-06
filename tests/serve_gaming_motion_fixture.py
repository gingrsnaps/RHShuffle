"""Temporary native-browser fixture; never loads private configuration or providers."""
from pathlib import Path
import json,os,sys,tempfile
from unittest.mock import patch
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from wager_backend import create_app
from waitress import create_server
with tempfile.TemporaryDirectory() as folder,patch.dict(os.environ,{'APP_ENV':'test','ADMIN_BOOTSTRAP_PASS':'fixture-only','SUPERADMIN_USER':'fixtureadmin','SESSION_COOKIE_SECURE':'never','TRUST_APP_PLATFORM':'1'},clear=True):
 app=create_app(Path(folder),testing=True)
 extra={}
 if '--legacy' in sys.argv:
  # A genuine v4 unfinished hand, isolated from every real account/configuration.
  import time
  from fairness import V4_VERSION,commitment
  from gaming import Gaming
  client=app.test_client();token=client.get('/gaming/api/state').json['player_csrf']
  wallet=client.post('/gaming/api/profile',json={'username':'Legacy Fixture'},headers={'X-CSRF-Token':token}).json['wallet']
  game=app.extensions['gaming']
  with game.store.connection(transaction=True) as conn:
   player=next(iter(conn['gaming']['players'].values()))
   seed=player['server_seed']
   player['poker']=dict(rules_version=V4_VERSION,season=wallet['season']['id'],game='poker',wager=100,nonce=0,
                       request_id='legacy-motion-hand',client_seed='legacy-fixture',client_salt='ab'*16,
                       options={'variant':'jacks_or_better'},commitment=commitment(seed),server_seed=seed,holds=None,at=int(time.time()))
   player['balance']-=100;player.pop('poker_stats_version',None)
  Gaming(game.store)
  extra['legacy_cookie']=client.get_cookie('rh_raider').value
 server=create_server(app,host='127.0.0.1',port=0,threads=6)
 print(json.dumps({'port':server.effective_port,**extra}),flush=True)
 try:server.run()
 finally:server.close()
