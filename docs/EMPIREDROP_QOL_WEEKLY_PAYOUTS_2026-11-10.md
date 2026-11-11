# RedHunllef · EmpireDrop race administration and UI update

Release: `2026.11.10-empiredrop-qol-v2`.

## Features delivered

1. **Matching public names.** Both provider tabs now show first two characters followed by exactly six `*`. Shuffle admin names remain unmasked when its API supplies them. EmpireDrop admin names remain as masked by EmpireDrop itself; the API cannot reveal full names.
2. **Independent EmpireDrop payout pool.** Superadmin can enable/disable the pool, choose EUR or USD, and configure 15 rank rewards individually. The pool is the sum of these 15 entries. Zero/disabled by default, because the project must not advertise an unapproved prize. This is site-advertised data; it does not initiate payments or modify EmpireDrop's own prizes. Provider rank ties split a rank's amount among the players returned at that rank, and skipped ranks stay skipped.
3. **Timeframes.** Modern partner races use the provider's own dates, as in OpenAPI 2.0.1. For arbitrary week/custom dates, the admin calendar saves its own period and activates the deprecated `GET /api/v1/race/affiliates/{publicKey}?start_timestamp=...&end_timestamp=...`. The old endpoint requires a private key header and could be removed by EmpireDrop. Use this only when the site owner accepts that risk. To use current official race standings, switch back to Official race mode and select the official race slug.
4. **Enhanced logs.** Admin → Diagnostics → Activity logs supports service/severity filters and safe JSON/TXT exports. Only event names, service, timestamp, counts, HTTP status and duration are logged. Sensitive data, IP addresses, user names and raw provider responses are excluded. The ring contains at most 300 events and resets on restart.
5. **Health dashboard.** EmpireDrop appears next to Shuffle and Kick in admin health checks. Its staleness test respects provider `race.cache_duration` instead of assuming Shuffle's 60 seconds.
6. **Prettier player UI.** Both tabs have a countdown, a payout pool, top-3 podium with payout, and places 4–15 with prize column. Empty states don't fabricate wager amounts, names or prizes. Text is concise: “Each site has its own race, standings, and prizes.”
7. **Saved history.** Four most recent verified EmpireDrop snapshots can be shown publicly with anonymized names. Changing a later reward schedule does not modify the frozen prize configuration on newly archived snapshots. These are local snapshots, not proof of official payment or definitive results.
8. **Safety and recovery.** New EmpireDrop settings export/import contains only the mode, slug, time window and local rewards, never credentials. Import requires Superadmin, CSRF, a current revision and explicit confirmation. Full recovery exports under Admin → Settings remain separate and are still required to back up account/game state. DigitalOcean App Platform local JSON files are ephemeral; make off-server recovery copies.

## Exact EmpireDrop API contract

- Production origin: `https://api.empiredrop.com`
- Running-races list: `GET /api/v1/affiliate-partner/races`
- Detail and ranking: `GET /api/v1/affiliate-partner/races/{slug}`
- Both current endpoints require `X-Public-Key` and `X-Private-Key` server-side headers.
- Current race dates: `race.start_date`, `race.end_date` (UTC). Ranking: `ranking[].rank`, `ranking[].user.name`, `ranking[].total`, `ranking[].unit`.
- `ranking[].total` is in minor currency units for rank races, but in whole tickets for raffle races. `total_value` is only a formatted string.
- Deprecated custom-window endpoint: `GET /api/v1/race/affiliates/{publicKey}` with `start_timestamp` and `end_timestamp` as Unix UTC seconds and `X-Private-Key` header. It does **not** change any modern race and has fewer features. A 404/410/other removal response will show as a safe warning and retain last successful data for the same scope.
- `race.ranks_limit` is authoritative. The website cannot fabricate positions when EmpireDrop returns fewer players.
- Use `race.cache_duration` to avoid needless calls. Manual requests are coalesced and the worker respects cache intervals.

## Admin instructions

1. Open **Admin → EmpireDrop**.
2. Under **Weekly payouts and prize pool**, enter positions 1–15, choose the payout currency, check **Show this payout schedule publicly**, then save.
3. Under **Affiliate race connection**, use **Official EmpireDrop race** and select the slug to use provider-defined dates and current standings. Leave the slug blank only when there is exactly one running race.
4. To set custom dates or weekly Tuesday 6 PM Eastern, use **Independent race dates**, then **Save EmpireDrop schedule**. This switches the provider mode to the deprecated time-window endpoint. The relevant code is explained in `empiredrop_races.py` and `empiredrop.py`.
5. Check **Test API connection** and **Request EmpireDrop refresh**. Results update automatically subject to the provider cache.
6. **Admin → Diagnostics → Activity logs** shows safe service events with downloadable reports. Download an EmpireDrop settings backup before changing many settings.

## Important limitations

- The project has not been authenticated live against your EmpireDrop account in this environment. Permissions, account IP allowlist and any provider API deprecation are external factors.
- The website **does not pay anyone** and cannot verify whether provider-listed prizes or site-listed prizes have been distributed.
- Only the user-supplied public/private key pair is retained in server-only private configuration and `empiredrop_deploy_keys.py`. The server must be deployed in a **private repository** and logs must remain sanitized. Prefer encrypted DigitalOcean environment variables for long-term deployment.
- A production deploy should contain `requirements.txt` and `wager_backend.py` at the repository root. DigitalOcean Build Command should be blank; Run Command `python wager_backend.py`, HTTP port `8080`, health check `/healthz`.

## Testing

No network calls are made by unit tests. Test commands:

```bash
python -m unittest tests.test_empiredrop_qol tests.test_empiredrop_races tests.test_empiredrop_contract
node tests/test_empiredrop_frontend.cjs
python -m compileall -q .
```

Flask and Waitress integration tests require installation of `requirements.txt` and an isolated testing state file. The above tests do not prove that the real provider is accessible from your DigitalOcean service.
