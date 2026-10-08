# Start RedHunllef

Release **2026.10.08-community-polish6** — complete configured package.

Install dependencies once, then run only the existing launcher:

```bash
python -m pip install -r requirements.txt
python wager_backend.py
```

Keep all root Python modules, templates and static files together. They are
imports, not separate launch commands. No database server, Node build, account
creation utility or extra worker is needed.

| Destination | Address |
| --- | --- |
| Homepage / wager leaderboard | `/` |
| Completed-week history | `/history` |
| Community boss | `/play` |
| Gaming dashboard | `/gaming` |
| RedPoints games | `/gaming/dice`, `/gaming/keno`, `/gaming/plinko`, `/gaming/blackjack`, `/gaming/limbo`, `/gaming/coinflip`, `/gaming/poker`, `/gaming/baccarat` |
| Fairness / local receipt verifier | `/gaming/fairness` |
| Admin / private game Top 5 lists | `/admin`, `/admin/gaming`, `/admin?tab=gaming` |
| Requested external Points Shop | `https://botrix.live/k/redhunllef/shop` |

The original supplied Superadmin remains **gingrsnaps / enok2121** on a fresh
install. Existing accounts and changed passwords take precedence. Original private
provider configuration and logos are included. Keep this configured package private.

Open **Gaming top 5** in the admin header. Confirm the installed label reads
**2026.10.08-community-polish6**; this complete package now includes the latest
eight games, shared wallets, five-second private rankings, the health overview and refined mobile controls.

## Updating an existing installation

Preserve current `data/`, private files, recovery seeds, runtime settings and player
cookies. Merge code into the matching paths; do not replace newer private seeds
with bundled originals. There is no reason to reset the boss or clear cookies.
Reload after restarting and check `/healthz` for **2026.10.08-community-polish6**.

On a persistent Linux host the existing `data/state.json` wins. A previous local
SQLite save is imported read-only once if no JSON exists. Corrupt saves stop
startup instead of silently resetting progress.

## DigitalOcean App Platform

Use one Web Service, one instance, source directory containing `wager_backend.py`,
port **8080**, health path **/healthz**. Set these runtime variables:

```text
APP_ENV=production
PORT=8080
TRUST_APP_PLATFORM=1
SESSION_COOKIE_SECURE=always
```

**Build:** `python -m pip install -r requirements.txt`

**Run:** `python wager_backend.py`

No database component is needed. Remove old unresolved database bindings.
The included `app.yaml` is a template; set its private GitHub repository name.

**App Platform replaces local files during redeploys/container replacement.**
Before a planned deployment, download **Settings → Private recovery file** as the
Superadmin and save it as `private/recovery.seed.json` in your private repository.
A fresh container imports that checkpoint. Changes after export, or after an
unexpected container loss, cannot be recovered without another saved copy.
The full export now includes RedPoints, current fairness seeds and receipts.

## What stays automatic

- Shuffle/Kick: 60-second background source checks and public/admin status refresh.
- Boss: five-second display checks, no regeneration, unlimited daily/weekly hits,
  30-second server cooldown, random weakness and eight unchanged achievements.
- Gaming: one shared 100,000-point allowance per browser profile, reset Tuesday at
  6 PM Eastern. No refill on refresh/name changes. Five-second wallet checks.
- History: four completed weeks, masked Top 25, independent retries and safe
  diagnostics in Admin → Completed-week history. Saved snapshots are provisional
  until confirmed. A live Shuffle history request timed out during validation;
  use the new diagnostics after deployment if your provider still fails.

RedPoints are play-only and separate from Botrix/Shuffle balances. Each round
publishes a seed commitment and then reveals a verifiable receipt. Full rules and
limits: `docs/REDPOINTS.md`. Setup/recovery: `README.md`. Complete code in separate
blocks: `FILE_STRUCTURE.md`.
