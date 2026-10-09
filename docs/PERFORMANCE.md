# Performance — 2026.10.08-community-clarity7

These measurements are local development samples. They are not DigitalOcean
production measurements, a 100-user HTTP load test, or a service-level guarantee.
No additional monitoring service is required by the application.

## Loading sample

Chromium, 390px, CPU 4x slowdown, 150ms latency, 200KB/s download; one cold sample per page. Transfer sizes include local resource response overhead.
The browser collected Largest Contentful Paint and layout-shift entries during
the initial load/settle period. CLS below is the observed sum for that short load,
not a full real-user session-window assessment.

| Page | LCP | Observed layout shift | Resource bytes |
| --- | ---: | ---: | ---: |
| `/` | 1.112 s | 0.0000 | 112,902 |
| `/gaming` | 1.280 s | 0.0661 | 219,891 |
| `/gaming/dice` | 1.272 s | 0.0000 | 219,891 |
| `/play` | 1.200 s | 0.0108 | 169,989 |
| `/history` | 0.976 s | 0.0000 | 124,170 |

Product targets are LCP <= 2.5 seconds, INP <= 200 milliseconds, and CLS <= 0.1
at the 75th percentile of real visits, evaluated separately on desktop and mobile.
INP and real-user percentiles were not measured in this local sample. Use field
measurements from your actual deployment before claiming those targets are met.
Google's definitions: https://web.dev/articles/vitals

## Community ledger test

100 independent saved players shared one test IP. Sixteen threads issued 100
Coinflip wagers plus an identical retry of every wager (200 calls total).
All 100 settled once; all retries returned the original result. Every wallet and
receipt passed validation. This exercises the transaction engine directly;
Waitress ingress and internet latency are not included.

- Operation p50: 67.17 ms; p95: 96.73 ms.
- Recent JSON-copy p95: 3.97 ms.
- Recent atomic-save p95: 1.37 ms.
- Recent lock-wait p95: 92.50 ms.
- Sample state size: 160,739 bytes.

The measured cost under this burst was principally waiting for serialized
transactions. This release retains synchronous atomic commits and the existing
JSON format. It does not weaken save-before-acknowledgment or introduce a second
store based on a small sample. Larger saved histories and slower disks require
measurement on the real server; the new admin instruments expose that cost.

## Applied optimizations

- The admin minute feed no longer duplicates private gaming rankings.
- The existing five-second local feed also updates the overview boss; no extra timer.
- Unchanged Top 5 rows are retained. Changed rows keep expanded player records
  and keyboard focus; identities remain confined to protected admin responses.

- Plinko's canvas renderer is downloaded only by the Plinko page.
- Unchanged wallet receipts/statistics keep their existing DOM nodes, focus and
  expanded-history state.
- The recent-rounds preview limits visible rows while retaining all saved receipts.
- Existing ETags, immutable versioned assets and hidden-tab polling pauses remain.
- Health measurements are bounded in memory and do not generate state-file writes.
- Readiness writes only a tiny temporary probe, cached for 15 seconds.

The health panel reports recent 512-request and 256-store-operation windows.
Its request timing includes Flask processing, not browser/network/Waitress queue
time. Counts and samples reset when the process restarts.
