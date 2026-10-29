# EmpireDrop independent release — test evidence and limits

- Offline EmpireDrop-specific backend tests: 13 passed (Python 3.13, synthetic requests) on 2026-10-29.
- Public provider-switching frontend test: 1 passed (Node.js; synthetic DOM).
- Python source compile: passed for modified files; all project Python modules are checked before packaging.
- Jinja templates: all templates parsed successfully with Jinja2.
- JavaScript syntax: new or modified JS files pass `node --check`.
- Package: SHA-256 manifest hashes and ZIP CRC checked during final packaging.
- **Not performed:** Live EmpireDrop API call (official contract unknown); full Flask integration regressions (Flask and Waitress unavailable in execution environment); DigitalOcean deployment or live user verification.
- Tests do not prove an actual provider API response exists, that the keys have required scopes, or that any wager is attributable to referral `red`.

All numeric fixtures are artificial. Failure cases reject 401, 403, 429, redirects, invalid data and unexpected pagination without publishing partial standings. The source tree includes `tests/test_empiredrop.py` for full Flask integration once dependencies are installed.
