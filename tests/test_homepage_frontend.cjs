const { test } = require("node:test");
const assert = require("node:assert/strict");
const fs = require("node:fs");
const path = require("node:path");
const { JSDOM } = require("jsdom");
const root = path.resolve(__dirname, ".."),
  fixtures = process.env.DOM_FIXTURES || path.join(root, ".test-fixtures");
const flush = async () => {
  for (let n = 0; n < 5; n++) await new Promise((r) => setImmediate(r));
};
function page() {
  const dom = new JSDOM(
    fs.readFileSync(path.join(fixtures, "public.html"), "utf8"),
    { url: "https://example.test/", runScripts: "outside-only" },
  );
  const w = dom.window,
    feed = JSON.parse(
      fs.readFileSync(path.join(fixtures, "public.json"), "utf8"),
    ),
    timers = new Map(),
    calls = [];
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
    calls.push({ url, at: now });
    if (fail) throw Error("offline");
    return {
      ok: true,
      headers: new Map([["content-type", "application/json"]]),
      json: async () => structuredClone(feed),
    };
  };
  w.eval(fs.readFileSync(path.join(root, "static/homepage.js"), "utf8"));
  return {
    w,
    feed,
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
      w.close();
    },
  };
}
test("homepage bar and remaining percentage drain together", async () => {
  const p = page();
  await flush();
  for (const percent of [0, 25, 75, 100]) {
    p.feed.boss.hp = (p.feed.boss.max_hp * (100 - percent)) / 100;
    p.feed.boss.version++;
    p.feed.boss.total_damage = p.feed.boss.max_hp - p.feed.boss.hp;
    p.feed.boss.total_attacks++;
    p.feed.boss.status = percent === 100 ? "victory" : "active";
    await p.advance(5000);
    assert.equal(
      p.w.document.querySelector("#inviteHealth").value,
      p.feed.boss.hp,
    );
    assert.equal(
      p.w.document.querySelector("#inviteHealth").max,
      p.feed.boss.max_hp,
    );
    assert.equal(
      p.w.document.querySelector("#invitePercent").textContent,
      (100 - percent).toFixed(2) + "% remaining",
    );
  }
  assert.match(
    p.w.document.querySelector("#inviteButtonLabel").textContent,
    /victory/,
  );
  p.close();
});
test("homepage checks only the local summary every five seconds and pauses while hidden", async () => {
  const p = page();
  await flush();
  await p.advance(5000);
  await p.advance(5000);
  assert.deepEqual(
    p.calls.map((c) => c.at),
    [0, 5000, 10000],
  );
  assert.ok(p.calls.every((c) => c.url === "/boss-summary"));
  Object.defineProperty(p.w.document, "hidden", {
    value: true,
    configurable: true,
  });
  p.w.document.dispatchEvent(new p.w.Event("visibilitychange"));
  await p.advance(60000);
  assert.equal(p.calls.length, 3);
  Object.defineProperty(p.w.document, "hidden", {
    value: false,
    configurable: true,
  });
  p.w.document.dispatchEvent(new p.w.Event("visibilitychange"));
  await flush();
  assert.equal(p.calls.length, 4);
  p.close();
});
test("a delayed minute poll cannot reverse damage; explicit admin heals can", async () => {
  const p = page();
  await flush();
  const old = structuredClone(p.feed);
  p.feed.boss.hp /= 4;
  p.feed.boss.version++;
  p.feed.boss.total_damage = p.feed.boss.max_hp - p.feed.boss.hp;
  p.feed.boss.total_attacks++;
  await p.advance(5000);
  p.w.document.dispatchEvent(
    new p.w.CustomEvent("boss:summary", { detail: old }),
  );
  assert.equal(
    p.w.document.querySelector("#inviteHealth").value,
    p.feed.boss.max_hp / 4,
  );
  p.feed.boss.health_revision++;
  p.feed.boss.version++;
  p.feed.boss.hp = p.feed.boss.max_hp;
  await p.advance(5000);
  assert.equal(
    p.w.document.querySelector("#inviteHealth").value,
    p.feed.boss.max_hp,
  );
  p.close();
});
test("new raid starts at zero and retired raid responses cannot return", async () => {
  const p = page();
  await flush();
  const old = structuredClone(p.feed);
  p.feed.boss.raid_id = "new-raid";
  p.feed.server_time += 10;
  p.feed.boss.created_at += 10;
  await p.advance(5000);
  old.server_time += 100;
  old.boss.hp = 0;
  old.boss.version += 100;
  p.w.document.dispatchEvent(
    new p.w.CustomEvent("boss:summary", { detail: old }),
  );
  assert.equal(
    p.w.document.querySelector("#inviteHealth").value,
    p.feed.boss.max_hp,
  );
  p.close();
});
test("connection failure retains confirmed progress and hostile boss names stay text", async () => {
  const p = page();
  await flush();
  p.feed.boss.name = "<img src=x>";
  p.feed.boss.status = "victory";
  p.feed.boss.hp = 0;
  p.feed.boss.version++;
  await p.advance(5000);
  assert.equal(p.w.document.querySelector("#inviteTitle img"), null);
  assert.match(
    p.w.document.querySelector("#inviteTitle").textContent,
    /<img src=x>/,
  );
  p.fail(true);
  await p.advance(5000);
  assert.equal(p.w.document.querySelector("#inviteHealth").value, 0);
  assert.equal(p.w.document.querySelector("#inviteError").hidden, false);
  p.close();
});
