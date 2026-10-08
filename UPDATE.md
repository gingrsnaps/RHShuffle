# Install the complete 2026.10.08 update

The ZIP contains the entire configured application, including all modules,
providers, original logos, eight RedPoints games, boss fight and admin dashboard.

Follow the update instructions in README.md. Preserve your existing data folder,
private settings, signing key and newer recovery seed. The bundled private files
are the original fresh-install configuration, not a replacement for changes you
made on your deployed server. Save a private recovery export before redeploying
on App Platform. Container replacement loses local files.

Install requirements, then run only `python wager_backend.py`.
The optional `python wager_backend.py --check` verifies the complete release.

The older combined FULL_CODE_BLOCKS.md and MANIFEST.json are not used by this
release. Current source is in its own files, and BUILD_MANIFEST.json describes it.
