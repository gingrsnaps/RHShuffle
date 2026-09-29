# Start RedHunllef

Release **2026.09.28-community-polish** — complete configured package.

Install dependencies once, then run the sole launcher:

```bash
python -m pip install -r requirements.txt
python wager_backend.py
```

Keep all supporting Python files, templates and static files together.
No database service, SQL setup, account-creation command or extra worker is needed.
The app creates `data/state.json` and imports an existing previous local save.

- Website: `/`
- Community boss: `/play`
- Admin: `/admin`
- Original supplied Superadmin: **gingrsnaps / enok2121**. Existing accounts/passwords win.

When updating, preserve current `data/`, `private/`, settings and environment
configuration. Copy the application code from this ZIP into matching paths.
Do not replace newer private seeds with the bundled originals.

DigitalOcean App Platform: use the same build/run commands, port **8080**,
health check **/healthz**, and **one instance**. Set `APP_ENV=production`,
`TRUST_APP_PLATFORM=1`, and `SESSION_COOKIE_SECURE=always`.
Remove stale database environment bindings. No database component is needed.

App Platform loses local files on redeployment/container replacement. Before
redeploying, download **Settings → Private recovery file** as the Superadmin and
save it as `private/recovery.seed.json` in your private repository. New changes
after the export can be lost. No external backup integration has been added.

Hits are **unlimited per day and week**, with a **30-second cooldown**. The eight
achievements and their existing display remain unchanged. Boss screens check every
5 seconds; Shuffle/Kick check automatically every 60 seconds.

This update adds player recovery codes, admin-approved households, cosmetic Red
rally, next-raid presets, edit previews, boss admin history and clearer live status.
Original credentials, logos, live feeds, private Code Red list and admin-only boss
uploads/name/HP/damage controls remain intact.

Read `README.md` for migration/deployment details and `FULL_CODE_BLOCKS.md` for the
complete source in individual code blocks.
