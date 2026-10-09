# Changes in 2026.10.08-community-clarity7

1. Restored the community boss above the homepage leaderboard, after the hero.
2. Changed all boss health labels/previews to remaining HP. Bar and percentage
   drain together; the combat engine and no-regeneration rule are retained.
3. Simplified the boss invitation and public update messages.
4. Reorganized the admin overview around race, boss, players and quick actions.
5. Grouped connections/history/performance inside expandable Diagnostics and
   consolidated routine connection warnings into one actionable summary.
6. Kept all eight Top 5 game lists visible, with full names and net winnings.
   Player IPs, balances, detailed totals and funding expand on demand.
7. Preserved expanded records and keyboard focus when rankings change, and
   skipped rebuilding unchanged rows. Removed duplicate minute-feed rankings.
8. Reused the five-second local gaming feed for the overview boss summary.
9. Split name and damage saves into guarded partial edits. Health and unrelated
   settings stay intact; existing combined-settings requests remain compatible.
10. Fixed fragment-only admin redirects: consecutive saves now reload confirmed
    values, current edit revisions and the correct success receipt.
11. Improved name/recovery links, initial Gaming confirmation text, attack states,
    unsaved upload detection, accessible feedback and mobile spacing.
12. Added regression coverage for partial-edit authorization, stale edits,
    conditional feeds, details/focus retention and real-browser repeated saves.

The complete package retains original private provider settings/account seed,
logos, single Python launch, all games/proofs and existing runtime-state format.
Keep newer deployed configuration and saved data when upgrading. See README.md
for App Platform recovery instructions and docs/VALIDATION.md for test limits.
