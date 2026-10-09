/* Keep a rejected form and its selected files intact. Native forms still work.
   Preview/review workflows remain native; only a committed write redirects. */
(() => {
  "use strict";
  if (document.body.dataset.page !== "admin") return;
  const receipt = document.querySelector(".saved-receipt");
  if (receipt) {
    for (
      let parent = receipt.parentElement;
      parent;
      parent = parent.parentElement
    )
      if (parent.tagName === "DETAILS") parent.open = true;
    receipt.focus({ preventScroll: true });
    receipt.scrollIntoView?.({ block: "center" });
  }
  for (const form of document.querySelectorAll('form[method="post"]')) {
    const endpoint = form.getAttribute("action");
    if (
      ![
        "/admin/action",
        "/admin/boss/action",
        "/admin/history/refresh",
      ].includes(endpoint) ||
      form.hasAttribute("data-refresh")
    )
      continue;
    const action = form.elements.namedItem("action")?.value;
    if (["save_race", "preview_restore"].includes(action)) continue;
    let busy = false;
    form.addEventListener("submit", async (event) => {
      if (event.defaultPrevented) return; // Respect the existing confirmation.
      event.preventDefault();
      if (busy) return;
      const data = new FormData(form);
      const button =
        event.submitter || form.querySelector('button[type="submit"]');
      if (button?.name) data.set(button.name, button.value);
      const label = button?.textContent.trim() || "Save change";
      let feedback = form.querySelector("[data-form-feedback]");
      if (!feedback) {
        feedback = document.createElement("p");
        feedback.dataset.formFeedback = "";
        feedback.setAttribute("role", "status");
        feedback.tabIndex = -1;
        form.append(feedback);
      }
      feedback.className = "form-feedback notice";
      feedback.textContent = label + ": saving…";
      busy = true;
      const controls = [...form.querySelectorAll('button[type="submit"]')];
      const prior = controls.map((node) => node.disabled);
      controls.forEach((node) => {
        node.disabled = true;
      });
      const controller = new AbortController();
      const timeout = setTimeout(() => controller.abort(), 15000);
      try {
        const response = await fetch(endpoint, {
          method: "POST",
          body: data,
          credentials: "same-origin",
          headers: { Accept: "application/json" },
          signal: controller.signal,
        });
        if (!response.headers.get("content-type")?.includes("application/json"))
          throw Error(
            "Unexpected response. Check the installed release before retrying.",
          );
        const result = await response.json();
        if (!response.ok || !result.ok)
          throw Error(
            (result.error || "The server did not confirm this change.") +
              (result.request_id ? ` Reference: ${result.request_id}.` : ""),
          );
        const next = new URL(result.redirect, location.origin);
        if (
          next.origin !== location.origin ||
          !["/admin", "/admin/login"].includes(next.pathname)
        )
          throw Error(
            "Save confirmed, but the return link is invalid. Reload to verify the saved value.",
          );
        feedback.className = "form-feedback notice success";
        feedback.textContent = result.message;
        document.dispatchEvent(
          new CustomEvent("admin:saved", { detail: { form } }),
        );
        if (next.pathname === location.pathname && next.search === location.search) {
          // A fragment-only navigation does not request a new document. Reload
          // after a confirmed save so receipts and edit revisions are current.
          history.replaceState(history.state, "", next.href);
          location.reload();
        } else {
          location.assign(next.href);
        }
      } catch (error) {
        feedback.className = "form-feedback notice warning";
        feedback.textContent =
          label +
          ": " +
          (error.name === "AbortError"
            ? "No confirmation received. Your draft is kept; verify the saved value before retrying."
            : error.message);
        feedback.focus({ preventScroll: true });
      } finally {
        clearTimeout(timeout);
        busy = false;
        controls.forEach((node, index) => {
          node.disabled = prior[index];
        });
      }
    });
  }
})();
