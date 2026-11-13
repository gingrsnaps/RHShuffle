# V12 Validation Report

Build date: 2026-11-13 UTC

## Passed offline checks

- 27 root Python modules compiled and parsed.
- 24 Jinja templates parsed successfully.
- All browser JavaScript files passed `node --check`.
- Shared CSS files have balanced blocks.
- 77 selected offline Python tests passed, including:
  - canonical admin navigation contract;
  - visible literal admin-link and form-target registration;
  - removal of retired routes/templates/assets;
  - DigitalOcean root-layout checks;
  - Shuffle admin hotfix behavior;
  - EmpireDrop OpenAPI mapping, authentication headers, rate-limit preservation, slug recovery, Top 10, masking, ties, minor-unit conversion, and local payout logic;
  - public server-rendered EmpireDrop standings.
- `release_check.py --source-only --strict` passed.
- `tools/deployment_diagnostics.py` passed against the source tree.

## Not executed in the offline build environment

Flask, Werkzeug and Waitress are not installed in the artifact-building container, and network package installation is unavailable. Therefore these checks are included in the project but were not executed here:

- authenticated Flask test-client navigation;
- live POST/redirect/form behavior;
- complete application startup under Waitress;
- live Shuffle and EmpireDrop authentication;
- DigitalOcean deployment;
- Playwright/jsdom browser acceptance.

## Required production acceptance

After deployment, run:

```bash
python tools/live_smoke_v12.py --base-url https://YOUR-DOMAIN --username gingrsnaps
```

Then manually verify EmpireDrop draft save, reload, publication, and public prize rendering using a low-risk test configuration or the intended final payout schedule.
