# Update to 2026.10.05-redpoints-arcade4

This ZIP is the full configured application. Run only `python wager_backend.py`.

1. Save a copy of the current project. Export the latest private recovery file
   before any DigitalOcean container replacement.
2. Stop the current app and merge the new code into matching paths. Preserve
   `data/`, your current `private/`, settings, environment and player cookies.
   Bundled original seeds are for fresh installations, not replacement of newer saves.
3. Keep all root modules, especially `race_support.py`, `poker.py` and `baccarat.py`.
4. Run `python -m pip install -r requirements.txt`, then `python wager_backend.py`.
5. Reload the browser once. `/healthz` and admin release labels should show
   **2026.10.05-redpoints-arcade4**. Thereafter gameplay updates without page reloads.

Existing accounts, names, game statistics, pending hands and receipts migrate
in place. Startup restores available balances to 100,000 as previously requested.
Baccarat's new statistics begin at zero. No existing game history is rewritten.
The admin grant remains an additional 100,000 per saved wallet.

Game pages are shorter; payouts and fairness remain expandable. Baccarat uses
Player / Banker / Tie bets and v4 proofs, independently verified in the browser.
All old proofs remain supported. See `README.md`, `docs/REDPOINTS.md` and
`docs/VALIDATION.md` for rules, deployment, limits and measured checks.

DigitalOcean App Platform still has temporary local storage. The current manual
private recovery file is the checkpoint for a fresh container; this update adds
no database or other storage service. It cannot recover unsaved previous progress.

No further files must be removed. `manage_admin.py` from an old release is unused;
Python caches may be discarded. Keep the application modules, configuration and saves.
