# V12 Admin Reliability and Feature Removal

## Purpose

V12 resolves two recurring failures: administrator links that opened 404 pages and EmpireDrop prize changes that did not reliably publish. It also removes the Community Boss feature completely while preserving RedPoints players.

## Canonical navigation

Every visible administrator destination has one direct GET route registered in Flask and one centralized entry in `admin_navigation.py`. Older supported bookmarks redirect to the canonical route. JavaScript no longer needs to synthesize destinations.

## EmpireDrop payout transaction

The payout editor has independent draft and published records. A save:

1. validates CSRF and Superadmin access;
2. checks the dedicated payout revision;
3. validates currency and exactly ten amounts;
4. creates a pre-change backup;
5. writes atomically;
6. rereads and compares the persisted record;
7. refreshes runtime state;
8. for publication, compares the public prize projection;
9. logs a sanitized success or rejection event.

## Gaming migration

The old browser identity is accepted only as a migration input. Existing Gaming wallets stay authoritative. V12 issues a new Gaming-owned cookie and provides name and recovery controls inside Gaming. No attack, HP, avatar, cooldown, raid, achievement, or damage state remains.

## Removed runtime surface

The release contains no retired feature routes, templates, static files, status cards, public JSON fields, admin actions, image-processing dependency, or scheduled poller.

## Acceptance criteria

- Every visible Admin link returns an authenticated 200 response.
- Every compatibility route reaches the same canonical destination.
- EmpireDrop draft survives reload.
- Publishing appears in the public payload and rendered page.
- Shuffle and EmpireDrop provider refreshes remain unchanged.
- Existing RedPoints wallet IDs and balances survive migration.
- No retired feature entry appears publicly or in Admin.
- Root deployment markers are present.
- A state backup is created before migration and payout changes.

## Live verification limitation

Offline checks verify route registration, templates, JavaScript syntax, state validation, manifests, and archives. The final authenticated DigitalOcean behavior must still be confirmed against the deployed application with `tools/live_smoke_v12.py`.
