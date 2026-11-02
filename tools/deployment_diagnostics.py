"""Validate the App Platform source layout without printing secrets.

Use `python tools/deployment_diagnostics.py` after extracting the ZIP.
Use `--archive /path/to/file.zip` to check the archive layout before extraction.
No Flask imports or network access are necessary for source validation.
"""
import argparse
import json
from pathlib import Path
import re
import sys
import time
import zipfile
from urllib.request import Request, urlopen
from urllib.error import HTTPError, URLError

ROOT = Path(__file__).resolve().parents[1]
REQUIRED_ROOT = ('wager_backend.py','requirements.txt','runtime.txt','Procfile','BUILD_MANIFEST.json')

def evaluate(root=ROOT):
    root=Path(root)
    errors=[]
    for name in REQUIRED_ROOT:
        if not (root/name).is_file():errors.append('Missing at source root: '+name)
    if not (root/'templates/index.html').is_file():errors.append('Missing templates/index.html')
    if not (root/'static/app.js').is_file():errors.append('Missing static/app.js')
    requirements=(root/'requirements.txt').read_text(encoding='utf-8') if (root/'requirements.txt').is_file() else ''
    if not re.search(r'^Flask==',requirements,re.M):errors.append('Flask must be in root requirements.txt')
    runtime=(root/'runtime.txt').read_text(encoding='utf-8').strip() if (root/'runtime.txt').is_file() else 'missing'
    if not re.fullmatch(r'python-3\.13\.\d+',runtime):errors.append('Python version missing/unexpected: '+runtime)
    spec=(root/'app.yaml').read_text(encoding='utf-8') if (root/'app.yaml').is_file() else ''
    if re.search(r'^\s*build_command\s*:',spec,re.M):errors.append('Custom build_command found; buildpack installs requirements already')
    match=re.search(r'^\s*source_dir:\s*([^\n#]+)',spec,re.M)
    if match and match.group(1).strip() != '/':errors.append('App YAML source_dir must be / for root-flat ZIP')
    if spec and not re.search(r'^\s*run_command:\s*python wager_backend\.py',spec,re.M):errors.append('Incorrect run command')
    m=root/'BUILD_MANIFEST.json'
    if m.is_file():
        try:
            files=json.loads(m.read_text(encoding='utf-8')).get('files',{})
            for entry in files:
                if entry.startswith(('private/','data/','docs/','tests/')):errors.append('Release manifest must not require optional files: '+entry)
                if not (root/entry).is_file():errors.append('Missing manifest source: '+entry)
        except (ValueError,TypeError) as e:errors.append('Invalid release manifest')
    print('Source directory:',root)
    print('Python:',runtime)
    print('Build command: none in app.yaml; also clear existing DigitalOcean dashboard build command')
    print('Configuration:','private files present in ZIP; Git ignores them by default' if (root/'private/settings.json').is_file() else 'private settings absent; configure encrypted App Platform environment variables')
    print('Stored JSON:','included, snapshot may be stale' if (root/'data/state.json').is_file() else 'not bundled; restore live backup if needed')
    if 'YOUR_GITHUB_USER/' in spec:print('Note: app.yaml has an example repo; do not import until you replace it')
    for err in errors:print('ERROR:',err)
    if not errors:print('PASS: source layout is ready for a Python web service')
    return not errors

def check_archive(path):
    errors=[]
    with zipfile.ZipFile(path) as z:
        names=set(z.namelist())
        for expected in REQUIRED_ROOT:
            if expected not in names:errors.append('Archive root missing '+expected)
        if 'redhunllef/requirements.txt' in names:errors.append('Archive has obsolete redhunllef/ wrapper directory')
        bad=z.testzip()
        if bad:errors.append('Corrupt ZIP entry: '+bad)
        print('ZIP members:',len(names))
    for err in errors:print('ERROR:',err)
    if not errors:print('PASS: flat ZIP root; all deployment entry points found')
    return not errors

def probe(url):
    if not (url.startswith('https://') or url.startswith('http://localhost') or url.startswith('http://127.0.0.1')):
        print('ERROR: use HTTPS for a remote website');return False
    ok=True
    for path in ('/healthz','/readyz'):
        start=time.perf_counter()
        try:
            with urlopen(Request(url.rstrip('/')+path,headers={'User-Agent':'RedHunllef-deployment-check'}),timeout=10) as response:
                print(path,response.status,'%.2fs'%(time.perf_counter()-start))
                ok &= response.status==200
        except (HTTPError,URLError,TimeoutError) as exc:
            print(path,'failed:',type(exc).__name__)
            ok=False
    return ok

if __name__=='__main__':
    parser=argparse.ArgumentParser()
    parser.add_argument('--archive',help='ZIP file to inspect for root nesting or corrupt members')
    parser.add_argument('--url',help='HTTPS URL to probe after deployment')
    args=parser.parse_args()
    ok=evaluate(ROOT)
    if args.archive:ok=check_archive(args.archive) and ok
    if args.url:ok=probe(args.url) and ok
    raise SystemExit(0 if ok else 1)
