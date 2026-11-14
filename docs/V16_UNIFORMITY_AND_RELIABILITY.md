# RedHunllef V16 — Uniform race summary and provider reliability

V16 is a focused reliability and presentation release built on V15. It does not
replace the working Shuffle, EmpireDrop, payout, Gaming, or JSON state models.

## Public race summary

Shuffle and EmpireDrop use the same `race-countdown` component, final CSS token,
line height, tabular numeral treatment, minimum card height, date-row height and
footer layout. Provider switching changes values, not typography or geometry.

Public operational text remains suppressed. Detailed request and source health
information stays in the protected Admin Control Center.

## EmpireDrop payout idempotency

The payout editor now includes a per-form submission ID. The server stores the
ID only after a verified change. Repeated browser submissions, double-clicks,
and retries of the same form return a no-change confirmation instead of writing
another revision or operational event. Submitting a schedule identical to the
current draft or publication also returns without writing.

The browser disables both payout buttons as soon as submission begins. The
existing atomic write, private backup, read-back check and public-projection
verification remain in place.

## Shuffle diagnostics and retry behavior

The provider client serializes active and history Shuffle calls through one
process lock. This prevents the current-race worker and completed-week worker
from issuing overlapping requests from the same instance.

Admin diagnostics retain a sanitized request fingerprint only:

- Method
- Endpoint kind
- Start and end Unix seconds
- Timestamp unit
- Query-key names

No API key, URL containing a key, response body, player data or provider message
is stored.

Repeated failures back off at 60, 120, 240 and 480 seconds. A successful check
immediately restores the normal interval. Existing verified standings remain
visible after a provider failure.

Data-quality events now distinguish ranked players, received source records,
accepted records and excluded records. Provider Overview cards also show a
rolling success/failure summary for the last 20 source checks.

## Visual acceptance

`tools/visual_acceptance_v16.py` checks desktop and mobile computed countdown
font size, line height and card height using Chromium or Chrome. The fixture is
`tests/fixtures/v16_countdown_uniformity.html`.

Some container environments cannot start Chromium because their system D-Bus or
browser sandbox is unavailable. In that case, run the tool on a development
machine or CI runner with Chromium installed.

## DigitalOcean

Use the root `requirements.txt`, leave Build Command blank, run
`python wager_backend.py`, and keep `RH_SPACES_ENABLE=0` unless a Spaces bucket
has intentionally been configured.
