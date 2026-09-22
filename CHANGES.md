# Changes — 2026.09.22-boss

Community game: add `/play` with a shared boss, signed guest profiles, atomic
attacks, one-minute cooldowns, 40-hit raid-day allowances, rotating weaknesses,
and every-tenth-hit Crimson burst. The default 2.4-million-HP encounter targets
4–8 days for 100 active raiders. Victory is retained until a host starts again.

Game presentation: animated red arena with the original logo, readable health,
weapon buttons, personal burst meter, Top 10 contributors, recent attacks,
past raids, and visible instructions. Add the homepage Join the boss fight CTA
and header link. Remove the public Admin footer link and dashboard site footer.

Host tools: a Community boss tab updates every five seconds and preserves input
drafts. Superadmin pause/resume/restart actions use CSRF and a current-raid guard.
Private recovery export/import now includes boss progress and hashed cooldown
records. Race-only backups remain separate. No extra production dependency.

DigitalOcean: use the documented DO-Connecting-IP visitor header when trusted
App Platform ingress is enabled; ignore it on direct hosts. This also improves
existing login rate limiting and IP access controls behind that ingress.

Verification: 75 Python tests pass; 4 optional PostgreSQL tests skip. All 28
DOM/CSS checks pass. Two real browser contexts see shared damage and host pause
changes. A 100-player simulation finishes on raid day four at maximum matching
attacks. Existing race publication, refresh, recovery, and Code Red checks pass.

Previous local-storage release: remove the production PostgreSQL startup requirement. Default to built-in SQLite, ignore stale DATABASE_URL values in local mode, and remove the PostgreSQL driver from normal requirements. App Platform configuration contains only the Python web service. Production cookies and proxy handling remain independent of storage.

Recovery: add a Superadmin-only private account/race export and automatic import from private/recovery.seed.json on a fresh instance. Existing saved state takes priority. The dashboard, logs, and README explicitly explain that App Platform local files do not persist through redeploys or container replacements; checkpoints are manual.


Date publication: the bottom button now submits the required confirmation and clearly says **Confirm and publish race**. Drafts no longer look like completed saves.

Refresh reliability: discard old-setting failure responses as well as successes; clear only obsolete ordinary backoff when dates change; retain provider rate limits. Keep one follow-up request when Refresh is pressed during an active check. Restart stopped workers from dashboard status reads.

Progress: every admin tab shows published dates and separate provider outcomes. Manual requests have completion tickets; date publication triggers short follow-up polling automatically. An in-flight browser read no longer drops an immediate refresh request.

Visuals: logo-red branding, burgundy surfaces, red buttons and active tabs, and readable progress panels. Original logo files are unchanged. No production dependency was added.

Earlier verification: 57 Python tests and 20 DOM/CSS checks passed. A local HTTP fixture exercises date changes during a failed request and subsequent automatic publication; external Shuffle/Kick connectivity remains unverified here.

Refresh patch: read the real form action attribute to avoid the hidden action input overriding the request URL. Fetch errors retain JSON and HTTP status; empty leaderboards explain waiting, source failure, and nonqualifying results. Regression tests cover the URL collision and manual-refresh publication to both boards. Accounts, credentials, and saved dates are retained.

UTF-8 patch: startup asset reads now explicitly use UTF-8, fixing the exact Windows CP1252 decoding failure. Account state is untouched. A regression test recreates the original failure and verifies startup with existing accounts; test fixture/log encoding is explicit too.

The underlying rebuild replaces the previous launcher, web handlers, update scheduler,
provider clients, templates, and browser controller. It retains the original
configuration, account seed, logo files, race meaning, weighting, and prizes.

| Area | Result |
| --- | --- |
| Launch | `python wager_backend.py` starts Waitress and both provider jobs. |
| Admin rendering | Complete HTML dashboard; scoped status updates cannot erase a form or page. |
| Update timing | Automatic independent 60-second jobs and page polling; bounded manual polling. |
| Persistence | Separate transactional admin and live records, local SQLite or hosted PostgreSQL. |
| Migration | Existing data wins; legacy files/table untouched; private recovery checkpoint. |
| Account setup | Original Superadmin imported automatically; no management command. |
| Public UI | Compact podium, Top 15 table, clear race phase/countdown, source freshness. |
| Admin UI | Overview, Race, Players, Settings; collapsible first 100 confirmed Code Red users. |
| Provider errors | Retain previous values, identify the failing source, retry automatically. |
| Code | Small focused Python modules, shared validation, native JS/CSS, comments at key boundaries. |
| Delivery | Full source, configured ZIP, updated Linux/App Platform instructions, tests and CI. |

The original files contain different schedules: the saved admin race is
August 4–11, while settings defaults are August 18–25 (2026, 6 PM Eastern).
Saved state takes precedence. This is documented and remains an explicit admin
choice rather than an automatic change to historical race data.

Legacy payout workflow and optional live-feed switches remain absent. The app
is always live, with stale-cache preservation only during provider failures.
