# Community boss — play and host guide

One page, one boss, one community. Open `/play`, choose a style, and press Attack.
No account, wager, purchase, separate process, or additional dependency is needed.
The original `wager_backend.py` launcher serves the game and existing wager site.

## Rules players see in the game

- **2,400,000 health** by default. Everyone chips away at the same pool.
- **One manual attack per 60 seconds**, with up to **40 attacks per raid day**.
- **Blade, Bow, or Magic** deal 100 damage. Matching the current weakness deals
  150. The weakness changes every 10 minutes according to the server clock.
- Every **tenth personal hit adds 100 damage** as a Crimson burst. A matching
  burst normally deals 250. The final hit is capped at the remaining HP.
- The first successful community attack starts the raid-day clock. Allowances
  renew every 24 hours from that point, not at each player's local midnight.
- The game never regenerates health or spends unused attacks. A missed day
  does not subtract your contribution. Pausing blocks hits but not the calendar.
- Awakening, Enraged (75%), and Last stand (25%) are visual/story phases. They
  do not secretly change the damage rules or punish players who joined late.
- Victory remains visible. The host chooses when to start another raid.

The server rejects any attempt to heal the same raid or reverse its committed
damage. Health is always maximum HP minus saved cumulative damage. Cooldowns,
weakness changes and daily resets affect attacks only. The browser also rejects
healing snapshots, and the initial page percentage reflects saved health.
Process restarts retain progress when the same data file is preserved. Losing
that file through a container replacement is a separate recovery concern below.

The mobile attack dock offers the same controls and cooldown while you scroll.
Cosmetic milestones at 25%, 50%, and 75% damage change the arena and celebrate
progress. Badges recognize your first hit, ten bursts (100 hits), and three
distinct raid days. They grant no damage advantage. Victory's expandable recap
lists every contributor by raid alias; the ordinary live board shows the Top 10.
Use **Copy raid link** to invite the community. Errors remain until dismissed,
retried, or resolved; a routine poll cannot erase an unsuccessful attack message.

## Why it should last several days

With matching hits, every full ten-attack sequence deals 1,600 damage.
The following estimates assume 100 distinct, active players/networks making
that many attacks **each day**, all matching the current weakness:

| Daily attacks per person | Community damage per day | Allowance-days required |
| --- | ---: | ---: |
| 20 | 320,000 | 7.5 — victory during raid day 8 |
| 30 | 480,000 | 5 — victory during raid day 5 |
| 40 | 640,000 | 3.75 — victory during raid day 4 |

Only the first strike starts the schedule. A full 40-hit session needs at least
39 minutes because hits are manual and one minute apart. Smaller participation,
missed weaknesses, and shared connections extend the encounter. Community size
alone does not guarantee a finish date. A 100-player maximum-activity simulation
is part of the test suite; the default boss survives the first three allowances.

For later raids, the Superadmin can set **100,000–100,000,000 HP** in the new-raid
form. The current boss HP cannot be edited accidentally during play. Try the
default first and adjust the next encounter based on actual participation.

## Together, without accounts

Each browser gets an HttpOnly, signed guest cookie, separate from admin login.
Its anonymous `Raider XXXXXXXX` name lasts for the raid. The public top ten and
recent twelve hits use these aliases. They are cosmetic guest profiles, not
verified individual identities. Clearing cookies, changing browser, or starting
a new raid can change the name.

The server checks both the browser allowance and the connection allowance.
Changing cookies does not reset a network's limit; moving the same browser to
another network does not reset its personal limit. IPv4-mapped IPv6 normalizes
to IPv4, and IPv6 addresses in the same /64 share a connection allowance.
Shared Wi-Fi/NAT users therefore share an allowance. VPNs plus new browser
profiles can evade these lightweight limits; this is not cheat-proof identity.

Game records store salted HMAC keys rather than raw IPs or browser tokens.
Public game APIs omit the salt and those keys. The existing private web-access
log can still contain visitor IPs for page visits; game polling/attacks do not
flood that log. Browser cookies expire after one year; privacy tools may clear
them sooner. No user-generated chat or custom names need moderation.

## Host controls and recovery

Sign in at `/admin` and choose **Community boss**. Admins can view the shared
stats; only the Superadmin can pause, resume, export private recovery, or start
a new raid. A restart requires a checked confirmation and guards against an
outdated raid ID. It archives the previous result and resets players/allowances.
The latest ten summaries remain. A complete pre-restart checkpoint is also
recorded locally; it is not a remote backup.

**Save a private recovery file regularly during a multi-day raid and before a
planned deployment.** It includes the boss ID, HP, players, network hashes,
receipts, allowances, timestamps, history, and account/session state. The
ordinary race-only backup does not contain the game.

The recovery panel tracks when an export was generated and the progress since
then. Generation does not prove you saved the file off-host. Its review form
checks a recovery JSON file and shows account/race/boss totals without importing
anything. See `COMMUNITY_UPDATE.md` for the full recovery and storage explanation.

On a fresh App Platform instance, `private/recovery.seed.json` is imported
before the original seed. Existing local state always wins; a recovery file
never silently resets a running raid. Corrupt game recovery stops the first
import transaction rather than partially replacing accounts. Keep the current
`data/` folder when upgrading on a persistent host.

App Platform local disk is ephemeral. An unexpected replacement may lose
progress since the last downloaded-and-committed checkpoint. In-app hits are
saved immediately to the local SQLite file, but that does not make the disk
persistent. A no-remote-storage deployment cannot promise lossless multi-day
progress on an ephemeral host. Keep one instance; do not scale local storage
across independent containers. If that limitation becomes unacceptable, use
a host with a persistent disk or deliberately opt into the existing remote
storage compatibility; neither is required for this package to launch.

## How updates stay lightweight

The server does no provider requests while handling a game click. A transaction
locks the boss record, reads current state, validates the hit and receipts, and
commits its damage. Race settings and provider snapshots are separate records.
Most viewer requests use a small in-memory snapshot; it reloads at most every
five seconds per process and immediately reflects local writes. A separate
GET returns only public summaries plus the requesting player's limits.

The page polls every five seconds while visible and immediately on return or
network recovery. Countdown animation uses server time plus a monotonic browser
clock. Old responses cannot undo newer damage. If the response to a click is
lost, the browser keeps that request ID and can retry it; the server returns
its saved receipt. There are no automatic attacks. Snapshot responses use
no-store and same-origin cookies/CSRF. Stale connections disable fresh attacks
until a successful update arrives.

Game data is bounded to 2,000 browser profiles per raid, 4,000 retained network
records, 12 recent hits, 10 leaders, and 10 past raid summaries. Old network
records are pruned as raid days advance. This is intended for the approximately
100-person community, not a public internet-scale MMO.

## DigitalOcean setup

Build: `python -m pip install -r requirements.txt`

Run: `python wager_backend.py`

Keep port `8080`, health check `/healthz`, and one web instance. No game worker
or new component is needed. Set `TRUST_APP_PLATFORM=1` only behind App Platform;
the game uses its documented `DO-Connecting-IP` header. For local/direct hosting,
use `TRUST_APP_PLATFORM=0` so arbitrary proxy headers are ignored. A missing or
invalid trusted header disables new attacks rather than merging all players
under an ingress IP. See README.md for full deployment and recovery steps.
