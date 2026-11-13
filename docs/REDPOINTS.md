# RedPoints Gaming

RedPoints wallets are identified by a signed browser identity and stored in JSON. V12 owns community names and recovery directly inside Gaming.

## Player profile

- Confirm or edit the community name on `/gaming`.
- Generate a recovery code from the Gaming profile area.
- Store the code privately; the server stores only its digest.
- Recovering a profile rebinds the browser to the original wallet identity.

## Migration

Existing wallet identifiers, names, balances, receipts, fairness records, and active game hands remain authoritative. V12 accepts the previous signed identity during transition and then issues `rh_player`. Retired profile data is removed after a backup and only contributes a recovery digest when a unique exact name match is safe.

## Administration

Admin → Games & RedPoints shows player count, leaders, receipts, and the controlled grant-all action. It no longer includes unrelated community-game state.
