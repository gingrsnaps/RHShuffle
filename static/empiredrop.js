/* Uniform public provider switcher. The browser renders only the server's
 * sanitized /public-state projection; credentials never reach this file. */
(() => {
  'use strict';
  const id = value => document.getElementById(value);
  const shuffleTab = id('shuffleTab');
  const empireTab = id('empireTab');
  if (!shuffleTab || !empireTab) return;

  const tabs = [shuffleTab, empireTab];
  let latest = null;
  let serverOffset = 0;
  let countdownTimer = null;
  const isEmpire = () => empireTab.getAttribute('aria-selected') === 'true';
  const date = unix => unix
    ? new Intl.DateTimeFormat('en-US', {timeZone:'America/New_York', dateStyle:'medium', timeStyle:'short'}).format(new Date(unix*1000)) + ' ET'
    : 'Schedule pending';

  function selectedProvider() {
    return isEmpire() ? 'empiredrop' : 'shuffle';
  }

  function writeProviderUrl(provider) {
    try {
      const url = new URL(location.href);
      if (provider === 'empiredrop') url.searchParams.set('provider', 'empiredrop');
      else url.searchParams.delete('provider');
      history.replaceState({provider}, '', url);
    } catch {}
  }

  function updateProviderChrome() {
    const empire = isEmpire();
    if (id('shuffleRaceClock')) id('shuffleRaceClock').hidden = empire;
    if (id('empireRaceClock')) id('empireRaceClock').hidden = !empire;
    const provider = selectedProvider();
    document.documentElement.dataset.publicProvider = provider;
    document.body.dataset.publicProvider = provider;
    document.querySelectorAll('[data-provider-brand]').forEach(card => {
      const selected = card.dataset.providerBrand === provider;
      card.classList.toggle('is-selected', selected);
      card.setAttribute('aria-current', selected ? 'true' : 'false');
    });
    const join = id('providerJoinLink');
    if (join) {
      join.href = empire ? 'https://empiredrop.com/c/red' : (id('sponsorLink')?.href || '#');
      join.textContent = empire ? 'Join on EmpireDrop ↗' : 'Join on Shuffle ↗';
    }
  }

  function select(tab, focus=false, updateUrl=true) {
    for (const current of tabs) {
      const active = current === tab;
      current.setAttribute('aria-selected', String(active));
      current.tabIndex = active ? 0 : -1;
      current.classList.toggle('active', active);
      const panel = id(current.getAttribute('aria-controls'));
      if (panel) panel.hidden = !active;
    }
    updateProviderChrome();
    updateCountdowns();
    if (updateUrl) writeProviderUrl(selectedProvider());
    if (focus) tab.focus();
  }

  tabs.forEach((tab, index) => {
    tab.addEventListener('click', () => select(tab));
    tab.addEventListener('keydown', event => {
      if (!['ArrowLeft','ArrowRight','Home','End'].includes(event.key)) return;
      event.preventDefault();
      const next = event.key === 'Home' ? 0 : event.key === 'End' ? tabs.length-1 :
        (index + (event.key === 'ArrowRight' ? 1 : -1) + tabs.length) % tabs.length;
      select(tabs[next], true);
    });
  });

  function renderHistory(board) {
    const history = id('empireHistoryList');
    if (!history) return;
    const snapshots = Array.isArray(board.history) ? board.history.slice(0, 4) : [];
    history.replaceChildren();
    if (!snapshots.length) {
      history.append(Object.assign(document.createElement('p'), {
        className:'small muted', textContent:'No completed race snapshots saved yet.'
      }));
      return;
    }
    for (const item of snapshots) {
      const row = document.createElement('article');
      row.className = 'empire-history-row';
      const name = document.createElement('strong');
      name.textContent = item.name || 'Previous race';
      const info = document.createElement('small');
      info.textContent = `${date(item.updated_at)} · ${item.rows?.length || 0} saved players`;
      row.append(name, info);
      history.append(row);
    }
  }

  function render(board) {
    if (!board || !Array.isArray(board.rows)) return;
    latest = board;
    if (Number.isFinite(Number(board.server_time))) serverOffset = Number(board.server_time) - Date.now()/1000;
    const rows = board.rows.slice(0, 10);
    const rewards = board.prizes || {};
    const configured = rewards.enabled === true;
    const providerLimit = Number(board.race_meta?.ranks_limit);
    const displayLimit = Number.isInteger(providerLimit) && providerLimit > 0 ? Math.min(10, providerLimit) : 10;

    for (let position=1; position<=10; position++) {
      const row = rows[position-1];
      const unreported = !row && position > displayLimit;
      const name = document.querySelector(position <= 3
        ? `[data-empire-name="${position}"]`
        : `[data-empire-row-name="${position}"]`);
      const amount = document.querySelector(position <= 3
        ? `[data-empire-wager="${position}"]`
        : `[data-empire-row-wager="${position}"]`);
      const place = id('empireBoard')?.querySelector(`[data-empire-place="${position}"]`);
      const prize = document.querySelector(position <= 3
        ? `[data-empire-prize="${position}"]`
        : `[data-empire-row-prize="${position}"]`);
      if (name) name.textContent = row?.username || (unreported ? 'Unavailable' : 'Open position');
      if (amount) amount.textContent = row?.wager || '—';
      if (place) place.textContent = String(row?.rank ?? position).padStart(2, '0');
      if (prize) {
        const serverPrize = row?.prize;
        const prizeRank = String(row?.rank ?? position);
        const announced = Boolean(serverPrize && serverPrize !== '—') || configured;
        prize.textContent = serverPrize && serverPrize !== '—'
          ? serverPrize
          : configured ? (rewards.formatted?.[prizeRank] || '—') : 'To be announced';
        prize.classList.toggle('is-unannounced', !announced);
      }
    }

    if (id('empirePoolTotal')) {
      id('empirePoolTotal').textContent = configured ? rewards.total : 'To be announced';
      id('empirePoolTotal').classList.toggle('is-unannounced', !configured);
    }
    if (board.schedule && id('empireRaceWindow')) {
      id('empireRaceWindow').textContent = `${board.schedule.start_et || ''} → ${board.schedule.end_et || ''}`;
    }
    const coverage = id('empireRankingCoverage');
    if (coverage) {
      coverage.textContent = providerLimit > 0 && providerLimit < 10
        ? `EmpireDrop currently exposes ${providerLimit} official positions for this race.`
        : rows.length < 10 ? 'Open positions will appear when activity is reported.' : '';
      coverage.hidden = !coverage.textContent;
    }
    const message = id('empireMessage');
    if (message) {
      message.textContent = rows.length ? '' : (board.updated_at ? 'Showing the most recent standings.' : 'Standings are temporarily unavailable.');
      message.hidden = rows.length > 0;
    }
    renderHistory(board);
    updateProviderChrome();
    updateCountdowns();
  }

  function countdownState(start, end, now) {
    if (!Number.isFinite(start) || !Number.isFinite(end) || !start || !end || end <= start)
      return {state:'unconfigured', label:'RACE SCHEDULE', text:'Set the race dates'};
    if (now >= end) return {state:'ended', label:'RACE SCHEDULE', text:'Race complete'};
    const upcoming = now < start;
    let seconds = Math.max(0, Math.ceil((upcoming ? start : end) - now));
    const days = Math.floor(seconds/86400); seconds %= 86400;
    const hours = Math.floor(seconds/3600); seconds %= 3600;
    const minutes = Math.floor(seconds/60); seconds %= 60;
    return {
      state: upcoming ? 'upcoming' : 'active',
      label: upcoming ? 'STARTS IN' : 'RACE ENDS IN',
      text:`${days}d ${String(hours).padStart(2,'0')}h ${String(minutes).padStart(2,'0')}m ${String(seconds).padStart(2,'0')}s`
    };
  }

  function updateCountdowns() {
    if (!latest || !id('empireCountdown')) return;
    const now = Math.floor(Date.now()/1000 + serverOffset);
    const schedule = latest.schedule || {};
    const value = countdownState(Number(schedule.start_time), Number(schedule.end_time), now);
    id('empireCountdown').textContent = value.text;
    if (id('empireClockLabel')) id('empireClockLabel').textContent = value.label;
    if (id('empireRaceBadge')) {
      id('empireRaceBadge').textContent = value.state.charAt(0).toUpperCase()+value.state.slice(1);
      id('empireRaceBadge').className = 'badge state-'+value.state;
    }
  }

  document.addEventListener('empiredrop:update', event => render(event.detail));
  function startCountdownTimer() {
    clearInterval(countdownTimer);
    if (document.hidden) return;
    updateCountdowns();
    countdownTimer = setInterval(updateCountdowns, 1000);
  }
  document.addEventListener('visibilitychange', startCountdownTimer);
  globalThis.addEventListener?.('pagehide', () => clearInterval(countdownTimer), {once:true});
  startCountdownTimer();

  try {
    const bootstrap = JSON.parse(document.body.dataset.bootstrap || '{}');
    render({...bootstrap.empiredrop, server_time:bootstrap.server_time});
  } catch {}

  let requested = '';
  try { requested = new URL(location.href).searchParams.get('provider') || ''; } catch {}
  select(requested === 'empiredrop' ? empireTab : shuffleTab, false, false);
  globalThis.addEventListener?.('popstate', () => {
    let provider = '';
    try { provider = new URL(location.href).searchParams.get('provider') || ''; } catch {}
    select(provider === 'empiredrop' ? empireTab : shuffleTab, false, false);
  });
})();
