# RedHunllef

Release **2026.10.06-redpoints-holdem5** — Hold’em update for the configured project.

Install dependencies once, then launch the entire website with the same script:

```bash
python -m pip install -r requirements.txt
python wager_backend.py
```

Open `http://localhost:8080`. There is no database server, Node build, separate
worker, game launcher or account-creation step. All supporting Python modules
must stay beside `wager_backend.py`; the app imports them automatically.

## This release

- **Eight games:** Dice, Keno, Plinko, Blackjack, Limbo, Coinflip, Texas Hold’em and
  Baccarat. All use the same RedPoints wallet and community name.
- **Less text:** controls, balance and results remain visible. Payouts, client seed
  and commitment details are expandable. Full rules live at `/gaming/fairness`.
- **Smooth play:** Dice travels to its recorded roll; Keno reveals numbers in order;
  Plinko follows its saved peg path; card games deal and reveal cards progressively;
  Limbo climbs to its exact multiplier; Coinflip lands on its saved face.
  Bets, draws and name saves use background requests, without page reloads or dialogs.
- Completed results are verified before presentation; unfinished card hands display their saved server state. Result labels follow the animation.
  Reduced-motion preferences, hidden tabs and animation fallback paths still show
  the exact saved outcome. Multiple Plinko balls share one canvas loop.
- **Baccarat:** fresh eight-deck Punto Banco, Player / Banker / Tie bets. Total
  returns are 2× / 1.95× / 9× respectively, rounded down to whole points. Banker
  includes 5% commission; Player and Banker wagers push on a tie. Automatic draw
  rules and exact receipt encoding are published in `docs/REDPOINTS.md`.
- All eight private admin Top 5 lists track actual net winnings, full names and
  recorded IPs. Funding grants do not count as winnings.
- New bets use **redpoints-v5**. All v1–v4 proofs remain verifiable. Saved Blackjack
  and Video Poker hands keep their original seed, cards and rules. Video Poker
  statistics move once into a separate admin legacy section.
- Original accounts, provider configuration, logos, live race/history, boss game,
  mobile navigation and the external Points Shop remain included.

This update supplies complete contents of changed and new files only. Apply them
to the working configured project, retaining `data/`, `private/`, settings, original
seeds and all unlisted files. Keep `poker.py`: archived hands still import it.
The launch command and requirements are unchanged. New supporting files are
`holdem.py`, `static/holdem-fairness.js`, `static/holdem-ui.js`,
`static/holdem.css` and `templates/holdem_table.html`.

## Retained: shared connections and automatic playable balances

The old one-wallet-per-IP rule could block an entire household, VPN or community
behind a proxy. Gaming now identifies each player by their signed browser cookie
and recovery code. Many people may share an IP; missing IP forwarding does not
block registration, bets or balance refreshes. Existing IP records migrate in
place and remain admin-only. No accounts, names or game results are merged.

- Save a community name on Gaming once to activate at least **100,000 RedPoints**.
- Refresh the Gaming dashboard or a game page to set your available points to
  **exactly 100,000**. Changing games and five-second polls keep your balance.
- Starting `wager_backend.py` restores **100,000 to every saved wallet**.
  This can reduce a larger balance; actual net winnings and receipts stay intact.
- Tuesday at 6 PM Eastern still starts a new weekly balance and standings.
- **Admin → Gaming → Give everyone +100,000 RedPoints** adds points to all existing
  wallets without altering winnings. Repeating the same request cannot grant twice.
- Name confirmation, unfinished card hands, fairness seeds, receipt history
  and per-game standings survive page refreshes and restarts within the same week.
- An admin grant, another tab or restart during a reload no longer requires another
  manual reload: the browser retries one stale-wallet response with current data.

Merge the complete package into your existing project, restart the same launcher,
then reload Gaming once to load this release. Do not delete `data/` or `private/`.
No new dependencies, database, account-creation command or launch script is needed.

