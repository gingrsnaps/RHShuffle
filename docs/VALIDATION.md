# Validation — 2026.09.29-player-access

All **132 backend tests** were validated across the suite and targeted reruns.
The initial suite passed 130; two assertions that expected the retired shared-IP
restriction were updated to test per-player cooldowns and passed on rerun. **57 DOM/interface checks**
passed, including the new shared-proxy, saved-name and delayed-response regressions.

| Area | Verified behavior |
| --- | --- |
| JSON saves | Fresh startup, retained accounts, cold restart, corrupt-file refusal, failed atomic replacement rollback, two simultaneous store instances retaining every hit. |
| Names | Retained after IP/header changes, refresh, application restart and new raid. Cookie is not silently replaced on reload. Recovery can share a network with another active player. |
| Isolation | One browser flooding rejected registrations does not stop other browsers on the same IP. Name collisions cannot claim another player. |
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
regression test simulates the earlier Windows text-decoding failure. Browser checks
use rendered templates in jsdom; native Chromium was unavailable, so no new native
visual-rendering claim is made.

The extracted ZIP startup checks and package integrity results are recorded during
packaging. The code is shipped with its tests for repeatable verification.
