# RedHunllef — complete configured source

Release **2026.09.22-local**. Every text file is included below in its own complete code block. The two original binary logos are included as complete base64 blocks. The ZIP supplies the actual ready-to-use files. This document includes your original private credentials and account seed; keep it private.

Start with README.md and FILE_STRUCTURE.md. The only launch command is `python wager_backend.py`. FULL_CODE_BLOCKS.md is this generated document and is not recursively repeated inside itself.

## .env.example

```text
# Reference for App Platform environment settings. The app does not load .env.
APP_ENV=production
STORAGE_MODE=local
PORT=8080
TRUST_APP_PLATFORM=1
SESSION_COOKIE_SECURE=always
APP_STATE_KEY=redhunllef
# No DATABASE_URL is needed. A leftover value is ignored in local mode.
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
    services:
      postgres:
        image: postgres:16
        env:
          POSTGRES_DB: race_test
          POSTGRES_USER: race_test
          POSTGRES_PASSWORD: test_database_only
        ports:
          - 5432:5432
        options: >-
          --health-cmd "pg_isready -U race_test -d race_test"
          --health-interval 5s --health-timeout 5s --health-retries 10
    env:
      TEST_DATABASE_URL: postgresql://race_test:test_database_only@localhost:5432/race_test
      TEST_DATABASE_SSLMODE: disable
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with:
          python-version: '3.13'
      - run: python -m pip install -r requirements-postgres.txt
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
# Changes — 2026.09.22-local

Local-storage release: remove the production PostgreSQL startup requirement. Default to built-in SQLite, ignore stale DATABASE_URL values in local mode, and remove the PostgreSQL driver from normal requirements. App Platform configuration contains only the Python web service. Production cookies and proxy handling remain independent of storage.

Recovery: add a Superadmin-only private account/race export and automatic import from private/recovery.seed.json on a fresh instance. Existing saved state takes priority. The dashboard, logs, and README explicitly explain that App Platform local files do not persist through redeploys or container replacements; checkpoints are manual.


Date publication: the bottom button now submits the required confirmation and clearly says **Confirm and publish race**. Drafts no longer look like completed saves.

Refresh reliability: discard old-setting failure responses as well as successes; clear only obsolete ordinary backoff when dates change; retain provider rate limits. Keep one follow-up request when Refresh is pressed during an active check. Restart stopped workers from dashboard status reads.

Progress: every admin tab shows published dates and separate provider outcomes. Manual requests have completion tickets; date publication triggers short follow-up polling automatically. An in-flight browser read no longer drops an immediate refresh request.

Visuals: logo-red branding, burgundy surfaces, red buttons and active tabs, and readable progress panels. Original logo files are unchanged. No production dependency was added.

Verification: 57 Python tests and 20 DOM/CSS checks pass. A local HTTP fixture exercises date changes during a failed request and subsequent automatic publication; external Shuffle/Kick connectivity remains unverified here.

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
```

## FILE_STRUCTURE.md

```markdown
# File structure — 2026.09.22-local

Extracted project folder: `redhunllef-rebuilt/`. Run only `wager_backend.py`; supporting files are imported or served automatically.

| Path | Purpose |
| --- | --- |
| `.env.example` | Reference environment settings; not automatically loaded. |
| `.github/workflows/test.yml` | CI application, PostgreSQL, and interface checks. |
| `.gitignore` | Excludes local runtime state and generated development files. |
| `CHANGES.md` | What changed and why. |
| `FILE_STRUCTURE.md` | Complete file map (this file). |
| `FULL_CODE_BLOCKS.md` | Complete source blocks plus original logo assets encoded as base64. |
| `MANIFEST.json` | Release identifier and SHA-256 digests of source/document files. |
| `Procfile` | App Platform process entry: python wager_backend.py. |
| `README.md` | Setup, deployment, migration, operation, troubleshooting, verification limits. |
| `START_HERE.md` | Quick launch instructions and original account information. |
| `app.yaml` | One Python web service, no database component; edit the repository name. |
| `config.py` | Credential precedence, deployment configuration, fixed update interval. |
| `docs/VALIDATION.md` | Test record and explicit verification limits. |
| `integrations.py` | Bounded provider requests, response validation, Kick token renewal. |
| `private/admin_store.seed.json` | Original account/password hash and saved state, unchanged. |
| `private/settings.json` | Original configured Shuffle/Kick credentials and settings, unchanged. |
| `race.py` | Source normalization, exact rankings, overrides, Code Red list, freshness. |
| `race_support.py` | Shared validation, Eastern Time/DST, money formatting, backup helpers. |
| `requirements-postgres.txt` | Optional compatibility dependencies for explicitly selected PostgreSQL storage. |
| `requirements.txt` | Default Python dependencies; no PostgreSQL driver required. |
| `runtime.py` | Shared cached state and independent Shuffle/Kick background jobs. |
| `runtime.txt` | App Platform Python 3.13.12 pin. |
| `static/app.js` | Native browser controller, automatic polling, countdown, scoped DOM updates. |
| `static/redlogo.ico` | Original favicon. |
| `static/redlogo.png` | Original PNG brand asset. |
| `static/style.css` | Responsive public/admin styling, focus states, reduced-motion support. |
| `storage.py` | SQLite/PostgreSQL transactions, migrations, account state, recovery checkpoints. |
| `store_schema.py` | Additive validation of original accounts and saved race state. |
| `templates/admin.html` | Rendered admin template. |
| `templates/admin_overview.html` | Rendered admin overview template. |
| `templates/admin_players.html` | Rendered admin players template. |
| `templates/admin_race.html` | Rendered admin race template. |
| `templates/admin_settings.html` | Rendered admin settings template. |
| `templates/base.html` | Rendered base template. |
| `templates/error.html` | Rendered error template. |
| `templates/index.html` | Rendered index template. |
| `templates/login.html` | Rendered login template. |
| `templates/macros.html` | Rendered macros template. |
| `tests/package.json` | Optional development test dependency; no Node runtime needed by the site. |
| `tests/render_fixtures.py` | Generate interface fixtures from actual templates. |
| `tests/test_app.py` | Application/calculation/startup tests with synthetic provider responses. |
| `tests/test_frontend.cjs` | DOM/CSS regressions including update cadence and draft preservation. |
| `tests/test_postgres.py` | Integration tests for a dedicated disposable PostgreSQL database. |
| `wager_backend.py` | Only launch script; Waitress, routes, native login, admin actions, session protection. |

Runtime-created local data lives under `data/` and is excluded from this ZIP. App Platform uses automatic local storage by default; local changes are temporary on that platform. An optional private/recovery.seed.json, downloaded by the Superadmin, can seed a fresh instance and is not supplied as a blank file. Compiled bytecode is regenerated by Python and is not shipped. No original runtime account file is overwritten by extracting the package.
```

## Procfile

```text
web: python wager_backend.py
```

## README.md

````markdown
# RedHunllef Wager Race

Release **2026.09.22-local**. Run the complete app with **`python wager_backend.py`**.
No PostgreSQL service, database connection string, account-creation script, or
separate update worker is required. Python's built-in SQLite creates a local
file automatically. The red theme, original credentials, original Superadmin,
public Top 15, private Code Red list, and automatic 60-second updates remain.

## What this release fixes

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
history, audit entries, bans, and the last Top 15. A fresh instance imports it
automatically from `private/recovery.seed.json`. Existing saved local state
always wins over seed files. Original provider credentials stay in the existing
configuration; the recovery download does not export the provider configuration.

## What persists on App Platform

**App Platform local files are temporary.** Redeploying, replacing, or scaling
an instance can discard changes made inside it. This includes edited race
dates, passwords, new accounts, overrides, and history. A replacement starts
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
5. Deploy. Startup should report **2026.09.22-local** and **Local file ready; no
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
   store it privately.
3. For a fresh App Platform deployment, add that file to your private GitHub
   repository as **`private/recovery.seed.json`**, then redeploy.
4. The app imports it automatically if no saved state exists. Check your login,
   dates, overrides, and history. The saved Top 15 appears until a live check
   loads the complete current standings. The uncensored Code Red list and Kick
   status are fetched again.

A recovery seed never overwrites a populated local store. On a persistent host,
back up the existing project and `data/` before any deliberate replacement.
A corrupt recovery file stops import with an error rather than resetting your
accounts to the original defaults.

The ordinary **Download race backup** remains available to administrators and
excludes passwords/account records. Its restore form previews the saved race
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
  The bottom button submits confirmation. **Published window** shows the saved
  dates; edited form values remain a draft until confirmed.
- Independent Shuffle and Kick jobs start automatically and run every **60
  seconds**. There is no live-mode switch or second worker command. Slow calls
  do not hold up the website or the other provider.
- Both public/admin pages use the same published snapshot and poll every 60
  seconds while visible. Returning to a hidden tab checks immediately.
- Manual refreshes queue one follow-up even if a check is already running.
  Repeated clicks coalesce. The admin briefly polls every two seconds after a
  manual request or date publication, then returns to its normal cadence.
- Every admin tab shows queued, checking, changed, unchanged, empty, and failed
  results. A queued retry displays its reason and retry time. Request tickets
  connect the completion message to the requested refresh.
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

## Dashboard and appearance

**Overview** shows the countdown, prize pool, player count, source freshness,
and separate provider results. **Race** edits Eastern Time dates, all 15 prizes,
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
START RedHunllef 2026.09.22-local listening on 0.0.0.0:8080; storage=local SQLite.
STORAGE Local file ready; no external database is required.
LIVE Automatic Shuffle and Kick checks started; cadence=60s.
```

Hosted local storage also logs the App Platform persistence limitation. Provider
logs show the requested window, outcome, and duration without API credentials.

| Symptom | Action |
| --- | --- |
| Old "Attach PostgreSQL" startup error | The old release is still deployed. Replace the complete code and verify release 2026.09.22-local; use `python wager_backend.py`. |
| DigitalOcean rejects a database variable binding | Remove the stale `DATABASE_URL` binding from service settings; local mode does not need it. |
| Missing Flask, Waitress, or tzdata | Install `requirements.txt` with the Python used to launch. |
| Login returns to login | Use the HTTPS app URL and the production cookie/proxy settings above. |
| Dates do not publish | Use the bottom **Confirm and publish race** button and verify **Published window**. |
| Refresh appears unchanged | Read **Live update progress**. It distinguishes unchanged/empty results from errors or queued retries. |
| Credentials fail with HTTP 401/403 | Check the provider permissions and selected credential source in diagnostics. |
| Edits disappeared after a redeploy | A new container started from repository seeds. Restore your saved checkpoint; unsaved-to-checkpoint changes cannot be recovered from the discarded disk. |
| Local storage cannot be read/written | Check disk space and directory permissions; preserve the existing file. |

## Verification

This release passes **57 Python application/calculation tests** and **20 DOM/CSS
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
````

## START_HERE.md

````markdown
# RedHunllef — start here

Release **2026.09.22-local**. No PostgreSQL service or DATABASE_URL is needed.
Extract the complete folder. Install dependencies once:

```bash
python -m pip install -r requirements.txt
```

Run only:

```bash
python wager_backend.py
```

On DigitalOcean App Platform use those same build/run commands, port **8080**,
health check **/healthz**, and **one instance**. Runtime environment:

```text
APP_ENV=production
STORAGE_MODE=local
TRUST_APP_PLATFORM=1
SESSION_COOKIE_SECURE=always
```

Remove an obsolete DATABASE_URL binding if you added one. Local mode ignores
that variable; DigitalOcean may still try to resolve bindings before startup.
No new database component is required. Keep existing data-bearing resources.

The original supplied login is **gingrsnaps / enok2121**. Original Shuffle/Kick
credentials and the account seed are included. Existing local state or a newer
recovery seed retains its accounts, passwords, and dates.

**App Platform replaces local files during redeploys/container replacements.**
After important edits, use **Settings → Private recovery file**. Add the
resulting file to your private repository as `private/recovery.seed.json`
before redeploying to restore that checkpoint automatically. New edits after
your latest saved checkpoint can still be lost. This is manual recovery,
not automatic persistent cloud storage. Read README.md for the full process.

For a persistent host, preserve the existing `data/` folder when replacing code.
The application automatically creates its local file and imports the seed;
there is no account-creation script or separate worker to run.

The original seed saves August 4–11, 2026, 6 PM Eastern. To publish your desired
schedule: **Race → Save race settings → Confirm and publish race** in the bottom
bar. Verify **Published window**. Both providers update automatically every
60 seconds. Read **Live update progress** for actual provider outcomes.

The red theme, original logos, refresh/publication fixes, UTF-8 startup handling,
and private 100-user Code Red list remain. Reload with Ctrl+F5 after deploying;
the release label must show **2026.09.22-local**.
````

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
      - key: STORAGE_MODE
        value: local
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

## config.py

```python
"""One configuration path; saved race settings win after the first import."""
import os
import re
from pathlib import Path

from race_support import DEFAULT_PRIZES, canonical_site, read_json

RELEASE = "2026.09.22-local"
INTERVAL = 60


