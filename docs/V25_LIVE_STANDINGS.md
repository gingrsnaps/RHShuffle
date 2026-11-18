# V25 live standings and movement

V25 separates **provider acquisition** from **browser synchronization**. Shuffle still contacts its provider on a 90-second healthy cadence; EmpireDrop uses a 90-second minimum and honors a longer provider cache TTL. The browser never calls either provider directly. Instead, an open public page conditionally checks `/public-standings` every five seconds for an already-verified local snapshot. The broader `/public-state` feed remains on its 15-second cadence.

## Placement movement

Each successful changed provider snapshot is compared only with the preceding successful snapshot. A changed row can carry an explicit movement event with an event ID, previous and current rank, `up`, `down`, or `new` kind, places moved, server change timestamp, and exact expiration timestamp. The default movement window is 45 seconds. Repeated polls, wager-only changes, page reloads, and provider failures do not restart that event.

The public browser uses the shared `static/rank-movement.js` renderer for both providers. Placement badges have dedicated layout space and show `NEW`, `↑N`, or `↓N`. A short entrance transition occurs only for a new event ID; the badge then stays static until its server expiration. Values that change without a rank move receive only a short value highlight.

## Ordering and recovery

Each provider publishes independent standings and movement sequences. Older responses from the same runtime are ignored. An entire provider snapshot is rendered in one JavaScript task, so rank swaps are not partially displayed. Visibility, focus, and back/forward-cache recovery immediately re-check the local standings feed and expire old movement badges.

## Admin diagnostics

Provider summaries expose the current standings sequence and latest movement count/sequence. The server retains the last 20 process-local placement events for authenticated diagnostics; these events are operational aids and reset when the process restarts. Provider failures retain the last verified public snapshot and do not create movement events.

## Timing contract

| Component | Timing |
| --- | ---: |
| Shuffle provider acquisition | 90 seconds |
| EmpireDrop provider acquisition | max(90 seconds, provider cache TTL) |
| Kick live status | 60 seconds |
| Lightweight public standings sync | 5 seconds |
| Full public-state sync | 15 seconds |
| Placement movement event | 45 seconds |
| Race countdown render | approximately 1 second, absolute server-synchronized time |
