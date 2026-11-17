# RedHunllef V22 — Shuffle Top 15 refresh reliability

V22 keeps the V21 race windows and V20 mobile presentation while tightening the live Shuffle leaderboard path.

## Public Top 15

- Every successful Shuffle result is converted into one validated Top 15 snapshot.
- Ranks must be sequential, player identities must be unique internally, and wager amounts must be non-negative.
- The public projection contains 15 explicit slots. Missing qualifying players become `Open position` slots rather than leaving stale DOM content behind.
- A `shuffle_revision` changes only when the actual Top 15 changes.
- Public rendering loops explicitly from rank 1 through 15 and updates podium and lower placements in one pass.
- Rank movement is calculated from full internal provider identities before public masking and is displayed briefly as `↑`, `↓`, or `NEW`.

## Refresh cadence

- Healthy Shuffle checks remain anchored to the 60-second `INTERVAL`.
- A successful response resets failure backoff immediately.
- Repeated failures retain the last verified Top 15 and use the existing 60/120/240/480-second backoff.
- Public `/public-state` checks remain on an anchored 60-second cadence and use conditional ETags.
- Manual refresh requests join an already-running check instead of queuing an immediate duplicate request.

## Admin diagnostics

Admin now distinguishes:

- last provider attempt,
- last successful response,
- last leaderboard change,
- next provider check,
- qualifying players,
- source records received/accepted/excluded,
- campaign-unverified rows,
- number of public Top 15 positions filled,
- recent provider reliability.

The next-check countdown is driven by the backend worker schedule rather than a browser-only 60-second timer.

## History

A completed Shuffle week freezes after its first verified provider result. Automatic background checks no longer repeatedly query that completed week. An administrator can still explicitly request a history recheck.

## Data safety

Provider errors never partially replace a public Top 15. JSON state writes remain atomic. Old race responses retain the settings-revision guard, so they cannot overwrite a newer race window.
