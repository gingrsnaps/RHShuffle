/* The minute feed owns provider and storage health. No extra provider requests are created here. */
(() => {
  "use strict";
  const root = document.getElementById("systemHealth");
  if (!root) return;
  const id = (name) => document.getElementById(name);
  const put = (node, value) => {
    if (node && node.textContent !== String(value)) node.textContent = value;
  };
  const date = (value) =>
    value ? new Date(value * 1000).toLocaleString() : "Not recorded";
  let health,
    issueKey = "",
    metricsKey = "";
  function attention() {
    const issues = (health?.components || []).filter(
      (item) => item.state !== "good",
    );
    // A failed save is one incident, even though both Games and Saved data report it.
    const shown = issues.filter(
      (item) =>
        item.key !== "games" ||
        !issues.some((other) => other.key === "storage"),
    );
    const key = JSON.stringify(shown.map((item) => [item.key, item.state]));
    const network = id("networkError") && !id("networkError").hidden;
    id("adminAttention").dataset.state =
      network || shown.length ? "warning" : "good";
    put(
      id("attentionSummary"),
      network
        ? "Dashboard updates delayed"
        : shown.length
          ? "Needs attention"
          : "Everything is connected",
    );
    if (key === issueKey) return;
    issueKey = key;
    const list = id("adminIssueList");
    list.hidden = !shown.length;
    list.replaceChildren(
      ...shown.map((item) => {
        const li = document.createElement("li");
        li.textContent =
          item.label +
          ": " +
          (["storage", "games"].includes(item.key)
            ? "Saving unavailable. Check storage before making changes."
            : "Updates delayed. Saved results remain visible; retrying automatically.");
        return li;
      }),
    );
  }
  function render(value) {
    if (!value?.components) return;
    health = value;
    for (const item of value.components) {
      const card = [...root.querySelectorAll("[data-health-card]")].find(
        (node) => node.dataset.healthCard === item.key,
      );
      if (!card) continue;
      card.dataset.state = item.state;
      put(card.querySelector("[data-health-status]"), item.status);
      put(card.querySelector("[data-health-detail]"), item.detail);
      put(
        card.querySelector("[data-health-time]"),
        item.last_success
          ? "Confirmed " + date(item.last_success)
          : "Waiting for first confirmation",
      );
    }
    attention();
    const m = value.metrics,
      s = m.storage;
    const items = [
      [
        "Request p95",
        m.latency.samples ? m.latency.p95_ms + " ms" : "Collecting",
      ],
      ["Save p95", s.write.samples ? s.write.p95_ms + " ms" : "Collecting"],
      ["Lock wait p95", s.lock_wait.p95_ms + " ms"],
      ["State file", (s.bytes / 1048576).toFixed(2) + " MB"],
      ["Server errors", String(m.server_errors)],
      ["Last save", date(s.last_write)],
    ];
    const key = JSON.stringify(items);
    if (key === metricsKey) return;
    metricsKey = key;
    id("healthMetrics").replaceChildren(
      ...items.map(([label, text]) => {
        const node = document.createElement("div"),
          name = document.createElement("span"),
          count = document.createElement("strong");
        name.textContent = label;
        count.textContent = text;
        node.append(name, count);
        return node;
      }),
    );
  }
  globalThis.RedHealth = { render, attention };
  render(JSON.parse(root.dataset.health));
  id("copyHealthReport").addEventListener("click", async (event) => {
    const feedback = id("healthReportFeedback"),
      button = event.currentTarget;
    button.disabled = true;
    try {
      const response = await fetch("/admin/health-report", {
        headers: { Accept: "application/json" },
        credentials: "same-origin",
        cache: "no-store",
        signal: AbortSignal.timeout(10000),
      });
      if ([401, 403].includes(response.status))
        throw Error("Sign in again to get a current report.");
      if (!response.ok) throw Error("Report unavailable. Check runtime logs.");
      const report = JSON.stringify(await response.json(), null, 2);
      try {
        await navigator.clipboard.writeText(report);
        feedback.textContent =
          "Support report copied. No private player data or credentials included.";
      } catch {
        const url = URL.createObjectURL(
          new Blob([report], { type: "application/json" }),
        );
        const link = document.createElement("a");
        link.href = url;
        link.download = "redhunllef-support.json";
        link.click();
        setTimeout(() => URL.revokeObjectURL(url), 1000);
        feedback.textContent =
          "Clipboard unavailable. The support report was downloaded instead.";
      }
    } catch (error) {
      feedback.textContent = error.message;
    } finally {
      button.disabled = false;
      feedback.hidden = false;
    }
  });
})();
