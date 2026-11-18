# Start here — V25

1. Keep this repository and generated private ZIP private.
2. Install dependencies with `python -m pip install -r requirements.txt`.
3. Deploy with an empty custom build command and `python wager_backend.py`.
4. Use one App Platform web instance and `RH_SPACES_ENABLE=0` unless Spaces is intentionally configured.
5. Verify Shuffle shows Nov 17–24, 2026 at 6 PM Eastern.
6. Verify EmpireDrop website schedule shows Oct 27–Nov 28, 2026 at 6 PM Eastern.
7. Leave the public page open through a provider refresh: placements, wager values, live-sync age, and movement badges should update without reloading the page.

## V25 validation

Shuffle provider acquisition remains 90 seconds; EmpireDrop uses a 90-second minimum while respecting a longer official cache TTL. The browser checks the lightweight `/public-standings` snapshot every 5 seconds and the broader `/public-state` every 15 seconds. Placement events are server-timed for 45 seconds and are not restarted by polls, reloads, tab changes, or wager-only changes.
