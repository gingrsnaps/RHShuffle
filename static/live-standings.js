/* V25 live standings channel.
 * Polls only RedHunllef's own lightweight endpoint every five seconds. It never
 * calls Shuffle or EmpireDrop directly and never reloads/navigates the page. */
(() => {
  'use strict';
  if (document.body?.dataset?.page !== 'public') return;

  const SYNC_MS = 5000;
  const id = name => document.getElementById(name);
  let timer = null;
  let busy = false;
  let again = false;
  let stopped = false;
  let etag = '';
  let serverOffsetMs = 0;
  let runtimeId = '';
  let lastSyncLocalMs = 0;
  let movementWindowSeconds = 45;
  const sequence = {shuffle:-1, empiredrop:-1};
  const movementSequence = {shuffle:-1, empiredrop:-1};

  const nowServerMs = () => Date.now() + serverOffsetMs;
  const money = value => new Intl.NumberFormat('en-US', {style:'currency', currency:'USD'}).format(Number(value) || 0);
  const padRank = value => String(Number(value) || 0).padStart(2, '0');

  function flash(node) {
    if (!node) return;
    node.classList.remove('live-value-changed');
    // Force a new animation only for a real value change.
    void node.offsetWidth;
    node.classList.add('live-value-changed');
    clearTimeout(node._liveValueTimer);
    node._liveValueTimer = setTimeout(() => node.classList.remove('live-value-changed'), 1050);
  }

  function setLiveText(node, value, animate = true) {
    if (!node) return false;
    const next = String(value ?? '');
    const before = node.textContent;
    const initialized = node.dataset.liveInitialized === '1';
    if (before !== next) {
      node.textContent = next;
      if (initialized && animate) flash(node);
    }
    node.dataset.liveInitialized = '1';
    return before !== next;
  }

  function setPlace(host, rank, row, newLabel) {
    if (!host) return;
    const number = host.querySelector('[data-place-number]');
    setLiveText(number, padRank(rank), false);
    globalThis.RedRankMovement?.render(host, row, {
      nowMs: nowServerMs(),
      windowSeconds: movementWindowSeconds,
      newAriaLabel: newLabel,
    });
  }

  function shuffleRows(board) {
    if (Array.isArray(board?.top15) && board.top15.length === 15) return board.top15;
    const rows = Array.isArray(board?.rows) ? board.rows : [];
    return Array.from({length:15}, (_, index) => rows.find(row => Number(row.rank) === index + 1) || {
      rank:index + 1, username:'Open position', wager:'$0.00', open:true,
      movement:null, new_entry:false, movement_event:null,
    });
  }

  function renderShuffle(board, force = false) {
    if (!board) return;
    const nextSequence = Number(board.standings_sequence || 0);
    const nextMovement = Number(board.movement_sequence || 0);
    if (!force && nextSequence < sequence.shuffle) return;
    if (!force && nextSequence === sequence.shuffle && nextMovement === movementSequence.shuffle) return;
    sequence.shuffle = Math.max(sequence.shuffle, nextSequence);
    movementSequence.shuffle = Math.max(movementSequence.shuffle, nextMovement);
    const rows = shuffleRows(board);
    for (let position=1; position<=15; position += 1) {
      const row = rows[position-1] || {rank:position, username:'Open position', wager:'$0.00', open:true};
      document.querySelectorAll(`#shuffleBoard [data-rank="${position}"]`).forEach(slot => {
        const name = slot.querySelector('[data-name]');
        const wager = slot.querySelector('[data-wager]');
        const prize = slot.querySelector('[data-prize]');
        const place = slot.querySelector('.placement, .rank');
        setLiveText(name, row.open ? 'Open position' : row.username);
        setLiveText(wager, row.open ? '$0.00' : row.wager);
        setLiveText(prize, money(board.prizes?.[String(position)] ?? board.prizes?.[position] ?? 0));
        slot.classList.toggle('is-open-position', Boolean(row.open));
        setPlace(place, row.rank ?? position, row, 'New in the Top 15');
      });
    }
  }

  function renderEmpire(board, force = false) {
    if (!board || !Array.isArray(board.rows)) return;
    const nextSequence = Number(board.standings_sequence || 0);
    const nextMovement = Number(board.movement_sequence || 0);
    if (!force && nextSequence < sequence.empiredrop) return;
    if (!force && nextSequence === sequence.empiredrop && nextMovement === movementSequence.empiredrop) return;
    sequence.empiredrop = Math.max(sequence.empiredrop, nextSequence);
    movementSequence.empiredrop = Math.max(movementSequence.empiredrop, nextMovement);
    const rows = board.rows.slice(0, 10);
    const providerLimit = Number(board.race_meta?.ranks_limit);
    const displayLimit = Number.isInteger(providerLimit) && providerLimit > 0 ? Math.min(10, providerLimit) : 10;
    const configured = board.prizes?.enabled === true;

    for (let position=1; position<=10; position += 1) {
      const row = rows[position-1];
      const unreported = !row && position > displayLimit;
      const name = document.querySelector(position <= 3 ? `[data-empire-name="${position}"]` : `[data-empire-row-name="${position}"]`);
      const wager = document.querySelector(position <= 3 ? `[data-empire-wager="${position}"]` : `[data-empire-row-wager="${position}"]`);
      const prize = document.querySelector(position <= 3 ? `[data-empire-prize="${position}"]` : `[data-empire-row-prize="${position}"]`);
      const place = id('empireBoard')?.querySelector(`[data-empire-place="${position}"]`);
      setLiveText(name, row?.username || (unreported ? 'Unavailable' : 'Open position'));
      setLiveText(wager, row?.wager || '—');
      if (place) setPlace(place, row?.rank ?? position, row, 'New in the Top 10');
      if (prize) {
        const rankKey = String(row?.rank ?? position);
        const nextPrize = row?.prize && row.prize !== '—'
          ? row.prize
          : configured ? (board.prizes?.formatted?.[rankKey] || '—') : 'To be announced';
        setLiveText(prize, nextPrize);
        prize.classList.toggle('is-unannounced', !(Boolean(row?.prize && row.prize !== '—') || configured));
      }
    }
    const coverage = id('empireRankingCoverage');
    if (coverage) {
      const value = providerLimit > 0 && providerLimit < 10
        ? `EmpireDrop currently exposes ${providerLimit} official positions for this race.`
        : rows.length < 10 ? 'Open positions will appear when activity is reported.' : '';
      setLiveText(coverage, value, false);
      coverage.hidden = !value;
    }
    const message = id('empireMessage');
    if (message) {
      const text = rows.length ? '' : (board.updated_at ? 'Showing the most recent standings.' : 'Standings are temporarily unavailable.');
      setLiveText(message, text, false);
      message.hidden = rows.length > 0;
    }
  }

  function syncLabel(provider) {
    const node = id(provider === 'shuffle' ? 'shuffleLiveSyncStatus' : 'empireLiveSyncStatus');
    if (!node) return;
    const seconds = lastSyncLocalMs ? Math.max(0, Math.floor((Date.now() - lastSyncLocalMs) / 1000)) : null;
    const text = seconds == null ? 'Live standings · connecting' : `Live standings · synced ${seconds}s ago`;
    node.lastChild ? node.lastChild.textContent = text : node.append(document.createTextNode(text));
    node.classList.toggle('is-delayed', seconds != null && seconds > 15);
  }

  function refreshSyncLabels() {
    syncLabel('shuffle');
    syncLabel('empiredrop');
    globalThis.RedRankMovement?.expireAll(document, nowServerMs());
  }

  function apply(payload, force = false) {
    if (!payload) return;
    if (Number.isFinite(Number(payload.server_time))) serverOffsetMs = Number(payload.server_time) * 1000 - Date.now();
    movementWindowSeconds = Number(payload.movement_window_seconds || 45);
    const incomingRuntime = String(payload.runtime_id || '');
    if (incomingRuntime && runtimeId && incomingRuntime !== runtimeId) {
      sequence.shuffle = sequence.empiredrop = -1;
      movementSequence.shuffle = movementSequence.empiredrop = -1;
      etag = '';
      force = true;
    }
    if (incomingRuntime) runtimeId = incomingRuntime;
    renderShuffle(payload.shuffle, force);
    renderEmpire(payload.empiredrop, force);
    lastSyncLocalMs = Date.now();
    refreshSyncLabels();
    document.dispatchEvent(new CustomEvent('live-standings:applied', {detail:payload}));
  }

  function bootstrapPayload() {
    try {
      const boot = JSON.parse(document.body.dataset.bootstrap || '{}');
      return {
        release: boot.release,
        runtime_id: boot.runtime_id,
        movement_window_seconds: boot.movement_window_seconds || 45,
        server_time: boot.server_time,
        shuffle: {
          standings_revision: boot.shuffle_revision || '',
          standings_sequence: boot.shuffle_sequence || 0,
          movement_sequence: boot.shuffle_movement_sequence || 0,
          movement_count: boot.shuffle_movement_count || 0,
          changed_at: boot.shuffle_changed_at || 0,
          updated_at: boot.provider_timing?.shuffle?.updated_at || boot.freshness?.updated_at || 0,
          next_check_at: boot.provider_timing?.shuffle?.next_check || 0,
          refresh_interval: boot.provider_timing?.shuffle?.refresh_interval || 90,
          top15: boot.top15 || [],
          prizes: boot.site?.prizes || {},
          total_prize: boot.site?.total_prize || '$0.00',
        },
        empiredrop: boot.empiredrop || {},
      };
    } catch {
      return null;
    }
  }

  async function poll() {
    if (stopped || document.hidden) return;
    if (busy) { again = true; return; }
    busy = true;
    clearTimeout(timer);
    try {
      const headers = {'Accept':'application/json'};
      if (etag) headers['If-None-Match'] = etag;
      const response = await fetch('/public-standings', {
        credentials:'same-origin', cache:'no-store', headers,
      });
      const clock = Number(response.headers?.get('X-Server-Time'));
      if (Number.isFinite(clock)) serverOffsetMs = clock * 1000 - Date.now();
      if (response.status === 304) {
        lastSyncLocalMs = Date.now();
        refreshSyncLabels();
      } else {
        if (!response.ok || !response.headers.get('content-type')?.includes('application/json')) throw new Error(`HTTP ${response.status}`);
        const payload = await response.json();
        payload.server_time = Number.isFinite(clock) ? clock : payload.server_time;
        etag = response.headers.get('ETag') || '';
        apply(payload);
      }
    } catch {
      for (const name of ['shuffleLiveSyncStatus','empireLiveSyncStatus']) {
        const node = id(name);
        if (node) node.classList.add('is-delayed');
      }
    } finally {
      busy = false;
      const delay = again ? 100 : SYNC_MS;
      again = false;
      if (!stopped && !document.hidden) timer = setTimeout(poll, delay);
    }
  }

  const bootstrap = bootstrapPayload();
  if (bootstrap) apply(bootstrap, true);
  const labelTimer = setInterval(refreshSyncLabels, 1000);
  timer = setTimeout(poll, 50);
  document.addEventListener('visibilitychange', () => {
    clearTimeout(timer);
    globalThis.RedRankMovement?.expireAll(document, nowServerMs());
    if (!document.hidden) timer = setTimeout(poll, 50);
  });
  window.addEventListener('focus', () => {
    if (!document.hidden) { clearTimeout(timer); timer = setTimeout(poll, 50); }
  });
  window.addEventListener('pageshow', () => {
    globalThis.RedRankMovement?.expireAll(document, nowServerMs());
    if (!document.hidden) { clearTimeout(timer); timer = setTimeout(poll, 50); }
  });
  window.addEventListener('pagehide', () => {
    stopped = true;
    clearTimeout(timer);
    clearInterval(labelTimer);
  }, {once:true});
})();
