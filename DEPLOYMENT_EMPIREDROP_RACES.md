**DigitalOcean deployment correction (2026-11-02):** This new full ZIP has
no nested `redhunllef/` directory. Extract the archive and upload its contents
to the Git repository root; Source Directory is `/`. See `DEPLOY_DIGITALOCEAN.md`.

# Fast deployment — EmpireDrop Races (2026-11-02)

Use `RedHunllef_EmpireDrop_Races_FastDeploy_Private_2026-11-02.zip` for
DigitalOcean App Platform. It contains all needed Python code, templates,
static assets, private configuration including the exact keys provided, admin
seed and bundled JSON state. The complete project ZIP also includes tests,
reference screenshots, historical artifacts and full documentation.

Build command: **empty** (remove the prior `pip install -r requirements.txt`).
Run command: `python wager_backend.py`. Port: `8080`. Health: `/healthz`.
Python runtime: 3.13.12. One instance. No database service.

**Data warning:** Back up your live state first. The bundled snapshot might be
older than your website; DigitalOcean App Platform files are ephemeral.

**Private keys:** Your supplied production keys are in `private/settings.json`.
The ZIP files are not encrypted. Existing environment variables on DigitalOcean
override these file values. `.gitignore` intentionally excludes private files
from ordinary Git commits. For secure Git-based deploys, configure encrypted
`EMPIREDROP_PUBLIC_KEY` / `EMPIREDROP_PRIVATE_KEY` variables in App Platform.

After deploying, go to Admin > EmpireDrop, discover races, inspect race field
names, confirm amount units and mapping, test and refresh. The portal-supplied
routes are implemented but a live successful API response was not verified.

Detailed procedure: `docs/EMPIREDROP_RACES_INTEGRATION_2026-11-02.md` in the
full ZIP. The production ZIP also includes this deployment summary.
