# DigitalOcean App Platform — V14

Use a Python Web Service with:

- Source Directory: `/`
- Build Command: blank
- Run Command: `python wager_backend.py`
- HTTP Port: `8080`
- Health Check: `/healthz`
- Instances: `1`
- `RH_SPACES_ENABLE=0` unless Spaces is intentionally configured

`requirements.txt`, `runtime.txt`, `wager_backend.py`, `app.yaml`, and `BUILD_MANIFEST.json` must be visible at the source root. Extract the ZIP before committing it; do not commit the ZIP as the repository source.

Before deploying, download the current private recovery checkpoint. The bundled JSON is a snapshot and App Platform local storage is replaceable. After deployment, verify both providers, EmpireDrop payouts, the Gaming public board, and all administrator workspaces.

## V16 deployment note

Keep `RH_SPACES_ENABLE=0` unless a Spaces bucket and credentials are intentionally
configured. Use Force Rebuild and Deploy after replacing the repository root.
The V16 Source Health screen exposes only sanitized request metadata; credentials
and provider payloads never reach the browser.
