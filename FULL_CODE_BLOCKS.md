# RedHunllef — complete configured code

Release **2026.09.29-player-access**. Every file below is a full text block. The ZIP contains ready-to-use files. Original logos are encoded as base64 here and are included as image files in the ZIP. This configured package includes private credentials/account seed data; keep it private.

Run only `python wager_backend.py`. Keep all supporting files together and preserve existing `data/` and private configuration when updating. The eight achievements are unchanged; hits remain unlimited per day/week with a 30-second cooldown. No external SQL or backup service is required.

## .env.example

```text
# Reference for App Platform environment settings. The app does not load .env.
APP_ENV=production
PORT=8080
TRUST_APP_PLATFORM=1
SESSION_COOKIE_SECURE=always
APP_STATE_KEY=redhunllef
# Saves use data/state.json automatically. No database variables are needed.
# Supplied credentials already load from private/settings.json.
# Nonempty runtime environment values take precedence if you need to replace them:
# SHUFFLE_API_KEY=
# KICK_CLIENT_ID=
# KICK_CLIENT_SECRET=
# Optional, stable secret (32+ characters); otherwise the saved store supplies it:
# SECRET_KEY=
# For a local check, use APP_ENV=local,
# TRUST_APP_PLATFORM=0, and SESSION_COOKIE_SECURE=auto.
```

## .github/workflows/test.yml

```yaml
name: Application checks
on: [push, pull_request, workflow_dispatch]
permissions:
  contents: read
jobs:
  tests:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with:
          python-version: '3.13'
      - run: python -m pip install -r requirements.txt
      - run: python -m unittest discover -s tests -v
      - uses: actions/setup-node@v4
        with:
          node-version: '22'
      - run: npm --prefix tests install --ignore-scripts
      - run: python tests/render_fixtures.py .test-fixtures
      - run: npm --prefix tests test
```

## .gitignore

```text
__pycache__/
*.pyc
.venv/
node_modules/
data/
recovery/
admin_store.json
settings.json
integrations.json
.env
.test-fixtures/
```

## CHANGES.md

```markdown
# Changes — 2026.09.29-player-access

## Fixed community access and username persistence

- Removed shared-IP registration limits and shared-IP attack cooldowns. Reproduced
  98 of 100 players blocked behind two IPs before the fix.
- Saved names and cooldowns follow the existing signed browser identity. IP changes
  no longer make a saved profile appear unregistered.
- Registration, recovery and attacks work without a proxy visitor-IP header.
  Arbitrary forwarding headers are still not trusted as verified identities.
- Rejected-request throttling belongs to a browser instead of a whole network.
- A confirmed name save wins over older polls and earlier request timestamps.
- Retired household-approval and connection-release UI; no approvals or raid reset
  are needed. Old submitted admin forms return a clear retired-control message.
- Kept every original account/configuration/logo, raid, player key, recovery code,
  contribution, achievement, avatar, combat setting and admin permission.
- Added concurrent 100-player shared-proxy tests and persistence/race regressions.

Hits stay unlimited per day/week, with one attack per player every 30 seconds.
The only launch command remains `python wager_backend.py`; JSON storage needs no
SQL service or extra setup. Existing local saves must be preserved when updating.

## Previous release — 2026.09.28-community-polish

Implemented suggestions 2–9. Excluded the achievement-display change (#1) and
external checkpoints (#10). No daily/weekly hit limits, new dependency, service,
management command or second launcher was added.

## Player experience

- Saved “Playing as…” summary with Edit; a private, downloadable recovery code.
- Recovery preserves identity, raid damage, badges and the last attack receipt.
- Admin-approved household allowances; 30-second server cooldown per approved player.
- Fifteen-player Red rally: rolling ten-minute participation, cosmetic arena unlock.
- Remembered style, compact totals with exact detail, stable attack buttons,
  consistent configured boss names and a live last-checked label.

## Administration

- Recent pace and estimates, plus next-raid HP presets. Never automatic HP scaling.
- Live health/damage previews and a bounded, persistent history of boss edits.
- Shared connection controls and private request activity flags.
- Separate source check and content-change times; automatic 60-second checks retained.
- All boss mutation endpoints remain authenticated and CSRF-protected.

## Runtime

- Replaced active SQLite/PostgreSQL storage with atomic UTF-8 JSON.
- Imports a previous local SQLite save once, read-only, and leaves it untouched.
- Preserves existing accounts, hashes, secrets, current progress and images.
- Caches committed files while detecting writes from another local process.
- Rejected-request throttles never block an otherwise eligible 30-second attack.
- Removed the optional PostgreSQL dependency file, its tests and CI service.
- Existing manual recovery remains. No remote checkpoint integration was added.

## Retained

Original Shuffle/Kick configuration, Superadmin seed, logos, race date publication,
automatic provider jobs, public masking, uncensored admin Code Red Top 100,
uncensored boss Top 5, admin image uploads, HP/damage editing, random weakness,
mouse/keyboard re-arm, no automatic HP regeneration, unlimited hits and eight badges.

See README for local-file lifetime on DigitalOcean App Platform.
```

## FILE_STRUCTURE.md

```markdown
# Complete file structure

Release **2026.09.29-player-access**. The archive extracts one `redhunllef-rebuilt/` folder.
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
| `tests/test_app.py` | Developer test/fixture support; not needed to launch the website. |
| `tests/test_boss.py` | Developer test/fixture support; not needed to launch the website. |
| `tests/test_boss_admin.py` | Developer test/fixture support; not needed to launch the website. |
| `tests/test_boss_frontend.cjs` | Developer test/fixture support; not needed to launch the website. |
| `tests/test_comfort_update.py` | Developer test/fixture support; not needed to launch the website. |
| `tests/test_community.py` | Developer test/fixture support; not needed to launch the website. |
| `tests/test_frontend.cjs` | Developer test/fixture support; not needed to launch the website. |
| `tests/test_player_access.py` | 100-player shared-proxy access, stable usernames, recovery and request isolation. |
| `tests/test_raid_update.py` | Developer test/fixture support; not needed to launch the website. |
| `wager_backend.py` | Only launch script; web routes, authentication and Waitress startup. |

The app creates `data/state.json`, its lock file and bounded local recovery copies automatically. Runtime data, test fixtures and caches are excluded from this ZIP. Preserve your current data and private configuration when merging an update.

Removed: the optional PostgreSQL dependency file and PostgreSQL tests. No external database/backup service is required.
```

## Procfile

```text
web: python wager_backend.py
```

## README.md

````markdown
# RedHunllef

Release **2026.09.29-player-access**. This is the complete configured application.
Run **`python wager_backend.py`**. All supporting modules load automatically.
There is no database server, SQL setup, extra worker, scheduler or account-creation
command. The app saves its state to `data/state.json` automatically.

## Boss access repair

The earlier version reserved one player per visible IP and checked that a saved
profile still used that IP. A shared proxy could make the whole community look
like one or two players. A changing mobile/VPN/proxy address made an existing
username appear unsaved. Reproduction: 100 browsers behind two IPs admitted only
two players before this repair.

Player admission, username ownership and the 30-second cooldown now follow the
**signed browser cookie**, independently of network addresses. Shared connections
need no approval. A missing or changing proxy IP header cannot disable gameplay.
Rejected-request throttles are isolated per browser, so one client's mistakes do
not lock other players out. Delayed polls cannot undo a confirmed username save.

**No raid reset, cookie clearing or data deletion is needed.** Existing profile
keys, names, recovery codes, badges, health, damage and administrator accounts are
retained. Use the same browser; if its cookie was previously lost, use your saved
player recovery code. A username alone cannot reclaim someone else's profile.

## Retained improvements

Suggestions **2–9** are implemented. Suggestions **1 and 10** are excluded:
the eight achievements and their progress display are unchanged, and no external
backup service or storage account has been added.

| Change | Result |
| --- | --- |
| Returning players | A saved name collapses to “Playing as…” with an Edit button. |
| Player recovery | A private recovery code restores the original player after cookie loss, including hits, badges and cooldown. |
| Shared connections | Everyone can join automatically, with a separate signed player identity and cooldown. |
| Boss planning | Recent damage/hour, an estimated time remaining, and presets that fill the **next raid** HP field. Nothing adjusts HP automatically. |
| Red rally | Fifteen distinct raiders hitting within ten minutes unlock a cosmetic arena effect for that raid. No damage bonus. |
| Safer host edits | Live HP before/after and damage previews, plus the last 100 boss admin actions with account, time and changed values. |
| Cleaner interface | Remembered attack style, compact large totals with exact values available, consistent boss names, steady attack controls and restrained red accents. |
| Clearer refresh status | Boss “Last checked” age, and separate successful provider checks versus content-change times in admin. |
| Request protection | Bursts of rejected attacks/registration attempts are briefly throttled and flagged to admins. No automatic bans. |
| Simpler saves | Atomic UTF-8 JSON, with automatic import of the previous local save. No SQL is used for ongoing operation. |

**Hits have no daily or weekly limit.** A player can keep attacking whenever the
**30-second server cooldown** expires. Achievements are milestones, not attack
quotas. Every player retains their own 30-second cooldown on shared connections.
An eligible hit remains allowed even when rejected-request throttling is active.

## Keep your current progress when updating

1. Stop the running app before replacing its code. Keep a copy of the existing folder.
2. Merge the application files from this complete ZIP into the existing folder.
   Preserve your current `data/`, `private/`, root settings/account files, and
   environment settings. Do not replace newer private files with the bundled
   original seed. Do not create another nested project folder.
3. Keep **every root `.py` module** beside `wager_backend.py`; they are imports,
   not separate programs to launch. Missing `race_support.py` means the package
   was not copied in full; it is not a pip package.
4. Install the requirements, then start the same launcher:

```bash
python -m pip install -r requirements.txt
python wager_backend.py
```

On an existing persistent disk, startup first uses `data/state.json`. If that file
does not yet exist and the previous `data/redhunllef.sqlite3` exists, the app
imports its accounts, hashes, settings, live snapshots, boss, avatar and recovery
metadata into JSON. That import uses Python's built-in SQLite reader only once.
The old file is left intact. Keep it as a rollback copy; it is no longer updated.
A malformed existing save stops startup with a clear message instead of resetting
accounts or raid progress.

If your older installation set `LOCAL_DATABASE_PATH`, retain it for the one-time
import. `STATE_FILE` can select a different JSON path, but no setting is required.
Existing JSON wins over old files and seeds. Do not delete it to reset an account.

**App Platform deployment is different:** its replacement container cannot see
the old container's local files. Before redeploying, use the existing Superadmin
**Settings → Private recovery file** download and put the latest file in your
private repository as `private/recovery.seed.json`. Startup imports it on a fresh
filesystem. Changes made after that download will not be in that recovery file.

## Fresh installation

Extract the entire `redhunllef-rebuilt/` folder, open a terminal in it, and use the
two commands above. Visit `http://localhost:8080`, `/play`, and `/admin`.

The original supplied Superadmin is **gingrsnaps / enok2121**. The bundled original
account hashes and Shuffle/Kick configuration are preserved. Existing saved
accounts and changed passwords take precedence. There is no `manage_admin.py`
step. The configured ZIP and `FULL_CODE_BLOCKS.md` contain private configuration;
keep them in your private repository.

Requirements include Waitress, Pillow and timezone data. If an import such as
`waitress`, `PIL` or `tzdata` is missing, run `python -m pip install -r requirements.txt`
using the same Python environment that runs the app. `PIL` is supplied by Pillow.
No Node, frontend build, database package or separate game process is needed.

## DigitalOcean App Platform

Use one **Web Service** from the private GitHub repository containing these files.
Set the source directory to the folder containing `wager_backend.py`.

**Build command**

```bash
python -m pip install -r requirements.txt
```

**Run command**

```bash
python wager_backend.py
```

| Setting | Value |
| --- | --- |
| HTTP port | `8080` |
| Health check | `/healthz` |
| Instance count | `1` |
| `APP_ENV` | `production` |
| `PORT` | `8080` |
| `TRUST_APP_PLATFORM` | `1` |
| `SESSION_COOKIE_SECURE` | `always` |

`app.yaml` contains the same deployment shape; replace its GitHub repository
placeholder if you import that specification. `Procfile` uses the same launcher.
Remove an obsolete database binding from the App Platform environment: the
platform may try to resolve that binding before Python starts. This build ignores
`DATABASE_URL` and `STORAGE_MODE`; it never connects to PostgreSQL.

Keep one instance. Each App Platform instance has its own temporary filesystem,
so multiple replicas would split the raid. A process restart that keeps the same
data folder preserves progress; a container replacement or redeployment does not.
DigitalOcean documents this restriction in
[Store Data in App Platform](https://docs.digitalocean.com/products/app-platform/how-to/store-data/).
This release adds no external persistence service. The existing manual recovery
export is the available checkpoint method on App Platform. On a persistent Linux
host, preserve the `data/` folder during code updates.

Use `TRUST_APP_PLATFORM=1` only behind App Platform ingress. The app then uses
`DO-Connecting-IP` for admin request logging and existing access controls. Game identity does not depend on that header. On a directly exposed/local host, leave
it unset or `0`. Arbitrary client forwarding headers are not accepted as identity.

## Accounts and automatic updates

`/admin` renders the login or dashboard directly. All management routes require a
current admin account, an unrevoked session, and CSRF protection for writes.
The Superadmin manages administrator accounts and downloads full private recovery.
Other current admins can manage boss controls and avatars, and
view full player names in the private Top 5.

Both Shuffle and Kick are checked **automatically every 60 seconds**, by independent
threads inside the sole launch process. There is no live-data switch or manual-only
mode. The public leaderboard and admin provider views refresh every 60 seconds;
a manual source refresh shows progress until the check finishes. Boss public and
admin views refresh every **5 seconds**. Hidden browser tabs pause their own polling
and catch up when visible; the server's source jobs continue.

The original seed's race window is historical. To publish the intended window,
open **Race**, edit the Eastern Time dates, choose **Save race settings**, review the
changes, then **Confirm and publish race**. Check the published window in
**Live connections**. A successful source check does not necessarily mean wager
values changed; both times are shown separately. Failures retain previously
confirmed data and show the reason. No lifetime-wager fallback or fabricated data
replaces a failed live response.

The public leaderboard masks names. The admin Players tab retains the collapsible
first 100 confirmed Code Red wagerers, search, full names, exports and overrides.
Provider keys are read from the original private configuration, with nonempty
runtime environment overrides available for `SHUFFLE_API_KEY`, `KICK_CLIENT_ID`
and `KICK_CLIENT_SECRET`.

## Community boss

Open `/play` or the homepage boss button. Save a self-reported Community/Shuffle
username once, then choose Blade, Bow or Magic. Your full submitted name is visible
to you and administrators; other visitors see a raider alias.

| Rule | Behavior |
| --- | --- |
| Attack cooldown | 30 seconds, checked by the server. |
| Daily/weekly quota | None. |
| Default damage | 100 base, 150 weakness, +100 burst every tenth hit. Admin-editable. |
| Weakness | Random stable draw every 10 minutes, shared by all players. Repeats are valid. |
| Health | Never regenerates automatically. Confirmed damage stays saved. |
| Progress bar | 0% to 100% defeated, based on remaining/max HP. |
| Input re-arm | Mouse pointer must leave the attack button; keyboard must release its activation key; touch taps work on release. |
| Red rally | 15 distinct raiders in a rolling 10-minute window; cosmetic arena lighting lasts until a new raid. |
| Achievements | Existing eight badges and progress display retained; achievement history carries across raids. |

The pointer rule discourages a stationary clicker. It cannot prove that a human
clicked; the server independently enforces identity, cooldowns, damage and
idempotent receipts. Retrying an unconfirmed hit never deals damage twice.

Expand **Player recovery**, create a code, and save the text file somewhere private.
Only a digest of the code is saved. The full code is shown in that response, not
published in game feeds or stored in browser local storage. Creating a replacement
invalidates the previous code. The code restores the same player identity, so it
does not erase cooldowns, receipts or contributions. It also works after a new
raid. It requires the same saved app secret and profile data; it cannot restore a
profile after all server saves have been lost. Anyone with a valid code can use
that player profile, so do not post it publicly.

Each signed browser identity owns one saved username. Independent players on the
same IP, VPN, carrier network or proxy can play together without approval. Multiple
tabs sharing one browser cookie share one player and one cooldown. An IP change
neither renames a player nor gives an extra hit. Old connection/household records
are accepted when reading existing saves but are no longer admission rules.

A cookie identifies a browser, not a verified person. Clearing cookies or using a
new browser can create a different identity with a different name; the game does
not claim to prevent every multi-account bot. It retains server cooldowns,
idempotent receipts, per-browser request throttles and admin-only controls. Names
remain self-reported; a Shuffle spelling match is not ownership verification.

## Boss administration

Use **Community boss** in the admin menu:

- Upload PNG, JPG, JPEG or WebP. The server validates real image content, file size,
  dimensions and animation before resizing to a safe PNG. Public visitors can view
  the avatar; only current admins can replace or reset it.
- Rename the boss and set future base/weakness/burst damage. The preview shows both
  normal and tenth-hit totals together. Existing damage is retained.
- Change maximum HP or set remaining HP explicitly. The preview uses current
  confirmed health. Saving requires confirmation; stale admin revisions cannot
  overwrite another admin's edit. Raising health is an explicit admin heal.
- Review recent pace and time remaining. Estimates require at least five minutes,
  ten hits and positive damage. Presets target roughly three, five or seven days
  **at the observed pace**. Before enough activity exists, 10M/25M/50M are starting
  suggestions, not promised durations. Presets only fill the new-raid field.
- Start a new raid only after confirming. Names, recovery digests, achievements,
  avatar and combat settings carry forward. Current raid
  contributions/cooldowns reset and the previous raid is summarized in history.
- View the uncensored Top 5, the last 100 saved boss
  admin actions and temporary rejected-request flags. Normal timer-perfect hits
  are never flagged merely for regular timing. Flags are diagnostic, not bans.

Whole-number maximum HP accepts `1` through `9,007,199,254,740,991` (the browser's
largest exact integer). Remaining HP accepts `0` through the current maximum;
zero defeats the boss. Damage components accept `0` through that same exact-integer
maximum. Every actual hit is capped by remaining HP. There is no smaller arbitrary
HP/damage cap. The numeric capacity of a single raid is distinct from a daily or
weekly quota.

## Save files and recovery

| Path | Purpose |
| --- | --- |
| `data/state.json` | Current accounts, race settings, live snapshots, raid, profiles, avatar and history. |
| `data/state.json.lock` | Automatic process lock for file transactions. |
| `data/recovery/` | Bounded local copies made before important admin changes; no external service. |
| `private/recovery.seed.json` | Optional existing manual recovery export used only when no current local save exists. |
| `private/admin_store.seed.json` | Original supplied account seed for a fresh install. |
| `private/settings.json` | Original supplied provider configuration. |

All state writes use UTF-8, flush to disk, and replace the current file atomically.
Readers see a complete old or new save. A write failure does not acknowledge a new
hit; safe receipt retries handle an uncertain response. Local recovery copies live
on the same disk and do not survive loss of an App Platform container.

The private recovery export includes accounts, secret, race configuration, saved
Top 15, boss avatar, private profiles, contribution totals and boss admin history.
It is not exposed publicly. A restored Top 15 remains a snapshot until the next
successful live source check. The recovery status records when an export was
created, not proof that someone saved it externally.

## File structure and complete code

See `FILE_STRUCTURE.md` for every shipped file and its purpose.
`FULL_CODE_BLOCKS.md` contains every application text file in its own full code
block; the ZIP contains those ready-to-use files plus the original logos.

The previous optional `requirements-postgres.txt` and `tests/test_postgres.py`
are removed. An old `manage_admin.py` is not needed by this release. Keep the old
local save as a rollback copy and keep every current root support module.

## Verification

The release passed 132 backend tests and 57 DOM/interface checks. Coverage includes
source refresh behavior, actual launcher startup, login, authorization, image
validation, nonregenerating HP, unlimited attacks, recovery-code privacy, independent
cooldowns, migration, atomic-write failures and simultaneous writers. New regression
checks include 100 concurrent players sharing one proxy, absent IP headers, changing
addresses, names retained after restart, and delayed browser responses.

No live Shuffle/Kick request or DigitalOcean deployment was performed during these
checks. Provider tests use synthetic responses; native browser visual rendering was
unavailable in the test environment. See `docs/VALIDATION.md` for the scope.

Developer checks (not required to run the website):

```bash
python -m unittest discover -s tests -v
python tests/render_fixtures.py .test-fixtures
npm --prefix tests install --ignore-scripts
npm --prefix tests test
```
````

## START_HERE.md

````markdown
# Start RedHunllef

Release **2026.09.29-player-access** — complete configured package.

Install dependencies once, then run the sole launcher:

```bash
python -m pip install -r requirements.txt
python wager_backend.py
```

Keep all supporting Python files, templates and static files together.
No database service, SQL setup, account-creation command or extra worker is needed.
The app creates `data/state.json` and imports an existing previous local save.

- Website: `/`
- Community boss: `/play`
- Admin: `/admin`
- Original supplied Superadmin: **gingrsnaps / enok2121**. Existing accounts/passwords win.

When updating, preserve current `data/`, `private/`, settings and environment
configuration. Copy the application code from this ZIP into matching paths.
Do not replace newer private seeds with the bundled originals.

DigitalOcean App Platform: use the same build/run commands, port **8080**,
health check **/healthz**, and **one instance**. Set `APP_ENV=production`,
`TRUST_APP_PLATFORM=1`, and `SESSION_COOKIE_SECURE=always`.
Remove stale database environment bindings. No database component is needed.

App Platform loses local files on redeployment/container replacement. Before
redeploying, download **Settings → Private recovery file** as the Superadmin and
save it as `private/recovery.seed.json` in your private repository. New changes
after the export can be lost. No external backup integration has been added.

Hits are **unlimited per day and week**, with a **30-second cooldown**. The eight
achievements and their existing display remain unchanged. Boss screens check every
5 seconds; Shuffle/Kick check automatically every 60 seconds.

This update fixes community access and saved usernames. Players use signed browser
cookies; shared IPs no longer block registration or share attack cooldowns. Changing
IP addresses and missing proxy headers no longer disable an existing player.
**Do not reset the raid or clear cookies to install this fix.** Preserve existing
saved data and reload the game after updating. Recovery codes restore a lost cookie.
Cosmetic rally, next-raid presets, edit previews, boss admin history and live status
remain available. Connection-release and household-approval controls are retired
because those restrictions no longer apply.
Original credentials, logos, live feeds, private Code Red list and admin-only boss
uploads/name/HP/damage controls remain intact.

Read `README.md` for migration/deployment details and `FULL_CODE_BLOCKS.md` for the
complete source in individual code blocks.
````

## abuse_guard.py

```python
"""Bounded, in-memory throttles for rejected requests, separate from gameplay.

Successful eligible attacks are never counted or blocked by this guard. A regular
30-second rhythm is not a reason to flag someone. Records expire; no bans exist.
"""
from collections import deque
import hashlib
import hmac
import threading
import time


class AbuseGuard:
    def __init__(self, secret):
        self.secret = secret.encode()
        self.lock = threading.Lock()
        self.records, self.flags = {}, deque(maxlen=50)

    def key(self, identity, address):
        # Admin diagnostics need a correlation tag, never a raw IP or cookie.
        return hmac.new(self.secret, (identity + ':' + address).encode(), hashlib.sha256).hexdigest()[:16]

    def _entry(self, category, key, now):
        for k, v in list(self.records.items()):
            if now - v['at'] >= 60: del self.records[k]
        pair = (category, key)
        if pair not in self.records:
            if len(self.records) >= 4000:
                self.records.pop(next(iter(self.records)))
            self.records[pair] = dict(at=now, count=0)
        return self.records[pair]

    def retry_after(self, category, key):
        with self.lock:
            now = time.monotonic()
            item = self._entry(category, key, now)
            threshold = 20 if category == 'registration' else 12
            return max(1, int(60 - now + item['at']) + 1) if item['count'] >= threshold else 0

    def rejected(self, category, key, alias):
        with self.lock:
            item = self._entry(category, key, time.monotonic())
            item['count'] += 1
            threshold = 20 if category == 'registration' else 12
            if item['count'] == threshold:
                self.flags.appendleft(dict(at=int(time.time()), category=category, tag=key,
                                           alias=alias[:40], rejected=threshold))

    def status(self):
        with self.lock:
            cutoff = time.time() - 86400
            return [dict(f) for f in self.flags if f['at'] > cutoff]
```

## app.yaml

```yaml
# Replace the repository name before importing. No database component is needed.
# App Platform local files are temporary; see README for private recovery seeds.
name: redhunllef
region: nyc
features:
  - buildpack-stack=ubuntu-22
services:
  - name: web
    environment_slug: python
    github:
      repo: YOUR_GITHUB_USER/YOUR_PRIVATE_REPOSITORY
      branch: main
      deploy_on_push: false
    source_dir: /
    build_command: python -m pip install -r requirements.txt
    run_command: python wager_backend.py
    http_port: 8080
    instance_count: 1
    instance_size_slug: apps-s-1vcpu-1gb
    health_check:
      http_path: /healthz
      initial_delay_seconds: 20
      period_seconds: 15
      timeout_seconds: 5
      failure_threshold: 3
    envs:
      - key: APP_ENV
        value: production
        scope: RUN_TIME
      - key: APP_STATE_KEY
        value: redhunllef
        scope: RUN_TIME
      - key: PORT
        value: "8080"
        scope: RUN_TIME
      - key: SESSION_COOKIE_SECURE
        value: always
        scope: RUN_TIME
      - key: TRUST_APP_PLATFORM
        value: "1"
        scope: RUN_TIME
      - key: SUPERADMIN_USER
        value: gingrsnaps
        scope: RUN_TIME
ingress:
  rules:
    - component:
        name: web
      match:
        path:
          prefix: /
alerts:
  - rule: DEPLOYMENT_FAILED
  - rule: DOMAIN_FAILED
```

## boss.py

```python
"""Shared community raid rules. Every hit is validated and committed server-side.

The boss lives in a separate record, so attacks cannot change race settings or
invalidate administrator forms. One web instance serves the whole community.
"""
import copy
import hashlib
import hmac
import ipaddress
import logging
import math
import re
import secrets
import threading
import time

from boss_extras import audit, balance_view, host_snapshot, rally_view, record_activity, validate_extras
from boss_avatar import image_bytes, validate_avatar
from boss_progress import MAX_NUMBER, badges, new_profile, record_hit, username, validate_profiles

LOG = logging.getLogger("redhunllef")
DEFAULT_HP = 2_400_000
MIN_HP, MAX_HP = 1, MAX_NUMBER
COOLDOWN = 30
DAILY_ATTACKS = None  # Legacy contract: null now means unlimited hits.
DAY = 86400
WARD_SECONDS = 600
POLL_SECONDS = 5
BASE_DAMAGE, WEAK_DAMAGE, BURST_EVERY, BURST_BONUS = 100, 150, 10, 100
MAX_DAMAGE = MAX_NUMBER
# Historical receipts must remain valid if the host later lowers attack damage.
MAX_HIT = MAX_NUMBER
DEFAULT_NAME = 'Crimson Hunllef'
STYLES = {"blade": "Blade", "bow": "Bow", "magic": "Magic"}
MAX_PLAYERS, MAX_NETWORKS = 2000, 4000
TOKEN = re.compile(r"[a-f0-9]{64}\Z")


def combat_settings(value=None):
    """Validate editable settings separately from immutable player damage totals."""
    if value is not None and not isinstance(value, dict):
        raise ValueError('Invalid boss settings.')
    value = value or {}
    name = value.get('name', DEFAULT_NAME)
    if not isinstance(name, str) or not 1 <= len(name) <= 60 or not name.strip() or not name.isprintable():
        raise ValueError('Boss name must contain 1–60 printable characters.')
    result = dict(name=name.strip(), damage=value.get('damage', BASE_DAMAGE),
                  weak_damage=value.get('weak_damage', WEAK_DAMAGE), burst_bonus=value.get('burst_bonus', BURST_BONUS))
    for field in ('damage', 'weak_damage', 'burst_bonus'):
        if type(result[field]) is not int or not 0 <= result[field] <= MAX_DAMAGE:
            raise ValueError(f'Damage must be a whole number from 0 to {MAX_DAMAGE:,}.')
    return result


def rules(state=None):
    """One contract for server validation, host controls, and browser labels."""
    settings = combat_settings((state or {}).get('settings'))
    return dict(cooldown=COOLDOWN, daily_attacks=DAILY_ATTACKS, raid_day=DAY,
                poll_seconds=POLL_SECONDS, ward_seconds=WARD_SECONDS, default_hp=DEFAULT_HP, identity_mode="browser",
                damage=settings['damage'], weak_damage=settings['weak_damage'], burst_every=BURST_EVERY,
                burst_bonus=settings['burst_bonus'],
                styles=dict(STYLES), min_hp=MIN_HP, max_hp=MAX_HP, max_damage=MAX_DAMAGE)


class BossError(ValueError):
    def __init__(self, message, code="invalid", status=400, retry_after=0):
        super().__init__(message)
        self.code, self.status, self.retry_after = code, status, retry_after


def fresh_raid(now=None, health=DEFAULT_HP, history=None, settings=None):
    now = int(time.time() if now is None else now)
    return dict(schema=1, id=secrets.token_hex(16), salt=secrets.token_hex(32),
                version=1, max_hp=health, hp=health, created_at=now, started_at=0,
                finished_at=0, paused=False, total_attacks=0, total_damage=0,
                players={}, networks={}, recent=[], history=list(history or [])[-10:],
                settings=combat_settings(settings), settings_revision=0)


def _integer(value, minimum=0, maximum=MAX_NUMBER):
    if type(value) is not int or not minimum <= value <= maximum:
        raise ValueError("The community boss recovery has an invalid number.")
    return value


def _timestamp(value):
    if type(value) not in (int, float) or not math.isfinite(value) or not 0 <= value <= 10**12:
        raise ValueError("The community boss recovery has an invalid timestamp.")


def validate_boss(value):
    """Validate recovery before a transaction imports any account or game data."""
    if not isinstance(value, dict) or value.get("schema") != 1:
        raise ValueError("Unsupported community boss recovery. Existing data was not replaced.")
    for field, pattern in (("id", r"[a-f0-9]{32}"), ("salt", r"[a-f0-9]{64}")):
        if not isinstance(value.get(field), str) or not re.fullmatch(pattern, value[field]):
            raise ValueError("The community boss recovery has an invalid identifier.")
    _integer(value.get("version"), 1)
    _integer(value.get("health_revision", 0))
    _integer(value.get('settings_revision', 0))
    combat_settings(value.get('settings'))  # Older raids inherit the original defaults.
    maximum = _integer(value.get("max_hp"), 1, MAX_HP)
    adjustment = _integer(value.get("health_adjustment", 0), -MAX_NUMBER, MAX_NUMBER)
    validate_extras(value, MAX_NETWORKS)
    validate_profiles(value.get("profiles", {}), MAX_PLAYERS, value.get("households"))
    hp = _integer(value.get("hp"), 0, maximum)
    for field in ("created_at", "started_at", "finished_at", "total_attacks", "total_damage"):
        _integer(value.get(field))
    if type(value.get("paused")) is not bool or value["total_damage"] != maximum - hp + adjustment:
        raise ValueError("The community boss recovery has inconsistent health.")
    if bool(value["finished_at"]) != (hp == 0) or (value["total_attacks"] and not value["started_at"]):
        raise ValueError("The community boss recovery has inconsistent progress.")
    players, networks = value.get("players"), value.get("networks")
    if not isinstance(players, dict) or len(players) > MAX_PLAYERS or not isinstance(networks, dict) or len(networks) > MAX_NETWORKS:
        raise ValueError("The community boss recovery has invalid player records.")
    for records in (players, networks):
        for key, record in records.items():
            if not isinstance(key, str) or not TOKEN.fullmatch(key) or not isinstance(record, dict):
                raise ValueError("The community boss recovery has an invalid player identifier.")
            _timestamp(record.get("last_attack"))
            _integer(record.get("day"))
            _integer(record.get("used"))
    for player in players.values():
        _integer(player.get("attacks"), 1)
        _integer(player.get("damage"), 0, MAX_NUMBER)
        if "active_days" in player:
            _integer(player["active_days"], 1, player["attacks"])
        receipt = player.get("last_hit")
        if not isinstance(receipt, dict) or not isinstance(receipt.get("style"), str) or receipt["style"] not in STYLES:
            raise ValueError("The community boss recovery has an invalid attack receipt.")
        if not isinstance(player.get("request_id"), str) or not re.fullmatch(r"[A-Za-z0-9_-]{8,64}", player["request_id"]):
            raise ValueError("The community boss recovery has an invalid request receipt.")
        _integer(receipt.get("damage"), 0, MAX_HIT)
        _integer(receipt.get("at"))
        if type(receipt.get("weakness")) is not bool or type(receipt.get("burst")) is not bool:
            raise ValueError("The community boss recovery has an invalid attack bonus.")
    if sum(p["damage"] for p in players.values()) != value["total_damage"] or sum(p["attacks"] for p in players.values()) != value["total_attacks"]:
        raise ValueError("The community boss recovery totals do not match its players.")
    recent, history = value.get("recent"), value.get("history")
    if not isinstance(recent, list) or len(recent) > 12 or not isinstance(history, list) or len(history) > 10:
        raise ValueError("The community boss recovery has an invalid history.")
    for hit in recent:
        if not isinstance(hit, dict) or not re.fullmatch(r"Raider [A-F0-9]{8}", str(hit.get("name", ""))) or not isinstance(hit.get("style"), str) or hit["style"] not in STYLES:
            raise ValueError("The community boss recovery has an invalid recent hit.")
        _integer(hit.get("damage"), 0, MAX_HIT)
        _integer(hit.get("at"))
    for entry in history:
        if not isinstance(entry, dict) or entry.get("outcome") not in {"Victory", "Restarted"}:
            raise ValueError("The community boss recovery has an invalid raid history.")
        for field in ("started_at", "ended_at", "max_hp", "damage", "attacks", "raiders"):
            _integer(entry.get(field))
    return copy.deepcopy(value)


def network_identity(address):
    """Normalize IPv4; group IPv6 /64 privacy addresses to limit easy rotation."""
    try:
        ip = ipaddress.ip_address(address)
    except ValueError:
        raise BossError("Your connection could not be identified. Reload and try again.") from None
    if getattr(ip, "ipv4_mapped", None):
        ip = ip.ipv4_mapped
    return str(ipaddress.ip_network((ip, 64), strict=False)) if ip.version == 6 else str(ip)


def _key(raid, kind, value):
    # Raw IP addresses and browser identifiers never enter game records/feeds.
    return hmac.new(bytes.fromhex(raid["salt"]), (kind + ":" + value).encode(), hashlib.sha256).hexdigest()


def _name(key):
    return "Raider " + key[:8].upper()


class CommunityBoss:
    def __init__(self, store):
        self.store, self.lock = store, threading.RLock()
        with self.store.connection(transaction=True) as conn:
            row = self.store.boss_read(conn)
            if not row:
                value = fresh_raid()
                self.store.boss_write(conn, value)
            else:
                value = validate_boss(row)
            self.avatar_document = validate_avatar(self.store.avatar(conn))
        self.state, self.loaded_at = value, time.monotonic()

    def _read(self, conn, locked=False):
        value = self.store.boss_read(conn)
        if value is None:
            raise ValueError("Community boss state is missing. Restore the private recovery checkpoint.")
        return validate_boss(value)

    def _write(self, conn, state, *, previous=None, new_raid=False, health_change=False, settings_change=False):
        """Only an explicit host health edit or new raid may replenish health.

        Callers already hold the storage transaction. Compare against the row
        read inside that transaction, never an older viewer/cache snapshot.
        """
        previous = self._read(conn, locked=True) if previous is None else previous
        if state["id"] != previous["id"]:
            if not new_raid:
                raise BossError("Starting a new boss requires the host's new-raid action.", "new_raid_required", 409)
        elif (state["total_damage"] < previous["total_damage"]
              or state["total_attacks"] < previous["total_attacks"]
              or state["version"] < previous["version"]
              or (not health_change and (state["max_hp"] != previous["max_hp"] or state["hp"] > previous["hp"]
                  or state.get("health_revision", 0) != previous.get("health_revision", 0)
                  or state.get("health_adjustment", 0) != previous.get("health_adjustment", 0)))
              or (health_change and (state.get("health_revision", 0) != previous.get("health_revision", 0) + 1
                  or state["total_damage"] != previous["total_damage"] or state["total_attacks"] != previous["total_attacks"]))):
            LOG.error("BOSS Blocked a progress reversal. Saved damage and health were not changed.")
            raise BossError("Boss progress cannot move backwards. Existing damage was preserved.", "progress_reversal", 409)
        if not 0 <= state["hp"] <= state["max_hp"] or state["hp"] != state["max_hp"] - state["total_damage"] + state.get("health_adjustment", 0):
            raise BossError("Boss health does not match saved damage. Existing progress was preserved.", "invalid_health", 409)
        if state['id'] == previous['id']:
            changed = combat_settings(state.get('settings')) != combat_settings(previous.get('settings'))
            revision, old_revision = state.get('settings_revision', 0), previous.get('settings_revision', 0)
            if ((not settings_change and (changed or revision != old_revision)) or
                (settings_change and (revision != old_revision + 1 or state['hp'] != previous['hp'] or
                 state['total_damage'] != previous['total_damage'] or state['total_attacks'] != previous['total_attacks']))):
                raise BossError('Boss settings require an explicit admin edit. Existing progress was preserved.', 'settings_guard', 409)
        self.store.boss_write(conn, state)

    def _load(self, force=False):
        # Most 5-second viewer polls use memory, not another disk read. A
        # periodic reload also picks up writes from another process during tests
        # or a short deployment overlap. Local mode still requires one instance.
        if force or time.monotonic() - self.loaded_at >= POLL_SECONDS:
            with self.store.connection() as conn:
                self.state = self._read(conn)
                # Images stay outside the frequently rewritten gameplay record.
                if self.state.get('avatar_hash') != (self.avatar_document or {}).get('sha256'):
                    self.avatar_document = validate_avatar(self.store.avatar(conn))
            self.loaded_at = time.monotonic()

    def _project(self, state, guest, address, now):
        keys = list(STYLES)
        # A secret-keyed draw is random to visitors, stable for every viewer and
        # process, and needs no scheduler writes. Repeats are valid random draws.
        window = int(now) // WARD_SECONDS
        draw = _key(state, "ward", state["id"] + ":" + str(window))
        weakness = keys[int(draw, 16) % len(keys)]
        day = max(0, int((now - state["started_at"]) // DAY)) if state["started_at"] else 0
        reset = state["started_at"] + (day + 1) * DAY if state["started_at"] else 0
        player_key = _key(state, "player", guest) if guest else ""
        player = state["players"].get(player_key, {})
        profile = state.get("profiles", {}).get(player_key, {})
        # A proxy, household, campus or carrier may expose one IP for many
        # people. The signed browser cookie owns the profile and its cooldown.
        # Legacy network records remain readable but never decide who can play.
        identity_ready = bool(profile)
        ready = player.get("last_attack", 0) + COOLDOWN
        phase = "Awakening" if state["hp"] > state["max_hp"] * .75 else "Enraged" if state["hp"] > state["max_hp"] * .25 else "Last stand"
        status = "victory" if state["hp"] == 0 else "paused" if state["paused"] else "active" if state["started_at"] else "waiting"
        leaders = sorted(state["players"].items(), key=lambda item: (-item[1]["damage"], item[0]))[:10]
        return dict(server_time=now, raid_id=state["id"], version=state["version"], status=status, connection_ready=bool(guest),
                    name=combat_settings(state.get('settings'))['name'], settings_revision=state.get('settings_revision', 0),
                    health_revision=state.get("health_revision", 0), avatar_url=self.avatar_url(), avatar_custom=bool(self.avatar_document),
                    hp=state["hp"], max_hp=state["max_hp"], phase=phase, started_at=state["started_at"],
                    finished_at=state["finished_at"], day=day + 1, resets_at=reset,
                    total_damage=state["total_damage"], total_attacks=state["total_attacks"], raiders=len(state["players"]),
                    weakness=weakness, weakness_label=STYLES[weakness], ward_changes_at=(int(now) // WARD_SECONDS + 1) * WARD_SECONDS,
                    rules=rules(state), rally=rally_view(state, now),
                    milestones=[dict(percent=p, label=label, reached=(state["max_hp"] - state["hp"]) * 100 >= state["max_hp"] * p)
                                for p, label in ((25, "Armor cracked"), (50, "The crew rallies"), (75, "Final stand"), (100, "Crimson conquered"))],
                    you=dict(name=_name(player_key) if guest else "Spectator", damage=player.get("damage", 0),
                             attacks=player.get("attacks", 0), remaining=None, ready_at=ready,
                             display_name=profile.get("name", ""), identity_ready=identity_ready,
                             recovery_saved=bool(profile.get("recovery_hash")), shared_connection=False,
                             burst_in=BURST_EVERY - player.get("attacks", 0) % BURST_EVERY,
                             active_days=profile.get("active_days", player.get("active_days", 1 if player else 0)),
                             badges=badges(profile or player, now),
                             last_request=player.get("request_id", ""), last_hit=copy.deepcopy(player.get("last_hit")),
                             can_attack=bool(guest and status in {"waiting", "active"} and identity_ready and now >= ready)),
                    leaders=[dict(name=_name(key), damage=p["damage"], attacks=p["attacks"], you=key == player_key) for key, p in leaders],
                    recent=copy.deepcopy(state["recent"]), history=copy.deepcopy(state["history"]))

    def register(self, guest, address, raid_id, name):
        """Persist a private name for this signed browser, independently of IP.

        Existing profile keys and stats are untouched. Recovery codes remain
        the way to restore a lost cookie; matching a name or IP proves nothing.
        """
        name = username(name)
        now = time.time()
        with self.lock:
            with self.store.connection(transaction=True) as conn:
                state = self._read(conn, locked=True)
                if raid_id != state['id']:
                    raise BossError('Another raid started. Refresh before saving your name.', 'new_raid', 409)
                previous = copy.deepcopy(state)
                pk = _key(state, 'player', guest)
                profiles = state.setdefault('profiles', {})
                for key, profile in profiles.items():
                    if key != pk and profile['name'].casefold() == name.casefold():
                        raise BossError('That username is already registered. Use your recovery code or original browser.', 'name_claimed', 409)
                own = profiles.get(pk)
                if own and own['name'] == name:
                    self.state, self.loaded_at = state, time.monotonic()
                    return self._project(state, guest, address, now)
                if own and now - own['named_at'] < COOLDOWN:
                    raise BossError('Wait 30 seconds before changing your name again.', 'profile_cooldown', 429,
                                    max(1, math.ceil(COOLDOWN - now + own['named_at'])))
                if not own and len(profiles) >= MAX_PLAYERS:
                    raise BossError('The player registry is full. Contact an admin.', 'capacity', 409)
                if own:
                    own.update(name=name, named_at=now)
                else:
                    # Retain the legacy field shape for portable old-save recovery.
                    # It is a browser-specific reservation, not an IP claim.
                    profiles[pk] = new_profile(name, _key(state, 'reservation', guest), now, state['players'].get(pk))
                state['version'] += 1
                self._write(conn, state, previous=previous)
            self.state, self.loaded_at = state, time.monotonic()
            return self._project(state, guest, address, now)

    def release_profile(self, raid_id, name, *, actor="System"):
        raise BossError("Connection claims are retired. Each player can join directly; no release or raid reset is needed.", "retired_control", 409)

    def save_recovery(self, guest, code_hash):
        """Store only a digest. The full bearer code is displayed once to its owner."""
        with self.lock:
            with self.store.connection(transaction=True) as conn:
                state = self._read(conn, locked=True)
                previous = copy.deepcopy(state)
                pk = _key(state, 'player', guest)
                if pk not in state.get('profiles', {}):
                    raise BossError('Save your username before creating a recovery code.')
                profile = state['profiles'][pk]
                now = time.time()
                if now - profile.get('recovery_at', 0) < COOLDOWN:
                    raise BossError('Wait 30 seconds before replacing your recovery code.', 'profile_cooldown', 429)
                profile['recovery_at'] = now
                profile['recovery_hash'] = code_hash
                state['version'] += 1
                self._write(conn, state, previous=previous)
            self.state, self.loaded_at = state, time.monotonic()

    def recover_profile(self, guest, address, code_hash, raid_id):
        with self.lock:
            with self.store.connection(transaction=True) as conn:
                state = self._read(conn, locked=True)
                if raid_id != state['id']:
                    raise BossError('A new raid started. Reload before recovering.', 'new_raid', 409)
                previous = copy.deepcopy(state)
                pk = _key(state, 'player', guest)
                profiles = state.get('profiles', {})
                profile = profiles.get(pk, {})
                if not hmac.compare_digest(profile.get('recovery_hash', ''), code_hash):
                    raise BossError('That recovery code is invalid or was replaced.', 'invalid_recovery', 400)
                # Same browser key restores all hits and cooldowns exactly. The
                # HTTP layer validates the signed code before calling this method.
                # No network binding is changed or required during recovery.
                state['version'] += 1
                self._write(conn, state, previous=previous)
            self.state, self.loaded_at = state, time.monotonic()
            return self._project(state, guest, address, time.time())

    def household(self, raid_id, name, slots, *, actor="System"):
        raise BossError("Household approvals are no longer needed. Shared connections support all players automatically.", "retired_control", 409)

    def admin_status(self):
        """Private top five. Public projections always keep anonymous aliases."""
        with self.lock:
            self._load()
            result = self._project(self.state, None, None, time.time())
            profiles = self.state.get('profiles', {})
            leaders = sorted(self.state['players'].items(), key=lambda item: (-item[1]['damage'], item[0]))[:5]
            result['balance'] = balance_view(self.state, time.time())
            result['admin_history'] = list(reversed(copy.deepcopy(self.state.get('admin_history', []))))
            result['admin_leaders'] = [dict(name=profiles.get(key, {}).get('name', _name(key)),
                                            alias=_name(key), name_provided=key in profiles,
                                            damage=p['damage'], attacks=p['attacks']) for key, p in leaders]
            return result

    def summary(self):
        """Small anonymous homepage projection: no guest, receipt, or network data."""
        with self.lock:
            self._load()
            state = self.state
            status = "victory" if state["hp"] == 0 else "paused" if state["paused"] else "active" if state["started_at"] else "waiting"
            return dict(raid_id=state["id"], hp=state["hp"], max_hp=state["max_hp"],
                        name=combat_settings(state.get('settings'))['name'],
                        status=status, raiders=len(state["players"]), total_attacks=state["total_attacks"],
                        total_damage=state["total_damage"], version=state["version"],
                        health_revision=state.get("health_revision", 0), avatar_url=self.avatar_url(), avatar_custom=bool(self.avatar_document))

    def avatar_url(self):
        return '/play/avatar/' + self.avatar_document['sha256'] + '.png' if self.avatar_document else '/static/redlogo.png'

    def avatar_image(self, digest):
        with self.lock:
            self._load()
            return image_bytes(self.avatar_document) if self.avatar_document and self.avatar_document['sha256'] == digest else None

    def set_avatar(self, raid_id, avatar, *, actor="System"):
        avatar = validate_avatar(avatar)
        with self.lock:
            with self.store.connection(transaction=True) as conn:
                state = self._read(conn, locked=True)
                if raid_id != state['id']:
                    raise BossError('Another raid started. Reload before changing the avatar.', 'new_raid', 409)
                previous = copy.deepcopy(state)
                self.store.backup_in(conn, 'before-boss-avatar', dict(community_boss=state, community_boss_avatar=self.store.avatar(conn)))
                self.store.avatar_in(conn, avatar)
                state['version'] += 1
                state['avatar_hash'] = avatar['sha256'] if avatar else None
                audit(state, 'Change avatar', actor, {'avatar': previous.get('avatar_hash') or 'Original logo'}, {'avatar': state['avatar_hash'] or 'Original logo'})
                self._write(conn, state, previous=previous)
            self.state, self.avatar_document, self.loaded_at = state, avatar, time.monotonic()
        LOG.info('BOSS Avatar %s; raid progress retained.', 'updated' if avatar else 'reset to original logo')

    def contributors(self):
        """Victory recap includes every contributor, using only raid aliases."""
        with self.lock:
            self._load()
            if self.state["hp"]:
                return []
            return [dict(name=_name(key), damage=p["damage"], attacks=p["attacks"])
                    for key, p in sorted(self.state["players"].items(), key=lambda item: (-item[1]["damage"], item[0]))]

    def status(self, guest=None, address=None):
        with self.lock:
            self._load()
            return self._project(self.state, guest, address, time.time())

    def export(self):
        with self.lock:
            self._load(force=True)
            return copy.deepcopy(self.state)

    def recovery(self):
        with self.lock:
            self._load(force=True)
            return dict(community_boss=copy.deepcopy(self.state), community_boss_avatar=copy.deepcopy(self.avatar_document))

    def attack(self, guest, address, style, raid_id, request_id, *, require_profile=False):
        if not isinstance(style, str) or style not in STYLES or not isinstance(request_id, str) or not re.fullmatch(r"[A-Za-z0-9_-]{8,64}", request_id):
            raise BossError("Choose Blade, Bow, or Magic, then try again.")
        with self.lock:
            now = time.time()
            with self.store.connection(transaction=True) as conn:
                state = self._read(conn, locked=True)
                self.state = copy.deepcopy(state)
                if raid_id != state["id"]:
                    raise BossError("A new raid has started. Review the new boss before attacking.", "new_raid", 409)
                view = self._project(state, guest, address, now)
                pk = _key(state, "player", guest)
                existing = state["players"].get(pk, {})
                # A retry of an acknowledged click never lands a second hit,
                # including retries after victory or after the cooldown ends.
                if existing.get("request_id") == request_id:
                    return dict(ok=True, duplicate=True, hit=copy.deepcopy(existing["last_hit"]), state=view)
                if view["status"] in {"paused", "victory"}:
                    raise BossError("The host paused the raid." if state["paused"] and state["hp"] else "The community has already defeated this boss.", view["status"], 409)
                if now < view["you"]["ready_at"]:
                    retry = max(1, math.ceil(view["you"]["ready_at"] - now))
                    raise BossError("Your player is cooling down. Wait for the timer.", "cooldown", 429, retry)
                if require_profile and not view['you']['identity_ready']:
                    raise BossError('Save your username once in this browser before attacking.', 'username_required', 409)
                day = view["day"] - 1
                if pk not in state["players"] and len(state["players"]) >= MAX_PLAYERS:
                    raise BossError("This raid has reached its player capacity. The host can start a new raid.", "capacity", 409)
                player = state["players"].setdefault(pk, dict(attacks=0, damage=0))
                # Older saves cannot reconstruct every past participation day.
                # Credit one known day, then count future distinct days exactly.
                active_days = player.get("active_days", 1 if player["attacks"] else 0)
                player["active_days"] = active_days + int(player.get("day") != day)
                burst = (player["attacks"] + 1) % BURST_EVERY == 0
                weak = style == view["weakness"]
                # Public requests select a style only. Damage always comes from
                # the saved, validated admin settings read in this transaction.
                damage = min(state["hp"], (view['rules']['weak_damage'] if weak else view['rules']['damage'])
                             + (view['rules']['burst_bonus'] if burst else 0))
                hit = dict(style=style, damage=damage, weakness=weak, burst=burst, at=int(now))
                player.update(used=(player.get("used", 0) if player.get("day") == day else 0) + 1,
                              day=day, last_attack=now)
                # Preserve fractional seconds so early clicks never shorten
                # the server-enforced cooldown.
                player.update(attacks=player["attacks"] + 1, damage=player["damage"] + damage,
                              request_id=request_id, last_hit=hit)
                # Cumulative committed damage is never reset by cooldowns,
                # weakness rotations, midnight, idle time, or source refreshes.
                total_damage = state["total_damage"] + damage
                if total_damage > MAX_NUMBER:
                    raise BossError("This raid reached its numeric capacity. Ask an admin to start a new raid.", "capacity", 409)
                if pk in state.get("profiles", {}):
                    record_hit(state["profiles"][pk], hit, now)
                state.update(hp=state["hp"] - damage, total_damage=total_damage,
                             total_attacks=state["total_attacks"] + 1, version=state["version"] + 1,
                             started_at=state["started_at"] or int(now))
                state["recent"] = [dict(name=_name(pk), **hit)] + state["recent"][:11]
                record_activity(state, pk, damage, now)
                if not state["hp"]:
                    state["finished_at"] = int(now)
                self._write(conn, state, previous=self.state)
            self.state, self.loaded_at = state, time.monotonic()
            if state["finished_at"]:
                LOG.info("BOSS Victory; %s attacks from %s raider profiles.", state["total_attacks"], len(state["players"]))
            elif state["total_attacks"] == 1:
                LOG.info("BOSS Shared raid started; HP=%s, cooldown=%ss, daily cap=none; health regeneration=off.",
                         state["max_hp"], COOLDOWN)
            return dict(ok=True, duplicate=False, hit=hit, state=self._project(state, guest, address, now))

    def configure(self, raid_id, values, settings_revision, *, actor="System"):
        """Called only after the HTTP admin-session and CSRF guards succeed."""
        values = combat_settings(values)
        with self.lock:
            with self.store.connection(transaction=True) as conn:
                state = self._read(conn, locked=True)
                if raid_id != state['id']:
                    raise BossError('Another raid started. Reload before changing its settings.', 'new_raid', 409)
                if settings_revision != state.get('settings_revision', 0):
                    raise BossError('Another admin saved boss settings. Reload and review before saving.', 'settings_conflict', 409)
                if values == combat_settings(state.get('settings')):
                    return
                previous = copy.deepcopy(state)
                self.store.backup_in(conn, 'before-boss-settings', dict(community_boss=state))
                state.update(settings=values, settings_revision=state.get('settings_revision', 0) + 1,
                             version=state['version'] + 1)
                audit(state, "Boss settings", actor, combat_settings(previous.get("settings")), values)
                self._write(conn, state, previous=previous, settings_change=True)
            self.state, self.loaded_at = state, time.monotonic()
        LOG.info('BOSS Name/damage settings saved; base=%s, weakness=%s, burst=%s. Existing hits and HP retained.',
                 values['damage'], values['weak_damage'], values['burst_bonus'])

    def control(self, action, raid_id, health=DEFAULT_HP, *, health_revision=None, actor="System"):
        if action not in {"pause", "resume", "restart", "health", "remaining_health"}:
            raise BossError("Choose a valid boss action.")
        if action in {"restart", "health", "remaining_health"}:
            if type(health) is not int or not (0 if action == "remaining_health" else MIN_HP) <= health <= MAX_HP:
                raise BossError(f'Enter whole-number HP up to {MAX_HP:,}; only remaining HP may be zero.')
        with self.lock:
            with self.store.connection(transaction=True) as conn:
                state = self._read(conn, locked=True)
                if state["id"] != raid_id:
                    raise BossError("Another raid has started. Reload before changing it.", "new_raid", 409)
                previous = copy.deepcopy(state)
                if action in {"health", "remaining_health"}:
                    if health_revision != state.get('health_revision', 0):
                        raise BossError('Another health edit was saved. Reload and review before changing it again.', 'health_conflict', 409)
                    maximum = health if action == 'health' else state['max_hp']
                    if action == 'remaining_health' and health > maximum:
                        raise BossError('Remaining HP cannot exceed maximum HP. Raise maximum HP first.')
                    remaining = max(0, min(maximum, state['hp'] + maximum - state['max_hp'])) if action == 'health' else health
                    if maximum == state['max_hp'] and remaining == state['hp']:
                        return
                    self.store.backup_in(conn, 'before-boss-health', dict(community_boss=state))
                    # Explicit admin edits never erase player damage. The offset
                    # separates health adjustments from permanent contributions.
                    state.update(max_hp=maximum, hp=remaining, version=state['version'] + 1,
                                 health_adjustment=remaining - maximum + state['total_damage'],
                                 health_revision=state.get('health_revision', 0) + 1)
                    state['finished_at'] = (state['finished_at'] or int(time.time())) if state['hp'] == 0 else 0
                elif action == "restart":
                    self.store.backup_in(conn, "before-boss-restart", {"community_boss": state})
                    history = state["history"]
                    if state["total_attacks"]:
                        history.append(dict(outcome="Victory" if not state["hp"] else "Restarted", started_at=state["started_at"],
                                            ended_at=state["finished_at"] or int(time.time()), max_hp=state["max_hp"],
                                            damage=state["total_damage"], attacks=state["total_attacks"], raiders=len(state["players"])))
                    state = fresh_raid(health=health, history=history, settings=previous.get('settings'))
                    # Preserve the image version so polls need no image-record
                    # read unless an administrator actually changes the avatar.
                    state['avatar_hash'] = previous.get('avatar_hash')
                    # Names and week-long achievements survive a boss defeat.
                    state['salt'] = previous['salt']
                    state['profiles'] = copy.deepcopy(previous.get('profiles', {}))
                    state['households'] = copy.deepcopy(previous.get('households', {}))
                    state['admin_history'] = copy.deepcopy(previous.get('admin_history', []))
                else:
                    state["paused"], state["version"] = action == "pause", state["version"] + 1
                audit(state, action.replace("_", " ").title(), actor, host_snapshot(previous), host_snapshot(state))
                self._write(conn, state, previous=previous, new_raid=action == "restart", health_change=action in {'health', 'remaining_health'})
            self.state, self.loaded_at = state, time.monotonic()
        if action in {'health', 'remaining_health'}:
            LOG.info('BOSS Maximum HP %s -> %s; %s HP remains; %s saved damage retained. Automatic regeneration stays off.',
                     previous['max_hp'], state['max_hp'], state['hp'], state['total_damage'])
        else:
            LOG.info("BOSS Host action: %s.", action)
```

## boss_avatar.py

```python
"""Bounded PNG/JPEG/WebP uploads; store only a decoded, metadata-free PNG.

The image is a separate record, so every hit does not rewrite image bytes.
Recovery files carry this record alongside the raid, not inside its counters.
"""
import base64
import binascii
import hashlib
import io
import warnings

from PIL import Image, ImageOps, UnidentifiedImageError

MAX_UPLOAD = 4 * 1024 * 1024
MAX_PIXELS = 16_000_000
MAX_EDGE = 512
MAX_SAVED = 1_100_000


def from_upload(upload):
    if not upload or not upload.filename or upload.filename.rsplit('.', 1)[-1].lower() not in {'png', 'jpg', 'jpeg', 'webp'}:
        raise ValueError('Choose a PNG, JPG, JPEG or WebP image.')
    raw = upload.read(MAX_UPLOAD + 1)
    if not raw or len(raw) > MAX_UPLOAD:
        raise ValueError('Choose an image smaller than 4 MB.')
    try:
        with warnings.catch_warnings():
            warnings.simplefilter('error', Image.DecompressionBombWarning)
            with Image.open(io.BytesIO(raw)) as source:
                if source.format not in {'PNG', 'JPEG', 'WEBP'}:
                    raise ValueError('Only PNG, JPEG and WebP image contents are accepted.')
                if source.width * source.height > MAX_PIXELS:
                    raise ValueError('Use an image with at most 16 million pixels.')
                if getattr(source, 'n_frames', 1) != 1:
                    raise ValueError('Choose a still image, not an animated image.')
                source.load()  # Detect truncated/corrupt data before replacing anything.
                oriented = ImageOps.exif_transpose(source).convert('RGBA')
                oriented.thumbnail((MAX_EDGE, MAX_EDGE), Image.Resampling.LANCZOS)
                clean = Image.new('RGBA', oriented.size)
                clean.paste(oriented)
                output = io.BytesIO()
                clean.save(output, format='PNG')
    except (UnidentifiedImageError, OSError, Image.DecompressionBombError, Image.DecompressionBombWarning):
        raise ValueError('That image could not be read safely. Choose another PNG, JPEG or WebP.') from None
    data = output.getvalue()
    if len(data) > MAX_SAVED:
        raise ValueError('The processed image is too large. Choose a simpler image.')
    return dict(sha256=hashlib.sha256(data).hexdigest(), data=base64.b64encode(data).decode('ascii'))


def validate_avatar(value):
    """Validate an optional recovery image before the import transaction commits."""
    if value is None:
        return None
    if not isinstance(value, dict) or not isinstance(value.get('data'), str) or len(value['data']) > (MAX_SAVED + 2) // 3 * 4:
        raise ValueError('Invalid boss avatar recovery.')
    try:
        raw = base64.b64decode(value['data'], validate=True)
        if not raw or len(raw) > MAX_SAVED or hashlib.sha256(raw).hexdigest() != value.get('sha256'):
            raise ValueError('Boss avatar recovery checksum does not match.')
        with warnings.catch_warnings():
            warnings.simplefilter('error', Image.DecompressionBombWarning)
            with Image.open(io.BytesIO(raw)) as image:
                if image.format != 'PNG' or not (1 <= image.width <= MAX_EDGE and 1 <= image.height <= MAX_EDGE) or getattr(image, 'n_frames', 1) != 1:
                    raise ValueError('Invalid boss avatar dimensions or format.')
                image.verify()
    except (binascii.Error, UnicodeEncodeError, UnidentifiedImageError, OSError, Image.DecompressionBombError, Image.DecompressionBombWarning):
        raise ValueError('Invalid boss avatar recovery image.') from None
    return dict(sha256=value['sha256'], data=value['data'])


def image_bytes(value):
    return base64.b64decode(value['data'])
```

## boss_extras.py

```python
"""Small, bounded raid additions: cosmetic rally, pace estimates and host history.

These features never change damage, replenish health or limit successful hits.
All timestamps and counts come from committed server attacks.
"""
import copy
import math
import re
import time

MAX_NUMBER = 2**53 - 1
RALLY_GOAL, RALLY_WINDOW = 15, 600


def record_activity(state, player_key, damage, now):
    rally = state.setdefault('rally', {'players': {}, 'unlocked_at': 0})
    if not rally['unlocked_at']:
        rally['players'] = {k: t for k, t in rally['players'].items() if t > now - RALLY_WINDOW}
        rally['players'][player_key] = now
        if len(rally['players']) >= RALLY_GOAL:
            rally['unlocked_at'] = now
            rally['players'] = {}  # No ongoing writes needed after the cosmetic unlock.
    minute = int(now // 60)
    pace = [b for b in state.get('pace', []) if b['minute'] > minute - 60]
    if not pace or pace[-1]['minute'] != minute:
        pace.append(dict(minute=minute, damage=0, attacks=0))
    pace[-1]['damage'] += damage
    pace[-1]['attacks'] += 1
    state['pace'] = pace


def rally_view(state, now):
    rally = state.get('rally', {})
    reached = bool(rally.get('unlocked_at'))
    times = [t for t in rally.get('players', {}).values() if t > now - RALLY_WINDOW]
    return dict(goal=RALLY_GOAL, count=RALLY_GOAL if reached else len(times),
                window_seconds=RALLY_WINDOW, unlocked=reached,
                unlocked_at=rally.get('unlocked_at', 0),
                next_expiry=min(times) + RALLY_WINDOW if times else 0)


def balance_view(state, now):
    # Whole minute buckets bound the work to sixty records per view. Label the
    # estimate as approximate: attendance and selected styles can change it.
    recent = [b for b in state.get('pace', []) if b['minute'] > int(now // 60) - 60]
    elapsed = max(60, min(3600, now - state['started_at'])) if state['started_at'] else 60
    damage, hits = sum(b['damage'] for b in recent), sum(b['attacks'] for b in recent)
    enough = elapsed >= 300 and hits >= 10 and damage > 0
    rate = damage * 3600 / elapsed if enough else 0
    return dict(damage_per_hour=round(rate), sample_hits=hits, sample_seconds=round(elapsed),
                remaining_seconds=math.ceil(state['hp'] / rate * 3600) if rate else None,
                observed=bool(rate), presets=[dict(label=label, days=days,
                    hp=min(MAX_NUMBER, max(1, round(rate * 24 * days))) if rate else fallback)
                    for label, days, fallback in [('Short raid', 3, 10_000_000), ('Long raid', 5, 25_000_000), ('Epic raid', 7, 50_000_000)]])


def host_snapshot(state):
    return dict(name=state.get('settings', {}).get('name', 'Crimson Hunllef'),
                hp=state['hp'], max_hp=state['max_hp'], paused=state['paused'],
                damage=state.get('settings', {}).get('damage', 100),
                weak_damage=state.get('settings', {}).get('weak_damage', 150),
                burst_bonus=state.get('settings', {}).get('burst_bonus', 100),
                avatar=state.get('avatar_hash') or 'Original logo')


def audit(state, action, actor, before, after, now=None):
    entry = dict(action=action, actor=str(actor)[:64], at=int(time.time() if now is None else now),
                 before=copy.deepcopy(before), after=copy.deepcopy(after))
    state['admin_history'] = (state.get('admin_history', []) + [entry])[-100:]


def validate_extras(state, limit):
    households = state.get('households', {})
    if not isinstance(households, dict) or len(households) > limit:
        raise ValueError('Invalid shared connection settings.')
    for key, slots in households.items():
        if not isinstance(key, str) or not re.fullmatch(r'[a-f0-9]{64}', key) or type(slots) is not int or not 2 <= slots <= 10:
            raise ValueError('Invalid shared connection allowance.')
    rally = state.get('rally', {'players': {}, 'unlocked_at': 0})
    if not isinstance(rally, dict) or not isinstance(rally.get('players'), dict) or len(rally['players']) > RALLY_GOAL:
        raise ValueError('Invalid community rally.')
    timestamps = [rally.get('unlocked_at')]
    for key, t in rally['players'].items():
        if not isinstance(key, str) or not re.fullmatch(r'[a-f0-9]{64}', key): raise ValueError('Invalid rally player.')
        timestamps.append(t)
    if any(type(n) not in (int, float) or not 0 <= n <= 10**12 for n in timestamps):
        raise ValueError('Invalid rally time.')
    pace = state.get('pace', [])
    if not isinstance(pace, list) or len(pace) > 60:
        raise ValueError('Invalid raid pace.')
    previous = -1
    for b in pace:
        if (not isinstance(b, dict) or any(type(b.get(k)) is not int or not 0 <= b[k] <= MAX_NUMBER for k in ('minute', 'damage', 'attacks'))
                or b['minute'] <= previous): raise ValueError('Invalid raid pace bucket.')
        previous = b['minute']
    history = state.get('admin_history', [])
    if not isinstance(history, list) or len(history) > 100: raise ValueError('Invalid boss admin history.')
    for entry in history:
        if (not isinstance(entry, dict) or type(entry.get('at')) is not int or not 0 <= entry['at'] <= 10**12
                or any(not isinstance(entry.get(k), str) or len(entry[k]) > 64 for k in ('actor', 'action'))):
            raise ValueError('Invalid boss admin history entry.')
        for k in ('before', 'after'):
            if not isinstance(entry.get(k), dict) or len(entry[k]) > 12: raise ValueError('Invalid boss change summary.')
            for name, v in entry[k].items():
                if (not isinstance(name, str) or len(name) > 64 or
                    not (v is None or type(v) is bool or type(v) is int and abs(v) <= MAX_NUMBER
                         or isinstance(v, str) and len(v) <= 256)):
                    raise ValueError('Invalid boss change value.')
```

## boss_progress.py

```python
"""Private community names and eight persistent, server-earned raid badges.

Names are self-reported, not verified Shuffle identities. Records are keyed by
salted browser/network hashes; raw addresses never enter the gameplay save.
"""
import copy
import re

DAY = 86400
MAX_NUMBER = 2**53 - 1  # Exact integer range shared by Python and browser JSON.
STYLES = ('blade', 'bow', 'magic')


def username(value):
    if not isinstance(value, str) or not 1 <= len(value.strip()) <= 64 or not value.isprintable():
        raise ValueError('Enter a username of 1–64 printable characters.')
    return value.strip()


def new_profile(name, network, now, player=None):
    old = player or {}
    return dict(name=username(name), network=network, named_at=now,
                attacks=old.get('attacks', 0), active_days=old.get('active_days', 1 if old else 0),
                first_hit_at=old.get('last_attack', 0), last_day=0 if old else -1, weak_hits=0, bursts=old.get('attacks', 0) // 10,
                styles={style: 0 for style in STYLES})


def record_hit(profile, hit, now):
    if not profile['first_hit_at']:
        profile['first_hit_at'] = now
    # Personal 24-hour periods prevent a midnight click from earning two days.
    day = int(max(0, now - profile['first_hit_at']) // DAY)
    if day > profile['last_day']:
        profile['active_days'] += 1
        profile['last_day'] = day
    profile['attacks'] += 1
    profile['weak_hits'] += int(hit['weakness'])
    profile['bursts'] += int(hit['burst'])
    profile['styles'][hit['style']] += 1


def badges(player, now=0):
    hits, days = player.get('attacks', 0), player.get('active_days', 0)
    week = bool(player.get('first_hit_at')) and now - player['first_hit_at'] >= 6 * DAY and days >= 7
    goals = (
        ('first', 'First strike', 'Land your first hit.', hits, 1),
        ('burst', 'Crimson veteran', 'Trigger 10 Crimson bursts.', player.get('bursts', hits // 10), 10),
        ('weak', 'Weakness hunter', 'Match 100 random weaknesses.', player.get('weak_hits', 0), 100),
        ('arsenal', 'Full arsenal', 'Land 25 hits with each of the three styles.', min(player.get('styles', {}).get(s, 0) for s in STYLES), 25),
        ('loyal', 'Three-day crew', 'Attack in 3 different personal raid days.', days, 3),
        ('regular', 'Crimson regular', 'Attack in 5 different personal raid days.', days, 5),
        ('week', 'Weeklong guardian', 'Attack in 7 personal raid days over at least 6 full days.', min(days, 7) if week else min(days, 6), 7),
        ('legend', 'Crimson legend', 'Land 500 hits and earn Weeklong guardian.', min(hits, 500) if week else min(hits, 499), 500),
    )
    return [dict(id=key, label=label, description=description, earned=value >= target,
                 progress=min(value, target), target=target) for key, label, description, value, target in goals]


def validate_profiles(profiles, limit, households=None):
    if not isinstance(profiles, dict) or len(profiles) > limit:
        raise ValueError('Invalid community player profiles.')
    names = set()
    # Network/household fields are accepted for recovery compatibility only.
    # Multiple independent profiles may have the same legacy network value.
    for key, p in profiles.items():
        if not isinstance(key, str) or not re.fullmatch(r'[a-f0-9]{64}', key) or not isinstance(p, dict):
            raise ValueError('Invalid community player profile.')
        name = username(p.get('name'))
        network = p.get('network')
        if not isinstance(network, str) or not re.fullmatch(r'[a-f0-9]{64}', network):
            raise ValueError('Invalid private connection identifier.')
        if name.casefold() in names:
            raise ValueError('Duplicate community username.')
        names.add(name.casefold())
        if 'recovery_hash' in p and (not isinstance(p['recovery_hash'], str) or not re.fullmatch(r'[a-f0-9]{64}', p['recovery_hash'])):
            raise ValueError('Invalid private recovery digest.')
        if 'recovery_at' in p and (type(p['recovery_at']) not in (int, float) or not 0 <= p['recovery_at'] <= 10**12):
            raise ValueError('Invalid recovery timestamp.')
        for field in ('named_at', 'first_hit_at'):
            n = p.get(field)
            if type(n) not in (float, int) or not 0 <= n <= 10**12:
                raise ValueError('Invalid player timestamp.')
        for field in ('attacks', 'active_days', 'weak_hits', 'bursts', 'last_day'):
            n = p.get(field)
            if type(n) is not int or not (-1 if field == 'last_day' else 0) <= n <= MAX_NUMBER:
                raise ValueError('Invalid achievement progress.')
        if not isinstance(p.get('styles'), dict) or set(p['styles']) != set(STYLES):
            raise ValueError('Invalid style progress.')
        for n in p['styles'].values():
            if type(n) is not int or not 0 <= n <= p['attacks']:
                raise ValueError('Invalid style count.')
        if (p['weak_hits'] > p['attacks'] or p['bursts'] > p['attacks'] // 10
                or p['active_days'] > p['attacks'] or sum(p['styles'].values()) > p['attacks']):
            raise ValueError('Inconsistent achievement totals.')
    return copy.deepcopy(profiles)
```

## config.py

```python
"""One configuration path; saved race settings win after the first import."""
import os
import re
from pathlib import Path

from race_support import DEFAULT_PRIZES, canonical_site, read_json

RELEASE = "2026.09.29-player-access"
INTERVAL = 60


class Config:
    def __init__(self, root=None):
        self.root = Path(root or Path(__file__).parent).resolve()
        path = lambda name, default: Path(os.getenv(name) or self.root / default)
        self.legacy = path("ADMIN_STORE_PATH", "admin_store.json")
        self.seed = path("ADMIN_SEED_PATH", "private/admin_store.seed.json")
        self.recovery = path("RECOVERY_SEED_PATH", "private/recovery.seed.json")
        self.db_path = path("LOCAL_DATABASE_PATH", "data/redhunllef.sqlite3")
        self.state_path = path("STATE_FILE", "data/state.json")
        explicit = os.getenv("SETTINGS_PATH")
        bundled = self.root / "private/settings.json"
        private = read_json(bundled) if bundled.is_file() and not explicit else {}
        settings_path = path("SETTINGS_PATH", "settings.json")
        settings = read_json(settings_path) if settings_path.is_file() else {}
        integration_path = path("INTEGRATIONS_PATH", "integrations.json")
        integrations = read_json(integration_path) if integration_path.is_file() else {}
        defaults = {**private, **settings}
        self.credentials, self.sources = {}, {}
        for key in ("shuffle_api_key", "kick_client_id", "kick_client_secret"):
            layers = [(os.getenv(key.upper()), key.upper())]
            if key == "shuffle_api_key":
                layers.append((os.getenv("API_KEY"), "API_KEY"))
            layers += [(settings.get(key), "settings.json"), (integrations.get(key), "integrations.json"),
                       (private.get(key), "private/settings.json")]
            value, source = next(((str(v).strip(), source) for v, source in layers if v and str(v).strip()), ("", "missing"))
            self.credentials[key], self.sources[key] = value, source
        # This build deliberately uses only local JSON. Old database variables
        # cannot make startup depend on a removed service.
        self.storage_mode, self.db_url = "local", ""
        self.ignored_database_url = bool(os.getenv("DATABASE_URL"))
        self.state_key = os.getenv("APP_STATE_KEY", "redhunllef")
        if not re.fullmatch(r"[A-Za-z0-9_-]{1,64}", self.state_key):
            raise ValueError("APP_STATE_KEY must contain 1–64 letters, numbers, underscores or hyphens.")
        # Storage and web security are independent: local storage on App Platform
        # still uses production cookies, proxy handling, and the normal server.
        mode = os.getenv("APP_ENV", "production" if "PORT" in os.environ else "local")
        self.production = mode == "production"
        self.port = int(os.getenv("PORT", "8080"))
        if not 1 <= self.port <= 65535:
            raise ValueError("PORT must be between 1 and 65535.")
        self.proxy = os.getenv("TRUST_APP_PLATFORM", "0") == "1"
        self.secure_cookie = os.getenv("SESSION_COOKIE_SECURE", "always" if self.production else "auto").lower()
        self.secret = os.getenv("SECRET_KEY", "").strip()
        if self.secret and len(self.secret) < 32:
            raise ValueError("SECRET_KEY must have at least 32 characters when set.")
        self.superadmin = os.getenv("SUPERADMIN_USER", defaults.get("superadmin_user", "gingrsnaps"))
        self.bootstrap_password = os.getenv("ADMIN_BOOTSTRAP_PASS", "enok2121")
        self.endpoint = os.getenv("SHUFFLE_ENDPOINT_KIND", defaults.get("shuffle_endpoint_kind", "wager"))
        if not re.fullmatch(r"[A-Za-z0-9_-]+", self.endpoint):
            raise ValueError("SHUFFLE_ENDPOINT_KIND must be one endpoint name.")
        self.aggregation = os.getenv("SHUFFLE_AGGREGATION_MODE", defaults.get("shuffle_aggregation_mode", "sum"))
        if self.aggregation not in {"sum", "max"}:
            raise ValueError("SHUFFLE_AGGREGATION_MODE must be sum or max.")
        self.raw_fallback = str(os.getenv("ALLOW_RAW_WAGER_FALLBACK", defaults.get("allow_raw_wager_fallback", False))).lower() in {"1", "true"}
        self.limit = min(10000, max(100, int(os.getenv("FULL_LEADERBOARD_MAX", "300"))))
        site = dict(site_name="RedHunllef", race_title="RedHunllef Wager Race",
                    race_description="Your wagers. Your place. The race is on.", start_time=0, end_time=0,
                    refresh_seconds=60, leaderboard_size=15, prizes={str(k): str(v) for k, v in DEFAULT_PRIZES.items()},
                    kick_channel_slug="redhunllef", campaign_code_filter="Red", sponsor_name="Shuffle.com",
                    sponsor_url="https://shuffle.com/?r=Red", stream_url="https://kick.com/redhunllef",
                    community_name="Red Community", community_url="", responsible_gambling_url="https://www.ncpgambling.org/")
        for name in ("START_TIME", "END_TIME", "KICK_CHANNEL_SLUG", "CAMPAIGN_CODE_FILTER"):
            if name in os.environ:
                defaults[name.lower()] = int(os.environ[name]) if name.endswith("TIME") else os.environ[name]
        self.site = canonical_site(defaults, site)

    def diagnostics(self):
        return {key: {"configured": bool(value), "source": self.sources[key]} for key, value in self.credentials.items()}
```

## docs/COMMUNITY_BOSS.md

```markdown
# Community boss reference

Run `python wager_backend.py`; the game is served at `/play`. No separate process,
SQL server or external account is required. State uses `data/state.json`.

The shared boss defaults to 2,400,000 HP. Registered players attack every 30 seconds,
without daily or weekly quotas. A random shared weakness lasts ten minutes;
consecutive identical draws are valid. Defaults are 100 normal damage, 150 weakness
damage, and a 100 bonus every tenth hit. Admins can change those whole-number values.

Health never regenerates automatically. Only an explicit admin health edit or a new
raid can increase it. The percentage measures defeated HP from 0% through 100%.
Requests never supply trusted damage. Repeated request receipts return the original
hit without dealing damage twice. A lost response can therefore be retried safely.

Names are self-reported. Public leaderboards show aliases; the owner and signed-in
admins can see submitted names. The admin Top 5 contains full names. A Shuffle
spelling match does not verify an account or connection. The game does not claim
access to a Shuffle IP mapping.

Each player is identified by a persistent signed browser cookie. Shared IPv4,
IPv6, VPN, carrier and proxy addresses do not restrict how many players can join.
The same cookie keeps its saved username and cooldown when IPs change. Tabs sharing
a cookie are the same player; separate browser identities get independent cooldowns.
Game writes still require a valid cookie and CSRF token. Missing IP headers do not
block registration, recovery or attacks. No household approval or raid reset is
needed. Old network records are retained for compatibility, not used for admission.

A browser identity is not proof of a unique human; cookie deletion can create a
new player. Existing names cannot be claimed just by typing them. Use the original
browser or a valid recovery code to restore an existing profile.

A private recovery code restores the original identity after cookie loss. The
server stores a digest; the code is shown once when created. A replacement revokes
the old code. Codes need the saved secret and profile data and cannot recover a
lost server disk by themselves. They remain valid across new raids.

The eight existing badges, progress labels and week-long prerequisites are unchanged.
Badges do not cap hits. The added Red rally is a separate cosmetic community goal:
15 distinct raiders hit within a rolling ten-minute window to light the arena for
the rest of the raid. It does not change health or damage.

Admin controls require current authenticated sessions and CSRF tokens. Avatar
uploads accept validated PNG/JPG/JPEG/WebP and reject malformed/animated/oversized
images. Health and damage previews show expected effects; revision checks prevent
stale admin edits. The last 100 host actions retain actor/time/before/after details.
All private fields are excluded from public projections.

Recent activity estimates use up to sixty minute buckets. After five minutes and
ten hits with damage, admin shows approximate damage/hour and remaining duration.
Presets fill the next raid's HP input only. They do not guarantee a duration or
change the current boss automatically. Before sufficient data exists, the preset
health amounts are only starting suggestions.

Rejected requests are counted in bounded, in-memory windows. Bursts are briefly
throttled per signed browser and visible as private diagnostic flags, without automatic bans or shared-IP lockouts. Valid
eligible attacks bypass that guard and keep their regular 30-second cadence.

Screens poll every five seconds. Hidden browser tabs resume on visibility. The
server's Shuffle/Kick minute workers run independently of game polling. The only
launch script remains `wager_backend.py`.

App Platform replaces local files on redeploy/container replacement. Use the
existing manual private recovery export before a planned redeployment; progress
after the latest export can still be lost. No external backup service was added.
```

## docs/COMMUNITY_UPDATE.md

```markdown
# Community comfort update and access repair

Approved scope: suggestions 2–9. Excluded: achievement-progress redesign and
external checkpoint storage. Unlimited daily/weekly hits and the 30-second cooldown
are unchanged. `boss_progress.badges()` is unchanged from the preceding release.

| Area | Implementation |
| --- | --- |
| Identity | Existing cookie key retained during recovery; signed random recovery bearer code, saved digest, CSRF-protected POSTs, no code in URLs/logs/public feeds. |
| Shared connections | No IP admission limit; each signed browser retains its username and 30-second cooldown. Old network fields remain readable for migration. |
| Activity | Bounded minute buckets for approximate pace; bounded rolling distinct-player set for a cosmetic rally. |
| Admin history | At most 100 actor/time/before/after entries, committed with the successful game edit. |
| UI | Stable keyed lists, preserved form drafts, remembered style, safe text rendering, compact totals, exact details, reduced-motion styling. |
| Source freshness | Success time is separate from rows/content-change time; existing automatic 60-second jobs remain. |
| Abuse | Per-browser isolation, at most 4,000 short-lived request buckets and 50 temporary flags. Eligible hits and receipt retries are not throttled. No automatic bans. |
| Saves | Atomic UTF-8 JSON, OS file lock, flushed replacement, cached reads; prior local save imported without overwriting it. |

The public page remains focused on the game. Recovery controls and exact totals
are collapsed; detailed host controls stay in the authenticated admin panel.

There is no new runtime dependency. Optional browser-development checks use Node,
but deploying and running the app requires only the existing Python requirements.

The player-access repair also orders browser updates by committed revision and
discards polls started before an in-flight player write. Saving a username does
not require resetting the boss. Identity fields never come from arbitrary IP headers.
```

## docs/VALIDATION.md

```markdown
# Validation — 2026.09.29-player-access

All **132 backend tests** were validated across the suite and targeted reruns.
The initial suite passed 130; two assertions that expected the retired shared-IP
restriction were updated to test per-player cooldowns and passed on rerun. **57 DOM/interface checks**
passed, including the new shared-proxy, saved-name and delayed-response regressions.

| Area | Verified behavior |
| --- | --- |
| JSON saves | Fresh startup, retained accounts, cold restart, corrupt-file refusal, failed atomic replacement rollback, two simultaneous store instances retaining every hit. |
| Names | Retained after IP/header changes, refresh, application restart and new raid. Cookie is not silently replaced on reload. Recovery can share a network with another active player. |
| Isolation | One browser flooding rejected registrations does not stop other browsers on the same IP. Name collisions cannot claim another player. |
| Migration | Previous SQLite accounts/revision/live snapshot/raid imported exactly; old file unchanged; no SQLite created on a fresh install. |
| Recovery codes | Authenticated owner issuance, CSRF rejection, forgery and replaced-code rejection, digest-only storage, original alias/hits/badges/receipt/cooldown retained. |
| Community access | 100 concurrent browser identities register and attack through one proxy IP, then each attacks again after 30 seconds. No approvals. Same-identity simultaneous clicks still allow only one hit. |
| Unlimited hits | Repeated eligible hits accepted beyond previous daily counts; rejected-request throttle does not block an eligible hit. Existing week-long gameplay/achievement tests pass. |
| Rally/estimates | Distinct rolling-window players, repeat-player deduplication, window expiry, next-raid reset, cosmetic unlock, no automatic HP/damage changes. |
| Admin edits | Private persistent actor/before/after history, existing avatar/name/HP/damage permissions and stale revision checks. |
| Interface | Identity collapse/edit, safe code recovery, remembered style, rally display, exact previews, presets without submission, private history clearing on expiry, saved names winning over stale polls, and attack controls pausing during profile writes. |
| Status | Five-second boss polling, 60-second provider polling, distinct source success/change timestamps, dynamic boss victory name, ETag reuse and reconnect behavior. |
| Existing features | Native login, race date publication, provider envelopes, safe failure responses, Code Red Top 100, public masking, uploads and recovery export. |

The original provider configuration, account seed, PNG and ICO are preserved byte
for byte. The badge calculation function is preserved unchanged; #1 was excluded.
No remote checkpoint feature or external SQL service was added; #10 was excluded.

Validation uses synthetic provider responses and disposable local saves. It did
not contact the live Shuffle/Kick accounts or deploy to DigitalOcean. This Linux
workspace ran Python 3.12; Windows/Python 3.14 was not executed natively. An encoding
regression test simulates the earlier Windows text-decoding failure. Browser checks
use rendered templates in jsdom; native Chromium was unavailable, so no new native
visual-rendering claim is made.

The extracted ZIP startup checks and package integrity results are recorded during
packaging. The code is shipped with its tests for repeatable verification.
```

## integrations.py

```python
"""Official provider requests with bounded waits and secret-free failures."""
from datetime import datetime, timezone
from decimal import Decimal
from email.utils import parsedate_to_datetime
import json
import threading
import time
from urllib.parse import quote

import requests


class ProviderError(RuntimeError):
    def __init__(self, message, *, retry_after=0, status=None):
        super().__init__(message)
        self.retry_after, self.status = retry_after, status


def retry_delay(value):
    try:
        return max(0, int(value))
    except (ValueError, TypeError):
        try:
            stamp = parsedate_to_datetime(str(value))
            return max(0, int((stamp - datetime.now(timezone.utc)).total_seconds()))
        except (ValueError, TypeError, OverflowError):
            return 0


class Providers:
    def __init__(self, config):
        self.config, self.local = config, threading.local()
        self.token, self.token_until = "", 0

    def request(self, method, url, service, **kwargs):
        self.local.http_status = None
        # Each background thread owns its session; cookies/auth do not cross.
        if not hasattr(self.local, "session"):
            self.local.session = requests.Session()
            self.local.session.headers.update(Accept="application/json", **{"User-Agent":"RedHunllef/9"})
        try:
            # Redirects could leak a key in a URL or Authorization header. Only
            # the configured official endpoint is allowed to handle the request.
            with self.local.session.request(method, url, timeout=(5, 20), allow_redirects=False, stream=True, **kwargs) as response:
                code = response.status_code
                self.local.http_status = code
                if code == 429 or code >= 500:
                    raise ProviderError(f"{service} returned HTTP {code}; retrying automatically.",
                                        retry_after=retry_delay(response.headers.get("Retry-After")), status=code)
                if code in (401, 403):
                    raise ProviderError(f"{service} rejected the credentials or access permissions (HTTP {code}).", status=code)
                if not 200 <= code < 300:
                    message = "Shuffle rejected the saved race window; check its dates and affiliate configuration." if service == "Shuffle" and code == 400 else f"{service} returned HTTP {code}."
                    raise ProviderError(message, status=code)
                body = bytearray()
                deadline = time.monotonic() + 30
                for chunk in response.iter_content(65536):
                    body.extend(chunk)
                    if len(body) > 8 * 1024 * 1024 or time.monotonic() > deadline:
                        raise ProviderError(f"{service} response exceeded its size or time allowance.")
                try:
                    return json.loads(body, parse_float=Decimal)
                except (ValueError, UnicodeDecodeError):
                    raise ProviderError(f"{service} returned invalid JSON.") from None
        except requests.Timeout:
            raise ProviderError(f"{service} timed out; previous results are retained and checks continue.") from None
        except requests.RequestException:
            raise ProviderError(f"{service} could not be reached; check outbound connectivity.") from None

    def shuffle(self, site):
        key = self.config.credentials["shuffle_api_key"]
        if not key:
            raise ProviderError("Shuffle API key is missing. Add SHUFFLE_API_KEY and restart.")
        start, end = site["start_time"], min(site["end_time"], int(time.time()))
        if not 0 < start < end:
            raise ProviderError("The race does not have an active or completed date window.")
        data = self.request("GET", "https://affiliate.shuffle.com/" + self.config.endpoint + "/" + quote(key, safe=""),
                            "Shuffle", params={"startTime": start, "endTime": end})
        rows = data if isinstance(data, list) else next((data[k] for k in ("data", "results", "leaderboard", "users", "items")
                    if isinstance(data, dict) and isinstance(data.get(k), list)), None)
        if rows is None or len(rows) > 10000:
            raise ProviderError("Shuffle returned an unsupported leaderboard format or over 10,000 source records.")
        return rows

    def kick(self, site):
        keys = self.config.credentials
        if not keys["kick_client_id"] or not keys["kick_client_secret"]:
            raise ProviderError("Kick client credentials are missing. Configure them and restart.")
        for attempt in range(2):
            if attempt or not self.token or time.time() >= self.token_until:
                data = self.request("POST", "https://id.kick.com/oauth/token", "Kick authorization",
                                    data={"grant_type":"client_credentials", "client_id":keys["kick_client_id"], "client_secret":keys["kick_client_secret"]})
                if not isinstance(data, dict) or not isinstance(data.get("access_token"), str):
                    raise ProviderError("Kick did not return a valid app access token.")
                self.token = data["access_token"]
                try:
                    self.token_until = time.time() + max(1, int(data.get("expires_in", 3600)) - 60)
                except (TypeError, ValueError):
                    raise ProviderError("Kick returned an invalid token expiry.") from None
            try:
                data = self.request("GET", "https://api.kick.com/public/v1/channels", "Kick",
                                    params={"slug":site["kick_channel_slug"]}, headers={"Authorization":"Bearer " + self.token})
                break
            except ProviderError as exc:
                if exc.status != 401 or attempt:
                    raise
        rows = data.get("data") if isinstance(data, dict) else None
        channel = next((r for r in rows or [] if isinstance(r, dict) and str(r.get("slug", "")).casefold() == site["kick_channel_slug"].casefold()), None)
        if channel is None:
            raise ProviderError("Kick did not return the configured channel.")
        stream = channel.get("stream")
        if not isinstance(stream, dict) or not isinstance(stream.get("is_live"), bool):
            raise ProviderError("Kick did not provide a valid live status.")
        viewers = stream.get("viewer_count")
        return dict(live=stream["is_live"], title=str(channel.get("stream_title") or stream.get("title") or "")[:240],
                    viewers=int(viewers) if isinstance(viewers, (int, Decimal)) and not isinstance(viewers, bool) and viewers > 0 and stream["is_live"] else None,
                    category=str((channel.get("category") or {}).get("name", ""))[:120], channel=site["kick_channel_slug"])

    def close(self):
        if hasattr(self.local, "session"):
            self.local.session.close()

    def last_http_status(self):
        return getattr(self.local, "http_status", None)
```

## presentation.py

```python
"""Small view models for change review and private recovery status."""
import re

from boss_progress import MAX_NUMBER
from race import token
from race_support import fmt_et, money

LABELS = {
    'start_time': 'Starts · Eastern Time', 'end_time': 'Ends · Eastern Time',
    'site_name': 'Website name', 'race_title': 'Race title',
    'race_description': 'Description', 'kick_channel_slug': 'Kick channel',
    'campaign_code_filter': 'Campaign filter', 'stream_url': 'Livestream link',
    'sponsor_name': 'Sponsor name', 'sponsor_url': 'Sponsor link',
    'community_name': 'Community label', 'community_url': 'Community link',
    'responsible_gambling_url': 'Responsible play link',
}


def changes(before, after):
    result = []
    for key, label in LABELS.items():
        old, new = before.get(key), after.get(key)
        if old != new:
            display = fmt_et if key.endswith('_time') else lambda v: str(v or 'Not set')
            result.append(dict(label=label, before=display(old), after=display(new)))
    for rank in range(1, 16):
        old, new = before.get('prizes', {}).get(str(rank), '0'), after.get('prizes', {}).get(str(rank), '0')
        if money(old) != money(new):
            result.append(dict(label=f'Place {rank} prize', before=money(old), after=money(new)))
    return result


def admin_fingerprint(admin):
    # Exclude migration fields and background timestamps. Exporting a checkpoint
    # never increments the settings revision or invalidates an open admin form.
    return token({key: admin.get(key) for key in (
        'users', 'secret_key', 'site_settings', 'overrides', 'race_history', 'banned_ips', 'audit_log')})


def export_marker(admin, snapshot, boss, generated_at):
    return dict(generated_at=generated_at, admin_token=admin_fingerprint(admin),
                standings_token=token(snapshot['last_top15']), raid_id=boss['id'],
                boss_version=boss['version'], attacks=boss['total_attacks'], damage=boss['total_damage'])


def valid_marker(value):
    """Ignore damaged optional metadata without discarding recovered game data."""
    if not isinstance(value, dict):
        return None
    for key in ('generated_at', 'boss_version', 'attacks', 'damage'):
        if type(value.get(key)) is not int or not 0 <= value[key] <= (10**12 if key == 'generated_at' else MAX_NUMBER):
            return None
    for key, length in (('admin_token', 20), ('standings_token', 20), ('raid_id', 32)):
        if not isinstance(value.get(key), str) or not re.fullmatch(r'[a-f0-9]{%d}' % length, value[key]):
            return None
    return {key: value[key] for key in ('generated_at', 'boss_version', 'attacks', 'damage',
                                       'admin_token', 'standings_token', 'raid_id')}


def checkpoint_status(marker, admin, rows, boss):
    marker = valid_marker(marker)
    if not marker:
        return dict(generated_at=0, label='No recovery export recorded', changes=True,
                    details='Generate a private recovery file to protect this checkpoint.')
    new_raid = marker.get('raid_id') != boss['raid_id']
    attacks = max(0, boss['total_attacks'] - marker.get('attacks', 0)) if not new_raid else boss['total_attacks']
    damage = max(0, boss['total_damage'] - marker.get('damage', 0)) if not new_raid else boss['total_damage']
    changed = admin_fingerprint(admin) != marker.get('admin_token')
    standings = token(rows[:15]) != marker.get('standings_token')
    raid_changed = new_raid or boss['version'] != marker.get('boss_version')
    notes = ([f'{attacks:,} new hits · {damage:,} damage'] if attacks else [])
    if new_raid: notes.append('a different raid is active')
    elif raid_changed and not attacks: notes.append('raid controls changed')
    if changed: notes.append('account or race settings changed')
    if standings: notes.append('standings changed')
    return dict(generated_at=marker.get('generated_at', 0), changes=changed or standings or raid_changed,
                label='Changes since last export' if notes else 'Checkpoint matches current progress',
                details='; '.join(notes) or 'No new saved progress since this export.',
                attacks=attacks, damage=damage, new_raid=new_raid)
```

## private/admin_store.seed.json

```json
{
  "version": 6,
  "secret_key": "0f471b557fe98828d7ae45022198fe6b7f32d2f5eaa43f0d8dd2e87bd8ef7d57",
  "users": {
    "gingrsnaps": {
      "pw_hash": "scrypt:32768:8:1$cspkSfDFuHU92tds$bedc2c1e4ec355027fcbd0ed9857a341d0179d0a5201edc8a2549a2e9c50112f78a28fa81a65a7b7f19089defd85a0dda51282eb2069bb31f5d992b7e9961aac",
      "created_at": 1786043027,
      "created_by": "bootstrap"
    }
  },
  "overrides": {},
  "site_settings": {
    "site_name": "RedHunllef",
    "race_title": "RedHunllef Wager Race",
    "race_description": "Track the top weighted wagerers for RedHunllef's active race.",
    "start_time": 1785880800,
    "end_time": 1786485600,
    "refresh_seconds": 60,
    "leaderboard_size": 15,
    "prizes": {
      "1": 1800.0,
      "2": 1200.0,
      "3": 800.0,
      "4": 450.0,
      "5": 200.0,
      "6": 150.0,
      "7": 90.0,
      "8": 80.0,
      "9": 70.0,
      "10": 60.0,
      "11": 20.0,
      "12": 20.0,
      "13": 20.0,
      "14": 20.0,
      "15": 20.0
    },
    "kick_channel_slug": "redhunllef",
    "campaign_code_filter": "Red",
    "sponsor_name": "Shuffle.com",
    "sponsor_url": "https://shuffle.com/?r=Red",
    "stream_url": "https://kick.com/redhunllef",
    "community_name": "Discord",
    "community_url": "https://discord.gg/nhCbCZQEMK",
    "responsible_gambling_url": "https://www.ncpgambling.org/responsible-gambling/"
  },
  "audit_log": [
    {
      "ts": 1786043053,
      "ts_et": "Aug 06, 2026 07:04:13 PM UTC",
      "admin_user": "gingrsnaps",
      "ip": "10.102.15.72",
      "action": "login_ok",
      "detail": {
        "user": "gingrsnaps"
      }
    }
  ],
  "banned_ips": [],
  "health": {
    "last_refresh_ok": true,
    "last_refresh_et": "Aug 06, 2026 07:03:49 PM UTC",
    "last_error": null,
    "last_api_ms": 1682,
    "last_source": "weighted_range",
    "last_row_count": 765,
    "last_weighted_row_count": 765,
    "last_skipped_missing_weighted": 0,
    "aggregation_mode": "sum",
    "endpoint_kind": "wager"
  },
  "leaderboard_snapshots": {
    "prev_top15": [],
    "last_top15": [
      {
        "rank": 1,
        "username": "swisscheez",
        "weighted_wager": 119459.63509594648,
        "wager": "$119,459.64",
        "raw_wager": 130311.9709619956,
        "raw_wager_str": "$130,311.97",
        "source": "shuffle",
        "row_count": 1
      },
      {
        "rank": 2,
        "username": "RedLovesMe",
        "weighted_wager": 24707.208233709047,
        "wager": "$24,707.21",
        "raw_wager": 42293.792873268765,
        "raw_wager_str": "$42,293.79",
        "source": "shuffle",
        "row_count": 1
      },
      {
        "rank": 3,
        "username": "lightningmcqueen",
        "weighted_wager": 18496.683703336937,
        "wager": "$18,496.68",
        "raw_wager": 21542.298069083663,
        "raw_wager_str": "$21,542.30",
        "source": "shuffle",
        "row_count": 1
      },
      {
        "rank": 4,
        "username": "NeverEnoughllef",
        "weighted_wager": 4418.297924537552,
        "wager": "$4,418.30",
        "raw_wager": 5374.578288447698,
        "raw_wager_str": "$5,374.58",
        "source": "shuffle",
        "row_count": 1
      },
      {
        "rank": 5,
        "username": "ClavicsRedsSlave",
        "weighted_wager": 2517.4193723568037,
        "wager": "$2,517.42",
        "raw_wager": 6162.370911998532,
        "raw_wager_str": "$6,162.37",
        "source": "shuffle",
        "row_count": 1
      },
      {
        "rank": 6,
        "username": "chalkeater",
        "weighted_wager": 2419.574141415062,
        "wager": "$2,419.57",
        "raw_wager": 3417.150372848572,
        "raw_wager_str": "$3,417.15",
        "source": "shuffle",
        "row_count": 1
      },
      {
        "rank": 7,
        "username": "WetBoxOfLemons",
        "weighted_wager": 2280.631387650379,
        "wager": "$2,280.63",
        "raw_wager": 5238.313876503828,
        "raw_wager_str": "$5,238.31",
        "source": "shuffle",
        "row_count": 1
      },
      {
        "rank": 8,
        "username": "Nathanfr",
        "weighted_wager": 1627.8904496808987,
        "wager": "$1,627.89",
        "raw_wager": 2267.1644968089986,
        "raw_wager_str": "$2,267.16",
        "source": "shuffle",
        "row_count": 1
      },
      {
        "rank": 9,
        "username": "sleepyagain",
        "weighted_wager": 1241.7057630137851,
        "wager": "$1,241.71",
        "raw_wager": 1246.710083791074,
        "raw_wager_str": "$1,246.71",
        "source": "shuffle",
        "row_count": 1
      },
      {
        "rank": 10,
        "username": "Geoghraphy",
        "weighted_wager": 1166.06981698937,
        "wager": "$1,166.07",
        "raw_wager": 1954.7901524132,
        "raw_wager_str": "$1,954.79",
        "source": "shuffle",
        "row_count": 1
      },
      {
        "rank": 11,
        "username": "SupraboigameZz",
        "weighted_wager": 938.4793928362079,
        "wager": "$938.48",
        "raw_wager": 6114.410885837267,
        "raw_wager_str": "$6,114.41",
        "source": "shuffle",
        "row_count": 1
      },
      {
        "rank": 12,
        "username": "IrmelaChinaMan",
        "weighted_wager": 552.96779330065,
        "wager": "$552.97",
        "raw_wager": 687.6779330065,
        "raw_wager_str": "$687.68",
        "source": "shuffle",
        "row_count": 1
      },
      {
        "rank": 13,
        "username": "MixWan",
        "weighted_wager": 446.75887090376773,
        "wager": "$446.76",
        "raw_wager": 759.6830222636072,
        "raw_wager_str": "$759.68",
        "source": "shuffle",
        "row_count": 1
      },
      {
        "rank": 14,
        "username": "infinityz",
        "weighted_wager": 405.1713445673372,
        "wager": "$405.17",
        "raw_wager": 436.39835618060715,
        "raw_wager_str": "$436.40",
        "source": "shuffle",
        "row_count": 1
      },
      {
        "rank": 15,
        "username": "nyqlcs2",
        "weighted_wager": 370.951585070083,
        "wager": "$370.95",
        "raw_wager": 439.9866247215001,
        "raw_wager_str": "$439.99",
        "source": "shuffle",
        "row_count": 1
      }
    ],
    "updated_at": 1786043029
  },
  "updated_at": 1786043053
}
```

## private/settings.json

```json
{
  "port": 8080,
  "secret_key": "0b538bc33b89488aac36aab4a797fc9791b4ad952500d099348c4f3bef2eec87",
  "session_cookie_secure": "auto",
  "admin_bootstrap_user": "gingrsnaps",
  "superadmin_user": "gingrsnaps",
  "admin_bootstrap_pass": "enok2121",
  "reset_admin_store_on_start": false,
  "reset_bootstrap_password_on_start": false,
  "shuffle_api_key": "f45f746d-b021-494d-b9b6-b47628ee5cc9",
  "shuffle_endpoint_kind": "wager",
  "shuffle_aggregation_mode": "sum",
  "allow_raw_wager_fallback": false,
  "campaign_code_filter": "Red",
  "start_time": 1787090400,
  "end_time": 1787695200,
  "refresh_seconds": 60,
  "leaderboard_size": 15,
  "full_leaderboard_max": 300,
  "prizes": {
    "1": 1800,
    "2": 1200,
    "3": 800,
    "4": 450,
    "5": 200,
    "6": 150,
    "7": 90,
    "8": 80,
    "9": 70,
    "10": 60,
    "11": 20,
    "12": 20,
    "13": 20,
    "14": 20,
    "15": 20
  },
  "kick_channel_slug": "redhunllef",
  "kick_client_id": "01K39PNSMPVX2PS4EEJ2K69EVF",
  "kick_client_secret": "47970da4c8790427e09eaebd1b7c8d522ef233c54bbd896514c7f562c66ca74e",
  "kick_status_ttl": 30,
  "kick_channel_ttl": 86400,
  "proxy_fix_x_for": 1,
  "proxy_fix_x_proto": 1,
  "proxy_fix_x_host": 1,
  "proxy_fix_x_port": 1,
  "proxy_fix_x_prefix": 0,
  "site_name": "RedHunllef",
  "race_title": "RedHunllef Wager Race",
  "race_description": "Track the top weighted wagerers for RedHunllef's active race.",
  "sponsor_name": "Shuffle.com",
  "sponsor_url": "https://shuffle.com/?r=Red",
  "stream_url": "https://kick.com/redhunllef",
  "community_name": "Discord",
  "community_url": "https://discord.gg/nhCbCZQEMK",
  "responsible_gambling_url": "https://www.ncpgambling.org/responsible-gambling/",
  "repair_bootstrap_login_on_upgrade": true
}
```

## race.py

```python
"""Pure race calculations: exact decimal rankings and one public projection."""
from decimal import Decimal, localcontext
import hashlib
import json
import time

from race_support import decimal_amount, money, race_key

NAMES = ("username", "displayName", "userName", "player", "name")
WEIGHTED = ("weightedWagerAmount", "weightedWager", "weightedAmount", "wagerWeighted")
RAW = ("wagerAmount", "totalWagered", "wageredAmount", "rawWagerAmount")
CAMPAIGN = ("campaignCode", "campaign", "code", "referralCode", "affiliateCode")


def first(row, keys):
    return next((row[k] for k in keys if row.get(k) is not None), None)


def phase(site, now=None):
    now = time.time() if now is None else now
    start, end = site["start_time"], site["end_time"]
    return "unconfigured" if not start or end <= start else "upcoming" if now < start else "ended" if now >= end else "active"


def token(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(",", ":")).encode()).hexdigest()[:20]


def normalize(rows, site, raw_fallback=False):
    accepted, red, rejected, missing_campaign = [], [], {}, 0
    for row in rows:
        reason = None
        if not isinstance(row, dict):
            reason = "invalid record"
        else:
            name, weighted, raw, campaign = first(row, NAMES), first(row, WEIGHTED), first(row, RAW), first(row, CAMPAIGN)
            campaign = None if campaign is None else str(campaign).strip().casefold()
            if not isinstance(name, str) or not name.strip() or len(name) > 64:
                reason = "missing or invalid username"
            elif weighted is None and not raw_fallback:
                reason = "missing weighted amount"
            else:
                try:
                    amount = decimal_amount(raw if weighted is None else weighted)
                except ValueError:
                    reason = "invalid weighted amount"
                if reason is None:
                    raw_invalid = False
                    try:
                        raw_amount = None if raw is None else str(decimal_amount(raw))
                    except ValueError:
                        raw_amount, raw_invalid = None, True
                    item = dict(username=name.strip(), weighted=str(amount), raw=raw_amount, raw_invalid=raw_invalid, row_count=1)
                    if campaign == "red":
                        red.append(item)
                    if campaign is None:
                        missing_campaign += 1
                    expected = site.get("campaign_code_filter", "").strip().casefold()
                    if not expected or campaign is None or campaign == expected:
                        accepted.append(item)
                    else:
                        reason = "other campaign"
        if reason:
            rejected[reason] = rejected.get(reason, 0) + 1
    invalid = sum(v for k, v in rejected.items() if k != "other campaign")
    if invalid and not accepted:
        raise ValueError("Shuffle returned no usable race records. Previous results are retained.")
    warning = f"{invalid} incomplete source record(s) skipped; rankings may be incomplete." if invalid else ""
    if any(row["raw_invalid"] for row in accepted):
        warning += " Some raw totals are unavailable; valid weighted totals still update."
    return dict(source=accepted, red_source=red, rejected=rejected, missing_campaign=missing_campaign,
                received=len(rows), accepted=len(accepted), warning=warning.strip())


def aggregate(rows, mode="sum"):
    result = {}
    for row in rows:
        name = row["username"]
        if name not in result:
            result[name] = dict(row)
            continue
        old = result[name]
        old["row_count"] += row.get("row_count", 1)
        old["raw_invalid"] = old.get("raw_invalid", False) or row.get("raw_invalid", False)
        for key in ("weighted", "raw"):
            if row.get(key) is not None:
                with localcontext() as ctx:
                    ctx.prec = 60
                    a, b = decimal_amount(old.get(key) or 0), decimal_amount(row[key])
                    old[key] = str(max(a, b) if mode == "max" else a + b)
    for row in result.values():
        if row.get("raw_invalid"):
            row["raw"] = None
    return result


def rank(source, overrides, mode="sum", limit=300):
    values = aggregate(source, mode)
    for name in overrides:
        values.setdefault(name, dict(username=name, weighted=None, raw=None, row_count=1))
    ordered = sorted(values.values(), key=lambda r: (-decimal_amount(overrides.get(r["username"], r["weighted"]) or 0), r["username"].casefold(), r["username"]))
    ranked, edits, count = [], [], 0
    for row in ordered:
        original = row["weighted"]
        amount = overrides.get(row["username"], original) or "0"
        qualifies = decimal_amount(amount) >= Decimal("0.01")
        count += int(qualifies)
        item = dict(rank=count if qualifies else None, username=row["username"], weighted_wager=amount,
                    wager=money(amount), original_weighted_wager=original, original_weighted_str=money(original),
                    raw_wager=row["raw"], raw_wager_str=money(row["raw"]), row_count=row.get("row_count", 1),
                    source="override" if row["username"] in overrides else "shuffle")
        if qualifies and len(ranked) < limit:
            ranked.append(item)
        if item["source"] == "override":
            edits.append(item)
    return ranked, edits, count


def empty(site):
    return dict(key=race_key(site), source=[], red_source=[], rows=[], edits=[], red=[], red_total=0, count=0,
                updated_at=0, attempt_at=0, ok=None, error="", warning="", received=0, accepted=0,
                rejected={}, missing_campaign=0, previous_top=[], snapshot_only=False)


def calculate(snapshot, admin, config):
    result = dict(snapshot)
    site = admin["site_settings"]
    rows, edits, count = rank(result["source"], admin["overrides"], config.aggregation, config.limit)
    # Code Red includes raw wagerers with zero weighted contribution, too.
    red = aggregate(result.get("red_source", []), config.aggregation)
    red = [r for r in red.values() if max(decimal_amount(r["weighted"]), decimal_amount(r.get("raw") or 0)) >= Decimal("0.01")]
    red.sort(key=lambda r: (-decimal_amount(r["weighted"]), r["username"].casefold(), r["username"]))
    result.update(rows=rows, edits=edits, count=count,
                  red=[dict(username=r["username"], weighted=money(r["weighted"]), raw=money(r["raw"])) for r in red[:100]], red_total=len(red))
    if phase(site) in {"upcoming", "unconfigured"}:
        result.update(rows=[], red=[], red_total=0, count=0)
        result["edits"] = [{**r, "rank": None} for r in edits]
    result["revision"] = token([race_key(site), result["rows"], result["edits"], result["red"], result.get("warning")])
    return result


def freshness(snapshot):
    stamp = snapshot.get("updated_at", 0)
    stale = bool(snapshot.get("snapshot_only") or snapshot.get("error") or (stamp and time.time() - stamp > 180))
    state = "delayed" if stale else "waiting" if not stamp else "partial" if snapshot.get("warning") else "current"
    return dict(state=state, updated_at=stamp, attempt_at=snapshot.get("attempt_at", 0),
                label={"delayed":"Updates delayed", "waiting":"Waiting for source data", "partial":"Updated with incomplete data", "current":"Up to date"}[state],
                warning=snapshot.get("warning", ""), error=snapshot.get("error", ""))
```

## race_support.py

```python
"""Pure validation, Eastern Time conversion, and safe JSON file operations.

This module has no Flask state and makes no network requests. Decimal values
remain exact until they are formatted; persistent amounts use decimal strings.
"""
from __future__ import annotations

import hashlib
import json
import re
import time
from datetime import datetime, timezone
from decimal import Decimal, InvalidOperation
from pathlib import Path
from urllib.parse import urlsplit
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

try:
    EASTERN = ZoneInfo("America/New_York")
except ZoneInfoNotFoundError as exc:
    raise RuntimeError("Eastern Time data is missing. Install requirements.txt, including tzdata.") from exc

STORE_VERSION = 7
DEFAULT_PRIZES = dict(enumerate(
    [1800, 1200, 800, 450, 200, 150, 90, 80, 70, 60, 20, 20, 20, 20, 20], 1
))
WEIGHTING_RULES = [
    {"range": "RTP ≤ 98%", "counts": "100% counts"},
    {"range": "98% < RTP < 99%", "counts": "50% counts"},
    {"range": "RTP ≥ 99%", "counts": "10% counts"},
]
TEXT_LIMITS = {
    "site_name": 60, "race_title": 100, "race_description": 240,
    "sponsor_name": 60, "community_name": 60, "campaign_code_filter": 64,
}
URL_FIELDS = ("sponsor_url", "stream_url", "community_url", "responsible_gambling_url")
OPTIONAL_URLS = {"community_url", "responsible_gambling_url"}
DECIMAL_PATTERN = re.compile(r"^\+?(?:\d+(?:\.\d*)?|\.\d+)(?:[eE][+-]?\d+)?$")
MONEY_PATTERN = re.compile(r"^\$?\s*(?:\d+|\d{1,3}(?:,\d{3})+)(?:\.\d{1,2})?$")


def decimal_amount(value, *, limit=Decimal("1000000000000000")) -> Decimal:
    """Reject malformed, negative, non-finite, or excessive API amounts."""
    if isinstance(value, bool) or value is None:
        raise ValueError("An amount must be a non-negative number.")
    text = str(value).strip()
    # Legacy snapshots may contain formatted amounts, but arbitrary text must
    # never be stripped into a seemingly valid financial value.
    if "$" in text or "," in text:
        if not MONEY_PATTERN.fullmatch(text):
            raise ValueError("Invalid formatted amount.")
        text = text.replace("$", "").replace(",", "").strip()
    if not DECIMAL_PATTERN.fullmatch(text):
        raise ValueError("Invalid numeric amount.")
    try:
        amount = Decimal(text)
    except InvalidOperation as exc:
        raise ValueError("Invalid numeric amount.") from exc
    if not amount.is_finite() or amount < 0 or amount > limit:
        raise ValueError("Amount is outside the allowed range.")
    return amount


def money_input(value) -> Decimal:
    text = str(value or "").strip()
    if not MONEY_PATTERN.fullmatch(text):
        raise ValueError("Use a non-negative amount such as 25000 or $25,000.00.")
    return decimal_amount(text, limit=Decimal("1000000000000"))


def money(value) -> str:
    if value is None:
        return "—"
    try:
        return "$" + format(decimal_amount(value), ",.2f")
    except ValueError:
        return "—"


def integer(value, default=0) -> int:
    try:
        if isinstance(value, bool):
            return default
        return int(value)
    except (TypeError, ValueError, OverflowError):
        return default


def valid_url(value, *, allow_blank=False) -> bool:
    text = str(value or "").strip()
    if not text:
        return allow_blank
    if len(text) > 2048 or any(ord(c) < 33 for c in text) or "\\" in text:
        return False
    try:
        parsed = urlsplit(text)
        _ = parsed.port  # Validate malformed/out-of-range ports as well.
        return (parsed.scheme in {"http", "https"} and bool(parsed.hostname)
                and not parsed.username and not parsed.password)
    except ValueError:
        return False


def fmt_et(epoch) -> str:
    if not epoch:
        return "Not configured"
    try:
        return datetime.fromtimestamp(int(epoch), EASTERN).strftime("%b %d, %Y · %I:%M %p %Z")
    except (ValueError, OSError, OverflowError, TypeError):
        return "Invalid date"


def local_input(epoch) -> str:
    return datetime.fromtimestamp(int(epoch), EASTERN).strftime("%Y-%m-%dT%H:%M") if epoch else ""


def eastern_epoch(value) -> int:
    """Reject nonexistent and ambiguous DST times instead of guessing an hour."""
    try:
        naive = datetime.strptime(str(value), "%Y-%m-%dT%H:%M")
    except (ValueError, TypeError) as exc:
        raise ValueError("Choose a valid date and time.") from exc
    if not 1970 <= naive.year <= 2099:
        raise ValueError("Choose a year between 1970 and 2099.")
    candidates = set()
    for fold in (0, 1):
        aware = naive.replace(tzinfo=EASTERN, fold=fold)
        epoch = int(aware.timestamp())
        if datetime.fromtimestamp(epoch, EASTERN).replace(tzinfo=None) == naive:
            candidates.add(epoch)
    if not candidates:
        raise ValueError("This Eastern Time does not exist because the clocks move forward. Choose another time.")
    if len(candidates) > 1:
        raise ValueError("This Eastern Time occurs twice when the clocks move back. Choose a time outside the repeated hour.")
    return candidates.pop()


def race_key(site) -> str:
    """The affiliate window defines a race; cosmetic edits do not."""
    identity = [integer(site.get("start_time")), integer(site.get("end_time")),
                str(site.get("campaign_code_filter") or "").strip().casefold()]
    return hashlib.sha256(json.dumps(identity).encode()).hexdigest()[:24]


def empty_snapshots(key) -> dict:
    return {"race_key": key, "last_top15": [], "prev_top15": [], "updated_at": None}


def validate_site(site) -> dict:
    """Return field errors; reused by normal saves and backup restoration."""
    errors = {}
    for key, maximum in TEXT_LIMITS.items():
        value = site.get(key)
        if not isinstance(value, str) or len(value) > maximum:
            errors[key] = "Use text up to " + str(maximum) + " characters."
    for key in ("site_name", "race_title", "sponsor_name"):
        if not str(site.get(key) or "").strip():
            errors[key] = "This field is required."
    start, end = integer(site.get("start_time"), -1), integer(site.get("end_time"), -1)
    if not ((start == 0 and end == 0) or (0 < start < end <= 4102444799)):
        errors["end_et"] = "The end must be after the start, within the supported date range."
    for key in ("start_time", "end_time"):
        if isinstance(site.get(key), bool) or not isinstance(site.get(key), int):
            errors["end_et"] = "Race timestamps must be whole epoch seconds."
    if integer(site.get("refresh_seconds")) != 60:
        errors["refresh_seconds"] = "Automatic updates run every 60 seconds."
    if not re.fullmatch(r"[a-z0-9_-]{2,25}", str(site.get("kick_channel_slug") or "")):
        errors["kick_channel_slug"] = "Use a Kick channel name of 2–25 letters, numbers, underscores, or hyphens."
    for key in URL_FIELDS:
        if not valid_url(site.get(key), allow_blank=key in OPTIONAL_URLS):
            errors[key] = "Enter a complete http or https link without embedded credentials."
    prizes = site.get("prizes")
    if not isinstance(prizes, dict) or set(prizes) != {str(n) for n in range(1, 16)}:
        errors["prizes"] = "Include all 15 placement prizes."
    else:
        for rank, amount in prizes.items():
            try:
                number = money_input(str(amount))
                if number.as_tuple().exponent < -2:
                    raise ValueError("Use at most two decimal places.")
            except ValueError as exc:
                errors["prize_" + rank] = str(exc)
    return errors


def canonical_site(source, defaults) -> dict:
    """Fill legacy missing fields without changing saved race choices."""
    clean = dict(defaults)
    clean.update({k: source[k] for k in defaults if k in source})
    clean["leaderboard_size"] = 15
    # Old saved intervals migrate to the required cadence; race dates and
    # financial values retain their saved meanings.
    clean["refresh_seconds"] = 60
    raw = clean.get("prizes")
    raw = raw if isinstance(raw, dict) else {}
    clean["prizes"] = {
        str(n): str(decimal_amount(raw.get(str(n), DEFAULT_PRIZES[n])))
        for n in range(1, 16)
    }
    return clean


def clean_snapshots(snapshots, key) -> dict:
    """Validate every restored row before it can reach a cache or template."""
    if not isinstance(snapshots, dict):
        raise ValueError("Leaderboard snapshots must be an object.")
    if snapshots.get("race_key", key) != key:
        raise ValueError("Snapshot race does not match its schedule.")
    result = empty_snapshots(key)
    for field in ("last_top15", "prev_top15"):
        rows = snapshots.get(field, [])
        if not isinstance(rows, list) or len(rows) > 15:
            raise ValueError("Each saved leaderboard must contain at most 15 rows.")
        ranks, names = set(), set()
        for row in rows:
            if not isinstance(row, dict):
                raise ValueError("Every snapshot entry must be an object.")
            rank = row.get("rank")
            username = row.get("username")
            if (isinstance(rank, bool) or not isinstance(rank, int) or not 1 <= rank <= 15
                    or rank in ranks or not isinstance(username, str)
                    or not username.strip() or len(username) > 128 or username in names):
                raise ValueError("Snapshot ranks or usernames are invalid or duplicated.")
            ranks.add(rank)
            names.add(username)
            weighted = decimal_amount(row.get("weighted_wager", row.get("wager")))
            raw = row.get("raw_wager")
            # Older stores did not always retain the API total beneath an
            # override. Unknown is more accurate than inventing an original.
            base = row.get("original_weighted_wager", None if row.get("source") == "override" else weighted)
            original = None if base is None else str(decimal_amount(base))
            clean = {
                "rank": rank, "username": username.strip(),
                "weighted_wager": str(weighted), "wager": money(weighted),
                "original_weighted_wager": original,
                "original_weighted_str": money(original),
                "raw_wager": None if raw is None else str(decimal_amount(raw)),
                "raw_wager_str": money(raw),
                "source": "override" if row.get("source") == "override" else "shuffle",
                "row_count": max(1, integer(row.get("row_count"), 1)),
            }
            result[field].append(clean)
        result[field].sort(key=lambda row: row["rank"])
    updated = snapshots.get("updated_at")
    if updated is not None and (isinstance(updated, bool) or not isinstance(updated, int)
                                or updated < 0 or updated > int(time.time()) + 300):
        raise ValueError("Snapshot update time is invalid.")
    result["updated_at"] = updated
    return result


def clean_overrides(value) -> dict:
    if not isinstance(value, dict) or len(value) > 10000:
        raise ValueError("Overrides must be an object with at most 10,000 entries.")
    result = {}
    for username, amount in value.items():
        if not isinstance(username, str) or not username.strip() or len(username) > 64:
            raise ValueError("An override username is invalid.")
        result[username.strip()] = str(money_input(str(amount)))
    return result


def csv_text(value) -> str:
    """Prevent text cells from being interpreted as formulas by spreadsheet apps."""
    text = str(value or "")
    unsafe = text.lstrip().startswith(("=", "+", "-", "@")) or bool(text and text[0] in "\t\r\n")
    return "'" + text if unsafe else text


def read_json(path: Path) -> dict:
    try:
        with path.open(encoding="utf-8") as handle:
            value = json.load(handle)
        if not isinstance(value, dict):
            raise ValueError("The file must contain a JSON object.")
        return value
    except (OSError, ValueError) as exc:
        raise RuntimeError("Cannot read " + str(path) + ". The original file was left untouched. Restore a verified recovery copy.") from exc
```

## requirements.txt

```text
Flask==3.1.3
requests==2.34.2
waitress==3.0.2
tzdata==2026.3
Pillow==12.3.0
```

## runtime.py

```python
"""One runtime, two independent minute jobs, and atomic published snapshots."""
import copy
from decimal import Decimal
import logging
import secrets
import threading
import time

from config import INTERVAL, RELEASE
from integrations import Providers, ProviderError
from storage import Store, StoreError, Conflict
from race import calculate, empty, freshness, normalize, phase, rank, token
from race_support import fmt_et, money, race_key

LOG = logging.getLogger("redhunllef")


class Runtime:
    def __init__(self, config):
        self.config, self.store, self.providers = config, Store(config), Providers(config)
        self.lock, self.stop_event = threading.RLock(), threading.Event()
        self.revision, self.admin = self.store.admin()
        self.shuffle = self.store.live("shuffle") or empty(self.admin["site_settings"])
        if self.shuffle.get("key") != race_key(self.admin["site_settings"]):
            self.shuffle = empty(self.admin["site_settings"])
        self.restore_edits()
        self.kick = self.store.live("kick") or dict(updated_at=0, attempt_at=0, error="", live=False)
        self.events = {name: threading.Event() for name in ("shuffle", "kick")}
        self.threads, self.started = {}, False
        self.instance_id = secrets.token_hex(8)
        self.jobs = {name: dict(state="starting", next_check=0, duration_ms=0, http_status=None,
                               retry_after=0, attempt_at=0, error="", not_before=0,
                               requested=0, completed=0, runs=0, completed_at=0, result="waiting",
                               checked_scope="", checked_start=0, checked_end=0, checked_channel="")
                     for name in self.events}

    def restore_edits(self):
        # Imported Top 15 backups may omit the separate overrides view. Keep
        # the saved ranking intact while making every saved edit accessible.
        _, edits, _ = rank(self.shuffle.get("source", []), self.admin["overrides"],
                           self.config.aggregation, self.config.limit)
        if self.shuffle.get("snapshot_only") or phase(self.admin["site_settings"]) in {"upcoming", "unconfigured"}:
            ranks = {row["username"]: row["rank"] for row in self.shuffle["rows"]}
            edits = [{**row, "rank": ranks.get(row["username"])} for row in edits]
        self.shuffle["edits"] = edits

    def sync(self):
        revision, admin = self.store.admin()
        with self.lock:
            if revision != self.revision:
                self.revision, self.admin = revision, admin
                saved = self.store.live("shuffle")
                self.shuffle = saved if saved and saved.get("key") == race_key(admin["site_settings"]) else empty(admin["site_settings"])
                self.restore_edits()
            return self.revision, copy.deepcopy(self.admin)

    def commit(self, admin, expected, *, snapshot=None, reason=None):
        with self.lock:
            revision = self.store.save(admin, expected, snapshot=snapshot, backup_reason=reason)
            self.revision, self.admin = revision, copy.deepcopy(admin)
            if snapshot is not None:
                self.shuffle = copy.deepcopy(snapshot)

    def public(self):
        with self.lock:
            site, value, kick = copy.deepcopy(self.admin["site_settings"]), copy.deepcopy(self.shuffle), copy.deepcopy(self.kick)
        site.update(start_et=fmt_et(site["start_time"]), end_et=fmt_et(site["end_time"]),
                    total_prize=money(sum(Decimal(v) for v in site["prizes"].values())), race_state=phase(site))
        # Projection is an explicit allowlist. Provider source rows, raw totals,
        # admin names, password hashes, and keys cannot reach the public API.
        rows = [dict(rank=r["rank"], username=r["username"][:2] + "******", wager=r["wager"]) for r in value["rows"][:15]]
        if phase(site) in {"upcoming", "unconfigured"}:
            rows = []
        available = bool(kick.get("updated_at") and not kick.get("error") and time.time() - kick["updated_at"] <= 180
                         and kick.get("channel") == site["kick_channel_slug"])
        stream = {k: kick.get(k) for k in ("live", "title", "viewers", "updated_at")}
        stream["available"] = available
        fresh = freshness(value)
        fresh.pop("error", None)
        return dict(release=RELEASE, server_time=int(time.time()), interval=INTERVAL, site=site, rows=rows,
                    leaderboard_message=self.empty_message(site, value),
                    freshness=fresh, stream=stream, revision=token([site, rows, fresh, stream]))

    @staticmethod
    def empty_message(site, snapshot):
        """Explain an empty board without inventing results or exposing records."""
        state = phase(site)
        if state == "unconfigured":
            return "The race schedule has not been configured."
        if state == "upcoming":
            return "This race has not started. Wagers will load after " + fmt_et(site["start_time"]) + "."
        if snapshot["rows"]:
            return ""
        if snapshot.get("error"):
            return "Shuffle updates are delayed. No successful leaderboard is available for this race window yet."
        if not snapshot.get("updated_at"):
            return "Waiting for Shuffle's first successful update for this race window."
        if not snapshot.get("received"):
            return "Shuffle returned no wagers for " + fmt_et(site["start_time"]) + " to " + fmt_et(site["end_time"]) + "."
        if not snapshot.get("accepted"):
            return "None of the returned wagers match this race's saved campaign filter."
        return "No returned wagers currently meet the $0.01 weighted qualification for this race."

    def status(self):
        if self.started:
            self.start()  # Recover a stopped worker without starting jobs in factory-only tests.
        with self.lock:
            data = self.public()
            data["runtime_id"] = self.instance_id
            data.update(rows=copy.deepcopy(self.shuffle["rows"]), edits=copy.deepcopy(self.shuffle.get("edits", [])),
                        red=copy.deepcopy(self.shuffle.get("red", [])), red_total=self.shuffle.get("red_total", 0),
                        count=self.shuffle.get("count", len(self.shuffle["rows"])), snapshot_only=self.shuffle.get("snapshot_only", False),
                        freshness=freshness(self.shuffle), jobs=self.job_status(),
                        diagnostics=dict(release=RELEASE, credentials=self.config.diagnostics(),
                            storage="Local JSON file (automatic)", settings_revision=self.revision,
                            start_et=fmt_et(self.admin["site_settings"]["start_time"]), end_et=fmt_et(self.admin["site_settings"]["end_time"]),
                            received=self.shuffle.get("received", 0), accepted=self.shuffle.get("accepted", 0),
                            rejected=self.shuffle.get("rejected", {}), missing_campaign=self.shuffle.get("missing_campaign", 0)))
            data["diagnostics"].update(race_state=phase(self.admin["site_settings"]),
                campaign_filter=self.admin["site_settings"]["campaign_code_filter"], endpoint_kind=self.config.endpoint,
                aggregation=self.config.aggregation, qualifying_players=data["count"], loaded_players=len(data["rows"]))
            return data

    def job_status(self):
        with self.lock:
            return {name: {**{k: v for k, v in job.items() if k != "not_before"},
                           "pending": self.events[name].is_set(),
                           "worker_alive": bool(self.threads.get(name) and self.threads[name].is_alive()),
                           "changed_at": (self.shuffle if name == "shuffle" else self.kick).get("changed_at", 0),
                           "last_success": (self.shuffle if name == "shuffle" else self.kick).get("updated_at", 0)}
                    for name, job in self.jobs.items()}

    def check(self, name):
        began, now = time.monotonic(), int(time.time())
        with self.lock:
            ticket = self.jobs[name]["requested"]
            self.jobs[name].update(state="checking", attempt_at=now, next_check=0,
                                   runs=self.jobs[name]["runs"]+1)
        error, status, retry, warning, result, revision = "", None, 0, "", "waiting", None
        try:
            with self.store.job(name) as acquired:
                revision, admin = self.sync()
                site = admin["site_settings"]
                with self.lock:
                    self.jobs[name].update(checked_scope=race_key(site) if name == "shuffle" else site["kick_channel_slug"],
                        checked_start=site["start_time"] if name == "shuffle" else 0,
                        checked_end=min(site["end_time"], now) if name == "shuffle" else 0,
                        checked_channel=site["kick_channel_slug"] if name == "kick" else "")
                if not acquired:
                    saved = self.store.live(name)
                    with self.lock:
                        if saved and (name == "kick" or saved.get("key") == race_key(site)):
                            setattr(self, name, saved)
                    result = "shared"
                    return 0
                if name == "shuffle":
                    with self.lock:
                        previous = copy.deepcopy(self.shuffle)
                    if phase(site) in {"upcoming", "unconfigured"}:
                        value = empty(site)
                        value["attempt_at"] = now
                        result = phase(site)
                    else:
                        LOG.info("SHUFFLE Checking saved window %s -> %s.", fmt_et(site["start_time"]), fmt_et(min(site["end_time"], now)))
                        incoming = normalize(self.providers.shuffle(site), site, self.config.raw_fallback)
                        status = self.providers.last_http_status()
                        value = calculate({**empty(site), **incoming, "updated_at":int(time.time()), "attempt_at":now, "ok":True}, admin, self.config)
                        value["changed_at"] = value["updated_at"] if previous["rows"] != value["rows"] else previous.get("changed_at", 0)
                        value["previous_top"] = previous["rows"][:15] if previous["rows"][:15] != value["rows"][:15] else previous.get("previous_top", [])
                        warning = value["warning"]
                        result = "empty" if not value["rows"] else "updated" if previous["rows"] != value["rows"] else "unchanged"
                    with self.lock:
                        self.store.publish(name, value, revision)
                        self.shuffle = value
                    LOG.info("SHUFFLE %s; %s accepted / %s received; race %s → %s.",
                             "Updated" if previous["rows"] != value["rows"] else "Confirmed unchanged",
                             value.get("accepted", 0), value.get("received", 0), fmt_et(site["start_time"]), fmt_et(site["end_time"]))
                    if not value["rows"]:
                        LOG.info("SHUFFLE %s", self.empty_message(site, value))
                else:
                    value = {**self.providers.kick(site), "updated_at":int(time.time()), "attempt_at":now, "error":""}
                    fields = ("live", "title", "viewers", "channel")
                    with self.lock:
                        value["changed_at"] = value["updated_at"] if any(value.get(k) != self.kick.get(k) for k in fields) else self.kick.get("changed_at", 0)
                    status, result = self.providers.last_http_status(), "live" if value["live"] else "offline"
                    with self.lock:
                        self.store.publish(name, value, revision)
                        self.kick = value
                    LOG.info("KICK Confirmed %s.", "LIVE" if value["live"] else "OFFLINE")
        except Conflict:
            self.events[name].set()
            result = "superseded"
            LOG.info("%s Settings changed during this check; checking again.", name.upper())
        except Exception as exc:
            error = str(exc) if isinstance(exc, (ProviderError, StoreError, ValueError)) else "Internal check failed (" + type(exc).__name__ + ")."
            status, retry = getattr(exc, "status", None), getattr(exc, "retry_after", 0)
            superseded, result = False, "failed"
            with self.lock:
                superseded = revision is not None and revision != self.revision
                if not superseded:
                    old = copy.deepcopy(getattr(self, name))
                    old.update(error=error, attempt_at=now, ok=False)
                    try:
                        # Failed responses have the same revision guard as
                        # successful ones. An old window cannot poison a new one.
                        self.store.publish(name, old, revision if revision is not None else self.revision)
                    except Conflict:
                        superseded = True
                    except StoreError:
                        setattr(self, name, old)
                    else:
                        setattr(self, name, old)
                if superseded:
                    self.events[name].set()
            if superseded:
                result = "superseded"
                LOG.info("%s Ignored a failed response for superseded settings; the current settings are queued.", name.upper())
                # A provider rate limit still applies across race windows.
                if status != 429 and not retry:
                    error = ""
            if error:
                LOG.warning("%s %s Previous data retained; retry in %ss.", name.upper(), error, max(INTERVAL, retry))
        finally:
            duration = round((time.monotonic() - began) * 1000)
            with self.lock:
                self.jobs[name].update(state="delayed" if error else "scheduled", error=error, http_status=status,
                                       duration_ms=duration, retry_after=retry, result=result,
                                       completed=max(ticket, self.jobs[name]["completed"]), completed_at=int(time.time()))
            if warning:
                LOG.warning("SHUFFLE %s", warning)
            LOG.info("%s Check took %sms. Automatic checks stay enabled.", name.upper(), duration)
        return max(INTERVAL, retry) if error else 0

    def request_refresh(self, name=None):
        if self.started:
            self.start()
        targets = {}
        for service in (name,) if name else self.events:
            with self.lock:
                job = self.jobs[service]
                scope = race_key(self.admin["site_settings"]) if service == "shuffle" else self.admin["site_settings"]["kick_channel_slug"]
                # A new race should not wait on an ordinary error from the old
                # dates. Explicit provider Retry-After/429 limits remain binding.
                if job["checked_scope"] != scope and not job["retry_after"] and job["http_status"] != 429:
                    job["not_before"] = 0
                if not self.events[service].is_set():
                    job["requested"] += 1
                targets[service] = job["requested"]
                if job["state"] != "checking":
                    job["state"] = "queued"
                    job["next_check"] = int(time.time() + max(0, job["not_before"]-time.monotonic()))
                # Even an active check must retain one follow-up request. The
                # event coalesces repeated clicks without concurrent API calls.
                self.events[service].set()
        return dict(runtime_id=self.instance_id, requests=targets)

    def loop(self, name):
        due = time.monotonic()
        try:
            while not self.stop_event.is_set():
                delay = max(due, self.jobs[name]["not_before"]) - time.monotonic()
                with self.lock:
                    self.jobs[name]["next_check"] = int(time.time() + max(0, delay))
                if delay > 0:
                    triggered = self.events[name].wait(min(delay, 1))
                    if not triggered:
                        continue
                    self.events[name].clear()
                    due = time.monotonic()
                    continue
                self.events[name].clear()
                anchor = due
                retry = self.check(name)
                finished = time.monotonic()
                if retry:
                    self.jobs[name]["not_before"] = finished + retry
                    due = finished + retry
                else:
                    self.jobs[name]["not_before"] = 0
                    due = anchor + (int(max(0, finished - anchor) // INTERVAL) + 1) * INTERVAL
                if self.events[name].is_set():
                    due = finished
        finally:
            self.providers.close()
            self.store.close_job()
            with self.lock:
                self.jobs[name]["state"] = "stopped"

    def start(self):
        with self.lock:
            if self.stop_event.is_set():
                return
            initial = not self.started
            self.started = True
            for name in self.events:
                if self.threads.get(name) and self.threads[name].is_alive():
                    continue
                thread = threading.Thread(target=self.loop, args=(name,), daemon=True, name=name + "-updates")
                self.threads[name] = thread
                thread.start()
                if not initial:
                    LOG.warning("%s Restarted a stopped automatic worker.", name.upper())
        if initial:
            LOG.info("LIVE Automatic Shuffle and Kick checks started; cadence=%ss.", INTERVAL)

    def stop(self):
        self.stop_event.set()
        for event in self.events.values():
            event.set()
        for thread in self.threads.values():
            thread.join(timeout=1)
```

## runtime.txt

```text
python-3.13.12
```

## static/app.js

```javascript
/* Shared page controller. Native navigation/forms work before this file loads. */
(() => {
  "use strict";
  const id = (name) => document.getElementById(name);
  const text = (node, value) => {
    // Only leaf labels can be text destinations. Never erase a page or form.
    if (!node) return;
    if (
      node.childElementCount ||
      ["BODY", "MAIN", "FORM", "HTML"].includes(node.tagName)
    )
      throw new Error("Invalid text destination");
    if (node.textContent !== String(value ?? ""))
      node.textContent = String(value ?? "");
  };
  const notice = (name, value) => {
    const node = id(name);
    if (node) {
      node.hidden = !value;
      text(node, value);
    }
  };
  const currency = (value) =>
    new Intl.NumberFormat("en-US", {
      style: "currency",
      currency: "USD",
    }).format(Number(value) || 0);
  const eastern = new Intl.DateTimeFormat("en-US", {
    timeZone: "America/New_York",
    month: "short",
    day: "numeric",
    year: "numeric",
    hour: "numeric",
    minute: "2-digit",
    timeZoneName: "short",
  });
  const date = (value) =>
    value
      ? eastern.format(new Date(value * 1000))
      : "Waiting for first source update";
  document.documentElement.classList.add("js");
  let toastTimer;
  function toast(message) {
    notice("toast", message);
    clearTimeout(toastTimer);
    toastTimer = setTimeout(() => notice("toast", ""), 4000);
  }
  document.addEventListener("click", async (event) => {
    const button = event.target.closest("[data-copy]");
    if (!button) return;
    try {
      await navigator.clipboard.writeText(button.dataset.copy);
      toast("Username copied.");
    } catch {
      toast("Select and copy the username manually.");
    }
  });
  let dirty = false;
  document.querySelectorAll("[data-dirty]").forEach((form) => {
    const initial = new URLSearchParams(new FormData(form)).toString();
    const update = () => {
      dirty = new URLSearchParams(new FormData(form)).toString() !== initial;
      text(id("saveLabel"), dirty ? "Unsaved changes" : "All changes saved");
    };
    form.addEventListener("input", update);
    form.addEventListener("change", update);
    form.addEventListener("reset", () => setTimeout(update, 0));
    form.addEventListener("submit", () => {
      dirty = false;
    });
  });
  window.addEventListener("beforeunload", (event) => {
    if (dirty) {
      event.preventDefault();
      event.returnValue = "";
    }
  });
  document.querySelectorAll("[data-confirm]").forEach((form) =>
    form.addEventListener("submit", (event) => {
      if (!window.confirm(form.dataset.confirm)) event.preventDefault();
    }),
  );
  id("raceForm")?.addEventListener("input", () => {
    const sum = [...id("raceForm").querySelectorAll('[name^="prize_"]')].reduce(
      (n, input) => n + Number(input.value.replace(/[$,\s]/g, "")),
      0,
    );
    text(
      id("prizeTotal"),
      Number.isFinite(sum) ? currency(sum) + " total" : "Review prize amounts",
    );
  });
  // The date picker stores Eastern local wall time. Server validation handles
  // nonexistent/ambiguous DST times; a shortcut never silently publishes a race.
  function easternInput(stamp) {
    const parts = new Intl.DateTimeFormat("en-US", {
      timeZone: "America/New_York",
      year: "numeric",
      month: "2-digit",
      day: "2-digit",
      hour: "2-digit",
      minute: "2-digit",
      hourCycle: "h23",
    }).formatToParts(new Date(stamp));
    const v = Object.fromEntries(parts.map((p) => [p.type, p.value]));
    return `${v.year}-${v.month}-${v.day}T${v.hour}:${v.minute}`;
  }
  function daysAfter(value, days) {
    const d = new Date(value + "Z");
    d.setUTCDate(d.getUTCDate() + days);
    return d.toISOString().slice(0, 16);
  }
  id("startNow")?.addEventListener("click", () => {
    id("f-start_et").value = easternInput(Date.now());
    id("f-end_et").value = daysAfter(id("f-start_et").value, 7);
    id("f-start_et").dispatchEvent(new Event("input", { bubbles: true }));
  });
  id("nextRace")?.addEventListener("click", () => {
    const start = id("f-start_et"),
      end = id("f-end_et");
    const duration = Math.max(
      1,
      Math.round(
        (new Date(end.value + "Z") - new Date(start.value + "Z")) / 86400000,
      ) || 7,
    );
    start.value = end.value || easternInput(Date.now());
    end.value = daysAfter(start.value, duration);
    start.dispatchEvent(new Event("input", { bubbles: true }));
    toast("Draft prepared. Review the dates before saving.");
  });

  if (!document.body.dataset.feed) return;
  const isAdmin = document.body.dataset.page === "admin";
  let site = {},
    offset = 0,
    sourceAt = 0,
    jobs = {},
    busy = false,
    timer,
    next = 0,
    urgentUntil = 0;
  let pollAgain = false,
    lastWork = "",
    receipt = null;
  let publicCache = null,
    publicETag = "",
    lastProviderFailure = "";
  let participantVersion = "",
    redVersion = "";
  try {
    const boot = JSON.parse(document.body.dataset.bootstrap);
    site = boot.site;
    offset = boot.server_time * 1000 - Date.now();
  } catch {}
  function clock() {
    if (document.hidden) return;
    const now = (Date.now() + offset) / 1000;
    const state =
      !site.start_time || site.end_time <= site.start_time
        ? "unconfigured"
        : now < site.start_time
          ? "upcoming"
          : now >= site.end_time
            ? "ended"
            : "active";
    const badge = id("raceBadge");
    text(badge, state.charAt(0).toUpperCase() + state.slice(1));
    if (badge) badge.className = "badge state-" + state;
    const left = Math.max(
      0,
      Math.ceil((state === "upcoming" ? site.start_time : site.end_time) - now),
    );
    text(
      id("countdown"),
      state === "unconfigured"
        ? "Set the race dates"
        : state === "ended"
          ? "Race complete"
          : `${Math.floor(left / 86400)}d ${String(Math.floor(left / 3600) % 24).padStart(2, "0")}h ${String(Math.floor(left / 60) % 60).padStart(2, "0")}m ${String(left % 60).padStart(2, "0")}s`,
    );
    text(
      id("clockLabel"),
      state === "upcoming"
        ? "STARTS IN"
        : state === "active"
          ? "RACE ENDS IN"
          : "RACE SCHEDULE",
    );
    text(
      id("raceWindow"),
      site.start_time
        ? date(site.start_time) + " → " + date(site.end_time)
        : "Choose the race dates in Race settings.",
    );
    if (id("endedNotice")) id("endedNotice").hidden = state !== "ended";
    if (sourceAt)
      text(
        id("sourceTime"),
        "Last checked " + Math.max(0, Math.floor(now - sourceAt)) + "s ago",
      );
    for (const [name, job] of Object.entries(jobs)) {
      const remaining = Math.max(0, Math.ceil(job.next_check - now));
      text(
        id(name + "Freshness"),
        `Last successful check: ${date(job.last_success)} · Content last changed: ${job.changed_at ? date(job.changed_at) : "No recorded change yet"}`,
      );
      text(
        id(name + "Timing"),
        job.state === "checking"
          ? "Checking now…"
          : `${job.duration_ms || 0} ms · ${job.next_check ? "Next check in " + remaining + "s" : "Check queued"} · Last success: ${date(job.last_success)}`,
      );
    }
  }
  function filterRed() {
    const q = (id("redSearch")?.value || "").trim().toLowerCase();
    id("redBody")
      ?.querySelectorAll("[data-red-name]")
      .forEach(
        (row) => (row.hidden = !row.dataset.redName.toLowerCase().includes(q)),
      );
  }
  id("redSearch")?.addEventListener("input", filterRed);
  function checkingSoon(job) {
    const pending =
      job.pending || job.requested > job.completed || job.state === "queued";
    return (
      job.state === "checking" ||
      (pending &&
        (!job.next_check || job.next_check <= (Date.now() + offset) / 1000 + 3))
    );
  }
  function progress(value) {
    for (const name of ["shuffle", "kick"]) {
      const job = jobs[name] || {},
        pending =
          job.pending ||
          job.requested > job.completed ||
          job.state === "queued";
      let message = "Automatic check is starting.";
      if (job.state === "checking")
        message = job.pending
          ? "Checking now; your follow-up refresh is queued."
          : "Checking the provider now…";
      else if (pending) {
        message =
          job.next_check > (Date.now() + offset) / 1000 + 3
            ? "Queued. Retry scheduled for " + date(job.next_check) + "."
            : "Refresh queued; waiting for the worker.";
        if (job.error)
          message +=
            " Last check" +
            (job.http_status ? " (HTTP " + job.http_status + ")" : "") +
            ": " +
            job.error;
      } else if (job.error)
        message =
          "Check failed" +
          (job.http_status ? " (HTTP " + job.http_status + ")" : "") +
          ": " +
          job.error;
      else if (
        name === "shuffle" &&
        ["updated", "unchanged"].includes(job.result)
      )
        message =
          (job.result === "updated" ? "Published " : "Confirmed ") +
          (value.count || 0) +
          " qualifying players. Last check: " +
          date(job.completed_at) +
          ".";
      else if (name === "shuffle" && job.result === "empty")
        message =
          value.leaderboard_message ||
          "Check completed; no qualifying wagers were returned.";
      else if (["upcoming", "unconfigured"].includes(job.result))
        message =
          value.leaderboard_message ||
          "Waiting for the configured race to start.";
      else if (job.result === "superseded")
        message =
          "The old settings were superseded; a check for the current settings is queued.";
      else if (job.result === "shared")
        message = "Another app instance is checking this provider.";
      else if (name === "kick" && ["live", "offline"].includes(job.result))
        message =
          "Confirmed " +
          job.result +
          " on Kick. Last check: " +
          date(job.completed_at) +
          ".";
      text(id(name + "Progress"), message);
      const summary = job.error
        ? "Needs attention"
        : job.state === "checking"
          ? "Checking now"
          : pending
            ? "Queued"
            : name === "kick" && ["live", "offline"].includes(job.result)
              ? job.result === "live"
                ? "Live"
                : "Offline"
              : job.result === "waiting"
                ? "Waiting for data"
                : job.result === "upcoming"
                  ? "Race upcoming"
                  : job.result === "unconfigured"
                    ? "Set race dates"
                    : "Up to date";
      text(
        id(name + "Summary"),
        `${name === "shuffle" ? "Shuffle" : "Kick"} · ${summary}`,
      );
      id(name + "Summary")?.classList.toggle("has-error", Boolean(job.error));
    }
    const failure = JSON.stringify(
      Object.entries(jobs)
        .filter(([, job]) => job.error)
        .map(([name, job]) => [name, job.error, job.http_status]),
    );
    if (
      failure !== "[]" &&
      failure !== lastProviderFailure &&
      id("connectionDetails")
    )
      id("connectionDetails").open = true;
    lastProviderFailure = failure;
    text(
      id("publishedWindow"),
      "Published window: " +
        date(site.start_time) +
        " → " +
        date(site.end_time),
    );
    const work = JSON.stringify([
      value.runtime_id,
      ...Object.values(jobs).map((job) => [job.requested, job.runs, job.state]),
    ]);
    if (work !== lastWork && Object.values(jobs).some(checkingSoon))
      urgentUntil = Date.now() + 60000;
    lastWork = work;
    if (receipt && value.runtime_id) {
      if (receipt.runtime_id !== value.runtime_id) {
        receipt = null;
        toast("The backend restarted. Current update progress is shown below.");
      } else if (
        Object.entries(receipt.requests).every(
          ([name, target]) => jobs[name]?.completed >= target,
        )
      ) {
        const failed = Object.keys(receipt.requests).some(
          (name) => jobs[name]?.error,
        );
        toast(
          failed
            ? "Refresh finished with a provider error. See update progress below."
            : "Refresh finished. See the update result below.",
        );
        receipt = null;
      }
    }
  }
  function cell(value, className = "") {
    const td = document.createElement("td");
    td.textContent = String(value ?? "—");
    td.className = className;
    return td;
  }
  function updateTable(body, rows, red = false) {
    if (!body) return;
    const encoded = JSON.stringify(rows);
    if (encoded === (red ? redVersion : participantVersion)) return;
    if (red) redVersion = encoded;
    else participantVersion = encoded;
    const scroll = body.closest(".table-scroll"),
      top = scroll?.scrollTop,
      left = scroll?.scrollLeft;
    const focused = document.activeElement,
      focusRow = focused?.closest("tr"),
      focusName = focusRow?.dataset.player || focusRow?.dataset.redName;
    const focusCopy = focused?.hasAttribute("data-copy");
    const fragment = document.createDocumentFragment();
    rows.forEach((r, index) => {
      const tr = document.createElement("tr");
      tr.dataset[red ? "redName" : "player"] = r.username;
      tr.append(cell(red ? index + 1 : r.rank, "rank"));
      const name = cell("");
      const strong = document.createElement("strong");
      strong.textContent = r.username;
      name.append(strong);
      const copy = document.createElement("button");
      copy.type = "button";
      copy.className = "copy-button";
      copy.dataset.copy = r.username;
      copy.textContent = "⧉";
      copy.setAttribute("aria-label", "Copy " + r.username);
      name.append(copy);
      if (!red && r.source === "override") {
        const label = document.createElement("span");
        label.className = "tag";
        label.textContent = "Adjusted";
        name.append(label);
      }
      tr.append(name, cell(red ? r.weighted : r.wager, "number accent"));
      if (!red) tr.append(cell(r.original_weighted_str, "number"));
      tr.append(cell(red ? r.raw : r.raw_wager_str, "number"));
      if (!red) {
        const action = cell(""),
          link = document.createElement("a");
        link.href =
          "/admin?tab=players&edit=" +
          encodeURIComponent(r.username) +
          "#override";
        link.className = "text-link";
        link.textContent = "Edit";
        action.append(link);
        tr.append(action);
      }
      fragment.append(tr);
    });
    if (!rows.length) {
      const tr = document.createElement("tr"),
        td = cell(
          red
            ? "No confirmed Code Red wagerers for this window."
            : "No matching qualifying wagers.",
          "empty",
        );
      td.colSpan = red ? 4 : 6;
      tr.append(td);
      fragment.append(tr);
    }
    body.replaceChildren(fragment);
    if (scroll) {
      scroll.scrollTop = top;
      scroll.scrollLeft = left;
    }
    if (focusName)
      [...body.rows]
        .find(
          (row) => (row.dataset.player || row.dataset.redName) === focusName,
        )
        ?.querySelector(focusCopy ? "button" : "a")
        ?.focus({ preventScroll: true });
    if (red) filterRed();
  }
  function apply(value, began) {
    if (!value.site || !value.freshness || !Number.isFinite(value.server_time))
      throw new Error("The update response is incomplete.");
    site = value.site;
    offset = value.server_time * 1000 - (began + Date.now()) / 2;
    sourceAt = value.freshness.updated_at;
    text(id("raceTitle"), site.race_title);
    text(id("raceDescription"), site.race_description);
    text(id("sponsorName"), site.sponsor_name);
    text(id("poolTotal"), site.total_prize);
    text(id("playerCount"), value.count);
    text(id("dataState"), value.freshness.label);
    text(id("sourceTime"), date(sourceAt));
    notice("leaderboardMessage", value.leaderboard_message || "");
    notice(
      "sourceWarning",
      [value.freshness.warning, isAdmin ? value.freshness.error : ""]
        .filter(Boolean)
        .join(" "),
    );
    document
      .querySelectorAll("[data-site-text]")
      .forEach((node) => text(node, site[node.dataset.siteText]));
    document.querySelectorAll("[data-site-link]").forEach((a) => {
      const href = site[a.dataset.siteLink];
      a.hidden = !href;
      if (href && /^https?:\/\//.test(href)) a.href = href;
    });
    if (id("sponsorLink") && /^https?:\/\//.test(site.sponsor_url))
      id("sponsorLink").href = site.sponsor_url;
    if (isAdmin) {
      jobs = value.jobs || {};
      if (value.checkpoint) {
        text(id("checkpointLabel"), value.checkpoint.label);
        text(id("checkpointDetails"), value.checkpoint.details);
        text(
          id("checkpointTime"),
          value.checkpoint.generated_at
            ? "Last export generated: " + date(value.checkpoint.generated_at)
            : "No export generated yet.",
        );
        id("checkpointLabel")?.classList.toggle(
          "accent",
          value.checkpoint.changes,
        );
      }
      progress(value);
      updateTable(id("participantsBody"), value.participants || []);
      if (id("codeRed")?.open && value.red)
        updateTable(id("redBody"), value.red, true);
      text(id("redCount"), Math.min(100, value.red_total || 0) + " / 100");
      text(
        id("redMembership"),
        (value.diagnostics?.missing_campaign || 0) +
          " source rows have no campaign metadata; membership cannot be verified for those rows.",
      );
      for (const name of ["shuffle", "kick"])
        text(
          id(name + "Message"),
          jobs[name]?.error ||
            (name === "shuffle"
              ? value.freshness.label
              : value.stream?.available
                ? value.stream.live
                  ? "Live on Kick"
                  : "Kick offline"
                : "Kick status unavailable"),
        );
      const stream = value.stream || {};
      text(
        id("streamDetail"),
        stream.available && stream.live
          ? [
              stream.title,
              stream.viewers
                ? stream.viewers.toLocaleString() + " watching"
                : "Viewer count unavailable",
            ]
              .filter(Boolean)
              .join(" · ")
          : "",
      );
      document
        .querySelectorAll("[data-diagnostic]")
        .forEach((node) =>
          text(node, value.diagnostics?.[node.dataset.diagnostic]),
        );
      text(
        id("browserCheck"),
        "Dashboard checked " +
          date(value.server_time) +
          " · next update in 60 seconds",
      );
    } else {
      const rows = new Map((value.rows || []).map((row) => [row.rank, row]));
      document.querySelectorAll("[data-rank]").forEach((node) => {
        const n = Number(node.dataset.rank),
          row = rows.get(n);
        text(
          node.querySelector("[data-name]"),
          row?.username || "Open position",
        );
        text(node.querySelector("[data-wager]"), row?.wager || "$0.00");
        text(node.querySelector("[data-prize]"), currency(site.prizes[n]));
      });
      if (value.boss) {
        const b = value.boss;
        text(id("inviteBossName"), b.name || "Crimson Hunllef");
        const avatar = id("inviteAvatar");
        if (avatar && b.avatar_url) {
          if (avatar.getAttribute("src") !== b.avatar_url)
            avatar.src = b.avatar_url;
          avatar.classList.toggle("custom-avatar", Boolean(b.avatar_custom));
        }
        text(
          id("inviteTitle"),
          b.status === "victory"
            ? `The crew conquered ${b.name || "Crimson Hunllef"}.`
            : b.status === "paused"
              ? "The raid is taking a breather."
              : "Red needs a raid party.",
        );
        text(
          id("inviteProgress"),
          `${Number(b.hp).toLocaleString()} HP left · ${b.raiders} raiders united`,
        );
        text(
          id("inviteButtonLabel"),
          b.status === "victory"
            ? "View the victory"
            : b.status === "paused"
              ? "View the raid"
              : "Join the boss fight",
        );
        const bar = id("inviteHealth");
        if (bar) {
          bar.max = b.max_hp;
          bar.value = b.max_hp - b.hp;
        }
      }
      text(
        id("streamStatus"),
        !value.stream?.available
          ? "Kick status unavailable"
          : value.stream.live
            ? "● Live on Kick"
            : "Kick offline",
      );
    }
    clock();
  }
  async function getJSON(url, options = {}) {
    const controller = new AbortController(),
      timeout = setTimeout(() => controller.abort(), 10000);
    try {
      const conditional =
        !isAdmin &&
        !options.method &&
        new URL(url, location.origin).pathname === "/public-state";
      const headers = { Accept: "application/json", ...options.headers };
      if (conditional && publicETag) headers["If-None-Match"] = publicETag;
      const response = await fetch(url, {
        ...options,
        credentials: "same-origin",
        cache: "no-store",
        signal: controller.signal,
        headers,
      });
      const clockHeader = response.headers?.get("X-Server-Time");
      const currentTime =
        clockHeader && Number.isFinite(Number(clockHeader))
          ? Number(clockHeader)
          : null;
      if (conditional && response.status === 304) {
        if (!publicCache)
          throw new Error("The cached update is unavailable. Reload the page.");
        return {
          ...publicCache,
          server_time: currentTime ?? Date.now() / 1000,
        };
      }
      if (response.status === 401)
        throw new Error(
          "Your session expired. Sign in again to resume updates.",
        );
      if (
        response.redirected &&
        response.url &&
        new URL(response.url, location.origin).pathname === "/admin/login"
      ) {
        throw new Error(
          "Your session expired. Sign in again to resume updates.",
        );
      }
      if (!response.headers.get("content-type")?.includes("application/json")) {
        const hint =
          response.status === 404
            ? "The update endpoint was not found. Reload the page after installing the complete update."
            : response.status >= 500
              ? "Check the backend runtime logs. Previous results are retained."
              : "Reload the page and sign in again if needed.";
        // Never render an HTML error/proxy page into the dashboard.
        throw new Error(
          `Expected JSON but received a non-JSON response (HTTP ${response.status}). ${hint}`,
        );
      }
      let value;
      try {
        value = await response.json();
      } catch {
        throw new Error(
          `The server returned invalid JSON (HTTP ${response.status}). Check the runtime logs.`,
        );
      }
      if (!response.ok)
        throw new Error(
          `${value?.error || "The server could not complete this request."} (HTTP ${response.status})`,
        );
      if (conditional) {
        publicCache = value;
        publicETag = response.headers.get("ETag") || "";
        value = {
          ...value,
          server_time: currentTime ?? value.server_time ?? Date.now() / 1000,
        };
      }
      return value;
    } finally {
      clearTimeout(timeout);
    }
  }
  async function poll() {
    if (document.hidden) return;
    if (busy) {
      pollAgain = true;
      return;
    }
    busy = true;
    clearTimeout(timer);
    const began = Date.now();
    try {
      const url = new URL(document.body.dataset.feed, location.origin);
      if (isAdmin) {
        for (const [key, value] of new URLSearchParams(location.search))
          url.searchParams.set(key, value);
        if (id("codeRed")?.open) url.searchParams.set("code_red", "1");
      }
      const result = await getJSON(url);
      apply(result, began);
      notice("networkError", "");
      if (result.release && result.release !== "2026.09.29-player-access")
        notice(
          "networkError",
          "A newer version was deployed. Save your draft, then reload.",
        );
    } catch (error) {
      notice(
        "networkError",
        error.name === "AbortError"
          ? "Dashboard request timed out. Previous results are retained; updates will retry."
          : error.message,
      );
    } finally {
      busy = false;
      if (!next) next = began + 60000;
      else if (next <= began)
        next += 60000 * (Math.floor((began - next) / 60000) + 1);
      if (next <= Date.now())
        next += 60000 * (Math.floor((Date.now() - next) / 60000) + 1);
      const urgent =
        Date.now() < urgentUntil && Object.values(jobs).some(checkingSoon);
      const delay = pollAgain
        ? 50
        : urgent
          ? 2000
          : Math.max(250, next - Date.now());
      pollAgain = false;
      if (!document.hidden) timer = setTimeout(poll, delay);
    }
  }
  document.querySelectorAll("[data-refresh]").forEach((form) =>
    form.addEventListener("submit", async (event) => {
      event.preventDefault();
      const button = form.querySelector("button");
      if (button.disabled) return;
      button.disabled = true;
      try {
        // A hidden input named "action" shadows form.action in real browsers.
        // Read the HTML attribute so every refresh reaches the backend route.
        const value = await getJSON(form.getAttribute("action"), {
          method: "POST",
          body: new FormData(form),
        });
        receipt = value.requests
          ? { runtime_id: value.runtime_id, requests: value.requests }
          : null;
        jobs = value.jobs || jobs;
        toast(value.message);
        urgentUntil = Date.now() + 60000;
        next = 0;
        await poll();
      } catch (error) {
        toast(error.message);
      } finally {
        button.disabled = false;
      }
    }),
  );
  document
    .querySelectorAll("[data-recovery-download]")
    .forEach((link) =>
      link.addEventListener("click", () => setTimeout(() => void poll(), 1000)),
    );
  id("codeRed")?.addEventListener("toggle", () => {
    if (id("codeRed").open) {
      next = 0;
      poll();
    }
  });
  document.addEventListener("visibilitychange", () => {
    clearTimeout(timer);
    if (!document.hidden) {
      next = 0;
      poll();
    }
  });
  window.addEventListener("pageshow", (event) => {
    if (event.persisted) {
      next = 0;
      poll();
    }
  });
  clock();
  setInterval(clock, 1000);
  poll();
})();
```

## static/boss.css

```css
/* A small CSS arena using the original logo; no canvas engine or image bundle. */
.boss-settings-grid {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 24px;
  margin: 26px 0;
}
.boss-setting {
  min-width: 0;
  border: 1px solid var(--line);
  padding: 22px;
  border-radius: 12px;
}
.boss-identity-setting {
  grid-column: 1 / -1;
}
.boss-page #bossName,
[data-mode="admin"] #bossName {
  overflow-wrap: anywhere;
}
[data-mode="admin"] > .section-title > div {
  min-width: 0;
}
.boss-damage-fields {
  display: grid;
  grid-template-columns: repeat(3, minmax(0, 1fr));
  gap: 16px;
}
@media (max-width: 700px) {
  .boss-damage-fields {
    grid-template-columns: 1fr;
  }
}
.boss-avatar-preview {
  display: block;
  object-fit: contain;
  margin: 12px 0 20px;
  border-radius: 12px;
  background: #160e14;
  image-rendering: pixelated;
}
.boss-sprite.custom-avatar,
.boss-avatar-preview.custom-avatar {
  image-rendering: auto;
}
@media (max-width: 700px) {
  .boss-settings-grid {
    grid-template-columns: 1fr;
  }
}
.boss-page {
  padding-top: 40px;
}
.boss-heading {
  display: flex;
  justify-content: space-between;
  align-items: flex-end;
  gap: 24px;
  margin-bottom: 30px;
}
.boss-heading h1 {
  font-size: clamp(2.3rem, 4vw, 3.6rem);
  margin: 16px 0;
}
.boss-heading .lead {
  max-width: 520px;
  margin-bottom: 0;
}
.boss-heading > a {
  white-space: nowrap;
  margin-bottom: 5px;
}
.boss-live {
  display: flex;
  justify-content: space-between;
  gap: 16px;
  color: var(--muted);
  font-size: 0.72rem;
  margin-bottom: 16px;
}
.boss-live > span:first-child {
  color: var(--accent);
}
.raid-layout {
  display: grid;
  grid-template-columns: minmax(0, 1.35fr) minmax(0, 1fr);
  gap: 22px;
}
.arena {
  padding: 24px 28px;
  overflow: hidden;
  background:
    radial-gradient(ellipse at 50% 30%, #671c253d, transparent 65%), #191216;
}
.arena-heading,
.boss-name-row,
.hp-label,
.combo-row {
  display: flex;
  justify-content: space-between;
  align-items: center;
  gap: 12px;
}
.arena-heading .eyebrow {
  font-size: 0.6rem;
}
.boss-stage {
  height: 280px;
  display: grid;
  place-items: center;
  position: relative;
  isolation: isolate;
}
.boss-sprite {
  object-fit: contain;
  width: 190px;
  height: 190px;
  image-rendering: pixelated;
  filter: drop-shadow(0 15px 25px #ff24243d);
  z-index: 1;
  animation: boss-hover 4s ease-in-out infinite;
}
.rune-ring {
  position: absolute;
  border: 1px solid #bb35375c;
  border-radius: 50%;
  width: 254px;
  height: 254px;
  box-shadow:
    0 0 45px #ff323210,
    inset 0 0 38px #f33b3810;
}
.rune-ring.inner {
  width: 220px;
  height: 220px;
  border-style: dashed;
  opacity: 0.55;
  animation: ring-turn 80s linear infinite;
}
.arena-rune {
  position: absolute;
  color: #ff666d;
  font-size: 22px;
  opacity: 0.65;
}
.rune-one {
  left: 15%;
  top: 30%;
}
.rune-two {
  right: 14%;
  bottom: 23%;
}
.boss-shadow {
  position: absolute;
  bottom: 20px;
  background: #0006;
  width: 145px;
  height: 18px;
  border-radius: 50%;
  filter: blur(6px);
}
.boss-name-row {
  margin-top: 8px;
}
.boss-name-row h2 {
  font-size: 1.6rem;
}
.boss-name-row .eyebrow {
  font-size: 0.57rem;
  margin-bottom: 4px;
}
.hp-label {
  font-size: 0.77rem;
  margin: 10px 0 8px;
  font-variant-numeric: tabular-nums;
}
.hp-label > span {
  color: var(--muted);
}
.health-bar {
  appearance: none;
  -webkit-appearance: none;
  width: 100%;
  height: 12px;
  border: none;
  border-radius: 8px;
  background: #382128;
  overflow: hidden;
  display: block;
  accent-color: #ff3a47;
}
.health-bar::-webkit-progress-bar {
  background: #382128;
  border-radius: 8px;
}
.health-bar::-webkit-progress-value {
  background: linear-gradient(90deg, #b91732, #ff4a51);
  border-radius: 8px;
  transition: width 0.45s;
}
.health-bar::-moz-progress-bar {
  background: linear-gradient(90deg, #b91732, #ff4a51);
  border-radius: 8px;
}
.boss-story {
  color: var(--muted);
  font-size: 0.75rem;
  margin: 14px 0 20px;
  min-height: 2.8em;
}
.raid-stats {
  display: grid;
  grid-template-columns: repeat(3, minmax(0, 1fr));
  border-top: 1px solid var(--line);
  padding-top: 18px;
  gap: 14px;
}
.raid-stats strong,
.personal-stats strong {
  display: block;
  font-size: 1.35rem;
  font-variant-numeric: tabular-nums;
  letter-spacing: -0.035em;
}
.raid-stats span,
.personal-stats span {
  display: block;
  font-size: 0.66rem;
  color: var(--muted);
  margin-top: 2px;
}
.attack-panel {
  padding: 26px;
}
.attack-panel > .row {
  align-items: flex-start;
}
.attack-panel .eyebrow {
  font-size: 0.59rem;
}
.attack-panel h2 {
  font-size: 1.65rem;
  margin-top: 5px;
}
.weakness-box {
  display: flex;
  align-items: center;
  gap: 14px;
  padding: 14px 16px;
  border: 1px solid #73402f;
  background: linear-gradient(105deg, #40261d, #291c19);
  border-radius: 10px;
  margin: 22px 0 17px;
}
.weakness-symbol {
  font-size: 2.1rem;
  color: #ffcd86;
}
.weakness-box small,
.weakness-box strong,
.weakness-box div > span {
  display: block;
}
.weakness-box small {
  font-size: 0.56rem;
  letter-spacing: 0.13em;
  color: #e3b777;
}
.weakness-box strong {
  font-size: 0.93rem;
  color: #ffe5c1;
  margin: 3px 0;
}
.weakness-box div > span {
  font-size: 0.65rem;
  color: #c5ae99;
}
.strike-options {
  display: grid;
  grid-template-columns: repeat(3, minmax(0, 1fr));
  gap: 8px;
}
.strike-options button {
  border: 1px solid var(--line);
  border-radius: 10px;
  background: #21161c;
  color: var(--text);
  padding: 12px 6px;
  position: relative;
}
.strike-options button[aria-pressed="true"] {
  border-color: var(--accent);
  background: #481f2b;
  box-shadow: inset 0 0 0 1px var(--accent);
}
.strike-options button.is-weak:after {
  content: "WEAK";
  position: absolute;
  right: 5px;
  top: 5px;
  font-size: 0.42rem;
  letter-spacing: 0.05em;
  color: #ffd397;
}
.strike-options button > span {
  display: block;
  font-size: 1.65rem;
  line-height: 1.2;
  margin: 4px 0 7px;
  color: #ffd5d7;
}
.strike-options strong {
  display: block;
  font-size: 0.8rem;
}
.strike-options small {
  display: block;
  font-size: 0.55rem;
  color: var(--muted);
  margin-top: 4px;
}
.combo-row {
  font-size: 0.65rem;
  margin: 20px 0 8px;
}
.combo-row > span {
  color: var(--muted);
}
.burst-meter {
  display: flex;
  gap: 4px;
}
.burst-meter span {
  height: 5px;
  flex: 1;
  background: #462632;
  border-radius: 2px;
}
.burst-meter span.filled {
  background: var(--accent);
  box-shadow: 0 0 8px #ff2d2d25;
}
.attack-button {
  width: 100%;
  min-height: 53px;
  font-size: 0.98rem;
  margin-top: 22px;
}
.attack-button:disabled {
  cursor: default;
  opacity: 0.6;
}
.attack-hint {
  text-align: center;
  color: var(--muted);
  font-size: 0.64rem;
  margin: 9px 0 0;
}
.hit-result {
  min-height: 2.8em;
  font-size: 0.78rem;
  text-align: center;
  color: var(--accent);
  margin: 16px 0;
}
.personal-stats {
  display: grid;
  grid-template-columns: 1fr 1fr;
  border-top: 1px solid var(--line);
  padding-top: 14px;
  gap: 15px;
}
.raider-name {
  color: var(--muted);
  font-size: 0.62rem;
  margin: 14px 0 5px;
}
.raider-name strong {
  color: #eed5dd;
}
.attack-panel > #raidReset {
  font-size: 0.6rem;
  margin-bottom: 0;
}
.hit-float {
  position: absolute;
  z-index: 3;
  top: 30%;
  left: 50%;
  font-size: 2.4rem;
  font-weight: 850;
  color: #ffe7ae;
  opacity: 0;
  pointer-events: none;
  text-shadow: 0 3px 12px #270008;
}
.boss-stage.struck .hit-float {
  animation: damage-pop 0.8s ease-out;
}
.boss-stage.struck .boss-sprite {
  animation: boss-hit 0.45s ease-out;
}
.boss-stage.victory .boss-sprite {
  filter: grayscale(0.8);
  opacity: 0.6;
  animation: none;
  transform: rotate(-9deg);
}
.arena:has(.victory) {
  border-color: #a6753e;
}
.instructions {
  padding: 28px;
  margin-top: 24px;
  scroll-margin-top: 95px;
}
.instruction-grid {
  list-style: none;
  counter-reset: steps;
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 28px;
  padding: 0;
  margin: 24px 0;
}
.instruction-grid li {
  counter-increment: steps;
}
.instruction-grid li:before {
  content: "0" counter(steps);
  display: block;
  color: var(--accent);
  font-size: 0.8rem;
  font-weight: 750;
  margin-bottom: 10px;
}
.instruction-grid strong {
  font-size: 0.93rem;
}
.instruction-grid p {
  color: var(--muted);
  font-size: 0.79rem;
  margin: 9px 0 0;
}
.instruction-grid b {
  color: #f0d9de;
  font-weight: 550;
}
.raid-fineprint {
  border-top: 1px solid var(--line);
  padding-top: 18px;
  display: grid;
  gap: 10px;
}
.raid-fineprint p {
  font-size: 0.71rem;
  color: var(--muted);
  margin: 0;
}
.raid-fineprint strong {
  color: #e9cdd4;
}
.raid-bottom {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 22px;
  margin-top: 24px;
}
.raid-list {
  padding: 25px;
}
.raid-list h2 {
  font-size: 1.45rem;
}
.combat-list {
  list-style: none;
  padding: 0;
  margin: 19px 0;
}
.combat-list li {
  display: flex;
  justify-content: space-between;
  align-items: center;
  gap: 12px;
  border-bottom: 1px solid #35232b;
  padding: 11px 0;
  font-size: 0.76rem;
}
.combat-list li:last-child {
  border: 0;
}
.combat-list strong {
  font-size: 0.8rem;
  font-weight: 600;
}
.combat-list small {
  display: block;
  color: var(--muted);
  font-size: 0.61rem;
  margin-top: 3px;
}
.combat-list .score {
  color: var(--accent);
  font-variant-numeric: tabular-nums;
  white-space: nowrap;
}
.combat-list .self strong {
  color: #ffb8bf;
}
.raid-history {
  margin-top: 22px;
  padding: 18px 24px;
  font-size: 0.82rem;
}
.boss-restart {
  display: grid;
  gap: 18px;
  max-width: 500px;
  margin-top: 22px;
}
.boss-confirm {
  display: flex;
  align-items: flex-start;
  gap: 10px;
  font-size: 0.78rem;
}
.boss-confirm input {
  width: 18px;
  min-height: 18px;
  margin-top: 2px;
  accent-color: var(--action);
}
@keyframes boss-hover {
  50% {
    transform: translateY(-8px);
  }
}
@keyframes ring-turn {
  to {
    transform: rotate(360deg);
  }
}
@keyframes boss-hit {
  25% {
    transform: translateX(-9px) rotate(-4deg);
  }
  60% {
    transform: translateX(6px) rotate(3deg);
  }
}
@keyframes damage-pop {
  0% {
    opacity: 1;
    transform: translate(-50%, 0) scale(0.8);
  }
  25% {
    opacity: 1;
    transform: translate(-50%, -15px) scale(1.15);
  }
  100% {
    opacity: 0;
    transform: translate(-50%, -65px) scale(1);
  }
}
@media (max-width: 850px) {
  .raid-layout {
    grid-template-columns: 1fr 1fr;
    gap: 16px;
  }
  .arena {
    padding: 21px;
  }
  .attack-panel {
    padding: 21px;
  }
  .boss-stage {
    height: 255px;
  }
  .boss-sprite {
    width: 165px;
    height: 165px;
  }
  .rune-ring {
    width: 215px;
    height: 215px;
  }
  .rune-ring.inner {
    width: 185px;
    height: 185px;
  }
  .boss-name-row {
    align-items: flex-start;
    flex-direction: column;
    gap: 0;
  }
  .arena-heading {
    flex-wrap: wrap;
  }
  .arena-heading .badge {
    font-size: 0.61rem;
  }
  .instructions {
    padding: 23px;
  }
  .instruction-grid {
    gap: 20px;
  }
  .raid-stats strong {
    font-size: 1.1rem;
  }
}
@media (max-width: 650px) {
  .boss-page {
    padding-top: 28px;
  }
  .boss-heading {
    display: block;
    margin-bottom: 22px;
  }
  .boss-heading .lead {
    font-size: 0.87rem;
    margin-bottom: 15px;
  }
  .boss-heading h1 {
    font-size: 2.6rem;
  }
  .boss-live {
    flex-direction: column;
    gap: 4px;
    font-size: 0.66rem;
  }
  .raid-layout,
  .raid-bottom {
    grid-template-columns: 1fr;
  }
  .arena {
    padding: 20px;
  }
  .boss-stage {
    height: 245px;
  }
  .boss-name-row {
    flex-direction: row;
    align-items: center;
    gap: 10px;
  }
  .boss-name-row h2 {
    font-size: 1.5rem;
  }
  .arena-heading {
    flex-wrap: nowrap;
  }
  .attack-panel {
    padding: 24px;
  }
  .raid-stats strong {
    font-size: 1.25rem;
  }
  .instruction-grid {
    grid-template-columns: 1fr;
    gap: 22px;
  }
  .instructions .section-title {
    align-items: flex-start;
    flex-direction: column;
  }
  .instruction-grid li:before {
    float: left;
    margin: 0 15px 35px 0;
  }
  .raid-list {
    padding: 22px;
  }
  .raid-bottom {
    gap: 16px;
  }
  .hp-label {
    font-size: 0.73rem;
  }
  .boss-heading .text-link {
    font-size: 0.8rem;
  }
}
@media (prefers-reduced-motion: reduce) {
  .boss-sprite,
  .rune-ring.inner,
  .boss-stage.struck .hit-float,
  .boss-stage.struck .boss-sprite {
    animation: none !important;
  }
  .health-bar::-webkit-progress-value {
    transition: none;
  }
}

/* Milestones and badges are cosmetic; the server's damage rules stay fixed. */
.boss-stage[data-milestone="25"] .rune-ring {
  border-color: #d6485799;
}
.boss-stage[data-milestone="50"] .rune-ring {
  border-color: #ff647599;
  box-shadow:
    0 0 55px #ff303033,
    inset 0 0 45px #ff404026;
}
.boss-stage[data-milestone="75"] .rune-ring {
  border-color: #ffab8aaa;
  box-shadow:
    0 0 65px #ff32324d,
    inset 0 0 45px #f336363d;
}
.boss-stage[data-milestone="100"] .rune-ring {
  border-color: #ffce83aa;
  box-shadow: 0 0 50px #ffd07a24;
}
.milestone-rail {
  display: grid;
  grid-template-columns: repeat(4, minmax(0, 1fr));
  gap: 8px;
  list-style: none;
  padding: 0;
  margin: 15px 0;
}
.milestone-rail li {
  font-size: 0.7rem;
  color: var(--muted);
  border-left: 2px solid #653141;
  padding-left: 8px;
}
.milestone-rail li > span {
  display: block;
}
.milestone-rail strong {
  font-size: 0.8rem;
  color: var(--accent);
}
.milestone-rail small {
  display: block;
  font-size: 0.66rem;
  margin: 4px 0;
  min-height: 2.7em;
}
.milestone-rail .score {
  font-size: 0.64rem;
}
.milestone-banner {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 15px;
  background: #4b2630;
  border: 1px solid #ff8b89;
  border-radius: 12px;
  padding: 15px 18px;
  margin-bottom: 18px;
  font-size: 0.91rem;
}
.dismiss-error {
  display: block;
  margin: -11px 0 18px;
  color: var(--accent);
  padding-left: 0;
}
.raid-recognition,
.victory-recap {
  padding: 25px;
  margin-top: 24px;
}
.raid-recognition h2,
.victory-recap h2 {
  font-size: 1.45rem;
}
.share-tools {
  display: flex;
  align-items: flex-end;
  flex-direction: column;
  gap: 7px;
}
.share-tools input {
  max-width: 330px;
}
.share-tools #shareResult {
  max-width: 300px;
  text-align: right;
}
.badge-grid {
  display: grid;
  grid-template-columns: repeat(3, minmax(0, 1fr));
  gap: 12px;
  list-style: none;
  padding: 0;
  margin: 20px 0 14px;
}
.badge-grid li {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 13px;
  padding: 16px;
  border: 1px solid var(--line);
  border-radius: 10px;
  background: #20171d;
}
.badge-grid li.earned {
  border-color: #ba7154;
  background: linear-gradient(120deg, #442822, #27191d);
}
.badge-grid strong {
  font-size: 0.82rem;
  display: block;
}
.badge-grid small {
  display: block;
  font-size: 0.73rem;
  color: var(--muted);
  margin-top: 7px;
}
.badge-grid .score {
  font-size: 0.66rem;
  color: var(--muted);
}
.badge-grid .earned .score {
  color: #ffd18b;
}
.victory-recap {
  border-color: #b6874d;
  background: linear-gradient(120deg, #3c291c, #251920);
}
.victory-recap > p {
  color: #e5c5a2;
}
.victory-recap details {
  padding-top: 15px;
  border-top: 1px solid #7b503f;
}
.victory-recap #allContributors {
  max-height: 420px;
  overflow: auto;
  padding-right: 10px;
}
.personal-stats {
  grid-template-columns: repeat(3, minmax(0, 1fr));
  gap: 10px;
}
.personal-stats strong {
  font-size: 1.2rem;
}
.personal-stats span,
.raid-stats span {
  font-size: 0.75rem;
}
.raider-name {
  font-size: 0.75rem;
}
.attack-panel > #raidReset {
  font-size: 0.72rem;
}
.attack-hint {
  font-size: 0.75rem;
}
.attack-panel .eyebrow,
.arena-heading .eyebrow {
  font-size: 0.66rem;
}
.strike-options small {
  font-size: 0.65rem;
}
.strike-options strong {
  font-size: 0.87rem;
}
.weakness-box small {
  font-size: 0.65rem;
}
.weakness-box div > span,
.combo-row {
  font-size: 0.75rem;
}
.raid-fineprint p,
.combat-list small {
  font-size: 0.78rem;
}
.combat-list li {
  font-size: 0.85rem;
}
.combat-list strong {
  font-size: 0.88rem;
}
.boss-story {
  font-size: 0.84rem;
}
.instruction-grid p {
  font-size: 0.9rem;
}
.boss-live {
  font-size: 0.78rem;
}
.raid-list .eyebrow {
  font-size: 0.7rem;
}
.mobile-attack-dock {
  display: none;
}
.strike-options .ui-icon {
  display: block;
  margin: 0 auto;
}
.boss-page .footer {
  padding-bottom: 30px;
}
@media (max-width: 800px) {
  .badge-grid {
    grid-template-columns: 1fr;
  }
  .badge-grid small {
    margin-top: 4px;
  }
  .raid-recognition .section-title {
    align-items: flex-start;
    flex-direction: column;
    gap: 16px;
  }
  .share-tools {
    align-items: flex-start;
  }
  .share-tools #shareResult {
    text-align: left;
  }
}
@media (max-width: 650px) {
  body[data-page="boss"] {
    padding-bottom: 116px;
  }
  .mobile-attack-dock {
    display: flex;
    position: fixed;
    z-index: 6;
    bottom: 0;
    left: 0;
    right: 0;
    align-items: center;
    justify-content: space-between;
    gap: 13px;
    padding: 12px 16px calc(12px + env(safe-area-inset-bottom));
    background: #22141cf5;
    border-top: 1px solid #a95361;
    backdrop-filter: blur(12px);
    box-shadow: 0 -8px 25px #0005;
  }
  .mobile-attack-dock > div {
    width: 125px;
    flex-shrink: 0;
  }
  .mobile-attack-dock label {
    font-size: 0.66rem;
    display: block;
    color: var(--muted);
    margin-bottom: 3px;
  }
  .mobile-attack-dock select {
    padding: 6px 9px;
    min-height: 34px;
    font-size: 0.8rem;
  }
  .mobile-attack-dock small {
    font-size: 0.64rem;
    color: var(--muted);
    display: block;
    margin-top: 4px;
  }
  .mobile-attack-dock .button {
    flex: 1;
    white-space: normal;
    min-height: 49px;
    padding: 10px 8px;
    font-size: 0.78rem;
  }
  .milestone-rail {
    gap: 5px;
  }
  .milestone-rail small {
    font-size: 0.65rem;
  }
  .milestone-rail li {
    padding-left: 5px;
  }
  .personal-stats strong {
    font-size: 1.15rem;
  }
  .raid-recognition,
  .victory-recap {
    padding: 22px;
  }
  .badge-grid strong {
    font-size: 0.87rem;
  }
  .badge-grid small {
    font-size: 0.8rem;
  }
  .attack-panel .eyebrow {
    font-size: 0.62rem;
  }
  .attack-panel {
    padding: 22px;
  }
  .raid-fineprint p {
    font-size: 0.8rem;
  }
  .combat-list small {
    font-size: 0.72rem;
  }
  .boss-heading .lead {
    font-size: 0.94rem;
  }
}

/* Compact identity controls and achievements keep the arena uncluttered. */
.player-name-form {
  display: grid;
  gap: 0.45rem;
  margin: 1rem 0;
}
.player-name-row {
  display: flex;
  gap: 0.5rem;
}
.player-name-row input {
  flex: 1;
  min-width: 0;
  width: 100%;
}
.boss-admin-leaders {
  margin: 1.5rem 0;
}
.badge-grid {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 0.5rem;
}
.badge-grid li {
  border: 1px solid var(--line);
  border-radius: 12px;
  padding: 0.85rem;
}
#rearmHint {
  min-height: 1.4em;
  margin: 0.5rem 0;
}
@media (max-width: 600px) {
  .badge-grid {
    grid-template-columns: 1fr;
  }
}

/* Comfort controls stay quiet so the arena and primary attack keep focus. */
.player-identity {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 1rem;
  padding: 0.8rem 0;
  border-bottom: 1px solid var(--line);
  margin-bottom: 0.5rem;
}
.player-identity span {
  min-width: 0;
  overflow-wrap: anywhere;
}
.player-identity[hidden],
.player-name-form[hidden],
[hidden] {
  display: none !important;
}
.profile-recovery {
  font-size: 0.82rem;
  margin: 0.65rem 0 1rem;
}
.profile-recovery summary {
  color: var(--muted);
  cursor: pointer;
}
.profile-recovery .stack,
#recoveryOwner {
  margin-top: 0.85rem;
}
.profile-recovery textarea {
  width: 100%;
  resize: vertical;
  font: inherit;
  overflow-wrap: anywhere;
}
.attack-button,
#dockAttack {
  min-height: 3.5rem;
  font-variant-numeric: tabular-nums;
}
.attack-button {
  width: 100%;
}
#dockAttack {
  flex: 1;
  min-width: 0;
}
.rally-status {
  border: 1px solid var(--line);
  border-radius: 12px;
  padding: 0.8rem 1rem;
  margin: 1rem 0;
  text-align: left;
  background: rgba(255, 255, 255, 0.025);
}
.rally-status > div {
  display: flex;
  flex-wrap: wrap;
  justify-content: space-between;
  gap: 0.5rem;
  font-size: 0.85rem;
}
.rally-status progress {
  width: 100%;
  height: 5px;
  accent-color: #ff3a43;
  margin: 0.6rem 0 0.2rem;
}
.rally-status small {
  color: var(--muted);
}
.rally-status.unlocked {
  border-color: #ff4b5666;
  background: #e8243210;
}
.rally-lit {
  background: radial-gradient(ellipse at center, #fa29363d, transparent 70%);
}
.rally-lit .rune-ring {
  border-color: #ff6874;
  box-shadow: 0 0 32px #ff283844;
}
.exact-totals {
  text-align: left;
  font-size: 0.75rem;
  color: var(--muted);
  margin-top: 0.6rem;
}
.exact-totals summary {
  cursor: pointer;
}
.boss-balance {
  padding: 1rem;
  margin: 1rem 0;
  border: 1px solid var(--line);
  border-radius: 12px;
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 1rem;
}
.boss-balance h3 {
  margin: 0.25rem 0 0.7rem;
}
.edit-preview {
  display: block;
  background: #ffffff06;
  border: 1px solid var(--line);
  border-left: 3px solid #f44952;
  border-radius: 8px;
  padding: 0.8rem;
  font-size: 0.82rem;
  line-height: 1.65;
  overflow-wrap: anywhere;
  font-variant-numeric: tabular-nums;
}
.preset-row {
  display: flex;
  flex-wrap: wrap;
  gap: 0.5rem;
  grid-column: 1/-1;
}
.audit-list {
  max-height: 26rem;
  overflow: auto;
}
.audit-list li {
  align-items: flex-start;
}
.audit-list small {
  max-width: 70ch;
  white-space: normal;
  overflow-wrap: anywhere;
}
.audit-list .score {
  font-size: 0.75rem;
  white-space: normal;
  min-width: 7rem;
  text-align: right;
}
#bossHealth {
  overflow-wrap: anywhere;
}
@media (max-width: 640px) {
  .boss-balance {
    grid-template-columns: 1fr;
  }
  .audit-list li {
    flex-direction: column;
    gap: 0.5rem;
  }
  .audit-list .score {
    text-align: left;
  }
}
@media (prefers-reduced-motion: reduce) {
  .rally-lit,
  .rally-status {
    transition: none;
  }
}
```

## static/boss.js

```javascript
/* Shared raid UI. The server owns damage, identity, cooldowns and private names.
   Polling never attacks. A failed POST keeps its receipt ID for a safe retry. */
(() => {
  "use strict";
  const root = document.querySelector("[data-boss-root]");
  if (!root) return;
  const admin = root.dataset.mode === "admin";
  const $ = (id) => root.querySelector("#" + id);
  const text = (id, value) => {
    const el = $(id);
    if (el) el.textContent = String(value);
  };
  const number = (value) =>
    (typeof value === "bigint" ? value : Number(value)).toLocaleString("en-US");
  const compact = new Intl.NumberFormat("en-US", {
    notation: "compact",
    maximumFractionDigits: 1,
  });
  function metric(id, value) {
    text(id, Math.abs(value) >= 10000 ? compact.format(value) : number(value));
    const el = $(id);
    if (el) {
      el.title = number(value);
      el.setAttribute("aria-label", number(value));
    }
  }
  let editingName = false;
  let labels = {};
  let armed = true,
    lockedButton = null,
    inputMode = "mouse",
    keyHeld = false,
    nameDirty = false;
  const nameInput = $("playerUsername");
  nameInput?.addEventListener("input", () => {
    nameDirty = true;
  });
  const listCache = new Map();
  const effects = new Map();
  const button = $("attackButton"),
    dockButton = $("dockAttack"),
    stage = $("bossStage");
  let state,
    csrf = "",
    selected = "blade",
    busy = false,
    timer,
    polling = false,
    authExpired = false,
    pendingWrites = 0,
    mutationEpoch = 0;
  let receivedAt = performance.now(),
    lastGood = -Infinity,
    pending = null,
    lastAnimated = "";
  let milestoneTimer,
    recapRaid = "",
    recapPending = false;
  const pendingKey = "rh.boss.pending";
  // Session storage remembers a click if the connection drops or the tab reloads.
  // Gameplay still works in browsers that disable storage; cookies are required.
  try {
    pending = JSON.parse(sessionStorage.getItem(pendingKey));
    selected = localStorage.getItem("rh.boss.style") || "blade";
  } catch (_) {
    /* optional */
  }
  function remember(value) {
    pending = value;
    try {
      value
        ? sessionStorage.setItem(pendingKey, JSON.stringify(value))
        : sessionStorage.removeItem(pendingKey);
    } catch (_) {
      /* optional */
    }
  }
  function error(message = "") {
    const el = $("bossError");
    if (el) {
      el.hidden = !message;
      el.textContent = message;
    }
    if ($("dismissBossError")) $("dismissBossError").hidden = !message;
  }
  const now = () =>
    state ? state.server_time + (performance.now() - receivedAt) / 1000 : 0;
  function duration(seconds) {
    const s = Math.max(0, Math.ceil(seconds));
    return s >= 3600
      ? `${Math.floor(s / 3600)}h ${Math.floor((s % 3600) / 60)}m`
      : `${Math.floor(s / 60)}:${String(s % 60).padStart(2, "0")}`;
  }
  function strikeFeedback(hit, receipt) {
    if (!hit || receipt === lastAnimated) return;
    lastAnimated = receipt;
    text(
      "hitResult",
      `${hit.burst ? "CRIMSON BURST! " : ""}${labels[hit.style]} hit for ${number(hit.damage)}${hit.weakness ? " · Weakness matched!" : " · Nice hit."}`,
    );
    text("hitFloat", "−" + number(hit.damage));
    if (
      stage &&
      !window.matchMedia?.("(prefers-reduced-motion: reduce)").matches
    ) {
      const sprite = stage.querySelector(".boss-sprite"),
        float = $("hitFloat");
      for (const [element, frames, duration] of [
        [
          sprite,
          [
            { transform: "translateX(0)" },
            { transform: "translateX(-8px) rotate(-3deg)" },
            { transform: "translateX(6px)" },
            { transform: "translateX(0)" },
          ],
          400,
        ],
        [
          float,
          [
            { opacity: 1, transform: "translate(-50%,0) scale(.8)" },
            {
              opacity: 1,
              transform: "translate(-50%,-15px) scale(1.1)",
              offset: 0.25,
            },
            { opacity: 0, transform: "translate(-50%,-65px)" },
          ],
          800,
        ],
      ]) {
        if (element?.animate) {
          effects.get(element)?.cancel();
          effects.set(
            element,
            element.animate(frames, { duration, easing: "ease-out" }),
          );
        }
      }
    }
  }
  function rows(id, values, empty, mapper) {
    const list = $(id);
    if (!list) return;
    const signature = JSON.stringify(values),
      previous = listCache.get(id);
    if (previous?.signature === signature) return;
    const records = new Map();
    const nodes = values.map((value, index) => {
      const key = String(
        value.id || (value.name ? value.name + ":" + (value.at || "") : index),
      );
      const rowSignature = JSON.stringify([value, index]);
      const old = previous?.records.get(key);
      const node =
        old?.signature === rowSignature ? old.node : mapper(value, index);
      records.set(key, { signature: rowSignature, node });
      return node;
    });
    if (!nodes.length) {
      const li = document.createElement("li");
      li.className = "muted";
      li.textContent = empty;
      nodes.push(li);
    }
    // Retain untouched nodes, keyboard focus and scroll position between polls.
    nodes.forEach((node, index) => {
      if (list.children[index] !== node)
        list.insertBefore(node, list.children[index] || null);
    });
    while (list.children.length > nodes.length) list.lastElementChild.remove();
    listCache.set(id, { signature, records });
  }
  function item(title, detail, score, self = false) {
    const li = document.createElement("li"),
      left = document.createElement("span"),
      strong = document.createElement("strong"),
      small = document.createElement("small"),
      right = document.createElement("span");
    strong.textContent = title;
    small.textContent = detail;
    right.textContent = score;
    right.className = "score";
    left.append(strong, small);
    li.append(left, right);
    if (self) li.className = "self";
    return li;
  }
  function apply(value) {
    const next = value.state;
    if (
      !next ||
      typeof next.raid_id !== "string" ||
      !Number.isFinite(next.server_time) ||
      !next.you
    )
      throw new Error(
        "The game returned an incomplete update. Reload in a moment.",
      );
    // Committed revisions outrank request clocks: a username save can wait
    // behind another hit while a poll starts later and returns first.
    if (state) {
      const sameRaid = next.raid_id === state.raid_id;
      if (
        (sameRaid &&
          (next.version < state.version ||
            (next.health_revision || 0) < (state.health_revision || 0) ||
            (next.settings_revision || 0) < (state.settings_revision || 0))) ||
        ((!sameRaid || next.version === state.version) &&
          next.server_time < state.server_time)
      )
        return;
    }
    // Only a newer explicit host health revision may change maximum HP.
    // Ordinary snapshots cannot heal the same boss on screen.
    // Keep the last confirmed state and let stale-state handling disable hits;
    // never fabricate a lower HP value while accepting inconsistent counters.
    if (
      state &&
      next.raid_id === state.raid_id &&
      (next.total_damage < state.total_damage ||
        next.total_attacks < state.total_attacks ||
        ((next.health_revision || 0) === (state.health_revision || 0) &&
          (next.hp > state.hp || next.max_hp !== state.max_hp)))
    )
      throw new Error(
        "Boss progress moved backwards; retaining the last confirmed state.",
      );
    if (value.csrf) csrf = value.csrf;
    state = next;
    labels = state.rules.styles;
    text("bossName", state.name || "Crimson Hunllef");
    root.querySelectorAll("[data-boss-avatar]").forEach((image) => {
      if (state.avatar_url && image.getAttribute("src") !== state.avatar_url)
        image.src = state.avatar_url;
      image.classList.toggle("custom-avatar", Boolean(state.avatar_custom));
      if (image.classList.contains("boss-sprite"))
        image.alt = state.name || "Crimson Hunllef";
    });
    receivedAt = performance.now();
    lastGood = receivedAt;
    if (
      pending &&
      (pending.raid_id !== state.raid_id || pending.name !== state.you.name)
    )
      remember(null);
    if (pending && state.you.last_request === pending.request_id) {
      strikeFeedback(state.you.last_hit, pending.request_id);
      remember(null);
      error();
    }
    text("bossConnection", "Live · Shared raid connected");
    text(
      "bossHealth",
      `${compact.format(state.hp)} / ${compact.format(state.max_hp)} HP`,
    );
    if ($("bossHealth"))
      $("bossHealth").title =
        `${number(state.hp)} / ${number(state.max_hp)} HP`;
    text(
      "exactRaidTotals",
      `${number(state.hp)} / ${number(state.max_hp)} HP · ${number(state.total_damage)} damage · ${number(state.total_attacks)} hits`,
    );
    text(
      "bossPercent",
      (((state.max_hp - state.hp) / state.max_hp) * 100).toFixed(2) +
        "% defeated",
    );
    const bar = $("bossHealthBar");
    if (bar) {
      bar.max = state.max_hp;
      bar.value = state.max_hp - state.hp;
    }
    text(
      "bossPhase",
      state.status === "victory"
        ? "DEFEATED"
        : state.status === "paused"
          ? "PAUSED"
          : state.phase,
    );
    text("bossDay", "Raid day " + state.day);
    text("bossRaiders", number(state.raiders));
    text("bossAttacks", number(state.total_attacks));
    metric("bossDamage", state.total_damage);
    const story =
      state.status === "victory"
        ? "VICTORY. The Red crew brought the beast down. Every hit made this happen."
        : state.status === "paused"
          ? "The host has paused attacks. Your progress is safe; the raid-day clock keeps running."
          : state.status === "waiting"
            ? "The first strike starts the raid. Let’s wake the beast."
            : state.phase === "Last stand"
              ? "Last stand. The beast is cornered. Rally the crew and finish what you started."
              : state.phase === "Enraged"
                ? "Enraged. The arena is heating up. Watch the weakness and keep the pressure on."
                : "Awakening. The beast stirs. Small hits become a massive takedown.";
    text("bossStory", story);
    if (stage) stage.classList.toggle("victory", state.status === "victory");
    text(
      "bossWeakness",
      `${state.weakness_label} · ${number(state.rules.weak_damage)} damage`,
    );
    root
      .querySelectorAll("[data-style]")
      .forEach((el) =>
        el.classList.toggle("is-weak", el.dataset.style === state.weakness),
      );
    text("yourName", state.you.name);
    metric("yourDamage", state.you.damage);
    text("yourAttacks", number(state.you.attacks));
    if (nameInput && !nameDirty && document.activeElement !== nameInput)
      nameInput.value = state.you.display_name || "";
    identityView();
    rally();
    if (admin) adminTools();
    if (admin)
      rows(
        "adminBossLeaders",
        state.admin_leaders || [],
        "No hits yet.",
        (r, i) =>
          item(
            `${i + 1}. ${r.name}`,
            `${r.alias} · ${number(r.attacks)} hits · ${r.name_provided ? (r.shuffle_name_in_feed ? "Shuffle name match · unverified" : "Self-reported") : "Username not supplied yet"}`,
            number(r.damage),
          ),
      );

    text(
      "burstLabel",
      state.you.burst_in === 1
        ? `NEXT HIT: +${state.rules.burst_bonus} damage`
        : `${state.you.burst_in} hits to +${state.rules.burst_bonus} damage`,
    );
    root
      .querySelectorAll("#burstMeter span")
      .forEach((el, i) =>
        el.classList.toggle(
          "filled",
          i < state.rules.burst_every - state.you.burst_in,
        ),
      );
    rows(
      "bossLeaders",
      state.leaders,
      "Land the first hit to lead the charge.",
      (r, i) =>
        item(
          `${String(i + 1).padStart(2, "0")}  ${r.name}${r.you ? " · You" : ""}`,
          `${number(r.attacks)} hits`,
          number(r.damage),
          r.you,
        ),
    );
    rows(
      "bossRecent",
      state.recent,
      "The arena is waiting for your community.",
      (r) =>
        item(
          r.name,
          `${labels[r.style]}${r.burst ? " · Burst" : ""}${r.weakness ? " · Weakness" : ""} · ${new Date(r.at * 1000).toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" })}`,
          "−" + number(r.damage),
        ),
    );
    rows(
      "bossHistory",
      state.history.slice().reverse(),
      "The first chapter is yours to write.",
      (r) =>
        item(
          r.outcome,
          `${number(r.raiders)} raiders · ${number(r.attacks)} hits · ${new Date(r.ended_at * 1000).toLocaleDateString()}`,
          number(r.damage) + " damage",
        ),
    );
    achievements();
    if (!admin && state.status === "victory") void recap();
    tick();
  }
  function identityView() {
    if (admin) return;
    const own = Boolean(state.you.display_name);
    text("playingAs", state.you.display_name || "");
    if ($("playerIdentity"))
      $("playerIdentity").hidden =
        !own || !state.you.identity_ready || editingName;
    if ($("playerNameForm"))
      $("playerNameForm").hidden =
        own && state.you.identity_ready && !editingName;
    if ($("recoveryOwner")) $("recoveryOwner").hidden = !own;
    text(
      "recoverySaved",
      state.you.recovery_saved
        ? "Recovery code created. Creating another replaces the previous code."
        : "Save a code to keep your player if cookies are cleared.",
    );
  }
  function rally() {
    const r = state.rally;
    if (!r) return;
    stage?.classList.toggle("rally-lit", Boolean(r.unlocked));
    $("rallyStatus")?.classList.toggle("unlocked", Boolean(r.unlocked));
    text("rallyTitle", r.unlocked ? "Red rally · Arena lit" : "Red rally");
    text("rallyCount", `${r.count} / ${r.goal} raiders`);
    text(
      "rallyHint",
      r.unlocked
        ? "Unlocked together for this raid."
        : "15 raiders hit within 10 minutes to light the arena.",
    );
    if ($("rallyBar")) {
      $("rallyBar").max = r.goal;
      $("rallyBar").value = r.count;
    }
  }
  const changeLabels = {
    hp: "Remaining HP",
    max_hp: "Maximum HP",
    damage: "Base",
    weak_damage: "Weakness",
    burst_bonus: "Burst bonus",
    paused: "Paused",
    name: "Name",
    player: "Player",
    slots: "Players",
    avatar: "Avatar",
    connection: "Connection",
  };
  function displayChange(key, value) {
    if (key === "avatar" && typeof value === "string" && value.length === 64)
      return "Image " + value.slice(0, 8);
    return typeof value === "number" ? number(value) : String(value);
  }
  function adminTools() {
    const b = state.balance;
    if (b) {
      text(
        "bossPace",
        b.observed
          ? `${number(b.damage_per_hour)} damage / hour`
          : "Collecting recent hits…",
      );
      text(
        "bossEstimate",
        state.status === "victory"
          ? "Boss defeated."
          : b.observed
            ? `About ${b.remaining_seconds >= 86400 ? (b.remaining_seconds / 86400).toFixed(1) + " days" : duration(b.remaining_seconds)} remaining at this pace · ${number(b.sample_hits)} recent hits`
            : `${number(b.sample_hits)} recent hits. Estimates appear after 5 minutes and 10 hits with damage.`,
      );
      const presets = $("raidPresets");
      if (presets) {
        for (const p of b.presets) {
          let el = [...presets.children].find(
            (e) => e.dataset.days === String(p.days),
          );
          if (!el) {
            el = document.createElement("button");
            el.type = "button";
            el.className = "button small";
            el.dataset.days = String(p.days);
            el.addEventListener("click", () => {
              $("bossHealthInput").value = el.dataset.hp;
              $("bossHealthInput").focus();
            });
            presets.append(el);
          }
          el.dataset.hp = String(p.hp);
          el.textContent = `${p.label} · ${compact.format(p.hp)} HP`;
          el.title = `${number(p.hp)} HP${b.observed ? ` · about ${p.days} days at recent pace` : " · starting suggestion"}`;
        }
      }
      text(
        "presetBasis",
        b.observed
          ? "Presets target roughly 3, 5 or 7 days at the observed pace. They fill the next-raid field only; review and confirm to start."
          : "Starting suggestions: 10M / 25M / 50M HP. Duration is unknown until activity is measured. These only fill the next-raid field.",
      );
    }
    rows(
      "bossAdminHistory",
      (state.admin_history || []).map((h, i) => ({
        ...h,
        id: String(h.at) + ":" + i,
      })),
      "No host edits recorded in this release yet.",
      (h) => {
        const keys = [
          ...new Set([...Object.keys(h.before), ...Object.keys(h.after)]),
        ];
        const changes = keys
          .filter((k) => h.before[k] !== h.after[k])
          .map(
            (k) =>
              `${changeLabels[k] || k}: ${displayChange(k, h.before[k])} → ${displayChange(k, h.after[k])}`,
          );
        return item(
          `${h.action} · ${h.actor}`,
          changes.join(" · ") || "Action confirmed; values unchanged.",
          new Date(h.at * 1000).toLocaleString(),
        );
      },
    );
    rows(
      "bossAbuseFlags",
      (state.abuse_flags || []).map((f, i) => ({ ...f, id: String(i) + f.at })),
      "No bursts of rejected requests detected.",
      (f) =>
        item(
          `${f.alias} · ${f.category}`,
          `${f.rejected} rejected requests · Browser ${f.tag}`,
          new Date(f.at * 1000).toLocaleTimeString(),
        ),
    );
    previews();
  }
  function whole(id) {
    const value = $(id)?.value || "";
    if (!/^\d+$/.test(value)) return null;
    const n = BigInt(value);
    return n <= BigInt(Number.MAX_SAFE_INTEGER) ? n : null;
  }
  function previews() {
    if (!admin || !state) return;
    const hp = BigInt(state.hp),
      max = BigInt(state.max_hp),
      nextMax = whole("bossMaxHealth"),
      remaining = whole("bossRemainingHealth");
    if (nextMax !== null && nextMax > 0n) {
      const next = hp + nextMax - max;
      text(
        "maxHealthPreview",
        `Remaining HP: ${number(hp)} → ${number(next < 0n ? 0n : next > nextMax ? nextMax : next)} · Maximum: ${number(max)} → ${number(nextMax)}`,
      );
    } else text("maxHealthPreview", "Enter a valid whole-number maximum HP.");
    text(
      "remainingHealthPreview",
      remaining !== null && remaining <= max
        ? `Remaining HP: ${number(hp)} → ${number(remaining)}${remaining > hp ? " · Explicit heal" : remaining === 0n ? " · Defeats the boss" : ""}`
        : "Remaining HP must be between 0 and the current maximum.",
    );
    const base = whole("bossBaseDamage"),
      weak = whole("bossWeakDamage"),
      burst = whole("bossBurstBonus");
    text(
      "damagePreview",
      [base, weak, burst].every((n) => n !== null)
        ? `Next hit: base ${number(base)} · weakness ${number(weak)}. Every tenth hit: base ${number(base + burst)} · weakness ${number(weak + burst)}. Actual damage stops at remaining HP.`
        : "Enter valid whole-number damage values.",
    );
  }
  root
    .querySelectorAll(
      "#bossMaxHealth, #bossRemainingHealth, #bossBaseDamage, #bossWeakDamage, #bossBurstBonus",
    )
    .forEach((el) => el.addEventListener("input", previews));
  $("editPlayerName")?.addEventListener("click", () => {
    editingName = true;
    identityView();
    nameInput?.focus();
  });
  $("makeRecoveryCode")?.addEventListener("click", async (event) => {
    const el = event.currentTarget;
    el.disabled = true;
    try {
      const { response, value } = await request("/play/api/recovery-code", {
        method: "POST",
        headers: { "X-CSRF-Token": csrf },
      });
      if (!response.ok)
        throw new Error(value.error || "Could not create a recovery code.");
      apply(value);
      $("recoveryCode").value = value.code;
      $("recoveryCodeBox").hidden = false;
      text(
        "recoveryResult",
        "Save this code somewhere private. It is only shown here.",
      );
    } catch (e) {
      text("recoveryResult", e.message);
    } finally {
      el.disabled = false;
    }
  });
  $("downloadRecovery")?.addEventListener("click", () => {
    const blob = new Blob(
      [
        "RedHunllef player recovery code\nKeep private. Paste into Player recovery at /play.\n\n" +
          $("recoveryCode").value +
          "\n",
      ],
      { type: "text/plain;charset=utf-8" },
    );
    const url = URL.createObjectURL(blob),
      link = document.createElement("a");
    link.href = url;
    link.download = "redhunllef-player-recovery.txt";
    link.click();
    setTimeout(() => URL.revokeObjectURL(url), 1000);
  });
  $("recoverPlayerForm")?.addEventListener("submit", async (event) => {
    event.preventDefault();
    const el = event.currentTarget.querySelector("button");
    el.disabled = true;
    try {
      const { response, value } = await request("/play/api/recover", {
        method: "POST",
        headers: { "Content-Type": "application/json", "X-CSRF-Token": csrf },
        body: JSON.stringify({
          raid_id: state.raid_id,
          code: $("recoveryInput").value.trim(),
        }),
      });
      if (!response.ok) throw new Error(value.error || "Recovery failed.");
      remember(null);
      editingName = false;
      nameDirty = false;
      apply(value);
      $("recoveryInput").value = "";
      text(
        "recoveryResult",
        "Player restored. Your hits, badges and cooldown were kept.",
      );
    } catch (e) {
      text("recoveryResult", e.message);
    } finally {
      el.disabled = false;
    }
  });
  function achievements() {
    const milestones = state.milestones || [],
      achieved = milestones.filter((m) => m.reached);
    const level = achieved.at(-1)?.percent || 0;
    if (stage) stage.dataset.milestone = String(level);
    rows("bossMilestones", milestones, "", (m) =>
      item(
        `${m.reached ? "✓" : "◇"} ${m.percent}%`,
        m.label,
        m.reached ? "Reached" : "Next",
      ),
    );
    rows(
      "yourBadges",
      state.you.badges || [],
      "Land a hit to earn your first badge.",
      (b) => {
        const li = item(
          b.label,
          b.description,
          b.earned ? "Earned" : `${b.progress || 0} / ${b.target || 1}`,
        );
        li.classList.toggle("earned", b.earned);
        return li;
      },
    );
    text("yourActiveDays", state.you.active_days || 0);
    text(
      "badgeCount",
      `${(state.you.badges || []).filter((b) => b.earned).length} / 8`,
    );
    if (admin) return;
    const key = "rh.boss.achievements";
    try {
      const old = JSON.parse(sessionStorage.getItem(key) || "null");
      const earned = (state.you.badges || [])
        .filter((b) => b.earned)
        .map((b) => b.id);
      const same = old?.raid === state.raid_id && old?.name === state.you.name;
      const unlocked = same
        ? (state.you.badges || []).filter(
            (b) => b.earned && !old.badges.includes(b.id),
          )
        : [];
      if (same && (level > old.level || unlocked.length)) {
        const message =
          level > old.level
            ? `Community milestone: ${achieved.at(-1).label}! ${level}% conquered together.`
            : `Badge earned: ${unlocked.map((b) => b.label).join(", ")}!`;
        text("milestoneMessage", message);
        const banner = $("milestoneBanner");
        if (banner) banner.hidden = false;
        clearTimeout(milestoneTimer);
        milestoneTimer = setTimeout(() => {
          if (banner) banner.hidden = true;
        }, 8000);
      }
      sessionStorage.setItem(
        key,
        JSON.stringify({
          raid: state.raid_id,
          name: state.you.name,
          level,
          badges: earned,
        }),
      );
    } catch (_) {
      /* Badges still render when browser storage is unavailable. */
    }
    const victory = $("victoryRecap");
    if (victory) victory.hidden = state.status !== "victory";
    if (state.status === "victory")
      text(
        "victorySummary",
        `${number(state.raiders)} raiders · ${number(state.total_attacks)} hits · ${number(state.total_damage)} damage. You contributed ${number(state.you.damage)} damage. Every hit helped.`,
      );
  }
  async function recap() {
    // A host may reopen this same raid with an explicit health edit. Its next
    // victory needs a fresh contributor list, not the previous victory's cache.
    const key = `${state.raid_id}:${state.health_revision || 0}`;
    if (recapRaid === key || recapPending) return;
    recapPending = true;
    const raid = state.raid_id;
    try {
      const { response, value } = await request(
        "/play/api/contributors?raid_id=" + encodeURIComponent(raid),
      );
      if (
        !response.ok ||
        value.raid_id !== state.raid_id ||
        state.status !== "victory" ||
        value.health_revision !== (state.health_revision || 0)
      )
        return;
      rows(
        "allContributors",
        value.contributors,
        "Everyone who landed a hit helped win.",
        (r, i) =>
          item(
            `${i + 1}. ${r.name}`,
            `${number(r.attacks)} hits`,
            number(r.damage),
          ),
      );
      text(
        "recapNote",
        "Every contributor is included, using their raid alias.",
      );
      recapRaid = key;
    } catch (_) {
      text(
        "recapNote",
        "Contributor list is reconnecting. It will retry automatically.",
      );
    } finally {
      recapPending = false;
    }
  }
  function tick() {
    if (!state || authExpired) return;
    const seconds = now(),
      stale = performance.now() - lastGood > 15000;
    text(
      "wardTimer",
      seconds >= state.ward_changes_at
        ? "Weakness changing…"
        : `Changes in ${duration(state.ward_changes_at - seconds)}`,
    );
    text(
      "raidReset",
      state.resets_at
        ? `Next raid day in ${duration(state.resets_at - seconds)}.`
        : "The first community hit starts the 24-hour raid-day schedule.",
    );
    if (!stale)
      text(
        "bossConnection",
        `Live · Last checked ${Math.max(0, Math.floor((performance.now() - lastGood) / 1000))}s ago`,
      );
    else
      text("bossConnection", "Reconnecting · Showing the last confirmed state");
    if (!button) return;
    const active = ["waiting", "active"].includes(state.status);
    // An unacknowledged click can be retried even if its first delivery caused
    // a cooldown or victory. The backend returns the original receipt.
    const retry = Boolean(pending && !busy && !stale && !pendingWrites);
    const ready =
      active &&
      state.connection_ready &&
      state.you.identity_ready &&
      seconds >= state.you.ready_at &&
      !stale &&
      !busy &&
      !pendingWrites;
    button.disabled = !(armed && (retry || ready));
    button.textContent = busy
      ? "Landing your hit…"
      : pendingWrites
        ? "Saving your player…"
        : stale
          ? "Reconnecting…"
          : pending
            ? "Retry last strike"
            : state.status === "victory"
              ? "Victory · We did it!"
              : state.status === "paused"
                ? "Raid paused"
                : !state.connection_ready
                  ? "Connection setup needed"
                  : !state.you.identity_ready
                    ? "Save your username to play"
                    : seconds < state.you.ready_at
                      ? `Next strike in ${duration(state.you.ready_at - seconds)}`
                      : !armed
                        ? inputMode === "keyboard"
                          ? "Release the key to re-arm"
                          : "Move off the button to re-arm"
                        : `Attack with ${labels[selected]} →`;
    text(
      "attackHint",
      pending
        ? "Last strike unconfirmed. Retry safely; it won’t count twice."
        : state.status === "victory"
          ? "You helped write this chapter. The host can open the next raid."
          : !state.you.identity_ready
            ? "Save your username once in this browser."
            : `One strike every ${state.rules.cooldown}s · ${selected === state.weakness ? state.rules.weak_damage : state.rules.damage} damage${state.you.burst_in === 1 ? " + " + state.rules.burst_bonus + " burst" : ""}`,
    );
    if (dockButton) {
      dockButton.disabled = button.disabled;
      dockButton.textContent = button.textContent;
    }
    text("dockRemaining", `${state.rules.cooldown}s cooldown · Unlimited hits`);
    text(
      "rearmHint",
      !armed
        ? inputMode === "keyboard"
          ? "Release Enter or Space before your next hit."
          : "Move your pointer off the attack button before your next hit."
        : "",
    );
    if (stale)
      text("bossConnection", "Reconnecting · Showing the last confirmed state");
  }
  async function request(url, options = {}) {
    const write = options.method === "POST";
    if (write) {
      mutationEpoch++;
      pendingWrites++;
      tick();
    }
    const controller = new AbortController(),
      timeout = setTimeout(() => controller.abort(), 10000);
    try {
      const response = await fetch(url, {
        ...options,
        credentials: "same-origin",
        cache: "no-store",
        signal: controller.signal,
        headers: { Accept: "application/json", ...options.headers },
      });
      if (!response.headers.get("content-type")?.includes("application/json"))
        throw new Error(
          "The game server returned an unexpected response. Try again in a moment.",
        );
      return { response, value: await response.json() };
    } finally {
      clearTimeout(timeout);
      if (write) {
        pendingWrites--;
        tick();
        // Refresh after applying the POST result, including failures. This also
        // replaces any stale poll discarded while the player was being saved.
        if (!pendingWrites) {
          clearTimeout(timer);
          timer = setTimeout(poll, 0);
        }
      }
    }
  }
  async function poll() {
    clearTimeout(timer);
    if (document.hidden || polling || authExpired || pendingWrites) return;
    polling = true;
    const epoch = mutationEpoch;
    try {
      const { response, value } = await request(
        admin ? "/admin/boss/status" : "/play/api/state",
      );
      if (!response.ok) {
        if (admin && response.status === 401) {
          authExpired = true;
          rows(
            "adminBossLeaders",
            [],
            "Sign in again to see private names.",
            () => null,
          );
          for (const id of ["bossAdminHistory", "bossAbuseFlags"])
            rows(id, [], "Sign in again to view this information.", () => null);
          root.querySelectorAll("form button, form input").forEach((el) => {
            el.disabled = true;
          });
          text("bossConnection", "Session expired · Sign in again");
          clearTimeout(timer);
          polling = false;
          return;
        }
        throw new Error(value.error || "The raid is temporarily unavailable.");
      }
      if (epoch === mutationEpoch && !pendingWrites) apply(value);
    } catch (_) {
      text("bossConnection", "Reconnecting · Your saved damage is safe");
      tick();
    } finally {
      polling = false;
      if (!document.hidden && !authExpired)
        timer = setTimeout(poll, (state?.rules.poll_seconds || 5) * 1000);
    }
  }
  function choose(style) {
    if (!labels[style]) return;
    selected = style;
    try {
      localStorage.setItem("rh.boss.style", style);
    } catch (_) {
      /* storage is optional */
    }
    root
      .querySelectorAll("[data-style]")
      .forEach((b) =>
        b.setAttribute("aria-pressed", String(b.dataset.style === style)),
      );
    if ($("dockStyle")) $("dockStyle").value = style;
    tick();
  }
  root
    .querySelectorAll("[data-style]")
    .forEach((el) =>
      el.addEventListener("click", () => choose(el.dataset.style)),
    );
  $("dockStyle")?.addEventListener("change", (event) =>
    choose(event.target.value),
  );
  function rearm() {
    armed = true;
    lockedButton = null;
    tick();
  }
  for (const control of [button, dockButton].filter(Boolean)) {
    control.addEventListener("pointerdown", (event) => {
      inputMode = event.pointerType || "mouse";
    });
    control.addEventListener("pointerleave", () => {
      if (lockedButton === control && inputMode !== "keyboard") rearm();
    });
    control.addEventListener("keydown", (event) => {
      if (!["Enter", " "].includes(event.key)) return;
      if (event.repeat) {
        event.preventDefault();
        return;
      }
      inputMode = "keyboard";
      keyHeld = true;
    });
    // Mouse click latches until the pointer leaves. Touch taps naturally leave
    // the surface on release. Keyboard users must release their activation key.
    control.addEventListener("click", (event) => {
      void attack(event, control);
    });
  }
  document.addEventListener("keyup", (event) => {
    if (["Enter", " "].includes(event.key)) {
      keyHeld = false;
      if (inputMode === "keyboard") rearm();
    }
  });
  document.addEventListener("pointermove", (event) => {
    if (
      armed ||
      !lockedButton ||
      inputMode === "keyboard" ||
      event.pointerType === "touch"
    )
      return;
    const r = lockedButton.getBoundingClientRect();
    if (
      event.clientX < r.left ||
      event.clientX > r.right ||
      event.clientY < r.top ||
      event.clientY > r.bottom
    )
      rearm();
  });
  // A name is saved by the server, never trusted from attack JSON or a URL.
  $("playerNameForm")?.addEventListener("submit", async (event) => {
    event.preventDefault();
    const submitted = nameInput.value;
    const save = event.currentTarget.querySelector("button");
    save.disabled = true;
    try {
      const { response, value } = await request("/play/api/profile", {
        method: "POST",
        headers: { "Content-Type": "application/json", "X-CSRF-Token": csrf },
        body: JSON.stringify({ raid_id: state.raid_id, username: submitted }),
      });
      if (!response.ok)
        throw new Error(value.error || "Your username could not be saved.");
      if (nameInput.value === submitted) nameDirty = false;
      editingName = false;
      apply(value);
      text(
        "playerNameResult",
        "Saved · Admins can see your full submitted name.",
      );
    } catch (e) {
      text("playerNameResult", e.message);
    } finally {
      save.disabled = false;
    }
  });
  $("dismissBossError")?.addEventListener("click", () => error());
  $("dismissMilestone")?.addEventListener("click", () => {
    $("milestoneBanner").hidden = true;
  });
  $("copyRaidLink")?.addEventListener("click", async () => {
    const url = new URL("/play", location.origin).href;
    try {
      await navigator.clipboard.writeText(url);
      text("shareResult", "Raid link copied. Rally the crew!");
    } catch {
      const fallback = $("shareUrl");
      if (fallback) {
        fallback.hidden = false;
        fallback.value = url;
        fallback.focus();
        fallback.select();
      }
      text("shareResult", "Select and copy your raid link.");
    }
  });
  async function attack(event, control) {
    if (busy || control.disabled || !armed) return;
    armed = false;
    lockedButton = control;
    // Touch click follows pointer-up; no held pointer remains on the button.
    if (inputMode === "touch" || (inputMode === "keyboard" && !keyHeld))
      rearm();
    if (!pending) {
      const bytes = new Uint8Array(16);
      crypto.getRandomValues(bytes);
      remember({
        request_id: Array.from(bytes, (b) =>
          b.toString(16).padStart(2, "0"),
        ).join(""),
        raid_id: state.raid_id,
        style: selected,
        name: state.you.name,
      });
    }
    const receipt = pending.request_id;
    busy = true;
    error();
    tick();
    try {
      const { response, value } = await request("/play/api/attack", {
        method: "POST",
        headers: { "Content-Type": "application/json", "X-CSRF-Token": csrf },
        body: JSON.stringify({
          request_id: pending.request_id,
          raid_id: pending.raid_id,
          style: pending.style,
        }),
      });
      if (value.state) apply(value);
      if (!response.ok) {
        // A definitive rejection did not land. A 5xx may have happened after
        // commit, so retain its receipt until a state check resolves it.
        if (response.status < 500) remember(null);
        throw new Error(value.error || "The strike could not be confirmed.");
      }
      strikeFeedback(value.hit, receipt);
      remember(null);
    } catch (e) {
      error(
        e.name === "AbortError"
          ? "The connection timed out. Your hit may have landed. Retry the same strike safely."
          : e.message,
      );
    } finally {
      busy = false;
      tick();
      void poll();
    }
  }
  document.addEventListener("visibilitychange", () => {
    if (document.hidden) clearTimeout(timer);
    else void poll();
  });
  window.addEventListener("online", () => void poll());
  try {
    apply(JSON.parse(root.dataset.bossBootstrap));
    choose(labels[selected] ? selected : "blade");
  } catch (_) {
    error("Reload to reconnect to the raid.");
  }
  setInterval(tick, 1000);
  void poll();
})();
```

## static/redlogo.ico

```base64
AAABAAEAICAAAAEAIACoEAAAFgAAACgAAAAgAAAAQAAAAAEAIAAAAAAAABAAABMLAAATCwAAAAAAAAAAAAD5QyP/+UMj//lDI//6QyP/8EAh/9w6Hf/5QyP/+UMj//lDI//5QyP/+UMj//lDI//5QyP/+UMj//lDI//5QyP/+UMj//lDI//5QyP/+UMj//lDI//5QyP/+UMj//lDI5H5QyMA+UMjAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAPlDI//5QyP/+UMj//pDI//wQCH/3Dod//lDI//5QyP/+UMj//lDI//5QyP/+UMj//lDI//5QyP/+UMj//lDI//5QyP/+UMj//lDI//5QyP/+UMj//lDI//5QyP/+UMjkflDIwD5QyMAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA+UMj//lDI//5QyP/+kMj//BAIf/dOhv/+0Mh//pDIf/6QyH/+kMh//pDIf/6QyH/+kMh//pDIf/6QyH/+kMh//pDIf/6QyH/+kMh//pDIf/6QyH/+kMh//pDIf/6QyGR+kMhAPpDIQAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAD5QyP/+UMj//lDI//6QyL/6kEu/4k0jP+CNqP/gzai/4M2ov+DNqL/gzai/4M2ov+DNqL/gzai/4M2ov+DNqL/gzai/4M2ov+DNqL/gzai/4M2ov+DNqL/gzai/4M2opGDNqIAgzaiAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAPlDI//5QyP/+UMj//pDIv/mQTj/STDe/ygt//8qLf//Ki3//yot//8qLf//Ki3//yot//8qLf//Ki3//yot//8qLf//Ki3//yot//8qLf//Ki3//yot//8qLf//Ki3/kSot/wAqLf8AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA+UMj//lDI//5QyP/+kMi/+ZBOP9MMN7/Ky3//y0t//8tLf//LS3//y0t//8tLf//LS3//y0t//8tLf//LS3//y0t//8tLf//LS3//y0t//8tLf//LS3//y0t//8tLf+RLS3/AC0t/wAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAD5QyP/+UMj//lDI//6QyL/5kE4/0ww3v8rLf//LS3//y0t//8tLf//LS3//y0t//8tLf//LjHz/y816P8vNej/LzXo/y816P8vNej/LzXo/y816P8vNej/LzXo/zA53Ks1T5Y5NU6ZPDVOmTI1TpkGNU6ZAAAAAAAAAAAAAAAAAPxDIP/8QyD//EMg//1DH//pQTX/TTHd/ywt//8tLf//LS3//y0t//8tLf//LS3//y0t//8xPsz/NU2d/zVNnv81TZ7/NU2e/zVNnv81TZ7/NU2e/zVNnv81TZ7/NU2c+jVOmfQ1Tpn2NU6ZzzVOmRc1TpkAAAAAAAAAAAAAAAAAmTmK/5k5iv+ZOYr/mjmK/402iv8rHYX/HR6r/y0t/f8tLf//LS3//y0t//8tLf//LS3//zE+yv81T5f/NU6Z/zVOmf81Tpn/NU6Z/zVOmf81Tpn/NU6Z/zVOmf81Tpn/NU6Z/zVOmv8xSI3rCQ4bhwAAAEkAAAAAAAAAAAAAAAArLf//Ky3//yst//8rLf//Jynn/wYGIv8NDUj/Kyv0/y0t/f8tLf//LS3//y0t//8tLf//MT7L/zVNmv81TZz/NU2c/zVNnP81TZz/NU2c/zVNnP81TZz/NU2c/zVNnP81TZz/Nk6e/y1Bhf8FBw7/AAAAnwAAAAYAAAACAAAAAC0t//8tLf//LS3//y0t//8pKef/Bwcl/wMDE/8NDUT/Hx+w/y4u//8tLf//LS3//y0t//8uMvD/Lzbj/y824/8vNuP/Lzbj/y824/8vNuP/Lzbj/y824/8vNuP/Lzbj/y824/8vN+X/KC7B/wQFFf8AAADkAAAAtwAAAD4AAAAALS3//y0t//8tLf//LS3//ykp5/8HByb/AAAA/wAAAP8aGpH/Li7//y0t//8tLf//LS3//y0s//8tLP//LSz//y0s//8tLP//LSz//y0s//8tLP//LSz//y0s//8tLP//LSz//y0s//8mJdn/BAQY/wAAAP8AAAD9AAAAVgAAAAAuLv//Li7//y4u//8uLv//Kirn/wcHJv8AAAD/AAAA/xoakf8tLf//Kir//yoq//8uLv//Li7//y4u//8qKv//KSn//ykp//8pKf//KSn//ykp//8qKv//Li7//y4u//8uLv//Kyv//yMj2f8EBBj/AAAA/wAAAP0AAABWAAAAAB0dov8dHaL/HR2i/x0do/8aGpP/BAQY/wAAAP8AAAD/GRmR/zMz//9tbf//Y2Pn/yAgpf8dHaL/IiKn/2Zm6/97e///enr//3p6//96ev//e3v//2lp7v8kJKn/HByh/x8fpP9fX+X/bGzo/xoabP8PD1z/EBBd/RAQXVYQEF0AAAAB/wAAAf8AAAH/AAAB/wAAAf8AAAD/AAAA/wAAAP8ZGZH/PT3//9zc///AwL7/CAgJ/wAAAP8NDQ7/x8fH////////////////////////////0NDR/xISE/8AAAD/BQUG/7W1s//k5P//QUH+/yws/v8tLf79LS3+Vi0t/gAAAAD/AAAA/wAAAP8AAAD/AAAA/wAAAP8AAAD/AAAA/xkZkf89Pf//3Nz//8DAvv8ICAj/AAAA/w0NDf/Hx8f////////////////////////////Q0ND/EhIS/wAAAP8FBQX/tbWz/+Tk//9BQf//LCz//y0t//0tLf9WLS3/AAAAAP8AAAD/AAAA/wAAAP8AAAD/AAAA/wEBB/8EBBT/Gxub/zs7///Nzf//s7PD/wwMHv8DAxX/EBAi/7q6zP/w8P//7e3//+3t///t7f//8PD//8LC1P8UFCb/AwMV/wgIGv+qqrr/1NT//z8///8sLP//LS3//S0t/1YtLf8AAAAA/wAAAP8AAAD/AAAA/wAAAP8AAAD/CwtA/yUl0/8qKu7/Ly///0lJ//9ERPX/JyfY/yYm1/8oKNn/RUX2/09P//9OTv//Tk7//05O//9OTv//R0f4/ykp2v8mJtf/JyfY/0JC8/9KSv//MDD//y0t//8tLf/9LS3/Vi0t/wAAAAC5AAAA0QAAAP4AAAD/AQEG/woKOP8WFn3/LCz7/y0t//8tLf//Kyv//ysr//8tLf//LS3//y0t//8rK///Kyv//ysr//8rK///Kyv//ysr//8rK///LS3//y0t//8tLf//LCz//ysr//8tLf//LS3//y0t//0tLf9WLS3/AAAAAAIAAABbAAAA/QAAAP8EBBf/JSXT/y0t/P8tLf//LS3//y0t//8tLf//LS3//y0t//8tLf//LS3//y0t//8tLf//LS3//y0t//8tLf//LS3//y0t//8tLf//LS3//y0t//8tLf//LS3//y4u//8uLv//LS3//S0t/1YtLf8AAAAAAAAAAFYAAAD9AAAA/wICDPMhIbuPLi7/ei0t/3stLf96LS3/hC0t/+ctLf//LS3//y0t//8tLf//LS3//y0t/+ItLf+CLS3/ei0t/38tLf/dLS3//y0t//8tLf//LS3//y0t//8qKuv/GBiG/xsbmcwtLf96LS3/KS0t/wAAAAAAAAAAVgAAAP0AAAD/AAAA5wAAACYAAAAAAAAAAC0t/wAtLf8SLS3/0C0t//8tLf//LS3//y0t//8tLf//LS3/xy0t/w0tLf8ALS3/CC0t/74tLf//LS3//y0t//8tLf//LS3//yYm2f8EBBj/AAAAnQAAAAAAAAAAAAAAAAAAAAAAAABWAAAA/QAAAP8AAADnAAAAJgAAAAAAAAAALS3/AC0t/xItLf/QLS3//y0t//8tLf//LS3//y0t//8tLf/HLS3/DS0t/wAtLf8ILS3/vi0t//8tLf//LS3//y4u//8uLv//JyfZ/wQEGP8AAACdAAAAAAAAAAAAAAAAAAAAAAAAAEYAAADOAAAA0QAAAMEAAABHAAAALQAAAC8AAAATMDD/Di0t/6otLf/SLS3/0C0t/9AtLf/QLS3/0y0t/6MtLf8KLS3/AC0t/wctLf+bLS3/0y0t/88pKejkJSXQ/yUl0v8gILb4BAQX2AAAAIAAAAAAAAAAAAAAAAAAAAAAAAAABgAAABIAAAARAAAAJwAAAMwAAADvAAAA7wAAAGYAAAAALS3/Dy0t/xItLf8SLS3/Ei0t/xItLf8SLS3/Di0t/wEtLf8ALS3/AS0t/w0tLf8SOjr/DgcHJngDAxL/AwMS/wMDEtsCAgspAAAACgAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAYAAAA2QAAAP8AAAD/AAAAbgAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAbgAAAP8AAAD/AAAA2QAAABgAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAABgAAADXAAAA/wAAAP8AAABuAAAAAAAAAAIAAAACAAAAAgAAAAIAAAACAAAAAgAAAAIAAAACAAAAAgAAAAIAAAACAAAAAgAAAAAAAABuAAAA/wAAAP8AAADXAAAAGAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAACAAAAEgAAABWAAAAVAAAAIUAAACrAAAAqgAAAKoAAACqAAAAqgAAAKoAAACqAAAAqgAAAKoAAACqAAAAqgAAAKoAAACqAAAAqwAAAIUAAABUAAAAVgAAAEgAAAAIAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAkQAAAP8AAAD/AAAA/wAAAP8AAAD/AAAA/wAAAP8AAAD/AAAA/wAAAP8AAAD/AAAA/wAAAP8AAAD/AAAAkQAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAACRAAAA/wAAAP8AAAD/AAAA/wAAAP8AAAD/AAAA/wAAAP8AAAD/AAAA/wAAAP8AAAD/AAAA/wAAAP8AAACRAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAGMAAACxAAAArgAAAK4AAACuAAAArgAAAK4AAACuAAAArgAAAK4AAACuAAAArgAAAK4AAACuAAAAsQAAAGMAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAgAAAAQAAAAEAAAABAAAAAQAAAAEAAAABAAAAAQAAAAEAAAABAAAAAQAAAAEAAAABAAAAAQAAAAEAAAAAgAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA/wAAAP8AAAD/AAAA/wAAAP8AAAD/AAAADwAAAA8AAAAHAAAAAQAAAAEAAAABAAAAAQAAAAEAAAABAAAAAQAAAAEAAAABAAAAAQAAAAGAAAABg4AgB4OAIAeAACAHgEAgB/B//g/wQAIP8AAAD/8AAP//AAD//wAA//8AAP8=
```

## static/redlogo.png

```base64
iVBORw0KGgoAAAANSUhEUgAAAvgAAALuCAYAAADbrWJlAAARinpUWHRSYXcgcHJvZmlsZSB0eXBlIGV4aWYAAHja7ZpZkhw9coTfcQodAXsAx8FqNjfQ8fUFkNUbuzn8h3qRmbrIrmQuASAWD3ckzfrvf23zX/ykINnEJCXXnC0/scbqGwfF3p9+fjsbz+/zs4v1z9lP581azwXPqcB3uBeqf4wtznPsnn/XZxD3uv9l6HXgGkfp/UJrz/n++Xx/DPry1dAzg+DuyHY+DzyGgn9mFO+/xzOjXIt8Wtocz8jxOVXe/8YgPqfsJPI7eiuSK8fF2yj4c+pEg1zXmNdIrxOvf79u9czJr+CC5XcI/s4y6N8QGuf9+Z2Mf52K57cP8TjeEkqmgOH6ROtZqjrzo2/effTDz58syzLIXnrzh6i9fX/Jm7ejL3mzH9++0uYtaiU/t4TPYbX57fvb8y69DL0uhLfx/ceRy3iO/Ofzebrw0RXmY7j3nmWfRbOKFjO+yM+iXks8R9zX1YvnqcxHbDZkbeFAP5VPsc0OUmDaQaV1jqvzjL1ddNM1t90638MNphj98sK398P4cE4WglT9ID8cicDHbS+hhhkKKTFODsXg3+bizrD1DDdcsdPY6bjVO4xpcv3HH/OnN+4Tb+eOL28AmJfXTGcW1hF+/eI2IuL249R0HPz6fP3RuAYimI6bCwtstptroif3nlzhBDpwY+L71p6T+RjARQydmIwLRMBmCs1lZiTei3M4shCgxtQpN9+JgEvJTybpqcJMcKgOxuYZcedWn/w9DaqGaEIKOQixqaERrBgT+SOxkEMthRRTSjlJKqmmlkPWystZssJzkyBRkmQRKUaqtBJKLKnkIqWUWlr1NQDfqVKntdRaW2PQhuXG040bWuu+hx576rlLL72a3gbpM+JIIw8ZZdTRpp9hUuAzT5ll1tmWW6TSiiutvGSVVVfbpNoOO+608xazy667vUXtCesvn38QNfdEzZ9I6Y3yFjXOirxMOIWTpDEjYj46Ai5EjYiR2BozW1yMXiOnMaMfURXJM8mkwZlOI0YE43I+bfcWuydyBi/+r8TNSDlx838bOaOh+8PI/Rq376I2tUuME7FbhupUG6g+rq/SfGnaXn/8Nv/uhj/9/n9D//cN7Zx73ORO2aT6Xr02/ZfXNHY/XenDCXi02xxhAb4x8cdTf4/RMbazevMoneTWozTKlBqStLFLkb1iWn3plbZMzH1gdXrsDssNdXn6NhUnTVa79qE0O1hpa5W6N611Bn189bk4mJbCZkYNLJANN9S5q3Ws6PemWyRZffgKZo0907Zz01aleW6/M68hW/32BtpcVg86DkWqq58tnlFYhZ3Sdv7d1VDcBmA2wDZS2ANkWEwjXOu9U8nPSDTW7743mLNtXNWmSIsTfMSqdrwrBsASYcs1KbTUBfkCGtssa+UNnm3JswMGewTHGXzXzpPQBmda2O36RgAXYqiWufDL+VT2hLHsygCyW09lLhpJV0KFWTM/2f1js1Gu1Teb5ho9kqN3ogyTStw9JaS9UjqATvhYr2tLaDwQ5o1Lk1SWGtb2vk0Xi3nyL9+EgRtm+Zhrbb0SrZJFM4c+e6x5tjR2hTZwaihTSwZO8INPZi2ZdtrE5RZlzCX0kSQj466xaCmDoKSdwpj0ArMjyykRCiLnkEXuJacgWvnxSm+Bcotb66iTqm2YrHl8Kok/tA1H1tFIG09M6eM82GxpfSeXerQ103w4GlInPJXqGBXfWZM9nWoHH/FADyRMoSn5OrLfzb9KGYHyZONTBtrdP6a6yqxXtndsM6CETEvDvwzoqVkaXYJ0lZAoBqWGBUGyV9ViJZVvIktaxoEnubbjz7VEHn/SsRu+jGnGHTJVMynsBT+Aw+khBk6Oz0yU9Lz59cKiYS4KMNB7j2vxycGLcxc99ESJacsa2c1Ay6Zdm9hlzpWidMlrQSQGBA57PeTe0G/Jx9rCCCRzS7HR/OvoEmfb/UESKAV+NCcLXVqTCIsDA3wfKReymAoPVCwDUmZp+zambDxd9xz0f4gD7IFTXubY2QzWPwa4ezIFoqShUNzzGGJcJgZJysmv1Hmg59EDXk+LTCJKfDDHqvGR1Qi7VN0q9xCO9s+/zbcXKNwJi9E5KimjZpZ1NzX9zD7luUvvZG4u/aRAsYaggtapVNw0PZEcMp2jIHHhXpsq34O1jVnuxFFYbwX+Vuh9F0Ndtrnj0oQAF6loEr91+D4ElGojHU4BLcjnqR9ZlbnsGQSwhsxNBytMw6DFWuxQu9UB1lAHorFV6b6BuDSUmY+ZLN0uaBvnVqs2xI2cd1ImroacgkdacDidFCOcZEg5TZG6PUUgnNmaEmS4xgiC21wQB0CubIl3p3oyM6qGWnUzE3OtmVWbK2SnJggjc09Oizrfkd6qjbekw5gHnFVCo/loMsJIZZq+MrpuLQ9DJmhIugU1BQd7vFGzWTFlMovbUyHmYJBiaGXsA9OZO41uVkD76XWoU0391QRm20sN8HEaPbU+j7ttZNYKdUMiRqlI3NfJWkIdYbXD53B69gnEPJdp24H8KRvnMtuhxZdHphyGABEb3zeRT4+at2e16ceIMYRzGws0TRN0UQyZlNxajAvB8NNnW6H/dgRV6KKrHbMbZdu7HIAFMgu5tQbq46y9+ZrvrJhgWJ5JhVXpX6cuyRhRZGnENjqDA/pZ63n0wSkSqAAmNLp5+4qcvrJGJZfpGzAFoFixqoqC/9zdMANbV5C7uGP8sa1Q198w8JNtuSD30bZR4xRV92qMaKoPXRg3n396HJAm8UAY15RyiLRq0iwHoTo8ZWWUFbDvnXIVQY4MRDY51Xqd9PYDtYix7XRvo3gNIJyk65RM+DilHonugQVPK7hdo5bD91TgxOsxrdrhD6t7JRXtqD7BfzKLWYWzaN/A8gqRALwD+JoBf6ovBNB+fwMFRrEADkGrsp1STmOSKpJi9yit1OaM6M9SYA78Sbp7M8SlHeC3k9Kx4xRLFUP1MSor3/WZCJEldpMHpr/TYFlwRSKhbGhBJeoA8YJX+kZi0lHDMp7eTaXWMGm+vSrOWeyk0wo8GX4Z9kK9KpbmznLgOozkywxEJ25AswYD/0RponJpsV3z+OkFY0jPIJB8BOdi35G5yydUN19gnT4ZdQmOupOlHInsmlDsDe7Qmy5MA0eufG4Y5kPnKLJsuBjkT0i1LbKyphkPov0WP80Edwsx8wPcCeHIB9cSVkH1gxUlqGJYvbTzlO/cXvDzJpqSGKhr7TIjvAbpAS01QaKruV4Bk87sVEeMqATlzJVG3I5npoLjwtdQmuFnAdhmAxPzhr/UR29lKJtMLWdFQi91uSOquk0Un4r3U4O+n06lyEbUqCaIAIWDH84Mkp+UQfzaBJnX2lfskIA4pIoil9w8Q9SQPM3DPUTpouZOJD0J0M62XwCbDt5FaFnjK06fk/rktHmSGm1DYeGeoVyjetqQm1d0EUE6FHw+AbRcc5n2Rix3qAcMI6WkeYR5G353C3dUdA2S0CG5cCyAheKB5/pHTBWy25QwOtRqXnYE38d1N5uUJI8I09ruZMF0cpZqTy5N68C1A1aJZRC1RmX6NbTlrEVMCMmuHa4WBkUPUhA2Og1ql78676XsXYbuDBXFOC0+N0zrXVmMUyWh7tgdGeJWvGUb1IOLy8mrpwcVKVlH/mxyO1r2WDA7YJWxGxUOkGaVIPUUqSb0VdEF12iHtqFTAzUuX2ONnuLl5IQe53KVJQRhhan7uaIKVsdCHqXrdKdkJgMy+2zrFncJdQM4r79SNkhOxtflkQAO3M3gG2w09mm7MuRFmjVaJifL3dCvlWnOXMEw/ArgkMLTEDB8A05tvArB6L4uFeMZiQZDlRBCR6zFAKgoshznvbkuysu75nEv602+1zS+dT5gQA8EpxqSZIWuEiuSo2dD8LwWmEalZWuIDgZ2oZBIq1AaMGwIoBIihcFT70oaVXB8f8VMOjnaKUPf0arpABoxnoitDSOflB0gpClJn9WGpg3nm/MG+lYRt/gC3rJGq4fz99/NKuQ4oXNIO7K2em0sC34ExkBVYZm2bHRnSKpEQlVlsuG2uKp1ZYZfk/BL4hvIMTQIJ6PNFXO/1EVbA207dcPFj2TnmsClawVS7eEJeHjRzFqb5pOXM8y2dRWB0SsGTRZFHvdwxbGfOKPTy4Es4SjmrYPujAgyrLXrwoXU+16tvm/NIEhpWXCQIULhS6R9BqaJDu8mVwJA5VNn83KOjnOIRHpFyOlGAq6/VddVcSw8CcVf8/hj49Cs4dcDpGaLmtrow1GWytuGMCODYcynHyCaqU86+20QCt5T3rfrqP6cVUYFoqjr+QME6B8QYBdfGXKT2UgJVgrcQkA6SiyhkpjYRGxVeryvhUYDLWKMQ9ftkQSVJGxbxSkygcJORoq+iabug3L6JgSQuKzpK/oOIBU3f9/IYWrKmY2ltPApSIOLAn5BsSVWNRY9foC4PSKCdDc9eeQcTOhElqcDUUSqgRa6QWaunqVNnJ5FXCEgOJ6QNgowqZ0Cwi70GvDemHlR8bKUrzTdjVfPzojw0w5hK8Es8E8mCcQoVytwIi31WvKlp/quKdl9Lz7msEO6pGDnNKfBAGNfBwvVQY0QZEr5IAETzArPpWdAH+yZzJmL+beTKVBPPArDQMkdxX+2ScBQcoBwZOVvsaL7kdCoJd3xuswNDPewjSg2M4gSAI/SDaU2GEwbDi7cXz0Wx9V5jo0v9mbroDuvrEDRT+Xr7s45QeDfTnUlgfDZfkRa2gpjSBXywLTDIFkXVQJQMYqToZBHjYwzR6gbbvlw6pyAT432VKcCqhnH3ldzP5UH5PCryWnzDB5nwwQQdJNiEBqeQjE6QvchQLvtJTmYMyQbXsIDKhIFOeh9GDHSMatfkUY9t0md+S2HPyiprKxjVOiGTgSM5dGm20AwcxsL7LPNbMtEyeRYlLXUmRQJWgdGdE9hcZ7EHZxD1iOyqLV4NjveSJAL+mbstYEMsDB8QylQOLvkps525CBSjZ48/a4cknuHlgOF/U93fqg1nK7pRkXL2XqsWtmaTPxVWHkoen/2/dd+y0d4RQ9QTSLQDQxrvfYbReujvCkBQPicXfDn8r7Xk9A1MI8BjGx9cyanrxgZdEdKBvVmN2TJViBMX6IfQtPF1mttwAik/UqaHRCTuivmcjFYf+jgBwRP0zfQILgKOSSFIxSmKJYhJIAVDCB9YlZCCfBHuhkckpZN9JRPgYooWoiTbkNqTMGKfFBC1Q71DRbUH027RdEqWoDZRxVfudf3y6B7jUFLp0vTtECOwRKnCmDd9ZbHoEkNojBbgdxVqB7Ogayj8sagO68IAhV9uaB7ocgZj9pjNCJEBUzVJQPiANkRs0gplPkgY0Lctutb1FxoYrRuCMekZ+tGydAN0vPGQucMcZOr2Euk8/FdUZCRsjhgCsNHICdmrZtGElYKBDBo948gZGe6vqlpyAlKgHY1l5OU6ORDX/jScKinpW8+oRDCI7q7OdSN2j3i+8Zh+U2Omd8l2T/JMfNNkv3pN8py6+aOYmgxZMjsp55mBYPzD5EhSxLCtyk7QGAoAkHDoIb77CNNb/BGnMcHcF66Vvmhun8uPdW0qxnSahCnAADj/Jz0ZYpLULa7OYAmXsBDSLnhkgm4kQVALEoYTGuV4oJVhrRMGYDQW7do+xe4v1tmdJAGj4aXEkeA0WGrKPKR2rrVJqZDMZ42dJT0/mrlZQMEBei1Krbgw3cT14L5exPXgvl7E9eC+XsT14L5exPXgvl7E9eC+Q9MAHZDefve2aPMx6SdFzMqECNoTpAth3GKBfl+d0rDLZ18cE4sJEv/s8hoQfd/EVVCxwWgHdBgSFpHfnalPis/ZLwA6eOnV+kb5XB6704pjOfVbjH6Px/D2XC6+7NoEm5wZzMpdd0XS0V5CQS6QjF07/6ayT5+HML8o9f6dKyN2GXQet9sHUdkxXuzfry49f+p4D97sGKouHGqj8ubBwaf9MzLfOODPau15n8AEUZ/YtLA6/oAAAGGaUNDUElDQyBwcm9maWxlAAB4nH2RPUjDQBzFX1NLRSoKdhBxyFDFwYKoiOAiVSyChdJWaNXB5NIPoUlDkuLiKLgWHPxYrDq4OOvq4CoIgh8gri5Oii5S4v+SQosYD4778e7e4+4dINTLTDU7xgBVs4xUPCZmcyti8BUh9CKAEcxIzNQT6YUMPMfXPXx8vYvyLO9zf45uJW8ywCcSzzLdsIjXiac2LZ3zPnGYlSSF+Jx41KALEj9yXXb5jXPRYYFnho1Mao44TCwW21huY1YyVOJJ4oiiapQvZF1WOG9xVstV1rwnf2Eory2nuU5zEHEsIoEkRMioYgNlWIjSqpFiIkX7MQ//gONPkksm1wYYOeZRgQrJ8YP/we9uzcLEuJsUigGBF9v+GAKCu0CjZtvfx7bdOAH8z8CV1vJX6sD0J+m1lhY5Anq2gYvrlibvAZc7QP+TLhmSI/lpCoUC8H5G35QD+m6BrlW3t+Y+Th+ADHW1dAMcHALDRcpe83h3Z3tv/55p9vcD211y0dXjY+0AAA12aVRYdFhNTDpjb20uYWRvYmUueG1wAAAAAAA8P3hwYWNrZXQgYmVnaW49Iu+7vyIgaWQ9Ilc1TTBNcENlaGlIenJlU3pOVGN6a2M5ZCI/Pgo8eDp4bXBtZXRhIHhtbG5zOng9ImFkb2JlOm5zOm1ldGEvIiB4OnhtcHRrPSJYTVAgQ29yZSA0LjQuMC1FeGl2MiI+CiA8cmRmOlJERiB4bWxuczpyZGY9Imh0dHA6Ly93d3cudzMub3JnLzE5OTkvMDIvMjItcmRmLXN5bnRheC1ucyMiPgogIDxyZGY6RGVzY3JpcHRpb24gcmRmOmFib3V0PSIiCiAgICB4bWxuczp4bXBNTT0iaHR0cDovL25zLmFkb2JlLmNvbS94YXAvMS4wL21tLyIKICAgIHhtbG5zOnN0RXZ0PSJodHRwOi8vbnMuYWRvYmUuY29tL3hhcC8xLjAvc1R5cGUvUmVzb3VyY2VFdmVudCMiCiAgICB4bWxuczpkYz0iaHR0cDovL3B1cmwub3JnL2RjL2VsZW1lbnRzLzEuMS8iCiAgICB4bWxuczpHSU1QPSJodHRwOi8vd3d3LmdpbXAub3JnL3htcC8iCiAgICB4bWxuczp0aWZmPSJodHRwOi8vbnMuYWRvYmUuY29tL3RpZmYvMS4wLyIKICAgIHhtbG5zOnhtcD0iaHR0cDovL25zLmFkb2JlLmNvbS94YXAvMS4wLyIKICAgeG1wTU06RG9jdW1lbnRJRD0iZ2ltcDpkb2NpZDpnaW1wOmIwOTJhNDlmLTAxZWEtNGIzYy05OWNhLTY4ZjMyOWQ0MDFmMyIKICAgeG1wTU06SW5zdGFuY2VJRD0ieG1wLmlpZDo5OGYyODgxYi0zYjMyLTQwMTgtYjQxZi03NTE2NGZlOTgzMzMiCiAgIHhtcE1NOk9yaWdpbmFsRG9jdW1lbnRJRD0ieG1wLmRpZDoyNGY0ZWNiYi02YmFkLTQ5ZmItYmFjYy1jNzIxNzZiOWNiOGIiCiAgIGRjOkZvcm1hdD0iaW1hZ2UvcG5nIgogICBHSU1QOkFQST0iMi4wIgogICBHSU1QOlBsYXRmb3JtPSJXaW5kb3dzIgogICBHSU1QOlRpbWVTdGFtcD0iMTcwMjcwNTQwNTAwMjQ2NSIKICAgR0lNUDpWZXJzaW9uPSIyLjEwLjMyIgogICB0aWZmOk9yaWVudGF0aW9uPSIxIgogICB4bXA6Q3JlYXRvclRvb2w9IkdJTVAgMi4xMCIKICAgeG1wOk1ldGFkYXRhRGF0ZT0iMjAyMzoxMjoxNVQyMzo0MzoyNC0wNjowMCIKICAgeG1wOk1vZGlmeURhdGU9IjIwMjM6MTI6MTVUMjM6NDM6MjQtMDY6MDAiPgogICA8eG1wTU06SGlzdG9yeT4KICAgIDxyZGY6U2VxPgogICAgIDxyZGY6bGkKICAgICAgc3RFdnQ6YWN0aW9uPSJzYXZlZCIKICAgICAgc3RFdnQ6Y2hhbmdlZD0iLyIKICAgICAgc3RFdnQ6aW5zdGFuY2VJRD0ieG1wLmlpZDo1OGE1ZWQ4Yy01YTA0LTRmOWUtOGRiNC02MmM1YTJlMzg0YzciCiAgICAgIHN0RXZ0OnNvZnR3YXJlQWdlbnQ9IkdpbXAgMi4xMCAoV2luZG93cykiCiAgICAgIHN0RXZ0OndoZW49IjIwMjMtMTItMTVUMjM6NDM6MjUiLz4KICAgIDwvcmRmOlNlcT4KICAgPC94bXBNTTpIaXN0b3J5PgogIDwvcmRmOkRlc2NyaXB0aW9uPgogPC9yZGY6UkRGPgo8L3g6eG1wbWV0YT4KICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgIAogICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgCiAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAKICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgIAogICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgCiAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAKICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgIAogICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgCiAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAKICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgIAogICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgCiAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAKICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgIAogICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgCiAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAKICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgIAogICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgCiAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAKICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgIAogICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgCiAgICAgICAgICAgICAgICAgICAgICAgICAgIAo8P3hwYWNrZXQgZW5kPSJ3Ij8+jQ3cfAAAAAZiS0dEAOoA8ADvHlboOAAAAAlwSFlzAAALEwAACxMBAJqcGAAAAAd0SU1FB+cMEAUrGDGrnNAAAAAZdEVYdENvbW1lbnQAQ3JlYXRlZCB3aXRoIEdJTVBXgQ4XAAANh0lEQVR42u3Yu00DQRSG0R20EsQERCRIpNcRzdCAG6AbaiLyFEAbiOSS89LKD+3M7Dmxg9U/XvvTTBMAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA7SomgH+lCQA0DPTkygQAACDwAQAAgQ8AAAh8AABA4AMAgMAHAAAEPgAAIPABAACBDwAACHwAABD4AACAwAcAAAQ+AAAg8AEAAIEPAAACHwAAEPgAAIDABwAABD4AAAh8AABA4AMAAAIfAAAQ+AAAgMAHAACBDwAACHwAAEDgAwAAAh8AABD4AAAg8AEAAIEPAAAIfAAAQOADAIDABwAABD4AACDwAQAAgQ8AAAh8AAAQ+AAAgMAHAAAEPgAAIPABAACBDwAAAh8AABD4AACAwAcAAAQ+AAAIfAAAQOADAAACHwAAEPgAAIDABwAAgQ8AAAh8AABA4AMAAAIfAAAQ+AAAIPABAACBDwAACHwAAEDgAwCAwAcAAAQ+AAAg8AEAAIEPAAAIfAAAEPgAAIDABwAABD4AACDwAQAAgQ8AAAIfAAAQ+AAAgMAHAAAEPgAAIPABAEDgAwAAAh8AABD4AADAUsUEw0sTeEcA/L/h/2073OADAIDABwAABD4AACDwAQAAgQ8AAAIfAAAQ+AAAgMAHAAAEPgAAIPABAEDgAwAAAh8AABD4AACAwAcAAAQ+AAAIfAAAQOADAAACHwAAEPgAACDwAQAAgQ8AAAh8AABA4AMAAAIfAAAEPgAAIPABAACBDwAACHwAAEDgAwCAwAcAAAQ+AAAg8AEAAIEPAAACHwAAEPgAAIDABwAABD4AACDwAQBA4AMAAAIfAAAQ+AAAgMAHAAAEPgAACHwAAEDgAwAAAh8AABD4AAAg8AEAAIEPAAAIfAAAQOADAAACHwAABD4AACDwAQAAgQ8AAAh8AABA4AMAgMAHAAAEPgAAIPABAACBDwAAAt8EAAAg8AEAAIEPAAAIfAAAQOADAIDABwAABD4AACDwAQAAgQ8AAAh8AAAQ+AAAgMAHAAAEPgAAIPABAACBDwAAAh8AABD4AACAwAcAABYrHTxjOqbhz5hjX44I7wfr/bjU6vfF+0u/769+GZgbfAAAEPgAAIDABwAABD4AACDwAQBA4AMAAAIfAAAQ+AAAgMAHAAAEPgAACHwAAEDgAwAAAh8AABD4AACAwAcAAIEPAAAIfAAAQOADAAACHwAABD4AACDwAQAAgQ8AAAh8AABA4AMAgMAHAAAEPgAAIPABAACBDwAACHwAABD4AACAwAcAAAQ+AAAg8AEAQOADAAACHwAAEPgAAIDABwAABD4AAAh8AABA4AMAAAIfAAAQ+AAAgMAHAACBDwAACHwAAEDgAwAAAh8AAAQ+AAAg8AEAAIEPAAAIfAAAQOADAIDABwAABD4AACDwAQAAgQ8AAAh8AAAQ+AAAgMAHAAAEPgAAIPABAEDgmwAAAAQ+AAAg8AEAAIEPAAAIfAAAEPgAAIDABwAABD4AACDwAQAAgQ8AAAIfAAAQ+AAAgMAHAAAEPgAAIPABAEDgAwAAAh8AABD4AADAYqWDZ0zHdMJ4EUYAADhnQNfadEO7wQcAgIEIfAAAEPgAAIDABwAABD4AACDwAQBA4AMAAAIfAAAQ+AAAgMAHAAAEPgAACHwAAEDgAwAAAh8AABD4AACAwAcAAIEPAAAIfAAAQOADAAACHwAABD4AACDwAQAAgQ8AAAh8AABA4AMAgMAHAAAEPgAAIPABAACBDwAACHwAABD4AACAwAcAAAQ+AAAg8AEAQOADAAACHwAAEPgAAIDABwAABD4AAGzFPE1TmmFcpdamny8jHBIAwBm5wQcAAIEPAAAIfAAAQOADAAACHwAABD4AACDwAQAAgQ8AAAh8AABA4AMAgMAHAAAEPgAAIPABAACBDwAACHwAABD4AACAwAcAAAQ+AAAg8AEAQOADAAACHwAAEPgAAIDABwAABD4AAAh8AABA4AMAAAIfAAAQ+AAAgMAHAACBDwAACHwAAEDgAwAAAh8AAAQ+AAAg8AEAAIEPAAAIfAAAQOADAIDABwAAujObgDWVWpt+voxoe8DDoe3zLcWX/JTvX6YR8P56fy9jt3NIA3ODDwAAAh8AABD4AACAwAcAAAQ+AAAIfAAAQOADAAACHwAAEPgAAIDABwAAgQ8AAAh8AABA4AMAAAIfAAAQ+AAAIPABAACBDwAACHwAAEDgAwCAwAcAAAQ+AAAg8AEAAIEPAAAIfAAAEPgAAIDABwAABD4AACDwAQAAgQ8AAAIfAAAQ+AAAgMAHAAAEPgAACHwAAEDgAwAAAh8AABD4AACAwAcAAIEPAAAIfAAAQOADAAACHwAAEPgAACDwAQAAgQ8AAAh8AABA4AMAgMAHAAAEPgAAIPABAACBDwAACHwAABD4AACAwAcAAAQ+AAAg8AEAAIEPAAACHwAAEPgAAIDABwAABD4AAAh8EwAAgMAHAAAEPgAAIPABAACBDwAAAh8AABD4AACAwAcAAAQ+AAAg8AEAQOADAAACHwAAEPgAAIDABwAABD4AAAh8AABA4AMAAAIfAABYrGREmmHgA67VCCfICCMAoA/4MWHLD+cGHwAABiLwAQBA4AMAAAIfAAAQ+AAAgMAHAACBDwAACHwAAEDgAwAAAh8AABD4AAAg8AEAAIEPAAAIfAAAQOADAAACHwAABD4AACDwAQAAgQ8AAAh8AAAQ+AAAgMAHAAAEPgAAIPABAACBDwAAAh8AABD4AACAwAcAAAQ+AAAg8AEAQOADAAACHwAAEPgAAIDABwAAgQ8AAAh8AABA4AMAAAIfAAAQ+AAAIPABAACBDwAACHwAAEDgAwAAAh8AAAQ+AAAg8AEAAIEPAAAIfAAAEPgAAIDABwAABD4AACDwAQAAgQ8AAAIfAAAQ+AAAgMAHAAAEPgAAIPABAEDgAwAAAh8AABD4AACAwAcAAIFvAgAAEPgAAIDABwAABD4AACDwAQBA4AMAAAIfAAAQ+AAAgMAHAAAEPgAACHwAAEDgAwAAAh8AABD4AACAwAcAAIEPAAAIfAAA4NJmE7CmjDACq3l9uDECsE21+ScsDul4bvABAEDgAwAAAh8AABD4AACAwAcAAIEPAAAIfAAAQOADAAACHwAAEPgAACDwAQAAgQ8AAAh8AABA4AMAAAIfAAAEPgAAIPABAACBDwAACHwAABD4AACAwAcAAAQ+AAAg8AEAAIEPAAACHwAAEPgAAIDABwAABD4AACDwAQBA4AMAAAIfAAAQ+AAAgMAHAACBDwAACHwAAEDgAwAAAh8AABD4AAAg8AEAgO7Mj3dvVhhYxpMRAIDvignG5QYfAAAEPgAAIPABAACBDwAACHwAABD4AACAwAcAAAQ+AAAg8AEAAIEPAAACHwAAEPgAAIDABwAABD4AACDwAQBA4AMAAAIfAAAQ+AAAgMAHAACBDwAACHwAAEDgAwAAAh8AABD4AAAg8AEAAIEPAAAIfAAAQOADAAACHwAABD4AACDwAQAAgQ8AAAh8AAAQ+AAAgMAHAAAEPgAAIPABAACBDwAAAh8AAOjObAJgq/bvH0aATpVaixXgd27wAQBA4AMAAAIfAAAQ+AAAgMAHAACBDwAACHwAAEDgAwAAAh8AABD4AAAg8AEAAIEPAAAIfAAAQOADAAACHwAABD4AACDwAQAAgQ8AAAh8AAAQ+AAAgMAHAAAEPgAAIPABAACBDwAAAh8AABD4AACAwAcAAAQ+AAAg8AEAQOADAAACHwAAEPgAAIDABwAAgQ8AAAh8AABA4AMAAAIfAAAQ+AAAIPABAACBDwAACHwAAEDgAwAAAh8AAAQ+AAAg8AEAAIEPAAAIfAAAEPgAAIDABwAABD4AACDwAQAAgQ8AAAIfAAAQ+AAAgMAHAAAEPgAAIPABAEDgAwAAAh8AABD4AACAwAcAAIFvAgAAEPgAAIDABwAABD4AACDwAQBA4AMAAAIfAAAQ+AAAgMAHAAAEPgAACHwAAEDgAwAAAh8AABD4AACAwAcAAIEPAAAIfAAAQOADAACLzSYY2+3ny7LP3T8bC4COXJsA/uAGHwAABD4AACDwAQAAgQ8AAAh8AAAQ+AAAgMAHAAAEPgAAIPABAACBDwAAAh8AABD4AACAwAcAAAQ+AAAg8AEAQOADAAACHwAAEPgAAIDABwAAgQ8AAAh8AABA4AMAAAIfAAAQ+AAAIPABAACBDwAACHwAAEDgAwAAAh8AAAQ+AAAg8AEAAIEPAAAIfAAAEPgAAIDABwAABD4AACDwAQAAgQ8AAAIfAAAQ+AAAgMAHAAAEPgAAIPABAEDgAwAAAh8AABD4AACAwAcAAIEPAAAIfAAAQOADAAACHwAAEPgAACDwAQAAgQ8AAAh8AABA4AMAAAIfAAAEPgAAIPABAACBDwAACHwAABD4JgAAAIEPAAAIfAAAQOADAAACHwAABD4AACDwAQAAgQ8AAAh8AABA4AMAgMAHAAAEPgAAIPABAACBDwAACHwAABD4AACAwAcAAAQ+AACw2BcP6zbwFUGMVAAAAA5lWElmTU0AKgAAAAgAAAAAAAAA0lOTAAAAAElFTkSuQmCC
```

## static/style.css

```css
/* Logo red (#ff2d2d), warm charcoal panels, and lighter red for readable text.
   Filled action buttons use a deeper red so their white labels stay readable. */
.play-invite img.custom-avatar {
  image-rendering: auto;
  object-fit: contain;
}
:root {
  color-scheme: dark;
  --bg: #110e11;
  --panel: #1a1418;
  --panel-high: #231a20;
  --line: #39282f;
  --text: #faf1f3;
  --muted: #b8a8ae;
  --accent: #ff737b;
  --brand: #ff2d2d;
  --action: #d92236;
  --warning: #f3c77a;
  --radius: 16px;
  --shadow: 0 12px 40px #0002;
  font-family:
    Inter,
    ui-sans-serif,
    system-ui,
    -apple-system,
    BlinkMacSystemFont,
    "Segoe UI",
    sans-serif;
  font-size: 15px;
  line-height: 1.5;
}
* {
  box-sizing: border-box;
}
html {
  scroll-behavior: smooth;
  scroll-padding-top: 95px;
}
body {
  margin: 0;
  background: var(--bg);
  color: var(--text);
}
body:before {
  content: "";
  position: absolute;
  z-index: -1;
  inset: 0 0 auto;
  height: 500px;
  background: radial-gradient(ellipse at 90% -15%, #ff2d2d24, transparent 65%);
  pointer-events: none;
}
a {
  color: inherit;
  text-decoration: none;
}
a:hover {
  color: var(--accent);
}
button,
input,
textarea,
select {
  font: inherit;
}
button,
a,
input,
textarea,
select {
  touch-action: manipulation;
}
button {
  cursor: pointer;
}
button:disabled {
  opacity: 0.55;
  cursor: wait;
}
[hidden] {
  display: none !important;
}
.js-only {
  display: none;
}
.js .js-only {
  display: inline-flex;
}
:focus-visible {
  outline: 3px solid var(--accent);
  outline-offset: 4px;
}
.shell {
  max-width: 1200px;
  margin: auto;
  padding: 0 32px;
}
.accent,
.text-link {
  color: var(--accent);
}
.muted {
  color: var(--muted);
}
.small {
  font-size: 0.82rem;
}
.eyebrow {
  font-size: 0.67rem;
  font-weight: 700;
  letter-spacing: 0.16em;
  color: var(--muted);
  display: flex;
  gap: 9px;
  align-items: center;
}
h1,
h2,
h3,
p {
  margin-top: 0;
}
h1 {
  font-size: clamp(2.1rem, 4vw, 3.65rem);
  letter-spacing: -0.055em;
  line-height: 1.08;
  font-weight: 650;
  margin-bottom: 20px;
}
h2 {
  font-size: 1.65rem;
  line-height: 1.2;
  letter-spacing: -0.035em;
  margin-bottom: 12px;
}
h3 {
  font-size: 1.05rem;
  letter-spacing: -0.015em;
  margin-bottom: 9px;
}
p {
  margin-bottom: 16px;
}
.dot {
  display: inline-block;
  width: 7px;
  height: 7px;
  border-radius: 50%;
  background: var(--accent);
  box-shadow: 0 0 12px #ff2d2d50;
}
.panel {
  border: 1px solid var(--line);
  border-radius: var(--radius);
  background: var(--panel);
  box-shadow: var(--shadow);
}
.row,
.section-title,
.button-row {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 16px;
}
.button-row {
  justify-content: flex-start;
  flex-wrap: wrap;
}
.section-title {
  margin-bottom: 22px;
}
.section-title h2 {
  margin-bottom: 0;
}
.section-title .eyebrow {
  margin-bottom: 7px;
}
.button {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  gap: 13px;
  min-height: 42px;
  padding: 10px 17px;
  border: 1px solid #59313c;
  border-radius: 9px;
  background: #351e27;
  color: var(--text);
  font-weight: 600;
  font-size: 0.84rem;
  white-space: nowrap;
  transition:
    background 0.16s,
    transform 0.16s;
}
.button:hover {
  background: #48232f;
  color: #fff;
}
.button.primary {
  background: var(--action);
  color: #fff;
  border-color: var(--action);
}
.button.primary:hover {
  background: #b8182b;
  border-color: #b8182b;
}
.button.small {
  min-height: 36px;
  padding: 7px 13px;
  font-size: 0.76rem;
}
.button.danger {
  border-color: #745047;
  background: #382521;
  color: #ffb6a3;
}
.text-button,
.copy-button {
  border: 0;
  background: transparent;
  color: var(--muted);
  padding: 7px;
}
.copy-button {
  font-size: 1rem;
  min-width: 34px;
  min-height: 34px;
}
.text-button:hover,
.copy-button:hover {
  color: var(--accent);
}
.text-link {
  font-size: 0.82rem;
  font-weight: 600;
}
.badge,
.tag {
  display: inline-flex;
  align-items: center;
  padding: 5px 10px;
  border: 1px solid #57333e;
  border-radius: 7px;
  font-size: 0.71rem;
  color: #edc1ca;
  background: #331e27;
  white-space: nowrap;
}
.tag {
  font-size: 0.64rem;
  padding: 3px 8px;
  margin-left: 6px;
}
.state-active {
  color: var(--accent);
  border-color: #89434f;
  background: #411d28;
}
.state-ended {
  color: var(--warning);
  background: #312a1f;
  border-color: #665330;
}
.state-upcoming {
  color: #b6c9fb;
  background: #222b40;
  border-color: #404e73;
}
.skip-link {
  position: fixed;
  z-index: 20;
  top: -80px;
  left: 16px;
  padding: 12px;
  background: var(--accent);
  color: #111;
}
.skip-link:focus {
  top: 12px;
}
.site-header {
  border-bottom: 1px solid #40252f;
  background: #160e14ed;
  position: sticky;
  top: 0;
  z-index: 5;
  backdrop-filter: blur(10px);
}
.header-inner {
  min-height: 78px;
  display: flex;
  justify-content: space-between;
  align-items: center;
  gap: 24px;
}
.brand {
  display: flex;
  gap: 12px;
  align-items: center;
  font-size: 0.92rem;
  font-weight: 800;
  letter-spacing: 0.07em;
}
.brand img {
  border-radius: 8px;
  object-fit: contain;
  background: #11080c;
}
.brand-sub {
  display: block;
  color: var(--muted);
  font-size: 0.48rem;
  font-weight: 600;
  letter-spacing: 0.2em;
  margin-top: 3px;
}
.site-header nav {
  display: flex;
  align-items: center;
  gap: 26px;
  font-size: 0.8rem;
  color: #ead7dc;
}
.site-header form {
  margin: 0;
}
.hero {
  display: grid;
  grid-template-columns: 1.2fr 1fr;
  gap: 52px;
  padding: 52px 0 45px;
  align-items: center;
}
.hero h1 {
  max-width: 580px;
  margin-top: 14px;
}
.lead {
  color: var(--muted);
  font-size: 1rem;
  max-width: 440px;
}
.hero-links {
  display: flex;
  align-items: center;
  gap: 24px;
  margin-top: 26px;
  flex-wrap: wrap;
}
.sponsor {
  display: flex;
  align-items: center;
  gap: 13px;
}
.sponsor small {
  display: block;
  font-size: 0.54rem;
  letter-spacing: 0.13em;
  color: var(--muted);
}
.sponsor strong {
  font-size: 0.9rem;
}
.sponsor-symbol {
  display: grid;
  place-items: center;
  background: #29213d;
  color: #d1baff;
  font-size: 1.2rem;
  font-weight: 900;
  width: 39px;
  height: 39px;
  border-radius: 11px;
}
.race-clock {
  padding: 27px 28px;
  background: linear-gradient(125deg, #311b25, #1a1418);
}
.clock {
  font-size: clamp(1.3rem, 2.4vw, 2.2rem);
  letter-spacing: -0.045em;
  font-weight: 600;
  font-variant-numeric: tabular-nums;
  margin: 28px 0 16px;
  white-space: nowrap;
}
.race-clock p {
  font-size: 0.72rem;
}
.clock-footer {
  border-top: 1px solid var(--line);
  display: flex;
  justify-content: space-between;
  padding-top: 15px;
  gap: 14px;
  font-size: 0.71rem;
  color: var(--muted);
}
.clock-footer strong {
  font-size: 1rem;
  display: inline-block;
  margin-left: 7px;
}
.source-status {
  text-align: right;
  font-size: 0.74rem;
  display: flex;
  flex-direction: column;
  gap: 4px;
}
.source-status small {
  color: var(--muted);
  font-size: 0.66rem;
}
.podium {
  display: grid;
  grid-template-columns: 1fr 1.15fr 1fr;
  align-items: end;
  gap: 16px;
  margin: 35px 0 22px;
}
.podium-card {
  padding: 21px;
  border: 1px solid var(--line);
  border-radius: var(--radius);
  background: linear-gradient(160deg, #291b22, #1a1418);
  min-width: 0;
}
.podium-card.place-1 {
  background: linear-gradient(135deg, #461d2b, #211319);
  border-color: #a34755;
  padding-top: 28px;
  box-shadow: 0 6px 35px #ff2d2d14;
}
.podium-top {
  display: flex;
  align-items: center;
  gap: 12px;
}
.placement {
  font-size: 1.05rem;
  font-weight: 600;
  color: var(--muted);
  font-variant-numeric: tabular-nums;
}
.podium-top .eyebrow {
  font-size: 0.56rem;
  letter-spacing: 0.13em;
  flex: 1;
}
.podium-symbol {
  color: var(--accent);
  font-size: 1.3rem;
}
.podium-name {
  display: block;
  font-size: 1.4rem;
  font-weight: 600;
  letter-spacing: -0.03em;
  margin: 24px 0 27px;
  overflow-wrap: anywhere;
}
.place-1 .podium-name {
  font-size: 1.7rem;
  margin-bottom: 30px;
}
.podium-values {
  display: grid;
  grid-template-columns: 1.5fr 1fr;
  gap: 10px;
}
.podium-values small {
  display: block;
  font-size: 0.51rem;
  letter-spacing: 0.12em;
  color: var(--muted);
  margin-bottom: 7px;
}
.podium-values strong {
  font-size: 1rem;
  font-variant-numeric: tabular-nums;
  overflow-wrap: anywhere;
}
.podium-values > div:last-child {
  text-align: right;
}
.public-table {
  padding: 0 20px;
}
table {
  border-collapse: collapse;
  width: 100%;
  font-size: 0.81rem;
}
th {
  text-align: left;
  font-size: 0.64rem;
  letter-spacing: 0.055em;
  text-transform: uppercase;
  font-weight: 600;
  color: var(--muted);
  padding: 16px 14px;
  border-bottom: 1px solid var(--line);
  white-space: nowrap;
}
td {
  padding: 13px 14px;
  border-bottom: 1px solid #36242c;
}
tbody tr:last-child td {
  border-bottom: 0;
}
tbody tr:hover {
  background: #ffffff03;
}
.number {
  text-align: right;
  font-variant-numeric: tabular-nums;
  white-space: nowrap;
}
.rank {
  color: var(--muted);
  font-variant-numeric: tabular-nums;
  width: 65px;
}
.table-scroll {
  overflow: auto;
  max-width: 100%;
  scrollbar-color: #8c4a5b transparent;
}
.leaderboard-foot {
  display: flex;
  justify-content: space-between;
  gap: 16px;
  color: var(--muted);
  font-size: 0.67rem;
  margin: 15px 0 26px;
}
.explanation {
  padding: 0 22px;
  margin-top: 24px;
}
.explanation summary {
  padding: 18px 0;
  font-size: 0.82rem;
}
.weighting-grid {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 22px;
  border-top: 1px solid var(--line);
  padding-top: 20px;
}
.weighting-grid strong {
  font-size: 0.9rem;
}
.weighting-grid p {
  color: var(--muted);
  font-size: 0.79rem;
  margin: 5px 0 22px;
}
.footer {
  display: flex;
  justify-content: space-between;
  gap: 20px;
  padding-top: 36px;
  padding-bottom: 28px;
  font-size: 0.69rem;
  color: #cfb7c0;
}
.footer span:last-child {
  display: flex;
  gap: 22px;
}
.admin-main {
  padding-top: 35px;
}
.admin-heading {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 24px;
  margin-bottom: 25px;
}
.admin-heading h1 {
  font-size: 2.05rem;
  margin: 9px 0 13px;
}
.admin-heading p {
  font-size: 0.8rem;
  margin: 0;
}
.tabs {
  display: flex;
  align-items: center;
  gap: 8px;
  border-bottom: 1px solid var(--line);
  padding-bottom: 15px;
  margin-bottom: 26px;
}
.tabs a {
  color: var(--muted);
  padding: 9px 17px;
  font-size: 0.83rem;
  border-radius: 8px;
}
.tabs a[aria-current] {
  background: #3c1d29;
  color: var(--accent);
}
.tabs a:hover {
  background: #2c1923;
}
.auto-label {
  margin-left: auto;
  font-size: 0.67rem;
  color: var(--muted);
  display: flex;
  gap: 8px;
  align-items: center;
}
.stat-grid {
  display: grid;
  grid-template-columns: 1.5fr 1fr 1fr;
  gap: 18px;
  margin-bottom: 32px;
}
.stat {
  padding: 24px;
  min-width: 0;
}
.stat-value {
  display: block;
  font-size: 2rem;
  line-height: 1.2;
  letter-spacing: -0.035em;
  margin: 24px 0 12px;
  font-variant-numeric: tabular-nums;
}
.stat #countdown {
  font-size: 1.4rem;
  white-space: nowrap;
}
.stat p {
  font-size: 0.77rem;
  margin-bottom: 12px;
}
.stat small {
  font-size: 0.7rem;
}
.connection-grid {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 18px;
}
.connection {
  display: flex;
  align-items: flex-start;
  gap: 16px;
  padding: 23px;
}
.connection > div:nth-child(2) {
  flex: 1;
  min-width: 0;
}
.connection h3 {
  font-size: 0.93rem;
}
.connection p {
  font-size: 0.8rem;
  margin-bottom: 8px;
  overflow-wrap: anywhere;
}
.connection small {
  font-size: 0.64rem;
}
.connection-icon {
  flex-shrink: 0;
  display: grid;
  place-items: center;
  width: 40px;
  height: 40px;
  border-radius: 10px;
  background: #441f2d;
  color: var(--accent);
  font-size: 1.2rem;
  font-weight: 800;
}
.quick-guide {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 25px;
  padding: 25px;
  margin-top: 24px;
  background: linear-gradient(120deg, #311a25, #1a1418);
}
.quick-guide p {
  font-size: 0.81rem;
  margin: 0;
}
.notice {
  padding: 16px 18px;
  border: 1px solid var(--line);
  border-radius: 10px;
  background: #281b23;
  font-size: 0.83rem;
  margin: 0 0 20px;
  overflow-wrap: anywhere;
}
.notice.warning {
  color: #f4d6a8;
  background: #2a241a;
  border-color: #655237;
}
.notice.success {
  color: #d0efae;
  background: #23301d;
  border-color: #4c683b;
}
.notice p:last-child {
  margin-bottom: 0;
}
.notice strong {
  display: block;
  margin-bottom: 6px;
}
.notice ul {
  padding-left: 20px;
  margin: 6px 0;
}
.ended-notice {
  display: flex;
  justify-content: space-between;
  align-items: center;
  gap: 20px;
}
.ended-notice span {
  color: var(--muted);
  font-size: 0.78rem;
}
.stack {
  display: flex;
  flex-direction: column;
  gap: 20px;
}
.form-panel {
  padding: 25px;
  margin-bottom: 20px;
}
.stack .form-panel {
  margin-bottom: 0;
}
.form-panel h2 {
  font-size: 1.4rem;
}
.form-panel h3 {
  margin-top: 24px;
}
.form-grid {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 18px 22px;
  margin-top: 20px;
}
.field {
  display: flex;
  flex-direction: column;
  gap: 7px;
  min-width: 0;
}
.field label {
  font-size: 0.77rem;
  font-weight: 600;
}
.field small {
  font-size: 0.69rem;
  min-height: 1em;
}
.field-error {
  color: #ffbd9f;
}
input,
textarea,
select {
  width: 100%;
  min-height: 42px;
  background: #160f15;
  color: var(--text);
  border: 1px solid #573240;
  border-radius: 8px;
  padding: 10px 12px;
  font-size: 0.83rem;
}
input:focus,
textarea:focus,
select:focus {
  border-color: var(--accent);
  outline: 1px solid var(--accent);
}
input[type="file"] {
  padding: 7px;
}
input::placeholder {
  color: #ab909c;
}
textarea {
  resize: vertical;
}
input[aria-invalid] {
  border-color: var(--warning);
}
.form-panel > .field {
  margin-top: 20px;
}
.prize-grid {
  display: grid;
  grid-template-columns: repeat(5, 1fr);
  gap: 14px;
}
.prize-grid input {
  font-variant-numeric: tabular-nums;
}
.prize-grid .field small:empty {
  display: none;
}
.save-bar {
  display: flex;
  justify-content: space-between;
  align-items: center;
  gap: 20px;
  padding: 17px 20px;
  background: #301923ef;
  border: 1px solid #89505f;
  border-radius: 12px;
  position: sticky;
  bottom: 15px;
  z-index: 4;
  backdrop-filter: blur(10px);
}
.save-bar strong,
.save-bar span {
  display: block;
}
.save-bar strong {
  font-size: 0.86rem;
  margin-bottom: 3px;
}
.filter-bar {
  display: flex;
  align-items: flex-start;
  gap: 14px;
  margin: 22px 0 14px;
  flex-wrap: wrap;
}
.filter-bar .field {
  flex: 1;
  min-width: 150px;
}
.filter-bar .grow {
  flex: 2;
}
.filter-bar > .button {
  margin-top: 26px;
}
.name-cell {
  display: flex;
  align-items: center;
  gap: 6px;
  overflow-wrap: anywhere;
}
.empty {
  text-align: center;
  padding: 35px;
  color: var(--muted);
}
details summary {
  cursor: pointer;
  list-style: none;
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 18px;
  font-weight: 600;
}
details summary::-webkit-details-marker {
  display: none;
}
summary h2 {
  margin: 0;
}
summary .eyebrow {
  display: block;
  margin-bottom: 7px;
}
details[open] > summary {
  margin-bottom: 18px;
}
.explanation[open] > summary {
  margin-bottom: 0;
}
.expand-icon {
  font-size: 1.4rem;
  color: var(--accent);
}
details[open] > summary .expand-icon {
  transform: rotate(45deg);
}
.details-content > .field {
  margin: 22px 0;
}
.nested {
  border-top: 1px solid var(--line);
  margin-top: 22px;
  padding-top: 18px;
}
.nested summary {
  font-size: 0.83rem;
  color: #dac2cc;
}
.account-row {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 12px 0;
  border-bottom: 1px solid var(--line);
}
.account-row strong {
  font-size: 0.85rem;
}
.diagnostic-grid {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 20px;
  margin: 22px 0;
}
.diagnostic-grid strong,
.diagnostic-grid small {
  display: block;
  overflow-wrap: anywhere;
}
.diagnostic-grid strong {
  font-size: 0.82rem;
  margin-top: 5px;
}
.diagnostic-grid small {
  font-size: 0.68rem;
}
.admin-foot {
  display: flex;
  justify-content: space-between;
  gap: 20px;
  font-size: 0.65rem;
  color: #b396a4;
  margin: 30px 0;
}
.login-wrap {
  min-height: 70vh;
  display: grid;
  place-items: center;
  padding-top: 45px;
  padding-bottom: 45px;
}
.login-panel {
  width: 100%;
  max-width: 450px;
  padding: 38px;
}
.login-panel h1 {
  font-size: 2.35rem;
  margin: 22px 0 14px;
}
.login-panel > .muted {
  font-size: 0.82rem;
}
.login-panel .stack {
  margin: 27px 0;
}
.release {
  font-size: 0.64rem;
  color: #b39aa5;
}
.toast {
  position: fixed;
  bottom: 25px;
  left: 50%;
  transform: translateX(-50%);
  z-index: 20;
  padding: 14px 22px;
  border: 1px solid #8a455c;
  border-radius: 10px;
  background: #3b1c2a;
  box-shadow: var(--shadow);
  max-width: calc(100vw - 30px);
  font-size: 0.83rem;
}
@media (min-width: 1600px) {
  .shell {
    max-width: 1330px;
  }
  .hero {
    padding-top: 64px;
  }
}
@media (max-width: 1000px) {
  .shell {
    padding-left: 24px;
    padding-right: 24px;
  }
  .hero {
    gap: 24px;
    grid-template-columns: 1fr 1fr;
  }
  .race-clock {
    padding: 22px;
  }
  .stat-grid {
    grid-template-columns: 1fr 1fr;
  }
  .stat:first-child {
    grid-column: 1/-1;
  }
  .stat:first-child .stat-value {
    font-size: 2rem;
  }
  .connection-grid {
    grid-template-columns: 1fr;
  }
  .podium {
    gap: 12px;
  }
  .podium-card {
    padding: 16px;
  }
  .podium-values strong {
    font-size: 0.83rem;
  }
  .podium-top .eyebrow {
    font-size: 0.5rem;
  }
  .prize-grid {
    grid-template-columns: repeat(3, 1fr);
  }
  .stat #countdown {
    font-size: 1.8rem;
  }
}
@media (max-width: 700px) {
  html {
    scroll-padding-top: 80px;
  }
  .shell {
    padding-left: 18px;
    padding-right: 18px;
  }
  .header-inner {
    min-height: 68px;
  }
  .brand {
    font-size: 0.75rem;
    gap: 8px;
  }
  .brand img {
    width: 30px;
    height: 30px;
  }
  .brand-sub {
    font-size: 0.4rem;
  }
  .site-header nav {
    gap: 12px;
    font-size: 0.72rem;
  }
  .site-header nav > a:first-child {
    display: none;
  }
  .site-header .button {
    padding: 8px 11px;
  }
  .hero {
    grid-template-columns: 1fr;
    gap: 27px;
    padding: 34px 0;
  }
  .hero h1 {
    font-size: 2.7rem;
    max-width: 480px;
    margin-top: 15px;
  }
  .hero-links {
    margin-top: 20px;
  }
  .race-clock {
    padding: 22px;
  }
  .clock {
    font-size: 1.9rem;
    margin: 23px 0 14px;
  }
  .clock-footer strong {
    font-size: 1rem;
  }
  .section-title h2 {
    font-size: 1.5rem;
  }
  .section-title {
    align-items: flex-start;
    gap: 12px;
  }
  .source-status {
    font-size: 0.66rem;
    max-width: 155px;
  }
  .source-status small {
    font-size: 0.59rem;
  }
  .podium {
    grid-template-columns: 1fr 1fr;
    margin-top: 24px;
    gap: 12px;
  }
  .podium .place-1 {
    grid-column: 1/-1;
    grid-row: 1;
    padding: 22px;
  }
  .podium .place-1 .podium-name {
    margin: 14px 0 20px;
    font-size: 1.65rem;
  }
  .place-1 .podium-values strong {
    font-size: 1.3rem;
  }
  .podium .place-2,
  .podium .place-3 {
    padding: 16px;
  }
  .podium-top .eyebrow {
    font-size: 0.49rem;
  }
  .podium-name {
    font-size: 1.1rem;
    margin: 17px 0 20px;
  }
  .podium-values {
    grid-template-columns: 1fr;
    gap: 15px;
  }
  .podium-values > div:last-child {
    text-align: left;
  }
  .place-1 .podium-values {
    grid-template-columns: 1fr 1fr;
  }
  .place-1 .podium-values > div:last-child {
    text-align: right;
  }
  .podium-values strong {
    font-size: 1rem;
  }
  .podium-top {
    gap: 8px;
  }
  .podium-symbol {
    font-size: 1rem;
  }
  .public-table {
    padding: 0 5px;
  }
  th {
    font-size: 0.58rem;
    padding: 14px 9px;
  }
  td {
    font-size: 0.74rem;
    padding: 12px 9px;
  }
  .public-table table {
    min-width: 355px;
  }
  .rank {
    width: 45px;
  }
  .leaderboard-foot {
    flex-direction: column;
    gap: 5px;
    font-size: 0.63rem;
  }
  .weighting-grid {
    grid-template-columns: 1fr;
    gap: 0;
  }
  .weighting-grid p {
    margin-bottom: 16px;
  }
  .footer {
    flex-direction: column;
    gap: 12px;
    padding-top: 26px;
  }
  .footer span:last-child {
    gap: 18px;
  }
  .admin-heading {
    align-items: flex-start;
    gap: 12px;
  }
  .admin-heading h1 {
    font-size: 1.75rem;
  }
  .admin-heading > .button,
  .admin-heading form .button {
    font-size: 0.69rem;
    padding: 9px;
  }
  .admin-heading p {
    font-size: 0.72rem;
  }
  .tabs {
    gap: 2px;
    flex-wrap: wrap;
  }
  .tabs a {
    padding: 9px 13px;
    font-size: 0.76rem;
  }
  .auto-label {
    width: 100%;
    margin: 10px 0 0 13px;
    font-size: 0.65rem;
  }
  .stat-grid {
    gap: 12px;
  }
  .stat {
    padding: 18px;
  }
  .stat-value {
    font-size: 1.7rem;
  }
  .stat:first-child .stat-value {
    font-size: 1.65rem;
  }
  .stat .eyebrow {
    font-size: 0.6rem;
  }
  .stat p {
    font-size: 0.7rem;
  }
  .connection {
    padding: 18px;
    gap: 12px;
  }
  .connection-icon {
    width: 32px;
    height: 32px;
  }
  .quick-guide {
    align-items: flex-start;
    flex-direction: column;
    padding: 20px;
  }
  .form-panel {
    padding: 18px;
  }
  .form-panel .section-title {
    flex-direction: column;
  }
  .form-grid {
    grid-template-columns: 1fr;
    gap: 15px;
  }
  .prize-grid {
    grid-template-columns: repeat(3, minmax(0, 1fr));
    gap: 12px;
  }
  .prize-grid input {
    padding: 9px;
    font-size: 0.78rem;
  }
  .prize-grid label {
    font-size: 0.7rem;
  }
  .save-bar {
    bottom: 8px;
    padding: 14px;
    gap: 12px;
    flex-wrap: wrap;
  }
  .save-bar .button {
    min-height: 40px;
  }
  .save-bar .button-row {
    margin-left: auto;
    gap: 8px;
  }
  .filter-bar .field {
    min-width: 130px;
  }
  .ended-notice {
    align-items: flex-start;
    flex-direction: column;
  }
  .diagnostic-grid {
    grid-template-columns: 1fr 1fr;
    gap: 17px;
  }
  .admin-foot {
    flex-direction: column;
    gap: 5px;
  }
  .login-panel {
    padding: 28px 24px;
  }
  .login-panel h1 {
    font-size: 2.1rem;
  }
}
@media (prefers-reduced-motion: reduce) {
  html {
    scroll-behavior: auto;
  }
  *,
  *:before,
  *:after {
    animation: none !important;
    transition: none !important;
  }
}

/* Provider progress stays visible on every admin tab. */
.refresh-progress {
  padding: 21px 24px;
  margin-bottom: 24px;
  border-top: 2px solid var(--brand);
  background: linear-gradient(120deg, #321821, #1a1418);
}
.progress-heading {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 18px;
  margin-bottom: 15px;
}
.progress-heading p {
  margin-bottom: 5px;
}
.progress-heading .text-link {
  white-space: nowrap;
}
.progress-services {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 24px;
  border-top: 1px solid var(--line);
  padding-top: 15px;
}
.progress-services strong {
  font-size: 0.8rem;
  color: var(--accent);
}
.progress-services p {
  margin: 7px 0 0;
  font-size: 0.78rem;
  overflow-wrap: anywhere;
  color: var(--text);
}
@media (max-width: 700px) {
  .refresh-progress {
    padding: 18px;
  }
  .progress-heading {
    flex-direction: column;
    gap: 10px;
  }
  .progress-services {
    grid-template-columns: 1fr;
    gap: 17px;
  }
}

/* The homepage invitation is visible on mobile as well as desktop. */
.play-invite {
  display: flex;
  align-items: center;
  gap: 22px;
  padding: 23px 25px;
  margin: 0 0 36px;
  background: linear-gradient(105deg, #431b25, #22141c);
  border-color: #853344;
}
.play-invite img {
  image-rendering: pixelated;
  object-fit: contain;
  border-radius: 10px;
}
.play-invite > div {
  flex: 1;
}
.play-invite h2 {
  font-size: 1.3rem;
  margin-bottom: 6px;
}
.play-invite .eyebrow {
  font-size: 0.57rem;
  margin-bottom: 6px;
}
.play-invite p:last-child {
  font-size: 0.78rem;
  color: var(--muted);
  margin: 0;
}
.site-header .play-nav {
  color: var(--accent);
  font-weight: 650;
}
@media (max-width: 900px) {
  .site-header .community-nav {
    display: none;
  }
}
@media (max-width: 700px) {
  .play-invite {
    flex-wrap: wrap;
    padding: 20px;
    gap: 16px;
  }
  .play-invite img {
    width: 45px;
    height: 45px;
  }
  .play-invite .button {
    width: 100%;
  }
  .play-invite h2 {
    font-size: 1.17rem;
  }
  .play-invite > div {
    min-width: 180px;
  }
  .site-header nav {
    gap: 10px;
  }
  .site-header .button {
    font-size: 0.64rem;
  }
  .site-header .play-nav {
    font-size: 0.69rem;
  }
}

/* Community release: tighter hierarchy and readable, consistent controls. */
:root {
  --muted: #c8b8be;
  font-size: 16px;
  --radius: 14px;
}
.hero {
  padding: 32px 0 27px;
  gap: 30px;
}
.hero h1 {
  font-size: clamp(2rem, 3.6vw, 3.1rem);
  margin-bottom: 13px;
}
.hero-links {
  margin-top: 17px;
  gap: 20px;
}
.hero .lead {
  font-size: 0.92rem;
  margin-bottom: 10px;
}
.race-clock {
  padding: 23px;
}
.clock {
  margin: 18px 0 12px;
}
.play-invite {
  padding: 16px 20px;
  gap: 17px;
  margin-bottom: 28px;
}
.play-invite h2 {
  font-size: 1.13rem;
}
.play-invite p:last-of-type {
  font-size: 0.79rem;
}
.play-invite .eyebrow {
  font-size: 0.63rem;
}
.invite-copy {
  min-width: 0;
}
#inviteHealth {
  appearance: none;
  -webkit-appearance: none;
  height: 5px;
  display: block;
  width: min(100%, 390px);
  border: 0;
  background: #4b2934;
  border-radius: 6px;
  margin-top: 9px;
  accent-color: var(--brand);
}
#inviteHealth::-webkit-progress-bar {
  background: #4b2934;
  border-radius: 6px;
}
#inviteHealth::-webkit-progress-value {
  background: var(--brand);
  border-radius: 6px;
}
#inviteHealth::-moz-progress-bar {
  background: var(--brand);
}
.source-status small,
.leaderboard-foot,
.podium-values small,
.clock-footer,
.race-clock p {
  font-size: 0.74rem;
}
.podium-top .eyebrow {
  font-size: 0.62rem;
}
.field label {
  font-size: 0.85rem;
}
.field small,
.small {
  font-size: 0.8rem;
}
.button {
  min-height: 44px;
}
.button.small {
  min-height: 40px;
}
.ui-icon {
  vertical-align: middle;
  flex-shrink: 0;
}
.connection-summary > span:first-child {
  display: grid;
  gap: 8px;
}
.connection-summary strong {
  font-size: 0.94rem;
}
.connection-chips {
  display: flex;
  flex-wrap: wrap;
  gap: 9px 20px;
  color: var(--muted);
  font-size: 0.76rem;
  font-weight: 450;
}
.connection-chips .has-error {
  color: var(--warning);
}
.refresh-progress {
  padding: 18px 22px;
  margin-bottom: 23px;
}
.refresh-progress > summary {
  font-size: 0.82rem;
}
.connection-details {
  padding-top: 19px;
  border-top: 1px solid var(--line);
  margin-top: 18px;
}
.connection-details .progress-services {
  border: 0;
  padding-top: 4px;
}
.progress-services form {
  margin: 7px 0 0;
}
.progress-services .text-button {
  padding-left: 0;
  color: var(--accent);
}
.admin-shortcuts {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 18px;
}
.admin-shortcuts > a {
  padding: 24px;
  background: linear-gradient(120deg, #291821, var(--panel));
}
.admin-shortcuts h2 {
  font-size: 1.25rem;
  margin: 16px 0 10px;
}
.admin-shortcuts p {
  color: var(--muted);
  font-size: 0.83rem;
  margin: 0;
}
.change-review {
  padding: 22px;
  margin-bottom: 20px;
}
.change-review h2 {
  font-size: 1.35rem;
}
.change-review table {
  table-layout: fixed;
  min-width: 480px;
}
.change-review th,
.change-review td {
  white-space: normal;
  overflow-wrap: anywhere;
  vertical-align: top;
}
.change-review th:first-child {
  width: 26%;
}
.change-review > p:last-child {
  margin: 14px 0 0;
}
.checkpoint-status {
  padding: 16px 18px;
  border: 1px solid #77414c;
  border-radius: 10px;
  background: #341d27;
  margin: 18px 0;
}
.checkpoint-status p {
  margin: 6px 0;
  font-size: 0.85rem;
}
.checkpoint-status small {
  color: var(--muted);
  font-size: 0.75rem;
}
.recovery-review {
  padding: 18px;
  border: 1px solid var(--line);
  border-radius: 10px;
}
.recovery-review dl {
  display: grid;
  grid-template-columns: 120px minmax(0, 1fr);
  gap: 10px;
  font-size: 0.85rem;
}
.recovery-review dt {
  color: var(--muted);
}
.recovery-review dd {
  margin: 0;
  overflow-wrap: anywhere;
}
.admin-foot {
  font-size: 0.74rem;
}
.site-header nav {
  font-size: 0.83rem;
}
@media (max-width: 700px) {
  .hero {
    padding: 26px 0 22px;
    gap: 20px;
  }
  .hero h1 {
    font-size: 2.2rem;
    margin-top: 10px;
  }
  .hero .lead {
    font-size: 0.91rem;
  }
  .race-clock {
    padding: 20px;
  }
  .clock {
    font-size: 1.65rem;
    margin: 14px 0 10px;
  }
  .clock-footer {
    font-size: 0.73rem;
  }
  .play-invite {
    padding: 17px;
    gap: 12px;
  }
  .play-invite .button {
    width: 100%;
  }
  .play-invite > div {
    min-width: 190px;
  }
  .play-invite img {
    width: 42px;
    height: 42px;
  }
  .podium-values small {
    font-size: 0.67rem;
  }
  .podium-top .eyebrow {
    font-size: 0.59rem;
  }
  .public-table th {
    font-size: 0.68rem;
  }
  .public-table td {
    font-size: 0.83rem;
  }
  .source-status small {
    font-size: 0.72rem;
  }
  .site-header nav {
    gap: 9px;
  }
  .site-header .button {
    font-size: 0.69rem;
  }
  .site-header .play-nav {
    font-size: 0.74rem;
  }
  .brand {
    font-size: 0.75rem;
    letter-spacing: 0.01em;
  }
  .brand-sub {
    font-size: 0.43rem;
  }
  .admin-shortcuts {
    grid-template-columns: 1fr;
  }
  .refresh-progress {
    padding: 17px;
  }
  .connection-chips {
    gap: 7px 14px;
    font-size: 0.73rem;
  }
  .connection-summary {
    align-items: flex-start;
  }
  .connection-summary > span:last-child {
    font-size: 0.69rem;
  }
  .recovery-review dl {
    grid-template-columns: 1fr;
    gap: 5px;
  }
  .recovery-review dd {
    margin-bottom: 10px;
  }
  .change-review {
    padding: 18px;
  }
  .tabs a {
    font-size: 0.78rem;
  }
  .tabs {
    gap: 4px;
  }
}
```

## storage.py

```python
"""Atomic UTF-8 file storage. No database service, SQL runtime, or setup command.

One small JSON document holds current state. A process lock serializes writers,
including a brief local deployment overlap. Writes use fsync + atomic replace;
a failed write never publishes half a raid. Keep one App Platform instance.
"""
from contextlib import contextmanager
import copy
import json
import logging
import os
from pathlib import Path
import secrets
import tempfile
import threading
import time

from werkzeug.security import generate_password_hash
from race_support import read_json, clean_snapshots, race_key
from store_schema import upgrade_store
from race import empty
from boss import validate_boss
from boss_avatar import validate_avatar
from presentation import valid_marker

LOG = logging.getLogger("redhunllef")


class StoreError(RuntimeError):
    pass


class Conflict(StoreError):
    pass


def encode(value):
    return json.dumps(value, separators=(",", ":"), ensure_ascii=False, allow_nan=False)


def atomic_json(path, value):
    """Create the replacement beside its target so rename stays atomic."""
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, temporary = tempfile.mkstemp(prefix=path.name + ".", suffix=".tmp", dir=path.parent)
    try:
        with os.fdopen(fd, "w", encoding="utf-8", newline="\n") as output:
            output.write(encode(value))
            output.flush()
            os.fsync(output.fileno())
        os.replace(temporary, path)
        if os.name != "nt":
            directory = os.open(path.parent, os.O_RDONLY)
            try:
                os.fsync(directory)
            finally:
                os.close(directory)
    finally:
        if os.path.exists(temporary):
            os.unlink(temporary)


class Store:
    def __init__(self, config):
        self.config, self.key, self.pg = config, config.state_key, False
        self.path = config.state_path
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.lock = threading.RLock()
        self.cached, self.stamp = None, None
        self.initialize()

    @contextmanager
    def _file_lock(self):
        # The lock file is separate from the atomically replaced state file.
        with open(str(self.path) + ".lock", "a+b") as handle:
            if os.name == "nt":
                import msvcrt
                handle.seek(0, os.SEEK_END)
                if not handle.tell():
                    handle.write(b"0"); handle.flush()
                handle.seek(0)
                msvcrt.locking(handle.fileno(), msvcrt.LK_LOCK, 1)
            else:
                import fcntl
                fcntl.flock(handle, fcntl.LOCK_EX)
            try:
                yield
            finally:
                if os.name == "nt":
                    handle.seek(0)
                    msvcrt.locking(handle.fileno(), msvcrt.LK_UNLCK, 1)
                else:
                    fcntl.flock(handle, fcntl.LOCK_UN)

    def _remember(self, value):
        # We just committed these exact bytes. Avoid re-parsing them on the next
        # poll while still noticing another process's atomic replacement.
        stat = self.path.stat()
        self.cached = value
        self.stamp = (stat.st_mtime_ns, stat.st_size, stat.st_ino)

    def _disk(self):
        if not self.path.exists():
            if self.cached is not None:
                raise StoreError("The saved state file is missing. Restore it; accounts were not reset.")
            return None
        stat = self.path.stat()
        stamp = (stat.st_mtime_ns, stat.st_size, stat.st_ino)
        if stamp != self.stamp:
            value = read_json(self.path)
            if (not isinstance(value, dict) or value.get("format") != 1 or value.get("key") != self.key
                    or type(value.get("revision")) is not int or value["revision"] < 1
                    or not isinstance(value.get("admin"), dict) or not isinstance(value.get("live"), dict)):
                raise StoreError("The saved state file is invalid. It was not overwritten.")
            self.cached, self.stamp = value, stamp
        return self.cached

    @contextmanager
    def connection(self, transaction=False):
        """Existing call sites use this as a transaction, not a SQL connection."""
        with self.lock:
            try:
                with self._file_lock():
                    current = self._disk()
                    value = copy.deepcopy(current) if transaction else current
                    yield value
                    if transaction and value != current:
                        atomic_json(self.path, value)
                        self._remember(value)
            except (Conflict, ValueError, RuntimeError):
                raise
            except OSError as exc:
                LOG.error("STORAGE Local file operation failed (%s).", type(exc).__name__)
                raise StoreError("Local storage could not be read or written. Check free space and the data folder permissions; keep your saved file.") from None

    def initialize(self):
        with self.lock, self._file_lock():
            existing = self._disk()
            if existing is not None:
                upgrade_store(existing["admin"], self.config.site, {})
                if not existing['admin'].get('users'):
                    raise StoreError('Saved account store contains no accounts. It was not replaced.')
                if existing.get('boss') is not None:
                    validate_boss(existing['boss'])
                validate_avatar(existing.get('avatar'))
                LOG.info("ACCOUNTS Existing accounts, settings and raid retained from JSON.")
                return
            value = self._import_sqlite()
            if value is None:
                legacy, source = None, "first-run defaults"
                for path in (self.config.recovery, self.config.legacy, self.config.seed):
                    if path.is_file():
                        legacy, source = read_json(path), path.name
                        break
                if legacy is None:
                    legacy = dict(version=7, users={self.config.superadmin: dict(
                        pw_hash=generate_password_hash(self.config.bootstrap_password), auth_version=1)},
                        secret_key=secrets.token_hex(32), site_settings=self.config.site)
                admin, _ = upgrade_store(legacy, self.config.site, {})
                game = admin.pop("community_boss", None)
                game = validate_boss(game) if game is not None else None
                avatar = validate_avatar(admin.pop("community_boss_avatar", None))
                marker = valid_marker(admin.pop("recovery_export", None))
                if not admin["users"]:
                    raise StoreError("Saved account store contains no accounts. The original was not replaced.")
                snapshots = clean_snapshots(admin.pop("leaderboard_snapshots"), race_key(admin["site_settings"]))
                admin.pop("health", None)
                admin["superadmin"] = self.config.superadmin
                saved = empty(admin["site_settings"])
                saved.update(rows=snapshots["last_top15"], previous_top=snapshots["prev_top15"],
                             updated_at=snapshots["updated_at"] or 0, snapshot_only=bool(snapshots["last_top15"]),
                             count=len(snapshots["last_top15"]), warning="Only the saved Top 15 is available until Shuffle responds." if snapshots["last_top15"] else "")
                saved["source"] = [dict(username=r["username"], weighted=r["original_weighted_wager"],
                                        raw=r["raw_wager"], row_count=r["row_count"]) for r in saved["rows"]]
                value = dict(format=1, key=self.key, revision=1, admin=admin, live={"shuffle": saved},
                             boss=game, avatar=avatar, checkpoint=marker, recoveries=[])
                self.backup_in(value, "before-rebuild-import", {"admin": legacy, "source": source})
                LOG.info("MIGRATION Imported %s; original accounts, hashes and dates retained.", source)
            atomic_json(self.path, value)
            self._remember(value)
            LOG.info("STORAGE JSON save ready. No SQL or extra service is used.")

    def _import_sqlite(self):
        """One-time, read-only bridge from the previous release. Never delete it."""
        path = self.config.db_path
        if not path.is_file():
            return None
        import sqlite3  # Standard library, used only for the old-save import.
        try:
            with sqlite3.connect(path.resolve().as_uri() + "?mode=ro", uri=True) as old:
                old.execute("BEGIN")
                row = old.execute("SELECT revision,document FROM rh_admin WHERE name=?", (self.key,)).fetchone()
                if not row:
                    raise StoreError("The previous local save has no matching account record. It was not replaced.")
                admin = json.loads(row[1])
                upgrade_store(admin, self.config.site, {})
                if not admin.get('users'):
                    raise StoreError('The previous local save has no accounts. It was not replaced.')
                tables = {r[0] for r in old.execute("SELECT name FROM sqlite_master WHERE type='table'")}
                value = dict(format=1, key=self.key, revision=row[0], admin=admin,
                             live={r[0]: json.loads(r[1]) for r in old.execute("SELECT service,document FROM rh_live WHERE name=?", (self.key,))},
                             recoveries=[])
                for field, table in (("boss", "rh_boss"), ("avatar", "rh_boss_avatar"), ("checkpoint", "rh_checkpoint")):
                    row = old.execute(f"SELECT document FROM {table} WHERE name=?", (self.key,)).fetchone() if table in tables else None
                    value[field] = json.loads(row[0]) if row else None
                if value['boss'] is not None: validate_boss(value['boss'])
                validate_avatar(value['avatar'])
                if 'rh_recovery' in tables:
                    for reason, created, document in old.execute("SELECT reason,created,document FROM rh_recovery WHERE name=? ORDER BY created DESC LIMIT 10", (self.key,)):
                        self.backup_in(value, reason, json.loads(document), created=created)
        except (sqlite3.Error, ValueError) as exc:
            raise StoreError("The old local save could not be imported. Keep it intact; no default accounts or raid replaced it.") from exc
        LOG.info("MIGRATION Previous SQLite save imported into JSON; old file left intact. New writes use JSON only.")
        return value

    def admin(self):
        with self.connection() as value:
            return value['revision'], copy.deepcopy(value['admin'])

    def boss_read(self, conn):
        return copy.deepcopy(conn.get('boss'))

    def boss_write(self, conn, value):
        conn['boss'] = copy.deepcopy(value)

    def avatar(self, conn):
        return copy.deepcopy(conn.get('avatar'))

    def avatar_in(self, conn, value):
        conn['avatar'] = copy.deepcopy(value)

    def checkpoint(self, marker=None):
        if marker is not None:
            marker = valid_marker(marker)
            if marker is None: raise ValueError("Invalid recovery export metadata.")
        with self.connection(transaction=marker is not None) as value:
            if marker is not None: value['checkpoint'] = marker
            return copy.deepcopy(value.get('checkpoint'))

    def live(self, service):
        with self.connection() as value:
            return copy.deepcopy(value['live'].get(service))

    def live_in(self, conn, service, value):
        conn['live'][service] = copy.deepcopy(value)

    def publish(self, service, value, expected_revision=None):
        with self.connection(transaction=True) as conn:
            if expected_revision is not None and conn['revision'] != expected_revision:
                raise Conflict("Race settings changed during the provider check; a new check is queued.")
            self.live_in(conn, service, value)

    def save(self, value, revision, *, snapshot=None, backup_reason=None):
        with self.connection(transaction=True) as conn:
            if conn['revision'] != revision:
                raise Conflict("Another administrator saved changes. Reload and review before saving again.")
            if backup_reason:
                self.backup_in(conn, backup_reason, {'admin': conn['admin'], 'live': conn['live']})
            conn['admin'], conn['revision'] = copy.deepcopy(value), revision + 1
            if snapshot is not None: self.live_in(conn, 'shuffle', snapshot)
        return revision + 1

    def backup_in(self, conn, reason, document, *, created=None):
        # Local recovery copies are bounded and are NOT a remote backup service.
        created = int(time.time()) if created is None else created
        folder = self.path.parent / 'recovery'
        name = f"{created}-{secrets.token_hex(8)}.json"
        atomic_json(folder / name, dict(reason=reason, created=created, document=document))
        records = conn.setdefault('recoveries', [])
        records.append(dict(file=name, reason=reason, created=created))
        conn['recoveries'] = records[-10:]
        # Retain a few additional files so a failed parent commit never deletes
        # a recovery file still referenced by the committed state.
        for path in sorted(folder.glob('*.json'), key=lambda p: p.stat().st_mtime_ns, reverse=True)[20:]:
            path.unlink(missing_ok=True)

    @contextmanager
    def job(self, service):
        yield True

    def close_job(self):
        pass

    def close(self):
        pass
```

## store_schema.py

```python
"""Non-destructive document validation shared by startup and migration tools."""
from __future__ import annotations
import copy
import secrets
import time
from race_support import STORE_VERSION, canonical_site, clean_overrides, clean_snapshots, integer, race_key, validate_site


def upgrade_store(value, defaults, health_defaults):
    """Upgrade additively and preserve password hashes, settings, and history."""
    if not isinstance(value, dict):
        raise ValueError("The admin store must contain a JSON object.")
    original = copy.deepcopy(value)
    store = copy.deepcopy(value)
    version = integer(store.get("version"))
    if version > STORE_VERSION:
        raise RuntimeError("This admin store belongs to a newer application version.")
    users = store.setdefault("users", {})
    if not isinstance(users, dict):
        raise RuntimeError("Admin accounts are malformed. Restore a verified recovery copy.")
    seen = set()
    for username, record in users.items():
        if not isinstance(record, dict) or not isinstance(record.get("pw_hash"), str):
            raise RuntimeError("An admin account is malformed. The original store is unchanged.")
        folded = username.casefold()
        if folded in seen:
            raise RuntimeError("Duplicate case-insensitive admin usernames need offline resolution before upgrade.")
        seen.add(folded)
        record.setdefault("auth_version", 1)
    secret = str(store.get("secret_key") or "")
    if version < 3 or len(secret) < 32 or secret.upper().startswith(("REPLACE_", "GENERATED_")):
        store["secret_key"] = secrets.token_hex(32)
    raw_site = store.get("site_settings", {})
    if not isinstance(raw_site, dict):
        raise ValueError("Saved race settings must be an object; they were not replaced with defaults.")
    site = canonical_site(raw_site, defaults)
    errors = validate_site(site)
    if errors:
        raise RuntimeError("Saved race settings need correction: " + "; ".join(errors.values()))
    store["site_settings"] = site
    store.setdefault("settings_revision", 1)
    store.setdefault("data_revision", 1)
    for field in ("settings_revision", "data_revision"):
        if isinstance(store[field], bool) or not isinstance(store[field], int) or store[field] < 1:
            raise ValueError("Saved revision counters must be positive integers.")
    store.setdefault("overrides", {})
    store["overrides"] = clean_overrides(store["overrides"])
    store.setdefault("race_history", [])
    store.setdefault("audit_log", [])
    store.setdefault("banned_ips", [])
    for key in ("race_history", "audit_log", "banned_ips"):
        if not isinstance(store[key], list):
            raise RuntimeError("Saved " + key + " has an invalid format.")
    for entry in store["race_history"]:
        if not isinstance(entry, dict) or not isinstance(entry.get("site_settings"), dict):
            raise ValueError("An archived race has invalid settings.")
        archived_site = canonical_site(entry["site_settings"], defaults)
        if validate_site(archived_site):
            raise ValueError("An archived race has invalid dates, prizes, or links.")
        clean_overrides(entry.get("overrides", {}))
        clean_snapshots(entry.get("leaderboard_snapshots", {}), race_key(archived_site))
    health = store.setdefault("health", {})
    if not isinstance(health, dict):
        raise RuntimeError("Saved health data has an invalid format.")
    for key, default in health_defaults.items():
        health.setdefault(key, default)
    if "http://" in str(health.get("last_error") or "") or "https://" in str(health.get("last_error") or ""):
        health["last_error"] = "Previous external-service error redacted during migration."
    snapshots = store.setdefault("leaderboard_snapshots", {})
    if not isinstance(snapshots, dict):
        raise ValueError("Saved leaderboard snapshots must be an object.")
    snapshots.setdefault("last_top15", snapshots.get("last_top11") or [])
    snapshots.setdefault("prev_top15", snapshots.get("prev_top11") or [])
    snapshots.setdefault("updated_at", None)
    snapshots.setdefault("race_key", race_key(site))
    # Validate a legacy snapshot without discarding any unknown original fields.
    clean_snapshots(snapshots, race_key(site))
    health["last_success"] = health.get("last_success") or snapshots.get("updated_at") or 0
    store.pop("payout_status", None)
    store["version"] = STORE_VERSION
    store.setdefault("updated_at", int(time.time()))
    return store, store != original
```

## templates/admin.html

```html
{% extends 'base.html' %}{% from 'macros.html' import form_fields,field,player_rows with context %}
{% block title %}{{ tabs[tab] }} · RedHunllef Admin{% endblock %}
{% block attributes %}data-page="admin" data-feed="/admin/status" data-bootstrap="{{ {'server_time':data.server_time,'site':data.site}|tojson|forceescape }}"{% endblock %}
{% block styles %}{% if tab=='boss' %}<link rel="stylesheet" href="{{ url_for('static',filename='boss.css',v=asset_version) }}">{% endif %}{% endblock %}
{% block scripts %}{% if tab=='boss' %}<script src="{{ url_for('static',filename='boss.js',v=asset_version) }}" defer></script>{% endif %}{% endblock %}
{% block navigation %}<a href="/" target="_blank" rel="noopener">View website ↗</a><form method="post" action="/admin/logout"><input type="hidden" name="csrf" value="{{ csrf() }}"><button class="text-button" type="submit">Sign out</button></form>{% endblock %}
{% block content %}<main id="main" class="shell admin-main"><div class="admin-heading"><div><p class="eyebrow">CONTROL CENTER</p><h1>Your race, at a glance<span class="accent">.</span></h1><p class="muted">Welcome, {{ user }} <span class="tag">{{ 'Superadmin' if superadmin else 'Admin' }}</span></p></div><form method="post" action="/admin/action" data-refresh>{{ form_fields('refresh',tab,revision) }}<button type="submit" class="button primary">↻ Refresh data</button></form></div>
<nav class="tabs" aria-label="Administration">{% for key,label in tabs.items() %}<a href="{{ url_for('login',tab=key) }}" {% if tab==key %}aria-current="page"{% endif %}>{{ label }}</a>{% endfor %}<span class="auto-label"><span class="dot"></span> {{ 'Boss · 5 sec / Sources · 60 sec' if tab=='boss' else 'Automatic · 60 sec' }}</span></nav>
{% if hosted_local %}<p class="notice warning">Local storage is active. On App Platform, saved changes can be lost when the app is redeployed or replaced. {% if superadmin %}<a class="text-link" href="/admin?tab=settings#recovery">Save a private recovery file →</a>{% else %}Ask the Superadmin to save a private recovery file after important changes.{% endif %}</p>{% endif %}
{% with messages=get_flashed_messages() %}{% for message in messages %}<p class="notice success" role="status">{{ message }}</p>{% endfor %}{% endwith %}
{% if errors %}<div class="notice warning" role="alert"><strong>Review before saving.</strong><ul>{% for key,message in errors.items() %}<li>{{ message }}</li>{% endfor %}</ul></div>{% endif %}
{% if tab in ['overview','race','players'] %}<p id="leaderboardMessage" class="notice" role="status" {% if not data.leaderboard_message %}hidden{% endif %}>{{ data.leaderboard_message }}</p>{% endif %}
<p id="networkError" class="notice warning" role="status" hidden></p><p id="sourceWarning" class="notice warning" role="status" {% if not data.freshness.warning %}hidden{% endif %}>{{ data.freshness.warning }}</p>
{% if tab in ['overview','race','players'] %}<div id="endedNotice" class="notice ended-notice" {% if data.site.race_state!='ended' %}hidden{% endif %}><div><strong>This saved race has ended.</strong><span>New wagers outside its dates do not count toward these results.</span></div><a class="button small" href="{{ url_for('login',tab='race') }}">Prepare next race →</a></div>{% endif %}
<details class="panel refresh-progress" id="connectionDetails" {% if data.jobs.shuffle.error or data.jobs.kick.error %}open{% endif %}>
<summary class="connection-summary"><span><strong>Live connections</strong><span class="connection-chips"><span id="shuffleSummary">Shuffle · {{ 'Needs attention' if data.jobs.shuffle.error else 'Checking automatically' }}</span><span id="kickSummary">Kick · {{ 'Needs attention' if data.jobs.kick.error else 'Checking automatically' }}</span></span></span><span class="small muted">Details <span aria-hidden="true">⌄</span></span></summary>
<div class="connection-details"><div class="progress-heading"><p id="publishedWindow" class="muted small">Published window: {{ data.site.start_et }} → {{ data.site.end_et }}</p><a class="text-link" href="/admin/diagnostics">Download diagnostics</a></div>
<div class="progress-services">{% for name,label in [('shuffle','Shuffle · Leaderboard'),('kick','Kick · Stream status')] %}<div><strong>{{ label }}</strong><p id="{{ name }}Freshness" class="small muted"></p><p id="{{ name }}Progress" role="status">{{ data.jobs[name].error or 'Automatic check queued.' }}</p><form method="post" action="/admin/action" data-refresh>{{ form_fields('refresh',tab,revision) }}<input type="hidden" name="service" value="{{ name }}"><button class="text-button small" type="submit">Check {{ name|capitalize }} now</button></form></div>{% endfor %}</div></div>
</details>
{% include 'admin_' ~ tab ~ '.html' %}
<div class="admin-foot"><span id="browserCheck">Connecting to automatic updates…</span><span>Release {{ release }}</span></div>
<noscript><p class="notice">Forms and navigation work without JavaScript. Reload for current statistics.</p></noscript></main>{% endblock %}
{% block site_footer %}{% endblock %}
```

## templates/admin_boss.html

```html
<section class="panel form-panel" data-boss-root data-mode="admin" data-boss-bootstrap="{{ {'state':boss_data,'csrf':csrf()}|tojson|forceescape }}">
<div class="section-title"><div><p class="eyebrow">ONE SHARED COMMUNITY RAID</p><h2 id="bossName">{{ boss_data.name }}</h2></div><a href="/play" class="button primary" target="_blank" rel="noopener">Open the arena ↗</a></div>
<p id="bossConnection" class="muted small" role="status">Connecting to the raid…</p><p id="bossError" class="notice warning" role="alert" hidden></p>
<div class="hp-label"><strong id="bossHealth">{{ '{:,}'.format(boss_data.hp) }} / {{ '{:,}'.format(boss_data.max_hp) }} HP</strong><span id="bossPercent"></span></div><progress id="bossHealthBar" class="health-bar" value="{{ boss_data.max_hp - boss_data.hp }}" max="{{ boss_data.max_hp }}" aria-label="Boss defeat progress"></progress><p id="bossStory" class="muted"></p>
<div class="raid-stats"><div><strong id="bossRaiders">{{ boss_data.raiders }}</strong><span>raiders</span></div><div><strong id="bossAttacks">{{ boss_data.total_attacks }}</strong><span>attacks</span></div><div><strong id="bossDamage">{{ boss_data.total_damage }}</strong><span>damage</span></div></div>
<p class="muted small">Live · Updates every 5 seconds</p>
<section class="boss-balance" aria-labelledby="paceHeading">
  <div><p class="eyebrow">RECENT RAID PACE</p><h3 id="paceHeading">Plan the next boss</h3><strong id="bossPace">Collecting recent hits…</strong><p id="bossEstimate" class="muted small"></p></div>
  <p class="small muted">An estimate from the last hour, after at least 5 minutes and 10 hits. Attendance and damage settings can change it. HP is never adjusted automatically.</p>
</section>
<section class="boss-admin-leaders" aria-labelledby="adminLeadersHeading">
  <h3 id="adminLeadersHeading">Top 5 damage <span class="tag">Admin only</span></h3>
  <p class="small muted">Full player-submitted names. A Shuffle name match confirms spelling in the feed, not account ownership or an IP match.</p>
  <ol id="adminBossLeaders" class="combat-list">
    {% for row in boss_data.admin_leaders %}<li><div><strong>{{ loop.index }}. {{ row.name }}</strong><small>{{ row.alias }} · {{ row.attacks }} hits · {{ 'Self-reported' if row.name_provided else 'Username not supplied yet' }}</small></div><b>{{ '{:,}'.format(row.damage) }}</b></li>
    {% else %}<li class="muted">No hits yet.</li>{% endfor %}
  </ol>
</section>
{% if user %}<div class="button-row"><form method="post" action="/admin/boss/action"><input type="hidden" name="csrf" value="{{ csrf() }}"><input type="hidden" name="raid_id" value="{{ boss_data.raid_id }}"><button class="button" type="submit" name="action" value="pause">Pause attacks</button></form><form method="post" action="/admin/boss/action"><input type="hidden" name="csrf" value="{{ csrf() }}"><input type="hidden" name="raid_id" value="{{ boss_data.raid_id }}"><button class="button" type="submit" name="action" value="resume">Resume attacks</button></form>{% if superadmin %}<a class="button" href="/admin/recovery-backup">Save private recovery checkpoint</a>{% endif %}</div>
<div class="boss-settings-grid">
  <section class="boss-setting" aria-labelledby="avatarHeading">
    <h3 id="avatarHeading">Boss avatar</h3>
    <img class="boss-avatar-preview{% if boss_data.avatar_custom %} custom-avatar{% endif %}"
         data-boss-avatar src="{{ boss_data.avatar_url }}" alt="Current boss avatar" width="128" height="128">
    <form method="post" action="/admin/boss/action" enctype="multipart/form-data" class="stack">
      <input type="hidden" name="csrf" value="{{ csrf() }}">
      <input type="hidden" name="raid_id" value="{{ boss_data.raid_id }}">
      <input type="hidden" name="action" value="avatar">
      <div class="field">
        <label for="bossAvatarFile">PNG, JPG, JPEG or WebP image</label>
        <input id="bossAvatarFile" name="avatar" type="file" accept=".png,.jpg,.jpeg,.webp,image/png,image/jpeg,image/webp" required>
        <small class="muted">Up to 4 MB. Resized automatically.</small>
      </div>
      <button class="button primary" type="submit">Upload avatar</button>
    </form>
    <form method="post" action="/admin/boss/action">
      <input type="hidden" name="csrf" value="{{ csrf() }}">
      <input type="hidden" name="raid_id" value="{{ boss_data.raid_id }}">
      <button class="text-button" type="submit" name="action" value="avatar_reset">Use original avatar</button>
    </form>
  </section>
  <section class="boss-setting" aria-labelledby="healthHeading">
    <h3 id="healthHeading">Current raid health</h3>
    <form method="post" action="/admin/boss/action" class="stack" id="bossHealthForm">
      <input type="hidden" name="csrf" value="{{ csrf() }}">
      <input type="hidden" name="raid_id" value="{{ boss_data.raid_id }}">
      <input type="hidden" name="action" value="health">
      <input type="hidden" name="health_revision" value="{{ boss_data.health_revision }}">
      <div class="field">
        <label for="bossMaxHealth">Maximum HP</label>
        <input id="bossMaxHealth" name="health" type="number" min="{{ boss_data.rules.min_hp }}"
               max="{{ boss_data.rules.max_hp }}" step="1" value="{{ boss_data.max_hp }}" required>
        <small class="muted">Damage already dealt stays. Raising maximum HP adds the difference to remaining HP. Lowering it may defeat the boss. Recorded damage is retained.</small>
      </div>
      <output id="maxHealthPreview" class="edit-preview" aria-live="polite"></output>
      <p class="muted small">This changes the current boss without clearing players or cooldowns. Raising HP can reopen a defeated boss. Automatic regeneration stays off.</p>
      <label class="boss-confirm"><input type="checkbox" name="confirm_health" value="yes" required> Change this raid's health.</label>
      <button class="button primary" type="submit">Save health</button>
    </form>
    <form method="post" action="/admin/boss/action" class="stack">
      <input type="hidden" name="csrf" value="{{ csrf() }}"><input type="hidden" name="raid_id" value="{{ boss_data.raid_id }}">
      <input type="hidden" name="action" value="remaining_health"><input type="hidden" name="health_revision" value="{{ boss_data.health_revision }}">
      <div class="field"><label for="bossRemainingHealth">Set remaining HP directly</label>
        <input id="bossRemainingHealth" name="health" type="number" min="0" max="{{ boss_data.max_hp }}" step="1" value="{{ boss_data.hp }}" required>
        <small class="muted">0 defeats the boss. Raising this value is an explicit admin heal; automatic regeneration stays off.</small></div>
      <output id="remainingHealthPreview" class="edit-preview" aria-live="polite"></output>
      <label class="boss-confirm"><input type="checkbox" name="confirm_health" value="yes" required> Set the remaining health.</label>
      <button class="button" type="submit">Set remaining HP</button>
    </form>
  </section>
  <section class="boss-setting boss-identity-setting" aria-labelledby="bossSettingsHeading">
    <h3 id="bossSettingsHeading">Boss name &amp; damage</h3>
    <form method="post" action="/admin/boss/action" class="stack" id="bossSettingsForm">
      <input type="hidden" name="csrf" value="{{ csrf() }}">
      <input type="hidden" name="raid_id" value="{{ boss_data.raid_id }}">
      <input type="hidden" name="action" value="settings">
      <input type="hidden" name="settings_revision" value="{{ boss_data.settings_revision }}">
      <div class="field">
        <label for="bossNameInput">Boss name</label>
        <input id="bossNameInput" name="boss_name" maxlength="60" value="{{ boss_data.name }}" required>
      </div>
      <div class="boss-damage-fields">
        <div class="field"><label for="bossBaseDamage">Base damage</label><input id="bossBaseDamage" name="base_damage" type="number" min="0" max="{{ boss_data.rules.max_damage }}" step="1" value="{{ boss_data.rules.damage }}" required></div>
        <div class="field"><label for="bossWeakDamage">Weakness damage</label><input id="bossWeakDamage" name="weak_damage" type="number" min="0" max="{{ boss_data.rules.max_damage }}" step="1" value="{{ boss_data.rules.weak_damage }}" required></div>
        <div class="field"><label for="bossBurstBonus">Burst bonus</label><input id="bossBurstBonus" name="burst_bonus" type="number" min="0" max="{{ boss_data.rules.max_damage }}" step="1" value="{{ boss_data.rules.burst_bonus }}" required></div>
      </div>
      <output id="damagePreview" class="edit-preview" aria-live="polite"></output>
      <p class="muted small">Damage changes apply to future hits. Existing damage and cooldowns stay. The burst bonus applies every tenth hit.</p>
      <button class="button primary" type="submit">Save boss settings</button>
    </form>
  </section>
</div>
<p class="muted small">Player access uses a signed browser cookie. Shared networks can play together without approvals. Each player has a 30-second cooldown. Names survive refreshes, IP changes and new raids; recovery codes restore lost cookies.</p>
<details class="nested"><summary>Start a new raid <span aria-hidden="true">+</span></summary><p class="muted small">Archives this raid and resets damage, current raid totals and cooldowns. Names and achievement progress carry forward. Your avatar, boss name and damage settings stay.</p><form method="post" action="/admin/boss/action" class="boss-restart" data-confirm="Archive the current raid and start a new one? Current progress will become a past-raid summary."><input type="hidden" name="csrf" value="{{ csrf() }}"><input type="hidden" name="raid_id" value="{{ boss_data.raid_id }}"><input type="hidden" name="action" value="restart"><div id="raidPresets" class="preset-row" aria-label="Health presets for the next raid"></div><p id="presetBasis" class="muted small"></p><div class="field"><label for="bossHealthInput">New boss health</label><input id="bossHealthInput" name="health" type="number" min="{{ boss_data.rules.min_hp }}" max="{{ boss_data.rules.max_hp }}" step="1" value="{{ boss_data.rules.default_hp }}" required></div><label class="boss-confirm"><input type="checkbox" name="confirm_restart" value="yes" required> End this raid and begin a new one.</label><button class="button danger" type="submit">Start new raid</button></form></details>{% endif %}
<details class="nested"><summary>Boss admin history <span aria-hidden="true">+</span></summary>
<p class="muted small">Last 100 saved actions. Player hits are tracked separately.</p><ol id="bossAdminHistory" class="combat-list audit-list"></ol></details>
<details class="nested"><summary>Request activity <span aria-hidden="true">+</span></summary>
<p class="muted small">Temporary flags for bursts of rejected requests. These are not bans or proof of cheating. Normal 30-second attacks are allowed. Flags clear on restart.</p><ol id="bossAbuseFlags" class="combat-list"></ol></details>
</section>

{% if superadmin %}{% include "recovery_panel.html" %}{% endif %}
```

## templates/admin_overview.html

```html
<section class="stat-grid"><article class="panel stat"><div class="row"><span class="eyebrow">RACE STATUS</span><span id="raceBadge" class="badge state-{{ data.site.race_state }}">{{ data.site.race_state|capitalize }}</span></div><strong id="countdown" class="stat-value">{{ data.site.race_state|capitalize }}</strong><p id="raceWindow" class="muted">{{ data.site.start_et }} → {{ data.site.end_et }}</p><a class="text-link" href="{{ url_for('login',tab='race') }}">Review schedule →</a></article>
<article class="panel stat"><span class="eyebrow">TOTAL PRIZE POOL</span><strong class="stat-value accent" id="poolTotal">{{ data.site.total_prize }}</strong><p class="muted">Across 15 paid places</p><a class="text-link" href="{{ url_for('login',tab='race') }}#prizes">Manage prizes →</a></article>
<article class="panel stat"><span class="eyebrow">QUALIFYING PLAYERS</span><strong class="stat-value" id="playerCount">{{ data.count }}</strong><p id="dataState">{{ data.freshness.label }}</p><small id="sourceTime" class="muted">{{ fmt_et(data.freshness.updated_at) }}</small></article></section>
<section class="admin-shortcuts"><a class="panel" href="/admin?tab=race"><span class="eyebrow">SCHEDULE & PRIZES</span><h2>Prepare your next race →</h2><p>Review exactly what changes before publishing.</p></a><a class="panel" href="/admin?tab=boss"><span class="eyebrow">YOUR COMMUNITY</span><h2>Manage the boss fight →</h2><p>See shared progress, pause attacks, or open a new raid.</p></a></section>
<section class="panel quick-guide"><div><h3>Keep the race moving.</h3><p class="muted">Set the Eastern Time schedule, review participants, and let automatic updates do the rest.</p></div><a class="button" href="{{ url_for('login',tab='players') }}">View players →</a></section>
```

## templates/admin_players.html

```html
<section class="panel form-panel"><div class="section-title"><div><p class="eyebrow">YOUR COMMUNITY, UNCENSORED</p><h2>Race participants</h2></div><a id="exportLink" class="button small" href="{{ url_for('export',view=request.args.get('view','all'),q=request.args.get('q',''),sort=request.args.get('sort','rank')) }}">↓ Export this view</a></div>
<form class="filter-bar" method="get" action="{{ url_for('login') }}"><input type="hidden" name="tab" value="players"><div class="field grow"><label for="search">Find a player</label><input id="search" name="q" value="{{ request.args.get('q','') }}" placeholder="Search full username"></div><div class="field"><label for="view">Show</label><select id="view" name="view">{% for key,label in [('all','All loaded players'),('top','Top 15'),('overrides','Adjusted players')] %}<option value="{{ key }}" {% if request.args.get('view','all')==key %}selected{% endif %}>{{ label }}</option>{% endfor %}</select></div><div class="field"><label for="sort">Sort by</label><select id="sort" name="sort">{% for key,label in [('rank','Race rank'),('name','Username'),('raw','Raw wager')] %}<option value="{{ key }}" {% if request.args.get('sort','rank')==key %}selected{% endif %}>{{ label }}</option>{% endfor %}</select></div><button class="button" type="submit">Apply</button></form>
<p class="muted small">Up to {{ limit }} qualifying players are loaded. Search and export cover those loaded records. Original race ranks are retained.</p><div class="table-scroll" tabindex="0" role="region" aria-label="Full race participants"><table><thead><tr><th>Rank</th><th>Player</th><th class="number">Effective weighted</th><th class="number">Original weighted</th><th class="number">Raw wager</th><th>Action</th></tr></thead><tbody id="participantsBody">{{ player_rows(participants) }}</tbody></table></div></section>
<section class="panel form-panel" id="override"><div class="section-title"><div><p class="eyebrow">A CLEAR AUDIT TRAIL</p><h2>Adjust a weighted total</h2></div></div><form action="/admin/action" method="post" class="filter-bar" data-dirty>{{ form_fields('override','players',revision) }}{{ field('username','Exact full username',request.args.get('edit','')) }}{{ field('amount','Replacement weighted total',admin.overrides.get(request.args.get('edit',''),''),help='Leave blank to remove the override.',required=false) }}<button class="button primary" type="submit">Save adjustment</button></form><p class="muted small">Raw and original weighted amounts remain available. An override changes the effective ranking amount.</p></section>
<details class="panel form-panel code-red" id="codeRed" {% if request.args.get('code_red')=='1' %}open{% endif %}><summary><div><span class="eyebrow">CODE RED</span><h2>Community wagerers <span class="tag" id="redCount">{{ data.red|length }} / 100</span></h2></div><span class="expand-icon" aria-hidden="true">+</span></summary><div class="details-content"><p class="muted">The first 100 confirmed Code Red wagerers, sorted by weighted wager. Full usernames are visible only to administrators. Overrides do not change this source list.</p><p id="redMembership" class="muted small">{{ data.diagnostics.missing_campaign }} source rows have no campaign metadata; membership cannot be verified for those rows.</p><div class="field js-only"><label for="redSearch">Search these Code Red users</label><input id="redSearch" type="search" placeholder="Full username"></div><div class="table-scroll" tabindex="0" role="region" aria-label="Code Red wagerers"><table><thead><tr><th>#</th><th>Full username</th><th class="number">Weighted wager</th><th class="number">Raw wager</th></tr></thead><tbody id="redBody">{% for row in data.red %}<tr data-red-name="{{ row.username }}"><td>{{ loop.index }}</td><td><strong>{{ row.username }}</strong><button class="copy-button js-only" type="button" data-copy="{{ row.username }}">⧉</button></td><td class="number accent">{{ row.weighted }}</td><td class="number">{{ row.raw }}</td></tr>{% else %}<tr><td colspan="4" class="empty">No confirmed Code Red wagerers for this window.</td></tr>{% endfor %}</tbody></table></div></div></details>
```

## templates/admin_race.html

```html
<form id="raceForm" method="post" action="/admin/action" class="stack" data-dirty>{{ form_fields('save_race','race',revision) }}
{% if confirm_race %}<input type="hidden" name="review_token" value="{{ review_token }}"><div class="notice warning"><strong>These changes are a draft. Confirm below to publish them.</strong><p>Changing the race window archives its results and resets its overrides. Changes to prizes or text keep the current race participants. Review the changes below.</p><p>The saved race stays active until you choose <strong>Confirm and publish race</strong> in the bottom save bar.</p></div>{% endif %}
{% if change_review %}{% include "change_review.html" %}{% endif %}
<section class="panel form-panel"><div class="section-title"><div><p class="eyebrow">THE NEXT CHAPTER</p><h2>Schedule &amp; details</h2></div><div class="button-row js-only"><button class="button small" type="button" id="startNow">Start now</button><button class="button small" type="button" id="nextRace">Prepare next race</button></div></div>
<div class="form-grid">{{ field('start_et','Starts · Eastern Time',form.start_et,'datetime-local',error=errors.get('start_et','')) }}{{ field('end_et','Ends · Eastern Time',form.end_et,'datetime-local',error=errors.get('end_et','')) }}</div><p class="muted small">Eastern Time includes daylight saving. Preparing a schedule creates a draft; saving a new window requires confirmation.</p>
<div class="form-grid">{{ field('site_name','Website name',form.site_name) }}{{ field('race_title','Race title',form.race_title) }}</div>{{ field('race_description','Short description',form.race_description,'textarea',required=false) }}</section>
<section class="panel form-panel" id="prizes"><div class="section-title"><div><p class="eyebrow">REWARD THE CLIMB</p><h2>Placement prizes</h2></div><span class="badge" id="prizeTotal">{{ data.site.total_prize }} total</span></div><div class="prize-grid">{% for n in range(1,16) %}{{ field('prize_'~n,'Place '~n,form['prize_'~n],error=errors.get('prize_'~n,'')) }}{% endfor %}</div></section>
<section class="panel form-panel"><h2>Channels &amp; links</h2><div class="form-grid">{% for key,label,type,required in [('kick_channel_slug','Kick channel name','text',true),('campaign_code_filter','Shuffle campaign code','text',false),('stream_url','Livestream link','url',true),('sponsor_name','Sponsor name','text',true),('sponsor_url','Sponsor link','url',true),('community_name','Community link label','text',false),('community_url','Community link','url',false),('responsible_gambling_url','Responsible play link','url',false)] %}{{ field(key,label,form[key],type,error=errors.get(key,''),required=required) }}{% endfor %}</div></section>
<div class="save-bar"><div><strong id="saveLabel">{{ 'Confirmation required — not published' if confirm_race else 'Review your draft' if errors else 'All changes saved' }}</strong><span class="muted small">Live updates preserve your unfinished edits.</span></div><div class="button-row"><button class="button js-only" type="reset">Discard edits</button><button class="button primary" type="submit" {% if confirm_race %}name="confirm_race" value="yes"{% endif %}>{{ 'Confirm and publish race' if confirm_race else 'Save race settings' }}</button></div></div></form>
```

## templates/admin_settings.html

```html
<section class="panel form-panel"><p class="eyebrow">YOUR ACCESS</p><h2>Account security</h2><form method="post" action="/admin/action" class="form-grid" data-dirty>{{ form_fields('password','settings',revision) }}{{ field('current_password','Current password',type='password') }}{{ field('new_password','New password',type='password',help='At least 12 characters.') }}{{ field('confirm_password','Confirm new password',type='password') }}<div class="field"><span>&nbsp;</span><button class="button primary" type="submit">Update password</button></div></form></section>
{% if superadmin %}<details class="panel form-panel" open><summary><h2>Administrator accounts</h2><span aria-hidden="true">+</span></summary><div class="details-content"><p class="muted">{{ admin.superadmin }} is the protected Superadmin. Existing accounts are retained while their saved storage is available. Use the private recovery file below before redeploying with local storage.</p><div class="account-list">{% for name,record in admin.users.items() %}<div class="account-row"><div><strong>{{ name }}</strong><span class="tag">{{ 'Superadmin' if name|lower==admin.superadmin|lower else 'Admin' }}</span></div>{% if name|lower!=admin.superadmin|lower %}<form action="/admin/action" method="post" data-confirm="Remove this account and revoke its sessions?">{{ form_fields('remove_account','settings',revision) }}<input type="hidden" name="username" value="{{ name }}"><button class="button small danger" type="submit">Remove</button></form>{% endif %}</div>{% endfor %}</div><h3>Add an administrator</h3><form action="/admin/action" method="post" class="form-grid">{{ form_fields('add_account','settings',revision) }}{{ field('username','New username',prefix='add-') }}{{ field('new_password','Initial password',type='password',help='At least 12 characters.',prefix='add-') }}{{ field('confirm_password','Confirm password',type='password',prefix='add-') }}<div class="field"><span>&nbsp;</span><button class="button" type="submit">Add administrator</button></div></form>
<details class="nested"><summary>Reset an administrator password</summary><form action="/admin/action" method="post" class="form-grid" data-confirm="Reset this password and revoke previous sessions?">{{ form_fields('reset_password','settings',revision) }}<div class="field"><label for="resetUser">Account</label><select name="username" id="resetUser">{% for name in admin.users %}<option>{{ name }}</option>{% endfor %}</select></div>{{ field('new_password','Replacement password',type='password',prefix='reset-') }}{{ field('confirm_password','Confirm replacement',type='password',prefix='reset-') }}<div class="field"><span>&nbsp;</span><button class="button" type="submit">Reset password</button></div></form></details></div></details>{% endif %}
<details class="panel form-panel" {% if restore %}open{% endif %}><summary><h2>Backups &amp; race history</h2><span aria-hidden="true">+</span></summary><div class="details-content"><p class="muted">Race backups include settings, results, overrides, and history. Passwords and integration credentials are excluded.</p><a class="button" href="/admin/backup">↓ Download race backup</a><form class="filter-bar" method="post" action="/admin/action" enctype="multipart/form-data">{{ form_fields('preview_restore','settings',revision) }}<div class="field grow"><label for="backupFile">Restore a race backup</label><input id="backupFile" name="backup" type="file" accept=".json,application/json" required></div><button class="button" type="submit">Review backup</button></form>
{% if restore %}<div class="notice warning"><strong>Review this restore</strong><p>{{ restore.start }} → {{ restore.end }} · {{ restore.rows }} saved participants</p><p>{{ restore.overrides }} overrides · {{ restore.history }} archived races. Boss progress and accounts stay intact.</p>{% if restore.changes %}{% with change_review=restore.changes %}{% include "change_review.html" %}{% endwith %}{% endif %}<p>Current race data will be replaced. Accounts remain intact, and a private recovery copy is created first.</p><form method="post" action="/admin/action">{{ form_fields('restore','settings',revision) }}<input type="hidden" name="restore_token" value="{{ restore.token }}"><button class="button danger" type="submit">Confirm restore</button></form></div>{% endif %}
{% for race in admin.race_history|reverse %}<details class="nested"><summary>{{ fmt_et(race.site_settings.start_time) }} → {{ fmt_et(race.site_settings.end_time) }}</summary><div class="table-scroll"><table><thead><tr><th>Rank</th><th>Username</th><th class="number">Weighted wager</th></tr></thead><tbody>{% for row in race.leaderboard_snapshots.last_top15 %}<tr><td>{{ row.rank }}</td><td>{{ row.username }}</td><td class="number">{{ row.wager }}</td></tr>{% else %}<tr><td colspan="3">No saved participants.</td></tr>{% endfor %}</tbody></table></div></details>{% else %}<p class="muted small">Completed races appear here after you save a new window.</p>{% endfor %}</div></details>
{% if superadmin %}{% include 'recovery_panel.html' %}{% endif %}
<details class="panel form-panel" id="diagnostics" open><summary><h2>Connections &amp; diagnostics</h2><span aria-hidden="true">+</span></summary><div class="details-content"><div class="diagnostic-grid">{% for key,label in [('storage','Storage'),('start_et','Race starts'),('end_et','Race ends'),('received','Source records received'),('accepted','Valid race records'),('missing_campaign','Records without campaign')] %}<div><span class="muted small">{{ label }}</span><strong data-diagnostic="{{ key }}">{{ data.diagnostics[key] }}</strong></div>{% endfor %}{% for key,value in data.diagnostics.credentials.items() %}<div><span class="muted small">{{ key|replace('_',' ')|title }}</span><strong>{{ 'Configured' if value.configured else 'Missing' }}</strong><small class="muted">{{ value.source }}</small></div>{% endfor %}</div>
{% for name in ['shuffle','kick'] %}<div class="notice"><strong>{{ name|capitalize }}</strong><p id="{{ name }}Message">{{ data.jobs[name].error or 'Waiting for first update' }}</p><small id="{{ name }}Timing" class="muted">Automatic updates every 60 seconds</small></div>{% endfor %}<a class="button" href="/admin/diagnostics">↓ Download redacted diagnostics</a><p class="muted small">The report excludes keys, password hashes, provider response bodies, and participant usernames.</p></div></details>
<details class="panel form-panel"><summary><h2>Access controls &amp; logs</h2><span aria-hidden="true">+</span></summary><div class="details-content"><form method="post" action="/admin/action" class="filter-bar" data-confirm="Block requests from this IP address?">{{ form_fields('ban_ip','settings',revision) }}{{ field('ip','Block an IPv4 or IPv6 address') }}<button class="button danger" type="submit">Block address</button></form><div class="button-row">{% for ip in admin.banned_ips %}<form action="/admin/action" method="post">{{ form_fields('unban_ip','settings',revision) }}<input type="hidden" name="ip" value="{{ ip }}"><button class="button small" type="submit">Unblock {{ ip }}</button></form>{% endfor %}</div><h3>Recent access</h3><div class="table-scroll"><table><thead><tr><th>Time</th><th>Address</th><th>Path</th><th>Status</th></tr></thead><tbody>{% for row in access_log %}<tr><td>{{ fmt_et(row.time) }}</td><td>{{ row.ip }}</td><td>{{ row.method }} {{ row.path }}</td><td>{{ row.status }}</td></tr>{% endfor %}</tbody></table></div><form method="post" action="/admin/action" data-confirm="Clear recent access entries?">{{ form_fields('clear_access','settings',revision) }}<button class="button small" type="submit">Clear access log</button></form><h3>Administrator activity</h3><div class="table-scroll"><table><thead><tr><th>Time</th><th>Administrator</th><th>Action</th></tr></thead><tbody>{% for row in admin.audit_log|reverse %}<tr><td>{{ row.ts_et }}</td><td>{{ row.admin_user }}</td><td>{{ row.action }}</td></tr>{% endfor %}</tbody></table></div>{% if superadmin %}<form action="/admin/action" method="post" data-confirm="Clear the audit log after saving a private recovery copy?">{{ form_fields('clear_audit','settings',revision) }}<button class="button small" type="submit">Clear audit log</button></form>{% endif %}</div></details>
```

## templates/base.html

```html
<!doctype html>
<html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<meta name="theme-color" content="#160e14"><title>{% block title %}RedHunllef · Wager Race{% endblock %}</title>
<link rel="icon" href="{{ url_for('static', filename='redlogo.ico') }}">
<link rel="stylesheet" href="{{ url_for('static',filename='style.css',v=asset_version) }}">{% block styles %}{% endblock %}</head>
<body {% block attributes %}{% endblock %}>
<a class="skip-link" href="#main">Skip to content</a>
<header class="site-header"><div class="shell header-inner"><a class="brand" href="/"><img src="{{ url_for('static',filename='redlogo.png') }}" alt="" width="36" height="36"><span><span data-site-text="site_name">{{ data.site.site_name if data is defined else 'RedHunllef' }}</span><span class="brand-sub">THE COMMUNITY RACE</span></span></a>
<nav aria-label="Main navigation">{% block navigation %}<a href="/#leaderboard">Leaderboard</a><a class="play-nav" href="/play">Boss fight</a><a class="community-nav" data-site-text="community_name" data-site-link="community_url" href="{{ data.site.community_url }}" {% if not data.site.community_url %}hidden{% endif %} target="_blank" rel="noopener">{{ data.site.community_name }}</a><a class="button small" data-site-link="stream_url" href="{{ data.site.stream_url }}" target="_blank" rel="noopener">Watch on Kick <span aria-hidden="true">↗</span></a>{% endblock %}</nav></div></header>
{% block content %}{% endblock %}
{% block site_footer %}<footer class="shell footer"><span>RedHunllef <span class="muted">· Community first.</span></span><span class="muted">{% block footer %}<a data-site-link="responsible_gambling_url" href="{{ data.site.responsible_gambling_url }}" {% if not data.site.responsible_gambling_url %}hidden{% endif %} target="_blank" rel="noopener">Play responsibly · 18+</a>{% endblock %}</span></footer>{% endblock %}
<div id="toast" class="toast" role="status" hidden></div>
<script src="{{ url_for('static',filename='app.js',v=asset_version) }}" defer></script>
{% block scripts %}{% endblock %}
</body></html>
```

## templates/boss.html

```html
{% extends 'base.html' %}
{% from 'icons.html' import icon %}

{% block title %}Boss fight · RedHunllef{% endblock %}
{% block attributes %}data-page="boss"{% endblock %}
{% block styles %}
<link rel="stylesheet" href="{{ url_for('static', filename='boss.css', v=asset_version) }}">
{% endblock %}
{% block scripts %}
<script src="{{ url_for('static', filename='boss.js', v=asset_version) }}" defer></script>
{% endblock %}

{% block content %}
<main id="main" class="shell boss-page" data-boss-root
      data-boss-bootstrap="{{ {'state': boss_data, 'csrf': csrf()} | tojson | forceescape }}">
  <div class="boss-live">
    <span id="bossConnection" role="status">Connecting…</span>
    <div class="share-tools">
      <button class="button small" id="copyRaidLink" type="button">{{ icon('link', 18) }} Copy link</button>
      <span id="shareResult" class="small muted" role="status"></span>
      <input id="shareUrl" type="text" readonly aria-label="Raid link to copy" hidden>
    </div>
  </div>

  <p id="bossError" class="notice warning" role="alert" hidden></p>
  <button type="button" id="dismissBossError" class="text-button dismiss-error" hidden>Dismiss</button>
  <div id="milestoneBanner" class="milestone-banner" role="status" hidden>
    <strong id="milestoneMessage"></strong>
    <button id="dismissMilestone" class="text-button" type="button" aria-label="Dismiss milestone">{{ icon('close') }}</button>
  </div>

  <div class="raid-layout">
    <section class="arena panel" aria-labelledby="bossName">
      <div class="arena-heading">
        <h1 class="eyebrow">BOSS FIGHT</h1>
        <span class="badge" id="bossPhase">{{ boss_data.phase }}</span>
      </div>
      <div class="boss-stage" id="bossStage">
        <div class="rune-ring" aria-hidden="true"></div>
        <div class="rune-ring inner" aria-hidden="true"></div>
        <span class="arena-rune rune-one" aria-hidden="true">✦</span>
        <span class="arena-rune rune-two" aria-hidden="true">✧</span>
        <img class="boss-sprite{% if boss_data.avatar_custom %} custom-avatar{% endif %}" data-boss-avatar src="{{ boss_data.avatar_url }}"
             alt="{{ boss_data.name }}" width="220" height="220">
        <span id="hitFloat" class="hit-float" aria-hidden="true"></span>
        <span class="boss-shadow" aria-hidden="true"></span>
      </div>
      <div class="boss-name-row">
        <h2 id="bossName">{{ boss_data.name }}</h2>
        <span id="bossDay" class="tag">Raid day {{ boss_data.day }}</span>
      </div>
      <div class="hp-label">
        <strong id="bossHealth">{{ '{:,}'.format(boss_data.hp) }} / {{ '{:,}'.format(boss_data.max_hp) }} HP</strong>
        <span id="bossPercent">{{ '%.2f' | format((boss_data.max_hp - boss_data.hp) / boss_data.max_hp * 100) }}% defeated</span>
      </div>
      <progress id="bossHealthBar" class="health-bar" max="{{ boss_data.max_hp }}"
                value="{{ boss_data.max_hp - boss_data.hp }}" aria-label="Boss defeat progress"></progress>
      <details class="exact-totals"><summary>Exact raid totals</summary><p id="exactRaidTotals" class="small"></p></details>
      <ul id="bossMilestones" class="milestone-rail" aria-label="Community milestones"></ul>
      <div class="rally-status" id="rallyStatus">
        <div><strong id="rallyTitle">Red rally</strong><span id="rallyCount">0 / 15 raiders</span></div>
        <progress id="rallyBar" max="15" value="0" aria-label="Community rally progress"></progress>
        <small id="rallyHint">15 raiders hit within 10 minutes to light the arena.</small>
      </div>
      <div class="raid-stats">
        <div><strong id="bossRaiders">{{ boss_data.raiders }}</strong><span>Raiders</span></div>
        <div><strong id="bossAttacks">{{ boss_data.total_attacks }}</strong><span>Hits</span></div>
        <div><strong id="bossDamage">{{ '{:,}'.format(boss_data.total_damage) }}</strong><span>Damage</span></div>
      </div>
    </section>

    <section class="attack-panel panel" aria-labelledby="yourTurn">
      <h2 id="yourTurn">Attack</h2>
      <div class="weakness-box">
        <span class="weakness-symbol" aria-hidden="true">✦</span>
        <div>
          <small>WEAKNESS</small>
          <strong id="bossWeakness">{{ boss_data.weakness_label }} · {{ boss_data.rules.weak_damage }} damage</strong>
          <span id="wardTimer">—</span>
        </div>
      </div>
      <div class="strike-options" role="group" aria-label="Attack style">
        {% for key, label in boss_data.rules.styles.items() %}
        <button type="button" data-style="{{ key }}" aria-pressed="{{ 'true' if loop.first else 'false' }}">
          <span aria-hidden="true">{{ icon(key, 26) }}</span>
          <strong>{{ label }}</strong>
        </button>
        {% endfor %}
      </div>
      <div class="combo-row">
        <strong>Crimson burst</strong>
        <span id="burstLabel">{{ boss_data.you.burst_in }} hits to +{{ boss_data.rules.burst_bonus }} damage</span>
      </div>
      <div class="burst-meter" id="burstMeter" aria-hidden="true">
        {% for n in range(boss_data.rules.burst_every) %}<span></span>{% endfor %}
      </div>
      <div id="playerIdentity" class="player-identity" hidden>
        <span>Playing as <strong id="playingAs"></strong></span>
        <button id="editPlayerName" type="button" class="text-button">Edit</button>
      </div>
      <form id="playerNameForm" class="player-name-form">
        <label for="playerUsername">Community / Shuffle username</label>
        <div class="player-name-row"><input id="playerUsername" name="username" maxlength="64" required
          autocomplete="username" value="{{ boss_data.you.display_name }}"><button class="button small" type="submit">Save</button></div>
        <small class="muted">Your name stays on this browser. Other players see only your raider alias.</small>
        <span id="playerNameResult" class="small" role="status"></span>
      </form>
      <details id="profileRecovery" class="profile-recovery">
        <summary>Player recovery</summary>
        <div id="recoveryOwner" hidden>
          <button type="button" id="makeRecoveryCode" class="button small">Create recovery code</button>
          <p id="recoverySaved" class="muted small"></p>
          <div id="recoveryCodeBox" hidden>
            <label for="recoveryCode">Keep this code private. It restores your player.</label>
            <textarea id="recoveryCode" readonly rows="3" spellcheck="false"></textarea>
            <button id="downloadRecovery" type="button" class="text-button">Save code as a text file</button>
          </div>
        </div>
        <form id="recoverPlayerForm" class="stack">
          <label for="recoveryInput">Have a saved code?</label>
          <input id="recoveryInput" type="password" maxlength="512" autocomplete="off" required placeholder="Paste your recovery code">
          <button class="button small" type="submit">Recover player</button>
        </form>
        <p id="recoveryResult" class="small" role="status"></p>
      </details>
      <button class="button primary attack-button" id="attackButton" type="button" disabled>Connecting…</button>
      <p id="rearmHint" class="small muted" role="status"></p>
      <p id="hitResult" class="hit-result" role="status"></p>
      <div class="personal-stats">
        <div><strong id="yourDamage">{{ '{:,}'.format(boss_data.you.damage) }}</strong><span>Your damage</span></div>
        <div><strong id="yourAttacks">{{ boss_data.you.attacks }}</strong><span>Your hits</span></div>
        <div><strong id="yourActiveDays">{{ boss_data.you.active_days }}</strong><span>Raid days</span></div>
      </div>
      <p class="raider-name"><strong id="yourName">{{ boss_data.you.name }}</strong></p>
    </section>
  </div>

  <section id="victoryRecap" class="panel victory-recap" hidden>
    <h2>Victory</h2>
    <details>
      <summary>All raiders <span aria-hidden="true">+</span></summary>
      <ol id="allContributors" class="combat-list"></ol>
    </details>
  </section>

  <div class="raid-bottom">
    <section class="panel raid-list">
      <h2>Top raiders</h2>
      <ol id="bossLeaders" class="combat-list"></ol>
    </section>
    <section class="panel raid-list">
      <h2>Recent hits</h2>
      <ol id="bossRecent" class="combat-list"></ol>
    </section>
  </div>
  <details class="panel raid-history" id="badgeDetails">
    <summary>Your achievements · <span id="badgeCount">0 / 8</span></summary>
    <ul id="yourBadges" class="combat-list badge-grid"></ul>
  </details>
  <details class="panel raid-history">
    <summary>Past raids <span aria-hidden="true">+</span></summary>
    <ul class="combat-list" id="bossHistory"></ul>
  </details>

  <section class="mobile-attack-dock" aria-label="Quick attack controls">
    <div>
      <label for="dockStyle">Style</label>
      <select id="dockStyle">
        {% for key, label in boss_data.rules.styles.items() %}<option value="{{ key }}">{{ label }}</option>{% endfor %}
      </select>
      <small id="dockRemaining">30s cooldown · Unlimited hits</small>
    </div>
    <button type="button" class="button primary" id="dockAttack" disabled>Connecting…</button>
  </section>
  <noscript><p class="notice warning">JavaScript is required to play.</p></noscript>
</main>
{% endblock %}
{% block site_footer %}{% endblock %}
```

## templates/change_review.html

```html
<section class="panel change-review" aria-labelledby="changeReviewTitle">
<p class="eyebrow">REVIEW BEFORE PUBLISHING</p><h2 id="changeReviewTitle">Here is exactly what changes.</h2>
<div class="table-scroll" tabindex="0" role="region" aria-label="Current and proposed values"><table><thead><tr><th>Setting</th><th>Current</th><th>Proposed</th></tr></thead><tbody>{% for change in change_review %}<tr><th scope="row">{{ change.label }}</th><td>{{ change.before }}</td><td class="accent">{{ change.after }}</td></tr>{% endfor %}</tbody></table></div>
<p class="small muted">Review expires after 15 minutes. Editing a reviewed value requires a fresh preview before publishing.</p>
</section>
```

## templates/error.html

```html
{% extends 'base.html' %}{% block title %}{{ title }} · RedHunllef{% endblock %}
{% block navigation %}<a href="/">View race ↗</a>{% endblock %}
{% block content %}<main class="shell login-wrap" id="main"><section class="panel login-panel"><p class="eyebrow">REDHUNLLEF</p><h1>{{ title }}</h1><p class="muted">{{ message }}</p><a class="button primary" href="/admin">Return to admin →</a><p class="release">{{ release }}</p></section></main>{% endblock %}
{% block footer %}RedHunllef Wager Race{% endblock %}
```

## templates/icons.html

```html
{% macro icon(name, size=20) -%}
<svg class="ui-icon" width="{{ size }}" height="{{ size }}" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.7" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true" focusable="false">
{% if name=='blade' %}<path d="m4 3 7 3 10 15-7-3L4 3ZM3 16l5 5m-4 0 4-5"/>
{% elif name=='bow' %}<path d="M5 3c18 0 18 18 0 18V3Zm0 0 12 9-12 9M2 12h20m-4-4 4 4-4 4"/>
{% elif name=='magic' %}<path d="m12 2 3 7 7 3-7 3-3 7-3-7-7-3 7-3 3-7Z"/>
{% elif name=='close' %}<path d="m6 6 12 12M18 6 6 18"/>
{% elif name=='link' %}<path d="m9 15 6-6m-5-3 2-2a5 5 0 0 1 7 7l-2 2M7 11l-2 2a5 5 0 0 0 7 7l2-2"/>
{% endif %}</svg>
{%- endmacro %}
```

## templates/index.html

```html
{% extends 'base.html' %}
{% block attributes %}data-page="public" data-feed="/public-state" data-bootstrap="{{ data|tojson|forceescape }}"{% endblock %}
{% block content %}
<main id="main" class="shell">
<section class="hero"><div><div class="eyebrow"><span class="dot"></span> CODE RED. YOUR COMMUNITY.</div><h1 id="raceTitle">{{ data.site.race_title }}</h1><p id="raceDescription" class="lead">{{ data.site.race_description }}</p><div class="hero-links"><a id="sponsorLink" class="sponsor" href="{{ data.site.sponsor_url }}" target="_blank" rel="noopener"><span class="sponsor-symbol">S</span><span><small>POWERED BY</small><strong id="sponsorName">{{ data.site.sponsor_name }}</strong></span><span aria-hidden="true">↗</span></a><span class="tag" id="streamStatus">Checking Kick</span></div></div>
<aside class="race-clock panel"><div class="row"><span class="eyebrow" id="clockLabel">RACE SCHEDULE</span><span id="raceBadge" class="badge state-{{ data.site.race_state }}">{{ data.site.race_state|capitalize }}</span></div><div id="countdown" class="clock" aria-hidden="true">—</div><p id="raceWindow" class="muted">{{ data.site.start_et }} → {{ data.site.end_et }}</p><div class="clock-footer"><span>Prize pool <strong class="accent" id="poolTotal">{{ data.site.total_prize }}</strong></span><span>15 paid places</span></div></aside></section>
<section class="play-invite panel" aria-labelledby="inviteTitle">
<img id="inviteAvatar" src="{{ data.boss.avatar_url }}" class="{% if data.boss.avatar_custom %}custom-avatar{% endif %}" alt="" width="52" height="52">
<div class="invite-copy"><p class="eyebrow"><span id="inviteBossName">{{ data.boss.name }}</span> · COMMUNITY BOSS</p><h2 id="inviteTitle">{{ 'The crew conquered ' ~ data.boss.name ~ '.' if data.boss.status=='victory' else 'The raid is taking a breather.' if data.boss.status=='paused' else 'Red needs a raid party.' }}</h2>
<p id="inviteProgress">{{ '{:,}'.format(data.boss.hp) }} HP left · {{ data.boss.raiders }} raiders united</p>
<progress id="inviteHealth" max="{{ data.boss.max_hp }}" value="{{ data.boss.max_hp - data.boss.hp }}" aria-label="Community boss defeat progress"></progress></div>
<a class="button primary" id="inviteButton" href="/play"><span id="inviteButtonLabel">{{ 'View the victory' if data.boss.status=='victory' else 'View the raid' if data.boss.status=='paused' else 'Join the boss fight' }}</span> <span aria-hidden="true">→</span></a>
</section>
<section id="leaderboard"><div class="section-title"><div><p class="eyebrow">EVERY WAGER COUNTS</p><h2>The leaderboard<span class="accent">.</span></h2></div><div class="source-status"><span id="dataState">{{ data.freshness.label }}</span><small id="sourceTime">{{ fmt_et(data.freshness.updated_at) }}</small></div></div>
<p id="sourceWarning" class="notice warning" role="status" {% if not data.freshness.warning %}hidden{% endif %}>{{ data.freshness.warning }}</p>
<p id="leaderboardMessage" class="notice" role="status" {% if not data.leaderboard_message %}hidden{% endif %}>{{ data.leaderboard_message }}</p>
<p id="networkError" class="notice warning" role="status" hidden></p>
<div class="podium">{% for n in [2,1,3] %}{% set r=data.rows|selectattr('rank','equalto',n)|first %}<article class="podium-card place-{{ n }}" data-rank="{{ n }}"><div class="podium-top"><span class="placement">{{ '%02d'|format(n) }}</span><span class="eyebrow">{{ 'LEADING THE RACE' if n==1 else 'SECOND PLACE' if n==2 else 'THIRD PLACE' }}</span><span class="podium-symbol" aria-hidden="true">{{ '♜' if n==1 else '✦' }}</span></div><strong class="podium-name" data-name>{{ r.username if r else 'Open position' }}</strong><div class="podium-values"><div><small>WEIGHTED WAGER</small><strong data-wager>{{ r.wager if r else '$0.00' }}</strong></div><div><small>PRIZE</small><strong class="accent" data-prize>{{ money(data.site.prizes[n|string]) }}</strong></div></div></article>{% endfor %}</div>
<div class="panel public-table table-scroll" tabindex="0" role="region" aria-label="Leaderboard places four through fifteen"><table><thead><tr><th>Place</th><th>Player</th><th class="number">Weighted wager</th><th class="number">Prize</th></tr></thead><tbody>{% for n in range(4,16) %}{% set r=data.rows|selectattr('rank','equalto',n)|first %}<tr data-rank="{{ n }}"><td class="rank">{{ '%02d'|format(n) }}</td><td><strong data-name>{{ r.username if r else 'Open position' }}</strong></td><td class="number" data-wager>{{ r.wager if r else '$0.00' }}</td><td class="number accent" data-prize>{{ money(data.site.prizes[n|string]) }}</td></tr>{% endfor %}</tbody></table></div>
<div class="leaderboard-foot"><span>Usernames protected · weighted affiliate data</span><span>Automatic updates every 60 seconds</span></div>
<details class="panel explanation"><summary>How weighted wagers are counted <span aria-hidden="true">+</span></summary><div class="weighting-grid">{% for rule in weighting %}<div><strong>{{ rule.range }}</strong><p>{{ rule.counts }}</p></div>{% endfor %}</div><p class="muted small">Rankings cover the saved race window. Results and prizes may be reviewed or adjusted. Independently operated; not affiliated with Shuffle.com.</p></details>
<noscript><p class="notice">Live screen updates require JavaScript. Reload to see the latest saved results.</p></noscript>
</section></main>
{% endblock %}
```

## templates/login.html

```html
{% extends 'base.html' %}{% block title %}Sign in · RedHunllef{% endblock %}
{% block navigation %}<a href="/">Back to the race ↗</a>{% endblock %}
{% block content %}<main id="main" class="shell login-wrap"><section class="panel login-panel"><div class="eyebrow"><span class="dot"></span> YOUR RACE. YOUR CONTROL.</div><h1>Welcome back<span class="accent">.</span></h1><p class="muted">Sign in to manage the race and your community.</p>
{% if error %}<p class="notice warning" role="alert">{{ error }}</p>{% endif %}
<form action="{{ url_for('login') }}" method="post" class="stack"><input type="hidden" name="csrf" value="{{ csrf() }}"><div class="field"><label for="username">Username</label><input id="username" name="username" autocomplete="username" required autofocus maxlength="64"></div><div class="field"><label for="password">Password</label><input id="password" name="password" type="password" autocomplete="current-password" required maxlength="256"></div><button class="button primary" type="submit">Sign in <span aria-hidden="true">→</span></button></form><p class="muted small">Administration only. Public visitors do not need an account.</p><span class="release">{{ release }}</span></section></main>{% endblock %}
{% block footer %}Private administration{% endblock %}
```

## templates/macros.html

```html
{% macro form_fields(action, tab, revision=0) -%}
<input type="hidden" name="csrf" value="{{ csrf() }}"><input type="hidden" name="action" value="{{ action }}"><input type="hidden" name="tab" value="{{ tab }}"><input type="hidden" name="revision" value="{{ revision }}">
{%- endmacro %}
{% macro field(key, label, value='', type='text', help='', error='', required=true, prefix='') -%}
<div class="field"><label for="f-{{ prefix }}{{ key }}">{{ label }}</label>{% if type == 'textarea' %}<textarea id="f-{{ prefix }}{{ key }}" name="{{ key }}" rows="3" {% if required %}required{% endif %} aria-describedby="help-{{ prefix }}{{ key }}">{{ value }}</textarea>{% else %}<input id="f-{{ prefix }}{{ key }}" name="{{ key }}" type="{{ type }}" {% if type=='password' %}autocomplete="{{ 'current-password' if key=='current_password' else 'new-password' }}"{% endif %} value="{{ value }}" {% if required %}required{% endif %} aria-describedby="help-{{ prefix }}{{ key }}" {% if error %}aria-invalid="true"{% endif %}>{% endif %}<small id="help-{{ prefix }}{{ key }}" class="{{ 'field-error' if error else 'muted' }}">{{ error or help }}</small></div>
{%- endmacro %}
{% macro player_rows(rows, tab='players') -%}
{% for row in rows %}<tr data-player="{{ row.username }}"><td class="rank">{{ '%02d'|format(row.rank) if row.rank else '—' }}</td><td><div class="name-cell"><strong>{{ row.username }}</strong><button type="button" class="copy-button js-only" data-copy="{{ row.username }}" aria-label="Copy {{ row.username }}">⧉</button></div>{% if row.source == 'override' %}<span class="tag">Adjusted</span>{% endif %}</td><td class="number accent">{{ row.wager }}</td><td class="number">{{ row.original_weighted_str }}</td><td class="number">{{ row.raw_wager_str }}</td><td><a class="text-link" href="{{ url_for('login',tab='players',edit=row.username) }}#override">Edit</a></td></tr>{% else %}<tr><td colspan="6" class="empty">No matching qualifying wagers. Check the race dates and connection status.</td></tr>{% endfor %}
{%- endmacro %}
```

## templates/recovery_panel.html

```html
<section class="panel form-panel" id="recovery"><p class="eyebrow">KEEP YOUR COMMUNITY'S PROGRESS</p><h2>Private recovery checkpoint</h2>
<div class="checkpoint-status"><strong id="checkpointLabel">{{ data.checkpoint.label }}</strong><p id="checkpointDetails">{{ data.checkpoint.details }}</p><small id="checkpointTime">{{ 'Last export generated: ' ~ fmt_et(data.checkpoint.generated_at) if data.checkpoint.generated_at else 'No export generated yet.' }}</small></div>
<p class="muted">Includes administrator accounts, password hashes, the signing key, race settings, saved standings, boss progress, and the uploaded boss avatar. Keep this file private.</p>
<a class="button primary" href="/admin/recovery-backup" data-recovery-download>↓ Download private recovery file</a>
<p class="small muted">“Generated” means the server prepared a download. It does not confirm that you saved it elsewhere. On App Platform, add the latest file as <code>private/recovery.seed.json</code> to your private repository before redeploying. A new instance imports it automatically; existing saved state always wins. Local copies alone do not survive a container replacement.</p>
<details class="nested" {% if recovery_review %}open{% endif %}><summary>Check a recovery file before restoring <span aria-hidden="true">+</span></summary>
<form method="post" action="/admin/recovery-preview" enctype="multipart/form-data" class="filter-bar"><input type="hidden" name="csrf" value="{{ csrf() }}"><div class="field grow"><label for="recoveryFile">Private recovery JSON</label><input id="recoveryFile" name="recovery" type="file" accept=".json,application/json" required></div><button type="submit" class="button">Review recovery file</button></form>
{% if recovery_review %}<div class="recovery-review"><h3>Validated recovery file</h3><dl><dt>Race dates</dt><dd>{{ recovery_review.start }} → {{ recovery_review.end }}</dd><dt>Accounts</dt><dd>{{ recovery_review.accounts }} administrators</dd><dt>Race data</dt><dd>{{ recovery_review.rows }} saved places · {{ recovery_review.overrides }} overrides · {{ recovery_review.history }} archived races</dd><dt>Community boss</dt><dd>{% if recovery_review.game %}{{ '{:,}'.format(recovery_review.game.hp) }} / {{ '{:,}'.format(recovery_review.game.max_hp) }} HP · {{ recovery_review.game.raiders }} raiders · {{ recovery_review.game.attacks }} hits{% else %}No boss record; a fresh raid will be created on a new instance.{% endif %}</dd><dt>Boss avatar</dt><dd>{{ 'Custom image included' if recovery_review.avatar else 'Original logo' }}</dd></dl><p class="small muted">This review changes nothing. To restore on a fresh deployment, place this file in <code>private/recovery.seed.json</code>. Use the separate race-backup restore form for replacing only a live race.</p></div>{% endif %}
</details></section>
```

## tests/package.json

```json
{
  "name": "redhunllef-interface-tests",
  "private": true,
  "scripts": {"test": "node --test test_*.cjs"},
  "devDependencies": {"jsdom": "26.1.0"}
}
```

## tests/render_fixtures.py

```python
"""Render real templates against synthetic data for the optional DOM test suite."""
import json
import os
from pathlib import Path
import sys
import tempfile
import time
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from wager_backend import create_app
from race import calculate, empty, normalize


def render(destination):
    destination.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory() as directory, patch.dict(os.environ, {
        "APP_ENV": "test", "DATABASE_URL": "", "ADMIN_BOOTSTRAP_PASS": "fixture-password-only",
        "SUPERADMIN_USER": "gingrsnaps", "SECRET_KEY": "", "ADMIN_STORE_PATH": directory + "/none.json",
        "ADMIN_SEED_PATH": directory + "/none-seed.json", "LOCAL_DATABASE_PATH": directory + "/test.sqlite3",
        "SETTINGS_PATH": directory + "/none-settings.json",
    }):
        app = create_app(Path(directory), testing=True)
        runtime = app.extensions["runtime"]
        try:
            now = int(time.time())
            admin = runtime.admin
            admin["site_settings"].update(start_time=now-3600, end_time=now+86400)
            admin["overrides"]["ExamplePlayer000"] = "2000"
            source = [{"username": f"ExamplePlayer{i:03}", "weightedWagerAmount": str(1000-i),
                       "wagerAmount": str(3000-i), "campaignCode": "Red"} for i in range(105)]
            source.append({"username": "<img src=x onerror=alert(1)>", "weightedWagerAmount": "99999", "campaignCode": "Red"})
            snapshot = calculate({**empty(admin["site_settings"]), **normalize(source, admin["site_settings"]),
                                  "updated_at": now, "ok": True}, admin, runtime.config)
            runtime.commit(admin, runtime.revision, snapshot=snapshot)
            client = app.test_client()
            opening = client.get('/play/api/state').json
            client.post('/play/api/profile', json={'raid_id':opening['state']['raid_id'], 'username':'FixtureRaider'}, headers={'X-CSRF-Token':opening['csrf']})
            for name, url in {"public": "/", "login": "/admin", "error": "/missing", "play": "/play"}.items():
                (destination/(name+".html")).write_text(client.get(url).text, encoding="utf-8")
            with client.session_transaction() as session:
                session.update(user="gingrsnaps", auth_version=1, csrf="fixture-csrf")
            for tab in ("overview", "race", "players", "boss", "settings"):
                (destination/(tab+".html")).write_text(client.get("/admin?tab="+tab).text, encoding="utf-8")
            (destination/"boss.json").write_text(json.dumps(client.get("/play/api/state").json), encoding="utf-8")
            (destination/"boss-admin.json").write_text(json.dumps(client.get("/admin/boss/status").json), encoding="utf-8")
            public = client.get("/public-state")
            (destination/"public.json").write_text(json.dumps({**public.json, "server_time":float(public.headers["X-Server-Time"])}), encoding="utf-8")
            (destination/"admin.json").write_text(json.dumps(client.get("/admin/status?code_red=1").json), encoding="utf-8")
        finally:
            runtime.store.close()


if __name__ == "__main__":
    render(Path(sys.argv[1]))
```

## tests/test_app.py

```python
"""Real app/storage tests with synthetic provider responses; no live accounts."""
import copy
import io
import json
import os
from pathlib import Path
import re
import socket
import subprocess
import sys
import tempfile
import threading
import time
import unittest
from unittest.mock import patch
from urllib.request import urlopen

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from wager_backend import create_app
from config import Config
from integrations import ProviderError, Providers
from race import aggregate, normalize, phase, rank
from race_support import eastern_epoch, money_input, race_key
from storage import Conflict, Store, StoreError

ROOT = Path(__file__).resolve().parents[1]
PASSWORD = "a-private-test-password"


def player(name="AlphaMember", amount="100", raw="150", campaign="Red"):
    return dict(username=name, weightedWagerAmount=amount, wagerAmount=raw, campaignCode=campaign)


class AppTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.env = patch.dict(os.environ, {"APP_ENV":"test", "DATABASE_URL":"", "ADMIN_BOOTSTRAP_PASS":PASSWORD,
                              "SUPERADMIN_USER":"gingrsnaps", "PORT":"8080"}, clear=True)
        self.env.start(); self.addCleanup(self.env.stop)
        self.app = create_app(self.root, testing=True)
        self.r = self.app.extensions["runtime"]
        self.addCleanup(self.r.store.close)
        self.client = self.app.test_client()
        self.guard = patch("requests.Session.request", side_effect=AssertionError("Unexpected live request"))
        self.guard.start(); self.addCleanup(self.guard.stop)
        with self.client.session_transaction() as s:
            s.update(user="gingrsnaps", auth_version=1, csrf="test-token")

    def schedule(self, start=None, end=None):
        now = int(time.time())
        admin = copy.deepcopy(self.r.admin)
        admin["site_settings"].update(start_time=start or now-3600, end_time=end or now+86400)
        from race import empty
        self.r.commit(admin, self.r.revision, snapshot=empty(admin["site_settings"]))

    def update(self, rows):
        with patch.object(self.r.providers, "shuffle", return_value=rows):
            self.r.check("shuffle")

    def action(self, name, **values):
        if name == 'save_race' and values.get('confirm_race') == 'yes' and 'review_token' not in values:
            preview = self.action(name, **{k:v for k,v in values.items() if k != 'confirm_race'})
            match = re.search('name="review_token" value="([^"]+)"', preview.text)
            if match:
                values['review_token'] = match.group(1)
        return self.client.post("/admin/action", data={"csrf":"test-token", "action":name, "tab":"settings",
                                                       "revision":self.r.revision, **values})

    def form(self):
        from race_support import local_input
        site = copy.deepcopy(self.r.admin["site_settings"])
        return {**site, "start_et":local_input(site["start_time"]), "end_et":local_input(site["end_time"]),
                **{"prize_"+k:v for k,v in site["prizes"].items()}, "tab":"race"}

    def test_native_login_and_all_dashboard_pages(self):
        c=self.app.test_client()
        page=c.get("/admin")
        csrf=re.search('name="csrf" value="([^"]+)"',page.text).group(1)
        response=c.post("/admin",data={"csrf":csrf,"username":"GINGRSNAPS","password":PASSWORD},follow_redirects=True)
        self.assertEqual(response.status_code,200)
        self.assertIn("CONTROL CENTER",response.text)
        for tab in ("overview","race","players","settings"):
            p=c.get('/admin?tab='+tab)
            self.assertEqual(p.status_code,200)
            self.assertIn('aria-label="Administration"',p.text)

    def test_startup_with_windows_default_encoding_preserves_existing_state(self):
        # Use the shipped assets, including Unicode that CP1252 cannot decode.
        # Linux normally hides this Windows startup failure with its UTF-8 locale.
        static = self.root / "static"
        static.mkdir()
        for asset in (ROOT / "static").glob("*"):
            if asset.suffix in {".css", ".js"}:
                (static / asset.name).write_bytes(asset.read_bytes())
        before = self.r.store.admin()
        native_open = Path.open

        def windows_open(path, mode="r", buffering=-1, encoding=None, errors=None, newline=None):
            if "b" not in mode and encoding in (None, "locale"):
                encoding = "cp1252"
            return native_open(path, mode, buffering, encoding, errors, newline)

        with patch.object(Path, "open", windows_open):
            app = create_app(self.root, testing=True)
            try:
                client = app.test_client()
                self.assertEqual(client.get("/healthz").status_code, 200)
                self.assertIn("Sign in", client.get("/admin").text)
                self.assertEqual(app.extensions["runtime"].store.admin(), before)
            finally:
                app.extensions["runtime"].store.close()

    def test_login_csrf_is_bound_to_browser(self):
        a,b=self.app.test_client(),self.app.test_client()
        a.get('/admin');b.get('/admin')
        with a.session_transaction() as s: csrf=s['csrf']
        self.assertEqual(b.post('/admin',data={'csrf':csrf,'username':'gingrsnaps','password':PASSWORD}).status_code,400)

    def test_refresh_queues_background_work_and_populates_both_boards(self):
        self.schedule()
        amount = {"value": "100"}
        headers = {"Accept": "application/json"}

        def wait_for_total(expected):
            deadline = time.monotonic() + 2
            while time.monotonic() < deadline:
                value = self.client.get("/data").json
                if value["rows"] and value["rows"][0]["wager"] == expected:
                    return value
                time.sleep(.01)
            self.fail("Background refresh did not publish the expected leaderboard")

        with patch.object(self.r.providers, "shuffle", side_effect=lambda site: [player(amount=amount["value"])]), \
             patch.object(self.r.providers, "kick", return_value=dict(live=False, channel="redhunllef")):
            self.r.start()
            try:
                wait_for_total("$100.00")
                revision = self.r.revision
                amount["value"] = "250"
                response = self.client.post("/admin/action", headers=headers,
                    data={"csrf": "test-token", "action": "refresh", "service": "shuffle"})
                self.assertEqual(response.status_code, 202)
                self.assertTrue(response.is_json)
                value = wait_for_total("$250.00")
                self.assertEqual(value["rows"][0]["username"], "Al******")
                admin = self.client.get("/admin/status?tab=players").json
                self.assertEqual(admin["participants"][0]["username"], "AlphaMember")
                self.assertEqual(admin["participants"][0]["wager"], "$250.00")
                self.assertEqual(self.r.revision, revision)
            finally:
                self.r.stop()

    def test_refresh_invalid_csrf_returns_specific_json_without_queueing(self):
        response = self.client.post("/admin/action", headers={"Accept": "application/json"},
                                    data={"action": "refresh", "csrf": "expired"})
        self.assertEqual(response.status_code, 400)
        self.assertTrue(response.is_json)
        self.assertIn("form expired", response.json["error"])
        self.assertFalse(any(event.is_set() for event in self.r.events.values()))

    def test_refresh_expired_login_returns_json_and_does_not_queue(self):
        client = self.app.test_client()
        response = client.post("/admin/action", headers={"Accept": "application/json"},
                               data={"action": "refresh", "csrf": "test-token"})
        self.assertEqual(response.status_code, 401)
        self.assertTrue(response.is_json)
        self.assertFalse(any(event.is_set() for event in self.r.events.values()))

    def test_fetch_http_errors_are_json_and_native_errors_remain_html(self):
        headers = {"Accept": "application/json"}
        responses = [
            (self.client.post("/[object HTMLInputElement]", headers=headers), 404),
            (self.client.get("/admin/action", headers=headers), 405),
            (self.client.post("/admin/action", headers=headers,
                 data={"csrf": "test-token", "action": "refresh", "service": "invalid"}), 400),
        ]
        for response, status in responses:
            self.assertEqual(response.status_code, status)
            self.assertTrue(response.is_json)
            self.assertEqual(response.json["status"], status)
            self.assertIn("error", response.json)
        native = self.client.get("/missing")
        self.assertEqual(native.status_code, 404)
        self.assertEqual(native.mimetype, "text/html")

    def test_refresh_storage_failure_is_json(self):
        with patch.object(self.r, "sync", side_effect=StoreError("Database temporarily unreachable")):
            response = self.client.post("/admin/action", headers={"Accept": "application/json"},
                data={"csrf": "test-token", "action": "refresh"})
        self.assertEqual(response.status_code, 503)
        self.assertEqual(response.json["error"], "Database temporarily unreachable")

    def test_refresh_unexpected_failure_has_safe_json_error(self):
        self.app.config["PROPAGATE_EXCEPTIONS"] = False
        with patch.object(self.r, "request_refresh", side_effect=RuntimeError("private-error-detail")):
            response = self.client.post("/admin/action", headers={"Accept": "application/json"},
                data={"csrf": "test-token", "action": "refresh"})
        self.assertEqual(response.status_code, 500)
        self.assertTrue(response.is_json)
        self.assertNotIn("private-error-detail", response.text)

    def test_empty_leaderboards_explain_waiting_empty_filtered_and_failed_sources(self):
        self.schedule()
        self.assertIn("first successful update", self.client.get("/data").json["leaderboard_message"])
        self.update([])
        self.assertIn("returned no wagers", self.client.get("/data").json["leaderboard_message"])
        self.update([player(campaign="Other")])
        self.assertIn("campaign filter", self.client.get("/data").json["leaderboard_message"])
        self.update([player(amount="0")])
        self.assertIn("$0.01", self.client.get("/data").json["leaderboard_message"])
        with patch.object(self.r.providers, "shuffle", side_effect=ProviderError("Fixture source timeout")):
            self.r.check("shuffle")
        self.assertIn("delayed", self.client.get("/data").json["leaderboard_message"])
        self.update([player()])
        self.assertEqual(self.client.get("/data").json["leaderboard_message"], "")
        diagnostic = self.client.get("/admin/diagnostics").json["diagnostics"]
        self.assertEqual(diagnostic["campaign_filter"], "Red")
        self.assertEqual(diagnostic["qualifying_players"], 1)

    def test_login_rate_limit(self):
        c=self.app.test_client();c.get('/admin')
        with c.session_transaction() as s: csrf=s['csrf']
        for _ in range(5):
            self.assertEqual(c.post('/admin',data={'csrf':csrf,'username':'x','password':'wrong'}).status_code,401)
        self.assertEqual(c.post('/admin',data={'csrf':csrf,'username':'x','password':'wrong'}).status_code,429)

    def test_protected_endpoints_never_disclose_names(self):
        self.schedule();self.update([player()])
        public=self.app.test_client()
        for path in ('/admin/status','/admin/export.csv','/admin/diagnostics','/admin/backup'):
            self.assertEqual(public.get(path).status_code,401)
        self.assertNotIn('AlphaMember',public.get('/data').text)
        self.assertIn('Al******',public.get('/data').text)
        for path in ('/private/settings.json','/private/admin_store.seed.json','/data/redhunllef.sqlite3','/data/state.json','/data/state.json.lock'):
            self.assertEqual(public.get(path).status_code,404)

    def test_mixed_shuffle_response_updates_and_warns(self):
        self.schedule();self.update([player(amount='100')]);before=self.r.revision
        self.update([player(amount='200'),player('Missing',None),None,player('BetaMember','150',campaign=' Red ')])
        data=self.client.get('/data').json
        self.assertEqual(data['rows'][0]['wager'],'$200.00')
        self.assertEqual(len(data['rows']),2)
        self.assertEqual(data['freshness']['state'],'partial')
        self.assertEqual(self.r.revision,before,'A provider update must not rewrite admin state')
        admin=self.client.get('/admin/status?code_red=1').json
        self.assertEqual(len(admin['red']),2)
        self.assertIn('AlphaMember',str(admin['participants']))

    def test_invalid_response_retains_saved_results(self):
        self.schedule();self.update([player()]);stamp=self.r.shuffle['updated_at']
        self.update([None,player(amount='NaN')])
        self.assertEqual(self.r.shuffle['rows'][0]['wager'],'$100.00')
        self.assertEqual(self.r.shuffle['updated_at'],stamp)
        self.assertEqual(self.client.get('/data').json['freshness']['state'],'delayed')

    def test_valid_empty_response_clears_old_rows(self):
        self.schedule();self.update([player()]);self.update([])
        self.assertEqual(self.r.shuffle['rows'],[])
        self.assertEqual(self.client.get('/data').json['freshness']['state'],'current')

    def test_clean_response_clears_warning(self):
        self.schedule();self.update([player(),None]);self.update([player()])
        self.assertEqual(self.r.shuffle['warning'],'')

    def test_missing_raw_does_not_freeze_weighted_wager(self):
        self.schedule();self.update([player(amount='200',raw='bad')])
        row=self.r.shuffle['rows'][0]
        self.assertEqual(row['wager'],'$200.00');self.assertIsNone(row['raw_wager'])

    def test_future_race_never_calls_shuffle(self):
        now=int(time.time());self.schedule(now+3600,now+7200)
        with patch.object(self.r.providers,'shuffle') as mock:
            self.r.check('shuffle');mock.assert_not_called()
        self.assertEqual(self.r.public()['site']['race_state'],'upcoming')

    def test_kick_failure_does_not_publish_offline(self):
        with patch.object(self.r.providers,'kick',return_value={'live':True,'channel':'redhunllef','title':'Live fixture','viewers':42}):self.r.check('kick')
        with patch.object(self.r.providers,'kick',side_effect=ProviderError('Kick timed out')):self.r.check('kick')
        self.assertTrue(self.r.kick['live']);self.assertFalse(self.r.public()['stream']['available'])

    def test_override_retains_raw_and_original_and_can_be_removed(self):
        self.schedule();self.update([player()])
        self.assertEqual(self.action('override',username='AlphaMember',amount='250').status_code,303)
        row=self.r.shuffle['rows'][0]
        self.assertEqual((row['weighted_wager'],row['original_weighted_wager'],row['raw_wager']),('250','100','150'))
        self.action('override',username='AlphaMember',amount='')
        self.assertEqual(self.r.shuffle['rows'][0]['wager'],'$100.00')

    def test_zero_override_stays_manageable(self):
        self.schedule();self.update([player()]);self.action('override',username='AlphaMember',amount='0')
        self.assertEqual(self.r.shuffle['rows'],[])
        self.assertEqual(self.r.shuffle['edits'][0]['username'],'AlphaMember')

    def test_race_change_requires_confirmation_and_archives(self):
        self.schedule();self.update([player()]);old=copy.deepcopy(self.r.admin)
        form={**self.form(),'start_et':'2027-01-01T18:00','end_et':'2027-01-08T18:00'}
        response=self.action('save_race',**form)
        self.assertEqual(response.status_code,200);self.assertEqual(self.r.admin,old)
        self.assertEqual(self.action('save_race',confirm_race='yes',**form).status_code,303)
        self.assertEqual(len(self.r.admin['race_history']),1)
        self.assertEqual(self.r.admin['race_history'][0]['leaderboard_snapshots']['last_top15'][0]['username'],'AlphaMember')
        self.assertEqual(self.r.shuffle['rows'],[])
        self.assertEqual(self.r.admin['users'],old['users'])

    def test_invalid_settings_preserve_draft(self):
        self.schedule();before=copy.deepcopy(self.r.admin)
        response=self.action('save_race',**{**self.form(),'race_title':'Unsaved draft','prize_2':'bad'})
        self.assertEqual(response.status_code,422);self.assertIn('Unsaved draft',response.text)
        self.assertEqual(self.r.admin,before)

    def test_stale_revision_rejected(self):
        self.assertEqual(self.action('override',revision=0,username='User',amount='100').status_code,409)

    def test_case_insensitive_duplicate_accounts(self):
        self.assertEqual(self.action('add_account',username='GINGRSNAPS',new_password=PASSWORD,confirm_password=PASSWORD).status_code,422)

    def test_removed_account_loses_access(self):
        self.action('add_account',username='another_admin',new_password=PASSWORD,confirm_password=PASSWORD)
        other=self.app.test_client()
        with other.session_transaction() as s:s.update(user='another_admin',auth_version=1,csrf='test-token')
        self.assertEqual(other.get('/admin/status').status_code,200)
        self.action('remove_account',username='another_admin')
        self.assertEqual(other.get('/admin/status').status_code,401)

    def test_superadmin_cannot_be_removed(self):
        self.assertEqual(self.action('remove_account',username='GINGRSNAPS').status_code,422)

    def test_non_superadmin_cannot_manage_accounts(self):
        self.action('add_account',username='another_admin',new_password=PASSWORD,confirm_password=PASSWORD)
        with self.client.session_transaction() as s:s.update(user='another_admin',auth_version=1)
        self.assertEqual(self.action('remove_account',username='gingrsnaps').status_code,403)

    def test_password_change_revokes_other_sessions(self):
        other=self.app.test_client()
        with other.session_transaction() as s:s.update(user='gingrsnaps',auth_version=1)
        self.assertEqual(self.action('password',current_password=PASSWORD,new_password=PASSWORD+'2',confirm_password=PASSWORD+'2').status_code,303)
        self.assertEqual(other.get('/admin/status').status_code,401)
        self.assertEqual(self.client.get('/admin/status').status_code,200)

    def test_safe_backup_and_redacted_diagnostics(self):
        self.schedule();self.update([player()])
        backup=self.client.get('/admin/backup').json
        self.assertNotIn('users',backup);self.assertNotIn('secret_key',backup)
        report=self.client.get('/admin/diagnostics').text
        self.assertNotIn('AlphaMember',report);self.assertNotIn('pw_hash',report)

    def test_restore_previews_then_preserves_accounts(self):
        self.schedule();self.update([player()]);saved=self.client.get('/admin/backup').json
        self.action('override',username='AlphaMember',amount='999')
        response=self.action('preview_restore',backup=(io.BytesIO(json.dumps(saved).encode()),'backup.json'))
        self.assertEqual(response.status_code,200);self.assertEqual(self.r.shuffle['rows'][0]['wager'],'$999.00')
        identifier=re.search('name="restore_token" value="([^"]+)"',response.text).group(1)
        users=copy.deepcopy(self.r.admin['users'])
        self.assertEqual(self.action('restore',restore_token=identifier).status_code,303)
        self.assertEqual(self.r.shuffle['rows'][0]['wager'],'$100.00');self.assertEqual(self.r.admin['users'],users)
        with self.r.store.connection() as c:
            self.assertGreaterEqual(len(c['recoveries']),2)

    def test_bad_restore_does_not_mutate_state(self):
        self.schedule();saved=self.client.get('/admin/backup').json;saved['site_settings']['prizes']['1']='NaN'
        before=copy.deepcopy(self.r.admin)
        response=self.action('preview_restore',backup=(io.BytesIO(json.dumps(saved).encode()),'backup.json'))
        self.assertEqual(response.status_code,422);self.assertEqual(self.r.admin,before)

    def test_code_red_first_100_excludes_other_and_unknown_campaigns(self):
        self.schedule();self.update([player('User'+str(n),str(1000-n)) for n in range(130)]+[player('Unknown','100',campaign=None),player('Other','100',campaign='Other')])
        self.assertEqual(len(self.r.shuffle['red']),100);self.assertEqual(self.r.shuffle['red_total'],130)
        self.assertEqual(self.r.shuffle['missing_campaign'],1)

    def test_csv_filter_preserves_rank_and_escapes_formula(self):
        self.schedule();self.update([player('AlphaMember','200'),player('=cmd','100')])
        value=self.client.get('/admin/export.csv?q=%3Dcmd').text
        self.assertIn("'=cmd",value);self.assertIn('2,',value);self.assertNotIn('AlphaMember',value)

    def test_existing_store_wins_on_restart(self):
        self.action('add_account',username='new_admin',new_password=PASSWORD,confirm_password=PASSWORD)
        again=Store(self.app.extensions['settings'])
        try:self.assertIn('new_admin',again.admin()[1]['users'])
        finally:again.close()

    def test_seed_import_preserves_original_bytes_and_unknown_fields(self):
        target=self.root/'other';target.mkdir()
        value=copy.deepcopy(self.r.admin);value['unknown_legacy_field']={'keep':'this'}
        raw=json.dumps(value,indent=3).encode();(target/'admin_store.json').write_bytes(raw)
        store=Store(Config(target))
        try:
            self.assertEqual(store.admin()[1]['users'],value['users'])
            self.assertEqual(store.admin()[1]['unknown_legacy_field'],value['unknown_legacy_field'])
            self.assertEqual((target/'admin_store.json').read_bytes(),raw)
        finally:store.close()

    def test_corrupt_seed_is_never_replaced(self):
        target=self.root/'bad';target.mkdir();(target/'admin_store.json').write_text('{broken',encoding='utf-8')
        with self.assertRaises(RuntimeError):Store(Config(target))
        self.assertEqual((target/'admin_store.json').read_text(encoding='utf-8'),'{broken')

    def test_production_starts_locally_without_database_configuration(self):
        # Reproduce the App Platform environment that used to stop startup.
        with patch.dict(sys.modules,{'psycopg':None}), patch.dict(os.environ,{'APP_ENV':'production','DATABASE_URL':'${race-db.DATABASE_URL}',
                                     'DATABASE_SSLMODE':'unused-invalid-value'}):
            app=create_app(self.root,testing=True)
            runtime=app.extensions['runtime']
            try:
                self.assertFalse(runtime.store.pg)
                self.assertTrue(app.extensions['settings'].production)
                client=app.test_client()
                response=client.get('/admin',base_url='https://example.test')
                self.assertIn('Secure',response.headers['Set-Cookie'])
                csrf=re.search('name="csrf" value="([^"]+)"',response.text).group(1)
                response=client.post('/admin',base_url='https://example.test',data={'csrf':csrf,'username':'gingrsnaps','password':PASSWORD},follow_redirects=True)
                self.assertEqual(response.status_code,200)
                self.assertIn('Local storage is active',response.text)
                self.assertEqual(client.get('/admin/status',base_url='https://example.test').status_code,200)
                self.assertEqual(runtime.admin['users'],self.r.admin['users'])
            finally:runtime.store.close()

    def test_private_recovery_restores_accounts_and_dates_on_a_fresh_instance(self):
        self.schedule();self.update([player()])
        self.action('add_account',username='retained_admin',new_password=PASSWORD+'2',confirm_password=PASSWORD+'2')
        self.action('password',current_password=PASSWORD,new_password=PASSWORD+'3',confirm_password=PASSWORD+'3')
        self.action('override',username='AlphaMember',amount='321')
        response=self.client.get('/admin/recovery-backup')
        self.assertEqual(response.status_code,200)
        self.assertIn('no-store',response.headers['Cache-Control'])
        self.assertIn('recovery.seed.json',response.headers['Content-Disposition'])
        self.assertEqual(response.json['users'],self.r.admin['users'])
        target=self.root/'fresh';(target/'private').mkdir(parents=True)
        (target/'private/recovery.seed.json').write_bytes(response.data)
        # Newest recovery must win over the original legacy seed on a new disk.
        original=copy.deepcopy(response.json);original['site_settings']['race_title']='Old seed title'
        (target/'admin_store.json').write_text(json.dumps(original),encoding='utf-8')
        restored=create_app(target,testing=True)
        runtime=restored.extensions['runtime']
        try:
            for key in ['users','site_settings','overrides','race_history','secret_key']:
                self.assertEqual(runtime.admin[key],self.r.admin[key])
            self.assertEqual(runtime.shuffle['rows'][0]['wager'],'$321.00')
            client=restored.test_client();page=client.get('/admin')
            csrf=re.search('name="csrf" value="([^"]+)"',page.text).group(1)
            self.assertEqual(client.post('/admin',data={'csrf':csrf,'username':'gingrsnaps','password':PASSWORD+'3'}).status_code,303)
            self.assertEqual((target/'private/recovery.seed.json').read_bytes(),response.data)
            candidate=copy.deepcopy(runtime.admin);candidate['site_settings']['race_title']='Newer local state'
            runtime.commit(candidate,runtime.revision)
        finally:runtime.store.close()
        reopened=Store(Config(target))
        try:self.assertEqual(reopened.admin()[1]['site_settings']['race_title'],'Newer local state')
        finally:reopened.close()

    def test_private_recovery_requires_superadmin_and_is_never_public(self):
        self.assertEqual(self.app.test_client().get('/admin/recovery-backup').status_code,401)
        self.action('add_account',username='another_admin',new_password=PASSWORD,confirm_password=PASSWORD)
        with self.client.session_transaction() as s:s.update(user='another_admin',auth_version=1)
        response=self.client.get('/admin/recovery-backup')
        self.assertEqual(response.status_code,403)
        self.assertNotIn('pw_hash',response.text)
        self.assertNotIn('href="/admin/recovery-backup"',self.client.get('/admin?tab=settings').text)
        self.assertNotIn('pw_hash',self.client.get('/data').text)

    def test_invalid_recovery_file_stops_import_without_resetting_accounts(self):
        target=self.root/'invalid-recovery';(target/'private').mkdir(parents=True)
        seed=target/'private/recovery.seed.json';seed.write_text('{broken',encoding='utf-8')
        (target/'private/admin_store.seed.json').write_text(json.dumps(self.r.admin),encoding='utf-8')
        with self.assertRaises(RuntimeError):Store(Config(target))
        self.assertEqual(seed.read_text(encoding='utf-8'),'{broken')

    def test_removed_database_configuration_cannot_require_a_service(self):
        with patch.dict(os.environ, {'STORAGE_MODE':'postgres','DATABASE_URL':'postgresql://unused'}):
            config = Config(self.root)
            self.assertEqual(config.db_url, '')
            self.assertEqual(config.state_path, self.root/'data/state.json')
            store = Store(config)
            self.assertEqual(store.admin(), self.r.store.admin())
            self.assertFalse(store.pg)

    def test_shuffle_and_kick_workers_do_not_block_each_other(self):
        self.schedule();entered,release,kick=threading.Event(),threading.Event(),threading.Event()
        def slow(site):entered.set();release.wait(3);return [player()]
        def fast(site):kick.set();return dict(live=False,channel='redhunllef')
        with patch.object(self.r.providers,'shuffle',side_effect=slow),patch.object(self.r.providers,'kick',side_effect=fast):
            self.r.start()
            try:
                self.assertTrue(entered.wait(2));self.assertTrue(kick.wait(2));self.assertEqual(self.client.get('/data').status_code,200)
            finally:release.set();self.r.stop()

    def test_no_stale_publication_after_settings_change(self):
        self.schedule()
        def changing(site):
            candidate=copy.deepcopy(self.r.admin);candidate['site_settings']['race_title']='Changed during fetch'
            self.r.commit(candidate,self.r.revision)
            return [player()]
        with patch.object(self.r.providers,'shuffle',side_effect=changing):self.r.check('shuffle')
        self.assertEqual(self.r.shuffle['rows'],[]);self.assertTrue(self.r.events['shuffle'].is_set())

    def test_failed_old_request_does_not_poison_new_race_or_delay_its_check(self):
        self.schedule()
        before = self.r.revision
        def old_request(site):
            candidate = copy.deepcopy(self.r.admin)
            candidate['site_settings']['start_time'] -= 86400
            from race import empty
            self.r.commit(candidate, before, snapshot=empty(candidate['site_settings']))
            self.r.request_refresh('shuffle')
            raise ProviderError('The old date range was rejected', status=400)
        with patch.object(self.r.providers, 'shuffle', side_effect=old_request):
            delay = self.r.check('shuffle')
        self.assertEqual(self.r.shuffle['error'], '')
        self.assertEqual(delay, 0)
        self.assertTrue(self.r.events['shuffle'].is_set())
        self.update([player(amount='350')])
        self.assertEqual(self.client.get('/data').json['rows'][0]['wager'], '$350.00')

    def test_manual_request_during_a_check_queues_one_followup(self):
        self.r.jobs['shuffle']['state'] = 'checking'
        self.r.request_refresh('shuffle')
        self.r.request_refresh('shuffle')
        self.assertTrue(self.r.events['shuffle'].is_set())
        self.assertEqual(self.r.jobs['shuffle']['state'], 'checking')

    def test_bottom_confirmation_button_actually_publishes_the_new_dates(self):
        self.schedule()
        form = {**self.form(), 'start_et':'2026-09-01T18:00', 'end_et':'2026-09-08T18:00'}
        preview = self.action('save_race', **form)
        # Submit the same visible bottom button a person uses after reviewing.
        bottom = preview.text.split('class="save-bar"', 1)[1]
        submitter = re.search(r'<button\b[^>]*type="submit"[^>]*>', bottom).group(0)
        attributes = dict(re.findall(r'([\w-]+)="([^"]*)"', submitter))
        extra = {attributes['name']:attributes.get('value', '')} if 'name' in attributes else {}
        response = self.action('save_race', **form, **extra)
        self.assertEqual(response.status_code, 303)
        self.assertEqual(self.r.admin['site_settings']['start_time'], eastern_epoch(form['start_et']))

    def test_date_publication_and_automatic_refresh_through_real_http_transport(self):
        """Exercise requests/JSON/parser/worker publication against a local fixture.

        The scheduling interval is shortened only inside this isolated test.
        Real Shuffle credentials and services are never contacted.
        """
        from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
        from urllib.parse import parse_qs, urlsplit
        from race_support import local_input
        import requests
        self.schedule()
        old_start = self.r.admin['site_settings']['start_time']
        entered, release = threading.Event(), threading.Event()
        fixture = {'amount':'200', 'windows':[]}

        class Upstream(BaseHTTPRequestHandler):
            def log_message(self, *_):
                pass
            def do_GET(self):
                query = parse_qs(urlsplit(self.path).query)
                window = (int(query['startTime'][0]), int(query['endTime'][0]))
                fixture['windows'].append(window)
                if window[0] == old_start:
                    entered.set()
                    release.wait(3)
                    status, payload = 400, {'error':'old range'}
                else:
                    status, payload = 200, {'data':[player(amount=fixture['amount'])]}
                body = json.dumps(payload).encode('utf-8')
                self.send_response(status)
                self.send_header('Content-Type', 'application/json')
                self.send_header('Content-Length', str(len(body)))
                self.end_headers()
                self.wfile.write(body)

        server = ThreadingHTTPServer(('127.0.0.1', 0), Upstream)
        thread = threading.Thread(target=server.serve_forever, daemon=True)
        thread.start()
        self.guard.stop()
        native_request = requests.Session.request
        self.r.config.credentials['shuffle_api_key'] = 'fixture-key'

        def route(session, method, url, **kwargs):
            parsed = urlsplit(url)
            self.assertEqual(parsed.netloc, 'affiliate.shuffle.com')
            return native_request(session, method,
                f'http://127.0.0.1:{server.server_port}'+parsed.path, **kwargs)

        def wait_for_wager(amount):
            deadline = time.monotonic()+3
            while time.monotonic() < deadline:
                value = self.client.get('/data').json
                if value['rows'] and value['rows'][0]['wager'] == amount:
                    return
                time.sleep(.01)
            self.fail('Latest source value was not automatically published')

        try:
            with patch('requests.Session.request', new=route), patch('runtime.INTERVAL', .2), \
                 patch.object(self.r.providers, 'kick', return_value=dict(live=False, channel='redhunllef')):
                self.r.start()
                try:
                    self.assertTrue(entered.wait(2))
                    now = int(time.time())
                    form = {**self.form(), 'start_et':local_input(now-7200), 'end_et':local_input(now+7200)}
                    self.assertEqual(self.action('save_race', **form).status_code, 200)
                    self.assertEqual(self.action('save_race', confirm_race='yes', **form).status_code, 303)
                    release.set()
                    wait_for_wager('$200.00')
                    self.assertEqual(self.r.shuffle['error'], '')
                    self.assertEqual(self.r.jobs['shuffle']['http_status'], 200)
                    self.assertEqual(fixture['windows'][1][0], eastern_epoch(form['start_et']))
                    # No manual request: the next scheduled cycle must publish.
                    fixture['amount'] = '375'
                    wait_for_wager('$375.00')
                    admin = self.client.get('/admin/status?tab=players').json
                    self.assertEqual(admin['participants'][0]['wager'], '$375.00')
                    self.assertEqual(admin['participants'][0]['username'], 'AlphaMember')
                    self.assertGreaterEqual(len(fixture['windows']), 3)
                finally:
                    release.set()
                    self.r.stop()
        finally:
            server.shutdown()
            server.server_close()
            thread.join(timeout=2)

    def test_new_dates_clear_old_soft_retry_but_preserve_provider_rate_limit(self):
        self.schedule()
        job = self.r.jobs['shuffle']
        job.update(checked_scope='previous-race', not_before=time.monotonic()+60, http_status=400, retry_after=0)
        first = self.r.request_refresh('shuffle')
        self.assertEqual(job['not_before'], 0)
        second = self.r.request_refresh('shuffle')
        self.assertEqual(first['requests'], second['requests'], 'Repeated clicks should coalesce')
        deadline = time.monotonic()+120
        job.update(not_before=deadline, http_status=429, retry_after=120)
        self.r.request_refresh('shuffle')
        self.assertEqual(job['not_before'], deadline)

    def test_superseded_rate_limit_still_delays_new_provider_requests(self):
        self.schedule()
        def limited(site):
            candidate = copy.deepcopy(self.r.admin)
            candidate['site_settings']['start_time'] -= 86400
            from race import empty
            self.r.commit(candidate, self.r.revision, snapshot=empty(candidate['site_settings']))
            raise ProviderError('Provider rate limit', status=429, retry_after=120)
        with patch.object(self.r.providers, 'shuffle', side_effect=limited):
            delay = self.r.check('shuffle')
        self.assertEqual(delay, 120)
        self.assertEqual(self.r.shuffle['error'], '')
        self.assertTrue(self.r.events['shuffle'].is_set())

    def test_provider_envelopes_and_range_never_use_lifetime_fallback(self):
        self.schedule();providers=self.r.providers;providers.config.credentials['shuffle_api_key']='fake-key'
        for key in ('data','results','leaderboard','users','items'):
            with patch.object(providers,'request',return_value={'data':None,key:[player()]}) as mock:
                self.assertEqual(len(providers.shuffle(self.r.admin['site_settings'])),1)
                self.assertIn('startTime',mock.call_args.kwargs['params'])
        with patch.object(providers,'request',side_effect=ProviderError('Bad race',status=400)) as mock:
            with self.assertRaises(ProviderError):providers.shuffle(self.r.admin['site_settings'])
            self.assertEqual(mock.call_count,1)

    def test_kick_reauthenticates_once_after_401(self):
        providers=self.r.providers;providers.config.credentials.update(kick_client_id='fake',kick_client_secret='fake')
        channel={'data':[{'slug':'redhunllef','stream':{'is_live':True,'viewer_count':42},'stream_title':'Fixture'}]}
        with patch.object(providers,'request',side_effect=[{'access_token':'first'},ProviderError('expired',status=401),{'access_token':'second'},channel]) as mock:
            value=providers.kick(self.r.admin['site_settings'])
            self.assertEqual(mock.call_count,4);self.assertTrue(value['live']);self.assertEqual(value['viewers'],42)

    def test_sole_launch_command_serves_actual_http(self):
        with socket.socket() as sock:sock.bind(('127.0.0.1',0));port=sock.getsockname()[1]
        env={**os.environ,'PORT':str(port),'APP_ENV':'production','STORAGE_MODE':'local',
             'DATABASE_URL':'${race-db.DATABASE_URL}','LOCAL_DATABASE_PATH':str(self.root/'cli.sqlite3'),'STATE_FILE':str(self.root/'cli-state.json'),
             'SETTINGS_PATH':str(self.root/'missing-settings.json'),'ADMIN_SEED_PATH':str(self.root/'missing-seed.json'),
             'PYTHONIOENCODING':'utf-8'}
        log=self.root/'startup.log'
        with log.open('w',encoding='utf-8') as stream:
            process=subprocess.Popen([sys.executable,str(ROOT/'wager_backend.py')],env=env,stdout=stream,stderr=stream)
            try:
                for _ in range(60):
                    if process.poll() is not None:self.fail(log.read_text(encoding='utf-8'))
                    try:
                        with urlopen(f'http://127.0.0.1:{port}/healthz',timeout=.3) as response:
                            self.assertTrue(json.load(response)['ok']);break
                    except OSError:time.sleep(.05)
                else:self.fail('Server did not bind its HTTP port: '+log.read_text(encoding='utf-8'))
                with urlopen(f'http://127.0.0.1:{port}/admin',timeout=2) as response:self.assertIn('Sign in',response.read().decode())
            finally:process.terminate();process.wait(timeout=8)
        self.assertIn('listening on 0.0.0.0:',log.read_text(encoding='utf-8'))
        self.assertIn('cadence=60s',log.read_text(encoding='utf-8'))
        self.assertIn('no external database is required',log.read_text(encoding='utf-8'))
        self.assertNotIn('ERROR STARTUP',log.read_text(encoding='utf-8'))


class CalculationTests(unittest.TestCase):
    def test_timezone_boundaries(self):
        for value in ('2026-03-08T02:30','2026-11-01T01:30'):
            with self.assertRaises(ValueError):eastern_epoch(value)
        self.assertEqual(time.gmtime(eastern_epoch('2026-09-21T18:00')).tm_hour,22)

    def test_invalid_money(self):
        for value in ('NaN','-5','1,23','25k'):
            with self.assertRaises(ValueError):money_input(value)

    def test_phase_boundaries(self):
        site={'start_time':100,'end_time':200}
        self.assertEqual([phase(site,x) for x in (99,100,199,200)],['upcoming','active','active','ended'])

    def test_exact_aggregation_and_incomplete_raw_totals(self):
        rows=[dict(username='user',weighted='0.1',raw=None,raw_invalid=True,row_count=1),dict(username='user',weighted='0.2',raw='500',row_count=1)]
        value=aggregate(rows)['user'];self.assertEqual(value['weighted'],'0.3');self.assertIsNone(value['raw'])
        self.assertEqual(aggregate(rows,'max')['user']['weighted'],'0.2')


if __name__=='__main__':unittest.main()
```

## tests/test_boss.py

```python
"""Shared raid, HTTP, fairness, concurrency, and portable recovery regressions."""
import copy
from concurrent.futures import ThreadPoolExecutor
import json
import os
from pathlib import Path
import secrets
import sys
import tempfile
import unittest
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from boss import BossError, CommunityBoss, DAY, DEFAULT_HP, fresh_raid, network_identity, validate_boss
from storage import Store
from wager_backend import create_app


class BossTests(unittest.TestCase):
    def setUp(self):
        temp=tempfile.TemporaryDirectory(); self.addCleanup(temp.cleanup)
        self.root=Path(temp.name)
        env=patch.dict(os.environ, {'APP_ENV':'test','ADMIN_BOOTSTRAP_PASS':'test-only-password'}, clear=True)
        env.start(); self.addCleanup(env.stop)
        self.app=create_app(self.root, testing=True)
        self.r=self.app.extensions['runtime']; self.b=self.app.extensions['boss']
        self.addCleanup(self.r.store.close)
        self.clock=patch('boss.time.time',return_value=1_800_000_000.375)
        self.time=self.clock.start(); self.addCleanup(self.clock.stop)
        self.start=self.time.return_value

    def hit(self,guest='a',ip='192.0.2.1',style=None,request_id=None):
        state=self.b.status(guest,ip)
        return self.b.attack(guest,ip,style or state['weakness'],state['raid_id'],request_id or secrets.token_hex(16))

    def client(self,ip='192.0.2.1'):
        c=self.app.test_client(); c.environ_base['REMOTE_ADDR']=ip
        state=c.get('/play/api/state').json
        return c,state

    def post(self,c,value,**extra):
        state=value['state']
        c.post('/play/api/profile', json={'raid_id':state['raid_id'], 'username':state['you']['name']}, headers={'X-CSRF-Token':value['csrf']})
        return c.post('/play/api/attack',json={'raid_id':state['raid_id'],'request_id':secrets.token_hex(16),'style':state['weakness'],**extra},headers={'X-CSRF-Token':value['csrf']})

    def test_two_players_share_health_and_separate_identity(self):
        a,sa=self.client(); b,sb=self.client('192.0.2.2')
        first=self.post(a,sa); second=self.post(b,sb)
        self.assertEqual(first.status_code,200); self.assertEqual(second.status_code,200)
        current=a.get('/play/api/state').json['state']
        self.assertEqual(current['hp'],DEFAULT_HP-300)
        self.assertEqual(current['raiders'],2)
        self.assertEqual(current['you']['damage'],150)
        self.assertNotEqual(sa['state']['you']['name'],sb['state']['you']['name'])
        self.assertEqual(len(current['recent']),2)
        html=a.get('/play').text
        self.assertIn('id="attackButton"',html)
        self.assertIn('id="bossHealthBar"',html)
        self.assertNotIn('How to play together',html)
        self.assertNotIn('id="howToPlay"',html)
        self.assertNotIn('href="/admin"',a.get('/').text)
        self.assertIn('Join the boss fight',a.get('/').text)

    def test_simultaneous_hits_from_distinct_players_are_atomic(self):
        def attack(i): return self.hit(str(i),f'198.51.100.{i+1}')
        with ThreadPoolExecutor(max_workers=12) as pool:
            hits=list(pool.map(attack,range(40)))
        state=self.b.export()
        self.assertEqual(state['total_attacks'],40)
        self.assertEqual(state['hp'],DEFAULT_HP-sum(r['hit']['damage'] for r in hits))
        validate_boss(state)

    def test_same_identity_simultaneous_tabs_only_one_lands(self):
        def attack(i):
            try: return self.hit('same-browser')['ok']
            except BossError as exc: return exc.code
        with ThreadPoolExecutor(max_workers=10) as pool:
            result=list(pool.map(attack,range(20)))
        self.assertEqual(result.count(True),1)
        self.assertEqual(result.count('cooldown'),19)

    def test_cooldown_fractional_seconds_and_browser_limit_across_ips(self):
        self.hit()
        self.time.return_value=self.start+29.99
        with self.assertRaises(BossError) as blocked:self.hit(ip='192.0.2.2')
        self.assertEqual(blocked.exception.status,429)
        self.time.return_value=self.start+30
        self.assertEqual(self.hit(ip='192.0.2.2')['hit']['damage'],150)
        validate_boss(self.b.export())

    def test_unlimited_hits_and_per_player_cooldown(self):
        for i in range(100):
            self.time.return_value=self.start+i*30
            self.hit()
        self.assertEqual(self.b.status('a','192.0.2.1')['you']['attacks'],100)
        self.assertIsNone(self.b.status('a','192.0.2.1')['you']['remaining'])
        with self.assertRaises(BossError) as blocked:self.hit(guest='a')
        self.assertEqual(blocked.exception.code,'cooldown')
        self.time.return_value += 30
        self.assertEqual(self.hit()['state']['you']['attacks'],101)
        self.time.return_value=int(self.start)+DAY
        self.assertEqual(self.hit()['state']['you']['attacks'],102)

    def test_ipv6_normalization_and_mapped_ipv4(self):
        self.hit(ip='2001:db8::abcd')
        with self.assertRaises(BossError):self.hit(guest='a',ip='2001:db8::eeff')
        self.assertTrue(self.hit(guest='new',ip='2001:db8::eeff')['ok'])
        self.assertEqual(network_identity('::ffff:192.0.2.1'),'192.0.2.1')
        self.assertEqual(self.hit(guest='other',ip='2001:db8:0:1::1')['hit']['damage'],150)

    def test_weakness_bonus_and_tenth_hit_burst(self):
        s=self.b.status('a','192.0.2.1')
        wrong=next(x for x in ('blade','bow','magic') if x!=s['weakness'])
        self.assertEqual(self.hit(style=wrong)['hit']['damage'],100)
        for i in range(1,10):
            self.time.return_value=self.start+i*60
            result=self.hit()
        self.assertEqual(result['hit']['damage'],250)
        self.assertTrue(result['hit']['burst'])
        self.assertEqual(result['state']['you']['burst_in'],10)

    def test_receipt_retry_after_cooldown_and_victory_is_idempotent(self):
        first=self.hit(request_id='test-receipt-001')
        self.time.return_value+=120
        again=self.hit(request_id='test-receipt-001')
        self.assertTrue(again['duplicate']); self.assertEqual(first['hit'],again['hit'])
        self.assertEqual(self.b.export()['total_attacks'],1)
        # A tiny isolated raid verifies final damage clamping and victory receipts.
        value=fresh_raid(health=50)
        with self.r.store.connection(transaction=True) as conn:self.b._write(conn,value,new_raid=True)
        self.b.loaded_at=0
        final=self.hit(request_id='victory-receipt')
        self.assertEqual(final['hit']['damage'],50)
        self.assertEqual(final['state']['hp'],0)
        self.assertTrue(self.hit(request_id='victory-receipt')['duplicate'])
        with self.assertRaises(BossError):self.hit(guest='b',ip='192.0.2.2')
        validate_boss(self.b.export())

    def test_race_settings_and_provider_cache_untouched_by_game(self):
        before=self.r.store.admin(); snapshot=self.r.store.live('shuffle')
        self.hit(); self.b.control('pause',self.b.status()['raid_id'])
        self.assertEqual(self.r.store.admin(),before)
        self.assertEqual(self.r.store.live('shuffle'),snapshot)

    def test_health_never_regenerates_during_idle_time_daily_reset_or_pause(self):
        hit = self.hit()
        saved = self.b.export()
        for elapsed in (60, 601, DAY + 1, 7 * DAY):
            self.time.return_value = self.start + elapsed
            self.b.loaded_at = 0
            view = self.b.status('a', '192.0.2.1')
            self.assertEqual(view['hp'], hit['state']['hp'])
            self.assertEqual(view['total_damage'], 150)
            self.assertEqual(self.b.export(), saved)
        self.assertIsNone(view['you']['remaining'])
        self.b.control('pause', saved['id'])
        self.time.return_value += DAY
        self.b.control('resume', saved['id'])
        self.assertEqual(self.b.status()['hp'], saved['hp'])
        # Reloaded HTML must not briefly label a damaged boss as 100% health.
        page = self.app.test_client().get('/play')
        self.assertIn(f'id="bossPercent">{(saved["max_hp"] - saved["hp"]) / saved["max_hp"] * 100:.2f}% defeated</span>', page.text)

    def test_cold_app_restart_retains_all_committed_damage(self):
        self.hit()
        self.time.return_value += 60
        self.hit()
        saved = self.b.export()
        self.r.store.close()
        restarted = create_app(self.root, testing=True)
        self.addCleanup(restarted.extensions['runtime'].store.close)
        restored = restarted.extensions['boss']
        self.assertEqual(restored.export(), saved)
        self.assertEqual(restored.status()['hp'], DEFAULT_HP - 300)

    def test_storage_refuses_health_increases_and_implicit_new_raids(self):
        self.hit()
        saved = self.b.export()
        healed = copy.deepcopy(saved)
        healed['hp'] += 1
        healed['total_damage'] -= 1
        healed['version'] += 1
        next(iter(healed['players'].values()))['damage'] -= 1
        validate_boss(healed)  # Structurally valid, but it reverses committed damage.
        with self.assertRaises(BossError) as rejected:
            with self.r.store.connection(transaction=True) as conn:
                self.b._write(conn, healed)
        self.assertEqual(rejected.exception.code, 'progress_reversal')
        self.assertEqual(self.b.export(), saved)
        with self.assertRaises(BossError) as rejected:
            with self.r.store.connection(transaction=True) as conn:
                self.b._write(conn, fresh_raid())
        self.assertEqual(rejected.exception.code, 'new_raid_required')
        self.assertEqual(self.b.export(), saved)

    def test_pause_resume_restart_and_stale_raid(self):
        first=self.hit(); raid=first['state']['raid_id']
        self.b.control('pause',raid)
        with self.assertRaises(BossError):self.hit(guest='b',ip='192.0.2.2')
        self.b.control('resume',raid)
        self.assertEqual(self.hit(guest='b',ip='192.0.2.2')['state']['hp'],DEFAULT_HP-300)
        self.b.control('restart',raid,3_000_000)
        with self.assertRaises(BossError) as old:self.b.attack('a','192.0.2.1','blade',raid,'old-request-001')
        self.assertEqual(old.exception.code,'new_raid')
        state=self.b.export()
        self.assertEqual(state['hp'],3_000_000); self.assertEqual(len(state['history']),1)
        self.assertEqual(state['players'],{})

    def test_auth_csrf_malformed_attack_and_forged_damage(self):
        c,s=self.client()
        self.assertEqual(c.post('/play/api/attack',json={}).status_code,400)
        self.assertEqual(self.post(c,s,style=[]).status_code,400)
        forged=self.post(c,s,damage=99_999_999,cooldown=0,remaining=9999)
        self.assertEqual(forged.json['hit']['damage'],150)
        self.assertEqual(self.post(c,s).status_code,429)
        self.assertEqual(c.post('/admin/boss/action',data={'action':'pause'}).status_code,302)
        self.assertEqual(c.get('/play/api/state').headers['Cache-Control'],'no-store')
        # Public state does not reveal persisted identifiers, raw IPs or salt.
        payload=c.get('/play/api/state').text
        persisted=self.b.export()
        for private in (persisted['salt'],'192.0.2.1',*persisted['players'],*persisted['networks']):
            self.assertNotIn(private,payload)

    def test_admin_controls_require_admin_and_restart_confirmation(self):
        c,s=self.client()
        with c.session_transaction() as sess:sess.update(user='gingrsnaps',auth_version=1)
        form={'csrf':s['csrf'],'action':'restart','raid_id':s['state']['raid_id'],'health':'2400000'}
        self.assertEqual(c.post('/admin/boss/action',data=form).status_code,422)
        self.assertEqual(c.post('/admin/boss/action',data={**form,'confirm_restart':'yes'}).status_code,303)
        self.assertIn('Pause attacks',c.get('/admin?tab=boss').text)
        self.r.admin['users']['helper']=copy.deepcopy(self.r.admin['users']['gingrsnaps'])
        self.r.commit(self.r.admin,self.r.revision)
        with c.session_transaction() as sess:sess['user']='helper'
        current=self.b.status()['raid_id']
        self.assertEqual(c.post('/admin/boss/action',data={**form,'action':'pause','raid_id':current}).status_code,303)

    def test_proxy_headers_do_not_change_identity_or_reset_cooldowns(self):
        from flask import g
        a, sa = self.client(); b, sb = self.client()
        a.environ_base['HTTP_DO_CONNECTING_IP'] = '198.51.100.1'
        b.environ_base['HTTP_DO_CONNECTING_IP'] = '198.51.100.2'
        with self.app.test_request_context('/healthz', environ_base={'REMOTE_ADDR':'192.0.2.1'}, headers={'DO-Connecting-IP':'198.51.100.1'}):
            self.app.preprocess_request()
            self.assertEqual(g.client_ip, '192.0.2.1')  # Still untrusted on a direct host.
        self.assertEqual(self.post(a, sa).status_code, 200)
        self.assertEqual(self.post(b, sb).status_code, 200)
        self.app.extensions['settings'].proxy = True
        with self.app.test_request_context('/healthz', environ_base={'REMOTE_ADDR':'192.0.2.1'}, headers={'DO-Connecting-IP':'198.51.100.1'}):
            self.app.preprocess_request()
            self.assertEqual(g.client_ip, '198.51.100.1')
        self.assertEqual(self.post(b, sb).status_code, 429)
        c, sc = self.client('127.0.0.1')
        self.assertEqual(self.post(c, sc).status_code, 200)  # No IP header needed to play.
        c.environ_base['HTTP_DO_CONNECTING_IP'] = '198.51.100.3'
        c.environ_base['HTTP_X_FORWARDED_FOR'] = '198.51.100.1'
        self.assertEqual(self.post(c, sc).status_code, 429)

    def test_guest_profile_survives_admin_logout(self):
        c,s=self.client(); name=s['state']['you']['name']
        c.post('/admin/logout',data={'csrf':s['csrf']})
        self.assertEqual(c.get('/play/api/state').json['state']['you']['name'],name)

    def test_recovery_preserves_game_identity_cooldowns_and_progress(self):
        c,s=self.client(); self.post(c,s)
        with c.session_transaction() as sess:sess.update(user='gingrsnaps',auth_version=1)
        recovery=c.get('/admin/recovery-backup').json
        self.assertEqual(recovery['community_boss'],self.b.export())
        with tempfile.TemporaryDirectory() as directory:
            root=Path(directory); (root/'private').mkdir()
            (root/'private/recovery.seed.json').write_text(json.dumps(recovery))
            restored=create_app(root,testing=True)
            try:
                restored_boss=restored.extensions['boss']
                self.assertEqual(restored_boss.export(),self.b.export())
                r=restored.test_client()
                r.set_cookie('rh_raider',c.get_cookie('rh_raider').value)
                current=r.get('/play/api/state').json
                self.assertEqual(current['state']['you']['name'],s['state']['you']['name'])
                self.assertEqual(current['state']['you']['damage'],150)
                self.assertEqual(self.post(r,current).status_code,429)
            finally:restored.extensions['runtime'].store.close()

    def test_corrupt_game_recovery_rolls_back_account_import(self):
        self.hit()
        value=copy.deepcopy(self.r.admin); value['community_boss']=self.b.export()
        value['community_boss']['hp']-=1
        with tempfile.TemporaryDirectory() as directory:
            root=Path(directory); (root/'private').mkdir()
            (root/'private/recovery.seed.json').write_text(json.dumps(value))
            with self.assertRaises(ValueError):create_app(root,testing=True)
        bad=self.b.export(); next(iter(bad['players'].values()))['last_attack']=float('nan')
        with self.assertRaises(ValueError):validate_boss(bad)

    def test_saved_game_survives_process_reconstruction(self):
        self.hit(); before=self.b.export()
        store=Store(self.r.config)
        try:self.assertEqual(CommunityBoss(store).export(),before)
        finally:store.close()

    def test_one_hundred_raiders_can_keep_attacking_without_a_daily_cap(self):
        # 100 profiles all using weaknesses: 150 rounds defeat default HP.
        # This deliberately verifies the faster requested uncapped balance.
        finished = False
        for turn in range(150):
            self.time.return_value=self.start+turn*30
            for player in range(100):
                hit=self.hit(f'raider-{player}',f'203.0.113.{player+1}')
                if hit['state']['hp']==0:
                    finished=True; break
            if finished: break
        self.assertTrue(finished)
        self.assertEqual(turn,149)
        self.assertEqual(self.time.return_value-self.start,4470)


if __name__=='__main__':unittest.main()
```

## tests/test_boss_admin.py

```python
"""Host edits must preserve raid progress and validate real image bytes."""
import copy
import io
import json
import os
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from PIL import Image, PngImagePlugin

from boss import BossError, DEFAULT_HP, fresh_raid, validate_boss
from boss_avatar import image_bytes
from wager_backend import create_app


def picture(fmt='PNG', size=(900, 450)):
    stream = io.BytesIO()
    metadata = PngImagePlugin.PngInfo()
    metadata.add_text('Comment', 'Private image metadata')
    Image.new('RGB', size, '#d82832').save(stream, format=fmt, pnginfo=metadata)
    return stream.getvalue()


class BossAdminTests(unittest.TestCase):
    def setUp(self):
        directory = tempfile.TemporaryDirectory()
        self.addCleanup(directory.cleanup)
        self.root = Path(directory.name)
        environment = patch.dict(os.environ, {
            'APP_ENV': 'test', 'ADMIN_BOOTSTRAP_PASS': 'test-only-password',
        }, clear=True)
        environment.start()
        self.addCleanup(environment.stop)
        self.app = create_app(self.root, testing=True)
        self.runtime = self.app.extensions['runtime']
        self.boss = self.app.extensions['boss']
        self.addCleanup(self.runtime.store.close)
        self.client = self.app.test_client()
        self.client.environ_base['REMOTE_ADDR'] = '192.0.2.1'
        opening = self.client.get('/play/api/state').json
        self.csrf = opening['csrf']
        self.client.post('/play/api/profile', json={'raid_id':opening['state']['raid_id'], 'username':'TestAdminRaider'}, headers={'X-CSRF-Token':self.csrf})
        with self.client.session_transaction() as session:
            session.update(user='gingrsnaps', auth_version=1)

    def form(self, action, **fields):
        state = self.boss.status()
        return dict(csrf=self.csrf, action=action, raid_id=state['raid_id'],
                    health_revision=str(state['health_revision']), settings_revision=str(state['settings_revision']), **fields)

    def post(self, action, **fields):
        return self.client.post('/admin/boss/action', data=self.form(action, **fields))

    def upload(self, raw=None, filename='boss.png'):
        return self.post('avatar', avatar=(io.BytesIO(raw if raw is not None else picture()), filename))

    def hit(self, guest='one', ip='192.0.2.1'):
        state = self.boss.status(guest, ip)
        return self.boss.attack(guest, ip, state['weakness'], state['raid_id'], 'request-' + guest)

    def test_png_jpg_jpeg_webp_are_decoded_resized_and_cacheable_without_metadata(self):
        for fmt, filename in [('PNG', 'boss.png'), ('JPEG', '../../boss.JPG'), ('JPEG', 'boss.jpeg'), ('WEBP', 'boss.webp')]:
            with self.subTest(fmt=fmt):
                self.assertEqual(self.upload(picture(fmt), filename).status_code, 303)
                view = self.boss.status()
                self.assertTrue(view['avatar_custom'])
                response = self.client.get(view['avatar_url'])
                self.assertEqual(response.status_code, 200)
                self.assertEqual(response.mimetype, 'image/png')
                self.assertIn('immutable', response.headers['Cache-Control'])
                self.assertEqual(response.headers['X-Content-Type-Options'], 'nosniff')
                with Image.open(io.BytesIO(response.data)) as saved:
                    self.assertEqual(saved.size, (512, 256))
                    self.assertNotIn('Comment', saved.info)
                    self.assertNotIn('exif', saved.info)
                cached = self.client.get(view['avatar_url'], headers={'If-None-Match': response.headers['ETag']})
                self.assertEqual(cached.status_code, 304)
                self.assertEqual(cached.data, b'')
                self.assertIn(view['avatar_url'], self.client.get('/play').text)
                self.assertIn(view['avatar_url'], self.client.get('/').text)
                self.assertIn(view['avatar_url'], self.client.get('/admin?tab=boss').text)
                self.assertNotIn('community_boss_avatar', self.client.get('/play/api/state').text)
                self.assertNotIn(self.boss.avatar_document['data'], self.client.get('/public-state').text)

    def test_invalid_images_cannot_replace_existing_avatar_or_raid(self):
        self.upload()
        before = self.boss.recovery()
        gif = picture('GIF', (20, 20))
        for raw, filename in [(b'', 'boss.png'), (b'<script>alert(1)</script>', 'boss.png'),
                              (gif, 'boss.png'), (picture()[:40], 'boss.png'),
                              (picture(), 'boss.svg'), (b'x' * (4 * 1024 * 1024 + 1), 'boss.jpg')]:
            with self.subTest(filename=filename, length=len(raw)):
                self.assertEqual(self.upload(raw, filename).status_code, 422)
                self.assertEqual(self.boss.recovery(), before)
        with patch('boss_avatar.MAX_PIXELS', 100):
            self.assertEqual(self.upload(picture(size=(11, 10))).status_code, 422)
        frames = [Image.new('RGBA', (10, 10), color) for color in ('red', 'blue')]
        animation = io.BytesIO()
        frames[0].save(animation, format='PNG', save_all=True, append_images=frames[1:], duration=100, loop=0)
        self.assertEqual(self.upload(animation.getvalue()).status_code, 422)
        animation = io.BytesIO()
        frames[0].save(animation, format='WEBP', save_all=True, append_images=frames[1:], duration=100, loop=0)
        self.assertEqual(self.upload(animation.getvalue(), 'boss.webp').status_code, 422)
        self.assertEqual(self.boss.recovery(), before)

    def test_avatar_changes_keep_progress_accounts_and_cooldowns(self):
        self.hit()
        raid = self.boss.export()
        admin = self.runtime.store.admin()
        self.assertEqual(self.upload().status_code, 303)
        current = self.boss.export()
        for field in ('id', 'hp', 'max_hp', 'total_damage', 'total_attacks', 'players', 'networks'):
            self.assertEqual(current[field], raid[field])
        self.assertEqual(self.runtime.store.admin(), admin)
        with self.assertRaises(BossError) as blocked:
            self.boss.attack('one', '192.0.2.99', 'blade', current['id'], 'new-request-after-avatar')
        self.assertEqual(blocked.exception.code, 'cooldown')
        self.assertTrue(self.hit('two', '192.0.2.1')['ok'])
        image_url = self.boss.status()['avatar_url']
        self.boss.control('restart', current['id'])
        self.boss.loaded_at = 0
        self.assertEqual(self.boss.status()['avatar_url'], image_url)
        self.assertEqual(self.post('avatar_reset').status_code, 303)
        self.assertEqual(self.boss.status()['avatar_url'], '/static/redlogo.png')
        self.assertEqual(self.client.get(image_url).status_code, 404)

    def test_explicit_health_edit_uses_latest_damage_and_keeps_allowances(self):
        self.hit()
        form = self.form('health', health='3000000', confirm_health='yes')
        self.hit('two', '192.0.2.2')  # A hit after the host opened the form is not lost.
        before = self.boss.export()
        self.assertEqual(self.client.post('/admin/boss/action', data=form).status_code, 303)
        current = self.boss.export()
        self.assertEqual(current['hp'], 3_000_000 - 300)
        self.assertEqual(current['health_revision'], 1)
        for field in ('id', 'total_damage', 'total_attacks', 'players', 'networks'):
            self.assertEqual(current[field], before[field])
        self.assertEqual(self.post('health', health='2000000', confirm_health='yes').status_code, 303)
        self.assertEqual(self.boss.status()['hp'], 2_000_000 - 300)
        with patch('boss.time.time', return_value=current['started_at'] + 7 * 86400):
            self.boss.loaded_at = 0
            self.assertEqual(self.boss.status()['hp'], 2_000_000 - 300)
        validate_boss(self.boss.export())

    def test_health_edit_requires_confirmation_valid_range_and_current_revision(self):
        before = self.boss.export()
        for fields in ({'health': '3000000'}, {'health': 'oops', 'confirm_health': 'yes'},
                       {'health': '0', 'confirm_health': 'yes'}, {'health': str(2**53), 'confirm_health': 'yes'}):
            self.assertEqual(self.post('health', **fields).status_code, 422)
            self.assertEqual(self.boss.export(), before)
        old = self.form('health', health='3000000', confirm_health='yes')
        self.assertEqual(self.post('health', health='4000000', confirm_health='yes').status_code, 303)
        self.assertEqual(self.client.post('/admin/boss/action', data=old).status_code, 422)
        self.assertEqual(self.boss.status()['max_hp'], 4_000_000)
        self.boss.control('restart', before['id'])
        self.assertEqual(self.client.post('/admin/boss/action', data=old).status_code, 422)
        self.assertEqual(self.boss.status()['max_hp'], DEFAULT_HP)

    def test_completed_raid_only_reopens_after_explicit_health_edit(self):
        small = fresh_raid(health=50)
        with self.runtime.store.connection(transaction=True) as conn:
            self.boss._write(conn, small, new_raid=True)
        self.boss.loaded_at = 0
        self.hit()
        self.assertEqual(self.boss.status()['status'], 'victory')
        self.upload()
        self.assertEqual(self.boss.status()['hp'], 0)
        self.assertEqual(self.post('health', health='100000', confirm_health='yes').status_code, 303)
        self.assertEqual(self.boss.status()['hp'], 99_950)
        self.assertEqual(self.boss.status()['status'], 'active')
        self.assertEqual(self.boss.status()['total_damage'], 50)
        validate_boss(self.boss.export())

    def test_private_recovery_and_cold_start_keep_avatar_and_health_edits(self):
        self.hit()
        self.upload()
        self.post('health', health='3000000', confirm_health='yes')
        self.post('settings', boss_name='The Scarlet Beast', base_damage='120', weak_damage='180', burst_bonus='90')
        saved = self.boss.recovery()
        checkpoint = self.client.get('/admin/recovery-backup').json
        for field in saved:
            self.assertEqual(checkpoint[field], saved[field])
        # Existing state takes precedence, even with a malformed new seed.
        (self.root / 'private').mkdir(exist_ok=True)
        (self.root / 'private/recovery.seed.json').write_text('{}', encoding='utf-8')
        restarted = create_app(self.root, testing=True)
        self.addCleanup(restarted.extensions['runtime'].store.close)
        self.assertEqual(restarted.extensions['boss'].recovery(), saved)
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / 'private').mkdir()
            (root / 'private/recovery.seed.json').write_text(json.dumps(checkpoint), encoding='utf-8')
            restored = create_app(root, testing=True)
            self.addCleanup(restored.extensions['runtime'].store.close)
            self.assertEqual(restored.extensions['boss'].recovery(), saved)
            url = restored.extensions['boss'].status()['avatar_url']
            self.assertEqual(restored.test_client().get(url).data, image_bytes(saved['community_boss_avatar']))
            restored.extensions['runtime'].store.close()
        preview = self.client.post('/admin/recovery-preview', data={
            'csrf': self.csrf, 'recovery': (io.BytesIO(json.dumps(checkpoint).encode()), 'checkpoint.json'),
        })
        self.assertEqual(preview.status_code, 200)
        self.assertIn('Custom image included', preview.text)
        checkpoint['community_boss_avatar']['sha256'] = '0' * 64
        response = self.client.post('/admin/recovery-preview', data={
            'csrf': self.csrf, 'recovery': (io.BytesIO(json.dumps(checkpoint).encode()), 'checkpoint.json'),
        })
        self.assertEqual(response.status_code, 422)
        self.assertIn('checksum', response.text)
        self.assertEqual(self.boss.recovery(), saved)

    def test_upload_and_health_require_admin_and_csrf(self):
        for action, fields in [('avatar', {'avatar': (io.BytesIO(picture()), 'boss.png')}),
                               ('health', {'health': '3000000', 'confirm_health': 'yes'})]:
            form = self.form(action, **fields)
            form['csrf'] = 'forged'
            self.assertEqual(self.client.post('/admin/boss/action', data=form).status_code, 400)
        self.runtime.admin['users']['helper'] = copy.deepcopy(self.runtime.admin['users']['gingrsnaps'])
        self.runtime.commit(self.runtime.admin, self.runtime.revision)
        with self.client.session_transaction() as session:
            session['user'] = 'helper'
        self.assertIn('id="bossAvatarFile"', self.client.get('/admin?tab=boss').text)
        self.assertEqual(self.upload().status_code, 303)
        self.assertEqual(self.post('health', health='3000000', confirm_health='yes').status_code, 303)
        self.assertEqual(self.client.get('/admin/recovery-backup').status_code, 403)
        before = self.boss.recovery()
        with self.client.session_transaction() as session:
            session.pop('user')
        self.assertEqual(self.upload().status_code, 302)
        self.assertEqual(self.post('health', health='3000000', confirm_health='yes').status_code, 302)
        self.assertEqual(self.boss.recovery(), before)

    def test_every_boss_write_rejects_guests_forged_roles_and_revoked_sessions(self):
        before = self.boss.recovery()
        for mode in ('guest', 'unknown-account', 'revoked', 'bad-cookie', 'bad-csrf', 'missing-token', 'unicode-token'):
            self.client.delete_cookie('session')
            with self.client.session_transaction() as session:
                session.update(csrf=self.csrf, is_admin=True, role='superadmin')
                if mode != 'guest':
                    session.update(user='missing' if mode == 'unknown-account' else 'gingrsnaps',
                                   auth_version=0 if mode == 'revoked' else 1)
                if mode == 'missing-token':
                    session.pop('csrf')
            if mode == 'bad-cookie':
                self.client.set_cookie('session', 'forged-not-signed')
            for action in ('avatar', 'avatar_reset', 'health', 'settings', 'pause', 'resume', 'restart'):
                with self.subTest(mode=mode, action=action), patch('wager_backend.from_upload') as decode:
                    form = self.form(action, health='3000000', confirm_health='yes', confirm_restart='yes',
                                     boss_name='Unauthorized', base_damage='9000', weak_damage='9999', burst_bonus='9999',
                                     role='superadmin', is_admin='true', user='gingrsnaps')
                    if action == 'avatar':
                        form['avatar'] = (io.BytesIO(picture('WEBP')), 'boss.webp')
                    if mode == 'bad-csrf':
                        form['csrf'] = 'forged'
                    if mode == 'missing-token':
                        form['csrf'] = '!'
                    if mode == 'unicode-token':
                        form['csrf'] = '🔥'
                    response = self.client.post('/admin/boss/action', data=form, headers={
                        'Accept': 'application/json', 'X-Admin': 'true', 'X-User': 'gingrsnaps',
                    })
                    self.assertEqual(response.status_code, 400 if mode in {'bad-csrf', 'missing-token', 'unicode-token'} else 401)
                    decode.assert_not_called()
                    self.assertEqual(self.boss.recovery(), before)

    def test_regular_admin_can_sign_in_and_manage_boss_but_not_export_accounts(self):
        self.runtime.admin['users']['helper'] = copy.deepcopy(self.runtime.admin['users']['gingrsnaps'])
        self.runtime.commit(self.runtime.admin, self.runtime.revision)
        self.client.post('/admin/logout', data={'csrf': self.csrf})
        opening = self.client.get('/play/api/state').json
        self.csrf = opening['csrf']
        self.client.post('/play/api/profile', json={'raid_id':opening['state']['raid_id'], 'username':'TestAdminRaider'}, headers={'X-CSRF-Token':self.csrf})
        login = self.client.post('/admin', data={'csrf': self.csrf, 'username': 'helper', 'password': 'test-only-password'})
        self.assertEqual(login.status_code, 303)
        opening = self.client.get('/play/api/state').json
        self.csrf = opening['csrf']
        self.client.post('/play/api/profile', json={'raid_id':opening['state']['raid_id'], 'username':'TestAdminRaider'}, headers={'X-CSRF-Token':self.csrf})
        page = self.client.get('/admin?tab=boss').text
        self.assertIn('id="bossSettingsForm"', page)
        self.assertIn('image/webp', page)
        self.assertNotIn('Download private recovery file', page)
        self.assertEqual(self.post('settings', boss_name='Ruby Colossus', base_damage='120', weak_damage='180', burst_bonus='75').status_code, 303)
        self.assertEqual(self.upload(picture('WEBP'), 'boss.webp').status_code, 303)
        self.assertEqual(self.post('health', health='3500000', confirm_health='yes').status_code, 303)
        for action in ('pause', 'resume', 'avatar_reset'):
            self.assertEqual(self.post(action).status_code, 303)
        self.assertEqual(self.post('restart', health='2500000', confirm_restart='yes').status_code, 303)
        self.assertEqual(self.boss.status()['name'], 'Ruby Colossus')
        self.assertEqual(self.boss.status()['rules']['weak_damage'], 180)
        self.assertEqual(self.client.get('/admin/recovery-backup').status_code, 403)
        # Deleting an admin invalidates its existing browser session immediately.
        self.runtime.admin['users'].pop('helper')
        self.runtime.commit(self.runtime.admin, self.runtime.revision)
        before = self.boss.export()
        self.assertEqual(self.post('pause').status_code, 302)
        self.assertEqual(self.boss.export(), before)

    def test_damage_settings_apply_to_future_hits_and_public_forgery_has_no_effect(self):
        self.assertEqual(self.post('settings', boss_name='Ruby Colossus', base_damage='300', weak_damage='400', burst_bonus='50').status_code, 303)
        # Keep signed admin cookies within their real 12-hour lifetime while
        # advancing the combat clock through ten one-minute cooldowns.
        with patch('boss.time.time', return_value=self.boss.export()['created_at']) as clock:
            for index in range(10):
                clock.return_value += 60
                state = self.boss.status('player', '192.0.2.10')
                result = self.boss.attack('player', '192.0.2.10', state['weakness'], state['raid_id'], f'damage-hit-{index}')
                self.assertEqual(result['hit']['damage'], 450 if index == 9 else 400)
            saved = self.boss.export()
            self.assertEqual(self.post('settings', boss_name='Ruby Colossus', base_damage='10', weak_damage='20', burst_bonus='0').status_code, 303)
            after = self.boss.export()
            for field in ('id', 'hp', 'players', 'networks', 'total_damage', 'total_attacks'):
                self.assertEqual(after[field], saved[field])
            retry = self.boss.attack('player', '192.0.2.10', 'blade', saved['id'], 'damage-hit-9')
            self.assertTrue(retry['duplicate'])
            self.assertEqual(retry['hit']['damage'], 450)
            guest = self.app.test_client()
            snapshot = guest.get('/play/api/state').json
            guest.post('/play/api/profile', json={'raid_id':snapshot['state']['raid_id'], 'username':'PublicTest'}, headers={'X-CSRF-Token':snapshot['csrf']})
            forged = guest.post('/play/api/attack', json={
                'raid_id': snapshot['state']['raid_id'], 'style': snapshot['state']['weakness'], 'request_id': 'forged-damage-attempt',
                'damage': 99_999_999, 'hp': 0, 'name': 'Changed', 'settings_revision': 999,
                'settings': {'damage': 9999}, 'role': 'superadmin', 'action': 'health',
            }, headers={'X-CSRF-Token': snapshot['csrf']})
            self.assertEqual(forged.status_code, 200)
            self.assertEqual(forged.json['hit']['damage'], 20)
            self.assertEqual(self.boss.status()['name'], 'Ruby Colossus')
            self.assertEqual(self.boss.status()['hp'], saved['hp'] - 20)
            validate_boss(self.boss.export())  # Old 450-point receipts remain valid.

    def test_name_and_damage_validation_stale_forms_and_storage_write_guard(self):
        values = dict(boss_name='Ruby Colossus', base_damage='100', weak_damage='150', burst_bonus='100')
        before = self.boss.export()
        for invalid in ({'boss_name': ''}, {'boss_name': 'x' * 61}, {'boss_name': 'bad\nname'},
                        {'base_damage': '-1'}, {'weak_damage': '-1'}, {'weak_damage': str(2**53)},
                        {'burst_bonus': '-1'}, {'burst_bonus': '0.5'}, {'base_damage': 'true'}):
            self.assertEqual(self.post('settings', **{**values, **invalid}).status_code, 422)
            self.assertEqual(self.boss.export(), before)
        stale = self.form('settings', **values)
        self.assertEqual(self.post('settings', **values).status_code, 303)
        self.assertEqual(self.client.post('/admin/boss/action', data=stale).status_code, 422)
        saved = self.boss.export()
        bypass = copy.deepcopy(saved)
        bypass['settings']['damage'] = 10
        with self.assertRaises(BossError) as blocked:
            with self.runtime.store.connection(transaction=True) as conn:
                self.boss._write(conn, bypass)
        self.assertEqual(blocked.exception.code, 'settings_guard')
        self.assertEqual(self.boss.export(), saved)
        stale = self.form('settings', **values)
        self.post('restart', confirm_restart='yes')
        self.assertEqual(self.client.post('/admin/boss/action', data=stale).status_code, 422)
        self.assertEqual(self.boss.status()['name'], 'Ruby Colossus')

    def test_public_pages_have_no_editor_and_boss_names_render_as_text(self):
        name = '<img src=x onerror=alert(1)>'
        self.post('settings', boss_name=name, base_damage='100', weak_damage='150', burst_bonus='100')
        guest = self.app.test_client()
        for url in ('/', '/play'):
            page = guest.get(url).text
            self.assertIn('&lt;img', page)
            self.assertNotIn(name, page)
            for editor in ('bossAvatarFile', 'bossNameInput', 'bossMaxHealth', 'bossSettingsForm'):
                self.assertNotIn('id="' + editor + '"', page)
            self.assertNotIn('action="/admin/boss/action"', page)
        before = self.boss.recovery()
        self.assertEqual(guest.get('/admin/boss/action?action=health&health=0').status_code, 405)
        self.assertEqual(guest.post('/play/api/state', json={'hp': 0}).status_code, 405)
        self.assertEqual(guest.get('/admin?tab=boss').status_code, 200)
        self.assertNotIn('bossSettingsForm', guest.get('/admin?tab=boss').text)
        self.assertEqual(self.boss.recovery(), before)


if __name__ == '__main__':
    unittest.main()
```

## tests/test_boss_frontend.cjs

```javascript
/* Real rendered templates; fake clock/transport exercise shared-state behavior. */
const { test } = require("node:test");
const assert = require("node:assert/strict");
const fs = require("node:fs");
const path = require("node:path");
const { JSDOM } = require("jsdom");
const root = path.resolve(__dirname, ".."),
  fixtures = process.env.DOM_FIXTURES || path.join(root, ".test-fixtures");
const code = fs.readFileSync(path.join(root, "static/boss.js"), "utf8");
const flush = async () => {
  for (let i = 0; i < 8; i++) await new Promise((r) => setImmediate(r));
};
const response = (value, status = 200) => ({
  ok: status < 400,
  status,
  headers: new Map([["content-type", "application/json"]]),
  json: async () => structuredClone(value),
});
function page(name = "play", initialStyle) {
  const dom = new JSDOM(
    fs.readFileSync(path.join(fixtures, name + ".html"), "utf8"),
    { url: "https://example.test/play", runScripts: "outside-only" },
  );
  const w = dom.window,
    calls = [],
    timers = new Map(),
    intervals = new Map();
  let clock = 0,
    serial = 0;
  let value = JSON.parse(
    fs.readFileSync(
      path.join(fixtures, name === "boss" ? "boss-admin.json" : "boss.json"),
      "utf8",
    ),
  );
  Object.defineProperty(w.performance, "now", { value: () => clock });
  Object.defineProperty(w.document, "hidden", {
    value: false,
    configurable: true,
  });
  w.setTimeout = (fn, delay) => {
    const id = ++serial;
    timers.set(id, { fn, at: clock + delay });
    return id;
  };
  w.clearTimeout = (id) => timers.delete(id);
  w.setInterval = (fn) => {
    const id = ++serial;
    intervals.set(id, fn);
    return id;
  };
  let responder = async () => response(value);
  w.fetch = async (url, options) => {
    calls.push({ url, options });
    return responder(url, options);
  };
  if (initialStyle) w.localStorage.setItem("rh.boss.style", initialStyle);
  w.eval(code);
  return {
    w,
    dom,
    calls,
    value,
    timers,
    respond(fn) {
      responder = fn;
    },
    async advance(ms) {
      clock += ms;
      for (const [id, t] of [...timers])
        if (t.at <= clock) {
          timers.delete(id);
          t.fn();
        }
      for (const fn of intervals.values()) fn();
      await flush();
    },
    close() {
      dom.window.close();
    },
  };
}
test("bare game has unique IDs, working controls and no explanations or footer", async () => {
  const p = page();
  await flush();
  const doc = p.w.document,
    ids = [...doc.querySelectorAll("[id]")].map((e) => e.id);
  assert.equal(new Set(ids).size, ids.length);
  assert.equal(doc.querySelector("#howToPlay"), null);
  assert.equal(doc.querySelector("#bossStory"), null);
  assert.equal(doc.querySelector("#attackHint"), null);
  assert.equal(doc.querySelector('footer a[href="/admin"]'), null);
  assert.equal(doc.querySelector("#attackButton").disabled, false);
  p.close();
});
test("game polls every five seconds and pauses while hidden", async () => {
  const p = page();
  await flush();
  assert.equal(p.calls.length, 1);
  await p.advance(5000);
  assert.equal(p.calls.length, 2);
  Object.defineProperty(p.w.document, "hidden", {
    value: true,
    configurable: true,
  });
  p.w.document.dispatchEvent(new p.w.Event("visibilitychange"));
  await p.advance(10000);
  assert.equal(p.calls.length, 2);
  Object.defineProperty(p.w.document, "hidden", {
    value: false,
    configurable: true,
  });
  p.w.document.dispatchEvent(new p.w.Event("visibilitychange"));
  await flush();
  assert.equal(p.calls.length, 3);
  assert.ok(p.calls.every((x) => !x.options.method));
  p.close();
});
test("attack sends only server-validated inputs and renders countdown", async () => {
  const p = page();
  await flush();
  let sent;
  p.respond(async (url, options) => {
    if (options.method === "POST") {
      sent = JSON.parse(options.body);
      const s = p.value.state;
      s.version++;
      s.hp -= 150;
      s.total_damage = 150;
      s.total_attacks = 1;
      s.you.ready_at = s.server_time + 30;
      s.you.last_request = sent.request_id;
      s.you.last_hit = {
        damage: 150,
        style: sent.style,
        weakness: true,
        burst: false,
      };
      return response({ ok: true, state: s, hit: s.you.last_hit });
    }
    return response(p.value);
  });
  p.w.document.querySelector('[data-style="bow"]').click();
  p.w.document.querySelector("#attackButton").click();
  await flush();
  assert.deepEqual(Object.keys(sent).sort(), [
    "raid_id",
    "request_id",
    "style",
  ]);
  assert.equal(sent.style, "bow");
  const post = p.calls.find((c) => c.options.method === "POST");
  assert.equal(post.options.headers["X-CSRF-Token"], p.value.csrf);
  assert.equal(p.w.document.querySelector("#attackButton").disabled, true);
  assert.match(p.w.document.querySelector("#attackButton").textContent, /0:30/);
  assert.match(p.w.document.querySelector("#hitResult").textContent, /150/);
  p.close();
});
test("uncertain delivery keeps receipt and retry uses same ID", async () => {
  const p = page();
  await flush();
  const ids = [];
  p.respond(async (url, options) => {
    if (options.method === "POST") {
      ids.push(JSON.parse(options.body).request_id);
      throw new Error("Network disconnected");
    }
    return response(p.value);
  });
  p.w.document.querySelector("#attackButton").click();
  await flush();
  assert.match(
    p.w.document.querySelector("#attackButton").textContent,
    /Retry last strike/,
  );
  p.w.document
    .querySelector("#attackButton")
    .dispatchEvent(new p.w.Event("pointerleave"));
  p.w.document.querySelector("#attackButton").click();
  await flush();
  assert.equal(ids.length, 2);
  assert.equal(ids[0], ids[1]);
  p.close();
});
test("older polls cannot reverse boss damage", async () => {
  const p = page();
  await flush();
  const old = structuredClone(p.value);
  p.value.state.hp -= 250;
  p.value.state.version++;
  p.value.state.server_time++;
  await p.advance(5000);
  assert.equal(
    p.w.document.querySelector("#bossHealthBar").value,
    p.value.state.max_hp - p.value.state.hp,
  );
  p.respond(async () => response(old));
  await p.advance(5000);
  assert.equal(
    p.w.document.querySelector("#bossHealthBar").value,
    p.value.state.max_hp - p.value.state.hp,
  );
  p.close();
});
test("victory and paused raids stop attacks, hostile names render as text", async () => {
  const p = page();
  await flush();
  p.value.state.status = "paused";
  p.value.state.leaders = [
    {
      name: "<img src=x onerror=alert(1)>",
      damage: 100,
      attacks: 1,
      you: false,
    },
  ];
  await p.advance(5000);
  assert.equal(p.w.document.querySelector("#attackButton").disabled, true);
  assert.equal(p.w.document.querySelector("#bossLeaders img"), null);
  p.value.state.status = "victory";
  p.value.state.hp = 0;
  await p.advance(5000);
  assert.match(
    p.w.document.querySelector("#attackButton").textContent,
    /Victory/,
  );
  assert.equal(p.w.document.querySelector("#victoryRecap").hidden, false);
  p.close();
});
test("admin boss updates preserve difficulty draft and restart confirmation", async () => {
  const p = page("boss");
  await flush();
  const input = p.w.document.querySelector("#bossHealthInput");
  input.value = "5000000";
  const confirm = p.w.document.querySelector('[name="confirm_restart"]');
  confirm.checked = true;
  await p.advance(5000);
  assert.equal(input.value, "5000000");
  assert.equal(confirm.checked, true);
  assert.equal(p.w.document.querySelector("footer"), null);
  p.close();
});

test("a successful background poll cannot erase an attack error", async () => {
  const p = page();
  await flush();
  p.respond(async (url, options) =>
    options.method === "POST"
      ? response({ error: "Your shared connection is cooling down." }, 429)
      : response(p.value),
  );
  p.w.document.querySelector("#attackButton").click();
  await flush();
  await p.advance(5000);
  await p.advance(5000);
  const error = p.w.document.querySelector("#bossError");
  assert.equal(error.hidden, false);
  assert.match(error.textContent, /shared connection/);
  p.w.document.querySelector("#dismissBossError").click();
  assert.equal(error.hidden, true);
  p.close();
});

test("unchanged contributor rows survive polls and mobile styles share attack controls", async () => {
  const p = page();
  await flush();
  p.value.state.leaders = [
    { name: "Raider ABCDEF12", damage: 150, attacks: 1, you: false },
  ];
  await p.advance(5000);
  const row = p.w.document.querySelector("#bossLeaders li");
  await p.advance(5000);
  assert.strictEqual(p.w.document.querySelector("#bossLeaders li"), row);
  const style = p.w.document.querySelector("#dockStyle");
  style.value = "magic";
  style.dispatchEvent(new p.w.Event("change"));
  assert.equal(
    p.w.document
      .querySelector('[data-style="magic"]')
      .getAttribute("aria-pressed"),
    "true",
  );
  let sent;
  p.respond(async (url, options) => {
    if (options.method === "POST") {
      sent = JSON.parse(options.body);
      return response({ error: "Fixture rejection" }, 400);
    }
    return response(p.value);
  });
  p.w.document.querySelector("#dockAttack").click();
  await flush();
  assert.equal(sent.style, "magic");
  p.close();
});

test("copy link supplies selectable text if clipboard access is unavailable", async () => {
  const p = page();
  await flush();
  p.w.document.querySelector("#copyRaidLink").click();
  await flush();
  const field = p.w.document.querySelector("#shareUrl");
  assert.equal(field.hidden, false);
  assert.equal(field.value, "https://example.test/play");
  assert.equal(field.selectionEnd, field.value.length);
  p.close();
});

test("same-raid updates cannot refill health even with a newer version or clock", async () => {
  const p = page();
  await flush();
  p.value.state.hp -= 150;
  p.value.state.total_damage = 150;
  p.value.state.total_attacks = 1;
  p.value.state.version++;
  await p.advance(5000);
  const hp = p.value.state.hp;
  p.value.state.hp += 150;
  p.value.state.total_damage = 0;
  p.value.state.total_attacks = 0;
  for (const versionBump of [0, 10]) {
    p.value.state.version += versionBump;
    p.value.state.server_time += 5;
    await p.advance(5000);
    assert.equal(
      p.w.document.querySelector("#bossHealthBar").value,
      p.value.state.max_hp - hp,
    );
    assert.equal(p.w.document.querySelector("#bossDamage").textContent, "150");
  }
  p.close();
});

test("defeat progress stays at 100 percent until a different raid starts", async () => {
  const p = page();
  await flush();
  p.value.state.hp = 0;
  p.value.state.total_damage = p.value.state.max_hp;
  p.value.state.status = "victory";
  p.value.state.version++;
  await p.advance(5000);
  assert.equal(
    p.w.document.querySelector("#bossHealthBar").value,
    p.value.state.max_hp,
  );
  p.value.state.hp = p.value.state.max_hp;
  p.value.state.total_damage = 0;
  p.value.state.status = "waiting";
  p.value.state.version++;
  await p.advance(5000);
  assert.equal(
    p.w.document.querySelector("#bossHealthBar").value,
    p.value.state.max_hp,
  );
  p.value.state.raid_id = "new-host-started-raid";
  p.value.state.server_time += 10;
  await p.advance(5000);
  assert.equal(p.w.document.querySelector("#bossHealthBar").value, 0);
  p.close();
});

test("explicit host health revisions update the current raid without losing damage", async () => {
  const p = page();
  await flush();
  p.value.state.hp -= 150;
  p.value.state.total_damage = 150;
  p.value.state.total_attacks = 1;
  p.value.state.version++;
  await p.advance(5000);
  const old = structuredClone(p.value);
  p.value.state.max_hp += 500000;
  p.value.state.hp += 500000;
  p.value.state.version++;
  p.value.state.health_revision = 1;
  await p.advance(5000);
  const bar = p.w.document.querySelector("#bossHealthBar");
  assert.equal(bar.value, p.value.state.max_hp - p.value.state.hp);
  assert.equal(bar.max, p.value.state.max_hp);
  assert.equal(p.w.document.querySelector("#bossDamage").textContent, "150");
  const saved = bar.value;
  old.state.server_time += 100;
  old.state.version += 100;
  p.respond(async () => response(old));
  await p.advance(5000);
  assert.equal(bar.value, saved);
  p.close();
});

test("avatar polls refresh the arena and admin preview while preserving host drafts", async () => {
  for (const name of ["play", "boss"]) {
    const p = page(name);
    await flush();
    const doc = p.w.document;
    if (name === "boss") {
      doc.querySelector("#bossMaxHealth").value = "5000000";
      doc.querySelector('[name="confirm_health"]').checked = true;
    }
    const url = "/play/avatar/" + "a".repeat(64) + ".png";
    p.value.state.avatar_url = url;
    p.value.state.avatar_custom = true;
    p.value.state.version++;
    await p.advance(5000);
    assert.equal(
      doc.querySelector("[data-boss-avatar]").getAttribute("src"),
      url,
    );
    assert.equal(
      doc
        .querySelector("[data-boss-avatar]")
        .classList.contains("custom-avatar"),
      true,
    );
    if (name === "boss") {
      assert.equal(doc.querySelector("#bossMaxHealth").value, "5000000");
      assert.equal(doc.querySelector('[name="confirm_health"]').checked, true);
      assert.equal(doc.querySelector('[name="health_revision"]').value, "0");
    }
    p.close();
  }
});

test("a revived raid refreshes its contributor recap on the next victory", async () => {
  const p = page();
  await flush();
  let recaps = 0;
  p.respond(async (url) => {
    if (url.startsWith("/play/api/contributors")) {
      recaps++;
      return response({
        raid_id: p.value.state.raid_id,
        health_revision: p.value.state.health_revision || 0,
        contributors: [
          {
            name: "Raider " + recaps,
            attacks: recaps,
            damage: p.value.state.total_damage,
          },
        ],
      });
    }
    return response(p.value);
  });
  const s = p.value.state;
  s.hp = 0;
  s.total_damage = s.max_hp;
  s.status = "victory";
  s.version++;
  await p.advance(5000);
  assert.equal(recaps, 1);
  assert.match(
    p.w.document.querySelector("#allContributors").textContent,
    /Raider 1/,
  );
  s.max_hp += 500;
  s.hp = 500;
  s.health_revision = 1;
  s.status = "active";
  s.version++;
  await p.advance(5000);
  assert.equal(p.w.document.querySelector("#victoryRecap").hidden, true);
  s.hp = 0;
  s.total_damage += 500;
  s.status = "victory";
  s.version++;
  await p.advance(5000);
  assert.equal(recaps, 2);
  assert.match(
    p.w.document.querySelector("#allContributors").textContent,
    /Raider 2/,
  );
  p.close();
});

test("boss name and damage updates use text and preserve admin settings drafts", async () => {
  for (const name of ["play", "boss"]) {
    const p = page(name);
    await flush();
    const doc = p.w.document;
    if (name === "boss") {
      doc.querySelector("#bossNameInput").value = "Unsaved boss";
      doc.querySelector("#bossBaseDamage").value = "200";
    }
    p.value.state.name = "<img src=x onerror=alert(1)>";
    p.value.state.rules.damage = 120;
    p.value.state.rules.weak_damage = 180;
    p.value.state.rules.burst_bonus = 80;
    p.value.state.settings_revision = 1;
    p.value.state.version++;
    await p.advance(5000);
    assert.equal(
      doc.querySelector("#bossName").textContent,
      p.value.state.name,
    );
    assert.equal(doc.querySelector("#bossName img"), null);
    if (name === "play") {
      assert.match(
        doc.querySelector("#bossWeakness").textContent,
        /180 damage/,
      );
      assert.match(doc.querySelector("#burstLabel").textContent, /80 damage/);
      assert.equal(doc.querySelector(".boss-sprite").alt, p.value.state.name);
      assert.equal(doc.querySelector("#bossNameInput"), null);
      assert.equal(doc.querySelector("#bossAvatarFile"), null);
    } else {
      assert.equal(doc.querySelector("#bossNameInput").value, "Unsaved boss");
      assert.equal(doc.querySelector("#bossBaseDamage").value, "200");
      assert.equal(doc.querySelector('[name="settings_revision"]').value, "0");
    }
    p.close();
  }
});

test("stationary clicks and the other attack button cannot bypass the pointer latch", async () => {
  const p = page();
  await flush();
  const doc = p.w.document,
    attack = doc.querySelector("#attackButton"),
    dock = doc.querySelector("#dockAttack");
  let hits = 0;
  p.respond(async (url, options) => {
    if (options.method === "POST") {
      const body = JSON.parse(options.body),
        s = p.value.state;
      hits++;
      s.version++;
      s.total_attacks++;
      s.you.attacks++;
      s.total_damage += 100;
      s.hp -= 100;
      s.you.ready_at = s.server_time + 30;
      s.you.last_request = body.request_id;
      s.you.last_hit = {
        damage: 100,
        style: body.style,
        weakness: false,
        burst: false,
      };
      return response({ ok: true, state: s, hit: s.you.last_hit });
    }
    return response(p.value);
  });
  attack.click();
  await flush();
  p.value.state.server_time += 30;
  await p.advance(5000);
  assert.equal(attack.disabled, true);
  attack.click();
  dock.click();
  await flush();
  assert.equal(hits, 1);
  assert.match(doc.querySelector("#rearmHint").textContent, /off/);
  // Moving outside is detected even when a native disabled button suppresses leave events.
  attack.getBoundingClientRect = () => ({
    left: 10,
    right: 110,
    top: 10,
    bottom: 60,
  });
  doc.dispatchEvent(
    new p.w.MouseEvent("pointermove", { clientX: 120, clientY: 20 }),
  );
  assert.equal(attack.disabled, false);
  attack.click();
  await flush();
  assert.equal(hits, 2);
  assert.equal(doc.querySelector("#yourAttacks").textContent, "2");
  p.close();
});

test("keyboard release re-arms attacks and a held activation key cannot repeat", async () => {
  const p = page();
  await flush();
  const doc = p.w.document,
    attack = doc.querySelector("#attackButton");
  attack.dispatchEvent(
    new p.w.KeyboardEvent("keydown", { key: "Enter", bubbles: true }),
  );
  attack.click();
  await flush();
  assert.equal(attack.disabled, true);
  const repeat = new p.w.KeyboardEvent("keydown", {
    key: "Enter",
    repeat: true,
    cancelable: true,
  });
  attack.dispatchEvent(repeat);
  assert.equal(repeat.defaultPrevented, true);
  doc.dispatchEvent(
    new p.w.KeyboardEvent("keyup", { key: "Enter", bubbles: true }),
  );
  assert.equal(attack.disabled, false);
  // Space normally dispatches click after keyup: it must not remain locked.
  attack.dispatchEvent(
    new p.w.KeyboardEvent("keydown", { key: " ", bubbles: true }),
  );
  doc.dispatchEvent(
    new p.w.KeyboardEvent("keyup", { key: " ", bubbles: true }),
  );
  attack.click();
  await flush();
  assert.equal(attack.disabled, false);
  p.close();
});

test("touch taps remain usable after their release", async () => {
  const p = page();
  await flush();
  const attack = p.w.document.querySelector("#attackButton");
  const touch = new p.w.Event("pointerdown");
  Object.defineProperty(touch, "pointerType", { value: "touch" });
  attack.dispatchEvent(touch);
  attack.click();
  await flush();
  assert.equal(attack.disabled, false); // fake server returns no cooldown in this gesture-only test
  p.close();
});

test("private admin feed uses admin authentication and removes names on expiry", async () => {
  const p = page("boss");
  await flush();
  assert.equal(p.calls[0].url, "/admin/boss/status");
  p.value.state.admin_leaders = [
    {
      name: "<img src=x onerror=alert(1)>",
      alias: "Raider ABCD1234",
      damage: 500,
      attacks: 5,
      name_provided: true,
    },
  ];
  p.value.state.version++;
  await p.advance(5000);
  const list = p.w.document.querySelector("#adminBossLeaders");
  assert.match(list.textContent, /<img/);
  assert.equal(list.querySelector("img"), null);
  p.respond(async () => response({ error: "Session expired" }, 401));
  await p.advance(5000);
  assert.doesNotMatch(list.textContent, /<img/);
  assert.match(list.textContent, /Sign in/);
  const count = p.calls.length;
  await p.advance(60000);
  assert.equal(p.calls.length, count);
  assert.equal(p.w.document.querySelector("#bossNameInput").disabled, true);
  p.close();
});

test("name save preserves typed drafts, unlocks play, and never sends an automatic attack", async () => {
  const p = page();
  await flush();
  const doc = p.w.document,
    input = doc.querySelector("#playerUsername");
  p.value.state.you.identity_ready = false;
  p.value.state.version++;
  await p.advance(5000);
  assert.equal(doc.querySelector("#attackButton").disabled, true);
  input.value = "My full name";
  input.dispatchEvent(new p.w.Event("input"));
  await p.advance(5000);
  assert.equal(input.value, "My full name");
  p.respond(async (url, options) => {
    if (url === "/play/api/profile") {
      assert.equal(JSON.parse(options.body).username, "My full name");
      p.value.state.you.display_name = "My full name";
      p.value.state.you.identity_ready = true;
      p.value.state.version++;
    }
    return response(p.value);
  });
  doc
    .querySelector("#playerNameForm")
    .dispatchEvent(new p.w.Event("submit", { cancelable: true }));
  await flush();
  assert.equal(doc.querySelector("#attackButton").disabled, false);
  assert.match(doc.querySelector("#playerNameResult").textContent, /Saved/);
  assert.equal(p.calls.filter((c) => c.url === "/play/api/attack").length, 0);
  assert.equal(doc.querySelectorAll("#yourBadges li").length, 8);
  assert.match(
    doc.querySelector("#bossPercent").textContent,
    /^0.00% defeated$/,
  );
  p.close();
});

test("saved name collapses into an editable identity without disturbing play", async () => {
  const p = page();
  await flush();
  const doc = p.w.document;
  assert.equal(doc.querySelector("#playerNameForm").hidden, true);
  assert.match(doc.querySelector("#playingAs").textContent, /FixtureRaider/);
  doc.querySelector("#editPlayerName").click();
  assert.equal(doc.querySelector("#playerNameForm").hidden, false);
  assert.equal(doc.activeElement.id, "playerUsername");
  await p.advance(5000);
  assert.equal(doc.querySelector("#playerNameForm").hidden, false);
  assert.equal(doc.querySelector("#attackButton").disabled, false);
  p.close();
});

test("style choice persists while weakness changes independently", async () => {
  const p = page("play", "magic");
  await flush();
  const doc = p.w.document;
  assert.equal(
    doc.querySelector('[data-style="magic"]').getAttribute("aria-pressed"),
    "true",
  );
  assert.equal(doc.querySelector("#dockStyle").value, "magic");
  doc.querySelector('[data-style="bow"]').click();
  assert.equal(p.w.localStorage.getItem("rh.boss.style"), "bow");
  p.value.state.weakness = "blade";
  p.value.state.version++;
  await p.advance(5000);
  assert.equal(
    doc.querySelector('[data-style="bow"]').getAttribute("aria-pressed"),
    "true",
  );
  p.close();
});

test("recovery code is created only by an explicit owner action", async () => {
  const p = page();
  await flush();
  const doc = p.w.document;
  assert.equal(
    p.calls.filter((c) => c.url.includes("recovery-code")).length,
    0,
  );
  p.respond(async (url, options) => {
    if (url.endsWith("recovery-code")) {
      assert.equal(options.method, "POST");
      assert.ok(options.headers["X-CSRF-Token"]);
      p.value.state.you.recovery_saved = true;
      p.value.state.version++;
      return response({ ...p.value, code: "private-fixture-code" });
    }
    return response(p.value);
  });
  doc.querySelector("#makeRecoveryCode").click();
  await flush();
  assert.equal(doc.querySelector("#recoveryCodeBox").hidden, false);
  assert.equal(
    doc.querySelector("#recoveryCode").value,
    "private-fixture-code",
  );
  assert.equal(p.w.localStorage.getItem("private-fixture-code"), null);
  assert.equal(p.calls.filter((c) => c.url.endsWith("/attack")).length, 0);
  p.close();
});

test("recovery posts a private code and restores the owner view", async () => {
  const p = page();
  await flush();
  const doc = p.w.document;
  p.respond(async (url, options) => {
    if (url.endsWith("/recover")) {
      assert.equal(JSON.parse(options.body).code, "fixture-secret");
      p.value.state.you.display_name = "Restored raider";
      p.value.state.version++;
    }
    return response(p.value);
  });
  doc.querySelector("#recoveryInput").value = "fixture-secret";
  doc
    .querySelector("#recoverPlayerForm")
    .dispatchEvent(new p.w.Event("submit", { cancelable: true }));
  await flush();
  assert.equal(doc.querySelector("#playingAs").textContent, "Restored raider");
  assert.equal(doc.querySelector("#recoveryInput").value, "");
  assert.match(
    doc.querySelector("#recoveryResult").textContent,
    /Player restored/,
  );
  p.close();
});

test("rally lights the arena without sending an attack or changing damage", async () => {
  const p = page();
  await flush();
  const doc = p.w.document;
  p.value.state.rally = { goal: 15, count: 15, unlocked: true };
  p.value.state.version++;
  const damage = p.value.state.rules.damage;
  await p.advance(5000);
  assert.ok(doc.querySelector("#bossStage").classList.contains("rally-lit"));
  assert.match(doc.querySelector("#rallyTitle").textContent, /Arena lit/);
  assert.equal(p.value.state.rules.damage, damage);
  assert.equal(p.calls.filter((c) => c.options.method === "POST").length, 0);
  p.close();
});

test("host previews are exact and presets never submit a new raid", async () => {
  const p = page("boss");
  await flush();
  const doc = p.w.document;
  doc.querySelector("#bossMaxHealth").value = "1";
  doc.querySelector("#bossMaxHealth").dispatchEvent(new p.w.Event("input"));
  assert.match(doc.querySelector("#maxHealthPreview").textContent, /→ 1/);
  doc.querySelector("#bossBaseDamage").value = "9007199254740991";
  doc.querySelector("#bossBurstBonus").value = "9007199254740991";
  doc.querySelector("#bossBaseDamage").dispatchEvent(new p.w.Event("input"));
  assert.match(
    doc.querySelector("#damagePreview").textContent,
    /18,014,398,509,481,982/,
  );
  doc.querySelector("#raidPresets button").click();
  assert.equal(doc.querySelector("#bossHealthInput").value, "10000000");
  assert.equal(p.calls.filter((c) => c.options.method === "POST").length, 0);
  p.close();
});

test("private history uses text and is cleared when the admin session expires", async () => {
  const p = page("boss");
  await flush();
  const doc = p.w.document;
  p.value.state.admin_history = [
    {
      action: "Boss settings",
      actor: "Host",
      at: 1800000000,
      before: { name: "Old" },
      after: { name: "<img src=x>" },
    },
  ];
  p.value.state.version++;
  await p.advance(5000);
  assert.match(
    doc.querySelector("#bossAdminHistory").textContent,
    /<img src=x>/,
  );
  assert.equal(doc.querySelector("#bossAdminHistory img"), null);
  p.respond(async () => response({ error: "Expired" }, 401));
  await p.advance(5000);
  assert.doesNotMatch(
    doc.querySelector("#bossAdminHistory").textContent,
    /<img src=x>/,
  );
  assert.match(doc.querySelector("#bossAdminHistory").textContent, /Sign in/);
  p.close();
});

test("last checked ages between polls and exact totals remain available", async () => {
  const p = page();
  await flush();
  const doc = p.w.document;
  await p.advance(2000);
  assert.match(
    doc.querySelector("#bossConnection").textContent,
    /Last checked 2s ago/,
  );
  assert.match(doc.querySelector("#bossHealth").textContent, /2.4M/);
  assert.match(doc.querySelector("#exactRaidTotals").textContent, /2,400,000/);
  p.close();
});

test("a committed username revision wins over an older request timestamp", async () => {
  const p = page();
  await flush();
  const doc = p.w.document;
  doc.querySelector("#editPlayerName").click();
  doc.querySelector("#playerUsername").value = "SavedWithoutReset";
  doc.querySelector("#playerUsername").dispatchEvent(new p.w.Event("input"));
  p.respond(async (url) => {
    if (url.endsWith("/profile")) {
      p.value.state.version++;
      p.value.state.server_time -= 1;
      p.value.state.you.display_name = "SavedWithoutReset";
      p.value.state.you.identity_ready = true;
    }
    return response(p.value);
  });
  doc
    .querySelector("#playerNameForm")
    .dispatchEvent(new p.w.Event("submit", { cancelable: true }));
  await flush();
  assert.equal(
    doc.querySelector("#playingAs").textContent,
    "SavedWithoutReset",
  );
  assert.equal(doc.querySelector("#playerNameForm").hidden, true);
  assert.equal(doc.querySelector("#attackButton").disabled, false);
  p.close();
});

test("a delayed pre-save poll cannot replace the confirmed player name", async () => {
  const p = page();
  await flush();
  const doc = p.w.document;
  const old = structuredClone(p.value);
  let release;
  p.respond(async (url) => {
    if (url.endsWith("/profile")) {
      p.value.state.version++;
      p.value.state.you.display_name = "LatestName";
      return response(p.value);
    }
    return new Promise((resolve) => {
      release = () => resolve(response(old));
    });
  });
  await p.advance(5000);
  assert.equal(typeof release, "function");
  doc.querySelector("#editPlayerName").click();
  doc.querySelector("#playerUsername").value = "LatestName";
  doc
    .querySelector("#playerNameForm")
    .dispatchEvent(new p.w.Event("submit", { cancelable: true }));
  await flush();
  release();
  await flush();
  assert.equal(doc.querySelector("#playingAs").textContent, "LatestName");
  assert.equal(doc.querySelector("#playerNameForm").hidden, true);
  p.close();
});

test("player writes briefly disable attacks without clearing a saved identity", async () => {
  const p = page();
  await flush();
  const doc = p.w.document;
  let finish;
  p.respond(
    async () =>
      new Promise((resolve) => {
        finish = () => resolve(response(p.value));
      }),
  );
  doc.querySelector("#makeRecoveryCode").click();
  await flush();
  assert.equal(doc.querySelector("#attackButton").disabled, true);
  assert.match(doc.querySelector("#playingAs").textContent, /FixtureRaider/);
  finish();
  await flush();
  assert.equal(doc.querySelector("#attackButton").disabled, false);
  p.close();
});
```

## tests/test_comfort_update.py

```python
"""Behavioral checks for player recovery, file durability and uncapped fairness."""
import copy
import hashlib
import json
import os
from pathlib import Path
import secrets
import sqlite3
import tempfile
import threading
import unittest
from unittest.mock import patch

from boss import CommunityBoss, BossError, validate_boss
from config import Config
from storage import Store, StoreError
from wager_backend import create_app


class ComfortTests(unittest.TestCase):
    def setUp(self):
        temp = tempfile.TemporaryDirectory(); self.addCleanup(temp.cleanup)
        self.root = Path(temp.name)
        env = patch.dict(os.environ, {'APP_ENV':'test', 'ADMIN_BOOTSTRAP_PASS':'test-password'}, clear=True)
        env.start(); self.addCleanup(env.stop)
        self.app = create_app(self.root, testing=True)
        self.r, self.b = self.app.extensions['runtime'], self.app.extensions['boss']
        clock = patch('boss.time.time', return_value=self.b.export()['created_at'] + 1.25)
        self.clock = clock.start(); self.addCleanup(clock.stop)

    def player(self, name=None, ip='192.0.2.1'):
        c = self.app.test_client(); c.environ_base['REMOTE_ADDR'] = ip
        v = c.get('/play/api/state').json
        if name: self.assertEqual(self.post(c, '/play/api/profile', username=name).status_code, 200)
        return c

    def post(self, c, path, **body):
        v = c.get('/play/api/state').json
        return c.post(path, json={'raid_id': v['state']['raid_id'], **body}, headers={'X-CSRF-Token': v['csrf']})

    def hit(self, c):
        v = c.get('/play/api/state').json
        return self.post(c, '/play/api/attack', style=v['state']['weakness'], request_id=secrets.token_hex(16))

    def admin(self):
        c = self.player(ip='198.51.100.1')
        with c.session_transaction() as s: s.update(user='gingrsnaps', auth_version=1)
        return c

    def action(self, c, action, **fields):
        v = c.get('/play/api/state').json
        return c.post('/admin/boss/action', data={'csrf':v['csrf'], 'raid_id':v['state']['raid_id'], 'action':action, **fields})

    def test_json_is_the_only_active_store_and_survives_restart(self):
        c = self.player('Alice'); self.hit(c)
        value = self.b.export(); before = self.r.store.admin()
        self.assertTrue((self.root/'data/state.json').is_file())
        self.assertFalse(list(self.root.rglob('*.sqlite3')))
        again = Store(Config(self.root))
        self.assertEqual(again.admin(), before)
        self.assertEqual(CommunityBoss(again).export(), value)
        self.assertEqual(json.loads((self.root/'data/state.json').read_text())['boss']['hp'], value['hp'])

    def test_failed_file_replace_rolls_back_in_memory_and_on_disk(self):
        c = self.player('Alice'); before = self.b.export(); disk = (self.root/'data/state.json').read_bytes()
        with patch('storage.os.replace', side_effect=OSError('fixture disk error')):
            response = self.hit(c)
        self.assertEqual(response.status_code, 503)
        self.assertEqual((self.root/'data/state.json').read_bytes(), disk)
        self.assertEqual(self.b.export(), before)
        self.assertFalse(list((self.root/'data').glob('*.tmp')))
        self.assertEqual(self.hit(c).status_code, 200)

    def test_corrupt_saved_json_never_resets_accounts(self):
        path = self.root/'data/state.json'; path.write_text('{broken', encoding='utf-8')
        with self.assertRaises(RuntimeError): Store(Config(self.root))
        self.assertEqual(path.read_text(), '{broken')

    def test_sqlite_migration_preserves_entire_saved_state_and_original_file(self):
        c = self.player('Alice'); self.hit(c)
        old = self.b.export(); admin = self.r.store.admin()
        target = self.root/'old-install'; (target/'data').mkdir(parents=True)
        path = target/'data/redhunllef.sqlite3'
        with sqlite3.connect(path) as db:
            db.execute('CREATE TABLE rh_admin (name TEXT, revision INTEGER, document TEXT)')
            db.execute('CREATE TABLE rh_live (name TEXT, service TEXT, document TEXT)')
            db.execute('CREATE TABLE rh_boss (name TEXT, document TEXT)')
            db.execute('INSERT INTO rh_admin VALUES (?, ?, ?)', ('redhunllef', admin[0], json.dumps(admin[1])))
            db.execute('INSERT INTO rh_live VALUES (?, ?, ?)', ('redhunllef', 'shuffle', json.dumps(self.r.shuffle)))
            db.execute('INSERT INTO rh_boss VALUES (?, ?)', ('redhunllef', json.dumps(old)))
        original = path.read_bytes()
        migrated = Store(Config(target))
        self.assertEqual(migrated.admin(), admin)
        self.assertEqual(CommunityBoss(migrated).export(), old)
        self.assertEqual(migrated.live('shuffle'), self.r.shuffle)
        self.assertEqual(path.read_bytes(), original)
        self.assertTrue((target/'data/state.json').exists())

    def test_two_store_instances_do_not_lose_concurrent_damage(self):
        other = CommunityBoss(Store(Config(self.root)))
        raid = self.b.status()['raid_id']; errors = []
        def attack(i):
            try: (self.b if i % 2 else other).attack(str(i), f'192.0.2.{i+1}', 'blade', raid, secrets.token_hex(16))
            except Exception as exc: errors.append(exc)
        workers = [threading.Thread(target=attack, args=(i,)) for i in range(12)]
        for t in workers: t.start()
        for t in workers: t.join(10)
        self.assertFalse(errors)
        state = self.b.export()
        self.assertEqual(state['total_attacks'], 12)
        validate_boss(state)

    def test_owner_recovery_retains_cookie_identity_receipts_and_badges(self):
        a = self.player('Alice'); hit = self.hit(a).json
        code_response = self.post(a, '/play/api/recovery-code')
        self.assertEqual(code_response.status_code, 200)
        code = code_response.json['code']
        disk = (self.root/'data/state.json').read_text()
        self.assertNotIn(code, disk)
        b = self.player(); recovered = self.post(b, '/play/api/recover', code=code)
        self.assertEqual(recovered.status_code, 200)
        you = recovered.json['state']['you']
        self.assertEqual(you['name'], hit['state']['you']['name'])
        self.assertEqual(you['damage'], hit['hit']['damage'])
        self.assertEqual(you['badges'], hit['state']['you']['badges'])
        self.assertEqual(self.hit(b).status_code, 429)
        self.clock.return_value += 30
        self.assertEqual(self.hit(b).status_code, 200)
        self.assertEqual(len(self.b.export()['players']), 1)
        public = self.player(ip='192.0.2.8').get('/play/api/state').text
        self.assertNotIn('Alice', public); self.assertNotIn('recovery_hash', public)
        with self.assertRaises(BossError): self.b.save_recovery('other', hashlib.sha256(b'bad').hexdigest())

    def test_recovery_rotation_forgery_csrf_and_other_connections(self):
        a = self.player('Alice'); code = self.post(a, '/play/api/recovery-code').json['code']
        self.assertEqual(a.post('/play/api/recovery-code').status_code, 400)
        b = self.player(ip='192.0.2.2')
        self.assertEqual(self.post(b, '/play/api/recover', code=code+'x').status_code, 400)
        self.clock.return_value += 30
        new = self.post(a, '/play/api/recovery-code').json['code']
        self.assertEqual(self.post(b, '/play/api/recover', code=code).status_code, 400)
        self.assertEqual(self.post(b, '/play/api/recover', code=new).status_code, 200)
        self.assertEqual(b.get('/play/api/state').json['state']['you']['display_name'], 'Alice')

    def test_household_approvals_are_retired_and_per_player_cooldowns_remain(self):
        a = self.player('Alice'); b = self.player(); host = self.admin()
        self.assertEqual(self.post(b, '/play/api/profile', username='Bob').status_code, 200)
        self.assertEqual(self.action(b, 'household', player_name='Alice', slots='2').status_code, 302)
        self.assertEqual(self.action(host, 'household', player_name='Alice', slots='2').status_code, 422)
        self.assertEqual(self.post(b, '/play/api/profile', username='Bob').status_code, 200)
        self.assertEqual(self.hit(a).status_code, 200); self.assertEqual(self.hit(b).status_code, 200)
        self.assertEqual(self.hit(a).status_code, 429); self.assertEqual(self.hit(b).status_code, 429)
        c = self.player(); self.assertEqual(self.post(c, '/play/api/profile', username='Charlie').status_code, 200)
        self.assertEqual(self.action(host, 'household', player_name='Alice', slots='1').status_code, 422)
        validate_boss(self.b.export())
        public = c.get('/play/api/state').text
        for secret in ('Alice', 'Bob', 'households', 'admin_history'): self.assertNotIn(secret, public)
        self.clock.return_value += 30
        self.assertEqual(self.hit(a).status_code, 200); self.assertEqual(self.hit(b).status_code, 200)

    def test_rejected_flood_is_throttled_but_eligible_hits_are_never_capped(self):
        c = self.player('Alice'); self.hit(c)
        for _ in range(13): last = self.hit(c)
        self.assertEqual(last.status_code, 429)
        self.assertEqual(last.json['code'], 'request_throttle')
        host = self.admin(); flags = host.get('/admin/boss/status').json['state']['abuse_flags']
        self.assertEqual(len(flags), 1)
        self.assertEqual(flags[0]['category'], 'attack')
        self.assertNotIn('192.0.2.1', json.dumps(flags))
        self.clock.return_value += 30
        self.assertEqual(self.hit(c).status_code, 200)  # Still inside the abuse window.
        for _ in range(120):
            self.clock.return_value += 30
            self.assertEqual(self.hit(c).status_code, 200)
        self.assertIsNone(c.get('/play/api/state').json['state']['rules']['daily_attacks'])
        self.assertNotIn('abuse_flags', c.get('/play/api/state').text)

    def test_rapid_registration_rejections_throttle_without_banning(self):
        c = self.player()
        for _ in range(21): response = self.post(c, '/play/api/profile', username='')
        self.assertEqual(response.status_code, 429)
        self.assertEqual(response.json['code'], 'request_throttle')
        self.assertEqual(self.r.admin['banned_ips'], [])

    def test_rally_counts_distinct_recent_players_and_changes_no_combat_rules(self):
        raid = self.b.status()['raid_id']; start = self.clock.return_value
        for i in range(14): self.b.attack(str(i), f'192.0.2.{i+1}', 'blade', raid, secrets.token_hex(16))
        self.assertEqual(self.b.status()['rally']['count'], 14)
        self.clock.return_value += 30
        self.b.attack('0', '192.0.2.1', 'blade', raid, secrets.token_hex(16))
        self.assertFalse(self.b.status()['rally']['unlocked'])
        self.b.attack('last', '192.0.2.99', 'blade', raid, secrets.token_hex(16))
        v = self.b.status(); self.assertTrue(v['rally']['unlocked']); hp = v['hp']
        self.clock.return_value = start + 86400
        self.assertTrue(self.b.status()['rally']['unlocked']); self.assertEqual(self.b.status()['hp'], hp)
        self.assertEqual(v['rules']['damage'], 100)
        self.b.control('restart', raid)
        self.assertFalse(self.b.status()['rally']['unlocked'])

    def test_rally_expiry_and_admin_pace_do_not_adjust_health(self):
        raid = self.b.status()['raid_id']
        for i in range(11):
            self.b.attack(str(i), f'192.0.2.{i+1}', 'blade', raid, secrets.token_hex(16))
            self.clock.return_value += 30
        old = self.b.export(); view = self.b.admin_status()
        self.assertTrue(view['balance']['observed'])
        self.assertEqual([p['days'] for p in view['balance']['presets']], [3,5,7])
        self.assertEqual(self.b.export(), old)
        self.clock.return_value += 601
        self.assertEqual(self.b.status()['rally']['count'], 0)
        self.assertEqual(self.b.status()['hp'], old['hp'])

    def test_admin_history_is_atomic_persistent_and_not_public(self):
        host = self.admin(); player = self.player('Alice')
        self.assertEqual(self.action(host, 'settings', settings_revision=0, boss_name='Ruby', base_damage=12, weak_damage=23, burst_bonus=34).status_code, 303)
        self.assertEqual(self.action(host, 'remaining_health', health=12345, health_revision=0, confirm_health='yes').status_code, 303)
        records = self.b.admin_status()['admin_history']
        self.assertEqual(records[0]['actor'], 'gingrsnaps'); self.assertEqual(records[0]['after']['hp'], 12345)
        self.assertEqual(records[1]['after']['name'], 'Ruby')
        self.assertEqual(CommunityBoss(Store(Config(self.root))).admin_status()['admin_history'], records)
        self.assertNotIn('admin_history', player.get('/play/api/state').text)
        self.assertEqual(self.action(player, 'pause').status_code, 302)
        self.assertEqual(self.b.admin_status()['admin_history'], records)
        validate_boss(self.b.export())

    def test_source_checks_and_content_changes_have_separate_times(self):
        from race import empty
        now = int(self.clock.return_value)
        admin = copy.deepcopy(self.r.admin); admin['site_settings'].update(start_time=now-100, end_time=now+10000)
        self.r.commit(admin, self.r.revision, snapshot=empty(admin['site_settings']))
        rows = [dict(username='Test', weightedWagerAmount='100', wagerAmount='150', campaignCode='Red')]
        with patch.object(self.r.providers, 'shuffle', return_value=rows): self.r.check('shuffle')
        first = self.r.job_status()['shuffle']
        self.clock.return_value += 60
        with patch.object(self.r.providers, 'shuffle', return_value=rows): self.r.check('shuffle')
        second = self.r.job_status()['shuffle']
        self.assertGreater(second['last_success'], first['last_success'])
        self.assertEqual(second['changed_at'], first['changed_at'])
        rows[0]['weightedWagerAmount'] = '200'; self.clock.return_value += 60
        with patch.object(self.r.providers, 'shuffle', return_value=rows): self.r.check('shuffle')
        self.assertGreater(self.r.job_status()['shuffle']['changed_at'], first['changed_at'])


if __name__ == '__main__': unittest.main()
```

## tests/test_community.py

```python
"""Regressions for community polish, reviewed publication and recovery metadata."""
import copy
import io
import json
from pathlib import Path
import re
import secrets
import tempfile
import unittest
from unittest.mock import patch

import test_app as support
from boss import CommunityBoss, DAY, fresh_raid, validate_boss
from wager_backend import create_app


class CommunityTests(unittest.TestCase):
    setUp = support.AppTests.setUp
    form = support.AppTests.form
    schedule = support.AppTests.schedule

    def hit(self, guest='community-test', ip='192.0.2.9'):
        boss = self.app.extensions['boss']
        state = boss.status(guest, ip)
        return boss.attack(guest, ip, state['weakness'], state['raid_id'], secrets.token_hex(16))

    def test_conditional_public_snapshot_and_private_cache_boundaries(self):
        first = self.client.get('/public-state')
        self.assertEqual(first.status_code, 200)
        self.assertEqual(first.headers['Cache-Control'], 'public, no-cache')
        self.assertNotIn('server_time', first.json)
        self.assertNotIn('you', first.json['boss'])
        self.assertNotIn('csrf', first.json)
        with patch('runtime.time.time', return_value=float(first.headers['X-Server-Time']) + 1):
            unchanged = self.client.get('/public-state', headers={'If-None-Match': first.headers['ETag']})
        self.assertEqual(unchanged.status_code, 304)
        self.assertEqual(unchanged.data, b'')
        self.assertGreater(float(unchanged.headers['X-Server-Time']), float(first.headers['X-Server-Time']))
        self.hit()
        changed = self.client.get('/public-state', headers={'If-None-Match': first.headers['ETag']})
        self.assertEqual(changed.status_code, 200)
        self.assertNotEqual(first.headers['ETag'], changed.headers['ETag'])
        for url in ('/play/api/state', '/admin/status', '/admin/recovery-backup'):
            response = self.client.get(url)
            self.assertEqual(response.headers['Cache-Control'], 'no-store')
            self.assertNotIn('ETag', response.headers)

    def test_review_signature_requires_the_exact_reviewed_changes(self):
        self.schedule()
        original = copy.deepcopy(self.r.admin)
        revision = self.r.revision
        form = dict(self.form(), csrf='test-token', action='save_race', revision=revision,
                    race_title='The new community race', prize_1='1801', sponsor_url='https://example.test/sponsor')
        preview = self.client.post('/admin/action', data=form)
        self.assertEqual(preview.status_code, 200)
        for label in ('Race title', 'Place 1 prize', 'Sponsor link'):
            self.assertIn(label, preview.text)
        review = re.search('name="review_token" value="([^"]+)"', preview.text).group(1)
        tampered = self.client.post('/admin/action', data={**form, 'confirm_race':'yes', 'review_token':review, 'prize_1':'1901'})
        self.assertEqual(tampered.status_code, 200)
        self.assertEqual(self.r.revision, revision)
        self.assertEqual(self.r.admin, original)
        confirmed = self.client.post('/admin/action', data={**form, 'confirm_race':'yes', 'review_token':review})
        self.assertEqual(confirmed.status_code, 303)
        self.assertEqual(self.r.revision, revision + 1)
        self.assertEqual(self.r.admin['site_settings']['prizes']['1'], '1801')

    def test_badges_reward_real_hits_and_distinct_raid_days(self):
        boss = self.app.extensions['boss']
        with patch('boss.time.time', return_value=1_800_000_000) as clock:
            for hit in range(100):
                clock.return_value = 1_800_000_000 + (hit // 40) * DAY + (hit % 40) * 60
                result = self.hit()
            state = result['state']
            self.assertEqual(state['you']['active_days'], 3)
            self.assertEqual(state['you']['attacks'], 100)
            self.assertTrue(all(badge['earned'] for badge in state['you']['badges'] if badge['id'] in {'first', 'burst', 'loyal'}))
            self.assertEqual(len(state['you']['badges']), 8)
            self.assertEqual(state['total_damage'], 16_000)
            self.assertIsNone(state['rules']['daily_attacks'])
            self.assertEqual(state['rules']['cooldown'], 30)
        validate_boss(boss.export())

    def test_legacy_raid_migration_keeps_progress_and_counts_only_known_days(self):
        boss = self.app.extensions['boss']
        with patch('boss.time.time', return_value=1_800_000_000) as clock:
            self.hit()
            old = boss.export()
            for player in old['players'].values():
                player.pop('active_days')
            with self.r.store.connection(transaction=True) as conn:
                boss._write(conn, old)
            restored = CommunityBoss(self.r.store)
            self.assertEqual(restored.export(), old)
            self.app.extensions['boss'] = restored
            clock.return_value += DAY
            state = self.hit()['state']
            self.assertEqual(state['you']['active_days'], 2)
            self.assertEqual(state['you']['damage'], 300)
            self.assertFalse(next(b for b in state['you']['badges'] if b['id'] == 'loyal')['earned'])

    def test_milestones_and_victory_recap_include_every_contributor(self):
        boss = self.app.extensions['boss']
        raid = fresh_raid(health=1650)
        with self.r.store.connection(transaction=True) as conn:
            boss._write(conn, raid, new_raid=True)
        boss.loaded_at = 0
        url = '/play/api/contributors?raid_id=' + raid['id']
        self.assertEqual(self.client.get(url).status_code, 409)
        for index in range(11):
            state = self.hit(str(index), f'192.0.2.{index + 1}')['state']
            if index == 2:
                self.assertEqual([m['percent'] for m in state['milestones'] if m['reached']], [25])
        self.assertTrue(all(m['reached'] for m in state['milestones']))
        result = self.client.get(url)
        self.assertEqual(result.status_code, 200)
        self.assertEqual(len(result.json['contributors']), 11)
        self.assertTrue(all(set(row) == {'name', 'damage', 'attacks'} for row in result.json['contributors']))
        self.assertEqual(self.client.get('/play/api/contributors?raid_id=old-raid').status_code, 409)

    def test_recovery_export_tracks_changes_without_invalidating_admin_forms(self):
        before = self.r.store.admin()
        recovery = self.client.get('/admin/recovery-backup').json
        self.assertEqual(self.r.store.admin(), before)
        self.assertEqual(self.r.store.checkpoint(), recovery['recovery_export'])
        self.assertFalse(self.client.get('/admin/status').json['checkpoint']['changes'])
        self.hit()
        status = self.client.get('/admin/status').json['checkpoint']
        self.assertEqual(status['attacks'], 1)
        self.assertEqual(status['damage'], 150)
        self.assertTrue(status['changes'])

    def test_private_recovery_review_validates_without_changing_live_state(self):
        self.hit()
        recovery = self.client.get('/admin/recovery-backup').json
        before = self.r.store.admin(), self.app.extensions['boss'].export()
        response = self.client.post('/admin/recovery-preview', data={
            'csrf':'test-token', 'recovery':(io.BytesIO(json.dumps(recovery).encode()), 'recovery.json')})
        self.assertEqual(response.status_code, 200)
        self.assertIn('Validated recovery file', response.text)
        self.assertIn('1 raiders', response.text)
        self.assertNotIn(recovery['users']['gingrsnaps']['pw_hash'], response.text)
        self.assertEqual((self.r.store.admin(), self.app.extensions['boss'].export()), before)
        invalid = self.client.post('/admin/recovery-preview', data={
            'csrf':'test-token', 'recovery':(io.BytesIO(b'{bad json'), 'bad.json')})
        self.assertEqual(invalid.status_code, 422)
        self.assertEqual(self.client.post('/admin/recovery-preview').status_code, 400)
        self.assertEqual(self.app.test_client().post('/admin/recovery-preview').status_code, 302)

    def test_recovered_metadata_survives_import_and_malformed_metadata_is_ignored(self):
        self.hit()
        recovery = self.client.get('/admin/recovery-backup').json
        for malformed in (False, True):
            with self.subTest(malformed=malformed), tempfile.TemporaryDirectory() as directory:
                value = copy.deepcopy(recovery)
                if malformed:
                    value['recovery_export']['attacks'] = 'untrusted number'
                root = Path(directory)
                (root / 'private').mkdir()
                (root / 'private/recovery.seed.json').write_text(json.dumps(value), encoding='utf-8')
                restored = create_app(root, testing=True)
                try:
                    store = restored.extensions['runtime'].store
                    self.assertEqual(restored.extensions['boss'].export(), recovery['community_boss'])
                    self.assertEqual(store.checkpoint(), None if malformed else recovery['recovery_export'])
                finally:
                    restored.extensions['runtime'].store.close()


if __name__ == '__main__':
    unittest.main()
```

## tests/test_frontend.cjs

```javascript
/* Optional development checks. The deployed app does not use Node or jsdom. */
const {test} = require('node:test');
const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');
const {JSDOM, VirtualConsole} = require('jsdom');
const root = path.resolve(__dirname, '..');
const fixtures = process.env.DOM_FIXTURES || path.join(root, '.test-fixtures');
const code = fs.readFileSync(path.join(root, 'static/app.js'), 'utf8');
const data = name => JSON.parse(fs.readFileSync(path.join(fixtures, name+'.json'), 'utf8'));
const flush = async () => {for (let n=0; n<5; n++) await new Promise(resolve=>setImmediate(resolve));};

function page(name, feed=data(name==='public'?'public':'admin')) {
  const errors=[];
  const console = new VirtualConsole().on('jsdomError', error=>errors.push(error.message));
  const dom = new JSDOM(fs.readFileSync(path.join(fixtures,name+'.html'),'utf8'), {
    url:'https://example.test/'+(name==='public'?'':'admin?tab='+name), runScripts:'outside-only', virtualConsole:console,
  });
  const window=dom.window, calls=[], timers=new Map(), intervals=new Map();
  let now=feed.server_time*1000, serial=0;
  window.Date.now=()=>now;
  Object.defineProperty(window.document,'hidden',{value:false,configurable:true});
  window.setTimeout=(fn,delay)=>{const id=++serial;timers.set(id,{fn,at:now+delay,delay});return id;};
  window.clearTimeout=id=>timers.delete(id);
  window.setInterval=(fn,delay)=>{const id=++serial;intervals.set(id,{fn,delay});return id;};
  window.clearInterval=id=>intervals.delete(id);
  let responder=async()=>({status:200,ok:true,headers:new Map([['content-type','application/json']]),json:async()=>structuredClone(feed)});
  window.fetch=async(url,options)=>{calls.push({url:String(url),options,at:now});return responder(url,options);};
  window.confirm=()=>true;
  window.eval(code);
  return {window, dom, calls, errors, feed, timers, intervals,
    respond(fn){responder=fn;},
    async advance(ms){now+=ms;for(const [id,timer] of [...timers])if(timer.at<=now){timers.delete(id);timer.fn();}await flush();},
    async tick(){for(const timer of intervals.values())timer.fn();await flush();},
    close(){dom.window.close();},
  };
}

for(const name of ['public','login','overview','race','players','boss','settings','error']) {
  test(name+' has unique IDs, connected labels, and no script errors',async()=>{
    const p=page(name);await flush();
    const ids=[...p.window.document.querySelectorAll('[id]')].map(node=>node.id);
    assert.equal(new Set(ids).size,ids.length,'Duplicate element ID');
    for(const label of p.window.document.querySelectorAll('label[for]'))assert.ok(p.window.document.getElementById(label.htmlFor));
    assert.equal(p.window.document.querySelectorAll('main').length,1);
    assert.deepEqual(p.errors,[]);p.close();
  });
}

test('public and admin automatically poll at the 60-second cadence',async()=>{
  for(const name of ['public','overview']) {
    const p=page(name);await flush();assert.equal(p.calls.length,1);
    await p.advance(60000);await p.advance(60000);
    assert.deepEqual(p.calls.map(c=>c.at-p.calls[0].at),[0,60000,120000]);p.close();
  }
});

test('repeated refreshes preserve the dashboard and unsaved race draft',async()=>{
  const p=page('race');await flush();
  const form=p.window.document.getElementById('raceForm'),field=form.querySelector('[name=race_title]');
  field.value='My unsaved race title';field.dispatchEvent(new p.window.Event('input',{bubbles:true}));
  for(let i=0;i<4;i++){p.feed.site.race_title='Saved title '+i;await p.advance(60000);}
  assert.strictEqual(p.window.document.getElementById('raceForm'),form);
  assert.equal(field.value,'My unsaved race title');assert.ok(p.window.document.body.textContent.includes('Race'));
  assert.notEqual(p.window.document.body.textContent.trim().toLowerCase(),'not yet');
  assert.deepEqual(p.errors,[]);p.close();
});

test('Code Red expands, searches, updates, and renders usernames as text',async()=>{
  const p=page('players');await flush();
  const details=p.window.document.getElementById('codeRed');details.open=true;
  details.dispatchEvent(new p.window.Event('toggle'));await flush();
  assert.ok(p.calls.at(-1).url.includes('code_red=1'));
  assert.equal(p.window.document.querySelectorAll('#redBody tr').length,100);
  assert.equal(p.window.document.querySelectorAll('#redBody img,#participantsBody img').length,0);
  const search=p.window.document.getElementById('redSearch');search.value='ExamplePlayer010';
  search.dispatchEvent(new p.window.Event('input'));
  assert.equal(p.window.document.querySelectorAll('#redBody tr:not([hidden])').length,1);
  p.feed.red[0].weighted='$555.00';await p.advance(60000);
  assert.equal(search.value,'ExamplePlayer010');assert.equal(details.open,true);
  assert.equal(p.window.document.querySelectorAll('#redBody tr:not([hidden])').length,1);p.close();
});

test('session and proxy errors retain rendered content and retry',async()=>{
  const p=page('players');await flush();const html=p.window.document.getElementById('participantsBody').innerHTML;
  p.respond(async()=>({status:401,ok:false}));await p.advance(60000);
  assert.match(p.window.document.getElementById('networkError').textContent,/session expired/);
  assert.equal(p.window.document.getElementById('participantsBody').innerHTML,html);
  p.respond(async()=>({status:502,ok:false,headers:new Map([['content-type','text/html']])}));await p.advance(60000);
  assert.match(p.window.document.getElementById('networkError').textContent,/HTTP 502/);
  assert.equal(p.window.document.getElementById('participantsBody').innerHTML,html);assert.equal(p.calls.length,3);p.close();
});

test('race state transitions use the server clock without waiting for polling',async()=>{
  const feed=data('public');feed.site.start_time=feed.server_time+10;feed.site.end_time=feed.server_time+20;
  const p=page('public',feed);await flush();assert.equal(p.window.document.getElementById('raceBadge').textContent,'Upcoming');
  await p.advance(11000);await p.tick();assert.equal(p.window.document.getElementById('raceBadge').textContent,'Active');
  await p.advance(10000);await p.tick();assert.equal(p.window.document.getElementById('raceBadge').textContent,'Ended');p.close();
});

test('manual check polls quickly then returns to the minute cadence',async()=>{
  const p=page('overview');await flush();let post=false;
  p.respond(async(url,options)=>{
    const value=options.method==='POST'?(post=true,{message:'Check queued'}):p.feed;
    return {status:200,ok:true,headers:new Map([['content-type','application/json']]),json:async()=>structuredClone(value)};
  });
  p.feed.jobs.shuffle.state='queued';
  p.window.document.querySelector('[data-refresh]').dispatchEvent(new p.window.Event('submit',{cancelable:true,bubbles:true}));await flush();
  assert.equal(post,true);const first=p.calls.length;await p.advance(2000);assert.equal(p.calls.length,first+1);
  p.feed.jobs.shuffle.state='scheduled';p.feed.jobs.kick.state='scheduled';await p.advance(2000);
  await p.advance(56000);assert.equal(p.calls.at(-1).at-p.calls[0].at,60000);p.close();
});

test('a named action control cannot redirect a refresh to the wrong URL',async()=>{
  const p=page('overview');await flush();
  try {
    for(const form of p.window.document.querySelectorAll('[data-refresh]')) {
      // jsdom omits this native-browser named-property behavior. Model the
      // actual input collision explicitly, then verify the request destination.
      const control=form.querySelector('[name="action"]');
      Object.defineProperty(form,'action',{configurable:true,value:control});
      p.respond(async(url,options)=>{
        const valid=options.method!=='POST'||new URL(String(url),p.window.location.href).pathname==='/admin/action';
        return {status:valid?200:404,ok:valid,headers:new Map([['content-type',valid?'application/json':'text/html']]),
          json:async()=>structuredClone(options.method==='POST'?{message:'Check requested'}:p.feed)};
      });
      form.dispatchEvent(new p.window.Event('submit',{cancelable:true,bubbles:true}));await flush();
      const sent=p.calls.filter(call=>call.options.method==='POST').at(-1);
      assert.equal(new URL(sent.url,p.window.location.href).pathname,'/admin/action');
      assert.equal(sent.options.body.get('action'),'refresh');
      assert.equal(sent.options.body.get('csrf'),'fixture-csrf');
      assert.equal(sent.options.headers.Accept,'application/json');
      assert.equal(form.querySelector('button').disabled,false);
      assert.match(p.window.document.getElementById('toast').textContent,/Check requested/);
    }
  } finally {p.close();}
});

test('refresh explains a rejected form and re-enables the button',async()=>{
  const p=page('overview');await flush();
  try {
    p.respond(async()=>({status:400,ok:false,headers:new Map([['content-type','application/json']]),
      json:async()=>({error:'This form expired. Reload the page and try again.'})}));
    const form=p.window.document.querySelector('[data-refresh]');
    form.dispatchEvent(new p.window.Event('submit',{cancelable:true,bubbles:true}));await flush();
    assert.match(p.window.document.getElementById('toast').textContent,/form expired.*HTTP 400/);
    assert.equal(form.querySelector('button').disabled,false);
  } finally {p.close();}
});

test('empty-board explanation clears when live rows arrive on either page',async()=>{
  for(const name of ['public','players']) {
    const feed=data(name==='public'?'public':'admin');
    const values=structuredClone(name==='public'?feed.rows:feed.participants);
    feed.rows=[];feed.participants=[];feed.leaderboard_message='Waiting for Shuffle data.';
    const p=page(name,feed);await flush();
    try {
      const message=p.window.document.getElementById('leaderboardMessage');
      assert.equal(message.hidden,false);assert.match(message.textContent,/Waiting for Shuffle/);
      feed.leaderboard_message='';if(name==='public')feed.rows=values;else feed.participants=values;
      await p.advance(60000);
      assert.equal(message.hidden,true);
      if(name==='public')assert.equal(p.window.document.querySelector('[data-rank="1"] [data-name]').textContent,values[0].username);
      else assert.equal(p.window.document.querySelector('#participantsBody strong').textContent,values[0].username);
    } finally {p.close();}
  }
});

test('stylesheet parses and includes responsive and reduced-motion rules',()=>{
  const css=fs.readFileSync(path.join(root,'static/style.css'),'utf8');
  const parsed=require('rrweb-cssom').parse(css);
  assert.ok(parsed.cssRules.length>50);assert.match(css,/prefers-reduced-motion/);assert.match(css,/@media/);
});

test('publishing dates automatically follows queued work and shows the saved window',async()=>{
  const feed=data('admin');
  Object.assign(feed.jobs.shuffle,{state:'queued',pending:true,requested:1,completed:0,next_check:feed.server_time});
  const p=page('race',feed);await flush();
  try {
    assert.match(p.window.document.getElementById('shuffleProgress').textContent,/Refresh queued/);
    const published=p.window.document.getElementById('publishedWindow').textContent;
    const field=p.window.document.querySelector('[name="start_et"]');
    field.value='2030-01-01T18:00';field.dispatchEvent(new p.window.Event('input',{bubbles:true}));
    Object.assign(feed.jobs.shuffle,{state:'checking',pending:false,runs:1});
    await p.advance(2000);
    assert.equal(p.calls.length,2);assert.match(p.window.document.getElementById('shuffleProgress').textContent,/Checking the provider now/);
    Object.assign(feed.jobs.shuffle,{state:'scheduled',completed:1,result:'updated',completed_at:feed.server_time+3,next_check:feed.server_time+60});
    await p.advance(2000);
    assert.match(p.window.document.getElementById('shuffleProgress').textContent,new RegExp('Published '+feed.count+' qualifying players'));
    assert.equal(p.window.document.getElementById('publishedWindow').textContent,published);
    assert.equal(field.value,'2030-01-01T18:00');
    assert.equal(p.calls.filter(c=>c.options.method==='POST').length,0);
  } finally {p.close();}
});

test('a queued provider retry shows both its reason and the scheduled time on every tab',async()=>{
  for(const name of ['overview','race','players','settings']) {
    const feed=data('admin');
    Object.assign(feed.jobs.shuffle,{state:'queued',pending:true,requested:1,completed:0,
      next_check:feed.server_time+120,error:'Shuffle rate limit reached.',http_status:429,retry_after:120});
    const p=page(name,feed);await flush();
    try {
      const message=p.window.document.getElementById('shuffleProgress').textContent;
      assert.match(message,/Retry scheduled/);assert.match(message,/HTTP 429/);assert.match(message,/rate limit/);
      await p.advance(2000);assert.equal(p.calls.length,1,'Respect the provider cooldown without fast browser polling');
    } finally {p.close();}
  }
});

test('a manual refresh during an in-flight status read schedules an immediate follow-up',async()=>{
  const p=page('overview');await flush();
  try {
    let release, held=false;
    p.respond(async(url,options)=>{
      if(options.method!=='POST'&&!held) {held=true;return new Promise(resolve=>{release=resolve;});}
      const value=options.method==='POST'?{message:'Refresh queued',runtime_id:p.feed.runtime_id,requests:{shuffle:1}}:p.feed;
      return {status:200,ok:true,headers:new Map([['content-type','application/json']]),json:async()=>structuredClone(value)};
    });
    await p.advance(60000);assert.equal(held,true);
    p.window.document.querySelector('[data-refresh]').dispatchEvent(new p.window.Event('submit',{cancelable:true,bubbles:true}));await flush();
    release({status:200,ok:true,headers:new Map([['content-type','application/json']]),json:async()=>structuredClone(p.feed)});await flush();
    const before=p.calls.length;await p.advance(50);assert.equal(p.calls.length,before+1);
    Object.assign(p.feed.jobs.shuffle,{completed:1,result:'updated',completed_at:p.feed.server_time+61});
    await p.advance(60000);
    assert.match(p.window.document.getElementById('toast').textContent,/Refresh finished\. See the update result/);
  } finally {p.close();}
});

test('conditional public updates reuse the cached body and take a fresh server clock',async()=>{
  const p=page('public');await flush();let reads=0;
  const payload=structuredClone(p.feed);delete payload.server_time;
  p.respond(async()=>{
    reads++;
    return reads===1?{status:200,ok:true,headers:new Map([['content-type','application/json'],['ETag','"same-public-state"'],['X-Server-Time',String(p.feed.server_time+60)]]),json:async()=>payload}:
      {status:304,ok:false,headers:new Map([['ETag','"same-public-state"'],['X-Server-Time',String(p.feed.server_time+120)]]),json:async()=>{throw Error('304 has no JSON body');}};
  });
  await p.advance(60000);const before=p.window.document.querySelector('#countdown').textContent;
  await p.advance(60000);await p.tick();
  assert.equal(p.calls.at(-1).options.headers['If-None-Match'],'"same-public-state"');
  assert.equal(p.window.document.querySelector('#networkError').hidden,true);
  assert.notEqual(p.window.document.querySelector('#countdown').textContent,before);
  assert.deepEqual(p.errors,[]);p.close();
});

test('homepage invitation follows boss health and paused or completed status',async()=>{
  const p=page('public');await flush();p.feed.boss.hp=1200000;p.feed.boss.status='paused';p.feed.boss.raiders=37;
  await p.advance(60000);
  assert.match(p.window.document.querySelector('#inviteButtonLabel').textContent,/pause|View/i);
  assert.match(p.window.document.querySelector('#inviteProgress').textContent,/37/);
  p.feed.boss.hp=0;p.feed.boss.status='victory';await p.advance(60000);
  assert.match(p.window.document.querySelector('#inviteButtonLabel').textContent,/victory/i);p.close();
});

test('homepage victory uses the configured boss name safely',async()=>{
  const p=page('public');await flush();
  p.feed.boss.name='<img src=x>';p.feed.boss.status='victory';p.feed.boss.hp=0;
  await p.advance(60000);
  const title=p.window.document.getElementById('inviteTitle');
  assert.equal(title.textContent,'The crew conquered <img src=x>.');
  assert.equal(title.querySelector('img'),null);p.close();
});

test('source success and last content change have separate labels',async()=>{
  const p=page('overview');await flush();
  p.feed.jobs.shuffle.last_success=p.feed.server_time;
  p.feed.jobs.shuffle.changed_at=p.feed.server_time-600;
  await p.advance(60000);await p.tick();
  const value=p.window.document.getElementById('shuffleFreshness').textContent;
  assert.match(value,/Last successful check:/);assert.match(value,/Content last changed:/);
  assert.ok(p.window.document.getElementById('shuffleProgress'));p.close();
});
```

## tests/test_player_access.py

```python
"""Real HTTP regressions for community access and persistent player names."""
from concurrent.futures import ThreadPoolExecutor
import copy
from pathlib import Path
import tempfile
import unittest

import test_comfort_update as support
from boss import CommunityBoss, validate_boss
from wager_backend import create_app


class PlayerAccessTests(unittest.TestCase):
    setUp = support.ComfortTests.setUp
    player = support.ComfortTests.player
    post = support.ComfortTests.post
    hit = support.ComfortTests.hit
    admin = support.ComfortTests.admin
    action = support.ComfortTests.action

    def test_100_players_share_one_proxy_and_all_attack_without_approvals(self):
        self.app.extensions['settings'].proxy = True
        clients = []
        for i in range(100):
            c = self.app.test_client()
            c.environ_base.update(REMOTE_ADDR='10.0.0.1', HTTP_DO_CONNECTING_IP='192.0.2.1')
            c.get('/play/api/state')
            clients.append(c)
        def register_and_hit(i):
            c = clients[i]
            registered = self.post(c, '/play/api/profile', username=f'CommunityMember{i:03}')
            if registered.status_code != 200: return ('registration', registered.status_code)
            return ('attack', self.hit(c).status_code)
        with ThreadPoolExecutor(max_workers=12) as pool:
            results = list(pool.map(register_and_hit, range(100)))
        self.assertEqual(results, [('attack', 200)] * 100)
        before = self.b.export()
        self.assertEqual(len(before['players']), 100)
        self.assertEqual(before['total_attacks'], 100)
        self.assertEqual(len(before['profiles']), 100)
        self.assertEqual(self.hit(clients[0]).status_code, 429)
        # Everybody gets their own next turn, not a shared connection cooldown.
        self.clock.return_value += 30
        with ThreadPoolExecutor(max_workers=12) as pool:
            self.assertEqual(list(pool.map(lambda c: self.hit(c).status_code, clients)), [200]*100)
        state = self.b.export()
        self.assertEqual(state['total_attacks'], 200)
        self.assertEqual(state['hp'], state['max_hp'] - state['total_damage'])
        self.assertEqual(len(state.get('households', {})), 0)
        validate_boss(state)

    def test_name_survives_ip_changes_refresh_restart_and_new_raid(self):
        c = self.player('StickyName'); self.hit(c)
        saved = self.b.export()
        for ip in ('192.0.2.2', '198.51.100.8', '2001:db8::a', '2001:db8:1::b'):
            c.environ_base['REMOTE_ADDR'] = ip
            current = c.get('/play/api/state').json['state']
            self.assertEqual(current['you']['display_name'], 'StickyName')
            self.assertTrue(current['you']['identity_ready'])
            self.assertIn('StickyName', c.get('/play').text)
            self.assertEqual(self.hit(c).status_code, 429)
        self.assertEqual(self.b.export(), saved)  # Polls do not rewrite a name or reset progress.
        rebuilt = create_app(self.root, testing=True)
        same = rebuilt.test_client()
        same.set_cookie('rh_raider', c.get_cookie('rh_raider').value)
        self.assertEqual(same.get('/play/api/state').json['state']['you']['display_name'], 'StickyName')
        self.assertEqual(rebuilt.extensions['boss'].export(), saved)
        self.clock.return_value += 30
        v = same.get('/play/api/state').json
        hit = same.post('/play/api/attack',json=dict(raid_id=v['state']['raid_id'],style='blade',request_id='retained-cookie-hit'),headers={'X-CSRF-Token':v['csrf']})
        self.assertEqual(hit.status_code, 200)
        rebuilt.extensions['boss'].control('restart', saved['id'])
        self.assertEqual(same.get('/play/api/state').json['state']['you']['display_name'], 'StickyName')
        self.assertTrue(same.get('/play/api/state').json['state']['you']['identity_ready'])

    def test_missing_or_changing_proxy_header_never_discards_a_player(self):
        self.app.extensions['settings'].proxy = True
        a = self.player('NoHeader'); self.assertEqual(self.hit(a).status_code, 200)
        a.environ_base['HTTP_DO_CONNECTING_IP'] = '192.0.2.44'
        self.assertEqual(a.get('/play/api/state').json['state']['you']['display_name'], 'NoHeader')
        a.environ_base['HTTP_DO_CONNECTING_IP'] = 'not-an-ip'
        self.clock.return_value += 30
        self.assertEqual(self.hit(a).status_code, 200)
        # The malformed header still is not trusted as a client IP.
        self.assertNotIn('not-an-ip', str(self.b.export()))

    def test_one_rejecting_browser_cannot_throttle_other_players_on_same_ip(self):
        bad = self.player()
        for _ in range(25): self.post(bad, '/play/api/profile', username='')
        self.assertEqual(self.post(bad, '/play/api/profile', username='BadClient').status_code, 429)
        for i in range(30):
            c = self.player(f'Unaffected{i}')
            self.assertEqual(self.hit(c).status_code, 200)
        self.assertEqual(self.b.export()['total_attacks'], 30)

    def test_valid_recovery_can_use_a_network_with_other_active_players(self):
        a = self.player('RecoverMe', '192.0.2.1'); self.hit(a)
        code = self.post(a, '/play/api/recovery-code').json['code']
        b = self.player('ExistingPlayer', '192.0.2.2'); self.hit(b)
        recovered = self.player(ip='192.0.2.2')
        response = self.post(recovered, '/play/api/recover', code=code)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json['state']['you']['display_name'], 'RecoverMe')
        self.assertEqual(self.hit(recovered).status_code, 429)
        self.clock.return_value += 30
        self.assertEqual(self.hit(recovered).status_code, 200)
        self.assertEqual(self.hit(b).status_code, 200)
        self.assertEqual(len(self.b.export()['players']), 2)

    def test_reloading_never_reissues_the_raider_identity_cookie(self):
        c = self.player('PersistentCookie'); cookie = c.get_cookie('rh_raider').value
        for _ in range(5):
            for path in ('/play', '/play/api/state'):
                response = c.get(path)
                self.assertFalse(any(h.startswith('rh_raider=') for h in response.headers.getlist('Set-Cookie')))
                self.assertEqual(c.get_cookie('rh_raider').value, cookie)
                self.assertIn('PersistentCookie', response.text)

    def test_legacy_network_claims_and_household_limits_do_not_require_a_reset(self):
        a = self.player('Existing'); self.hit(a)
        before = self.b.export()
        profile = next(iter(before['profiles'].values()))
        legacy = copy.deepcopy(before)
        legacy['networks'][profile['network']] = {'last_attack': self.clock.return_value + 300, 'day':0, 'used':500}
        legacy['households'] = {profile['network']:2}
        with self.r.store.connection(transaction=True) as conn: self.b._write(conn, legacy)
        self.b.loaded_at = 0
        current = self.b.export()
        self.assertEqual(current, legacy)
        for i in range(10):
            c = self.player(f'NewMember{i}'); self.assertEqual(self.hit(c).status_code, 200)
        after = self.b.export()
        pk = next(iter(before['profiles']))
        self.assertEqual(after['profiles'][pk], before['profiles'][pk])
        self.assertEqual(after['players'][pk], before['players'][pk])
        self.assertEqual(after['id'], before['id'])
        self.assertEqual(after['total_attacks'], before['total_attacks'] + 10)
        self.assertLess(after['hp'], before['hp'])
        validate_boss(after)

    def test_name_collision_does_not_give_access_to_someone_elses_profile(self):
        a = self.player('ReservedName'); self.hit(a)
        b = self.player()
        self.assertEqual(self.post(b, '/play/api/profile', username='reservedname').status_code, 409)
        self.assertEqual(self.hit(b).status_code, 409)
        self.assertNotIn('ReservedName', b.get('/play/api/state').text)
        self.assertEqual(self.post(b, '/play/api/profile', username='OwnName').status_code, 200)
        self.assertEqual(self.hit(b).status_code, 200)
        self.assertNotEqual(a.get('/play/api/state').json['state']['you']['name'], b.get('/play/api/state').json['state']['you']['name'])


if __name__ == '__main__': unittest.main()
```

## tests/test_raid_update.py

```python
"""Requested gameplay changes, identity boundaries and additive save upgrades."""
import copy
import json
import os
from pathlib import Path
import secrets
import tempfile
import unittest
from unittest.mock import patch

from boss import CommunityBoss, DAY, MAX_HP, MAX_DAMAGE, validate_boss
from wager_backend import create_app


class RaidUpdateTests(unittest.TestCase):
    def setUp(self):
        temp = tempfile.TemporaryDirectory(); self.addCleanup(temp.cleanup)
        self.root = Path(temp.name)
        env = patch.dict(os.environ, {'APP_ENV':'test', 'ADMIN_BOOTSTRAP_PASS':'test-password'}, clear=True)
        env.start(); self.addCleanup(env.stop)
        self.app = create_app(self.root, testing=True)
        self.r, self.b = self.app.extensions['runtime'], self.app.extensions['boss']
        self.addCleanup(self.r.store.close)
        clock = patch('boss.time.time', return_value=self.b.export()['created_at'] + 1.25)
        self.clock = clock.start(); self.addCleanup(clock.stop)

    def client(self, ip='192.0.2.1', name=None):
        c = self.app.test_client(); c.environ_base['REMOTE_ADDR'] = ip
        value = c.get('/play/api/state').json
        if name:
            self.assertEqual(self.name(c, name).status_code, 200)
        return c, value

    def name(self, c, name, **extra):
        v = c.get('/play/api/state').json
        return c.post('/play/api/profile', json={'raid_id':v['state']['raid_id'], 'username':name, **extra}, headers={'X-CSRF-Token':v['csrf']})

    def attack(self, c, **extra):
        v = c.get('/play/api/state').json
        return c.post('/play/api/attack', json={'raid_id':v['state']['raid_id'], 'style':v['state']['weakness'],
                      'request_id':secrets.token_hex(16), **extra}, headers={'X-CSRF-Token':v['csrf']})

    def core_hit(self, guest='a', ip='192.0.2.1', style=None):
        v = self.b.status(guest, ip)
        return self.b.attack(guest, ip, style or v['weakness'], v['raid_id'], secrets.token_hex(16))

    def admin(self):
        c, v = self.client('198.51.100.50')
        with c.session_transaction() as session: session.update(user='gingrsnaps', auth_version=1)
        return c, v['csrf']

    def test_username_is_required_on_http_and_cannot_be_forged_in_attack(self):
        c, v = self.client()
        self.assertEqual(self.attack(c, username='Fake', role='admin').status_code, 409)
        self.assertEqual(c.post('/play/api/profile', json={'username':'Fake'}).status_code, 400)
        for invalid in ('', ' ', 'x'*65, 'a\nb', 5, []):
            self.assertEqual(self.name(c, invalid).status_code, 422)
        self.assertEqual(self.name(c, 'Real submitted name').status_code, 200)
        self.assertEqual(self.attack(c).status_code, 200)
        self.assertEqual(self.b.export()['total_attacks'], 1)

    def test_distinct_players_share_ip_and_names_survive_ip_changes(self):
        a, _ = self.client(name='Alice'); b, _ = self.client()
        self.assertEqual(self.name(b, 'Bob').status_code, 200)
        self.assertNotIn('Alice', b.get('/play/api/state').text)
        self.attack(a)
        a.environ_base['REMOTE_ADDR'] = '192.0.2.2'
        self.assertEqual(self.attack(a).status_code, 429)
        self.clock.return_value += 30
        self.assertEqual(a.get('/play/api/state').json['state']['you']['display_name'], 'Alice')
        self.assertTrue(a.get('/play/api/state').json['state']['you']['identity_ready'])
        self.assertEqual(self.attack(a).status_code, 200)
        self.assertEqual(self.name(b, 'Alice').status_code, 409)
        self.assertEqual(self.name(b, 'Bob').status_code, 200)

    def test_profile_forgery_cannot_change_another_player_or_game_settings(self):
        a, _ = self.client(name='Alice'); b, _ = self.client('192.0.2.2')
        self.attack(a); before = self.b.export()
        response = self.name(b, 'Bob', guest='forged', player_id=next(iter(before['profiles'])), hp=0, damage=9999, role='admin')
        self.assertEqual(response.status_code, 200)
        after = self.b.export()
        for field in ('hp', 'players', 'total_damage', 'settings', 'networks'):
            self.assertEqual(after[field], before[field])
        self.assertEqual(next(iter(after['profiles'].values()))['name'], 'Alice')
        self.assertEqual(self.name(b, 'Other name').status_code, 429)

    def test_thirty_seconds_exact_and_no_daily_cap(self):
        c, _ = self.client(name='Unlimited')
        beginning = self.clock.return_value
        for i in range(101):
            self.clock.return_value = beginning + i*30
            self.assertEqual(self.attack(c).status_code, 200)
        saved = self.b.export()
        self.clock.return_value += 29.99
        blocked = self.attack(c)
        self.assertEqual(blocked.status_code, 429)
        self.assertEqual(blocked.headers['Retry-After'], '1')
        self.clock.return_value += .01
        self.assertEqual(self.attack(c).status_code, 200)
        self.assertEqual(saved['total_attacks'], 101)
        self.assertIsNone(c.get('/play/api/state').json['state']['rules']['daily_attacks'])

    def test_private_top_five_full_names_and_public_aliases(self):
        names = [f'FullName{i}' for i in range(7)]
        for i, name in enumerate(names):
            guest, ip = str(i), f'192.0.2.{i+1}'
            self.b.register(guest, ip, self.b.status()['raid_id'], name)
            for _ in range(i+1):
                self.core_hit(guest, ip); self.clock.return_value += 30
        anonymous, _ = self.client('198.51.100.1')
        self.assertEqual(anonymous.get('/admin/boss/status').status_code, 401)
        admin, _ = self.admin()
        response = admin.get('/admin/boss/status')
        self.assertEqual(response.headers['Cache-Control'], 'no-store')
        self.assertEqual([r['name'] for r in response.json['state']['admin_leaders']], names[-1:1:-1])
        for url in ('/play/api/state', '/play', '/public-state'):
            for name in names: self.assertNotIn(name, anonymous.get(url).text)
        self.r.admin['users']['helper'] = copy.deepcopy(self.r.admin['users']['gingrsnaps'])
        self.r.commit(self.r.admin, self.r.revision)
        with admin.session_transaction() as session: session['user'] = 'helper'
        self.assertEqual(admin.get('/admin/boss/status').status_code, 200)
        self.r.admin['users'].pop('helper'); self.r.commit(self.r.admin, self.r.revision)
        self.assertEqual(admin.get('/admin/boss/status').status_code, 401)

    def test_extreme_damage_zero_damage_and_explicit_hp_preserve_contributions(self):
        self.core_hit(); saved = self.b.export()
        self.b.control('health', saved['id'], 1, health_revision=0)
        s = self.b.export()
        self.assertEqual((s['hp'], s['max_hp'], s['total_damage']), (0, 1, 150))
        self.assertEqual(s['players'], saved['players'])
        self.b.control('health', s['id'], MAX_HP, health_revision=1)
        self.b.control('remaining_health', s['id'], MAX_HP, health_revision=2)
        self.b.configure(s['id'], dict(name='Flexible', damage=MAX_DAMAGE, weak_damage=0, burst_bonus=0), 0)
        self.clock.return_value += 30
        zero = self.core_hit()
        self.assertEqual(zero['hit']['damage'], 0)
        self.assertEqual(zero['state']['hp'], MAX_HP)
        validate_boss(self.b.export())
        self.b.control('remaining_health', s['id'], 5, health_revision=3)
        self.clock.return_value += 30
        v = self.b.status('a', '192.0.2.1')
        wrong = next(x for x in ('blade','bow','magic') if x != v['weakness'])
        self.assertEqual(self.core_hit(style=wrong)['hit']['damage'], 5)
        validate_boss(self.b.export())
        # Recovery metadata must handle the same numeric range as combat saves.
        self.b.control('restart', s['id'], MAX_HP)
        view = self.b.status('a', '192.0.2.1')
        wrong = next(x for x in ('blade','bow','magic') if x != view['weakness'])
        self.assertEqual(self.core_hit(style=wrong)['hit']['damage'], MAX_HP)
        admin, _ = self.admin()
        exported = admin.get('/admin/recovery-backup')
        self.assertEqual(exported.status_code, 200)
        self.assertEqual(exported.json['recovery_export']['damage'], MAX_HP)
        self.assertFalse(admin.get('/admin/status').json['checkpoint']['changes'])


    def test_random_weakness_is_shared_and_stable_without_writes(self):
        saved = self.b.export(); samples = []
        for i in range(60):
            self.clock.return_value += 600
            first = self.b.status('a', '192.0.2.1')['weakness']
            other = CommunityBoss(self.r.store).status('b', '192.0.2.2')['weakness']
            self.assertEqual(first, other); samples.append(first)
        self.assertEqual(set(samples), {'blade','bow','magic'})
        self.assertTrue(any(a == b for a,b in zip(samples, samples[1:])))
        self.assertEqual(saved, self.b.export())

    def test_eight_achievements_take_a_week_and_survive_new_raids(self):
        start = self.clock.return_value
        self.b.register('a', '192.0.2.1', self.b.status()['raid_id'], 'WeekPlayer')
        for day in range(7):
            if day == 3:
                self.b.control('restart', self.b.status()['raid_id'])
            for hit in range(75):
                self.clock.return_value = start + day*DAY + hit*30
                self.core_hit(style=('blade','bow','magic')[hit%3] if day == 0 else None)
            view = self.b.status('a', '192.0.2.1')
            if day < 6:
                self.assertFalse(next(b for b in view['you']['badges'] if b['id'] == 'week')['earned'])
        self.assertEqual(len(view['you']['badges']), 8)
        self.assertTrue(all(b['earned'] for b in view['you']['badges']))
        before = self.b.export()
        self.assertEqual(CommunityBoss(self.r.store).export(), before)
        self.b.control('restart', view['raid_id'])
        self.assertEqual(self.b.status('a', '192.0.2.1')['you']['badges'], view['you']['badges'])
        self.assertEqual(self.b.status()['total_damage'], 0)

    def test_legacy_save_migrates_additively_without_changing_hp(self):
        self.core_hit(); old = self.b.export()
        old.pop('profiles', None); old.pop('health_adjustment', None)
        for p in old['players'].values(): p['used'] = 40
        for p in old['networks'].values(): p['used'] = 40
        with self.r.store.connection(transaction=True) as conn: self.b._write(conn, old)
        self.b = CommunityBoss(self.r.store)
        self.assertEqual(self.b.export(), old)
        self.b.register('a', '192.0.2.1', old['id'], 'Returning player')
        self.assertEqual(self.b.export()['players'], old['players'])
        self.clock.return_value += 30
        self.assertEqual(self.core_hit()['state']['total_attacks'], 2)
        validate_boss(self.b.export())

    def test_profile_and_health_recovery_are_portable_and_reject_tampering(self):
        c, _ = self.client(name='RecoveryPlayer'); self.attack(c)
        saved = self.b.export()
        self.b.control('remaining_health', saved['id'], 17, health_revision=0)
        admin, _ = self.admin(); recovery = admin.get('/admin/recovery-backup').json
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory); (root/'private').mkdir()
            (root/'private/recovery.seed.json').write_text(json.dumps(recovery), encoding='utf-8')
            restored = create_app(root, testing=True)
            try: self.assertEqual(restored.extensions['boss'].export(), self.b.export())
            finally: restored.extensions['runtime'].store.close()
        bad = self.b.export(); next(iter(bad['profiles'].values()))['weak_hits'] = 99999
        with self.assertRaises(ValueError): validate_boss(bad)

    def test_connection_release_and_remaining_hp_are_admin_only(self):
        player, _ = self.client(name='Claimed')
        current = self.b.status(); admin, csrf = self.admin()
        form = dict(csrf=csrf, raid_id=current['raid_id'], action='release_player', player_name='Claimed', confirm_release='yes')
        self.assertEqual(player.post('/admin/boss/action', data=form).status_code, 302)
        self.assertEqual(admin.post('/admin/boss/action', data={**form,'csrf':'wrong'}).status_code, 400)
        self.assertEqual(admin.post('/admin/boss/action', data=form).status_code, 422)
        replacement, _ = self.client()
        self.assertEqual(self.name(replacement, 'Replacement').status_code, 200)
        self.assertEqual(self.attack(player).status_code, 200)
        hpform = dict(csrf=csrf, raid_id=current['raid_id'], action='remaining_health', health='0', health_revision='0', confirm_health='yes')
        self.assertEqual(admin.post('/admin/boss/action', data=hpform).status_code, 303)
        self.assertEqual(self.b.status()['hp'], 0)
        self.assertEqual(self.b.status()['status'], 'victory')


if __name__ == '__main__': unittest.main()
```

## wager_backend.py

```python
"""RedHunllef's sole launch command: python wager_backend.py.

App construction has no provider requests or hidden worker startup. The main
function binds one production server, then starts the two automatic jobs once.
"""
from collections import deque
import copy
import csv
from datetime import timedelta
from decimal import Decimal
from functools import wraps
import io
import hashlib
import ipaddress
import json
import logging
import re
import secrets
import signal
import threading
import time

from flask import Flask, Response, abort, flash, g, jsonify, redirect, render_template, request, session, url_for
from flask.sessions import SecureCookieSessionInterface
from itsdangerous import BadSignature, URLSafeSerializer, URLSafeTimedSerializer
from werkzeug.exceptions import HTTPException
from werkzeug.security import check_password_hash, generate_password_hash

from config import Config, RELEASE
from abuse_guard import AbuseGuard
from boss import BossError, CommunityBoss, DEFAULT_HP, rules as boss_rules, validate_boss
from boss_avatar import from_upload, validate_avatar
from presentation import changes, checkpoint_status, export_marker
from store_schema import upgrade_store
from race import calculate, empty, phase, token
from race_support import (DEFAULT_PRIZES, WEIGHTING_RULES, TEXT_LIMITS, URL_FIELDS,
                          canonical_site, clean_overrides, clean_snapshots, csv_text,
                          decimal_amount, eastern_epoch, empty_snapshots, fmt_et,
                          local_input, money, money_input, race_key, validate_site)
from runtime import Runtime
from storage import Conflict, StoreError

LOG = logging.getLogger("redhunllef")
TABS = {"overview":"Overview", "race":"Race", "players":"Players", "boss":"Community boss", "settings":"Settings"}


def account(users, name):
    return next(((k, v) for k, v in users.items() if k.casefold() == str(name).casefold()), (None, None))


def filtered(rows, edits, args):
    view, query, order = args.get("view", "all"), args.get("q", "").strip()[:64], args.get("sort", "rank")
    values = edits if view == "overrides" else rows[:15] if view == "top" else rows
    values = [r for r in values if query.casefold() in r["username"].casefold()]
    if order == "name":
        values = sorted(values, key=lambda r: (r["username"].casefold(), r["username"]))
    elif order == "raw":
        values = sorted(values, key=lambda r: (-decimal_amount(r.get("raw_wager") or 0), r["username"].casefold()))
    return values


def create_app(root=None, testing=False):
    config = Config(root)
    runtime = Runtime(config)
    app = Flask(__name__)
    app.config.update(TESTING=testing, SECRET_KEY=config.secret or runtime.admin["secret_key"],
                      MAX_CONTENT_LENGTH=8 * 1024 * 1024, SESSION_COOKIE_HTTPONLY=True,
                      SESSION_COOKIE_SAMESITE="Lax", PERMANENT_SESSION_LIFETIME=timedelta(hours=12))
    app.extensions["runtime"] = runtime
    app.extensions["settings"] = config
    boss = app.extensions["boss"] = CommunityBoss(runtime.store)
    guest_signer = URLSafeTimedSerializer(app.secret_key, salt="community-boss-guest-v1")
    recovery_signer = URLSafeSerializer(app.secret_key, salt="community-boss-recovery-v1")
    abuse = app.extensions["boss_abuse"] = AbuseGuard(app.secret_key)
    review_signer = URLSafeTimedSerializer(app.secret_key, salt="race-review-v1")
    failures, previews, access_log = {}, {}, deque(maxlen=150)
    auth_lock = threading.Lock()
    dummy_hash = generate_password_hash(secrets.token_hex(16))
    # Shipped assets are UTF-8. Never use the host's default text encoding:
    # Windows CP1252 cannot decode some Unicode characters in the browser code.
    assets = token([
        (p.name, p.read_text(encoding="utf-8"))
        for p in sorted((config.root / "static").glob("*"))
        if p.suffix in {".css", ".js"}
    ])

    class Cookies(SecureCookieSessionInterface):
        def get_cookie_secure(self, app):
            if config.secure_cookie in {"1", "true", "always"}:
                return True
            if config.secure_cookie in {"0", "false", "never"}:
                return False
            return request.is_secure
    app.session_interface = Cookies()

    def csrf():
        return session.setdefault("csrf", secrets.token_urlsafe(32))

    def wants_json():
        """Keep fetch failures machine-readable; native pages still render HTML."""
        return request.path.startswith("/play/api/") or request.accept_mimetypes.best == "application/json" or request.path in {
            "/data", "/public-state", "/config", "/stream", "/admin/status", "/admin/boss/status", "/admin/diagnostics", "/healthz", "/readyz"
        }

    def json_error(message, status):
        return jsonify(ok=False, error=message, status=status, release=RELEASE), status

    def require_csrf():
        expected = session.get('csrf')
        supplied = request.headers.get('X-CSRF-Token') or request.form.get('csrf', '')
        # A missing session token must never match a known fallback value.
        # Reject malformed Unicode cleanly before constant-time ASCII comparison.
        if (not isinstance(expected, str) or not expected or not expected.isascii() or
            not isinstance(supplied, str) or not supplied or not supplied.isascii() or
            not secrets.compare_digest(supplied, expected)):
            abort(400, description="This form expired. Reload the page and try again.")

    def protected(fn):
        @wraps(fn)
        def wrapped(*args, **kwargs):
            if not g.user:
                if request.path.endswith(("status", "diagnostics", ".csv", "backup")) or wants_json():
                    return jsonify(error="Your session expired. Sign in again.", login_url=url_for("login")), 401
                return redirect(url_for("login"))
            return fn(*args, **kwargs)
        return wrapped

    @app.before_request
    def before():
        g.began, g.user, g.superadmin = time.perf_counter(), None, False
        # App Platform supplies the visitor address in DO-Connecting-IP. Never
        # trust this header on a directly exposed/local server.
        address = request.headers.get("DO-Connecting-IP") if config.proxy else request.remote_addr
        try:
            g.client_ip = str(ipaddress.ip_address(address))
        except (ValueError, TypeError):
            g.client_ip = None
        if request.path.startswith("/admin"):
            g.revision, g.admin = runtime.sync()
            name, record = account(g.admin["users"], session.get("user"))
            if name and record.get("auth_version", 1) == session.get("auth_version"):
                g.user = name
                g.superadmin = name.casefold() == g.admin.get("superadmin", config.superadmin).casefold()
        if request.path not in {"/healthz", "/readyz"} and g.client_ip in runtime.admin.get("banned_ips", []):
            abort(403, description="Access from this address has been disabled.")

    @app.after_request
    def after(response):
        response.headers.update({"X-Content-Type-Options":"nosniff", "X-Frame-Options":"DENY",
            "Referrer-Policy":"strict-origin-when-cross-origin", "X-RedHunllef-Release":RELEASE,
            "Content-Security-Policy":"default-src 'self'; script-src 'self'; style-src 'self'; img-src 'self' data:; connect-src 'self'; frame-ancestors 'none'; base-uri 'self'; form-action 'self'",
            "Cache-Control":"public, max-age=31536000, immutable" if request.path.startswith("/static/") and request.args.get("v") == assets else "no-store"})
        if request.is_secure:
            response.headers["Strict-Transport-Security"] = "max-age=31536000"
        if request.path == "/public-state" and response.status_code in {200, 304}:
            response.headers["Cache-Control"] = "public, no-cache"
        if request.endpoint == 'boss_avatar_image' and response.status_code in {200, 304}:
            response.headers['Cache-Control'] = 'public, max-age=31536000, immutable'
        if request.path.startswith("/admin"):
            response.headers["X-Robots-Tag"] = "noindex, nofollow"
        if getattr(g, "new_guest", None):
            response.set_cookie("rh_raider", guest_signer.dumps(g.new_guest), max_age=365*86400,
                                secure=app.session_interface.get_cookie_secure(app), httponly=True, samesite="Lax")
        if request.path not in {"/data", "/public-state", "/config", "/stream", "/admin/status", "/admin/boss/status", "/healthz", "/readyz"} and not request.path.startswith(("/static/", "/play/api/")):
            with auth_lock:
                access_log.appendleft(dict(time=int(time.time()), method=request.method, path=request.path[:120], status=response.status_code,
                                           ip=g.client_ip, ms=round((time.perf_counter()-g.began)*1000)))
        return response

    @app.context_processor
    def context():
        return dict(release=RELEASE, asset_version=assets, csrf=csrf, money=money, fmt_et=fmt_et,
                    local_input=local_input, tabs=TABS, weighting=WEIGHTING_RULES,
                    local_storage=not runtime.store.pg, hosted_local=config.production and not runtime.store.pg,
                    boss_rules=boss_rules())

    @app.errorhandler(StoreError)
    def storage_error(error):
        LOG.error("STORAGE %s", str(error))
        if wants_json():
            return json_error(str(error), 503)
        return render_template("error.html", title="Connection interrupted", message=str(error)), 503

    @app.errorhandler(HTTPException)
    def page_error(error):
        LOG.warning("HTTP %s %s returned %s (%s).", request.method, request.endpoint or "unmatched route", error.code, error.name)
        if wants_json():
            return json_error(error.description, error.code)
        return render_template("error.html", title="Page unavailable" if error.code == 404 else "Request could not be completed",
                               message=error.description), error.code

    @app.errorhandler(500)
    def internal_error(error):
        if wants_json():
            return json_error("The backend could not complete this request. Check the runtime logs and try again.", 500)
        return render_template("error.html", title="Something interrupted this request", message="Reload and try again. Existing saved data remains in place."), 500

    @app.get("/")
    def index():
        return render_template("index.html", data=public_snapshot())

    def public_snapshot():
        value = runtime.public()
        value["boss"] = boss.summary()
        return value

    @app.get("/public-state")
    def public_state():
        # The representation excludes the moving clock, so its strong ETag
        # really describes identical bytes. Both 200 and 304 carry fresh time.
        value = public_snapshot()
        server_time = value.pop("server_time")
        response = jsonify(value)
        response.set_etag(token(value))
        response.headers["X-Server-Time"] = str(server_time)
        return response.make_conditional(request)

    def guest():
        if not hasattr(g, "guest"):
            try:
                value = guest_signer.loads(request.cookies.get("rh_raider", ""), max_age=365*86400)
                if not isinstance(value, str) or not re.fullmatch(r"[a-f0-9]{32}", value):
                    raise BadSignature("Invalid raider identifier")
                g.guest = value
            except BadSignature:
                g.guest = g.new_guest = secrets.token_hex(16)
        return g.guest

    @app.get("/play")
    def play():
        return render_template("boss.html", data=runtime.public(), boss_data=boss.status(guest(), g.client_ip))

    @app.get("/play/api/state")
    def boss_state():
        return jsonify(ok=True, state=boss.status(guest(), g.client_ip), csrf=csrf())

    def guard_key(identity, category):
        # Rejected requests belong to a signed browser, not every person behind
        # its proxy. One bad client must never lock a shared community network.
        return abuse.key(identity, '')

    def throttled(category, identity, alias):
        wait = abuse.retry_after(category, guard_key(identity, category))
        if not wait: return None
        response = jsonify(ok=False, code='request_throttle',
                           error=f'Too many rejected requests. Wait {wait} seconds, then try again.')
        response.headers['Retry-After'] = str(wait)
        return response, 429

    @app.post('/play/api/recovery-code')
    def boss_recovery_code():
        require_csrf()
        identity = guest()
        if getattr(g, 'new_guest', None):
            return json_error('Save your username before creating a recovery code.', 400)
        limited = throttled('registration', identity, '')
        if limited: return limited
        try:
            code = recovery_signer.dumps({'guest': identity, 'nonce': secrets.token_hex(16)})
            boss.save_recovery(identity, hashlib.sha256(code.encode()).hexdigest())
            return jsonify(ok=True, code=code, state=boss.status(identity, g.client_ip), csrf=csrf())
        except BossError as exc:
            abuse.rejected('registration', guard_key(identity, 'registration'), 'Player setup')
            return json_error(str(exc), exc.status)

    @app.post('/play/api/recover')
    def boss_recover():
        require_csrf()
        identity = guest()
        if getattr(g, 'new_guest', None):
            return json_error('Enable cookies and reload before recovering.', 400)
        limited = throttled('recovery', identity, '')
        if limited: return limited
        body = request.get_json(silent=True) or {}
        try:
            code = body.get('code', '') if isinstance(body, dict) else ''
            if not isinstance(code, str) or not 20 <= len(code) <= 512:
                raise BadSignature('Invalid recovery code')
            decoded = recovery_signer.loads(code)
            original = decoded.get('guest') if isinstance(decoded, dict) else None
            if not isinstance(original, str) or not re.fullmatch(r'[a-f0-9]{32}', original):
                raise BadSignature('Invalid recovery code')
            value = boss.recover_profile(original, g.client_ip, hashlib.sha256(code.encode()).hexdigest(), body.get('raid_id'))
            g.guest = g.new_guest = original
            return jsonify(ok=True, state=value, csrf=csrf())
        except (BadSignature, BossError) as exc:
            abuse.rejected('recovery', guard_key(identity, 'recovery'), 'Profile recovery')
            return json_error('That recovery code is invalid or was replaced.' if isinstance(exc, BadSignature) else str(exc),
                              getattr(exc, 'status', 400))

    @app.post('/play/api/profile')
    def boss_profile():
        require_csrf()
        identity = guest()
        if getattr(g, 'new_guest', None):
            return json_error('Enable cookies and reload before saving your username.', 400)
        limited = throttled('registration', identity, '')
        if limited: return limited
        body = request.get_json(silent=True)
        if not isinstance(body, dict):
            abuse.rejected('registration', guard_key(identity, 'registration'), 'Player setup')
            return json_error('Send a valid username request.', 400)
        try:
            view = boss.register(identity, g.client_ip, body.get('raid_id'), body.get('username'))
            return jsonify(ok=True, state=view, csrf=csrf())
        except (ValueError, BossError) as exc:
            abuse.rejected('registration', guard_key(identity, 'registration'), 'Player setup')
            response = jsonify(ok=False, error=str(exc), state=boss.status(identity, g.client_ip))
            if getattr(exc, 'retry_after', 0):
                response.headers['Retry-After'] = str(exc.retry_after)
            return response, getattr(exc, 'status', 422)

    def boss_admin_view():
        value = boss.admin_status()
        value["abuse_flags"] = abuse.status()
        with runtime.lock:
            # This is a spelling match only. No provider IP mapping or account
            # ownership proof exists in the current Shuffle leaderboard contract.
            names = {r['username'].casefold() for r in runtime.shuffle['rows']}
        for row in value['admin_leaders']:
            row['shuffle_name_in_feed'] = row['name_provided'] and row['name'].casefold() in names
        return value

    @app.get('/admin/boss/status')
    @protected
    def boss_admin_state():
        return jsonify(ok=True, state=boss_admin_view(), csrf=csrf())

    @app.get('/play/avatar/<digest>.png')
    def boss_avatar_image(digest):
        if not re.fullmatch(r'[a-f0-9]{64}', digest):
            abort(404)
        data = boss.avatar_image(digest)
        if data is None:
            abort(404)
        response = Response(data, mimetype='image/png')
        response.set_etag(digest)
        return response.make_conditional(request)

    @app.get("/play/api/contributors")
    def boss_contributors():
        # Keep a host restart from mixing one raid's ID with another's recap.
        with boss.lock:
            current = boss.summary()
            if request.args.get("raid_id") != current["raid_id"] or current["status"] != "victory":
                return json_error("The victory recap belongs to a completed raid. Refresh to see the current raid.", 409)
            return jsonify(ok=True, raid_id=current["raid_id"], health_revision=current["health_revision"],
                           contributors=boss.contributors())

    @app.post("/play/api/attack")
    def boss_attack():
        require_csrf()
        identity = guest()
        if getattr(g, "new_guest", None):
            return json_error("Enable cookies and reload the game before attacking.", 400)
        body = request.get_json(silent=True)
        view = boss.status(identity, g.client_ip)
        valid_body = (isinstance(body, dict) and isinstance(body.get('style'), str)
                      and body['style'] in boss_rules()['styles'])
        receipt = body.get('request_id') if isinstance(body, dict) else None
        valid_body = valid_body and isinstance(receipt, str) and bool(re.fullmatch(r'[A-Za-z0-9_-]{8,64}', receipt)) and body.get('raid_id') == view['raid_id']
        retry = valid_body and receipt == view['you']['last_request']
        if not (valid_body and view['you']['can_attack']) and not retry:
            limited = throttled('attack', identity, view['you']['name'])
            if limited: return limited
        if not isinstance(body, dict):
            abuse.rejected('attack', guard_key(identity, 'attack'), view['you']['name'])
            return json_error("Send a valid attack request.", 400)
        try:
            return jsonify(boss.attack(identity, g.client_ip, body.get("style"), body.get("raid_id"), body.get("request_id"), require_profile=True))
        except BossError as exc:
            abuse.rejected('attack', guard_key(identity, 'attack'), view['you']['name'])
            response = jsonify(ok=False, error=str(exc), code=exc.code, state=boss.status(identity, g.client_ip))
            if exc.retry_after:
                response.headers["Retry-After"] = str(exc.retry_after)
            return response, exc.status

    @app.get("/data")
    def data():
        return jsonify(runtime.public())

    @app.get("/config")
    def public_config():
        return jsonify(runtime.public()["site"])

    @app.get("/stream")
    def stream():
        return jsonify(runtime.public()["stream"])

    @app.get("/healthz")
    def health():
        return jsonify(ok=True, release=RELEASE)

    @app.get("/readyz")
    def ready():
        runtime.store.admin()
        value = runtime.public()
        ok = value["freshness"]["state"] in {"current", "partial"} or value["site"]["race_state"] == "upcoming"
        return jsonify(ok=ok, data_state=value["freshness"]["state"]), 200 if ok else 503

    def recovery_status():
        with runtime.lock:
            return checkpoint_status(runtime.store.checkpoint(), runtime.admin, runtime.shuffle["rows"], boss.summary())

    def render_admin(tab=None, draft=None, errors=None, confirm_race=False, restore=None, status=200,
                     change_review=None, review_token=None, recovery_review=None):
        tab = tab or request.args.get("tab", "overview")
        if tab not in TABS:
            tab = "overview"
        values = runtime.status()
        values["checkpoint"] = recovery_status() if g.superadmin else None
        visible = filtered(values["rows"], values["edits"], request.args)
        form = copy.deepcopy(g.admin["site_settings"])
        form.update(start_et=local_input(form["start_time"]), end_et=local_input(form["end_time"]))
        form.update({"prize_"+k: v for k, v in form["prizes"].items()})
        if draft:
            form.update(draft)
        return render_template("admin.html", data=values, tab=tab, form=form, errors=errors or {},
                               revision=(draft or {}).get("revision", g.revision), admin=g.admin, user=g.user,
                               superadmin=g.superadmin, participants=visible, confirm_race=confirm_race, restore=restore,
                               access_log=list(access_log), defaults=DEFAULT_PRIZES, limit=config.limit,
                               boss_data=boss_admin_view() if tab == "boss" else None,
                               change_review=change_review, review_token=review_token,
                               recovery_review=recovery_review), status

    @app.post("/admin/boss/action")
    @protected
    def boss_control():
        # g.user is populated only from a current administrator account and its
        # auth_version, never from a guest cookie or a client-supplied role flag.
        # Keep every boss configuration write behind this guard, including image decoding.
        require_csrf()
        try:
            action = request.form.get("action", "")
            if action == "restart" and request.form.get("confirm_restart") != "yes":
                raise ValueError("Confirm that you want to archive the current raid and start a new one.")
            if action in {'health', 'remaining_health'} and request.form.get('confirm_health') != 'yes':
                raise ValueError('Confirm that you want to change this raid\'s health.')
            if action in {'avatar', 'avatar_reset'}:
                boss.set_avatar(request.form.get('raid_id'), from_upload(request.files.get('avatar')) if action == 'avatar' else None, actor=g.user)
            elif action == 'release_player':
                if request.form.get('confirm_release') != 'yes':
                    raise ValueError('Confirm the connection release.')
                boss.release_profile(request.form.get('raid_id'), request.form.get('player_name'), actor=g.user)
            elif action == 'household':
                boss.household(request.form.get('raid_id'), request.form.get('player_name'), int(request.form.get('slots', '')), actor=g.user)
            elif action == 'settings':
                try:
                    values = dict(name=request.form.get('boss_name', ''),
                                  damage=int(request.form.get('base_damage', '')),
                                  weak_damage=int(request.form.get('weak_damage', '')),
                                  burst_bonus=int(request.form.get('burst_bonus', '')))
                    settings_revision = int(request.form.get('settings_revision', '-1'))
                except ValueError:
                    raise ValueError('Enter whole numbers for damage and reload if this form is out of date.') from None
                boss.configure(request.form.get('raid_id'), values, settings_revision, actor=g.user)
            else:
                boss.control(action, request.form.get("raid_id"), int(request.form.get("health", DEFAULT_HP)),
                             health_revision=int(request.form.get('health_revision', '-1')) if action in {'health', 'remaining_health'} else None, actor=g.user)
            flash({'restart':'New community raid is ready.', 'pause':'Community raid paused.', 'resume':'Community raid resumed.',
                   'health':'Maximum HP updated. Saved damage and cooldowns were kept.',
                   'remaining_health':'Remaining HP updated. Saved damage and cooldowns were kept.',
                   'household':'Shared connection allowance saved. Each approved player keeps a 30-second cooldown.',
                   'release_player':'Connection released. The original browser retains its name and achievements.',
                   'settings':'Boss name and damage settings saved. New damage values apply to future hits.',
                   'avatar':'Boss avatar updated.', 'avatar_reset':'Original boss avatar restored.'}[action])
            LOG.info('BOSS Admin action %s accepted for account %r.', action, g.user)
            return redirect(url_for("login", tab="boss"), 303)
        except ValueError as exc:
            return render_admin("boss", errors={"boss":str(exc)}, status=422)

    @app.route("/admin", methods=["GET", "POST"])
    @app.route("/admin/login", methods=["GET", "POST"])
    def login():
        if request.method == "GET":
            return render_admin() if g.user else render_template("login.html", error="")
        require_csrf()
        name, password = request.form.get("username", "").strip()[:64], request.form.get("password", "")
        key = g.client_ip or request.remote_addr or "unknown"
        with auth_lock:
            cutoff = time.monotonic() - 600
            for ip in list(failures):
                failures[ip] = [t for t in failures[ip] if t > cutoff]
                if not failures[ip]:
                    del failures[ip]
            if len(failures) >= 2000 and key not in failures:
                return render_template("login.html", error="Too many sign-in attempts. Please try again later."), 429
            if len(failures.get(key, [])) >= 5:
                return render_template("login.html", error="Too many sign-in attempts. Wait ten minutes and try again."), 429
            failures.setdefault(key, []).append(time.monotonic())
        canonical, record = account(g.admin["users"], name)
        valid = check_password_hash(record["pw_hash"] if record else dummy_hash, password[:256])
        if not valid or not canonical or len(password) > 256:
            return render_template("login.html", error="The username or password is incorrect."), 401
        with auth_lock:
            failures.pop(key, None)
        session.clear()
        session.update(user=canonical, auth_version=record.get("auth_version", 1), csrf=secrets.token_urlsafe(32))
        session.permanent = True
        LOG.info("ADMIN Sign-in successful.")
        return redirect(url_for("login", tab="overview"), 303)

    @app.post("/admin/logout")
    def logout():
        require_csrf()
        session.clear()
        return redirect(url_for("login"), 303)

    @app.get("/admin/status")
    @protected
    def status():
        value = runtime.status()
        value["checkpoint"] = recovery_status() if g.superadmin else None
        rows, edits = value.pop("rows"), value.pop("edits")
        # Other tabs have no participant table; keep their minute responses small.
        if request.args.get("tab", "players") == "players":
            value["participants"] = filtered(rows, edits, request.args)
        if request.args.get("code_red") != "1":
            value.pop("red", None)
        return jsonify(value)

    @app.get("/admin/diagnostics")
    @protected
    def diagnostics():
        value = runtime.status()
        safe = dict(diagnostics=value["diagnostics"], jobs=value["jobs"], freshness=value["freshness"], generated_at=int(time.time()))
        return Response(json.dumps(safe, indent=2), mimetype="application/json",
                        headers={"Content-Disposition":"attachment; filename=redhunllef-diagnostics.json"})

    def safe_backup():
        with runtime.lock:
            saved, current = runtime.shuffle, runtime.admin
            return dict(backup_version=3, generated_at=int(time.time()), site_settings=copy.deepcopy(current["site_settings"]),
                        overrides=copy.deepcopy(current["overrides"]), race_history=copy.deepcopy(current["race_history"]),
                        leaderboard_snapshots=dict(race_key=saved["key"], last_top15=copy.deepcopy(saved["rows"][:15]),
                                                   prev_top15=copy.deepcopy(saved.get("previous_top", [])), updated_at=saved["updated_at"]))

    @app.get("/admin/backup")
    @protected
    def backup():
        return Response(json.dumps(safe_backup(), indent=2), mimetype="application/json",
                        headers={"Content-Disposition":"attachment; filename=redhunllef-race-backup.json"})

    @app.get("/admin/recovery-backup")
    @protected
    def recovery_backup():
        # A full account export is private to the Superadmin. It uses the same
        # validated seed format as startup and is never part of public feeds.
        if not g.superadmin:
            abort(403, description="Only the Superadmin can download private account recovery files.")
        with runtime.lock:
            value = copy.deepcopy(runtime.admin)
            value["leaderboard_snapshots"] = safe_backup()["leaderboard_snapshots"]
            value.update(boss.recovery())
            marker = export_marker(runtime.admin, value["leaderboard_snapshots"], value["community_boss"], int(time.time()))
            value["recovery_export"] = marker
            runtime.store.checkpoint(marker)
        return Response(json.dumps(value, indent=2, ensure_ascii=False, allow_nan=False), mimetype="application/json",
                        headers={"Content-Disposition":"attachment; filename=recovery.seed.json"})

    @app.post("/admin/recovery-preview")
    @protected
    def recovery_preview():
        require_csrf()
        if not g.superadmin:
            abort(403)
        try:
            upload = request.files.get("recovery")
            if not upload:
                raise ValueError("Choose a private recovery JSON file.")
            value, _ = upgrade_store(json.load(upload), config.site, {})
            if not value["users"]:
                raise ValueError("The recovery file contains no administrator accounts.")
            game = validate_boss(value["community_boss"]) if value.get("community_boss") is not None else None
            avatar = validate_avatar(value.get('community_boss_avatar'))
            review = dict(accounts=len(value["users"]), overrides=len(value["overrides"]),
                          history=len(value["race_history"]), rows=len(value["leaderboard_snapshots"]["last_top15"]),
                          start=fmt_et(value["site_settings"]["start_time"]), end=fmt_et(value["site_settings"]["end_time"]),
                          game=game and dict(hp=game["hp"], max_hp=game["max_hp"], raiders=len(game["players"]), attacks=game["total_attacks"]),
                          avatar=bool(avatar))
            return render_admin("settings", recovery_review=review)
        except (ValueError, RuntimeError, UnicodeDecodeError) as exc:
            return render_admin("settings", errors={"recovery":str(exc)}, status=422)

    @app.get("/admin/export.csv")
    @protected
    def export():
        value = runtime.status()
        rows = filtered(value["rows"], value["edits"], request.args)
        output = io.StringIO(newline="")
        writer = csv.writer(output)
        writer.writerow(["rank", "username", "weighted_wager", "original_weighted_wager", "raw_wager", "prize", "source", "last_source_update_et", "data_state"])
        for row in rows:
            writer.writerow([row["rank"] or "", csv_text(row["username"]), row["weighted_wager"], row["original_weighted_wager"],
                             row["raw_wager"], value["site"]["prizes"].get(str(row["rank"]), ""), row["source"],
                             fmt_et(value["freshness"]["updated_at"]), value["freshness"]["state"]])
        return Response("\ufeff" + output.getvalue(), mimetype="text/csv",
                        headers={"Content-Disposition":"attachment; filename=redhunllef-" + value["freshness"]["state"] + ".csv"})

    def validate_backup(upload):
        try:
            value = json.load(upload)
        except (ValueError, UnicodeDecodeError):
            raise ValueError("Choose a valid JSON backup.") from None
        if not isinstance(value, dict) or value.get("backup_version") not in {1, 2, 3}:
            raise ValueError("This backup version is not supported.")
        if not isinstance(value.get("site_settings"), dict):
            raise ValueError("The backup has no valid race settings.")
        site = canonical_site(value["site_settings"], config.site)
        if validate_site(site):
            raise ValueError("The backup contains invalid dates, prizes, or links.")
        overrides = clean_overrides(value.get("overrides", {}))
        snapshots = clean_snapshots(value.get("leaderboard_snapshots", {}), race_key(site))
        history = value.get("race_history", [])
        if not isinstance(history, list):
            raise ValueError("Race history must be a list.")
        for entry in history:
            if not isinstance(entry, dict) or not isinstance(entry.get("site_settings"), dict):
                raise ValueError("An archived race is invalid.")
            old_site = canonical_site(entry["site_settings"], config.site)
            if validate_site(old_site):
                raise ValueError("An archived race has invalid settings.")
            clean_overrides(entry.get("overrides", {}))
            clean_snapshots(entry.get("leaderboard_snapshots", {}), race_key(old_site))
        return dict(site_settings=site, overrides=overrides, leaderboard_snapshots=snapshots, race_history=history)

    @app.post("/admin/action")
    @protected
    def action():
        require_csrf()
        action_name, tab = request.form.get("action"), request.form.get("tab", "overview")
        if action_name == "refresh":
            name = request.form.get("service") or None
            if name not in {None, "shuffle", "kick"}:
                abort(400)
            receipt = runtime.request_refresh(name)
            LOG.info("REFRESH Check requested for %s; provider retry delays still apply.", name or "Shuffle and Kick")
            if wants_json():
                return jsonify(ok=True, message="Refresh queued. Its progress and result appear below.",
                               **receipt, jobs=runtime.job_status()), 202
            flash("Check requested. Results update automatically.")
            return redirect(url_for("login", tab=tab), 303)
        try:
            expected = int(request.form.get("revision", "0"))
            if expected != g.revision:
                raise Conflict("Another administrator changed saved settings. Reload and review your edits.")
            candidate, snapshot, reason, detail = copy.deepcopy(g.admin), None, None, "Changes saved."
            if action_name == "save_race":
                site = copy.deepcopy(candidate["site_settings"])
                site.update({k: request.form.get(k, "").strip() for k in (*TEXT_LIMITS, *URL_FIELDS, "kick_channel_slug")})
                errors = {}
                for key in ("start", "end"):
                    try:
                        site[key + "_time"] = eastern_epoch(request.form.get(key + "_et"))
                    except ValueError as exc:
                        errors[key + "_et"] = str(exc)
                site["prizes"] = {str(n): request.form.get("prize_" + str(n), "") for n in range(1, 16)}
                errors.update(validate_site(site))
                if errors:
                    return render_admin("race", dict(request.form), errors, status=422)
                site["prizes"] = {k: str(money_input(v)) for k, v in site["prizes"].items()}
                changed_race = race_key(site) != race_key(candidate["site_settings"])
                review = changes(candidate["site_settings"], site)
                expected_review = dict(user=g.user, revision=expected, site=site)
                try:
                    confirmed = request.form.get("confirm_race") == "yes" and review_signer.loads(request.form.get("review_token", ""), max_age=900) == expected_review
                except BadSignature:
                    confirmed = False
                if review and not confirmed:
                    return render_admin("race", dict(request.form), confirm_race=True, change_review=review,
                                        review_token=review_signer.dumps(expected_review))
                if changed_race:
                    old = safe_backup()
                    if candidate["site_settings"]["start_time"]:
                        candidate["race_history"].append({k: old[k] for k in ("site_settings", "overrides", "leaderboard_snapshots")} | {"archived_at":int(time.time())})
                    candidate["overrides"], reason = {}, "before-race-change"
                candidate["site_settings"] = site
                snapshot = empty(site) if changed_race else calculate(runtime.shuffle, candidate, config)
                detail = "Race published. A fresh check is queued for the saved dates; watch its progress below."
            elif action_name == "override":
                name, amount = request.form.get("username", "").strip(), request.form.get("amount", "").strip()
                if not name or len(name) > 64:
                    raise ValueError("Enter the exact full username, up to 64 characters.")
                if amount:
                    candidate["overrides"][name] = str(money_input(amount))
                else:
                    candidate["overrides"].pop(name, None)
                snapshot = calculate(runtime.shuffle, candidate, config)
                detail = "Override saved. Original weighted and raw values are retained."
            elif action_name in {"add_account", "remove_account", "reset_password", "password"}:
                if action_name != "password" and not g.superadmin:
                    abort(403)
                name = request.form.get("username", "").strip() if action_name != "password" else g.user
                canonical, record = account(candidate["users"], name)
                if action_name == "remove_account":
                    if not canonical or canonical.casefold() == candidate.get("superadmin", config.superadmin).casefold():
                        raise ValueError("The protected Superadmin account cannot be removed.")
                    del candidate["users"][canonical]
                    reason = "before-account-removal"
                else:
                    password = request.form.get("new_password", "")
                    if not 12 <= len(password) <= 256 or password != request.form.get("confirm_password"):
                        raise ValueError("Use matching passwords with 12–256 characters.")
                    if action_name == "add_account":
                        if canonical or not re.fullmatch(r"[A-Za-z0-9_]{3,32}", name):
                            raise ValueError("Choose an unused username with 3–32 letters, numbers, or underscores.")
                        canonical, record = name, dict(auth_version=0, created_at=int(time.time()))
                    elif not record:
                        raise ValueError("That account does not exist.")
                    if action_name == "password" and not check_password_hash(record["pw_hash"], request.form.get("current_password", "")[:256]):
                        raise ValueError("The current password is incorrect.")
                    record.update(pw_hash=generate_password_hash(password), auth_version=record.get("auth_version", 1) + 1)
                    candidate["users"][canonical] = record
                    reason = "before-password-change" if action_name != "add_account" else None
                detail = "Account updated. Removed or reset accounts lose their previous sessions."
            elif action_name == "preview_restore":
                upload = request.files.get("backup")
                if not upload:
                    raise ValueError("Choose a backup file.")
                value = validate_backup(upload)
                identifier = secrets.token_urlsafe(32)
                with auth_lock:
                    for key in list(previews):
                        if previews[key]["expires"] < time.time():
                            del previews[key]
                    if len(previews) >= 20:
                        raise ValueError("Too many pending restores. Wait ten minutes and try again.")
                    previews[identifier] = dict(value=value, user=g.user, expires=time.time()+600, revision=expected)
                return render_admin("settings", restore=dict(token=identifier, start=fmt_et(value["site_settings"]["start_time"]),
                                    end=fmt_et(value["site_settings"]["end_time"]), rows=len(value["leaderboard_snapshots"]["last_top15"]),
                                    overrides=len(value["overrides"]), history=len(value["race_history"]),
                                    changes=changes(g.admin["site_settings"], value["site_settings"])))
            elif action_name == "restore":
                with auth_lock:
                    preview = previews.get(request.form.get("restore_token"))
                    if not preview or preview["expires"] < time.time() or preview["user"] != g.user or preview["revision"] != expected:
                        raise ValueError("Restore preview expired or settings changed. Review the backup again.")
                    value = copy.deepcopy(preview["value"])
                candidate.update({k: value[k] for k in ("site_settings", "overrides", "race_history")})
                saved = value["leaderboard_snapshots"]
                snapshot = empty(candidate["site_settings"])
                snapshot.update(rows=saved["last_top15"], previous_top=saved["prev_top15"], updated_at=saved["updated_at"] or 0,
                                count=len(saved["last_top15"]), snapshot_only=bool(saved["last_top15"]),
                                source=[dict(username=r["username"], weighted=r["original_weighted_wager"], raw=r["raw_wager"], row_count=r["row_count"]) for r in saved["last_top15"]])
                reason, detail = "before-restore", "Backup restored. Accounts preserved; a private recovery copy was saved."
            elif action_name in {"ban_ip", "unban_ip"}:
                ip = str(ipaddress.ip_address(request.form.get("ip", "")))
                if action_name == "ban_ip" and ip == request.remote_addr:
                    raise ValueError("You cannot block the address you are using.")
                candidate["banned_ips"] = sorted(set(candidate["banned_ips"]) | {ip}) if action_name == "ban_ip" else [x for x in candidate["banned_ips"] if x != ip]
            elif action_name == "clear_audit":
                if not g.superadmin:
                    abort(403)
                candidate["audit_log"], reason = [], "before-clearing-audit"
            elif action_name == "clear_access":
                with auth_lock:
                    access_log.clear()
            else:
                raise ValueError("This action is not supported.")
            candidate["updated_at"] = int(time.time())
            candidate["audit_log"].append(dict(ts_et=fmt_et(candidate["updated_at"]), admin_user=g.user, action=action_name, detail=detail))
            candidate["audit_log"] = candidate["audit_log"][-250:]
            runtime.commit(candidate, expected, snapshot=snapshot, reason=reason)
            if action_name in {"password", "reset_password"}:
                _, current = account(candidate["users"], g.user)
                session["auth_version"] = current["auth_version"]
            if action_name in {"save_race", "restore"}:
                runtime.request_refresh()
                LOG.info("RACE Published revision %s: %s -> %s; fresh provider checks queued.", runtime.revision,
                         fmt_et(candidate["site_settings"]["start_time"]), fmt_et(candidate["site_settings"]["end_time"]))
            LOG.info("ADMIN %s completed.", action_name)
            flash(detail)
            return redirect(url_for("login", tab=tab), 303)
        except (ValueError, Conflict) as exc:
            return render_admin(tab, dict(request.form) if tab == "race" else None,
                                errors={"form":str(exc)}, status=409 if isinstance(exc, Conflict) else 422)

    return app


def main():
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
    try:
        app = create_app()
        config, runtime = app.extensions["settings"], app.extensions["runtime"]
        from waitress import create_server
        options = dict(host="0.0.0.0", port=config.port, threads=6, ident="RedHunllef", expose_tracebacks=False,
                       max_request_body_size=8*1024*1024, channel_timeout=60, clear_untrusted_proxy_headers=True)
        if config.proxy:
            # App Platform is the only trusted ingress. Do not enable this on
            # a directly exposed host. Waitress applies proxy interpretation once.
            options.update(trusted_proxy="*", trusted_proxy_count=1,
                           trusted_proxy_headers={"x-forwarded-proto", "x-forwarded-for"})
        server = create_server(app, **options)
        LOG.info("START RedHunllef %s listening on 0.0.0.0:%s; storage=%s.", RELEASE, config.port, "local JSON")
        LOG.info("BOSS Shared raid at /play; screens update every 5s, attacks every 30s, no daily cap. Identity and cooldowns follow signed browser cookies, never shared IPs. Names are self-reported; public feeds stay anonymous. Host controls: /admin?tab=boss.")
        if not runtime.store.pg:
            LOG.info("STORAGE Local file ready; no external database is required.")
            if config.production:
                LOG.warning("STORAGE On App Platform, local changes are lost on redeploy/container replacement. Download the private recovery file from Settings after important changes.")
        for key, details in config.diagnostics().items():
            LOG.info("CONFIG %s: %s (%s).", key, "configured" if details["configured"] else "missing", details["source"])
        LOG.info("RACE Saved window: %s → %s. State=%s.", fmt_et(runtime.admin["site_settings"]["start_time"]),
                 fmt_et(runtime.admin["site_settings"]["end_time"]), phase(runtime.admin["site_settings"]))
        def shutdown(*_):
            raise KeyboardInterrupt
        signal.signal(signal.SIGTERM, shutdown)
        runtime.start()
        try:
            server.run()
        finally:
            runtime.stop()
            server.close()
            runtime.store.close()
        return 0
    except KeyboardInterrupt:
        return 0
    except (StoreError, ValueError, RuntimeError) as exc:
        LOG.error("STARTUP %s", str(exc))
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
```

## MANIFEST.json

```json
{
  "release": "2026.09.29-player-access",
  "packaging": "complete",
  "entry_point": "python wager_backend.py",
  "storage": "local JSON (automatic)",
  "root_modules": [
    "abuse_guard",
    "boss",
    "boss_avatar",
    "boss_extras",
    "boss_progress",
    "config",
    "integrations",
    "presentation",
    "race",
    "race_support",
    "runtime",
    "storage",
    "store_schema",
    "wager_backend"
  ],
  "source_files": {
    ".env.example": {
      "bytes": 659,
      "sha256": "2a90ed921cdeaaf654e141a38177ce390647b2892a8dbe670415ce79f65987e2"
    },
    ".github/workflows/test.yml": {
      "bytes": 612,
      "sha256": "81e76099af6f74334e32c677e075f8b70fb3babc184ed1d6b6af2aa2af483bdb"
    },
    ".gitignore": {
      "bytes": 126,
      "sha256": "b0c7255d064a0109a93e4082b580da57d58cf26d1cde4b85d953d59a9d5a88ad"
    },
    "CHANGES.md": {
      "bytes": 3461,
      "sha256": "b4a8b2a2f81a5a8b01575bc822f8c608fb40163cc8683dce9d6607048139d034"
    },
    "FILE_STRUCTURE.md": {
      "bytes": 5471,
      "sha256": "d37cf69420cd17a394c463f8a76a4daeedf20f6c85f33fdb3fdbf05c27664616"
    },
    "Procfile": {
      "bytes": 29,
      "sha256": "bcd054c38b5885dcf501be6763dbc12226edafe9320dc058cd820f563d035d83"
    },
    "README.md": {
      "bytes": 17122,
      "sha256": "e37c83e4906edc07b1331a9a9cff9ce65c09cb7949d31df2bd10776e7e0391dd"
    },
    "START_HERE.md": {
      "bytes": 2545,
      "sha256": "a0a0370e54e9a97c22e8ae8431c1712b2ec2bca31b2651d0f44ed92cdc64b6ce"
    },
    "abuse_guard.py": {
      "bytes": 2063,
      "sha256": "c86e98c9c0a44c2c80f631f3f39c8c42c284c7bd7577c12fbe38de229c9ba9fa"
    },
    "app.yaml": {
      "bytes": 1369,
      "sha256": "1a57629c19f2f3a294691d2fd6b74d5355f4311c10201858598058093bfc878b"
    },
    "boss.py": {
      "bytes": 37554,
      "sha256": "fca3fcc7162e711cf907dbb9f474cd6ec9f3cac9e0d1be71c3add50aeba9e48b"
    },
    "boss_avatar.py": {
      "bytes": 3708,
      "sha256": "d4cc504b1a090ca026fdf4ede179aad701680da3679acfa1194967abe49f88c0"
    },
    "boss_extras.py": {
      "bytes": 5898,
      "sha256": "dd7e5464f9e63c5afd9ffd6e1897318bcbdcf368028adf547c3ac4c150020a8d"
    },
    "boss_progress.py": {
      "bytes": 5234,
      "sha256": "509a8f5b6537588a639123112f869f26fcecab5473e3f9d31c347d26cf5be419"
    },
    "config.py": {
      "bytes": 5327,
      "sha256": "954572a23e7e92018f6ca5c88f7538ebdad999907116df4a145ecd81588547fa"
    },
    "docs/COMMUNITY_BOSS.md": {
      "bytes": 4032,
      "sha256": "6aa8fc79d99cd0a41988d94e3273a195c29d14c47bb859d4cc4b8b950e685ae2"
    },
    "docs/COMMUNITY_UPDATE.md": {
      "bytes": 2025,
      "sha256": "0acf9ed9d50e9701a7877d6b8447fab8c16d90dea1b5a837d2b5c5cc5e69cbd7"
    },
    "docs/VALIDATION.md": {
      "bytes": 3438,
      "sha256": "8953867170ca619f9c7376902ed14388cce42e71a5784345aa0f8c5d337b54c4"
    },
    "integrations.py": {
      "bytes": 7041,
      "sha256": "1468838afdf081e4ce09e3598f6b5861c2feca090ef6f5ae4d3f24db94e214ea"
    },
    "presentation.py": {
      "bytes": 4244,
      "sha256": "2360378fc3a78d495fb150873c0d2c3b56bae75b5dd2f93eae9a97771cf47f66"
    },
    "private/admin_store.seed.json": {
      "bytes": 6514,
      "sha256": "b02e8a52d277f1d5dc7a710a97c368b3b1549e9aa3aa7c8d73c5d6abda10f303"
    },
    "private/settings.json": {
      "bytes": 1758,
      "sha256": "eb8cb8ead9104da92840274f335e0bc7549ca315ca0883308aec329816530321"
    },
    "race.py": {
      "bytes": 7590,
      "sha256": "d342af11d32d65157c87f96b0cdf942be89446d9657f615f2157887d4cfab7ad"
    },
    "race_support.py": {
      "bytes": 12150,
      "sha256": "3b115fc83fc18f79695996787113693bd80593418cfc3ba3a5ccf8ad18824f96"
    },
    "requirements.txt": {
      "bytes": 76,
      "sha256": "4c1a45a322ba363062403c67632144a14742dfa8d2d4df090620a13da7d9d13d"
    },
    "runtime.py": {
      "bytes": 18063,
      "sha256": "903164f37004ce0d886e316f09dda4f338ff142d415abf85826218d6d4175532"
    },
    "runtime.txt": {
      "bytes": 15,
      "sha256": "25dce2482c93ab6271d90809cd8ab8474830723459d2d0b51ce75bf7a72be92d"
    },
    "static/app.js": {
      "bytes": 26877,
      "sha256": "38c0a28989d21f17bea731fcb15910531bac2ce64e104bb149c69b6e9cc87a0b"
    },
    "static/boss.css": {
      "bytes": 22172,
      "sha256": "48902dc3cbada39b92b6b4cff8bfb319437302c094aff9cfc2253a82760486fc"
    },
    "static/boss.js": {
      "bytes": 38037,
      "sha256": "8738eaf6f0092918ea4d273d5792750c1da84ceda81084f845c7dabe20e737c4"
    },
    "static/redlogo.ico": {
      "bytes": 4286,
      "sha256": "6a2c518c570d0f0357e39f7a8791daa4de681434ca51b2fa17381fd2d6cac63e"
    },
    "static/redlogo.png": {
      "bytes": 12003,
      "sha256": "671545b962e3ad7a4e2b9d1b0a4db070f2e278b16c358d8c4c142c8b86956186"
    },
    "static/style.css": {
      "bytes": 30033,
      "sha256": "e4819b9fed73309a9012580f1c24fa310ea87f7d8f96d96fd09c03ffdb349845"
    },
    "storage.py": {
      "bytes": 13758,
      "sha256": "025b24cba32af09d0891ae68bb93f6267f71166cf82fb32fe6f0afdc43ecb813"
    },
    "store_schema.py": {
      "bytes": 4551,
      "sha256": "b178eaa121bdf4dca84fc1daf5845bebaa04049c9e4302653f577bbb7a4bea98"
    },
    "templates/admin.html": {
      "bytes": 5061,
      "sha256": "fe0a2bae07c842ca2d084c96e91616c1e5aae80d32c0c34c796335a8a2c97f9e"
    },
    "templates/admin_boss.html": {
      "bytes": 11045,
      "sha256": "7a2bc09f5b6eff45a15ac7e1357055039e5e1c8b87e324f57f624c29df625ad2"
    },
    "templates/admin_overview.html": {
      "bytes": 1785,
      "sha256": "9c10664afcf466c04b562c538bf7eabd77be070b7c73fb9b9b0b5304feed4f9d"
    },
    "templates/admin_players.html": {
      "bytes": 4156,
      "sha256": "40eb1fa32633f4a0f9ce11a04f98bd8d99677227e443fee5c15bb48e671db859"
    },
    "templates/admin_race.html": {
      "bytes": 3276,
      "sha256": "98569a72716c515043386b72ddf4ba5579fc5e171ab34b81bdf7b11b2140f1a6"
    },
    "templates/admin_settings.html": {
      "bytes": 8297,
      "sha256": "eac3e3a11afe3a41e8f25c6b138a9f33ace38e782759407a90ca5ce493ae0aa0"
    },
    "templates/base.html": {
      "bytes": 2129,
      "sha256": "7e11c5da247412157017d31b42f0a976658d011fb7ad55616c15a92538a895b9"
    },
    "templates/boss.html": {
      "bytes": 9362,
      "sha256": "ae7445b6e8c03de01198b92cf509568f37cad82cdabba2156fecefa5abd5b044"
    },
    "templates/change_review.html": {
      "bytes": 690,
      "sha256": "c5469e3b96c979eaf815c6599180de30ef81c83112d786e468ccbb056cc17450"
    },
    "templates/error.html": {
      "bytes": 515,
      "sha256": "8c02ec7296f011932263817c387f5126d62238d1d7714bd57d64cb51917474be"
    },
    "templates/icons.html": {
      "bytes": 687,
      "sha256": "7d99dc9ee58e6f0827b2a3583cb028477ae304b078f3b1311e766594f189ce3c"
    },
    "templates/index.html": {
      "bytes": 5352,
      "sha256": "35e7678d07f0db18b36c26ec6c9240a204cf9012b42852bdbd03c9bbda53c263"
    },
    "templates/login.html": {
      "bytes": 1292,
      "sha256": "569a7023dbcb632ac9dd356660b23ea8e08b7d946b3905122c063cdb09b01a25"
    },
    "templates/macros.html": {
      "bytes": 2037,
      "sha256": "c221df4a851759c64be861363d83161223a367db24dde7f022c8b39e05a65324"
    },
    "templates/recovery_panel.html": {
      "bytes": 2840,
      "sha256": "3c015db9a845348874c940ca06b85f1a3573eb7dea176eda6c233a7ba549eaa6"
    },
    "tests/package.json": {
      "bytes": 153,
      "sha256": "c18c562cf375863cdc2b73e7221e18cdf6c3afd432783690389efc1d0bf4b9cd"
    },
    "tests/render_fixtures.py": {
      "bytes": 3264,
      "sha256": "aa767480ff5952bd49ddcd5ca84b734ea89d33b8def2957c407c6ba2cad5179e"
    },
    "tests/test_app.py": {
      "bytes": 41139,
      "sha256": "da032a0e70ec5bc238adde670312e45439fe03839b33384e50d61f22fd72aa62"
    },
    "tests/test_boss.py": {
      "bytes": 16673,
      "sha256": "7954398a96c8dcdf72b63082a6d3db624a46c9b125bc76b09ff9ecebc06bc8b7"
    },
    "tests/test_boss_admin.py": {
      "bytes": 23132,
      "sha256": "0135081f79b247dd4c9e8a582e948715f2ea9a854aeb1adcba1cf49707e6e59a"
    },
    "tests/test_boss_frontend.cjs": {
      "bytes": 30379,
      "sha256": "68280f0dd5e99a69c7e732e33cdd3425cb8150d9838400b5eddd86c37b356f5b"
    },
    "tests/test_comfort_update.py": {
      "bytes": 14098,
      "sha256": "923a35e0d2e1e7e4fe16d65ff5e91e1cf6137286dd26c1c88d0d92b951ffaed1"
    },
    "tests/test_community.py": {
      "bytes": 9228,
      "sha256": "b25c22cc7af7056b6a218c1d1d8b91ab58084067767e8138f3b4dd3c5c18a31c"
    },
    "tests/test_frontend.cjs": {
      "bytes": 16897,
      "sha256": "9c586be46edbac59571842f55b16adb604173c0d5537f079924adaf369d051da"
    },
    "tests/test_player_access.py": {
      "bytes": 8262,
      "sha256": "c4a13b8b93882dcd9c89b730be450dc37995efbfb23ffd01d623f91cd06592cc"
    },
    "tests/test_raid_update.py": {
      "bytes": 12891,
      "sha256": "ba4fa7f9396e2c9539b42e2ffba7e1b567b95efa8010d845b3c27e593213a3b2"
    },
    "wager_backend.py": {
      "bytes": 47402,
      "sha256": "dc0f4b3e8270a72a78edf2232c67ae8b76ab66396b7c09c003004f79f6734a9c"
    }
  }
}
```
