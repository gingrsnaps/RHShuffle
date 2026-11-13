# RedHunllef V13

A single-process Flask/Waitress website providing independent Shuffle Top 15 and EmpireDrop Top 10 wager leaderboards, RedPoints games, race history, and a protected administration panel.

## V13 repair

This release fixes the shared administrator rendering defect and the EmpireDrop payout publish failure. The exact causes and acceptance checks are documented in `docs/ADMIN_RELIABILITY_V13.md`.

## Run

```bash
python -m pip install -r requirements.txt
python wager_backend.py
```

DigitalOcean App Platform should use a blank Build Command and `python wager_backend.py` as the Run Command.

## Validate the release

```bash
python wager_backend.py --check
python -m unittest tests.test_navigation_v12 tests.test_admin_reliability_v13
```

## Race dates bundled in this private package

- Start: November 10, 2026 at 6:00 PM Eastern
- End: November 17, 2026 at 6:00 PM Eastern

## Security and storage

The private package contains production credentials and a saved JSON snapshot. Keep it private. App Platform container storage is not durable; export a current recovery file before every deployment or configure the optional Spaces mirror.