class Config:
    def __init__(self, root=None):
        self.root = Path(root or Path(__file__).parent).resolve()
        path = lambda name, default: Path(os.getenv(name) or self.root / default)
        self.legacy = path("ADMIN_STORE_PATH", "admin_store.json")
        self.seed = path("ADMIN_SEED_PATH", "private/admin_store.seed.json")
        self.recovery = path("RECOVERY_SEED_PATH", "private/recovery.seed.json")
        self.db_path = path("LOCAL_DATABASE_PATH", "data/redhunllef.sqlite3")
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
        # Local storage needs no account, service, or connection string. A stale
        # DATABASE_URL from an earlier deployment cannot break this default.
        self.storage_mode = os.getenv("STORAGE_MODE", "local").strip().lower()
        if self.storage_mode not in {"local", "postgres"}:
            raise ValueError("STORAGE_MODE must be local or postgres.")
        supplied_url = os.getenv("DATABASE_URL", "").strip()
        self.db_url = supplied_url if self.storage_mode == "postgres" else ""
        self.ignored_database_url = bool(supplied_url and not self.db_url)
        if self.storage_mode == "postgres" and not self.db_url:
            raise ValueError("STORAGE_MODE=postgres needs DATABASE_URL. Use STORAGE_MODE=local for automatic local storage.")
        self.state_key = os.getenv("APP_STATE_KEY", "redhunllef")
        if not re.fullmatch(r"[A-Za-z0-9_-]{1,64}", self.state_key):
            raise ValueError("APP_STATE_KEY must contain 1–64 letters, numbers, underscores or hyphens.")
        # Storage and web security are independent: local storage on App Platform
        # still uses production cookies, proxy handling, and the normal server.
        mode = os.getenv("APP_ENV", "production" if self.db_url or "PORT" in os.environ else "local")
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
        self.sslmode = os.getenv("DATABASE_SSLMODE", "require")
        if self.db_url and self.sslmode not in {"require", "verify-full", "verify-ca", "disable"}:
            raise ValueError("Unsupported DATABASE_SSLMODE.")
        self.sslrootcert = os.getenv("DATABASE_SSLROOTCERT", "")
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

## docs/VALIDATION.md

