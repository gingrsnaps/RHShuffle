# Community update — 2026.09.22-community

Run **`python wager_backend.py`**. The imports, web server, source jobs, and game
remain in one process. No additional service or production dependency was added.
Original Shuffle/Kick configuration, Superadmin seed, and logo files are retained
byte for byte. Existing saved accounts, dates, and raid progress take precedence.

## What changed for visitors

The homepage is shorter and brings the standings into view sooner. Its boss
invitation shows remaining HP and community participation, with appropriate
labels for a paused raid or victory. It shares the public page's automatic
60-second update cycle. The arena still updates every five seconds while visible.

On narrow screens a fixed attack bar exposes style selection, remaining attacks,
and cooldown. It uses the same action and receipt as the main attack button.
There are no automatic attacks. Errors survive normal successful polls; players
can dismiss them, retry, or wait for the server to confirm the pending hit.

Quarter-health milestones change the arena's appearance and show a brief
celebration when crossed during a visit. Cosmetic badges reward the first hit,
100 hits (ten Crimson bursts), and participation on three distinct raid days.
Different visits on the same raid day do not count twice. A legacy profile starts
with one known participation day because its previous distinct days were not
recorded. Existing hit totals still qualify for first-hit/ten-burst badges.

Victory thanks everyone, with the complete list of raid aliases available in an
expandable recap. It is loaded once per completed raid and cannot return a live
raid's private records. A copy-link button has a selectable-text fallback when
the browser denies clipboard access. There is no chat, account signup, paid
reward, extra damage, or new wager requirement.

## What changed for administrators

Connections are summarized in two compact status chips. Expand the connection
details for timing, last success, retry reasons and individual source refreshes.
New failures expand the details automatically; repeated identical polls respect
a manually collapsed panel. Overview offers shortcuts to race and boss controls.
Draft fields, confirmations, filters, and Code Red expansion survive live updates.

Race publication shows current and proposed values side by side, including all
changed prizes, links, labels, dates, channel and campaign. A signed confirmation
is bound to the user, settings revision and full proposed settings. It expires
after 15 minutes. Editing reviewed values requires another review; another
administrator's save still triggers the existing revision-conflict protection.
Race-backup restore also shows changed values and saved-data counts.

The Superadmin recovery panel reports the last export generated and changes
since then: hits/damage, a new raid, raid controls, settings/accounts and standings.
Export metadata is separate from the admin record, so a download does not
invalidate open edit forms. A private recovery file can be uploaded for validation
and a readable account/race/boss summary. This preview imports nothing. Actual
fresh-instance recovery continues to use `private/recovery.seed.json`.

**An export-generation timestamp is not proof of an off-host backup.** Save the
download privately. Provider credentials remain in the supplied configuration
and are not copied into the recovery export. Malformed optional export metadata
is ignored during import while valid account/game progress remains recoverable.

## Performance and maintenance

- `boss.py` supplies one rules contract to validation, HTML instructions and JS.
- `/public-state` contains anonymous published data, excludes the moving clock,
  and uses a strong ETag. A matching request receives 304 with `X-Server-Time`.
  The browser reuses its in-memory body and updates its clock. Existing `/data`
  compatibility is retained. Cached data is always revalidated before reuse.
- Admin responses, personal cooldowns, CSRF values, recovery files and game
  actions remain `no-store`. No account or visitor identifiers enter the public
  conditional snapshot. This cache does not slow provider polling.
- Game lists retain unchanged DOM nodes instead of rebuilding every five seconds.
  Hit effects use `Element.animate()` without synchronous layout reads and honor
  reduced-motion preferences. Semantic controls retain keyboard support.
- `presentation.py` isolates change-review and recovery view models. JS and CSS
  are expanded into readable source, with comments around the state, retry,
  privacy, cache and transaction boundaries. No frontend build step is required.

## Upgrade and storage choice

1. Save a private recovery checkpoint before replacing the installation.
2. Keep the current `data/`, newer private recovery seed, and custom configuration.
3. Replace application modules, templates and static assets together. Install
   requirements and run the same sole launcher. Hard-refresh the browser.
4. Verify release `2026.09.22-community`, published dates, source results and boss
   progress. The original historical race is not silently advanced.

Local SQLite remains automatic. Use one process/instance with local storage.
On DigitalOcean App Platform, filesystem changes can disappear with container
replacement; this update cannot make that disk durable. The export tracker helps
identify unprotected progress but does not upload backups automatically.

For automatic durability **without a database service**, run this same package
on a persistent Linux host, preserve `data/`, and back it up off-host. Run under
a normal process supervisor with `wager_backend.py` as its command, set
`TRUST_APP_PLATFORM=0` for direct hosting, and provide HTTPS for production.
Alternatively, staying on App Platform requires a separately configured durable
storage or off-host backup destination. None is provisioned by this package;
downloaded checkpoints protect only the state they contain.

## Verification and references

See [VALIDATION.md](VALIDATION.md) for executed tests and external-service limits.
The default multi-day balance, existing account import, native admin login,
date publication and 60-second source cadence are regression-tested.

- [Conditional HTTP requests — MDN](https://developer.mozilla.org/en-US/docs/Web/HTTP/Guides/Conditional_requests)
- [Element.animate — MDN](https://developer.mozilla.org/en-US/docs/Web/API/Element/animate)
- [App Platform storage — DigitalOcean](https://docs.digitalocean.com/products/app-platform/how-to/store-data/)
