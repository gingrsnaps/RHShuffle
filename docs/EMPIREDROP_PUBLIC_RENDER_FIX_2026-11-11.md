# EmpireDrop public leaderboard: all returned positions — November 11, 2026

## Symptom and root cause

Admin correctly displayed 10 EmpireDrop player names, ranks and wager totals, while the public page displayed only position 1. The client renderer in `static/empiredrop.js` referenced `const configured` and `const rewards` in a prize expression **before their declaration below the rendering loop**. When an unannounced prize was represented as `—`, JavaScript raised `ReferenceError: Cannot access 'configured' before initialization`. The exception terminated the loop after writing the first player's name and wager. The previous fake-DOM test never provided prize elements, so it did not exercise the failing branch.

This was a presentation defect; there was no evidence of a failed API pull in the screenshots.

## What changed

1. `static/empiredrop.js` initializes `rewards` and `configured` **before** looping over 15 display positions. All prizes are rendered after reading the server's validated independent EmpireDrop payout configuration.
2. Rendering maps the API's ordered `rows[]` by **array position** and displays the true provider `rank` independently, preserving tied rank numbers.
3. Added a simple count/status sentence. If `race_meta.ranks_limit` is below 15, unavailable positions say *Not reported by EmpireDrop*, rather than suggesting there are vacant positions. No missing names are fabricated.
4. `templates/index.html` now **server-renders** public, masked EmpireDrop names, wager amounts and configured payouts into all 15 positions on initial page load. This is resilience against future JavaScript exceptions; live updates continue through the existing `/public-state` feed. Jinja auto-escapes rendered player names.
5. `tests/test_empiredrop_frontend.cjs` covers ten returned rows with payouts disabled (the exact original failure), fifteen returned rows with payouts enabled, provider ties, mid-race updates, and empty results.
6. `tests/test_empiredrop_public_ssr.py` verifies first-paint HTML shows all ten/fifteen rows, preserves ties, and HTML-escapes names.
7. No change to Shuffle, EmpireDrop API authentication, race slug selection, wager calculations, local payout allocations, games, Community Boss, or the user's existing JSON settings/state. Production source files remain at the ZIP root for DigitalOcean App Platform.

## Provider limitation

EmpireDrop's official race API exposes **at most `race.ranks_limit`** players. The user's current Admin screenshot shows 10 positions. After this update the public page should display all 10. Positions 11–15 cannot be populated without the provider increasing the race's ranks limit; the website must not invent them. The same logic also supports races where the API supplies 15 positions.

## Post-deployment checklist

- Back up the live state and accounts **from the deployed site** before redeploying. The bundled `data/state.json` is an older snapshot; App Platform's container-local storage is not durable.
- Extract the ZIP and commit its **contents at repository root** to a private Git repository. `requirements.txt` and `wager_backend.py` must sit directly in the source directory.
- Keep App Platform Build Command blank, Run Command `python wager_backend.py`, HTTP Port `8080`, and health check `/healthz`.
- Reload the public page. Hard-refresh if your browser held a cached asset; the release updates the asset version automatically.
- Select EmpireDrop, confirm that every returned player (currently 10) is visible in the public standings, and compare amounts with Admin. Provider-masked names will show only their first two visible characters plus six asterisks.
- Check Admin → EmpireDrop and Activity & Logs for any separate API errors. Do **not** change a working race slug just to fix display rendering.

## Validation and limits

Offline Python provider/contract/admin tests and the Node fake-DOM browser tests must pass. A real authenticated request from DigitalOcean is not part of this build and cannot be guaranteed by the tests. The container used for release preparation does not have Flask and Waitress installed, so a full web-service startup was not executed.

## Security

As requested previously, both ZIPs preserve the original server-only production keys in `private/settings.json` and fallback modules. Do not place either archive in a public repository or share publicly. No keys or unmasked Shuffle usernames were added to the public HTML, CSS or JavaScript.
