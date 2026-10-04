const { test } = require("node:test");
const assert = require("node:assert/strict");
const vectors = [
  ...require("./fairness_vectors.json"),
  ...require("./fairness_v2_vectors.json"),
  ...require("./fairness_v3_vectors.json"),
];
const fair = require("../static/fairness.js");
test("independent browser verifier reproduces every published Python reference receipt", async () => {
  for (const receipt of vectors) {
    assert.equal(
      await fair.verify(receipt, receipt.commitment),
      true,
      receipt.request_id,
    );
    assert.equal(
      await fair.verify(
        { ...receipt, payout: receipt.payout + 1 },
        receipt.commitment,
      ),
      false,
    );
    assert.equal(await fair.verify(receipt, "0".repeat(64)), false);
  }
});
test("browser and backend use identical payout units and committed paths", async () => {
  for (const receipt of vectors) {
    const result = await fair.outcome(receipt.server_seed, receipt);
    assert.deepEqual(result, receipt.result);
  }
});

test("v2 edge payouts and doubled Blackjack stake are verified exactly", async () => {
  assert.equal(Math.max(...fair.table("plinko", 16, "high")), 10000000);
  const edge = vectors.find(
    (r) =>
      r.rules_version === "redpoints-v2" &&
      r.game === "plinko" &&
      r.result.multiplier === 10000000,
  );
  assert.equal(edge.payout, edge.wager * 1000);
  const doubled = vectors.find(
    (r) => r.game === "blackjack" && r.actions.includes("double"),
  );
  assert.equal(doubled.result.total_wager, doubled.wager * 2);
  assert.equal(doubled.net, doubled.payout - doubled.result.total_wager);
  assert.equal(await fair.verify(doubled), true);
  assert.equal(await fair.verify({ ...doubled, actions: ["stand"] }), false);
});
