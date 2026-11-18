/* Shared placement-movement renderer for Shuffle and EmpireDrop.
 * V25 consumes explicit server-authored movement events. Their expiration is
 * authoritative, so polling, reloads, or tab resumes can never restart them. */
(() => {
  'use strict';
  const DEFAULT_WINDOW_SECONDS = 45;

  function eventFor(row, windowSeconds = DEFAULT_WINDOW_SECONDS) {
    const explicit = row?.movement_event;
    if (explicit && typeof explicit === 'object') {
      const expiresAt = Number(explicit.expires_at || 0);
      const changedAt = Number(explicit.changed_at || 0);
      if (expiresAt > 0 && changedAt > 0) {
        return {
          eventId: String(explicit.event_id || row?.movement_event_id || ''),
          kind: String(explicit.kind || explicit.direction || ''),
          direction: String(explicit.direction || explicit.kind || ''),
          places: Math.max(0, Number(explicit.places || 0)),
          previousRank: explicit.previous_rank == null ? null : Number(explicit.previous_rank),
          currentRank: Number(explicit.current_rank || row?.rank || 0),
          changedAtMs: changedAt * 1000,
          expiresAtMs: expiresAt * 1000,
        };
      }
    }
    const movement = Number(row?.movement || 0);
    const isNew = Boolean(row?.new_entry && !row?.open);
    const changedAt = Number(row?.movement_at || 0);
    const explicitExpires = Number(row?.movement_expires_at || 0);
    const seconds = Number(windowSeconds);
    const expires = explicitExpires > 0
      ? explicitExpires
      : changedAt && Number.isFinite(seconds) && seconds > 0 ? changedAt + seconds : 0;
    if ((!movement && !isNew) || !changedAt || !expires) return null;
    return {
      eventId: String(row?.movement_event_id || `${isNew ? 'new' : movement > 0 ? 'up' : 'down'}:${row?.rank || 0}:${changedAt}`),
      kind: isNew ? 'new' : movement > 0 ? 'up' : 'down',
      direction: isNew ? 'new' : movement > 0 ? 'up' : 'down',
      places: Math.abs(movement),
      previousRank: row?.previous_rank == null ? (movement ? Number(row?.rank || 0) + movement : null) : Number(row.previous_rank),
      currentRank: Number(row?.rank || 0),
      changedAtMs: changedAt * 1000,
      expiresAtMs: expires * 1000,
    };
  }

  function expiresAtMs(row, windowSeconds = DEFAULT_WINDOW_SECONDS) {
    return eventFor(row, windowSeconds)?.expiresAtMs || 0;
  }

  function hostFor(container) {
    if (!container) return null;
    return container.matches?.('.placement, .rank') ? container :
      container.querySelector?.('.placement, .rank') || container;
  }

  function removeTimer(host) {
    if (host?._rankMovementTimer) clearTimeout(host._rankMovementTimer);
    if (host) host._rankMovementTimer = null;
  }

  function render(container, row, options = {}) {
    const host = hostFor(container);
    if (!host?.querySelector || !host?.append) return null;
    let badge = host.querySelector('[data-rank-movement]');
    const event = eventFor(row, options.windowSeconds);
    const current = Number.isFinite(Number(options.nowMs)) ? Number(options.nowMs) : Date.now();
    const remaining = (event?.expiresAtMs || 0) - current;
    if (!event || remaining <= 0) {
      badge?.remove?.();
      removeTimer(host);
      return null;
    }
    const isNew = event.direction === 'new';
    const label = isNew ? 'NEW' : event.direction === 'up' ? `↑${event.places}` : `↓${event.places}`;
    const priorEvent = badge?.dataset?.eventId || '';
    if (!badge) {
      badge = document.createElement('span');
      badge.dataset.rankMovement = '';
      host.append(badge);
    }
    badge.className = `rank-movement ${isNew ? 'is-new' : event.direction === 'up' ? 'is-up' : 'is-down'}`;
    badge.textContent = label;
    badge.dataset.eventId = event.eventId;
    badge.dataset.expiresAt = String(event.expiresAtMs);
    const places = event.places;
    badge.setAttribute('aria-label', isNew
      ? (options.newAriaLabel || 'New in the leaderboard')
      : `${event.direction === 'up' ? 'Up' : 'Down'} ${places} position${places === 1 ? '' : 's'}`);

    // Animate only when the browser encounters a genuinely new server event.
    if (event.eventId && event.eventId !== priorEvent) {
      badge.classList?.add?.('is-entering');
      clearTimeout(badge._rankMovementEntranceTimer);
      badge._rankMovementEntranceTimer = setTimeout(() => badge?.classList?.remove?.('is-entering'), 500);
    }
    removeTimer(host);
    host._rankMovementTimer = setTimeout(() => badge?.remove?.(), Math.max(0, remaining) + 25);
    return badge;
  }

  function expireAll(root, nowMs = Date.now()) {
    root?.querySelectorAll?.('[data-rank-movement][data-expires-at]')?.forEach?.(badge => {
      if (Number(badge.dataset.expiresAt || 0) <= nowMs) badge.remove?.();
    });
  }

  globalThis.RedRankMovement = Object.freeze({DEFAULT_WINDOW_SECONDS, eventFor, expiresAtMs, render, expireAll});
})();
