# RedHunllef

Release **2026.10.03-weekly-history**. This is the complete configured application.
Run **`python wager_backend.py`**. All supporting modules load automatically.
There is no database server, SQL setup, extra worker, scheduler or account-creation
command. The app saves its state to `data/state.json` automatically.

## This update: health bars and weekly history

The homepage uses a different health bar from the arena. The earlier patch changed
the arena/admin templates but missed `templates/index.html` and `static/app.js`.
This release corrects both initial HTML and automatic homepage updates: **full HP
means a full bar; zero HP means an empty bar**. The separate percentage-defeated
label in the arena still increases from 0% to 100%.

Choose **History** in the public navigation, or open `/history`:

- Four most recently **completed** weeks, newest first. Each runs from Tuesday
  at **6:00 PM America/New_York** to the following Tuesday at that same local time.
  Daylight saving changes are included; a calendar week can be 167 or 169 hours.
  The in-progress week stays on the current leaderboard.
- Each week shows the **top 25 qualifying weighted-wager players**. Names are
  censored on the server in both HTML and JSON, using the existing first-two-letters
  masking convention. Browsers never receive full historical usernames.
- Four native week links work without JavaScript. With JavaScript, the page reads
  the shared cache automatically every 60 seconds, pauses while hidden, and catches
  up when visible. Switching weeks does not trigger an affiliate API request.
- One background thread inside `wager_backend.py` loads the four date ranges using
  the existing Shuffle affiliate endpoint and credentials. It notices a newly
  completed week within 60 seconds, subject to provider delays. The newest closed
  week is rechecked hourly during its first day; older weeks are rechecked daily
  for corrections. Live race/Kick checks remain automatic every 60 seconds.
- Saved settings and overrides for an exact historical window determine its
  campaign and recorded prizes. When no matching settings exist, history queries
  the current campaign for that date range, applies no current-race overrides, and
  shows prizes as `—`. It never substitutes today's prize pool for an old week.
  The existing 15 paid places are unchanged; places 16–25 receive no prize when a
  matching schedule is known. Recorded prizes do not assert payment was made.
- The cache uses the existing JSON save and is included in the Superadmin's full
  **Private recovery file**. No SQL or additional process is needed. Failed checks
  retain saved results and show a delayed status. Missing results are not presented
  as a confirmed zero-player week.

Historical retrieval uses the same date-window API contract as the live race.
Actual historical availability depends on Shuffle retaining and returning those
periods for your affiliate account. This release was tested with synthetic data;
it does not claim that the live account's historical responses were verified.

Admin regression coverage includes all five dashboard tabs, native login/logout,
race preview/publication, automatic/manual refresh, overrides, Code Red Top 100,
CSV export, accounts/passwords, backups/restore, logs/IP controls, and boss
name/avatar/HP/damage/pause/restart controls. Also fixed the self-block check to use
the actual trusted visitor IP on App Platform instead of the proxy socket address.

After updating, restart the app and reload the homepage. `/healthz` should report
**2026.10.03-weekly-history**. Asset versions change automatically, so the new
scripts are requested. Preserve `data/`, current private files and player cookies.

## Username save repair

The previous save could be rejected after the separate page/admin session expired,
even though the persistent player cookie was still valid. The form also lacked a
native POST action, so a missing JavaScript handler reloaded the page without saving.
Finally, a display name left in an older profile could block a returning player.

- Game writes now use a CSRF token bound to the signed player cookie. Expiring,
  logging into or logging out of admin does not invalidate the game form. Admin
  writes still require their authenticated session and separate CSRF token.
- Save works through both the live interface and a regular server form. A successful
  save shows **Playing as…** and a visible confirmation. The regular form redirects
  back to the game without putting the username in the URL.
- Errors retain the draft and show the reason. A failed live save offers **Save with
  page reload**. The interface never reports success without a confirmed saved name.
- Display names are labels, not login credentials. A name can be reused by a new
  browser, but that never grants another player's stats, badges or recovery code.
  To restore your existing stats after losing cookies, use your private recovery code.
- A host starting a new raid while the name form is open no longer blocks saving.
- Player records, recovery codes, boss health, damage, admin accounts and original
  integration credentials remain intact. No new dependency or separate launcher.

After updating, restart the app and reload `/play`. `/healthz` should show release
**2026.10.03-weekly-history**. If it shows something else, the old application is
still serving requests. Do not clear your player cookie or delete `data/`.

For a hosted installation, open the normal **HTTPS** website directly. Cookies are
specific to the browser and hostname; changing between localhost, an IP address,
the App Platform hostname and your custom domain does not share a player cookie.
Local testing should use `http://localhost:8080` with `APP_ENV=local` and
`SESSION_COOKIE_SECURE=auto`; keep `SESSION_COOKIE_SECURE=always` for hosted HTTPS.
If cookies are blocked, the app now says so instead of claiming a successful save.

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
two commands above. Visit `http://localhost:8080`, `/history`, `/play`, and `/admin`.

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
| Health bar | Full to empty on the homepage, game and admin views; the separate defeated counter rises from 0% to 100%. |
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
new browser can create a different identity, including the same display name; the game does
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

Validation covers 157 backend tests and 65 DOM/HTTP interface checks. Coverage includes
source refresh behavior, actual launcher startup, login, authorization, image
validation, nonregenerating HP, unlimited attacks, recovery-code privacy, independent
cooldowns, migration, atomic-write failures and simultaneous writers. New regression
checks include 100 concurrent players sharing one proxy, absent IP headers, changing
addresses, names retained after restart, expired page sessions, native form saves,
duplicate-name isolation, visible save failures and delayed browser responses.
Weekly-history tests cover all four ranges, DST, Top 25 masking, cached reads,
historical prizes, retry preservation, recovery and automatic navigation updates.
The HTTP interface test loads both shipped scripts and uses a real Waitress server
and cookie jar; the username endpoint is not mocked. It saves a name, reloads the
page, lands an attack and checks a second independent player with the same label.

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

The HTTP interface test runs `python` by default. If your test environment uses a
different interpreter, set `RH_TEST_PYTHON` to that interpreter's executable path.
Node is used only by developer tests; it is not a deployment dependency.
