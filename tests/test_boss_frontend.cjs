/* Real rendered templates; fake clock/transport exercise shared-state behavior. */
const { test } = require("node:test");
const assert = require("node:assert/strict");
const fs = require("node:fs");
const path = require("node:path");
const { JSDOM } = require("jsdom");
const root = path.resolve(__dirname, ".."),
  fixtures = process.env.DOM_FIXTURES || path.join(root, ".test-fixtures");
const code = fs.readFileSync(path.join(root, "static/boss.js"), "utf8");
const flush = async () => {
  for (let i = 0; i < 8; i++) await new Promise((r) => setImmediate(r));
};
const response = (value, status = 200) => ({
  ok: status < 400,
  status,
  headers: new Map([["content-type", "application/json"]]),
  json: async () => structuredClone(value),
});
function page(name = "play", initialStyle) {
  const dom = new JSDOM(
    fs.readFileSync(path.join(fixtures, name + ".html"), "utf8"),
    { url: "https://example.test/play", runScripts: "outside-only" },
  );
  const w = dom.window,
    calls = [],
    timers = new Map(),
    intervals = new Map();
  let clock = 0,
    serial = 0;
  let value = JSON.parse(
    fs.readFileSync(
      path.join(fixtures, name === "boss" ? "boss-admin.json" : "boss.json"),
      "utf8",
    ),
  );
  Object.defineProperty(w.performance, "now", { value: () => clock });
  Object.defineProperty(w.document, "hidden", {
    value: false,
    configurable: true,
  });
  w.setTimeout = (fn, delay) => {
    const id = ++serial;
    timers.set(id, { fn, at: clock + delay });
    return id;
  };
  w.clearTimeout = (id) => timers.delete(id);
  w.setInterval = (fn) => {
    const id = ++serial;
    intervals.set(id, fn);
    return id;
  };
  let responder = async () => response(value);
  w.fetch = async (url, options) => {
    calls.push({ url, options });
    return responder(url, options);
  };
  if (initialStyle) w.localStorage.setItem("rh.boss.style", initialStyle);
  w.eval(code);
  return {
    w,
    dom,
    calls,
    value,
    timers,
    respond(fn) {
      responder = fn;
    },
    async advance(ms) {
      clock += ms;
      for (const [id, t] of [...timers])
        if (t.at <= clock) {
          timers.delete(id);
          t.fn();
        }
      for (const fn of intervals.values()) fn();
      await flush();
    },
    close() {
      dom.window.close();
    },
  };
}
test("bare game has unique IDs, working controls and no explanations or footer", async () => {
  const p = page();
  await flush();
  const doc = p.w.document,
    ids = [...doc.querySelectorAll("[id]")].map((e) => e.id);
  assert.equal(new Set(ids).size, ids.length);
  assert.equal(doc.querySelector("#howToPlay"), null);
  assert.equal(doc.querySelector("#bossStory"), null);
  assert.equal(doc.querySelector("#attackHint"), null);
  assert.equal(doc.querySelector('footer a[href="/admin"]'), null);
  assert.equal(doc.querySelector("#attackButton").disabled, false);
  p.close();
});
test("game polls every five seconds and pauses while hidden", async () => {
  const p = page();
  await flush();
  assert.equal(p.calls.length, 1);
  await p.advance(5000);
  assert.equal(p.calls.length, 2);
  Object.defineProperty(p.w.document, "hidden", {
    value: true,
    configurable: true,
  });
  p.w.document.dispatchEvent(new p.w.Event("visibilitychange"));
  await p.advance(10000);
  assert.equal(p.calls.length, 2);
  Object.defineProperty(p.w.document, "hidden", {
    value: false,
    configurable: true,
  });
  p.w.document.dispatchEvent(new p.w.Event("visibilitychange"));
  await flush();
  assert.equal(p.calls.length, 3);
  assert.ok(p.calls.every((x) => !x.options.method));
  p.close();
});
test("attack sends only server-validated inputs and renders countdown", async () => {
  const p = page();
  await flush();
  let sent;
  p.respond(async (url, options) => {
    if (options.method === "POST") {
      sent = JSON.parse(options.body);
      const s = p.value.state;
      s.version++;
      s.hp -= 150;
      s.total_damage = 150;
      s.total_attacks = 1;
      s.you.ready_at = s.server_time + 30;
      s.you.last_request = sent.request_id;
      s.you.last_hit = {
        damage: 150,
        style: sent.style,
        weakness: true,
        burst: false,
      };
      return response({ ok: true, state: s, hit: s.you.last_hit });
    }
    return response(p.value);
  });
  p.w.document.querySelector('[data-style="bow"]').click();
  p.w.document.querySelector("#attackButton").click();
  await flush();
  assert.deepEqual(Object.keys(sent).sort(), [
    "raid_id",
    "request_id",
    "style",
  ]);
  assert.equal(sent.style, "bow");
  const post = p.calls.find((c) => c.options.method === "POST");
  assert.equal(post.options.headers["X-CSRF-Token"], p.value.csrf);
  assert.equal(p.w.document.querySelector("#attackButton").disabled, true);
  assert.match(p.w.document.querySelector("#attackButton").textContent, /0:30/);
  assert.match(p.w.document.querySelector("#hitResult").textContent, /150/);
  p.close();
});
test("uncertain delivery keeps receipt and retry uses same ID", async () => {
  const p = page();
  await flush();
  const ids = [];
  p.respond(async (url, options) => {
    if (options.method === "POST") {
      ids.push(JSON.parse(options.body).request_id);
      throw new Error("Network disconnected");
    }
    return response(p.value);
  });
  p.w.document.querySelector("#attackButton").click();
  await flush();
  assert.match(
    p.w.document.querySelector("#attackButton").textContent,
    /Retry last strike/,
  );
  p.w.document
    .querySelector("#attackButton")
    .dispatchEvent(new p.w.Event("pointerleave"));
  p.w.document.querySelector("#attackButton").click();
  await flush();
  assert.equal(ids.length, 2);
  assert.equal(ids[0], ids[1]);
  p.close();
});
test("older polls cannot reverse boss damage", async () => {
  const p = page();
  await flush();
  const old = structuredClone(p.value);
  p.value.state.hp -= 250;
  p.value.state.version++;
  p.value.state.server_time++;
  await p.advance(5000);
  assert.equal(
    p.w.document.querySelector("#bossHealthBar").value,
    p.value.state.max_hp - p.value.state.hp,
  );
  p.respond(async () => response(old));
  await p.advance(5000);
  assert.equal(
    p.w.document.querySelector("#bossHealthBar").value,
    p.value.state.max_hp - p.value.state.hp,
  );
  p.close();
});
test("victory and paused raids stop attacks, hostile names render as text", async () => {
  const p = page();
  await flush();
  p.value.state.status = "paused";
  p.value.state.leaders = [
    {
      name: "<img src=x onerror=alert(1)>",
      damage: 100,
      attacks: 1,
      you: false,
    },
  ];
  await p.advance(5000);
  assert.equal(p.w.document.querySelector("#attackButton").disabled, true);
  assert.equal(p.w.document.querySelector("#bossLeaders img"), null);
  p.value.state.status = "victory";
  p.value.state.hp = 0;
  await p.advance(5000);
  assert.match(
    p.w.document.querySelector("#attackButton").textContent,
    /Victory/,
  );
  assert.equal(p.w.document.querySelector("#victoryRecap").hidden, false);
  p.close();
});
test("admin boss updates preserve difficulty draft and restart confirmation", async () => {
  const p = page("boss");
  await flush();
  const input = p.w.document.querySelector("#bossHealthInput");
  input.value = "5000000";
  const confirm = p.w.document.querySelector('[name="confirm_restart"]');
  confirm.checked = true;
  await p.advance(5000);
  assert.equal(input.value, "5000000");
  assert.equal(confirm.checked, true);
  assert.equal(p.w.document.querySelector("footer"), null);
  p.close();
});

