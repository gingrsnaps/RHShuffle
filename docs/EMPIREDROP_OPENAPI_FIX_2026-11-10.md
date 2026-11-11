# EmpireDrop Partner API 2.0.1 — verified integration changes

The contract in `docs/empiredrop_partner_openapi_2.0.1.yaml` is the user-provided official OpenAPI 3.0.3 specification. This release removes the earlier guessing and implements the two *current* endpoints.

## Endpoints and authentication

- Base: `https://api.empiredrop.com`
- `GET /api/v1/affiliate-partner/races` lists **running** races, without participants.
- `GET /api/v1/affiliate-partner/races/{slug}` returns the selected race details and `ranking[]`.
- Both requests MUST send both `X-Public-Key` and `X-Private-Key`, read only on the Python server.
- The legacy `GET /api/v1/race/affiliates/{publicKey}` is deprecated and **not used** by race mode.
- Never follow redirects with credentials or make API calls from the public browser.

## JSON mapping

- Races list: `races[]`; select the only running race, or specify the slug in Admin.
- Race metadata: `race.slug`, `race.name`, `race.start_date`, `race.end_date`, `race.engine`, `race.type`, `race.currency`, `race.is_active`, `race.ranks_limit`, `race.cache_duration`.
- Ranking: `ranking[].rank`, `ranking[].user.hash_id`, `ranking[].user.name`, `ranking[].total`, `ranking[].unit`.
- Currency on **RANKING** races: `ranking[].total` is *minor units* of `ranking[].unit`; EUR 563744 => €5,637.44. `total_value` is display-only and is deliberately ignored to avoid losing decimals.
- **RAFFLE** races: `ranking[].total` counts **tickets**; no currency sign is applied. Unit must be `TICKETS`.
- **DEPOSIT** races: amounts represent deposits and are labeled **Deposited**, never wagered.
- Display provider-assigned rank numbers; ties may share a rank and cause skipped ranks.
- The provider already anonymizes `user.name`; even the Admin UI cannot reveal clear names using this API.
- The count may be less than 15: `race.ranks_limit` is authoritative.
- `prizes[].amount`, `winners[].amount`, `race.total_prizes` are in minor units of the site's **default** currency, not necessarily `race.currency`. The current page does not falsely convert those values.
- Rankings may be empty when the race has ended. Previously verified standings are retained as a local snapshot when the slug is unchanged.

## Automatic polling

The race response is cached for `race.cache_duration` seconds; the worker refresh interval follows it, not 60 seconds. A 429 response triggers a longer backoff. The public website may poll its own local state frequently without generating extra EmpireDrop API traffic.

## Your keys and deployment

Your production public/private keys are present in `private/settings.json` and in `empiredrop_deploy_keys.py` (server-side fallback). This was explicitly requested so Git deployments can still use them even when `.gitignore` excludes `private/`.

**Do not put this project in a public repository.** The fallback Python module is deliberately NOT ignored by Git. Use a private repository, encrypted deployment environment variables as a stronger alternative, and rotate the keys if this code was previously shared. Backend environment variables override the bundled pair.

When deploying to DigitalOcean App Platform:

- Source Directory: `/` (files at repository root, not in an enclosing ZIP folder)
- Runtime: the pinned `runtime.txt`
- Build Command: **empty** (buildpack handles requirements.txt)
- Run Command: `python wager_backend.py`
- HTTP port: `8080`
- Health check: `/healthz`
- Only one instance when using local JSON storage; App Platform's filesystem is ephemeral, so back up state frequently.

**A live authorized provider connection was not performed here.** The downloadable package is verified against the supplied OpenAPI schema and mocked 200/401/403/404/429 scenarios, but not against your actual live race. If the admin reports `403`, check whether the partner key pair is enabled and whether its API IP allowlist permits the DigitalOcean outbound IP.

## First launch

1. Back up current site data (`data/state.json` or your admin recovery export).
2. Deploy the corrected source from a **private** Git repository.
3. Sign in as Superadmin; open **Admin → EmpireDrop**.
4. Click **Discover affiliate races**. The list contains running races only.
5. If one is running, it is auto-selected; if multiple run, enter the correct slug from the EmpireDrop dashboard and save.
6. Click **Test API connection (no changes)**. Check any typed error in the admin panel.
7. Click **Request EmpireDrop refresh**, then inspect the public EmpireDrop tab. Its currency/unit, dates and Top N should match the partner dashboard.
8. When importing old `data/state.json`, the previous incorrect auth/field settings are overridden in memory by the current contract. If it still says **legacy** mode, choose **Official EmpireDrop Partner API** and save.

## What is intentionally unchanged

Shuffle integration, Community Boss, RedPoints games, site branding, history, prize definitions and administrator accounts were not redesigned. The production ZIP excludes heavy development-only documents; the full ZIP keeps original project files, private configuration and recovery snapshots.
