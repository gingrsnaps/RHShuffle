# RedHunllef Wager Race + Community Boss

Release **2026.09.22-no-regen**. Run the complete app with **`python wager_backend.py`**.
No PostgreSQL service, database connection string, account-creation script, or
separate update worker is required. Python's built-in SQLite creates a local
file automatically. The red theme, original credentials, original Superadmin,
public Top 15, private Code Red list, and automatic 60-second updates remain.

## Boss health never regenerates

Every confirmed hit reduces the current raid's saved health. Cooldowns, weakness
rotations, daily allowance resets, inactivity, page refreshes and process restarts
with the same saved data do not restore HP. The server now explicitly rejects
same-raid writes that increase health or reverse damage. Remaining health is
calculated from maximum health minus cumulative committed damage.

The browser rejects same-raid updates that increase HP even if they carry a
newer timestamp/version. It retains the last confirmed state and disables fresh
attacks if valid updates stop arriving. Initial HTML renders the actual health
percentage, removing the previous brief “100%” label during page loading.
The host's confirmed **Start a new raid** action creates a different boss.

A loss of local files on App Platform is a storage reset, not regeneration.
This patch cannot recover damage absent from both the saved file and your latest
recovery checkpoint. Keep one instance, preserve `data/` on persistent hosts,
and save a private recovery checkpoint before redeploying. Existing configuration
and game state are not reset by installing these application files.

## Included community improvements

- A shorter homepage with live boss health, raider count, and a play button that
  reflects an active, paused, or completed raid.
- Fixed mobile attack controls: choose a style, see your remaining allowance,
  and attack without scrolling back up. They share the main button's cooldown
  and safe retry receipt.
- Cosmetic 25%, 50%, and 75% milestones, arena changes, a victory recap with
  every contributor, first-hit/ten-burst/three-day badges, and a copy-link button.
- Attack errors stay visible until dismissed, retried, or resolved by a
  confirmed receipt. Ordinary successful polls cannot erase them.
- Compact connection summaries in the dashboard. Expand **Live connections**
  to see timings and provider controls; new failures open the details automatically.
- Side-by-side review before publishing changed dates, prizes, text, links,
  channel, or campaign. Confirmation is signed, expires after 15 minutes, and
  applies only to the exact changes reviewed.
- Private recovery export tracking, progress since the last export, and a
  read-only recovery-file review with account/race/game totals.
- Conditional public updates, retained unchanged game rows, animation without
  forced layout reads, shared game-rule constants, and readable JS/CSS source.

See [docs/COMMUNITY_UPDATE.md](docs/COMMUNITY_UPDATE.md) for implementation and
upgrade details. Cosmetic rewards do not increase damage or shorten the raid.

## Community boss: ready at /play

Use the homepage **Join the boss fight** button or open **`/play`**. Everyone
attacks one shared Crimson Hunllef. The red arena uses your original logo,
animated hit feedback, three attack styles, rotating weaknesses, Crimson burst
bonuses, personal progress, badges, milestones, Top 10 raiders, recent hits, and
past raid summaries. Victory includes the full contributor list.
Instructions are built into the page. There is no signup or separate launch step.
The homepage Admin footer link is removed; sign in directly at **`/admin`**.
The admin dashboard also omits the site footer.

Default balance: **2,400,000 HP**, **one manual attack every 60 seconds**, and
**40 attacks per raid day** per browser and shared network. Matching the current
weakness deals 150 damage instead of 100; every tenth personal hit adds 100.
A 100-person community making 20–40 mostly matching attacks daily should take
roughly **4–8 raid days**. This assumes active daily participation, not merely
100 community members. The fastest tested 100-person scenario finishes on day
four. Raid days are 24-hour periods from the first successful community hit.
No damage regenerates. Victory remains until the host opens a new raid.

The game refreshes every **5 seconds** while visible, with a local countdown
between updates. Shuffle and Kick continue their original **60-second** checks.
All attacks and limits are enforced by the server in an atomic transaction.
A lost-response retry uses the same receipt so that click cannot land twice.
No WebSocket server, Redis, Node runtime, new dependency, or remote database is
needed. Keep **one instance** in local mode.

**Admin → Community boss** provides pause, resume, new-raid difficulty, and a
private recovery download. Only the Superadmin may change a raid. Starting a
new raid requires confirmation and archives a summary; changing the HP there
applies only to the new raid. Game writes do not change race settings or wagers.