## Eight RedPoints games and visible admin rankings

| Page | What it does |
| --- | --- |
| `/gaming` | Dashboard for all eight RedPoints games, shared balance, weekly results and recent receipts. |
| `/gaming/dice` | Choose a 1–95% win chance and roll under/over the target. |
| `/gaming/keno` | Pick 1–10 of 40 numbers, draw 10, choose Low/Medium/High risk. |
| `/gaming/plinko` | Choose 8/12/16 rows and Low/Medium/High risk; watch the verified path. |
| `/gaming/blackjack` | RedPoints-only six-deck Blackjack: Hit, Stand and Double; saved hands and verifiable receipts. |
| `/gaming/limbo` | Choose a target multiplier; reach it to win at that target. |
| `/gaming/coinflip` | Pick Heads or Tails; 50% win chance and 1.98× total return on a win. |
| `/gaming/poker` | Heads-up no-limit Texas Hold’em versus RedBot: blinds, betting rounds, shared board, saved hands and pot settlement. |
| `/gaming/baccarat` | Eight-deck Punto Banco with Player, Banker and Tie bets, automatic draws and verified card reveals. |
| `/gaming/fairness` | Published rules, exact seed format and a browser-only receipt verifier. |
| `/admin/gaming` or `/admin?tab=gaming` | Eight private Top 5 lists; full names, shared player IDs, linked IPs, actual net winnings, stakes, returns and counts. |
| `/history` | Four completed Tuesday-to-Tuesday weeks, public Top 25 masked before delivery. |

The public header keeps **Leaderboard, History, Boss fight, Gaming, Points Shop,
configured Red Community, and Watch on Kick** visible on mobile. It wraps into
rows with usable tap targets. Points Shop opens the requested external URL:
https://botrix.live/k/redhunllef/shop. Its balance is separate from RedPoints.

### One shared RedPoints wallet

Each confirmed player starts with **100,000 RedPoints total**, shared across
all eight games. Each browser player has a separate wallet, even on the same IP.
Page refreshes restore that player's balance to 100,000. Server restarts restore
all saved wallets to 100,000. Names, seeds, receipts, unfinished hands and winnings
are preserved. The weekly reset clears per-game standings at the next **Tuesday,
6:00 PM America/New_York** boundary, including daylight saving changes. This is
the same fixed boundary as public history; editing the race form does not reset it.

- Play-only points: no purchase, cash value, withdrawal or conversion to Shuffle or
  Botrix balances. These games do not add to the real Shuffle wager leaderboard.
- Wagers are positive whole points within the balance and exact-integer range.
  There is no fixed stake cap, timed delay or daily/weekly count limit. A player
  with no points can refresh the Gaming page to get 100,000 again.
- Save a community name on Gaming before playing. An existing boss name is offered
  as a suggestion; confirming it activates Gaming. Both use the same signed identity.
  A saved private recovery code restores that identity in another browser.
- Names are self-reported labels, not authentication or proof of a Shuffle account.
  An IP never grants access to someone else's wallet. People on a shared connection
  can all play independently. Moving networks keeps the same signed player's wallet.
  Connection records are visible only to admins; absent/full IP tracking never
  prevents a valid player from playing.
- Private rankings sort **net winnings = points returned − points wagered**,
  then total returned points, then a stable short profile tag. Losses remain visible
  and do not masquerade as profit. Only players who played that game appear.
  Both Admin Overview and Gaming include all eight Top 5 lists. A dedicated local
  poll refreshes them every five seconds, with a manual refresh button. Shuffle
  and Kick keep their separate 60-second refresh. Player/round counts cover all
  players, not just the displayed five. Rankings are cleared from the visible
  dashboard when the admin session expires.
- The server settles debit, return, next seed and receipt in one atomic save.
  Repeating an uncertain request returns its original receipt without a second
  debit. Concurrent tabs cannot spend the same seed/nonce twice.

### Verifiable outcomes

