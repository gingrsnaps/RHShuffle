# EmpireDrop race deployment — V18

V18 keeps the official EmpireDrop partner-race integration and fixes the payout
publication action. The public leaderboard uses the selected official race slug
and both API-key headers. Locally advertised Top 10 prizes are independent from
EmpireDrop payments.

After deployment:

1. Open Admin → Leaderboards → EmpireDrop → Prizes.
2. Confirm the public pool is `$2,000.00` and the status is **Published**.
3. Change a value only if needed, then click **Save & publish** once.
4. Confirm the public Top 10 displays the rank-specific values.

The browser now records the clicked publish action before disabling the buttons,
so the request cannot silently fall back to a draft save.
