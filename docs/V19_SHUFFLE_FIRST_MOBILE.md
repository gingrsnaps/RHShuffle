# RedHunllef V19

V19 makes Shuffle the deterministic default for `/`, retains `/?provider=empiredrop` deep links, removes permanent provider selection from localStorage, and adds mobile-first layouts for public leaderboards, History, Gaming, calendars, prizes, players, and logs.

## Provider rules
- `/` always opens Shuffle.
- `/?provider=empiredrop` opens EmpireDrop.
- Switching tabs updates the URL without reloading.
- Browser storage cannot override the URL.

## Mobile rules
- One active provider card is shown on phones.
- Podiums display 1st, 2nd, 3rd.
- Public and History tables become readable result cards.
- Admin tables become expandable-style cards without horizontal scrolling.
- Calendars stack and save bars respect safe areas.
- Prize grids use two columns, then one on narrow phones.
- Gaming cards and dialogs use touch-sized controls.
