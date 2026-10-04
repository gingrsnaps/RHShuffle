/* This verifier never fetches or posts. The seed is already revealed in a receipt. */
document
  .getElementById("receiptVerifier")
  ?.addEventListener("submit", async (event) => {
    event.preventDefault();
    const output = document.getElementById("verifyResult"),
      button = event.currentTarget.querySelector("button");
    button.disabled = true;
    output.textContent = "Verifying…";
    try {
      if (!crypto.subtle)
        throw Error("Use HTTPS or localhost for Web Crypto verification.");
      const raw = document.getElementById("verifyReceipt").value;
      if (raw.length > 2_000_000)
        throw Error("Verify a smaller receipt export (up to 2 MB). ");
      const parsed = JSON.parse(raw),
        list = Array.isArray(parsed) ? parsed : [parsed];
      const expected = document.getElementById("verifyCommitment").value.trim();
      if (!list.length || list.length > 100 || (expected && list.length !== 1))
        throw Error(
          "Provide 1–100 receipts, or one receipt with a saved commitment.",
        );
      let passed = 0;
      for (const receipt of list)
        if (await RedFair.verify(receipt, expected || undefined)) passed++;
      output.textContent =
        passed === list.length
          ? `Verified ${passed} receipt(s): seed hashes, outcomes and payouts match.${expected ? " The earlier commitment matches too." : " Compare against your earlier saved commitment to check pre-commitment."}`
          : `FAILED: ${list.length - passed} receipt(s) did not verify.`;
    } catch (error) {
      output.textContent = "Could not verify: " + error.message;
    } finally {
      button.disabled = false;
    }
  });
