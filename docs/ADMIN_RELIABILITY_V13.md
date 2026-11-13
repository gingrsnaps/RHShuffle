# RedHunllef V13 admin reliability repair

Release: `2026.11.13-admin-pages-payouts-v13`

## Confirmed causes repaired

1. The shared admin layout imported `form_fields` and `action_feedback`, but the Shuffle schedule, Shuffle players, and Settings templates also called `field` and `player_rows`. Jinja treated those names as undefined and returned HTTP 500.
2. EmpireDrop payout writes completed, then the activity logger rejected the new draft/publish event names. That exception turned a successful write into the generic HTTP 500 page.
3. Some older EmpireDrop history rows did not contain `race_meta`, while the template accessed it as though it was always present.
4. Several workspace buttons still depended on indirect navigation and stale anchors.

## V13 behavior

- Every admin template imports all macros it uses.
- Operational logging is fail-safe and cannot invalidate a completed settings write.
- EmpireDrop draft and publish events are allowlisted.
- EmpireDrop history uses safe optional-field access.
- Canonical direct routes render the selected workspace instead of relying on query-string routing.
- Admin HTML is served with `no-store` caching.
- A server-side exception is logged with the request ID and original exception type.
- Shuffle and EmpireDrop local race windows start November 10, 2026 at 6:00 PM Eastern and end November 17, 2026 at 6:00 PM Eastern.

## Acceptance criteria

- Overview, Shuffle standings, Shuffle schedule, Shuffle players, EmpireDrop, Gaming, Settings, and Activity render with StrictUndefined enabled.
- Every literal admin link and form action points at a registered route.
- EmpireDrop prizes can be saved as draft and published without the logger raising.
- The saved payout record is read back and the public payout projection is verified.
- Root deployment files and requirements are present.
