# RedHunllef V20

V20 replaces the separate square mobile cards for positions 4–15 and 4–10 with one compact grouped standings list. It also applies the same visual language to History, administrator ranking tables and operational logs.

## Public mobile standings

- One rounded outer panel
- Subtle row separators
- Compact horizontal rank, player, wager and prize layout
- Narrow-phone two-line fallback
- First place appears first, with second and third side by side on normal phones
- Neutral unpublished-prize styling
- No provider or wager-calculation changes

## Performance

The existing JavaScript continues updating rows in place. V20 removes per-row shadows, clipping layers and gaps, reducing mobile paint and layout work.

## Administrator and History

History and administrator result tables now use grouped lists on phones. Operational events use one timeline panel with separators instead of a stack of rounded cards.