test("a successful background poll cannot erase an attack error", async () => {
  const p = page();
  await flush();
  p.respond(async (url, options) =>
    options.method === "POST"
      ? response({ error: "Your shared connection is cooling down." }, 429)
      : response(p.value),
  );
  p.w.document.querySelector("#attackButton").click();
  await flush();
  await p.advance(5000);
  await p.advance(5000);
  const error = p.w.document.querySelector("#bossError");
  assert.equal(error.hidden, false);
  assert.match(error.textContent, /shared connection/);
  p.w.document.querySelector("#dismissBossError").click();
  assert.equal(error.hidden, true);
  p.close();
});

test("unchanged contributor rows survive polls and mobile styles share attack controls", async () => {
  const p = page();
  await flush();
  p.value.state.leaders = [
    { name: "Raider ABCDEF12", damage: 150, attacks: 1, you: false },
  ];
  await p.advance(5000);
  const row = p.w.document.querySelector("#bossLeaders li");
  await p.advance(5000);
  assert.strictEqual(p.w.document.querySelector("#bossLeaders li"), row);
  const style = p.w.document.querySelector("#dockStyle");
  style.value = "magic";
  style.dispatchEvent(new p.w.Event("change"));
  assert.equal(
    p.w.document
      .querySelector('[data-style="magic"]')
      .getAttribute("aria-pressed"),
    "true",
  );
  let sent;
  p.respond(async (url, options) => {
    if (options.method === "POST") {
      sent = JSON.parse(options.body);
      return response({ error: "Fixture rejection" }, 400);
    }
    return response(p.value);
  });
  p.w.document.querySelector("#dockAttack").click();
  await flush();
  assert.equal(sent.style, "magic");
  p.close();
});

