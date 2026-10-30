"""Static release sanity checks; provider credentials are never opened."""
import unittest
import sys
from pathlib import Path
root=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(root/'tools'))
from deployment_diagnostics import evaluate

class DeploymentTests(unittest.TestCase):
    def test_buildpack_has_no_second_pip_install(self):
        self.assertTrue(evaluate(root))
    def test_python_is_pinned(self):
        self.assertTrue((root/'runtime.txt').read_text().strip().startswith('python-3.13.'))
    def test_waitress_is_main_server(self):
        self.assertIn('server.run()', (root/'wager_backend.py').read_text())
    def test_health_is_local_not_external(self):
        text=(root/'wager_backend.py').read_text()
        idx=text.index('    @app.get("/healthz")')
        self.assertIn('return jsonify(ok=True, release=RELEASE)',text[idx:idx+180])

if __name__=='__main__': unittest.main()
