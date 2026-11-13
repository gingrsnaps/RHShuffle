# V12 Validation Matrix

| Area | Validation |
|---|---|
| Admin routes | Canonical and compatibility destinations are registered and audited. |
| EmpireDrop payouts | Ten-rank validation, dedicated revisions, draft persistence, atomic publication, and public projection checks. |
| Gaming migration | Existing wallets stay authoritative; old signed identity can migrate to `rh_player`; names and recovery live in Gaming. |
| Removed feature | No routes, templates, assets, public fields, production dependency, or new-state object remains. |
| Dependencies | Root runtime requirements are lean; dev and optional Spaces dependencies are separate. |
| Packaging | Flat-root markers, runtime hashes, archive integrity, and no protected caches. |
| Security | CSRF, Superadmin checks, same-origin redirects, private credentials server-side, sanitized logs. |
| Live acceptance | Use `tools/live_smoke_v12.py` after deployment; production provider and browser behavior cannot be proven by offline checks alone. |
