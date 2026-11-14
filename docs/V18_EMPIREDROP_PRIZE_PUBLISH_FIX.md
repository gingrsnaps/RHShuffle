# RedHunllef V18 — EmpireDrop public prize publication fix

## Root cause

The EmpireDrop payout page disabled both submit buttons during the browser's
native `submit` event. Disabled controls are omitted from form serialization,
so clicking **Save & publish** could reach Flask without the button's
`save_mode=publish` value. The backend then used its safe default of `draft`.
That produced exactly the observed state: the private $2,000 draft was saved,
while the public prize schedule stayed disabled and the public leaderboard
continued to show **Not announced**.

## Fix

- The browser stores the clicked action in the hidden `save_mode_intent` field
  before disabling either button.
- The backend resolves `save_mode_intent` first and retains the submit button as
  a no-JavaScript fallback.
- Invalid actions remain rejected server-side.
- Existing atomic write, read-back, public-projection verification,
  idempotency, and revision checks remain enabled.
- The bundled private state and clean-install seed contain the administrator's
  published USD Top 10 schedule shown in the supplied screenshots:
  `$1,000, $450, $200, $125, $75, $50, $25, $25, $25, $25`.

## Public result

The EmpireDrop race summary now reports a `$2,000.00` public pool, and the ten
public ranking positions receive their configured local advertised prizes.
Provider standings and actual EmpireDrop payments remain independent from these
locally advertised amounts.
