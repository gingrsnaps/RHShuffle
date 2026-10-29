/* Public EmpireDrop Top 15: no credentials and no direct provider calls.
 * Only /public-state (the server's sanitized projection) is rendered here.
 */
(() => {
  'use strict';
  const id = value => document.getElementById(value);
  const shuffleTab = id('shuffleTab'), empireTab = id('empireTab');
  if (!shuffleTab || !empireTab) return;
  let latest = null;
  const tabs = [shuffleTab, empireTab];
  const title = id('raceTitle'), description = id('raceDescription');
  // The old hero title belongs to Shuffle only.
  let shuffleTitle = title?.textContent || 'RedHunllef Wager Race';
  let shuffleDescription = description?.textContent || '';
  const date = unix => unix ? new Intl.DateTimeFormat('en-US', {timeZone:'America/New_York', dateStyle:'medium', timeStyle:'short'}).format(new Date(unix*1000))+' ET' : 'No confirmed update';
  const isEmpire = () => empireTab.getAttribute('aria-selected') === 'true';
  function setHero() {
    if (isEmpire()) {
      if (title) title.textContent = 'EmpireDrop Wager Race';
      if (description) description.textContent = 'Top 15 EmpireDrop wagers from players referred with code red.';
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
    const rows = new Map(board.rows.map(item => [Number(item.rank), item]));
    for (let rank=1; rank<=15; rank++) {
      const r = rows.get(rank);
      const name = document.querySelector(rank<=3 ? `[data-empire-name="${rank}"]` : `[data-empire-row-name="${rank}"]`);
      const amount = document.querySelector(rank<=3 ? `[data-empire-wager="${rank}"]` : `[data-empire-row-wager="${rank}"]`);
      if (name) name.textContent = r?.username || 'Open position';
      if (amount) amount.textContent = r?.wager || '—';
    }
    if (id('empireMessage')) id('empireMessage').textContent = board.label || 'Awaiting EmpireDrop';
    if (id('empireChecked')) id('empireChecked').textContent = board.updated_at ? 'Last verified: '+date(board.updated_at) : 'Not yet verified';
    if (board.schedule) {
      if (id('empireRaceMode')) id('empireRaceMode').textContent = board.schedule.mode === 'weekly' ? 'Weekly · Tuesday 6 PM ET' : 'Custom race';
      if (id('empireRaceWindow')) id('empireRaceWindow').textContent = (board.schedule.start_et || '')+' → '+(board.schedule.end_et || '');
    }
    // /public-state refreshes the main hero for Shuffle; restore EmpireDrop's
    // provider-specific title whenever it is selected.
    setHero();
  }
  document.addEventListener('empiredrop:update', event => render(event.detail));
  try { render(JSON.parse(document.body.dataset.bootstrap || '{}').empiredrop); }
  catch { /* Keep server-rendered unavailable state if bootstrap cannot load. */ }
  select(shuffleTab);
})();
