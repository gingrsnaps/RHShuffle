# Community comfort update

Approved scope: suggestions 2–9. Excluded: achievement-progress redesign and
external checkpoint storage. Unlimited daily/weekly hits and the 30-second cooldown
are unchanged. `boss_progress.badges()` is unchanged from the preceding release.

| Area | Implementation |
| --- | --- |
| Identity | Existing cookie key retained during recovery; signed random recovery bearer code, saved digest, CSRF-protected POSTs, no code in URLs/logs/public feeds. |
| Households | Explicit admin allowance on a salted connection identifier; default one claim, per-player cooldown for approved households. |
| Activity | Bounded minute buckets for approximate pace; bounded rolling distinct-player set for a cosmetic rally. |
| Admin history | At most 100 actor/time/before/after entries, committed with the successful game edit. |
| UI | Stable keyed lists, preserved form drafts, remembered style, safe text rendering, compact totals, exact details, reduced-motion styling. |
| Source freshness | Success time is separate from rows/content-change time; existing automatic 60-second jobs remain. |
| Abuse | At most 4,000 short-lived request buckets and 50 temporary flags. Eligible hits and receipt retries are not throttled. No automatic bans. |
| Saves | Atomic UTF-8 JSON, OS file lock, flushed replacement, cached reads; prior local save imported without overwriting it. |

The public page remains focused on the game. Recovery controls and exact totals
are collapsed; detailed host controls stay in the authenticated admin panel.

There is no new runtime dependency. Optional browser-development checks use Node,
but deploying and running the app requires only the existing Python requirements.
