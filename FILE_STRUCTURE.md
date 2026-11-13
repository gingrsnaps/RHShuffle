# RedHunllef V13 file structure

## Deployment root

- `wager_backend.py` — Flask application, routes, admin actions and Waitress entry point
- `requirements.txt` — production dependencies
- `runtime.txt` — Python runtime pin
- `app.yaml` / `Procfile` — deployment markers
- `config.py`, `runtime.py`, `storage.py` — configuration, workers and atomic JSON persistence
- `empiredrop*.py` — EmpireDrop API and public/admin projections
- `gaming.py`, game modules, `fairness.py` — RedPoints and provably fair games
- `admin_navigation.py` — canonical administrator destinations
- `operations_log.py`, `telemetry.py` — sanitized operations and health views

## Web assets

- `templates/` — public and protected Jinja templates
- `static/` — JavaScript, CSS and images

## Private runtime data

- `private/settings.json`
- `private/admin_store.seed.json`
- `data/state.json`

## Development-only content in the full archive

- `tests/`
- `tools/`
- `docs/`
- `FULL_CODE_BLOCKS.md`

Community Boss runtime files remain removed. Games and RedPoints use their own player identity and recovery system.
