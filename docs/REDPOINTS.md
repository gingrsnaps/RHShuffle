# RedPoints gaming

Release **2026.10.04-redpoints-arcade2**. New rounds use **redpoints-v2**; old
**redpoints-v1** receipts remain verifiable. Run only `python wager_backend.py`.

## Currency and identity

Dice, Keno, Plinko and Blackjack use one shared **RedPoints** wallet. These are
play-only points, with no purchases, withdrawals or conversion to Shuffle or
Botrix balances. None of these games sends bets to Shuffle.

The signed player identity owns the name, wallet, statistics and receipts. One
wallet may play per public IP each race week. All four games use that same mapping.
A name or IP alone never authenticates someone else's wallet: restore an existing
player in a new browser with its private recovery code. Users sharing a public IP
cannot open separate gaming wallets that week. An existing signed player can move
to a previously unclaimed IP without losing their points. IPv4 aliases and IPv6
spelling are normalized. Canonical IPs are retained in private state for the admin
view; they are not published in public wallet responses or receipts.

The existing boss identity and recovery code are reused. Boss household settings,
30-second attacks, damage, health, uploads and achievements keep their own rules.

## Wallet and records

- One **100,000-point** allowance per player/week, shared across four games.
- Weekly boundary: Tuesday **18:00 America/New_York**, including daylight saving.
- No fixed stake cap or daily/weekly round-count limit. Stakes must be positive
  whole points, affordable, and safe under the exact-integer range `2^53−1`.
- Reloads, changing names or switching games do not refill a wallet.
- Net winnings mean **returned points minus total points wagered**. Returned
  points include the original stake. Losses remain negative.
- Debits, returns, seed rotation, receipts and statistics save under one file lock
  with atomic UTF-8 JSON replacement. Failed writes leave the previous save intact.
- Receipts keep unique request IDs and sequential nonces. Retrying the same
  request/move cannot charge another stake or apply the same Blackjack hit twice.
- The latest 30 settled receipts per wallet remain available across weekly resets.
  Download receipts for longer retention. Full recovery includes wallets and seeds.
- Existing three-game saves gain a zeroed Blackjack stats entry. Migration retains
  balances, names, original seeds, nonces and receipts; it never merges players.

## Admin rankings

Sign in and open **Gaming top 5**, `/admin/gaming`, or `/admin?tab=gaming`.
Overview also includes the same four lists. The visible installed release should
be **2026.10.04-redpoints-arcade2**. Complete packages and patch files must match.

Each game shows up to five players ranked by actual net winnings, then total
returned points, then a stable short player identifier. Records include the full
submitted name, shared player identifier, canonical linked IPs, available balance,
completed rounds, total wagered and total returned. Per-game player/round counts
cover every qualifying player before slicing the five leaders. In-progress
Blackjack hands count only once they settle.

Gaming polls the authenticated local endpoint every five seconds while visible;
a manual refresh is also available. These polls do not request Shuffle data.
Shuffle and Kick retain their separate 60-second checks. When a session expires,
the visible private rows are cleared and late responses cannot repopulate them.

An empty board means no completed RedPoints rounds are saved for that game in the
current weekly period. It does not copy the Shuffle leaderboard or boss scores.
After redeployment, restore the saved private recovery backup if local data was
lost. The application cannot recreate unrecorded results or invent five players.

## Game rules

| Game | Rules |
| --- | --- |
| Dice | Choose a 1–95% integer win chance. Under wins below C×100; Over wins at or above 10000−C×100 on an unbiased integer roll 0–9999. A win returns floor(stake×99/C). The large bar, smaller slider, percentage and target are synchronized. |
| Keno | Pick 1–10 distinct values from 1–40. Quick pick chooses ten. Ten values are drawn without replacement. Hits select the published risk/count payout table. |
| Plinko | Choose 8, 12 or 16 rows and Low/Medium/High risk. Unbiased left/right bits define the path; their sum determines the slot. Fixed symmetric v2 tables determine payouts. 16-row High has 1000× edge payouts, 12-row High 170×, and 8-row High 29×. |
| Blackjack | Six standard decks, freshly sampled without replacement each hand. Hit, Stand, or Double on the first two cards. Dealer checks for a natural before player decisions and stands on hard/soft 17. Naturals pay 3:2 profit, other wins 1:1, and pushes return the stake. No split, insurance or surrender. |