Read [docs/COMMUNITY_BOSS.md](docs/COMMUNITY_BOSS.md) for the rules, balancing,
privacy limits, and recovery process. Multi-day game progress is part of the
private recovery checkpoint; save it regularly and before redeploying.

## Storage and existing functionality

The previous release refused to start in production without PostgreSQL. That
requirement is removed. Storage now defaults to `STORAGE_MODE=local`, including
on DigitalOcean App Platform. A leftover `DATABASE_URL` is ignored in local
mode, so an unresolved database placeholder cannot stop startup. Web security
still uses production cookies and proxy handling; local storage does not turn
on Flask debug mode or weaken login protection.

The PostgreSQL driver is removed from the normal dependency list. Optional
compatibility for existing PostgreSQL installations remains separate.

A new **Private recovery file** download in Settings lets the Superadmin save
accounts, password hashes, the session signing key, race settings, overrides,
history, audit entries, bans, the last Top 15, and the complete community boss state. A fresh instance imports it
automatically from `private/recovery.seed.json`. Existing saved local state
always wins over seed files. Original provider credentials stay in the existing
configuration; the recovery download does not export the provider configuration.

## What persists on App Platform

**App Platform local files are temporary.** Redeploying, replacing, or scaling
an instance can discard changes made inside it. This includes edited race
dates, passwords, new accounts, overrides, history, and all community boss progress. A replacement starts
from the files committed to your repository, including your latest recovery
seed if you supplied one. Live standings and Kick status are fetched again.

The recovery download is a manual checkpoint, not automatic cloud persistence.
Save a new copy after important changes and add it to your private repository
before a planned redeploy. Changes since your last checkpoint can still be lost
in an unexpected container replacement. The admin panel and startup logs state
this limitation. Keep the app at **one instance** because each instance has its
own local file.

