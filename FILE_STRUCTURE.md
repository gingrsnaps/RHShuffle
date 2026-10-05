# Complete file structure

Release **2026.10.05-redpoints-arcade4**. The archive extracts one `redhunllef-rebuilt/` folder.
Run only `python wager_backend.py`; all supporting modules load automatically.

| File | Purpose |
| --- | --- |
| `CHANGES.md` | Changes in this release and retained features. |
| `FILE_STRUCTURE.md` | This file inventory. |
| `FULL_CODE_BLOCKS.md` | Complete text files in individual code blocks; binary assets encoded as base64. |
| `MANIFEST.json` | Release, launch command, module list and source-file hashes. |
| `Procfile` | Runs python wager_backend.py. |
| `RAID_UPDATE.md` | Application support file. |
| `README.md` | Complete update, operation, recovery and DigitalOcean instructions. |
| `START_HERE.md` | Short installation and launch instructions. |
| `UPDATE.md` | Full-package merge, preservation and restart instructions. |
| `abuse_guard.py` | Per-browser rejected-request throttles and temporary admin flags. |
| `app.yaml` | Single-service DigitalOcean App Platform template. |
| `baccarat.py` | Fresh eight-deck Punto Banco, automatic draw tableau and exact commissions/returns. |
| `blackjack.py` | Pure six-deck RedPoints Blackjack replay and hand scoring. |
| `boss.py` | Independent signed-browser players, multiplayer rules, recovery and admin controls. |
| `boss_avatar.py` | Image validation, resizing and safe PNG avatar storage. |
| `boss_extras.py` | Cosmetic rally, pace estimates and private boss admin history. |
| `boss_progress.py` | Private names and the unchanged eight achievement calculations. |
| `config.py` | Configuration, original provider keys, save locations and release. |
| `docs/ADMIN_GAMING.png` | Four private leaderboards with synthetic players/IPs. |
| `docs/BACCARAT_MOBILE.png` | Synthetic visual preview. |
| `docs/BLACKJACK_DESKTOP.png` | Verified RedPoints Blackjack hand with synthetic results. |
| `docs/COINFLIP_MOBILE.png` | Synthetic visual preview. |
| `docs/COMMUNITY_BOSS.md` | Current mechanics, permissions, identity and storage behavior. |
| `docs/COMMUNITY_UPDATE.md` | Implementation notes for approved suggestions 2–9. |
| `docs/GAMING_DESKTOP.png` | Native Chromium Gaming dashboard preview with synthetic data. |
| `docs/GAMING_MOBILE.png` | Native Chromium mobile Gaming preview with all configured header links. |
| `docs/LIMBO_MOBILE.png` | Synthetic visual preview. |
| `docs/PLINKO_DESKTOP.png` | Native Chromium Plinko preview with verified synthetic results. |
| `docs/POKER_DESKTOP.png` | Synthetic visual preview. |
| `docs/PREVIEW_DESKTOP.png` | Native Chromium desktop preview with synthetic data. |
| `docs/PREVIEW_MOBILE.png` | Native Chromium mobile preview with synthetic data. |
| `docs/REDPOINTS.md` | All game rules, wallet behavior, byte format and technical references. |
| `docs/VALIDATION.md` | Current measured checks, optional reproduction and practical limits. |
| `fairness.py` | Versioned v1–v4 committed outcomes and exact payout rules for eight games. |
| `gaming.py` | Shared RedPoints wallets, saved card hands, idempotent settlement and private Top 5 records. |
| `integrations.py` | Shuffle and Kick HTTP clients, timeouts and provider errors. |
| `poker.py` | One-deck Video Poker replay and 9/6 Jacks or Better classification. |
| `presentation.py` | Race change previews and existing recovery-export status. |
| `private/admin_store.seed.json` | Original supplied Superadmin/account seed; unchanged. |
| `private/settings.json` | Original supplied private Shuffle/Kick configuration; unchanged. |
| `race.py` | Leaderboard calculations, qualification, ranking and freshness. |
| `race_support.py` | Shared timezone, amount, configuration and file helpers. |
| `requirements.txt` | The existing five Python runtime dependencies; no SQL driver. |
| `runtime.py` | Independent automatic 60-second Shuffle/Kick workers and published snapshots. |
| `runtime.txt` | Python runtime declaration. |
| `static/admin-feedback.js` | Inline save failures, draft preservation and confirmed-write navigation. |
| `static/admin-gaming.js` | Private five-second rankings, actual counts, IP details and session-expiry cleanup. |
| `static/app.js` | Public/admin race interface, game Top 5 updates, history diagnostics and refresh controls. |
| `static/boss-preview.js` | Admin draft homepage name/avatar preview using current confirmed HP. |
| `static/boss.css` | Responsive arena, game controls and boss admin styling. |
| `static/boss.js` | Game/admin interface, recovery UI, previews and automatic polls. |
| `static/fairness.js` | Independent Web Crypto/BigInt verifier, including Baccarat and all older proofs. |
| `static/gaming.css` | Responsive red arcade, compact controls, cards and reduced-motion styling. |
| `static/gaming.js` | Background gameplay requests, verified animation sequences, recovery and shared balances. |
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
| `templates/gaming.html` | Eight-game dashboard and simple game pages with expandable details. |
| `templates/gaming_fairness.html` | Complete published rules, commitment protocol and local receipt verifier. |
| `templates/history.html` | Rendered page or shared template. |
| `templates/icons.html` | Rendered page or shared template. |
| `templates/index.html` | Rendered page or shared template. |
| `templates/login.html` | Rendered page or shared template. |
| `templates/macros.html` | Rendered page or shared template. |
| `templates/recovery_panel.html` | Rendered page or shared template. |
| `tests/assert_visual_pixels.py` | Developer test/fixture support; not needed to launch the website. |
| `tests/fairness_v2_vectors.json` | 86 synthetic version-two receipt fixtures. |
| `tests/fairness_v3_vectors.json` | Optional developer test/fixture; not needed to launch the website. |
| `tests/fairness_v4_vectors.json` | 151 independently checked v4 receipts, including all Baccarat bet/outcome combinations. |
| `tests/fairness_vectors.json` | Developer test/fixture support; not needed to launch the website. |
| `tests/gaming_motion.cjs` | Optional native Chromium game, animation, recovery, mobile and admin checks. |
| `tests/generate_fairness_vectors.py` | Developer test/fixture support; not needed to launch the website. |
| `tests/generate_v4_vectors.py` | Rebuilds v4 synthetic proof vectors without changing older references. |
| `tests/package.json` | Developer test/fixture support; not needed to launch the website. |
| `tests/render_fixtures.py` | Developer test/fixture support; not needed to launch the website. |
| `tests/serve_admin_gaming_fixture.py` | Eight-game fixture for private ranking DOM checks. |
| `tests/serve_game_fixture.py` | Temporary local HTTP test fixture, never starts provider jobs. |
| `tests/serve_gaming_motion_fixture.py` | Disposable native-browser HTTP fixture; no providers or private configuration. |
| `tests/serve_gui_fixture.py` | Developer test/fixture support; not needed to launch the website. |
| `tests/test_admin_controls.py` | Developer test/fixture support; not needed to launch the website. |
| `tests/test_admin_gaming_frontend.cjs` | Private rankings rendering, release mismatch and expired-session checks. |
| `tests/test_app.py` | Developer test/fixture support; not needed to launch the website. |
| `tests/test_baccarat.py` | Exhaustive tableau boundaries, three bets, accounting and v3 hand migrations. |
| `tests/test_blackjack.py` | Deterministic Blackjack rules and payout checks. |
| `tests/test_boss.py` | Developer test/fixture support; not needed to launch the website. |
| `tests/test_boss_admin.py` | Developer test/fixture support; not needed to launch the website. |
| `tests/test_boss_frontend.cjs` | Developer test/fixture support; not needed to launch the website. |
| `tests/test_comfort_update.py` | Developer test/fixture support; not needed to launch the website. |
| `tests/test_community.py` | Developer test/fixture support; not needed to launch the website. |
| `tests/test_extra_games.py` | Optional developer test/fixture; not needed to launch the website. |
| `tests/test_fairness_frontend.cjs` | Developer test/fixture support; not needed to launch the website. |
| `tests/test_frontend.cjs` | Developer test/fixture support; not needed to launch the website. |
| `tests/test_gaming_ip.py` | IP binding, private rankings and actual total counts. |
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

The app creates `data/state.json`, its lock and bounded local recovery copies automatically. Runtime saves, caches, test dependencies and generated fixture data are excluded. Preserve current data and private configuration when updating. No SQL or additional service is required.
