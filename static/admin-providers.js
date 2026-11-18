/* Shared admin source cards. Status comes from the existing /admin/status feed;
   this file NEVER makes additional Shuffle or EmpireDrop API requests. */
(() => {
  'use strict';
  const fmt = timestamp => Number(timestamp) > 0
    ? new Intl.DateTimeFormat('en-US', {timeZone:'America/New_York',year:'numeric',month:'short',day:'numeric',hour:'numeric',minute:'2-digit',timeZoneName:'short'}).format(new Date(timestamp*1000))
    : 'Not verified yet';
  const set = (selector, value) => {
    for (const node of document.querySelectorAll(selector)) node.textContent = String(value);
  };
  const tickNextChecks = () => {
    const now = Math.floor(Date.now()/1000);
    document.querySelectorAll('[data-provider-next-check]').forEach(node => {
      const stamp = Number(node.dataset.nextCheck || 0);
      node.textContent = stamp > now ? `in ${stamp-now}s` : stamp ? 'Checking now…' : 'Check queued';
    });
  };
  function renderMovementHistory(payload) {
    const all = payload?.movement_diagnostics || {};
    for (const provider of ['shuffle','empiredrop']) {
      const list = document.querySelector(`[data-movement-events="${provider}"]`);
      if (!list) continue;
      const events = Array.isArray(all?.[provider]?.events) ? all[provider].events.slice(0,20) : [];
      if (!events.length) {
        const item=document.createElement('li'); item.className='empty'; item.textContent='No placement changes recorded in this process yet.';
        list.replaceChildren(item); continue;
      }
      list.replaceChildren(...events.map(event => {
        const item=document.createElement('li'); item.dataset.eventId=String(event.event_id || '');
        const name=document.createElement('strong'); name.textContent=String(event.username || 'Player');
        const change=document.createElement('span');
        change.textContent=event.direction === 'new'
          ? `NEW at #${event.current_rank}`
          : `#${event.previous_rank} → #${event.current_rank} · ${event.direction === 'up' ? '↑' : '↓'}${event.places}`;
        const time=document.createElement('small'); time.textContent=fmt(event.changed_at);
        item.append(name,change,time); return item;
      }));
    }
  }

  function render(payload) {
    if (!payload?.providers) return;
    for (const name of ['shuffle','empiredrop']) {
      const item = payload.providers[name];
      if (!item) continue;
      for (const node of document.querySelectorAll(`[data-provider-state="${name}"]`)) {
        node.dataset.state = item.state;
        node.textContent = item.status;
      }
      const fields = {last_success:fmt(item.last_success),last_attempt:item.last_attempt ? fmt(item.last_attempt) : 'Not attempted',
        last_changed:item.last_changed ? fmt(item.last_changed) : 'No recorded change yet',
        participants:item.participants,filled:`${item.filled ?? item.participants}/15`,quality:item.quality,metric:item.metric,cadence:`Every ${item.refresh_seconds} seconds`,
        standings_sequence:`#${item.standings_sequence || 0}`,
        movement_count:`${item.movement_count || 0} placement change${Number(item.movement_count) === 1 ? '' : 's'} · event #${item.movement_sequence || 0}`};
      for (const [key,value] of Object.entries(fields))
        set(`[data-provider-field="${name}:${key}"]`, value);
      document.querySelectorAll(`[data-provider-next-check="${name}"]`).forEach(node => { node.dataset.nextCheck = String(item.next_check || 0); });
      tickNextChecks();
      const wrapper = document.querySelector(`[data-provider-issues="${name}"]`);
      if (wrapper) {
        const issues = Array.isArray(item.issues) ? item.issues : [];
        wrapper.hidden = issues.length === 0;
        const list = wrapper.querySelector('ul');
        if (list) list.replaceChildren(...issues.map(message=>{
          const row=document.createElement('li'); row.textContent=message; return row;
        }));
      }
    }
    renderMovementHistory(payload);
  }
  // Table searches filter only the visible loaded records, not the entire provider.
  document.querySelectorAll('[data-provider-search]').forEach(input => {
    const body = document.getElementById(input.dataset.providerSearch);
    if (!body) return;
    input.addEventListener('input', () => {
      const query=input.value.trim().toLocaleLowerCase();
      for (const row of body.querySelectorAll('tr'))
        row.hidden = Boolean(query && !row.textContent.toLocaleLowerCase().includes(query));
    });
  });
  tickNextChecks();
  setInterval(tickNextChecks, 1000);
  globalThis.RedProviderCards = {render};
})();
