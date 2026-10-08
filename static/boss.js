/* Shared raid UI. The server owns damage, identity, cooldowns and private names.
   Polling never attacks. A failed POST keeps its receipt ID for a safe retry. */
(() => {
  "use strict";
  const root = document.querySelector("[data-boss-root]");
  if (!root) return;
  const admin = root.dataset.mode === "admin";
  const $ = (id) => root.querySelector("#" + id);
  const text = (id, value) => {
    const el = $(id);
    if (el) el.textContent = String(value);
  };
  const number = (value) =>
    (typeof value === "bigint" ? value : Number(value)).toLocaleString("en-US");
  const compact = new Intl.NumberFormat("en-US", {
    notation: "compact",
    maximumFractionDigits: 1,
  });
  function metric(id, value) {
    text(id, Math.abs(value) >= 10000 ? compact.format(value) : number(value));
    const el = $(id);
    if (el) {
      el.title = number(value);
      el.setAttribute("aria-label", number(value));
    }
  }
  let editingName = root.dataset.editName === "1",
    savingName = false;
  let labels = {};
  let armed = true,
    lockedButton = null,
    inputMode = "mouse",
    keyHeld = false,
    nameDirty = editingName;
  const nameInput = $("playerUsername");
  nameInput?.addEventListener("input", () => {
    nameDirty = true;
  });
  const listCache = new Map();
  const effects = new Map();
  const button = $("attackButton"),
    dockButton = $("dockAttack"),
    stage = $("bossStage");
  let state,
    csrf = "",
    selected = "blade",
    busy = false,
    timer,
    polling = false,
    authExpired = false,
    pendingWrites = 0,
    mutationEpoch = 0;
  let receivedAt = performance.now(),
    lastGood = -Infinity,
    pending = null,
    lastAnimated = "";
  let milestoneTimer,
    recapRaid = "",
    recapPending = false;
  const pendingKey = "rh.boss.pending";
  // Session storage remembers a click if the connection drops or the tab reloads.
  // Gameplay still works in browsers that disable storage; cookies are required.
  try {
    pending = JSON.parse(sessionStorage.getItem(pendingKey));
    selected = localStorage.getItem("rh.boss.style") || "blade";
  } catch (_) {
    /* optional */
  }
  function remember(value) {
    pending = value;
    try {
      value
        ? sessionStorage.setItem(pendingKey, JSON.stringify(value))
        : sessionStorage.removeItem(pendingKey);
    } catch (_) {
      /* optional */
    }
  }
  function error(message = "") {
    const el = $("bossError");
    if (el) {
      el.hidden = !message;
      el.textContent = message;
    }
    if ($("dismissBossError")) $("dismissBossError").hidden = !message;
  }
  const now = () =>
    state ? state.server_time + (performance.now() - receivedAt) / 1000 : 0;
  function duration(seconds) {
    const s = Math.max(0, Math.ceil(seconds));
    return s >= 3600
      ? `${Math.floor(s / 3600)}h ${Math.floor((s % 3600) / 60)}m`
      : `${Math.floor(s / 60)}:${String(s % 60).padStart(2, "0")}`;
  }
  function strikeFeedback(hit, receipt) {
    if (!hit || receipt === lastAnimated) return;
    lastAnimated = receipt;
    text(
      "hitResult",
      `${hit.burst ? "CRIMSON BURST! " : ""}${labels[hit.style]} hit for ${number(hit.damage)}${hit.weakness ? " · Weakness matched!" : " · Nice hit."}`,
    );
    text("hitFloat", "−" + number(hit.damage));
    if (
      stage &&
      !window.matchMedia?.("(prefers-reduced-motion: reduce)").matches
    ) {
      const sprite = stage.querySelector(".boss-sprite"),
        float = $("hitFloat");
      for (const [element, frames, duration] of [
        [
          sprite,
          [
            { transform: "translateX(0)" },
            { transform: "translateX(-8px) rotate(-3deg)" },
            { transform: "translateX(6px)" },
            { transform: "translateX(0)" },
          ],
          400,
        ],
        [
          float,
          [
            { opacity: 1, transform: "translate(-50%,0) scale(.8)" },
            {
              opacity: 1,
              transform: "translate(-50%,-15px) scale(1.1)",
              offset: 0.25,
            },
            { opacity: 0, transform: "translate(-50%,-65px)" },
          ],
          800,
        ],
      ]) {
        if (element?.animate) {
          effects.get(element)?.cancel();
          effects.set(
            element,
            element.animate(frames, { duration, easing: "ease-out" }),
          );
        }
      }
    }
  }
  function rows(id, values, empty, mapper) {
    const list = $(id);
    if (!list) return;
    const signature = JSON.stringify(values),
      previous = listCache.get(id);
    if (previous?.signature === signature) return;
    const records = new Map();
    const nodes = values.map((value, index) => {
      const key = String(
        value.id || (value.name ? value.name + ":" + (value.at || "") : index),
      );
      const rowSignature = JSON.stringify([value, index]);
      const old = previous?.records.get(key);
      const node =
        old?.signature === rowSignature ? old.node : mapper(value, index);
      records.set(key, { signature: rowSignature, node });
      return node;
    });
    if (!nodes.length) {
      const li = document.createElement("li");
      li.className = "muted";
      li.textContent = empty;
      nodes.push(li);
    }
    // Retain untouched nodes, keyboard focus and scroll position between polls.
    nodes.forEach((node, index) => {
      if (list.children[index] !== node)
        list.insertBefore(node, list.children[index] || null);
    });
    while (list.children.length > nodes.length) list.lastElementChild.remove();
    listCache.set(id, { signature, records });
  }
  function item(title, detail, score, self = false) {
    const li = document.createElement("li"),
      left = document.createElement("span"),
      strong = document.createElement("strong"),
      small = document.createElement("small"),
      right = document.createElement("span");
    strong.textContent = title;
    small.textContent = detail;
    right.textContent = score;
    right.className = "score";
    left.append(strong, small);
    li.append(left, right);
    if (self) li.className = "self";
    return li;
  }
  function apply(value) {
    const next = value.state;
    if (
      !next ||
      typeof next.raid_id !== "string" ||
      !Number.isFinite(next.server_time) ||
      !next.you
    )
      throw new Error(
        "The game returned an incomplete update. Reload in a moment.",
      );
    // Committed revisions outrank request clocks: a username save can wait
    // behind another hit while a poll starts later and returns first.
    if (state) {
      const sameRaid = next.raid_id === state.raid_id;
      if (
        (sameRaid &&
          (next.version < state.version ||
            (next.health_revision || 0) < (state.health_revision || 0) ||
            (next.settings_revision || 0) < (state.settings_revision || 0))) ||
        ((!sameRaid || next.version === state.version) &&
          next.server_time < state.server_time)
      )
        return;
    }
    // Only a newer explicit host health revision may change maximum HP.
    // Ordinary snapshots cannot heal the same boss on screen.
    // Keep the last confirmed state and let stale-state handling disable hits;
    // never fabricate a lower HP value while accepting inconsistent counters.
    if (
      state &&
      next.raid_id === state.raid_id &&
      (next.total_damage < state.total_damage ||
        next.total_attacks < state.total_attacks ||
        ((next.health_revision || 0) === (state.health_revision || 0) &&
          (next.hp > state.hp || next.max_hp !== state.max_hp)))
    )
      throw new Error(
        "Boss progress moved backwards; retaining the last confirmed state.",
      );
    if (value.player_csrf && !admin) csrf = value.player_csrf;
    else if (value.csrf) csrf = value.csrf;
    const nameForm = $("playerNameForm");
    if (nameForm && csrf) {
      nameForm.elements.namedItem("csrf").value = csrf;
      nameForm.elements.namedItem("raid_id").value = next.raid_id;
    }
    state = next;
    labels = state.rules.styles;
    text("bossName", state.name || "Crimson Hunllef");
    root.querySelectorAll("[data-boss-avatar]").forEach((image) => {
      if (state.avatar_url && image.getAttribute("src") !== state.avatar_url)
        image.src = state.avatar_url;
      image.classList.toggle("custom-avatar", Boolean(state.avatar_custom));
      if (image.classList.contains("boss-sprite"))
        image.alt = state.name || "Crimson Hunllef";
    });
    receivedAt = performance.now();
    lastGood = receivedAt;
    if (
      pending &&
      (pending.raid_id !== state.raid_id || pending.name !== state.you.name)
    )
      remember(null);
    if (pending && state.you.last_request === pending.request_id) {
      strikeFeedback(state.you.last_hit, pending.request_id);
      remember(null);
      error();
    }
    text("bossConnection", "Live · Shared raid connected");
    text(
      "bossHealth",
      `${compact.format(state.hp)} / ${compact.format(state.max_hp)} HP`,
    );
    if ($("bossHealth"))
      $("bossHealth").title =
        `${number(state.hp)} / ${number(state.max_hp)} HP`;
    text(
      "exactRaidTotals",
      `${number(state.hp)} / ${number(state.max_hp)} HP · ${number(state.total_damage)} damage · ${number(state.total_attacks)} hits`,
    );
    text(
      "bossPercent",
      (((state.max_hp - state.hp) / state.max_hp) * 100).toFixed(2) +
        "% defeated",
    );
    const bar = $("bossHealthBar");
    if (stage) stage.dataset.healthPhase = state.hp === 0 ? 'defeated' : state.hp/state.max_hp <= .25 ? 'critical' : state.hp/state.max_hp <= .5 ? 'fierce' : state.hp/state.max_hp <= .75 ? 'stirring' : 'full';
    if (bar) {
      bar.max = state.max_hp;
      bar.value = state.hp;
    }
    text(
      "bossPhase",
      state.status === "victory"
        ? "DEFEATED"
        : state.status === "paused"
          ? "PAUSED"
          : state.phase,
    );
    text("bossDay", "Raid day " + state.day);
    text("bossRaiders", number(state.raiders));
    text("bossAttacks", number(state.total_attacks));
    metric("bossDamage", state.total_damage);
    const story =
      state.status === "victory"
        ? "VICTORY. The Red crew brought the beast down. Every hit made this happen."
        : state.status === "paused"
          ? "The host has paused attacks. Your progress is safe; the raid-day clock keeps running."
          : state.status === "waiting"
            ? "The first strike starts the raid. Let’s wake the beast."
            : state.phase === "Last stand"
              ? "Last stand. The beast is cornered. Rally the crew and finish what you started."
              : state.phase === "Enraged"
                ? "Enraged. The arena is heating up. Watch the weakness and keep the pressure on."
                : "Awakening. The beast stirs. Small hits become a massive takedown.";
    text("bossStory", story);
    if (stage) stage.classList.toggle("victory", state.status === "victory");
    text(
      "bossWeakness",
      `${state.weakness_label} · ${number(state.rules.weak_damage)} damage`,
    );
    root
      .querySelectorAll("[data-style]")
      .forEach((el) =>
        el.classList.toggle("is-weak", el.dataset.style === state.weakness),
      );
    text("yourName", state.you.name);
    metric("yourDamage", state.you.damage);
    text("yourAttacks", number(state.you.attacks));
    if (nameInput && !nameDirty && document.activeElement !== nameInput)
      nameInput.value = state.you.display_name || "";
    identityView();
    rally();
    if (admin) {
      adminTools();
      document.dispatchEvent(
        new CustomEvent("boss:admin-state", { detail: state }),
      );
    }
    if (admin)
      rows(
        "adminBossLeaders",
        state.admin_leaders || [],
        "No hits yet.",
        (r, i) =>
          item(
            `${i + 1}. ${r.name}`,
            `${r.alias} · ${number(r.attacks)} hits · ${r.name_provided ? (r.shuffle_name_in_feed ? "Shuffle name match · unverified" : "Self-reported") : "Username not supplied yet"}`,
            number(r.damage),
          ),
      );

    text(
      "burstLabel",
      state.you.burst_in === 1
        ? `NEXT HIT: +${state.rules.burst_bonus} damage`
        : `${state.you.burst_in} hits to +${state.rules.burst_bonus} damage`,
    );
    root
      .querySelectorAll("#burstMeter span")
      .forEach((el, i) =>
        el.classList.toggle(
          "filled",
          i < state.rules.burst_every - state.you.burst_in,
        ),
      );
    rows(
      "bossLeaders",
      state.leaders,
      "Land the first hit to lead the charge.",
      (r, i) =>
        item(
          `${String(i + 1).padStart(2, "0")}  ${r.name}${r.you ? " · You" : ""}`,
          `${number(r.attacks)} hits`,
          number(r.damage),
          r.you,
        ),
    );
    rows(
      "bossRecent",
      state.recent,
      "The arena is waiting for your community.",
      (r) =>
        item(
          r.name,
          `${labels[r.style]}${r.burst ? " · Burst" : ""}${r.weakness ? " · Weakness" : ""} · ${new Date(r.at * 1000).toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" })}`,
          "−" + number(r.damage),
        ),
    );
    rows(
      "bossHistory",
      state.history.slice().reverse(),
      "The first chapter is yours to write.",
      (r) =>
        item(
          r.outcome,
          `${number(r.raiders)} raiders · ${number(r.attacks)} hits · ${new Date(r.ended_at * 1000).toLocaleDateString()}`,
          number(r.damage) + " damage",
        ),
    );
    achievements();
    if (!admin && state.status === "victory") void recap();
    tick();
  }
  function identityView() {
    if (admin) return;
    const own = Boolean(state.you.display_name);
    text("playingAs", state.you.display_name || "");
    if ($("playerIdentity"))
      $("playerIdentity").hidden =
        !own || !state.you.identity_ready || editingName;
    if ($("playerNameForm"))
      $("playerNameForm").hidden =
        own && state.you.identity_ready && !editingName;
    if ($("recoveryOwner")) $("recoveryOwner").hidden = !own;
    text(
      "recoverySaved",
      state.you.recovery_saved
        ? "Recovery code created. Creating another replaces the previous code."
        : "Save a code to keep your player if cookies are cleared.",
    );
  }
  function rally() {
    const r = state.rally;
    if (!r) return;
    stage?.classList.toggle("rally-lit", Boolean(r.unlocked));
    $("rallyStatus")?.classList.toggle("unlocked", Boolean(r.unlocked));
    text("rallyTitle", r.unlocked ? "Red rally · Arena lit" : "Red rally");
    text("rallyCount", `${r.count} / ${r.goal} raiders`);
    text(
      "rallyHint",
      r.unlocked
        ? "Unlocked together for this raid."
        : "15 raiders hit within 10 minutes to light the arena.",
    );
    if ($("rallyBar")) {
      $("rallyBar").max = r.goal;
      $("rallyBar").value = r.count;
    }
  }
  const changeLabels = {
    hp: "Remaining HP",
    max_hp: "Maximum HP",
    damage: "Base",
    weak_damage: "Weakness",
    burst_bonus: "Burst bonus",
    paused: "Paused",
    name: "Name",
    player: "Player",
    slots: "Players",
    avatar: "Avatar",
    connection: "Connection",
  };
  function displayChange(key, value) {
    if (key === "avatar" && typeof value === "string" && value.length === 64)
      return "Image " + value.slice(0, 8);
    return typeof value === "number" ? number(value) : String(value);
  }
  function adminTools() {
    const b = state.balance;
    if (b) {
      text(
        "bossPace",
        b.observed
          ? `${number(b.damage_per_hour)} damage / hour`
          : "Collecting recent hits…",
      );
      text(
        "bossEstimate",
        state.status === "victory"
          ? "Boss defeated."
          : b.observed
            ? `About ${b.remaining_seconds >= 86400 ? (b.remaining_seconds / 86400).toFixed(1) + " days" : duration(b.remaining_seconds)} remaining at this pace · ${number(b.sample_hits)} recent hits`
            : `${number(b.sample_hits)} recent hits. Estimates appear after 5 minutes and 10 hits with damage.`,
      );
      const presets = $("raidPresets");
      if (presets) {
        for (const p of b.presets) {
          let el = [...presets.children].find(
            (e) => e.dataset.days === String(p.days),
          );
          if (!el) {
            el = document.createElement("button");
            el.type = "button";
            el.className = "button small";
            el.dataset.days = String(p.days);
            el.addEventListener("click", () => {
              $("bossHealthInput").value = el.dataset.hp;
              $("bossHealthInput").focus();
            });
            presets.append(el);
          }
          el.dataset.hp = String(p.hp);
          el.textContent = `${p.label} · ${compact.format(p.hp)} HP`;
          el.title = `${number(p.hp)} HP${b.observed ? ` · about ${p.days} days at recent pace` : " · starting suggestion"}`;
        }
      }
      text(
        "presetBasis",
        b.observed
          ? "Presets target roughly 3, 5 or 7 days at the observed pace. They fill the next-raid field only; review and confirm to start."
          : "Starting suggestions: 10M / 25M / 50M HP. Duration is unknown until activity is measured. These only fill the next-raid field.",
      );
    }
    rows(
      "bossAdminHistory",
      (state.admin_history || []).map((h, i) => ({
        ...h,
        id: String(h.at) + ":" + i,
      })),
      "No host edits recorded in this release yet.",
      (h) => {
        const keys = [
          ...new Set([...Object.keys(h.before), ...Object.keys(h.after)]),
        ];
        const changes = keys
          .filter((k) => h.before[k] !== h.after[k])
          .map(
            (k) =>
              `${changeLabels[k] || k}: ${displayChange(k, h.before[k])} → ${displayChange(k, h.after[k])}`,
          );
        return item(
          `${h.action} · ${h.actor}`,
          changes.join(" · ") || "Action confirmed; values unchanged.",
          new Date(h.at * 1000).toLocaleString(),
        );
      },
    );
    rows(
      "bossAbuseFlags",
      (state.abuse_flags || []).map((f, i) => ({ ...f, id: String(i) + f.at })),
      "No bursts of rejected requests detected.",
      (f) =>
        item(
          `${f.alias} · ${f.category}`,
          `${f.rejected} rejected requests · Browser ${f.tag}`,
          new Date(f.at * 1000).toLocaleTimeString(),
        ),
    );
    previews();
  }
  function whole(id) {
    const value = $(id)?.value || "";
    if (!/^\d+$/.test(value)) return null;
    const n = BigInt(value);
    return n <= BigInt(Number.MAX_SAFE_INTEGER) ? n : null;
  }
  function previews() {
    if (!admin || !state) return;
    const hp = BigInt(state.hp),
      max = BigInt(state.max_hp),
      nextMax = whole("bossMaxHealth"),
      remaining = whole("bossRemainingHealth");
    if (nextMax !== null && nextMax > 0n) {
      const next = hp + nextMax - max;
      text(
        "maxHealthPreview",
        `Remaining HP: ${number(hp)} → ${number(next < 0n ? 0n : next > nextMax ? nextMax : next)} · Maximum: ${number(max)} → ${number(nextMax)}`,
      );
    } else text("maxHealthPreview", "Enter a valid whole-number maximum HP.");
    text(
      "remainingHealthPreview",
      remaining !== null && remaining <= max
        ? `Remaining HP: ${number(hp)} → ${number(remaining)}${remaining > hp ? " · Explicit heal" : remaining === 0n ? " · Defeats the boss" : ""}`
        : "Remaining HP must be between 0 and the current maximum.",
    );
    const base = whole("bossBaseDamage"),
      weak = whole("bossWeakDamage"),
      burst = whole("bossBurstBonus");
    text(
      "damagePreview",
      [base, weak, burst].every((n) => n !== null)
        ? `Next hit: base ${number(base)} · weakness ${number(weak)}. Every tenth hit: base ${number(base + burst)} · weakness ${number(weak + burst)}. Actual damage stops at remaining HP.`
        : "Enter valid whole-number damage values.",
    );
  }
  root
    .querySelectorAll(
      "#bossMaxHealth, #bossRemainingHealth, #bossBaseDamage, #bossWeakDamage, #bossBurstBonus",
    )
    .forEach((el) => el.addEventListener("input", previews));
  $("editPlayerName")?.addEventListener("click", (event) => {
    event.preventDefault();
    editingName = true;
    identityView();
    nameInput?.focus();
  });
  $("makeRecoveryCode")?.addEventListener("click", async (event) => {
    const el = event.currentTarget;
    el.disabled = true;
    try {
      const { response, value } = await request("/play/api/recovery-code", {
        method: "POST",
        headers: { "X-CSRF-Token": csrf },
      });
      if (!response.ok)
        throw new Error(value.error || "Could not create a recovery code.");
      apply(value);
      $("recoveryCode").value = value.code;
      $("recoveryCodeBox").hidden = false;
      text(
        "recoveryResult",
        "Save this code somewhere private. It is only shown here.",
      );
    } catch (e) {
      text("recoveryResult", e.message);
    } finally {
      el.disabled = false;
    }
  });
  $("downloadRecovery")?.addEventListener("click", () => {
    const blob = new Blob(
      [
        "RedHunllef player recovery code\nKeep private. Paste into Player recovery at /play.\n\n" +
          $("recoveryCode").value +
          "\n",
      ],
      { type: "text/plain;charset=utf-8" },
    );
    const url = URL.createObjectURL(blob),
      link = document.createElement("a");
    link.href = url;
    link.download = "redhunllef-player-recovery.txt";
    link.click();
    setTimeout(() => URL.revokeObjectURL(url), 1000);
  });
  $("recoverPlayerForm")?.addEventListener("submit", async (event) => {
    event.preventDefault();
    const el = event.currentTarget.querySelector("button");
    el.disabled = true;
    try {
      const { response, value } = await request("/play/api/recover", {
        method: "POST",
        headers: { "Content-Type": "application/json", "X-CSRF-Token": csrf },
        body: JSON.stringify({
          raid_id: state.raid_id,
          code: $("recoveryInput").value.trim(),
        }),
      });
      if (!response.ok) throw new Error(value.error || "Recovery failed.");
      remember(null);
      editingName = false;
      nameDirty = false;
      apply(value);
      $("recoveryInput").value = "";
      text(
        "recoveryResult",
        "Player restored. Your hits, badges and cooldown were kept.",
      );
    } catch (e) {
      text("recoveryResult", e.message);
    } finally {
      el.disabled = false;
    }
  });
  function achievements() {
    const milestones = state.milestones || [],
      achieved = milestones.filter((m) => m.reached);
    const level = achieved.at(-1)?.percent || 0;
    if (stage) stage.dataset.milestone = String(level);
    rows("bossMilestones", milestones, "", (m) =>
      item(
        `${m.reached ? "✓" : "◇"} ${m.percent}%`,
        m.label,
        m.reached ? "Reached" : "Next",
      ),
    );
    rows(
      "yourBadges",
      state.you.badges || [],
      "Land a hit to earn your first badge.",
      (b) => {
        const li = item(
          b.label,
          b.description,
          b.earned ? "Earned" : `${b.progress || 0} / ${b.target || 1}`,
        );
        li.classList.toggle("earned", b.earned);
        return li;
      },
    );
    text("yourActiveDays", state.you.active_days || 0);
    text(
      "badgeCount",
      `${(state.you.badges || []).filter((b) => b.earned).length} / 8`,
    );
    if (admin) return;
    const key = "rh.boss.achievements";
    try {
      const old = JSON.parse(sessionStorage.getItem(key) || "null");
      const earned = (state.you.badges || [])
        .filter((b) => b.earned)
        .map((b) => b.id);
      const same = old?.raid === state.raid_id && old?.name === state.you.name;
      const unlocked = same
        ? (state.you.badges || []).filter(
            (b) => b.earned && !old.badges.includes(b.id),
          )
        : [];
      if (same && (level > old.level || unlocked.length)) {
        const message =
          level > old.level
            ? `Community milestone: ${achieved.at(-1).label}! ${level}% conquered together.`
            : `Badge earned: ${unlocked.map((b) => b.label).join(", ")}!`;
        text("milestoneMessage", message);
        const banner = $("milestoneBanner");
        if (banner) banner.hidden = false;
        clearTimeout(milestoneTimer);
        milestoneTimer = setTimeout(() => {
          if (banner) banner.hidden = true;
        }, 8000);
      }
      sessionStorage.setItem(
        key,
        JSON.stringify({
          raid: state.raid_id,
          name: state.you.name,
          level,
          badges: earned,
        }),
      );
    } catch (_) {
      /* Badges still render when browser storage is unavailable. */
    }
    const victory = $("victoryRecap");
    if (victory) victory.hidden = state.status !== "victory";
    if (state.status === "victory")
      text(
        "victorySummary",
        `${number(state.raiders)} raiders · ${number(state.total_attacks)} hits · ${number(state.total_damage)} damage. You contributed ${number(state.you.damage)} damage. Every hit helped.`,
      );
  }
  async function recap() {
    // A host may reopen this same raid with an explicit health edit. Its next
    // victory needs a fresh contributor list, not the previous victory's cache.
    const key = `${state.raid_id}:${state.health_revision || 0}`;
    if (recapRaid === key || recapPending) return;
    recapPending = true;
    const raid = state.raid_id;
    try {
      const { response, value } = await request(
        "/play/api/contributors?raid_id=" + encodeURIComponent(raid),
      );
      if (
        !response.ok ||
        value.raid_id !== state.raid_id ||
        state.status !== "victory" ||
        value.health_revision !== (state.health_revision || 0)
      )
        return;
      rows(
        "allContributors",
        value.contributors,
        "Everyone who landed a hit helped win.",
        (r, i) =>
          item(
            `${i + 1}. ${r.name}`,
            `${number(r.attacks)} hits`,
            number(r.damage),
          ),
      );
      text(
        "recapNote",
        "Every contributor is included, using their raid alias.",
      );
      recapRaid = key;
    } catch (_) {
      text(
        "recapNote",
        "Contributor list is reconnecting. It will retry automatically.",
      );
    } finally {
      recapPending = false;
    }
  }
  function tick() {
    if (!state || authExpired) return;
    const seconds = now(),
      stale = performance.now() - lastGood > 15000;
    text(
      "wardTimer",
      seconds >= state.ward_changes_at
        ? "Weakness changing…"
        : `Changes in ${duration(state.ward_changes_at - seconds)}`,
    );
    text(
      "raidReset",
      state.resets_at
        ? `Next raid day in ${duration(state.resets_at - seconds)}.`
        : "The first community hit starts the 24-hour raid-day schedule.",
    );
    if (!stale)
      text(
        "bossConnection",
        `Live · Last checked ${Math.max(0, Math.floor((performance.now() - lastGood) / 1000))}s ago`,
      );
    else
      text("bossConnection", "Reconnecting · Showing the last confirmed state");
    if (!button) return;
    const active = ["waiting", "active"].includes(state.status);
    // An unacknowledged click can be retried even if its first delivery caused
    // a cooldown or victory. The backend returns the original receipt.
    const retry = Boolean(pending && !busy && !stale && !pendingWrites);
    const ready =
      active &&
      state.connection_ready &&
      state.you.identity_ready &&
      seconds >= state.you.ready_at &&
      !stale &&
      !busy &&
      !pendingWrites;
    button.disabled = !(armed && (retry || ready));
    button.textContent = busy
      ? "Landing your hit…"
      : pendingWrites
        ? "Saving your player…"
        : stale
          ? "Reconnecting…"
          : pending
            ? "Retry last strike"
            : state.status === "victory"
              ? "Victory · We did it!"
              : state.status === "paused"
                ? "Raid paused"
                : !state.connection_ready
                  ? "Connection setup needed"
                  : !state.you.identity_ready
                    ? "Save your username to play"
                    : seconds < state.you.ready_at
                      ? `Next strike in ${duration(state.you.ready_at - seconds)}`
                      : !armed
                        ? inputMode === "keyboard"
                          ? "Release the key to re-arm"
                          : "Move off the button to re-arm"
                        : `Attack with ${labels[selected]} →`;
    text(
      "attackHint",
      pending
        ? "Last strike unconfirmed. Retry safely; it won’t count twice."
        : state.status === "victory"
          ? "You helped write this chapter. The host can open the next raid."
          : !state.you.identity_ready
            ? "Save your username once in this browser."
            : `One strike every ${state.rules.cooldown}s · ${selected === state.weakness ? state.rules.weak_damage : state.rules.damage} damage${state.you.burst_in === 1 ? " + " + state.rules.burst_bonus + " burst" : ""}`,
    );
    if (dockButton) {
      dockButton.disabled = button.disabled;
      dockButton.textContent = button.textContent;
    }
    text("dockRemaining", `${state.rules.cooldown}s cooldown · Unlimited hits`);
    text(
      "rearmHint",
      !armed
        ? inputMode === "keyboard"
          ? "Release Enter or Space before your next hit."
          : "Move your pointer off the attack button before your next hit."
        : "",
    );
    if (stale)
      text("bossConnection", "Reconnecting · Showing the last confirmed state");
  }
  async function request(url, options = {}) {
    const write = options.method === "POST";
    if (write) {
      mutationEpoch++;
      pendingWrites++;
      tick();
    }
    const controller = new AbortController(),
      timeout = setTimeout(() => controller.abort(), 10000);
    try {
      const response = await fetch(url, {
        ...options,
        credentials: "same-origin",
        cache: "no-store",
        signal: controller.signal,
        headers: { Accept: "application/json", ...options.headers },
      });
      if (!response.headers.get("content-type")?.includes("application/json"))
        throw new Error(
          "The game server returned an unexpected response. Try again in a moment.",
        );
      return { response, value: await response.json() };
    } finally {
      clearTimeout(timeout);
      if (write) {
        pendingWrites--;
        tick();
        // Refresh after applying the POST result, including failures. This also
        // replaces any stale poll discarded while the player was being saved.
        if (!pendingWrites) {
          clearTimeout(timer);
          timer = setTimeout(poll, 0);
        }
      }
    }
  }
  async function poll() {
    clearTimeout(timer);
    if (document.hidden || polling || authExpired || pendingWrites) return;
    polling = true;
    const epoch = mutationEpoch;
    try {
      const { response, value } = await request(
        admin ? "/admin/boss/status" : "/play/api/state",
      );
      if (!response.ok) {
        if (admin && response.status === 401) {
          authExpired = true;
          rows(
            "adminBossLeaders",
            [],
            "Sign in again to see private names.",
            () => null,
          );
          for (const id of ["bossAdminHistory", "bossAbuseFlags"])
            rows(id, [], "Sign in again to view this information.", () => null);
          root.querySelectorAll("form button, form input").forEach((el) => {
            el.disabled = true;
          });
          text("bossConnection", "Session expired · Sign in again");
          clearTimeout(timer);
          polling = false;
          return;
        }
        throw new Error(value.error || "The raid is temporarily unavailable.");
      }
      if (epoch === mutationEpoch && !pendingWrites) apply(value);
    } catch (_) {
      text("bossConnection", "Reconnecting · Your saved damage is safe");
      tick();
    } finally {
      polling = false;
      if (!document.hidden && !authExpired)
        timer = setTimeout(poll, (state?.rules.poll_seconds || 5) * 1000);
    }
  }
  function choose(style) {
    if (!labels[style]) return;
    selected = style;
    try {
      localStorage.setItem("rh.boss.style", style);
    } catch (_) {
      /* storage is optional */
    }
    root
      .querySelectorAll("[data-style]")
      .forEach((b) =>
        b.setAttribute("aria-pressed", String(b.dataset.style === style)),
      );
    if ($("dockStyle")) $("dockStyle").value = style;
    tick();
  }
  root
    .querySelectorAll("[data-style]")
    .forEach((el) =>
      el.addEventListener("click", () => choose(el.dataset.style)),
    );
  $("dockStyle")?.addEventListener("change", (event) =>
    choose(event.target.value),
  );
  function rearm() {
    armed = true;
    lockedButton = null;
    tick();
  }
  for (const control of [button, dockButton].filter(Boolean)) {
    control.addEventListener("pointerdown", (event) => {
      inputMode = event.pointerType || "mouse";
    });
    control.addEventListener("pointerleave", () => {
      if (lockedButton === control && inputMode !== "keyboard") rearm();
    });
    control.addEventListener("keydown", (event) => {
      if (!["Enter", " "].includes(event.key)) return;
      if (event.repeat) {
        event.preventDefault();
        return;
      }
      inputMode = "keyboard";
      keyHeld = true;
    });
    // Mouse click latches until the pointer leaves. Touch taps naturally leave
    // the surface on release. Keyboard users must release their activation key.
    control.addEventListener("click", (event) => {
      void attack(event, control);
    });
  }
  document.addEventListener("keyup", (event) => {
    if (["Enter", " "].includes(event.key)) {
      keyHeld = false;
      if (inputMode === "keyboard") rearm();
    }
  });
  document.addEventListener("pointermove", (event) => {
    if (
      armed ||
      !lockedButton ||
      inputMode === "keyboard" ||
      event.pointerType === "touch"
    )
      return;
    const r = lockedButton.getBoundingClientRect();
    if (
      event.clientX < r.left ||
      event.clientX > r.right ||
      event.clientY < r.top ||
      event.clientY > r.bottom
    )
      rearm();
  });
  // A name is saved by the server, never trusted from attack JSON or a URL.
  $("playerNameForm")?.addEventListener("submit", async (event) => {
    // The HTML POST is a complete fallback when scripts/bootstrap/network fail.
    // Never intercept it until the game has a usable state and CSRF token.
    if (!state || !csrf || event.submitter?.id === "saveNamePage") return;
    event.preventDefault();
    if (savingName) return;
    const submitted = nameInput.value;
    const form = event.currentTarget,
      save = form.querySelector("button"),
      label = save.textContent;
    savingName = true;
    save.disabled = true;
    save.textContent = "Saving…";
    form.setAttribute("aria-busy", "true");
    text("playerNameResult", "Saving your username…");
    $("saveNamePage").hidden = true;
    try {
      const { response, value } = await request("/play/api/profile", {
        method: "POST",
        headers: { "Content-Type": "application/json", "X-CSRF-Token": csrf },
        body: JSON.stringify({ raid_id: state.raid_id, username: submitted }),
      });
      if (!response.ok || value.ok === false)
        throw new Error(value.error || "Your username could not be saved.");
      if (
        !value.state?.you?.identity_ready ||
        value.state.you.display_name !== submitted.trim()
      )
        throw new Error(
          "The server did not confirm your username. Your draft is still here; try Save with page reload.",
        );
      nameDirty = nameInput.value !== submitted;
      editingName = nameDirty;
      apply(value);
      text(
        "playerNameResult",
        "Saved. Playing as " + value.state.you.display_name + ".",
      );
    } catch (e) {
      editingName = true;
      nameDirty = true;
      identityView();
      text(
        "playerNameResult",
        e.name === "AbortError"
          ? "Save timed out. Your name may already be saved; retry safely or use Save with page reload."
          : e.message,
      );
      $("saveNamePage").hidden = false;
    } finally {
      savingName = false;
      save.disabled = false;
      save.textContent = label;
      form.removeAttribute("aria-busy");
    }
  });
  $("dismissBossError")?.addEventListener("click", () => error());
  $("dismissMilestone")?.addEventListener("click", () => {
    $("milestoneBanner").hidden = true;
  });
  $("copyRaidLink")?.addEventListener("click", async () => {
    const url = new URL("/play", location.origin).href;
    try {
      await navigator.clipboard.writeText(url);
      text("shareResult", "Raid link copied. Rally the crew!");
    } catch {
      const fallback = $("shareUrl");
      if (fallback) {
        fallback.hidden = false;
        fallback.value = url;
        fallback.focus();
        fallback.select();
      }
      text("shareResult", "Select and copy your raid link.");
    }
  });
  async function attack(event, control) {
    if (busy || control.disabled || !armed) return;
    armed = false;
    lockedButton = control;
    // Touch click follows pointer-up; no held pointer remains on the button.
    if (inputMode === "touch" || (inputMode === "keyboard" && !keyHeld))
      rearm();
    if (!pending) {
      const bytes = new Uint8Array(16);
      crypto.getRandomValues(bytes);
      remember({
        request_id: Array.from(bytes, (b) =>
          b.toString(16).padStart(2, "0"),
        ).join(""),
        raid_id: state.raid_id,
        style: selected,
        name: state.you.name,
      });
    }
    const receipt = pending.request_id;
    busy = true;
    error();
    tick();
    try {
      const { response, value } = await request("/play/api/attack", {
        method: "POST",
        headers: { "Content-Type": "application/json", "X-CSRF-Token": csrf },
        body: JSON.stringify({
          request_id: pending.request_id,
          raid_id: pending.raid_id,
          style: pending.style,
        }),
      });
      if (value.state) apply(value);
      if (!response.ok) {
        // A definitive rejection did not land. A 5xx may have happened after
        // commit, so retain its receipt until a state check resolves it.
        if (response.status < 500) remember(null);
        throw new Error(value.error || "The strike could not be confirmed.");
      }
      strikeFeedback(value.hit, receipt);
      remember(null);
    } catch (e) {
      error(
        e.name === "AbortError"
          ? "The connection timed out. Your hit may have landed. Retry the same strike safely."
          : e.message,
      );
    } finally {
      busy = false;
      tick();
      void poll();
    }
  }
  document.addEventListener("visibilitychange", () => {
    if (document.hidden) clearTimeout(timer);
    else void poll();
  });
  window.addEventListener("online", () => void poll());
  try {
    apply(JSON.parse(root.dataset.bossBootstrap));
    choose(labels[selected] ? selected : "blade");
  } catch (_) {
    error("Reload to reconnect to the raid.");
  }
  setInterval(tick, 1000);
  void poll();
})();
