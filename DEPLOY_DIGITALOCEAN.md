# Unified Admin and Provider Data Quality — November 10, 2026

The latest update adds matching Shuffle and EmpireDrop administration cards, a dedicated Activity & Logs tab, read-only record validation metrics, clean JSON/TXT logs, and a fix for EmpireDrop player search. No new dependencies or provider API changes were introduced. See `docs/ADMIN_UNIFORMITY_DATA_QUALITY_2026-11-10.md` for the full changes and limitations.

**Deployment:** use the repository root, blank custom Build Command, `python wager_backend.py` as Run Command, port 8080, `/healthz`, and one instance. Source ZIPs include existing private settings as requested; Git ignores private files. Back up live JSON state first.

> **CURRENT RELEASE (Nov 10, 2026):** EmpireDrop now has independent payouts, admin date controls, masked public usernames, a source-aware countdown, sanitized activity logs, and settings backup/restore. See [the new setup and limitations guide](docs/EMPIREDROP_QOL_WEEKLY_PAYOUTS_2026-11-10.md). Official races use their own EmpireDrop dates; custom/weekly windows use a **deprecated** endpoint that EmpireDrop may remove.

> **CURRENT RELEASE (Nov 10, 2026):** The authoritative EmpireDrop integration instructions are in [docs/EMPIREDROP_OPENAPI_FIX_2026-11-10.md](docs/EMPIREDROP_OPENAPI_FIX_2026-11-10.md). Previous generic API configuration, legacy `/race/affiliates/{publicKey}` discovery, and manually mapped rows are superseded. The official production origin is `https://api.empiredrop.com`, and both authentication headers are mandatory.

# DigitalOcean App Platform — build and deploy fix

This release is **flat-root**. After extracting this ZIP, `requirements.txt`,
`runtime.txt`, `Procfile`, and `wager_backend.py` are all at the top level.
The older full ZIP had a `redhunllef/` wrapper folder, which was easy to push
as a subfolder while keeping App Platform **Source Directory** set to `/`.

## Correct procedure: existing App Platform app

1. Download a **fresh private recovery export** from the currently running website
   if it is still available. Its data can be newer than the state bundled in this ZIP.
2. Extract this ZIP **on your computer**. You should immediately see
   `requirements.txt` and `wager_backend.py`, not another `redhunllef/` folder.
3. Put the **contents of the extracted folder**, not the folder itself and
   not the ZIP archive, in the top level of your **private GitHub repository**.
   DigitalOcean App Platform builds from GitHub/GitLab/Bitbucket or a container
   registry; uploading a ZIP alone is not an App Platform source deployment.
4. In DigitalOcean: Apps → your app → Settings → Components → web → Edit:
   - Source directory: `/` (root of that repository)
   - Build command: **BLANK** (remove existing pip-install text)
   - Run command: `python wager_backend.py`
   - HTTP port: `8080`
   - HTTP health check: `/healthz`
   - Instance count: `1`
   - Environment: **Python**; version from `runtime.txt` is `3.13.12`.
5. Trigger a redeploy **from the latest source commit**. See Deployments →
   active deployment → Build Logs, then Deploy Logs. Diagnose each phase
   separately, rather than assuming a long build is a source packaging issue.
6. On the deployed site, check `https://YOUR_DOMAIN/healthz` (HTTP 200 JSON),
   then `/readyz`. If Build succeeds but Deploy fails, inspect deploy logs for
   `BOOT stages` / `STARTUP` errors and confirm the health check port.

For a newly created app, choose Web Service → Python in the App Platform UI.
The bundled `app.yaml` is a *reference spec*: its `github.repo` entry is a
placeholder. Do **not** import the spec without substituting your real private
repository, and don't replace an existing app spec without checking its domains,
secrets and other settings.

## Why the earlier release could fail

* The old ZIP had an extra `redhunllef/` folder layer. App Platform only detects
  `requirements.txt` in the configured source directory.
* The old `BUILD_MANIFEST.json` required 190 files, including `private/` and
  `data/` that `.gitignore` excludes. Source could build but then fail startup
  with a misleading "Missing release file" error. This version validates
  only runnable source files, preserving optional state and private settings.
* The default Python runtime is a newer version if `runtime.txt` is not found;
  the root-level version pin prevents accidental buildpack changes.
* Adding an extra custom `pip install -r requirements.txt` duplicates the
  automatic Python buildpack dependency install. Leave it empty.

## Secrets and state are intentionally protected

The archive contains the original private configuration and keys **unchanged**, per
request. The ZIP is unencrypted and should be treated as a credential backup.
**Do not commit `private/`, `data/`, or `.env` to Git**, even in a private repo.
The `.gitignore` ensures normal `git add` operations omit those paths, so Git
builds **will not** contain them automatically. In DigitalOcean App Platform,
set the required production credentials as encrypted RUN_TIME environment
variables (especially `EMPIREDROP_PUBLIC_KEY` and `EMPIREDROP_PRIVATE_KEY`,
plus the existing Shuffle/Kick keys as applicable). If creating new accounts
without the saved state or admin seed, set a strong, unique `ADMIN_BOOTSTRAP_PASS`
and `SECRET_KEY` before starting the app. Do not rely on the code's legacy
bootstrap password. Set `APP_ENV=production`, `APP_STATE_KEY=redhunllef`,
`SESSION_COOKIE_SECURE=always`, `TRUST_APP_PLATFORM=1`, and `PORT=8080`.

**Do not assume redeploying from a ZIP preserves recent accounts or game state.**
Local JSON state in App Platform is ephemeral across container replacements.
Export/restore from the administrator recovery panel or use a supported external
persistence strategy before running production competitions. One instance
helps avoid concurrent, divergent local JSON copies but does not prevent resets.

## Useful checks

From the project root (no pip dependencies required):

```bash
python tools/deployment_diagnostics.py
python tools/deployment_diagnostics.py --archive /path/to/RedHunllef_DO_Full_Fixed.zip
```

Then install dependencies locally and verify startup:

```bash
python -m pip install -r requirements.txt
python wager_backend.py --check
python wager_backend.py
```

**Important distinction:** these three commands are for local verification.
DigitalOcean's Python buildpack installs dependencies automatically: do not
configure the local pip-install command as an App Platform Build Command.

If build logs show `Installing dependencies` for a long time, check network/
package download timing and build cache. If deploy logs show startup errors,
inspect the first `STARTUP` or `Missing dependency` message. If the app runs
but returns unhealthy, check the port and `/healthz` route.

The EmpireDrop race adapter is unchanged from the previous release. Its
external response mapping and live authentication are not verified by this
packaging/deployment change.


## November 10 admin / Shuffle recovery patch

See `docs/SHUFFLE_400_ADMIN_TIMEZONE_FIX_2026-11-10.md` for verified findings from
the operations report and actions for the live DigitalOcean server. The original
JSON state, accounts, historical race and private settings are preserved.

**Private repository only:** `shuffle_deploy_key.py` and
`empiredrop_deploy_keys.py` contain live server-only fallback credentials as
requested. Never publish this repository; encrypted environment variables
remain the safer long-term option.


### November 11 EmpireDrop 404 recovery

See `docs/EMPIREDROP_SLUG_RECOVERY_2026-11-11.md` for the documented recovery rules, admin steps and validation limits. No API or admin settings were silently changed in the bundled JSON snapshot.
