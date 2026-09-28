# Verification record — 2026.09.28-boss-controls

Verified in the supplied Linux workspace on 2026-09-28 using synthetic accounts,
images and provider responses. No production raid or account was modified.

| Check | Result |
| --- | --- |
| Python suite | 103 discovered: **99 passed**, 4 optional PostgreSQL tests skipped. |
| DOM/CSS suite | **39 passed** against the real rendered templates using jsdom. |
| PNG/JPG/JPEG/WebP upload | Actual decoding, 512 × 256 resize of a 900 × 450 source, metadata removal, served PNG bytes, cache headers and conditional 304 response passed. |
| Invalid uploads | Empty, fake, corrupt, renamed GIF, wrong extension, oversized, excessive-pixel, animated PNG and animated WebP images rejected without changing the existing avatar or raid. |
| Avatar visibility | Public game, homepage invitation and admin preview render the uploaded URL. Game/admin polling updates the image and preserves health form drafts. Original-logo reset and avatar retention after a new raid passed. |
| Current raid health | Explicit confirmation and valid bounds required. Edits use the latest committed damage, even if attacks arrive after the form opens. Player totals, network limits and receipts are retained. Stale health revisions and old raid forms cannot overwrite newer edits. |
| No automatic regeneration | Idle time, daily rollover, pause/resume and cold app restart retain damage. Ordinary writes and browser snapshots cannot refill HP. Only an explicit health edit can reopen the same defeated raid. |
| Recovery | Fresh-instance import and cold initialization retain avatar bytes, boss name, damage settings, health revision and progress. Existing state wins over a malformed newer seed. Recovery preview rejects a mismatched image checksum without mutation. |
| Authorization | All seven boss management actions reject guests, unknown accounts, revoked session versions and tampered cookies before image decoding or writes. Forged role flags cannot grant access. Missing, invalid and Unicode CSRF tokens return controlled errors. Ordinary admin sign-in and boss editing pass; private recovery remains Superadmin-only. Removed accounts lose access immediately. |
| Boss name and damage | Validated settings affect future hits only. A 450-point historical receipt remains valid after lowering damage. Publicly supplied damage, HP, role and settings fields cannot alter server calculations. Invalid names/ranges and stale forms are rejected; storage guards reject unapproved settings changes. Names render as text and admin drafts survive polling. |
| Public edit isolation | Public pages contain no management forms; management GET requests and writes to read-only game state return 405 without changing saved data. The public can view the chosen avatar and play normally. |
| Barebones game | Tutorial/story/help elements and footer are absent. Controls, cooldowns, safe retries, milestones, recent hits and victory contributors remain functional in DOM checks. |
| Multiplayer rules | Concurrent hits retain damage; shared-network requests enforce one hit; cooldowns, IPv6 grouping, daily caps, burst damage and final-hit clamping passed. The 100-player maximum-activity simulation finishes on raid day four. |
| Existing app functionality | Native login, date publication, original Superadmin import, source normalization, provider worker refreshes, unchanged-data handling, public masking, private Code Red rows, recovery and account roles passed. |
| Launch | Existing subprocess test exercises Waitress startup via `python wager_backend.py`, local storage and a stale database binding. No management script or separate game worker is needed. |
| Preserved files | Original provider settings, account seed and both logo assets match the supplied bytes exactly. |

## Verification limits

- The previous turn's native-browser visual attempt could not run: the workspace Chromium
  executable crashed at launch with SIGSEGV, before loading the app. The earlier
  release's browser screenshots are not evidence for this release's new layout.
  No new native-browser claim is made here. Current template/DOM checks and HTTP
  image/form integration tests passed.
- No dedicated disposable PostgreSQL database was provided; four optional
  compatibility tests skipped. Default local SQLite was tested. CI provisions
  PostgreSQL separately for that optional mode.
- No DigitalOcean deployment or successful live Shuffle/Kick connection was
  verified for this release. Provider checks use synthetic responses and local
  HTTP fixtures. Earlier live provider probes timed out.
- App Platform container storage is temporary. Recovery tests prove that a saved
  checkpoint restores its contents; they do not provide automatic remote backups
  or protect changes made after that checkpoint.

## Reproduce

```bash
python -m pip install -r requirements.txt
python -m unittest discover -s tests -v
```

Optional interface checks require Node only for development:

```bash
npm --prefix tests install --ignore-scripts
python tests/render_fixtures.py .test-fixtures
npm --prefix tests test
```

All published test counts are from actual executed checks. Generated fixture
accounts, preview data and runtime databases are excluded from the release ZIP.
