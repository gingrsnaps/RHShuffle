# RedHunllef changes

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
