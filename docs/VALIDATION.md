# Validation — 2026.10.08-community-polish6

Checks used disposable synthetic accounts, game seeds and provider replies.
No live Shuffle/Kick credentials were used and no real-money wagers were placed.

| Check | Evidence |
| --- | --- |
| Existing Python tests | 238 executed. 237 passed initially; the remaining assertion expected the previous release name. It was changed to compare the current release constant, and all 17 tests in that module then passed. |
| New health/release tests | All 6 passed: provider-independent readiness, failed local writes, admin-session enforcement, support-report privacy, request IDs, consistent pending-hand export, recovery comparisons, 100-player retries, and missing-asset detection. |
| JavaScript regression suite | All 74 passed. After final admin/report changes, all 26 tests in the affected shared/admin modules passed again. |
| Independent proof vectors | 484 Python/JavaScript matches: 47 v1, 86 v2, 112 v3, 151 v4 and 88 v5 receipts. Tampering checks remained passing. |
| Native game browser tests | All eight games played and verified. No gameplay navigation. Dice drag stayed synchronized. Keno/Baccarat dealt sequentially. Multiple Plinko drops survived resizing and finished in their recorded slots. |
| Hold'em browser tests | Legal raises/costs, all-in double-click idempotency, lost nonterminal response recovery, legacy Video Poker completion, and new Hold'em afterward passed. |
| Experience browser tests | Every mobile header destination visible; homepage standings first; five-row history expands; focus and unsaved raise survive polling; wallet shows reserved points; redundant opening form hides during a hand; health-report copying excludes private data. |
| Layout | No document overflow in exercised 320/390/768/1440px homepage views, mobile game paths, admin overview, boss and history. Reduced-motion behavior exercised. |
| Browser exceptions | None in the completed native game/Hold'em/experience checks. |
| Community concurrency | 100 players on one IP, 200 direct ledger calls, 16 threads. Each wager settled once, including retries; balances and proofs validated. |
| Loading lab sample | Five cold pages at 390px, 4x CPU slowdown, 150ms latency and 200KB/s. Observed LCP approximately 0.9–1.3s. Details and limits in PERFORMANCE.md. |
| Original configuration | Original private settings/account seed, logo files, provider integration code and game/fairness engines retained; hashes compared against the saved baseline. |

The runs above resolve all observed test failures. They are a broad initial run
plus focused correction runs, not a claim that a single final 244-test command
was executed. Existing tests additionally cover admin permissions, upload
validation, state rollback, weekly/Eastern-time windows and older proofs.

The environment was Linux, Python 3.12 and headless Chromium. Installed test
libraries were Flask 3.1.3, requests 2.34.2, waitress 3.0.2, Pillow 12.3.0 and tzdata
2026.4. The deployment requirements retain the existing tzdata 2026.3 pin and the
runtime declaration retains Python 3.13.12. This is not a native Windows/Python
3.14 or DigitalOcean deployment test.

Current screenshots in this folder are named HEALTH_DESKTOP, HEALTH_MOBILE,
POKER_MOBILE, GAMING_DESKTOP, PREVIEW_MOBILE, BOSS_MOBILE and HISTORY_MOBILE.
Other screenshots are retained earlier design references. All use synthetic data.

## Repeat checks

```bash
python -m unittest discover -s tests -p 'test_*.py'
python tests/render_fixtures.py .test-fixtures
npm --prefix tests install --ignore-scripts
npm --prefix tests test
```

Native scripts: gaming_motion.cjs, holdem_motion.cjs and experience_motion.cjs
inside tests/. Set RH_TEST_PYTHON, RH_CHROMIUM and RH_SCREENSHOTS when using a
specific Python/browser/output folder. Node and browser tooling are optional
development dependencies, not production launch requirements.

## Limits

This package was not deployed to the user's DigitalOcean service. Live provider
availability and account permissions were not tested. JSON/local-file storage
cannot survive a destroyed App Platform container without an externally retained
checkpoint. Animation frame rate depends on the player's device. Receipt replay
is independently implemented but is not a third-party fairness certification.
Accessibility checks cover the exercised controls, focus, sizing and layouts;
this is not a comprehensive assistive-technology/WCAG conformance audit.
