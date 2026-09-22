"""Real app/storage tests with synthetic provider responses; no live accounts."""
import copy
import io
import json
import os
from pathlib import Path
import re
import socket
import subprocess
import sys
import tempfile
import threading
import time
import unittest
from unittest.mock import patch
from urllib.request import urlopen

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from wager_backend import create_app
from config import Config
from integrations import ProviderError, Providers
from race import aggregate, normalize, phase, rank
from race_support import eastern_epoch, money_input, race_key
from storage import Conflict, Store, StoreError

ROOT = Path(__file__).resolve().parents[1]
PASSWORD = "a-private-test-password"


def player(name="AlphaMember", amount="100", raw="150", campaign="Red"):
    return dict(username=name, weightedWagerAmount=amount, wagerAmount=raw, campaignCode=campaign)


class AppTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.env = patch.dict(os.environ, {"APP_ENV":"test", "DATABASE_URL":"", "ADMIN_BOOTSTRAP_PASS":PASSWORD,
                              "SUPERADMIN_USER":"gingrsnaps", "PORT":"8080"}, clear=True)
        self.env.start(); self.addCleanup(self.env.stop)
        self.app = create_app(self.root, testing=True)
        self.r = self.app.extensions["runtime"]
        self.addCleanup(self.r.store.close)
        self.client = self.app.test_client()
        self.guard = patch("requests.Session.request", side_effect=AssertionError("Unexpected live request"))
        self.guard.start(); self.addCleanup(self.guard.stop)
        with self.client.session_transaction() as s:
            s.update(user="gingrsnaps", auth_version=1, csrf="test-token")

    def schedule(self, start=None, end=None):
        now = int(time.time())
        admin = copy.deepcopy(self.r.admin)
        admin["site_settings"].update(start_time=start or now-3600, end_time=end or now+86400)
        from race import empty
        self.r.commit(admin, self.r.revision, snapshot=empty(admin["site_settings"]))

    def update(self, rows):
        with patch.object(self.r.providers, "shuffle", return_value=rows):
            self.r.check("shuffle")

    def action(self, name, **values):
        if name == 'save_race' and values.get('confirm_race') == 'yes' and 'review_token' not in values:
            preview = self.action(name, **{k:v for k,v in values.items() if k != 'confirm_race'})
            match = re.search('name="review_token" value="([^"]+)"', preview.text)
            if match:
                values['review_token'] = match.group(1)
        return self.client.post("/admin/action", data={"csrf":"test-token", "action":name, "tab":"settings",
                                                       "revision":self.r.revision, **values})

    def form(self):
        from race_support import local_input
        site = copy.deepcopy(self.r.admin["site_settings"])
        return {**site, "start_et":local_input(site["start_time"]), "end_et":local_input(site["end_time"]),
                **{"prize_"+k:v for k,v in site["prizes"].items()}, "tab":"race"}

    def test_native_login_and_all_dashboard_pages(self):
        c=self.app.test_client()
        page=c.get("/admin")
        csrf=re.search('name="csrf" value="([^"]+)"',page.text).group(1)
        response=c.post("/admin",data={"csrf":csrf,"username":"GINGRSNAPS","password":PASSWORD},follow_redirects=True)
        self.assertEqual(response.status_code,200)
        self.assertIn("CONTROL CENTER",response.text)
        for tab in ("overview","race","players","settings"):
            p=c.get('/admin?tab='+tab)
            self.assertEqual(p.status_code,200)
            self.assertIn('aria-label="Administration"',p.text)

    def test_startup_with_windows_default_encoding_preserves_existing_state(self):
        # Use the shipped assets, including Unicode that CP1252 cannot decode.
        # Linux normally hides this Windows startup failure with its UTF-8 locale.
        static = self.root / "static"
        static.mkdir()
        for asset in (ROOT / "static").glob("*"):
            if asset.suffix in {".css", ".js"}:
                (static / asset.name).write_bytes(asset.read_bytes())
        before = self.r.store.admin()
        native_open = Path.open

        def windows_open(path, mode="r", buffering=-1, encoding=None, errors=None, newline=None):
            if "b" not in mode and encoding in (None, "locale"):
                encoding = "cp1252"
            return native_open(path, mode, buffering, encoding, errors, newline)

        with patch.object(Path, "open", windows_open):
            app = create_app(self.root, testing=True)
            try:
                client = app.test_client()
                self.assertEqual(client.get("/healthz").status_code, 200)
                self.assertIn("Sign in", client.get("/admin").text)
                self.assertEqual(app.extensions["runtime"].store.admin(), before)
            finally:
                app.extensions["runtime"].store.close()

    def test_login_csrf_is_bound_to_browser(self):
        a,b=self.app.test_client(),self.app.test_client()
        a.get('/admin');b.get('/admin')
        with a.session_transaction() as s: csrf=s['csrf']
        self.assertEqual(b.post('/admin',data={'csrf':csrf,'username':'gingrsnaps','password':PASSWORD}).status_code,400)

    def test_refresh_queues_background_work_and_populates_both_boards(self):
        self.schedule()
        amount = {"value": "100"}
        headers = {"Accept": "application/json"}

        def wait_for_total(expected):
            deadline = time.monotonic() + 2
            while time.monotonic() < deadline:
                value = self.client.get("/data").json
                if value["rows"] and value["rows"][0]["wager"] == expected:
                    return value
                time.sleep(.01)
            self.fail("Background refresh did not publish the expected leaderboard")

        with patch.object(self.r.providers, "shuffle", side_effect=lambda site: [player(amount=amount["value"])]), \
             patch.object(self.r.providers, "kick", return_value=dict(live=False, channel="redhunllef")):
            self.r.start()
            try:
                wait_for_total("$100.00")
                revision = self.r.revision
                amount["value"] = "250"
                response = self.client.post("/admin/action", headers=headers,
                    data={"csrf": "test-token", "action": "refresh", "service": "shuffle"})
                self.assertEqual(response.status_code, 202)
                self.assertTrue(response.is_json)
                value = wait_for_total("$250.00")
                self.assertEqual(value["rows"][0]["username"], "Al******")
                admin = self.client.get("/admin/status?tab=players").json
                self.assertEqual(admin["participants"][0]["username"], "AlphaMember")
                self.assertEqual(admin["participants"][0]["wager"], "$250.00")
                self.assertEqual(self.r.revision, revision)
            finally:
                self.r.stop()

    def test_refresh_invalid_csrf_returns_specific_json_without_queueing(self):
        response = self.client.post("/admin/action", headers={"Accept": "application/json"},
                                    data={"action": "refresh", "csrf": "expired"})
        self.assertEqual(response.status_code, 400)
        self.assertTrue(response.is_json)
        self.assertIn("form expired", response.json["error"])
        self.assertFalse(any(event.is_set() for event in self.r.events.values()))

    def test_refresh_expired_login_returns_json_and_does_not_queue(self):
        client = self.app.test_client()
        response = client.post("/admin/action", headers={"Accept": "application/json"},
                               data={"action": "refresh", "csrf": "test-token"})
        self.assertEqual(response.status_code, 401)
        self.assertTrue(response.is_json)
        self.assertFalse(any(event.is_set() for event in self.r.events.values()))

    def test_fetch_http_errors_are_json_and_native_errors_remain_html(self):
        headers = {"Accept": "application/json"}
        responses = [
            (self.client.post("/[object HTMLInputElement]", headers=headers), 404),
            (self.client.get("/admin/action", headers=headers), 405),
            (self.client.post("/admin/action", headers=headers,
                 data={"csrf": "test-token", "action": "refresh", "service": "invalid"}), 400),
        ]
        for response, status in responses:
            self.assertEqual(response.status_code, status)
            self.assertTrue(response.is_json)
            self.assertEqual(response.json["status"], status)
            self.assertIn("error", response.json)
        native = self.client.get("/missing")
        self.assertEqual(native.status_code, 404)
        self.assertEqual(native.mimetype, "text/html")

    def test_refresh_storage_failure_is_json(self):
        with patch.object(self.r, "sync", side_effect=StoreError("Database temporarily unreachable")):
            response = self.client.post("/admin/action", headers={"Accept": "application/json"},
                data={"csrf": "test-token", "action": "refresh"})
        self.assertEqual(response.status_code, 503)
        self.assertEqual(response.json["error"], "Database temporarily unreachable")

    def test_refresh_unexpected_failure_has_safe_json_error(self):
        self.app.config["PROPAGATE_EXCEPTIONS"] = False
        with patch.object(self.r, "request_refresh", side_effect=RuntimeError("private-error-detail")):
            response = self.client.post("/admin/action", headers={"Accept": "application/json"},
                data={"csrf": "test-token", "action": "refresh"})
        self.assertEqual(response.status_code, 500)
        self.assertTrue(response.is_json)
        self.assertNotIn("private-error-detail", response.text)

    def test_empty_leaderboards_explain_waiting_empty_filtered_and_failed_sources(self):
        self.schedule()
        self.assertIn("first successful update", self.client.get("/data").json["leaderboard_message"])
        self.update([])
        self.assertIn("returned no wagers", self.client.get("/data").json["leaderboard_message"])
        self.update([player(campaign="Other")])
        self.assertIn("campaign filter", self.client.get("/data").json["leaderboard_message"])
        self.update([player(amount="0")])
        self.assertIn("$0.01", self.client.get("/data").json["leaderboard_message"])
        with patch.object(self.r.providers, "shuffle", side_effect=ProviderError("Fixture source timeout")):
            self.r.check("shuffle")
        self.assertIn("delayed", self.client.get("/data").json["leaderboard_message"])
        self.update([player()])
        self.assertEqual(self.client.get("/data").json["leaderboard_message"], "")
        diagnostic = self.client.get("/admin/diagnostics").json["diagnostics"]
        self.assertEqual(diagnostic["campaign_filter"], "Red")
        self.assertEqual(diagnostic["qualifying_players"], 1)

    def test_login_rate_limit(self):
        c=self.app.test_client();c.get('/admin')
        with c.session_transaction() as s: csrf=s['csrf']
        for _ in range(5):
            self.assertEqual(c.post('/admin',data={'csrf':csrf,'username':'x','password':'wrong'}).status_code,401)
        self.assertEqual(c.post('/admin',data={'csrf':csrf,'username':'x','password':'wrong'}).status_code,429)

    def test_protected_endpoints_never_disclose_names(self):
        self.schedule();self.update([player()])
        public=self.app.test_client()
        for path in ('/admin/status','/admin/export.csv','/admin/diagnostics','/admin/backup'):
            self.assertEqual(public.get(path).status_code,401)
        self.assertNotIn('AlphaMember',public.get('/data').text)
        self.assertIn('Al******',public.get('/data').text)
        for path in ('/private/settings.json','/private/admin_store.seed.json','/data/redhunllef.sqlite3'):
            self.assertEqual(public.get(path).status_code,404)

    def test_mixed_shuffle_response_updates_and_warns(self):
        self.schedule();self.update([player(amount='100')]);before=self.r.revision
        self.update([player(amount='200'),player('Missing',None),None,player('BetaMember','150',campaign=' Red ')])
        data=self.client.get('/data').json
        self.assertEqual(data['rows'][0]['wager'],'$200.00')
        self.assertEqual(len(data['rows']),2)
        self.assertEqual(data['freshness']['state'],'partial')
        self.assertEqual(self.r.revision,before,'A provider update must not rewrite admin state')
        admin=self.client.get('/admin/status?code_red=1').json
        self.assertEqual(len(admin['red']),2)
        self.assertIn('AlphaMember',str(admin['participants']))

    def test_invalid_response_retains_saved_results(self):
        self.schedule();self.update([player()]);stamp=self.r.shuffle['updated_at']
        self.update([None,player(amount='NaN')])
        self.assertEqual(self.r.shuffle['rows'][0]['wager'],'$100.00')
        self.assertEqual(self.r.shuffle['updated_at'],stamp)
        self.assertEqual(self.client.get('/data').json['freshness']['state'],'delayed')

    def test_valid_empty_response_clears_old_rows(self):
        self.schedule();self.update([player()]);self.update([])
        self.assertEqual(self.r.shuffle['rows'],[])
        self.assertEqual(self.client.get('/data').json['freshness']['state'],'current')

    def test_clean_response_clears_warning(self):
        self.schedule();self.update([player(),None]);self.update([player()])
        self.assertEqual(self.r.shuffle['warning'],'')

    def test_missing_raw_does_not_freeze_weighted_wager(self):
        self.schedule();self.update([player(amount='200',raw='bad')])
        row=self.r.shuffle['rows'][0]
        self.assertEqual(row['wager'],'$200.00');self.assertIsNone(row['raw_wager'])

    def test_future_race_never_calls_shuffle(self):
        now=int(time.time());self.schedule(now+3600,now+7200)
        with patch.object(self.r.providers,'shuffle') as mock:
            self.r.check('shuffle');mock.assert_not_called()
        self.assertEqual(self.r.public()['site']['race_state'],'upcoming')

    def test_kick_failure_does_not_publish_offline(self):
        with patch.object(self.r.providers,'kick',return_value={'live':True,'channel':'redhunllef','title':'Live fixture','viewers':42}):self.r.check('kick')
        with patch.object(self.r.providers,'kick',side_effect=ProviderError('Kick timed out')):self.r.check('kick')
        self.assertTrue(self.r.kick['live']);self.assertFalse(self.r.public()['stream']['available'])

    def test_override_retains_raw_and_original_and_can_be_removed(self):
        self.schedule();self.update([player()])
        self.assertEqual(self.action('override',username='AlphaMember',amount='250').status_code,303)
        row=self.r.shuffle['rows'][0]
        self.assertEqual((row['weighted_wager'],row['original_weighted_wager'],row['raw_wager']),('250','100','150'))
        self.action('override',username='AlphaMember',amount='')
        self.assertEqual(self.r.shuffle['rows'][0]['wager'],'$100.00')

    def test_zero_override_stays_manageable(self):
        self.schedule();self.update([player()]);self.action('override',username='AlphaMember',amount='0')
        self.assertEqual(self.r.shuffle['rows'],[])
        self.assertEqual(self.r.shuffle['edits'][0]['username'],'AlphaMember')

    def test_race_change_requires_confirmation_and_archives(self):
        self.schedule();self.update([player()]);old=copy.deepcopy(self.r.admin)
        form={**self.form(),'start_et':'2027-01-01T18:00','end_et':'2027-01-08T18:00'}
        response=self.action('save_race',**form)
        self.assertEqual(response.status_code,200);self.assertEqual(self.r.admin,old)
        self.assertEqual(self.action('save_race',confirm_race='yes',**form).status_code,303)
        self.assertEqual(len(self.r.admin['race_history']),1)
        self.assertEqual(self.r.admin['race_history'][0]['leaderboard_snapshots']['last_top15'][0]['username'],'AlphaMember')
        self.assertEqual(self.r.shuffle['rows'],[])
        self.assertEqual(self.r.admin['users'],old['users'])

    def test_invalid_settings_preserve_draft(self):
        self.schedule();before=copy.deepcopy(self.r.admin)
        response=self.action('save_race',**{**self.form(),'race_title':'Unsaved draft','prize_2':'bad'})
        self.assertEqual(response.status_code,422);self.assertIn('Unsaved draft',response.text)
        self.assertEqual(self.r.admin,before)

    def test_stale_revision_rejected(self):
        self.assertEqual(self.action('override',revision=0,username='User',amount='100').status_code,409)

    def test_case_insensitive_duplicate_accounts(self):
        self.assertEqual(self.action('add_account',username='GINGRSNAPS',new_password=PASSWORD,confirm_password=PASSWORD).status_code,422)

    def test_removed_account_loses_access(self):
        self.action('add_account',username='another_admin',new_password=PASSWORD,confirm_password=PASSWORD)
        other=self.app.test_client()
        with other.session_transaction() as s:s.update(user='another_admin',auth_version=1,csrf='test-token')
        self.assertEqual(other.get('/admin/status').status_code,200)
        self.action('remove_account',username='another_admin')
        self.assertEqual(other.get('/admin/status').status_code,401)

    def test_superadmin_cannot_be_removed(self):
        self.assertEqual(self.action('remove_account',username='GINGRSNAPS').status_code,422)

    def test_non_superadmin_cannot_manage_accounts(self):
        self.action('add_account',username='another_admin',new_password=PASSWORD,confirm_password=PASSWORD)
        with self.client.session_transaction() as s:s.update(user='another_admin',auth_version=1)
        self.assertEqual(self.action('remove_account',username='gingrsnaps').status_code,403)

    def test_password_change_revokes_other_sessions(self):
        other=self.app.test_client()
        with other.session_transaction() as s:s.update(user='gingrsnaps',auth_version=1)
        self.assertEqual(self.action('password',current_password=PASSWORD,new_password=PASSWORD+'2',confirm_password=PASSWORD+'2').status_code,303)
        self.assertEqual(other.get('/admin/status').status_code,401)
        self.assertEqual(self.client.get('/admin/status').status_code,200)

    def test_safe_backup_and_redacted_diagnostics(self):
        self.schedule();self.update([player()])
        backup=self.client.get('/admin/backup').json
        self.assertNotIn('users',backup);self.assertNotIn('secret_key',backup)
        report=self.client.get('/admin/diagnostics').text
        self.assertNotIn('AlphaMember',report);self.assertNotIn('pw_hash',report)

    def test_restore_previews_then_preserves_accounts(self):
        self.schedule();self.update([player()]);saved=self.client.get('/admin/backup').json
        self.action('override',username='AlphaMember',amount='999')
        response=self.action('preview_restore',backup=(io.BytesIO(json.dumps(saved).encode()),'backup.json'))
        self.assertEqual(response.status_code,200);self.assertEqual(self.r.shuffle['rows'][0]['wager'],'$999.00')
        identifier=re.search('name="restore_token" value="([^"]+)"',response.text).group(1)
        users=copy.deepcopy(self.r.admin['users'])
        self.assertEqual(self.action('restore',restore_token=identifier).status_code,303)
        self.assertEqual(self.r.shuffle['rows'][0]['wager'],'$100.00');self.assertEqual(self.r.admin['users'],users)
        with self.r.store.connection() as c:
            self.assertGreaterEqual(c.execute('SELECT count(*) FROM rh_recovery').fetchone()[0],2)

    def test_bad_restore_does_not_mutate_state(self):
        self.schedule();saved=self.client.get('/admin/backup').json;saved['site_settings']['prizes']['1']='NaN'
        before=copy.deepcopy(self.r.admin)
        response=self.action('preview_restore',backup=(io.BytesIO(json.dumps(saved).encode()),'backup.json'))
        self.assertEqual(response.status_code,422);self.assertEqual(self.r.admin,before)

    def test_code_red_first_100_excludes_other_and_unknown_campaigns(self):
        self.schedule();self.update([player('User'+str(n),str(1000-n)) for n in range(130)]+[player('Unknown','100',campaign=None),player('Other','100',campaign='Other')])
        self.assertEqual(len(self.r.shuffle['red']),100);self.assertEqual(self.r.shuffle['red_total'],130)
        self.assertEqual(self.r.shuffle['missing_campaign'],1)

    def test_csv_filter_preserves_rank_and_escapes_formula(self):
        self.schedule();self.update([player('AlphaMember','200'),player('=cmd','100')])
        value=self.client.get('/admin/export.csv?q=%3Dcmd').text
        self.assertIn("'=cmd",value);self.assertIn('2,',value);self.assertNotIn('AlphaMember',value)

    def test_existing_store_wins_on_restart(self):
        self.action('add_account',username='new_admin',new_password=PASSWORD,confirm_password=PASSWORD)
        again=Store(self.app.extensions['settings'])
        try:self.assertIn('new_admin',again.admin()[1]['users'])
        finally:again.close()

    def test_seed_import_preserves_original_bytes_and_unknown_fields(self):
        target=self.root/'other';target.mkdir()
        value=copy.deepcopy(self.r.admin);value['unknown_legacy_field']={'keep':'this'}
        raw=json.dumps(value,indent=3).encode();(target/'admin_store.json').write_bytes(raw)
        store=Store(Config(target))
        try:
            self.assertEqual(store.admin()[1]['users'],value['users'])
            self.assertEqual(store.admin()[1]['unknown_legacy_field'],value['unknown_legacy_field'])
            self.assertEqual((target/'admin_store.json').read_bytes(),raw)
        finally:store.close()

    def test_corrupt_seed_is_never_replaced(self):
        target=self.root/'bad';target.mkdir();(target/'admin_store.json').write_text('{broken',encoding='utf-8')
        with self.assertRaises(RuntimeError):Store(Config(target))
        self.assertEqual((target/'admin_store.json').read_text(encoding='utf-8'),'{broken')

    def test_production_starts_locally_without_database_configuration(self):
        # Reproduce the App Platform environment that used to stop startup.
        with patch.dict(sys.modules,{'psycopg':None}), patch.dict(os.environ,{'APP_ENV':'production','DATABASE_URL':'${race-db.DATABASE_URL}',
                                     'DATABASE_SSLMODE':'unused-invalid-value'}):
            app=create_app(self.root,testing=True)
            runtime=app.extensions['runtime']
            try:
                self.assertFalse(runtime.store.pg)
                self.assertTrue(app.extensions['settings'].production)
                client=app.test_client()
                response=client.get('/admin',base_url='https://example.test')
                self.assertIn('Secure',response.headers['Set-Cookie'])
                csrf=re.search('name="csrf" value="([^"]+)"',response.text).group(1)
                response=client.post('/admin',base_url='https://example.test',data={'csrf':csrf,'username':'gingrsnaps','password':PASSWORD},follow_redirects=True)
                self.assertEqual(response.status_code,200)
                self.assertIn('Local storage is active',response.text)
                self.assertEqual(client.get('/admin/status',base_url='https://example.test').status_code,200)
                self.assertEqual(runtime.admin['users'],self.r.admin['users'])
            finally:runtime.store.close()

    def test_private_recovery_restores_accounts_and_dates_on_a_fresh_instance(self):
        self.schedule();self.update([player()])
        self.action('add_account',username='retained_admin',new_password=PASSWORD+'2',confirm_password=PASSWORD+'2')
        self.action('password',current_password=PASSWORD,new_password=PASSWORD+'3',confirm_password=PASSWORD+'3')
        self.action('override',username='AlphaMember',amount='321')
        response=self.client.get('/admin/recovery-backup')
        self.assertEqual(response.status_code,200)
        self.assertIn('no-store',response.headers['Cache-Control'])
        self.assertIn('recovery.seed.json',response.headers['Content-Disposition'])
        self.assertEqual(response.json['users'],self.r.admin['users'])
        target=self.root/'fresh';(target/'private').mkdir(parents=True)
        (target/'private/recovery.seed.json').write_bytes(response.data)
        # Newest recovery must win over the original legacy seed on a new disk.
        original=copy.deepcopy(response.json);original['site_settings']['race_title']='Old seed title'
        (target/'admin_store.json').write_text(json.dumps(original),encoding='utf-8')
        restored=create_app(target,testing=True)
        runtime=restored.extensions['runtime']
        try:
            for key in ['users','site_settings','overrides','race_history','secret_key']:
                self.assertEqual(runtime.admin[key],self.r.admin[key])
            self.assertEqual(runtime.shuffle['rows'][0]['wager'],'$321.00')
            client=restored.test_client();page=client.get('/admin')
            csrf=re.search('name="csrf" value="([^"]+)"',page.text).group(1)
            self.assertEqual(client.post('/admin',data={'csrf':csrf,'username':'gingrsnaps','password':PASSWORD+'3'}).status_code,303)
            self.assertEqual((target/'private/recovery.seed.json').read_bytes(),response.data)
            candidate=copy.deepcopy(runtime.admin);candidate['site_settings']['race_title']='Newer local state'
            runtime.commit(candidate,runtime.revision)
        finally:runtime.store.close()
        reopened=Store(Config(target))
        try:self.assertEqual(reopened.admin()[1]['site_settings']['race_title'],'Newer local state')
        finally:reopened.close()

    def test_private_recovery_requires_superadmin_and_is_never_public(self):
        self.assertEqual(self.app.test_client().get('/admin/recovery-backup').status_code,401)
        self.action('add_account',username='another_admin',new_password=PASSWORD,confirm_password=PASSWORD)
        with self.client.session_transaction() as s:s.update(user='another_admin',auth_version=1)
        response=self.client.get('/admin/recovery-backup')
        self.assertEqual(response.status_code,403)
        self.assertNotIn('pw_hash',response.text)
        self.assertNotIn('href="/admin/recovery-backup"',self.client.get('/admin?tab=settings').text)
        self.assertNotIn('pw_hash',self.client.get('/data').text)

    def test_invalid_recovery_file_stops_import_without_resetting_accounts(self):
        target=self.root/'invalid-recovery';(target/'private').mkdir(parents=True)
        seed=target/'private/recovery.seed.json';seed.write_text('{broken',encoding='utf-8')
        (target/'private/admin_store.seed.json').write_text(json.dumps(self.r.admin),encoding='utf-8')
        with self.assertRaises(RuntimeError):Store(Config(target))
        self.assertEqual(seed.read_text(encoding='utf-8'),'{broken')

    def test_postgres_is_explicit_and_never_silently_falls_back(self):
        with patch.dict(os.environ,{'STORAGE_MODE':'postgres','DATABASE_URL':''}):
            with self.assertRaisesRegex(ValueError,'needs DATABASE_URL'):Config(self.root)
        with patch.dict(os.environ,{'STORAGE_MODE':'postgres','DATABASE_URL':'postgresql://fixture'}):
            self.assertEqual(Config(self.root).db_url,'postgresql://fixture')

    def test_shuffle_and_kick_workers_do_not_block_each_other(self):
        self.schedule();entered,release,kick=threading.Event(),threading.Event(),threading.Event()
        def slow(site):entered.set();release.wait(3);return [player()]
        def fast(site):kick.set();return dict(live=False,channel='redhunllef')
        with patch.object(self.r.providers,'shuffle',side_effect=slow),patch.object(self.r.providers,'kick',side_effect=fast):
            self.r.start()
            try:
                self.assertTrue(entered.wait(2));self.assertTrue(kick.wait(2));self.assertEqual(self.client.get('/data').status_code,200)
            finally:release.set();self.r.stop()

    def test_no_stale_publication_after_settings_change(self):
        self.schedule()
        def changing(site):
            candidate=copy.deepcopy(self.r.admin);candidate['site_settings']['race_title']='Changed during fetch'
            self.r.commit(candidate,self.r.revision)
            return [player()]
        with patch.object(self.r.providers,'shuffle',side_effect=changing):self.r.check('shuffle')
        self.assertEqual(self.r.shuffle['rows'],[]);self.assertTrue(self.r.events['shuffle'].is_set())

    def test_failed_old_request_does_not_poison_new_race_or_delay_its_check(self):
        self.schedule()
        before = self.r.revision
        def old_request(site):
            candidate = copy.deepcopy(self.r.admin)
            candidate['site_settings']['start_time'] -= 86400
            from race import empty
            self.r.commit(candidate, before, snapshot=empty(candidate['site_settings']))
            self.r.request_refresh('shuffle')
            raise ProviderError('The old date range was rejected', status=400)
        with patch.object(self.r.providers, 'shuffle', side_effect=old_request):
            delay = self.r.check('shuffle')
        self.assertEqual(self.r.shuffle['error'], '')
        self.assertEqual(delay, 0)
        self.assertTrue(self.r.events['shuffle'].is_set())
        self.update([player(amount='350')])
        self.assertEqual(self.client.get('/data').json['rows'][0]['wager'], '$350.00')

    def test_manual_request_during_a_check_queues_one_followup(self):
        self.r.jobs['shuffle']['state'] = 'checking'
        self.r.request_refresh('shuffle')
        self.r.request_refresh('shuffle')
        self.assertTrue(self.r.events['shuffle'].is_set())
        self.assertEqual(self.r.jobs['shuffle']['state'], 'checking')

    def test_bottom_confirmation_button_actually_publishes_the_new_dates(self):
        self.schedule()
        form = {**self.form(), 'start_et':'2026-09-01T18:00', 'end_et':'2026-09-08T18:00'}
        preview = self.action('save_race', **form)
        # Submit the same visible bottom button a person uses after reviewing.
        bottom = preview.text.split('class="save-bar"', 1)[1]
        submitter = re.search(r'<button\b[^>]*type="submit"[^>]*>', bottom).group(0)
        attributes = dict(re.findall(r'([\w-]+)="([^"]*)"', submitter))
        extra = {attributes['name']:attributes.get('value', '')} if 'name' in attributes else {}
        response = self.action('save_race', **form, **extra)
        self.assertEqual(response.status_code, 303)
        self.assertEqual(self.r.admin['site_settings']['start_time'], eastern_epoch(form['start_et']))

    def test_date_publication_and_automatic_refresh_through_real_http_transport(self):
        """Exercise requests/JSON/parser/worker publication against a local fixture.

        The scheduling interval is shortened only inside this isolated test.
        Real Shuffle credentials and services are never contacted.
        """
        from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
        from urllib.parse import parse_qs, urlsplit
        from race_support import local_input
        import requests
        self.schedule()
        old_start = self.r.admin['site_settings']['start_time']
        entered, release = threading.Event(), threading.Event()
        fixture = {'amount':'200', 'windows':[]}

        class Upstream(BaseHTTPRequestHandler):
            def log_message(self, *_):
                pass
            def do_GET(self):
                query = parse_qs(urlsplit(self.path).query)
                window = (int(query['startTime'][0]), int(query['endTime'][0]))
                fixture['windows'].append(window)
                if window[0] == old_start:
                    entered.set()
                    release.wait(3)
                    status, payload = 400, {'error':'old range'}
                else:
                    status, payload = 200, {'data':[player(amount=fixture['amount'])]}
                body = json.dumps(payload).encode('utf-8')
                self.send_response(status)
                self.send_header('Content-Type', 'application/json')
                self.send_header('Content-Length', str(len(body)))
                self.end_headers()
                self.wfile.write(body)

        server = ThreadingHTTPServer(('127.0.0.1', 0), Upstream)
        thread = threading.Thread(target=server.serve_forever, daemon=True)
        thread.start()
        self.guard.stop()
        native_request = requests.Session.request
        self.r.config.credentials['shuffle_api_key'] = 'fixture-key'

        def route(session, method, url, **kwargs):
            parsed = urlsplit(url)
            self.assertEqual(parsed.netloc, 'affiliate.shuffle.com')
            return native_request(session, method,
                f'http://127.0.0.1:{server.server_port}'+parsed.path, **kwargs)

        def wait_for_wager(amount):
            deadline = time.monotonic()+3
            while time.monotonic() < deadline:
                value = self.client.get('/data').json
                if value['rows'] and value['rows'][0]['wager'] == amount:
                    return
                time.sleep(.01)
            self.fail('Latest source value was not automatically published')

        try:
            with patch('requests.Session.request', new=route), patch('runtime.INTERVAL', .2), \
                 patch.object(self.r.providers, 'kick', return_value=dict(live=False, channel='redhunllef')):
                self.r.start()
                try:
                    self.assertTrue(entered.wait(2))
                    now = int(time.time())
                    form = {**self.form(), 'start_et':local_input(now-7200), 'end_et':local_input(now+7200)}
                    self.assertEqual(self.action('save_race', **form).status_code, 200)
                    self.assertEqual(self.action('save_race', confirm_race='yes', **form).status_code, 303)
                    release.set()
                    wait_for_wager('$200.00')
                    self.assertEqual(self.r.shuffle['error'], '')
                    self.assertEqual(self.r.jobs['shuffle']['http_status'], 200)
                    self.assertEqual(fixture['windows'][1][0], eastern_epoch(form['start_et']))
                    # No manual request: the next scheduled cycle must publish.
                    fixture['amount'] = '375'
                    wait_for_wager('$375.00')
                    admin = self.client.get('/admin/status?tab=players').json
                    self.assertEqual(admin['participants'][0]['wager'], '$375.00')
                    self.assertEqual(admin['participants'][0]['username'], 'AlphaMember')
                    self.assertGreaterEqual(len(fixture['windows']), 3)
                finally:
                    release.set()
                    self.r.stop()
        finally:
            server.shutdown()
            server.server_close()
            thread.join(timeout=2)

    def test_new_dates_clear_old_soft_retry_but_preserve_provider_rate_limit(self):
        self.schedule()
        job = self.r.jobs['shuffle']
        job.update(checked_scope='previous-race', not_before=time.monotonic()+60, http_status=400, retry_after=0)
        first = self.r.request_refresh('shuffle')
        self.assertEqual(job['not_before'], 0)
        second = self.r.request_refresh('shuffle')
        self.assertEqual(first['requests'], second['requests'], 'Repeated clicks should coalesce')
        deadline = time.monotonic()+120
        job.update(not_before=deadline, http_status=429, retry_after=120)
        self.r.request_refresh('shuffle')
        self.assertEqual(job['not_before'], deadline)

    def test_superseded_rate_limit_still_delays_new_provider_requests(self):
        self.schedule()
        def limited(site):
            candidate = copy.deepcopy(self.r.admin)
            candidate['site_settings']['start_time'] -= 86400
            from race import empty
            self.r.commit(candidate, self.r.revision, snapshot=empty(candidate['site_settings']))
            raise ProviderError('Provider rate limit', status=429, retry_after=120)
        with patch.object(self.r.providers, 'shuffle', side_effect=limited):
            delay = self.r.check('shuffle')
        self.assertEqual(delay, 120)
        self.assertEqual(self.r.shuffle['error'], '')
        self.assertTrue(self.r.events['shuffle'].is_set())

    def test_provider_envelopes_and_range_never_use_lifetime_fallback(self):
        self.schedule();providers=self.r.providers;providers.config.credentials['shuffle_api_key']='fake-key'
        for key in ('data','results','leaderboard','users','items'):
            with patch.object(providers,'request',return_value={'data':None,key:[player()]}) as mock:
                self.assertEqual(len(providers.shuffle(self.r.admin['site_settings'])),1)
                self.assertIn('startTime',mock.call_args.kwargs['params'])
        with patch.object(providers,'request',side_effect=ProviderError('Bad race',status=400)) as mock:
            with self.assertRaises(ProviderError):providers.shuffle(self.r.admin['site_settings'])
            self.assertEqual(mock.call_count,1)

    def test_kick_reauthenticates_once_after_401(self):
        providers=self.r.providers;providers.config.credentials.update(kick_client_id='fake',kick_client_secret='fake')
        channel={'data':[{'slug':'redhunllef','stream':{'is_live':True,'viewer_count':42},'stream_title':'Fixture'}]}
        with patch.object(providers,'request',side_effect=[{'access_token':'first'},ProviderError('expired',status=401),{'access_token':'second'},channel]) as mock:
            value=providers.kick(self.r.admin['site_settings'])
            self.assertEqual(mock.call_count,4);self.assertTrue(value['live']);self.assertEqual(value['viewers'],42)

    def test_sole_launch_command_serves_actual_http(self):
        with socket.socket() as sock:sock.bind(('127.0.0.1',0));port=sock.getsockname()[1]
        env={**os.environ,'PORT':str(port),'APP_ENV':'production','STORAGE_MODE':'local',
             'DATABASE_URL':'${race-db.DATABASE_URL}','LOCAL_DATABASE_PATH':str(self.root/'cli.sqlite3'),
             'SETTINGS_PATH':str(self.root/'missing-settings.json'),'ADMIN_SEED_PATH':str(self.root/'missing-seed.json'),
             'PYTHONIOENCODING':'utf-8'}
        log=self.root/'startup.log'
        with log.open('w',encoding='utf-8') as stream:
            process=subprocess.Popen([sys.executable,str(ROOT/'wager_backend.py')],env=env,stdout=stream,stderr=stream)
            try:
                for _ in range(60):
                    if process.poll() is not None:self.fail(log.read_text(encoding='utf-8'))
                    try:
                        with urlopen(f'http://127.0.0.1:{port}/healthz',timeout=.3) as response:
                            self.assertTrue(json.load(response)['ok']);break
                    except OSError:time.sleep(.05)
                else:self.fail('Server did not bind its HTTP port: '+log.read_text(encoding='utf-8'))
                with urlopen(f'http://127.0.0.1:{port}/admin',timeout=2) as response:self.assertIn('Sign in',response.read().decode())
            finally:process.terminate();process.wait(timeout=8)
        self.assertIn('listening on 0.0.0.0:',log.read_text(encoding='utf-8'))
        self.assertIn('cadence=60s',log.read_text(encoding='utf-8'))
        self.assertIn('no external database is required',log.read_text(encoding='utf-8'))
        self.assertNotIn('ERROR STARTUP',log.read_text(encoding='utf-8'))


class CalculationTests(unittest.TestCase):
    def test_timezone_boundaries(self):
        for value in ('2026-03-08T02:30','2026-11-01T01:30'):
            with self.assertRaises(ValueError):eastern_epoch(value)
        self.assertEqual(time.gmtime(eastern_epoch('2026-09-21T18:00')).tm_hour,22)

    def test_invalid_money(self):
        for value in ('NaN','-5','1,23','25k'):
            with self.assertRaises(ValueError):money_input(value)

    def test_phase_boundaries(self):
        site={'start_time':100,'end_time':200}
        self.assertEqual([phase(site,x) for x in (99,100,199,200)],['upcoming','active','active','ended'])

    def test_exact_aggregation_and_incomplete_raw_totals(self):
        rows=[dict(username='user',weighted='0.1',raw=None,raw_invalid=True,row_count=1),dict(username='user',weighted='0.2',raw='500',row_count=1)]
        value=aggregate(rows)['user'];self.assertEqual(value['weighted'],'0.3');self.assertIsNone(value['raw'])
        self.assertEqual(aggregate(rows,'max')['user']['weighted'],'0.2')


if __name__=='__main__':unittest.main()