test("copy link supplies selectable text if clipboard access is unavailable", async () => {
  const p = page();
  await flush();
  p.w.document.querySelector("#copyRaidLink").click();
  await flush();
  const field = p.w.document.querySelector("#shareUrl");
  assert.equal(field.hidden, false);
  assert.equal(field.value, "https://example.test/play");
  assert.equal(field.selectionEnd, field.value.length);
  p.close();
});

test("same-raid updates cannot refill health even with a newer version or clock", async () => {
  const p = page();
  await flush();
  p.value.state.hp -= 150;
  p.value.state.total_damage = 150;
  p.value.state.total_attacks = 1;
  p.value.state.version++;
  await p.advance(5000);
  const hp = p.value.state.hp;
  p.value.state.hp += 150;
  p.value.state.total_damage = 0;
  p.value.state.total_attacks = 0;
  for (const versionBump of [0, 10]) {
    p.value.state.version += versionBump;
    p.value.state.server_time += 5;
    await p.advance(5000);
    assert.equal(
      p.w.document.querySelector("#bossHealthBar").value,
      p.value.state.max_hp - hp,
    );
    assert.equal(p.w.document.querySelector("#bossDamage").textContent, "150");
  }
  p.close();
});

test("defeat progress stays at 100 percent until a different raid starts", async () => {
  const p = page();
  await flush();
  p.value.state.hp = 0;
  p.value.state.total_damage = p.value.state.max_hp;
  p.value.state.status = "victory";
  p.value.state.version++;
  await p.advance(5000);
  assert.equal(
    p.w.document.querySelector("#bossHealthBar").value,
    p.value.state.max_hp,
  );
  p.value.state.hp = p.value.state.max_hp;
  p.value.state.total_damage = 0;
  p.value.state.status = "waiting";
  p.value.state.version++;
  await p.advance(5000);
  assert.equal(
    p.w.document.querySelector("#bossHealthBar").value,
    p.value.state.max_hp,
  );
  p.value.state.raid_id = "new-host-started-raid";
  p.value.state.server_time += 10;
  await p.advance(5000);
  assert.equal(p.w.document.querySelector("#bossHealthBar").value, 0);
  p.close();
});

