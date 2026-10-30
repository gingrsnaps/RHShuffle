"""Read-only diagnostics for the deployment archive and its public health routes."""
import argparse
import json
import os
from pathlib import Path
import re
import sys
import time
from urllib.request import Request, urlopen
from urllib.error import HTTPError, URLError

ROOT = Path(__file__).resolve().parents[1]

def evaluate(root=ROOT):
    app_spec = (root/'app.yaml').read_text(encoding='utf-8')
    requirements = (root/'requirements.txt').read_text(encoding='utf-8').splitlines()
    errors = []
    if re.search(r'^\s*build_command\s*:', app_spec, re.M):
        errors.append('app.yaml has a custom build_command; remove redundant pip installs')
    if not (root/'wager_backend.py').is_file(): errors.append('No wager_backend.py')
    for asset in ('templates/index.html','templates/admin.html','static/app.js','runtime.txt'):
        if not (root/asset).is_file(): errors.append('Missing '+asset)
    if not any(line.startswith('Flask==') for line in requirements): errors.append('Flask pin missing')
    files = [p for p in root.rglob('*') if p.is_file()]
    print('Deployment inventory:',len(files),'files,',sum(p.stat().st_size for p in files),'bytes')
    print('Python target:',(root/'runtime.txt').read_text(encoding='utf-8').strip())
    print('Custom build command:', 'found' if re.search(r'^\s*build_command\s*:', app_spec, re.M) else 'none')
    print('Private directory:', 'present (contents never printed)' if (root/'private').is_dir() else 'not included')
    print('Saved state:', 'present' if (root/'data/state.json').is_file() else 'not included')
    for error in errors: print('ERROR:',error)
    return not errors

def probe(url):
    base = url.rstrip('/')
    if not base.startswith('https://') and not base.startswith('http://localhost') and not base.startswith('http://127.0.0.1'):
        print('ERROR: remote URL must use HTTPS',file=sys.stderr); return False
    result = True
    for path in ('/healthz','/readyz'):
        started=time.perf_counter()
        try:
            with urlopen(Request(base+path,headers={'User-Agent':'RedHunllef-deploy-diagnostics/1.0'}),timeout=8) as response:
                payload = response.read(4096)
                healthy = response.status==200
                print(path, 'HTTP',response.status,'%.3fs'%(time.perf_counter()-started))
                try:
                    obj = json.loads(payload)
                    print('  ok:',obj.get('ok'),'release:',str(obj.get('release',''))[:100])
                except ValueError: print('  WARNING: Response was not JSON')
                result &= healthy
        except HTTPError as exc:
            print(path,'HTTP',exc.code,'%.3fs'%(time.perf_counter()-started)); result=False
        except (URLError,TimeoutError) as exc:
            print(path,'FAILED:',type(exc).__name__,'%.3fs'%(time.perf_counter()-started)); result=False
    return result

if __name__=='__main__':
    parser=argparse.ArgumentParser()
    parser.add_argument('--url',help='HTTPS base URL of deployed site (optional)')
    args=parser.parse_args()
    ok=evaluate()
    if args.url: ok=probe(args.url) and ok
    raise SystemExit(0 if ok else 1)
