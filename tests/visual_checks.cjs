/* Real Chromium layout checks + reproducible screenshots, using synthetic data.
   Optional developer check; neither Node nor Chromium is needed in production. */
const { chromium } = require("playwright");
const assert = require("node:assert/strict");
const path = require("node:path");
const fs = require("node:fs");
const { spawn, spawnSync } = require("node:child_process");
const { once } = require("node:events");
const output =
  process.env.RH_VISUAL_OUTPUT || path.join(__dirname, "..", ".visual-checks");
const flush = (ms) => new Promise((r) => setTimeout(r, ms));
(async () => {
  const server = spawn(
    process.env.RH_TEST_PYTHON || "python",
    [path.join(__dirname, "serve_gui_fixture.py")],
    { stdio: ["ignore", "pipe", "pipe"] },
  );
  let stdout = "",
    stderr = "",
    browser;
  server.stdout.on("data", (c) => (stdout += c));
  server.stderr.on("data", (c) => (stderr += c));
  try {
    for (let n = 0; n < 100 && !stdout.includes("\n"); n++) {
      if (server.exitCode !== null) throw Error(stderr);
      await flush(50);
    }
    const base = "http://127.0.0.1:" + JSON.parse(stdout.split("\n")[0]).port;
    browser = await chromium.launch({
      headless: true,
      executablePath: process.env.RH_BROWSER_EXECUTABLE || undefined,
      args: [
        "--no-sandbox",
        "--disable-dev-shm-usage",
        "--disable-gpu",
        "--disable-software-rasterizer",
      ],
    });
    fs.mkdirSync(output, { recursive: true });
    const context = await browser.newContext({ reducedMotion: "reduce" });
    await context.addInitScript(() => {
      Date.now = () => 1791028800000;
    });
    const page = await context.newPage();
    const errors = [];
    const measurements = [];
    page.on("pageerror", (e) => errors.push(e.message));
    for (const [size, width, height] of [
      ["desktop", 1440, 1000],
      ["mobile", 390, 844],
    ]) {
      await page.setViewportSize({ width, height });
      for (const percent of [0, 25, 75, 100]) {
        await context.request.post(base + "/__fixture__/progress/" + percent);
        await page.goto(base);
        await page
          .locator("#invitePercent")
          .filter({ hasText: (100 - percent).toFixed(2) + "% remaining" })
          .waitFor();
        assert.equal(
          await page
            .locator("#inviteHealth")
            .evaluate((el) => (el.value / el.max) * 100),
          100 - percent,
        );
        const geometry = await page.evaluate(() => ({
          width: document.documentElement.scrollWidth,
          viewport: innerWidth,
          leaderboard: document
            .querySelector("#leaderboard")
            .getBoundingClientRect().top,
          nav: [...document.querySelectorAll(".section-nav")].map(
            (x) => x.getBoundingClientRect().height,
          ),
        }));
        assert.ok(geometry.width <= width, "Homepage overflows " + size);
        const bossTop = await page.locator('#communityBoss').evaluate(node => node.getBoundingClientRect().top);
        assert.ok(bossTop < geometry.leaderboard, "Boss above standings");
        if (size === "mobile")
          assert.ok(
            geometry.nav.every((h) => h >= 44),
            "Mobile navigation tap targets",
          );
        for (const href of [
          "/#leaderboard",
          "/history",
          "/play",
          "/gaming",
          "https://botrix.live/k/redhunllef/shop",
          "https://example.test/community",
        ]) {
          assert.ok(
            await page.locator(`.site-header a[href="${href}"]`).isVisible(),
            `Missing navigation: ${href}`,
          );
        }
        const bar = await page.locator("#inviteHealth").boundingBox();
        measurements.push({
          file: `home-${size}-${percent}.png`,
          bar,
          percent,
        });
        await page.screenshot({
          path: path.join(output, `home-${size}-${percent}.png`),
          fullPage: true,
          animations: "disabled",
        });
      }
      await page.goto(base + "/history");
      await page.locator("#historyRows tr").nth(24).waitFor();
      assert.ok(
        await page.evaluate(
          () => document.documentElement.scrollWidth <= innerWidth,
        ),
        "History page overflows",
      );
      if (size === "mobile") {
        assert.equal(await page.locator("#historyWeeks").isVisible(), false);
        assert.equal(await page.locator(".history-picker").isVisible(), true);
        await page.locator("#historyPrevious").click();
        await page.waitForURL(/week=/);
        assert.equal(
          await page.locator("#historyNext").getAttribute("aria-disabled"),
          null,
        );
        const older = await page
          .locator("#historyWeekSelect option")
          .last()
          .getAttribute("value");
        await page.selectOption("#historyWeekSelect", older);
        await page.locator(".history-picker button").click();
        await page.waitForURL("**week=" + older);
        assert.equal(
          await page.locator("#historyPrevious").getAttribute("aria-disabled"),
          "true",
        );
      }
      await page.screenshot({
        path: path.join(output, `history-${size}.png`),
        fullPage: true,
        animations: "disabled",
      });
    }
    await page.setViewportSize({ width: 320, height: 860 });
    await page.goto(base);
    assert.ok(
      await page.evaluate(
        () => document.documentElement.scrollWidth <= innerWidth,
      ),
      "320px page overflows",
    );
    await page.setViewportSize({ width: 1440, height: 1000 });
    await page.goto(base + "/admin");
    await page.locator('input[name="username"]').fill("gingrsnaps");
    await page
      .locator('input[name="password"]')
      .fill("visual-fixture-password");
    await page.locator('button[type="submit"]').click();
    await page.waitForURL(/tab=|\/admin$/);
    await page.goto(base + "/admin?tab=boss");
    await page.locator("#bossNameInput").fill("Ruby Guardian");
    assert.equal(
      await page.locator("#bossPreviewName").textContent(),
      "Ruby Guardian",
    );
    await page
      .locator("#bossAvatarFile")
      .setInputFiles(path.join(__dirname, "..", "static", "redlogo.png"));
    await page.waitForFunction(() =>
      document.getElementById("bossPreviewAvatar").src.startsWith("data:"),
    );
    await page.locator("#bossBaseDamage").fill("234");
    await page.locator('#bossSettingsForm button[type="submit"]').click();
    await page.locator("#feedback-bossSettingsHeading").waitFor();
    assert.match(
      await page.locator("#feedback-bossSettingsHeading").textContent(),
      /base: 234/,
    );
    await page.locator("#bossNameInput").fill("Draft to preserve");
    const form = page.locator("#bossSettingsForm");
    await form
      .locator('input[name="settings_revision"]')
      .evaluate((el) => (el.value = -1));
    await form.locator('button[type="submit"]').click();
    await form.locator("[data-form-feedback].warning").waitFor();
    assert.equal(
      await page.locator("#bossNameInput").inputValue(),
      "Draft to preserve",
    );
    assert.match(
      await form.locator("[data-form-feedback]").textContent(),
      /Save boss settings:/,
    );
    await page.screenshot({
      path: path.join(output, "admin-boss-feedback.png"),
      fullPage: true,
      animations: "disabled",
    });
    const games = await context.newPage();
    games.on("pageerror", (error) => errors.push(error.message));
    await games.goto(base + "/gaming");
    await games.locator("#gamingUsername").fill("BrowserRedPlayer");
    await games.locator("#gamingNameForm button").click();
    await games.locator("#gamingIdentity").waitFor();
    assert.equal(
      await games.locator("#pointsBalance").textContent(),
      "100,000",
    );
    let balance = 100000,
      lastReceipt;
    for (const game of ["dice", "keno", "plinko"]) {
      await context.request.post(base + "/__fixture__/advance");
      await games.goto(base + "/gaming/" + game);
      await games.locator("#redWager").fill("125");
      if (game === "keno")
        for (const n of [1, 5, 15])
          await games.locator(`[data-keno="${n}"]`).click();
      const reply = games.waitForResponse(
        (r) =>
          r.url().endsWith("/gaming/api/bet") &&
          r.request().method() === "POST",
      );
      await games.locator("#betButton").click();
      const response = await reply;
      assert.equal(response.status(), 200);
      const value = await response.json();
      lastReceipt = value.receipt;
      balance += lastReceipt.net;
      await games
        .locator("#betProof")
        .filter({ hasText: "Verified in your browser" })
        .waitFor();
      assert.equal(
        await games.locator("#pointsBalance").textContent(),
        balance.toLocaleString("en-US"),
      );
      const repeat = await context.request.post(base + "/gaming/api/bet", {
        data: response.request().postDataJSON(),
        headers: {
          "X-CSRF-Token": await games
            .locator(".gaming-page")
            .getAttribute("data-csrf"),
        },
      });
      const duplicated = await repeat.json();
      assert.equal(duplicated.duplicate, true);
      assert.equal(duplicated.wallet.balance, balance);
      for (const [size, width, height] of [
        ["desktop", 1440, 1000],
        ["mobile", 390, 844],
      ]) {
        await games.setViewportSize({ width, height });
        assert.ok(
          await games.evaluate(
            () => document.documentElement.scrollWidth <= innerWidth,
          ),
          game + " overflows " + size,
        );
        if (game === "keno" && size === "mobile") {
          assert.ok(
            (await games.locator('[data-keno="1"]').boundingBox()).height >= 44,
          );
        }
        await games.evaluate(() => {
          scrollTo({ top: 0, behavior: "instant" });
          document.activeElement?.blur();
        });
        await games.screenshot({
          path: path.join(output, game + "-" + size + ".png"),
          fullPage: true,
          animations: "disabled",
        });
      }
      await games.reload();
      assert.equal(
        await games.locator("#pointsBalance").textContent(),
        balance.toLocaleString("en-US"),
      );
    }
    await games.goto(base + "/gaming");
    await games.screenshot({
      path: path.join(output, "gaming-mobile.png"),
      fullPage: true,
    });
    await games.setViewportSize({ width: 1440, height: 1000 });
    await games.screenshot({
      path: path.join(output, "gaming-desktop.png"),
      fullPage: true,
    });
    await games.goto(base + "/gaming/fairness");
    await games.locator("#verifyReceipt").fill(JSON.stringify(lastReceipt));
    await games.locator("#verifyCommitment").fill(lastReceipt.commitment);
    await games.locator("#receiptVerifier button").click();
    await games
      .locator("#verifyResult")
      .filter({ hasText: "Verified 1 receipt" })
      .waitFor();
    await games.goto(base + "/admin?tab=gaming");
    for (const game of ["dice", "keno", "plinko"])
      assert.match(
        await games.locator("#gamingLeaders-" + game).textContent(),
        /BrowserRedPlayer/,
      );
    await games.screenshot({
      path: path.join(output, "admin-gaming.png"),
      fullPage: true,
    });
    assert.deepEqual(errors, []);
    fs.writeFileSync(
      path.join(output, "progress-measurements.json"),
      JSON.stringify(measurements),
    );
    const pixels = spawnSync(
      process.env.RH_TEST_PYTHON || "python",
      [path.join(__dirname, "assert_visual_pixels.py"), output],
      { encoding: "utf8" },
    );
    assert.equal(pixels.status, 0, pixels.stderr || pixels.stdout);
    console.log(
      JSON.stringify({
        passed: true,
        progress_states: [0, 25, 75, 100],
        viewports: [1440, 390, 320],
        screenshots: 20,
        games_verified: ["dice", "keno", "plinko"],
        duplicate_wagers_preserved: true,
        admin_save_and_draft_preservation: true,
        output,
      }),
    );
  } finally {
    if (browser) await browser.close();
    if (server.exitCode === null) {
      const done = once(server, "exit");
      server.kill();
      await done;
    }
  }
})().catch((error) => {
  console.error(error);
  process.exitCode = 1;
});
