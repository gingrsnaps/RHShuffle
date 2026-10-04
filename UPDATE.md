# RedPoints gaming update — 2026.10.04-redpoints-arcade2

Blackjack is a RedPoints game. It shares the existing RedPoints wallet with Dice, Keno and Plinko. It does not use Shuffle funds, credentials, wagers, or casino accounts.

## Apply the update

1. Save your current private recovery backup from Admin → Settings before redeploying on DigitalOcean. The existing JSON storage design is unchanged: App Platform local files can be replaced during deployment. Preserve the saved state/recovery data; this update contains no seed files or replacement balances.
2. Extract the archive into your existing project, keeping the `static/`, `templates/`, and `tests/` folders. Replace all matching files together. Add the new `blackjack.py` and `static/admin-gaming.js`; both are included. This is a patch for the existing project, not a standalone application.
3. On **DigitalOcean App Platform**, set the runtime environment variable `TRUST_APP_PLATFORM=1`. App Platform provides the visitor address through `DO-Connecting-IP`. Without that setting, visitors may appear to come from a shared ingress address. For a directly exposed/local Python server, leave this setting at `0` so visitors cannot supply a fake trusted header. Official reference: https://docs.digitalocean.com/support/where-can-i-find-the-client-ip-address-of-a-request-connecting-to-my-app/
4. Restart/redeploy and reload open Gaming pages. The launch command stays `python wager_backend.py`. No new dependencies, database, background service, or second launch command is required. The existing build command remains `pip install -r requirements.txt`.

5. Open **`/admin/gaming`**, also linked as **Gaming top 5** in the admin header. Confirm the installed release is **2026.10.04-redpoints-arcade2**. The complete ZIP previously lagged this cumulative patch; both downloads now contain the same four-game implementation. On a current installation, use this patch to preserve private configuration and saved state.

The dedicated dashboard shows all four lists before JavaScript starts. Each game displays its actual total players and completed rounds, counted before selecting the top five. Empty panels explain that only completed RedPoints rounds in this week's saved state count. This update cannot recreate records lost with a replaced container unless you restore a saved recovery export. Private names and IPs disappear if the admin session expires; late responses cannot put them back. A mixed-version response requests a page reload instead of claiming fresh statistics.

## Changes

- **One shared player and wallet:** the same signed player, name, balance and weekly IP bindings apply to all four games. Refreshes, name edits and switching games do not create another allowance. An existing signed player can move to an unclaimed IP and keep their wallet. A new browser on an already-used IP must restore the original player using their existing recovery code; IP alone never grants access to someone else's balance. People sharing a public IP cannot create separate gaming wallets during that race week. This does not change the boss-fight household settings.
- **Existing data stays intact:** existing balances, seeds, receipts and three-game statistics are preserved. Blackjack statistics are added at zero. New IP bindings are claimed when an existing named player next visits. Conflicting old wallets are retained, not merged or deleted.
- **Plinko:** fixed symmetric payout tables. Maximum High-risk multiplier: 29× with 8 rows, 170× with 12 rows, **1000× with 16 rows**. The shown multiplier is the actual server settlement multiplier. The previous precise path animation is retained: a single animation loop supports overlapping balls, follows the committed left/right path and lands in its correct slot. A blocked button shows its reason instead of an indefinite waiting cursor.
- **Keno:** Quick pick selects **10 distinct numbers**. Manual selection remains 1–10 numbers; the draw contains ten distinct numbers. The payout table follows the actual selection count.
- **Dice:** the large board bar is now a real draggable control. Its threshold, the Win Chance slider, percentage label, target and payout stay synchronized. Roll Over correctly uses the inverse threshold. Mouse, touch, keyboard and wheel controls are supported.
- **Blackjack:** a fresh six-deck shoe per hand, sampled without replacement. Hit, Stand, and Double on the first two cards. Dealer checks for a natural before player actions and stands on all 17s. Naturals pay 3:2 profit, ordinary wins 1:1, and pushes return the stake. No splits, insurance, surrender or side bets. Returns are whole RedPoints, rounded down. A Double counts the full doubled stake in the ledger and rankings. The wager is reserved while a hand is active; another game cannot spend it. Reloads restore the hand. At the weekly boundary, an unfinished hand automatically stands and settles under the old week before the new allowance is granted.
- **Actual admin rankings:** Admin → Overview and Admin → Gaming show the top five for **each of the four games**, ordered by net winnings (returned minus wagered). Each entry includes the full submitted name, player identifier, total wagered, total returned, completed rounds, available balance and linked IP addresses. Empty rankings say there are no completed rounds; no placeholder players or simulated earnings are added. Active Blackjack hands count only when settled. Gaming statistics refresh every five seconds, separately from the unchanged 60-second provider refresh, with a manual refresh button too.
- **Private IP information:** canonical addresses are retained in private JSON state for the current race week's admin view, alongside keyed ownership digests. Public wallet endpoints and receipts do not list IPs or other players' names. Admin authentication protects the rankings and addresses. Player names remain self-reported and are not claimed to verify a Shuffle account.
- **Versioned fairness:** new rounds use `redpoints-v2`; old `redpoints-v1` receipts still verify and old committed requests remain recoverable without another debit. The server and browser independently reproduce outcomes and exact integer payouts. Blackjack reveals its seed only once the hand is complete, then the verifier replays the recorded actions and cards. No fixed Blackjack RTP is advertised because results depend on decisions; admin totals come from actual settled rounds.
- **Same weekly rules:** 100,000 starting RedPoints, Tuesday at 6 PM Eastern, including daylight saving changes. No daily/weekly play count limit and no fixed stake cap beyond available balance and exact-integer safety. Shuffle/Kick integration, admin accounts, race history, boss gameplay and uploads keep their existing behavior.

