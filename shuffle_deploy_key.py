"""PRIVATE REPOSITORY ONLY. Server-side Shuffle credential fallback.

Used only when the private JSON file is ignored by Git and no encrypted
SHUFFLE_API_KEY environment variable is set. Never import in public scripts.
Prefer encrypted App Platform environment variables for future deployments.
"""

SHUFFLE_BUNDLED_KEY = 'f45f746d-b021-494d-b9b6-b47628ee5cc9'
