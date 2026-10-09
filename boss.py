"""Shared community raid rules. Every hit is validated and committed server-side.

The boss lives in a separate record, so attacks cannot change race settings or
invalidate administrator forms. One web instance serves the whole community.
"""
import copy
import hashlib
import hmac
import ipaddress
import logging
import math
import re
import secrets
import threading
import time

from boss_extras import audit, balance_view, host_snapshot, rally_view, record_activity, validate_extras
from boss_avatar import image_bytes, validate_avatar
from boss_progress import MAX_NUMBER, badges, new_profile, record_hit, username, validate_profiles

LOG = logging.getLogger("redhunllef")
DEFAULT_HP = 2_400_000
MIN_HP, MAX_HP = 1, MAX_NUMBER
COOLDOWN = 30
DAILY_ATTACKS = None  # Legacy contract: null now means unlimited hits.
DAY = 86400
WARD_SECONDS = 600
POLL_SECONDS = 5
BASE_DAMAGE, WEAK_DAMAGE, BURST_EVERY, BURST_BONUS = 100, 150, 10, 100
MAX_DAMAGE = MAX_NUMBER
# Historical receipts must remain valid if the host later lowers attack damage.
MAX_HIT = MAX_NUMBER
DEFAULT_NAME = 'Crimson Hunllef'
STYLES = {"blade": "Blade", "bow": "Bow", "magic": "Magic"}
MAX_PLAYERS, MAX_NETWORKS = 2000, 4000
TOKEN = re.compile(r"[a-f0-9]{64}\Z")


def combat_settings(value=None):
    """Validate editable settings separately from immutable player damage totals."""
    if value is not None and not isinstance(value, dict):
        raise ValueError('Invalid boss settings.')
    value = value or {}
    name = value.get('name', DEFAULT_NAME)
    if not isinstance(name, str) or not 1 <= len(name) <= 60 or not name.strip() or not name.isprintable():
        raise ValueError('Boss name must contain 1–60 printable characters.')
    result = dict(name=name.strip(), damage=value.get('damage', BASE_DAMAGE),
                  weak_damage=value.get('weak_damage', WEAK_DAMAGE), burst_bonus=value.get('burst_bonus', BURST_BONUS))
    for field in ('damage', 'weak_damage', 'burst_bonus'):
        if type(result[field]) is not int or not 0 <= result[field] <= MAX_DAMAGE:
            raise ValueError(f'Damage must be a whole number from 0 to {MAX_DAMAGE:,}.')
    return result


def rules(state=None):
    """One contract for server validation, host controls, and browser labels."""
    settings = combat_settings((state or {}).get('settings'))
    return dict(cooldown=COOLDOWN, daily_attacks=DAILY_ATTACKS, raid_day=DAY,
                poll_seconds=POLL_SECONDS, ward_seconds=WARD_SECONDS, default_hp=DEFAULT_HP, identity_mode="browser",
                damage=settings['damage'], weak_damage=settings['weak_damage'], burst_every=BURST_EVERY,
                burst_bonus=settings['burst_bonus'],
                styles=dict(STYLES), min_hp=MIN_HP, max_hp=MAX_HP, max_damage=MAX_DAMAGE)


class BossError(ValueError):
    def __init__(self, message, code="invalid", status=400, retry_after=0):
        super().__init__(message)
        self.code, self.status, self.retry_after = code, status, retry_after


def fresh_raid(now=None, health=DEFAULT_HP, history=None, settings=None):
    now = int(time.time() if now is None else now)
    return dict(schema=1, id=secrets.token_hex(16), salt=secrets.token_hex(32),
                version=1, max_hp=health, hp=health, created_at=now, started_at=0,
                finished_at=0, paused=False, total_attacks=0, total_damage=0,
                players={}, networks={}, recent=[], history=list(history or [])[-10:],
                settings=combat_settings(settings), settings_revision=0)


def _integer(value, minimum=0, maximum=MAX_NUMBER):
    if type(value) is not int or not minimum <= value <= maximum:
        raise ValueError("The community boss recovery has an invalid number.")
    return value


def _timestamp(value):
    if type(value) not in (int, float) or not math.isfinite(value) or not 0 <= value <= 10**12:
        raise ValueError("The community boss recovery has an invalid timestamp.")


