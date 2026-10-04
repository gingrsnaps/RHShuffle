# RedPoints Gaming — rules, fairness and operation

Release **2026.10.04-redpoints**, fairness protocol **redpoints-v1**.

## Player experience

Gaming is a separate dashboard at `/gaming`. Dice, Keno and Plinko have their own
URLs, controls, board and payout preview. Desktop uses controls beside the board;
mobile stacks them with touch-sized controls. The global header keeps every
configured public destination visible. Points Shop opens
https://botrix.live/k/redhunllef/shop in a separate tab.

RedPoints are play-only: no purchase, withdrawal, cash value, transfer or conversion
to Botrix/Shuffle balances. Nothing here contributes to real Shuffle wagers.

A player saves a name once using the existing signed browser profile. If that name
was already saved in the boss fight, Gaming reuses it. The same profile owns one
wallet across all three games. A username is a display label, not authentication;
using another player's spelling does not acquire that player's wallet.

## Wallet and weekly reset

- Start: **100,000 whole RedPoints**, shared across Dice, Keno and Plinko.
- Wager: **1–10,000 whole points**, never more than the current balance.
- Settlement: `new_balance = previous_balance − wager + returned_points`.
- A returned amount includes the stake; a 2× return is a 1× net profit.
- At zero points the player waits for the next reset. There is no refill button.
- One second between settled rounds; no daily/weekly round-count limit.
- Reset: Tuesday **18:00 America/New_York**, using timezone data. A season starts
  at that boundary and ends at the following Tuesday boundary. DST weeks can be
  167/169 hours. The displayed reset is based on the server's clock.
- The first read/bet after a new boundary resets that profile to 100,000 and clears
  its weekly game counters. Admin rankings immediately exclude old-season totals.
  No separate scheduler or mass midnight rewrite is necessary.
- The schedule is the same fixed Tuesday-to-Tuesday calendar as completed history.
  Editing race dates, prizes, title or campaign early does not mint extra points.
  This allowance is not dynamically tied to arbitrary off-schedule race windows.
- Reloads, game switches, name changes and process restarts with the same save do
  not refill a wallet. Changing browser/hostname without recovering the original
  profile creates a separate identity, as in the boss fight.

Keep the existing player recovery code from the boss page. Recovering that identity
also recovers its RedPoints wallet if the server still has its saved state. The
code does not contain a balance and cannot recreate lost server data. Normal raid
restarts do not reset Gaming balances. The community boss remains unlimited hits,
30-second cooldown, no regeneration and the same eight achievements.

## Admin rankings

`/admin?tab=gaming` has three Top 5 lists. The overview includes the same lists.
They update through the existing authenticated status poll, every 60 seconds while
the page is visible, and catch up when the tab becomes visible again.

Each list includes full submitted names, a short profile tag, rounds played,
points wagered, points returned and net winnings. The private game statistics also
record each player's biggest return. Sort order is:

1. Net winnings descending: `returned − wagered`.
2. Total returned points descending.
3. Stable short profile tag for deterministic ties.

Only profiles with a wager in that game in the current week appear. Negative net
results remain negative. If only three profiles played, the list contains three.
There is no public full-name Gaming ranking endpoint. Admin pages and status
require the existing current admin session; management writes retain CSRF checks.

## Fairness protocol

The backend publishes a commitment before each bet and reveals that one-time
secret immediately afterward. Reusing a revealed secret for another bet would be
unsafe, so every settled round installs a new random secret.

1. Generate 32 random bytes using Python `secrets`; store them as 64 lowercase hex
   characters. The commitment is SHA-256 of the **decoded 32 bytes**, lowercase hex.
2. Send the commitment with the player's current season and sequential nonce.
   Nonces start at zero and do not reset with the weekly allowance.
3. Let the player choose a client-seed string. After reading the commitment, the
   browser generates 16 additional random bytes with `crypto.getRandomValues`.
   Their lowercase 32-character hex representation is the client salt.
4. Submit game, canonical options, whole-point wager, client seed/salt, season,
   expected commitment, nonce, rules version and unique request ID.
5. Verify those values server-side. Reproduce the deterministic result, debit the
   wager, credit the return, update per-game statistics, store the revealed receipt
   and install the next secret in **one atomic JSON transaction**.
