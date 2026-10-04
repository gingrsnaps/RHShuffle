/* Independent RedPoints v1 verifier. Uses Web Crypto and integer arithmetic.
   No API call, wallet mutation, or provider dependency is involved. */
(() => {
  "use strict";
  const VERSION = "redpoints-v1",
    SCALE = 10000n;
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
  function table(game, size, risk) {
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
      VERSION,
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
        multiplier = table("keno", o.picks.length, o.risk)[hits];
      return {
        drawn,
        hits,
        multiplier,
        payout: Number((BigInt(r.wager) * BigInt(multiplier)) / SCALE),
      };
    }
    if (r.game !== "plinko") throw Error("Unknown game");
    const path = [];
    for (let i = 0; i < o.rows; i++) path.push(await pick(2));
    const slot = path.reduce((a, b) => a + b, 0),
      multiplier = table("plinko", o.rows, o.risk)[slot];
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
      r.rules_version !== VERSION ||
      typeof r.season !== "string" ||
      typeof r.client_seed !== "string" ||
      typeof r.client_salt !== "string" ||
      ![r.nonce, r.wager, r.payout, r.net].every(Number.isSafeInteger) ||
      r.nonce < 0 ||
      r.wager < 1 ||
      r.wager > 10000 ||
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
      r.net === result.payout - r.wager
    );
  }
  globalThis.RedFair = { VERSION, canonical, table, outcome, verify };
  if (typeof module !== "undefined") module.exports = globalThis.RedFair;
})();
