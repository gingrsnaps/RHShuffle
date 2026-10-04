# RedPoints gaming

Release **2026.10.04-redpoints-arcade3-seven-games**. New rounds use **redpoints-v3**. Earlier
**redpoints-v1** and **redpoints-v2** receipts remain verifiable. Run only `python wager_backend.py`.

## Currency and identity

Dice, Keno, Plinko, Blackjack, Limbo, Coinflip and Poker use one shared **RedPoints** wallet. These are
play-only points, with no purchases, withdrawals or conversion to Shuffle or
Botrix balances. None of these games sends bets to Shuffle.

The signed player identity owns the name, wallet, statistics and receipts. Everyone
on a shared IP may have a separate wallet. A missing IP address or a full tracking
directory never blocks play. Moving networks retains the same signed player's
records. A name or IP never authenticates access to someone else's wallet; use the
private recovery code to restore your own player in another browser.

Save your community name on Gaming before playing. Existing boss names are offered
as suggestions. First confirmation activates at least 100,000 points, preserving
larger balances or prior admin grants. IP aliases are normalized and saved only as
admin tracking information. Older exclusive IP claims migrate to many-player
associations without merging wallets or dropping prior connection records.

The existing boss identity and recovery code are reused. Boss household settings,
30-second attacks, damage, health, uploads and achievements keep their own rules.

## Wallet and records

- **100,000 starting points** per confirmed player, shared across seven games.
- Weekly boundary: Tuesday **18:00 America/New_York**, including daylight saving.
- No fixed stake cap or daily/weekly round-count limit. Stakes must be positive
  whole points, affordable, and safe under the exact-integer range `2^53−1`.
- Reloading a Gaming page sets its player to exactly **100,000 available points**.
  Server startup sets every saved wallet to **100,000**. Larger balances are also
  set to 100,000. Changing games, changing names or automatic polls do not refill.
- The admin grant adds **100,000 per saved wallet**, retaining existing points.
  Grants require an authenticated admin, CSRF and an idempotent request ID.
- Funding uses a separate wallet adjustment. It never counts as game profit.
  Names, nonces, commitments, receipts and active Blackjack and Poker hands are preserved.
  The normal weekly reset still clears standings and settles old pending hands.
- Net winnings mean **returned points minus total points wagered**. Returned
  points include the original stake. Losses remain negative.
- Debits, returns, seed rotation, receipts and statistics save under one file lock
  with atomic UTF-8 JSON replacement. Failed writes leave the previous save intact.
- Receipts keep unique request IDs and sequential nonces. Retrying the same
  request/move cannot charge another stake or apply the same Blackjack hit twice.
- The latest 30 settled receipts per wallet remain available across weekly resets.
  Download receipts for longer retention. Full recovery includes wallets and seeds.
- Existing saves gain zeroed entries for any newly added games. Migration retains
  names, original seeds, nonces and receipts; it never merges players. The startup
  funding rule restores available balances separately after validation.

## Admin rankings

Sign in and open **Gaming top 5**, `/admin/gaming`, or `/admin?tab=gaming`.
Overview also includes the same seven lists. The visible installed release should
be **2026.10.04-redpoints-arcade3-seven-games**. Complete packages and patch files must match.

Each game shows up to five players ranked by actual net winnings, then total
returned points, then a stable short player identifier. Records include the full
submitted name, shared player identifier, canonical linked IPs, available balance,
completed rounds, total wagered and total returned. Per-game player/round counts
cover every qualifying player before slicing the five leaders. In-progress
Blackjack and Poker hands count only once they settle.

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
| Plinko | Choose 8, 12 or 16 rows and Low/Medium/High risk. Unbiased left/right bits define the path; their sum determines the slot. Fixed symmetric v2/v3 tables determine payouts. 16-row High has 1000× edge payouts, 12-row High 170×, and 8-row High 29×. |
| Blackjack | Six standard decks, freshly sampled without replacement each hand. Hit, Stand, or Double on the first two cards. Dealer checks for a natural before player decisions and stands on hard/soft 17. Naturals pay 3:2 profit, other wins 1:1, and pushes return the stake. No split, insurance or surrender. |
| Limbo | Choose a target from 1.01× to 1,000,000× in 0.01 steps. Reach it or higher to win. A win returns the wager times the chosen target, rounded down; a higher result does not raise the payout. |
| Coinflip | Pick Heads or Tails, each with a 50% chance. A win returns floor(stake×198/100); a loss returns 0. |
| Poker | Single-player five-card draw Video Poker. One 52-card deck, no jokers. Hold any of the five initial cards, then draw replacements once. The 9/6 Jacks or Better paytable below applies at every wager size. |

Multipliers include the wager; whole-point payouts round down. Keno tables target
99% before multiplier/payout rounding. Plinko's fixed table expectation is shown
for the selected risk and rows and can differ slightly from 99%. Blackjack and Poker have
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

## Limbo and Coinflip probabilities

