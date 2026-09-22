"""Shared community raid rules. Every hit is validated and committed server-side.

The boss lives in a separate record, so attacks cannot change race settings or
invalidate administrator forms. One web instance serves the whole community.
"""
import copy
import hashlib
import hmac
import ipaddress
import json
import logging
import math
import re
import secrets
import threading
import time

LOG = logging.getLogger("redhunllef")
DEFAULT_HP = 2_400_000
COOLDOWN = 60
DAILY_ATTACKS = 40
DAY = 86400
WARD_SECONDS = 600
POLL_SECONDS = 5
BASE_DAMAGE, WEAK_DAMAGE, BURST_EVERY, BURST_BONUS = 100, 150, 10, 100
MAX_HIT = WEAK_DAMAGE + BURST_BONUS
STYLES = {"blade": "Blade", "bow": "Bow", "magic": "Magic"}
MAX_PLAYERS, MAX_NETWORKS = 2000, 4000
TOKEN = re.compile(r"[a-f0-9]{64}\Z")


def rules():
    """One contract for server validation, page instructions, and browser labels."""
    return dict(cooldown=COOLDOWN, daily_attacks=DAILY_ATTACKS, raid_day=DAY,
                poll_seconds=POLL_SECONDS, ward_seconds=WARD_SECONDS, default_hp=DEFAULT_HP,
                damage=BASE_DAMAGE, weak_damage=WEAK_DAMAGE, burst_every=BURST_EVERY,
                burst_bonus=BURST_BONUS, styles=dict(STYLES))


def badges(player):
    hits, days = player.get("attacks", 0), player.get("active_days", 0)
    return [dict(id=key, label=label, description=description, earned=earned) for key, label, description, earned in (
        ("first", "First strike", "Land your first hit.", hits >= 1),
        ("burst", "Crimson veteran", f"Land {10 * BURST_EVERY} hits for ten Crimson bursts.", hits >= 10 * BURST_EVERY),
        ("loyal", "Three-day crew", "Land a hit on three different raid days.", days >= 3),
    )]


class BossError(ValueError):
    def __init__(self, message, code="invalid", status=400, retry_after=0):
        super().__init__(message)
        self.code, self.status, self.retry_after = code, status, retry_after


def fresh_raid(now=None, health=DEFAULT_HP, history=None):
    now = int(time.time() if now is None else now)
    return dict(schema=1, id=secrets.token_hex(16), salt=secrets.token_hex(32),
                version=1, max_hp=health, hp=health, created_at=now, started_at=0,
                finished_at=0, paused=False, total_attacks=0, total_damage=0,
                players={}, networks={}, recent=[], history=list(history or [])[-10:])


