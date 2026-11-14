# DigitalOcean App Platform — RedHunllef V18

## Required component settings

```text
Source Directory: /
Build Command:    leave blank
Run Command:      python wager_backend.py
HTTP Port:        8080
Health Check:     /healthz
Instances:        1
RH_SPACES_ENABLE: 0
```

The Python buildpack installs the root `requirements.txt`; do not add a second
manual pip-install command.

Before deployment, export the current private recovery checkpoint. After a
forced rebuild, verify `/healthz`, sign in, open EmpireDrop Prizes, and confirm
that the public pool and all ten prize values are visible on the public board.

This private package contains production credentials and state. Keep the
repository private.
