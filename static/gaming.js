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
    refreshing = false,
    fatal = false,
    pending = null,
    pendingAction = null,
    timer,
    polling = false,
    feedback = "";
  let selections = new Set(),
    walletEtag = "";
  const betLabel = id("betButton")?.textContent || "Play";
  const betForm = id("betForm");
  if (betForm) {
    // Handle validation ourselves so a rejected click has an inline reason.
    betForm.noValidate = true;
    const status = document.createElement("p");
    status.id = "betStatus";
    status.className = "small gaming-bet-status";
    id("betButton").before(status);
    id("betButton").setAttribute("aria-describedby", status.id);
    id("betButton").setAttribute("autocomplete", "off");
  }
  const verifierReady = typeof globalThis.RedFair?.verify === "function";
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
    // guarantees ten distinct picks even if the RNG repeats a value.
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
    feedback = value;
    id("gamingError").textContent = value;
    id("gamingError").hidden = !value;
    controls();
  };
  try {
    pending = JSON.parse(sessionStorage.getItem("rh.gaming.pending"));
    pendingAction = JSON.parse(sessionStorage.getItem("rh.blackjack.action"));
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
  function wagerProblem() {
    if (!id("redWager") || !wallet) return "";
    const wager = Number(id("redWager").value);
    if (!Number.isSafeInteger(wager) || wager < 1)
      return "Enter a positive whole-point wager.";
    if (wager > wallet.balance)
      return `Your wager exceeds your ${number(wallet.balance)} RedPoints balance. Lower it to play.`;
    return "";
  }
  function playBlock() {
    if (fatal)
      return "Verification failed. Reload and review your saved receipts before playing.";
    if (!secure) return secureMessage;
    if (!verifierReady || rules.version !== RedFair.VERSION)
      return "Game rules changed or did not load. Reload this page to continue.";
    if (!wallet) return "Loading your balance…";
    if (wallet.play_blocked) return wallet.play_blocked.message;
    if (wallet.needs_profile)
      return "Save your community name above to activate your RedPoints and play.";
    if (wallet.blackjack) {
      if (wallet.play_blocked) return wallet.play_blocked.message;
      if (pendingAction && !wallet.play_blocked) return "";
      return game === "blackjack"
        ? "Use Hit, Stand or Double to finish this hand."
        : "Continue your saved Blackjack hand before starting another game.";
    }
    // Recovering an existing receipt remains possible without another debit.
    if (pending && !wallet.needs_profile) return "";
    if (wallet.balance < 1)
      return "Refresh this page to restore 100,000 RedPoints, or wait for the weekly reset.";
    if (game === "keno" && !selections.size)
      return "Pick 1–10 numbers to play.";
    return "";
  }
  function controls() {
    const disabled = locked() || Boolean(wallet?.needs_profile);
    root
      .querySelectorAll(
        "#betForm input, #betForm select, #betForm button, [data-keno], #clientSeed, #diceBoardChance",
      )
      .forEach((el) => {
        if (el.id !== "betButton" && el.disabled !== disabled)
          el.disabled = disabled;
      });
    if (id("betButton")) {
      // Only a real in-flight request disables the button. Other blocked
      // states stay clickable so players can see why and how to recover.
      id("betButton").disabled = busy || Boolean(wallet?.needs_profile);
      id("betButton").setAttribute(
        "aria-disabled",
        String(busy || Boolean(playBlock())),
      );
      id("betButton").setAttribute("aria-busy", String(busy));
      id("betButton").textContent = busy
        ? refreshing ? "Restoring 100,000 points…" : "Checking your round…"
        : wallet?.needs_profile
          ? "Save your community name first"
        : pendingAction
          ? "Recover your move"
          : wallet?.blackjack
            ? "Hand in progress"
            : pending
              ? "Recover previous round"
              : betLabel;
      let reason = busy
        ? refreshing ? "Restoring your balance; game records are kept." : "Saving and verifying your round…"
        : playBlock();
      if (!reason)
        reason =
          feedback ||
          (pending
            ? "Recover the saved request here without a duplicate debit."
            : wagerProblem());
      if (!reason)
        reason =
          game === "plinko"
            ? "You can drop again while earlier balls are moving."
            : "Ready to play.";
      if (id("betStatus")) {
        id("betStatus").textContent = reason;
        id("betStatus").classList.toggle(
          "is-error",
          Boolean(
            !busy && (feedback || playBlock() || (!pending && wagerProblem())),
          ),
        );
      }
      if (wagerProblem()) id("redWager").setAttribute("aria-invalid", "true");
      else id("redWager").removeAttribute("aria-invalid");
    }
    root.querySelectorAll("[data-blackjack]").forEach((button) => {
      button.disabled =
        busy ||
        fatal ||
        !secure ||
        !verifierReady ||
        Boolean(wallet?.needs_profile) ||
        !wallet?.blackjack ||
        Boolean(pendingAction) ||
        Boolean(wallet?.play_blocked) ||
        (button.dataset.blackjack === "double" && !wallet.blackjack.can_double);
    });
    if (id("retryBet")) {
      id("retryBet").textContent = pendingAction
        ? "Recover your move"
        : "Recover pending result";
      id("retryBet").hidden =
        !pending || Boolean(wallet?.blackjack && !pendingAction);
      id("retryBet").disabled = busy || fatal || !secure || !verifierReady || Boolean(wallet?.needs_profile);
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
    if (!wallet && id("redWager")?.value === "100" && next.balance > 0)
      id("redWager").value = String(Math.min(100, next.balance));
    wallet = next;
    if (next.blackjack && !pending) remember(next.blackjack.bet);
    if (id("blackjackResume"))
      id("blackjackResume").hidden = !next.blackjack || game === "blackjack";
    renderBlackjack(next.blackjack);
    // A not-yet-activated allowance is labelled explicitly. An IP conflict is
    // an access problem, not a real zero balance and never another user's wallet.
    const unclaimed = next.needs_profile && !next.play_blocked;
    id("pointsBalance").textContent = next.play_blocked && next.needs_profile
      ? "—" : number(unclaimed ? Math.max(100000, next.balance) : next.balance);
    id("pointsLabel").textContent = unclaimed ? "YOUR STARTING REDPOINTS" : "YOUR REDPOINTS";
    if (id("redWager")) id("redWager").max = String(next.balance);
    id("pointsReset").textContent = unclaimed
      ? "Save your community name to activate this balance."
      : "100,000 on refresh · Weekly reset " + next.season.end_et;
    id("gamingProfile").hidden = !next.needs_profile;
    if (id("gamingNetworkNotice")) {
      id("gamingNetworkNotice").hidden = !next.play_blocked;
      id("gamingNetworkReason").textContent = next.play_blocked?.message || "";
      id("gamingRestore").hidden =
        next.play_blocked?.code !== "ip_wallet_exists";
    }
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
              number(receipt.result?.total_wager ?? receipt.wager),
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
    game === "blackjack"
      ? { decks: 6 }
      : game === "dice"
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
      id("diceMarker").hidden = true;
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
      const threshold =
        options.side === "under" ? options.chance : 100 - options.chance;
      if (id("diceBoardChance")) {
        id("diceBoardChance").value = String(threshold);
        id("diceBoardChance").setAttribute(
          "aria-valuetext",
          `${options.chance}% win chance; threshold ${threshold}`,
        );
        id("diceBoardChanceLabel").textContent =
          `${options.chance}% win chance`;
        const track = id("diceBoardChance").closest(".dice-track");
        track.style.setProperty("--dice-threshold", threshold + "%");
        track.classList.toggle("is-over", options.side === "over");
      }
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
    if (game === "blackjack") {
      id("payoutDescription").textContent =
        "Natural Blackjack: 3:2 profit (2.5× returned). Normal win: 2×. Push: stake returned. Bust or loss: 0. Whole-point rounding applies. Odds depend on your decisions; no fixed RTP is claimed.";
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
    if (game === "plinko") plinko.setBoard(options.rows, info.multipliers);
  }
  // One canvas loop for every visible ball. Outcomes come only from verified
  // receipts; the renderer never samples randomness or changes a payout.
  const plinko = (() => {
    const canvas = id("plinkoCanvas");
    const width = 720,
      height = 510,
      pegRadius = 3.5,
      ballRadius = 8;
    let board,
      layer,
      ctx,
      key = "",
      balls = [],
      resting = null;
    let frameId = null,
      timeoutId,
      lastHit = -1,
      warned = false;

    function cancelFrames() {
      if (frameId !== null && typeof cancelAnimationFrame === "function")
        cancelAnimationFrame(frameId);
      frameId = null;
      clearTimeout(timeoutId);
    }

    function unavailable(error) {
      cancelFrames();
      balls = [];
      if (!warned) {
        warned = true;
        console.warn(
          "PLINKO Animation unavailable; verified results and balances are still saved.",
          error,
        );
      }
      return false;
    }

    function slot(context, index, active = false) {
      const x = 360 + (index - board.rows / 2) * board.step;
      context.fillStyle = active
        ? "#fff2b6"
        : index < 2 || index > board.rows - 2
          ? "#a91f36"
          : "#672334";
      context.fillRect(x - board.step * 0.47, 438, board.step * 0.94, 38);
      context.fillStyle = active ? "#1b1020" : "#ffffff";
      const label = multiple(board.values[index]);
      let size = board.rows > 12 ? 10 : 12;
      context.font = `600 ${size}px sans-serif`;
      while (size > 6 && context.measureText(label).width > board.step * 0.84)
        context.font = `600 ${--size}px sans-serif`;
      context.textAlign = "center";
      context.fillText(label, x, 461);
    }

    function setBoard(rows, values) {
      if (!canvas) return false;
      try {
        const scale = Math.max(
          1,
          Math.min(
            2,
            ((canvas.getBoundingClientRect().width || width) / width) *
              (globalThis.devicePixelRatio || 1),
          ),
        );
        const nextKey = `${rows}:${values.join(",")}:${scale.toFixed(2)}`;
        if (key === nextKey && board) return true;
        // A different board cannot display an earlier board's path accurately.
        cancelFrames();
        balls = [];
        resting = null;
        lastHit = -1;
        board = {
          rows,
          values,
          step: 620 / (rows + 1),
          top: 64,
          dy: 332 / (rows - 1),
        };
        canvas.width = Math.round(width * scale);
        canvas.height = Math.round(height * scale);
        ctx = canvas.getContext("2d");
        layer = document.createElement("canvas");
        layer.width = canvas.width;
        layer.height = canvas.height;
        const background = layer.getContext("2d");
        if (!ctx || !background) return unavailable("Canvas context missing");
        ctx.setTransform(scale, 0, 0, scale, 0, 0);
        background.setTransform(scale, 0, 0, scale, 0, 0);
        for (let r = 0; r < rows; r++) {
          for (let c = 0; c <= r; c++) {
            background.beginPath();
            background.arc(
              360 + (c - r / 2) * board.step,
              board.top + r * board.dy,
              pegRadius,
              0,
              2 * Math.PI,
            );
            background.fillStyle = "#e9d9de";
            background.fill();
          }
        }
        values.forEach((_, index) => slot(background, index));
        key = nextKey;
        return paint(performance.now());
      } catch (error) {
        key = "";
        return unavailable(error);
      }
    }

    function trajectory(result, now) {
      const points = [
        { x: 360, y: 18 },
        { x: 360, y: board.top - pegRadius - ballRadius },
      ];
      let right = 0;
      result.path.forEach((bit, row) => {
        right += bit;
        points.push({
          x: 360 + (right - (row + 1) / 2) * board.step,
          y:
            row === board.rows - 1
              ? 427
              : board.top + (row + 1) * board.dy - pegRadius - ballRadius,
        });
      });
      return {
        points,
        slot: result.slot,
        began: now,
        duration: 360 + (board.rows - 1) * 105,
      };
    }

    function sample(ball, now) {
      const elapsed = Math.max(0, Math.min(ball.duration, now - ball.began));
      let segment, t;
      if (elapsed < 180) {
        segment = 0;
        t = elapsed / 180;
      } else {
        const middle = (board.rows - 1) * 105;
        if (elapsed < 180 + middle) {
          segment = 1 + Math.floor((elapsed - 180) / 105);
          t = ((elapsed - 180) % 105) / 105;
        } else {
          segment = board.rows;
          t = Math.min(1, (elapsed - 180 - middle) / 180);
        }
      }
      const a = ball.points[segment],
        b = ball.points[segment + 1];
      const dy = b.y - a.y;
      // Contact points sit above each peg, not inside it. Each verified bit
      // sends the ball to the left/right peg using a short parabolic bounce.
      const rise = Math.min(5, dy * 0.2);
      const launch = 2 * rise + 2 * Math.sqrt(rise * (rise + dy));
      return {
        x: a.x + (b.x - a.x) * t,
        y:
          segment === 0
            ? a.y + dy * t * t
            : a.y - launch * t + (dy + launch) * t * t,
      };
    }

    function paint(now) {
      if (!ctx || !layer) return false;
      try {
        ctx.clearRect(0, 0, width, height);
        ctx.drawImage(layer, 0, 0, width, height);
        if (lastHit >= 0) slot(ctx, lastHit, true);
        const positions = balls.map((ball) => sample(ball, now));
        if (resting && !balls.length) positions.push(resting);
        for (const position of positions) {
          ctx.beginPath();
          ctx.arc(position.x, position.y, ballRadius, 0, 2 * Math.PI);
          ctx.fillStyle = "#ff415b";
          ctx.shadowColor = "#ff415b";
          ctx.shadowBlur = 10;
          ctx.fill();
        }
        ctx.shadowBlur = 0;
        return true;
      } catch (error) {
        return unavailable(error);
      }
    }

    function finish() {
      const last = balls[balls.length - 1];
      if (last) {
        resting = last.points[last.points.length - 1];
        lastHit = last.slot;
      }
      balls = [];
      cancelFrames();
      paint(performance.now());
    }

    function frame() {
      frameId = null;
      try {
        // Use one monotonic clock. Older RAF timestamps and slow frames must
        // never rewind a ball or leave an animation waiting indefinitely.
        const now = performance.now();
        balls = balls.filter((ball) => {
          if (now - ball.began < ball.duration) return true;
          resting = ball.points[ball.points.length - 1];
          lastHit = ball.slot;
          return false;
        });
        if (!paint(now)) return;
        if (balls.length && !document.hidden)
          frameId = requestAnimationFrame(frame);
        else finish();
      } catch (error) {
        unavailable(error);
      }
    }

    function drop(rows, values, result) {
      try {
        if (!setBoard(rows, values)) return;
        const now = performance.now();
        balls.push(trajectory(result, now));
        if (
          document.hidden ||
          globalThis.matchMedia?.("(prefers-reduced-motion: reduce)").matches ||
          typeof requestAnimationFrame !== "function"
        ) {
          finish();
          return;
        }
        if (frameId === null) frameId = requestAnimationFrame(frame);
        clearTimeout(timeoutId);
        timeoutId = setTimeout(finish, balls[balls.length - 1].duration + 400);
      } catch (error) {
        unavailable(error);
      }
    }

    if (canvas) {
      document.addEventListener("visibilitychange", () => {
        if (document.hidden) finish();
      });
      window.addEventListener("pagehide", () => finish());
      let resizeId;
      window.addEventListener("resize", () => {
        clearTimeout(resizeId);
        resizeId = setTimeout(() => {
          if (board) setBoard(board.rows, board.values);
        }, 120);
      });
    }
    return { setBoard, drop };
  })();

  function showReceipt(receipt) {
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
      id("diceMarker").hidden = false;
      id("diceMarker").textContent = (r.roll / 100).toFixed(2);
      id("diceMarker").style.left =
        `calc(${r.roll / 100}% + ${12 - (24 * r.roll) / 10000}px)`;
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
    } else if (game === "blackjack") {
      renderBlackjack({
        ...r,
        nonce: receipt.nonce,
        round_id: receipt.request_id,
      });
    } else {
      const rows = receipt.options.rows,
        values = RedFair.table(
          "plinko",
          rows,
          receipt.options.risk,
          receipt.rules_version,
        );
      // Keep the verified outcome visible even if animation is unavailable.
      id("plinkoResult").textContent =
        `Slot ${r.slot} · ${multiple(r.multiplier)} · path ${r.path.map((n) => (n ? "R" : "L")).join(" ")}`;
      plinko.drop(rows, values, r);
    }
  }
  async function verifyReceipt(receipt, body) {
    const fields = [
      "rules_version",
      "request_id",
      "season",
      "game",
      "client_seed",
      "client_salt",
      "nonce",
      "wager",
      "options",
    ];
    let timeout;
    const verified = await Promise.race([
      RedFair.verify(receipt, body.commitment),
      new Promise((_, reject) => {
        timeout = setTimeout(
          () =>
            reject(
              Error(
                "Verification timed out. Recover this round before playing again.",
              ),
            ),
          10000,
        );
      }),
    ]).finally(() => clearTimeout(timeout));
    if (
      !fields.every(
        (key) =>
          RedFair.canonical(receipt[key]) === RedFair.canonical(body[key]),
      ) ||
      !verified
    ) {
      fatal = true;
      throw Error(
        "Fairness verification failed. Stop playing and download your receipts for review.",
      );
    }
  }
  async function recoverSavedRound(next) {
    if (!pending || busy || fatal || !secure || !verifierReady) return;
    const body = pending;
    const receipt = next.receipts.find(
      (item) => item.request_id === body.request_id,
    );
    if (!receipt) return;
    busy = true;
    controls();
    try {
      // Read-only recovery: verify the existing receipt against the original
      // commitment before clearing a lost-response marker. Never debit again.
      await verifyReceipt(receipt, body);
      remember(null);
      rememberAction(null);
      message();
      showReceipt(receipt);
    } catch (error) {
      message(error.message);
    } finally {
      busy = false;
      controls();
    }
  }
  async function submit(body) {
    if (busy || fatal || !secure || !verifierReady) return;
    busy = true;
    controls();
    message();
    try {
      const result = await api("/gaming/api/bet", body),
        receipt = result.receipt;
      if (!receipt && result.wallet?.blackjack) {
        renderWallet(result.wallet);
        message();
        return;
      }
      await verifyReceipt(receipt, body);
      remember(null);
      rememberAction(null);
      renderWallet(result.wallet);
      // Rendering is independent of the transaction lock. A verified drop
      // may keep animating while the next wager is submitted.
      showReceipt(receipt);
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
  function rememberAction(value) {
    pendingAction = value;
    try {
      value
        ? sessionStorage.setItem("rh.blackjack.action", JSON.stringify(value))
        : sessionStorage.removeItem("rh.blackjack.action");
    } catch {}
  }
  function renderBlackjack(hand) {
    if (!id("blackjackPlayer")) return;
    if (!hand) return;
    for (const [target, cards] of [
      ["blackjackPlayer", hand.player],
      ["blackjackDealer", hand.dealer],
    ]) {
      const row = id(target);
      // Retain existing card elements during balance polls and later hits.
      cards.forEach((card, index) => {
        const key = String(card),
          old = row.children[index];
        if (
          old?.dataset.card === key &&
          row.dataset.round === String(hand.round_id || hand.nonce)
        )
          return;
        const node = document.createElement("span");
        node.className = "playing-card";
        node.dataset.card = key;
        node.style.setProperty("--deal-delay", `${Math.min(index, 5) * 70}ms`);
        if (card === null) {
          node.classList.add("is-hidden");
          node.textContent = "◆";
          node.setAttribute("aria-label", "Face-down card");
        } else {
          const rank = (card % 13) + 1,
            suit = Math.floor((card % 52) / 13);
          const label = [
            "",
            "A",
            "2",
            "3",
            "4",
            "5",
            "6",
            "7",
            "8",
            "9",
            "10",
            "J",
            "Q",
            "K",
          ][rank];
          node.textContent = label + ["♠", "♥", "♣", "♦"][suit];
          node.classList.toggle("is-red", suit === 1 || suit === 3);
          node.setAttribute(
            "aria-label",
            label + " of " + ["spades", "hearts", "clubs", "diamonds"][suit],
          );
        }
        old ? old.replaceWith(node) : row.append(node);
      });
      while (row.children.length > cards.length) row.lastElementChild.remove();
      row.dataset.round = String(hand.round_id || hand.nonce);
    }
    id("blackjackPlayerTotal").textContent =
      hand.player_total + (hand.player_soft ? " · soft" : "");
    id("blackjackDealerTotal").textContent =
      hand.dealer_total +
      (hand.ended ? (hand.dealer_soft ? " · soft" : "") : " shown");
    id("blackjackStatus").textContent = hand.ended
      ? {
          blackjack: "Blackjack!",
          win: "You win.",
          push: "Push — your stake is returned.",
          lose: "Dealer wins.",
        }[hand.status] || "Hand complete."
      : `${number(hand.wager)} RedPoints in play. Choose Hit, Stand${hand.can_double ? " or Double" : ""}.`;
  }
  async function submitAction(body) {
    if (busy || fatal || !secure || !verifierReady) return;
    busy = true;
    message();
    controls();
    try {
      const result = await api("/gaming/api/blackjack/action", body);
      if (result.receipt) {
        await verifyReceipt(result.receipt, pending || wallet.blackjack.bet);
        remember(null);
        rememberAction(null);
        renderWallet(result.wallet);
        showReceipt(result.receipt);
      } else {
        rememberAction(null);
        renderWallet(result.wallet);
      }
    } catch (error) {
      if (error.definitive) {
        rememberAction(null);
        try {
          renderWallet((await api("/gaming/api/state")).wallet);
        } catch {}
      }
      message(
        error.name === "AbortError"
          ? "Move response timed out. Recover your move; it will not be played twice."
          : error.message,
      );
    } finally {
      busy = false;
      controls();
    }
  }
  root.querySelectorAll("[data-blackjack]").forEach((button) =>
    button.addEventListener("click", () => {
      const hand = wallet?.blackjack;
      if (
        !hand ||
        busy ||
        fatal ||
        pendingAction ||
        !secure ||
        !verifierReady ||
        wallet.play_blocked
      )
        return;
      const action = button.dataset.blackjack;
      if (action === "double" && !hand.can_double) return;
      const body = {
        round_id: hand.round_id,
        step: hand.step,
        action,
        action_id: randomHex(),
      };
      rememberAction(body);
      void submitAction(body);
    }),
  );

  id("betForm")?.addEventListener("submit", (event) => {
    event.preventDefault();
    if (busy) return;
    const blocked = playBlock();
    if (blocked) {
      message(blocked);
      if (wallet?.needs_profile && !wallet.play_blocked) {
        id("gamingUsername").scrollIntoView({ block: "center" });
        id("gamingUsername").focus({ preventScroll: true });
      }
      return;
    }
    if (pendingAction) {
      void submitAction(pendingAction);
      return;
    }
    if (pending) {
      void (pendingAction ? submitAction(pendingAction) : submit(pending));
      return;
    }
    const options = opt();
    if (game === "keno" && !selections.size)
      return message("Pick at least one Keno number.");
    const client = id("clientSeed").value,
      wager = Number(id("redWager").value);
    if (!/^[A-Za-z0-9 _.\-]{1,64}$/.test(client))
      return message("Use a valid 1–64 character client seed.");
    const invalidWager = wagerProblem();
    if (invalidWager) {
      message(invalidWager);
      id("redWager").focus();
      return;
    }
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
    if (pending)
      void (pendingAction ? submitAction(pendingAction) : submit(pending));
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
      for (let index = 0; index < 10; index++) {
        const other = index + randomBelow(pool.length - index);
        [pool[index], pool[other]] = [pool[other], pool[index]];
      }
      // Replace the selection only after all ten picks were generated.
      selections = new Set(pool.slice(0, 10));
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
  function boardChanceChanged() {
    if (locked()) return;
    const threshold = Number(id("diceBoardChance").value);
    const chance =
      id("diceSide").value === "under" ? threshold : 100 - threshold;
    id("diceChance").value = String(
      Math.max(1, Math.min(95, Math.round(chance))),
    );
    settingsChanged();
  }
  id("diceBoardChance")?.addEventListener("input", boardChanceChanged);
  id("diceBoardChance")?.addEventListener("change", boardChanceChanged);
  for (const name of ["diceChance", "diceBoardChance"]) {
    id(name)?.addEventListener(
      "wheel",
      (event) => {
        if (
          locked() ||
          event.currentTarget.disabled ||
          event.ctrlKey ||
          event.metaKey ||
          !event.deltaY
        )
          return;
        event.preventDefault();
        const slider = id("diceChance"),
          previous = slider.value;
        if (event.deltaY < 0) slider.stepUp();
        else slider.stepDown();
        if (slider.value !== previous)
          slider.dispatchEvent(new Event("input", { bubbles: true }));
      },
      { passive: false },
    );
  }
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
      if (value && !busy) {
        renderWallet(value.wallet);
        await recoverSavedRound(value.wallet);
      }
      id("gamingChecked").textContent =
        "Balance confirmed · checks every 5 seconds";
    } catch (error) {
      id("gamingChecked").textContent = "Balance update delayed · retrying";
    } finally {
      ((polling = false), (feedback = ""));
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
  if (pending && !wallet.blackjack)
    message(
      "An earlier wager needs confirmation. Recover its result before placing another.",
    );
  if (!secure) message(secureMessage);
  async function start() {
    // Recover an uncertain wager before resetting points. Its receipt and any
    // active Blackjack hand must survive a browser reload unchanged.
    await recoverSavedRound(wallet);
    const navigation = globalThis.performance?.getEntriesByType?.("navigation")?.[0];
    const reloaded = navigation?.type === "reload" ||
      (!navigation && globalThis.performance?.navigation?.type === 1);
    // Link navigation and automatic wallet polls must not refill the balance.
    if (reloaded && secure && !fatal && !wallet.needs_profile && !wallet.play_blocked) {
      busy = refreshing = true;
      controls();
      try {
        const result = await api("/gaming/api/refresh", {
          season: wallet.season.id,
          version: wallet.version,
        });
        renderWallet(result.wallet);
        walletEtag = "";
      } catch (error) {
        message(error.name === "AbortError"
          ? "The refresh response timed out. Checking the saved balance; reload to try again."
          : error.message);
      } finally {
        busy = refreshing = false;
        controls();
      }
    }
    poll();
  }
  void start();
})();
