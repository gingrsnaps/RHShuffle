# Optimized deployment — RedHunllef / EmpireDrop

Release: **2026-10-30 deployment optimization**. The existing application and
previously bundled private configuration are preserved. There are **two ZIPs**:

- **Complete archive**: all original private settings, seeded administrator accounts,
  JSON state, recovery snapshots, historical SQLite artifacts, documentation,
  full code reference, tests, source code and assets. KEEP PRIVATE.
- **Production archive**: the same runnable Python application, templates, static
  assets, `private/settings.json`, `private/admin_store.seed.json`, and `data/state.json`.
  The production archive excludes tests, screenshots, reference markdown, stale SQLite
  files, and old recovery snapshots to reduce deployment payload. KEEP PRIVATE.

## DigitalOcean settings

Use a **Python Web Service**, one instance, and the existing Python 3.13.12
pin in `runtime.txt`. Extract the production ZIP and push its `redhunllef/`
contents to the **root** of a **private GitHub repository**. App Platform should
use source directory `/` and the following values:

| Setting | Value |
|---|---|
| Build command | **Leave empty** (remove any old custom command in the DigitalOcean console) |
| Run command | `python wager_backend.py` |
| Port | `8080` |
| HTTP health check | `/healthz` |
| Instance count | `1` |
| App environment | `APP_ENV=production` |
| Cookies | `SESSION_COOKIE_SECURE=always` |
| Proxy | `TRUST_APP_PLATFORM=1` only behind App Platform ingress |

The buildpack automatically installs pinned dependencies from `requirements.txt`.
A redundant custom `pip install -r requirements.txt` runs **after** the buildpack
build and can double-install dependencies. Removing it avoids that extra step; it
does not eliminate the normal dependency installation required for each new build.
If your DigitalOcean app already has an old Build Command set in the dashboard,
**delete it there**. Editing the local `app.yaml` does not update existing apps.
The `github.repo` entry in `app.yaml` is a placeholder until you set it to your
own private repository. Do not apply `app.yaml` to an existing app without
checking existing routing/domain/secret settings: App Platform specs are complete
configuration replacements.

## Secrets and Git behavior

The ZIP files include private credentials, at your request. Neither ZIP is
password protected. A `.gitignore` protects `private/` and `data/` against
accidental `git add`; this means **plain Git upload does not deploy the embedded
keys or state**. Deploy keys via DigitalOcean encrypted runtime environment
variables (`SHUFFLE_API_KEY`, `KICK_CLIENT_ID`, `KICK_CLIENT_SECRET`,
`EMPIREDROP_PUBLIC_KEY`, `EMPIREDROP_PRIVATE_KEY`, etc.) and keep the unredacted
private files offline. Review `private/settings.json` locally to map other values.
The application accepts its original bundled private files when they are present
on the server, such as an appropriately secured private deployment; never post
those files in a public repository. Avoid committing player data or admin seeds.

**State preservation:** Download your freshest admin private recovery backup before
deploying. The bundled `data/state.json` is a snapshot from the original ZIP and
is NOT guaranteed to match the live server. App Platform local storage is
**ephemeral** and a deployment can reset current accounts, boss HP, game receipts
and progress. A ZIP preserving old state does not preserve newer live state.
Without an external persistent store (or careful recovery export/import), fully
lossless redeploys are impossible with the JSON-only architecture. Do not delete
or overwrite a current recovery backup before confirming the replacement.

## Health and troubleshooting

`/healthz` checks that the web process is answering (fast; no provider calls).
`/readyz` checks the local JSON store and returns HTTP 503 on failure. It is
not a proxy for Shuffle, Kick, or EmpireDrop availability. Startup logs now
report durations for **preflight**, **application construction**, **listener**
and **ready**. The Admin health report is still available after login.

Run the packaged check after installing dependencies:

```bash
python wager_backend.py --check
```

Check the local production package or probe a running deployment with standard
Python (no extra dependency):

```bash
python tools/deployment_diagnostics.py
python tools/deployment_diagnostics.py --url https://YOUR-SITE.example
```

If deploy remains slow, check the **Build logs** for buildpack dependency
installation versus a separate `build_command` phase. Check **Deploy logs** for
`BOOT stages` and `BOOT ready` to tell slow startup from slow builds or health
probes. Repeated platform build times can include queue, image and rollout time,
not just ZIP size. Compare the deploy timestamps before concluding that this
optimization improved overall elapsed time.

## EmpireDrop status

No live EmpireDrop endpoint, authentication contract, or active referral statistics
have been independently verified; the new adapter still requires the documented
provider contract in Admin → EmpireDrop. Deployment optimization does not claim
that the unavailable provider integration has been fixed. See the complete
archive's `docs/EMPIREDROP_DEVELOPER_PORTAL_SETUP.md`.
