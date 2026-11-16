# Start here — RedHunllef V20

Deploy the FastDeploy archive to DigitalOcean and keep the Full archive as the private development backup. Export the newest recovery checkpoint before replacing the running source.

DigitalOcean settings:

```text
Source Directory: /
Build Command: leave blank
Run Command: python wager_backend.py
HTTP Port: 8080
Health Check: /healthz
RH_SPACES_ENABLE: 0
```

V20 changes only presentation, responsive layout and release tests. Shuffle and EmpireDrop data paths remain the V19 implementations.
