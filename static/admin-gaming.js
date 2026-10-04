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
    expired = false;
  function render(data) {
    if (expired) return;
    if (
      Number(data.season.id) < season ||
      (Number(data.season.id) === season && data.revision < revision)
    )
      return;
    season = Number(data.season.id);
    revision = data.revision;
    id("gamingAdminReset").textContent =
      `Balances and rankings reset ${data.season.end_et}. One shared 100,000-point wallet per public IP this race week.`;
    id("gamingAdminSummary").textContent =
      `Wallets: ${fmt(data.player_count)} · Completed rounds: ${fmt(data.completed_rounds)} · Linked IPs: ${fmt(data.ip_count)} · Active Blackjack hands: ${fmt(data.active_hands)}`;
    id("gamingNoRecords").hidden = data.completed_rounds > 0;
    if (typeof data.visitor_ip_configured === "boolean")
      id("gamingIpWarning").hidden = data.visitor_ip_configured;
    for (const [game, rows] of Object.entries(data.games)) {
      const list = id("gamingLeaders-" + game);
      if (!list) continue;
      if (data.counts?.[game]) {
        id("gamingCount-" + game).textContent =
          `Players: ${fmt(data.counts[game].players)} · Completed rounds: ${fmt(data.counts[game].rounds)}`;
      }
      list.replaceChildren(
        ...(rows.length
          ? rows.map((row, index) => {
              const item = document.createElement("li");
              for (const [tag, text] of [
                ["strong", `${index + 1}. ${row.name}`],
                ["b", `${row.net > 0 ? "+" : ""}${fmt(row.net)} net RP`],
                [
                  "small",
                  `${fmt(row.paid)} returned · ${fmt(row.wagered)} wagered · ${fmt(row.bets)} rounds`,
                ],
                [
                  "small",
                  `${fmt(row.balance)} available RP · player ${row.player_tag}`,
                ],
                [
                  "small",
                  `IPs: ${row.ips.join(", ") || "Not linked this week yet"}`,
                ],
              ]) {
                const node = document.createElement(tag);
                node.textContent = text;
                item.append(node);
              }
              return item;
            })
          : [
              Object.assign(document.createElement("li"), {
                className: "muted",
                textContent: "No completed rounds this week.",
              }),
            ]),
      );
    }
  }
  function clearPrivateRankings() {
    // A late response from the shared admin feed must not reveal these again.
    expired = true;
    etag = "";
    clearTimeout(timer);
    root.removeAttribute("data-rankings");
    root.querySelectorAll('[id^="gamingLeaders-"]').forEach(list => list.replaceChildren());
    root.querySelectorAll('[id^="gamingCount-"]').forEach(node => { node.textContent = "Sign in to view statistics."; });
    id("gamingAdminSummary").textContent = "Private player information hidden.";
    id("gamingAdminSession").hidden = false;
    id("gamingNoRecords").hidden = true;
    id("gamingIpWarning").hidden = true;
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
          throw Error("The server release changed. Reload this page to use the matching gaming dashboard.");
        render(value);
        etag = response.headers.get("etag") || "";
      }
      id("gamingAdminChecked").textContent =
        "Updated " +
        new Date().toLocaleTimeString() +
        " · checks every 5 seconds";
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
  render(JSON.parse(root.dataset.rankings));
  root.removeAttribute("data-rankings");
  id("refreshGaming").addEventListener("click", refresh);
  document.addEventListener("visibilitychange", () => {
    clearTimeout(timer);
    if (!document.hidden) void refresh();
  });
  void refresh();
})();
