# Changes in 2026.10.08-community-polish6

1. Decoupled readiness from Shuffle freshness; temporary local-write probe.
2. Added the five-card admin health overview and private support-report copying.
3. Added bounded request, JSON copy/write and lock-wait measurements.
4. Added trace IDs to responses, JSON errors and server-error logs.
5. Made full recovery exports atomic across accounts, wallets, boss and history.
6. Added recovery preview comparisons and an overview checkpoint reminder.
7. Added automatic release completeness checks and an optional strict check.
8. Refined the red design, mobile header, game selector, focus and touch controls.
9. Added Available / In play / Last net wallet labels and explicit play phases.
10. Reduced recent-history clutter and preserved focus during unchanged polls.
11. Loaded Plinko rendering only on its page; preserved receipt-driven motion.
12. Prioritized homepage standings, clarified saved/final history and added boss
    health-phase shading without changing damage or cooldowns.
13. Distinguished admin funding adjustments from settled game winnings.
14. Added readiness/privacy/recovery tests, a 100-player concurrency check and
    native-browser experience/performance checks.

Original accounts, credentials, logos, wager weighting and game/fairness rules are
retained. No SQL service, extra worker, launch script or play-count quota was added.
The full package contains actual source files; it is not a patch-only archive.

See docs/VALIDATION.md for evidence. Local App Platform files remain temporary;
this update does not claim to provide durable external storage.
