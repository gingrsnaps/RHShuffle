# V14 public races and Gaming community board

## Purpose

V14 reduces public visual competition while keeping complete operational detail in the authenticated Admin Control Center. It also introduces a public Gaming community feed without exposing private player or wallet data.

## Uniform wager-race presentation

Both provider views use:

- `RedHunllef Wager Race` as the fixed page title
- `Powered By` as the provider label
- equal provider cards and typography
- the same race-summary, podium and standings components
- the same Place, Player, Wagered and Prize columns
- one segmented provider selector

Provider behavior remains independent:

- Shuffle: Top 15 and weighted wager rules
- EmpireDrop: Top 10 and official partner-race data
- independent schedules, prizes and API refreshes

The public page no longer displays provider health, HTTP state, retry cadence, cache duration, next check or last provider attempt. Those fields remain available in Admin. Visitors receive only a calm unavailable or cached-data message when needed.

## Public Gaming feed

`GET /gaming/api/public-leaderboard` returns a deliberately small allowlisted projection:

- current RedPoints season
- recent aggregate activity count
- opted-in named recent players
- opted-in weekly Top 10
- opted-in per-game Top 10 rankings
- recent aggregate counts by game

It does not return:

- player or wallet IDs
- IP addresses or network metadata
- balances
- receipts or pending wagers
- server seeds or commitments
- recovery information
- administrator grants or funding adjustments

### Activity rules

Only a confirmed server-side game action updates activity. Opening a page, refreshing a wallet, or receiving a five-second poll does not make a visitor appear active.

- Playing now: confirmed activity in the last 30 seconds
- Recently active: confirmed activity in the last two minutes
- Active card hand: shown as `In a hand`

### Public-name privacy

Players explicitly choose whether their community name appears publicly. Existing wallets migrate with public visibility disabled. New players see the choice when confirming a name. Aggregate activity counts can include private players, but private names never enter the public response.

### Refresh and performance

The Gaming page uses its existing five-second state request for both the private wallet and the public community board. Polling pauses when the browser tab is hidden. The server caches the sanitized projection and invalidates it only after confirmed activity or when a visible activity status must change. ETags permit unchanged responses to use conditional delivery.

## Administrator additions

The private Gaming admin view includes:

- current or last game
- last confirmed action time
- public-name visibility
- public recent-player count
- public feed revision

Existing wallet, funding and network details remain protected by administrator authorization.

## Deployment

The root `requirements.txt` remains the production dependency source. The optional Spaces SDK is not required while `RH_SPACES_ENABLE=0`. Use a forced DigitalOcean rebuild after replacing the source tree.

## Validation

The package includes `tests/test_v14_public_experience.py`, which checks:

- public name opt-in behavior
- aggregate-only inclusion of private activity
- removal of private fields
- activity expiration and status transitions
- settled-stat rankings
- provider-title and branding consistency
- absence of public operational status text
- public Gaming route and hidden-tab polling support
