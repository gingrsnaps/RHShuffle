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
