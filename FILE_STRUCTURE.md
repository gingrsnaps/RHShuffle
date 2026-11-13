# RedHunllef V14 file structure

## Deployment root

- `wager_backend.py` — Flask application, public/admin routes and Waitress entry point
- `requirements.txt` — production dependencies installed by DigitalOcean
- `runtime.txt` — Python runtime pin
- `app.yaml` / `Procfile` — deployment markers
- `config.py`, `runtime.py`, `storage.py` — configuration, workers and atomic JSON persistence
- `empiredrop*.py` — official EmpireDrop partner-race API and projections
- `gaming.py`, game modules, `fairness.py` — RedPoints wallets, public community activity and provably fair games
- `admin_navigation.py` — canonical administrator destinations
- `operations_log.py`, `telemetry.py` — sanitized operations and health views
- `release_check.py` — source, template, asset and optional-dependency validation

## Web assets

- `templates/index.html` — uniform Shuffle and EmpireDrop public race view
- `templates/gaming.html` — Gaming dashboard, public community board and games
- `templates/admin*.html` — protected Control Center workspaces
- `static/v14-modern.css` — final public design layer loaded after legacy styles
- `static/empiredrop.js` — uniform provider switching and EmpireDrop Top 10 rendering
- `static/gaming.js` — wallet/gameplay plus five-second community updates
- remaining `static/` files — shared, game-specific and admin assets

## Private runtime data

- `private/settings.json`
- `private/admin_store.seed.json`
- `data/state.json`

## Development-only content in the full archive

- `tests/`
- `tools/`
- `docs/`
- `FULL_CODE_BLOCKS.md`

The FastDeploy archive excludes development-only content but retains every executable file, template, static asset, private configuration file and root deployment marker.
