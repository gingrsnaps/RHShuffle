# RedHunllef V18

A single-process Python/Flask community wager-race and RedPoints application
with independent Shuffle Top 15 and EmpireDrop Top 10 leaderboards.

V18 fixes EmpireDrop public prize publication, retains the compact matching race
timer cards, and includes the confirmed ten-place USD payout schedule.

## Run

```bash
python -m pip install -r requirements.txt
python wager_backend.py
```

DigitalOcean App Platform should use a blank custom Build Command, run
`python wager_backend.py`, expose port `8080`, and check `/healthz`.

The private packages contain unencrypted credentials and state. Keep them
private and export a current recovery file before deployment.
