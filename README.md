# RedHunllef V24

Run with `python wager_backend.py`. This release preserves the current race schedules and V23 cross-platform reliability while upgrading provider cadence, placement movement timing, and live status accuracy. See `docs/V24_PROVIDER_CADENCE.md`.

## V24 provider cadence and movement verification

V24 changes Shuffle to a 90-second provider cadence, gives EmpireDrop a 90-second minimum while respecting provider cache TTL, and extends shared server-timed placement indicators to 45 seconds. Public state synchronization remains 15 seconds and Kick remains 60 seconds. See `docs/V24_PROVIDER_CADENCE.md`.