Every round has a SHA-256 server-seed commitment published **before** the bet,
a player-editable client seed, fresh random client salt generated after the
commitment is read, and a sequential nonce. HMAC-SHA-256 plus unbiased rejection
sampling determines the outcome. The one-time server seed is revealed immediately
after settlement. Independent browser code verifies the previous commitment,
submitted inputs, result and payout before reporting “Verified.”

Keep downloaded receipts and the commitment seen before playing. The dashboard
retains the latest 30 receipts per profile across all eight games and weekly
resets. An older standalone receipt proves internal consistency, not publication
time unless you separately kept its earlier commitment. The independent verifier
can also run offline with `python tools/verify_redpoints.py receipts.json`; this is
an optional audit utility, never another server process. Full algorithm, payout
math, examples and limits: [docs/REDPOINTS.md](docs/REDPOINTS.md).

### Verify the installed gaming release

Use every file in the current cumulative update ZIP together; an older complete
archive does not include this fix until these files are applied over it.

After applying all included code/templates/static files and restarting, open
**`/admin/gaming`**. Its installed-release label must show
**2026.10.06-redpoints-holdem5**. The header also includes **Gaming top 5**.
If the panels are empty, check the displayed player/round counts and weekly reset.
Only completed RedPoints rounds on this server create those records. Shuffle
wagers and boss attacks are separate. Never invent entries to fill five places.
Restore the latest private recovery backup if a redeployment replaced local data;
this update cannot reconstruct results that were never saved or backed up.

### Game controls and card hands

- Plinko follows the verified left/right path with a single animation loop and
  parabolic peg bounces; multiple balls can animate together. High risk with
  **16 rows reaches 1000×** (8-row High: 29×; 12-row High: 170×).
- Keno's **Quick pick 10** chooses ten distinct numbers. Manual picks stay 1–10.
- The large Dice bar is draggable on mouse and touch, with matching threshold,
  win percentage and payout. Roll Over inverts the threshold correctly.
- Blackjack spends **RedPoints only**, with the same wallet as the other games.
  A fresh six-deck shoe is sampled without replacement per hand. Dealer stands
  on all 17s and checks naturals before decisions. Hit, Stand and Double on the
  first two cards are available. Naturals pay 3:2 profit, other wins 1:1, pushes
  return the stake. Returns round down to whole points. No splitting, insurance
  or surrender. No fixed Blackjack RTP is advertised: decisions affect returns.
- Blackjack reserves the stake, hides the hole card/seed until completion, resumes
  on reload, and settles each move/hand only once. At the weekly boundary an
  unfinished hand automatically stands under the old week before the new balance.
  Double counts the full doubled stake in both the ledger and admin rankings.
- Hold’em reserves an equal table stack for each seat. The player chooses a stack
  of at least 20 RP; blinds are 1/50 of that stack (minimum 2), and half that for
  the small blind. The button alternates. Preflop, flop, turn and river have legal
  Fold, Check, Call, Bet, Raise and All-in actions. Best five of seven wins.
- An unfinished Hold’em hand resumes on refresh. Weekly expiry folds it under the
  old week without placing another bet, then resets the allowance. Unused and
  uncalled chips return with pot winnings. Rankings count only actual committed
  chips and pot awards, not the reserved stack or refresh funding.
- RedBot is a published deterministic heuristic, not a human or external AI API.
  It receives only its own cards and public betting information. The independent
  verifier replays its decisions as well as the fixed deck and pot accounting.
- Legacy Video Poker hands still hold/draw once under their original v3/v4 rules.
  Its old module and proofs are retained; its results are separate from Hold’em.
- Current fairness rules are `redpoints-v5`; v1–v4 receipts remain verifiable.
  The startup rule still restores available points to 100,000.

### Homepage and boss refinements

- **Boss health** explicitly labels the bar. All HP bars drain full → empty;
  the separate **percent defeated** label rises 0% → 100%.
