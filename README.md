# RedHunllef V25

Run with `python wager_backend.py`. V25 keeps the verified V24 provider cadence and adds a dedicated lightweight live-standings channel so an already-open page receives placement and wager changes without F5 or navigation. See `docs/V25_LIVE_STANDINGS.md`.

## Live standings

- Shuffle provider acquisition: 90-second healthy cadence.
- EmpireDrop acquisition: 90-second minimum; a longer provider `race.cache_duration` remains authoritative.
- Kick status: 60 seconds.
- Full public-state synchronization: 15 seconds.
- Lightweight standings synchronization: 5 seconds, conditional/ETag based, and local-server only.
- Placement movement: server-authored `NEW`, `↑N`, and `↓N` events with an exact 45-second expiration.

The browser updates all affected positions atomically from one provider snapshot. Wager-only changes update the value without creating a false rank arrow, repeated polls do not restart movement events, and provider failures retain the last verified standings.
