# DigitalOcean App Platform — V21

- Source Directory: `/`
- Build Command: leave blank
- Run Command: `python wager_backend.py`
- HTTP Port: `8080`
- Health Check: `/healthz`
- Instances: `1`
- `RH_SPACES_ENABLE=0` unless Spaces is configured intentionally.

The packaged first-run state contains the V21 requested race windows. Runtime schedule edits are written atomically and read back before success is reported. App Platform local files are still ephemeral across container replacement; export recovery state before redeploying if Spaces is not enabled.
