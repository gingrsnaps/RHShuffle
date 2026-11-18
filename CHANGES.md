# V21 changes

- Updated Shuffle window to Nov 17–24, 2026 at 6 PM Eastern.
- Updated EmpireDrop website window to Oct 27–Nov 28, 2026 at 6 PM Eastern.
- Updated bundled state, first-run seed, and Shuffle defaults together.
- Added post-save schedule read-back verification for Shuffle and EmpireDrop.
- Preserved V20 mobile layout, provider integrations, payouts, Gaming, and Admin behavior.

## V22

- Added atomic, versioned Shuffle Top 15 snapshots with explicit 1–15 public rendering.
- Added brief rank-movement indicators, backend-driven next-check timing, and clearer source funnel metrics.
- Manual refresh joins an in-flight provider check; verified historical weeks freeze until explicitly rechecked.
- Public ETags now follow actual public content rather than moving provider timestamps.

## V23

- Placement movement indicators now use a server event timestamp and remain visible for 30 seconds without restarting on repeated polls.
- EmpireDrop receives the same server-side movement metadata and display behavior as Shuffle.
- Public state checks run every 15 seconds with conditional ETags while external provider pulls keep their existing worker cadence.
- Public responses include a runtime id and monotonic snapshot sequence; older same-runtime responses are ignored by the browser.
- Countdown clocks synchronize to fractional server time and recalculate from absolute race timestamps instead of decrementing counters.
- Desktop countdown CSS can no longer truncate valid seconds into an ellipsis; numeric typography is fixed-width/tabular.
- Visibility, focus and back-forward-cache recovery immediately resynchronize clocks and state.
- Strong public ETags now represent the complete non-clock public payload, including freshness information.
