# Complete file structure

Release **2026.10.04-redpoints-arcade3-seven-games**. This describes the full application. The update ZIP uses paths relative to your existing project root; it contains changed/new files only.
Run only `python wager_backend.py`; all support modules are imported automatically.

| File | Purpose |
| --- | --- |
| `CHANGES.md` | Changes in this release and retained features. |
| `FILE_STRUCTURE.md` | This file inventory. |
| `FULL_CODE_BLOCKS.md` | Every text file in its own full code block; original logos as base64. |
| `MANIFEST.json` | Release, launch command, module list and source-file hashes. |
| `Procfile` | Runs python wager_backend.py. |
| `README.md` | Complete update, operation, recovery and DigitalOcean instructions. |
| `START_HERE.md` | Short installation and launch instructions. |
| `UPDATE.md` | Cumulative gaming patch instructions and verification. |
| `abuse_guard.py` | Per-browser rejected-request throttles and temporary admin flags. |
| `app.yaml` | Single-service DigitalOcean App Platform template. |
| `poker.py` | Five-card draw engine and Jacks or Better paytable; imported by the main launcher. |
| `blackjack.py` | Pure six-deck RedPoints Blackjack replay and hand scoring. |
| `boss.py` | Independent signed-browser players, multiplayer rules, recovery and admin controls. |
| `boss_avatar.py` | Image validation, resizing and safe PNG avatar storage. |
| `boss_extras.py` | Cosmetic rally, pace estimates and private boss admin history. |
| `boss_progress.py` | Private names and the unchanged eight achievement calculations. |
| `config.py` | Configuration, original provider keys, save locations and release. |
| `docs/COMMUNITY_BOSS.md` | Current mechanics, permissions, identity and storage behavior. |
| `docs/COMMUNITY_UPDATE.md` | Implementation notes for approved suggestions 2–9. |
| `docs/ADMIN_GAMING.png` | Four private leaderboards with synthetic players/IPs. |
| `docs/BLACKJACK_DESKTOP.png` | Verified RedPoints Blackjack hand with synthetic results. |
| `docs/GAMING_DESKTOP.png` | Native Chromium Gaming dashboard preview with synthetic data. |
| `docs/GAMING_MOBILE.png` | Native Chromium mobile Gaming preview with all configured header links. |
| `docs/PLINKO_DESKTOP.png` | Native Chromium Plinko preview with verified synthetic results. |
| `docs/PREVIEW_DESKTOP.png` | Native Chromium desktop preview with synthetic data. |
| `docs/PREVIEW_MOBILE.png` | Native Chromium mobile preview with synthetic data. |
| `docs/REDPOINTS.md` | Complete game rules, fairness specification, exact payouts and storage limits. |
| `docs/VALIDATION.md` | Test scope, results and limits. |
| `fairness.py` | Pure deterministic game outcomes, exact payout math and offline verification. |
| `gaming.py` | Atomic shared RedPoints wallets, weekly resets, receipts and private per-game Top 5. |
| `integrations.py` | Shuffle and Kick HTTP clients, timeouts and provider errors. |
| `presentation.py` | Race change previews and existing recovery-export status. |
| `private/admin_store.seed.json` | Original supplied Superadmin/account seed; unchanged. |
| `private/settings.json` | Original supplied private Shuffle/Kick configuration; unchanged. |
| `race.py` | Leaderboard calculations, qualification, ranking and freshness. |
| `race_support.py` | Shared timezone, amount, configuration and file helpers. |
| `requirements.txt` | The existing five Python runtime dependencies; no SQL driver. |
| `runtime.py` | Independent automatic 60-second Shuffle/Kick workers and published snapshots. |
| `runtime.txt` | Python runtime declaration. |
| `static/admin-feedback.js` | Inline save failures, draft preservation and confirmed-write navigation. |
| `static/app.js` | Public/admin race interface, game Top 5 updates, history diagnostics and refresh controls. |
| `static/boss-preview.js` | Admin draft homepage name/avatar preview using current confirmed HP. |
| `static/boss.css` | Responsive arena, game controls and boss admin styling. |
| `static/boss.js` | Game/admin interface, recovery UI, previews and automatic polls. |
| `static/fairness.js` | Independent browser HMAC/rejection sampling, payout math and receipt verification. |
| `static/admin-gaming.js` | Private five-second rankings, actual counts, IP details and session-expiry cleanup. |
| `static/gaming.css` | Responsive red Gaming dashboard, Dice/Keno/Plinko/Blackjack boards and controls. |
| `static/gaming.js` | Game controls, conditional wallet polls, safe settlement and local receipt checks. |
| `static/history.css` | Responsive red completed-week cards and table. |
| `static/history.js` | Automatic cached-history reads, native week navigation and safe rendering. |
| `static/homepage.js` | Five-second boss reads, last-confirmed age, host-edit notice and masked latest hit. |
| `static/receipt-verifier.js` | Local-only pasted receipt verification; never sends the receipt to a server. |
| `static/redlogo.ico` | Original favicon; unchanged. |
| `static/redlogo.png` | Original PNG logo; unchanged. |
| `static/style.css` | Shared responsive red website/admin styling. |
| `storage.py` | Atomic UTF-8 JSON saves and read-only import of the previous local save. |
| `store_schema.py` | Account/settings migrations and private recovery validation. |
| `templates/admin.html` | Rendered page or shared template. |
| `templates/admin_boss.html` | Rendered page or shared template. |
| `templates/admin_gaming.html` | Rendered page or shared template. |
| `templates/admin_overview.html` | Rendered page or shared template. |
| `templates/admin_players.html` | Rendered page or shared template. |
| `templates/admin_race.html` | Rendered page or shared template. |
| `templates/admin_settings.html` | Rendered page or shared template. |
| `templates/base.html` | Rendered page or shared template. |
| `templates/boss.html` | Rendered page or shared template. |
| `templates/change_review.html` | Rendered page or shared template. |
| `templates/error.html` | Rendered page or shared template. |
| `templates/gaming.html` | Rendered page or shared template. |
| `templates/gaming_fairness.html` | Rendered page or shared template. |
| `templates/history.html` | Rendered page or shared template. |
| `templates/icons.html` | Rendered page or shared template. |
| `templates/index.html` | Rendered page or shared template. |
| `templates/login.html` | Rendered page or shared template. |
| `templates/macros.html` | Rendered page or shared template. |
| `templates/recovery_panel.html` | Rendered page or shared template. |
| `tests/assert_visual_pixels.py` | Developer test/fixture support; not needed to launch the website. |
| `tests/fairness_vectors.json` | Developer test/fixture support; not needed to launch the website. |
| `tests/generate_fairness_vectors.py` | Developer test/fixture support; not needed to launch the website. |
| `tests/fairness_v2_vectors.json` | 86 synthetic version-two receipt fixtures. |
| `tests/test_blackjack.py` | Deterministic Blackjack rules and payout checks. |
| `tests/test_gaming_ip.py` | IP binding, private rankings and actual total counts. |
| `tests/test_admin_gaming_frontend.cjs` | Private rankings rendering, release mismatch and expired-session checks. |
| `tests/serve_admin_gaming_fixture.py` | Disposable seven-game fixture for native browser or DOM checks. |
| `tests/package.json` | Developer test/fixture support; not needed to launch the website. |
| `tests/render_fixtures.py` | Developer test/fixture support; not needed to launch the website. |
| `tests/serve_game_fixture.py` | Temporary local HTTP test fixture, never starts provider jobs. |
| `tests/serve_gui_fixture.py` | Developer test/fixture support; not needed to launch the website. |
| `tests/test_admin_controls.py` | Developer test/fixture support; not needed to launch the website. |
| `tests/test_app.py` | Developer test/fixture support; not needed to launch the website. |
| `tests/test_boss.py` | Developer test/fixture support; not needed to launch the website. |
| `tests/test_boss_admin.py` | Developer test/fixture support; not needed to launch the website. |
| `tests/test_boss_frontend.cjs` | Developer test/fixture support; not needed to launch the website. |
| `tests/test_comfort_update.py` | Developer test/fixture support; not needed to launch the website. |
| `tests/test_community.py` | Developer test/fixture support; not needed to launch the website. |
| `tests/test_fairness_frontend.cjs` | Developer test/fixture support; not needed to launch the website. |
| `tests/test_frontend.cjs` | Developer test/fixture support; not needed to launch the website. |
| `tests/test_gui_update.py` | Developer test/fixture support; not needed to launch the website. |
| `tests/test_history_frontend.cjs` | Developer test/fixture support; not needed to launch the website. |
| `tests/test_homepage_frontend.cjs` | Developer test/fixture support; not needed to launch the website. |
| `tests/test_player_access.py` | 100-player shared-proxy access, stable usernames, recovery and request isolation. |
| `tests/test_raid_update.py` | Developer test/fixture support; not needed to launch the website. |
| `tests/test_redpoints.py` | Developer test/fixture support; not needed to launch the website. |
| `tests/test_username_http.cjs` | Both shipped scripts against real HTTP and a cookie jar; no mocked username save. |
| `tests/test_username_save.py` | Native saves, expired page sessions, browser ownership, recovery, and admin isolation. |
| `tests/test_weekly_history.py` | Developer test/fixture support; not needed to launch the website. |
| `tests/visual_checks.cjs` | Developer test/fixture support; not needed to launch the website. |
| `tools/verify_redpoints.py` | Optional offline receipt audit utility, not a web-server launcher. |
| `wager_backend.py` | Only launch script; web routes, authentication and Waitress startup. |
| `weekly_history.py` | Four completed Tuesday 6 PM Eastern weeks, masked Top 25, snapshot rescue and independent retries. |

The app creates `data/state.json`, its lock file and bounded local recovery copies automatically. Runtime data, test fixtures and caches are excluded from this ZIP. Preserve your current data and private configuration when merging an update.

Removed: the optional PostgreSQL dependency file and PostgreSQL tests. No external database/backup service is required.


## Seven-game update

- `poker.py` — standard-deck draw and Jacks or Better classification/paytable.
  Imported automatically by the single `wager_backend.py` launcher.
- `fairness.py` — versioned v1/v2/v3 outcomes for seven RedPoints games.
- `gaming.py` — shared wallets, reserved Blackjack/Poker hands, receipts and rankings.
- `static/fairness.js` — independent browser verification of all three versions.
- `templates/gaming.html`, `static/gaming.js`, `static/gaming.css` — seven game pages
  and dashboard, including Limbo, Coinflip and Poker.
- `tests/test_extra_games.py` and `tests/fairness_v3_vectors.json` — new rule,
  accounting, migration and cross-language verification cases.

The update ZIP contains changed/new files only. Retain the other application
files and both `data/` and `private/` from your existing installation.
