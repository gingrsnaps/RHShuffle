# EmpireDrop Top 10 and last verified refresh — November 11, 2026

## Summary

This release is based on `2026.11.11-empire-public-mask-v7` (the previously working EmpireDrop public leaderboard). It does not change the EmpireDrop API host, authentication headers, race slug, rank calculation, Shuffle worker, Community Boss, games, or database/storage architecture.

## Changes

- **Public leaderboard:** EmpireDrop is **Top 10**, not Top 15. Places 11–15 no longer appear, even if the provider offers more. The server-rendered first paint and live JavaScript both show the same ten places. The podium (positions 1–3) and table (4–10) preserve official tied ranks.
- **Admin:** EmpireDrop's current standings table and payout editor show ten positions. Shuffle remains Top 15. Admin's player ID/name handling is unchanged.
- **Independent EmpireDrop reward pool:** New payout configurations have places 1–10. Older saved settings and backup exports with 15 places load correctly, but the saved values for places 11–15 are ignored in the *displayed pool and rewards*. When an administrator saves again, only ten places are stored. The previous bundled JSON bytes are not overwritten by this archive.
- **Time since successful update:** The same source-status area that Shuffle uses now displays `Updated Ns ago` for EmpireDrop, based on the `updated_at` timestamp from the last successful provider check. Failed or repeated local `/public-state` polls do not reset the timer.
- **Next check:** Shows `Next provider check in Ns` derived from the worker's actual monotonic deadline and the provider's `race.cache_duration` (often 300 s). It is *not* a fabricated 60-second provider fetch. During initial checks and when the worker is stopped, the display says `Provider refresh not scheduled`; transient `Next provider check due` means the job is due.
- **Unified status:** Switching tabs switches the source status without overwriting Shuffle's time. Refresh indicators tick every second on the browser and update after every successful `/public-state` poll.
- **Secrets:** The existing production keys and private state are preserved verbatim in both private ZIPs. Browser assets and public data never contain the credentials.

## Tests

- `tests/test_empiredrop_public_ssr.py` validates Top 10 initial HTML with 10/15 provider rows and tied ranks.
- `tests/test_empiredrop_frontend.cjs` validates initial and live Top 10, local prizes, rank ties, refresh countdown, delayed updates, and source-status tab switching.
- `tests/test_empiredrop_qol.py` checks historical 15-place prize migration, public/admin/history Top 10, and private user-ID isolation.
- Other existing contract and race tests are retained. An authenticated live production fetch and full Flask startup are not exercised in the isolated packaging environment.

## Deployment

Extract the ZIP contents into the root of a **private** Git repository and deploy with DigitalOcean App Platform's Python buildpack. Build command is blank; run command is `python wager_backend.py`; port is 8080; health check is `/healthz`. Do not deploy the ZIP as a single file inside the repository. Clear the browser cache after rollout if the old JavaScript is still cached (asset version is updated).

**Important:** Live JSON in DigitalOcean's container filesystem is ephemeral. Back up the *current* running state before redeploying. The saved state in the ZIP is an older snapshot and must not overwrite newer production state. Keep the unencrypted production credential archives private.
