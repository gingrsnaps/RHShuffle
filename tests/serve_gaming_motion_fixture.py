"""Temporary native-browser fixture; never loads private configuration or providers."""
from pathlib import Path
import json,os,sys,tempfile
from unittest.mock import patch
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from wager_backend import create_app
from waitress import create_server
with tempfile.TemporaryDirectory() as folder,patch.dict(os.environ,{'APP_ENV':'test','ADMIN_BOOTSTRAP_PASS':'fixture-only','SUPERADMIN_USER':'fixtureadmin','SESSION_COOKIE_SECURE':'never','TRUST_APP_PLATFORM':'1'},clear=True):
 app=create_app(Path(folder),testing=True)
 server=create_server(app,host='127.0.0.1',port=0,threads=6)
 print(json.dumps({'port':server.effective_port}),flush=True)
 try:server.run()
 finally:server.close()
