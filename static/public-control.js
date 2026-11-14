/* Navigation UX only: never touches provider data, games or user accounts. */
(() => {
  'use strict';
  const toggle = document.getElementById('publicMenuToggle');
  const nav = document.getElementById('publicPrimaryNav');
  const more = document.getElementById('publicMore');
  let lastFocused = null;
  if (!toggle || !nav) return;
  const close = (restoreFocus = false) => {
    nav.dataset.open = 'false';
    toggle.setAttribute('aria-expanded', 'false');
    toggle.setAttribute('aria-label', 'Open site navigation');
    if (more) more.open = false;
    document.documentElement.classList.remove('public-menu-open');
    document.body.classList.remove('public-menu-open');
    if (restoreFocus) (lastFocused || toggle).focus({preventScroll: true});
  };
  const open = () => {
    lastFocused = document.activeElement;
    nav.dataset.open = 'true';
    toggle.setAttribute('aria-expanded', 'true');
    toggle.setAttribute('aria-label', 'Close site navigation');
    document.documentElement.classList.add('public-menu-open');
    document.body.classList.add('public-menu-open');
    nav.querySelector('a,summary,button')?.focus({preventScroll:true});
  };
  toggle.addEventListener('click', () => nav.dataset.open === 'true' ? close() : open());
  nav.addEventListener('click', event => {
    if (event.target.closest('a') && window.matchMedia('(max-width: 980px)').matches) close();
  });
  document.addEventListener('keydown', event => {
    if (event.key === 'Tab' && nav.dataset.open === 'true' && window.matchMedia('(max-width: 980px)').matches) {
      const focusable = [...nav.querySelectorAll('a[href],button:not([disabled]),summary,[tabindex]:not([tabindex="-1"])')].filter(el => !el.hidden && el.offsetParent !== null);
      if (focusable.length) {
        const first = focusable[0], last = focusable[focusable.length - 1];
        if (event.shiftKey && document.activeElement === first) { event.preventDefault(); last.focus(); }
        else if (!event.shiftKey && document.activeElement === last) { event.preventDefault(); first.focus(); }
      }
    }
    if (event.key === 'Escape') {
      if (nav.dataset.open === 'true') close(true);
      else if (more?.open) more.open = false;
    }
  });
  document.addEventListener('click', event => {
    if (more?.open && !more.contains(event.target)) more.open = false;
    if (nav.dataset.open === 'true' && window.matchMedia('(max-width: 980px)').matches && !nav.contains(event.target) && !toggle.contains(event.target)) close();
  });
  window.matchMedia('(min-width: 981px)').addEventListener('change', event => {
    if (event.matches) close();
  });
})();
