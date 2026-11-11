/* Public EmpireDrop Top 10: no credentials and no direct provider calls.
 * Only /public-state (the server's sanitized projection) is rendered here.
 */
(() => {
  'use strict';
  const id = value => document.getElementById(value);
  const shuffleTab = id('shuffleTab'), empireTab = id('empireTab');
  if (!shuffleTab || !empireTab) return;
  let latest = null;
  let dateOffset = 0;
  const tabs = [shuffleTab, empireTab];
  const title = id('raceTitle'), description = id('raceDescription');
  // The old hero title belongs to Shuffle only.
  let shuffleTitle = title?.textContent || 'RedHunllef Wager Race';
  let shuffleDescription = description?.textContent || '';
  const date = unix => unix ? new Intl.DateTimeFormat('en-US', {timeZone:'America/New_York', dateStyle:'medium', timeStyle:'short'}).format(new Date(unix*1000))+' ET' : 'No confirmed update';
  const isEmpire = () => empireTab.getAttribute('aria-selected') === 'true';
  function setHero() {
    if (isEmpire()) {
      if (title) title.textContent = 'EmpireDrop ' + (latest?.race_meta?.engine === 'RAFFLE' ? 'Raffle' : latest?.race_meta?.type === 'DEPOSIT' ? 'Deposit' : 'Wager') + ' Race';
      if (description) description.textContent = latest?.race_meta?.name ? `EmpireDrop race: ${latest.race_meta.name}` : 'EmpireDrop partner race standings, updated from the official API.';
    } else {
      if (title) title.textContent = shuffleTitle;
      if (description) description.textContent = shuffleDescription;
    }
    if (id('shuffleRaceClock')) id('shuffleRaceClock').hidden = isEmpire();
    if (id('empireRaceClock')) id('empireRaceClock').hidden = !isEmpire();
    const shuffleStatus = id('shuffleSourceStatus');
    if (shuffleStatus) shuffleStatus.hidden = isEmpire();
    const empireStatus = id('empireSourceStatus');
    if (empireStatus) empireStatus.hidden = !isEmpire();
    if (isEmpire()) updateRefreshStatus();
  }
  function select(tab, focus=false) {
    // Capture Shuffle's latest text before switching *away*.
    if (!isEmpire()) {
      shuffleTitle = title?.textContent || shuffleTitle;
      shuffleDescription = description?.textContent || shuffleDescription;
    }
    for (const current of tabs) {
      const active = current === tab;
      current.setAttribute('aria-selected', String(active));
      current.tabIndex = active ? 0 : -1;
      current.classList.toggle('active', active);
      const panel = id(current.getAttribute('aria-controls'));
      if (panel) panel.hidden = !active;
    }
    setHero();
    if (focus) tab.focus();
  }
  tabs.forEach((tab,index) => {
    tab.addEventListener('click', () => select(tab));
    tab.addEventListener('keydown', event => {
      if (!['ArrowLeft','ArrowRight','Home','End'].includes(event.key)) return;
      event.preventDefault();
      const next = event.key === 'Home' ? 0 : event.key === 'End' ? tabs.length-1 :
        (index+(event.key === 'ArrowRight' ? 1 : -1)+tabs.length)%tabs.length;
      select(tabs[next], true);
    });
  });
  function render(board) {
    if (!board || !Array.isArray(board.rows)) return;
    latest = board;
    if (Number.isFinite(Number(board.server_time))) dateOffset = Number(board.server_time) - Date.now()/1000;
    // The regular source poll may update Shuffle's title while EmpireDrop is selected.
    if (board.shuffle_site) {
      shuffleTitle = String(board.shuffle_site.race_title || shuffleTitle);
      shuffleDescription = String(board.shuffle_site.race_description || shuffleDescription);
    }
    // Standings are ordered by the provider. Two users can share the same
    // rank; map by displayed POSITION rather than rank, or ties disappear.
    const rows = Array.isArray(board.rows) ? board.rows.slice(0, 10) : [];
    const metric = board.race_meta?.metric || 'Wagered';

    // Read the independently configured EmpireDrop prize schedule BEFORE
    // rendering player slots. Previously `configured` was accessed inside
    // this loop before its `const` declaration (temporal dead zone). When
    // payouts were not announced, a ReferenceError stopped the entire render
    // after writing the first player's name and wager. Admin still showed
    // every player because its renderer does not use this payout loop.
    const rewards = board.prizes || {};
    const configured = rewards.enabled === true;
    const providerLimit = Number(board.race_meta?.ranks_limit);
    const hasProviderLimit = Number.isInteger(providerLimit) && providerLimit > 0;
    const displayLimit = hasProviderLimit ? Math.min(10, providerLimit) : 10;

    document.querySelectorAll?.('[data-empire-metric]')?.forEach(node => {
      node.textContent = 'EmpireDrop ' + metric.toLowerCase();
    });
    // The official API can return fewer than 10 places (race.ranks_limit).
    // Clarify that positions the provider does not expose are not vacant.
    const coverage = id('empireRankingCoverage');
    if (coverage) {
      coverage.textContent = hasProviderLimit && providerLimit < 10
        ? `Showing ${rows.length} of ${providerLimit} official positions. EmpireDrop does not expose places ${providerLimit + 1}–10 for this race.`
        : `Showing ${rows.length} of 10 leaderboard positions${hasProviderLimit && providerLimit > 10 ? ` (Top 10 of ${providerLimit} supplied by EmpireDrop)` : ''}.`;
    }
    for (let position=1; position<=10; position++) {
      // Position is the position in the returned array, not necessarily the
      // provider rank: tied players can both be rank 2 (then rank 4).
      const r = rows[position - 1];
      const unreported = !r && position > displayLimit;
      const name = document.querySelector(position<=3 ? `[data-empire-name="${position}"]` : `[data-empire-row-name="${position}"]`);
      const amount = document.querySelector(position<=3 ? `[data-empire-wager="${position}"]` : `[data-empire-row-wager="${position}"]`);
      if (name) name.textContent = r?.username || (unreported ? 'Not reported by EmpireDrop' : 'Open position');
      const place = id('empireBoard')?.querySelector?.(`[data-empire-place="${position}"]`);
      if (place) place.textContent = String(r?.rank ?? position).padStart(2, '0');
      if (amount) amount.textContent = r?.wager || '—';
      const prize = document.querySelector(position<=3 ? `[data-empire-prize="${position}"]` : `[data-empire-row-prize="${position}"]`);
      if (prize) {
        // The server has already allocated provider-rank prizes and split
        // tied places; prefer that verified value over a local fallback.
        const serverPrize = r?.prize;
        const prizeRank = String(r?.rank ?? position);
        prize.textContent = serverPrize && serverPrize !== '—' ? serverPrize :
          configured ? (rewards.formatted?.[prizeRank] || '—') : 'Not announced';
      }
    }
    // Independent site-managed EmpireDrop payout pool, never Shuffle's.
    if (id('empirePoolTotal')) id('empirePoolTotal').textContent = configured ? rewards.total : 'Not announced';
    if (id('empireMessage')) id('empireMessage').textContent = board.label || 'Awaiting EmpireDrop';
    // Refresh *status* from a successful provider fetch, not a browser poll.
    updateRefreshStatus();
    if (board.schedule) {
      if (id('empireRaceMode')) id('empireRaceMode').textContent = board.schedule.mode === 'provider' ? 'EmpireDrop official race' : board.schedule.mode === 'weekly' ? 'Weekly · Tuesday 6 PM ET' : 'Custom race';
      if (id('empireRaceWindow')) id('empireRaceWindow').textContent = (board.schedule.start_et || '')+' → '+(board.schedule.end_et || '');
    }
    const showClock = () => {
      const node = id('empireCountdown');
      if (!node) return;
      const sch = latest?.schedule || {};
      const now = Math.floor(Date.now()/1000) + dateOffset;
      const start = Number(sch.start_time), end = Number(sch.end_time);
      if (!start || !end || !Number.isFinite(start) || !Number.isFinite(end)) {
        node.textContent = 'Race schedule pending'; return;
      }
      if (now >= end) { node.textContent = 'Race ended'; return; }
      const future = now < start;
      let seconds = Math.max(0, (future ? start : end) - now);
      const d = Math.floor(seconds/86400); seconds%=86400;
      const h = Math.floor(seconds/3600); seconds%=3600;
      const m = Math.floor(seconds/60), sec = seconds%60;
      node.textContent = `${future ? 'Starts in ' : ''}${d ? d+'d ' : ''}${String(h).padStart(2,'0')}:${String(m).padStart(2,'0')}:${String(sec).padStart(2,'0')}`;
    };
    showClock();
    const history = id('empireHistoryList');
    if (history) {
      const snapshots = Array.isArray(board.history) ? board.history.slice(0,4) : [];
      history.replaceChildren();
      if (!snapshots.length) {
        const note=document.createElement('p');note.className='small muted';
        note.textContent='No completed race snapshots saved yet.';history.append(note);
      } else for (const item of snapshots) {
        const row=document.createElement('article');row.className='empire-history-row';
        const name=document.createElement('strong');name.textContent=item.name||'Previous race';
        const info=document.createElement('small');
        info.textContent='Last verified '+date(item.updated_at)+' · '+
          (item.rows?.length||0)+' saved players · '+
          (item.prizes?.enabled?'Pool '+item.prizes.total:'Prizes not announced');
        row.append(name,info);history.append(row);
      }
    }
    // /public-state refreshes the main hero for Shuffle; restore EmpireDrop's
    // provider-specific title whenever it is selected.
    setHero();
  }
  // Match Shuffle's live 'Updated Ns ago' indicator, while showing the
  // next actual EmpireDrop provider check (typically cache_duration=300s).
  // A failed check NEVER resets the successful-update age.
  function updateRefreshStatus() {
    if (!latest) return;
    const now = Math.floor(Date.now()/1000) + dateOffset;
    const success = Number(latest.updated_at);
    const age = Number.isFinite(success) && success > 0 ? Math.max(0, Math.floor(now - success)) : null;
    const ageLabel = age === null ? 'No successful update yet' : `Updated ${age}s ago`;
    const next = Number(latest.next_check_at);
    const interval = Number(latest.refresh_interval);
    const nextLabel = Number.isFinite(next) && next > 0
      ? (next > now ? `Next provider check in ${Math.ceil(next - now)}s` : 'Next provider check due')
      : 'Provider refresh not scheduled';
    const source = id('empireSourceTime');
    if (source) source.textContent = ageLabel;
    const nextNode = id('empireNextCheck');
    if (nextNode) nextNode.textContent = nextLabel;
    const label = id('empireSourceLabel');
    if (label) label.textContent = latest.label?.startsWith('Updates delayed') || latest.label?.startsWith('Source unavailable')
      ? 'EmpireDrop · updates delayed' : 'EmpireDrop · verified standings';
    const details = id('empireChecked');
    if (details) details.textContent = success > 0
      ? `Last successful update: ${date(success)} · ${nextLabel}`
      : `No successful update yet · ${nextLabel}`;
  }
  document.addEventListener('empiredrop:update', event => render(event.detail));
  if (typeof setInterval === 'function') setInterval(() => { updateRefreshStatus(); if (!latest || !id('empireCountdown')) return; const sch=latest.schedule||{}; const n=Math.floor(Date.now()/1000); const start=Number(sch.start_time),end=Number(sch.end_time); const box=id('empireCountdown'); if(!start||!end){box.textContent='Race schedule pending';return;} if(n>=end){box.textContent='Race ended';return;} let s=Math.max(0,(n<start?start:end)-n);const d=Math.floor(s/86400);s%=86400;const h=Math.floor(s/3600);s%=3600;box.textContent=(n<start?'Starts in ':'')+(d?d+'d ':'')+String(h).padStart(2,'0')+':'+String(Math.floor(s/60)).padStart(2,'0')+':'+String(s%60).padStart(2,'0'); },1000);
  try { const bootstrap = JSON.parse(document.body.dataset.bootstrap || '{}'); render({...bootstrap.empiredrop, server_time:bootstrap.server_time}); }
  catch { /* Keep server-rendered unavailable state if bootstrap cannot load. */ }
  select(shuffleTab);
})();
