# RedHunllef V14

A single-process Flask/Waitress website providing independent Shuffle Top 15 and EmpireDrop Top 10 wager leaderboards, public RedPoints community activity, race history, provably fair games, and a protected administration panel.

## V14 update

V14 makes the two public wager races visually uniform, removes provider-operation noise from visitor pages, and adds a privacy-safe public Gaming leaderboard. The working V13 administrator, EmpireDrop, DigitalOcean and payout repairs remain included.

Detailed implementation notes are in `docs/V14_PUBLIC_RACES_AND_GAMING.md`.

## Run

```bash
python -m pip install -r requirements.txt
python wager_backend.py
```

DigitalOcean App Platform should use a blank Build Command and `python wager_backend.py` as the Run Command.

## Validate

```bash
python wager_backend.py --check
PYTHONPATH=. python tests/test_v14_public_experience.py
```

The full acceptance suite additionally requires the packages from `requirements-dev.txt`.

## Bundled race window

- Start: November 10, 2026 at 6:00 PM Eastern
- End: November 17, 2026 at 6:00 PM Eastern

## Security and storage

The private package contains production credentials and a saved JSON snapshot. Keep it private. Public Gaming activity is an allowlisted projection and never returns wallet IDs, IPs, balances, receipts, seeds, recovery details or administrator grants.

App Platform container storage is not durable. Export a current recovery file before every deployment or configure the optional Spaces mirror. Keep `RH_SPACES_ENABLE=0` unless Spaces and its boto3 dependency are intentionally configured.
