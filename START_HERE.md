# Start here — RedHunllef V17

V17 restores the less-square Shuffle-style race timer cards for both Shuffle and
EmpireDrop while retaining all V16 functionality.

Run with:

```bash
python wager_backend.py
```

DigitalOcean App Platform:

- Build command: blank
- Run command: `python wager_backend.py`
- Port: `8080`
- Health check: `/healthz`
- `RH_SPACES_ENABLE=0` unless Spaces is intentionally configured
