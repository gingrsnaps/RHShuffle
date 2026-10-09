/* Browser checks for task-specific edits, stable details, and the depleting bar. */
const { chromium } = require("playwright"),
  { spawn } = require("node:child_process");
const assert = require("node:assert/strict"),
  path = require("node:path"),
  fs = require("node:fs");
(async () => {
  const server = spawn(process.env.RH_TEST_PYTHON || "python3", [
    path.join(__dirname, "serve_gui_fixture.py"),
  ]);
  let out = "",
    browser;
  server.stdout.on("data", (c) => (out += c));
  server.stderr.on("data", (c) => process.stderr.write(c));
  const folder = process.env.RH_SCREENSHOTS || require("node:os").tmpdir();
  fs.mkdirSync(folder, { recursive: true });
  try {
    for (let n = 0; n < 100 && !out.includes("\n"); n++)
      await new Promise((r) => setTimeout(r, 50));
    const base = "http://127.0.0.1:" + JSON.parse(out.split("\n")[0]).port;
    browser = await chromium.launch({
      headless: true,
      executablePath: process.env.RH_CHROMIUM || undefined,
      args: ["--no-sandbox", "--disable-dev-shm-usage", "--disable-gpu"],
    });
    const ctx = await browser.newContext({
        viewport: { width: 1440, height: 1000 },
        reducedMotion: "reduce",
      }),
      page = await ctx.newPage(),
      errors = [];
    page.on("pageerror", (e) => errors.push(e.message));
    page.setDefaultTimeout(10000);
    for (const percent of [0, 25, 75, 100]) {
      await ctx.request.post(base + "/__fixture__/progress/" + percent);
      await page.goto(base + "/");
      assert.equal(
        await page
          .locator("#inviteHealth")
          .evaluate((n) => (100 * n.value) / n.max),
        100 - percent,
      );
      assert.equal(
        await page.locator("#invitePercent").textContent(),
        (100 - percent).toFixed(2) + "% remaining",
      );
    }
    await ctx.request.post(base + "/__fixture__/progress/25");
    await page.goto(base + "/");
    await page.evaluate(() => { document.activeElement?.blur(); scrollTo({top:0,behavior:"instant"}); });
    await page.screenshot({
      path: path.join(folder, "home-desktop.png"),
      fullPage: true,
    });
    await page.goto(base + "/play");
    await page.locator("#playerUsername").fill("Clarity Player");
    await page.locator("#playerNameForm button[type=submit]").first().click();
    await page.locator("#playerIdentity").waitFor();
    await page.locator("#attackButton").click();
    await page.locator("#hitResult").filter({ hasText: "hit for" }).waitFor();
    assert.match(
      await page.locator("#attackButton").textContent(),
      /Next attack/,
    );
    await page.reload();
    assert.equal(
      await page.locator("#playingAs").textContent(),
      "Clarity Player",
    );
    await page.goto(base + "/gaming");
    assert.equal(
      await page.locator("#gamingUsername").inputValue(),
      "Clarity Player",
    );
    await page.locator("#gamingNameForm button").click();
    await page.locator("#gamingIdentity").waitFor();
    assert.equal(
      await page.locator("#gamingPlayerName").textContent(),
      "Clarity Player",
    );
    await page
      .locator("#gamingIdentity a")
      .filter({ hasText: "Edit name" })
      .click();
    await page.locator("#playerNameForm").waitFor();
    await page.goto(base + "/admin");
    await page.locator("#username").fill("gingrsnaps");
    await page.locator("#password").fill("visual-fixture-password");
    await page.locator("form button[type=submit]").click();
    await page.locator("#gamingAdmin").waitFor();
    assert.equal(
      await page.locator("#diagnostics").evaluate((n) => n.open),
      false,
    );
    await page.evaluate(() => { document.activeElement?.blur(); scrollTo({top:0,behavior:"instant"}); });
    await page.screenshot({
      path: path.join(folder, "overview-desktop.png"),
      fullPage: true,
    });
    await page.goto(base + "/admin?tab=boss");
    await page.locator("#bossNameForm").waitFor();
    const before = (
      await (await ctx.request.get(base + "/admin/boss/status")).json()
    ).state;
    await page.locator("#bossNameInput").fill("Ruby Clarity");
    await page.locator("#bossNameForm button").click();
    await page.locator("#feedback-bossNameHeading").waitFor();
    let after = (
      await (await ctx.request.get(base + "/admin/boss/status")).json()
    ).state;
    assert.equal(after.name, "Ruby Clarity");
    assert.equal(after.hp, before.hp);
    assert.equal(after.rules.damage, before.rules.damage);
    await page.locator("#bossBaseDamage").fill("777");
    await page.locator("#bossSettingsForm button").click();
    await page.locator("#feedback-bossSettingsHeading").waitFor();
    after = (await (await ctx.request.get(base + "/admin/boss/status")).json())
      .state;
    assert.equal(after.rules.damage, 777);
    assert.equal(after.name, "Ruby Clarity");
    assert.equal(after.hp, before.hp);
    // A background state response must not overwrite an in-progress form.
    await page.locator("#bossBaseDamage").fill("888");
    await page.waitForTimeout(5300);
    assert.equal(await page.locator("#bossBaseDamage").inputValue(), "888");
    await page.locator("#bossBaseDamage").fill("777");
    await page.locator("#bossNameInput").fill("Preview only");
    await page.locator(".boss-home-preview summary").click();
    assert.equal(
      await page.locator("#bossPreviewName").textContent(),
      "Preview only",
    );
    assert.equal(
      (await (await ctx.request.get(base + "/admin/boss/status")).json()).state
        .name,
      "Ruby Clarity",
    );
    await page.locator("#bossNameInput").fill("Ruby Clarity");
    await page.evaluate(() => { document.activeElement?.blur(); scrollTo({top:0,behavior:"instant"}); });
    await page.screenshot({
      path: path.join(folder, "boss-controls-desktop.png"),
      fullPage: true,
    });
    for (const width of [320, 390]) {
      await page.setViewportSize({ width, height: 844 });
      for (const route of [
        "/admin?tab=boss",
        "/admin/gaming",
        "/admin",
        "/play",
      ]) {
        await page.goto(base + route);
        if (!await page.evaluate(() => document.documentElement.scrollWidth <= innerWidth)) {
          console.log(JSON.stringify(await page.evaluate(() => [...document.querySelectorAll('main *')].filter(n => n.getBoundingClientRect().right > innerWidth+1).map(n => ({tag:n.tagName,id:n.id,cls:n.className,right:n.getBoundingClientRect().right})).slice(0,24))));
          await page.evaluate(() => { document.activeElement?.blur(); scrollTo({top:0,behavior:"instant"}); });
    await page.screenshot({path:path.join(folder,'overflow.png'),fullPage:true});
        }
        assert.equal(
          await page.evaluate(
            () => document.documentElement.scrollWidth <= innerWidth,
          ),
          true,
          route + " " + width,
        );
      }
    }
    await page.goto(base + "/admin?tab=boss");
    await page.evaluate(() => { document.activeElement?.blur(); scrollTo({top:0,behavior:"instant"}); });
    await page.screenshot({
      path: path.join(folder, "boss-controls-mobile.png"),
      fullPage: true,
    });
    await page.goto(base + "/admin");
    await page.evaluate(() => { document.activeElement?.blur(); scrollTo({top:0,behavior:"instant"}); });
    await page.screenshot({
      path: path.join(folder, "overview-mobile.png"),
      fullPage: true,
    });
    await page.goto(base + "/admin/gaming#gamingFunding");
    assert.equal(
      await page.locator("#gamingFunding").evaluate((n) => n.open),
      true,
    );
    await page.locator("#grantGamingButton").click();
    await page
      .locator("#gamingGrantMessage")
      .filter({ hasText: /Granted.*100,000/ })
      .waitFor();
    assert.deepEqual(errors, []);
    console.log(
      JSON.stringify({
        depleting_hp: true,
        name_saved_across_pages: true,
        separate_admin_saves: true,
        polls_keep_drafts: true,
        local_preview_only: true,
        mobile_no_overflow: true,
        deep_link_and_points_grant: true,
        browser_errors: errors,
      }),
    );
  } finally {
    if (browser) await browser.close();
    server.kill("SIGTERM");
  }
})().catch((e) => {
  console.error(e);
  process.exitCode = 1;
});
