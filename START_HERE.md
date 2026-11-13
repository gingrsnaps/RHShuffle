# Start here — RedHunllef V14

Release: `2026.11.13-public-uniform-gaming-v14`

## DigitalOcean App Platform

- Source Directory: `/`
- Build Command: leave blank
- Run Command: `python wager_backend.py`
- HTTP Port: `8080`
- Health Check: `/healthz`
- Instances: `1`
- `RH_SPACES_ENABLE=0` unless DigitalOcean Spaces is intentionally configured

The source root must contain `requirements.txt`, `runtime.txt`, `wager_backend.py`, `app.yaml`, and `BUILD_MANIFEST.json`.

## Before deployment

1. Export the current private recovery file from the running site.
2. Extract this package and commit the extracted contents, not the ZIP itself.
3. Keep the repository private because the private build includes credentials and a state snapshot.
4. Force Rebuild and Deploy in DigitalOcean.
5. Verify `/healthz` and `/readyz`.
6. Verify Shuffle Top 15 and EmpireDrop Top 10 both populate.
7. Verify the public Gaming dashboard updates after an opted-in player completes a confirmed action.
8. Verify no private Gaming fields appear in `/gaming/api/public-leaderboard`.
9. Sign in and verify Leaderboards, Games & RedPoints, Settings and Activity.

## Bundled race window

Shuffle and the local EmpireDrop display schedule are set to November 10, 2026 at 6:00 PM Eastern through November 17, 2026 at 6:00 PM Eastern. EmpireDrop's official API race window is controlled by the selected provider race slug.

See `docs/V14_PUBLIC_RACES_AND_GAMING.md`.
