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
    feedback = "",
    holdemTable = null;
  let selections = new Set(),
    pokerHolds = new Set(),
    pokerRound = "",
    walletEtag = "",
    presentationSequence = 0;
  const cardAnimations = new Set();
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
  const verifierReady = typeof globalThis.RedFair?.verify === "function" &&
    (game !== "poker" || (typeof globalThis.RedHoldemFair?.replay === "function" && typeof globalThis.RedHoldemUI?.create === "function"));
  const secure = Boolean(
    globalThis.crypto?.subtle && globalThis.crypto?.getRandomValues,
  );
  const isHoldem = value => value?.variant === "texas_holdem" || value?.options?.variant === "texas_holdem";
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
    pendingAction = JSON.parse(sessionStorage.getItem("rh.gaming.action") || sessionStorage.getItem("rh.blackjack.action"));
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
    if (!Number.isSafeInteger(wager) || wager < (game === "poker" ? 20 : 1))
      return game === "poker" ? "Choose a table stack of at least 20 whole RedPoints." : "Enter a positive whole-point wager.";
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
      return "Save your community name to play.";
    if (wallet.blackjack || wallet.poker) {
      if (wallet.play_blocked) return wallet.play_blocked.message;
      if (pendingAction && !wallet.play_blocked) return "";
      if (wallet.poker) return game === "poker"
        ? isHoldem(wallet.poker) ? "Your hand is saved. Use the table controls." : "Choose the cards to hold, then draw once."
        : "Continue your saved Poker hand before starting another game.";
      return game === "blackjack"
        ? "Use Hit, Stand or Double to finish this hand."
        : "Continue your saved Blackjack hand before starting another game.";
    }
    // Recovering an existing receipt remains possible without another debit.
    if (pending && !wallet.needs_profile) return "";
    if (wallet.balance < 1)
      return "Refresh this page to restore 100,000 RedPoints, or wait for the weekly reset.";
    if (game === "limbo" && limboProblem()) return limboProblem();
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
        ? refreshing ? "Restoring points…" : "Playing…"
        : wallet?.needs_profile
          ? "Save your name first"
        : pendingAction
          ? "Recover your move"
          : (wallet?.blackjack || wallet?.poker)
            ? "Hand in progress"
            : pending
              ? "Recover previous round"
              : betLabel;
      let reason = busy
        ? refreshing ? "Restoring balance…" : "Verifying…"
        : playBlock();
      if (!reason)
        reason =
          feedback ||
          (pending
            ? "Recover the saved round."
            : wagerProblem());
      if (!reason)
        reason =
          game === "plinko"
            ? ""
            : "";
      if (id("betStatus")) {
        id("betStatus").textContent = reason;
        id("betStatus").classList.toggle(
          "is-error",
          Boolean(
            !busy && (feedback || (!(wallet?.blackjack || wallet?.poker) && playBlock()) || (!pending && wagerProblem())),
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
    const pokerLocked = busy || fatal || !secure || !verifierReady ||
      !wallet?.poker || Boolean(wallet?.needs_profile) || Boolean(pendingAction);
    root.querySelectorAll("[data-poker-hold],#pokerDraw,#pokerHoldAll,#pokerClear").forEach(button => {
      button.disabled = pokerLocked;
    });
    if (id("pokerDraw")) id("pokerDraw").textContent = busy ? "Saving draw…" :
      pokerHolds.size === 5 ? "Keep all · finish hand" : `Draw ${5-pokerHolds.size} card${pokerHolds.size === 4 ? "" : "s"}`;
    holdemTable?.controls(pokerLocked || !isHoldem(wallet?.poker));
    if (id("retryBet")) {
      id("retryBet").textContent = pendingAction
        ? "Recover your move"
        : "Recover pending result";
      id("retryBet").hidden =
        !pending || Boolean((wallet?.blackjack || wallet?.poker) && !pendingAction);
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
    if (next.poker) {
      if (pending?.request_id === next.poker.round_id && pending.initial_cards &&
          RedFair.canonical(pending.initial_cards) !== RedFair.canonical(next.poker.initial)) {
        fatal = true;
        throw Error("The saved initial Poker cards changed. Keep your receipt and reload before playing.");
      }
      if (isHoldem(next.poker)) {
        assertHoldemActions(next.poker, pending);
        if (pendingAction?.variant === "texas_holdem" && pendingAction.round_id === next.poker.round_id && next.poker.step > pendingAction.step) {
          rememberAction(null); // A lost reply is acknowledged by the saved matching action.
          message();
        }
      }
      if (!pending || pending.request_id === next.poker.round_id)
        remember({ ...(pending || next.poker.bet), initial_cards: [...next.poker.initial],
          ...(isHoldem(next.poker) ? {player_actions:next.poker.actions} : {}) });
    }
    if (id("pokerResume")) id("pokerResume").hidden = !next.poker || game === "poker";
    renderPoker(next.poker);
    renderBlackjack(next.blackjack);
    // The signed player owns this balance. Connection metadata never blocks play.
    // Label the allowance until the player confirms their community name.
    const unclaimed = next.needs_profile && !next.play_blocked;
    id("pointsBalance").textContent = next.play_blocked && next.needs_profile
      ? "—" : number(unclaimed ? Math.max(100000, next.balance) : next.balance);
    id("pointsLabel").textContent = unclaimed ? "YOUR STARTING REDPOINTS" : "YOUR REDPOINTS";
    if (id("redWager")) id("redWager").max = String(next.balance);
    id("pointsReset").textContent = unclaimed
      ? "Save your name to play."
      : "Resets " + next.season.end_et;
    id("gamingProfile").hidden = !next.needs_profile;
    if (id("gamingNetworkNotice")) {
      id("gamingNetworkNotice").hidden = !next.play_blocked;
      id("gamingNetworkReason").textContent = next.play_blocked?.message || "";
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
            ["strong", name === "poker" ? "Hold’em" : name[0].toUpperCase() + name.slice(1)],
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
              receipt.game === "poker" ? isHoldem(receipt) ? "Hold’em" : "Video Poker · legacy" : receipt.game,
              number(receipt.result?.total_wager ?? receipt.wager),
              number(isHoldem(receipt) ? receipt.result.returned : receipt.payout),
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
            button.textContent = "Verify";
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
        error.code = value.code || "";
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
  function opt() {
    if (game === "blackjack") return { decks: 6 };
    if (game === "baccarat") return {decks:8, side:root.querySelector('[name="baccaratSide"]:checked').value};
    if (game === "poker") return { variant: "texas_holdem", button:wallet?.poker_button || "player" };
    if (game === "limbo") return { target: Math.round(Number(id("limboTarget").value)*100) };
    if (game === "coinflip") return { side: root.querySelector('[name="coinSide"]:checked').value };
    if (game === "dice") return { chance: Number(id("diceChance").value), side: id("diceSide").value };
    if (game === "keno") return { picks: [...selections].sort((a,b) => a-b), risk: root.querySelector('[name="risk"]:checked').value };
    return { rows: Number(id("plinkoRows").value), risk: root.querySelector('[name="risk"]:checked').value };
  }
  function limboProblem() {
    const value = Number(id("limboTarget")?.value);
    return !Number.isFinite(value) || value < 1.01 || value > 1000000 ||
      Math.abs(value*100-Math.round(value*100)) > 0.000001
      ? "Use a target from 1.01× to 1,000,000× with at most two decimals." : "";
  }
  const multiple = (units) =>
    (units / 10000).toLocaleString("en-US", { maximumFractionDigits: 4 }) + "×";
  function clearResult() {
    presentationSequence++;
    delete root.dataset.animating;
    // Old receipt highlights must never look like the next selection or draw.
    root
      .querySelectorAll("[data-keno]")
      .forEach((el) => el.classList.remove("drawn", "matched"));
    if (id("gameResult")) {
      id("gameResult").textContent = "Ready.";
      id("gameResult").classList.remove("is-win");
      id("betProof").textContent = "";
    }
    if (id("diceRoll")) {
      id("diceRoll").textContent = "—";
      id("diceRollLabel").textContent = "Your next roll";
      id("diceMarker").hidden = true;
    }
    if (id("limboResult")) {
      id("limboResult").textContent = "1.00×";
      id("limboResult").closest(".limbo-stage").classList.remove("is-win");
      id("limboTrail").style.transform = "scaleX(0)";
      id("limboStatus").textContent = "Ready.";
    }
    if (id("redCoin")) {
      id("redCoin").style.transform = "rotateY(0deg)";
      id("redCoin").setAttribute("aria-label", "Ready to flip");
      id("coinStatus").textContent = "Ready.";
    }
    if (id("plinkoResult"))
      id("plinkoResult").textContent =
        "Ready to drop.";
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
        `${options.chance}% chance · ${(99 / options.chance).toFixed(4)}× return`;
      return;
    }
    if (game === "blackjack") {
      id("payoutDescription").textContent =
        "Blackjack 2.5× · Win 2× · Push 1× · Loss 0×";
      return;
    }
    if (game === "limbo") {
      const invalid = limboProblem();
      if (invalid) {
        id("payoutDescription").textContent = invalid;
        id("limboPayout").textContent = "Choose a valid target";
        id("limboChance").textContent = "—";
        return;
      }
      const wins = 99n*4294967296n/BigInt(options.target);
      const chance = (Number(wins)*100/4294967296).toLocaleString("en-US", {maximumFractionDigits:7});
      const target = (options.target/100).toLocaleString("en-US",{minimumFractionDigits:2,maximumFractionDigits:2});
      id("limboChance").textContent = `${chance}% win chance`;
      id("limboPayout").textContent = `${number(amount*BigInt(options.target)/100n)} points returned on a win`;
      id("limboTargetLabel").textContent = `Your target · ${target}×`;
      id("payoutDescription").textContent = `${target}× target · ${chance}% chance`;
      return;
    }
    if (game === "coinflip") {
      id("coinPayout").textContent = `${number(amount*198n/100n)} points returned on a win`;
      id("payoutDescription").textContent = "Win 1.98× · Loss 0× · 50% chance";
      return;
    }
    if (game === "poker" && !wallet?.poker?.holds && (!wallet?.poker || isHoldem(wallet.poker))) {
      const stack = Number(id("redWager").value), big = Math.max(2, Math.floor(stack/50));
      id("holdemNextBlinds").textContent = `Blinds ${number(Math.max(1,Math.floor(big/2)))} / ${number(big)} RP`;
      id("payoutDescription").textContent = "Strongest to weakest. Best five of seven wins; suits do not break ties.";
      id("payoutTable").replaceChildren(...[...(globalThis.RedHoldemFair?.labels || [])].reverse().map(label => Object.assign(document.createElement("div"), {textContent:label})));
      return;
    }
    if (game === "poker") {
      id("payoutDescription").textContent = "9/6 Jacks or Better · Total returns";
      id("payoutTable").classList.add("poker-paytable");
      id("payoutTable").replaceChildren(...Object.entries(rules.poker.legacy_paytable).sort((a,b) => b[1]-a[1]).map(([hand, multiplier]) => {
        const cell = document.createElement("div");cell.dataset.hand = hand;
        for (const [tag, text] of [["small", rules.poker.legacy_labels[hand]], ["strong", `${multiplier}×`], ["small", `${number(amount*BigInt(multiplier))} returned`]]) {
          const node = document.createElement(tag);node.textContent = text;cell.append(node);
        }
        return cell;
      }));
      return;
    }
    if (game === "baccarat") {
      id("baccaratPayout").textContent = `${number(amount*BigInt(rules.baccarat.returns[options.side])/10000n)} points returned on a win`;
      id("payoutDescription").textContent = "Player 2× · Banker 1.95× · Tie 9×. Banker includes 5% commission. Player / Banker push on a tie.";
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
      `${game === "keno" ? size + " picked number(s) · payout by matches" : "Slot 0 at the left → slot " + size + " at the right"} · ${info.rtp_percent}% RTP`;
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
      for (const ball of balls) ball.done?.();
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
        const changed = board && (board.rows !== rows || board.values.join(',') !== values.join(','));
        // Resizing rebuilds only the cached pixels, preserving ball positions.
        // A genuinely different paytable finishes old presentations first.
        if (changed) {
          for (const ball of balls) ball.done?.();
          balls = []; resting = null; lastHit = -1;
          cancelFrames();
        }
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
      for (const ball of balls) ball.done?.();
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
          ball.done?.();
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

    function drop(rows, values, result, done) {
      try {
        if (!setBoard(rows, values)) { done?.(); return; }
        const now = performance.now();
        balls.push({...trajectory(result, now), done});
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
        done?.();
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

  // Animation is presentation only: settle and verify first, then reveal the
  // recorded outcome. No fake rolls, re-deals, navigation or wallet mutations.
  const reducedMotion = () => document.hidden || globalThis.matchMedia?.("(prefers-reduced-motion: reduce)").matches;
  function tween(duration, paint) {
    return new Promise(resolve => {
      let frame, timeout, finished = false;
      const start = performance.now();
      const finish = () => {
        if (finished) return;
        finished = true;
        cancelAnimationFrame(frame); clearTimeout(timeout);
        document.removeEventListener("visibilitychange", hidden);
        paint(1); resolve();
      };
      const hidden = () => { if (document.hidden) finish(); };
      const tick = now => {
        const progress = Math.min(1, Math.max(0, (now-start)/duration));
        if (progress === 1) return finish();
        paint(progress); frame = requestAnimationFrame(tick);
      };
      if (reducedMotion() || typeof requestAnimationFrame !== "function") return finish();
      paint(0);
      document.addEventListener("visibilitychange", hidden);
      frame = requestAnimationFrame(tick);
      timeout = setTimeout(finish, duration+120);
    });
  }
  function animateElement(node, frames, duration=380, delay=0) {
    if (!node?.animate || reducedMotion()) return Promise.resolve();
    const animation = node.animate(frames, {duration, delay, easing:"cubic-bezier(.2,.75,.25,1)", fill:"backwards"});
    // Bounded by a wall-clock timer and visibility handling; a suspended RAF
    // can never leave gameplay disabled or display an intermediate outcome.
    return tween(duration+delay, () => {}).finally(() => animation.cancel());
  }
  function dealCard(node, delay=0, flip=false) {
    const task = animateElement(node, flip
      ? [{opacity:.25,transform:"rotateY(90deg)"},{opacity:1,transform:"rotateY(0)"}]
      : [{opacity:0,transform:"translate(24px,-32px) rotate(8deg) scale(.92)"},{opacity:1,transform:"translate(0,0) rotate(0) scale(1)"}], 420, delay);
    cardAnimations.add(task);
    task.finally(() => cardAnimations.delete(task));
  }
  const waitForCards = () => Promise.all([...cardAnimations]);
  function playingCard(card) {
    const node = document.createElement("span");
    node.className = "playing-card";
    node.dataset.card = String(card);
    if (card === null) {
      node.classList.add("is-hidden"); node.textContent = "◆";
      node.setAttribute("aria-label", "Face-down card");
    } else {
      const rank = card % 13+1, suit = Math.floor((card % 52)/13);
      const label = ["","A","2","3","4","5","6","7","8","9","10","J","Q","K"][rank];
      node.textContent = label+["♠","♥","♣","♦"][suit];
      node.classList.toggle("is-red", suit === 1 || suit === 3);
      node.setAttribute("aria-label", `${label} of ${["spades","hearts","clubs","diamonds"][suit]}`);
    }
    return node;
  }
  async function animateBaccarat(result) {
    const revealed = {player:[],banker:[]};
    for (const side of ["player","banker"]) {
      const label = side[0].toUpperCase()+side.slice(1);
      id(`baccarat${label}`).replaceChildren();
      id(`baccarat${label}Total`).textContent = "—";
      id(`baccarat${label}Hand`).classList.remove("is-winner");
    }
    id("baccaratStatus").textContent = "Dealing…";
    const sequence = [["player",0],["banker",0],["player",1],["banker",1]];
    if (result.player.length === 3) sequence.push(["player",2]);
    if (result.banker.length === 3) sequence.push(["banker",2]);
    let shown = 0;
    await tween(sequence.length*190+240, progress => {
      const count = progress === 1 ? sequence.length : Math.min(sequence.length,Math.floor(progress*(sequence.length+1)));
      while (shown < count) {
        const [side,index] = sequence[shown++], card = result[side][index];
        const label = side[0].toUpperCase()+side.slice(1), node = playingCard(card);
        id(`baccarat${label}`).append(node); revealed[side].push(card);
        dealCard(node);
        const total = revealed[side].reduce((sum,c) => sum+(c%13+1 < 10 ? c%13+1 : 0),0)%10;
        id(`baccarat${label}Total`).textContent = total;
      }
    });
    await waitForCards();
    for (const side of ["player","banker"]) {
      const label = side[0].toUpperCase()+side.slice(1);
      id(`baccarat${label}Hand`).classList.toggle("is-winner",result.winner === side || result.winner === "tie");
    }
    id("baccaratStatus").textContent = `${result.winner === "tie" ? "Tie" : result.winner === "player" ? "Player wins" : "Banker wins"}${result.natural ? " · Natural" : ""}`;
  }
  async function showReceipt(receipt) {
    if (!id("gameResult")) return;
    const ticket = ++presentationSequence, r = receipt.result;
    const done = () => {
      if (ticket !== presentationSequence) return;
      delete root.dataset.animating;
      id("gameResult").textContent = isHoldem(receipt)
        ? `${points(receipt.net)} RP net · ${number(r.payout)} returned to wallet`
        : `${points(receipt.net)} RP · ${number(receipt.payout)} returned`;
      if (receipt.game === "keno") id("gameResult").textContent = `${r.hits} matched · `+id("gameResult").textContent;
      id("gameResult").classList.toggle("is-win",receipt.net > 0);
      id("betProof").textContent = `Verified · #${receipt.nonce}`;
      void animateElement(id("gameResult"), [{opacity:0,transform:"translateY(6px)"},{opacity:1,transform:"translateY(0)"}],240);
    };
    if (receipt.game !== game) { done(); return; }
    root.dataset.animating = game;
    id("gameResult").textContent = "Playing…";
    id("betProof").textContent = "";
    if (game === "plinko") {
      id("plinkoResult").textContent = "Dropping…";
      plinko.drop(receipt.options.rows, RedFair.table("plinko",receipt.options.rows,receipt.options.risk,receipt.rules_version), r, () => {
        if (ticket === presentationSequence) id("plinkoResult").textContent = `Slot ${r.slot} · ${multiple(r.multiplier)}`;
        done();
      });
      return; // Multiple committed balls can share one rendering loop.
    }
    if (game === "dice") {
      id("diceRollLabel").textContent = "Rolling…";
      id("diceMarker").hidden = false;
      await tween(750, progress => {
        const roll = r.roll*(1-(1-progress)**3);
        id("diceRoll").textContent = progress === 1 ? (r.roll/100).toFixed(2) : "···";
        id("diceMarker").textContent = progress === 1 ? (r.roll/100).toFixed(2) : "●";
        id("diceMarker").style.left = `calc(${roll/100}% + ${12-24*roll/10000}px)`;
      });
      id("diceRollLabel").textContent = r.won ? "Target matched" : "Outside target";
    } else if (game === "keno") {
      root.querySelectorAll("[data-keno]").forEach(node => node.classList.remove("drawn","matched"));
      let shown = 0;
      await tween(1600, progress => {
        const count = progress === 1 ? 10 : Math.min(10,Math.floor(progress*10));
        while (shown < count) {
          const n = r.drawn[shown++], node = root.querySelector(`[data-keno="${n}"]`);
          node.classList.add("drawn"); node.classList.toggle("matched",receipt.options.picks.includes(n));
          void animateElement(node,[{transform:"scale(.88)"},{transform:"scale(1.08)",offset:.6},{transform:"scale(1)"}],220);
        }
      });
    } else if (game === "limbo") await animateLimbo(r);
    else if (game === "coinflip") await animateCoin(r);
    else if (game === "baccarat") await animateBaccarat(r);
    else if (game === "poker") { renderPoker({...r, round_id:receipt.request_id, wager:receipt.wager}); await waitForCards(); }
    else if (game === "blackjack") { renderBlackjack({...r, nonce:receipt.nonce, round_id:receipt.request_id}); await waitForCards(); }
    done();
  }
  function assertHoldemActions(value, body) {
    if (!isHoldem(value)) return;
    const actions = value.actions || [], saved = body?.player_actions || [];
    const mismatch = saved.some((move,index) => RedFair.canonical(move) !== RedFair.canonical(actions[index]));
    const pendingMismatch = pendingAction?.variant === "texas_holdem" &&
      pendingAction.round_id === (value.round_id || value.request_id) && value.ending !== "weekly_reset" &&
      (value.ended || value.result || actions.length > pendingAction.step) &&
      RedFair.canonical(actions[pendingAction.step]) !== RedFair.canonical(pendingAction.move);
    if (mismatch || pendingMismatch) {
      fatal = true;
      throw Error("Hold’em action history changed. Your saved proof has been retained.");
    }
  }
  async function verifyReceipt(receipt, body) {
    assertHoldemActions(receipt, body);
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
    if (body.game === "poker" && !isHoldem(body) && pendingAction?.game === "poker" &&
        pendingAction.round_id === receipt.request_id && receipt.ending !== "weekly_reset" &&
        RedFair.canonical(receipt.holds) !== RedFair.canonical(pendingAction.holds)) {
      fatal = true;
      throw Error("Poker hold verification failed. Keep your receipt for review.");
    }
    if (body.game === "poker" && body.initial_cards &&
        RedFair.canonical(body.initial_cards) !== RedFair.canonical(receipt.result?.initial)) {
      fatal = true;
      throw Error("Poker initial-card verification failed. Keep your receipt for review.");
    }
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
      await showReceipt(receipt);
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
      if (!receipt && (result.wallet?.blackjack || result.wallet?.poker)) {
        renderWallet(result.wallet);
        await waitForCards();
        message();
        return;
      }
      await verifyReceipt(receipt, body);
      remember(null);
      rememberAction(null);
      await showReceipt(receipt);
      renderWallet(result.wallet);
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
        ? sessionStorage.setItem("rh.gaming.action", JSON.stringify(value))
        : sessionStorage.removeItem("rh.gaming.action");
      sessionStorage.removeItem("rh.blackjack.action");
    } catch {}
  }
  async function animateLimbo(result) {
    const display = id("limboResult"), multiplier = result.multiplier/100;
    display.closest(".limbo-stage").classList.remove("is-win");
    id("limboStatus").textContent = "Climbing…";
    await tween(950, progress => {
      const value = progress === 1 ? multiplier : Math.exp(Math.log(multiplier)*(1-(1-progress)**2));
      display.textContent = value.toLocaleString("en-US",{minimumFractionDigits:2,maximumFractionDigits:2})+"×";
      id("limboTrail").style.transform = `scaleX(${progress})`;
    });
    display.closest(".limbo-stage").classList.toggle("is-win",result.won);
    id("limboStatus").textContent = result.won ? "Target reached" : "Below target";
  }
  async function animateCoin(result) {
    const coin = id("redCoin"), face = result.side === "heads" ? 0 : 180;
    coin.style.transform = `rotateY(${face}deg)`;
    id("coinStatus").textContent = "Flipping…";
    await animateElement(coin,[{transform:"rotateY(0deg) translateY(0)"},
      {transform:`rotateY(${540+face/2}deg) translateY(-28px)`,offset:.5},
      {transform:`rotateY(${1080+face}deg) translateY(0)`}],1050);
    coin.setAttribute("aria-label",result.side === "heads" ? "Heads" : "Tails");
    id("coinStatus").textContent = `${result.side === "heads" ? "Heads" : "Tails"} · ${result.won ? "Correct call" : "Other side"}`;
  }
  holdemTable = globalThis.RedHoldemUI?.create(root, {
    number, playingCard, animateElement, tween, error:message, changed:controls,
    move(move) {
      const hand = wallet?.poker;
      if (!isHoldem(hand) || busy || fatal || pendingAction || !secure || !verifierReady || holdemTable?.isMoving()) return;
      const body = {game:"poker",variant:"texas_holdem",round_id:hand.round_id,step:hand.step,move,action_id:randomHex()};
      rememberAction(body); void submitAction(body);
    },
  });
  function renderPoker(hand) {
    if (!id("pokerCards")) return;
    if (isHoldem(hand) || !hand) {
      if (hand) { id("legacyPokerTable").hidden = true; id("holdemTable").hidden = false; }
      const task = holdemTable?.render(hand);
      if (task) { cardAnimations.add(task); task.finally(() => cardAnimations.delete(task)); }
      return;
    }
    id("legacyPokerTable").hidden = false; id("holdemTable").hidden = true;
    if (pokerRound !== hand.round_id) {
      pokerRound = hand.round_id;
      const saved = pending?.request_id === hand.round_id ? pending.poker_holds : [];
      pokerHolds = new Set(Array.isArray(saved) ? saved.filter(n => Number.isInteger(n) && n >= 0 && n < 5) : []);
    }
    if (hand.ended) pokerHolds = new Set(hand.holds);
    const row = id("pokerCards");
    hand.cards.forEach((card, index) => {
      let button = row.children[index];
      if (button?.dataset.card !== String(card) || button?.dataset.round !== hand.round_id) {
        const rank = card % 13+1, suit = Math.floor(card/13);
        const label = ["","A","2","3","4","5","6","7","8","9","10","J","Q","K"][rank];
        const node = document.createElement("button");node.type = "button";
        node.className = "poker-card"+(suit === 1 || suit === 3 ? " is-red" : "");
        node.dataset.pokerHold = String(index);node.dataset.card = String(card);node.dataset.round = hand.round_id;
        node.setAttribute("aria-label",`${label} of ${["spades","hearts","clubs","diamonds"][suit]}; toggle hold`);
        const value = document.createElement("b");value.textContent = label+["♠","♥","♣","♦"][suit];
        node.append(value,document.createElement("small"));
        node.addEventListener("click",() => {
          if (node.disabled || !wallet?.poker || busy || pendingAction) return;
          pokerHolds.has(index) ? pokerHolds.delete(index) : pokerHolds.add(index);
          savePokerHolds();
        });
        button ? button.replaceWith(node) : row.append(node);
        button = node;
        dealCard(node,index*85,Boolean(hand.ended));
      }
      button.setAttribute("aria-pressed",String(pokerHolds.has(index)));
      button.querySelector("small").textContent = pokerHolds.has(index) ? "HELD" : hand.ended ? "DRAWN" : "HOLD";
    });
    const pokerStatus = () => { id("pokerStatus").textContent = hand.ended
      ? `${rules.poker.legacy_labels[hand.category]} · ${hand.multiplier}× returned`
      : `${pokerHolds.size} held · ${5-pokerHolds.size} to draw`; };
    if (cardAnimations.size) { id("pokerStatus").textContent = "Dealing…"; void waitForCards().then(pokerStatus); }
    else pokerStatus();
    if (!hand.ended) {
      id("gameResult").textContent = "Tap to hold. Then draw.";
      id("betProof").textContent = "Hand saved";
    }
    root.querySelectorAll("[data-hand]").forEach(cell => cell.classList.toggle("is-hit",Boolean(hand.ended && cell.dataset.hand === hand.category)));
    controls();
  }
  function savePokerHolds() {
    if (pending) remember({ ...pending, poker_holds: [...pokerHolds].sort((a,b) => a-b) });
    renderPoker(wallet.poker);
  }
  id("pokerHoldAll")?.addEventListener("click", () => { pokerHolds = new Set([0,1,2,3,4]);savePokerHolds(); });
  id("pokerClear")?.addEventListener("click", () => { pokerHolds.clear();savePokerHolds(); });
  id("pokerDraw")?.addEventListener("click", () => {
    if (busy || fatal || !secure || !verifierReady || pendingAction || !wallet?.poker) return;
    const body = { game:"poker",round_id:wallet.poker.round_id,holds:[...pokerHolds].sort((a,b) => a-b),action_id:randomHex() };
    rememberAction(body);
    void submitAction(body);
  });
  root.querySelectorAll("[data-limbo-target]").forEach(button => button.addEventListener("click", () => {
    if (locked()) return;
    id("limboTarget").value = Number(button.dataset.limboTarget).toFixed(2);
    settingsChanged();
  }));
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
        const node = playingCard(card);
        const fresh = row.dataset.round !== String(hand.round_id || hand.nonce);
        const delay = fresh ? (index*2+(target === "blackjackDealer" ? 1 : 0))*100 : Math.max(0,index-1)*130;
        const flip = old?.dataset.card === "null";
        old ? old.replaceWith(node) : row.append(node);
        dealCard(node,delay,flip);
      });
      while (row.children.length > cards.length) row.lastElementChild.remove();
      row.dataset.round = String(hand.round_id || hand.nonce);
    }
    const totals = () => {
    id("blackjackPlayerTotal").textContent =
      hand.player_total + (hand.player_soft ? " · soft" : "");
    id("blackjackDealerTotal").textContent =
      hand.dealer_total +
      (hand.ended ? (hand.dealer_soft ? " · soft" : "") : " shown");
    id("blackjackStatus").textContent = hand.ended
      ? {
          blackjack: "Blackjack!",
          win: "You win.",
          push: "Push · stake returned",
          lose: "Dealer wins.",
        }[hand.status] || "Hand complete."
      : `${number(hand.wager)} RP in play`;
    };
    if (cardAnimations.size) {
      id("blackjackStatus").textContent = "Dealing…";
      id("blackjackPlayerTotal").textContent = "—";
      id("blackjackDealerTotal").textContent = "—";
      void waitForCards().then(totals);
    } else totals();
  }
  async function submitAction(body) {
    if (busy || fatal || !secure || !verifierReady) return;
    busy = true;
    message();
    controls();
    try {
      const pokerMove = body.game === "poker";
      const result = await api(pokerMove ? "/gaming/api/poker/action" : "/gaming/api/blackjack/action", body);
      if (result.receipt) {
        if (pokerMove && body.variant !== "texas_holdem" && RedFair.canonical(result.receipt.holds) !== RedFair.canonical(body.holds)) {
          fatal = true;
          throw Error("Poker hold verification failed. Your receipt is retained for review.");
        }
        await verifyReceipt(result.receipt, pending || wallet.blackjack?.bet || wallet.poker.bet);
        remember(null);
        rememberAction(null);
        await showReceipt(result.receipt);
        renderWallet(result.wallet);
      } else {
        assertHoldemActions(result.wallet?.poker, pending);
        rememberAction(null);
        renderWallet(result.wallet);
        await waitForCards();
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
    .querySelectorAll("#redWager,#diceChance,#diceSide,#plinkoRows,#limboTarget,[name=risk],[name=coinSide],[name=baccaratSide]")
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
        "Saved · live";
    } catch (error) {
      id("gamingChecked").textContent = "Reconnecting…";
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
  if (pending && !wallet.blackjack && !wallet.poker)
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
        for (let attempt = 0; attempt < 2; attempt++) {
          try {
            const result = await api("/gaming/api/refresh", {
              season: wallet.season.id,
              version: wallet.version,
            });
            renderWallet(result.wallet);
            break;
          } catch (error) {
            // A restart, admin grant or other tab can race this page load.
            // Read the latest wallet and retry once, retaining the server's
            // version check; never blindly overwrite a concurrent wager.
            if (attempt || error.code !== "stale_wallet") throw error;
            renderWallet((await api("/gaming/api/state")).wallet);
          }
        }
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
