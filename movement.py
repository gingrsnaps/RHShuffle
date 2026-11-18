"""Shared placement-movement event helpers.

Movement is computed with full provider identity before public username masking.
The public event id is a one-way digest; identities never leave the server through
these helpers. Events are timestamped once by the successful provider snapshot so
polling, reloads, and background-tab resumes cannot restart their lifetime.
"""
from __future__ import annotations

import hashlib
import json


def _event_id(provider, identity, previous_rank, current_rank, changed_at):
    payload = [str(provider), str(identity).strip().casefold(), previous_rank, current_rank, int(changed_at)]
    return hashlib.sha256(json.dumps(payload, separators=(",", ":"), ensure_ascii=True).encode("utf-8")).hexdigest()[:20]


def preserve_movement_event(row, old, window_seconds):
    """Copy one already-authored event without restarting its expiration."""
    row["movement"] = old.get("movement")
    row["new_entry"] = bool(old.get("new_entry"))
    row["previous_rank"] = old.get("previous_rank")
    row["movement_at"] = int(old.get("movement_at", 0) or 0)
    row["movement_expires_at"] = int(old.get("movement_expires_at", 0) or
                                      (row["movement_at"] + int(window_seconds) if row["movement_at"] else 0))
    row["movement_event_id"] = str(old.get("movement_event_id") or "")
    row["movement_kind"] = str(old.get("movement_kind") or "")
    return row


def stamp_movement_event(row, provider, identity, changed_at, window_seconds):
    """Author one event from movement/new-entry fields already on the row."""
    current_rank = row.get("rank")
    movement = row.get("movement")
    movement = int(movement) if type(movement) is int else 0
    is_new = bool(row.get("new_entry"))
    active = bool(movement or is_new)
    previous_rank = (current_rank + movement) if movement and type(current_rank) is int else None
    row["previous_rank"] = previous_rank
    if not active:
        row.update(movement_at=0, movement_expires_at=0, movement_event_id="", movement_kind="")
        return row
    kind = "new" if is_new else "up" if movement > 0 else "down"
    stamp = int(changed_at)
    row["movement_at"] = stamp
    row["movement_expires_at"] = stamp + int(window_seconds)
    row["movement_kind"] = kind
    row["movement_event_id"] = _event_id(provider, identity, previous_rank, current_rank, stamp)
    return row


def public_movement_event(row):
    """Return an allowlisted public movement event, or None for unchanged rows."""
    event_id = str(row.get("movement_event_id") or "")
    movement = row.get("movement")
    movement = int(movement) if type(movement) is int else 0
    is_new = bool(row.get("new_entry"))
    changed_at = int(row.get("movement_at", 0) or 0)
    expires_at = int(row.get("movement_expires_at", 0) or 0)
    if not (is_new or movement) or not changed_at or not expires_at:
        return None
    current_rank = row.get("rank") if type(row.get("rank")) is int else 0
    previous_rank = row.get("previous_rank")
    if previous_rank is not None and type(previous_rank) is not int:
        previous_rank = None
    kind = str(row.get("movement_kind") or ("new" if is_new else "up" if movement > 0 else "down"))
    if not event_id:
        # Legacy saved snapshots may predate event ids. This fallback uses only
        # non-sensitive numeric event facts and exists solely for UI continuity.
        event_id = hashlib.sha256(json.dumps([kind, previous_rank, current_rank, changed_at], separators=(",", ":")).encode("ascii")).hexdigest()[:20]
    return {
        "event_id": event_id,
        "kind": kind,
        "direction": "new" if is_new else "up" if movement > 0 else "down",
        "places": abs(movement),
        "previous_rank": previous_rank,
        "current_rank": current_rank,
        "changed_at": changed_at,
        "expires_at": expires_at,
    }


def admin_event_record(provider, row):
    """Admin-only event record. Caller decides which identity/name is displayed."""
    event = public_movement_event(row)
    if not event:
        return None
    return {"provider": provider, **event}
