# RedHunllef

**Release: 2026.10.08-community-polish6** — complete configured Python application.

Run everything through **`python wager_backend.py`**. The web server, automatic
Shuffle/Kick checks, race history, community boss and all eight RedPoints games
start together. Supporting Python files are imports, not additional launchers.
No SQL service, Node production build, separate worker or account-creation command
is required.

## Start

Install the included requirements, then start the application:

```bash
python -m pip install -r requirements.txt
python wager_backend.py
```

Open `http://localhost:8080`. Production should use the HTTPS address supplied by
DigitalOcean. Gameplay verification requires HTTPS or localhost.

The bundled original account seed and provider configuration are included.
Existing saved accounts and changed passwords take precedence over the seed.
The original fresh-install Superadmin is documented in `START_HERE.md`.
**Keep this configured package and its private files private.**

An optional packaging check uses the same launcher and does not create accounts,
reset balances, contact providers or start a server:

```bash
python wager_backend.py --check
```

Normal startup checks required imports, templates and assets automatically.
`--check` additionally checks packaged file hashes. Intentional code edits require
updating the build manifest before using strict verification; they do not silently
reset data or block ordinary startup merely because a hash changed.

## DigitalOcean App Platform

Use a Python **Web Service** connected to your private repository.

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
| Instance count | `1` |
| Health check | `/healthz` |
| `APP_ENV` | `production` |
| `PORT` | `8080` |
| `SESSION_COOKIE_SECURE` | `always` |
| `TRUST_APP_PLATFORM` | `1` |

`app.yaml` contains the same deployment shape. Replace its repository placeholder
before importing it. `Procfile` uses the same Python launcher. No database binding
is needed. Remove obsolete database binding expressions from the App Platform
configuration if the platform tries to resolve them before startup.

Use `TRUST_APP_PLATFORM=1` only behind App Platform ingress. The app accepts
`DO-Connecting-IP` as connection metadata in that mode; it does not make an IP
address a player credential. Keep one instance because separate local files cannot
coordinate multiple replicas.

### What persists

A process restart that retains `data/` preserves accounts, names, boss progress,
receipts and unfinished hands. By the requested rules it resets available Gaming
balances to 100,000. Refreshing a Gaming page also sets that player's available
balance to 100,000, preserving pending stakes and records.

**App Platform container replacement is different. Its local filesystem is
not persistent.** A deployment/replacement can remove the entire `data/` folder,
including local recovery copies. This package does not add an external storage
service and cannot guarantee recovery from a lost container.

Before a planned replacement, use **Admin → Settings → Private recovery
checkpoint**. Save the download outside the server. For a new container, place
your latest export at `private/recovery.seed.json` in your private deployment
source. It is imported only if current state does not exist. This restores the
exported checkpoint, not activity that occurred after it. During an active
community session, arrange a quiet update window to minimize that gap.

Official storage explanation:
https://docs.digitalocean.com/products/app-platform/how-to/store-data/

## Updating an existing installation

1. Save a private recovery export and retain a copy of the currently working code.
2. Stop the old process. Merge the new source, templates and static files into the
   matching folders. Preserve your current `data/`, private configuration, recovery
   seeds, environment settings and session-signing key. Do not replace newer
   private configuration with the bundled original seed.
3. Install `requirements.txt` with the Python interpreter used for startup.
4. Run `python wager_backend.py`. Reload the browser after startup.
5. Check `/healthz` for `2026.10.08-community-polish6`, sign into `/admin`, and
   review **Overview → Behind the scenes**. Confirm the intended race dates.

Existing state wins over bootstrap files. A corrupt state file causes a clear
startup failure rather than a silent reset. The old local SQLite importer remains
for existing installations migrating from that historical release; new operation
uses the JSON file and no database service.

The old combined `FULL_CODE_BLOCKS.md` is not needed at runtime. This distribution
contains the actual files in their own folders instead of a combined source dump.

## Pages

