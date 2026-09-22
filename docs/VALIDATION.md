# Verification record — 2026.09.22-local

Verified in the supplied Linux workspace on 2026-09-22.

| Check | Result |
| --- | --- |
| Python tests | 57 passed. |
| PostgreSQL integration tests | 4 skipped: no dedicated database supplied. CI provisions one. |
| DOM and CSS checks | 20 passed with jsdom 26.1.0; no browser build required in production. |
| Date publication | Bottom confirmation button submits confirmation and persists the edited window. |
| Superseded failure | An old-window HTTP failure cannot mark the new race as failed or impose its ordinary retry delay. Explicit provider rate limits remain honored. |
| Concurrent refresh | An active provider check retains one follow-up request; repeated clicks coalesce. An in-flight browser read schedules a follow-up instead of dropping the request. |
| HTTP date-change and scheduled update | Real Requests transport to a local HTTP fixture: old-range failure, new-range success, then a second automatic publication without a refresh click. Only this isolated test uses an accelerated timer. |
| Progress feedback | Saved window, checking, completed, and rate-limit retry messages appear on all admin tabs; unsaved input values remain intact. |
| Windows encoding regression | Exact original CP1252 error reproduced before the fix. Startup and existing-state preservation pass after the fix, using a simulated Windows default on Linux. |
| Named form collision | Test models the native input/property collision: the old script posts to `/[object HTMLInputElement]`; the corrected script posts to `/admin/action` with CSRF/action/service intact. |
| Manual refresh publication | Real worker threads with synthetic provider data update both the masked public board and uncensored admin board after an authenticated refresh. |
| Refresh error handling | JSON 400/401/404/405/500/503 cases checked; native HTML errors still render. |
| Empty board | Waiting, empty source, campaign filter, zero weighted qualification, and failure/recovery checked. |
| Actual HTTP startup | Passed: child process launched with `python wager_backend.py` in production/local mode with a stale database binding, served `/healthz` and `/admin`, started both automatic jobs, and shut down. |
| Production without PostgreSQL | Passed with no usable DATABASE_URL and psycopg imports blocked; original accounts and secure HTTPS login remain functional. |
| Private recovery | Passed: only Superadmin can download; fresh-instance import preserves password changes, accounts, dates, overrides, history, signing key, and saved Top 15. A newer local store wins over seeds; corrupt recovery files stop import without resetting accounts. |
| Supplied credential files | Match original uploaded bytes. |
| Original Superadmin | Original password/hash verified; native login and all four dashboard tabs return successfully. |
| Account migration | Preserves every original account field; adds auth_version for session revocation. |
| Real Shuffle request | Timeout; successful provider connectivity not verified. |
| Real Kick authorization | Timeout; successful provider connectivity not verified. |
| Native browser checks | Passed in Chromium 153.0.8010.0 against Waitress with isolated accounts and synthetic providers: login, actual refresh POST/202, bottom-button date confirmation, published rows, expanded 100-user Code Red list, and the private recovery download. Production local-storage mode is used with a cookie override only for the HTTP test fixture; secure production cookies are separately checked over simulated HTTPS. No JavaScript errors; no horizontal overflow at 390 px. |
| Browser screenshot review | Public page/admin red theme retained; the new private recovery section was reviewed at mobile width. Test previews contain synthetic wagers and stream status. |
| DigitalOcean deployment | Not performed; no deployed site was provided for validation. |

The Python tests cover valid/invalid/mixed source responses, stale-cache
retention, original field envelopes, date-range requests with no lifetime
fallback, Kick reauthorization, independent workers, in-flight settings changes,
protected routes, CSRF, session revocation, login rate limits, account roles,
CSV safety, overrides, archive/restore confirmation, corrupt-store preservation,
DST validation, exact monetary calculations, and sole-script startup.

DOM checks render the real templates and verify unique IDs/label targets,
automatic polling, manual polling cadence, state/countdown boundaries, form
preservation across updates, Code Red expansion/search, text-only username
rendering, and session/proxy error recovery. They use synthetic source data.

The included PostgreSQL checks cover transactional revision conflicts, separate
live writes, advisory locks, import from the old JSONB table, and rollback of a
failed admin save. Run them against a disposable database before relying on a
first production migration. The code does not substitute a passing mocked SQL
check for a real database test.

The native form-property collision is emulated explicitly in jsdom because its default form implementation does not reproduce this browser behavior. The corrected refresh was also clicked in actual Chromium. Neither verification is a claim of a successful live Shuffle response.
