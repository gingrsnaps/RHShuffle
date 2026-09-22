"""One runtime, two independent minute jobs, and atomic published snapshots."""
import copy
from decimal import Decimal
import logging
import secrets
import threading
import time

from config import INTERVAL, RELEASE
from integrations import Providers, ProviderError
from storage import Store, StoreError, Conflict
from race import calculate, empty, freshness, normalize, phase, rank, token
from race_support import fmt_et, money, race_key

LOG = logging.getLogger("redhunllef")


class Runtime:
    def __init__(self, config):
        self.config, self.store, self.providers = config, Store(config), Providers(config)
        self.lock, self.stop_event = threading.RLock(), threading.Event()
        self.revision, self.admin = self.store.admin()
        self.shuffle = self.store.live("shuffle") or empty(self.admin["site_settings"])
        if self.shuffle.get("key") != race_key(self.admin["site_settings"]):
            self.shuffle = empty(self.admin["site_settings"])
        self.restore_edits()
        self.kick = self.store.live("kick") or dict(updated_at=0, attempt_at=0, error="", live=False)
        self.events = {name: threading.Event() for name in ("shuffle", "kick")}
        self.threads, self.started = {}, False
        self.instance_id = secrets.token_hex(8)
        self.jobs = {name: dict(state="starting", next_check=0, duration_ms=0, http_status=None,
                               retry_after=0, attempt_at=0, error="", not_before=0,
                               requested=0, completed=0, runs=0, completed_at=0, result="waiting",
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

    def sync(self):
        revision, admin = self.store.admin()
        with self.lock:
            if revision != self.revision:
                self.revision, self.admin = revision, admin
                saved = self.store.live("shuffle")
                self.shuffle = saved if saved and saved.get("key") == race_key(admin["site_settings"]) else empty(admin["site_settings"])
                self.restore_edits()
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
        site.update(start_et=fmt_et(site["start_time"]), end_et=fmt_et(site["end_time"]),
                    total_prize=money(sum(Decimal(v) for v in site["prizes"].values())), race_state=phase(site))
        # Projection is an explicit allowlist. Provider source rows, raw totals,
        # admin names, password hashes, and keys cannot reach the public API.
        rows = [dict(rank=r["rank"], username=r["username"][:2] + "******", wager=r["wager"]) for r in value["rows"][:15]]
        if phase(site) in {"upcoming", "unconfigured"}:
            rows = []
        available = bool(kick.get("updated_at") and not kick.get("error") and time.time() - kick["updated_at"] <= 180
                         and kick.get("channel") == site["kick_channel_slug"])
        stream = {k: kick.get(k) for k in ("live", "title", "viewers", "updated_at")}
        stream["available"] = available
        fresh = freshness(value)
        fresh.pop("error", None)
        return dict(release=RELEASE, server_time=int(time.time()), interval=INTERVAL, site=site, rows=rows,
                    leaderboard_message=self.empty_message(site, value),
                    freshness=fresh, stream=stream, revision=token([site, rows, fresh, stream]))

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
                            storage="PostgreSQL" if self.store.pg else "Local file (automatic)", settings_revision=self.revision,
                            start_et=fmt_et(self.admin["site_settings"]["start_time"]), end_et=fmt_et(self.admin["site_settings"]["end_time"]),
                            received=self.shuffle.get("received", 0), accepted=self.shuffle.get("accepted", 0),
                            rejected=self.shuffle.get("rejected", {}), missing_campaign=self.shuffle.get("missing_campaign", 0)))
            data["diagnostics"].update(race_state=phase(self.admin["site_settings"]),
                campaign_filter=self.admin["site_settings"]["campaign_code_filter"], endpoint_kind=self.config.endpoint,
                aggregation=self.config.aggregation, qualifying_players=data["count"], loaded_players=len(data["rows"]))
            return data

    def job_status(self):
        with self.lock:
            return {name: {**{k: v for k, v in job.items() if k != "not_before"},
                           "pending": self.events[name].is_set(),
                           "worker_alive": bool(self.threads.get(name) and self.threads[name].is_alive()),
                           "last_success": (self.shuffle if name == "shuffle" else self.kick).get("updated_at", 0)}
                    for name, job in self.jobs.items()}

    def check(self, name):
        began, now = time.monotonic(), int(time.time())
        with self.lock:
            ticket = self.jobs[name]["requested"]
            self.jobs[name].update(state="checking", attempt_at=now, next_check=0,
                                   runs=self.jobs[name]["runs"]+1)
        error, status, retry, warning, result, revision = "", None, 0, "", "waiting", None
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
                    if phase(site) in {"upcoming", "unconfigured"}:
                        value = empty(site)
                        value["attempt_at"] = now
                        result = phase(site)
                    else:
                        LOG.info("SHUFFLE Checking saved window %s -> %s.", fmt_et(site["start_time"]), fmt_et(min(site["end_time"], now)))
                        incoming = normalize(self.providers.shuffle(site), site, self.config.raw_fallback)
                        status = self.providers.last_http_status()
                        value = calculate({**empty(site), **incoming, "updated_at":int(time.time()), "attempt_at":now, "ok":True}, admin, self.config)
                        value["previous_top"] = previous["rows"][:15] if previous["rows"][:15] != value["rows"][:15] else previous.get("previous_top", [])
                        warning = value["warning"]
                        result = "empty" if not value["rows"] else "updated" if previous["rows"] != value["rows"] else "unchanged"
                    with self.lock:
                        self.store.publish(name, value, revision)
                        self.shuffle = value
                    LOG.info("SHUFFLE %s; %s accepted / %s received; race %s → %s.",
                             "Updated" if previous["rows"] != value["rows"] else "Confirmed unchanged",
                             value.get("accepted", 0), value.get("received", 0), fmt_et(site["start_time"]), fmt_et(site["end_time"]))
                    if not value["rows"]:
                        LOG.info("SHUFFLE %s", self.empty_message(site, value))
                else:
                    value = {**self.providers.kick(site), "updated_at":int(time.time()), "attempt_at":now, "error":""}
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
                LOG.warning("%s %s Previous data retained; retry in %ss.", name.upper(), error, max(INTERVAL, retry))
        finally:
            duration = round((time.monotonic() - began) * 1000)
            with self.lock:
                self.jobs[name].update(state="delayed" if error else "scheduled", error=error, http_status=status,
                                       duration_ms=duration, retry_after=retry, result=result,
                                       completed=max(ticket, self.jobs[name]["completed"]), completed_at=int(time.time()))
            if warning:
                LOG.warning("SHUFFLE %s", warning)
            LOG.info("%s Check took %sms. Automatic checks stay enabled.", name.upper(), duration)
        return max(INTERVAL, retry) if error else 0

    def request_refresh(self, name=None):
        if self.started:
            self.start()
        targets = {}
        for service in (name,) if name else self.events:
            with self.lock:
                job = self.jobs[service]
                scope = race_key(self.admin["site_settings"]) if service == "shuffle" else self.admin["site_settings"]["kick_channel_slug"]
                # A new race should not wait on an ordinary error from the old
                # dates. Explicit provider Retry-After/429 limits remain binding.
                if job["checked_scope"] != scope and not job["retry_after"] and job["http_status"] != 429:
                    job["not_before"] = 0
                if not self.events[service].is_set():
                    job["requested"] += 1
                targets[service] = job["requested"]
                if job["state"] != "checking":
                    job["state"] = "queued"
                    job["next_check"] = int(time.time() + max(0, job["not_before"]-time.monotonic()))
                # Even an active check must retain one follow-up request. The
                # event coalesces repeated clicks without concurrent API calls.
                self.events[service].set()
        return dict(runtime_id=self.instance_id, requests=targets)

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
                if retry:
                    self.jobs[name]["not_before"] = finished + retry
                    due = finished + retry
                else:
                    self.jobs[name]["not_before"] = 0
                    due = anchor + (int(max(0, finished - anchor) // INTERVAL) + 1) * INTERVAL
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
            LOG.info("LIVE Automatic Shuffle and Kick checks started; cadence=%ss.", INTERVAL)

    def stop(self):
        self.stop_event.set()
        for event in self.events.values():
            event.set()
        for thread in self.threads.values():
            thread.join(timeout=1)
