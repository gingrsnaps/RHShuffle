# Unified Admin and Provider Data Quality — November 10, 2026

The latest update adds matching Shuffle and EmpireDrop administration cards, a dedicated Activity & Logs tab, read-only record validation metrics, clean JSON/TXT logs, and a fix for EmpireDrop player search. No new dependencies or provider API changes were introduced. See `docs/ADMIN_UNIFORMITY_DATA_QUALITY_2026-11-10.md` for the full changes and limitations.

> **CURRENT RELEASE (Nov 10, 2026):** EmpireDrop now has independent payouts, admin date controls, masked public usernames, a source-aware countdown, sanitized activity logs, and settings backup/restore. See [the new setup and limitations guide](docs/EMPIREDROP_QOL_WEEKLY_PAYOUTS_2026-11-10.md). Official races use their own EmpireDrop dates; custom/weekly windows use a **deprecated** endpoint that EmpireDrop may remove.

> **CURRENT RELEASE (Nov 10, 2026):** The authoritative EmpireDrop integration instructions are in [docs/EMPIREDROP_OPENAPI_FIX_2026-11-10.md](docs/EMPIREDROP_OPENAPI_FIX_2026-11-10.md). Previous generic API configuration, legacy `/race/affiliates/{publicKey}` discovery, and manually mapped rows are superseded. The official production origin is `https://api.empiredrop.com`, and both authentication headers are mandatory.

> **DigitalOcean App Platform:** This ZIP is flat-root. Do NOT upload the ZIP as a file in GitHub. Extract it, commit the root-level code, and read [DEPLOY_DIGITALOCEAN.md](DEPLOY_DIGITALOCEAN.md). The App Platform build command must be blank; `python -m pip install -r requirements.txt` below is for local usage only.

# Start RedHunllef

Release **2026.10.08-community-clarity7** — complete configured package.

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
**2026.10.08-community-clarity7**; this complete package now includes the latest
eight games, shared wallets, five-second private rankings, the health overview and refined mobile controls.

## Updating an existing installation

Preserve current `data/`, private files, recovery seeds, runtime settings and player
cookies. Merge code into the matching paths; do not replace newer private seeds
with bundled originals. There is no reason to reset the boss or clear cookies.
Reload after restarting and check `/healthz` for **2026.10.08-community-clarity7**.

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

**DigitalOcean Build Command:** leave empty (dependency install is automatic)

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


## November 10 admin / Shuffle recovery patch

See `docs/SHUFFLE_400_ADMIN_TIMEZONE_FIX_2026-11-10.md` for verified findings from
the operations report and actions for the live DigitalOcean server. The original
JSON state, accounts, historical race and private settings are preserved.

**Private repository only:** `shuffle_deploy_key.py` and
`empiredrop_deploy_keys.py` contain live server-only fallback credentials as
requested. Never publish this repository; encrypted environment variables
remain the safer long-term option.
