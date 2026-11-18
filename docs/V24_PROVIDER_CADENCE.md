# RedHunllef V24 — provider cadence and placement verification

Release: `2026.11.17-provider-cadence-v24`

V24 keeps the V23 JSON-only/single-launch architecture and hardens the live race timing contract.

- Shuffle healthy provider cadence: **90 seconds**.
- Kick cadence remains **60 seconds**.
- EmpireDrop target/minimum cadence: **90 seconds**, but the worker never checks faster than `race.cache_duration`.
- Public `/public-state` sync remains **15 seconds** and does not call either wager provider.
- Placement movement/NEW indicators remain visible for **45 seconds from the server event**, not 45 seconds from when a browser notices them.
- Backend snapshots include `movement_expires_at`; both providers use one shared browser renderer.
- Browser focus, bfcache restore and visibility recovery recalculate timers immediately.
- Failed provider calls retain the previous verified standings and never become the movement baseline.
- Shuffle scheduling stays anchored to the intended 90-second grid so slow requests do not accumulate drift.
- Public status lines distinguish last confirmed data, next provider check and browser sync cadence.

EmpireDrop cache example: if the provider advertises 300 seconds, the effective provider cadence remains 300 seconds rather than issuing redundant 90-second requests.
