# DigitalOcean App Platform — V13

Use a Python Web Service with:

- Source Directory: `/`
- Build Command: blank
- Run Command: `python wager_backend.py`
- HTTP Port: `8080`
- Health Check: `/healthz`
- Instances: `1`

`requirements.txt`, `runtime.txt`, `wager_backend.py`, `app.yaml`, and `BUILD_MANIFEST.json` must be visible at the source root. Extract the ZIP before committing it. Do not upload the ZIP as the repository source.

Before deploying, download the current private recovery checkpoint. The bundled JSON is a snapshot and App Platform local storage is replaceable.