test("explicit host health revisions update the current raid without losing damage", async () => {
  const p = page();
  await flush();
  p.value.state.hp -= 150;
  p.value.state.total_damage = 150;
  p.value.state.total_attacks = 1;
  p.value.state.version++;
  await p.advance(5000);
  const old = structuredClone(p.value);
  p.value.state.max_hp += 500000;
  p.value.state.hp += 500000;
  p.value.state.version++;
  p.value.state.health_revision = 1;
  await p.advance(5000);
  const bar = p.w.document.querySelector("#bossHealthBar");
  assert.equal(bar.value, p.value.state.max_hp - p.value.state.hp);
  assert.equal(bar.max, p.value.state.max_hp);
  assert.equal(p.w.document.querySelector("#bossDamage").textContent, "150");
  const saved = bar.value;
  old.state.server_time += 100;
  old.state.version += 100;
  p.respond(async () => response(old));
  await p.advance(5000);
  assert.equal(bar.value, saved);
  p.close();
});

test("avatar polls refresh the arena and admin preview while preserving host drafts", async () => {
  for (const name of ["play", "boss"]) {
    const p = page(name);
    await flush();
    const doc = p.w.document;
    if (name === "boss") {
      doc.querySelector("#bossMaxHealth").value = "5000000";
      doc.querySelector('[name="confirm_health"]').checked = true;
    }
    const url = "/play/avatar/" + "a".repeat(64) + ".png";
    p.value.state.avatar_url = url;
    p.value.state.avatar_custom = true;
    p.value.state.version++;
    await p.advance(5000);
    assert.equal(
      doc.querySelector("[data-boss-avatar]").getAttribute("src"),
      url,
    );
    assert.equal(
      doc
        .querySelector("[data-boss-avatar]")
        .classList.contains("custom-avatar"),
      true,
    );
    if (name === "boss") {
      assert.equal(doc.querySelector("#bossMaxHealth").value, "5000000");
      assert.equal(doc.querySelector('[name="confirm_health"]').checked, true);
      assert.equal(doc.querySelector('[name="health_revision"]').value, "0");
    }
    p.close();
  }
});

test("a revived raid refreshes its contributor recap on the next victory", async () => {
  const p = page();
  await flush();
  let recaps = 0;
  p.respond(async (url) => {
    if (url.startsWith("/play/api/contributors")) {
      recaps++;
      return response({
        raid_id: p.value.state.raid_id,
        health_revision: p.value.state.health_revision || 0,
        contributors: [
          {
            name: "Raider " + recaps,
            attacks: recaps,
            damage: p.value.state.total_damage,
          },
        ],
      });
    }
    return response(p.value);
  });
  const s = p.value.state;
  s.hp = 0;
  s.total_damage = s.max_hp;
  s.status = "victory";
  s.version++;
  await p.advance(5000);
  assert.equal(recaps, 1);
  assert.match(
    p.w.document.querySelector("#allContributors").textContent,
    /Raider 1/,
  );
  s.max_hp += 500;
  s.hp = 500;
  s.health_revision = 1;
  s.status = "active";
  s.version++;
  await p.advance(5000);
  assert.equal(p.w.document.querySelector("#victoryRecap").hidden, true);
  s.hp = 0;
  s.total_damage += 500;
  s.status = "victory";
  s.version++;
  await p.advance(5000);
  assert.equal(recaps, 2);
  assert.match(
    p.w.document.querySelector("#allContributors").textContent,
    /Raider 2/,
  );
  p.close();
});