On a persistent Linux host, the same local file survives process restarts as
long as its disk is preserved. The application cannot make App Platform's
container disk persistent. DigitalOcean documents this behavior here:
[App Platform data storage](https://docs.digitalocean.com/products/app-platform/how-to/store-data/).

## Install and run

Use Python 3.12 or newer. The package pins Python 3.13.12 for App Platform.

```bash
python -m pip install -r requirements.txt
python wager_backend.py
```

Local URLs: `http://127.0.0.1:8080/` and `http://127.0.0.1:8080/admin`.
Install dependencies once during setup/build. Supporting Python modules are
imported automatically. Node is not required to run the website.

The default local file is `data/redhunllef.sqlite3`. The app creates it and its
tables automatically. Paths resolve from the installed project, so startup also
works from another working directory. Preserve `data/` when updating files on
a persistent host. Do not delete it to fix an unrelated deployment problem.

## DigitalOcean App Platform: no database setup

1. Replace the application files in your **private** GitHub repository with the
   contents of `redhunllef-rebuilt/` from this ZIP. Keep your existing provider
   configuration and any newer recovery file. If the code lives in a subfolder,
   choose that folder as the service's source directory.
2. Configure a **Python Web Service** with **one instance**. You do not need to
   add a database component.
3. Use these settings:

   | Setting | Value |
   | --- | --- |
   | Build command | `python -m pip install -r requirements.txt` |
   | Run command | `python wager_backend.py` |
   | HTTP port | `8080` |
   | Health check | `/healthz` |
   | Instances | `1` |

4. Set the following runtime environment variables:

   | Name | Value |
   | --- | --- |
   | `APP_ENV` | `production` |
   | `STORAGE_MODE` | `local` (also the default when omitted) |
   | `PORT` | `8080` |
   | `TRUST_APP_PLATFORM` | `1` |
   | `SESSION_COOKIE_SECURE` | `always` |

   `DATABASE_URL` is unnecessary and ignored in local mode. Remove an obsolete
   `${race-db.DATABASE_URL}` binding from the service if you added one, because
   DigitalOcean may try to resolve bindings before starting Python. Do not
   delete an existing database that might contain saved data.
5. Deploy. Startup should report **2026.09.22-no-regen** and **Local file ready; no
   external database is required**. Open the HTTPS app URL and `/admin`.
6. Reload your browser with Ctrl+F5. Review the published race dates and provider
   results. Publish the desired schedule if the original seeded race has ended.
7. After important changes, use **Settings → Private recovery file** and follow
   the recovery instructions below.

The included `app.yaml` has one web service and no database component or database
binding. Replace its repository placeholder before importing it. If your app
already has other components, edit its existing configuration instead of
replacing it wholesale with this standalone template. The `.env.example` file
is a reference; the app does not automatically read `.env` files.

`/healthz` checks the process. `/readyz` also checks storage and source freshness;
it can return 503 before the first successful source update or during an outage.
Use `/healthz` for deployment health checks so a Shuffle outage does not trigger
repeated container replacements.

## Original login, credentials, and dates

The original login is **gingrsnaps / enok2121**. Existing accounts keep their
current passwords when their local file or newer recovery seed is retained.
The protected Superadmin can add administrators from Settings. No management
script is required.

| File | Purpose |
| --- | --- |
| `private/settings.json` | Original Shuffle key, Kick client ID/secret, channel, campaign, defaults, and links. |
| `private/admin_store.seed.json` | Original account/password hash, saved dates, and original records. |
| `private/recovery.seed.json` | Optional newer checkpoint downloaded by you; not supplied as a blank file. |

The two supplied private configuration files and both logo assets match the
original uploaded bytes. Keep the configured ZIP, full-code document, recovery
files, and repository private. Public APIs never expose account hashes or
provider credentials.

Nonempty provider environment values override packaged credentials:
`SHUFFLE_API_KEY` (or legacy `API_KEY`), `KICK_CLIENT_ID`, and `KICK_CLIENT_SECRET`.
The remaining precedence is root `settings.json`, root `integrations.json`, then
`private/settings.json`. An explicit `SETTINGS_PATH` disables the implicit
private settings fallback. Restart after changing provider credentials.

The original admin seed saves **August 4–11, 2026, 6 PM Eastern**. The original
settings defaults instead contain August 18–25. Saved admin dates win. Neither
window is silently advanced at startup. Newer local state or your recovery seed
keeps its saved dates.

## Save and restore a private recovery file

1. Sign in as the Superadmin and open **Settings → Private recovery file**.
2. Choose **Download private recovery file**. The filename is
   `recovery.seed.json`. It contains password hashes and a session signing key;
   store it privately. The dashboard records when the export was generated and
   reports later hits, damage, and changes. It cannot confirm that you saved the
   download elsewhere. Expand **Check a recovery file before restoring** to
   validate its contents and review totals without changing the running site.
3. For a fresh App Platform deployment, add that file to your private GitHub
   repository as **`private/recovery.seed.json`**, then redeploy.
4. The app imports it automatically if no saved state exists. Check your login,
   dates, overrides, history, boss health, and personal raid progress. The saved Top 15 appears until a live check
   loads the complete current standings. The uncensored Code Red list and Kick
   status are fetched again.

A recovery seed never overwrites a populated local store. On a persistent host,
back up the existing project and `data/` before any deliberate replacement.
A corrupt recovery file stops import with an error rather than resetting your
accounts to the original defaults.

The ordinary **Download race backup** remains available to administrators and
excludes passwords/account records and the community boss. Its restore form previews the saved race
before replacing the current race; current accounts stay intact. Use the private
recovery download when account recovery is needed. Internal rollback checkpoints
remain local and do not protect against App Platform discarding the container.

## Upgrade an existing installation

Keep the current `data/` folder, any newer root settings/integrations files,
and any newer `private/recovery.seed.json`. Replace the application modules,
templates, and assets together. Back up before replacing files, install the
requirements, then run the same sole launcher.

For a fresh local store, initialization checks a recovery seed first, then
root `admin_store.json`, then the original packaged account seed. Existing saved
state takes priority over all seeds. Legacy files are read without modification;
password hashes are preserved. The migration records a private local checkpoint.

If you actually have newer accounts/settings in PostgreSQL, this local build
does not automatically copy them. Keep the database intact and export those
records before switching to local storage. Optional PostgreSQL compatibility
is described at the end of this README.

## Race publication and live updates

- Change dates under **Race → Save race settings → Confirm and publish race**.
  A side-by-side table lists every changed setting. Review it and use the
  bottom confirmation button. Changing the form after
  reviewing requires a new review. **Published window** shows saved dates;
  edited form values remain a draft until confirmed.
- Independent Shuffle and Kick jobs start automatically and run every **60
  seconds**. There is no live-mode switch or second worker command. Slow calls
  do not hold up the website or the other provider.
- Both public/admin pages use the same published snapshot and poll every 60
  seconds while visible. Returning to a hidden tab checks immediately. Public
  `/public-state` requests use ETags; unchanged data returns a body-free 304 and
  a fresh server-time header. Admin and personal game responses remain no-store.
- Manual refreshes queue one follow-up even if a check is already running.
  Repeated clicks coalesce. The admin briefly polls every two seconds after a
  manual request or date publication, then returns to its normal cadence.
- Every admin tab has a connection summary and expandable provider results.
  New failures open the details. A queued retry displays its reason and retry
  time. Request tickets connect completion to the requested refresh.
- Successes and failures from old settings cannot publish over a newer race.
  An old ordinary retry delay is cleared when dates change; provider rate limits
  and explicit `Retry-After` instructions are still honored.
- Failed checks retain the last results and mark them delayed. An error never
  fabricates zero wagers or labels Kick offline. Future races wait for their
  start; ended races continue checking their saved range for final corrections.
- Shuffle uses the original affiliate endpoint and `startTime`/`endTime` range.
  A rejected range never falls back to lifetime totals. Decimal calculations,
  original sum/max aggregation, $0.01 qualification, and existing weighting and
  prizes remain. Invalid source rows are disclosed; a wholly invalid response
  retains the previous board.
- Kick uses app-token authorization, caches tokens, and retries authentication
  once after HTTP 401. Unknown status differs from confirmed offline.

The earlier native form-action collision, JSON error handling, UTF-8 startup
fix, stopped-worker recovery, and draft preservation remain included. Provider
latency and browser scheduling can delay delivery; a 60-second interval does
not mean the external provider necessarily publishes new results every minute.

## Visitor IP addresses on DigitalOcean

`TRUST_APP_PLATFORM=1` tells the app to use the validated **DO-Connecting-IP**
header for visitor identity. DigitalOcean documents that header; do not use
`X-Forwarded-For` as a substitute for per-player cooldowns. Without the expected
header, game attacks are unavailable with a clear setup response instead of
silently sharing an ingress address across all players.

Set `TRUST_APP_PLATFORM=0` on a local/direct Python host. Forwarded headers are
then ignored. Enable the App Platform setting only behind its trusted ingress;
placing a directly accessible server behind an untrusted header permits spoofing.
Official reference: [DigitalOcean client IP header](https://docs.digitalocean.com/support/where-can-i-find-the-client-ip-address-of-a-request-connecting-to-my-app/).

## Dashboard and appearance

**Overview** shows the countdown, prize pool, player count, source freshness,
and shortcuts to race and boss controls. **Race** edits Eastern Time dates, all 15 prizes,
site text, links, channel, and campaign. DST edge cases receive field errors.

**Players** shows full usernames, weighted/raw totals, filters, exports, and
editable weighted overrides. Expand **Community wagerers** for up to 100
confirmed Code Red users, with search and copy buttons. Public usernames stay
masked as two characters plus six asterisks. Default loaded-player capacity is
300, configurable with `FULL_LEADERBOARD_MAX` from 100 to 10,000; filters operate
on loaded records. Overrides do not change source/raw totals.

**Settings** contains passwords, Superadmin account management, race backups,
private recovery, race history, redacted diagnostics, IP bans, and activity logs.
Native forms/navigation remain usable without JavaScript; automatic browser
updates require JavaScript.

The red theme uses the original logo's #ff2d2d, burgundy panels, red active tabs,
and darker red buttons. It includes responsive layouts, keyboard focus states,
and reduced-motion support. No remote fonts or frontend framework are required.

## Console output and troubleshooting

```text
START RedHunllef 2026.09.22-no-regen listening on 0.0.0.0:8080; storage=local SQLite.
STORAGE Local file ready; no external database is required.
LIVE Automatic Shuffle and Kick checks started; cadence=60s.
```

Hosted local storage also logs the App Platform persistence limitation. Provider
logs show the requested window, outcome, and duration without API credentials.

| Symptom | Action |
| --- | --- |
| Old "Attach PostgreSQL" startup error | The old release is still deployed. Replace the complete code and verify release 2026.09.22-no-regen; use `python wager_backend.py`. |
| DigitalOcean rejects a database variable binding | Remove the stale `DATABASE_URL` binding from service settings; local mode does not need it. |
| Missing Flask, Waitress, or tzdata | Install `requirements.txt` with the Python used to launch. |
| Login returns to login | Use the HTTPS app URL and the production cookie/proxy settings above. |
| Dates do not publish | Use the bottom **Confirm and publish race** button and verify **Published window**. |
| Refresh appears unchanged | Expand **Live connections**. It distinguishes unchanged/empty results from errors or queued retries. |
| Credentials fail with HTTP 401/403 | Check the provider permissions and selected credential source in diagnostics. |
| Edits disappeared after a redeploy | A new container started from repository seeds. Restore your saved checkpoint; unsaved-to-checkpoint changes cannot be recovered from the discarded disk. |
| Local storage cannot be read/written | Check disk space and directory permissions; preserve the existing file. |

## Game troubleshooting

| Symptom | Action |
| --- | --- |
| “Connection setup needed” | On App Platform set `TRUST_APP_PLATFORM=1` and check that ingress supplies `DO-Connecting-IP`. For direct/local hosting use `0`. Do not run a directly exposed server with proxy trust enabled. |
| Shared cooldown on Wi-Fi | Intended: one network shares the 60-second cooldown and 40-hit allowance. A separate signed browser identity also keeps its own allowance when its network changes. |
| “Retry last strike” | The response was lost. Click it to resend the same receipt safely. A state update may confirm the hit first. It never auto-attacks. |
| Progress changed after deploy | Local container state was replaced. A new instance starts from your last committed `private/recovery.seed.json`, or a fresh boss if it has none. |
| Raider name changed | Cookies were cleared/expired, a different browser is in use, or the host started a new raid. No account sign-in is needed. |
| Old raid form rejected | Another raid started after you opened the tab. Reload to review it before submitting controls again. |

## Verification

This release passes **86 Python application/game/calculation tests** and **35 DOM/CSS
checks**. Startup is exercised through an actual Waitress child process using
`python wager_backend.py`, production mode, and a leftover database placeholder.
Another check blocks importing psycopg and verifies production login with secure
cookies still works. Recovery tests verify changed passwords, accounts, dates,
overrides, and saved results on a fresh instance, along with authorization,
corrupt-file preservation, and existing-state precedence.

The suite retains date-publication, in-flight failure, automatic update,
manual refresh, privacy, and original field-envelope regressions. Real HTTP
transport to a local fixture server tests provider parsing and scheduled
publication; source data is synthetic. See `docs/VALIDATION.md` for browser
checks and limits.

Current successful live Shuffle/Kick connectivity and an actual DigitalOcean
deployment have not been verified from this workspace. Earlier external provider
probes timed out; the real deployment's progress/errors must be checked there.
Four optional PostgreSQL tests are skipped without a dedicated test database.

```bash
python -m unittest discover -s tests -v
```

Optional development interface checks (Node 22+, not required to deploy):

```bash
npm --prefix tests install --ignore-scripts
python tests/render_fixtures.py .test-fixtures
npm --prefix tests test
```

## Optional compatibility for an existing PostgreSQL deployment

This is not needed for the requested local-storage deployment. To deliberately
continue using an existing remote store, install `requirements-postgres.txt`,
set `STORAGE_MODE=postgres`, and retain `DATABASE_URL`, `APP_STATE_KEY`, and TLS
settings. Use the direct connection rather than a transaction-pooled URL;
provider coordination uses session advisory locks. The launcher remains
`python wager_backend.py`. An explicit PostgreSQL failure does not silently
fall back to a new local account store.

The CI workflow installs the optional driver and provisions a disposable database
for its PostgreSQL compatibility tests. Locally those tests require
`TEST_DATABASE_URL`; never point that variable at production.

## Files

`FILE_STRUCTURE.md` maps every supplied file. `FULL_CODE_BLOCKS.md` contains each
text file in its own complete block plus base64 for the original binary logos.
The ZIP contains the ready-to-use files. Python regenerates bytecode; it is not
shipped. Runtime state and test preview data are excluded from the ZIP.