- A last-confirmed age makes the five-second boss checks visible. Failed or stale
  replies retain confirmed health and cannot pretend to be a new successful check.
- Explicit admin HP adjustments show a brief public notice. Recorded player damage
  is unchanged. A new raid still has its own separate identity and progress.
- An optional collapsed **Latest community hit** shows a masked name and damage.
- Boss administration includes a homepage appearance preview for a draft name,
  a local avatar file, and current health. Previewing never submits an upload or
  changes a setting; the existing separate save controls remain authoritative.
- Original red logos, compact leaderboard-first layout, native admin navigation,
  inline confirmed-save receipts, draft preservation and reduced-motion behavior
  remain intact. No new runtime dependencies or additional launch processes.

## Four completed weeks of public history

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

### Why history could stay stuck, and what changed

Previously, a failed request for the first completed week ended the whole batch.
That same week was retried first, so the other three could remain unrequested.
The queue now attempts each independent date range and prioritizes untried weeks.
Shared access failures, rate limits or upstream outages defer all four together,
with explicit retry information instead of unexplained “Loading” messages.

Exact-window saved race snapshots are recovered before the next request. These
are visibly marked **provisional saved places**, since an earlier Top 15/25
snapshot is not necessarily the final standings. A successful historical response
replaces them with the provider's confirmed Top 25. No results are fabricated.

Open **Admin → Completed-week history** (available on each dashboard tab) for
HTTP status, a safe failure reason, last result, next retry, and the active week.
**Check history now** queues background checks and respects provider retry windows.
It does not tie up the admin request or flood a rejected account. Console lines
start with `HISTORY` and name the period and category without exposing credentials.
Independent errors retry after 60 seconds, increasing to at most 15 minutes;
provider Retry-After instructions can extend that wait. Completed requests have
longer read timeouts than the live feed because historical ranges can be slower.

The existing Shuffle endpoint, authentication and date parameters are unchanged.
**Live requests from the validation environment timed out without an HTTP response.**
The queue/retry/recovery changes were verified with controlled provider responses;
this package does not claim that your four real historical weeks were retrieved.
After deployment, the private diagnostics distinguish access, rate limiting,
upstream failure, date-range rejection, malformed data and network timeouts.

Admin regression coverage includes all existing dashboard tabs plus Gaming, native login/logout,
race preview/publication, automatic/manual refresh, overrides, Code Red Top 100,
CSV export, accounts/passwords, backups/restore, logs/IP controls, and boss
name/avatar/HP/damage/pause/restart controls. Also fixed the self-block check to use
the actual trusted visitor IP on App Platform instead of the proxy socket address.

