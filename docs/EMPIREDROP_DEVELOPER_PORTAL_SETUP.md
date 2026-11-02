# EmpireDrop Developer Portal: configuration and validation

Official portal: https://developers.empiredrop.com/

**Status: API contract NOT independently verified.** The linked portal loads client-side and did not expose an accessible Swagger/OpenAPI definition in this environment on October 30, 2026. We could not identify an official authenticated affiliate-wager endpoint, auth scheme, player response schema, pagination, or rate limit. The application will not make a production request until its *verified contract* checkbox is enabled by the site operator. No undocumented endpoint, request signing or guessed path is silently enabled.

## What was preserved

The complete source ZIP carries forward the original `private/settings.json`, `private/admin_store.seed.json`, and `data/` contents including any historical configuration and credentials, unchanged. Do not distribute or publish the archive or upload it to public Git hosting. A ZIP is **not encrypted**. The configuration is never rendered to public clients.

## Configure the endpoint (Superadmin)

1. Open the official portal with your affiliate account and find a *read-only, referral-scoped wager volume/leaderboard* endpoint. Confirm that the account is entitled to access it. An affiliate commission or deposit report is NOT the same as wager volume.
2. In Admin > EmpireDrop, enter the precise HTTPS API URL on an `empiredrop.com` subdomain, **not** the portal page.
3. Select the portal-documented authorization type: two separately named key headers, one key header, `Authorization: Bearer ...`, or HTTP Basic key pair. If the portal requires HMAC request signing, OAuth, or different headers/body, do **not** enable: the signed request format must be implemented to that official specification first.
4. Select HTTP GET or POST, query string or JSON parameter location, and whether timestamps are Unix seconds, Unix milliseconds, or ISO 8601 UTC. Dates are race start and current time, with independent Tuesday 6 PM ET windows. Confirm start inclusive/end semantics against the API.
5. Map the documented data fields, optionally with dotted JSON paths (`payload.players`, `player.username`, `stats.wagered`). Only wager volume fields should be mapped. A response can include referral code `red` in every row or the endpoint must be explicitly documented as scoped to code `red`.
6. Select already-aggregated per-player totals or uniquely identified transactions. Choose cursor pagination only when the official API documents the parameter and cursor response path.
7. Verify and save the contract checkbox. Use **Test API connection** first (read-only; doesn't publish). Compare with the source dashboard for the exact time window, currency, and player count. Only then use **Refresh**.

## Why the previous integration failed

The old adapter had empty official API URL, presumed two headers, Unix-second dates, GET query parameters, and shallow data fields. Those assumptions could block a correct provider response. This version supports multiple *configurable* request/response formats, but successful live operation still requires actual documented settings. It will not invent one.

## Troubleshooting

- `configuration`: missing verified contract, missing required key for selected auth method, or blank endpoint.
- `access` (401/403): key/environment mismatch, unsupported auth mode, IP allowlist, or missing API permissions. Check official contract; never put secrets in a URL.
- `rate_limit` (429): increase poll interval if official API rate limits don't allow 60 seconds; do not retry aggressively.
- `format`: wrong JSON rows path, field mapping, unit divisor, missing scope, incomplete pagination, or unexpected page schema. Avoid treating deposits/commission as wagers.
- `connection`: DNS, firewall, provider outage, or outbound network issue.
- Worker and HTTP failures do not replace previous same-period verified standings. New periods never inherit prior weeks' standings.

## Deployment

Build: `python -m pip install -r requirements.txt`

Run: `python wager_backend.py`

Health: `/healthz`

Use one App Platform instance. Container-local JSON storage may be lost on redeployment; download an authenticated private recovery checkpoint and preserve it externally. Never commit private keys or state to a public repository.
