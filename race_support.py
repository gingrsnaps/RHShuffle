"""Pure validation, Eastern Time conversion, and safe JSON file operations.

This module has no Flask state and makes no network requests. Decimal values
remain exact until they are formatted; persistent amounts use decimal strings.
"""
from __future__ import annotations

import hashlib
import json
import re
import time
from datetime import datetime, timezone
from decimal import Decimal, InvalidOperation
from pathlib import Path
from urllib.parse import urlsplit
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

try:
    EASTERN = ZoneInfo("America/New_York")
except ZoneInfoNotFoundError as exc:
    raise RuntimeError("Eastern Time data is missing. Install requirements.txt, including tzdata.") from exc

STORE_VERSION = 7
DEFAULT_PRIZES = dict(enumerate(
    [1800, 1200, 800, 450, 200, 150, 90, 80, 70, 60, 20, 20, 20, 20, 20], 1
))
WEIGHTING_RULES = [
    {"range": "RTP ≤ 98%", "counts": "100% counts"},
    {"range": "98% < RTP < 99%", "counts": "50% counts"},
    {"range": "RTP ≥ 99%", "counts": "10% counts"},
]
TEXT_LIMITS = {
    "site_name": 60, "race_title": 100, "race_description": 240,
    "sponsor_name": 60, "community_name": 60, "campaign_code_filter": 64,
}
URL_FIELDS = ("sponsor_url", "stream_url", "community_url", "responsible_gambling_url")
OPTIONAL_URLS = {"community_url", "responsible_gambling_url"}
DECIMAL_PATTERN = re.compile(r"^\+?(?:\d+(?:\.\d*)?|\.\d+)(?:[eE][+-]?\d+)?$")
MONEY_PATTERN = re.compile(r"^\$?\s*(?:\d+|\d{1,3}(?:,\d{3})+)(?:\.\d{1,2})?$")


def decimal_amount(value, *, limit=Decimal("1000000000000000")) -> Decimal:
    """Reject malformed, negative, non-finite, or excessive API amounts."""
    if isinstance(value, bool) or value is None:
        raise ValueError("An amount must be a non-negative number.")
    text = str(value).strip()
    # Legacy snapshots may contain formatted amounts, but arbitrary text must
    # never be stripped into a seemingly valid financial value.
    if "$" in text or "," in text:
        if not MONEY_PATTERN.fullmatch(text):
            raise ValueError("Invalid formatted amount.")
        text = text.replace("$", "").replace(",", "").strip()
    if not DECIMAL_PATTERN.fullmatch(text):
        raise ValueError("Invalid numeric amount.")
    try:
        amount = Decimal(text)
    except InvalidOperation as exc:
        raise ValueError("Invalid numeric amount.") from exc
    if not amount.is_finite() or amount < 0 or amount > limit:
        raise ValueError("Amount is outside the allowed range.")
    return amount


def money_input(value) -> Decimal:
    text = str(value or "").strip()
    if not MONEY_PATTERN.fullmatch(text):
        raise ValueError("Use a non-negative amount such as 25000 or $25,000.00.")
    return decimal_amount(text, limit=Decimal("1000000000000"))


def money(value) -> str:
    if value is None:
        return "—"
    try:
        return "$" + format(decimal_amount(value), ",.2f")
    except ValueError:
        return "—"


def integer(value, default=0) -> int:
    try:
        if isinstance(value, bool):
            return default
        return int(value)
    except (TypeError, ValueError, OverflowError):
        return default


def valid_url(value, *, allow_blank=False) -> bool:
    text = str(value or "").strip()
    if not text:
        return allow_blank
    if len(text) > 2048 or any(ord(c) < 33 for c in text) or "\\" in text:
        return False
    try:
        parsed = urlsplit(text)
        _ = parsed.port  # Validate malformed/out-of-range ports as well.
        return (parsed.scheme in {"http", "https"} and bool(parsed.hostname)
                and not parsed.username and not parsed.password)
    except ValueError:
        return False


