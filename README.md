# RedHunllef Wager Race

A single Flask application for a responsive Top 15 weighted Shuffle wager leaderboard with Kick live status and a nontechnical **Wager Race Control Center**.

## What the Wager Race admin can do

- Edit the Wager Race start and end with normal Eastern Time date pickers.
- Use quick schedule controls: **Start now**, **End in 7 days**, **End in 14 days**, and **Use previous duration**.
- Edit all 15 prize amounts and see the total prize pool update immediately.
- Restore the standard 15-place prize schedule with one confirmation.
- Edit public text, sponsor links, Kick channel, community link, campaign code, and refresh interval.
- See a clear Upcoming, Active, Ended, or Not Configured Wager Race banner.
- Test Shuffle and Kick connections with one click and receive plain-language next steps.
- See a setup checklist and last-update status.
- View raw and weighted wager totals together, copy usernames, review rank movement, and apply weighted-wager overrides.
- Export the full leaderboard as `redhunllef_wager_race_leaderboard.csv`.
- Download and restore safe JSON backups.
- Change the current admin password.
- Warn before leaving with unsaved Wager Race settings.
- Navigate the long admin page through desktop section links or a mobile **Jump to section** selector.
- The configured `gingrsnaps` Superadmin can add Admin users, confirm temporary passwords, reset passwords, and remove non-Superadmin accounts.
- Access IP bans, raw leaderboard data, and logs under **Advanced administration**.

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
   $env:SESSION_COOKIE_SECURE = "auto"
   python wager_backend.py
   ```

4. Open `http://localhost:8080`.
5. Open `http://localhost:8080/admin` for the Wager Race Control Center.

## Admin login

The configured bootstrap account is read from `ADMIN_BOOTSTRAP_USER` / `ADMIN_BOOTSTRAP_PASS`, with `settings.json` as the fallback. Login names are matched without case sensitivity.

Version 6 performs a one-time repair of the configured bootstrap account when upgrading an existing version-5 `admin_store.json`. This makes the stored password hash match the configured bootstrap password without deleting other admins, settings, overrides, or logs. Later password changes are preserved because the repair runs only during the version upgrade unless `RESET_BOOTSTRAP_PASSWORD_ON_START=1` is explicitly enabled.

The login page uses a short-lived signed form token that does not depend on an existing browser session. The session cookie is marked Secure for HTTPS requests and is allowed on local HTTP, preventing the login/CSRF loop caused by Secure-only cookies. Authenticated admin actions continue to use session-bound CSRF protection.

## DigitalOcean App Platform

Use the included `Procfile`, or set the run command to:

```bash
gunicorn --workers 1 --threads 8 --timeout 120 --bind 0.0.0.0:$PORT wager_backend:app
```

Keep one Gunicorn worker. The application uses an in-memory refresh cache, Kick token cache, and login limiter. Multiple workers would create separate copies of that state.

Use `/healthz` for the hosting health check. It remains HTTP 200 when an external API is temporarily unavailable. `/readyz` is the stricter diagnostic endpoint.

## Persistence

`admin_store.json` contains:

- Admin accounts and password hashes
- Wager Race settings saved through the admin panel
- Weighted-wager overrides
- Audit history
- Saved leaderboard snapshots

Do not overwrite an existing `admin_store.json` during deployment. Existing stores are migrated automatically, and obsolete payout-status data is removed because payout tracking is no longer part of the project.

On hosting platforms with an ephemeral filesystem, mount persistent storage and point `ADMIN_STORE_PATH` to it.

The safe backup downloaded through the admin panel intentionally excludes admin accounts, password hashes, the Flask secret, IP bans, access logs, and audit logs. Restoring a backup cannot replace the current admin password.

## Credentials

For production, store these as encrypted environment variables instead of committing them to `settings.json`:

```text
SECRET_KEY
SHUFFLE_API_KEY
KICK_CLIENT_ID
KICK_CLIENT_SECRET
SUPERADMIN_USER
ADMIN_BOOTSTRAP_USER
ADMIN_BOOTSTRAP_PASS
SESSION_COOKIE_SECURE=auto
REPAIR_BOOTSTRAP_LOGIN_ON_UPGRADE=1
```

Environment variables override `settings.json`. Rotate any credential that has been shared in source files or chat before publishing the project.

## Tests

```bash
python -m unittest discover -s tests
```