test("boss name and damage updates use text and preserve admin settings drafts", async () => {
  for (const name of ["play", "boss"]) {
    const p = page(name);
    await flush();
    const doc = p.w.document;
    if (name === "boss") {
      doc.querySelector("#bossNameInput").value = "Unsaved boss";
      doc.querySelector("#bossBaseDamage").value = "200";
    }
    p.value.state.name = "<img src=x onerror=alert(1)>";
    p.value.state.rules.damage = 120;
    p.value.state.rules.weak_damage = 180;
    p.value.state.rules.burst_bonus = 80;
    p.value.state.settings_revision = 1;
    p.value.state.version++;
    await p.advance(5000);
    assert.equal(
      doc.querySelector("#bossName").textContent,
      p.value.state.name,
    );
    assert.equal(doc.querySelector("#bossName img"), null);
    if (name === "play") {
      assert.match(
        doc.querySelector("#bossWeakness").textContent,
        /180 damage/,
      );
      assert.match(doc.querySelector("#burstLabel").textContent, /80 damage/);
      assert.equal(doc.querySelector(".boss-sprite").alt, p.value.state.name);
      assert.equal(doc.querySelector("#bossNameInput"), null);
      assert.equal(doc.querySelector("#bossAvatarFile"), null);
    } else {
      assert.equal(doc.querySelector("#bossNameInput").value, "Unsaved boss");
      assert.equal(doc.querySelector("#bossBaseDamage").value, "200");
      assert.equal(doc.querySelector('[name="settings_revision"]').value, "0");
    }
    p.close();
  }
});

test("stationary clicks and the other attack button cannot bypass the pointer latch", async () => {
  const p = page();
  await flush();
  const doc = p.w.document,
    attack = doc.querySelector("#attackButton"),
    dock = doc.querySelector("#dockAttack");
  let hits = 0;
  p.respond(async (url, options) => {
    if (options.method === "POST") {
      const body = JSON.parse(options.body),
        s = p.value.state;
      hits++;
      s.version++;
      s.total_attacks++;
      s.you.attacks++;
      s.total_damage += 100;
      s.hp -= 100;
      s.you.ready_at = s.server_time + 30;
      s.you.last_request = body.request_id;
      s.you.last_hit = {
        damage: 100,
        style: body.style,
        weakness: false,
        burst: false,
      };
      return response({ ok: true, state: s, hit: s.you.last_hit });
    }
    return response(p.value);
  });
  attack.click();
  await flush();
  p.value.state.server_time += 30;
  await p.advance(5000);
  assert.equal(attack.disabled, true);
  attack.click();
  dock.click();
  await flush();
  assert.equal(hits, 1);
  assert.match(doc.querySelector("#rearmHint").textContent, /off/);
  // Moving outside is detected even when a native disabled button suppresses leave events.
  attack.getBoundingClientRect = () => ({
    left: 10,
    right: 110,
    top: 10,
    bottom: 60,
  });
  doc.dispatchEvent(
    new p.w.MouseEvent("pointermove", { clientX: 120, clientY: 20 }),
  );
  assert.equal(attack.disabled, false);
  attack.click();
  await flush();
  assert.equal(hits, 2);
  assert.equal(doc.querySelector("#yourAttacks").textContent, "2");
  p.close();
});

test("keyboard release re-arms attacks and a held activation key cannot repeat", async () => {
  const p = page();
  await flush();
  const doc = p.w.document,
    attack = doc.querySelector("#attackButton");
  attack.dispatchEvent(
    new p.w.KeyboardEvent("keydown", { key: "Enter", bubbles: true }),
  );
  attack.click();
  await flush();
  assert.equal(attack.disabled, true);
  const repeat = new p.w.KeyboardEvent("keydown", {
    key: "Enter",
    repeat: true,
    cancelable: true,
  });
  attack.dispatchEvent(repeat);
  assert.equal(repeat.defaultPrevented, true);
  doc.dispatchEvent(
    new p.w.KeyboardEvent("keyup", { key: "Enter", bubbles: true }),
  );
  assert.equal(attack.disabled, false);
  // Space normally dispatches click after keyup: it must not remain locked.
  attack.dispatchEvent(
    new p.w.KeyboardEvent("keydown", { key: " ", bubbles: true }),
  );
  doc.dispatchEvent(
    new p.w.KeyboardEvent("keyup", { key: " ", bubbles: true }),
  );
  attack.click();
  await flush();
  assert.equal(attack.disabled, false);
  p.close();
});