def fmt_et(epoch) -> str:
    if not epoch:
        return "Not configured"
    try:
        return datetime.fromtimestamp(int(epoch), EASTERN).strftime("%b %d, %Y · %I:%M %p %Z")
    except (ValueError, OSError, OverflowError, TypeError):
        return "Invalid date"


def local_input(epoch) -> str:
    return datetime.fromtimestamp(int(epoch), EASTERN).strftime("%Y-%m-%dT%H:%M") if epoch else ""


def eastern_epoch(value) -> int:
    """Reject nonexistent and ambiguous DST times instead of guessing an hour."""
    try:
        naive = datetime.strptime(str(value), "%Y-%m-%dT%H:%M")
    except (ValueError, TypeError) as exc:
        raise ValueError("Choose a valid date and time.") from exc
    if not 1970 <= naive.year <= 2099:
        raise ValueError("Choose a year between 1970 and 2099.")
    candidates = set()
    for fold in (0, 1):
        aware = naive.replace(tzinfo=EASTERN, fold=fold)
        epoch = int(aware.timestamp())
        if datetime.fromtimestamp(epoch, EASTERN).replace(tzinfo=None) == naive:
            candidates.add(epoch)
    if not candidates:
        raise ValueError("This Eastern Time does not exist because the clocks move forward. Choose another time.")
    if len(candidates) > 1:
        raise ValueError("This Eastern Time occurs twice when the clocks move back. Choose a time outside the repeated hour.")
    return candidates.pop()


def race_key(site) -> str:
    """The affiliate window defines a race; cosmetic edits do not."""
    identity = [integer(site.get("start_time")), integer(site.get("end_time")),
                str(site.get("campaign_code_filter") or "").strip().casefold()]
    return hashlib.sha256(json.dumps(identity).encode()).hexdigest()[:24]


def empty_snapshots(key) -> dict:
    return {"race_key": key, "last_top15": [], "prev_top15": [], "updated_at": None}


def validate_site(site) -> dict:
    """Return field errors; reused by normal saves and backup restoration."""
    errors = {}
    for key, maximum in TEXT_LIMITS.items():
        value = site.get(key)
        if not isinstance(value, str) or len(value) > maximum:
            errors[key] = "Use text up to " + str(maximum) + " characters."
    for key in ("site_name", "race_title", "sponsor_name"):
        if not str(site.get(key) or "").strip():
            errors[key] = "This field is required."
    start, end = integer(site.get("start_time"), -1), integer(site.get("end_time"), -1)
    if not ((start == 0 and end == 0) or (0 < start < end <= 4102444799)):
        errors["end_et"] = "The end must be after the start, within the supported date range."
    for key in ("start_time", "end_time"):
        if isinstance(site.get(key), bool) or not isinstance(site.get(key), int):
            errors["end_et"] = "Race timestamps must be whole epoch seconds."
    if integer(site.get("refresh_seconds")) != 60:
        errors["refresh_seconds"] = "Automatic updates run every 60 seconds."
    if not re.fullmatch(r"[a-z0-9_-]{2,25}", str(site.get("kick_channel_slug") or "")):
        errors["kick_channel_slug"] = "Use a Kick channel name of 2–25 letters, numbers, underscores, or hyphens."
    for key in URL_FIELDS:
        if not valid_url(site.get(key), allow_blank=key in OPTIONAL_URLS):
            errors[key] = "Enter a complete http or https link without embedded credentials."
    prizes = site.get("prizes")
    if not isinstance(prizes, dict) or set(prizes) != {str(n) for n in range(1, 16)}:
        errors["prizes"] = "Include all 15 placement prizes."
    else:
        for rank, amount in prizes.items():
            try:
                number = money_input(str(amount))
                if number.as_tuple().exponent < -2:
                    raise ValueError("Use at most two decimal places.")
            except ValueError as exc:
                errors["prize_" + rank] = str(exc)
    return errors


