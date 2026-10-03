# Validation — 2026.10.03-community-gui

**162 backend tests passed in a single full run.**
**68 DOM/HTTP interface checks passed together.**
**Native Chromium visual and interaction checks passed** at 1440px desktop, 390px
mobile and 320px narrow widths. Eleven screenshots cover eight homepage progress
states, two History layouts and admin feedback. Pixel checks measure the actual
red fill at 0%, 25%, 75%, and 100%, not just the HTML value.

This release verifies anonymous five-second boss summaries without provider calls
or player cookies, stale minute-feed rejection, explicit host heals and new raids,
confirmed progress values, error retention, server-created admin receipts, precise
accepted settings, failed-write rollback, and draft retention. The real browser
also submits a boss settings change, verifies the nearby receipt, then submits a
stale form and confirms the typed name remains intact.

History coverage includes Tuesday 6 PM cutoffs, 167/169-hour DST weeks, Top 25
masking, cache-only page reads, rollover, archived overrides/prizes, retry delays,
recovery, native mobile selection and previous/next navigation.

Admin coverage includes all five tabs, login/logout, account creation/reset/removal,
ban/unban, clearing logs, self-block prevention behind App Platform ingress, every
general write's session/CSRF requirements, race settings and publication, CSV,
backups/restore, image formats, boss edits and private leaderboards.

New coverage includes both shipped browser scripts talking to a real Waitress
server through a cookie jar: save after page-session loss, reload, attack, a second
player with the same name, and a real native form POST without JavaScript. Server
tests also cover cold restart, invalid cookie/CSRF rejection, preservation of drafts,
admin token separation, a raid restart during name entry and recovery-token rotation.
The real HTTP transport does not stub the username endpoint or its JSON responses.

| Area | Verified behavior |
| --- | --- |
| JSON saves | Fresh startup, retained accounts, cold restart, corrupt-file refusal, failed atomic replacement rollback, two simultaneous store instances retaining every hit. |
| Names | Retained after IP/header changes, refresh, application restart and new raid. Cookie is not silently replaced on reload. Recovery can share a network with another active player. |
| Isolation | One browser flooding rejected registrations does not stop other browsers on the same IP. Duplicate labels stay independent and cannot claim another player. |
| Migration | Previous SQLite accounts/revision/live snapshot/raid imported exactly; old file unchanged; no SQLite created on a fresh install. |
| Recovery codes | Authenticated owner issuance, CSRF rejection, forgery and replaced-code rejection, digest-only storage, original alias/hits/badges/receipt/cooldown retained. |
| Community access | 100 concurrent browser identities register and attack through one proxy IP, then each attacks again after 30 seconds. No approvals. Same-identity simultaneous clicks still allow only one hit. |
| Unlimited hits | Repeated eligible hits accepted beyond previous daily counts; rejected-request throttle does not block an eligible hit. Existing week-long gameplay/achievement tests pass. |
| Rally/estimates | Distinct rolling-window players, repeat-player deduplication, window expiry, next-raid reset, cosmetic unlock, no automatic HP/damage changes. |
| Admin edits | Private persistent actor/before/after history, existing avatar/name/HP/damage permissions and stale revision checks. |
| Interface | Identity collapse/edit, safe code recovery, remembered style, rally display, exact previews, presets without submission, private history clearing on expiry, saved names winning over stale polls, and attack controls pausing during profile writes. |
| Status | Five-second boss polling, 60-second provider polling, distinct source success/change timestamps, dynamic boss victory name, ETag reuse and reconnect behavior. |
| Existing features | Native login, race date publication, provider envelopes, safe failure responses, Code Red Top 100, public masking, uploads and recovery export. |

The original provider configuration, account seed, PNG and ICO are preserved byte
for byte. The badge calculation function is preserved unchanged; #1 was excluded.
No remote checkpoint feature or external SQL service was added; #10 was excluded.

Validation uses synthetic provider responses and disposable local saves. It did
not contact the live Shuffle/Kick accounts or deploy to DigitalOcean. This Linux
workspace ran Python 3.12; Windows/Python 3.14 was not executed natively. An encoding
regression test simulates the earlier Windows text-decoding failure. Browser checks use both jsdom/real HTTP integration and native Chromium. Screenshots
and geometry/pixel assertions use synthetic data. Their fixtures are disposable
and never run against the deployed app.

The extracted ZIP startup checks and package integrity results are recorded during
packaging. The code is shipped with its tests for repeatable verification.
