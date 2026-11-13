# EmpireDrop Integration Changelog

The integration now follows Partner Public API v2.0.1:

- Production host `https://api.empiredrop.com`.
- Dual `X-Public-Key` and `X-Private-Key` authentication.
- Running-race discovery through `/api/v1/affiliate-partner/races`.
- Race detail and standings through `/api/v1/affiliate-partner/races/{slug}`.
- Top 10 display, official ranks and ties, provider cache timing, and amount-unit validation.
- Consistent public masking while preserving provider-anonymized names and public IDs in Admin.
- Independent local payouts with draft and publication states.

V12 adds a dedicated payout revision, atomic verification, and public-projection confirmation.