```markdown
# Verification record — 2026.09.22-local

Verified in the supplied Linux workspace on 2026-09-22.

| Check | Result |
| --- | --- |
| Python tests | 57 passed. |
| PostgreSQL integration tests | 4 skipped: no dedicated database supplied. CI provisions one. |
| DOM and CSS checks | 20 passed with jsdom 26.1.0; no browser build required in production. |
| Date publication | Bottom confirmation button submits confirmation and persists the edited window. |
| Superseded failure | An old-window HTTP failure cannot mark the new race as failed or impose its ordinary retry delay. Explicit provider rate limits remain honored. |
| Concurrent refresh | An active provider check retains one follow-up request; repeated clicks coalesce. An in-flight browser read schedules a follow-up instead of dropping the request. |
| HTTP date-change and scheduled update | Real Requests transport to a local HTTP fixture: old-range failure, new-range success, then a second automatic publication without a refresh click. Only this isolated test uses an accelerated timer. |
| Progress feedback | Saved window, checking, completed, and rate-limit retry messages appear on all admin tabs; unsaved input values remain intact. |
| Windows encoding regression | Exact original CP1252 error reproduced before the fix. Startup and existing-state preservation pass after the fix, using a simulated Windows default on Linux. |
| Named form collision | Test models the native input/property collision: the old script posts to `/[object HTMLInputElement]`; the corrected script posts to `/admin/action` with CSRF/action/service intact. |
| Manual refresh publication | Real worker threads with synthetic provider data update both the masked public board and uncensored admin board after an authenticated refresh. |
| Refresh error handling | JSON 400/401/404/405/500/503 cases checked; native HTML errors still render. |
| Empty board | Waiting, empty source, campaign filter, zero weighted qualification, and failure/recovery checked. |
| Actual HTTP startup | Passed: child process launched with `python wager_backend.py` in production/local mode with a stale database binding, served `/healthz` and `/admin`, started both automatic jobs, and shut down. |
| Production without PostgreSQL | Passed with no usable DATABASE_URL and psycopg imports blocked; original accounts and secure HTTPS login remain functional. |
| Private recovery | Passed: only Superadmin can download; fresh-instance import preserves password changes, accounts, dates, overrides, history, signing key, and saved Top 15. A newer local store wins over seeds; corrupt recovery files stop import without resetting accounts. |
| Supplied credential files | Match original uploaded bytes. |
| Original Superadmin | Original password/hash verified; native login and all four dashboard tabs return successfully. |
| Account migration | Preserves every original account field; adds auth_version for session revocation. |
| Real Shuffle request | Timeout; successful provider connectivity not verified. |
| Real Kick authorization | Timeout; successful provider connectivity not verified. |
| Native browser checks | Passed in Chromium 153.0.8010.0 against Waitress with isolated accounts and synthetic providers: login, actual refresh POST/202, bottom-button date confirmation, published rows, expanded 100-user Code Red list, and the private recovery download. Production local-storage mode is used with a cookie override only for the HTTP test fixture; secure production cookies are separately checked over simulated HTTPS. No JavaScript errors; no horizontal overflow at 390 px. |
| Browser screenshot review | Public page/admin red theme retained; the new private recovery section was reviewed at mobile width. Test previews contain synthetic wagers and stream status. |
| DigitalOcean deployment | Not performed; no deployed site was provided for validation. |

The Python tests cover valid/invalid/mixed source responses, stale-cache
retention, original field envelopes, date-range requests with no lifetime
fallback, Kick reauthorization, independent workers, in-flight settings changes,
protected routes, CSRF, session revocation, login rate limits, account roles,
CSV safety, overrides, archive/restore confirmation, corrupt-store preservation,
DST validation, exact monetary calculations, and sole-script startup.

DOM checks render the real templates and verify unique IDs/label targets,
automatic polling, manual polling cadence, state/countdown boundaries, form
preservation across updates, Code Red expansion/search, text-only username
rendering, and session/proxy error recovery. They use synthetic source data.

The included PostgreSQL checks cover transactional revision conflicts, separate
live writes, advisory locks, import from the old JSONB table, and rollback of a
failed admin save. Run them against a disposable database before relying on a
first production migration. The code does not substitute a passing mocked SQL
check for a real database test.

The native form-property collision is emulated explicitly in jsdom because its default form implementation does not reproduce this browser behavior. The corrected refresh was also clicked in actual Chromium. Neither verification is a claim of a successful live Shuffle response.
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

## requirements-postgres.txt

```text
# Optional compatibility for an existing PostgreSQL deployment; not needed by
# the default local-storage build. Select STORAGE_MODE=postgres explicitly.
-r requirements.txt
psycopg[binary]==3.3.5
```

## requirements.txt

```text
Flask==3.1.3
requests==2.34.2
waitress==3.0.2
tzdata==2026.3
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
                            storage="PostgreSQL" if self.store.pg else "Local file (automatic)", settings_revision=self.revision,
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
  'use strict';
  const id = name => document.getElementById(name);
  const text = (node, value) => {
    // Only leaf labels can be text destinations. Never erase a page or form.
    if (!node) return;
    if (node.childElementCount || ['BODY','MAIN','FORM','HTML'].includes(node.tagName)) throw new Error('Invalid text destination');
    if (node.textContent !== String(value ?? '')) node.textContent = String(value ?? '');
  };
  const notice = (name, value) => { const node=id(name); if(node) {node.hidden=!value; text(node,value);} };
  const currency = value => new Intl.NumberFormat('en-US',{style:'currency',currency:'USD'}).format(Number(value)||0);
  const eastern = new Intl.DateTimeFormat('en-US',{timeZone:'America/New_York',month:'short',day:'numeric',year:'numeric',hour:'numeric',minute:'2-digit',timeZoneName:'short'});
  const date = value => value ? eastern.format(new Date(value*1000)) : 'Waiting for first source update';
  document.documentElement.classList.add('js');
  let toastTimer;
  function toast(message) { notice('toast',message); clearTimeout(toastTimer); toastTimer=setTimeout(()=>notice('toast',''),4000); }
  document.addEventListener('click',async event=>{
    const button=event.target.closest('[data-copy]');
    if(!button) return;
    try { await navigator.clipboard.writeText(button.dataset.copy); toast('Username copied.'); }
    catch { toast('Select and copy the username manually.'); }
  });
  let dirty=false;
  document.querySelectorAll('[data-dirty]').forEach(form=>{
    const initial=new URLSearchParams(new FormData(form)).toString();
    const update=()=>{dirty=new URLSearchParams(new FormData(form)).toString()!==initial; text(id('saveLabel'),dirty?'Unsaved changes':'All changes saved');};
    form.addEventListener('input',update);
    form.addEventListener('change',update);
    form.addEventListener('reset',()=>setTimeout(update,0));
    form.addEventListener('submit',()=>{dirty=false;});
  });
  window.addEventListener('beforeunload',event=>{if(dirty){event.preventDefault();event.returnValue='';}});
  document.querySelectorAll('[data-confirm]').forEach(form=>form.addEventListener('submit',event=>{
    if(!window.confirm(form.dataset.confirm)) event.preventDefault();
  }));
  id('raceForm')?.addEventListener('input',()=>{
    const sum=[...id('raceForm').querySelectorAll('[name^="prize_"]')].reduce((n,input)=>n+Number(input.value.replace(/[$,\s]/g,'')),0);
    text(id('prizeTotal'),Number.isFinite(sum)?currency(sum)+' total':'Review prize amounts');
  });
  // The date picker stores Eastern local wall time. Server validation handles
  // nonexistent/ambiguous DST times; a shortcut never silently publishes a race.
  function easternInput(stamp) {
    const parts=new Intl.DateTimeFormat('en-US',{timeZone:'America/New_York',year:'numeric',month:'2-digit',day:'2-digit',hour:'2-digit',minute:'2-digit',hourCycle:'h23'}).formatToParts(new Date(stamp));
    const v=Object.fromEntries(parts.map(p=>[p.type,p.value])); return `${v.year}-${v.month}-${v.day}T${v.hour}:${v.minute}`;
  }
  function daysAfter(value,days) { const d=new Date(value+'Z');d.setUTCDate(d.getUTCDate()+days);return d.toISOString().slice(0,16); }
  id('startNow')?.addEventListener('click',()=>{
    id('f-start_et').value=easternInput(Date.now());id('f-end_et').value=daysAfter(id('f-start_et').value,7);
    id('f-start_et').dispatchEvent(new Event('input',{bubbles:true}));
  });
  id('nextRace')?.addEventListener('click',()=>{
    const start=id('f-start_et'),end=id('f-end_et');
    const duration=Math.max(1,Math.round((new Date(end.value+'Z')-new Date(start.value+'Z'))/86400000)||7);
    start.value=end.value||easternInput(Date.now());end.value=daysAfter(start.value,duration);
    start.dispatchEvent(new Event('input',{bubbles:true}));toast('Draft prepared. Review the dates before saving.');
  });

  if(!document.body.dataset.feed) return;
  const isAdmin=document.body.dataset.page==='admin';
  let site={}, offset=0, sourceAt=0, jobs={}, busy=false, timer, next=0, urgentUntil=0;
  let pollAgain=false, lastWork='', receipt=null;
  let participantVersion='',redVersion='';
  try {const boot=JSON.parse(document.body.dataset.bootstrap);site=boot.site;offset=boot.server_time*1000-Date.now();} catch {}
  function clock() {
    if(document.hidden) return;
    const now=(Date.now()+offset)/1000;
    const state=!site.start_time||site.end_time<=site.start_time?'unconfigured':now<site.start_time?'upcoming':now>=site.end_time?'ended':'active';
    const badge=id('raceBadge');text(badge,state.charAt(0).toUpperCase()+state.slice(1));
    if(badge) badge.className='badge state-'+state;
    const left=Math.max(0,Math.ceil((state==='upcoming'?site.start_time:site.end_time)-now));
    text(id('countdown'),state==='unconfigured'?'Set the race dates':state==='ended'?'Race complete':`${Math.floor(left/86400)}d ${String(Math.floor(left/3600)%24).padStart(2,'0')}h ${String(Math.floor(left/60)%60).padStart(2,'0')}m ${String(left%60).padStart(2,'0')}s`);
    text(id('clockLabel'),state==='upcoming'?'STARTS IN':state==='active'?'RACE ENDS IN':'RACE SCHEDULE');
    text(id('raceWindow'),site.start_time?date(site.start_time)+' → '+date(site.end_time):'Choose the race dates in Race settings.');
    if(id('endedNotice')) id('endedNotice').hidden=state!=='ended';
    if(sourceAt) text(id('sourceTime'),'Source checked '+Math.max(0,Math.floor(now-sourceAt))+'s ago');
    for(const [name,job] of Object.entries(jobs)) {
      const remaining=Math.max(0,Math.ceil(job.next_check-now));
      text(id(name+'Timing'),job.state==='checking'?'Checking now…':`${job.duration_ms||0} ms · ${job.next_check?'Next check in '+remaining+'s':'Check queued'} · Last success: ${date(job.last_success)}`);
    }
  }
  function filterRed() {
    const q=(id('redSearch')?.value||'').trim().toLowerCase();
    id('redBody')?.querySelectorAll('[data-red-name]').forEach(row=>row.hidden=!row.dataset.redName.toLowerCase().includes(q));
  }
  id('redSearch')?.addEventListener('input',filterRed);
  function checkingSoon(job) {
    const pending=job.pending||job.requested>job.completed||job.state==='queued';
    return job.state==='checking'||(pending&&(!job.next_check||job.next_check<=(Date.now()+offset)/1000+3));
  }
  function progress(value) {
    for(const name of ['shuffle','kick']) {
      const job=jobs[name]||{}, pending=job.pending||job.requested>job.completed||job.state==='queued';
      let message='Automatic check is starting.';
      if(job.state==='checking') message=job.pending?'Checking now; your follow-up refresh is queued.':'Checking the provider now…';
      else if(pending) {
        message=job.next_check>(Date.now()+offset)/1000+3?'Queued. Retry scheduled for '+date(job.next_check)+'.':'Refresh queued; waiting for the worker.';
        if(job.error) message+=' Last check'+(job.http_status?' (HTTP '+job.http_status+')':'')+': '+job.error;
      }
      else if(job.error) message='Check failed'+(job.http_status?' (HTTP '+job.http_status+')':'')+': '+job.error;
      else if(name==='shuffle'&&['updated','unchanged'].includes(job.result)) message=(job.result==='updated'?'Published ':'Confirmed ')+(value.count||0)+' qualifying players. Last check: '+date(job.completed_at)+'.';
      else if(name==='shuffle'&&job.result==='empty') message=value.leaderboard_message||'Check completed; no qualifying wagers were returned.';
      else if(['upcoming','unconfigured'].includes(job.result)) message=value.leaderboard_message||'Waiting for the configured race to start.';
      else if(job.result==='superseded') message='The old settings were superseded; a check for the current settings is queued.';
      else if(job.result==='shared') message='Another app instance is checking this provider.';
      else if(name==='kick'&&['live','offline'].includes(job.result)) message='Confirmed '+job.result+' on Kick. Last check: '+date(job.completed_at)+'.';
      text(id(name+'Progress'),message);
    }
    text(id('publishedWindow'),'Published window: '+date(site.start_time)+' → '+date(site.end_time));
    const work=JSON.stringify([value.runtime_id,...Object.values(jobs).map(job=>[job.requested,job.runs,job.state])]);
    if(work!==lastWork&&Object.values(jobs).some(checkingSoon)) urgentUntil=Date.now()+60000;
    lastWork=work;
    if(receipt&&value.runtime_id) {
      if(receipt.runtime_id!==value.runtime_id) {receipt=null;toast('The backend restarted. Current update progress is shown below.');}
      else if(Object.entries(receipt.requests).every(([name,target])=>jobs[name]?.completed>=target)) {
        const failed=Object.keys(receipt.requests).some(name=>jobs[name]?.error);
        toast(failed?'Refresh finished with a provider error. See update progress below.':'Refresh finished. See the update result below.');
        receipt=null;
      }
    }
  }
  function cell(value,className='') {const td=document.createElement('td');td.textContent=String(value??'—');td.className=className;return td;}
  function updateTable(body,rows,red=false) {
    if(!body) return;
    const encoded=JSON.stringify(rows);
    if(encoded===(red?redVersion:participantVersion)) return;
    if(red) redVersion=encoded; else participantVersion=encoded;
    const scroll=body.closest('.table-scroll'), top=scroll?.scrollTop,left=scroll?.scrollLeft;
    const focused=document.activeElement, focusRow=focused?.closest('tr'), focusName=focusRow?.dataset.player||focusRow?.dataset.redName;
    const focusCopy=focused?.hasAttribute('data-copy');
    const fragment=document.createDocumentFragment();
    rows.forEach((r,index)=>{
      const tr=document.createElement('tr');tr.dataset[red?'redName':'player']=r.username;
      tr.append(cell(red?index+1:r.rank,'rank'));
      const name=cell('');const strong=document.createElement('strong');strong.textContent=r.username;name.append(strong);
      const copy=document.createElement('button');copy.type='button';copy.className='copy-button';copy.dataset.copy=r.username;copy.textContent='⧉';copy.setAttribute('aria-label','Copy '+r.username);name.append(copy);
      if(!red&&r.source==='override') {const label=document.createElement('span');label.className='tag';label.textContent='Adjusted';name.append(label);}
      tr.append(name,cell(red?r.weighted:r.wager,'number accent'));
      if(!red) tr.append(cell(r.original_weighted_str,'number'));
      tr.append(cell(red?r.raw:r.raw_wager_str,'number'));
      if(!red) {const action=cell(''),link=document.createElement('a');link.href='/admin?tab=players&edit='+encodeURIComponent(r.username)+'#override';link.className='text-link';link.textContent='Edit';action.append(link);tr.append(action);}
      fragment.append(tr);
    });
    if(!rows.length) {const tr=document.createElement('tr'),td=cell(red?'No confirmed Code Red wagerers for this window.':'No matching qualifying wagers.','empty');td.colSpan=red?4:6;tr.append(td);fragment.append(tr);}
    body.replaceChildren(fragment);
    if(scroll){scroll.scrollTop=top;scroll.scrollLeft=left;}
    if(focusName) [...body.rows].find(row=>(row.dataset.player||row.dataset.redName)===focusName)?.querySelector(focusCopy?'button':'a')?.focus({preventScroll:true});
    if(red) filterRed();
  }
  function apply(value,began) {
    if(!value.site||!value.freshness||!Number.isFinite(value.server_time)) throw new Error('The update response is incomplete.');
    site=value.site;offset=value.server_time*1000-(began+Date.now())/2;sourceAt=value.freshness.updated_at;
    text(id('raceTitle'),site.race_title);text(id('raceDescription'),site.race_description);text(id('sponsorName'),site.sponsor_name);
    text(id('poolTotal'),site.total_prize);text(id('playerCount'),value.count);
    text(id('dataState'),value.freshness.label);text(id('sourceTime'),date(sourceAt));
    notice('leaderboardMessage',value.leaderboard_message||'');
    notice('sourceWarning',[value.freshness.warning,isAdmin?value.freshness.error:''].filter(Boolean).join(' '));
    document.querySelectorAll('[data-site-text]').forEach(node=>text(node,site[node.dataset.siteText]));
    document.querySelectorAll('[data-site-link]').forEach(a=>{const href=site[a.dataset.siteLink];a.hidden=!href;if(href&&/^https?:\/\//.test(href))a.href=href;});
    if(id('sponsorLink')&&/^https?:\/\//.test(site.sponsor_url)) id('sponsorLink').href=site.sponsor_url;
    if(isAdmin) {
      jobs=value.jobs||{};
      progress(value);
      updateTable(id('participantsBody'),value.participants||[]);
      if(id('codeRed')?.open&&value.red) updateTable(id('redBody'),value.red,true);
      text(id('redCount'),Math.min(100,value.red_total||0)+' / 100');
      text(id('redMembership'),(value.diagnostics?.missing_campaign||0)+' source rows have no campaign metadata; membership cannot be verified for those rows.');
      for(const name of ['shuffle','kick']) text(id(name+'Message'),jobs[name]?.error || (name==='shuffle'?value.freshness.label:value.stream?.available?(value.stream.live?'Live on Kick':'Kick offline'):'Kick status unavailable'));
      const stream=value.stream||{};
      text(id('streamDetail'),stream.available&&stream.live?[stream.title,stream.viewers?stream.viewers.toLocaleString()+' watching':'Viewer count unavailable'].filter(Boolean).join(' · '):'');
      document.querySelectorAll('[data-diagnostic]').forEach(node=>text(node,value.diagnostics?.[node.dataset.diagnostic]));
      text(id('browserCheck'),'Dashboard checked '+date(value.server_time)+' · next update in 60 seconds');
    } else {
      const rows=new Map((value.rows||[]).map(row=>[row.rank,row]));
      document.querySelectorAll('[data-rank]').forEach(node=>{const n=Number(node.dataset.rank),row=rows.get(n);text(node.querySelector('[data-name]'),row?.username||'Open position');text(node.querySelector('[data-wager]'),row?.wager||'$0.00');text(node.querySelector('[data-prize]'),currency(site.prizes[n]));});
      text(id('streamStatus'),!value.stream?.available?'Kick status unavailable':value.stream.live?'● Live on Kick':'Kick offline');
    }
    clock();
  }
  async function getJSON(url,options={}) {
    const controller=new AbortController(),timeout=setTimeout(()=>controller.abort(),10000);
    try {
      const response=await fetch(url,{...options,credentials:'same-origin',cache:'no-store',signal:controller.signal,headers:{Accept:'application/json'}});
      if(response.status===401) throw new Error('Your session expired. Sign in again to resume updates.');
      if(response.redirected&&response.url&&new URL(response.url,location.origin).pathname==='/admin/login') {
        throw new Error('Your session expired. Sign in again to resume updates.');
      }
      if(!response.headers.get('content-type')?.includes('application/json')) {
        const hint=response.status===404?'The update endpoint was not found. Reload the page after installing the complete update.':
          response.status>=500?'Check the backend runtime logs. Previous results are retained.':
          'Reload the page and sign in again if needed.';
        // Never render an HTML error/proxy page into the dashboard.
        throw new Error(`Expected JSON but received a non-JSON response (HTTP ${response.status}). ${hint}`);
      }
      let value;
      try {value=await response.json();}
      catch {throw new Error(`The server returned invalid JSON (HTTP ${response.status}). Check the runtime logs.`);}
      if(!response.ok)throw new Error(`${value?.error||'The server could not complete this request.'} (HTTP ${response.status})`);
      return value;
    } finally {clearTimeout(timeout);}
  }
  async function poll() {
    if(document.hidden) return;
    if(busy) {pollAgain=true;return;}
    busy=true;clearTimeout(timer);
    const began=Date.now();
    try {
      const url=new URL(document.body.dataset.feed,location.origin);
      if(isAdmin) {for(const [key,value] of new URLSearchParams(location.search))url.searchParams.set(key,value);if(id('codeRed')?.open)url.searchParams.set('code_red','1');}
      const result=await getJSON(url);apply(result,began);notice('networkError','');
      if(result.release&&result.release!=='2026.09.22-local') notice('networkError','A newer version was deployed. Save your draft, then reload.');
    } catch(error) {notice('networkError',error.name==='AbortError'?'Dashboard request timed out. Previous results are retained; updates will retry.':error.message);}
    finally {
      busy=false;
      if(!next) next=began+60000;
      else if(next<=began) next+=60000*(Math.floor((began-next)/60000)+1);
      if(next<=Date.now())next+=60000*(Math.floor((Date.now()-next)/60000)+1);
      const urgent=Date.now()<urgentUntil&&Object.values(jobs).some(checkingSoon);
      const delay=pollAgain?50:urgent?2000:Math.max(250,next-Date.now());
      pollAgain=false;
      if(!document.hidden)timer=setTimeout(poll,delay);
    }
  }
  document.querySelectorAll('[data-refresh]').forEach(form=>form.addEventListener('submit',async event=>{
    event.preventDefault();const button=form.querySelector('button');if(button.disabled)return;button.disabled=true;
    try {
      // A hidden input named "action" shadows form.action in real browsers.
      // Read the HTML attribute so every refresh reaches the backend route.
      const value=await getJSON(form.getAttribute('action'),{method:'POST',body:new FormData(form)});
      receipt=value.requests?{runtime_id:value.runtime_id,requests:value.requests}:null;
      jobs=value.jobs||jobs;
      toast(value.message);urgentUntil=Date.now()+60000;next=0;await poll();
    }
    catch(error){toast(error.message);}finally{button.disabled=false;}
  }));
  id('codeRed')?.addEventListener('toggle',()=>{if(id('codeRed').open){next=0;poll();}});
  document.addEventListener('visibilitychange',()=>{clearTimeout(timer);if(!document.hidden){next=0;poll();}});
  window.addEventListener('pageshow',event=>{if(event.persisted){next=0;poll();}});
  clock();setInterval(clock,1000);poll();
})();
```

## static/redlogo.ico

Complete binary file encoded as base64.

```base64
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//96ev//e3v//2lp7v8kJKn/HByh/x8fpP9fX+X/bGzo/xoabP8PD1z/EBBd/RAQXVYQEF0AAAAB/wAAAf8AAAH/AAAB/wAAAf8AAAD/AAAA/wAAAP8ZGZH/PT3//9zc///AwL7/CAgJ/wAAAP8NDQ7/x8fH////////////////////////////0NDR/xISE/8AAAD/BQUG/7W1s//k5P//QUH+/yws/v8tLf79LS3+Vi0t/gAAAAD/AAAA/wAAAP8AAAD/AAAA/wAAAP8AAAD/AAAA/xkZkf89Pf//3Nz//8DAvv8ICAj/AAAA/w0NDf/Hx8f////////////////////////////Q0ND/EhIS/wAAAP8FBQX/tbWz/+Tk//9BQf//LCz//y0t//0tLf9WLS3/AAAAAP8AAAD/AAAA/wAAAP8AAAD/AAAA/wEBB/8EBBT/Gxub/zs7///Nzf//s7PD/wwMHv8DAxX/EBAi/7q6zP/w8P//7e3//+3t///t7f//8PD//8LC1P8UFCb/AwMV/wgIGv+qqrr/1NT//z8///8sLP//LS3//S0t/1YtLf8AAAAA/wAAAP8AAAD/AAAA/wAAAP8AAAD/CwtA/yUl0/8qKu7/Ly///0lJ//9ERPX/JyfY/yYm1/8oKNn/RUX2/09P//9OTv//Tk7//05O//9OTv//R0f4/ykp2v8mJtf/JyfY/0JC8/9KSv//MDD//y0t//8tLf/9LS3/Vi0t/wAAAAC5AAAA0QAAAP4AAAD/AQEG/woKOP8WFn3/LCz7/y0t//8tLf//Kyv//ysr//8tLf//LS3//y0t//8rK///Kyv//ysr//8rK///Kyv//ysr//8rK///LS3//y0t//8tLf//LCz//ysr//8tLf//LS3//y0t//0tLf9WLS3/AAAAAAIAAABbAAAA/QAAAP8EBBf/JSXT/y0t/P8tLf//LS3//y0t//8tLf//LS3//y0t//8tLf//LS3//y0t//8tLf//LS3//y0t//8tLf//LS3//y0t//8tLf//LS3//y0t//8tLf//LS3//y4u//8uLv//LS3//S0t/1YtLf8AAAAAAAAAAFYAAAD9AAAA/wICDPMhIbuPLi7/ei0t/3stLf96LS3/hC0t/+ctLf//LS3//y0t//8tLf//LS3//y0t/+ItLf+CLS3/ei0t/38tLf/dLS3//y0t//8tLf//LS3//y0t//8qKuv/GBiG/xsbmcwtLf96LS3/KS0t/wAAAAAAAAAAVgAAAP0AAAD/AAAA5wAAACYAAAAAAAAAAC0t/wAtLf8SLS3/0C0t//8tLf//LS3//y0t//8tLf//LS3/xy0t/w0tLf8ALS3/CC0t/74tLf//LS3//y0t//8tLf//LS3//yYm2f8EBBj/AAAAnQAAAAAAAAAAAAAAAAAAAAAAAABWAAAA/QAAAP8AAADnAAAAJgAAAAAAAAAALS3/AC0t/xItLf/QLS3//y0t//8tLf//LS3//y0t//8tLf/HLS3/DS0t/wAtLf8ILS3/vi0t//8tLf//LS3//y4u//8uLv//JyfZ/wQEGP8AAACdAAAAAAAAAAAAAAAAAAAAAAAAAEYAAADOAAAA0QAAAMEAAABHAAAALQAAAC8AAAATMDD/Di0t/6otLf/SLS3/0C0t/9AtLf/QLS3/0y0t/6MtLf8KLS3/AC0t/wctLf+bLS3/0y0t/88pKejkJSXQ/yUl0v8gILb4BAQX2AAAAIAAAAAAAAAAAAAAAAAAAAAAAAAABgAAABIAAAARAAAAJwAAAMwAAADvAAAA7wAAAGYAAAAALS3/Dy0t/xItLf8SLS3/Ei0t/xItLf8SLS3/Di0t/wEtLf8ALS3/AS0t/w0tLf8SOjr/DgcHJngDAxL/AwMS/wMDEtsCAgspAAAACgAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAYAAAA2QAAAP8AAAD/AAAAbgAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAbgAAAP8AAAD/AAAA2QAAABgAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAABgAAADXAAAA/wAAAP8AAABuAAAAAAAAAAIAAAACAAAAAgAAAAIAAAACAAAAAgAAAAIAAAACAAAAAgAAAAIAAAACAAAAAgAAAAAAAABuAAAA/wAAAP8AAADXAAAAGAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAACAAAAEgAAABWAAAAVAAAAIUAAACrAAAAqgAAAKoAAACqAAAAqgAAAKoAAACqAAAAqgAAAKoAAACqAAAAqgAAAKoAAACqAAAAqwAAAIUAAABUAAAAVgAAAEgAAAAIAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAkQAAAP8AAAD/AAAA/wAAAP8AAAD/AAAA/wAAAP8AAAD/AAAA/wAAAP8AAAD/AAAA/wAAAP8AAAD/AAAAkQAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAACRAAAA/wAAAP8AAAD/AAAA/wAAAP8AAAD/AAAA/wAAAP8AAAD/AAAA/wAAAP8AAAD/AAAA/wAAAP8AAACRAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAGMAAACxAAAArgAAAK4AAACuAAAArgAAAK4AAACuAAAArgAAAK4AAACuAAAArgAAAK4AAACuAAAAsQAAAGMAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAgAAAAQAAAAEAAAABAAAAAQAAAAEAAAABAAAAAQAAAAEAAAABAAAAAQAAAAEAAAABAAAAAQAAAAEAAAAAgAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA/wAAAP8AAAD/AAAA/wAAAP8AAAD/AAAADwAAAA8AAAAHAAAAAQAAAAEAAAABAAAAAQAAAAEAAAABAAAAAQAAAAEAAAABAAAAAQAAAAGAAAABg4AgB4OAIAeAACAHgEAgB/B//g/wQAIP8AAAD/8AAP//AAD//wAA//8AAP8=
```

## static/redlogo.png

Complete binary file encoded as base64.

```base64
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bWxuczp0aWZmPSJodHRwOi8vbnMuYWRvYmUuY29tL3RpZmYvMS4wLyIKICAgIHhtbG5zOnhtcD0iaHR0cDovL25zLmFkb2JlLmNvbS94YXAvMS4wLyIKICAgeG1wTU06RG9jdW1lbnRJRD0iZ2ltcDpkb2NpZDpnaW1wOmIwOTJhNDlmLTAxZWEtNGIzYy05OWNhLTY4ZjMyOWQ0MDFmMyIKICAgeG1wTU06SW5zdGFuY2VJRD0ieG1wLmlpZDo5OGYyODgxYi0zYjMyLTQwMTgtYjQxZi03NTE2NGZlOTgzMzMiCiAgIHhtcE1NOk9yaWdpbmFsRG9jdW1lbnRJRD0ieG1wLmRpZDoyNGY0ZWNiYi02YmFkLTQ5ZmItYmFjYy1jNzIxNzZiOWNiOGIiCiAgIGRjOkZvcm1hdD0iaW1hZ2UvcG5nIgogICBHSU1QOkFQST0iMi4wIgogICBHSU1QOlBsYXRmb3JtPSJXaW5kb3dzIgogICBHSU1QOlRpbWVTdGFtcD0iMTcwMjcwNTQwNTAwMjQ2NSIKICAgR0lNUDpWZXJzaW9uPSIyLjEwLjMyIgogICB0aWZmOk9yaWVudGF0aW9uPSIxIgogICB4bXA6Q3JlYXRvclRvb2w9IkdJTVAgMi4xMCIKICAgeG1wOk1ldGFkYXRhRGF0ZT0iMjAyMzoxMjoxNVQyMzo0MzoyNC0wNjowMCIKICAgeG1wOk1vZGlmeURhdGU9IjIwMjM6MTI6MTVUMjM6NDM6MjQtMDY6MDAiPgogICA8eG1wTU06SGlzdG9yeT4KICAgIDxyZGY6U2VxPgogICAgIDxyZGY6bGkKICAgICAgc3RFdnQ6YWN0aW9uPSJzYXZlZCIKICAgICAgc3RFdnQ6Y2hhbmdlZD0iLyIKICAgICAgc3RFdnQ6aW5zdGFuY2VJRD0ieG1wLmlpZDo1OGE1ZWQ4Yy01YTA0LTRmOWUtOGRiNC02MmM1YTJlMzg0YzciCiAgICAgIHN0RXZ0OnNvZnR3YXJlQWdlbnQ9IkdpbXAgMi4xMCAoV2luZG93cykiCiAgICAgIHN0RXZ0OndoZW49IjIwMjMtMTItMTVUMjM6NDM6MjUiLz4KICAgIDwvcmRmOlNlcT4KICAgPC94bXBNTTpIaXN0b3J5PgogIDwvcmRmOkRlc2NyaXB0aW9uPgogPC9yZGY6UkRGPgo8L3g6eG1wbWV0YT4KICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgIAogICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgCiAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAKICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgIAogICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgCiAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAKICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgIAogICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgCiAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAKICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgIAogICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgCiAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAKICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgIAogICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgCiAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAKICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgIAogICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgCiAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAKICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgIAogICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgCiAgICAgICAgICAgICAgICAgICAgICAgICAgIAo8P3hwYWNrZXQgZW5kPSJ3Ij8+jQ3cfAAAAAZiS0dEAOoA8ADvHlboOAAAAAlwSFlzAAALEwAACxMBAJqcGAAAAAd0SU1FB+cMEAUrGDGrnNAAAAAZdEVYdENvbW1lbnQAQ3JlYXRlZCB3aXRoIEdJTVBXgQ4XAAANh0lEQVR42u3Yu00DQRSG0R20EsQERCRIpNcRzdCAG6AbaiLyFEAbiOSS89LKD+3M7Dmxg9U/XvvTTBMAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA7SomgH+lCQA0DPTkygQAACDwAQAAgQ8AAAh8AABA4AMAgMAHAAAEPgAAIPABAACBDwAACHwAABD4AACAwAcAAAQ+AAAg8AEAAIEPAAACHwAAEPgAAIDABwAABD4AAAh8AABA4AMAAAIfAAAQ+AAAgMAHAACBDwAACHwAAEDgAwAAAh8AABD4AAAg8AEAAIEPAAAIfAAAQOADAIDABwAABD4AACDwAQAAgQ8AAAh8AAAQ+AAAgMAHAAAEPgAAIPABAACBDwAAAh8AABD4AACAwAcAAAQ+AAAIfAAAQOADAAACHwAAEPgAAIDABwAAgQ8AAAh8AABA4AMAAAIfAAAQ+AAAIPABAACBDwAACHwAAEDgAwCAwAcAAAQ+AAAg8AEAAIEPAAAIfAAAEPgAAIDABwAABD4AACDwAQAAgQ8AAAIfAAAQ+AAAgMAHAAAEPgAAIPABAEDgAwAAAh8AABD4AADAUsUEw0sT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
```

## static/style.css

```css
/* Logo red (#ff2d2d), warm charcoal panels, and lighter red for readable text.
   Filled action buttons use a deeper red so their white labels stay readable. */
:root{color-scheme:dark;--bg:#110e11;--panel:#1a1418;--panel-high:#231a20;--line:#39282f;--text:#faf1f3;--muted:#b8a8ae;--accent:#ff737b;--brand:#ff2d2d;--action:#d92236;--warning:#f3c77a;--radius:16px;--shadow:0 12px 40px #0002;font-family:Inter,ui-sans-serif,system-ui,-apple-system,BlinkMacSystemFont,"Segoe UI",sans-serif;font-size:15px;line-height:1.5}
*{box-sizing:border-box}html{scroll-behavior:smooth;scroll-padding-top:95px}body{margin:0;background:var(--bg);color:var(--text)}body:before{content:"";position:absolute;z-index:-1;inset:0 0 auto;height:500px;background:radial-gradient(ellipse at 90% -15%,#ff2d2d24,transparent 65%);pointer-events:none}a{color:inherit;text-decoration:none}a:hover{color:var(--accent)}button,input,textarea,select{font:inherit}button,a,input,textarea,select{touch-action:manipulation}button{cursor:pointer}button:disabled{opacity:.55;cursor:wait}[hidden]{display:none!important}.js-only{display:none}.js .js-only{display:inline-flex}:focus-visible{outline:3px solid var(--accent);outline-offset:4px}.shell{max-width:1200px;margin:auto;padding:0 32px}.accent,.text-link{color:var(--accent)}.muted{color:var(--muted)}.small{font-size:.82rem}.eyebrow{font-size:.67rem;font-weight:700;letter-spacing:.16em;color:var(--muted);display:flex;gap:9px;align-items:center}h1,h2,h3,p{margin-top:0}h1{font-size:clamp(2.1rem,4vw,3.65rem);letter-spacing:-.055em;line-height:1.08;font-weight:650;margin-bottom:20px}h2{font-size:1.65rem;line-height:1.2;letter-spacing:-.035em;margin-bottom:12px}h3{font-size:1.05rem;letter-spacing:-.015em;margin-bottom:9px}p{margin-bottom:16px}.dot{display:inline-block;width:7px;height:7px;border-radius:50%;background:var(--accent);box-shadow:0 0 12px #ff2d2d50}.panel{border:1px solid var(--line);border-radius:var(--radius);background:var(--panel);box-shadow:var(--shadow)}.row,.section-title,.button-row{display:flex;align-items:center;justify-content:space-between;gap:16px}.button-row{justify-content:flex-start;flex-wrap:wrap}.section-title{margin-bottom:22px}.section-title h2{margin-bottom:0}.section-title .eyebrow{margin-bottom:7px}.button{display:inline-flex;align-items:center;justify-content:center;gap:13px;min-height:42px;padding:10px 17px;border:1px solid #59313c;border-radius:9px;background:#351e27;color:var(--text);font-weight:600;font-size:.84rem;white-space:nowrap;transition:background .16s,transform .16s}.button:hover{background:#48232f;color:#fff}.button.primary{background:var(--action);color:#fff;border-color:var(--action)}.button.primary:hover{background:#b8182b;border-color:#b8182b}.button.small{min-height:36px;padding:7px 13px;font-size:.76rem}.button.danger{border-color:#745047;background:#382521;color:#ffb6a3}.text-button,.copy-button{border:0;background:transparent;color:var(--muted);padding:7px}.copy-button{font-size:1rem;min-width:34px;min-height:34px}.text-button:hover,.copy-button:hover{color:var(--accent)}.text-link{font-size:.82rem;font-weight:600}.badge,.tag{display:inline-flex;align-items:center;padding:5px 10px;border:1px solid #57333e;border-radius:7px;font-size:.71rem;color:#edc1ca;background:#331e27;white-space:nowrap}.tag{font-size:.64rem;padding:3px 8px;margin-left:6px}.state-active{color:var(--accent);border-color:#89434f;background:#411d28}.state-ended{color:var(--warning);background:#312a1f;border-color:#665330}.state-upcoming{color:#b6c9fb;background:#222b40;border-color:#404e73}.skip-link{position:fixed;z-index:20;top:-80px;left:16px;padding:12px;background:var(--accent);color:#111}.skip-link:focus{top:12px}
.site-header{border-bottom:1px solid #40252f;background:#160e14ed;position:sticky;top:0;z-index:5;backdrop-filter:blur(10px)}.header-inner{min-height:78px;display:flex;justify-content:space-between;align-items:center;gap:24px}.brand{display:flex;gap:12px;align-items:center;font-size:.92rem;font-weight:800;letter-spacing:.07em}.brand img{border-radius:8px;object-fit:contain;background:#11080c}.brand-sub{display:block;color:var(--muted);font-size:.48rem;font-weight:600;letter-spacing:.2em;margin-top:3px}.site-header nav{display:flex;align-items:center;gap:26px;font-size:.8rem;color:#ead7dc}.site-header form{margin:0}.hero{display:grid;grid-template-columns:1.2fr 1fr;gap:52px;padding:52px 0 45px;align-items:center}.hero h1{max-width:580px;margin-top:14px}.lead{color:var(--muted);font-size:1rem;max-width:440px}.hero-links{display:flex;align-items:center;gap:24px;margin-top:26px;flex-wrap:wrap}.sponsor{display:flex;align-items:center;gap:13px}.sponsor small{display:block;font-size:.54rem;letter-spacing:.13em;color:var(--muted)}.sponsor strong{font-size:.9rem}.sponsor-symbol{display:grid;place-items:center;background:#29213d;color:#d1baff;font-size:1.2rem;font-weight:900;width:39px;height:39px;border-radius:11px}.race-clock{padding:27px 28px;background:linear-gradient(125deg,#311b25,#1a1418)}.clock{font-size:clamp(1.3rem,2.4vw,2.2rem);letter-spacing:-.045em;font-weight:600;font-variant-numeric:tabular-nums;margin:28px 0 16px;white-space:nowrap}.race-clock p{font-size:.72rem}.clock-footer{border-top:1px solid var(--line);display:flex;justify-content:space-between;padding-top:15px;gap:14px;font-size:.71rem;color:var(--muted)}.clock-footer strong{font-size:1rem;display:inline-block;margin-left:7px}.source-status{text-align:right;font-size:.74rem;display:flex;flex-direction:column;gap:4px}.source-status small{color:var(--muted);font-size:.66rem}.podium{display:grid;grid-template-columns:1fr 1.15fr 1fr;align-items:end;gap:16px;margin:35px 0 22px}.podium-card{padding:21px;border:1px solid var(--line);border-radius:var(--radius);background:linear-gradient(160deg,#291b22,#1a1418);min-width:0}.podium-card.place-1{background:linear-gradient(135deg,#461d2b,#211319);border-color:#a34755;padding-top:28px;box-shadow:0 6px 35px #ff2d2d14}.podium-top{display:flex;align-items:center;gap:12px}.placement{font-size:1.05rem;font-weight:600;color:var(--muted);font-variant-numeric:tabular-nums}.podium-top .eyebrow{font-size:.56rem;letter-spacing:.13em;flex:1}.podium-symbol{color:var(--accent);font-size:1.3rem}.podium-name{display:block;font-size:1.4rem;font-weight:600;letter-spacing:-.03em;margin:24px 0 27px;overflow-wrap:anywhere}.place-1 .podium-name{font-size:1.7rem;margin-bottom:30px}.podium-values{display:grid;grid-template-columns:1.5fr 1fr;gap:10px}.podium-values small{display:block;font-size:.51rem;letter-spacing:.12em;color:var(--muted);margin-bottom:7px}.podium-values strong{font-size:1rem;font-variant-numeric:tabular-nums;overflow-wrap:anywhere}.podium-values>div:last-child{text-align:right}.public-table{padding:0 20px}table{border-collapse:collapse;width:100%;font-size:.81rem}th{text-align:left;font-size:.64rem;letter-spacing:.055em;text-transform:uppercase;font-weight:600;color:var(--muted);padding:16px 14px;border-bottom:1px solid var(--line);white-space:nowrap}td{padding:13px 14px;border-bottom:1px solid #36242c}tbody tr:last-child td{border-bottom:0}tbody tr:hover{background:#ffffff03}.number{text-align:right;font-variant-numeric:tabular-nums;white-space:nowrap}.rank{color:var(--muted);font-variant-numeric:tabular-nums;width:65px}.table-scroll{overflow:auto;max-width:100%;scrollbar-color:#8c4a5b transparent}.leaderboard-foot{display:flex;justify-content:space-between;gap:16px;color:var(--muted);font-size:.67rem;margin:15px 0 26px}.explanation{padding:0 22px;margin-top:24px}.explanation summary{padding:18px 0;font-size:.82rem}.weighting-grid{display:grid;grid-template-columns:repeat(3,1fr);gap:22px;border-top:1px solid var(--line);padding-top:20px}.weighting-grid strong{font-size:.9rem}.weighting-grid p{color:var(--muted);font-size:.79rem;margin:5px 0 22px}.footer{display:flex;justify-content:space-between;gap:20px;padding-top:36px;padding-bottom:28px;font-size:.69rem;color:#cfb7c0}.footer span:last-child{display:flex;gap:22px}
.admin-main{padding-top:35px}.admin-heading{display:flex;align-items:center;justify-content:space-between;gap:24px;margin-bottom:25px}.admin-heading h1{font-size:2.05rem;margin:9px 0 13px}.admin-heading p{font-size:.8rem;margin:0}.tabs{display:flex;align-items:center;gap:8px;border-bottom:1px solid var(--line);padding-bottom:15px;margin-bottom:26px}.tabs a{color:var(--muted);padding:9px 17px;font-size:.83rem;border-radius:8px}.tabs a[aria-current]{background:#3c1d29;color:var(--accent)}.tabs a:hover{background:#2c1923}.auto-label{margin-left:auto;font-size:.67rem;color:var(--muted);display:flex;gap:8px;align-items:center}.stat-grid{display:grid;grid-template-columns:1.5fr 1fr 1fr;gap:18px;margin-bottom:32px}.stat{padding:24px;min-width:0}.stat-value{display:block;font-size:2rem;line-height:1.2;letter-spacing:-.035em;margin:24px 0 12px;font-variant-numeric:tabular-nums}.stat #countdown{font-size:1.4rem;white-space:nowrap}.stat p{font-size:.77rem;margin-bottom:12px}.stat small{font-size:.7rem}.connection-grid{display:grid;grid-template-columns:1fr 1fr;gap:18px}.connection{display:flex;align-items:flex-start;gap:16px;padding:23px}.connection>div:nth-child(2){flex:1;min-width:0}.connection h3{font-size:.93rem}.connection p{font-size:.8rem;margin-bottom:8px;overflow-wrap:anywhere}.connection small{font-size:.64rem}.connection-icon{flex-shrink:0;display:grid;place-items:center;width:40px;height:40px;border-radius:10px;background:#441f2d;color:var(--accent);font-size:1.2rem;font-weight:800}.quick-guide{display:flex;align-items:center;justify-content:space-between;gap:25px;padding:25px;margin-top:24px;background:linear-gradient(120deg,#311a25,#1a1418)}.quick-guide p{font-size:.81rem;margin:0}.notice{padding:16px 18px;border:1px solid var(--line);border-radius:10px;background:#281b23;font-size:.83rem;margin:0 0 20px;overflow-wrap:anywhere}.notice.warning{color:#f4d6a8;background:#2a241a;border-color:#655237}.notice.success{color:#d0efae;background:#23301d;border-color:#4c683b}.notice p:last-child{margin-bottom:0}.notice strong{display:block;margin-bottom:6px}.notice ul{padding-left:20px;margin:6px 0}.ended-notice{display:flex;justify-content:space-between;align-items:center;gap:20px}.ended-notice span{color:var(--muted);font-size:.78rem}.stack{display:flex;flex-direction:column;gap:20px}.form-panel{padding:25px;margin-bottom:20px}.stack .form-panel{margin-bottom:0}.form-panel h2{font-size:1.4rem}.form-panel h3{margin-top:24px}.form-grid{display:grid;grid-template-columns:1fr 1fr;gap:18px 22px;margin-top:20px}.field{display:flex;flex-direction:column;gap:7px;min-width:0}.field label{font-size:.77rem;font-weight:600}.field small{font-size:.69rem;min-height:1em}.field-error{color:#ffbd9f}input,textarea,select{width:100%;min-height:42px;background:#160f15;color:var(--text);border:1px solid #573240;border-radius:8px;padding:10px 12px;font-size:.83rem}input:focus,textarea:focus,select:focus{border-color:var(--accent);outline:1px solid var(--accent)}input[type=file]{padding:7px}input::placeholder{color:#ab909c}textarea{resize:vertical}input[aria-invalid]{border-color:var(--warning)}.form-panel>.field{margin-top:20px}.prize-grid{display:grid;grid-template-columns:repeat(5,1fr);gap:14px}.prize-grid input{font-variant-numeric:tabular-nums}.prize-grid .field small:empty{display:none}.save-bar{display:flex;justify-content:space-between;align-items:center;gap:20px;padding:17px 20px;background:#301923ef;border:1px solid #89505f;border-radius:12px;position:sticky;bottom:15px;z-index:4;backdrop-filter:blur(10px)}.save-bar strong,.save-bar span{display:block}.save-bar strong{font-size:.86rem;margin-bottom:3px}.filter-bar{display:flex;align-items:flex-start;gap:14px;margin:22px 0 14px;flex-wrap:wrap}.filter-bar .field{flex:1;min-width:150px}.filter-bar .grow{flex:2}.filter-bar>.button{margin-top:26px}.name-cell{display:flex;align-items:center;gap:6px;overflow-wrap:anywhere}.empty{text-align:center;padding:35px;color:var(--muted)}details summary{cursor:pointer;list-style:none;display:flex;align-items:center;justify-content:space-between;gap:18px;font-weight:600}details summary::-webkit-details-marker{display:none}summary h2{margin:0}summary .eyebrow{display:block;margin-bottom:7px}details[open]>summary{margin-bottom:18px}.explanation[open]>summary{margin-bottom:0}.expand-icon{font-size:1.4rem;color:var(--accent)}details[open]>summary .expand-icon{transform:rotate(45deg)}.details-content>.field{margin:22px 0}.nested{border-top:1px solid var(--line);margin-top:22px;padding-top:18px}.nested summary{font-size:.83rem;color:#dac2cc}.account-row{display:flex;justify-content:space-between;align-items:center;padding:12px 0;border-bottom:1px solid var(--line)}.account-row strong{font-size:.85rem}.diagnostic-grid{display:grid;grid-template-columns:repeat(3,1fr);gap:20px;margin:22px 0}.diagnostic-grid strong,.diagnostic-grid small{display:block;overflow-wrap:anywhere}.diagnostic-grid strong{font-size:.82rem;margin-top:5px}.diagnostic-grid small{font-size:.68rem}.admin-foot{display:flex;justify-content:space-between;gap:20px;font-size:.65rem;color:#b396a4;margin:30px 0}.login-wrap{min-height:70vh;display:grid;place-items:center;padding-top:45px;padding-bottom:45px}.login-panel{width:100%;max-width:450px;padding:38px}.login-panel h1{font-size:2.35rem;margin:22px 0 14px}.login-panel>.muted{font-size:.82rem}.login-panel .stack{margin:27px 0}.release{font-size:.64rem;color:#b39aa5}.toast{position:fixed;bottom:25px;left:50%;transform:translateX(-50%);z-index:20;padding:14px 22px;border:1px solid #8a455c;border-radius:10px;background:#3b1c2a;box-shadow:var(--shadow);max-width:calc(100vw - 30px);font-size:.83rem}
@media(min-width:1600px){.shell{max-width:1330px}.hero{padding-top:64px}}
@media(max-width:1000px){.shell{padding-left:24px;padding-right:24px}.hero{gap:24px;grid-template-columns:1fr 1fr}.race-clock{padding:22px}.stat-grid{grid-template-columns:1fr 1fr}.stat:first-child{grid-column:1/-1}.stat:first-child .stat-value{font-size:2rem}.connection-grid{grid-template-columns:1fr}.podium{gap:12px}.podium-card{padding:16px}.podium-values strong{font-size:.83rem}.podium-top .eyebrow{font-size:.5rem}.prize-grid{grid-template-columns:repeat(3,1fr)}.stat #countdown{font-size:1.8rem}}
@media(max-width:700px){html{scroll-padding-top:80px}.shell{padding-left:18px;padding-right:18px}.header-inner{min-height:68px}.brand{font-size:.75rem;gap:8px}.brand img{width:30px;height:30px}.brand-sub{font-size:.4rem}.site-header nav{gap:12px;font-size:.72rem}.site-header nav>a:first-child{display:none}.site-header .button{padding:8px 11px}.hero{grid-template-columns:1fr;gap:27px;padding:34px 0}.hero h1{font-size:2.7rem;max-width:480px;margin-top:15px}.hero-links{margin-top:20px}.race-clock{padding:22px}.clock{font-size:1.9rem;margin:23px 0 14px}.clock-footer strong{font-size:1rem}.section-title h2{font-size:1.5rem}.section-title{align-items:flex-start;gap:12px}.source-status{font-size:.66rem;max-width:155px}.source-status small{font-size:.59rem}.podium{grid-template-columns:1fr 1fr;margin-top:24px;gap:12px}.podium .place-1{grid-column:1/-1;grid-row:1;padding:22px}.podium .place-1 .podium-name{margin:14px 0 20px;font-size:1.65rem}.place-1 .podium-values strong{font-size:1.3rem}.podium .place-2,.podium .place-3{padding:16px}.podium-top .eyebrow{font-size:.49rem}.podium-name{font-size:1.1rem;margin:17px 0 20px}.podium-values{grid-template-columns:1fr;gap:15px}.podium-values>div:last-child{text-align:left}.place-1 .podium-values{grid-template-columns:1fr 1fr}.place-1 .podium-values>div:last-child{text-align:right}.podium-values strong{font-size:1rem}.podium-top{gap:8px}.podium-symbol{font-size:1rem}.public-table{padding:0 5px}th{font-size:.58rem;padding:14px 9px}td{font-size:.74rem;padding:12px 9px}.public-table table{min-width:355px}.rank{width:45px}.leaderboard-foot{flex-direction:column;gap:5px;font-size:.63rem}.weighting-grid{grid-template-columns:1fr;gap:0}.weighting-grid p{margin-bottom:16px}.footer{flex-direction:column;gap:12px;padding-top:26px}.footer span:last-child{gap:18px}.admin-heading{align-items:flex-start;gap:12px}.admin-heading h1{font-size:1.75rem}.admin-heading>.button,.admin-heading form .button{font-size:.69rem;padding:9px}.admin-heading p{font-size:.72rem}.tabs{gap:2px;flex-wrap:wrap}.tabs a{padding:9px 13px;font-size:.76rem}.auto-label{width:100%;margin:10px 0 0 13px;font-size:.65rem}.stat-grid{gap:12px}.stat{padding:18px}.stat-value{font-size:1.7rem}.stat:first-child .stat-value{font-size:1.65rem}.stat .eyebrow{font-size:.6rem}.stat p{font-size:.7rem}.connection{padding:18px;gap:12px}.connection-icon{width:32px;height:32px}.quick-guide{align-items:flex-start;flex-direction:column;padding:20px}.form-panel{padding:18px}.form-panel .section-title{flex-direction:column}.form-grid{grid-template-columns:1fr;gap:15px}.prize-grid{grid-template-columns:repeat(3,minmax(0,1fr));gap:12px}.prize-grid input{padding:9px;font-size:.78rem}.prize-grid label{font-size:.7rem}.save-bar{bottom:8px;padding:14px;gap:12px;flex-wrap:wrap}.save-bar .button{min-height:40px}.save-bar .button-row{margin-left:auto;gap:8px}.filter-bar .field{min-width:130px}.ended-notice{align-items:flex-start;flex-direction:column}.diagnostic-grid{grid-template-columns:1fr 1fr;gap:17px}.admin-foot{flex-direction:column;gap:5px}.login-panel{padding:28px 24px}.login-panel h1{font-size:2.1rem}}
@media(prefers-reduced-motion:reduce){html{scroll-behavior:auto}*,*:before,*:after{animation:none!important;transition:none!important}}

/* Provider progress stays visible on every admin tab. */
.refresh-progress{padding:21px 24px;margin-bottom:24px;border-top:2px solid var(--brand);background:linear-gradient(120deg,#321821,#1a1418)}
.progress-heading{display:flex;align-items:flex-start;justify-content:space-between;gap:18px;margin-bottom:15px}
.progress-heading p{margin-bottom:5px}.progress-heading .text-link{white-space:nowrap}
.progress-services{display:grid;grid-template-columns:1fr 1fr;gap:24px;border-top:1px solid var(--line);padding-top:15px}
.progress-services strong{font-size:.8rem;color:var(--accent)}.progress-services p{margin:7px 0 0;font-size:.78rem;overflow-wrap:anywhere;color:var(--text)}
@media(max-width:700px){.refresh-progress{padding:18px}.progress-heading{flex-direction:column;gap:10px}.progress-services{grid-template-columns:1fr;gap:17px}}
```

## storage.py

```python
"""Small transactional store: admin state and live snapshots are separate rows.

SQLite is automatic and needs no database service. PostgreSQL remains an
explicit opt-in for existing deployments. App Platform local files are
temporary; private recovery exports can seed a replacement instance.
"""
from contextlib import contextmanager
import copy
import hashlib
import json
import logging
import secrets
import sqlite3
import threading
import time

from werkzeug.security import generate_password_hash
from race_support import read_json, clean_snapshots, race_key, empty_snapshots
from store_schema import upgrade_store
from race import empty

LOG = logging.getLogger("redhunllef")


class StoreError(RuntimeError):
    pass


class Conflict(StoreError):
    pass


def encode(value):
    return json.dumps(value, separators=(",", ":"), ensure_ascii=False, allow_nan=False)


class Store:
    def __init__(self, config):
        self.config, self.key = config, config.state_key
        self.pg = bool(config.db_url)
        self.lock, self.conn, self.job_local = threading.RLock(), None, threading.local()
        if not self.pg:
            config.db_path.parent.mkdir(parents=True, exist_ok=True)
            if config.ignored_database_url:
                LOG.info("STORAGE Using local storage; DATABASE_URL is ignored because STORAGE_MODE=local.")
        self.initialize()

    def connect(self):
        if self.pg:
            try:
                import psycopg
            except ImportError:
                raise StoreError("Optional PostgreSQL support is not installed. Install requirements-postgres.txt or use STORAGE_MODE=local.") from None
            options = dict(autocommit=True, connect_timeout=8, sslmode=self.config.sslmode,
                           options="-c statement_timeout=8000 -c lock_timeout=5000")
            if self.config.sslrootcert:
                options["sslrootcert"] = self.config.sslrootcert
            return psycopg.connect(self.config.db_url, **options)
        conn = sqlite3.connect(self.config.db_path, check_same_thread=False, isolation_level=None, timeout=8)
        conn.execute("PRAGMA journal_mode=WAL")
        conn.execute("PRAGMA foreign_keys=ON")
        return conn

    @contextmanager
    def connection(self, transaction=False):
        # No network provider call or template rendering occurs inside this lock.
        with self.lock:
            try:
                if self.conn is None or (self.pg and self.conn.closed):
                    self.conn = self.connect()
                if transaction:
                    self.conn.execute("BEGIN" if self.pg else "BEGIN IMMEDIATE")
                yield self.conn
                if transaction:
                    self.conn.execute("COMMIT")
            except BaseException as exc:
                if transaction and self.conn:
                    try:
                        self.conn.execute("ROLLBACK")
                    except Exception:
                        pass
                if isinstance(exc, (Conflict, ValueError, RuntimeError)):
                    raise
                if not isinstance(exc, Exception):
                    raise
                self.close()
                message = "Database operation failed. Check connectivity, TLS, permissions, and runtime settings." if self.pg else "Local storage could not be read or written. Check disk space and the data folder permissions; do not delete your saved file."
                raise StoreError(message) from None

    def query(self, conn, sql, params=()):
        return conn.execute(sql.replace("?", "%s") if self.pg else sql, params)

    def initialize(self):
        with self.connection(transaction=True) as conn:
            if self.pg:
                conn.execute("SELECT pg_advisory_xact_lock(728364092)")
            conn.execute("CREATE TABLE IF NOT EXISTS rh_admin (name TEXT PRIMARY KEY, revision BIGINT NOT NULL, document TEXT NOT NULL)")
            conn.execute("CREATE TABLE IF NOT EXISTS rh_live (name TEXT NOT NULL, service TEXT NOT NULL, document TEXT NOT NULL, PRIMARY KEY(name, service))")
            conn.execute("CREATE TABLE IF NOT EXISTS rh_recovery (id TEXT PRIMARY KEY, name TEXT NOT NULL, reason TEXT NOT NULL, created BIGINT NOT NULL, document TEXT NOT NULL)")
            existing = self.query(conn, "SELECT document FROM rh_admin WHERE name=?", (self.key,)).fetchone()
            if existing:
                # Validate saved state rather than overwriting an unreadable account store.
                upgrade_store(json.loads(existing[0]), self.config.site, {})
                LOG.info("ACCOUNTS Existing accounts and settings retained.")
                return
            legacy = None
            source = "first-run defaults"
            if self.pg and conn.execute("SELECT to_regclass('wager_state')").fetchone()[0]:
                old = self.query(conn, "SELECT payload FROM wager_state WHERE name=?", (self.key,)).fetchone()
                if old:
                    legacy, source = old[0], "previous PostgreSQL state"
            if legacy is None:
                for path in (self.config.recovery, self.config.legacy, self.config.seed):
                    if path.is_file():
                        legacy, source = read_json(path), path.name
                        break
            if legacy is None:
                legacy = dict(version=7, users={self.config.superadmin: dict(
                    pw_hash=generate_password_hash(self.config.bootstrap_password), auth_version=1)},
                    secret_key=secrets.token_hex(32), site_settings=self.config.site)
            value, _ = upgrade_store(legacy, self.config.site, {})
            if not value["users"]:
                raise StoreError("Saved account store contains no accounts. The original was not replaced.")
            self.backup_in(conn, "before-rebuild-import", {"admin": legacy, "source": source})
            snapshots = clean_snapshots(value.pop("leaderboard_snapshots"), race_key(value["site_settings"]))
            value.pop("health", None)
            value["superadmin"] = self.config.superadmin
            self.query(conn, "INSERT INTO rh_admin VALUES (?, ?, ?)", (self.key, 1, encode(value)))
            saved = empty(value["site_settings"])
            saved.update(rows=snapshots["last_top15"], previous_top=snapshots["prev_top15"],
                         updated_at=snapshots["updated_at"] or 0, snapshot_only=bool(snapshots["last_top15"]),
                         count=len(snapshots["last_top15"]), warning="Only the saved Top 15 is available until Shuffle responds." if snapshots["last_top15"] else "")
            saved["source"] = [dict(username=r["username"], weighted=r["original_weighted_wager"],
                                    raw=r["raw_wager"], row_count=r["row_count"]) for r in saved["rows"]]
            self.live_in(conn, "shuffle", saved)
            LOG.info("MIGRATION Imported %s; original accounts, hashes, and dates preserved. Recovery copy recorded.", source)
        if not self.pg:
            self.config.db_path.chmod(0o600)

    def admin(self):
        with self.connection() as conn:
            row = self.query(conn, "SELECT revision, document FROM rh_admin WHERE name=?", (self.key,)).fetchone()
        if not row:
            raise StoreError("Saved admin state is missing. Restore a verified database backup.")
        return row[0], json.loads(row[1])

    def live(self, service):
        with self.connection() as conn:
            row = self.query(conn, "SELECT document FROM rh_live WHERE name=? AND service=?", (self.key, service)).fetchone()
        return json.loads(row[0]) if row else None

    def live_in(self, conn, service, value):
        self.query(conn, "INSERT INTO rh_live VALUES (?, ?, ?) ON CONFLICT(name,service) DO UPDATE SET document=excluded.document",
                   (self.key, service, encode(value)))

    def publish(self, service, value, expected_revision=None):
        with self.connection(transaction=True) as conn:
            if expected_revision is not None:
                sql = "SELECT revision FROM rh_admin WHERE name=?" + (" FOR UPDATE" if self.pg else "")
                if self.query(conn, sql, (self.key,)).fetchone()[0] != expected_revision:
                    raise Conflict("Race settings changed during the provider check; a new check is queued.")
            self.live_in(conn, service, value)

    def save(self, value, revision, *, snapshot=None, backup_reason=None):
        with self.connection(transaction=True) as conn:
            old = self.query(conn, "SELECT revision, document FROM rh_admin WHERE name=?" + (" FOR UPDATE" if self.pg else ""), (self.key,)).fetchone()
            if not old or old[0] != revision:
                raise Conflict("Another administrator saved changes. Reload and review before saving again.")
            if backup_reason:
                rows = self.query(conn, "SELECT service,document FROM rh_live WHERE name=?", (self.key,)).fetchall()
                self.backup_in(conn, backup_reason, {"admin": json.loads(old[1]), "live": {r[0]: json.loads(r[1]) for r in rows}})
            self.query(conn, "UPDATE rh_admin SET document=?,revision=revision+1 WHERE name=?", (encode(value), self.key))
            if snapshot is not None:
                self.live_in(conn, "shuffle", snapshot)
        return revision + 1

    def backup_in(self, conn, reason, document):
        self.query(conn, "INSERT INTO rh_recovery VALUES (?, ?, ?, ?, ?)",
                   (secrets.token_hex(16), self.key, reason, int(time.time()), encode(document)))

    @contextmanager
    def job(self, service):
        # Reuse one dedicated connection per provider thread. Session locks
        # prevent duplicate provider calls during an overlapping deployment.
        if not self.pg:
            yield True
            return
        conn = getattr(self.job_local, "conn", None)
        try:
            if conn is None or conn.closed:
                conn = self.job_local.conn = self.connect()
            key = int.from_bytes(hashlib.blake2b((self.key + service).encode(), digest_size=8).digest(), "big", signed=True)
            acquired = conn.execute("SELECT pg_try_advisory_lock(%s)", (key,)).fetchone()[0]
        except Exception:
            self.close_job()
            raise StoreError("Provider coordination could not reach PostgreSQL. The next scheduled check will retry.") from None
        try:
            yield acquired
        finally:
            if acquired:
                try:
                    conn.execute("SELECT pg_advisory_unlock(%s)", (key,))
                except Exception:
                    self.close_job()

    def close_job(self):
        conn = getattr(self.job_local, "conn", None)
        if conn:
            conn.close()
        self.job_local.conn = None

    def close(self):
        with self.lock:
            if self.conn:
                self.conn.close()
            self.conn = None
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
{% block navigation %}<a href="/" target="_blank" rel="noopener">View website ↗</a><form method="post" action="/admin/logout"><input type="hidden" name="csrf" value="{{ csrf() }}"><button class="text-button" type="submit">Sign out</button></form>{% endblock %}
{% block content %}<main id="main" class="shell admin-main"><div class="admin-heading"><div><p class="eyebrow">CONTROL CENTER</p><h1>Your race, at a glance<span class="accent">.</span></h1><p class="muted">Welcome, {{ user }} <span class="tag">{{ 'Superadmin' if superadmin else 'Admin' }}</span></p></div><form method="post" action="/admin/action" data-refresh>{{ form_fields('refresh',tab,revision) }}<button type="submit" class="button primary">↻ Refresh data</button></form></div>
<nav class="tabs" aria-label="Administration">{% for key,label in tabs.items() %}<a href="{{ url_for('login',tab=key) }}" {% if tab==key %}aria-current="page"{% endif %}>{{ label }}</a>{% endfor %}<span class="auto-label"><span class="dot"></span> Automatic · 60 sec</span></nav>
{% if hosted_local %}<p class="notice warning">Local storage is active. On App Platform, saved changes can be lost when the app is redeployed or replaced. {% if superadmin %}<a class="text-link" href="/admin?tab=settings#recovery">Save a private recovery file →</a>{% else %}Ask the Superadmin to save a private recovery file after important changes.{% endif %}</p>{% endif %}
{% with messages=get_flashed_messages() %}{% for message in messages %}<p class="notice success" role="status">{{ message }}</p>{% endfor %}{% endwith %}
{% if errors %}<div class="notice warning" role="alert"><strong>Review before saving.</strong><ul>{% for key,message in errors.items() %}<li>{{ message }}</li>{% endfor %}</ul></div>{% endif %}
<p id="leaderboardMessage" class="notice" role="status" {% if not data.leaderboard_message %}hidden{% endif %}>{{ data.leaderboard_message }}</p>
<p id="networkError" class="notice warning" role="status" hidden></p><p id="sourceWarning" class="notice warning" role="status" {% if not data.freshness.warning %}hidden{% endif %}>{{ data.freshness.warning }}</p>
<div id="endedNotice" class="notice ended-notice" {% if data.site.race_state!='ended' %}hidden{% endif %}><div><strong>This saved race has ended.</strong><span>New wagers outside its dates do not count toward these results.</span></div><a class="button small" href="{{ url_for('login',tab='race') }}">Prepare next race →</a></div>
<section class="panel refresh-progress" aria-label="Live update progress">
<div class="progress-heading"><div><p class="eyebrow">LIVE UPDATE PROGRESS</p><p id="publishedWindow" class="muted small">Published window: {{ data.site.start_et }} → {{ data.site.end_et }}</p></div><a class="text-link" href="/admin/diagnostics">Download diagnostics</a></div>
<div class="progress-services"><div><strong>Shuffle · Leaderboard</strong><p id="shuffleProgress" role="status">{{ data.jobs.shuffle.error or ('Check in progress.' if data.jobs.shuffle.state=='checking' else 'Automatic check queued.') }}</p></div><div><strong>Kick · Stream status</strong><p id="kickProgress" role="status">{{ data.jobs.kick.error or ('Check in progress.' if data.jobs.kick.state=='checking' else 'Automatic check queued.') }}</p></div></div>
</section>
{% include 'admin_' ~ tab ~ '.html' %}
<div class="admin-foot"><span id="browserCheck">Connecting to automatic updates…</span><span>Release {{ release }}</span></div>
<noscript><p class="notice">Forms and navigation work without JavaScript. Reload for current statistics.</p></noscript></main>{% endblock %}
{% block footer %}Private administration{% endblock %}
```

## templates/admin_overview.html

```html
<section class="stat-grid"><article class="panel stat"><div class="row"><span class="eyebrow">RACE STATUS</span><span id="raceBadge" class="badge state-{{ data.site.race_state }}">{{ data.site.race_state|capitalize }}</span></div><strong id="countdown" class="stat-value">{{ data.site.race_state|capitalize }}</strong><p id="raceWindow" class="muted">{{ data.site.start_et }} → {{ data.site.end_et }}</p><a class="text-link" href="{{ url_for('login',tab='race') }}">Review schedule →</a></article>
<article class="panel stat"><span class="eyebrow">TOTAL PRIZE POOL</span><strong class="stat-value accent" id="poolTotal">{{ data.site.total_prize }}</strong><p class="muted">Across 15 paid places</p><a class="text-link" href="{{ url_for('login',tab='race') }}#prizes">Manage prizes →</a></article>
<article class="panel stat"><span class="eyebrow">QUALIFYING PLAYERS</span><strong class="stat-value" id="playerCount">{{ data.count }}</strong><p id="dataState">{{ data.freshness.label }}</p><small id="sourceTime" class="muted">{{ fmt_et(data.freshness.updated_at) }}</small></article></section>
<div class="section-title"><div><p class="eyebrow">CONNECTED TO YOUR COMMUNITY</p><h2>Live connections</h2></div><a class="text-link" href="{{ url_for('login',tab='settings') }}#diagnostics">View diagnostics →</a></div>
<section class="connection-grid">{% for name,label in [('shuffle','Shuffle wager data'),('kick','Kick livestream')] %}<article class="panel connection"><div class="connection-icon">{{ 'S' if name=='shuffle' else 'K' }}</div><div><h3>{{ label }}</h3><p id="{{ name }}Message">{{ data.jobs[name].error or 'Checking automatically' }}</p><small id="{{ name }}Timing" class="muted">Every 60 seconds</small>{% if name=='kick' %}<p id="streamDetail" class="muted small"></p>{% endif %}</div><form method="post" action="/admin/action" data-refresh>{{ form_fields('refresh','overview',revision) }}<input type="hidden" name="service" value="{{ name }}"><button class="button small" type="submit">Check</button></form></article>{% endfor %}</section>
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
{% if confirm_race %}<div class="notice warning"><strong>These dates are a draft. Confirm below to publish them.</strong><p>The current race will be archived, including its results and overrides. The new race starts with its own participants. Review the dates below.</p><p>The saved race stays active until you choose <strong>Confirm and publish race</strong> in the bottom save bar.</p></div>{% endif %}
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
{% if restore %}<div class="notice warning"><strong>Review this restore</strong><p>{{ restore.start }} → {{ restore.end }} · {{ restore.rows }} saved participants</p><p>Current race data will be replaced. Accounts remain intact, and a private recovery copy is created first.</p><form method="post" action="/admin/action">{{ form_fields('restore','settings',revision) }}<input type="hidden" name="restore_token" value="{{ restore.token }}"><button class="button danger" type="submit">Confirm restore</button></form></div>{% endif %}
{% for race in admin.race_history|reverse %}<details class="nested"><summary>{{ fmt_et(race.site_settings.start_time) }} → {{ fmt_et(race.site_settings.end_time) }}</summary><div class="table-scroll"><table><thead><tr><th>Rank</th><th>Username</th><th class="number">Weighted wager</th></tr></thead><tbody>{% for row in race.leaderboard_snapshots.last_top15 %}<tr><td>{{ row.rank }}</td><td>{{ row.username }}</td><td class="number">{{ row.wager }}</td></tr>{% else %}<tr><td colspan="3">No saved participants.</td></tr>{% endfor %}</tbody></table></div></details>{% else %}<p class="muted small">Completed races appear here after you save a new window.</p>{% endfor %}</div></details>
{% if superadmin %}<section class="panel form-panel" id="recovery"><p class="eyebrow">KEEP YOUR CHANGES</p><h2>Private recovery file</h2><p class="muted">Save your administrator accounts, password hashes, race dates, overrides, history, and last Top 15. This file contains sensitive account data; keep it private.</p><a class="button primary" href="/admin/recovery-backup">↓ Download private recovery file</a><p class="small muted">To carry these changes into a fresh deployment, add the downloaded <code>recovery.seed.json</code> to the <code>private/</code> folder in your private source repository before deploying. It imports automatically only when no saved local state exists. Download a new copy after important changes. Shuffle and Kick credentials stay in your existing configuration.</p><p class="small muted">On App Platform, local files can disappear during redeploys or container replacements. This download is a manual recovery copy, not automatic remote storage.</p></section>{% endif %}
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
<link rel="stylesheet" href="{{ url_for('static',filename='style.css',v=asset_version) }}"></head>
<body {% block attributes %}{% endblock %}>
<a class="skip-link" href="#main">Skip to content</a>
<header class="site-header"><div class="shell header-inner"><a class="brand" href="/"><img src="{{ url_for('static',filename='redlogo.png') }}" alt="" width="36" height="36"><span><span data-site-text="site_name">{{ data.site.site_name if data is defined else 'RedHunllef' }}</span><span class="brand-sub">THE COMMUNITY RACE</span></span></a>
<nav aria-label="Main navigation">{% block navigation %}<a href="/#leaderboard">Leaderboard</a><a data-site-text="community_name" data-site-link="community_url" href="{{ data.site.community_url }}" {% if not data.site.community_url %}hidden{% endif %} target="_blank" rel="noopener">{{ data.site.community_name }}</a><a class="button small" data-site-link="stream_url" href="{{ data.site.stream_url }}" target="_blank" rel="noopener">Watch on Kick <span aria-hidden="true">↗</span></a>{% endblock %}</nav></div></header>
{% block content %}{% endblock %}
<footer class="shell footer"><span>RedHunllef <span class="muted">· Community first.</span></span><span class="muted">{% block footer %}<a data-site-link="responsible_gambling_url" href="{{ data.site.responsible_gambling_url }}" {% if not data.site.responsible_gambling_url %}hidden{% endif %} target="_blank" rel="noopener">Play responsibly · 18+</a><a href="/admin">Admin</a>{% endblock %}</span></footer>
<div id="toast" class="toast" role="status" hidden></div>
<script src="{{ url_for('static',filename='app.js',v=asset_version) }}" defer></script>
</body></html>
```

## templates/error.html

```html
{% extends 'base.html' %}{% block title %}{{ title }} · RedHunllef{% endblock %}
{% block navigation %}<a href="/">View race ↗</a>{% endblock %}
{% block content %}<main class="shell login-wrap" id="main"><section class="panel login-panel"><p class="eyebrow">REDHUNLLEF</p><h1>{{ title }}</h1><p class="muted">{{ message }}</p><a class="button primary" href="/admin">Return to admin →</a><p class="release">{{ release }}</p></section></main>{% endblock %}
{% block footer %}RedHunllef Wager Race{% endblock %}
```

## templates/index.html

```html
{% extends 'base.html' %}
{% block attributes %}data-page="public" data-feed="/data" data-bootstrap="{{ data|tojson|forceescape }}"{% endblock %}
{% block content %}
<main id="main" class="shell">
<section class="hero"><div><div class="eyebrow"><span class="dot"></span> CODE RED. YOUR COMMUNITY.</div><h1 id="raceTitle">{{ data.site.race_title }}</h1><p id="raceDescription" class="lead">{{ data.site.race_description }}</p><div class="hero-links"><a id="sponsorLink" class="sponsor" href="{{ data.site.sponsor_url }}" target="_blank" rel="noopener"><span class="sponsor-symbol">S</span><span><small>POWERED BY</small><strong id="sponsorName">{{ data.site.sponsor_name }}</strong></span><span aria-hidden="true">↗</span></a><span class="tag" id="streamStatus">Checking Kick</span></div></div>
<aside class="race-clock panel"><div class="row"><span class="eyebrow" id="clockLabel">RACE SCHEDULE</span><span id="raceBadge" class="badge state-{{ data.site.race_state }}">{{ data.site.race_state|capitalize }}</span></div><div id="countdown" class="clock" aria-hidden="true">—</div><p id="raceWindow" class="muted">{{ data.site.start_et }} → {{ data.site.end_et }}</p><div class="clock-footer"><span>Prize pool <strong class="accent" id="poolTotal">{{ data.site.total_prize }}</strong></span><span>15 paid places</span></div></aside></section>
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

## tests/package.json

```json
{
  "name": "redhunllef-interface-tests",
  "private": true,
  "scripts": {"test": "node --test test_frontend.cjs"},
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
            for name, url in {"public": "/", "login": "/admin", "error": "/missing"}.items():
                (destination/(name+".html")).write_text(client.get(url).text, encoding="utf-8")
            with client.session_transaction() as session:
                session.update(user="gingrsnaps", auth_version=1, csrf="fixture-csrf")
            for tab in ("overview", "race", "players", "settings"):
                (destination/(tab+".html")).write_text(client.get("/admin?tab="+tab).text, encoding="utf-8")
            (destination/"public.json").write_text(json.dumps(client.get("/data").json), encoding="utf-8")
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
        for path in ('/private/settings.json','/private/admin_store.seed.json','/data/redhunllef.sqlite3'):
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
            self.assertGreaterEqual(c.execute('SELECT count(*) FROM rh_recovery').fetchone()[0],2)

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

    def test_postgres_is_explicit_and_never_silently_falls_back(self):
        with patch.dict(os.environ,{'STORAGE_MODE':'postgres','DATABASE_URL':''}):
            with self.assertRaisesRegex(ValueError,'needs DATABASE_URL'):Config(self.root)
        with patch.dict(os.environ,{'STORAGE_MODE':'postgres','DATABASE_URL':'postgresql://fixture'}):
            self.assertEqual(Config(self.root).db_url,'postgresql://fixture')

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
             'DATABASE_URL':'${race-db.DATABASE_URL}','LOCAL_DATABASE_PATH':str(self.root/'cli.sqlite3'),
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

for(const name of ['public','login','overview','race','players','settings','error']) {
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
```

## tests/test_postgres.py

```python
"""Run against a disposable database supplied as TEST_DATABASE_URL.

These checks never use DATABASE_URL implicitly. CI provisions its own database;
local development skips them unless a dedicated test database is provided.
"""
import copy
import os
from pathlib import Path
import secrets
import sys
import tempfile
import unittest
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from config import Config
from race import empty
from storage import Conflict, Store

TEST_URL = os.getenv("TEST_DATABASE_URL", "")
TEST_SSLMODE = os.getenv("TEST_DATABASE_SSLMODE", "require")


@unittest.skipUnless(TEST_URL, "No dedicated TEST_DATABASE_URL provided")
class PostgreSQLTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.key = "test_" + secrets.token_hex(12)
        self.environment = patch.dict(os.environ, {
            "APP_ENV": "production", "STORAGE_MODE": "postgres", "DATABASE_URL": TEST_URL, "DATABASE_SSLMODE": TEST_SSLMODE,
            "APP_STATE_KEY": self.key, "ADMIN_BOOTSTRAP_PASS": "synthetic-test-password",
        }, clear=True)
        self.environment.start()
        self.addCleanup(self.environment.stop)
        self.config = Config(Path(self.temp.name))
        self.store = Store(self.config)
        self.addCleanup(self.cleanup_database)

    def cleanup_database(self):
        self.store.close_job()
        with self.store.connection(transaction=True) as conn:
            for table in ("rh_live", "rh_recovery", "rh_admin"):
                conn.execute("DELETE FROM " + table + " WHERE name=%s", (self.key,))
            if conn.execute("SELECT to_regclass('wager_state')").fetchone()[0]:
                conn.execute("DELETE FROM wager_state WHERE name=%s", (self.key,))
        self.store.close()

    def test_admin_conflicts_are_transactional_and_live_updates_keep_revision(self):
        revision, admin = self.store.admin()
        snapshot = empty(admin["site_settings"])
        self.store.publish("shuffle", snapshot, revision)
        self.assertEqual(self.store.admin()[0], revision)
        admin["site_settings"]["race_title"] = "Saved change"
        self.store.save(admin, revision)
        with self.assertRaises(Conflict):
            self.store.save(admin, revision, snapshot={"wrong": True}, backup_reason="must-rollback")
        self.assertEqual(self.store.live("shuffle"), snapshot)
        with self.assertRaises(Conflict):
            self.store.publish("shuffle", {"wrong": True}, revision)
        self.assertEqual(self.store.live("shuffle"), snapshot)

    def test_provider_lock_is_shared_between_connections_and_services_are_independent(self):
        other = Store(self.config)
        try:
            with self.store.job("shuffle") as first, other.job("shuffle") as duplicate:
                self.assertTrue(first)
                self.assertFalse(duplicate)
                with other.job("kick") as kick:
                    self.assertTrue(kick)
            with other.job("shuffle") as released:
                self.assertTrue(released)
        finally:
            other.close_job()
            other.close()

    def test_previous_jsonb_state_imports_once_and_original_table_is_unchanged(self):
        from psycopg.types.json import Jsonb
        _, legacy = self.store.admin()
        legacy["site_settings"]["race_title"] = "Original saved title"
        legacy["custom_preserved_field"] = {"source": "existing deployment"}
        with self.store.connection(transaction=True) as conn:
            conn.execute("CREATE TABLE IF NOT EXISTS wager_state (name TEXT PRIMARY KEY, payload JSONB NOT NULL)")
            conn.execute("INSERT INTO wager_state(name,payload) VALUES (%s,%s)", (self.key, Jsonb(legacy)))
            conn.execute("DELETE FROM rh_admin WHERE name=%s", (self.key,))
        self.store.close()
        self.store = Store(self.config)
        revision, imported = self.store.admin()
        self.assertEqual(imported["users"], legacy["users"])
        self.assertEqual(imported["custom_preserved_field"], legacy["custom_preserved_field"])
        with self.store.connection() as conn:
            self.assertEqual(conn.execute("SELECT payload FROM wager_state WHERE name=%s", (self.key,)).fetchone()[0], legacy)
        imported["site_settings"]["race_title"] = "Newer title wins"
        self.store.save(imported, revision)
        self.store.close()
        self.store = Store(self.config)
        self.assertEqual(self.store.admin()[1]["site_settings"]["race_title"], "Newer title wins")

    def test_invalid_document_rolls_back_private_backup_and_admin_write(self):
        revision, admin = self.store.admin()
        candidate = copy.deepcopy(admin)
        candidate["invalid"] = float("nan")
        with self.store.connection() as conn:
            count = conn.execute("SELECT count(*) FROM rh_recovery WHERE name=%s", (self.key,)).fetchone()[0]
        with self.assertRaises(ValueError):
            self.store.save(candidate, revision, backup_reason="invalid-candidate")
        self.assertEqual(self.store.admin(), (revision, admin))
        with self.store.connection() as conn:
            self.assertEqual(conn.execute("SELECT count(*) FROM rh_recovery WHERE name=%s", (self.key,)).fetchone()[0], count)
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
from werkzeug.exceptions import HTTPException
from werkzeug.security import check_password_hash, generate_password_hash

from config import Config, RELEASE
from race import calculate, empty, phase, token
from race_support import (DEFAULT_PRIZES, WEIGHTING_RULES, TEXT_LIMITS, URL_FIELDS,
                          canonical_site, clean_overrides, clean_snapshots, csv_text,
                          decimal_amount, eastern_epoch, empty_snapshots, fmt_et,
                          local_input, money, money_input, race_key, validate_site)
from runtime import Runtime
from storage import Conflict, StoreError

LOG = logging.getLogger("redhunllef")
TABS = {"overview":"Overview", "race":"Race", "players":"Players", "settings":"Settings"}


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
        return request.accept_mimetypes.best == "application/json" or request.path in {
            "/data", "/config", "/stream", "/admin/status", "/admin/diagnostics", "/healthz", "/readyz"
        }

    def json_error(message, status):
        return jsonify(ok=False, error=message, status=status, release=RELEASE), status

    def require_csrf():
        if not secrets.compare_digest(str(request.form.get("csrf", "")), str(session.get("csrf", "!"))):
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
        if request.path.startswith("/admin"):
            g.revision, g.admin = runtime.sync()
            name, record = account(g.admin["users"], session.get("user"))
            if name and record.get("auth_version", 1) == session.get("auth_version"):
                g.user = name
                g.superadmin = name.casefold() == g.admin.get("superadmin", config.superadmin).casefold()
        if request.path not in {"/healthz", "/readyz"} and request.remote_addr in runtime.admin.get("banned_ips", []):
            abort(403, description="Access from this address has been disabled.")

    @app.after_request
    def after(response):
        response.headers.update({"X-Content-Type-Options":"nosniff", "X-Frame-Options":"DENY",
            "Referrer-Policy":"strict-origin-when-cross-origin", "X-RedHunllef-Release":RELEASE,
            "Content-Security-Policy":"default-src 'self'; script-src 'self'; style-src 'self'; img-src 'self' data:; connect-src 'self'; frame-ancestors 'none'; base-uri 'self'; form-action 'self'",
            "Cache-Control":"public, max-age=31536000, immutable" if request.path.startswith("/static/") and request.args.get("v") == assets else "no-store"})
        if request.is_secure:
            response.headers["Strict-Transport-Security"] = "max-age=31536000"
        if request.path.startswith("/admin"):
            response.headers["X-Robots-Tag"] = "noindex, nofollow"
        if request.path not in {"/data", "/config", "/stream", "/admin/status", "/healthz", "/readyz"} and not request.path.startswith("/static/"):
            with auth_lock:
                access_log.appendleft(dict(time=int(time.time()), method=request.method, path=request.path[:120], status=response.status_code,
                                           ip=request.remote_addr, ms=round((time.perf_counter()-g.began)*1000)))
        return response

    @app.context_processor
    def context():
        return dict(release=RELEASE, asset_version=assets, csrf=csrf, money=money, fmt_et=fmt_et,
                    local_input=local_input, tabs=TABS, weighting=WEIGHTING_RULES,
                    local_storage=not runtime.store.pg, hosted_local=config.production and not runtime.store.pg)

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
        return render_template("index.html", data=runtime.public())

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

    def render_admin(tab=None, draft=None, errors=None, confirm_race=False, restore=None, status=200):
        tab = tab or request.args.get("tab", "overview")
        if tab not in TABS:
            tab = "overview"
        values = runtime.status()
        visible = filtered(values["rows"], values["edits"], request.args)
        form = copy.deepcopy(g.admin["site_settings"])
        form.update(start_et=local_input(form["start_time"]), end_et=local_input(form["end_time"]))
        form.update({"prize_"+k: v for k, v in form["prizes"].items()})
        if draft:
            form.update(draft)
        return render_template("admin.html", data=values, tab=tab, form=form, errors=errors or {},
                               revision=(draft or {}).get("revision", g.revision), admin=g.admin, user=g.user,
                               superadmin=g.superadmin, participants=visible, confirm_race=confirm_race, restore=restore,
                               access_log=list(access_log), defaults=DEFAULT_PRIZES, limit=config.limit), status

    @app.route("/admin", methods=["GET", "POST"])
    @app.route("/admin/login", methods=["GET", "POST"])
    def login():
        if request.method == "GET":
            return render_admin() if g.user else render_template("login.html", error="")
        require_csrf()
        name, password = request.form.get("username", "").strip()[:64], request.form.get("password", "")
        key = request.remote_addr or "unknown"
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
        return Response(json.dumps(value, indent=2, ensure_ascii=False, allow_nan=False), mimetype="application/json",
                        headers={"Content-Disposition":"attachment; filename=recovery.seed.json"})

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
                if changed_race and request.form.get("confirm_race") != "yes":
                    return render_admin("race", dict(request.form), confirm_race=True)
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
                                    end=fmt_et(value["site_settings"]["end_time"]), rows=len(value["leaderboard_snapshots"]["last_top15"])))
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
        LOG.info("START RedHunllef %s listening on 0.0.0.0:%s; storage=%s.", RELEASE, config.port, "PostgreSQL" if runtime.store.pg else "local SQLite")
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
  "release": "2026.09.22-local",
  "entry_point": "python wager_backend.py",
  "source_files": {
    ".env.example": {
      "bytes": 673,
      "sha256": "36aa17cd82b15d44227ad341800246aaca78a207033ce8f6fd5f7f8c92b879c7"
    },
    ".github/workflows/test.yml": {
      "bytes": 1135,
      "sha256": "2a680f8f042171b63c2c7c73cebe0e087be46137f2004d1d15ebb3031787e48f"
    },
    ".gitignore": {
      "bytes": 126,
      "sha256": "b0c7255d064a0109a93e4082b580da57d58cf26d1cde4b85d953d59a9d5a88ad"
    },
    "CHANGES.md": {
      "bytes": 4263,
      "sha256": "44fc40835d61051bdbe83f2ff69d2eb88927e5e55f37a09c1e7a2a1ccfe37deb"
    },
    "FILE_STRUCTURE.md": {
      "bytes": 4172,
      "sha256": "58ad55b97c35f9f25011b10df7fbe3ce97452649a27a962923800b305a9de151"
    },
    "Procfile": {
      "bytes": 29,
      "sha256": "bcd054c38b5885dcf501be6763dbc12226edafe9320dc058cd820f563d035d83"
    },
    "README.md": {
      "bytes": 17323,
      "sha256": "b85e81ee4637b3b0da4b6f3d0b0a2a89985bdbdafd6f9d6739d267394426df3e"
    },
    "START_HERE.md": {
      "bytes": 2175,
      "sha256": "6cd58070da069bc46aa0cc07b26b8b4be1c3201e424b7810693f2299a4788252"
    },
    "app.yaml": {
      "bytes": 1440,
      "sha256": "8593c6d4ed1906bbcd675257f2e71af0e5fda94451704ef7a3d4d7e169bd231e"
    },
    "config.py": {
      "bytes": 6073,
      "sha256": "6e1060ebd963fe9e5a43850e3a6c27968495ca7565ba3e2c6d9da444f6af560c"
    },
    "docs/VALIDATION.md": {
      "bytes": 5296,
      "sha256": "1ab0814402250540784d15952dc6bb4adca499bfada404227821eeace572d739"
    },
    "integrations.py": {
      "bytes": 7041,
      "sha256": "1468838afdf081e4ce09e3598f6b5861c2feca090ef6f5ae4d3f24db94e214ea"
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
    "requirements-postgres.txt": {
      "bytes": 197,
      "sha256": "c77064a44093905f671aec742f1e9638eec34b1f295e89420053f17d3a7245a4"
    },
    "requirements.txt": {
      "bytes": 61,
      "sha256": "40f8bcf597ac5177f2f022e3ae5f787addb8e211c35f5d3505b7d778f4d0092d"
    },
    "runtime.py": {
      "bytes": 17577,
      "sha256": "426fcd9ec4ff3724e8be18208e7471f863379981f504b84466de62c95548d949"
    },
    "runtime.txt": {
      "bytes": 15,
      "sha256": "25dce2482c93ab6271d90809cd8ab8474830723459d2d0b51ce75bf7a72be92d"
    },
    "static/app.js": {
      "bytes": 18061,
      "sha256": "11adefead1598e50d8a10d8e74b514071bf9db993033dbaaefce86da3069ec4c"
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
      "bytes": 18352,
      "sha256": "fdccc104cb1f98987934725419519d6ba065c525b08151167c3e0ed010d65cb1"
    },
    "storage.py": {
      "bytes": 10998,
      "sha256": "f5c45adecbd2100b7b0bcde96e3a07ea3145072a5ef2a506a478ac6621150496"
    },
    "store_schema.py": {
      "bytes": 4551,
      "sha256": "b178eaa121bdf4dca84fc1daf5845bebaa04049c9e4302653f577bbb7a4bea98"
    },
    "templates/admin.html": {
      "bytes": 3982,
      "sha256": "f0ee24a6b915553881233e1f4f3e70cec6fdf0f3685d61fe77c43008dc6a29ef"
    },
    "templates/admin_overview.html": {
      "bytes": 2342,
      "sha256": "243bed71ed611c88606577258ee4e674457e8c9eda4151114446a41ac086206b"
    },
    "templates/admin_players.html": {
      "bytes": 4156,
      "sha256": "40eb1fa32633f4a0f9ce11a04f98bd8d99677227e443fee5c15bb48e671db859"
    },
    "templates/admin_race.html": {
      "bytes": 3121,
      "sha256": "12dafba7c83f846c25103f05af6ac266c84db667a2aaa08e4df45e3176e288a5"
    },
    "templates/admin_settings.html": {
      "bytes": 8993,
      "sha256": "d29d074e0139edd9f430b95415c6df3b3a8833ab38bccb682b3c5d69b26c260e"
    },
    "templates/base.html": {
      "bytes": 1983,
      "sha256": "cf741f66417d343e617b310f0e35dc2261a7aec3f3d277b8327849bde6ec8162"
    },
    "templates/error.html": {
      "bytes": 515,
      "sha256": "8c02ec7296f011932263817c387f5126d62238d1d7714bd57d64cb51917474be"
    },
    "templates/index.html": {
      "bytes": 4246,
      "sha256": "81af0536c04733b84a37c02e4d2685032f28ab03d842b9ccded523a112f2632d"
    },
    "templates/login.html": {
      "bytes": 1292,
      "sha256": "569a7023dbcb632ac9dd356660b23ea8e08b7d946b3905122c063cdb09b01a25"
    },
    "templates/macros.html": {
      "bytes": 2037,
      "sha256": "c221df4a851759c64be861363d83161223a367db24dde7f022c8b39e05a65324"
    },
    "tests/package.json": {
      "bytes": 160,
      "sha256": "6b16256bcf607689434a29ef7b06ead1bfea82387fa877c9f41f726395e12557"
    },
    "tests/render_fixtures.py": {
      "bytes": 2688,
      "sha256": "0efc4e2e8ccb6cc26ec3a1c1c2cf2466060381a0f50be677c1d68d819e3e12f1"
    },
    "tests/test_app.py": {
      "bytes": 40670,
      "sha256": "04d0c5621a3260f46b6cb4c13b9e059d4c40aae749700487c9faf8037db82eef"
    },
    "tests/test_frontend.cjs": {
      "bytes": 14283,
      "sha256": "9d6006ea5f499c0d56ad758c97859e0db24b49cdac043728f1e40ca1281e99f3"
    },
    "tests/test_postgres.py": {
      "bytes": 5360,
      "sha256": "88b177212c262aa3e289d155b8d41c5922a9afcf9ba88bb53d9e78e6357dbc89"
    },
    "wager_backend.py": {
      "bytes": 29370,
      "sha256": "dce9c159d449732ce3d1df4b3a5e53f7516aa9798dd6f74874f1eba266f89251"
    }
  }
}
```
