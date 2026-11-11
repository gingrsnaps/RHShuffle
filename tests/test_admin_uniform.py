"""Pure offline contract tests for uniform admin presentation and safe data feeds."""
import json
from pathlib import Path
import unittest

from operations_log import ActivityLog
from provider_admin import summarize_providers
from race import normalize, rank
from empiredrop_features import mask_public_username
from empiredrop_races import normalize_race

ROOT=Path(__file__).resolve().parents[1]


class ProviderDashboardTests(unittest.TestCase):
    def fixtures(self):
        base = {
            'health': {'components': [
                {'key': 'shuffle', 'state': 'good', 'status': 'Connected'},
                {'key': 'empiredrop', 'state': 'warning', 'status': 'Needs attention'}]},
            'jobs': {'shuffle': {'last_success': 1750000000, 'attempt_at': 1750000010}},
            'diagnostics': {'received': 10, 'accepted': 7, 'missing_campaign': 2,
                            'rejected': {'invalid weighted amount': 1}},
            'rows': [{'username':'PRIVATE_SHUFFLE_USER'}],
            'count': 7,
        }
        empire = {
            'race_meta': {'slug': 'test-race', 'engine':'RANKING', 'type':'WAGER',
                          'ranks_limit':10, 'is_active':True},
            'rows': [{'username':'Ha*********ms','user_id':'REF_HASH'}],
            'source_mode':'races', 'refresh_interval':300,
            'updated_at':1750000000, 'attempt_at':1750000100,
            'error_kind':'rate_limit'
        }
        return base, empire

    def test_both_providers_use_same_safe_operational_schema(self):
        data, empire = self.fixtures()
        result = summarize_providers(data, empire)
        self.assertEqual(set(result), {'shuffle','empiredrop'})
        self.assertEqual(set(result['shuffle']), set(result['empiredrop']))
        self.assertEqual(result['shuffle']['refresh_seconds'],60)
        self.assertEqual(result['empiredrop']['refresh_seconds'],300)
        self.assertEqual(result['empiredrop']['metric'],'Wagered')
        self.assertTrue(any('campaign metadata' in text for text in result['shuffle']['issues']))
        self.assertTrue(any('rate limit' in text.lower() for text in result['empiredrop']['issues']))
        content=json.dumps(result)
        self.assertNotIn('PRIVATE_SHUFFLE_USER',content)
        self.assertNotIn('REF_HASH',content)
        self.assertNotIn('Ha*********ms',content)

    def test_deposit_and_raffle_display_are_not_mislabelled_as_wagers(self):
        data, empire = self.fixtures()
        empire['race_meta'].update(engine='RAFFLE',type='DEPOSIT')
        raffle=summarize_providers(data,empire)['empiredrop']
        self.assertEqual(raffle['metric'],'Tickets')
        self.assertTrue(any('not wagered currency' in text for text in raffle['issues']))
        empire['race_meta']['engine']='RANKING'
        deposit=summarize_providers(data,empire)['empiredrop']
        self.assertEqual(deposit['metric'],'Deposited')

    def test_missing_provider_data_is_honestly_marked_unverified(self):
        data, empire=self.fixtures()
        data['jobs']['shuffle'].update(last_success=0)
        empire.update(updated_at=0,rows=[])
        results=summarize_providers(data,empire)
        self.assertIn('No verified',results['shuffle']['issues'][0])
        self.assertIn('No verified',results['empiredrop']['issues'][0])

    def test_masked_public_names_remain_stable(self):
        self.assertEqual(mask_public_username('Ha*********ms'),'Ha******')
        self.assertEqual(mask_public_username('ShufflePlayer'),'Sh******')

    def test_empire_openapi_minor_units_and_rank_ties(self):
        detail={
          'race':{'engine':'RANKING','type':'WAGER','currency':'EUR','ranks_limit':10},
          'ranking':[
            {'rank':1,'total':563744,'unit':'EUR','user':{'name':'Ha*******','hash_id':'U1'}},
            {'rank':1,'total':563744,'unit':'EUR','user':{'name':'Ot*******','hash_id':'U2'}},
            {'rank':3,'total':999,'unit':'EUR','user':{'name':'Tr*******','hash_id':'U3'}},
          ]
        }
        rows=normalize_race(detail,{})
        self.assertEqual([x['rank'] for x in rows],[1,1,3])
        self.assertEqual(rows[0]['wager'],'€5,637.44')
        self.assertEqual(rows[2]['wager'],'€9.99')

    def test_shuffle_rejects_fabricated_weighted_totals(self):
        rows=[{'username':'user-a','weightedWager': '100.50', 'wagerAmount':'120.00', 'campaign':'red'},
              {'username':'user-b','weightedWager': 'NaN', 'campaign':'red'}]
        value=normalize(rows,{'campaign_code_filter':'red'})
        self.assertEqual(value['received'],2)
        self.assertEqual(value['accepted'],1)
        self.assertEqual(value['rejected']['invalid weighted amount'],1)
        ranking, _,_=rank(value['source'],{})
        self.assertEqual(ranking[0]['wager'],'$100.50')

    def test_logs_do_not_accept_unrestricted_error_text(self):
        log=ActivityLog(maxlen=3)
        log.record('shuffle','warning','refresh_failed',code='access',http_status=403)
        log.record('empiredrop','success','refresh_ok',count=4,http_status=200)
        log.record('admin','info','settings_saved',code='secret sk_prod_example')
        entry=log.list()[0]
        self.assertEqual(entry['code'],'unknown')
        report=log.export()
        self.assertEqual(report['summary']['total'],3)
        self.assertEqual(report['summary']['levels']['warning'],1)
        self.assertNotIn('sk_prod_example',json.dumps(report))
        self.assertNotIn('PRIVATE_SHUFFLE_USER',json.dumps(report))

    def test_uniform_templates_and_log_controls_exist(self):
        admin=(ROOT/'templates/admin.html').read_text()
        self.assertIn('admin-providers.js', admin)
        self.assertIn('Activity & logs', (ROOT/'wager_backend.py').read_text())
        for template in ('admin_shuffle.html','admin_empiredrop.html'):
            self.assertIn('admin_provider_summary.html', (ROOT/'templates'/template).read_text())
        panel=(ROOT/'templates/admin_health.html').read_text()
        for control in ('opsSource','opsLevel','opsSearch','opsExport','opsExportTxt'):
            self.assertIn('id="'+control+'"',panel)
        self.assertNotIn('filterPlayers);',(ROOT/'static/admin-empiredrop.js').read_text())
        partial=(ROOT/'templates/admin_provider_summary.html').read_text()
        self.assertIn("'empireAdminTitle' if provider.key == 'empiredrop'",partial)


if __name__=='__main__':unittest.main()
