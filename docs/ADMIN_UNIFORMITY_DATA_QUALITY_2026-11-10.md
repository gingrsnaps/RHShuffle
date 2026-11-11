# RedHunllef — Unified Shuffle & EmpireDrop Admin

**Release:** `2026.11.10-admin-unified-v3`  
**Scope:** Admin UI, local operational diagnostics, source-quality presentation.  
**Compatibility:** Existing Shuffle wager engine, EmpireDrop Partner Public API v2.0.1, community games, boss, settings and JSON state remain in place.

## What changed

1. **Shared provider summary** (`provider_admin.py`, `templates/admin_provider_summary.html`). Shuffle and EmpireDrop now display the same operational fields: connection status, last verified update, last attempt, ranked players, provider refresh cadence, metric and data-quality flags. The dashboard shows a side-by-side provider overview on the main admin page. The dedicated tabs expose their own full details.
2. **Shuffle source reconciliation.** The Shuffle tab now displays source-record counts (returned, accepted, excluded, campaign metadata missing), full-source names for authorized admins, weighted and raw amounts, plus an advertised prize column for the current Top 15. Data remains scoped to the existing configured Shuffle race window. No wagering formula or campaign eligibility rule was changed.
3. **EmpireDrop source reconciliation.** The EmpireDrop tab displays provider-masked names, stable `user.hash_id` identifiers, official ranks (including tied ranks), race metric, localized wager/deposit amounts or ticket counts and locally advertised rank prizes. The underlying partner API still requires both `X-Public-Key` and `X-Private-Key`; no private keys are included in HTML or public feeds. Official race cache timing is respected, and the deprecated custom-date mode remains opt-in.
4. **Corrected search handler.** `static/admin-empiredrop.js` previously registered a nonexistent `filterPlayers` callback; the new shared source controller filters both tables, and EmpireDrop retains its own post-refresh filter logic.
5. **Separate Activity & Logs tab.** `templates/admin_activity.html`, `static/admin-logs.js` and `templates/admin_health.html` add structured status and log cards, severity/source filters, local keyword search, readable Eastern timestamps, explicit remediation hints, and JSON/TXT exports.
6. **Safer event classification** (`operations_log.py`). Backend logs now carry allowlisted categories such as `access`, `rate_limit`, `format`, `window`, `connection`, or the specific type of admin change. Arbitrary provider messages are *not* stored in the operations ring. Log retention is 300 process-local events; restarts clear the ring.
7. **Consolidated navigation and actions.** Shuffle-specific tabs are now labeled Shuffle race / Shuffle players, to distinguish them from EmpireDrop. The global admin refresh button is labeled Shuffle & Kick because it does not refresh EmpireDrop. EmpireDrop has its own worker-aware refresh control. Provider tiles link to the correct controls and the new Activity tab.
8. **Responsive styling.** Shared summary cards, per-source tables, optional explanatory warnings and service activity layouts now use consistent spacing, typography, and colors on desktop and mobile.

## Data correctness and limitations

### Shuffle

- The existing Shuffle affiliate feed returns raw and/or weighted wagering records for a configured reporting window. The code still uses the saved aggregation and weighting logic; it never mixes EmpireDrop amounts into Shuffle standings.
- The source validation counts accepted, rejected and missing campaign metadata in Admin. **Missing campaign metadata is a warning, not proof of affiliation.** The existing provider acceptance policy was preserved so this update doesn't unexpectedly remove players from a live competition. Confirm campaign scoping with Shuffle if your provider feed omits those fields.
- Admin can see full Shuffle names only when the source provides them; public names remain `first two characters + six asterisks`.

### EmpireDrop

- `GET https://api.empiredrop.com/api/v1/affiliate-partner/races` lists **running** races. It deliberately omits rankings and finished/scheduled races.
- `GET https://api.empiredrop.com/api/v1/affiliate-partner/races/{slug}` returns race details, `ranking[]`, `user.name`, `user.hash_id`, `total`, `unit`, `race.ranks_limit` and `race.cache_duration`. The endpoint is authenticated server-side with both partner API headers.
- `ranking[].total` is expressed in *minor currency units* on a ranking race but is a *ticket count* on a raffle. A deposit ranking is not a wager ranking. This release preserves the existing validated mapping and displays each metric explicitly.
- Provider-anonymized names cannot be reversed by the admin panel. Public rendering applies the two-character masking rule to the already-masked display names. Admin retains the official `user.hash_id` for tracking positions.
- The API may supply fewer than 15 ranks; the website cannot fabricate missing participants. Official dates are set by EmpireDrop. Custom periods use the deprecated legacy endpoint and may cease working.
- Historical prize figures are locally advertised settings, **not a payout transaction or confirmation**.

### Operational truthfulness

- A queued refresh is *not* a confirmed refresh. The admin status distinguishes the last attempted request from the last valid update.
- A failed provider response keeps the last valid snapshot and reports a warning. Empty rankings can be legitimate on new/closed races, not necessarily API errors.
- The operations viewer is not a durable audit log and cannot substitute for DigitalOcean runtime logs. Provider connection, keys, server outbound IP allowlisting, live response and deployment require validation on the actual service.
- No live EmpireDrop or Shuffle API calls were performed while preparing this package. Source mappings were validated against the supplied EmpireDrop OpenAPI specification and deterministic mock responses. **We cannot guarantee a live feed before testing from the deployed DigitalOcean server.**

## Admin instructions

1. Open **Admin → Overview** to compare both provider statuses quickly.
2. Open **Admin → Shuffle** for the Top 15 and received/accepted/rejected source counts, then use **Shuffle race** and **Shuffle players** for its settings and full participant list.
3. Open **Admin → EmpireDrop** to inspect its provider ranks and configure its own race slug, dates, and payouts. Use **Test API connection** before announcing results. Official race mode is strongly recommended.
4. Open **Admin → Activity & logs** for current service checks, source-specific errors, and JSON/TXT exports. Server health here is not a guarantee of upstream availability.
5. For failed requests, check the error category: `access` = API key/IP allowlist, `rate_limit` = provider throttle, `format` = response-schema change, `selection` = choose a race slug, `window` = date mismatch, `connection`/`timeout` = network or provider unavailability.
6. Export a **private recovery snapshot** under Settings before redeploying. JSON storage on DigitalOcean App Platform can be replaced on redeploy.

## Deployment

- Place the extracted source files **at the root** of a **private** Git repository.
- DigitalOcean Source Directory `/`; Python buildpack using `requirements.txt` with **no custom Build Command**; Run Command `python wager_backend.py`; port `8080`; health check `/healthz`; one instance.
- Both release ZIPs contain the user-requested existing private key pair in `private/settings.json` and the server-only fallback. Neither ZIP should be uploaded to a public repository. `.gitignore` excludes `private/` and `data/` from ordinary Git commits, so use encrypted DigitalOcean environment variables or another authorized way to provision your private configuration.
- A production health check can pass even when the provider blocks the app's outbound IP. Diagnose those errors in Admin → Activity & logs.

## Offline validation

```bash
python -m unittest tests.test_admin_uniform tests.test_empiredrop_qol tests.test_empiredrop_races tests.test_empiredrop_contract
node tests/test_empiredrop_frontend.cjs
python -m compileall -q .
python wager_backend.py --check  # Requires the pinned Python dependencies installed
```

Full application startup and Playwright browser tests require Flask/Waitress and Playwright to be installed. If dependencies aren't available, a source compilation pass is not a substitute for a production boot test.
