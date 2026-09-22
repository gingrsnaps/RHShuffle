# RedHunllef — start here

Release **2026.09.22-local**. No PostgreSQL service or DATABASE_URL is needed.
Extract the complete folder. Install dependencies once:

```bash
python -m pip install -r requirements.txt
```

Run only:

```bash
python wager_backend.py
```

On DigitalOcean App Platform use those same build/run commands, port **8080**,
health check **/healthz**, and **one instance**. Runtime environment:

```text
APP_ENV=production
STORAGE_MODE=local
TRUST_APP_PLATFORM=1
SESSION_COOKIE_SECURE=always
```

Remove an obsolete DATABASE_URL binding if you added one. Local mode ignores
that variable; DigitalOcean may still try to resolve bindings before startup.
No new database component is required. Keep existing data-bearing resources.

The original supplied login is **gingrsnaps / enok2121**. Original Shuffle/Kick
credentials and the account seed are included. Existing local state or a newer
recovery seed retains its accounts, passwords, and dates.

**App Platform replaces local files during redeploys/container replacements.**
After important edits, use **Settings → Private recovery file**. Add the
resulting file to your private repository as `private/recovery.seed.json`
before redeploying to restore that checkpoint automatically. New edits after
your latest saved checkpoint can still be lost. This is manual recovery,
not automatic persistent cloud storage. Read README.md for the full process.

For a persistent host, preserve the existing `data/` folder when replacing code.
The application automatically creates its local file and imports the seed;
there is no account-creation script or separate worker to run.

The original seed saves August 4–11, 2026, 6 PM Eastern. To publish your desired
schedule: **Race → Save race settings → Confirm and publish race** in the bottom
bar. Verify **Published window**. Both providers update automatically every
60 seconds. Read **Live update progress** for actual provider outcomes.

The red theme, original logos, refresh/publication fixes, UTF-8 startup handling,
and private 100-user Code Red list remain. Reload with Ctrl+F5 after deploying;
the release label must show **2026.09.22-local**.
