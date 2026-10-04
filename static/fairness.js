/* Independent RedPoints v1/v2 verifier. Uses Web Crypto and integer arithmetic.
   No API call, wallet mutation, or provider dependency is involved. */
(() => {
  "use strict";
  const VERSION = "redpoints-v2",
    SCALE = 10000n;
  const SUPPORTED_VERSIONS = ["redpoints-v1", VERSION];
  const PLINKO_TABLES = {
    8: {
      low: [56000, 21000, 11000, 10000, 5000, 10000, 11000, 21000, 56000],
      medium: [130000, 30000, 13000, 7000, 4000, 7000, 13000, 30000, 130000],
      high: [290000, 40000, 15000, 3000, 2000, 3000, 15000, 40000, 290000],
    },
    12: {
      low: [
        100000, 30000, 16000, 14000, 11000, 10000, 5000, 10000, 11000, 14000,
        16000, 30000, 100000,
      ],
      medium: [
        330000, 110000, 40000, 20000, 11000, 6000, 3000, 6000, 11000, 20000,
        40000, 110000, 330000,
      ],
      high: [
        1700000, 240000, 81000, 20000, 7000, 2000, 2000, 2000, 7000, 20000,
        81000, 240000, 1700000,
      ],
    },
    16: {
      low: [
        160000, 90000, 20000, 14000, 14000, 12000, 11000, 10000, 5000, 10000,
        11000, 12000, 14000, 14000, 20000, 90000, 160000,
      ],
      medium: [
        1100000, 410000, 100000, 50000, 30000, 15000, 10000, 5000, 3000, 5000,
        10000, 15000, 30000, 50000, 100000, 410000, 1100000,
      ],
      high: [
        10000000, 1300000, 260000, 90000, 40000, 20000, 2000, 2000, 2000, 2000,
        2000, 20000, 40000, 90000, 260000, 1300000, 10000000,
      ],
    },
  };
  const hex = (bytes) =>
    [...new Uint8Array(bytes)]
      .map((n) => n.toString(16).padStart(2, "0"))
      .join("");
  const bytes = (value) => {
    if (!/^[a-f0-9]{64}$/.test(value)) throw Error("Invalid server seed");
    return new Uint8Array(value.match(/../g).map((n) => parseInt(n, 16)));
  };
  const canonical = (value) =>
    JSON.stringify(value, (_, item) =>
      item && typeof item === "object" && !Array.isArray(item)
        ? Object.fromEntries(
            Object.keys(item)
              .sort()
              .map((key) => [key, item[key]]),
          )
        : item,
    );
  function comb(n, k) {
    let out = 1n;
    for (let i = 1; i <= k; i++) out = (out * BigInt(n - i + 1)) / BigInt(i);
    return out;
  }
  function table(game, size, risk, version = VERSION) {
    if (!SUPPORTED_VERSIONS.includes(version))
      throw Error("Unknown game rules version");
    if (game === "plinko" && version === VERSION) {
      const values = PLINKO_TABLES[size]?.[risk];
      if (!values) throw Error("Unknown Plinko board");
      return [...values];
    }
    const power = { low: 2n, medium: 4n, high: 7n }[risk];
    if (!power) throw Error("Unknown risk level");
    const denom = game === "keno" ? comb(40, 10) : 2n ** BigInt(size);
    const weights = [],
      probs = [];
    for (let i = 0; i <= size; i++) {
      weights.push(
        game === "keno"
          ? BigInt(i) ** power
          : 1n + 2n * BigInt(Math.abs(2 * i - size)) ** power,
      );
      probs.push(
        game === "keno"
          ? comb(size, i) * comb(40 - size, 10 - i)
          : comb(size, i),
      );
    }
    const sum = weights.reduce((n, w, i) => n + w * probs[i], 0n);
    return weights.map((w) => Number((99n * w * denom * SCALE) / (100n * sum)));
  }
  async function draw(seed, receipt) {
    const key = await crypto.subtle.importKey(
      "raw",
      bytes(seed),
      { name: "HMAC", hash: "SHA-256" },
      false,
      ["sign"],
    );
    let block = 0,
      data = new Uint8Array(0),
      pos = 0;
    const context = [
      receipt.rules_version || VERSION,
      receipt.season,
      receipt.game,
      receipt.client_seed,
      receipt.client_salt,
      receipt.nonce,
      receipt.wager,
      receipt.options,
    ];
    return async (size) => {
      const limit = 4294967296 - (4294967296 % size);
      while (true) {
        if (pos >= data.length) {
          data = new Uint8Array(
            await crypto.subtle.sign(
              "HMAC",
              key,
              new TextEncoder().encode(canonical([...context, block++])),
            ),
          );
          pos = 0;
        }
        const n = new DataView(data.buffer, data.byteOffset + pos, 4).getUint32(
          0,
          false,
        );
        pos += 4;
        if (n < limit) return n % size;
      }
    };
  }
  function handTotal(cards) {
    const ranks = cards.map((card) => (card % 13) + 1);
    const base = ranks.reduce((sum, rank) => sum + Math.min(rank, 10), 0);
    const soft = ranks.includes(1) && base + 10 <= 21;
    return [base + (soft ? 10 : 0), soft];
  }
  async function blackjackOutcome(pick, wager, actions) {
    if (!Array.isArray(actions) || actions.length > 32)
      throw Error("Invalid action history");
    const shoe = Array.from({ length: 312 }, (_, i) => i);
    let cursor = 0;
    async function card() {
      const other = cursor + (await pick(shoe.length - cursor));
      [shoe[cursor], shoe[other]] = [shoe[other], shoe[cursor]];
      return shoe[cursor++];
    }
    const player = [await card()],
      dealer = [await card()];
    player.push(await card());
    dealer.push(await card());
    let [pt] = handTotal(player),
      [dt] = handTotal(dealer);
    let ended = pt === 21 || dt === 21;
    const natural = pt === 21 && dt !== 21;
    let stake = BigInt(wager);
    for (let index = 0; index < actions.length; index++) {
      const action = actions[index];
      if (ended || !["hit", "stand", "double"].includes(action))
        throw Error("Illegal Blackjack move");
      if (action === "double") {
        if (index || player.length !== 2)
          throw Error("Double requires first two cards");
        stake = BigInt(wager) * 2n;
      }
      if (action === "hit" || action === "double") player.push(await card());
      [pt] = handTotal(player);
      ended = action === "stand" || action === "double" || pt >= 21;
    }
    if (
      ended &&
      !(player.length === 2 && (pt === 21 || dt === 21)) &&
      pt <= 21
    ) {
      while (handTotal(dealer)[0] < 17) dealer.push(await card());
    }
    const [player_total, player_soft] = handTotal(player),
      [dealer_total, dealer_soft] = handTotal(dealer);
    let status = "playing",
      payout = 0n;
    if (ended) {
      if (dealer.length === 2 && dealer_total === 21)
        status = player.length === 2 && player_total === 21 ? "push" : "lose";
      else if (natural) status = "blackjack";
      else if (player_total > 21) status = "lose";
      else if (dealer_total > 21 || player_total > dealer_total) status = "win";
      else if (player_total === dealer_total) status = "push";
      else status = "lose";
      payout =
        status === "blackjack"
          ? (BigInt(wager) * 5n) / 2n
          : status === "win"
            ? stake * 2n
            : status === "push"
              ? stake
              : 0n;
    }
    if (
      payout > BigInt(Number.MAX_SAFE_INTEGER) ||
      stake > BigInt(Number.MAX_SAFE_INTEGER)
    )
      throw Error("Points overflow");
    return {
      ended,
      player,
      dealer,
      player_total,
      dealer_total,
      player_soft,
      dealer_soft,
      status,
      total_wager: Number(stake),
      payout: Number(payout),
    };
  }

  async function outcome(seed, r) {
    const pick = await draw(seed, r),
      o = r.options;
    if (r.game === "dice") {
      const roll = await pick(10000),
        won =
          o.side === "under"
            ? roll < o.chance * 100
            : roll >= 10000 - o.chance * 100;
      return {
        roll,
        won,
        payout: won ? Number((BigInt(r.wager) * 99n) / BigInt(o.chance)) : 0,
      };
    }
    if (r.game === "keno") {
      const numbers = Array.from({ length: 40 }, (_, i) => i + 1),
        drawn = [];
      for (let i = 0; i < 10; i++) {
        const j = i + (await pick(40 - i));
        [numbers[i], numbers[j]] = [numbers[j], numbers[i]];
        drawn.push(numbers[i]);
      }
      const hits = drawn.filter((n) => o.picks.includes(n)).length,
        multiplier = table(
          "keno",
          o.picks.length,
          o.risk,
          r.rules_version || VERSION,
        )[hits];
      return {
        drawn,
        hits,
        multiplier,
        payout: Number((BigInt(r.wager) * BigInt(multiplier)) / SCALE),
      };
    }
    if (r.game === "blackjack") {
      if (r.rules_version !== VERSION)
        throw Error("Blackjack requires current rules");
      return blackjackOutcome(pick, r.wager, r.actions || []);
    }
    if (r.game !== "plinko") throw Error("Unknown game");
    const path = [];
    for (let i = 0; i < o.rows; i++) path.push(await pick(2));
    const slot = path.reduce((a, b) => a + b, 0),
      multiplier = table("plinko", o.rows, o.risk, r.rules_version || VERSION)[
        slot
      ];
    return {
      path,
      slot,
      multiplier,
      payout: Number((BigInt(r.wager) * BigInt(multiplier)) / SCALE),
    };
  }
  async function verify(r, expectedCommitment) {
    if (
      !r ||
      !SUPPORTED_VERSIONS.includes(r.rules_version) ||
      typeof r.season !== "string" ||
      typeof r.client_seed !== "string" ||
      typeof r.client_salt !== "string" ||
      ![r.nonce, r.wager, r.payout, r.net].every(Number.isSafeInteger) ||
      r.nonce < 0 ||
      r.wager < 1 ||
      !/^[0-9]{1,12}$/.test(r.season) ||
      !/^[a-f0-9]{32}$/.test(r.client_salt) ||
      !/^[A-Za-z0-9 _.\-]{1,64}$/.test(r.client_seed) ||
      !r.options
    )
      return false;
    const o = r.options;
    const keys = {
      dice: ["chance", "side"],
      keno: ["picks", "risk"],
      plinko: ["risk", "rows"],
      blackjack: ["decks"],
    }[r.game];
    if (!keys || canonical(Object.keys(o).sort()) !== canonical(keys))
      return false;
    if (r.game === "dice") {
      if (
        !Number.isInteger(o.chance) ||
        o.chance < 1 ||
        o.chance > 95 ||
        !["under", "over"].includes(o.side)
      )
        return false;
    } else if (r.game === "blackjack") {
      if (
        o.decks !== 6 ||
        r.rules_version !== VERSION ||
        !Array.isArray(r.actions)
      )
        return false;
    } else {
      if (!["low", "medium", "high"].includes(o.risk)) return false;
      if (r.game === "plinko") {
        if (![8, 12, 16].includes(o.rows)) return false;
      } else if (r.game === "keno") {
        if (
          !Array.isArray(o.picks) ||
          !o.picks.length ||
          o.picks.length > 10 ||
          o.picks.some((n) => !Number.isInteger(n) || n < 1 || n > 40) ||
          new Set(o.picks).size !== o.picks.length ||
          o.picks.some((n, i) => i && n < o.picks[i - 1])
        )
          return false;
      } else return false;
    }
    const hash = hex(
      await crypto.subtle.digest("SHA-256", bytes(r.server_seed)),
    );
    if (
      hash !== r.commitment ||
      (expectedCommitment && hash !== expectedCommitment)
    )
      return false;
    const result = await outcome(r.server_seed, r);
    return (
      canonical(result) === canonical(r.result) &&
      r.payout === result.payout &&
      (r.game !== "blackjack" || result.ended) &&
      r.net ===
        result.payout - (r.game === "blackjack" ? result.total_wager : r.wager)
    );
  }
  globalThis.RedFair = {
    VERSION,
    SUPPORTED_VERSIONS,
    canonical,
    table,
    outcome,
    verify,
  };
  if (typeof module !== "undefined") module.exports = globalThis.RedFair;
})();