For Limbo, let `N = 2^32` and draw an unbiased integer `r` in `[0,N−1]`.
The result in hundredths is `max(100, floor(99×N/(N−r)))`. The target `T` is
an integer from 101 to 100,000,000 hundredths. A win occurs at result ≥ T,
with exact probability `floor(99×N/T)/N`, and returns `floor(wager×T/100)`.
This gives an expected return at most 99% before whole-point payout rounding.
The UI displays the win probability as a rounded percentage. There is no cash-out
step or timing advantage; animation displays an already settled result.

Coinflip takes one unbiased bit: 0 means Heads, 1 means Tails. Each side has
probability 1/2. A correct selection returns `floor(wager×198/100)`. Before
whole-point rounding, the expected return is 99%. A one-point winning wager
returns one point, so very small bets have a lower effective expectation.

## Poker decisions and paytable

| Final five-card hand | Total return |
| --- | ---: |
| Royal flush | 800× |
| Straight flush | 50× |
| Four of a kind | 25× |
| Full house | 9× |
| Flush | 6× |
| Straight | 4× |
| Three of a kind | 3× |
| Two pair | 2× |
| Pair of jacks, queens, kings or aces | 1× |
| Any other hand | 0× |

Aces count high in A-K-Q-J-10 or low in A-2-3-4-5, without wrapping other
sequences. The royal pays 800× at every valid stake, with no special maximum-coin
condition. These are total returned points, including the original stake.
No fixed player RTP is advertised; choosing holds affects the expected return.

Deal reserves the stake and exposes only the first five cards. The server keeps
the seed and undealt cards private. Hold zero to five positions and Draw once.
Sampling continues from the same committed deck without replacement, so a discard
cannot return. Held cards stay in their original positions. The final receipt
records initial cards, sorted held positions, final cards, classification and payout.
The browser also checks its remembered initial cards and submitted hold decision.

Holds survive page refreshes when browser session storage is available. The hand
itself survives refreshes, restarts and admin grants using the existing JSON save.
An unfinished card hand must finish before that same wallet starts another game.
At the weekly boundary, a pending Poker hand keeps all five initial cards and
settles in the old week; then the usual new balance and standings apply.

## Poker byte format

Poker uses `{"variant":"jacks_or_better"}` with standard-deck card IDs 0–51.
Each ID is `suit×13 + rank−1`: suits spades, hearts, clubs, diamonds; ranks A=1
through K=13. At draw index i, choose j uniformly from i through 51, swap those
positions, and consume the card at i. Consume the first five cards for the deal.
At Draw, visit positions 0–4 in order, keeping held positions and consuming the
next sampled card for every replacement. Holds are not HMAC context inputs:
changing a decision never changes the underlying committed random sequence.

Coinflip options are `{"side":"heads"}` or `{"side":"tails"}`. Limbo uses
`{"target":200}` for 2.00×. The Limbo result multiplier is also in hundredths.
Poker multipliers use whole units; Coinflip, Keno and Plinko use 1/10,000 units.
All payout calculations use exact integer arithmetic.

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
This avoids modulo bias. Use the exact rules version on the receipt: v3 for new
wagers, or v1/v2 when verifying an earlier receipt.

Keno uses a partial Fisher–Yates shuffle of 1–40. Blackjack uses the same sampling
method on a six-deck shoe of 312 unique IDs: `deck×52 + suit×13 + rank−1`. Suits are
spades/hearts/clubs/diamonds, ranks A=1 through K=13. Initial deal order is player,
dealer, player, dealer. `blackjack.py` replays the recorded legal actions on that
fixed sequence; actions do not change or reshuffle the committed shoe.

The seed is revealed when a round finishes. The browser checks the earlier hash,
inputs, result and payout using its separate Web Crypto/BigInt implementation.
Blackjack verification reproduces the recorded action history. Poker verification
replays the initial deal and held-card draw before evaluating the final hand.
New v3 and earlier v2 receipts use the same fixed Plinko tables; v1 receipts use their original
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
from its `DO-Connecting-IP` header for private admin tracking. Missing forwarding
never blocks Gaming. On a directly exposed/local server leave it
at 0: do not trust visitor-supplied proxy headers. Use one application instance.

The requested JSON-only design remains. **App Platform local files can disappear
on redeploy/container replacement.** Preserve current `data/state.json`, private
recovery data and cookie-signing secrets. Export the latest full private backup
before deployment. Recovery restores only what was saved in that backup; neither
a recovery code nor the user's IP contains their balance. New database or service
setup is not required by this update.

`wager_backend.py` loads the wallet, fairness engine, Blackjack/Poker rules, templates
and static assets automatically. The source connection clients remain separate.
Blackjack has no Shuffle integration or real-money settlement path.

## Cryptographic references

- Python HMAC implementation: https://docs.python.org/3/library/hmac.html
- W3C Web Cryptography HMAC and SHA-256: https://www.w3.org/TR/WebCryptoAPI/

The independent browser verifier matches the backend reference receipts in
`tests/fairness_vectors.json`, `tests/fairness_v2_vectors.json` and
`tests/fairness_v3_vectors.json`. Old fixtures stay unchanged when v3 is added.