| Page | Address |
| --- | --- |
| Current wager race | `/` |
| Four completed weeks, public masked Top 25 | `/history` |
| Community boss | `/play` |
| Gaming dashboard | `/gaming` |
| Games | `/gaming/dice`, `/gaming/keno`, `/gaming/plinko`, `/gaming/blackjack`, `/gaming/limbo`, `/gaming/coinflip`, `/gaming/poker`, `/gaming/baccarat` |
| Rules and local receipt verifier | `/gaming/fairness` |
| Admin | `/admin` |
| Admin game rankings | `/admin/gaming` |
| Points Shop | `https://botrix.live/k/redhunllef/shop` |

## This update

- **Independent health checks.** `/healthz` checks the running process. `/readyz`
  checks local state access and a tiny temporary write, cached for 15 seconds.
  Shuffle/Kick outages no longer make readiness fail. They remain visible in the
  admin health cards and connection details.
- **Private health overview.** Website, Shuffle, Kick, Games and Saved data cards
  show current checks and next steps. A copyable/downloadable support report uses
  allow-listed fields and excludes player names, IPs, credentials, password hashes,
  private game seeds and provider response bodies.
- **Measured storage.** Bounded in-memory samples show request latency, file size,
  save time, copy time and lock waits. Every response receives `X-Request-ID`;
  machine-readable errors include the same reference. Server-error logs include
  that ID and the route name, without request bodies or query strings.
- **Consistent recovery.** Full exports capture accounts, wallets, pending hands,
  boss state and history from one store transaction. Preview compares account,
  wallet and pending-hand counts against the current save. Uploading a preview
  does not restore or change records. Superadmin recovery previews allow up to
  64 MiB; ordinary requests and avatar uploads retain their existing limits.
- **Cleaner mobile layout.** Every main header destination stays visible. Gaming
  has a compact selector, a smaller wallet, and available/in-play/last-net labels.
  Active card hands hide the redundant new-hand wager form. Mobile table actions
  stay within their game area.
- **Shorter dashboard.** Eight consistent game cards, visible resume-hand links,
  explicit positive/negative results and a five-round preview with View all.
  Expanding history or focusing a receipt survives unchanged wallet polls.
- **Clear play states.** Submitting, checking a proof, animating and recovering
  have different labels. Results remain server-authoritative. Animations never
  decide a payout, invent a reroll, or submit an extra bet.
- **Smaller page-specific code.** Only the Plinko page downloads the canvas
  renderer. Hold'em UI code is loaded only for Hold'em. Shared proof code stays
  available for verifying older receipts from any game.
- **Consistent red styling.** Shared colors, panel treatments, inputs, focus rings,
  comfortable primary touch controls and reduced-motion support. Boss phase
  shading changes cosmetically with remaining health; damage rules are unchanged.
- **Clearer history.** Saved standings are labelled separately from provider-
  confirmed results. The homepage prioritizes the race and standings, followed
  by the community boss invitation.

`docs/VALIDATION.md` records the checks run for this release and their limits.
`docs/PERFORMANCE.md` describes measurement targets and the local load sample.

## Automatic updates

Shuffle and Kick are checked automatically every **60 seconds** by independent
jobs inside the launch process. Public and admin source screens refresh every
60 seconds. Boss and wallet views check saved local state every **5 seconds**.
Hidden browser tabs pause their own polling and catch up when visible; source
workers continue running. There is no optional live-data mode.

ETags avoid unchanged wallet/public response bodies. Polls preserve user drafts,
selected numbers, focused controls and existing card hands. Failed provider
requests retain confirmed data and display a delayed status instead of fabricating
standings. A successful check and a change in standings are separate facts.

Four completed history windows run **Tuesday 6 PM Eastern → Tuesday 6 PM Eastern**,
using the time-zone database across daylight-saving changes. Public history shows
up to 25 censored names. Provider access/rate limits can still delay confirmation;
saved results remain available during retries.

## Admin and privacy

Existing administrator accounts and password hashes are preserved. Admin writes
require a current session and CSRF protection. Full recovery exports and account
management remain restricted to the Superadmin. Other current admins retain their
existing race, boss, avatar and ranking permissions.