test("touch taps remain usable after their release", async () => {
  const p = page();
  await flush();
  const attack = p.w.document.querySelector("#attackButton");
  const touch = new p.w.Event("pointerdown");
  Object.defineProperty(touch, "pointerType", { value: "touch" });
  attack.dispatchEvent(touch);
  attack.click();
  await flush();
  assert.equal(attack.disabled, false); // fake server returns no cooldown in this gesture-only test
  p.close();
});

test("private admin feed uses admin authentication and removes names on expiry", async () => {
  const p = page("boss");
  await flush();
  assert.equal(p.calls[0].url, "/admin/boss/status");
  p.value.state.admin_leaders = [
    {
      name: "<img src=x onerror=alert(1)>",
      alias: "Raider ABCD1234",
      damage: 500,
      attacks: 5,
      name_provided: true,
    },
  ];
  p.value.state.version++;
  await p.advance(5000);
  const list = p.w.document.querySelector("#adminBossLeaders");
  assert.match(list.textContent, /<img/);
  assert.equal(list.querySelector("img"), null);
  p.respond(async () => response({ error: "Session expired" }, 401));
  await p.advance(5000);
  assert.doesNotMatch(list.textContent, /<img/);
  assert.match(list.textContent, /Sign in/);
  const count = p.calls.length;
  await p.advance(60000);
  assert.equal(p.calls.length, count);
  assert.equal(p.w.document.querySelector("#bossNameInput").disabled, true);
  p.close();
});

test("name save preserves typed drafts, unlocks play, and never sends an automatic attack", async () => {
  const p = page();
  await flush();
  const doc = p.w.document,
    input = doc.querySelector("#playerUsername");
  p.value.state.you.identity_ready = false;
  p.value.state.version++;
  await p.advance(5000);
  assert.equal(doc.querySelector("#attackButton").disabled, true);
  input.value = "My full name";
  input.dispatchEvent(new p.w.Event("input"));
  await p.advance(5000);
  assert.equal(input.value, "My full name");
  p.respond(async (url, options) => {
    if (url === "/play/api/profile") {
      assert.equal(JSON.parse(options.body).username, "My full name");
      p.value.state.you.display_name = "My full name";
      p.value.state.you.identity_ready = true;
      p.value.state.version++;
    }
    return response(p.value);
  });
  doc
    .querySelector("#playerNameForm")
    .dispatchEvent(new p.w.Event("submit", { cancelable: true }));
  await flush();
  assert.equal(doc.querySelector("#attackButton").disabled, false);
  assert.match(doc.querySelector("#playerNameResult").textContent, /Saved/);
  assert.equal(p.calls.filter((c) => c.url === "/play/api/attack").length, 0);
  assert.equal(doc.querySelectorAll("#yourBadges li").length, 8);
  assert.match(
    doc.querySelector("#bossPercent").textContent,
    /^0.00% defeated$/,
  );
  p.close();
});

test("saved name collapses into an editable identity without disturbing play", async () => {
  const p = page();
  await flush();
  const doc = p.w.document;
  assert.equal(doc.querySelector("#playerNameForm").hidden, true);
  assert.match(doc.querySelector("#playingAs").textContent, /FixtureRaider/);
  doc.querySelector("#editPlayerName").click();
  assert.equal(doc.querySelector("#playerNameForm").hidden, false);
  assert.equal(doc.activeElement.id, "playerUsername");
  await p.advance(5000);
  assert.equal(doc.querySelector("#playerNameForm").hidden, false);
  assert.equal(doc.querySelector("#attackButton").disabled, false);
  p.close();
});

test("style choice persists while weakness changes independently", async () => {
  const p = page("play", "magic");
  await flush();
  const doc = p.w.document;
  assert.equal(
    doc.querySelector('[data-style="magic"]').getAttribute("aria-pressed"),
    "true",
  );
  assert.equal(doc.querySelector("#dockStyle").value, "magic");
  doc.querySelector('[data-style="bow"]').click();
  assert.equal(p.w.localStorage.getItem("rh.boss.style"), "bow");
  p.value.state.weakness = "blade";
  p.value.state.version++;
  await p.advance(5000);
  assert.equal(
    doc.querySelector('[data-style="bow"]').getAttribute("aria-pressed"),
    "true",
  );
  p.close();
});

