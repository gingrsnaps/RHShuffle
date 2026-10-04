/* Server-authoritative play points. Never generate an outcome in the UI.
   Unknown POST results keep their receipt ID so retries cannot debit twice. */
(() => {
  "use strict";
  const root = document.querySelector(".gaming-page");
  if (!root) return;
  const id = (n) => document.getElementById(n),
    game = root.dataset.game,
    rules = JSON.parse(root.dataset.rules);
  const number = (n) =>
      (typeof n === "bigint" ? n : Number(n)).toLocaleString("en-US"),
    points = (n) => (n > 0 ? "+" : "") + number(n);
  let wallet,
    csrf = root.dataset.csrf,
    busy = false,
    fatal = false,
    pending = null,
    timer,
    polling = false;
  let selections = new Set(),
    walletEtag = "";
  const betLabel = id("betButton")?.textContent || "Play";
  const secure = Boolean(
    globalThis.crypto?.subtle && globalThis.crypto?.getRandomValues,
  );
  const secureMessage =
    "Fairness verification requires HTTPS or localhost and a browser with Web Crypto. Wagering is disabled.";
  const randomHex = () =>
    [...crypto.getRandomValues(new Uint8Array(16))]
      .map((n) => n.toString(16).padStart(2, "0"))
      .join("");
  function randomBelow(size) {
    // Quick picks are selections, not outcomes. Sampling the remaining pool
    // guarantees five distinct picks even if the RNG repeats a value.
    if (!globalThis.crypto?.getRandomValues)
      throw Error(
        "Quick pick needs browser randomness. Select numbers manually.",
      );
    const limit = 4294967296 - (4294967296 % size);
    const word = new Uint32Array(1);
    for (let attempt = 0; attempt < 128; attempt++) {
      crypto.getRandomValues(word);
      if (word[0] < limit) return word[0] % size;
    }
    throw Error("Quick pick could not generate numbers. Please try again.");
  }
  const locked = () => busy || fatal || Boolean(pending);
  const message = (value = "") => {
    if (!value && !secure) value = secureMessage;
    id("gamingError").textContent = value;
    id("gamingError").hidden = !value;
  };
  try {
    pending = JSON.parse(sessionStorage.getItem("rh.gaming.pending"));
  } catch {}
  function remember(value) {
    pending = value;
    try {
      value
        ? sessionStorage.setItem("rh.gaming.pending", JSON.stringify(value))
        : sessionStorage.removeItem("rh.gaming.pending");
    } catch {}
    if (id("retryBet")) id("retryBet").hidden = !pending;
  }
  if (id("clientSeed") && secure) {
    let seed = "";
    try {
      seed = localStorage.getItem("rh.gaming.clientSeed") || "";
    } catch {}
    id("clientSeed").value = /^[A-Za-z0-9 _.\-]{1,64}$/.test(seed)
      ? seed
      : randomHex();
    id("clientSeed").addEventListener("change", () => {
      try {
        localStorage.setItem("rh.gaming.clientSeed", id("clientSeed").value);
      } catch {}
    });
  }
  function controls() {
    root
      .querySelectorAll(
        "#betForm input, #betForm select, #betForm button, [data-keno], #clientSeed",
      )
      .forEach((el) => (el.disabled = locked()));
    if (id("betButton")) {
      id("betButton").disabled =
        locked() ||
        !secure ||
        wallet?.needs_profile ||
        wallet?.balance < 1 ||
        (game === "keno" && !selections.size);
      id("betButton").textContent = busy ? "Checking your round…" : betLabel;
    }
    if (id("retryBet")) {
      id("retryBet").hidden = !pending;
      id("retryBet").disabled = busy || !secure;
    }
  }
  function renderWallet(next) {
    if (
      !next ||
      !Number.isSafeInteger(next.balance) ||
      next.balance < 0 ||
      !next.season
    )
      throw Error("Invalid wallet response");
    if (
      wallet &&
      (Number(next.season.id) < Number(wallet.season.id) ||
        next.version < wallet.version ||
        next.nonce < wallet.nonce)
    )
      return;
    wallet = next;
    id("pointsBalance").textContent = number(next.balance);
    if (id("redWager")) id("redWager").max = String(next.balance);
    id("pointsReset").textContent = "Resets " + next.season.end_et;
    id("gamingProfile").hidden = !next.needs_profile;
    id("gamingIdentity").hidden = next.needs_profile;
    id("gamingPlayerName").textContent = next.name;
    if (id("fairCommitment"))
      id("fairCommitment").textContent =
        next.commitment || "Save your name to prepare a commitment.";
    if (id("fairNonce")) id("fairNonce").textContent = next.nonce;
    if (id("gamingStats")) {
      id("gamingStats").replaceChildren(
        ...Object.entries(next.stats).map(([name, stat]) => {
          const article = document.createElement("article");
          for (const [tag, text] of [
            ["strong", name[0].toUpperCase() + name.slice(1)],
            ["b", points(stat.net)],
            ["small", `${stat.bets} rounds · net RedPoints`],
          ]) {
            const el = document.createElement(tag);
            el.textContent = text;
            article.append(el);
          }
          return article;
        }),
      );
    }
    id("betHistory").replaceChildren(
      ...(next.receipts.length
        ? next.receipts.map((receipt) => {
            const tr = document.createElement("tr");
            for (const text of [
              receipt.game,
              number(receipt.wager),
              number(receipt.payout),
              points(receipt.net),
            ]) {
              const td = document.createElement("td");
              td.textContent = text;
              tr.append(td);
            }
            const td = document.createElement("td"),
              button = document.createElement("button");
            button.type = "button";
            button.className = "text-link";
            button.textContent = "Verify / receipt";
            button.addEventListener("click", async () => {
              try {
                button.textContent = (await RedFair.verify(receipt))
                  ? "Verified · download"
                  : "Verification failed";
                const blob = new Blob([JSON.stringify(receipt, null, 2)], {
                    type: "application/json",
                  }),
                  url = URL.createObjectURL(blob),
                  a = document.createElement("a");
                a.href = url;
                a.download = `redpoints-${receipt.request_id}.json`;
                a.click();
                setTimeout(() => URL.revokeObjectURL(url), 1000);
              } catch {
                button.textContent = "Could not verify";
              }
            });
            td.append(button);
            tr.append(td);
            return tr;
          })
        : [
            (() => {
              const tr = document.createElement("tr"),
                td = document.createElement("td");
              td.colSpan = 5;
              td.textContent = "No rounds yet.";
              td.className = "empty";
              tr.append(td);
              return tr;
            })(),
          ]),
    );
    controls();
  }
  async function api(url, body, conditional = false) {
    const controller = new AbortController(),
      timeout = setTimeout(() => controller.abort(), 15000);
    try {
      const response = await fetch(url, {
        method: body ? "POST" : "GET",
        cache: "no-store",
        credentials: "same-origin",
        signal: controller.signal,
        headers: {
          Accept: "application/json",
          ...(conditional && walletEtag ? { "If-None-Match": walletEtag } : {}),
          ...(body
            ? { "Content-Type": "application/json", "X-CSRF-Token": csrf }
            : {}),
        },
        body: body ? JSON.stringify(body) : undefined,
      });
      if (conditional && response.status === 304) return null;
      if (conditional) walletEtag = response.headers.get("etag") || "";
      if (!response.headers.get("content-type")?.includes("application/json"))
        throw Error(
          `The server returned HTTP ${response.status}. Your pending wager is protected; retry to recover it.`,
        );
      const value = await response.json();
      if (!response.ok) {
        const error = Error(
          value.error || `Request failed (${response.status})`,
        );
        error.definitive = response.status < 500 && response.status !== 408;
        throw error;
      }
      if (value.release !== document.body.dataset.release)
        throw Error("The app was updated. Reload before continuing.");
      if (value.player_csrf) csrf = value.player_csrf;
      return value;
    } finally {
      clearTimeout(timeout);
    }
  }
  const opt = () =>
    game === "dice"
      ? { chance: Number(id("diceChance").value), side: id("diceSide").value }
      : game === "keno"
        ? {
            picks: [...selections].sort((a, b) => a - b),
            risk: root.querySelector('[name="risk"]:checked').value,
          }
        : {
            rows: Number(id("plinkoRows").value),
            risk: root.querySelector('[name="risk"]:checked').value,
          };
  const multiple = (units) =>
    (units / 10000).toLocaleString("en-US", { maximumFractionDigits: 4 }) + "×";
  function clearResult() {
    // Old receipt highlights must never look like the next selection or draw.
    root
      .querySelectorAll("[data-keno]")
      .forEach((el) => el.classList.remove("drawn", "matched"));
    if (id("gameResult")) {
      id("gameResult").textContent = "Ready when you are.";
      id("gameResult").classList.remove("is-win");
      id("betProof").textContent = "";
    }
    if (id("diceRoll")) {
      id("diceRoll").textContent = "—";
      id("diceRollLabel").textContent = "Your next roll";
      id("diceMarker").style.left = "50%";
    }
    if (id("plinkoResult"))
      id("plinkoResult").textContent =
        "The ball's path is fixed by the committed seeds.";
  }
  function settingsChanged() {
    if (locked()) return;
    clearResult();
    message();
    payout();
    controls();
  }
  function payout() {
    if (!game) return;
    const options = opt(),
      wager = Number(id("redWager").value) || 0;
    // Large stakes can overflow Number during multiplication even when the
    // final return is exact. Preview with the same integer math as settlement.
    const amount =
      Number.isSafeInteger(wager) && wager > 0 ? BigInt(wager) : 0n;
    if (game === "dice") {
      id("diceChanceLabel").textContent = options.chance + "%";
      id("diceTarget").textContent =
        options.side === "under"
          ? `Roll below ${options.chance.toFixed(2)}`
          : `Roll at or above ${(100 - options.chance).toFixed(2)}`;
      id("dicePayout").textContent =
        number((amount * 99n) / BigInt(options.chance)) +
        " points returned on a win";
      id("payoutDescription").textContent =
        `${options.chance}% win chance · ${(99 / options.chance).toFixed(4)}× return · 99% expected return before whole-point rounding.`;
      return;
    }
    const size = game === "keno" ? Math.max(1, selections.size) : options.rows,
      info = rules[game][String(size)][options.risk];
    if (game === "keno") {
      id("kenoSelection").textContent = selections.size
        ? `${selections.size} selected · ${[...selections].sort((a, b) => a - b).join(", ")}`
        : "Pick 1–10 numbers on the board.";
      root.querySelectorAll("[data-keno]").forEach((el) => {
        const selected = selections.has(Number(el.dataset.keno));
        el.classList.toggle("selected", selected);
        el.setAttribute("aria-pressed", String(selected));
      });
      if (!selections.size) {
        id("payoutDescription").textContent =
          "Select 1–10 numbers to see the payout table.";
        id("payoutTable").replaceChildren();
        return;
      }
    }
    id("payoutDescription").textContent =
      `${game === "keno" ? size + " picked number(s) · payout by matches" : "Slot 0 at the left → slot " + size + " at the right"} · ${info.rtp_percent}% expected return before whole-point rounding.`;
    id("payoutTable").replaceChildren(
      ...info.multipliers.map((value, index) => {
        const box = document.createElement("div");
        for (const [tag, text] of [
          [
            "small",
            game === "keno"
              ? `${index} match${index === 1 ? "" : "es"}`
              : `Slot ${index}`,
          ],
          ["strong", multiple(value)],
          ["small", `${number((amount * BigInt(value)) / 10000n)} RP`],
        ]) {
          const el = document.createElement(tag);
          el.textContent = text;
          box.append(el);
        }
        box.title = `Outcome probability: ${(info.probabilities[index] * 100).toFixed(6)}%`;
        return box;
      }),
    );
    if (game === "plinko") drawPlinko(options.rows, info.multipliers);
  }
  function drawPlinko(rows, multipliers, ball = null, hit = -1) {
    try {
      const canvas = id("plinkoCanvas");
      if (!canvas) return false;
      const ctx = canvas.getContext("2d"),
        step = 620 / (rows + 1),
        dy = 380 / rows;
      if (!ctx) return false;
      ctx.clearRect(0, 0, 720, 510);
      for (let r = 0; r < rows; r++)
        for (let c = 0; c <= r; c++) {
          ctx.beginPath();
          ctx.arc(360 + (c - r / 2) * step, 44 + r * dy, 3.5, 0, 2 * Math.PI);
          ctx.fillStyle = "#e9d9de";
          ctx.fill();
        }
      multipliers.forEach((value, index) => {
        const x = 360 + (index - rows / 2) * step;
        ctx.fillStyle =
          index === hit
            ? "#fff2b6"
            : index < 2 || index > rows - 2
              ? "#a91f36"
              : "#672334";
        ctx.fillRect(x - step * 0.47, 438, step * 0.94, 38);
        ctx.fillStyle = index === hit ? "#1b1020" : "#ffffff";
        ctx.font = `600 ${rows > 12 ? 9 : 12}px sans-serif`;
        ctx.textAlign = "center";
        ctx.fillText(
          (value / 10000).toFixed(value >= 100000 ? 0 : 2) + "×",
          x,
          461,
        );
      });
      if (ball) {
        ctx.beginPath();
        ctx.arc(ball.x, ball.y, 8, 0, 2 * Math.PI);
        ctx.fillStyle = "#ff415b";
        ctx.shadowColor = "#ff415b";
        ctx.shadowBlur = 15;
        ctx.fill();
        ctx.shadowBlur = 0;
      }
      return true;
    } catch {
      // A missing/lost canvas must not interrupt a settled, verified round.
      return false;
    }
  }
  function animatePlinko(rows, values, result) {
    const landing = {
      x: 360 + ((result.slot - rows / 2) * 620) / (rows + 1),
      y: 419,
    };
    const finalBoard = () => drawPlinko(rows, values, landing, result.slot);
    if (
      document.hidden ||
      globalThis.matchMedia?.("(prefers-reduced-motion: reduce)").matches ||
      typeof requestAnimationFrame !== "function" ||
      !drawPlinko(rows, values, { x: 360, y: 20 })
    ) {
      finalBoard();
      return Promise.resolve();
    }
    const steps = [{ x: 360, y: 20 }];
    let right = 0;
    result.path.forEach((bit, i) => {
      right += bit;
      steps.push({
        x: 360 + ((right - (i + 1) / 2) * 620) / (rows + 1),
        y: 44 + ((i + 1) * 380) / rows,
      });
    });
    steps[rows] = landing;
    return new Promise((resolve) => {
      let frameId,
        timeoutId,
        finished = false;
      const began = performance.now();
      function finish() {
        if (finished) return;
        finished = true;
        cancelAnimationFrame(frameId);
        clearTimeout(timeoutId);
        document.removeEventListener("visibilitychange", onVisibility);
        finalBoard();
        resolve();
      }
      function onVisibility() {
        if (document.hidden) finish();
      }
      function frame() {
        if (finished) return;
        try {
          // RAF timestamps can predate the bet callback. Use one clock and
          // clamp both ends so an older frame cannot index outside the path.
          const progress = Math.max(
            0,
            Math.min(1, (performance.now() - began) / 1100),
          );
          const position = progress * rows,
            index = Math.min(rows - 1, Math.floor(position)),
            part = position - index;
          const drawn = drawPlinko(rows, values, {
            x: steps[index].x + (steps[index + 1].x - steps[index].x) * part,
            y: steps[index].y + (steps[index + 1].y - steps[index].y) * part,
          });
          if (!drawn || progress >= 1 || document.hidden) finish();
          else frameId = requestAnimationFrame(frame);
        } catch {
          finish();
        }
      }
      // Animation is presentation only: stalled frames must always release
      // the controls. Settlement and fairness checks happen before this.
      timeoutId = setTimeout(finish, 1600);
      document.addEventListener("visibilitychange", onVisibility);
      try {
        frameId = requestAnimationFrame(frame);
      } catch {
        finish();
      }
    });
  }
  async function showReceipt(receipt) {
    if (id("gameResult")) {
      id("gameResult").textContent =
        `${receipt.game[0].toUpperCase() + receipt.game.slice(1)} · ${points(receipt.net)} RedPoints net · ${number(receipt.payout)} returned`;
      id("gameResult").classList.toggle("is-win", receipt.net > 0);
      id("betProof").textContent =
        `Verified in your browser · bet ${receipt.nonce} · seed revealed`;
    }
    if (receipt.game !== game) return;
    const r = receipt.result;
    if (game === "dice") {
      id("diceRoll").textContent = (r.roll / 100).toFixed(2);
      id("diceRollLabel").textContent = r.won
        ? "Target matched"
        : "Outside your target";
      id("diceMarker").style.left = r.roll / 100 + "%";
    } else if (game === "keno") {
      root.querySelectorAll("[data-keno]").forEach((el) => {
        const n = Number(el.dataset.keno),
          drawn = r.drawn.includes(n);
        el.classList.toggle("drawn", drawn);
        el.classList.toggle(
          "matched",
          drawn && receipt.options.picks.includes(n),
        );
      });
      id("gameResult").textContent =
        `${r.hits} matched · ${points(receipt.net)} RedPoints net · ${number(receipt.payout)} returned`;
    } else {
      const rows = receipt.options.rows,
        values = rules.plinko[String(rows)][receipt.options.risk].multipliers;
      // Keep the verified outcome visible even if animation is unavailable.
      id("plinkoResult").textContent =
        `Slot ${r.slot} · ${multiple(r.multiplier)} · path ${r.path.map((n) => (n ? "R" : "L")).join(" ")}`;
      await animatePlinko(rows, values, r);
    }
  }
  async function submit(body) {
    if (busy || !secure) return;
    busy = true;
    controls();
    message();
    try {
      const result = await api("/gaming/api/bet", body),
        receipt = result.receipt;
      const fields = [
        "request_id",
        "season",
        "game",
        "client_seed",
        "client_salt",
        "nonce",
        "wager",
        "options",
      ];
      if (
        !fields.every(
          (key) =>
            RedFair.canonical(receipt[key]) === RedFair.canonical(body[key]),
        ) ||
        !(await RedFair.verify(receipt, body.commitment))
      ) {
        fatal = true;
        throw Error(
          "Fairness verification failed. Stop playing and download your receipts for review.",
        );
      }
      remember(null);
      renderWallet(result.wallet);
      await showReceipt(receipt);
    } catch (error) {
      if (error.definitive) {
        remember(null);
        try {
          renderWallet((await api("/gaming/api/state")).wallet);
        } catch {}
      }
      message(
        error.name === "AbortError"
          ? "The response timed out. Recover the pending result before placing another wager."
          : error.message,
      );
    } finally {
      busy = false;
      controls();
    }
  }
  id("betForm")?.addEventListener("submit", (event) => {
    event.preventDefault();
    if (locked() || !secure || wallet.needs_profile) return;
    const options = opt();
    if (game === "keno" && !selections.size)
      return message("Pick at least one Keno number.");
    const client = id("clientSeed").value,
      wager = Number(id("redWager").value);
    if (!/^[A-Za-z0-9 _.\-]{1,64}$/.test(client))
      return message("Use a valid 1–64 character client seed.");
    if (!Number.isSafeInteger(wager) || wager < 1 || wager > wallet.balance)
      return message(
        "Enter a positive whole-point wager within your RedPoints balance.",
      );
    const body = {
      rules_version: RedFair.VERSION,
      game,
      request_id: randomHex(),
      season: wallet.season.id,
      nonce: wallet.nonce,
      commitment: wallet.commitment,
      client_seed: client,
      client_salt: randomHex(),
      wager,
      options,
    };
    clearResult();
    payout();
    remember(body);
    void submit(body);
  });
  id("retryBet")?.addEventListener("click", () => {
    if (pending) void submit(pending);
  });
  id("gamingNameForm").addEventListener("submit", async (event) => {
    event.preventDefault();
    const button = event.currentTarget.querySelector("button");
    button.disabled = true;
    try {
      const value = await api("/gaming/api/profile", {
        username: id("gamingUsername").value,
      });
      renderWallet(value.wallet);
      message();
    } catch (error) {
      message(error.message);
    } finally {
      button.disabled = false;
    }
  });
  root.querySelectorAll("[data-wager-scale]").forEach((button) =>
    button.addEventListener("click", () => {
      if (locked()) return;
      const current = Number(id("redWager").value);
      id("redWager").value = Math.max(
        1,
        Math.min(
          wallet.balance,
          Math.floor(
            (Number.isFinite(current) ? current : 1) *
              Number(button.dataset.wagerScale),
          ),
        ),
      );
      settingsChanged();
    }),
  );
  root.querySelectorAll("[data-keno]").forEach((button) =>
    button.addEventListener("click", () => {
      if (locked()) return;
      const n = Number(button.dataset.keno);
      if (selections.has(n)) selections.delete(n);
      else if (selections.size < 10) selections.add(n);
      else return message("You can pick up to 10 numbers.");
      settingsChanged();
    }),
  );
  id("kenoClear")?.addEventListener("click", () => {
    if (locked()) return;
    selections.clear();
    settingsChanged();
  });
  id("kenoAuto")?.addEventListener("click", () => {
    if (locked()) return;
    try {
      const pool = Array.from({ length: 40 }, (_, index) => index + 1);
      for (let index = 0; index < 5; index++) {
        const other = index + randomBelow(pool.length - index);
        [pool[index], pool[other]] = [pool[other], pool[index]];
      }
      // Replace the selection only after all five picks were generated.
      selections = new Set(pool.slice(0, 5));
      settingsChanged();
    } catch (error) {
      message(error.message);
    }
  });
  root
    .querySelectorAll("#redWager,#diceChance,#diceSide,#plinkoRows,[name=risk]")
    .forEach((el) => {
      el.addEventListener("input", settingsChanged);
      el.addEventListener("change", settingsChanged);
    });
  id("diceChance")?.addEventListener(
    "wheel",
    (event) => {
      const slider = event.currentTarget;
      if (
        locked() ||
        slider.disabled ||
        event.ctrlKey ||
        event.metaKey ||
        !event.deltaY
      )
        return;
      // Scroll only over this control; leave page scrolling and pinch zoom alone.
      event.preventDefault();
      const previous = slider.value;
      if (event.deltaY < 0) slider.stepUp();
      else slider.stepDown();
      if (slider.value !== previous)
        slider.dispatchEvent(new Event("input", { bubbles: true }));
    },
    { passive: false },
  );
  async function poll() {
    clearTimeout(timer);
    if (document.hidden || polling) return;
    if (busy) {
      timer = setTimeout(poll, 5000);
      return;
    }
    polling = true;
    try {
      const value = await api("/gaming/api/state", null, true);
      if (value && !busy) renderWallet(value.wallet);
      id("gamingChecked").textContent =
        "Balance confirmed · checks every 5 seconds";
    } catch (error) {
      id("gamingChecked").textContent = "Balance update delayed · retrying";
    } finally {
      polling = false;
      if (!document.hidden) timer = setTimeout(poll, 5000);
    }
  }
  document.addEventListener("visibilitychange", () => {
    clearTimeout(timer);
    if (!document.hidden) poll();
  });
  renderWallet(JSON.parse(root.dataset.wallet));
  remember(pending);
  payout();
  if (pending)
    message(
      "An earlier wager needs confirmation. Recover its result before placing another.",
    );
  if (!secure) message(secureMessage);
  poll();
})();
