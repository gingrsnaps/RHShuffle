"""Offline V12 navigation and retired-feature contract checks."""
import ast
import re
import unittest
from pathlib import Path
from urllib.parse import urlsplit

from admin_navigation import ADMIN_PATHS, ADMIN_TABS, admin_link

ROOT = Path(__file__).resolve().parents[1]


def decorator_routes():
    tree = ast.parse((ROOT/'wager_backend.py').read_text(encoding='utf-8'))
    routes = {}
    for fn in ast.walk(tree):
        if not isinstance(fn, (ast.FunctionDef, ast.AsyncFunctionDef)):
            continue
        for dec in fn.decorator_list:
            if not isinstance(dec, ast.Call) or not isinstance(dec.func, ast.Attribute):
                continue
            if not isinstance(dec.func.value, ast.Name) or dec.func.value.id != 'app':
                continue
            if dec.func.attr not in {'get','post','route'} or not dec.args or not isinstance(dec.args[0], ast.Constant):
                continue
            path = dec.args[0].value
            if not isinstance(path, str):
                continue
            verbs = {'GET'} if dec.func.attr == 'get' else {'POST'} if dec.func.attr == 'post' else {'GET','POST'}
            routes.setdefault(path, set()).update(verbs)
    return routes


class NavigationV12(unittest.TestCase):
    def test_every_canonical_admin_destination_is_registered(self):
        routes = decorator_routes()
        self.assertEqual(set(ADMIN_PATHS), set(ADMIN_TABS))
        for tab, path in ADMIN_PATHS.items():
            self.assertEqual(admin_link(tab), path)
            self.assertIn(path, routes, tab)
            self.assertIn('GET', routes[path], tab)

    def test_visible_direct_admin_paths_exist(self):
        routes = decorator_routes()
        expected = {
            '/admin/leaderboards/empiredrop/schedule',
            '/admin/leaderboards/empiredrop/payouts',
            '/admin/leaderboards/empiredrop/source',
            '/admin/recovery',
        }
        self.assertTrue(expected.issubset(routes))
        template = (ROOT/'templates/admin.html').read_text(encoding='utf-8')
        for path in expected - {'/admin/recovery'}:
            self.assertIn(path, template)


    def test_visible_literal_admin_links_and_forms_resolve(self):
        routes = decorator_routes()
        literal = set()
        for path in (ROOT/'templates').glob('*.html'):
            text = path.read_text(encoding='utf-8')
            self.assertNotIn('/admin?tab=', text, path.name)
            self.assertNotIn('/admin/section/', text, path.name)
            for match in re.finditer(r'(?:href|action)=["\'](/admin[^"\']*)', text):
                value = match.group(1).split('#', 1)[0].split('?', 1)[0]
                if '{{' not in value:
                    literal.add(value)
        missing = sorted(path for path in literal if path not in routes)
        self.assertEqual(missing, [], f'unregistered visible admin destinations: {missing}')

    def test_retired_feature_has_no_routes_templates_or_assets(self):
        routes = decorator_routes()
        self.assertFalse(any(path == '/play' or path.startswith('/play/') for path in routes))
        for path in ('boss.py','boss_avatar.py','boss_extras.py','boss_progress.py',
                     'templates/boss.html','templates/admin_boss.html',
                     'static/boss.js','static/boss.css','static/boss-preview.js'):
            self.assertFalse((ROOT/path).exists(), path)
        public = (ROOT/'templates/base.html').read_text() + (ROOT/'templates/index.html').read_text()
        self.assertNotRegex(public, r'/play|communityBoss|Boss Fight')

    def test_root_deployment_markers_and_lean_requirements(self):
        for name in ('requirements.txt','runtime.txt','wager_backend.py','app.yaml','BUILD_MANIFEST.json'):
            self.assertTrue((ROOT/name).is_file(), name)
        production = (ROOT/'requirements.txt').read_text()
        for package in ('Flask','requests','waitress','tzdata'):
            self.assertIn(package, production)
        self.assertNotIn('Pillow', production)
        self.assertFalse((ROOT/'requirements-postgres.txt').exists())

    def test_empiredrop_payout_workflow_is_explicit(self):
        template = (ROOT/'templates/admin_empiredrop.html').read_text()
        source = (ROOT/'wager_backend.py').read_text()
        self.assertIn('name="reward_revision"', template)
        self.assertIn('value="draft"', template)
        self.assertIn('value="publish"', template)
        self.assertNotIn('name="enabled"', template[template.index('id="empireRewards"'):template.index('id="empireBackup"')])
        for marker in ('empiredrop_rewards_draft', 'public projection did not refresh', 'payout write could not be verified'):
            self.assertIn(marker, source)


if __name__ == '__main__':
    unittest.main()