test("recovery code is created only by an explicit owner action", async () => {
  const p = page();
  await flush();
  const doc = p.w.document;
  assert.equal(
    p.calls.filter((c) => c.url.includes("recovery-code")).length,
    0,
  );
  p.respond(async (url, options) => {
    if (url.endsWith("recovery-code")) {
      assert.equal(options.method, "POST");
      assert.ok(options.headers["X-CSRF-Token"]);
      p.value.state.you.recovery_saved = true;
      p.value.state.version++;
      return response({ ...p.value, code: "private-fixture-code" });
    }
    return response(p.value);
  });
  doc.querySelector("#makeRecoveryCode").click();
  await flush();
  assert.equal(doc.querySelector("#recoveryCodeBox").hidden, false);
  assert.equal(
    doc.querySelector("#recoveryCode").value,
    "private-fixture-code",
  );
  assert.equal(p.w.localStorage.getItem("private-fixture-code"), null);
  assert.equal(p.calls.filter((c) => c.url.endsWith("/attack")).length, 0);
  p.close();
});

test("recovery posts a private code and restores the owner view", async () => {
  const p = page();
  await flush();
  const doc = p.w.document;
  p.respond(async (url, options) => {
    if (url.endsWith("/recover")) {
      assert.equal(JSON.parse(options.body).code, "fixture-secret");
      p.value.state.you.display_name = "Restored raider";
      p.value.state.version++;
    }
    return response(p.value);
  });
  doc.querySelector("#recoveryInput").value = "fixture-secret";
  doc
    .querySelector("#recoverPlayerForm")
    .dispatchEvent(new p.w.Event("submit", { cancelable: true }));
  await flush();
  assert.equal(doc.querySelector("#playingAs").textContent, "Restored raider");
  assert.equal(doc.querySelector("#recoveryInput").value, "");
  assert.match(
    doc.querySelector("#recoveryResult").textContent,
    /Player restored/,
  );
  p.close();
});

test("rally lights the arena without sending an attack or changing damage", async () => {
  const p = page();
  await flush();
  const doc = p.w.document;
  p.value.state.rally = { goal: 15, count: 15, unlocked: true };
  p.value.state.version++;
  const damage = p.value.state.rules.damage;
  await p.advance(5000);
  assert.ok(doc.querySelector("#bossStage").classList.contains("rally-lit"));
  assert.match(doc.querySelector("#rallyTitle").textContent, /Arena lit/);
  assert.equal(p.value.state.rules.damage, damage);
  assert.equal(p.calls.filter((c) => c.options.method === "POST").length, 0);
  p.close();
});

test("host previews are exact and presets never submit a new raid", async () => {
  const p = page("boss");
  await flush();
  const doc = p.w.document;
  doc.querySelector("#bossMaxHealth").value = "1";
  doc.querySelector("#bossMaxHealth").dispatchEvent(new p.w.Event("input"));
  assert.match(doc.querySelector("#maxHealthPreview").textContent, /→ 1/);
  doc.querySelector("#bossBaseDamage").value = "9007199254740991";
  doc.querySelector("#bossBurstBonus").value = "9007199254740991";
  doc.querySelector("#bossBaseDamage").dispatchEvent(new p.w.Event("input"));
  assert.match(
    doc.querySelector("#damagePreview").textContent,
    /18,014,398,509,481,982/,
  );
  doc.querySelector("#raidPresets button").click();
  assert.equal(doc.querySelector("#bossHealthInput").value, "10000000");
  assert.equal(p.calls.filter((c) => c.options.method === "POST").length, 0);
  p.close();
});

