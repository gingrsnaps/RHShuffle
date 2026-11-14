/* RedHunllef admin control center — navigation and presentation only.
 * No provider requests, credential handling, storage writes or new game logic.
 * Existing backend endpoints and CSRF-protected forms remain authoritative. */
(() => {
  'use strict';
  if (document.body.dataset.page !== 'admin') return;
  const get = (name) => document.getElementById(name);
  const app = get('adminApp');
  const menuButton = get('adminOpenMenu');
  const veil = get('adminVeil');
  const dialog = get('adminCommandDialog');
  const search = get('adminCommandSearch');
  const commandLinks = [...document.querySelectorAll('[data-command-link]')];
  let lastMenuFocus = null;
  const sidebar = get('adminSidebar');
  function syncSidebarAccessibility() {
    // Closed off-canvas navigation must not trap keyboard focus.
    if (sidebar) sidebar.inert = window.matchMedia('(max-width: 790px)').matches && app?.dataset.menuOpen !== 'true';
  }

  // Sidebar is a real drawer on mobile and an always-visible rail on desktop.
  function mobileMenu(open) {
    if (!app) return;
    app.dataset.menuOpen = String(open);
    menuButton?.setAttribute('aria-expanded', String(open));
    if (veil) veil.hidden = !open;
    syncSidebarAccessibility();
    document.documentElement.classList.toggle('admin-menu-open', open);
    document.body.classList.toggle('admin-menu-open', open);
    if (open) {
      lastMenuFocus = document.activeElement;
      get('adminCloseMenu')?.focus();
    } else if (lastMenuFocus) {
      lastMenuFocus.focus({preventScroll:true});
      lastMenuFocus = null;
    }
  }
  menuButton?.addEventListener('click', () => mobileMenu(true));
  get('adminCloseMenu')?.addEventListener('click', () => mobileMenu(false));
  veil?.addEventListener('click', () => mobileMenu(false));
  sidebar?.addEventListener('click', event => {
    if (event.target.closest('a') && window.matchMedia('(max-width: 790px)').matches) mobileMenu(false);
  });
  window.matchMedia('(min-width: 791px)').addEventListener('change', event => {
    if (event.matches) mobileMenu(false);
    syncSidebarAccessibility();
  });
  syncSidebarAccessibility();

  function filterCommands() {
    const needle = (search?.value || '').trim().toLocaleLowerCase();
    let count = 0;
    for (const link of commandLinks) {
      link.hidden = !link.dataset.search.includes(needle);
      if (!link.hidden) count++;
    }
    if (get('adminCommandEmpty')) get('adminCommandEmpty').hidden = count !== 0;
  }
  function openCommands() {
    if (!dialog || typeof dialog.showModal !== 'function') return;
    mobileMenu(false);
    if (!dialog.open) dialog.showModal();
    search.value = '';
    filterCommands();
    search.focus();
  }
  get('adminCommandOpen')?.addEventListener('click', openCommands);
  get('adminCommandClose')?.addEventListener('click', () => dialog?.close());
  dialog?.addEventListener('click', event => {
    // Clicking the backdrop closes the dialog; clicking its contents does not.
    if (event.target === dialog) dialog.close();
  });
  search?.addEventListener('input', filterCommands);
  search?.addEventListener('keydown', event => {
    if (event.key === 'Enter') {
      const first = commandLinks.find(link => !link.hidden);
      if (first) { event.preventDefault(); first.click(); }
    }
  });
  document.addEventListener('keydown', event => {
    if (event.key === 'Tab' && app?.dataset.menuOpen === 'true' && window.matchMedia('(max-width: 790px)').matches) {
      const focusable = [...sidebar.querySelectorAll('a[href],button:not([disabled]),[tabindex]:not([tabindex="-1"])')].filter(el => !el.hidden && el.offsetParent !== null);
      if (focusable.length) {
        const first = focusable[0], last = focusable[focusable.length - 1];
        if (event.shiftKey && document.activeElement === first) { event.preventDefault(); last.focus(); }
        else if (!event.shiftKey && document.activeElement === last) { event.preventDefault(); first.focus(); }
      }
    }
    if ((event.ctrlKey || event.metaKey) && event.key.toLocaleLowerCase() === 'k') {
      event.preventDefault();
      if (dialog?.open) dialog.close(); else openCommands();
    }
    if (event.key === 'Escape') mobileMenu(false);
  });

  // Lightweight dirty-state chip. The existing shared app controller protects
  // unsaved drafts on navigation; this is only a human-readable indicator.
  const saveStatus = get('adminSaveStatus');
  const dirtyForms = [...document.querySelectorAll('form[data-dirty]')];
  const snapshots = new Map();
  const snapshot = form => JSON.stringify([...new FormData(form)].map(([key,val]) =>
    [key, typeof val === 'string' ? val : [val.name,val.size,val.lastModified]]));
  for (const form of dirtyForms) snapshots.set(form, snapshot(form));
  function showSaveStatus() {
    if (!saveStatus) return;
    const modified = dirtyForms.some(form => snapshot(form) !== snapshots.get(form));
    const needsReview = saveStatus.dataset.validation === 'true';
    saveStatus.dataset.state = modified ? 'dirty' : needsReview ? 'warning' : 'saved';
    saveStatus.textContent = modified ? '● Unsaved changes' :
      needsReview ? '● Review required — not saved' : '✓ All changes saved';
  }
  for (const form of dirtyForms) {
    form.addEventListener('input', showSaveStatus);
    form.addEventListener('change', showSaveStatus);
    form.addEventListener('reset', () => queueMicrotask(showSaveStatus));
  }
  document.addEventListener('admin:saved', event => {
    const form = event.detail?.form;
    if (form && snapshots.has(form)) snapshots.set(form, snapshot(form));
    showSaveStatus();
  });
  showSaveStatus();

  // The existing minute-long admin status response is the only source of live
  // state. No parallel polling requests are introduced by the new sidebar.
  document.addEventListener('admin:status', event => {
    const providers = event.detail?.providers;
    if (!providers) return;
    for (const name of ['shuffle','empiredrop']) {
      const source = providers[name];
      const indicator = document.querySelector(`[data-provider-indicator="${name}"]`);
      if (!indicator || !source) continue;
      indicator.dataset.state = source.state || 'unknown';
      const label = indicator.closest('.admin-side-provider')?.querySelector('small');
      if (label) label.textContent = source.status || 'Checking';
    }
  });

  // The legacy EmpireDrop page bundled credentials, recovery and API contract
  // settings between everyday controls. Collapse these under one titled drawer.
  // Keep the original DOM nodes/forms so IDs, CSRF actions, and event listeners
  // remain stable. Without JS the original sections remain fully accessible.
  if (document.body.dataset.adminTab === 'empiredrop') {
    const selectors = ['#empireBackupTitle','#empireKeysTitle','#empireContractTitle'];
    const targets = selectors.map(selector => document.querySelector(selector)?.closest('section')).filter(Boolean);
    if (targets.length) {
      const details = document.createElement('details');
      details.className = 'admin-advanced-fold';
      details.id = 'empireAdvanced';
      const summary = document.createElement('summary');
      summary.innerHTML = '<span>Advanced settings &amp; recovery</span><small>Backups, credentials and compatibility controls</small>';
      targets[0].before(details);
      details.append(summary);
      for (const target of targets) details.append(target);
      function honorHash() {
        let id = '';
        try { id = decodeURIComponent(location.hash.slice(1)); } catch { return; }
        const target = get(id);
        if (target && details.contains(target)) details.open = true;
      }
      honorHash();
      window.addEventListener('hashchange', honorHash);
      // On failed save, show the relevant advanced form and its error.
      if (document.querySelector('[role="alert"]') && location.hash.startsWith('#empire')) details.open = true;
    }
  }

  // On the Operations screen, lead with the logs. The health cards remain in
  // the same section beneath them for deeper investigation.
  if (document.body.dataset.adminTab === 'activity') {
    const operations = get('adminOperations');
    const host = get('adminOperationsHost');
    if (operations && host) {
      host.append(operations);
      operations.open = true;
      operations.setAttribute('aria-label','Recent operational activity');
    }
  }
  // Native details elements own their focus and state. When a quick link lands
  // inside a closed details section, reveal only the relevant ancestor panels.
  function revealAnchor() {
    let id = '';
    try { id = decodeURIComponent(location.hash.slice(1)); } catch { return; }
    const target = id ? get(id) : null;
    if (!target) return;
    for (let ancestor = target.parentElement; ancestor; ancestor = ancestor.parentElement) {
      if (ancestor.tagName === 'DETAILS') ancestor.open = true;
    }
  }
  function revealServerFocus() {
    const focus = document.querySelector('.admin-workspace')?.dataset.focus || '';
    if (!focus) return;
    const target = get(focus);
    if (!target) return;
    for (let ancestor = target.parentElement; ancestor; ancestor = ancestor.parentElement) {
      if (ancestor.tagName === 'DETAILS') ancestor.open = true;
    }
    queueMicrotask(() => target.scrollIntoView({block:'start'}));
  }
  revealAnchor();
  revealServerFocus();
  window.addEventListener('hashchange', revealAnchor);
  // Hidden required inputs must be visible when native form validation runs.
  // Otherwise browsers can reject the save with an un-focusable control.
  document.addEventListener('invalid', event => {
    let parent = event.target?.parentElement;
    while (parent) {
      if (parent.tagName === 'DETAILS') parent.open = true;
      parent = parent.parentElement;
    }
  }, true);
})();
