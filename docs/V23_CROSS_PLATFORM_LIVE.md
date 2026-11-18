# RedHunllef V23 — cross-platform live reliability

V23 builds on the V22 atomic Shuffle Top 15 without changing the JSON-only deployment model or increasing external provider request cadence.

## Placement movement

- Shuffle and EmpireDrop movement is calculated from verified server snapshots, never from a browser's local previous render.
- `movement_at` is an authoritative server event timestamp.
- `↑`, `↓`, and `NEW` remain visible for 30 seconds from that event, not 30 seconds from page load or polling.
- Repeated confirmations of the same standings preserve the original movement timestamp, so polling cannot restart the indicator.

## Public-state synchronization

- Browsers check the inexpensive local `/public-state` endpoint every 15 seconds.
- Shuffle's healthy external provider cadence remains 60 seconds. EmpireDrop keeps its provider/cache/backoff cadence.
- Requests use ETags. A 304 still carries fresh server time.
- Every content change receives a process-local monotonic `snapshot_sequence` plus `runtime_id`; a browser ignores an older sequence from the same runtime.
- Strong ETags represent the complete non-clock public payload.

## Countdown reliability

- Countdown values are recalculated from `start_time`/`end_time` and synchronized fractional server time on every tick; they are never decremented counters.
- Timer callbacks align to server-second boundaries and recover immediately on visibility, focus, and back-forward-cache restoration.
- Desktop timer CSS no longer uses `text-overflow: ellipsis`; valid seconds cannot become `...`.
- Tabular numerals and a bounded desktop font size keep the whole timer stable across Chrome, Firefox, Edge, and Safari-class layout engines.

## Data safety

- Shuffle still validates and atomically publishes ranks 1–15 as one snapshot.
- EmpireDrop retains verified last-good standings on provider errors and now versions the visible standings separately.
- Failed provider requests do not clear verified public data.
- Provider requests remain server-side; the 15-second public poll never calls Shuffle or EmpireDrop directly.
