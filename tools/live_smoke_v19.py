"""Read-only V19 production acceptance checks. Requires requests."""
import argparse, re, sys
import requests

def main():
 p=argparse.ArgumentParser();p.add_argument('--base-url',required=True);p.add_argument('--username');p.add_argument('--password');a=p.parse_args()
 base=a.base_url.rstrip('/');s=requests.Session();ok=True
 for path in ['/healthz','/readyz','/','/?provider=empiredrop','/gaming','/history']:
  r=s.get(base+path,timeout=20,allow_redirects=True);print(path,r.status_code,r.url);ok &= r.status_code==200
  if path=='/': ok &= 'Shuffle · Top 15' in r.text and 'aria-selected="true" aria-controls="shuffleBoard"' in r.text
  if 'provider=empiredrop' in path: ok &= 'EmpireDrop · Top 10' in r.text and 'aria-selected="true" aria-controls="empireBoard"' in r.text
 if a.username and a.password:
  login=s.get(base+'/admin/login',timeout=20); token=re.search(r'name="csrf" value="([^"]+)"',login.text)
  if not token: print('CSRF token not found');return 1
  r=s.post(base+'/admin/login',data={'csrf':token.group(1),'username':a.username,'password':a.password},timeout=20)
  for path in ['/admin','/admin/leaderboards/shuffle','/admin/leaderboards/shuffle/schedule','/admin/leaderboards/shuffle/prizes','/admin/leaderboards/shuffle/players','/admin/leaderboards/empiredrop','/admin/leaderboards/empiredrop/schedule','/admin/leaderboards/empiredrop/payouts','/admin/gaming','/admin/settings','/admin/activity']:
   r=s.get(base+path,timeout=20);print(path,r.status_code);ok &= r.status_code==200
 return 0 if ok else 1
if __name__=='__main__':raise SystemExit(main())
