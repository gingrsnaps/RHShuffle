# EmpireDrop Race Slug 404 Recovery — November 11, 2026

## Evidence behind the patch

The owner reported `Source unavailable · EmpireDrop 404: race slug not found or not owned by partner.` followed by `EmpireDrop check did not finish (scope)`. The operational JSON from earlier the same day contained an authenticated EmpireDrop HTTP 200 with ten players. The Shuffle worker later recovered 829/829 received rows, so neither issue indicates a general HTTP listener failure.

## What was wrong

The backend used the manually saved `race_slug` without checking whether it had been replaced by a newer active race. A 404 immediately stopped the refresh even with the **Automatically select** box enabled. A configuration-scope change also hides standings from a different race, which is correct for contest integrity but can make the public board appear empty after an invalid slug is saved.

## Patch behavior

- The current `GET /api/v1/affiliate-partner/races/{slug}` is tried first when an explicit slug is saved.
- If that exact request returns **404** and automatic selection was enabled, the worker requests `GET /api/v1/affiliate-partner/races` with both official API key headers.
- Recovery is allowed only when **exactly one currently active WAGER/RANKING race** exists. A deposit or raffle race cannot silently replace the wager competition.
- The fallback race detail must then return HTTP 200 and pass the same strict race response validation before rankings are published.
- If zero or multiple eligible races exist, or the single listed race's details also return 404, the system stops and reports an actionable error. It does not guess or fabricate standings.
- The successful response records `race_meta.selection: recovered` and provides a protected admin warning. The saved explicit slug is **not rewritten** without administrator approval.
- Manual refresh after a saved configuration-scope change may run immediately rather than waiting for the old race's `cache_duration`. Unchanged-scope requests still honor the provider's cache interval.
- The **Discover affiliate races** button now offers verified race slugs in a selector. Choosing one only fills the form; an administrator must click **Save race API connection** to change settings.

## Admin recovery steps

1. Open **Admin → EmpireDrop → Race API & selection**.
2. Choose **Official EmpireDrop race · provider-controlled dates** and **Official EmpireDrop start_date / end_date**.
3. Click **Discover affiliate races**. This endpoint lists running races only; it cannot list finished or scheduled ones.
4. If exactly one eligible race appears, either **clear the saved Race slug** and enable **Automatically select**, or choose that race and explicitly save its slug.
5. Click **Save race API connection**. This schedules a provider check for the new scope.
6. Run **Test API connection** and verify that the result reports a successful authenticated validation and the expected number of players.
7. Verify the public EmpireDrop tab. The provider controls its ranking window and `race.ranks_limit` controls the maximum returned positions.

## Interpretation of common responses

- **404:** selected slug not found or inaccessible with these partner credentials. Verify the exact slug and API partner account.
- **401:** missing API keys.
- **403:** mismatched/invalid credentials or blocked egress IP.
- **429:** rate limited; respect `race.cache_duration`.
- **HTTP 200 with zero rows:** may be a new, ended, or inactive race; is not automatically an API failure.
- **`EmpireDrop check did not finish (scope)`:** a backend classification of the slug issue, not an additional provider failure.
- **`HTTP GET unmatched route returned 404`:** your website's inbound 404, unrelated to the EmpireDrop API unless the requested route proves otherwise.

## What this patch cannot prove

There is no authenticated live EmpireDrop request from the DigitalOcean app in these offline tests. A successful API list/detail response is still required to confirm that the live partner account owns the race and has standings. `private/settings.json`, account seed, gaming state and Shuffle behavior are carried forward unchanged. The packages intentionally contain server-side production keys, so **keep the archive and Git repository private**.
