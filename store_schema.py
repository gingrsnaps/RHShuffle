"""Non-destructive document validation shared by startup and migration tools."""
from __future__ import annotations
import copy
import secrets
import time
from race_support import STORE_VERSION, canonical_site, clean_overrides, clean_snapshots, integer, race_key, validate_site


def upgrade_store(value, defaults, health_defaults):
    """Upgrade additively and preserve password hashes, settings, and history."""
    if not isinstance(value, dict):
        raise ValueError("The admin store must contain a JSON object.")
    original = copy.deepcopy(value)
    store = copy.deepcopy(value)
    version = integer(store.get("version"))
    if version > STORE_VERSION:
        raise RuntimeError("This admin store belongs to a newer application version.")
    users = store.setdefault("users", {})
    if not isinstance(users, dict):
        raise RuntimeError("Admin accounts are malformed. Restore a verified recovery copy.")
    seen = set()
    for username, record in users.items():
        if not isinstance(record, dict) or not isinstance(record.get("pw_hash"), str):
            raise RuntimeError("An admin account is malformed. The original store is unchanged.")
        folded = username.casefold()
        if folded in seen:
            raise RuntimeError("Duplicate case-insensitive admin usernames need offline resolution before upgrade.")
        seen.add(folded)
        record.setdefault("auth_version", 1)
    secret = str(store.get("secret_key") or "")
    if version < 3 or len(secret) < 32 or secret.upper().startswith(("REPLACE_", "GENERATED_")):
        store["secret_key"] = secrets.token_hex(32)
    raw_site = store.get("site_settings", {})
    if not isinstance(raw_site, dict):
        raise ValueError("Saved race settings must be an object; they were not replaced with defaults.")
    site = canonical_site(raw_site, defaults)
    errors = validate_site(site)
    if errors:
        raise RuntimeError("Saved race settings need correction: " + "; ".join(errors.values()))
    store["site_settings"] = site
    store.setdefault("settings_revision", 1)
    store.setdefault("data_revision", 1)
    for field in ("settings_revision", "data_revision"):
        if isinstance(store[field], bool) or not isinstance(store[field], int) or store[field] < 1:
            raise ValueError("Saved revision counters must be positive integers.")
    store.setdefault("overrides", {})
    store["overrides"] = clean_overrides(store["overrides"])
    store.setdefault("race_history", [])
    store.setdefault("audit_log", [])
    store.setdefault("banned_ips", [])
    for key in ("race_history", "audit_log", "banned_ips"):
        if not isinstance(store[key], list):
            raise RuntimeError("Saved " + key + " has an invalid format.")
    for entry in store["race_history"]:
        if not isinstance(entry, dict) or not isinstance(entry.get("site_settings"), dict):
            raise ValueError("An archived race has invalid settings.")
        archived_site = canonical_site(entry["site_settings"], defaults)
        if validate_site(archived_site):
            raise ValueError("An archived race has invalid dates, prizes, or links.")
        clean_overrides(entry.get("overrides", {}))
        clean_snapshots(entry.get("leaderboard_snapshots", {}), race_key(archived_site))
    health = store.setdefault("health", {})
    if not isinstance(health, dict):
        raise RuntimeError("Saved health data has an invalid format.")
    for key, default in health_defaults.items():
        health.setdefault(key, default)
    if "http://" in str(health.get("last_error") or "") or "https://" in str(health.get("last_error") or ""):
        health["last_error"] = "Previous external-service error redacted during migration."
    snapshots = store.setdefault("leaderboard_snapshots", {})
    if not isinstance(snapshots, dict):
        raise ValueError("Saved leaderboard snapshots must be an object.")
    snapshots.setdefault("last_top15", snapshots.get("last_top11") or [])
    snapshots.setdefault("prev_top15", snapshots.get("prev_top11") or [])
    snapshots.setdefault("updated_at", None)
    snapshots.setdefault("race_key", race_key(site))
    # Validate a legacy snapshot without discarding any unknown original fields.
    clean_snapshots(snapshots, race_key(site))
    health["last_success"] = health.get("last_success") or snapshots.get("updated_at") or 0
    store.pop("payout_status", None)
    store["version"] = STORE_VERSION
    store.setdefault("updated_at", int(time.time()))
    return store, store != original
