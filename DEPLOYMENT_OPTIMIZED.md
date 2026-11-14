# Optimized DigitalOcean deployment — V18

Use the FastDeploy archive for DigitalOcean App Platform. Its source root
contains `requirements.txt`, `runtime.txt`, `wager_backend.py`, `app.yaml`, and
`BUILD_MANIFEST.json`.

Settings:

- Source Directory: `/`
- Custom Build Command: blank
- Run Command: `python wager_backend.py`
- HTTP Port: `8080`
- Health Check: `/healthz`
- `RH_SPACES_ENABLE=0` unless Spaces is intentionally configured

Use **Force Rebuild and Deploy** so the V18 release and corrected payout
JavaScript replace cached V17 assets.
