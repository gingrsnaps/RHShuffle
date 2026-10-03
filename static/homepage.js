/* Homepage progress is damage/maximum HP. The arena's separate HP bar drains.
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
    flashTimer;

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
    if (retired.has(next.raid_id)) return;
    if (state) {
      if (next.raid_id === state.raid_id) {
        if (
          next.version < state.version ||
          (next.health_revision || 0) < (state.health_revision || 0)
        )
          return;
        if (
          next.total_damage < state.total_damage ||
          next.total_attacks < state.total_attacks ||
          ((next.health_revision || 0) === (state.health_revision || 0) &&
            (next.hp > state.hp || next.max_hp !== state.max_hp))
        )
          return;
      } else {
        if (at < lastTime || (next.created_at || 0) < (state.created_at || 0))
          return;
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
    const percent = ((next.max_hp - next.hp) / next.max_hp) * 100;
    bar.value = percent;
    bar.setAttribute("aria-valuetext", percent.toFixed(2) + "% defeated");
    text("invitePercent", percent.toFixed(2) + "% defeated");
    text(
      "inviteProgress",
      `${next.hp.toLocaleString()} HP left · ${next.raiders} raiders united`,
    );
    text("inviteBossName", next.name);
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
      apply(value);
      text("inviteChecked", "Live · checks every 5 seconds");
      id("inviteError").hidden = true;
    } catch {
      text("inviteChecked", "Update delayed");
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
  poll();
})();
