/* Real browser checks for the shared experience. Uses disposable local data. */
const { chromium } = require("playwright");
const { spawn } = require("node:child_process");
const assert = require("node:assert/strict"),
  path = require("node:path"),
  fs = require("node:fs");
const dir = process.env.RH_SCREENSHOTS || require("node:os").tmpdir();
fs.mkdirSync(dir, { recursive: true });
(async () => {
  const server = spawn(process.env.RH_TEST_PYTHON || "python3", [
    path.join(__dirname, "serve_gui_fixture.py"),
  ]);
  let out = "",
    browser;
  server.stdout.on("data", (chunk) => (out += chunk));
  server.stderr.on("data", (chunk) => process.stderr.write(chunk));
  try {
    for (let n = 0; n < 100 && !out.includes("\n"); n++)
      await new Promise((r) => setTimeout(r, 50));
    const base = "http://127.0.0.1:" + JSON.parse(out.split("\n")[0]).port;
    browser = await chromium.launch({
      executablePath: process.env.RH_CHROMIUM || undefined,
      headless: true,
      args: ["--no-sandbox", "--disable-dev-shm-usage", "--disable-gpu"],
    });
    const ctx = await browser.newContext({
      viewport: { width: 390, height: 844 },
      reducedMotion: "reduce",
      permissions: ["clipboard-read", "clipboard-write"],
    });
    const page = await ctx.newPage(),
      errors = [];
    page.on("pageerror", (error) => errors.push(error.message));
    page.setDefaultTimeout(12000);
    await page.goto(base + "/");
    for (const name of [
      "Leaderboard",
      "History",
      "Boss fight",
      "Gaming",
      "Points Shop",
      "Red Community",
      "Watch on Kick",
    ])
      assert.equal(
        await page
          .locator(".site-header a")
          .filter({ hasText: name })
          .isVisible(),
        true,
        name,
      );
    const first = await page.locator("#leaderboard").boundingBox(),
      boss = await page.locator(".play-invite").boundingBox();
    assert.ok(boss.y < first.y, "Community boss above standings");
    for (const width of [320, 390, 768, 1440]) {
      await page.setViewportSize({ width, height: 900 });
      await page.goto(base + "/");
      assert.equal(
        await page.evaluate(
          () => document.documentElement.scrollWidth <= innerWidth,
        ),
        true,
        "home " + width,
      );
    }
    await page.setViewportSize({ width: 390, height: 844 });
    await page.goto(base + "/gaming/coinflip");
    await page.locator("#gamingUsername").fill("Experience Player");
    await page.locator("#gamingNameForm button").click();
    await page.locator("#gamingIdentity").waitFor();
    for (let n = 0; n < 7; n++) {
      await page.locator("#betButton").click();
      await page.locator("#betProof").filter({ hasText: "Verified" }).waitFor();
      await page.waitForFunction(
        () => !document.querySelector("#betButton").disabled,
      );
    }
    await page.goto(base + "/gaming");
    assert.equal(await page.locator("#betHistory tr:visible").count(), 5);
    await page.locator("#historyToggle").click();
    assert.equal(await page.locator("#betHistory tr:visible").count(), 7);
    await page.locator("#betHistory button").first().focus();
    await page.waitForTimeout(5300);
    assert.equal(
      await page.evaluate(
        () =>
          document.activeElement?.dataset.receipt ===
          document.querySelector("#betHistory button").dataset.receipt,
      ),
      true,
      "poll retains receipt focus",
    );
    await page.locator("#gameSelect").selectOption("/gaming/poker");
    await page.waitForURL("**/gaming/poker");
    await page.locator("#betButton").click();
    await page.locator("#holdemControls").waitFor();
    await page.waitForFunction(
      () => !document.querySelector("#holdemRaise").disabled,
    );
    await page.locator("#holdemRaise").fill("80");
    await page.waitForTimeout(5300);
    assert.equal(
      await page.locator("#holdemRaise").inputValue(),
      "80",
      "poll retains raise draft",
    );
    assert.equal(await page.locator("#pointsInPlay").textContent(), "1,000");
    assert.equal(await page.locator("#betForm").isHidden(), true);
    await page.evaluate(() => {
      document.activeElement?.blur();
      scrollTo({ top: 0, behavior: "instant" });
    });
    await page.screenshot({
      path: path.join(dir, "polish-holdem-mobile.png"),
      fullPage: true,
    });
    await page.goto(base + "/admin");
    await page.locator("#username").fill("gingrsnaps");
    await page.locator("#password").fill("visual-fixture-password");
    await page.locator("form button[type=submit]").click();
    await page.locator("#gamingAdmin").waitFor();
    assert.equal(
      await page.locator("#diagnostics").evaluate((node) => node.open),
      false,
    );
    await page.locator('a[href="#diagnostics"]').click();
    await page.locator("#systemHealth").waitFor();
    assert.equal(await page.locator("[data-health-card]").count(), 5);
    await page.locator("#copyHealthReport").click();
    await page
      .locator("#healthReportFeedback")
      .filter({ hasText: "copied" })
      .waitFor();
    const report = JSON.parse(
      await page.evaluate(() => navigator.clipboard.readText()),
    );
    assert.equal(report.ready, true);
    assert.ok(!JSON.stringify(report).includes("Experience Player"));
    await page.setViewportSize({ width: 1440, height: 1000 });
    await page.evaluate(() => scrollTo({ top: 0, behavior: "instant" }));
    await page.screenshot({
      path: path.join(dir, "polish-admin-desktop.png"),
      fullPage: true,
    });
    await page.setViewportSize({ width: 390, height: 844 });
    assert.equal(
      await page.evaluate(
        () => document.documentElement.scrollWidth <= innerWidth,
      ),
      true,
      "admin mobile",
    );
    await page.screenshot({
      path: path.join(dir, "polish-admin-mobile.png"),
      fullPage: true,
    });
    // Capture laboratory loading data, not a claim about real-user p75 INP.
    const lab = await browser.newContext({
        viewport: { width: 390, height: 844 },
      }),
      sample = await lab.newPage(),
      cdp = await lab.newCDPSession(sample),
      measurements = [];
    await cdp.send("Network.enable");
    await cdp.send("Network.emulateNetworkConditions", {
      offline: false,
      latency: 150,
      downloadThroughput: 200000,
      uploadThroughput: 80000,
    });
    await cdp.send("Emulation.setCPUThrottlingRate", { rate: 4 });
    await sample.addInitScript(() => {
      globalThis.lab = { lcp_ms: 0, cls: 0 };
      new PerformanceObserver((list) => {
        for (const entry of list.getEntries()) lab.lcp_ms = entry.startTime;
      }).observe({ type: "largest-contentful-paint", buffered: true });
      new PerformanceObserver((list) => {
        for (const entry of list.getEntries())
          if (!entry.hadRecentInput) lab.cls += entry.value;
      }).observe({ type: "layout-shift", buffered: true });
    });
    for (const route of ["/", "/gaming", "/gaming/dice", "/play", "/history"]) {
      await cdp.send("Network.clearBrowserCache");
      await sample.goto(base + route);
      await sample.waitForTimeout(1400);
      const value = await sample.evaluate(() => ({
        ...lab,
        bytes: performance
          .getEntriesByType("resource")
          .reduce((total, item) => total + item.transferSize, 0),
      }));
      measurements.push({ route, ...value });
      assert.equal(
        await sample.evaluate(
          () => document.documentElement.scrollWidth <= innerWidth,
        ),
        true,
        route + " overflow",
      );
      if (route === "/" || route === "/play" || route === "/history")
        await sample.screenshot({
          path: path.join(
            dir,
            "polish-" +
              (route === "/" ? "home" : route.slice(1)) +
              "-mobile.png",
          ),
          fullPage: true,
        });
    }
    fs.writeFileSync(
      path.join(dir, "loading-measurements.json"),
      JSON.stringify(
        {
          environment:
            "Chromium, 390px, CPU 4x slowdown, 150ms latency, 200KB/s download; one cold sample per page",
          measurements,
        },
        null,
        2,
      ),
    );
    assert.deepEqual(errors, []);
    console.log(
      JSON.stringify({
        mobile_header_complete: true,
        boss_first: true,
        history_preview_and_focus: true,
        pending_raise_preserved: true,
        private_health_report: true,
        overflow: false,
        page_errors: errors,
        lab: measurements,
      }),
    );
    await ctx.close();
    await lab.close();
  } finally {
    if (browser) await browser.close();
    server.kill("SIGTERM");
  }
})().catch((error) => {
  console.error(error);
  process.exitCode = 1;
});
