# RedHunllef Wager Race

A Flask website that displays a masked Top 15 weighted Shuffle wager leaderboard, fixed placement prizes, a race countdown, and cached Kick live status.


## Project structure

```text
.
├── wager_backend.py
├── settings.json
├── requirements.txt
├── Procfile
├── .env.example
├── admin_store.example.json
├── static/
│   ├── redlogo.ico
│   ├── redlogo.png
│   ├── script.js
│   └── style.css
├── templates/
│   ├── 404.html
│   ├── admin_login.html
│   ├── admin_panel.html
│   └── index.html
└── tests/
    └── test_core.py
```

## Setup

1. Install Python 3.10 or newer.
2. Install dependencies:

   ```bash
   pip install -r requirements.txt
   ```

3. `settings.json` already contains the credentials supplied for this project so the application can run without additional secret configuration. Environment variables still take priority and are safer for production.
4. The Kick client ID and client secret are used only by the Flask server to obtain an app access token; they are never sent to browser JavaScript. Because the credentials are now present in source text, rotate them before placing the project in a public repository.
5. To override the values locally with environment variables, set them before starting:

   ```powershell
   $env:SECRET_KEY = "replace-with-a-long-random-value"
   $env:SHUFFLE_API_KEY = "replace-with-your-key"
   $env:KICK_CLIENT_ID = "replace-with-your-client-id"
   $env:KICK_CLIENT_SECRET = "replace-with-your-client-secret"
   $env:ADMIN_BOOTSTRAP_USER = "gingrsnaps"
   $env:ADMIN_BOOTSTRAP_PASS = "replace-with-a-strong-password"
   $env:SESSION_COOKIE_SECURE = "0"
   python wager_backend.py
   ```

   On macOS/Linux, use `export NAME=value` instead.

6. Open `http://localhost:8080`. The admin page is `/admin`.

## Production

Use one Gunicorn worker because the application keeps its refresh cache and login limiter in memory:

```bash
gunicorn --workers 1 --threads 8 --timeout 120 --bind 0.0.0.0:$PORT wager_backend:app
```

`Procfile` contains the same command for platforms that support it.

Keep `SESSION_COOKIE_SECURE=1` behind HTTPS. Confirm the `PROXY_FIX_*` values match the number of trusted reverse proxies between visitors and Flask. An incorrect value can break IP bans and login rate limiting.

For DigitalOcean App Platform, use the included `Procfile` command or set the run command to:

```bash
gunicorn --workers 1 --threads 8 --timeout 120 --bind 0.0.0.0:$PORT wager_backend:app
```

For better security, add the secret values through **Settings → Environment Variables**, mark them encrypted, and then remove those secret values from `settings.json`. The included `settings.json` contains them only because the complete ready-to-run configuration was explicitly requested.

`admin_store.json` contains admin accounts, overrides, audit history, and saved leaderboard snapshots. Back it up and **do not overwrite it** when deploying this update. The package contains `admin_store.example.json` only; a fresh deployment creates the real store automatically after `ADMIN_BOOTSTRAP_USER` and `ADMIN_BOOTSTRAP_PASS` are set. Existing version-2 stores are migrated from Top 11 to Top 15 automatically.

To rotate the password of an existing bootstrap/superadmin account, set `RESET_BOOTSTRAP_PASSWORD_ON_START=1` for one deployment, verify the new login, and immediately return it to `0`. On an ephemeral hosting filesystem, point `ADMIN_STORE_PATH` to persistent storage or the file will reset after redeployment.

## Health checks

Use `/healthz` for the hosting platform. It is a process-liveness endpoint and returns HTTP 200 even when Shuffle or Kick is temporarily unavailable; the JSON body reports `status: "degraded"` in that situation. This prevents an external API problem from causing an endless deployment restart loop.

Use `/readyz` for a strict diagnostic check. It returns HTTP 503 until a current leaderboard has been loaded successfully.

Configuration files and `admin_store.json` are resolved relative to `wager_backend.py`, so the application works even when Python or Gunicorn is launched from a different working directory.

## Tests

```bash
python -m unittest discover -s tests
```
