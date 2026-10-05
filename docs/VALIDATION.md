# Validation — 2026.10.05-redpoints-arcade4

Checks use temporary state, synthetic players, seeds and provider replies. They
do not read the configured private provider keys or place real-money wagers.

| Check | Result |
| --- | --- |
| Full Python suite | **226 passed**, including original race, history, boss, account, upload, recovery and RedPoints behavior. |
| Full JavaScript suite | **74 passed**, using freshly rendered fixtures; includes admin privacy, gameplay controls, shared UI, CSS parsing and browser proof replay. |
| Reference receipts | **396** match the independent Python/JavaScript implementations: 47 v1, 86 v2, 112 v3 and 151 v4. Modified payouts/commitments fail verification. |
| Baccarat rules | Every initial Player/Banker total, every Player third-card value and all three bet sides: **3,000 scenarios**. Naturals, Banker exceptions, distinct physical cards, total calculation, pushes, commissions and whole-point returns checked. |
| Compatibility | Saved v2/v3 Blackjack and v3 Poker hands retain seeds/cards; old proofs remain valid; new statistics start at zero. Failed writes roll back, duplicate bets/actions settle once. |
| Native Chromium | All eight games play and verify; game requests cause **no page navigation**. Keno and Baccarat reveal in sequence. Dice dragging updates its percentage. |
| Animation recovery | Three overlapping Plinko drops finish in the correct slots after resizing. Reduced-motion Baccarat and a simulated hidden-tab event finish at the exact recorded result. No control remains locked. |
| Player continuity | Poker holds survive polls and actual reloads. A lost draw response recovers the saved result once. Reloads restore the requested 100,000 allowance without duplicating a hand. |
| Private rankings | All eight games appear in admin with full names, IP metadata and net winnings. Expired sessions clear private rows. Public responses do not disclose another player's identity or IP. |
| Mobile | Exercised at 390px and 430px; no horizontal document overflow on any game. Original navigation remains visible. |
| Browser errors | None in the native game/registration/admin paths exercised. |
| Package | All 20 root Python modules, current templates/scripts, original private seeds and logo files included. Source hashes and ZIP integrity checked. |

Fresh browser previews are in `GAMING_DESKTOP.png`, `BACCARAT_MOBILE.png`,
`POKER_DESKTOP.png`, `COINFLIP_MOBILE.png` and `LIMBO_MOBILE.png` in this folder.
Other previews are earlier design references. All use synthetic data.

## Repeat checks

The website requires only its five Python dependencies and the single launcher.
The following optional developer commands are separate from deployment:

```bash
python -m unittest discover -s tests -q
python tests/render_fixtures.py .test-fixtures
npm --prefix tests install --ignore-scripts
npm --prefix tests test
```

For native animation checks, install the optional Playwright Chromium browser,
then run `node tests/gaming_motion.cjs`. Set `NODE_PATH=tests/node_modules` if the
module cannot be found. `RH_TEST_PYTHON` selects the Python interpreter;
`RH_CHROMIUM` can select an existing Chromium executable; `RH_SCREENSHOTS`
selects the output directory. The HTTP fixture is disposable and never starts
live provider workers. Fixture data and test dependencies are excluded from the ZIP.

The current suite was run on Linux with Python 3.12 and Chromium. The App Platform
runtime declaration remains Python 3.13.12. The ordinary launcher and UTF-8 reads
have regression checks, but this is not a native Windows/Python 3.14 test.

## Practical limits

The package has not been deployed to the user's service. Shuffle and Kick
availability, historical affiliate access and the hosting account were not tested
live in this revision. Their existing 60-second workers remain intact.

JSON storage and one app instance remain the requested design. App Platform can
erase local state when replacing a container; a prior private recovery export
restores only the data it contains. This release cannot recreate erased records.
There is no new SQL, backup service or other infrastructure to manage.

Animations present saved outcomes; they do not simulate new random results.
Frame rate depends on device/browser load and is not guaranteed. Reproducible
proofs are not third-party certification or proof that a host never changes its
code. Keep the commitment observed before each bet for independent verification.