6. Return the receipt and authoritative wallet only after that transaction saves.
7. The browser independently checks the commitment it saw before submission,
   every submitted outcome input, the result and payout before displaying Verified.

The fresh client salt makes the completed HMAC input unpredictable when the honest
client first reads the server commitment. The secret is not exposed in public
state, templates, rankings or routine logs. Full Superadmin recovery exports must
contain active secrets to preserve outstanding commitments, so those exports
must remain private.

### Canonical message and random draws

Decode `server_seed` from hex. Use those bytes as the HMAC-SHA-256 key.
The message is the ASCII encoding of compact JSON:

```json
["redpoints-v1","1790719200","dice","example-client","0123456789abcdef0123456789abcdef",0,100,{"chance":50,"side":"under"},0]
```

In order: protocol version, season ID string, game, client seed, client salt,
nonce, wager, options, block number. All option object keys are lexicographically
sorted. No insignificant spaces are inserted around JSON separators. Client
seeds allow only 1–64 ASCII letters, digits, spaces, periods, underscores and
hyphens, avoiding cross-language Unicode normalization differences.

Block numbers start at zero. Consume each 32-byte digest in consecutive four-byte
big-endian unsigned integers. When the digest is exhausted, increment the block
number and generate another digest. To draw from `N` equally likely outcomes:

```text
limit = 2^32 − (2^32 mod N)
read the next 32-bit integer x
if x >= limit, discard it and try the next integer
otherwise return x mod N
```

Rejection sampling removes modulo bias. This matters especially while Keno's
remaining pool changes. The request ID, timestamp, post-bet balance and next
commitment are receipt metadata; they are not HMAC inputs.

### Dice

Choose whole-number win chance `C` from 1 through 95 and side Under or Over.
Draw one unbiased integer `r` in `[0, 9999]`; display `r / 100` with two decimals.

```text
Under wins when r < C × 100
Over wins when r >= 10000 − C × 100
If won: returned_points = floor(wager × 99 / C)
Otherwise: returned_points = 0
```

Both sides have exactly `C%` win probability. Before whole-point rounding the
expected return is 99% of the stake. For example, a 100-point bet at 50% returns
198 on a win, making net winnings +98; a loss returns 0, making net winnings −100.

### Keno

Choose 1–10 unique integers in `[1, 40]`. Sort picks ascending for the canonical
options. Draw ten distinct numbers with a partial Fisher–Yates shuffle:

```text
pool = [1, 2, ..., 40]
for i from 0 through 9:
    j = i + unbiased_draw_below(40 − i)
    swap pool[i] with pool[j]
    append pool[i] to drawn
hits = number of selected picks in drawn
```

If `k` numbers were selected, the probability of exactly `h` matches is:

```text
P(h) = choose(k, h) × choose(40 − k, 10 − h) / choose(40, 10)
```

The risk exponent `p` is 2 for Low, 4 for Medium, and 7 for High. Define weight
`w(h) = h^p`. Zero hits have zero weight. Higher risk concentrates returns in the
less frequent high-match outcomes. The risk selection does not change the draw.

### Plinko

Choose 8, 12 or 16 rows. Draw one unbiased bit per row: zero is left, one is right.
The landing slot is the sum of those bits, numbered zero at the left edge through
`rows` at the right edge. The corresponding probability is:

```text
P(slot) = choose(rows, slot) / 2^rows
w(slot) = 1/2 + abs(2 × slot − rows)^p
```

The exponent `p` again uses 2, 4 or 7 for Low, Medium or High risk. The table is
symmetric. The canvas animates the already committed path; frame rate, screen
size, animation timing and physics do not decide outcomes.

### Exact Keno and Plinko payout tables

Use exact rational arithmetic to compute the probability-weighted mean:

```text
mean = sum(P(i) × w(i)) across every possible outcome i
multiplier_units(i) = floor((99/100) × w(i) / mean × 10000)
multiplier(i) = multiplier_units(i) / 10000
returned_points = floor(wager × multiplier_units(i) / 10000)
```

The server uses Python `Fraction` and integers. The independent browser verifier
uses `BigInt` integer ratios; it does not trust the server's returned multiplier.
Multipliers are fixed at four decimal places. Every supported table targets 99%
expected return before rounding; tests show table rounding keeps that expectation
between 98.99% and 99%. Whole-point payout rounding lowers the effective return
further, particularly with very small stakes. The on-page table displays the
rounded return for the selected wager before submission. Some central/high-risk
outcomes legitimately return zero points at small wagers.

