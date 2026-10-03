"""Calendar, public privacy and persistence tests; never contacts live accounts."""
import copy
from datetime import datetime
import json
import re
import time
import unittest
from unittest.mock import patch

import test_app
from integrations import ProviderError
from race_support import EASTERN
from storage import Conflict
from wager_backend import create_app
from weekly_history import WeeklyHistory, clean_history, completed_weeks


def stamp(value):
    return int(datetime.fromisoformat(value).replace(tzinfo=EASTERN).timestamp())


class WeeklyHistoryTests(unittest.TestCase):
    setUp = test_app.AppTests.setUp
    action = test_app.AppTests.action
    schedule = test_app.AppTests.schedule
    form = test_app.AppTests.form

    def fill(self, now=None, count=30):
        rows = [test_app.player('HistoryPlayer%03d' % n, str(1000-n)) for n in range(count)]
        with patch.object(self.r.providers, 'shuffle', return_value=rows) as provider:
            self.r.history.check(now)
        return provider

    def test_tuesday_exact_cutoff_and_four_contiguous_completed_weeks(self):
        before = completed_weeks(stamp('2026-10-06T17:59:59'))
        after = completed_weeks(stamp('2026-10-06T18:00:00'))
        self.assertEqual(before[0]['id'], '2026-09-29')
        self.assertEqual(after[0]['id'], '2026-10-06')
        self.assertEqual(len(after), 4)
        for n, week in enumerate(after):
            for field in ('start_time', 'end_time'):
                local = datetime.fromtimestamp(week[field], EASTERN)
                self.assertEqual((local.weekday(), local.hour, local.minute), (1, 18, 0))
            if n:
                self.assertEqual(week['end_time'], after[n-1]['start_time'])

    def test_dst_weeks_follow_eastern_wall_time_not_168_fixed_hours(self):
        for end, hours in [('2026-03-10T18:00', 167), ('2026-11-03T18:00', 169)]:
            week = completed_weeks(stamp(end))[0]
            self.assertEqual(week['end_time']-week['start_time'], hours*3600)

    def test_top_25_and_all_public_responses_mask_names_before_delivery(self):
        provider = self.fill()
        self.assertEqual(provider.call_count, 4)
        for call, week in zip(provider.call_args_list, completed_weeks()):
            self.assertEqual(call.args[0]['start_time'], week['start_time'])
            self.assertEqual(call.args[0]['end_time'], week['end_time'])
        guest = self.app.test_client()
        for url in ('/history', '/history-state'):
            response = guest.get(url)
            self.assertEqual(response.status_code, 200)
            self.assertNotIn('HistoryPlayer', response.text)
            self.assertNotIn('shuffle_api_key', response.text)
            self.assertNotIn('raw_wager', response.text)
            self.assertIn('Hi******', response.text)
        value = guest.get('/history-state').json
        self.assertEqual(len(value['weeks']), 4)
        for week in value['weeks']:
            self.assertEqual(len(week['rows']), 25)
            self.assertEqual(week['count'], 30)
            self.assertEqual([row['rank'] for row in week['rows']], list(range(1, 26)))
            self.assertEqual(week['rows'][0]['wager'], '$1,000.00')
            self.assertEqual(week['rows'][-1]['wager'], '$976.00')

    def test_views_and_fresh_cache_never_call_provider(self):
        self.fill()
        with patch.object(self.r.providers, 'shuffle', side_effect=AssertionError('Must use cache')):
            self.r.history.check()
            weeks = completed_weeks()
            for week in weeks:
                response = self.client.get('/history?week='+week['id'])
                self.assertEqual(response.status_code, 200)
                self.assertIn('data-selected-week="'+week['id']+'"', response.text)
                self.assertEqual(self.client.get('/history-state?week='+week['id']).json['selected']['id'], week['id'])
            self.assertEqual(self.client.get('/history-state?week=bad').json['selected']['id'], weeks[0]['id'])

    def test_rollover_retains_only_last_four_weeks_and_automatically_loads_newest(self):
        now = stamp('2026-10-06T17:59:59')
        self.fill(now)
        with patch.object(self.r.providers, 'shuffle', return_value=[test_app.player()]):
            self.r.history.check(now+1)
        self.assertEqual({w['id'] for w in self.r.store.live('weekly_history')['weeks']},
                         {w['id'] for w in completed_weeks(now+1)})
        self.assertEqual(self.r.history.public(now=now+1)['selected']['rows'][0]['username'], 'Al******')

    def test_archived_settings_apply_only_to_the_matching_week(self):
        week = completed_weeks()[0]
        admin = copy.deepcopy(self.r.admin)
        old = copy.deepcopy(admin['site_settings'])
        old.update(start_time=week['start_time'], end_time=week['end_time'])
        old['prizes']['1'] = '321'
        admin['race_history'].append(dict(site_settings=old, overrides={'HistoryPlayer000':'5000'}))
        admin['overrides'] = {'HistoryPlayer001':'99999'}
        admin['site_settings']['prizes']['1'] = '9999'
        self.r.commit(admin, self.r.revision)
        self.fill()
        value = self.r.history.public()
        self.assertEqual(value['weeks'][0]['rows'][0]['wager'], '$5,000.00')
        self.assertEqual(value['weeks'][0]['rows'][0]['prize'], '$321.00')
        self.assertEqual(value['weeks'][0]['rows'][24]['prize'], '$0.00')
        self.assertFalse(value['weeks'][1]['prizes_known'])
        self.assertEqual(value['weeks'][1]['rows'][0]['wager'], '$1,000.00')
        self.assertEqual(value['weeks'][1]['rows'][0]['prize'], '—')

    def test_failure_retains_results_and_respects_provider_retry(self):
        now = int(time.time())
        self.fill(now)
        before = self.r.history.public(now=now)['selected']['rows']
        later = now+86400
        with patch.object(self.r.providers, 'shuffle', side_effect=ProviderError('secret upstream details', status=429, retry_after=180)) as provider:
            self.assertEqual(self.r.history.check(later), 180)
            self.assertEqual(provider.call_count, 1)
        value = self.r.history.public(now=later)
        self.assertEqual(value['selected']['rows'], before)
        self.assertEqual(value['selected']['status'], 'delayed')
        self.assertNotIn('secret upstream details', json.dumps(value))
        self.assertEqual(self.r.store.live('weekly_history')['weeks'][0]['retry_at'], later+180)

    def test_missing_and_successfully_empty_are_distinct(self):
        self.assertEqual(self.r.history.public()['selected']['status'], 'loading')
        self.assertIsNone(self.r.history.public()['selected']['count'])
        self.fill(count=0)
        value = self.r.history.public()['selected']
        self.assertEqual(value['status'], 'ready')
        self.assertEqual(value['count'], 0)

    def test_history_save_survives_restart_and_full_private_recovery(self):
        self.fill()
        before = self.r.history.public()
        reloaded = WeeklyHistory(self.r.config, self.r.store, self.r.providers)
        self.assertEqual(reloaded.public()['weeks'], before['weeks'])
        response = self.client.get('/admin/recovery-backup')
        self.assertEqual(len(response.json['weekly_history']['weeks']), 4)
        target = self.root/'fresh'
        (target/'private').mkdir(parents=True)
        (target/'private/recovery.seed.json').write_bytes(response.data)
        restored = create_app(target, testing=True)
        runtime = restored.extensions['runtime']
        try:
            self.assertEqual(runtime.history.public()['weeks'], before['weeks'])
            self.assertNotIn('weekly_history', runtime.admin)
        finally:
            runtime.store.close()

    def test_configuration_change_during_fetch_cannot_publish_old_results(self):
        def changed(site):
            admin = copy.deepcopy(self.r.admin)
            admin['site_settings']['campaign_code_filter'] = 'other'
            self.r.commit(admin, self.r.revision)
            return [test_app.player()]
        with patch.object(self.r.providers, 'shuffle', side_effect=changed):
            with self.assertRaises(Conflict):
                self.r.history.check()
        self.assertEqual(self.r.history.public()['selected']['rows'], [])

    def test_invalid_recovery_cache_rejected(self):
        self.fill()
        saved = self.r.store.live('weekly_history')
        saved['weeks'][0]['rows'][0]['weighted_wager'] = 'NaN'
        with self.assertRaises(ValueError):
            clean_history(saved)

    def test_homepage_defeat_progress_server_rendered_zero_partial_and_full(self):
        for hp in (2400000, 765432, 0):
            admin = self.client.get('/admin/boss/status').json
            response = self.client.post('/admin/boss/action', data={
                'csrf':'test-token', 'action':'remaining_health', 'raid_id':admin['state']['raid_id'],
                'health_revision':admin['state']['health_revision'],
                'health':str(hp), 'confirm_health':'yes'})
            self.assertEqual(response.status_code, 303)
            page = self.client.get('/').text
            progress = re.search(r'<progress id="inviteHealth"[^>]*>', page).group()
            self.assertAlmostEqual(float(re.search(r'value="([^"]+)"', progress).group(1)), (2400000-hp)/2400000*100)
            self.assertIn('max="100"', progress)


if __name__ == '__main__':
    unittest.main()
