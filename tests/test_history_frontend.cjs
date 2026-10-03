/* Optional development tests; Node/jsdom are not runtime dependencies. */
const { test } = require("node:test");
const assert = require("node:assert/strict");
const fs = require("node:fs");
const path = require("node:path");
const { JSDOM } = require("jsdom");
const root = path.resolve(__dirname, "..");
const fixture = process.env.DOM_FIXTURES || path.join(root, ".test-fixtures");
const flush = async () => {
  for (let n = 0; n < 5; n++) await new Promise((r) => setImmediate(r));
};
function page() {
  const dom = new JSDOM(
    fs.readFileSync(path.join(fixture, "history.html"), "utf8"),
    { url: "https://example.test/history", runScripts: "outside-only" },
  );
  const w = dom.window,
    timers = new Map(),
    calls = [];
  const value = JSON.parse(
    fs.readFileSync(path.join(fixture, "history.json"), "utf8"),
  );
  let now = 0,
    serial = 0,
    fail = false;
  Object.defineProperty(w.document, "hidden", {
    value: false,
    configurable: true,
  });
  w.setTimeout = (fn, delay) => {
    const id = ++serial;
    timers.set(id, { fn, at: now + delay });
    return id;
  };
  w.clearTimeout = (id) => timers.delete(id);
  w.fetch = async (url) => {
    calls.push({ url, now });
    if (fail) throw Error("offline");
    return {
      ok: true,
      headers: new Map([["content-type", "application/json"]]),
      json: async () => structuredClone(value),
    };
  };
  w.eval(fs.readFileSync(path.join(root, "static/app.js"), "utf8"));
  w.eval(fs.readFileSync(path.join(root, "static/history.js"), "utf8"));
  return {
    w,
    value,
    calls,
    fail(v) {
      fail = v;
    },
    async advance(ms) {
      now += ms;
      for (const [id, t] of [...timers])
        if (t.at <= now) {
          timers.delete(id);
          t.fn();
        }
      await flush();
    },
    close() {
      dom.window.close();
    },
  };
}
test("history renders 25 masked rows, four native links and the active navigation tab", async () => {
  const p = page();
  await flush();
  const d = p.w.document;
  assert.equal(d.querySelectorAll("#historyRows tr").length, 25);
  assert.equal(d.querySelectorAll("#historyWeeks a").length, 4);
  assert.equal(
    d.querySelectorAll('nav[aria-label="Main navigation"] [aria-current]')
      .length,
    1,
  );
  for (const a of d.querySelectorAll("#historyWeeks a"))
    assert.match(a.href, /\/history\?week=\d{4}-\d{2}-\d{2}$/);
  assert.ok(!d.body.textContent.includes("ExamplePlayer"));
  assert.equal(d.querySelectorAll("#historyRows img").length, 0);
  const ids = [...d.querySelectorAll("[id]")].map((x) => x.id);
  assert.equal(new Set(ids).size, ids.length);
  p.close();
});
test("history polls every minute, pauses hidden tabs and reconnects without erasing results", async () => {
  const p = page();
  await flush();
  await p.advance(60000);
  await p.advance(60000);
  assert.deepEqual(
    p.calls.map((c) => c.now),
    [0, 60000, 120000],
  );
  const before = p.w.document.getElementById("historyRows").textContent;
  p.fail(true);
  await p.advance(60000);
  assert.equal(p.w.document.getElementById("historyNetwork").hidden, false);
  assert.equal(p.w.document.getElementById("historyRows").textContent, before);
  Object.defineProperty(p.w.document, "hidden", {
    value: true,
    configurable: true,
  });
  p.w.document.dispatchEvent(new p.w.Event("visibilitychange"));
  await p.advance(180000);
  assert.equal(p.calls.length, 4);
  p.fail(false);
  Object.defineProperty(p.w.document, "hidden", {
    value: false,
    configurable: true,
  });
  p.w.document.dispatchEvent(new p.w.Event("visibilitychange"));
  await flush();
  assert.equal(p.calls.length, 5);
  assert.equal(p.w.document.getElementById("historyNetwork").hidden, true);
  p.close();
});
test("updates use text nodes and preserve table nodes when the results did not change", async () => {
  const p = page();
  await flush();
  const d = p.w.document;
  const first = d.querySelector("#historyRows tr");
  await p.advance(60000);
  assert.strictEqual(d.querySelector("#historyRows tr"), first);
  p.value.selected.rows[0].username = "<img src=x onerror=alert(1)>";
  await p.advance(60000);
  assert.equal(d.querySelector("#historyRows img"), null);
  assert.match(d.querySelector("#historyRows").textContent, /<img/);
  p.close();
});
test("weekly rollover rebuilds four links and follows the selected period", async () => {
  const p = page();
  await flush();
  const week = structuredClone(p.value.weeks[0]);
  week.id = "2030-01-01";
  week.label = "New week";
  p.value.weeks = [week, ...p.value.weeks.slice(0, 3)];
  p.value.selected = week;
  await p.advance(60000);
  assert.equal(p.w.document.querySelectorAll("#historyWeeks a").length, 4);
  assert.equal(
    p.w.document.querySelector("#historyWeeks [aria-current]").dataset.week,
    "2030-01-01",
  );
  await p.advance(60000);
  assert.match(p.calls.at(-1).url, /week=2030-01-01/);
  p.close();
});
