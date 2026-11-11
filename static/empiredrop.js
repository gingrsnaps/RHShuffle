/* Public EmpireDrop Top 15: no credentials and no direct provider calls.
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
    const status = document.querySelector('#leaderboard > .section-title .source-status');
    if (status) status.hidden = isEmpire();
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
    // The regular source poll may update Shuffle's title while EmpireDrop is selected.
    if (board.shuffle_site) {
      shuffleTitle = String(board.shuffle_site.race_title || shuffleTitle);
      shuffleDescription = String(board.shuffle_site.race_description || shuffleDescription);
    }
    // Standings are ordered by the provider. Two users can share the same
    // rank; map by displayed POSITION rather than rank, or ties disappear.
    const rows = Array.isArray(board.rows) ? board.rows.slice(0, 15) : [];
    const metric = board.race_meta?.metric || 'Wagered';
    document.querySelectorAll?.('[data-empire-metric]')?.forEach(node => {
      node.textContent = 'EmpireDrop ' + metric.toLowerCase();
    });
    for (let rank=1; rank<=15; rank++) {
      const r = rows[rank - 1];
      const name = document.querySelector(rank<=3 ? `[data-empire-name="${rank}"]` : `[data-empire-row-name="${rank}"]`);
      const amount = document.querySelector(rank<=3 ? `[data-empire-wager="${rank}"]` : `[data-empire-row-wager="${rank}"]`);
      if (name) name.textContent = r?.username || 'Open position';
      const place = id('empireBoard')?.querySelector?.(`[data-empire-place="${rank}"]`);
      if (place) place.textContent = String(r?.rank || rank).padStart(2, '0');
      if (amount) amount.textContent = r?.wager || '—';
      const prize = document.querySelector(rank<=3 ? `[data-empire-prize="${rank}"]` : `[data-empire-row-prize="${rank}"]`);
      if (prize) prize.textContent = r?.prize && r.prize !== '—' ? r.prize :
        configured ? (rewards.formatted?.[String(rank)] || '—') : 'Not announced';
    }
    // Independent site-managed EmpireDrop payout pool, never Shuffle's.
    const rewards = board.prizes || {};
    const configured = rewards.enabled === true;
    if (id('empirePoolTotal')) id('empirePoolTotal').textContent = configured ? rewards.total : 'Not announced';
    if (id('empireMessage')) id('empireMessage').textContent = board.label || 'Awaiting EmpireDrop';
    if (id('empireChecked')) id('empireChecked').textContent = board.updated_at ? 'Last verified: '+date(board.updated_at) : 'Not yet verified';
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
  document.addEventListener('empiredrop:update', event => render(event.detail));
  if (typeof setInterval === 'function') setInterval(() => { if (!latest || !id('empireCountdown')) return; const sch=latest.schedule||{}; const n=Math.floor(Date.now()/1000); const start=Number(sch.start_time),end=Number(sch.end_time); const box=id('empireCountdown'); if(!start||!end){box.textContent='Race schedule pending';return;} if(n>=end){box.textContent='Race ended';return;} let s=Math.max(0,(n<start?start:end)-n);const d=Math.floor(s/86400);s%=86400;const h=Math.floor(s/3600);s%=3600;box.textContent=(n<start?'Starts in ':'')+(d?d+'d ':'')+String(h).padStart(2,'0')+':'+String(Math.floor(s/60)).padStart(2,'0')+':'+String(s%60).padStart(2,'0'); },1000);
  try { render(JSON.parse(document.body.dataset.bootstrap || '{}').empiredrop); }
  catch { /* Keep server-rendered unavailable state if bootstrap cannot load. */ }
  select(shuffleTab);
})();
