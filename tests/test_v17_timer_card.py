from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]


class V17TimerCardTests(unittest.TestCase):
    def test_shared_macro_still_renders_both_providers(self):
        page = (ROOT / "templates" / "index.html").read_text(encoding="utf-8")
        macro = (ROOT / "templates" / "macros.html").read_text(encoding="utf-8")
        self.assertGreaterEqual(page.count("public_race_summary("), 2)
        self.assertIn('class="clock race-countdown"', macro)

    def test_timer_cards_use_natural_height_shuffle_proportions(self):
        css = (ROOT / "static" / "v16-system.css").read_text(encoding="utf-8")
        self.assertIn("align-items:center", css)
        self.assertIn("--race-summary-card-width:520px", css)
        self.assertIn("width:min(100%,var(--race-summary-card-width))", css)
        self.assertIn("min-height:0!important", css)
        self.assertIn("height:auto", css)
        self.assertIn("border-radius:18px!important", css)
        self.assertNotIn("--race-summary-min-height", css)
        self.assertNotIn("align-items:stretch", css)
        self.assertNotIn("height:100%", css)
        self.assertNotIn("grid-template-rows:auto minmax(3.7rem,auto)", css)

    def test_both_countdowns_keep_identical_typography(self):
        css = (ROOT / "static" / "v16-system.css").read_text(encoding="utf-8")
        self.assertIn("#shuffleRaceClock .race-countdown", css)
        self.assertIn("#empireRaceClock .race-countdown", css)
        self.assertIn("font-size:var(--race-countdown-size)!important", css)
        self.assertIn("font-variant-numeric:tabular-nums lining-nums", css)


if __name__ == "__main__":
    unittest.main()