These are custom RedPoints rules and tables, not copies of another operator's
payout schedule. A specific player's results can vary substantially from expected
return, especially at high risk. A verified receipt is not a winning guarantee.

## Receipts and independent verification

The latest 30 receipts across all three games are retained for each profile,
including through weekly resets. Download them to keep a longer history. Each
contains the revealed seed, its commitment, client inputs, version/season/nonce,
options, wager, result, returned points, net points, post-bet balance and next
commitment. Game metadata is separate from the user's display name.

Use **Verify / receipt** for a stored round. Use `/gaming/fairness` to paste one
receipt or an array of up to 100, at most 2 MB. Verification runs locally in the
browser with Web Crypto and makes no form submission or API request. HTTPS or
localhost is needed for Web Crypto.

For an independent local check using the bundled pure-Python implementation:

```bash
python tools/verify_redpoints.py receipts.json
python tools/verify_redpoints.py one-receipt.json --commitment YOUR_SAVED_PRE_BET_HASH
```

This utility does not start a server or open the application's state file. It
returns a nonzero exit code if verification fails. Synthetic reference vectors
are in `tests/fairness_vectors.json`; the JavaScript test verifies all 47 against
the separately implemented browser algorithm.

Keep the commitment observed **before** playing. Checking a receipt against only
its own embedded hash verifies internal consistency; it cannot prove when that
hash was first published. The browser retains its pre-bet value during normal
submission and checks it against the response. The code is inspectable, but there
is no external auditor, notarized commitment ledger or third-party certification.
A host controls the server and distributed client code and can refuse requests;
cryptographic reproducibility alone does not prove service availability or prevent
all dishonest hosting. Download the verifier/commitments independently if auditing.

## Reliability and storage boundaries

- All balance changes, statistics, seeds and receipts commit under the existing
  file lock with UTF-8 atomic replacement. A failed save leaves the prior balance
  and seed intact. The browser never optimistically adds winnings.
- A repeated request ID in the retained receipt window returns its old settlement.
  Old nonce/season/commitment checks prevent an evicted or stale request from being
  treated as a new valid wager. No uncertain POST is automatically resubmitted.
- A pending request is kept in that tab's session storage. An explicit Retry checks
  the same request; concurrent tabs receive a refresh message if another spent
  the commitment first. The UI verifies the receipt before enabling the next round.
- Routine wallet reads use cached state and ETags. Hidden tabs pause polling.
- Amounts use exact integers up to `2^53 − 1`, including worst-case payout checks.
  The registry allows up to 10,000 browser profiles; 100 independent profiles were
  tested. This is not a throughput benchmark or one-person-per-account guarantee.
- Full private recovery includes wallets, current seeds and receipts. Race-only
  backups/restores do not replace wallets. Recovery validation checks balances
  against weekly net totals and verifies saved receipts before accepting a seed.
- Preserve `data/state.json` and original cookie-signing secrets. Do not clear
  player cookies as an update step. A name alone is not a recovery credential.

**DigitalOcean App Platform local files are ephemeral.** With the requested
local-only design, a process restart can retain state only if the same filesystem
remains. A redeploy/container replacement can lose everything since the last
private recovery export. A fresh container imports `private/recovery.seed.json`
when present. This is a checkpoint, not continuous durable storage. One instance
is required; replicas have independent local wallets. See README deployment steps
and DigitalOcean's [storage documentation](https://docs.digitalocean.com/products/app-platform/how-to/store-data/).

## Files and console output

`gaming.py` handles wallets, seasons, settlement and rankings. `fairness.py` is
pure deterministic math. `static/fairness.js` implements that math independently.
`static/gaming.js` handles live state, controls, receipts and presentation.
`templates/gaming.html`, `templates/gaming_fairness.html`, `templates/admin_gaming.html`
and `static/gaming.css` provide the pages. Existing `wager_backend.py` imports all
of them automatically. There is no new runtime package, build tool or server.

Console records use a `GAMING` prefix and report game, nonce, wager and return after
commit. They do not log player identity, active server seeds or provider credentials.
History source checks have their separate `HISTORY` category and safe diagnostics.
