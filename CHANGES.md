# Changes — 2026.10.03-community-gui

- Homepage defeat progress now fills 0% → 100%, while arena/admin HP still drains.
- Dedicated anonymous five-second boss snapshots; source checks remain 60 seconds.
- Reject stale boss snapshots and distinguish explicit host heals/new raids.
- Compact hero/countdown, larger avatar, legible percentage, one boss CTA and
  restrained red styling. Confirmed-hit animation respects reduced motion.
- Three clear mobile section links, a native history selector and week navigation.
- Server-confirmed admin receipts near controls; failed enhanced forms retain
  drafts and uploads. Existing authentication, CSRF and confirmation gates remain.
- Added real Chromium screenshot/layout checks with red-pixel assertions for
  0/25/75/100 percent progress at desktop/mobile widths and live admin-form tests.
- Single launcher, JSON saves, credentials/accounts and unlimited hits preserved.

## Previous release

# Changes — 2026.10.03-weekly-history

- Fixed the separately rendered homepage boss HP bar in HTML and live JavaScript.
  Full HP is full; victory is empty. Included the existing arena/admin bar fixes.
- Added History navigation, a responsive public page and a cached read-only API.
  Four completed Tuesday 6 PM Eastern weeks, including DST changes, show Top 25
  weighted wagers with server-masked usernames.
- Backfill runs automatically inside the sole launcher. Cache reads do not contact
  Shuffle; retries retain saved results and honor provider backoff.
- Reuse exact archived race settings/overrides/prizes where present. Unknown
  historical prizes remain unknown; no current prize-pool substitution.
- Include weekly history in the existing full private recovery export/import.
- Fixed admin self-block protection when using DigitalOcean's visitor IP header.
- Added calendar/privacy/cache/recovery/HP tests and expanded account/log/IP/admin
  permission checks. Existing admin and multiplayer regression suites are retained.
- No new runtime dependencies, database, extra launcher, or hit quotas.

## Previous release — 2026.09.29-username-save

- Reproduced and fixed a rejected name save when the page session expired while
  the signed player cookie remained valid. Game CSRF is now bound to that player.
- Added a complete native POST form and POST/redirect/GET confirmation.
- Kept typed drafts on errors; added visible confirmation and a full-page fallback.
- Stop false success responses and duplicate in-flight form submissions.
- Allow reuse of display labels without reading, merging or replacing another player.
- Save names independently of raid IDs; a host restart cannot invalidate a name form.
- Added actual HTTP/cookie/script integration tests plus permission and persistence checks.
- Read the release from rendered page metadata so upgrades do not leave a stale
  hardcoded version warning in the public/admin JavaScript.
- No data reset, dependency, SQL service, hit quota or extra launch script added.

## Previous release

# Changes — 2026.09.29-player-access

## Fixed community access and username persistence

- Removed shared-IP registration limits and shared-IP attack cooldowns. Reproduced
  98 of 100 players blocked behind two IPs before the fix.
- Saved names and cooldowns follow the existing signed browser identity. IP changes
  no longer make a saved profile appear unregistered.
- Registration, recovery and attacks work without a proxy visitor-IP header.
  Arbitrary forwarding headers are still not trusted as verified identities.
- Rejected-request throttling belongs to a browser instead of a whole network.
- A confirmed name save wins over older polls and earlier request timestamps.
- Retired household-approval and connection-release UI; no approvals or raid reset
  are needed. Old submitted admin forms return a clear retired-control message.
- Kept every original account/configuration/logo, raid, player key, recovery code,
  contribution, achievement, avatar, combat setting and admin permission.
- Added concurrent 100-player shared-proxy tests and persistence/race regressions.

Hits stay unlimited per day/week, with one attack per player every 30 seconds.
The only launch command remains `python wager_backend.py`; JSON storage needs no
SQL service or extra setup. Existing local saves must be preserved when updating.

## Previous release — 2026.09.28-community-polish

Implemented suggestions 2–9. Excluded the achievement-display change (#1) and
external checkpoints (#10). No daily/weekly hit limits, new dependency, service,
management command or second launcher was added.

## Player experience

- Saved “Playing as…” summary with Edit; a private, downloadable recovery code.
- Recovery preserves identity, raid damage, badges and the last attack receipt.
- Admin-approved household allowances; 30-second server cooldown per approved player.
- Fifteen-player Red rally: rolling ten-minute participation, cosmetic arena unlock.
- Remembered style, compact totals with exact detail, stable attack buttons,
  consistent configured boss names and a live last-checked label.

## Administration

- Recent pace and estimates, plus next-raid HP presets. Never automatic HP scaling.
- Live health/damage previews and a bounded, persistent history of boss edits.
- Shared connection controls and private request activity flags.
- Separate source check and content-change times; automatic 60-second checks retained.
- All boss mutation endpoints remain authenticated and CSRF-protected.

## Runtime

- Replaced active SQLite/PostgreSQL storage with atomic UTF-8 JSON.
- Imports a previous local SQLite save once, read-only, and leaves it untouched.
- Preserves existing accounts, hashes, secrets, current progress and images.
- Caches committed files while detecting writes from another local process.
- Rejected-request throttles never block an otherwise eligible 30-second attack.
- Removed the optional PostgreSQL dependency file, its tests and CI service.
- Existing manual recovery remains. No remote checkpoint integration was added.

## Retained

Original Shuffle/Kick configuration, Superadmin seed, logos, race date publication,
automatic provider jobs, public masking, uncensored admin Code Red Top 100,
uncensored boss Top 5, admin image uploads, HP/damage editing, random weakness,
mouse/keyboard re-arm, no automatic HP regeneration, unlimited hits and eight badges.

See README for local-file lifetime on DigitalOcean App Platform.
