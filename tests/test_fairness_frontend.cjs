const { test } = require("node:test");
const assert = require("node:assert/strict");
const vectors = require("./fairness_vectors.json");
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
