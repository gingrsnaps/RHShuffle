from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]


class V16AssetBudgetTests(unittest.TestCase):
    def test_runtime_frontend_asset_budget(self):
        javascript = sum(p.stat().st_size for p in (ROOT/'static').glob('*.js'))
        css = sum(p.stat().st_size for p in (ROOT/'static').glob('*.css'))
        self.assertLess(javascript, 260_000, f'JavaScript budget exceeded: {javascript:,} bytes')
        self.assertLess(css, 190_000, f'CSS budget exceeded: {css:,} bytes')

    def test_no_provider_specific_countdown_font_rule_remains(self):
        empire = (ROOT/'static'/'empiredrop.css').read_text(encoding='utf-8')
        self.assertNotIn('#empireRaceClock .clock {font-size:', empire)
        index = (ROOT/'templates'/'index.html').read_text(encoding='utf-8')
        self.assertGreaterEqual(index.count('public_race_summary('), 2)


if __name__ == '__main__':
    unittest.main()
