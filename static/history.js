/* Read the shared cache once a minute. Week links also work without scripts. */
(() => {
  "use strict";
  const main = document.querySelector(".history-page");
  if (!main) return;
  const id = (name) => document.getElementById(name);
  const text = (name, value) => {
    id(name).textContent = value;
  };
  const labels = {
    ready: "Provider confirmed",
    partial: "Partial results",
    delayed: "Update delayed",
    loading: "Loading results",
  };
  let selected = main.dataset.selectedWeek,
    timer,
    busy = false;
  let renderedRows = "";

  function apply(value) {
    const week = value.selected;
    if (
      value.release !== document.body.dataset.release ||
      !week ||
      !Array.isArray(week.rows) ||
      week.rows.length > 25 ||
      value.weeks?.length !== 4
    )
      throw new Error("Release mismatch or incomplete history response");
    // Only rebuild week links at the weekly rollover, preserving keyboard focus.
    const navigation = id("historyWeeks");
    const existing = [...navigation.querySelectorAll("[data-week]")].map(
      (a) => a.dataset.week,
    );
    if (existing.join() !== value.weeks.map((w) => w.id).join()) {
      const focusWeek = document.activeElement?.dataset.week;
      const links = value.weeks.map((item, index) => {
        const link = document.createElement("a");
        link.href = "/history?week=" + encodeURIComponent(item.id);
        link.dataset.week = item.id;
        for (const [tag, content, className] of [
          [
            "span",
            index ? "WEEK " + (index + 1) : "LATEST COMPLETED",
            "eyebrow",
          ],
          ["strong", item.label, ""],
          ["small", "Tuesday → Tuesday", ""],
        ]) {
          const node = document.createElement(tag);
          node.textContent = content;
          node.className = className;
          link.append(node);
        }
        return link;
      });
      navigation.replaceChildren(...links);
      links
        .find((a) => a.dataset.week === focusWeek)
        ?.focus({ preventScroll: true });
    }
    selected = week.id;
    const select = id("historyWeekSelect");
    const incomingIds = value.weeks.map((w) => w.id).join();
    if ([...select.options].map((o) => o.value).join() !== incomingIds) {
      const draft = select.value;
      select.replaceChildren(
        ...value.weeks.map((w) => new Option(w.label, w.id)),
      );
      select.value = value.weeks.some((w) => w.id === draft) ? draft : selected;
    }
    const position = value.weeks.findIndex((w) => w.id === selected);
    for (const [name, target] of [
      ["historyPrevious", value.weeks[position + 1]],
      ["historyNext", value.weeks[position - 1]],
    ]) {
      const link = id(name);
      if (target) {
        link.href = "/history?week=" + encodeURIComponent(target.id);
        link.removeAttribute("aria-disabled");
      } else {
        link.removeAttribute("href");
        link.setAttribute("aria-disabled", "true");
      }
    }
    for (const link of navigation.querySelectorAll("a")) {
      if (link.dataset.week === selected)
        link.setAttribute("aria-current", "page");
      else link.removeAttribute("aria-current");
    }
    text("historyTitle", week.label);
    text("historyWindow", week.start_et + " → " + week.end_et);
    text("historyStatus", week.origin === "snapshot" ? "Saved standings" : labels[week.status] || "Loading results");
    text("historyMessage", week.message || "");
    id("historyMessage").hidden = !week.message;
    text(
      "historyCount",
      week.count === null
        ? "Waiting for the first result"
        : week.count +
            (week.origin === "snapshot"
              ? " saved places · final top 25 awaiting confirmation"
              : " qualifying players · showing up to 25"),
    );
    text("historyChecked", "Last checked: " + week.updated_et);
    text(
      "historyPrizeNote",
      week.prizes_known
        ? "Prizes use this week’s saved race settings; only the top 15 places are paid."
        : "No matching prize schedule was saved for this week. Prizes are shown as —.",
    );
    const encoded = JSON.stringify([week.id, week.rows, week.status]);
    if (encoded !== renderedRows) {
      const rows = week.rows.map((row) => {
        const tr = document.createElement("tr");
        [
          String(row.rank).padStart(2, "0"),
          row.username,
          row.wager,
          row.prize,
        ].forEach((content, index) => {
          const td = document.createElement("td");
          td.className = ["rank", "", "number", "number accent"][index];
          td.textContent = content;
          tr.append(td);
        });
        return tr;
      });
      if (!rows.length) {
        const tr = document.createElement("tr"),
          td = document.createElement("td");
        td.colSpan = 4;
        td.className = "empty";
        td.textContent =
          week.status === "ready"
            ? "No qualifying wagers returned for this week."
            : "Results are not available yet. This page checks automatically.";
        tr.append(td);
        rows.push(tr);
      }
      id("historyRows").replaceChildren(...rows);
      renderedRows = encoded;
    }
  }

  async function poll() {
    clearTimeout(timer);
    if (document.hidden || busy) return;
    busy = true;
    const controller = new AbortController();
    const timeout = setTimeout(() => controller.abort(), 12000);
    try {
      const response = await fetch(
        "/history-state?week=" + encodeURIComponent(selected),
        {
          credentials: "same-origin",
          cache: "no-store",
          signal: controller.signal,
        },
      );
      if (
        !response.ok ||
        !response.headers.get("content-type")?.includes("application/json")
      )
        throw new Error("History unavailable");
      apply(await response.json());
      id("historyNetwork").hidden = true;
    } catch {
      text(
        "historyNetwork",
        "Could not check for updates. Saved results remain visible; retrying in 60 seconds. Reload if you recently installed an update.",
      );
      id("historyNetwork").hidden = false;
    } finally {
      clearTimeout(timeout);
      busy = false;
      if (!document.hidden) timer = setTimeout(poll, 60000);
    }
  }
  document.addEventListener("visibilitychange", () => {
    clearTimeout(timer);
    if (!document.hidden) poll();
  });
  poll();
})();
