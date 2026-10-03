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
          .filter({ hasText: percent.toFixed(2) + "% defeated" })
          .waitFor();
        assert.equal(
          await page.locator("#inviteHealth").evaluate((el) => el.value),
          percent,
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
        assert.ok(
          geometry.leaderboard < height,
          "Leaderboard heading must be visible on first screen",
        );
        if (size === "mobile")
          assert.ok(
            geometry.nav.every((h) => h >= 44),
            "Mobile navigation tap targets",
          );
        const bar = await page.locator('#inviteHealth').boundingBox();
        measurements.push({file:`home-${size}-${percent}.png`,bar,percent});
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
    assert.deepEqual(errors, []);
    fs.writeFileSync(path.join(output,'progress-measurements.json'),JSON.stringify(measurements));
    const pixels = spawnSync(process.env.RH_TEST_PYTHON || 'python',[path.join(__dirname,'assert_visual_pixels.py'),output],{encoding:'utf8'});
    assert.equal(pixels.status,0,pixels.stderr || pixels.stdout);
    console.log(
      JSON.stringify({
        passed: true,
        progress_states: [0, 25, 75, 100],
        viewports: [1440, 390, 320],
        screenshots: 11,
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
