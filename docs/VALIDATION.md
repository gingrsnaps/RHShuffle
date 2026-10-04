# Validation — 2026.10.04-redpoints

## Results

| Check | Result |
| --- | --- |
| Complete backend regression suite | **182 tests passed**, Python 3.12/Linux, including original race/admin/boss coverage and new Gaming/history/preview tests. |
| DOM and actual-HTTP interface suite | **70 checks passed** with Node, jsdom and a disposable Waitress server. |
| Independent fairness implementation | **47 synthetic reference receipts** match in Python and browser JavaScript; tampered returns and wrong commitments fail verification. |
| Native Chromium | All three real wager flows, shared balances, duplicate request handling, reload persistence, admin rankings and local receipt verification passed. |
| Responsive layouts | 1440 px desktop, 390 px mobile and 320 px narrow layout checks passed. All seven configured public header links are visible on mobile. |
| HP-bar pixels | Actual red fill verified at 100%, 75%, 25% and 0% remaining on desktop/mobile; defeated text moves oppositely. |
| Screenshots | 20 captured screens across home, history, Gaming, all three games and admin. Selected previews are included in docs. |

## New backend coverage

- One allowance shared across Dice, Keno and Plinko; no refill on refresh, name
  edits, recovery or a restart with the same state file.
- Exact Tuesday 6 PM Eastern rollover, including a 169-hour autumn DST week;
  weekly counters reset while nonces and saved proof receipts remain continuous.
- Five concurrent submissions of the same wager commit only once. Duplicate
  responses preserve the original receipt and do not debit again. Stale nonces
  cannot spend a commitment already used by another tab.
- Whole-point input validation, configured wager bounds, altered commitments and
  nonce rejection, player CSRF isolation and private seed suppression.
- Disk-write failure rolls back balance, seed, nonce and receipt together.
- Private Top 5 limits and descending net-winnings order for each game; unrelated
  public pages never contain those full submitted names.
- Full recovery retains wallet, seed, nonce, receipt and signed player identity;
  inconsistent balances are rejected instead of silently imported.
- 100 independent Gaming profiles receive separate allowances. Existing boss
  tests additionally register/attack concurrently through the same proxy.
- ETag 304 wallet polling and a changed ETag after settlement. Idle polls do not
  mark recovery stale, but a saved wager does.
- Probability tables cover every Keno pick count and Plinko row/risk setting;
  exact expected table return is bounded and Plinko payouts are symmetric.
- One failed completed date range does not starve the other three. Shared access
  failures defer all weeks visibly, without issuing four rejected requests.
- Exact saved race snapshots are rescued as masked provisional places while the
  provider is unavailable. They are not relabeled as final standings.
- Admin history refresh requires current authentication and CSRF, queues work,
  never calls the provider inside the web request, and honors retry times.
- Latest-hit names are masked in the homepage summary; health edits are described
  without exposing admin identity. Native preview checks exercise local name/avatar
  drafts without submitting them.

## Retained coverage

The existing suite exercises the sole launcher through real HTTP; native admin
login and dashboard tabs; races, date previews/publication, manual source refresh,
weighted wagers, Code Red Top 100, masking, CSV, overrides, accounts and passwords;
recovery, admin-only image uploads and boss edits; unlimited hits, 30-second
cooldowns, no regeneration, random weakness and eight badges; stale-response
rejection, signed profile recovery, saved usernames, per-browser throttles,
multiple players behind one proxy, UTF-8 startup, JSON transactions and legacy
read-only import. Rejected saves retain drafts and do not report false success.

Admin requests retain session/role checks, stale revisions and CSRF requirements.
The native browser saves boss settings, verifies a confirmed receipt, then sends
a stale form and confirms the typed draft remains. Gaming's full-name tables are
inspected after actual local wager submissions.

## Evidence and limits

Tests run against temporary local saves and synthetic provider responses. They
never reset deployed data or submit real Shuffle wagers. The 47 published seed
vectors are intentionally public synthetic values, not active player seeds.
There is no statistical claim that 47 examples alone prove all random outcomes;
exact probability/formula checks and independent implementations provide the
separate algorithm checks.

**The live Shuffle historical requests from this workspace timed out, without an
HTTP status.** The code fixes a reproduced queue-starvation bug and verifies
successful backfill/failure handling using controlled provider responses. It does
not claim that the live account returned four completed weeks. No Kick live check
or DigitalOcean deployment was performed for this update. Use the new authenticated
history diagnostics after deployment to identify remaining upstream failures.

These checks are not a throughput benchmark, penetration test or independent
fairness certification. The Linux test environment did not run Windows/Python 3.14
natively; the earlier encoding failure is covered by a simulated default-encoding
test. The declared hosted runtime remains Python 3.13.12.

The original private settings, original account seed, PNG and ICO are compared
byte for byte during packaging. The existing badge calculation function is also
compared with the prior version. The ZIP includes every local import and excludes
runtime state, test fixtures, caches and test dependencies. The exact extracted
package receives a separate startup/import/recovery/Gaming smoke check before
release; its results are recorded in the package manifest.

The previews use synthetic player names, points, dates, health and provider data.
They illustrate the shipped interface, not a live-account result. On App Platform,
local-only files remain ephemeral; the recovery export is a manual checkpoint,
not a promise of uninterrupted persistence during container replacement.

## Repeat locally (developer checks only)

```bash
python -m unittest discover -s tests -v
python tests/render_fixtures.py .test-fixtures
npm --prefix tests install --ignore-scripts
npm --prefix tests test
```

Native browser checks:

```bash
npm --prefix tests exec -- playwright install chromium
npm --prefix tests run test:visual
```

Set `RH_TEST_PYTHON` or `RH_BROWSER_EXECUTABLE` only if the tools are installed at
nondefault paths. The website itself requires no Node/Chromium setup. Its only
run command is `python wager_backend.py`.
