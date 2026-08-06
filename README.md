# RedHunllef Wager Race

A single Flask application for a responsive Top 15 weighted Shuffle wager leaderboard with Kick live status and a simple, nontechnical administration panel.

## What the admin panel can do

- Edit the race start and end with normal Eastern Time date pickers.
- Edit all 15 prize amounts, public text, sponsor links, Kick channel, community link, and refresh interval.
- Test the Shuffle and Kick connections with one click.
- See plain-language connection cards and a setup checklist.
- Copy usernames, review rank movement, apply weighted-wager overrides, and mark payouts as Pending, Verified, or Paid.
- Download a payout CSV.
- Download and restore safe JSON backups.
- Change the current admin password.
- Access IP bans, additional admin accounts, raw leaderboard data, and logs under Advanced administration.

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
│   ├── admin.js
│   └── style.css
├── templates/
│   ├── 404.html
│   ├── admin_login.html
│   ├── admin_panel.html
│   └── index.html
└── tests/
    └── test_core.py
```

## Local setup

1. Install Python 3.10 or newer.
2. Install dependencies:

   ```bash
   pip install -r requirements.txt
   ```

3. For local HTTP testing in PowerShell:

   ```powershell
   $env:SESSION_COOKIE_SECURE = "0"
   python wager_backend.py
   ```

4. Open `http://localhost:8080`.
5. Open `http://localhost:8080/admin` for administration.

## DigitalOcean App Platform

Use the included `Procfile`, or set the run command to:

```bash
gunicorn --workers 1 --threads 8 --timeout 120 --bind 0.0.0.0:$PORT wager_backend:app
```

Keep one Gunicorn worker. The application uses an in-memory refresh cache, Kick token cache, and login limiter. Multiple workers would create separate copies of that state.

The hosting health-check path should be `/healthz`. It remains HTTP 200 when an external API is temporarily unavailable. `/readyz` is the stricter diagnostic endpoint.

## Persistence

`admin_store.json` contains:

- Admin accounts and password hashes
- Event settings saved through the admin panel
- Weighted-wager overrides
- Payout statuses
- Audit history
- Saved leaderboard snapshots

Do not overwrite an existing `admin_store.json` during deployment. On hosting platforms with an ephemeral filesystem, mount persistent storage and point `ADMIN_STORE_PATH` to it.

The safe backup downloaded through the admin panel intentionally excludes admin accounts, password hashes, the Flask secret, IP bans, access logs, and audit logs. Restoring a backup cannot replace the current admin password.

## Credentials

For a production deployment, store these as encrypted environment variables instead of committing them to `settings.json`:

```text
SECRET_KEY
SHUFFLE_API_KEY
KICK_CLIENT_ID
KICK_CLIENT_SECRET
ADMIN_BOOTSTRAP_USER
ADMIN_BOOTSTRAP_PASS
SESSION_COOKIE_SECURE=1
```

Environment variables override `settings.json`. Rotate any credential that has been shared in source files or chat before publishing the project.

## Tests

```bash
python -m unittest discover -s tests
```