test("private history uses text and is cleared when the admin session expires", async () => {
  const p = page("boss");
  await flush();
  const doc = p.w.document;
  p.value.state.admin_history = [
    {
      action: "Boss settings",
      actor: "Host",
      at: 1800000000,
      before: { name: "Old" },
      after: { name: "<img src=x>" },
    },
  ];
  p.value.state.version++;
  await p.advance(5000);
  assert.match(
    doc.querySelector("#bossAdminHistory").textContent,
    /<img src=x>/,
  );
  assert.equal(doc.querySelector("#bossAdminHistory img"), null);
  p.respond(async () => response({ error: "Expired" }, 401));
  await p.advance(5000);
  assert.doesNotMatch(
    doc.querySelector("#bossAdminHistory").textContent,
    /<img src=x>/,
  );
  assert.match(doc.querySelector("#bossAdminHistory").textContent, /Sign in/);
  p.close();
});

test("last checked ages between polls and exact totals remain available", async () => {
  const p = page();
  await flush();
  const doc = p.w.document;
  await p.advance(2000);
  assert.match(
    doc.querySelector("#bossConnection").textContent,
    /Last checked 2s ago/,
  );
  assert.match(doc.querySelector("#bossHealth").textContent, /2.4M/);
  assert.match(doc.querySelector("#exactRaidTotals").textContent, /2,400,000/);
  p.close();
});

test("a committed username revision wins over an older request timestamp", async () => {
  const p = page();
  await flush();
  const doc = p.w.document;
  doc.querySelector("#editPlayerName").click();
  doc.querySelector("#playerUsername").value = "SavedWithoutReset";
  doc.querySelector("#playerUsername").dispatchEvent(new p.w.Event("input"));
  p.respond(async (url) => {
    if (url.endsWith("/profile")) {
      p.value.state.version++;
      p.value.state.server_time -= 1;
      p.value.state.you.display_name = "SavedWithoutReset";
      p.value.state.you.identity_ready = true;
    }
    return response(p.value);
  });
  doc
    .querySelector("#playerNameForm")
    .dispatchEvent(new p.w.Event("submit", { cancelable: true }));
  await flush();
  assert.equal(
    doc.querySelector("#playingAs").textContent,
    "SavedWithoutReset",
  );
  assert.equal(doc.querySelector("#playerNameForm").hidden, true);
  assert.equal(doc.querySelector("#attackButton").disabled, false);
  p.close();
});

test("a delayed pre-save poll cannot replace the confirmed player name", async () => {
  const p = page();
  await flush();
  const doc = p.w.document;
  const old = structuredClone(p.value);
  let release;
  p.respond(async (url) => {
    if (url.endsWith("/profile")) {
      p.value.state.version++;
      p.value.state.you.display_name = "LatestName";
      return response(p.value);
    }
    return new Promise((resolve) => {
      release = () => resolve(response(old));
    });
  });
  await p.advance(5000);
  assert.equal(typeof release, "function");
  doc.querySelector("#editPlayerName").click();
  doc.querySelector("#playerUsername").value = "LatestName";
  doc
    .querySelector("#playerNameForm")
    .dispatchEvent(new p.w.Event("submit", { cancelable: true }));
  await flush();
  release();
  await flush();
  assert.equal(doc.querySelector("#playingAs").textContent, "LatestName");
  assert.equal(doc.querySelector("#playerNameForm").hidden, true);
  p.close();
});

test("player writes briefly disable attacks without clearing a saved identity", async () => {
  const p = page();
  await flush();
  const doc = p.w.document;
  let finish;
  p.respond(
    async () =>
      new Promise((resolve) => {
        finish = () => resolve(response(p.value));
      }),
  );
  doc.querySelector("#makeRecoveryCode").click();
  await flush();
  assert.equal(doc.querySelector("#attackButton").disabled, true);
  assert.match(doc.querySelector("#playingAs").textContent, /FixtureRaider/);
  finish();
  await flush();
  assert.equal(doc.querySelector("#attackButton").disabled, false);
  p.close();
});
