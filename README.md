# RedHunllef V15

A single-process Flask application for the RedHunllef Shuffle Top 15, EmpireDrop Top 10 and RedPoints Games.

## Run locally

```bash
python -m pip install -r requirements.txt
python wager_backend.py
```

Open `http://localhost:8080`.

## DigitalOcean App Platform

- Source directory: `/`
- Build command: leave blank
- Run command: `python wager_backend.py`
- Port: `8080`
- Health check: `/healthz`
- Instances: `1`
- Set `RH_SPACES_ENABLE=0` unless Spaces is intentionally configured.

The root `requirements.txt`, `runtime.txt`, `wager_backend.py`, `app.yaml` and `BUILD_MANIFEST.json` must remain at the repository root.

## Important storage warning

App Platform local JSON is temporary across replacement or redeployment. Export a private recovery checkpoint before deploying. Optional DigitalOcean Spaces support remains available through `requirements-spaces.txt`.

## Private package warning

The private archives include production credentials and a saved-state snapshot. Keep the archive and repository private.
