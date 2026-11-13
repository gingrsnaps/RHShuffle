/* Navigation UX only: never touches provider data, games or user accounts. */
(() => {
  'use strict';
  const toggle = document.getElementById('publicMenuToggle');
  const nav = document.getElementById('publicPrimaryNav');
  const more = document.getElementById('publicMore');
  if (!toggle || !nav) return;
  const close = (restoreFocus = false) => {
    nav.dataset.open = 'false';
    toggle.setAttribute('aria-expanded', 'false');
    toggle.setAttribute('aria-label', 'Open site navigation');
    if (more) more.open = false;
    if (restoreFocus) toggle.focus({preventScroll: true});
  };
  const open = () => {
    nav.dataset.open = 'true';
    toggle.setAttribute('aria-expanded', 'true');
    toggle.setAttribute('aria-label', 'Close site navigation');
  };
  toggle.addEventListener('click', () => nav.dataset.open === 'true' ? close() : open());
  nav.addEventListener('click', event => {
    if (event.target.closest('a') && window.matchMedia('(max-width: 980px)').matches) close();
  });
  document.addEventListener('keydown', event => {
    if (event.key === 'Escape') {
      if (nav.dataset.open === 'true') close(true);
      else if (more?.open) more.open = false;
    }
  });
  document.addEventListener('click', event => {
    if (more?.open && !more.contains(event.target)) more.open = false;
  });
  window.matchMedia('(min-width: 981px)').addEventListener('change', event => {
    if (event.matches) close();
  });
})();
