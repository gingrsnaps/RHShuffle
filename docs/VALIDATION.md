# Validation — 2026.10.04-redpoints-arcade2

These results are for the current packaging and admin-dashboard revision. Tests
use disposable state, synthetic players and no live provider workers. None of the
fixture balances, usernames, IPs or test admin accounts are production seed data.

| Current check | Result |
| --- | --- |
| Python wallet/API tests | 17 passed in `test_redpoints.py`. |
| Python IP/admin tests | 12 passed in `test_gaming_ip.py`, including seven players per game counted before selecting five. |
| Python Blackjack rules | 8 passed in `test_blackjack.py`. |
| Independent browser verifier | Three tests passed against all 47 legacy and 86 v2 reference receipts, including the 1000× Plinko edge and doubled Blackjack stakes. |
| Admin DOM checks | Three passed: four populated lists, full counts/IPs; expired sessions clear private data and block late responses; release mismatches request reload. |
| Native Chromium admin | Real login, direct `/admin/gaming`, installed-release label, four lists of five players, 28 completed synthetic rounds across seven players. Session-expiry cleanup passed. |
| Native Chromium games | Plinko request, independent verification and exact slot landing; Blackjack hidden hole card, reload/resume, Stand and verified settlement; same player/balance on Dice; actual Dice dragging to 73%; Keno Quick pick 10. |
| Shared public IP | A second browser could not claim a second wallet or read the original player's identity/results. Recovery remains required. |
| Animation observation | Plinko's median frame interval was approximately 16–17 ms in the local browser runs. This is an observation, not a guaranteed frame rate on every device. |
| Browser script errors | None in the exercised routes. |

The complete and cumulative update archives contain byte-identical versions of
every shared file. The full archive includes Blackjack and its imports. Original
private provider settings, account seed and logos are retained unchanged. Runtime
state, caches, test dependencies and generated fixture data are excluded.

The older patch's broader 203 Python / 47 JavaScript checks and its Chromium and
Firefox runs remain historical evidence. They were not all rerun for this
dashboard/distribution revision. The current targeted checks exercise the changed
paths and their wallet/game dependencies. Exact probability tables and independent
reproduction are stronger checks than claiming random trials alone prove fairness.

## Limits

The user's hosted site, DigitalOcean deployment and live Shuffle/Kick responses
were not accessed or changed. The earlier complete archive was missing the newer
gaming changes; this is a verified distribution mismatch, not proof of which files
are currently deployed on the user's server. The visible release marker resolves
that ambiguity after installation.

Rankings are actual current-week settled RedPoints totals. They cannot recover
missing historical records from an erased local save. With the requested JSON-only
storage, App Platform container replacement can erase local files. Restore a saved
private recovery export when moving/deploying the app. No SQL dependency was added.

Tests ran on Linux, not native Windows/Python 3.14. The deployed runtime declaration
is unchanged. These checks are not a penetration test, independent fairness
certification, or a throughput benchmark.

## Repeat targeted checks

Install the normal Python requirements first. The website only needs
`python wager_backend.py`; the commands below are developer checks.

```bash
python -m unittest discover -s tests -p test_redpoints.py -v
python -m unittest discover -s tests -p test_gaming_ip.py -v
python -m unittest discover -s tests -p test_blackjack.py -v
npm --prefix tests install --ignore-scripts
node --test tests/test_fairness_frontend.cjs tests/test_admin_gaming_frontend.cjs
```

The admin DOM test generates synthetic HTML/JSON in a temporary directory and
removes it afterward. Set `RH_TEST_PYTHON` if Python is not available as `python3`.
For the existing full interface suite, run
`python tests/render_fixtures.py .test-fixtures` first, then `npm --prefix tests test`.

Selected screenshots in `docs/` illustrate synthetic UI states. Gaming, Plinko,
Blackjack and private-ranking previews reflect this release; homepage and boss
previews retain the previous release's unchanged designs.
