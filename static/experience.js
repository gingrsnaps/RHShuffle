/* Small shared enhancements. Native links and forms still work without JS. */
(() => {
  "use strict";
  document.documentElement.classList.add("js");
  // Deep links to a recovery form or diagnostics must reveal their ancestors.
  function revealAnchor() {
    let key;
    try {
      key = decodeURIComponent(location.hash.slice(1));
    } catch {
      return;
    }
    const target = document.getElementById(key);
    if (!target) return;
    let opened = false;
    for (let node = target; node; node = node.parentElement) {
      if (node.tagName === "DETAILS" && !node.open) {
        node.open = true;
        opened = true;
      }
    }
    if (opened)
      requestAnimationFrame(() => target.scrollIntoView({ block: "start" }));
  }
  addEventListener("hashchange", revealAnchor);
  revealAnchor();
  const select = document.getElementById("gameSelect");
  select?.addEventListener("change", () => {
    // Values are local template-owned routes, never arbitrary redirect inputs.
    if (
      /^\/gaming(?:\/(dice|keno|plinko|blackjack|limbo|coinflip|poker|baccarat))?$/.test(
        select.value,
      )
    )
      location.assign(select.value);
  });
})();
