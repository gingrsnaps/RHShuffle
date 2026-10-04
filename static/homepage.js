/* The health bar drains as HP falls; the separate defeated percentage rises.
   Five-second reads use saved anonymous state, never the affiliate providers. */
(() => {
  "use strict";
  const bar = document.getElementById("inviteHealth");
  if (!bar) return;
  const id = (name) => document.getElementById(name);
  const text = (name, value) => {
    id(name).textContent = value;
  };
  const card = bar.closest(".play-invite");
  const retired = new Set();
  let state,
    lastTime = 0,
    timer,
    busy = false,
    flashTimer,
    confirmedAt = null,
    delayed = false;

  function ageLabel(seconds) {
    if (seconds < 1) return "just now";
    if (seconds < 60) return `${seconds} seconds ago`;
    return `${Math.floor(seconds / 60)} minutes ago`;
  }
  function updateAge() {
    if (confirmedAt === null) return;
    const seconds = Math.max(
      0,
      Math.floor((performance.now() - confirmedAt) / 1000),
    );
    text(
      "inviteChecked",
      `Last confirmed ${ageLabel(seconds)}${delayed ? " · retrying" : " · checks every 5s"}`,
    );
    const change = state?.health_change;
    const notice = id("inviteHealthNotice");
    // A brief notice explains deliberate health increases without publishing
    // the admin's name or suggesting that the boss automatically regenerates.
    notice.hidden = !(
      change &&
      Number.isFinite(change.at) &&
      lastTime + seconds >= change.at &&
      lastTime + seconds - change.at < 300
    );
    if (!notice.hidden)
      text(
        "inviteHealthNotice",
        "Admin adjusted HP · recorded damage is unchanged.",
      );
  }

  function apply(value) {
    const next = value.boss,
      at = Number(value.server_time);
    if (
      !next ||
      !Number.isFinite(at) ||
      !Number.isSafeInteger(next.hp) ||
      !Number.isSafeInteger(next.max_hp) ||
      next.max_hp <= 0 ||
      next.hp < 0 ||
      next.hp > next.max_hp ||
      !Number.isSafeInteger(next.version) ||
      !next.raid_id
    )
      throw Error("Invalid boss update");
    if (retired.has(next.raid_id)) return false;
    if (state) {
      if (next.raid_id === state.raid_id) {
        if (
          next.version < state.version ||
          (next.health_revision || 0) < (state.health_revision || 0) ||
          (next.version === state.version && at < lastTime)
        )
          return false;
        if (
          next.total_damage < state.total_damage ||
          next.total_attacks < state.total_attacks ||
          ((next.health_revision || 0) === (state.health_revision || 0) &&
            (next.hp > state.hp || next.max_hp !== state.max_hp))
        )
          return false;
      } else {
        if (at < lastTime || (next.created_at || 0) < (state.created_at || 0))
          return false;
        retired.add(state.raid_id);
      }
    }
    const hit =
      state &&
      next.raid_id === state.raid_id &&
      next.hp < state.hp &&
      next.total_attacks > state.total_attacks;
    state = next;
    lastTime = Math.max(lastTime, at);
    confirmedAt = performance.now();
    delayed = false;
    id("inviteError").hidden = true;
    const percent = ((next.max_hp - next.hp) / next.max_hp) * 100;
    bar.max = next.max_hp;
    bar.value = next.hp;
    bar.setAttribute(
      "aria-valuetext",
      `${next.hp.toLocaleString()} of ${next.max_hp.toLocaleString()} HP remaining`,
    );
    text("invitePercent", percent.toFixed(2) + "% defeated");
    text(
      "inviteProgress",
      `${next.hp.toLocaleString()} HP left · ${next.raiders} raiders united`,
    );
    text("inviteBossName", next.name);
    const hitData = next.latest_hit;
    text(
      "inviteLatestHit",
      hitData && Number.isSafeInteger(hitData.damage) && hitData.damage >= 0
        ? `${String(hitData.name).slice(0, 2)}****** dealt ${hitData.damage.toLocaleString()} damage.`
        : "No hits in this raid yet.",
    );
    text(
      "inviteTitle",
      next.status === "victory"
        ? `The crew conquered ${next.name}.`
        : next.status === "paused"
          ? "The raid is taking a breather."
          : "Take your next shot.",
    );
    text(
      "inviteButtonLabel",
      next.status === "victory"
        ? "View the victory"
        : next.status === "paused"
          ? "View the raid"
          : "Join the fight",
    );
    const avatar = id("inviteAvatar");
    if (next.avatar_url?.startsWith("/") && !next.avatar_url.startsWith("//"))
      avatar.src = next.avatar_url;
    avatar.classList.toggle("custom-avatar", Boolean(next.avatar_custom));
    card.classList.toggle("is-victory", next.status === "victory");
    if (hit) {
      card.classList.add("confirmed-hit");
      clearTimeout(flashTimer);
      flashTimer = setTimeout(
        () => card.classList.remove("confirmed-hit"),
        650,
      );
    }
    updateAge();
    return true;
  }
  document.addEventListener("boss:summary", (event) => {
    try {
      apply(event.detail);
    } catch {}
  });
  try {
    apply(JSON.parse(document.body.dataset.bootstrap));
  } catch {}

  async function poll() {
    clearTimeout(timer);
    if (document.hidden || busy) return;
    busy = true;
    const controller = new AbortController();
    const timeout = setTimeout(() => controller.abort(), 8000);
    try {
      const response = await fetch("/boss-summary", {
        cache: "no-store",
        credentials: "same-origin",
        signal: controller.signal,
      });
      if (
        !response.ok ||
        !response.headers.get("content-type")?.includes("application/json")
      )
        throw Error("Boss unavailable");
      const value = await response.json();
      if (value.release !== document.body.dataset.release)
        throw Error("New release");
      if (!apply(value)) throw Error("Stale boss update");
    } catch {
      delayed = true;
      updateAge();
      text(
        "inviteError",
        "Showing the last confirmed progress. Retrying automatically; reload after an app update.",
      );
      id("inviteError").hidden = false;
    } finally {
      clearTimeout(timeout);
      busy = false;
      if (!document.hidden) timer = setTimeout(poll, 5000);
    }
  }
  document.addEventListener("visibilitychange", () => {
    clearTimeout(timer);
    if (!document.hidden) poll();
  });
  setInterval(() => {
    if (!document.hidden) updateAge();
  }, 1000);
  poll();
})();
