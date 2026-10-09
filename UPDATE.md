# Install the complete community-clarity7 update

This ZIP contains the entire configured application in redhunllef-rebuilt/.
It includes the providers, original logos/account seed, community boss, all eight
RedPoints games, admin dashboard, documentation and optional tests.

1. Save a private full recovery export from Admin → Settings before replacing an
   App Platform container. Follow README.md to carry that checkpoint into the new
   instance; App Platform's local filesystem is temporary.
2. Extract the full ZIP. Keep your existing data/ folder, private signing key,
   customized settings, changed credentials and newer recovery seed. The bundled
   original seed is for a fresh installation, not a replacement for recent data.
3. Install requirements: `python -m pip install -r requirements.txt`.
4. Start: `python wager_backend.py`.
5. Reload the browser. `/healthz` should report
   `2026.10.08-community-clarity7`. The boss card appears above standings, and
   admin Diagnostics are below daily controls. Test a name or damage save.

The same build/run commands work for the DigitalOcean Python Web Service. Keep
one instance. No SQL service, separate worker or second launch script is needed.
Optional completeness check: `python wager_backend.py --check`.

Old FULL_CODE_BLOCKS.md and MANIFEST.json are not used. Every source file is in
its own folder, and BUILD_MANIFEST.json describes this release.
