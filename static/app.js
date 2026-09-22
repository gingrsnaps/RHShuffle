/* Shared page controller. Native navigation/forms work before this file loads. */
(() => {
  "use strict";
  const id = (name) => document.getElementById(name);
  const text = (node, value) => {
    // Only leaf labels can be text destinations. Never erase a page or form.
    if (!node) return;
    if (
      node.childElementCount ||
      ["BODY", "MAIN", "FORM", "HTML"].includes(node.tagName)
    )
      throw new Error("Invalid text destination");
    if (node.textContent !== String(value ?? ""))
      node.textContent = String(value ?? "");
  };
  const notice = (name, value) => {
    const node = id(name);
    if (node) {
      node.hidden = !value;
      text(node, value);
    }
  };
  const currency = (value) =>
    new Intl.NumberFormat("en-US", {
      style: "currency",
      currency: "USD",
    }).format(Number(value) || 0);
  const eastern = new Intl.DateTimeFormat("en-US", {
    timeZone: "America/New_York",
    month: "short",
    day: "numeric",
    year: "numeric",
    hour: "numeric",
    minute: "2-digit",
    timeZoneName: "short",
  });
  const date = (value) =>
    value
      ? eastern.format(new Date(value * 1000))
      : "Waiting for first source update";
  document.documentElement.classList.add("js");
  let toastTimer;
  function toast(message) {
    notice("toast", message);
    clearTimeout(toastTimer);
    toastTimer = setTimeout(() => notice("toast", ""), 4000);
  }
  document.addEventListener("click", async (event) => {
    const button = event.target.closest("[data-copy]");
    if (!button) return;
    try {
      await navigator.clipboard.writeText(button.dataset.copy);
      toast("Username copied.");
    } catch {
      toast("Select and copy the username manually.");
    }
  });
  let dirty = false;
  document.querySelectorAll("[data-dirty]").forEach((form) => {
    const initial = new URLSearchParams(new FormData(form)).toString();
    const update = () => {
      dirty = new URLSearchParams(new FormData(form)).toString() !== initial;
      text(id("saveLabel"), dirty ? "Unsaved changes" : "All changes saved");
    };
    form.addEventListener("input", update);
    form.addEventListener("change", update);
    form.addEventListener("reset", () => setTimeout(update, 0));
    form.addEventListener("submit", () => {
      dirty = false;
    });
  });
  window.addEventListener("beforeunload", (event) => {
    if (dirty) {
      event.preventDefault();
      event.returnValue = "";
    }
  });
  document.querySelectorAll("[data-confirm]").forEach((form) =>
    form.addEventListener("submit", (event) => {
      if (!window.confirm(form.dataset.confirm)) event.preventDefault();
    }),
  );
  id("raceForm")?.addEventListener("input", () => {
    const sum = [...id("raceForm").querySelectorAll('[name^="prize_"]')].reduce(
      (n, input) => n + Number(input.value.replace(/[$,\s]/g, "")),
      0,
    );
    text(
      id("prizeTotal"),
      Number.isFinite(sum) ? currency(sum) + " total" : "Review prize amounts",
    );
  });
  // The date picker stores Eastern local wall time. Server validation handles
  // nonexistent/ambiguous DST times; a shortcut never silently publishes a race.
  function easternInput(stamp) {
    const parts = new Intl.DateTimeFormat("en-US", {
      timeZone: "America/New_York",
      year: "numeric",
      month: "2-digit",
      day: "2-digit",
      hour: "2-digit",
      minute: "2-digit",
      hourCycle: "h23",
    }).formatToParts(new Date(stamp));
    const v = Object.fromEntries(parts.map((p) => [p.type, p.value]));
    return `${v.year}-${v.month}-${v.day}T${v.hour}:${v.minute}`;
  }
  function daysAfter(value, days) {
    const d = new Date(value + "Z");
    d.setUTCDate(d.getUTCDate() + days);
    return d.toISOString().slice(0, 16);
  }
  id("startNow")?.addEventListener("click", () => {
    id("f-start_et").value = easternInput(Date.now());
    id("f-end_et").value = daysAfter(id("f-start_et").value, 7);
    id("f-start_et").dispatchEvent(new Event("input", { bubbles: true }));
  });
  id("nextRace")?.addEventListener("click", () => {
    const start = id("f-start_et"),
      end = id("f-end_et");
    const duration = Math.max(
      1,
      Math.round(
        (new Date(end.value + "Z") - new Date(start.value + "Z")) / 86400000,
      ) || 7,
    );
    start.value = end.value || easternInput(Date.now());
    end.value = daysAfter(start.value, duration);
    start.dispatchEvent(new Event("input", { bubbles: true }));
    toast("Draft prepared. Review the dates before saving.");
  });

  if (!document.body.dataset.feed) return;
  const isAdmin = document.body.dataset.page === "admin";
  let site = {},
    offset = 0,
    sourceAt = 0,
    jobs = {},
    busy = false,
    timer,
    next = 0,
    urgentUntil = 0;
  let pollAgain = false,
    lastWork = "",
    receipt = null;
  let publicCache = null,
    publicETag = "",
    lastProviderFailure = "";
  let participantVersion = "",
    redVersion = "";
  try {
    const boot = JSON.parse(document.body.dataset.bootstrap);
    site = boot.site;
    offset = boot.server_time * 1000 - Date.now();
  } catch {}
  function clock() {
    if (document.hidden) return;
    const now = (Date.now() + offset) / 1000;
    const state =
      !site.start_time || site.end_time <= site.start_time
        ? "unconfigured"
        : now < site.start_time
          ? "upcoming"
          : now >= site.end_time
            ? "ended"
            : "active";
    const badge = id("raceBadge");
    text(badge, state.charAt(0).toUpperCase() + state.slice(1));
    if (badge) badge.className = "badge state-" + state;
    const left = Math.max(
      0,
      Math.ceil((state === "upcoming" ? site.start_time : site.end_time) - now),
    );
    text(
      id("countdown"),
      state === "unconfigured"
        ? "Set the race dates"
        : state === "ended"
          ? "Race complete"
          : `${Math.floor(left / 86400)}d ${String(Math.floor(left / 3600) % 24).padStart(2, "0")}h ${String(Math.floor(left / 60) % 60).padStart(2, "0")}m ${String(left % 60).padStart(2, "0")}s`,
    );
    text(
      id("clockLabel"),
      state === "upcoming"
        ? "STARTS IN"
        : state === "active"
          ? "RACE ENDS IN"
          : "RACE SCHEDULE",
    );
    text(
      id("raceWindow"),
      site.start_time
        ? date(site.start_time) + " → " + date(site.end_time)
        : "Choose the race dates in Race settings.",
    );
    if (id("endedNotice")) id("endedNotice").hidden = state !== "ended";
    if (sourceAt)
      text(
        id("sourceTime"),
        "Source checked " + Math.max(0, Math.floor(now - sourceAt)) + "s ago",
      );
    for (const [name, job] of Object.entries(jobs)) {
      const remaining = Math.max(0, Math.ceil(job.next_check - now));
      text(
        id(name + "Timing"),
        job.state === "checking"
          ? "Checking now…"
          : `${job.duration_ms || 0} ms · ${job.next_check ? "Next check in " + remaining + "s" : "Check queued"} · Last success: ${date(job.last_success)}`,
      );
    }
  }
  function filterRed() {
    const q = (id("redSearch")?.value || "").trim().toLowerCase();
    id("redBody")
      ?.querySelectorAll("[data-red-name]")
      .forEach(
        (row) => (row.hidden = !row.dataset.redName.toLowerCase().includes(q)),
      );
  }
  id("redSearch")?.addEventListener("input", filterRed);
  function checkingSoon(job) {
    const pending =
      job.pending || job.requested > job.completed || job.state === "queued";
    return (
      job.state === "checking" ||
      (pending &&
        (!job.next_check || job.next_check <= (Date.now() + offset) / 1000 + 3))
    );
  }
  function progress(value) {
    for (const name of ["shuffle", "kick"]) {
      const job = jobs[name] || {},
        pending =
          job.pending ||
          job.requested > job.completed ||
          job.state === "queued";
      let message = "Automatic check is starting.";
      if (job.state === "checking")
        message = job.pending
          ? "Checking now; your follow-up refresh is queued."
          : "Checking the provider now…";
      else if (pending) {
        message =
          job.next_check > (Date.now() + offset) / 1000 + 3
            ? "Queued. Retry scheduled for " + date(job.next_check) + "."
            : "Refresh queued; waiting for the worker.";
        if (job.error)
          message +=
            " Last check" +
            (job.http_status ? " (HTTP " + job.http_status + ")" : "") +
            ": " +
            job.error;
      } else if (job.error)
        message =
          "Check failed" +
          (job.http_status ? " (HTTP " + job.http_status + ")" : "") +
          ": " +
          job.error;
      else if (
        name === "shuffle" &&
        ["updated", "unchanged"].includes(job.result)
      )
        message =
          (job.result === "updated" ? "Published " : "Confirmed ") +
          (value.count || 0) +
          " qualifying players. Last check: " +
          date(job.completed_at) +
          ".";
      else if (name === "shuffle" && job.result === "empty")
        message =
          value.leaderboard_message ||
          "Check completed; no qualifying wagers were returned.";
      else if (["upcoming", "unconfigured"].includes(job.result))
        message =
          value.leaderboard_message ||
          "Waiting for the configured race to start.";
      else if (job.result === "superseded")
        message =
          "The old settings were superseded; a check for the current settings is queued.";
      else if (job.result === "shared")
        message = "Another app instance is checking this provider.";
      else if (name === "kick" && ["live", "offline"].includes(job.result))
        message =
          "Confirmed " +
          job.result +
          " on Kick. Last check: " +
          date(job.completed_at) +
          ".";
      text(id(name + "Progress"), message);
      const summary = job.error
        ? "Needs attention"
        : job.state === "checking"
          ? "Checking now"
          : pending
            ? "Queued"
            : name === "kick" && ["live", "offline"].includes(job.result)
              ? job.result === "live"
                ? "Live"
                : "Offline"
              : job.result === "waiting"
                ? "Waiting for data"
                : job.result === "upcoming"
                  ? "Race upcoming"
                  : job.result === "unconfigured"
                    ? "Set race dates"
                    : "Up to date";
      text(
        id(name + "Summary"),
        `${name === "shuffle" ? "Shuffle" : "Kick"} · ${summary}`,
      );
      id(name + "Summary")?.classList.toggle("has-error", Boolean(job.error));
    }
    const failure = JSON.stringify(
      Object.entries(jobs)
        .filter(([, job]) => job.error)
        .map(([name, job]) => [name, job.error, job.http_status]),
    );
    if (
      failure !== "[]" &&
      failure !== lastProviderFailure &&
      id("connectionDetails")
    )
      id("connectionDetails").open = true;
    lastProviderFailure = failure;
    text(
      id("publishedWindow"),
      "Published window: " +
        date(site.start_time) +
        " → " +
        date(site.end_time),
    );
    const work = JSON.stringify([
      value.runtime_id,
      ...Object.values(jobs).map((job) => [job.requested, job.runs, job.state]),
    ]);
    if (work !== lastWork && Object.values(jobs).some(checkingSoon))
      urgentUntil = Date.now() + 60000;
    lastWork = work;
    if (receipt && value.runtime_id) {
      if (receipt.runtime_id !== value.runtime_id) {
        receipt = null;
        toast("The backend restarted. Current update progress is shown below.");
      } else if (
        Object.entries(receipt.requests).every(
          ([name, target]) => jobs[name]?.completed >= target,
        )
      ) {
        const failed = Object.keys(receipt.requests).some(
          (name) => jobs[name]?.error,
        );
        toast(
          failed
            ? "Refresh finished with a provider error. See update progress below."
            : "Refresh finished. See the update result below.",
        );
        receipt = null;
      }
    }
  }
  function cell(value, className = "") {
    const td = document.createElement("td");
    td.textContent = String(value ?? "—");
    td.className = className;
    return td;
  }
  function updateTable(body, rows, red = false) {
    if (!body) return;
    const encoded = JSON.stringify(rows);
    if (encoded === (red ? redVersion : participantVersion)) return;
    if (red) redVersion = encoded;
    else participantVersion = encoded;
    const scroll = body.closest(".table-scroll"),
      top = scroll?.scrollTop,
      left = scroll?.scrollLeft;
    const focused = document.activeElement,
      focusRow = focused?.closest("tr"),
      focusName = focusRow?.dataset.player || focusRow?.dataset.redName;
    const focusCopy = focused?.hasAttribute("data-copy");
    const fragment = document.createDocumentFragment();
    rows.forEach((r, index) => {
      const tr = document.createElement("tr");
      tr.dataset[red ? "redName" : "player"] = r.username;
      tr.append(cell(red ? index + 1 : r.rank, "rank"));
      const name = cell("");
      const strong = document.createElement("strong");
      strong.textContent = r.username;
      name.append(strong);
      const copy = document.createElement("button");
      copy.type = "button";
      copy.className = "copy-button";
      copy.dataset.copy = r.username;
      copy.textContent = "⧉";
      copy.setAttribute("aria-label", "Copy " + r.username);
      name.append(copy);
      if (!red && r.source === "override") {
        const label = document.createElement("span");
        label.className = "tag";
        label.textContent = "Adjusted";
        name.append(label);
      }
      tr.append(name, cell(red ? r.weighted : r.wager, "number accent"));
      if (!red) tr.append(cell(r.original_weighted_str, "number"));
      tr.append(cell(red ? r.raw : r.raw_wager_str, "number"));
      if (!red) {
        const action = cell(""),
          link = document.createElement("a");
        link.href =
          "/admin?tab=players&edit=" +
          encodeURIComponent(r.username) +
          "#override";
        link.className = "text-link";
        link.textContent = "Edit";
        action.append(link);
        tr.append(action);
      }
      fragment.append(tr);
    });
    if (!rows.length) {
      const tr = document.createElement("tr"),
        td = cell(
          red
            ? "No confirmed Code Red wagerers for this window."
            : "No matching qualifying wagers.",
          "empty",
        );
      td.colSpan = red ? 4 : 6;
      tr.append(td);
      fragment.append(tr);
    }
    body.replaceChildren(fragment);
    if (scroll) {
      scroll.scrollTop = top;
      scroll.scrollLeft = left;
    }
    if (focusName)
      [...body.rows]
        .find(
          (row) => (row.dataset.player || row.dataset.redName) === focusName,
        )
        ?.querySelector(focusCopy ? "button" : "a")
        ?.focus({ preventScroll: true });
    if (red) filterRed();
  }
  function apply(value, began) {
    if (!value.site || !value.freshness || !Number.isFinite(value.server_time))
      throw new Error("The update response is incomplete.");
    site = value.site;
    offset = value.server_time * 1000 - (began + Date.now()) / 2;
    sourceAt = value.freshness.updated_at;
    text(id("raceTitle"), site.race_title);
    text(id("raceDescription"), site.race_description);
    text(id("sponsorName"), site.sponsor_name);
    text(id("poolTotal"), site.total_prize);
    text(id("playerCount"), value.count);
    text(id("dataState"), value.freshness.label);
    text(id("sourceTime"), date(sourceAt));
    notice("leaderboardMessage", value.leaderboard_message || "");
    notice(
      "sourceWarning",
      [value.freshness.warning, isAdmin ? value.freshness.error : ""]
        .filter(Boolean)
        .join(" "),
    );
    document
      .querySelectorAll("[data-site-text]")
      .forEach((node) => text(node, site[node.dataset.siteText]));
    document.querySelectorAll("[data-site-link]").forEach((a) => {
      const href = site[a.dataset.siteLink];
      a.hidden = !href;
      if (href && /^https?:\/\//.test(href)) a.href = href;
    });
    if (id("sponsorLink") && /^https?:\/\//.test(site.sponsor_url))
      id("sponsorLink").href = site.sponsor_url;
    if (isAdmin) {
      jobs = value.jobs || {};
      if (value.checkpoint) {
        text(id("checkpointLabel"), value.checkpoint.label);
        text(id("checkpointDetails"), value.checkpoint.details);
        text(
          id("checkpointTime"),
          value.checkpoint.generated_at
            ? "Last export generated: " + date(value.checkpoint.generated_at)
            : "No export generated yet.",
        );
        id("checkpointLabel")?.classList.toggle(
          "accent",
          value.checkpoint.changes,
        );
      }
      progress(value);
      updateTable(id("participantsBody"), value.participants || []);
      if (id("codeRed")?.open && value.red)
        updateTable(id("redBody"), value.red, true);
      text(id("redCount"), Math.min(100, value.red_total || 0) + " / 100");
      text(
        id("redMembership"),
        (value.diagnostics?.missing_campaign || 0) +
          " source rows have no campaign metadata; membership cannot be verified for those rows.",
      );
      for (const name of ["shuffle", "kick"])
        text(
          id(name + "Message"),
          jobs[name]?.error ||
            (name === "shuffle"
              ? value.freshness.label
              : value.stream?.available
                ? value.stream.live
                  ? "Live on Kick"
                  : "Kick offline"
                : "Kick status unavailable"),
        );
      const stream = value.stream || {};
      text(
        id("streamDetail"),
        stream.available && stream.live
          ? [
              stream.title,
              stream.viewers
                ? stream.viewers.toLocaleString() + " watching"
                : "Viewer count unavailable",
            ]
              .filter(Boolean)
              .join(" · ")
          : "",
      );
      document
        .querySelectorAll("[data-diagnostic]")
        .forEach((node) =>
          text(node, value.diagnostics?.[node.dataset.diagnostic]),
        );
      text(
        id("browserCheck"),
        "Dashboard checked " +
          date(value.server_time) +
          " · next update in 60 seconds",
      );
    } else {
      const rows = new Map((value.rows || []).map((row) => [row.rank, row]));
      document.querySelectorAll("[data-rank]").forEach((node) => {
        const n = Number(node.dataset.rank),
          row = rows.get(n);
        text(
          node.querySelector("[data-name]"),
          row?.username || "Open position",
        );
        text(node.querySelector("[data-wager]"), row?.wager || "$0.00");
        text(node.querySelector("[data-prize]"), currency(site.prizes[n]));
      });
      if (value.boss) {
        const b = value.boss;
        text(
          id("inviteTitle"),
          b.status === "victory"
            ? "The crew conquered Crimson."
            : b.status === "paused"
              ? "The raid is taking a breather."
              : "Red needs a raid party.",
        );
        text(
          id("inviteProgress"),
          `${Number(b.hp).toLocaleString()} HP left · ${b.raiders} raiders united`,
        );
        text(
          id("inviteButtonLabel"),
          b.status === "victory"
            ? "View the victory"
            : b.status === "paused"
              ? "View the raid"
              : "Join the boss fight",
        );
        const bar = id("inviteHealth");
        if (bar) {
          bar.max = b.max_hp;
          bar.value = b.hp;
        }
      }
      text(
        id("streamStatus"),
        !value.stream?.available
          ? "Kick status unavailable"
          : value.stream.live
            ? "● Live on Kick"
            : "Kick offline",
      );
    }
    clock();
  }
  async function getJSON(url, options = {}) {
    const controller = new AbortController(),
      timeout = setTimeout(() => controller.abort(), 10000);
    try {
      const conditional =
        !isAdmin &&
        !options.method &&
        new URL(url, location.origin).pathname === "/public-state";
      const headers = { Accept: "application/json", ...options.headers };
      if (conditional && publicETag) headers["If-None-Match"] = publicETag;
      const response = await fetch(url, {
        ...options,
        credentials: "same-origin",
        cache: "no-store",
        signal: controller.signal,
        headers,
      });
      const clockHeader = response.headers?.get("X-Server-Time");
      const currentTime =
        clockHeader && Number.isFinite(Number(clockHeader))
          ? Number(clockHeader)
          : null;
      if (conditional && response.status === 304) {
        if (!publicCache)
          throw new Error("The cached update is unavailable. Reload the page.");
        return {
          ...publicCache,
          server_time: currentTime ?? Date.now() / 1000,
        };
      }
      if (response.status === 401)
        throw new Error(
          "Your session expired. Sign in again to resume updates.",
        );
      if (
        response.redirected &&
        response.url &&
        new URL(response.url, location.origin).pathname === "/admin/login"
      ) {
        throw new Error(
          "Your session expired. Sign in again to resume updates.",
        );
      }
      if (!response.headers.get("content-type")?.includes("application/json")) {
        const hint =
          response.status === 404
            ? "The update endpoint was not found. Reload the page after installing the complete update."
            : response.status >= 500
              ? "Check the backend runtime logs. Previous results are retained."
              : "Reload the page and sign in again if needed.";
        // Never render an HTML error/proxy page into the dashboard.
        throw new Error(
          `Expected JSON but received a non-JSON response (HTTP ${response.status}). ${hint}`,
        );
      }
      let value;
      try {
        value = await response.json();
      } catch {
        throw new Error(
          `The server returned invalid JSON (HTTP ${response.status}). Check the runtime logs.`,
        );
      }
      if (!response.ok)
        throw new Error(
          `${value?.error || "The server could not complete this request."} (HTTP ${response.status})`,
        );
      if (conditional) {
        publicCache = value;
        publicETag = response.headers.get("ETag") || "";
        value = {
          ...value,
          server_time: currentTime ?? value.server_time ?? Date.now() / 1000,
        };
      }
      return value;
    } finally {
      clearTimeout(timeout);
    }
  }
  async function poll() {
    if (document.hidden) return;
    if (busy) {
      pollAgain = true;
      return;
    }
    busy = true;
    clearTimeout(timer);
    const began = Date.now();
    try {
      const url = new URL(document.body.dataset.feed, location.origin);
      if (isAdmin) {
        for (const [key, value] of new URLSearchParams(location.search))
          url.searchParams.set(key, value);
        if (id("codeRed")?.open) url.searchParams.set("code_red", "1");
      }
      const result = await getJSON(url);
      apply(result, began);
      notice("networkError", "");
      if (result.release && result.release !== "2026.09.22-no-regen")
        notice(
          "networkError",
          "A newer version was deployed. Save your draft, then reload.",
        );
    } catch (error) {
      notice(
        "networkError",
        error.name === "AbortError"
          ? "Dashboard request timed out. Previous results are retained; updates will retry."
          : error.message,
      );
    } finally {
      busy = false;
      if (!next) next = began + 60000;
      else if (next <= began)
        next += 60000 * (Math.floor((began - next) / 60000) + 1);
      if (next <= Date.now())
        next += 60000 * (Math.floor((Date.now() - next) / 60000) + 1);
      const urgent =
        Date.now() < urgentUntil && Object.values(jobs).some(checkingSoon);
      const delay = pollAgain
        ? 50
        : urgent
          ? 2000
          : Math.max(250, next - Date.now());
      pollAgain = false;
      if (!document.hidden) timer = setTimeout(poll, delay);
    }
  }
  document.querySelectorAll("[data-refresh]").forEach((form) =>
    form.addEventListener("submit", async (event) => {
      event.preventDefault();
      const button = form.querySelector("button");
      if (button.disabled) return;
      button.disabled = true;
      try {
        // A hidden input named "action" shadows form.action in real browsers.
        // Read the HTML attribute so every refresh reaches the backend route.
        const value = await getJSON(form.getAttribute("action"), {
          method: "POST",
          body: new FormData(form),
        });
        receipt = value.requests
          ? { runtime_id: value.runtime_id, requests: value.requests }
          : null;
        jobs = value.jobs || jobs;
        toast(value.message);
        urgentUntil = Date.now() + 60000;
        next = 0;
        await poll();
      } catch (error) {
        toast(error.message);
      } finally {
        button.disabled = false;
      }
    }),
  );
  document
    .querySelectorAll("[data-recovery-download]")
    .forEach((link) =>
      link.addEventListener("click", () => setTimeout(() => void poll(), 1000)),
    );
  id("codeRed")?.addEventListener("toggle", () => {
    if (id("codeRed").open) {
      next = 0;
      poll();
    }
  });
  document.addEventListener("visibilitychange", () => {
    clearTimeout(timer);
    if (!document.hidden) {
      next = 0;
      poll();
    }
  });
  window.addEventListener("pageshow", (event) => {
    if (event.persisted) {
      next = 0;
      poll();
    }
  });
  clock();
  setInterval(clock, 1000);
  poll();
})();
