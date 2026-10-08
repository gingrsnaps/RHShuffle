/* Small shared enhancements. Native links and forms still work without JS. */
(() => {
  'use strict';
  document.documentElement.classList.add('js');
  const select = document.getElementById('gameSelect');
  select?.addEventListener('change', () => {
    // Values are local template-owned routes, never arbitrary redirect inputs.
    if (/^\/gaming(?:\/(dice|keno|plinko|blackjack|limbo|coinflip|poker|baccarat))?$/.test(select.value)) location.assign(select.value);
  });
})();
