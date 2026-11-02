# EmpireDrop Races integration — 2026-11-02

This update uses the two **GET** paths explicitly provided from the developer portal:

- `/api/v1/race/affiliates/{publicKey}` — locate affiliate races by public key.
- `/api/v1/affiliate-partner/races/{slug}` — obtain the selected race detail document.

The exact origin (`https://empiredrop.com` vs. a dedicated EmpireDrop API
subdomain), detail endpoint authentication, response schema, wager field
semantics and units **have not been independently verified**. The developer
portal is JavaScript-rendered and its referenced tag pages did not provide a
machine-readable response. This release is an implemented and offline-tested
integration, **not** a confirmed successful live production connection.

## Server-side credentials

Your supplied production public and private keys are embedded in
`private/settings.json` inside **both** ZIP packages, alongside the existing
secret configuration. The secret is NOT included in frontend JavaScript, HTML,
public `/public-state`, or unauthenticated diagnostics. Environment variables
`EMPIREDROP_PUBLIC_KEY` and `EMPIREDROP_PRIVATE_KEY` override the bundled keys
if they are already configured on DigitalOcean.

The public key is appended to the **discovery route** as a URL segment.
The secret is **not** sent for discovery. When an administrator selects a
provider-confirmed detail authentication method, the private key is included
only in the HTTPS request to the validated `*.empiredrop.com` host. Redirects
are rejected before following to a different host. HTTP read timeouts, payload
size limits, and response JSON validation apply.

## First deployment: safe admin workflow

1. Deploy the optimized production archive contents to your *private*
   deployment source, retaining the server-side private settings. Back up
   the current live JSON data **before redeploying**.
2. Log in as Superadmin and go to **Admin > EmpireDrop**.
3. Set **Official race endpoints** and check the API host. The routes are
   appended automatically; do not enter a path in the host field.
4. Click **Discover affiliate races**. This only uses the public key and
   returns sanitized race identifiers and response field shapes.
5. If the response contains multiple active races, enter the chosen `slug`.
   Otherwise auto-selection accepts only one clearly active race.
6. Click **Inspect selected race fields**. Check the field names/types returned.
   This does not output private keys, username values, or wager amounts.
7. Set participant array path, username field, amount field, units divisor,
   currency, and optional stable user ID based on the **actual** response and
   the official affiliate dashboard. No monetary results are published before
   you explicitly confirm these settings.
8. If the race details route returns 401/403, configure the documented
   authentication scheme and test it. Do **not** try random secret headers.
9. Check **I confirmed leaderboard fields, currency and divisor against
   EmpireDrop**, save, then run **Test API connection** and **Request refresh**.
   Results update automatically every 60 seconds thereafter, subject to the
   provider's rate limits.

## Important behavior

- `race_window_policy=provider` (default): show the actual reported EmpireDrop
  race dates if returned. If they are unavailable, show “Provider race dates not
  yet confirmed” instead of deceptively borrowing Shuffle's Tuesday schedule.
- `race_window_policy=local`: require a **precise** match to Tuesday 6PM Eastern
  race dates before publishing. You cannot safely segment one aggregate race
  total into different dates without transaction-level data.
- Only aggregated player wagers are accepted; repeated records for the same
  stable ID use their maximum, not a sum. The parser does **not** substitute
  deposits, earnings, prizes or box openings for wagering values.
- A failed fetch never wipes a previous verified leaderboard; it is labeled
  delayed. An unconfigured new race is not populated with old arbitrary data.
- Last four prior verified race snapshots are stored under `live.empiredrop_history`
  in the existing local JSON state file. Those snapshots are not an offsite
  backup and will be lost on ephemeral App Platform containers unless exported.
- The existing Shuffle backend, prizes, games, boss and admin system remain
  separate. No new database is introduced.

## API diagnostics and failure causes

| Symptom | Likely interpretation |
|---|---|
| Discovery 404 | Wrong API host/path, missing route, or invalid public key |
| Details 401 / 403 | Missing permissions or incorrect documented auth method |
| Details 429 | Rate limit; reduce polling frequency with provider approval |
| Discovery returns no recognizable slugs | Inspect response shape; do not invent a race slug |
| Multiple active races | Configure race slug explicitly |
| Participants array not found | Inspect `race_rows_path` |
| Records but no recognized wagers | Verify `race_name_field`, `race_wager_field`, amount divisor |
| Fields verified checkbox not checked | Intentional stop until admin confirms monetary mapping |
| Live data missing after successful ZIP deployment | Deploy success is unrelated to provider access; inspect admin diagnostics |

## Build and run

`requirements.txt` remains pinned and the custom build command remains blank.
Use `python wager_backend.py` and port `8080` on one DigitalOcean instance.

Because `.gitignore` excludes `private/` and `data/`, uploading the ZIP to Git
will **not** automatically commit the bundled secrets or saved data. Prefer
DigitalOcean encrypted environment variables for credentials. A ZIP with the
private file is included as specifically requested, but **never push** it into
public Git history, issue trackers or support tickets.

## Files changed

- `empiredrop_races.py`: new documented-endpoint adapter, mapping, validation.
- `empiredrop.py`: connected the real worker to the race adapter, selected
  race and provider period, latest-good fallback, four-race history.
- `wager_backend.py`: protected discovery, probe and save routes; test endpoint
  now tests the selected API mode.
- `templates/admin_empiredrop.html`: race settings, diagnostics and history.
- `static/admin-empiredrop.js`: safe interactive admin diagnostics.
- `static/empiredrop.js`, `templates/index.html`: provider race mode display.
- `private/settings.json`: your specifically supplied production key pair.
- `tests/test_empiredrop_races.py`: offline race API and worker regression tests.
- `tests/test_empiredrop_contract.py`: explicit legacy mode for legacy tests.
- `tests/test_empiredrop.py`: scope helper adjusted for race-mode-aware snapshots.
- Release manifests / release documentation: hashes and deployment details.

## Verification limits

Offline checks do not authenticate to EmpireDrop, and cannot establish the true
JSON contract, field units, permissions or whether your affiliate has an active
race. The package is deliberately explicit about these unresolved requirements.
