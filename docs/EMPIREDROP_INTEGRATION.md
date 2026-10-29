# EmpireDrop integration — independent provider release

## Run and navigate

Run only `python wager_backend.py` after `python -m pip install -r requirements.txt`.

- Public site: `/` → **EmpireDrop · Top 15** or **Shuffle · Top 15**.
- Admin: `/admin?tab=empiredrop` for EmpireDrop, `/admin?tab=shuffle` for Shuffle.
- Official EmpireDrop referral URL: `https://empiredrop.com/c/red`. The *case-sensitive intended code* is `red`.
- Both supplied `pk_prod_...` and `sk_prod_...` keys are retained in `private/settings.json` (confidential).
- JSON-only persistence remains at `data/state.json`; no SQL instance or second launcher.

## What's corrected

1. **Keys and status:** Config searches environment variables, settings.json, integrations.json, and private/settings.json (in that order), reporting a masked last-four-character preview and source to authenticated administrators. A Superadmin can change keys in an atomic 0600-protected private file. Empty fields retain existing keys. The private key is never sent to browser code, public APIs, diagnostics or logs.
2. **Independent calendar:** EmpireDrop's default is Tuesday 18:00 to Tuesday 18:00 *America/New_York*, computed each week with DST. Its `/admin/empiredrop/schedule` action can save a custom interval. Shuffle's race dates, overrides, prizes and history are never read or changed by EmpireDrop.
3. **Independent worker:** EmpireDrop checks every 60 seconds; manual check requests have a 15-second rate limit. Its last successful timestamp, last attempt, queued/checking state and error category are separate. Queuing is not falsely called a successful check.
4. **Read-only non-destructive connection test:** Superadmin's `POST /admin/empiredrop/test` validates authenticated data but does not publish a leaderboard or alter a wager.
5. **Correct accounting:** Only configured wager fields count. Referral `red` is required per row unless the *provider* has confirmed code-scoped results. Aggregated per-player rows are deduplicated (maximum reported cumulative value); individual transaction rows can be summed only when they carry unique transaction identifiers. Do not confuse deposits, commission, net revenue or balance with wagers. Currencies and unit divisor are explicit.
6. **Pagination:** One complete page is the default. If an unexpected next-cursor appears, the entire result is rejected rather than displaying an incomplete Top 15. Only verified cursor pagination retrieves subsequent pages; bounded to 20 pages and 10,000 records.
7. **Safer HTTP:** Only HTTPS URLs under `empiredrop.com`, no credential-bearing URLs or querystrings, no redirect following, 20-second read timeout, 4 MB response cap, safe 401/403/429/error handling, and no raw provider bodies in logs.
8. **Cache safety:** Failure or configuration edits preserve the last **same-period** confirmed result, marked stale. A period change displays an empty new-period board without deleting the previous checkpoint. An API connection failure never overwrites Shuffle's data.
9. **Provider-specific public UI:** Switching to EmpireDrop changes the hero schedule/heading and hides Shuffle's prize pool. Both boards mask player names publicly; admin gets full names only when authenticated.

## Remaining external API prerequisite

**The provider's official authenticated wager API contract has not been verified.** Public EmpireDrop policy pages discuss affiliate attribution and Wager Share, but do not specify the wagering URL, authentication signature/headers, response schema or pagination. No endpoint has been guessed, and live ranking claims cannot be made. The connection is **disabled until** an administrator obtains the official provider contract and explicitly checks **I verified ...** in the admin panel. An endpoint that uses a cryptographic signature or OAuth instead of two header keys would require adapting `EmpireDropBoard.fetch` to that verified scheme before enabling it.

Ask EmpireDrop support for: official allowed API host/path, whether the supplied public/private pair authenticates as two HTTP headers or requires signing, timestamp parameters and units, referral `red` filtering, individual vs cumulative wager values, player IDs, pagination, currency, and rate limits.

Admin pages accept these parameters only after confirmation. A green connection test means parsing succeeds against the configured contract, **not** independent certification of provider numbers or its identity system.

## Testing and deployment

Quick deterministic provider tests (offline):

```bash
python -m unittest discover -s tests -p 'test_empiredrop_contract.py' -v
node --test tests/test_empiredrop_frontend.cjs
```

Full application regression suite (requires `requirements.txt` and Node's optional test dependencies):

```bash
python -m unittest discover -s tests -p 'test_*.py'
npm --prefix tests install --ignore-scripts
npm --prefix tests test
```

Before deploying to DigitalOcean App Platform: export a private recovery checkpoint and retain it outside the container, keep private settings out of public Git hosting, and run **one** App Platform instance. App Platform's local filesystem can be replaced on deploy; local JSON changes and credentials may disappear without a saved recovery. Once authenticated data is available, compare the Top 15 with the EmpireDrop affiliate dashboard for the same date range before advertising accuracy.

**Security:** The keys were provided in chat and intentionally bundled with this package. Rotate production secrets if possible and protect ZIPs, backups, and repository history.