Multipliers include the wager; whole-point payouts round down. Keno tables target
99% before multiplier/payout rounding. Plinko's fixed table expectation is shown
for the selected risk and rows and can differ slightly from 99%. Blackjack has
no fixed RTP claim because the player's decisions affect its expectation. Admin
statistics are actual ledger results, not hypothetical returns.

Blackjack reserves the original stake at Deal. Double reserves one additional
original stake and draws exactly one final card. A saved active hand blocks new
wagers in other games and resumes after refreshing or reconnecting. Its hidden
hole card and server seed remain private until settlement. At a new week, an
unfinished hand automatically stands and settles against the old week, then the
new allowance and counters apply. A doubled hand's net subtracts its full stake.

Plinko animation uses a cached board and one `requestAnimationFrame` loop for
concurrent balls. Each verified bit controls a short parabolic bounce above the
next peg; the ball ends in its verified payout slot. Rendering never decides or
changes a payout. Reduced motion and canvas failures retain the textual result.

## Independent verification

1. The server creates a 32-byte random seed and publishes the SHA-256 hash of the
   decoded seed bytes before the wager. Its active seed stays private.
2. The player may choose a client seed. After reading the commitment, the browser
   adds 16 random bytes of salt. Each round also includes a season and nonce.
3. HMAC-SHA-256 uses the decoded server seed as its key and compact ASCII JSON of:

```text
[rules_version, season, game, client_seed, client_salt,
 nonce, original_wager, canonical_options, block_number]
```

Options have sorted keys and no insignificant whitespace. Blocks start at zero.
Read consecutive four-byte big-endian words. For a draw from N possibilities,
reject words at or above `2^32 − (2^32 mod N)`, then use the remainder modulo N.
This avoids modulo bias. The version prefix is v2 for new wagers, v1 for old ones.

Keno uses a partial Fisher–Yates shuffle of 1–40. Blackjack uses the same sampling
method on a six-deck shoe of 312 unique IDs: `deck×52 + suit×13 + rank−1`. Suits are
spades/hearts/clubs/diamonds, ranks A=1 through K=13. Initial deal order is player,
dealer, player, dealer. `blackjack.py` replays the recorded legal actions on that
fixed sequence; actions do not change or reshuffle the committed shoe.

The seed is revealed when a round finishes. The browser checks the earlier hash,
inputs, result and payout using its separate Web Crypto/BigInt implementation.
Blackjack verification also reproduces the hand from the recorded action history.
New receipts use fixed v2 Plinko tables; old v1 receipts use their original
weighted tables. All tables are published in `fairness.py` and
`static/fairness.js`; the page displays exact multipliers before a wager.

The `/gaming/fairness` page verifies downloaded receipts entirely in the browser.
`python tools/verify_redpoints.py receipts.json` is an optional offline utility,
not another web server or required launch command. Reference vectors and rule,
wallet, replay and migration tests are included under `tests/`.

Keep the commitment observed before playing. A receipt by itself proves internal
consistency, not when its hash was first published. This is an inspectable
algorithm, not independent certification. A host controls the server and client
code; reproducible results do not guarantee uptime or truthful hosting.

## Deployment and persistence

On DigitalOcean App Platform set `TRUST_APP_PLATFORM=1` so visitor addresses come
from its `DO-Connecting-IP` header. On a directly exposed/local server leave it
at 0: do not trust visitor-supplied proxy headers. Use one application instance.

The requested JSON-only design remains. **App Platform local files can disappear
on redeploy/container replacement.** Preserve current `data/state.json`, private
recovery data and cookie-signing secrets. Export the latest full private backup
before deployment. Recovery restores only what was saved in that backup; neither
a recovery code nor the user's IP contains their balance. New database or service
setup is not required by this update.

`wager_backend.py` loads the wallet, fairness engine, Blackjack rules, templates
and static assets automatically. The source connection clients remain separate.
Blackjack has no Shuffle integration or real-money settlement path.