def canonical_site(source, defaults) -> dict:
    """Fill legacy missing fields without changing saved race choices."""
    clean = dict(defaults)
    clean.update({k: source[k] for k in defaults if k in source})
    clean["leaderboard_size"] = 15
    # Old saved intervals migrate to the required cadence; race dates and
    # financial values retain their saved meanings.
    clean["refresh_seconds"] = 60
    raw = clean.get("prizes")
    raw = raw if isinstance(raw, dict) else {}
    clean["prizes"] = {
        str(n): str(decimal_amount(raw.get(str(n), DEFAULT_PRIZES[n])))
        for n in range(1, 16)
    }
    return clean


def clean_snapshots(snapshots, key) -> dict:
    """Validate every restored row before it can reach a cache or template."""
    if not isinstance(snapshots, dict):
        raise ValueError("Leaderboard snapshots must be an object.")
    if snapshots.get("race_key", key) != key:
        raise ValueError("Snapshot race does not match its schedule.")
    result = empty_snapshots(key)
    for field in ("last_top15", "prev_top15"):
        rows = snapshots.get(field, [])
        if not isinstance(rows, list) or len(rows) > 15:
            raise ValueError("Each saved leaderboard must contain at most 15 rows.")
        ranks, names = set(), set()
        for row in rows:
            if not isinstance(row, dict):
                raise ValueError("Every snapshot entry must be an object.")
            rank = row.get("rank")
            username = row.get("username")
            if (isinstance(rank, bool) or not isinstance(rank, int) or not 1 <= rank <= 15
                    or rank in ranks or not isinstance(username, str)
                    or not username.strip() or len(username) > 128 or username in names):
                raise ValueError("Snapshot ranks or usernames are invalid or duplicated.")
            ranks.add(rank)
            names.add(username)
            weighted = decimal_amount(row.get("weighted_wager", row.get("wager")))
            raw = row.get("raw_wager")
            # Older stores did not always retain the API total beneath an
            # override. Unknown is more accurate than inventing an original.
            base = row.get("original_weighted_wager", None if row.get("source") == "override" else weighted)
            original = None if base is None else str(decimal_amount(base))
            clean = {
                "rank": rank, "username": username.strip(),
                "weighted_wager": str(weighted), "wager": money(weighted),
                "original_weighted_wager": original,
                "original_weighted_str": money(original),
                "raw_wager": None if raw is None else str(decimal_amount(raw)),
                "raw_wager_str": money(raw),
                "source": "override" if row.get("source") == "override" else "shuffle",
                "row_count": max(1, integer(row.get("row_count"), 1)),
            }
            result[field].append(clean)
        result[field].sort(key=lambda row: row["rank"])
    updated = snapshots.get("updated_at")
    if updated is not None and (isinstance(updated, bool) or not isinstance(updated, int)
                                or updated < 0 or updated > int(time.time()) + 300):
        raise ValueError("Snapshot update time is invalid.")
    result["updated_at"] = updated
    return result


def clean_overrides(value) -> dict:
    if not isinstance(value, dict) or len(value) > 10000:
        raise ValueError("Overrides must be an object with at most 10,000 entries.")
    result = {}
    for username, amount in value.items():
        if not isinstance(username, str) or not username.strip() or len(username) > 64:
            raise ValueError("An override username is invalid.")
        result[username.strip()] = str(money_input(str(amount)))
    return result


def csv_text(value) -> str:
    """Prevent text cells from being interpreted as formulas by spreadsheet apps."""
    text = str(value or "")
    unsafe = text.lstrip().startswith(("=", "+", "-", "@")) or bool(text and text[0] in "\t\r\n")
    return "'" + text if unsafe else text


def read_json(path: Path) -> dict:
    try:
        with path.open(encoding="utf-8") as handle:
            value = json.load(handle)
        if not isinstance(value, dict):
            raise ValueError("The file must contain a JSON object.")
        return value
    except (OSError, ValueError) as exc:
        raise RuntimeError("Cannot read " + str(path) + ". The original file was left untouched. Restore a verified recovery copy.") from exc

