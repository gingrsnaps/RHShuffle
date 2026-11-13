# Start here — RedHunllef V13

Release: `2026.11.13-admin-pages-payouts-v13`

## DigitalOcean App Platform

- Source Directory: `/`
- Build Command: leave blank
- Run Command: `python wager_backend.py`
- HTTP Port: `8080`
- Health Check: `/healthz`
- Instances: `1`

The source root must contain `requirements.txt`, `runtime.txt`, `wager_backend.py`, `app.yaml`, and `BUILD_MANIFEST.json`.

## Before deployment

1. Export the current private recovery file from the running site.
2. Extract this package and commit the extracted contents, not the ZIP itself.
3. Keep the repository private because the private build includes credentials and a state snapshot.
4. Deploy and verify `/healthz` and `/readyz`.
5. Sign in and open every primary admin workspace.
6. Save an EmpireDrop payout draft, reload it, then publish it and verify the public Top 10.

## Bundled race window

Shuffle and the local EmpireDrop display schedule are set to November 10, 2026 at 6:00 PM Eastern through November 17, 2026 at 6:00 PM Eastern. EmpireDrop's official provider race must be the corresponding race selected by its slug/API discovery.

See `docs/ADMIN_RELIABILITY_V13.md` for the repair details.
