"""One runtime, independent live jobs, and cached completed-week history."""
import copy
from decimal import Decimal
import logging
import secrets
import threading
import time

from config import INTERVAL, KICK_INTERVAL, RANK_MOVEMENT_SECONDS, RELEASE
from integrations import Providers, ProviderError
from storage import Store, StoreError, Conflict
from race import calculate, empty, freshness, normalize, phase, rank, token, top_snapshot
from movement import preserve_movement_event, stamp_movement_event, public_movement_event, admin_event_record
from race_support import fmt_et, money, race_key
from weekly_history import WeeklyHistory
from empiredrop import EmpireDropBoard

LOG = logging.getLogger("redhunllef")


class Runtime:
    def __init__(self, config):
        self.config, self.store, self.providers = config, Store(config), Providers(config)
        self.history = WeeklyHistory(config, self.store, self.providers)
        self.empiredrop = EmpireDropBoard(config, self.store)
        self.lock, self.stop_event = threading.RLock(), threading.Event()
        self.revision, self.admin = self.store.admin()
        self.shuffle = self.store.live("shuffle") or empty(self.admin["site_settings"])
        if self.shuffle.get("key") != race_key(self.admin["site_settings"]):
            self.shuffle = empty(self.admin["site_settings"])
        self.restore_edits()
        self.ensure_top15(self.shuffle)
        self.kick = self.store.live("kick") or dict(updated_at=0, attempt_at=0, error="", live=False)
        self.events = {name: threading.Event() for name in ("shuffle", "kick")}
        self.threads, self.started = {}, False
        self.instance_id = secrets.token_hex(8)
        # Process-local monotonic public snapshot ordering. The runtime id makes a
        # restart explicit so browsers never compare a new process with an old one.
        self._public_signature = ""
        self._public_sequence = 0
        self.activity_log = None  # Injected after construction by Flask.
        self._movement_events = []  # Last 20 admin-only Shuffle movement events.
        self.jobs = {name: dict(state="starting", next_check=0, duration_ms=0, http_status=None,
                               retry_after=0, attempt_at=0, error="", not_before=0,
                               requested=0, completed=0, runs=0, completed_at=0, result="waiting",
                               failure_streak=0, request_meta={}, provider_reason=None,
                               checked_scope="", checked_start=0, checked_end=0, checked_channel="")
                     for name in self.events}

    def restore_edits(self):
        # Imported Top 15 backups may omit the separate overrides view. Keep
        # the saved ranking intact while making every saved edit accessible.
        _, edits, _ = rank(self.shuffle.get("source", []), self.admin["overrides"],
                           self.config.aggregation, self.config.limit)
        if self.shuffle.get("snapshot_only") or phase(self.admin["site_settings"]) in {"upcoming", "unconfigured"}:
            ranks = {row["username"]: row["rank"] for row in self.shuffle["rows"]}
            edits = [{**row, "rank": ranks.get(row["username"])} for row in edits]
        self.shuffle["edits"] = edits

    def ensure_top15(self, value, previous=None):
        """Attach one validated, ordered Top 15 with non-restarting movement events."""
        source_rows = list(value.get("rows", []))
        previous_rows = (previous or {}).get("rows", [])[:15]
        rows, revision = top_snapshot(source_rows, previous_rows, 15)
        prior_revision = (previous or {}).get("top15_revision", "")
        prior_sequence = int((previous or {}).get("top15_sequence", 0) or 0)
        prior_movement_sequence = int((previous or {}).get("top15_movement_sequence", 0) or 0)
        prior_movement_count = int((previous or {}).get("top15_movement_count", 0) or 0)

        if previous is None and value.get("top15_revision") == revision:
            # Startup/reload of an already-saved snapshot must not invent a new
            # movement window or erase one that still has a server timestamp.
            saved = {r.get("username"): r for r in source_rows[:15] if isinstance(r, dict)}
            for row in rows:
                preserve_movement_event(row, saved.get(row.get("username"), {}), RANK_MOVEMENT_SECONDS)
            sequence = int(value.get("top15_sequence", 0) or (1 if rows else 0))
            movement_sequence = int(value.get("top15_movement_sequence", 0) or 0)
            movement_count = int(value.get("top15_movement_count", 0) or 0)
        elif previous is not None and prior_revision == revision:
            # Re-confirming identical standings preserves the original event.
            saved = {r.get("username"): r for r in previous_rows if isinstance(r, dict)}
            for row in rows:
                preserve_movement_event(row, saved.get(row.get("username"), {}), RANK_MOVEMENT_SECONDS)
            sequence = prior_sequence or (1 if rows else 0)
            movement_sequence = prior_movement_sequence
            movement_count = prior_movement_count
        else:
            stamp = int(value.get("updated_at", 0) or time.time())
            movement_count = 0
            for row in rows:
                stamp_movement_event(row, "shuffle", row.get("username", ""), stamp, RANK_MOVEMENT_SECONDS)
                if row.get("movement_event_id"):
                    movement_count += 1
            sequence = prior_sequence + (1 if revision != prior_revision else 0)
            if rows and not sequence:
                sequence = 1
            movement_sequence = prior_movement_sequence + (1 if movement_count else 0)
            if movement_count and not movement_sequence:
                movement_sequence = 1

        value["rows"] = rows + source_rows[15:]
        value["top15_revision"] = revision
        value["top15_sequence"] = sequence
        value["top15_movement_sequence"] = movement_sequence
        value["top15_movement_count"] = movement_count
        value.setdefault("top15_changed_at", value.get("changed_at", value.get("updated_at", 0)))
        return value

    def _record_shuffle_movements(self, rows):
        """Keep a tiny process-local admin history; never expose full names publicly."""
        with self.lock:
            known = {item.get("event_id") for item in self._movement_events}
            for row in list(rows or [])[:15]:
                record = admin_event_record("shuffle", row)
                if not record or record["event_id"] in known:
                    continue
                record["username"] = str(row.get("username") or "")
                self._movement_events.append(record)
                known.add(record["event_id"])
            self._movement_events = self._movement_events[-20:]

    def movement_diagnostics(self):
        with self.lock:
            return {
                "shuffle": {
                    "standings_sequence": int(self.shuffle.get("top15_sequence", 0) or 0),
                    "movement_sequence": int(self.shuffle.get("top15_movement_sequence", 0) or 0),
                    "movement_count": int(self.shuffle.get("top15_movement_count", 0) or 0),
                    "events": copy.deepcopy(list(reversed(self._movement_events))),
                }
            }

    def sync(self):
        revision, admin = self.store.admin()
        with self.lock:
            if revision != self.revision:
                self.revision, self.admin = revision, admin
                saved = self.store.live("shuffle")
                self.shuffle = saved if saved and saved.get("key") == race_key(admin["site_settings"]) else empty(admin["site_settings"])
                self.restore_edits()
                self.ensure_top15(self.shuffle)
            return self.revision, copy.deepcopy(self.admin)

    def commit(self, admin, expected, *, snapshot=None, reason=None):
        with self.lock:
            revision = self.store.save(admin, expected, snapshot=snapshot, backup_reason=reason)
            self.revision, self.admin = revision, copy.deepcopy(admin)
            if snapshot is not None:
                self.shuffle = copy.deepcopy(snapshot)

    def public(self):
        with self.lock:
            site, value, kick = copy.deepcopy(self.admin["site_settings"]), copy.deepcopy(self.shuffle), copy.deepcopy(self.kick)
            settings_revision = self.revision
            shuffle_job = copy.deepcopy(self.jobs.get("shuffle", {}))
        site.update(start_et=fmt_et(site["start_time"]), end_et=fmt_et(site["end_time"]),
                    total_prize=money(sum(Decimal(v) for v in site["prizes"].values())), race_state=phase(site))
        # Projection is an explicit allowlist. Provider source rows, raw totals,
        # admin names, password hashes, and keys cannot reach the public API.
        rows = [dict(rank=r["rank"], username=r["username"][:2] + "******", wager=r["wager"],
                     movement=r.get("movement"), new_entry=bool(r.get("new_entry")),
                     previous_rank=r.get("previous_rank"),
                     movement_at=int(r.get("movement_at", 0) or 0),
                     movement_expires_at=int(r.get("movement_expires_at", 0) or 0),
                     movement_event_id=str(r.get("movement_event_id") or ""),
                     movement_event=public_movement_event(r))
                for r in value["rows"][:15]]
        if phase(site) in {"upcoming", "unconfigured"}:
            rows = []
        ranked = {row["rank"]: row for row in rows}
        top15 = [ranked.get(rank) or dict(rank=rank, username="Open position", wager="$0.00",
                                          movement=None, new_entry=False, movement_at=0,
                                          movement_expires_at=0, movement_event_id="", movement_event=None, open=True)
                 for rank in range(1, 16)]
        available = bool(kick.get("updated_at") and not kick.get("error") and time.time() - kick["updated_at"] <= 180
                         and kick.get("channel") == site["kick_channel_slug"])
        stream = {k: kick.get(k) for k in ("live", "title", "viewers", "updated_at")}
        stream["available"] = available
        fresh = freshness(value)
        fresh.pop("error", None)
        empire = self.empiredrop.public(site)
        # Build the complete non-clock payload first. Its signature includes every
        # public field, so a strong ETag can never claim that different JSON bytes
        # are the same representation. Sequence ordering protects clients from an
        # older response arriving after a newer one.
        payload = dict(release=RELEASE, interval=INTERVAL, site=site, rows=rows, top15=top15,
                       movement_window_seconds=RANK_MOVEMENT_SECONDS,
                       provider_intervals=dict(shuffle=INTERVAL, kick=KICK_INTERVAL,
                                               empiredrop_min=self.empiredrop.minimum_interval),
                       provider_timing=dict(shuffle=dict(
                           updated_at=int(value.get("updated_at", 0) or 0),
                           attempt_at=int(value.get("attempt_at", 0) or 0),
                           next_check=int(shuffle_job.get("next_check", 0) or 0),
                           refresh_interval=INTERVAL,
                           state=str(shuffle_job.get("state", "scheduled")))),
                       settings_revision=settings_revision,
                       shuffle_revision=value.get("top15_revision") or token(rows),
                       shuffle_sequence=int(value.get("top15_sequence", 0) or 0),
                       shuffle_movement_sequence=int(value.get("top15_movement_sequence", 0) or 0),
                       shuffle_movement_count=int(value.get("top15_movement_count", 0) or 0),
                       shuffle_changed_at=value.get("top15_changed_at", value.get("changed_at", 0)),
                       empiredrop=empire,
                       leaderboard_message=self.empty_message(site, value),
                       freshness=fresh, stream=stream)
        signature = token(payload)
        with self.lock:
            if signature != self._public_signature:
                self._public_signature = signature
                self._public_sequence += 1
            sequence = self._public_sequence
            runtime_id = self.instance_id
        payload.update(runtime_id=runtime_id, snapshot_sequence=sequence,
                       revision=f"{runtime_id}-{sequence}-{signature}",
                       # Fractional seconds reduce countdown skew caused by integer
                       # timestamp quantization on fast local/public-state requests.
                       server_time=time.time())
        return payload

    def public_standings(self):
        """Small live-feed projection used by open leaderboard pages every five seconds."""
        value = self.public()
        empire = value.get("empiredrop") or {}
        shuffle = {
            "standings_revision": value.get("shuffle_revision", ""),
            "standings_sequence": int(value.get("shuffle_sequence", 0) or 0),
            "movement_sequence": int(value.get("shuffle_movement_sequence", 0) or 0),
            "movement_count": int(value.get("shuffle_movement_count", 0) or 0),
            "changed_at": int(value.get("shuffle_changed_at", 0) or 0),
            "updated_at": int((value.get("provider_timing") or {}).get("shuffle", {}).get("updated_at", 0) or 0),
            "next_check_at": int((value.get("provider_timing") or {}).get("shuffle", {}).get("next_check", 0) or 0),
            "refresh_interval": INTERVAL,
            "top15": copy.deepcopy(value.get("top15") or []),
            "prizes": copy.deepcopy((value.get("site") or {}).get("prizes") or {}),
            "total_prize": (value.get("site") or {}).get("total_prize", "$0.00"),
        }
        empire_public = {key: copy.deepcopy(empire.get(key)) for key in (
            "rows", "prizes", "standings_revision", "standings_sequence", "movement_sequence",
            "movement_count", "standings_changed_at", "updated_at", "next_check_at",
            "refresh_interval", "minimum_refresh_interval", "race_meta", "label")}
        return {
            "release": RELEASE,
            "runtime_id": self.instance_id,
            "movement_window_seconds": RANK_MOVEMENT_SECONDS,
            "sync_interval_seconds": 5,
            "shuffle": shuffle,
            "empiredrop": empire_public,
            "server_time": time.time(),
        }

    @staticmethod
    def empty_message(site, snapshot):
        """Explain an empty board without inventing results or exposing records."""
        state = phase(site)
        if state == "unconfigured":
            return "The race schedule has not been configured."
        if state == "upcoming":
            return "This race has not started. Wagers will load after " + fmt_et(site["start_time"]) + "."
        if snapshot["rows"]:
            return ""
        if snapshot.get("error"):
            return "Shuffle updates are delayed. No successful leaderboard is available for this race window yet."
        if not snapshot.get("updated_at"):
            return "Waiting for Shuffle's first successful update for this race window."
        if not snapshot.get("received"):
            return "Shuffle returned no wagers for " + fmt_et(site["start_time"]) + " to " + fmt_et(site["end_time"]) + "."
        if not snapshot.get("accepted"):
            return "None of the returned wagers match this race's saved campaign filter."
        return "No returned wagers currently meet the $0.01 weighted qualification for this race."

    def status(self):
        if self.started:
            self.start()  # Recover a stopped worker without starting jobs in factory-only tests.
        with self.lock:
            data = self.public()
            data["runtime_id"] = self.instance_id
            data.update(rows=copy.deepcopy(self.shuffle["rows"]), edits=copy.deepcopy(self.shuffle.get("edits", [])),
                        red=copy.deepcopy(self.shuffle.get("red", [])), red_total=self.shuffle.get("red_total", 0),
                        count=self.shuffle.get("count", len(self.shuffle["rows"])), snapshot_only=self.shuffle.get("snapshot_only", False),
                        freshness=freshness(self.shuffle), jobs=self.job_status(),
                        diagnostics=dict(release=RELEASE, credentials=self.config.diagnostics(),
                            storage="Local JSON file (automatic)", settings_revision=self.revision,
                            start_et=fmt_et(self.admin["site_settings"]["start_time"]), end_et=fmt_et(self.admin["site_settings"]["end_time"]),
                            received=self.shuffle.get("received", 0), accepted=self.shuffle.get("accepted", 0),
                            rejected=self.shuffle.get("rejected", {}), missing_campaign=self.shuffle.get("missing_campaign", 0),
                            distinct_source_players=len({row.get("username") for row in self.shuffle.get("source", []) if isinstance(row, dict) and row.get("username")}),
                            additional_player_rows=max(0, self.shuffle.get("accepted", 0) - len({row.get("username") for row in self.shuffle.get("source", []) if isinstance(row, dict) and row.get("username")}))))
            data["diagnostics"].update(race_state=phase(self.admin["site_settings"]),
                campaign_filter=self.admin["site_settings"]["campaign_code_filter"], endpoint_kind=self.config.endpoint,
                aggregation=self.config.aggregation, qualifying_players=data["count"], loaded_players=len(data["rows"]),
                top15_filled=min(15, len(data["rows"])), top15_revision=self.shuffle.get("top15_revision", ""),
                top15_sequence=int(self.shuffle.get("top15_sequence", 0) or 0),
                top15_movement_sequence=int(self.shuffle.get("top15_movement_sequence", 0) or 0),
                top15_movement_count=int(self.shuffle.get("top15_movement_count", 0) or 0),
                top15_changed_at=self.shuffle.get("top15_changed_at", self.shuffle.get("changed_at", 0)))
            data['history'] = self.history.diagnostics()
            data['movement_diagnostics'] = self.movement_diagnostics()
            return data

    def job_status(self):
        with self.lock:
            return {name: {**{k: v for k, v in job.items() if k != "not_before"},
                           "pending": self.events[name].is_set(),
                           "worker_alive": bool(self.threads.get(name) and self.threads[name].is_alive()),
                           "changed_at": (self.shuffle if name == "shuffle" else self.kick).get("changed_at", 0),
                           "last_success": (self.shuffle if name == "shuffle" else self.kick).get("updated_at", 0)}
                    for name, job in self.jobs.items()}

    @staticmethod
    def cadence(name):
        return KICK_INTERVAL if name == "kick" else INTERVAL

    def check(self, name):
        began, now = time.monotonic(), int(time.time())
        cadence = self.cadence(name)
        with self.lock:
            ticket = self.jobs[name]["requested"]
            self.jobs[name].update(state="checking", attempt_at=now, next_check=0,
                                   runs=self.jobs[name]["runs"]+1)
        error, status, retry, warning, result, revision = "", None, 0, "", "waiting", None
        failure_code, request_meta = None, {}
        try:
            with self.store.job(name) as acquired:
                revision, admin = self.sync()
                site = admin["site_settings"]
                with self.lock:
                    self.jobs[name].update(checked_scope=race_key(site) if name == "shuffle" else site["kick_channel_slug"],
                        checked_start=site["start_time"] if name == "shuffle" else 0,
                        checked_end=min(site["end_time"], now) if name == "shuffle" else 0,
                        checked_channel=site["kick_channel_slug"] if name == "kick" else "")
                if not acquired:
                    saved = self.store.live(name)
                    with self.lock:
                        if saved and (name == "kick" or saved.get("key") == race_key(site)):
                            setattr(self, name, saved)
                    result = "shared"
                    return 0
                if name == "shuffle":
                    with self.lock:
                        previous = copy.deepcopy(self.shuffle)
                    top_changed = False
                    if phase(site) in {"upcoming", "unconfigured"}:
                        value = empty(site)
                        value["attempt_at"] = now
                        self.ensure_top15(value, previous)
                        top_changed = previous.get("top15_revision") != value.get("top15_revision")
                        value["top15_changed_at"] = now if top_changed else previous.get("top15_changed_at", 0)
                        result = phase(site)
                    else:
                        LOG.info("SHUFFLE Checking saved window %s -> %s.", fmt_et(site["start_time"]), fmt_et(min(site["end_time"], now)))
                        incoming = normalize(self.providers.shuffle(site), site, self.config.raw_fallback)
                        status = self.providers.last_http_status()
                        request_meta = self.providers.last_request_meta()
                        value = calculate({**empty(site), **incoming, "updated_at":int(time.time()), "attempt_at":now, "ok":True}, admin, self.config)
                        self.ensure_top15(value, previous)
                        # Warn once when incomplete campaign/amount records change.
                        # Store only counts, never source values or usernames.
                        missing = value.get('missing_campaign', 0)
                        invalid = sum(n for reason, n in value.get('rejected', {}).items()
                                      if reason != 'other campaign')
                        if (self.activity_log and (missing or invalid) and
                            (missing != previous.get('missing_campaign', 0) or
                             invalid != sum(n for reason, n in previous.get('rejected', {}).items()
                                            if reason != 'other campaign'))):
                            self.activity_log.record('shuffle', 'warning', 'data_quality',
                                                     code='partial', count=value.get('count', len(value.get('rows', []))),
                                                     received=value.get('received', 0), accepted=value.get('accepted', 0),
                                                     excluded=max(0, value.get('received', 0)-value.get('accepted', 0)),
                                                     unscoped=missing)
                        top_changed = previous.get("top15_revision") != value.get("top15_revision")
                        full_changed = previous.get("revision") != value.get("revision")
                        value["changed_at"] = value["updated_at"] if full_changed else previous.get("changed_at", 0)
                        value["top15_changed_at"] = value["updated_at"] if top_changed else previous.get("top15_changed_at", previous.get("changed_at", 0))
                        value["previous_top"] = previous["rows"][:15] if top_changed else previous.get("previous_top", [])
                        warning = value["warning"]
                        result = "empty" if not value["rows"] else "updated" if top_changed else "unchanged"
                    if name == "shuffle" and top_changed:
                        self._record_shuffle_movements(value.get("rows", [])[:15])
                    with self.lock:
                        self.store.publish(name, value, revision)
                        self.shuffle = value
                    LOG.info("SHUFFLE %s; %s accepted / %s received; race %s → %s.",
                             "Updated" if top_changed else "Confirmed unchanged",
                             value.get("accepted", 0), value.get("received", 0), fmt_et(site["start_time"]), fmt_et(site["end_time"]))
                    if not value["rows"]:
                        LOG.info("SHUFFLE %s", self.empty_message(site, value))
                else:
                    value = {**self.providers.kick(site), "updated_at":int(time.time()), "attempt_at":now, "error":""}
                    fields = ("live", "title", "viewers", "channel")
                    with self.lock:
                        value["changed_at"] = value["updated_at"] if any(value.get(k) != self.kick.get(k) for k in fields) else self.kick.get("changed_at", 0)
                    status, result = self.providers.last_http_status(), "live" if value["live"] else "offline"
                    with self.lock:
                        self.store.publish(name, value, revision)
                        self.kick = value
                    LOG.info("KICK Confirmed %s.", "LIVE" if value["live"] else "OFFLINE")
        except Conflict:
            self.events[name].set()
            result = "superseded"
            LOG.info("%s Settings changed during this check; checking again.", name.upper())
        except Exception as exc:
            error = str(exc) if isinstance(exc, (ProviderError, StoreError, ValueError)) else "Internal check failed (" + type(exc).__name__ + ")."
            status, retry = getattr(exc, "status", None), getattr(exc, "retry_after", 0)
            failure_code = getattr(exc, "kind", "unknown")
            request_meta = self.providers.last_request_meta() if name == "shuffle" else {}
            superseded, result = False, "failed"
            with self.lock:
                superseded = revision is not None and revision != self.revision
                if not superseded:
                    old = copy.deepcopy(getattr(self, name))
                    old.update(error=error, attempt_at=now, ok=False)
                    try:
                        # Failed responses have the same revision guard as
                        # successful ones. An old window cannot poison a new one.
                        self.store.publish(name, old, revision if revision is not None else self.revision)
                    except Conflict:
                        superseded = True
                    except StoreError:
                        setattr(self, name, old)
                    else:
                        setattr(self, name, old)
                if superseded:
                    self.events[name].set()
            if superseded:
                result = "superseded"
                LOG.info("%s Ignored a failed response for superseded settings; the current settings are queued.", name.upper())
                # A provider rate limit still applies across race windows.
                if status != 429 and not retry:
                    error = ""
            if error:
                LOG.warning("%s %s Previous data retained; retry in %ss.", name.upper(), error, max(cadence, retry))
        finally:
            duration = round((time.monotonic() - began) * 1000)
            with self.lock:
                previous_streak = int(self.jobs[name].get("failure_streak", 0) or 0)
                failure_streak = previous_streak + 1 if error else 0
                # Repeated provider failures back off without spawning overlapping
                # checks. A successful response immediately restores normal cadence.
                effective_retry = max(int(retry or 0),
                                      min(720, cadence * (2 ** min(3, max(0, failure_streak - 1))))) if error else 0
                self.jobs[name].update(state="delayed" if error else "scheduled", error=error, http_status=status,
                                       duration_ms=duration, retry_after=effective_retry, result=result,
                                       failure_streak=failure_streak,
                                       request_meta=request_meta if name == "shuffle" else {},
                                       provider_reason=failure_code if error else None,
                                       completed=max(ticket, self.jobs[name]["completed"]), completed_at=int(time.time()))
            if warning:
                LOG.warning("SHUFFLE %s", warning)
            if self.activity_log and (error or result in ('updated','empty') or
                (name=='kick' and result in ('live','offline') and
                 isinstance(value,dict) and value.get('changed_at')==value.get('updated_at'))):
                # Only meaningful changes/failures; no usernames or provider bodies.
                self.activity_log.record(name,'warning' if error else 'success',
                    'refresh_failed' if error else 'refresh_ok',duration_ms=duration,
                    http_status=status,
                    count=len(value.get('rows',[])) if not error and isinstance(value,dict) else None,
                    received=value.get('received') if not error and isinstance(value,dict) else None,
                    accepted=value.get('accepted') if not error and isinstance(value,dict) else None,
                    excluded=(max(0, value.get('received',0)-value.get('accepted',0))
                             if not error and isinstance(value,dict) and name == 'shuffle' else None),
                    unscoped=(value.get('missing_campaign',0)
                             if not error and isinstance(value,dict) and name == 'shuffle' else None),
                    code=failure_code if error else None)
            LOG.info("%s Check took %sms. Automatic checks stay enabled.", name.upper(), duration)
        return effective_retry if error else 0

    def request_refresh(self, name=None):
        if self.started:
            self.start()
        targets, joined = {}, []
        for service in (name,) if name else self.events:
            with self.lock:
                job = self.jobs[service]
                scope = race_key(self.admin["site_settings"]) if service == "shuffle" else self.admin["site_settings"]["kick_channel_slug"]
                # A new race should not wait on an ordinary error from the old
                # dates. Explicit provider Retry-After/429 limits remain binding.
                if job["checked_scope"] != scope and not job["retry_after"] and job["http_status"] != 429:
                    job["not_before"] = 0
                # A manual request joins an in-flight provider check rather than
                # queuing an immediate duplicate call. Otherwise repeated clicks
                # can create a needless follow-up request after the same response.
                if job["state"] == "checking":
                    targets[service] = job["requested"]
                    joined.append(service)
                    continue
                if not self.events[service].is_set():
                    job["requested"] += 1
                targets[service] = job["requested"]
                job["state"] = "queued"
                job["next_check"] = int(time.time() + max(0, job["not_before"]-time.monotonic()))
                self.events[service].set()
        return dict(runtime_id=self.instance_id, requests=targets, joined=joined)

    def loop(self, name):
        due = time.monotonic()
        try:
            while not self.stop_event.is_set():
                delay = max(due, self.jobs[name]["not_before"]) - time.monotonic()
                with self.lock:
                    self.jobs[name]["next_check"] = int(time.time() + max(0, delay))
                if delay > 0:
                    triggered = self.events[name].wait(min(delay, 1))
                    if not triggered:
                        continue
                    self.events[name].clear()
                    due = time.monotonic()
                    continue
                self.events[name].clear()
                anchor = due
                retry = self.check(name)
                finished = time.monotonic()
                cadence = self.cadence(name)
                if retry:
                    self.jobs[name]["not_before"] = finished + retry
                    due = finished + retry
                else:
                    self.jobs[name]["not_before"] = 0
                    # Anchor to the intended schedule instead of "request finished + cadence".
                    # A slow request therefore cannot create cumulative timer drift.
                    due = anchor + (int(max(0, finished - anchor) // cadence) + 1) * cadence
                if self.events[name].is_set():
                    due = finished
        finally:
            self.providers.close()
            self.store.close_job()
            with self.lock:
                self.jobs[name]["state"] = "stopped"

    def start(self):
        with self.lock:
            if self.stop_event.is_set():
                return
            initial = not self.started
            self.started = True
            for name in self.events:
                if self.threads.get(name) and self.threads[name].is_alive():
                    continue
                thread = threading.Thread(target=self.loop, args=(name,), daemon=True, name=name + "-updates")
                self.threads[name] = thread
                thread.start()
                if not initial:
                    LOG.warning("%s Restarted a stopped automatic worker.", name.upper())
        if initial:
            LOG.info("LIVE Automatic checks started; Shuffle=%ss, Kick=%ss.", INTERVAL, KICK_INTERVAL)
        self.history.start()
        self.empiredrop.start()

    def stop(self):
        self.stop_event.set()
        self.history.stop()
        self.empiredrop.stop()
        for event in self.events.values():
            event.set()
        for thread in self.threads.values():
            thread.join(timeout=1)
