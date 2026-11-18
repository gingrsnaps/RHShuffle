/* One placement-movement renderer shared by Shuffle and EmpireDrop.
 * Expiration is server-authored when available, so polling/reloads never restart it. */
(() => {
  'use strict';
  const DEFAULT_WINDOW_SECONDS = 45;

  function expiresAtMs(row, windowSeconds = DEFAULT_WINDOW_SECONDS) {
    const explicit = Number(row?.movement_expires_at || 0) * 1000;
    if (Number.isFinite(explicit) && explicit > 0) return explicit;
    const eventAt = Number(row?.movement_at || 0) * 1000;
    const seconds = Number(windowSeconds);
    return eventAt && Number.isFinite(seconds) && seconds > 0 ? eventAt + seconds * 1000 : 0;
  }

  function hostFor(container) {
    if (!container) return null;
    return container.querySelector?.('.placement, .rank') || container;
  }

  function removeTimer(host) {
    if (host?._rankMovementTimer) clearTimeout(host._rankMovementTimer);
    if (host) host._rankMovementTimer = null;
  }

  function render(container, row, options = {}) {
    const host = hostFor(container);
    if (!host?.querySelector || !host?.append) return null;
    let badge = host.querySelector('[data-rank-movement]');
    const movement = Number(row?.movement || 0);
    const isNew = Boolean(row?.new_entry && !row?.open);
    const nowMs = Number(options.nowMs);
    const current = Number.isFinite(nowMs) ? nowMs : Date.now();
    const expiresAt = expiresAtMs(row, options.windowSeconds);
    const remaining = expiresAt - current;
    const label = isNew ? 'NEW' : movement > 0 ? `↑${movement}` : movement < 0 ? `↓${Math.abs(movement)}` : '';
    if (!label || !expiresAt || remaining <= 0) {
      badge?.remove?.();
      removeTimer(host);
      return null;
    }
    if (!badge) {
      badge = document.createElement('span');
      badge.dataset.rankMovement = '';
      host.append(badge);
    }
    badge.className = `rank-movement ${isNew ? 'is-new' : movement > 0 ? 'is-up' : 'is-down'}`;
    badge.textContent = label;
    badge.dataset.expiresAt = String(expiresAt);
    const places = Math.abs(movement);
    badge.setAttribute('aria-label', isNew
      ? (options.newAriaLabel || 'New in the leaderboard')
      : `${movement > 0 ? 'Up' : 'Down'} ${places} position${places === 1 ? '' : 's'}`);
    removeTimer(host);
    host._rankMovementTimer = setTimeout(() => badge?.remove?.(), Math.max(0, remaining) + 25);
    return badge;
  }

  function expireAll(root, nowMs = Date.now()) {
    root?.querySelectorAll?.('[data-rank-movement][data-expires-at]')?.forEach?.(badge => {
      if (Number(badge.dataset.expiresAt || 0) <= nowMs) badge.remove?.();
    });
  }

  globalThis.RedRankMovement = Object.freeze({DEFAULT_WINDOW_SECONDS, expiresAtMs, render, expireAll});
})();