def validate_boss(value):
    """Validate recovery before a transaction imports any account or game data."""
    if not isinstance(value, dict) or value.get("schema") != 1:
        raise ValueError("Unsupported community boss recovery. Existing data was not replaced.")
    for field, pattern in (("id", r"[a-f0-9]{32}"), ("salt", r"[a-f0-9]{64}")):
        if not isinstance(value.get(field), str) or not re.fullmatch(pattern, value[field]):
            raise ValueError("The community boss recovery has an invalid identifier.")
    _integer(value.get("version"), 1)
    _integer(value.get("health_revision", 0))
    change = value.get('health_change')
    if change is not None:
        if not isinstance(change, dict):
            raise ValueError('Invalid boss health notice.')
        _timestamp(change.get('at'))
        _integer(change.get('max_hp'), 1, MAX_HP)
        _integer(change.get('hp'), 0, change['max_hp'])
    _integer(value.get('settings_revision', 0))
    combat_settings(value.get('settings'))  # Older raids inherit the original defaults.
    maximum = _integer(value.get("max_hp"), 1, MAX_HP)
    adjustment = _integer(value.get("health_adjustment", 0), -MAX_NUMBER, MAX_NUMBER)
    validate_extras(value, MAX_NETWORKS)
    validate_profiles(value.get("profiles", {}), MAX_PLAYERS, value.get("households"))
    hp = _integer(value.get("hp"), 0, maximum)
    for field in ("created_at", "started_at", "finished_at", "total_attacks", "total_damage"):
        _integer(value.get(field))
    if type(value.get("paused")) is not bool or value["total_damage"] != maximum - hp + adjustment:
        raise ValueError("The community boss recovery has inconsistent health.")
    if bool(value["finished_at"]) != (hp == 0) or (value["total_attacks"] and not value["started_at"]):
        raise ValueError("The community boss recovery has inconsistent progress.")
    players, networks = value.get("players"), value.get("networks")
    if not isinstance(players, dict) or len(players) > MAX_PLAYERS or not isinstance(networks, dict) or len(networks) > MAX_NETWORKS:
        raise ValueError("The community boss recovery has invalid player records.")
    for records in (players, networks):
        for key, record in records.items():
            if not isinstance(key, str) or not TOKEN.fullmatch(key) or not isinstance(record, dict):
                raise ValueError("The community boss recovery has an invalid player identifier.")
            _timestamp(record.get("last_attack"))
            _integer(record.get("day"))
            _integer(record.get("used"))
    for player in players.values():
        _integer(player.get("attacks"), 1)
        _integer(player.get("damage"), 0, MAX_NUMBER)
        if "active_days" in player:
            _integer(player["active_days"], 1, player["attacks"])
        receipt = player.get("last_hit")
        if not isinstance(receipt, dict) or not isinstance(receipt.get("style"), str) or receipt["style"] not in STYLES:
            raise ValueError("The community boss recovery has an invalid attack receipt.")
        if not isinstance(player.get("request_id"), str) or not re.fullmatch(r"[A-Za-z0-9_-]{8,64}", player["request_id"]):
            raise ValueError("The community boss recovery has an invalid request receipt.")
        _integer(receipt.get("damage"), 0, MAX_HIT)
        _integer(receipt.get("at"))
        if type(receipt.get("weakness")) is not bool or type(receipt.get("burst")) is not bool:
            raise ValueError("The community boss recovery has an invalid attack bonus.")
    if sum(p["damage"] for p in players.values()) != value["total_damage"] or sum(p["attacks"] for p in players.values()) != value["total_attacks"]:
        raise ValueError("The community boss recovery totals do not match its players.")
    recent, history = value.get("recent"), value.get("history")
    if not isinstance(recent, list) or len(recent) > 12 or not isinstance(history, list) or len(history) > 10:
        raise ValueError("The community boss recovery has an invalid history.")
    for hit in recent:
        if not isinstance(hit, dict) or not re.fullmatch(r"Raider [A-F0-9]{8}", str(hit.get("name", ""))) or not isinstance(hit.get("style"), str) or hit["style"] not in STYLES:
            raise ValueError("The community boss recovery has an invalid recent hit.")
        if 'public_name' in hit and (not isinstance(hit['public_name'], str) or not re.fullmatch(r'.{1,2}\*{6}', hit['public_name'])):
            raise ValueError('Invalid masked recent player name.')
        _integer(hit.get("damage"), 0, MAX_HIT)
        _integer(hit.get("at"))
    for entry in history:
        if not isinstance(entry, dict) or entry.get("outcome") not in {"Victory", "Restarted"}:
            raise ValueError("The community boss recovery has an invalid raid history.")
        for field in ("started_at", "ended_at", "max_hp", "damage", "attacks", "raiders"):
            _integer(entry.get(field))
    return copy.deepcopy(value)