## Files

All runtime files below are complete replacement files, not snippets:

- `wager_backend.py`: IP-aware wallet calls, Blackjack action API, conditional admin stats response.
- `gaming.py`: shared IP binding, save migration, reserved Blackjack stakes, idempotent moves, actual rankings.
- `fairness.py`: versioned rules, Plinko payouts and Blackjack replay verification.
- `blackjack.py`: new deterministic six-deck rules engine.
- `static/fairness.js`: independent v1/v2 browser verifier, including Blackjack.
- `static/gaming.js`: draggable Dice, Quick pick 10, game recovery and Blackjack controls/cards.
- `static/gaming.css`: game controls, red card table, responsive admin rankings and cursor fixes.
- `static/app.js`: passes game rankings to the dedicated admin renderer.
- `static/admin-gaming.js`: new private five-second ranking refresh and manual refresh control.
- `templates/gaming.html`: four-game dashboard, game pages and shared-wallet notices.
- `templates/gaming_fairness.html`: published tables, card rules and versioned verification format.
- `templates/admin.html`: loads the gaming renderer on Overview and Gaming.
- `templates/admin_gaming.html`: four rankings, private IP information and refresh controls.

- `config.py`: distinct installed-release identifier and matching asset version.

The files in `tests/` update or add regression checks, synthetic fixtures and reference receipts. They do not run in production and are not separate launch scripts. Updated README, setup, file-structure and gaming documentation are included. No existing files need to be removed.

## Verification performed

- This revision: 37 targeted Python tests passed, covering shared wallets, migration, IP isolation, actual rankings/counts, authenticated routes, reserved stakes, Blackjack rules and rollover behavior.
- Six JavaScript tests passed: three independent verifier tests covering 47 earlier and 86 new reference receipts; three admin-renderer tests for all four lists, private-session expiry and mixed-release handling.
- Native Chromium: four lists rendered with five entries each and totals of seven players/seven completed rounds per game. Expired-session cleanup and late-response rejection passed. Synthetic data is used only by tests.
- A real Plinko submission verified its receipt and landed in the exact payout slot. The observed median frame interval was about 16–17 ms; device performance varies.
- Native Blackjack Deal, hidden hole card, reload/resume, Stand, receipt verification and shared wallet checks passed. Dice dragged to 73%, Keno selected ten distinct numbers, and a second browser on the same IP could not create or read another wallet.
- The prior patch's broader 203-Python/47-JavaScript and Chromium/Firefox checks are historical results, not a claim that those entire suites were rerun for this revision. Current evidence and limits are in `docs/VALIDATION.md`.

The live deployment and real upstream Shuffle/Kick availability have not been changed or tested against your accounts in this update.