After updating, restart the app and reload the homepage. `/healthz` should report
**2026.10.06-redpoints-holdem5**. Asset versions change automatically, so the new
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
**2026.10.06-redpoints-holdem5**. If it shows something else, the old application is
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
2. Merge all files from the update ZIP into the existing folder.
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
two commands above. Visit `http://localhost:8080`, `/history`, `/play`, `/gaming`, and `/admin`.

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
so multiple replicas would split boss progress and RedPoints wallets. A process restart that keeps the same
data folder preserves names and game records and restores each wallet to 100,000.
A container replacement or redeployment can remove local saves.
DigitalOcean documents this restriction in
[Store Data in App Platform](https://docs.digitalocean.com/products/app-platform/how-to/store-data/).
**RedPoints cannot be guaranteed to survive container replacement with local-only storage.** This release adds no external persistence service. The existing manual recovery
export is the available checkpoint method on App Platform. On a persistent Linux
host, preserve the `data/` folder during code updates.

Use `TRUST_APP_PLATFORM=1` only behind App Platform ingress. The app then uses
`DO-Connecting-IP` for admin request logging and existing access controls. Game identity does not depend on that header. On a directly exposed/local host, leave
it unset or `0`. Arbitrary client forwarding headers are not accepted as identity.

## Accounts and automatic updates

`/admin` renders the login or dashboard directly. The new Gaming tab is part of the same authenticated dashboard. All management routes require a
current admin account, an unrevoked session, and CSRF protection for writes.
The Superadmin manages administrator accounts and downloads full private recovery.
Other current admins can manage boss controls and avatars, and
view full player names in the private Top 5.

Both Shuffle and Kick are checked **automatically every 60 seconds**, by independent
threads inside the sole launch process. There is no live-data switch or manual-only
mode. The public leaderboard and admin provider views refresh every 60 seconds;
a manual source refresh shows progress until the check finishes. Boss public/admin and Gaming wallet views refresh every **5 seconds**. Wallet polls use ETags so unchanged responses have no body. Hidden browser tabs pause their own polling
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
to you and administrators; the arena uses a raider alias and the homepage latest-hit panel uses a masked name.

| Rule | Behavior |
| --- | --- |
| Attack cooldown | 30 seconds, checked by the server. |
| Daily/weekly quota | None. |
| Default damage | 100 base, 150 weakness, +100 burst every tenth hit. Admin-editable. |
| Weakness | Random stable draw every 10 minutes, shared by all players. Repeats are valid. |
| Health | Never regenerates automatically. Confirmed damage stays saved. |
| Progress / HP bars | All health bars drain full → empty; the separate defeated percentage rises 0% → 100%. |
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
| `data/state.json` | Current accounts, race settings, live snapshots, raid, profiles, avatar, history and RedPoints wallets/proofs. |
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
Top 15, four-week history, boss avatar, private profiles, contribution totals, boss admin history, RedPoints balances, per-game totals, active private seeds and revealed receipts.
It is not exposed publicly. Keep the full recovery file private: it includes active fairness seeds and account secrets. The recovery reminder now notices wallet/proof changes too. A restored Top 15 remains a snapshot until the next
successful live source check. The recovery status records when an export was
created, not proof that someone saved it externally.

## File structure and complete code

The base configured project is still required. The Hold’em update contains only
changed/new files, each with its full contents. `holdem.py` and the new static
files are imports/assets; only `wager_backend.py` launches the site.

The older complete ZIP, `FULL_CODE_BLOCKS.md`, `FILE_STRUCTURE.md` and
`MANIFEST.json` describe the base release. Their archived inventory/hashes are
not a manifest for this patch. No account, logo or provider-setting replacement
is needed. Keep `poker.py`, `blackjack.py`, `baccarat.py` and all unlisted modules.

An old `manage_admin.py` is not required. Keep your existing local state and latest
private recovery export when updating. Do not include test fixtures or runtime
saves when committing this configured package to your private repository.

## Verification

See `docs/VALIDATION.md` for the base release checks; the Hold’em regression suite
is `tests/test_holdem.py`, with independent reference generation in `tests/holdem_vectors.py`. Tests use
synthetic players, seeds and provider replies; they do not place real bets or
contact Shuffle/Kick. This package has not been deployed to your account.

The Python and independent browser verifiers agree on **484 reference receipts**:
47 v1, 86 v2, 112 v3, 151 v4 and 88 v5. Baccarat checks cover every initial total and
possible Player third-card value, each bet side, payouts, naturals and pushes.
Native Chromium checks all eight games, animation sequencing without navigation,
mobile widths, Hold’em recovery, reduced motion and private admin rankings.

Developer checks are optional; they are not website launch commands:

```bash
python -m unittest discover -s tests -q
python tests/render_fixtures.py .test-fixtures
npm --prefix tests install --ignore-scripts
npm --prefix tests test
```

For native animation checks, install the optional Playwright Chromium browser and
run `node tests/gaming_motion.cjs`. Set `NODE_PATH=tests/node_modules` if needed.
`RH_TEST_PYTHON` selects the Python interpreter; `RH_CHROMIUM` may select an existing
Chromium executable. The fixture creates temporary state and never reads the
configured private files. `RH_SCREENSHOTS` selects the preview output directory.
