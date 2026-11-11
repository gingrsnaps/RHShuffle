# EmpireDrop public username consistency — 2026-11-11

## What was wrong

The official EmpireDrop race API **anonymizes the username before sending it**. Some returned names start with two readable characters (`Re********tie`), but others start with one followed by a provider mask (`s********z`). Our previous `mask_public_username()` simply used the first two source characters and appended six `*` characters. When the source's second character was already `*`, the website displayed seven consecutive asterisks (`s*******`), which did not look like Shuffle's consistent two-character/six-asterisk layout.

## Fix

- `empiredrop_features.py`: Render **two prefix slots followed by exactly six asterisks**. A second character that EmpireDrop has already obscured becomes `•` rather than a seventh star. Examples: `Re********tie` → `Re******`; `s********z` → `s•******`; `r******g` → `r•******`; a single visible letter (`A`) → `A•******`.
- Do **not** search for visible letters at the end of a provider-masked name, invent missing letters, or reveal Steam IDs. When the second letter is not supplied, **it cannot be recovered**.
- `templates/index.html`: Add a short explanation of the `•` placeholder to the existing public leaderboard footer.
- The correction is used by both `EmpireDropBoard.public()` and `EmpireDropBoard.public_history()` automatically; the initial server-rendered HTML and subsequent JavaScript live refreshes both receive the corrected display names. Admin continues to see the raw, provider-anonymized usernames and stable public IDs.
- `tests/test_empiredrop_qol.py`: Test all 10 patterns reported in the screenshot, second-character redaction, idempotency, initial public projection, admin names, saved-history projection, and absence of public IDs. Existing frontend, ranking and payout behavior is unchanged.

## Deployment

1. Back up **current** live state before replacing an App Platform instance; ZIP snapshots are not necessarily current, and App Platform's local filesystem is ephemeral.
2. Extract the private ZIP into a **private** repository's source root. Never commit the ZIP itself or make the bundled production keys public.
3. DigitalOcean App Platform: source directory `/`, blank build command, run command `python wager_backend.py`, port 8080, health check `/healthz`.
4. Redeploy and reload the public EmpireDrop tab; verify ranks remain the same and names now have exactly two prefix slots and six trailing stars.
5. No change to your working API credentials, race slug, approved payout schedule, Shuffle worker or games is needed for this display-only fix.

## Limitations

No authenticated live API request or full Flask startup was performed in the packaging environment. This corrects the tested server-side rendering projection; it does not cause EmpireDrop to reveal previously hidden names. This release preserves unencrypted live credentials in server-only files at the user's request.
