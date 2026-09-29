# Complete file structure

Release **2026.09.29-username-save**. The archive extracts one `redhunllef-rebuilt/` folder.
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
| `abuse_guard.py` | Per-browser rejected-request throttles and temporary admin flags. |
| `app.yaml` | Single-service DigitalOcean App Platform template. |
| `boss.py` | Independent signed-browser players, multiplayer rules, recovery and admin controls. |
| `boss_avatar.py` | Image validation, resizing and safe PNG avatar storage. |
| `boss_extras.py` | Cosmetic rally, pace estimates and private boss admin history. |
| `boss_progress.py` | Private names and the unchanged eight achievement calculations. |
| `config.py` | Configuration, original provider keys, save locations and release. |
| `docs/COMMUNITY_BOSS.md` | Current mechanics, permissions, identity and storage behavior. |
| `docs/COMMUNITY_UPDATE.md` | Implementation notes for approved suggestions 2–9. |
| `docs/VALIDATION.md` | Test scope, results and limits. |
| `integrations.py` | Shuffle and Kick HTTP clients, timeouts and provider errors. |
| `presentation.py` | Race change previews and existing recovery-export status. |
| `private/admin_store.seed.json` | Original supplied Superadmin/account seed; unchanged. |
| `private/settings.json` | Original supplied private Shuffle/Kick configuration; unchanged. |
| `race.py` | Leaderboard calculations, qualification, ranking and freshness. |
| `race_support.py` | Shared timezone, amount, configuration and file helpers. |
| `requirements.txt` | The existing five Python runtime dependencies; no SQL driver. |
| `runtime.py` | Independent automatic 60-second Shuffle/Kick workers and published snapshots. |
| `runtime.txt` | Python runtime declaration. |
| `static/app.js` | Public/admin race interface and source refresh controls. |
| `static/boss.css` | Responsive arena, game controls and boss admin styling. |
| `static/boss.js` | Game/admin interface, recovery UI, previews and automatic polls. |
| `static/redlogo.ico` | Original favicon; unchanged. |
| `static/redlogo.png` | Original PNG logo; unchanged. |
| `static/style.css` | Shared responsive red website/admin styling. |
| `storage.py` | Atomic UTF-8 JSON saves and read-only import of the previous local save. |
| `store_schema.py` | Account/settings migrations and private recovery validation. |
| `templates/admin.html` | Rendered page or shared template. |
| `templates/admin_boss.html` | Rendered page or shared template. |
| `templates/admin_overview.html` | Rendered page or shared template. |
| `templates/admin_players.html` | Rendered page or shared template. |
| `templates/admin_race.html` | Rendered page or shared template. |
| `templates/admin_settings.html` | Rendered page or shared template. |
| `templates/base.html` | Rendered page or shared template. |
| `templates/boss.html` | Rendered page or shared template. |
| `templates/change_review.html` | Rendered page or shared template. |
| `templates/error.html` | Rendered page or shared template. |
| `templates/icons.html` | Rendered page or shared template. |
| `templates/index.html` | Rendered page or shared template. |
| `templates/login.html` | Rendered page or shared template. |
| `templates/macros.html` | Rendered page or shared template. |
| `templates/recovery_panel.html` | Rendered page or shared template. |
| `tests/package.json` | Developer test/fixture support; not needed to launch the website. |
| `tests/render_fixtures.py` | Developer test/fixture support; not needed to launch the website. |
| `tests/serve_game_fixture.py` | Temporary local HTTP test fixture, never starts provider jobs. |
| `tests/test_app.py` | Developer test/fixture support; not needed to launch the website. |
| `tests/test_boss.py` | Developer test/fixture support; not needed to launch the website. |
| `tests/test_boss_admin.py` | Developer test/fixture support; not needed to launch the website. |
| `tests/test_boss_frontend.cjs` | Developer test/fixture support; not needed to launch the website. |
| `tests/test_comfort_update.py` | Developer test/fixture support; not needed to launch the website. |
| `tests/test_community.py` | Developer test/fixture support; not needed to launch the website. |
| `tests/test_frontend.cjs` | Developer test/fixture support; not needed to launch the website. |
| `tests/test_player_access.py` | 100-player shared-proxy access, stable usernames, recovery and request isolation. |
| `tests/test_raid_update.py` | Developer test/fixture support; not needed to launch the website. |
| `tests/test_username_http.cjs` | Both shipped scripts against real HTTP and a cookie jar; no mocked username save. |
| `tests/test_username_save.py` | Native saves, expired page sessions, browser ownership, recovery, and admin isolation. |
| `wager_backend.py` | Only launch script; web routes, authentication and Waitress startup. |

The app creates `data/state.json`, its lock file and bounded local recovery copies automatically. Runtime data, test fixtures and caches are excluded from this ZIP. Preserve your current data and private configuration when merging an update.

Removed: the optional PostgreSQL dependency file and PostgreSQL tests. No external database/backup service is required.
