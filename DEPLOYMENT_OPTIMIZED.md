# V14 FastDeploy package

The FastDeploy archive contains every executable Python module, template, static asset, root deployment marker, private configuration file, and the bundled JSON snapshot. It excludes tests, screenshots, large source references, historical documentation, caches, and Git metadata.

DigitalOcean installs the root `requirements.txt`. Leave the custom Build Command blank and use `python wager_backend.py` as the Run Command.

Keep `RH_SPACES_ENABLE=0` unless the optional Spaces mirror is intentionally configured with boto3. The normal local-JSON deployment does not require boto3 or botocore.
