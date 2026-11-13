"""V13 regression tests for the exact admin and payout failures seen in production."""
import ast
import copy
import json
import re
import tempfile
import unittest
from pathlib import Path

from jinja2 import Environment, FileSystemLoader, StrictUndefined

from operations_log import ActivityLog
from empiredrop_features import DEFAULT_REWARDS, rewards_public, validate_rewards

ROOT = Path(__file__).resolve().parents[1]
START = 1794351600
END = 1794956400


def route_inventory():
    tree = ast.parse((ROOT / 'wager_backend.py').read_text(encoding='utf-8'))
    routes = {}
    for node in ast.walk(tree):
        if not isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            continue
        for decorator in node.decorator_list:
            if not isinstance(decorator, ast.Call) or not isinstance(decorator.func, ast.Attribute):
                continue
            if not isinstance(decorator.func.value, ast.Name) or decorator.func.value.id != 'app':
                continue
            if decorator.func.attr not in {'get', 'post', 'route'} or not decorator.args:
                continue
            value = decorator.args[0]
            if not isinstance(value, ast.Constant) or not isinstance(value.value, str):
                continue
            verbs = {'GET'} if decorator.func.attr == 'get' else {'POST'} if decorator.func.attr == 'post' else {'GET', 'POST'}
            routes.setdefault(value.value, set()).update(verbs)
    return routes


class AdminReliabilityV13(unittest.TestCase):
    def test_shared_admin_imports_every_macro_used_by_child_templates(self):
        text = (ROOT / 'templates/admin.html').read_text(encoding='utf-8')
        line = next(line for line in text.splitlines() if "from 'macros.html'" in line)
        for macro in ('form_fields', 'action_feedback', 'field', 'player_rows'):
            self.assertIn(macro, line)

    def test_all_admin_templates_parse_with_strict_undefined_environment(self):
        env = Environment(loader=FileSystemLoader(ROOT / 'templates'), undefined=StrictUndefined)
        for name in env.list_templates():
            env.parse((ROOT / 'templates' / name).read_text(encoding='utf-8'))

    def test_empiredrop_activity_events_are_supported(self):
        log = ActivityLog()
        for event, level in (
            ('empire_rewards_draft', 'success'),
            ('empire_rewards_published', 'success'),
            ('empire_rewards_save_failed', 'warning'),
        ):
            row = log.record('admin', level, event, code='empire_rewards' if level == 'success' else 'validation', count=10)
            self.assertEqual(row['event'], event)

    def test_operational_logging_is_fail_safe_in_web_layer(self):
        source = (ROOT / 'wager_backend.py').read_text(encoding='utf-8')
        self.assertIn('def safe_activity(', source)
        self.assertIn("LOG.exception('ACTIVITY A structured event could not be recorded.')", source)
        self.assertEqual(source.count('activity.record('), 1)

    def test_payout_workflow_writes_then_verifies_public_projection(self):
        source = (ROOT / 'wager_backend.py').read_text(encoding='utf-8')
        for marker in (
            "conn['admin']['empiredrop_rewards_draft']",
            "conn['admin']['empiredrop_rewards']",
            'payout write could not be verified',
            'public projection did not refresh',
            "empire_rewards_published",
        ):
            self.assertIn(marker, source)
        value = copy.deepcopy(DEFAULT_REWARDS)
        value.update(enabled=True, revision=2, updated_at=1, updated_by='test')
        value['prizes'] = {str(i): str((11-i)*100) for i in range(1, 11)}
        valid = validate_rewards(value)
        public = rewards_public(valid)
        self.assertTrue(public['enabled'])
        self.assertEqual(len(public['prizes']), 10)

    def test_every_visible_literal_admin_link_and_form_is_registered(self):
        routes = route_inventory()
        literal = set()
        for template in (ROOT / 'templates').glob('*.html'):
            text = template.read_text(encoding='utf-8')
            for match in re.finditer(r'(?:href|action)=["\'](/admin[^"\']*)', text):
                path = match.group(1).split('#', 1)[0].split('?', 1)[0]
                if '{{' not in path:
                    literal.add(path)
        self.assertEqual(sorted(path for path in literal if path not in routes), [])

    def test_direct_workspaces_render_instead_of_redirecting(self):
        source = (ROOT / 'wager_backend.py').read_text(encoding='utf-8')
        expectations = {
            'admin_shuffle_page': "workspace('shuffle')",
            'admin_shuffle_schedule_page': "workspace('race')",
            'admin_shuffle_players_page': "workspace('players')",
            'admin_empiredrop_page': "workspace('empiredrop')",
            'admin_settings_page': "workspace('settings')",
            'admin_activity_page': "workspace('activity')",
        }
        tree = ast.parse(source)
        functions = {node.name: ast.get_source_segment(source, node) for node in ast.walk(tree) if isinstance(node, ast.FunctionDef)}
        for name, marker in expectations.items():
            self.assertIn(marker, functions[name])

    def test_bundled_dates_are_november_10_through_17_eastern(self):
        state = json.loads((ROOT / 'data/state.json').read_text(encoding='utf-8'))
        seed = json.loads((ROOT / 'private/admin_store.seed.json').read_text(encoding='utf-8'))
        settings = json.loads((ROOT / 'private/settings.json').read_text(encoding='utf-8'))
        for site in (state['admin']['site_settings'], seed['site_settings'], settings):
            self.assertEqual((site['start_time'], site['end_time']), (START, END))
        for admin in (state['admin'], seed):
            self.assertEqual((admin['empiredrop_race']['start_time'], admin['empiredrop_race']['end_time']), (START, END))

    def test_root_requirements_and_deployment_markers_exist(self):
        for name in ('requirements.txt', 'runtime.txt', 'wager_backend.py', 'app.yaml', 'BUILD_MANIFEST.json'):
            self.assertTrue((ROOT / name).is_file(), name)
        requirements = (ROOT / 'requirements.txt').read_text(encoding='utf-8')
        for line in ('Flask==3.1.3', 'Werkzeug==3.1.9', 'requests==2.34.2', 'waitress==3.0.2', 'tzdata==2026.6'):
            self.assertIn(line, requirements)

    def test_optional_history_metadata_is_accessed_safely(self):
        text = (ROOT / 'templates/admin_empiredrop.html').read_text(encoding='utf-8')
        self.assertNotIn('item.race_meta.slug', text)
        self.assertIn("history_meta = item.get('race_meta') or {}", text)
        self.assertIn("history_meta.get('slug')", text)


if __name__ == '__main__':
    unittest.main()
