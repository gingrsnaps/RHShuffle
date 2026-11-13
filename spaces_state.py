"""Optional one-writer DigitalOcean Spaces mirror for the JSON state document.

Disabled by default. When enabled, the remote `current.json` becomes authoritative
on boot; writes first upload an immutable revision checkpoint and then `current`.
This is a *single-writer* protocol, not a distributed database: run one App
Platform instance and avoid simultaneous old/new writers during deployments.
Private credentials must be provided as encrypted environment variables.
"""
import hashlib
import json
import os
import tempfile
from pathlib import Path
import re
import time


class SpacesError(RuntimeError):
    """Operational error that deliberately contains no secret settings."""


class SpacesMirror:
    def __init__(self, *, bucket, endpoint, region, prefix, key_id, secret, client=None):
        if not bucket or not endpoint.startswith('https://') or not key_id or not secret:
            raise SpacesError('Spaces mirror needs HTTPS endpoint, bucket and access keys.')
        if not re.fullmatch(r'[A-Za-z0-9/_-]{1,120}', prefix):
            raise SpacesError('Spaces mirror prefix must contain only safe path characters.')
        self.bucket, self.prefix = bucket, prefix.rstrip('/')
        if client is None:
            try:
                import boto3
                from botocore.config import Config as BotoConfig
            except ImportError:
                raise SpacesError('Install requirements-spaces.txt to enable durable Spaces storage.') from None
            client = boto3.client('s3', region_name=region, endpoint_url=endpoint,
                                  aws_access_key_id=key_id, aws_secret_access_key=secret,
                                  config=BotoConfig(retries={'max_attempts': 3, 'mode': 'standard'},
                                                    connect_timeout=5, read_timeout=12))
        self.client = client
        self.last_verified = 0

    @classmethod
    def from_environment(cls, state_key):
        if os.getenv('RH_SPACES_ENABLE', '').strip().lower() not in {'1', 'true'}:
            return None
        prefix = os.getenv('RH_SPACES_PREFIX', f'redhunllef/{state_key}')
        return cls(bucket=os.getenv('RH_SPACES_BUCKET', ''),
                   endpoint=os.getenv('RH_SPACES_ENDPOINT', ''),
                   region=os.getenv('RH_SPACES_REGION', 'nyc3'),
                   prefix=prefix, key_id=os.getenv('RH_SPACES_KEY_ID', ''),
                   secret=os.getenv('RH_SPACES_SECRET', ''))

    def _key(self, suffix):
        return self.prefix + '/' + suffix

    def fetch(self):
        """Return None only for a documented missing object (not for network errors)."""
        try:
            response = self.client.get_object(Bucket=self.bucket, Key=self._key('current.json'))
            payload = response['Body'].read()
            state = json.loads(payload)
            if not isinstance(state, dict) or state.get('format') != 1 or not isinstance(state.get('admin'), dict):
                raise SpacesError('Remote state is invalid; local data was not overwritten.')
            self.last_verified = int(time.time())
            return state
        except SpacesError:
            raise
        except Exception as exc:
            code = getattr(exc, 'response', {}).get('Error', {}).get('Code', '')
            if code in ('NoSuchKey', '404', 'NotFound'):
                return None
            raise SpacesError('Could not read the authoritative Spaces state; refusing to use a stale local snapshot.') from None

    def prepare(self, local_path, *, state_key, bootstrap=False):
        """Hydrate from authoritative remote state before ordinary store bootstrap."""
        remote = self.fetch()
        if remote is None:
            if not bootstrap:
                raise SpacesError('Spaces has no current state. Restore the latest live backup first or explicitly bootstrap a verified local state.')
            if not local_path.is_file():
                raise SpacesError('Cannot bootstrap Spaces without an existing verified local state file.')
            local = json.loads(local_path.read_text(encoding='utf-8'))
            if not isinstance(local, dict) or local.get('format') != 1 or local.get('key') != state_key:
                raise SpacesError('Local state is not a valid matching account snapshot.')
            self.persist(local, expected=None)
            return
        if remote.get('key') != state_key:
            raise SpacesError('Spaces state key does not match the configured website.')
        if local_path.is_file():
            local = json.loads(local_path.read_text(encoding='utf-8'))
            if int(local.get('_mirror_sequence', 0)) > int(remote.get('_mirror_sequence', 0)):
                raise SpacesError('Local state is newer than remote; stop and reconcile before deploying.')
        # Do not depend on the web stack for recovery; hydrate atomically.
        local_path = Path(local_path)
        local_path.parent.mkdir(parents=True, exist_ok=True)
        handle, tmp_name = tempfile.mkstemp(prefix=local_path.name+'.', suffix='.tmp', dir=local_path.parent)
        try:
            with os.fdopen(handle,'w',encoding='utf-8') as output:
                json.dump(remote,output,ensure_ascii=False,allow_nan=False)
                output.flush(); os.fsync(output.fileno())
            os.replace(tmp_name,local_path)
        finally:
            if os.path.exists(tmp_name): os.unlink(tmp_name)

    def persist(self, value, *, expected):
        """Check the prior revision, then write a versioned snapshot and current.

        Does not support concurrent independent writers. Run exactly one instance
        and coordinate deployment cutovers. A network/upload failure aborts the
        local transaction, rather than falsely reporting that data was saved.
        """
        previous = self.fetch()
        if expected is None:
            if previous is not None:
                raise SpacesError('Remote state already exists; refusing a bootstrap overwrite.')
        elif previous is None or previous != expected:
            raise SpacesError('Remote state changed; refusing to overwrite a newer revision.')
        blob = json.dumps(value, ensure_ascii=False, separators=(',', ':'), allow_nan=False).encode('utf-8')
        digest = hashlib.sha256(blob).hexdigest()[:16]
        seq = int(value.get('_mirror_sequence', 0))
        checkpoint = self._key(f'snapshots/{seq:012d}-{time.time_ns()}-{digest}.json')
        try:
            self.client.put_object(Bucket=self.bucket, Key=checkpoint, Body=blob, ContentType='application/json')
            self.client.put_object(Bucket=self.bucket, Key=self._key('current.json'),
                                   Body=blob, ContentType='application/json')
            self.last_verified = int(time.time())
        except Exception:
            raise SpacesError('Spaces state write failed. No local commit was published; retry when storage is reachable.') from None
