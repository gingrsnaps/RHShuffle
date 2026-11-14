# RedHunllef V17 — Timer card refinement

V17 is a narrow public-layout correction built on V16. It restores the earlier
Shuffle-style race timer proportions for both providers without changing API,
payout, schedule, Gaming, or administrator behavior.

## Changes

- Removed the forced equal-height hero behavior.
- Removed the 244px timer-card minimum height.
- Restored a natural-height, wide rectangular timer card.
- Applied an 18px radius and restrained gradient to both providers.
- Kept identical countdown typography, date layout, footer alignment, and mobile behavior.
- Changed the release identifier so DigitalOcean and browsers request fresh assets.

## Validation

Both `#shuffleRaceClock` and `#empireRaceClock` continue to use the same
`public_race_summary` macro and `.race-countdown` styling. No provider data or
server-side behavior was modified.