def _integer(value, minimum=0, maximum=10**12):
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
    maximum = _integer(value.get("max_hp"), 1, 100_000_000)
    hp = _integer(value.get("hp"), 0, maximum)
    for field in ("created_at", "started_at", "finished_at", "total_attacks", "total_damage"):
        _integer(value.get(field))
    if type(value.get("paused")) is not bool or value["total_damage"] != maximum - hp:
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
            _integer(record.get("used"), 0, DAILY_ATTACKS)
    for player in players.values():
        _integer(player.get("attacks"), 1)
        _integer(player.get("damage"), 1, maximum)
        if "active_days" in player:
            _integer(player["active_days"], 1, player["attacks"])
        receipt = player.get("last_hit")
        if not isinstance(receipt, dict) or not isinstance(receipt.get("style"), str) or receipt["style"] not in STYLES:
            raise ValueError("The community boss recovery has an invalid attack receipt.")
        if not isinstance(player.get("request_id"), str) or not re.fullmatch(r"[A-Za-z0-9_-]{8,64}", player["request_id"]):
            raise ValueError("The community boss recovery has an invalid request receipt.")
        _integer(receipt.get("damage"), 1, MAX_HIT)
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
        _integer(hit.get("damage"), 1, MAX_HIT)
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
            row = self.store.query(conn, "SELECT document FROM rh_boss WHERE name=?", (store.key,)).fetchone()
            if not row:
                value = fresh_raid()
                self.store.query(conn, "INSERT INTO rh_boss VALUES (?, ?)", (store.key, json.dumps(value)))
            else:
                value = validate_boss(json.loads(row[0]))
        self.state, self.loaded_at = value, time.monotonic()

    def _read(self, conn, locked=False):
        suffix = " FOR UPDATE" if locked and self.store.pg else ""
        row = self.store.query(conn, "SELECT document FROM rh_boss WHERE name=?" + suffix, (self.store.key,)).fetchone()
        if not row:
            raise ValueError("Community boss state is missing. Restore the private recovery checkpoint.")
        return validate_boss(json.loads(row[0]))

    def _write(self, conn, state, *, previous=None, new_raid=False):
        """Only a deliberate new raid may replenish health.

        Callers already hold the storage transaction. Compare against the row
        read inside that transaction, never an older viewer/cache snapshot.
        """
        previous = self._read(conn, locked=True) if previous is None else previous
        if state["id"] != previous["id"]:
            if not new_raid:
                raise BossError("Starting a new boss requires the host's new-raid action.", "new_raid_required", 409)
        elif (state["max_hp"] != previous["max_hp"] or state["hp"] > previous["hp"]
              or state["total_damage"] < previous["total_damage"]
              or state["total_attacks"] < previous["total_attacks"]
              or state["version"] < previous["version"]):
            LOG.error("BOSS Blocked a progress reversal. Saved damage and health were not changed.")
            raise BossError("Boss progress cannot move backwards. Existing damage was preserved.", "progress_reversal", 409)
        if state["hp"] != state["max_hp"] - state["total_damage"]:
            raise BossError("Boss health does not match saved damage. Existing progress was preserved.", "invalid_health", 409)
        self.store.query(conn, "UPDATE rh_boss SET document=? WHERE name=?",
                         (json.dumps(state, separators=(",", ":"), allow_nan=False), self.store.key))

    def _load(self, force=False):
        # Most 5-second viewer polls use memory, not another SQLite read. A
        # periodic reload also picks up writes from another process during tests
        # or a short deployment overlap. Local mode still requires one instance.
        if force or time.monotonic() - self.loaded_at >= POLL_SECONDS:
            with self.store.connection() as conn:
                self.state = self._read(conn)
            self.loaded_at = time.monotonic()

    @staticmethod
    def _project(state, guest, address, now):
        keys = list(STYLES)
        weakness = keys[(int(now) // WARD_SECONDS + int(state["id"][:8], 16)) % 3]
        day = max(0, int((now - state["started_at"]) // DAY)) if state["started_at"] else 0
        reset = state["started_at"] + (day + 1) * DAY if state["started_at"] else 0
        player_key = _key(state, "player", guest) if guest else ""
        network_key = _key(state, "network", network_identity(address)) if address else ""
        player, network = state["players"].get(player_key, {}), state["networks"].get(network_key, {})
        used = lambda record: record.get("used", 0) if record.get("day") == day else 0
        remaining = max(0, DAILY_ATTACKS - max(used(player), used(network)))
        ready = max(player.get("last_attack", 0), network.get("last_attack", 0)) + COOLDOWN
        if remaining == 0:
            ready = max(ready, reset)
        phase = "Awakening" if state["hp"] > state["max_hp"] * .75 else "Enraged" if state["hp"] > state["max_hp"] * .25 else "Last stand"
        status = "victory" if state["hp"] == 0 else "paused" if state["paused"] else "active" if state["started_at"] else "waiting"
        leaders = sorted(state["players"].items(), key=lambda item: (-item[1]["damage"], item[0]))[:10]
        return dict(server_time=now, raid_id=state["id"], version=state["version"], status=status, connection_ready=bool(address),
                    hp=state["hp"], max_hp=state["max_hp"], phase=phase, started_at=state["started_at"],
                    finished_at=state["finished_at"], day=day + 1, resets_at=reset,
                    total_damage=state["total_damage"], total_attacks=state["total_attacks"], raiders=len(state["players"]),
                    weakness=weakness, weakness_label=STYLES[weakness], ward_changes_at=(int(now) // WARD_SECONDS + 1) * WARD_SECONDS,
                    rules=rules(),
                    milestones=[dict(percent=p, label=label, reached=state["total_damage"] * 100 >= state["max_hp"] * p)
                                for p, label in ((25, "Armor cracked"), (50, "The crew rallies"), (75, "Final stand"), (100, "Crimson conquered"))],
                    you=dict(name=_name(player_key) if guest else "Spectator", damage=player.get("damage", 0),
                             attacks=player.get("attacks", 0), remaining=remaining, ready_at=ready,
                             burst_in=BURST_EVERY - player.get("attacks", 0) % BURST_EVERY,
                             active_days=player.get("active_days", 1 if player else 0), badges=badges(player),
                             last_request=player.get("request_id", ""), last_hit=copy.deepcopy(player.get("last_hit")),
                             can_attack=bool(guest and status in {"waiting", "active"} and remaining and now >= ready)),
                    leaders=[dict(name=_name(key), damage=p["damage"], attacks=p["attacks"], you=key == player_key) for key, p in leaders],
                    recent=copy.deepcopy(state["recent"]), history=copy.deepcopy(state["history"]))

    def summary(self):
        """Small anonymous homepage projection: no guest, receipt, or network data."""
        with self.lock:
            self._load()
            state = self.state
            status = "victory" if state["hp"] == 0 else "paused" if state["paused"] else "active" if state["started_at"] else "waiting"
            return dict(raid_id=state["id"], hp=state["hp"], max_hp=state["max_hp"],
                        status=status, raiders=len(state["players"]), total_attacks=state["total_attacks"],
                        total_damage=state["total_damage"], version=state["version"])

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

    def attack(self, guest, address, style, raid_id, request_id):
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
                pk, nk = _key(state, "player", guest), _key(state, "network", network_identity(address))
                existing = state["players"].get(pk, {})
                # A retry of an acknowledged click never lands a second hit,
                # including retries after victory or after the cooldown ends.
                if existing.get("request_id") == request_id:
                    return dict(ok=True, duplicate=True, hit=copy.deepcopy(existing["last_hit"]), state=view)
                if view["status"] in {"paused", "victory"}:
                    raise BossError("The host paused the raid." if state["paused"] and state["hp"] else "The community has already defeated this boss.", view["status"], 409)
                if not view["you"]["can_attack"]:
                    retry = max(1, math.ceil(view["you"]["ready_at"] - now))
                    message = f"Your browser or shared connection has used today's {DAILY_ATTACKS} attacks. Return next raid day." if not view["you"]["remaining"] else "Your browser or shared connection is cooling down. Wait for the timer."
                    raise BossError(message, "daily_limit" if not view["you"]["remaining"] else "cooldown", 429, retry)
                day = view["day"] - 1
                state["networks"] = {key: p for key, p in state["networks"].items() if p["day"] >= day - 1}
                if (pk not in state["players"] and len(state["players"]) >= MAX_PLAYERS) or (nk not in state["networks"] and len(state["networks"]) >= MAX_NETWORKS):
                    raise BossError("This raid has reached its player capacity. The host can start a new raid.", "capacity", 409)
                player = state["players"].setdefault(pk, dict(attacks=0, damage=0))
                network = state["networks"].setdefault(nk, {})
                # Older saves cannot reconstruct every past participation day.
                # Credit one known day, then count future distinct days exactly.
                active_days = player.get("active_days", 1 if player["attacks"] else 0)
                player["active_days"] = active_days + int(player.get("day") != day)
                burst = (player["attacks"] + 1) % BURST_EVERY == 0
                weak = style == view["weakness"]
                damage = min(state["hp"], (WEAK_DAMAGE if weak else BASE_DAMAGE) + (BURST_BONUS if burst else 0))
                hit = dict(style=style, damage=damage, weakness=weak, burst=burst, at=int(now))
                for record in (player, network):
                    record.update(used=(record.get("used", 0) if record.get("day") == day else 0) + 1,
                                  day=day, last_attack=now)
                # Preserve fractional seconds so early clicks never shorten
                # the server-enforced cooldown.
                player.update(attacks=player["attacks"] + 1, damage=player["damage"] + damage,
                              request_id=request_id, last_hit=hit)
                # Cumulative committed damage is never reset by cooldowns,
                # weakness rotations, midnight, idle time, or source refreshes.
                total_damage = state["total_damage"] + damage
                state.update(hp=state["max_hp"] - total_damage, total_damage=total_damage,
                             total_attacks=state["total_attacks"] + 1, version=state["version"] + 1,
                             started_at=state["started_at"] or int(now))
                state["recent"] = [dict(name=_name(pk), **hit)] + state["recent"][:11]
                if not state["hp"]:
                    state["finished_at"] = int(now)
                self._write(conn, state, previous=self.state)
            self.state, self.loaded_at = state, time.monotonic()
            if state["finished_at"]:
                LOG.info("BOSS Victory; %s attacks from %s raider profiles.", state["total_attacks"], len(state["players"]))
            elif state["total_attacks"] == 1:
                LOG.info("BOSS Shared raid started; HP=%s, cooldown=%ss, daily attacks=%s; health regeneration=off.",
                         state["max_hp"], COOLDOWN, DAILY_ATTACKS)
            return dict(ok=True, duplicate=False, hit=hit, state=self._project(state, guest, address, now))

    def control(self, action, raid_id, health=DEFAULT_HP):
        if action not in {"pause", "resume", "restart"}:
            raise BossError("Choose a valid boss action.")
        if action == "restart":
            _integer(health, 100_000, 100_000_000)
        with self.lock:
            with self.store.connection(transaction=True) as conn:
                state = self._read(conn, locked=True)
                if state["id"] != raid_id:
                    raise BossError("Another raid has started. Reload before changing it.", "new_raid", 409)
                previous = copy.deepcopy(state)
                if action == "restart":
                    self.store.backup_in(conn, "before-boss-restart", {"community_boss": state})
                    history = state["history"]
                    if state["total_attacks"]:
                        history.append(dict(outcome="Victory" if not state["hp"] else "Restarted", started_at=state["started_at"],
                                            ended_at=state["finished_at"] or int(time.time()), max_hp=state["max_hp"],
                                            damage=state["total_damage"], attacks=state["total_attacks"], raiders=len(state["players"])))
                    state = fresh_raid(health=health, history=history)
                else:
                    state["paused"], state["version"] = action == "pause", state["version"] + 1
                self._write(conn, state, previous=previous, new_raid=action == "restart")
            self.state, self.loaded_at = state, time.monotonic()
        LOG.info("BOSS Host action: %s.", action)
