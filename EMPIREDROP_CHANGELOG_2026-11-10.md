# EmpireDrop integration changelog

## V18 — November 14, 2026

- Fixed the browser omitting `save_mode=publish` after payout buttons were disabled.
- Added `save_mode_intent` with a server-validated no-JavaScript fallback.
- Preserved payout idempotency, dedicated revisions, atomic writes, read-back checks, and public projection verification.
- Bundled the confirmed USD Top 10 schedule totaling `$2,000.00`.

## Retained behavior

- Official `/api/v1/affiliate-partner/races` discovery
- Official `/api/v1/affiliate-partner/races/{slug}` details
- `X-Public-Key` and `X-Private-Key` headers
- Top 10 rankings and provider rank preservation
- Public username normalization
- Independent local prize configuration
