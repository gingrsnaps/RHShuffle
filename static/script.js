(() => {
  'use strict';

  const $ = (selector, root = document) => root.querySelector(selector);

  const podiumEl = $('#podium');
  const othersEl = $('#others-list');
  const liveEl = $('#liveStatus');
  const viewerChip = liveEl?.querySelector('.viewer-chip');
  const statusText = liveEl?.querySelector('.text');
  const dataStatus = $('#dataStatus');
  const dd = $('#dd');
  const hh = $('#hh');
  const mm = $('#mm');
  const ss = $('#ss');
  const yearOut = $('#year');

  const FALLBACK_PRIZES = {
    1: '$1,800.00',
    2: '$1,200.00',
    3: '$800.00',
    4: '$450.00',
    5: '$200.00',
    6: '$150.00',
    7: '$90.00',
    8: '$80.00',
    9: '$70.00',
    10: '$60.00',
    11: '$20.00',
    12: '$20.00',
    13: '$20.00',
    14: '$20.00',
    15: '$20.00'
  };

  let prizes = { ...FALLBACK_PRIZES };
  let leaderboardSize = 15;
  let refreshSeconds = 60;
  let endTime = 0;
  let countdownTimer = null;
  let leaderboardTimer = null;
  let streamTimer = null;

  function moneyToNumber(value) {
    if (typeof value === 'number') return value;
    if (!value) return 0;
    const parsed = Number.parseFloat(String(value).replace(/[^0-9.]/g, ''));
    return Number.isNaN(parsed) ? 0 : parsed;
  }

  function formatInteger(value) {
    return Number(value ?? 0).toLocaleString();
  }

  function clearChildren(element) {
    while (element?.firstChild) element.removeChild(element.firstChild);
  }

  function textElement(tag, className, value) {
    const element = document.createElement(tag);
    if (className) element.className = className;
    element.textContent = value;
    return element;
  }

  function normalizeLeaderboardEntry(entry, rank = null) {
    return {
      rank,
      username: entry?.username ?? '--',
      wagerStr: entry?.wager ?? '$0.00',
      wagerNum: moneyToNumber(entry?.wager)
    };
  }

  function buildPodium(rawEntries) {
    if (!podiumEl) return;

    const entries = (rawEntries || [])
      .map((entry) => normalizeLeaderboardEntry(entry))
      .sort((a, b) => b.wagerNum - a.wagerNum);

    const first = entries[0] || normalizeLeaderboardEntry(null);
    const second = entries[1] || normalizeLeaderboardEntry(null);
    const third = entries[2] || normalizeLeaderboardEntry(null);

    const seats = [
      { place: 2, className: 'col-second', medal: '🥈', entry: second },
      { place: 1, className: 'col-first', medal: '🥇', entry: first },
      { place: 3, className: 'col-third', medal: '🥉', entry: third }
    ];

    clearChildren(podiumEl);
    seats.forEach((seat) => {
      const card = document.createElement('article');
      card.className = `podium-seat ${seat.className} fade-in`;

      const head = document.createElement('div');
      head.className = 'podium-head';
      head.appendChild(textElement('span', 'rank-badge', `#${seat.place}`));
      const medal = textElement('span', 'crown', seat.medal);
      medal.setAttribute('aria-hidden', 'true');
      head.appendChild(medal);

      card.appendChild(head);
      card.appendChild(textElement('div', 'user', seat.entry.username));
      card.appendChild(textElement('div', 'label', 'WEIGHTED WAGER'));
      card.appendChild(textElement('div', 'wager', seat.entry.wagerStr));
      card.appendChild(textElement('div', 'label', 'PRIZE'));
      card.appendChild(textElement('div', 'prize', prizes[seat.place] || '$0.00'));
      podiumEl.appendChild(card);
    });
  }

  function buildOthers(rawEntries) {
    if (!othersEl) return;

    let entries = (rawEntries || []).map((entry) => ({
      ...normalizeLeaderboardEntry(entry, Number.isInteger(entry?.rank) ? entry.rank : null)
    }));

    const hasRanks = entries.some((entry) => entry.rank !== null);
    if (hasRanks) {
      entries.sort((a, b) => (a.rank ?? 999) - (b.rank ?? 999));
    } else {
      entries.sort((a, b) => b.wagerNum - a.wagerNum);
      entries = entries.map((entry, index) => ({ ...entry, rank: 4 + index }));
    }

    const desiredCards = Math.max(0, leaderboardSize - 3);
    if (entries.length < desiredCards) {
      const occupiedRanks = new Set(entries.map((entry) => entry.rank));
      for (let rank = 4; rank <= leaderboardSize; rank += 1) {
        if (!occupiedRanks.has(rank)) {
          entries.push({
            rank,
            username: '--',
            wagerStr: '$0.00',
            wagerNum: 0
          });
        }
      }
      entries.sort((a, b) => (a.rank ?? 999) - (b.rank ?? 999));
    }
    entries = entries.slice(0, desiredCards);

    clearChildren(othersEl);
    entries.forEach((entry) => {
      const item = document.createElement('li');
      item.className = 'leaderboard-card fade-in';
      item.appendChild(textElement('span', 'position', `#${entry.rank}`));
      item.appendChild(textElement('div', 'username', entry.username));
      item.appendChild(textElement('div', 'label emphasized', 'WEIGHTED WAGER'));
      item.appendChild(textElement('div', 'wager', entry.wagerStr));
      item.appendChild(textElement('div', 'label', 'PRIZE'));
      item.appendChild(textElement('div', 'prize', prizes[entry.rank] || '$0.00'));
      othersEl.appendChild(item);
    });
  }

  function setDataStatus(message, state = 'ok') {
    if (!dataStatus) return;
    dataStatus.textContent = message;
    dataStatus.dataset.state = state;
  }

  async function fetchLeaderboard() {
    try {
      const response = await fetch('/data', { cache: 'no-store' });
      if (!response.ok) throw new Error(`data status ${response.status}`);
      const payload = await response.json();
      buildPodium(payload.podium || []);
      buildOthers(payload.others || []);
      setDataStatus(
        payload.meta?.stale
          ? 'Showing the most recently saved leaderboard while the data source reconnects.'
          : `Leaderboard updated automatically every ${refreshSeconds} seconds.`,
        payload.meta?.stale ? 'warning' : 'ok'
      );
    } catch (error) {
      console.error('[leaderboard] failed', error);
      setDataStatus('Leaderboard update is temporarily unavailable. Existing results remain displayed.', 'error');
    }
  }

  function setLiveClass(className) {
    liveEl?.classList.remove('live', 'off', 'unk');
    liveEl?.classList.add(className);
  }

  async function fetchStream() {
    if (!liveEl || !statusText || !viewerChip) return;

    try {
      const response = await fetch('/stream', { cache: 'no-store' });
      if (!response.ok) throw new Error(`stream status ${response.status}`);
      const payload = await response.json();

      viewerChip.hidden = true;
      viewerChip.textContent = '';
      liveEl.removeAttribute('title');

      if (!payload.available) {
        setLiveClass('unk');
        statusText.textContent = payload.stale ? 'Live status delayed' : 'Status unavailable';
        return;
      }

      if (payload.live) {
        setLiveClass('live');
        statusText.textContent = 'Live on Kick';
        if (typeof payload.viewers === 'number') {
          viewerChip.hidden = false;
          viewerChip.textContent = `${formatInteger(payload.viewers)} watching`;
        }
        const details = [payload.title, payload.category].filter(Boolean).join(' · ');
        if (details) liveEl.title = details;
      } else {
        setLiveClass('off');
        statusText.textContent = 'Currently offline';
      }
    } catch (error) {
      console.warn('[stream] failed', error);
      setLiveClass('unk');
      statusText.textContent = 'Status unavailable';
      viewerChip.hidden = true;
    }
  }

  function startCountdown() {
    if (!dd || !hh || !mm || !ss) return;
    if (countdownTimer) window.clearInterval(countdownTimer);

    const tick = () => {
      const now = Math.floor(Date.now() / 1000);
      let remaining = Math.max(0, endTime - now);
      const days = Math.floor(remaining / 86400);
      remaining -= days * 86400;
      const hours = Math.floor(remaining / 3600);
      remaining -= hours * 3600;
      const minutes = Math.floor(remaining / 60);
      remaining -= minutes * 60;

      dd.textContent = String(days).padStart(2, '0');
      hh.textContent = String(hours).padStart(2, '0');
      mm.textContent = String(minutes).padStart(2, '0');
      ss.textContent = String(remaining).padStart(2, '0');
    };

    tick();
    countdownTimer = window.setInterval(tick, 1000);
  }

  async function loadConfig() {
    try {
      const response = await fetch('/config', { cache: 'no-store' });
      if (!response.ok) throw new Error(`config status ${response.status}`);
      const payload = await response.json();
      endTime = Number(payload.end_time) || 0;
      leaderboardSize = Math.max(3, Number(payload.leaderboard_size) || 15);
      refreshSeconds = Math.max(15, Number(payload.refresh_seconds) || 60);
      if (payload.prizes && typeof payload.prizes === 'object') {
        prizes = { ...FALLBACK_PRIZES, ...payload.prizes };
      }
    } catch (error) {
      console.warn('[config] failed; using safe defaults', error);
    }
    startCountdown();
  }

  function scheduleRefreshes() {
    if (leaderboardTimer) window.clearInterval(leaderboardTimer);
    if (streamTimer) window.clearInterval(streamTimer);

    if (podiumEl || othersEl) {
      leaderboardTimer = window.setInterval(fetchLeaderboard, refreshSeconds * 1000);
    }
    if (liveEl) {
      streamTimer = window.setInterval(fetchStream, Math.min(refreshSeconds, 60) * 1000);
    }
  }

  async function boot() {
    if (yearOut) yearOut.textContent = new Date().getFullYear();

    const needsConfig = Boolean(podiumEl || othersEl || (dd && hh && mm && ss));
    if (needsConfig) await loadConfig();

    const jobs = [];
    if (podiumEl || othersEl) jobs.push(fetchLeaderboard());
    if (liveEl) jobs.push(fetchStream());
    await Promise.allSettled(jobs);

    if (jobs.length) scheduleRefreshes();
  }

  document.addEventListener('DOMContentLoaded', boot);
})();
