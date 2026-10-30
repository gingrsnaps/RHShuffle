# RedHunllef Release Notes — October 30, 2026

## EmpireDrop API integration update

- Preserved the prior project's **original** `private/settings.json`, `private/admin_store.seed.json` and all `data/` files, including credentials and account history. This archive is **not encrypted**. Keep private.
- Kept the independent EmpireDrop referral `red` leaderboard, the Tuesday 6 PM Eastern schedule, automatic 60-second refresh, separate admin panels, public masked names, and isolation from Shuffle ranking/prizes.
- Added configurable HTTP GET/POST transport, query/JSON parameters, five standard authentication options (two-header, private-header, public-header, bearer-private, Basic key pair), three timestamp formats (Unix seconds/milliseconds/ISO 8601 UTC) and nested JSON field mappings.
- Retained strict HTTPS `empiredrop.com` host checking, no automatic redirects, safe HTTP errors, max body/page limits, unique transaction deduplication, referral-code gating and last-good same-period result protection.
- Expanded administrator configuration UI, and added offline unit tests for new auth, data, timestamp and request-body paths.
- Added `docs/EMPIREDROP_DEVELOPER_PORTAL_SETUP.md` with a step-by-step source-of-truth configuration workflow.

### Still required to enable live EmpireDrop results

`https://developers.empiredrop.com/` loads client-side and no official authenticated affiliate-wager OpenAPI contract was retrievable in the available tooling on October 30, 2026. **No official endpoint, auth scheme, request signing method or wager response field can be claimed as verified.** An empty official endpoint remains empty and the verified-contract safeguard remains false. This release is an improved, tested *adapter*, not proof of a working live provider API connection. Obtain the official endpoint and schema from the developer portal or EmpireDrop support, then configure and test before publishing standings.

### Validation

- Focused offline Python contract tests: 16 passed (synthetic responses only).
- Frontend EmpireDrop test: 1 passed (Node.js synthetic DOM).
- Python source compile: passed.
- All Jinja source parse checks: completed for templates.
- Full application suite: **not verified in this sandbox** because Flask/Werkzeug are not installed in the execution environment.
- Live EmpireDrop requests and actual DigitalOcean deployment: not performed.
