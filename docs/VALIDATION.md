# Validation — 2026.10.08-community-clarity7

Tests used disposable synthetic accounts, seeds and provider replies. No live
Shuffle/Kick account was contacted and no real-money wager was placed.

| Check | Result |
| --- | --- |
| Python regression suite | 247 executed: 244 passed initially. Three assertions expected old interface text; those assertions were updated and all three targeted cases passed. No unresolved Python failure. |
| JavaScript regression suite | All 75 passed in the final run. Includes Top 5 expansion/focus retention, automatic polling, private-data clearing on session expiry, health-bar direction, name persistence and actual HTTP/cookie flows. |
| Partial boss settings | Name and damage saves retain HP and unrelated settings; invalid, stale, missing-CSRF and anonymous requests cannot commit. |
| Local admin feeds | Minute responses can omit duplicate rankings; backward-compatible responses retain them. The protected five-second feed includes boss status and returns 304 when unchanged. |
| Experience browser | Mobile navigation, boss-before-standings ordering, receipt expansion/focus, pending poker draft preservation, reserved balance, copyable private health report and public layouts passed. |
| Consecutive saves browser | Name followed by damage saves display fresh receipts/revisions. HP is retained. Unsaved damage survives polls; appearance preview stays local. |
| Player browser | Boss name survives reload; Gaming prefills that same name for its original one-time confirmation. Attack cooldown, editing/recovery links and +100k admin grant work. |
| Layout | Homepage exercised at 320/390/768/1440px; boss controls, admin, Gaming and arena at 320/390px. Narrow recovery-button overflow was corrected. No overflow in the final affected-page check. |
| Browser exceptions | None in the completed experience and clarity runs. |
| Community concurrency | 100 signed players on one IP, 200 direct ledger calls, 16 threads; every wager settles once and retries return the original result. |
| Preserved source | Original private settings/account seed/logos, integrations, race/history, storage and all gaming/fairness engines compared byte-for-byte against the previous release. |
| Package | Strict single-launcher completeness check, ZIP CRC check and archive/source SHA-256 comparison performed during packaging. |

The Python evidence consists of the broad run and focused corrected-text reruns,
not a claim of a second full 247-test execution. The repeat-save browser test
found and resolved a real fragment-only navigation bug. The UI layout tests found
and resolved the narrow recovery-button overflow.

This was Linux with Python 3.12 and Chromium. Installed libraries were Flask
3.1.3, requests 2.34.2, Waitress 3.0.2, Pillow 12.3.0 and tzdata 2026.4. Deployment
pins remain unchanged, including Python 3.13.12 and tzdata 2026.3. Neither a live
DigitalOcean deployment nor native Windows/Python 3.14 was tested.

Current screenshots: PREVIEW_DESKTOP/MOBILE, HEALTH_DESKTOP/MOBILE,
BOSS_CONTROLS_DESKTOP/MOBILE, BOSS_MOBILE, HISTORY_MOBILE and POKER_MOBILE.
Other images are retained design references. All screenshots use synthetic data.

## Repeat locally

```bash
python -m unittest discover -s tests -p 'test_*.py'
python tests/render_fixtures.py .test-fixtures
npm --prefix tests install --ignore-scripts
npm --prefix tests test
```

Optional native scripts: tests/experience_motion.cjs and tests/clarity_motion.cjs.
Set RH_TEST_PYTHON, RH_CHROMIUM and RH_SCREENSHOTS for local interpreters/browser
and output. Existing gaming_motion.cjs and holdem_motion.cjs remain included.
Node/Chromium are development tools, not production requirements.

## Limits

Live provider permissions and availability were not tested. Local JSON state
requires an externally retained recovery checkpoint before replacing an App
Platform container. Lab timings are not production guarantees or field INP
measurements. The existing independently implemented proof verifier remains
included; this is not a third-party fairness or comprehensive accessibility audit.
