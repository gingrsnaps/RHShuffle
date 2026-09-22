"""Shared raid, HTTP, fairness, concurrency, and portable recovery regressions."""
import copy
from concurrent.futures import ThreadPoolExecutor
import json
import os
from pathlib import Path
import secrets
import sys
import tempfile
import unittest
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from boss import BossError, CommunityBoss, DAY, DEFAULT_HP, fresh_raid, network_identity, validate_boss
from storage import Store
from wager_backend import create_app


class BossTests(unittest.TestCase):
    def setUp(self):
        temp=tempfile.TemporaryDirectory(); self.addCleanup(temp.cleanup)
        self.root=Path(temp.name)
        env=patch.dict(os.environ, {'APP_ENV':'test','ADMIN_BOOTSTRAP_PASS':'test-only-password'}, clear=True)
        env.start(); self.addCleanup(env.stop)
        self.app=create_app(self.root, testing=True)
        self.r=self.app.extensions['runtime']; self.b=self.app.extensions['boss']
        self.addCleanup(self.r.store.close)
        self.clock=patch('boss.time.time',return_value=1_800_000_000.375)
        self.time=self.clock.start(); self.addCleanup(self.clock.stop)
        self.start=self.time.return_value

    def hit(self,guest='a',ip='192.0.2.1',style=None,request_id=None):
        state=self.b.status(guest,ip)
        return self.b.attack(guest,ip,style or state['weakness'],state['raid_id'],request_id or secrets.token_hex(16))

    def client(self,ip='192.0.2.1'):
        c=self.app.test_client(); c.environ_base['REMOTE_ADDR']=ip
        state=c.get('/play/api/state').json
        return c,state

    def post(self,c,value,**extra):
        state=value['state']
        return c.post('/play/api/attack',json={'raid_id':state['raid_id'],'request_id':secrets.token_hex(16),'style':state['weakness'],**extra},headers={'X-CSRF-Token':value['csrf']})

    def test_two_players_share_health_and_separate_identity(self):
        a,sa=self.client(); b,sb=self.client('192.0.2.2')
        first=self.post(a,sa); second=self.post(b,sb)
        self.assertEqual(first.status_code,200); self.assertEqual(second.status_code,200)
        current=a.get('/play/api/state').json['state']
        self.assertEqual(current['hp'],DEFAULT_HP-300)
        self.assertEqual(current['raiders'],2)
        self.assertEqual(current['you']['damage'],150)
        self.assertNotEqual(sa['state']['you']['name'],sb['state']['you']['name'])
        self.assertEqual(len(current['recent']),2)
        html=a.get('/play').text
        self.assertIn('How to play together',html)
        self.assertIn('40 attacks per raid day',html)
        self.assertNotIn('href="/admin"',a.get('/').text)
        self.assertIn('Join the boss fight',a.get('/').text)

    def test_simultaneous_hits_from_distinct_players_are_atomic(self):
        def attack(i): return self.hit(str(i),f'198.51.100.{i+1}')
        with ThreadPoolExecutor(max_workers=12) as pool:
            hits=list(pool.map(attack,range(40)))
        state=self.b.export()
        self.assertEqual(state['total_attacks'],40)
        self.assertEqual(state['hp'],DEFAULT_HP-sum(r['hit']['damage'] for r in hits))
        validate_boss(state)

    def test_same_network_simultaneous_tabs_only_one_lands(self):
        def attack(i):
            try: return self.hit(str(i))['ok']
            except BossError as exc: return exc.code
        with ThreadPoolExecutor(max_workers=10) as pool:
            result=list(pool.map(attack,range(20)))
        self.assertEqual(result.count(True),1)
        self.assertEqual(result.count('cooldown'),19)

    def test_cooldown_fractional_seconds_and_browser_limit_across_ips(self):
        self.hit()
        self.time.return_value=self.start+59.99
        with self.assertRaises(BossError) as blocked:self.hit(ip='192.0.2.2')
        self.assertEqual(blocked.exception.status,429)
        self.time.return_value=self.start+60
        self.assertEqual(self.hit(ip='192.0.2.2')['hit']['damage'],150)
        validate_boss(self.b.export())

    def test_daily_allowance_rollover_and_shared_network(self):
        for i in range(40):
            self.time.return_value=self.start+i*60
            self.hit()
        self.time.return_value=self.start+40*60
        with self.assertRaises(BossError) as blocked:self.hit()
        self.assertEqual(blocked.exception.code,'daily_limit')
        with self.assertRaises(BossError):self.hit(guest='cookie-cleared')
        with self.assertRaises(BossError):self.hit(ip='192.0.2.2')
        self.assertEqual(self.b.status('a','192.0.2.1')['you']['remaining'],0)
        self.time.return_value=int(self.start)+DAY
        self.assertEqual(self.hit()['state']['you']['remaining'],39)

    def test_ipv6_normalization_and_mapped_ipv4(self):
        self.hit(ip='2001:db8::abcd')
        with self.assertRaises(BossError):self.hit(guest='new',ip='2001:db8::eeff')
        self.assertEqual(network_identity('::ffff:192.0.2.1'),'192.0.2.1')
        self.assertEqual(self.hit(guest='other',ip='2001:db8:0:1::1')['hit']['damage'],150)

    def test_weakness_bonus_and_tenth_hit_burst(self):
        s=self.b.status('a','192.0.2.1')
        wrong=next(x for x in ('blade','bow','magic') if x!=s['weakness'])
        self.assertEqual(self.hit(style=wrong)['hit']['damage'],100)
        for i in range(1,10):
            self.time.return_value=self.start+i*60
            result=self.hit()
        self.assertEqual(result['hit']['damage'],250)
        self.assertTrue(result['hit']['burst'])
        self.assertEqual(result['state']['you']['burst_in'],10)

    def test_receipt_retry_after_cooldown_and_victory_is_idempotent(self):
        first=self.hit(request_id='test-receipt-001')
        self.time.return_value+=120
        again=self.hit(request_id='test-receipt-001')
        self.assertTrue(again['duplicate']); self.assertEqual(first['hit'],again['hit'])
        self.assertEqual(self.b.export()['total_attacks'],1)
        # A tiny isolated raid verifies final damage clamping and victory receipts.
        value=fresh_raid(health=50)
        with self.r.store.connection(transaction=True) as conn:self.b._write(conn,value,new_raid=True)
        self.b.loaded_at=0
        final=self.hit(request_id='victory-receipt')
        self.assertEqual(final['hit']['damage'],50)
        self.assertEqual(final['state']['hp'],0)
        self.assertTrue(self.hit(request_id='victory-receipt')['duplicate'])
        with self.assertRaises(BossError):self.hit(guest='b',ip='192.0.2.2')
        validate_boss(self.b.export())

    def test_race_settings_and_provider_cache_untouched_by_game(self):
        before=self.r.store.admin(); snapshot=self.r.store.live('shuffle')
        self.hit(); self.b.control('pause',self.b.status()['raid_id'])
        self.assertEqual(self.r.store.admin(),before)
        self.assertEqual(self.r.store.live('shuffle'),snapshot)

    def test_health_never_regenerates_during_idle_time_daily_reset_or_pause(self):
        hit = self.hit()
        saved = self.b.export()
        for elapsed in (60, 601, DAY + 1, 7 * DAY):
            self.time.return_value = self.start + elapsed
            self.b.loaded_at = 0
            view = self.b.status('a', '192.0.2.1')
            self.assertEqual(view['hp'], hit['state']['hp'])
            self.assertEqual(view['total_damage'], 150)
            self.assertEqual(self.b.export(), saved)
        self.assertEqual(view['you']['remaining'], 40)
        self.b.control('pause', saved['id'])
        self.time.return_value += DAY
        self.b.control('resume', saved['id'])
        self.assertEqual(self.b.status()['hp'], saved['hp'])
        # Reloaded HTML must not briefly label a damaged boss as 100% health.
        page = self.app.test_client().get('/play')
        self.assertIn(f'id="bossPercent">{saved["hp"] / saved["max_hp"] * 100:.2f}%</span>', page.text)

    def test_cold_app_restart_retains_all_committed_damage(self):
        self.hit()
        self.time.return_value += 60
        self.hit()
        saved = self.b.export()
        self.r.store.close()
        restarted = create_app(self.root, testing=True)
        self.addCleanup(restarted.extensions['runtime'].store.close)
        restored = restarted.extensions['boss']
        self.assertEqual(restored.export(), saved)
        self.assertEqual(restored.status()['hp'], DEFAULT_HP - 300)

    def test_storage_refuses_health_increases_and_implicit_new_raids(self):
        self.hit()
        saved = self.b.export()
        healed = copy.deepcopy(saved)
        healed['hp'] += 1
        healed['total_damage'] -= 1
        healed['version'] += 1
        next(iter(healed['players'].values()))['damage'] -= 1
        validate_boss(healed)  # Structurally valid, but it reverses committed damage.
        with self.assertRaises(BossError) as rejected:
            with self.r.store.connection(transaction=True) as conn:
                self.b._write(conn, healed)
        self.assertEqual(rejected.exception.code, 'progress_reversal')
        self.assertEqual(self.b.export(), saved)
        with self.assertRaises(BossError) as rejected:
            with self.r.store.connection(transaction=True) as conn:
                self.b._write(conn, fresh_raid())
        self.assertEqual(rejected.exception.code, 'new_raid_required')
        self.assertEqual(self.b.export(), saved)

    def test_pause_resume_restart_and_stale_raid(self):
        first=self.hit(); raid=first['state']['raid_id']
        self.b.control('pause',raid)
        with self.assertRaises(BossError):self.hit(guest='b',ip='192.0.2.2')
        self.b.control('resume',raid)
        self.assertEqual(self.hit(guest='b',ip='192.0.2.2')['state']['hp'],DEFAULT_HP-300)
        self.b.control('restart',raid,3_000_000)
        with self.assertRaises(BossError) as old:self.b.attack('a','192.0.2.1','blade',raid,'old-request-001')
        self.assertEqual(old.exception.code,'new_raid')
        state=self.b.export()
        self.assertEqual(state['hp'],3_000_000); self.assertEqual(len(state['history']),1)
        self.assertEqual(state['players'],{})

    def test_auth_csrf_malformed_attack_and_forged_damage(self):
        c,s=self.client()
        self.assertEqual(c.post('/play/api/attack',json={}).status_code,400)
        self.assertEqual(self.post(c,s,style=[]).status_code,400)
        forged=self.post(c,s,damage=99_999_999,cooldown=0,remaining=9999)
        self.assertEqual(forged.json['hit']['damage'],150)
        self.assertEqual(self.post(c,s).status_code,429)
        self.assertEqual(c.post('/admin/boss/action',data={'action':'pause'}).status_code,302)
        self.assertEqual(c.get('/play/api/state').headers['Cache-Control'],'no-store')
        # Public state does not reveal persisted identifiers, raw IPs or salt.
        payload=c.get('/play/api/state').text
        persisted=self.b.export()
        for private in (persisted['salt'],'192.0.2.1',*persisted['players'],*persisted['networks']):
            self.assertNotIn(private,payload)

    def test_admin_controls_require_superadmin_and_restart_confirmation(self):
        c,s=self.client()
        with c.session_transaction() as sess:sess.update(user='gingrsnaps',auth_version=1)
        form={'csrf':s['csrf'],'action':'restart','raid_id':s['state']['raid_id'],'health':'2400000'}
        self.assertEqual(c.post('/admin/boss/action',data=form).status_code,422)
        self.assertEqual(c.post('/admin/boss/action',data={**form,'confirm_restart':'yes'}).status_code,303)
        self.assertIn('Pause attacks',c.get('/admin?tab=boss').text)
        self.r.admin['users']['helper']=copy.deepcopy(self.r.admin['users']['gingrsnaps'])
        self.r.commit(self.r.admin,self.r.revision)
        with c.session_transaction() as sess:sess['user']='helper'
        self.assertEqual(c.post('/admin/boss/action',data={**form,'action':'pause'}).status_code,403)

    def test_digitalocean_ip_only_trusted_when_configured(self):
        a,sa=self.client(); b,sb=self.client()
        # Spoofing a header on direct hosting cannot get another allowance.
        a.environ_base['HTTP_DO_CONNECTING_IP']='198.51.100.1'
        b.environ_base['HTTP_DO_CONNECTING_IP']='198.51.100.2'
        self.assertEqual(self.post(a,sa).status_code,200)
        self.assertEqual(self.post(b,sb).status_code,429)
        self.app.extensions['settings'].proxy=True
        self.assertEqual(self.post(b,sb).status_code,200)
        c,sc=self.client('127.0.0.1')
        self.assertEqual(self.post(c,sc).status_code,503)
        c.environ_base['HTTP_DO_CONNECTING_IP']='198.51.100.3'
        c.environ_base['HTTP_X_FORWARDED_FOR']='198.51.100.1'
        self.assertEqual(self.post(c,sc).status_code,200)

    def test_guest_profile_survives_admin_logout(self):
        c,s=self.client(); name=s['state']['you']['name']
        c.post('/admin/logout',data={'csrf':s['csrf']})
        self.assertEqual(c.get('/play/api/state').json['state']['you']['name'],name)

    def test_recovery_preserves_game_identity_cooldowns_and_progress(self):
        c,s=self.client(); self.post(c,s)
        with c.session_transaction() as sess:sess.update(user='gingrsnaps',auth_version=1)
        recovery=c.get('/admin/recovery-backup').json
        self.assertEqual(recovery['community_boss'],self.b.export())
        with tempfile.TemporaryDirectory() as directory:
            root=Path(directory); (root/'private').mkdir()
            (root/'private/recovery.seed.json').write_text(json.dumps(recovery))
            restored=create_app(root,testing=True)
            try:
                restored_boss=restored.extensions['boss']
                self.assertEqual(restored_boss.export(),self.b.export())
                r=restored.test_client()
                r.set_cookie('rh_raider',c.get_cookie('rh_raider').value)
                current=r.get('/play/api/state').json
                self.assertEqual(current['state']['you']['name'],s['state']['you']['name'])
                self.assertEqual(current['state']['you']['damage'],150)
                self.assertEqual(self.post(r,current).status_code,429)
            finally:restored.extensions['runtime'].store.close()

    def test_corrupt_game_recovery_rolls_back_account_import(self):
        self.hit()
        value=copy.deepcopy(self.r.admin); value['community_boss']=self.b.export()
        value['community_boss']['hp']-=1
        with tempfile.TemporaryDirectory() as directory:
            root=Path(directory); (root/'private').mkdir()
            (root/'private/recovery.seed.json').write_text(json.dumps(value))
            with self.assertRaises(ValueError):create_app(root,testing=True)
        bad=self.b.export(); next(iter(bad['players'].values()))['last_attack']=float('nan')
        with self.assertRaises(ValueError):validate_boss(bad)

    def test_saved_game_survives_process_reconstruction(self):
        self.hit(); before=self.b.export()
        store=Store(self.r.config)
        try:self.assertEqual(CommunityBoss(store).export(),before)
        finally:store.close()

    def test_one_hundred_active_raiders_need_multiple_days(self):
        # Simulate 100 real profiles/IPs, 40 matching manual attacks per day.
        # Server time moves; no real sleeps or network calls are needed.
        ended_day=None
        for day in range(4):
            for turn in range(40):
                self.time.return_value=self.start+day*DAY+turn*60
                for player in range(100):
                    hit=self.hit(f'raider-{player}',f'203.0.113.{player+1}')
                    if hit['state']['hp']==0:
                        ended_day=day+1; break
                if ended_day:break
            if ended_day:break
            self.assertGreater(self.b.status()['hp'],0)
        self.assertEqual(ended_day,4)
        self.assertGreaterEqual(self.time.return_value-self.start,3*DAY)


if __name__=='__main__':unittest.main()
