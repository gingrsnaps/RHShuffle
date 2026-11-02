"""Deployment source checks; deliberately avoids importing Flask or reading secrets."""
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch
import sys
root=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(root/'tools'))
from deployment_diagnostics import evaluate, check_archive

class DigitalOceanDeploymentTests(unittest.TestCase):
    def test_root_is_detectable(self):
        self.assertTrue(evaluate(root))
    def test_manifest_excludes_optional_data(self):
        manifest=json.loads((root/'BUILD_MANIFEST.json').read_text())['files']
        self.assertIn('wager_backend.py',manifest)
        self.assertIn('templates/index.html',manifest)
        self.assertFalse(any(p.startswith(('data/','private/','docs/','tests/')) for p in manifest))
    def test_private_state_not_required_by_release_manifest(self):
        manifest=json.loads((root/'BUILD_MANIFEST.json').read_text())['files']
        self.assertNotIn('private/settings.json',manifest)
        self.assertNotIn('data/state.json',manifest)
    def test_no_duplicate_build_install(self):
        self.assertNotIn('build_command:',(root/'app.yaml').read_text())
    def test_run_command_is_present(self):
        self.assertIn('run_command: python wager_backend.py',(root/'app.yaml').read_text())

if __name__=='__main__':unittest.main()
