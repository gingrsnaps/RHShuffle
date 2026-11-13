# RedHunllef changes

## 2026.11.13-public-uniform-gaming-v14

### Public race presentation

- Uses the fixed title **RedHunllef Wager Race** for both Shuffle and EmpireDrop.
- Uses matching **Powered By** provider cards, typography, spacing, podiums and standings tables.
- Removes public provider-health, refresh-cadence and last-check noise while retaining full diagnostics in Admin.
- Keeps clean cached-data and unavailable-data messages without exposing API details.
- Preserves Shuffle Top 15, EmpireDrop Top 10, independent payouts, masking and provider schedules.

### Public Gaming community board

- Adds a privacy-safe public Live Now and weekly RedPoints leaderboard to `/gaming`.
- Refreshes through the existing five-second Gaming state request and pauses when the browser tab is hidden.
- Adds All Games and per-game filters, aggregate recent-player counts and subtle rank-movement indicators.
- Builds rankings only from settled server-side ledger statistics.
- Adds an explicit player opt-in for displaying a community name publicly; existing players remain private until they opt in.
- Excludes wallet IDs, IPs, balances, receipts, seeds, recovery data and administrator funding data from the public projection.
- Uses ETags and a server-side projection cache that invalidates on confirmed activity and visible status transitions.

### Administration and reliability

- Adds current-game, recent-action and public-visibility details to the private Gaming admin view.
- Preserves the V13 admin-page, payout-publishing, DigitalOcean optional-Spaces and official EmpireDrop race fixes.
- Keeps root deployment markers and the production `requirements.txt` unchanged.

## 2026.11.13-admin-pages-payouts-v13

### Fixed

- Imported the `field` and `player_rows` macros in the shared admin layout, eliminating the generic HTTP 500 page on Shuffle schedule, players, and Settings.
- Allowed EmpireDrop prize draft, publish, and save-failure events in the structured activity log.
- Wrapped operational logging so a logging problem can never turn a committed admin update into HTTP 500.
- Made optional EmpireDrop history metadata safe to render.
- Rendered canonical admin workspace routes directly, including EmpireDrop schedule, payouts, source health, and Recovery.
- Updated player search and edit links to the canonical Shuffle players route.
- Added original-exception logging with a request ID for future server errors.

### Configuration

- Bundled Shuffle window: November 10, 2026 6:00 PM EST through November 17, 2026 6:00 PM EST.
- Bundled EmpireDrop local display window: the same dates.
- Production dependencies are explicitly pinned in root `requirements.txt`.

### Preserved

- Shuffle Top 15 and weighted wager rules.
- EmpireDrop Top 10, selected race discovery, masking, and independent payouts.
- Games, RedPoints, accounts, credentials, history, and JSON state architecture.
