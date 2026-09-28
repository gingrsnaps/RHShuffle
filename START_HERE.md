# RedHunllef — start here

Release **2026.09.28-boss-controls**. No PostgreSQL service or DATABASE_URL is needed.
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
60 seconds. Expand **Live connections** for actual provider outcomes.

The red theme, original logos, refresh/publication fixes, UTF-8 startup handling,
and private 100-user Code Red list remain. Reload with Ctrl+F5 after deploying;
the release label must show **2026.09.28-boss-controls**.

Open **/play** or click **Join the boss fight** on the homepage. The public page
is just the game, with no tutorial or long explanation panels.
The shared boss starts at 2,400,000 HP. One attack per minute, 40 per raid day,
with a target of roughly 4–8 days for 100 active participants. Game views update
every 5 seconds. Wager/Kick views still update every 60 seconds.

Host controls live at **/admin?tab=boss**. Use **Boss avatar** to upload a PNG/JPG/JPEG/WebP,
or **Current raid health** to change maximum HP while keeping saved damage.
Only signed-in admins can save these changes. Use **Boss name & damage** to
rename the boss or adjust future hit damage. The Superadmin still controls admin
accounts and private recovery downloads. Reinstall requirements for Pillow.
 Save a **private recovery checkpoint**
regularly during the raid and before redeploying. It includes health, profiles,
attack receipts, cooldowns, health edits and the uploaded avatar. App Platform can lose changes after the last
checkpoint if it replaces the container. No extra launch command is required.

The Admin footer link is removed. Bookmark **/admin** for your dashboard.

Boss health never regenerates. Every confirmed hit remains in the saved raid
across refreshes, daily resets and process restarts with the same data. Only
an explicit maximum-HP edit or a confirmed new raid may raise health. The initial percentage now reflects
saved HP immediately. Save recovery before App Platform redeploys: losing the
local data file is separate from in-game health regeneration.

Earlier improvements retained here include mobile attack controls, milestones, the
full victory contributor list, a live homepage boss invitation, compact admin
connections, side-by-side change review, and recovery checkpoint tracking.
See `docs/COMMUNITY_UPDATE.md` for all changes. No new process is needed.
