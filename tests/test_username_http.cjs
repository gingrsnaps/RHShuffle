/* Real page + both shipped scripts + HTTP + cookie jar. No mocked save API. */
const { test } = require("node:test");
const assert = require("node:assert/strict");
const path = require("node:path");
const { spawn } = require("node:child_process");
const { once } = require("node:events");
const { JSDOM, CookieJar, VirtualConsole } = require("jsdom");

async function until(check, description) {
  const deadline = Date.now() + 7000;
  while (Date.now() < deadline) {
    if (await check()) return;
    await new Promise((resolve) => setTimeout(resolve, 20));
  }
  throw new Error("Timed out: " + description);
}

test("username saves through the actual website and persists with real cookies", async (t) => {
  const python = process.env.RH_TEST_PYTHON || "python";
  const server = spawn(
    python,
    [path.join(__dirname, "serve_game_fixture.py")],
    {
      stdio: ["ignore", "pipe", "pipe"],
    },
  );
  let output = "",
    errors = "",
    processError;
  const windows = new Set();
  let pendingRequests = 0;
  async function close(dom) {
    if (!windows.has(dom)) return;
    Object.defineProperty(dom.window.document, "hidden", {
      value: true,
      configurable: true,
    });
    dom.window.document.dispatchEvent(new dom.window.Event("visibilitychange"));
    await until(
      () => pendingRequests === 0,
      "HTTP requests finish before tab close",
    );
    for (let i = 0; i < 4; i++)
      await new Promise((resolve) => setImmediate(resolve));
    dom.window.close();
    windows.delete(dom);
  }
  server.stdout.on("data", (chunk) => (output += chunk));
  server.stderr.on("data", (chunk) => (errors += chunk));
  server.on("error", (error) => (processError = error));
  t.after(async () => {
    for (const dom of windows) await close(dom);
    if (server.exitCode === null && !processError) {
      const stopped = once(server, "exit");
      server.kill();
      await stopped;
    }
  });
  await until(() => {
    if (processError) throw processError;
    if (server.exitCode !== null) throw new Error(errors);
    return output.includes("\n");
  }, "fixture starts");
  const base = "http://127.0.0.1:" + JSON.parse(output.split("\n")[0]).port;

  async function transport(jar, url, options = {}) {
    const target = new URL(url, base).href;
    const headers = new Headers(options.headers);
    const cookie = jar.getCookieStringSync(target);
    if (cookie) headers.set("Cookie", cookie);
    pendingRequests++;
    try {
      const response = await fetch(target, {
        ...options,
        headers,
        redirect: "manual",
      });
      for (const cookie of response.headers.getSetCookie())
        jar.setCookieSync(cookie, target);
      await response.clone().arrayBuffer();
      return response;
    } finally {
      pendingRequests--;
    }
  }
  async function page(jar, scripts = true) {
    const faults = [];
    const console = new VirtualConsole();
    console.on("jsdomError", (error) => faults.push(error.message));
    const dom = await JSDOM.fromURL(base + "/play", {
      cookieJar: jar,
      runScripts: scripts ? "dangerously" : "outside-only",
      resources: scripts ? "usable" : undefined,
      pretendToBeVisual: true,
      virtualConsole: console,
      beforeParse(window) {
        // Undici requires its own AbortSignal class; this is transport glue,
        // not a substitute for the real script, request, cookie jar or server.
        window.AbortController = globalThis.AbortController;
        window.AbortSignal = globalThis.AbortSignal;
        window.fetch = (url, options) => transport(jar, url, options);
      },
    });
    windows.add(dom);
    if (scripts) {
      await until(
        () =>
          dom.window.document
            .querySelector("#bossConnection")
            .textContent.startsWith("Live"),
        "game scripts start",
      );
      assert.deepEqual(faults, []);
    }
    return { dom, w: dom.window, doc: dom.window.document, faults };
  }
  async function save(p, name) {
    const input = p.doc.querySelector("#playerUsername");
    input.value = name;
    input.dispatchEvent(new p.w.Event("input", { bubbles: true }));
    p.doc.querySelector("#playerNameForm button[type=submit]").click();
    try {
      await until(
        () => p.doc.querySelector("#playerIdentity").hidden === false,
        "saved player appears",
      );
    } catch (error) {
      throw new Error(
        error.message +
          ": " +
          JSON.stringify({
            result: p.doc.querySelector("#playerNameResult").textContent,
            game: p.doc.querySelector("#bossError").textContent,
            input: input.value,
            faults: p.faults,
            server: errors,
          }),
      );
    }
    assert.equal(p.doc.querySelector("#playingAs").textContent, name);
    assert.equal(p.doc.querySelector("#playerNameForm").hidden, true);
    assert.match(p.doc.querySelector("#playerNameResult").textContent, /Saved/);
    assert.equal(p.doc.querySelector("#attackButton").disabled, false);
    assert.deepEqual(p.faults, []);
  }

  const jar = new CookieJar();
  const first = await page(jar);
  // The old release rejects this Save even though the year-long player cookie
  // is valid. Keep the page open while the independent session is removed.
  jar.setCookieSync("session=; Max-Age=0; Path=/", base);
  await save(first, "HTTP Raider");
  const state = await (await transport(jar, "/play/api/state")).json();
  assert.equal(state.state.you.display_name, "HTTP Raider");
  assert.equal(state.player_cookie_ready, true);
  await close(first.dom);
  const reload = await page(jar);
  assert.equal(
    reload.doc.querySelector("#playingAs").textContent,
    "HTTP Raider",
  );
  assert.equal(reload.doc.querySelector("#playerNameForm").hidden, true);
  assert.equal(reload.doc.querySelector("#attackButton").disabled, false);
  reload.doc.querySelector("#attackButton").click();
  await until(
    () => reload.doc.querySelector("#yourAttacks").textContent === "1",
    "saved player can attack",
  );
  const afterHit = await (await transport(jar, "/play/api/state")).json();
  assert.equal(afterHit.state.you.display_name, "HTTP Raider");
  assert.equal(afterHit.state.you.attacks, 1);
  assert.equal(afterHit.state.you.can_attack, false);

  // Same display label, same HTTP peer, independent identity and progress.
  const otherJar = new CookieJar();
  const other = await page(otherJar);
  await save(other, "HTTP Raider");
  const otherState = await (
    await transport(otherJar, "/play/api/state")
  ).json();
  assert.notEqual(otherState.state.you.name, state.state.you.name);
  assert.equal(otherState.state.you.damage, 0);

  // Exercise the literal native form with no JS at all, including the redirect.
  const nativeJar = new CookieJar();
  const native = await page(nativeJar, false);
  const form = native.doc.querySelector("#playerNameForm");
  assert.equal(form.method, "post");
  form.elements.namedItem("username").value = "Native HTTP Raider";
  const fields = new URLSearchParams(new native.w.FormData(form));
  nativeJar.setCookieSync("session=; Max-Age=0; Path=/", base);
  const response = await transport(nativeJar, form.action, {
    method: "POST",
    headers: { "Content-Type": "application/x-www-form-urlencoded" },
    body: fields.toString(),
  });
  assert.equal(response.status, 303);
  const confirmed = await page(nativeJar, false);
  assert.equal(
    confirmed.doc.querySelector("#playingAs").textContent,
    "Native HTTP Raider",
  );
  assert.equal(confirmed.doc.querySelector("#playerIdentity").hidden, false);
  assert.equal(confirmed.doc.querySelector("#playerNameForm").hidden, true);
});
