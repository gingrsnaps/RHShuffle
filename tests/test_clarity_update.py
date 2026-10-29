"""UI contract smoke tests for the central admin and provider separation.
The original test file was not among the user's individual uploads.
"""
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


class ProviderUiContractTests(unittest.TestCase):
    def test_public_has_two_separate_boards(self):
        content = (ROOT/'templates/index.html').read_text(encoding='utf-8')
        self.assertIn('id="shuffleBoard"', content)
        self.assertIn('id="empireBoard"', content)
        self.assertIn('https://empiredrop.com/c/red', content)

    def test_admin_has_two_independent_tabs(self):
        for name in ('admin_shuffle.html', 'admin_empiredrop.html'):
            self.assertTrue((ROOT/'templates'/name).is_file())
        content = (ROOT/'wager_backend.py').read_text(encoding='utf-8')
        self.assertIn('"shuffle":"Shuffle"', content)
        self.assertIn('"empiredrop":"EmpireDrop"', content)


if __name__ == '__main__':
    unittest.main()
