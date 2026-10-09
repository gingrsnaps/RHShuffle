/* Admin-only local stats. No calls to Shuffle and no extra provider work. */
(() => {
  "use strict";
  const root = document.getElementById("gamingAdmin");
  if (!root) return;
  const id = (name) => document.getElementById(name),
    fmt = (n) => Number(n).toLocaleString("en-US");
  let timer,
    busy = false,
    etag = "",
    season = 0,
    revision = -1,
    granting = false,
    expired = false;
  const rowKeys = new Map();
  function render(data) {
    if (expired) return;
    if (data.boss) globalThis.RedHealth?.renderBoss(data.boss);
    if (
      Number(data.season.id) < season ||
      (Number(data.season.id) === season && data.revision < revision)
    )
      return;
    season = Number(data.season.id);
    revision = data.revision;
    id("gamingAdminReset").textContent = `Weekly reset: ${data.season.end_et}.`;
    id("gamingAdminSummary").textContent =
      `Players: ${fmt(data.player_count)} · Rounds: ${fmt(data.completed_rounds)} · Active hands: ${fmt(data.active_hands)}`;
    const grant = data.last_grant;
    id("gamingLastGrant").textContent = grant
      ? `Last grant: ${grant.actor} · +${fmt(grant.amount)} each · ${fmt(grant.players)} ${grant.players === 1 ? "wallet" : "wallets"} · ${new Date(grant.at * 1000).toLocaleString()}`
      : "No admin points grant has been saved yet.";
    id("gamingNoRecords").hidden = data.completed_rounds > 0;
    if (typeof data.visitor_ip_configured === "boolean")
      id("gamingIpWarning").hidden = data.visitor_ip_configured;
    for (const [game, rows] of Object.entries({
      ...data.games,
      video_poker: data.legacy_poker || [],
    })) {
      const list = id("gamingLeaders-" + game);
      if (!list) continue;
      const count =
        game === "video_poker" ? data.legacy_poker_counts : data.counts?.[game];
      if (count) {
        id("gamingCount-" + game).textContent =
          `Players: ${fmt(count.players)} · Completed rounds: ${fmt(count.rounds)}`;
      }
      const key = JSON.stringify(rows);
      if (rowKeys.get(game) === key) continue;
      rowKeys.set(game, key);
      // Preserve open records and keyboard focus when a score changes.
      const open = new Set(
        [...list.querySelectorAll("details[open]")].map(
          (node) => node.closest("[data-player-key]").dataset.playerKey,
        ),
      );
      const focused = list.contains(document.activeElement)
        ? document.activeElement.closest("[data-player-key]")?.dataset.playerKey
        : null;
      list.replaceChildren(
        ...(rows.length
          ? rows.map((row, index) => {
              const item = document.createElement("li"),
                detail = document.createElement("details"),
                summary = document.createElement("summary");
              item.dataset.playerKey = game + ":" + row.player_tag;
              item.dataset.tone =
                row.net > 0 ? "positive" : row.net < 0 ? "negative" : "neutral";
              detail.className = "player-breakdown";
              detail.open = open.has(item.dataset.playerKey);
              const name = document.createElement("span"),
                rank = document.createElement("small"),
                label = document.createElement("strong"),
                score = document.createElement("b"),
                unit = document.createElement("small");
              name.className = "leader-name";
              rank.textContent = index + 1;
              label.textContent = row.name;
              name.append(rank, label);
              score.textContent = `${row.net >= 0 ? "+" : ""}${fmt(row.net)} `;
              unit.textContent = "RP";
              score.append(unit);
              summary.append(name, score);
              const record = document.createElement("div");
              record.className = "player-record";
              for (const value of [
                `${fmt(row.paid)} returned · ${fmt(row.wagered)} wagered · ${row.bets} rounds`,
                `${fmt(row.balance)} available RP · player ${row.player_tag}`,
                `IPs: ${row.ips.join(", ") || "Not linked this week yet"}`,
                `Funding adjustments: ${(row.funding_adjustment || 0) >= 0 ? "+" : ""}${fmt(row.funding_adjustment || 0)} RP · excluded from winnings`,
              ]) {
                const node = document.createElement("small");
                node.textContent = value;
                record.append(node);
              }
              detail.append(summary, record);
              item.append(detail);
              return item;
            })
          : [
              Object.assign(document.createElement("li"), {
                className: "muted",
                textContent: "No completed rounds this week.",
              }),
            ]),
      );
      if (focused)
        [...list.children]
          .find((node) => node.dataset.playerKey === focused)
          ?.querySelector("summary")
          ?.focus({ preventScroll: true });
    }
  }
  function clearPrivateRankings() {
    // A late response from the shared admin feed must not reveal these again.
    expired = true;
    rowKeys.clear();
    etag = "";
    clearTimeout(timer);
    root.removeAttribute("data-rankings");
    root
      .querySelectorAll('[id^="gamingLeaders-"]')
      .forEach((list) => list.replaceChildren());
    root.querySelectorAll('[id^="gamingCount-"]').forEach((node) => {
      node.textContent = "Sign in to view statistics.";
    });
    id("gamingAdminSummary").textContent = "Private player information hidden.";
    id("gamingAdminSession").hidden = false;
    id("gamingNoRecords").hidden = true;
    id("gamingIpWarning").hidden = true;
    id("grantGamingButton").disabled = true;
    id("gamingGrantMessage").textContent = "Sign in again to grant points.";
    id("gamingLastGrant").textContent = "Sign in to view grant history.";
  }
  async function giveEveryone(event) {
    event.preventDefault();
    if (granting || expired) return;
    granting = true;
    const button = id("grantGamingButton"),
      form = event.currentTarget;
    button.disabled = true;
    id("gamingGrantMessage").textContent = "Saving the grant to every wallet…";
    const controller = new AbortController(),
      timeout = setTimeout(() => controller.abort(), 15000);
    try {
      // Keep the same request ID after failures, including a lost response.
      // The server remembers it so retrying cannot credit the grant twice.
      const response = await fetch(form.action, {
        method: "POST",
        body: new FormData(form),
        credentials: "same-origin",
        cache: "no-store",
        headers: { Accept: "application/json" },
        signal: controller.signal,
      });
      if (response.status === 401 || response.status === 403) {
        clearPrivateRankings();
        throw Error("Sign in again to grant points.");
      }
      if (!response.headers.get("content-type")?.includes("application/json"))
        throw Error(
          "Unexpected response. Reload the admin panel and check the last grant.",
        );
      const value = await response.json();
      if (!response.ok || !value.ok)
        throw Error(value.error || "The grant was not saved.");
      if (expired) return;
      if (value.release !== document.body.dataset.release)
        throw Error(
          "The release changed. Reload and check the last grant before continuing.",
        );
      render(value);
      etag = "";
      form.elements.namedItem("request_id").value = value.next_request_id;
      id("gamingGrantMessage").textContent = value.message;
    } catch (error) {
      id("gamingGrantMessage").textContent =
        error.name === "AbortError"
          ? "Response timed out. You can retry this same grant safely; it will not be added twice."
          : error.message;
    } finally {
      clearTimeout(timeout);
      granting = false;
      button.disabled = expired;
    }
  }
  async function refresh() {
    clearTimeout(timer);
    if (busy || expired || document.hidden) return;
    busy = true;
    id("refreshGaming").disabled = true;
    const controller = new AbortController(),
      timeout = setTimeout(() => controller.abort(), 10000);
    try {
      const response = await fetch("/admin/gaming/status", {
        credentials: "same-origin",
        cache: "no-store",
        signal: controller.signal,
        headers: {
          Accept: "application/json",
          ...(etag ? { "If-None-Match": etag } : {}),
        },
      });
      if (response.status === 401 || response.status === 403) {
        clearPrivateRankings();
        throw Error("Sign in again to view gaming statistics.");
      }
      if (response.status !== 304) {
        if (
          !response.ok ||
          !response.headers.get("content-type")?.includes("application/json")
        )
          throw Error("Stats are delayed. Saved rankings remain visible.");
        const value = await response.json();
        if (value.release && value.release !== document.body.dataset.release)
          throw Error(
            "The server release changed. Reload this page to use the matching gaming dashboard.",
          );
        render(value);
        etag = response.headers.get("etag") || "";
      }
      id("gamingAdminChecked").textContent =
        "Updated " + new Date().toLocaleTimeString() + "";
    } catch (error) {
      id("gamingAdminChecked").textContent =
        error.name === "AbortError"
          ? "Update timed out; retrying automatically."
          : error.message;
    } finally {
      clearTimeout(timeout);
      busy = false;
      id("refreshGaming").disabled = expired;
      if (!document.hidden && !expired) timer = setTimeout(refresh, 5000);
    }
  }
  globalThis.RedGamingAdmin = { render };
  document.addEventListener("admin:expired", clearPrivateRankings);
  render(JSON.parse(root.dataset.rankings));
  root.removeAttribute("data-rankings");
  id("refreshGaming").addEventListener("click", refresh);
  id("grantGamingForm").addEventListener("submit", giveEveryone);
  document.addEventListener("visibilitychange", () => {
    clearTimeout(timer);
    if (!document.hidden) void refresh();
  });
  void refresh();
})();