The admin Players tab retains full names and the expandable first 100 Code Red
wagerers. The Gaming section retains separate Top 5 lists for all eight games,
full community names and recorded connection IPs. Legacy Video Poker records
remain separate from Hold'em. Funding adjustments are labelled and excluded from
game net winnings. **Give everyone +100,000 RedPoints** remains additive and
retry-safe; it does not erase scores or pending hands.

Shuffle/Kick credentials are resolved from existing private configuration with
nonempty runtime environment overrides available for `SHUFFLE_API_KEY`,
`KICK_CLIENT_ID` and `KICK_CLIENT_SECRET`. The values are never included in public
pages or health reports.

## Boss and RedPoints rules retained

- Shared boss health drains full → empty and never regenerates automatically.
  Explicit admin HP edits remain possible. Attacks are allowed every 30 seconds,
  with no daily/weekly hit cap. Random weaknesses and eight achievements remain.
- Boss avatar/name/HP/damage settings remain admin-only. PNG/JPG/JPEG/WebP uploads
  are decoded and validated. HP/damage retain their existing exact-integer range.
- Gaming uses non-monetary RedPoints, not Shuffle funds or Botrix shop points.
  A confirmed community name and signed player identity share one wallet across
  all games. People on a shared IP can play independently. IPs are private admin
  metadata, not a credential for taking over another player's identity.
- Starting allowance is 100,000. Gaming refresh/restart funding and Tuesday weekly
  resets retain their requested behavior. Pending stakes remain reserved, and
  duplicate requests do not duplicate bets or admin grants.
- Dice sliders remain draggable; Keno allows 1–10 picks; 16-row High Plinko retains
  its 1000x edge outcomes. Blackjack, Limbo, Coinflip and Baccarat keep their
  existing rules and probability calculations.
- Hold'em is heads-up Texas Hold'em versus **RedBot**, a clearly labelled computer
  opponent. Pot accounting, blinds, legal raises, ties, all-ins and unmatched-bet
  refunds remain governed by the existing deterministic engine.
- New rounds use **redpoints-v5**. Existing v1–v4 proofs and unfinished legacy
  Video Poker/Blackjack hands remain supported. Published deck/seed commitments,
  client randomness and independent receipt replay are unchanged.

See `docs/REDPOINTS.md` for detailed rules and `docs/COMMUNITY_BOSS.md` for boss
controls. There is no new gameplay quota in this update.

## Files and developer checks

`FILE_STRUCTURE.md` lists this complete distribution. `BUILD_MANIFEST.json`
contains hashes for application source/assets; private configuration and mutable
state are intentionally not subject to source-integrity checks.

| Folder/file | Purpose |
| --- | --- |
| `wager_backend.py` | Sole launch script and HTTP routes |
| Root Python modules | Storage, providers, games, health and configuration |
| `templates/` | Server-rendered pages and reusable page parts |
| `static/` | Styles, browser behavior, proof verifiers and original logos |
| `private/` | Original private configuration and account seed |
| `data/` | Created at runtime; preserve on a persistent host |
| `docs/` | Rules, validation, performance notes and screenshots |
| `tests/` | Optional developer tests; not required to run the site |

Python regression checks:

```bash
python -m unittest discover -s tests -p 'test_*.py'
```

Optional frontend checks use Node only on a developer machine:

```bash
python tests/render_fixtures.py .test-fixtures
npm --prefix tests install --ignore-scripts
npm --prefix tests test
```

Real-browser scripts are `tests/gaming_motion.cjs`, `tests/holdem_motion.cjs` and
`tests/experience_motion.cjs`. They use temporary synthetic accounts and do not
contact Shuffle or Kick. Set `RH_TEST_PYTHON` to the desired Python interpreter
and `RH_CHROMIUM` to an installed Chromium executable, or install Playwright's
browser for development. `RH_SCREENSHOTS` selects a local output directory.