def network_identity(address):
    """Normalize IPv4; group IPv6 /64 privacy addresses to limit easy rotation."""
    try:
        ip = ipaddress.ip_address(address)
    except ValueError:
        raise BossError("Your connection could not be identified. Reload and try again.") from None
    if getattr(ip, "ipv4_mapped", None):
        ip = ip.ipv4_mapped
    return str(ipaddress.ip_network((ip, 64), strict=False)) if ip.version == 6 else str(ip)


def _key(raid, kind, value):
    # Raw IP addresses and browser identifiers never enter game records/feeds.
    return hmac.new(bytes.fromhex(raid["salt"]), (kind + ":" + value).encode(), hashlib.sha256).hexdigest()


def _name(key):
    return "Raider " + key[:8].upper()


class CommunityBoss:
    def __init__(self, store):
        self.store, self.lock = store, threading.RLock()
        with self.store.connection(transaction=True) as conn:
            row = self.store.boss_read(conn)
            if not row:
                value = fresh_raid()
                self.store.boss_write(conn, value)
            else:
                value = validate_boss(row)
            self.avatar_document = validate_avatar(self.store.avatar(conn))
        self.state, self.loaded_at = value, time.monotonic()

    def _read(self, conn, locked=False):
        value = self.store.boss_read(conn)
        if value is None:
            raise ValueError("Community boss state is missing. Restore the private recovery checkpoint.")
        return validate_boss(value)

    def _write(self, conn, state, *, previous=None, new_raid=False, health_change=False, settings_change=False):
        """Only an explicit host health edit or new raid may replenish health.

        Callers already hold the storage transaction. Compare against the row
        read inside that transaction, never an older viewer/cache snapshot.
        """
        previous = self._read(conn, locked=True) if previous is None else previous
        if state["id"] != previous["id"]:
            if not new_raid:
                raise BossError("Starting a new boss requires the host's new-raid action.", "new_raid_required", 409)
        elif (state["total_damage"] < previous["total_damage"]
              or state["total_attacks"] < previous["total_attacks"]
              or state["version"] < previous["version"]
              or (not health_change and (state["max_hp"] != previous["max_hp"] or state["hp"] > previous["hp"]
                  or state.get("health_revision", 0) != previous.get("health_revision", 0)
                  or state.get("health_adjustment", 0) != previous.get("health_adjustment", 0)))
              or (health_change and (state.get("health_revision", 0) != previous.get("health_revision", 0) + 1
                  or state["total_damage"] != previous["total_damage"] or state["total_attacks"] != previous["total_attacks"]))):
            LOG.error("BOSS Blocked a progress reversal. Saved damage and health were not changed.")
            raise BossError("Boss progress cannot move backwards. Existing damage was preserved.", "progress_reversal", 409)
        if not 0 <= state["hp"] <= state["max_hp"] or state["hp"] != state["max_hp"] - state["total_damage"] + state.get("health_adjustment", 0):
            raise BossError("Boss health does not match saved damage. Existing progress was preserved.", "invalid_health", 409)
        if state['id'] == previous['id']:
            changed = combat_settings(state.get('settings')) != combat_settings(previous.get('settings'))
            revision, old_revision = state.get('settings_revision', 0), previous.get('settings_revision', 0)
            if ((not settings_change and (changed or revision != old_revision)) or
                (settings_change and (revision != old_revision + 1 or state['hp'] != previous['hp'] or
                 state['total_damage'] != previous['total_damage'] or state['total_attacks'] != previous['total_attacks']))):
                raise BossError('Boss settings require an explicit admin edit. Existing progress was preserved.', 'settings_guard', 409)
        self.store.boss_write(conn, state)

    def _load(self, force=False):
        # Most 5-second viewer polls use memory, not another disk read. A
        # periodic reload also picks up writes from another process during tests
        # or a short deployment overlap. Local mode still requires one instance.
        if force or time.monotonic() - self.loaded_at >= POLL_SECONDS:
            with self.store.connection() as conn:
                self.state = self._read(conn)
                # Images stay outside the frequently rewritten gameplay record.
                if self.state.get('avatar_hash') != (self.avatar_document or {}).get('sha256'):
                    self.avatar_document = validate_avatar(self.store.avatar(conn))
            self.loaded_at = time.monotonic()

    def _project(self, state, guest, address, now):
        keys = list(STYLES)
        # A secret-keyed draw is random to visitors, stable for every viewer and
        # process, and needs no scheduler writes. Repeats are valid random draws.
        window = int(now) // WARD_SECONDS
        draw = _key(state, "ward", state["id"] + ":" + str(window))
        weakness = keys[int(draw, 16) % len(keys)]
        day = max(0, int((now - state["started_at"]) // DAY)) if state["started_at"] else 0
        reset = state["started_at"] + (day + 1) * DAY if state["started_at"] else 0
        player_key = _key(state, "player", guest) if guest else ""
        player = state["players"].get(player_key, {})
        profile = state.get("profiles", {}).get(player_key, {})
        # A proxy, household, campus or carrier may expose one IP for many
        # people. The signed browser cookie owns the profile and its cooldown.
        # Legacy network records remain readable but never decide who can play.
        identity_ready = bool(profile)
        ready = player.get("last_attack", 0) + COOLDOWN
        phase = "Awakening" if state["hp"] > state["max_hp"] * .75 else "Enraged" if state["hp"] > state["max_hp"] * .25 else "Last stand"
        status = "victory" if state["hp"] == 0 else "paused" if state["paused"] else "active" if state["started_at"] else "waiting"
        leaders = sorted(state["players"].items(), key=lambda item: (-item[1]["damage"], item[0]))[:10]
        return dict(server_time=now, raid_id=state["id"], version=state["version"], status=status, connection_ready=bool(guest),
                    name=combat_settings(state.get('settings'))['name'], settings_revision=state.get('settings_revision', 0),
                    health_revision=state.get("health_revision", 0), avatar_url=self.avatar_url(), avatar_custom=bool(self.avatar_document),
                    hp=state["hp"], max_hp=state["max_hp"], phase=phase, started_at=state["started_at"],
                    finished_at=state["finished_at"], day=day + 1, resets_at=reset,
                    total_damage=state["total_damage"], total_attacks=state["total_attacks"], raiders=len(state["players"]),
                    weakness=weakness, weakness_label=STYLES[weakness], ward_changes_at=(int(now) // WARD_SECONDS + 1) * WARD_SECONDS,
                    rules=rules(state), rally=rally_view(state, now),
                    milestones=[dict(percent=p, label=label, reached=(state["max_hp"] - state["hp"]) * 100 >= state["max_hp"] * p)
                                for p, label in ((25, "Armor cracked"), (50, "The crew rallies"), (75, "Final stand"), (100, "Crimson conquered"))],
                    you=dict(name=_name(player_key) if guest else "Spectator", damage=player.get("damage", 0),
                             attacks=player.get("attacks", 0), remaining=None, ready_at=ready,
                             display_name=profile.get("name", ""), identity_ready=identity_ready,
                             recovery_saved=bool(profile.get("recovery_hash")), shared_connection=False,
                             burst_in=BURST_EVERY - player.get("attacks", 0) % BURST_EVERY,
                             active_days=profile.get("active_days", player.get("active_days", 1 if player else 0)),
                             badges=badges(profile or player, now),
                             last_request=player.get("request_id", ""), last_hit=copy.deepcopy(player.get("last_hit")),
                             can_attack=bool(guest and status in {"waiting", "active"} and identity_ready and now >= ready)),
                    leaders=[dict(name=_name(key), damage=p["damage"], attacks=p["attacks"], you=key == player_key) for key, p in leaders],
                    recent=copy.deepcopy(state["recent"]), history=copy.deepcopy(state["history"]))

    def register(self, guest, address, raid_id, name):
        """Persist a private name for this signed browser, independently of IP.

        Existing profile keys and stats are untouched. Recovery codes remain
        the way to restore a lost cookie; matching a name or IP proves nothing.
        """
        name = username(name)
        now = time.time()
        with self.lock:
            with self.store.connection(transaction=True) as conn:
                state = self._read(conn, locked=True)
                # A name belongs to the persistent player, not one raid. A host
                # restart between page load and Save must not reject the name.
                previous = copy.deepcopy(state)
                pk = _key(state, 'player', guest)
                profiles = state.setdefault('profiles', {})
                # Names are self-reported labels, never recovery credentials.
                # Reusing a label creates no link to another player's record.
                own = profiles.get(pk)
                if own and own['name'] == name:
                    self.state, self.loaded_at = state, time.monotonic()
                    return self._project(state, guest, address, now)
                if own and now - own['named_at'] < COOLDOWN:
                    raise BossError('Wait 30 seconds before changing your name again.', 'profile_cooldown', 429,
                                    max(1, math.ceil(COOLDOWN - now + own['named_at'])))
                if not own and len(profiles) >= MAX_PLAYERS:
                    raise BossError('The player registry is full. Contact an admin.', 'capacity', 409)
                if own:
                    own.update(name=name, named_at=now)
                else:
                    # Retain the legacy field shape for portable old-save recovery.
                    # It is a browser-specific reservation, not an IP claim.
                    profiles[pk] = new_profile(name, _key(state, 'reservation', guest), now, state['players'].get(pk))
                state['version'] += 1
                self._write(conn, state, previous=previous)
            self.state, self.loaded_at = state, time.monotonic()
            return self._project(state, guest, address, now)

    def release_profile(self, raid_id, name, *, actor="System"):
        raise BossError("Connection claims are retired. Each player can join directly; no release or raid reset is needed.", "retired_control", 409)

    def save_recovery(self, guest, code_hash):
        """Store only a digest. The full bearer code is displayed once to its owner."""
        with self.lock:
            with self.store.connection(transaction=True) as conn:
                state = self._read(conn, locked=True)
                previous = copy.deepcopy(state)
                pk = _key(state, 'player', guest)
                if pk not in state.get('profiles', {}):
                    raise BossError('Save your username before creating a recovery code.')
                profile = state['profiles'][pk]
                now = time.time()
                if now - profile.get('recovery_at', 0) < COOLDOWN:
                    raise BossError('Wait 30 seconds before replacing your recovery code.', 'profile_cooldown', 429)
                profile['recovery_at'] = now
                profile['recovery_hash'] = code_hash
                state['version'] += 1
                self._write(conn, state, previous=previous)
            self.state, self.loaded_at = state, time.monotonic()

    def recover_profile(self, guest, address, code_hash, raid_id):
        with self.lock:
            with self.store.connection(transaction=True) as conn:
                state = self._read(conn, locked=True)
                if raid_id != state['id']:
                    raise BossError('A new raid started. Reload before recovering.', 'new_raid', 409)
                previous = copy.deepcopy(state)
                pk = _key(state, 'player', guest)
                profiles = state.get('profiles', {})
                profile = profiles.get(pk, {})
                if not hmac.compare_digest(profile.get('recovery_hash', ''), code_hash):
                    raise BossError('That recovery code is invalid or was replaced.', 'invalid_recovery', 400)
                # Same browser key restores all hits and cooldowns exactly. The
                # HTTP layer validates the signed code before calling this method.
                # No network binding is changed or required during recovery.
                state['version'] += 1
                self._write(conn, state, previous=previous)
            self.state, self.loaded_at = state, time.monotonic()
            return self._project(state, guest, address, time.time())

    def household(self, raid_id, name, slots, *, actor="System"):
        raise BossError("Household approvals are no longer needed. Shared connections support all players automatically.", "retired_control", 409)

    def admin_status(self):
        """Private top five. Public projections always keep anonymous aliases."""
        with self.lock:
            self._load()
            result = self._project(self.state, None, None, time.time())
            profiles = self.state.get('profiles', {})
            leaders = sorted(self.state['players'].items(), key=lambda item: (-item[1]['damage'], item[0]))[:5]
            result['balance'] = balance_view(self.state, time.time())
            result['admin_history'] = list(reversed(copy.deepcopy(self.state.get('admin_history', []))))
            result['admin_leaders'] = [dict(name=profiles.get(key, {}).get('name', _name(key)),
                                            alias=_name(key), name_provided=key in profiles,
                                            damage=p['damage'], attacks=p['attacks']) for key, p in leaders]
            return result

    def summary(self):
        """Small anonymous homepage projection: no guest, receipt, or network data."""
        with self.lock:
            self._load()
            state = self.state
            recent = state['recent'][0] if state['recent'] else None
            # Only a masked display name and committed damage leave this method.
            # Actor names, profile IDs, recovery keys and admin audit stay private.
            latest = (dict(name=str(recent.get('public_name') or recent['name'])[:2] + '******',
                           damage=recent['damage'], at=recent['at']) if recent else None)
            change = state.get('health_change')
            status = "victory" if state["hp"] == 0 else "paused" if state["paused"] else "active" if state["started_at"] else "waiting"
            return dict(raid_id=state["id"], created_at=state['created_at'], hp=state["hp"], max_hp=state["max_hp"],
                        name=combat_settings(state.get('settings'))['name'],
                        status=status, raiders=len(state["players"]), total_attacks=state["total_attacks"],
                        total_damage=state["total_damage"], version=state["version"],
                        health_revision=state.get("health_revision", 0), avatar_url=self.avatar_url(), avatar_custom=bool(self.avatar_document),
                        latest_hit=latest, health_change={k:change[k] for k in ('at', 'hp', 'max_hp')} if change else None)

    def avatar_url(self):
        return '/play/avatar/' + self.avatar_document['sha256'] + '.png' if self.avatar_document else '/static/redlogo.png'

    def avatar_image(self, digest):
        with self.lock:
            self._load()
            return image_bytes(self.avatar_document) if self.avatar_document and self.avatar_document['sha256'] == digest else None

    def set_avatar(self, raid_id, avatar, *, actor="System"):
        avatar = validate_avatar(avatar)
        with self.lock:
            with self.store.connection(transaction=True) as conn:
                state = self._read(conn, locked=True)
                if raid_id != state['id']:
                    raise BossError('Another raid started. Reload before changing the avatar.', 'new_raid', 409)
                previous = copy.deepcopy(state)
                self.store.backup_in(conn, 'before-boss-avatar', dict(community_boss=state, community_boss_avatar=self.store.avatar(conn)))
                self.store.avatar_in(conn, avatar)
                state['version'] += 1
                state['avatar_hash'] = avatar['sha256'] if avatar else None
                audit(state, 'Change avatar', actor, {'avatar': previous.get('avatar_hash') or 'Original logo'}, {'avatar': state['avatar_hash'] or 'Original logo'})
                self._write(conn, state, previous=previous)
            self.state, self.avatar_document, self.loaded_at = state, avatar, time.monotonic()
        LOG.info('BOSS Avatar %s; raid progress retained.', 'updated' if avatar else 'reset to original logo')

    def contributors(self):
        """Victory recap includes every contributor, using only raid aliases."""
        with self.lock:
            self._load()
            if self.state["hp"]:
                return []
            return [dict(name=_name(key), damage=p["damage"], attacks=p["attacks"])
                    for key, p in sorted(self.state["players"].items(), key=lambda item: (-item[1]["damage"], item[0]))]

    def status(self, guest=None, address=None):
        with self.lock:
            self._load()
            return self._project(self.state, guest, address, time.time())

    def export(self):
        with self.lock:
            self._load(force=True)
            return copy.deepcopy(self.state)

    def recovery(self):
        with self.lock:
            self._load(force=True)
            return dict(community_boss=copy.deepcopy(self.state), community_boss_avatar=copy.deepcopy(self.avatar_document))

    def attack(self, guest, address, style, raid_id, request_id, *, require_profile=False):
        if not isinstance(style, str) or style not in STYLES or not isinstance(request_id, str) or not re.fullmatch(r"[A-Za-z0-9_-]{8,64}", request_id):
            raise BossError("Choose Blade, Bow, or Magic, then try again.")
        with self.lock:
            now = time.time()
            with self.store.connection(transaction=True) as conn:
                state = self._read(conn, locked=True)
                self.state = copy.deepcopy(state)
                if raid_id != state["id"]:
                    raise BossError("A new raid has started. Review the new boss before attacking.", "new_raid", 409)
                view = self._project(state, guest, address, now)
                pk = _key(state, "player", guest)
                existing = state["players"].get(pk, {})
                # A retry of an acknowledged click never lands a second hit,
                # including retries after victory or after the cooldown ends.
                if existing.get("request_id") == request_id:
                    return dict(ok=True, duplicate=True, hit=copy.deepcopy(existing["last_hit"]), state=view)
                if view["status"] in {"paused", "victory"}:
                    raise BossError("The host paused the raid." if state["paused"] and state["hp"] else "The community has already defeated this boss.", view["status"], 409)
                if now < view["you"]["ready_at"]:
                    retry = max(1, math.ceil(view["you"]["ready_at"] - now))
                    raise BossError("Your player is cooling down. Wait for the timer.", "cooldown", 429, retry)
                if require_profile and not view['you']['identity_ready']:
                    raise BossError('Save your username once in this browser before attacking.', 'username_required', 409)
                day = view["day"] - 1
                if pk not in state["players"] and len(state["players"]) >= MAX_PLAYERS:
                    raise BossError("This raid has reached its player capacity. The host can start a new raid.", "capacity", 409)
                player = state["players"].setdefault(pk, dict(attacks=0, damage=0))
                # Older saves cannot reconstruct every past participation day.
                # Credit one known day, then count future distinct days exactly.
                active_days = player.get("active_days", 1 if player["attacks"] else 0)
                player["active_days"] = active_days + int(player.get("day") != day)
                burst = (player["attacks"] + 1) % BURST_EVERY == 0
                weak = style == view["weakness"]
                # Public requests select a style only. Damage always comes from
                # the saved, validated admin settings read in this transaction.
                damage = min(state["hp"], (view['rules']['weak_damage'] if weak else view['rules']['damage'])
                             + (view['rules']['burst_bonus'] if burst else 0))
                hit = dict(style=style, damage=damage, weakness=weak, burst=burst, at=int(now))
                player.update(used=(player.get("used", 0) if player.get("day") == day else 0) + 1,
                              day=day, last_attack=now)
                # Preserve fractional seconds so early clicks never shorten
                # the server-enforced cooldown.
                player.update(attacks=player["attacks"] + 1, damage=player["damage"] + damage,
                              request_id=request_id, last_hit=hit)
                # Cumulative committed damage is never reset by cooldowns,
                # weakness rotations, midnight, idle time, or source refreshes.
                total_damage = state["total_damage"] + damage
                if total_damage > MAX_NUMBER:
                    raise BossError("This raid reached its numeric capacity. Ask an admin to start a new raid.", "capacity", 409)
                if pk in state.get("profiles", {}):
                    record_hit(state["profiles"][pk], hit, now)
                state.update(hp=state["hp"] - damage, total_damage=total_damage,
                             total_attacks=state["total_attacks"] + 1, version=state["version"] + 1,
                             started_at=state["started_at"] or int(now))
                public_name = state.get('profiles', {}).get(pk, {}).get('name', _name(pk))[:2] + '******'
                state["recent"] = [dict(name=_name(pk), public_name=public_name, **hit)] + state["recent"][:11]
                record_activity(state, pk, damage, now)
                if not state["hp"]:
                    state["finished_at"] = int(now)
                self._write(conn, state, previous=self.state)
            self.state, self.loaded_at = state, time.monotonic()
            if state["finished_at"]:
                LOG.info("BOSS Victory; %s attacks from %s raider profiles.", state["total_attacks"], len(state["players"]))
            elif state["total_attacks"] == 1:
                LOG.info("BOSS Shared raid started; HP=%s, cooldown=%ss, daily cap=none; health regeneration=off.",
                         state["max_hp"], COOLDOWN)
            return dict(ok=True, duplicate=False, hit=hit, state=self._project(state, guest, address, now))

    def configure(self, raid_id, values, settings_revision, *, actor="System", partial=False):
        """Save one admin task without overwriting unrelated combat settings.

        Partial edits merge inside the same lock/transaction as the revision
        check. Appearance edits can never change HP or reset player damage.
        """
        if not partial:
            values = combat_settings(values)
        with self.lock:
            with self.store.connection(transaction=True) as conn:
                state = self._read(conn, locked=True)
                if raid_id != state['id']:
                    raise BossError('Another raid started. Reload before changing its settings.', 'new_raid', 409)
                if settings_revision != state.get('settings_revision', 0):
                    raise BossError('Another admin saved boss settings. Reload and review before saving.', 'settings_conflict', 409)
                if partial:
                    values = combat_settings({**combat_settings(state.get('settings')), **values})
                if values == combat_settings(state.get('settings')):
                    return
                previous = copy.deepcopy(state)
                self.store.backup_in(conn, 'before-boss-settings', dict(community_boss=state))
                state.update(settings=values, settings_revision=state.get('settings_revision', 0) + 1,
                             version=state['version'] + 1)
                audit(state, "Boss settings", actor, combat_settings(previous.get("settings")), values)
                self._write(conn, state, previous=previous, settings_change=True)
            self.state, self.loaded_at = state, time.monotonic()
        LOG.info('BOSS Name/damage settings saved; base=%s, weakness=%s, burst=%s. Existing hits and HP retained.',
                 values['damage'], values['weak_damage'], values['burst_bonus'])

    def control(self, action, raid_id, health=DEFAULT_HP, *, health_revision=None, actor="System"):
        if action not in {"pause", "resume", "restart", "health", "remaining_health"}:
            raise BossError("Choose a valid boss action.")
        if action in {"restart", "health", "remaining_health"}:
            if type(health) is not int or not (0 if action == "remaining_health" else MIN_HP) <= health <= MAX_HP:
                raise BossError(f'Enter whole-number HP up to {MAX_HP:,}; only remaining HP may be zero.')
        with self.lock:
            with self.store.connection(transaction=True) as conn:
                state = self._read(conn, locked=True)
                if state["id"] != raid_id:
                    raise BossError("Another raid has started. Reload before changing it.", "new_raid", 409)
                previous = copy.deepcopy(state)
                if action in {"health", "remaining_health"}:
                    if health_revision != state.get('health_revision', 0):
                        raise BossError('Another health edit was saved. Reload and review before changing it again.', 'health_conflict', 409)
                    maximum = health if action == 'health' else state['max_hp']
                    if action == 'remaining_health' and health > maximum:
                        raise BossError('Remaining HP cannot exceed maximum HP. Raise maximum HP first.')
                    remaining = max(0, min(maximum, state['hp'] + maximum - state['max_hp'])) if action == 'health' else health
                    if maximum == state['max_hp'] and remaining == state['hp']:
                        return
                    self.store.backup_in(conn, 'before-boss-health', dict(community_boss=state))
                    # Explicit admin edits never erase player damage. The offset
                    # separates health adjustments from permanent contributions.
                    state.update(max_hp=maximum, hp=remaining, version=state['version'] + 1,
                                 health_adjustment=remaining - maximum + state['total_damage'],
                                 health_revision=state.get('health_revision', 0) + 1,
                                 health_change=dict(at=int(time.time()), hp=remaining, max_hp=maximum))
                    state['finished_at'] = (state['finished_at'] or int(time.time())) if state['hp'] == 0 else 0
                elif action == "restart":
                    self.store.backup_in(conn, "before-boss-restart", {"community_boss": state})
                    history = state["history"]
                    if state["total_attacks"]:
                        history.append(dict(outcome="Victory" if not state["hp"] else "Restarted", started_at=state["started_at"],
                                            ended_at=state["finished_at"] or int(time.time()), max_hp=state["max_hp"],
                                            damage=state["total_damage"], attacks=state["total_attacks"], raiders=len(state["players"])))
                    state = fresh_raid(health=health, history=history, settings=previous.get('settings'))
                    # Preserve the image version so polls need no image-record
                    # read unless an administrator actually changes the avatar.
                    state['avatar_hash'] = previous.get('avatar_hash')
                    # Names and week-long achievements survive a boss defeat.
                    state['salt'] = previous['salt']
                    state['profiles'] = copy.deepcopy(previous.get('profiles', {}))
                    state['households'] = copy.deepcopy(previous.get('households', {}))
                    state['admin_history'] = copy.deepcopy(previous.get('admin_history', []))
                else:
                    state["paused"], state["version"] = action == "pause", state["version"] + 1
                audit(state, action.replace("_", " ").title(), actor, host_snapshot(previous), host_snapshot(state))
                self._write(conn, state, previous=previous, new_raid=action == "restart", health_change=action in {'health', 'remaining_health'})
            self.state, self.loaded_at = state, time.monotonic()
        if action in {'health', 'remaining_health'}:
            LOG.info('BOSS Maximum HP %s -> %s; %s HP remains; %s saved damage retained. Automatic regeneration stays off.',
                     previous['max_hp'], state['max_hp'], state['hp'], state['total_damage'])
        else:
            LOG.info("BOSS Host action: %s.", action)
