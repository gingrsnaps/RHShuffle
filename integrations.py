"""Official provider requests with bounded waits and secret-free failures."""
from datetime import datetime, timezone
from decimal import Decimal
from email.utils import parsedate_to_datetime
import json
import threading
import time
from urllib.parse import quote

import requests


class ProviderError(RuntimeError):
    def __init__(self, message, *, retry_after=0, status=None):
        super().__init__(message)
        self.retry_after, self.status = retry_after, status


def retry_delay(value):
    try:
        return max(0, int(value))
    except (ValueError, TypeError):
        try:
            stamp = parsedate_to_datetime(str(value))
            return max(0, int((stamp - datetime.now(timezone.utc)).total_seconds()))
        except (ValueError, TypeError, OverflowError):
            return 0


class Providers:
    def __init__(self, config):
        self.config, self.local = config, threading.local()
        self.token, self.token_until = "", 0

    def request(self, method, url, service, **kwargs):
        self.local.http_status = None
        # Each background thread owns its session; cookies/auth do not cross.
        if not hasattr(self.local, "session"):
            self.local.session = requests.Session()
            self.local.session.headers.update(Accept="application/json", **{"User-Agent":"RedHunllef/9"})
        try:
            # Redirects could leak a key in a URL or Authorization header. Only
            # the configured official endpoint is allowed to handle the request.
            with self.local.session.request(method, url, timeout=(5, 20), allow_redirects=False, stream=True, **kwargs) as response:
                code = response.status_code
                self.local.http_status = code
                if code == 429 or code >= 500:
                    raise ProviderError(f"{service} returned HTTP {code}; retrying automatically.",
                                        retry_after=retry_delay(response.headers.get("Retry-After")), status=code)
                if code in (401, 403):
                    raise ProviderError(f"{service} rejected the credentials or access permissions (HTTP {code}).", status=code)
                if not 200 <= code < 300:
                    message = "Shuffle rejected the saved race window; check its dates and affiliate configuration." if service == "Shuffle" and code == 400 else f"{service} returned HTTP {code}."
                    raise ProviderError(message, status=code)
                body = bytearray()
                deadline = time.monotonic() + 30
                for chunk in response.iter_content(65536):
                    body.extend(chunk)
                    if len(body) > 8 * 1024 * 1024 or time.monotonic() > deadline:
                        raise ProviderError(f"{service} response exceeded its size or time allowance.")
                try:
                    return json.loads(body, parse_float=Decimal)
                except (ValueError, UnicodeDecodeError):
                    raise ProviderError(f"{service} returned invalid JSON.") from None
        except requests.Timeout:
            raise ProviderError(f"{service} timed out; previous results are retained and checks continue.") from None
        except requests.RequestException:
            raise ProviderError(f"{service} could not be reached; check outbound connectivity.") from None

    def shuffle(self, site):
        key = self.config.credentials["shuffle_api_key"]
        if not key:
            raise ProviderError("Shuffle API key is missing. Add SHUFFLE_API_KEY and restart.")
        start, end = site["start_time"], min(site["end_time"], int(time.time()))
        if not 0 < start < end:
            raise ProviderError("The race does not have an active or completed date window.")
        data = self.request("GET", "https://affiliate.shuffle.com/" + self.config.endpoint + "/" + quote(key, safe=""),
                            "Shuffle", params={"startTime": start, "endTime": end})
        rows = data if isinstance(data, list) else next((data[k] for k in ("data", "results", "leaderboard", "users", "items")
                    if isinstance(data, dict) and isinstance(data.get(k), list)), None)
        if rows is None or len(rows) > 10000:
            raise ProviderError("Shuffle returned an unsupported leaderboard format or over 10,000 source records.")
        return rows

    def kick(self, site):
        keys = self.config.credentials
        if not keys["kick_client_id"] or not keys["kick_client_secret"]:
            raise ProviderError("Kick client credentials are missing. Configure them and restart.")
        for attempt in range(2):
            if attempt or not self.token or time.time() >= self.token_until:
                data = self.request("POST", "https://id.kick.com/oauth/token", "Kick authorization",
                                    data={"grant_type":"client_credentials", "client_id":keys["kick_client_id"], "client_secret":keys["kick_client_secret"]})
                if not isinstance(data, dict) or not isinstance(data.get("access_token"), str):
                    raise ProviderError("Kick did not return a valid app access token.")
                self.token = data["access_token"]
                try:
                    self.token_until = time.time() + max(1, int(data.get("expires_in", 3600)) - 60)
                except (TypeError, ValueError):
                    raise ProviderError("Kick returned an invalid token expiry.") from None
            try:
                data = self.request("GET", "https://api.kick.com/public/v1/channels", "Kick",
                                    params={"slug":site["kick_channel_slug"]}, headers={"Authorization":"Bearer " + self.token})
                break
            except ProviderError as exc:
                if exc.status != 401 or attempt:
                    raise
        rows = data.get("data") if isinstance(data, dict) else None
        channel = next((r for r in rows or [] if isinstance(r, dict) and str(r.get("slug", "")).casefold() == site["kick_channel_slug"].casefold()), None)
        if channel is None:
            raise ProviderError("Kick did not return the configured channel.")
        stream = channel.get("stream")
        if not isinstance(stream, dict) or not isinstance(stream.get("is_live"), bool):
            raise ProviderError("Kick did not provide a valid live status.")
        viewers = stream.get("viewer_count")
        return dict(live=stream["is_live"], title=str(channel.get("stream_title") or stream.get("title") or "")[:240],
                    viewers=int(viewers) if isinstance(viewers, (int, Decimal)) and not isinstance(viewers, bool) and viewers > 0 and stream["is_live"] else None,
                    category=str((channel.get("category") or {}).get("name", ""))[:120], channel=site["kick_channel_slug"])

    def close(self):
        if hasattr(self.local, "session"):
            self.local.session.close()

    def last_http_status(self):
        return getattr(self.local, "http_status", None)
