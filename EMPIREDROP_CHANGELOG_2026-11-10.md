# EmpireDrop OpenAPI 2.0.1 corrective release — Nov 10, 2026

- Correct host (`api.empiredrop.com`), mandatory dual-header auth on **both** current endpoints.
- Replace retired public-key discovery with current running-races listing.
- Race details use direct slug; no extra timestamp query parameters.
- Normalize ranking/user/amount schema and ties from OpenAPI; distinguish wagers, deposits, tickets.
- Read provider race dates, `is_active`, `ranks_limit`, and cache TTL; back off on 429.
- Preserve historical data and previously validated standings through network failures and closed races.
- Fix missing `race_configuration` and `race_history` template context.
- Preserve user-provided production keys in private config and a Git-trackable server-only fallback.
- Keep existing game, Shuffle, admin, history and site code intact.
- Add fixture-driven offline regression tests and the full provided API spec.

See `docs/EMPIREDROP_OPENAPI_FIX_2026-11-10.md` for rollout and security notes.
