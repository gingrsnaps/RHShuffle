/* Shared raid UI. The server owns damage, identity, cooldowns and daily limits.
   Polling never attacks. A failed POST keeps its receipt ID for a safe retry. */
(() => {
  'use strict';
  const root = document.querySelector('[data-boss-root]');
  if (!root) return;
  const admin = root.dataset.mode === 'admin';
  const $ = id => root.querySelector('#' + id);
  const text = (id, value) => { const el=$(id); if(el) el.textContent=String(value); };
  const number = value => Number(value).toLocaleString('en-US');
  const labels = {blade:'Blade',bow:'Bow',magic:'Magic'};
  const button=$('attackButton'), stage=$('bossStage');
  let state, csrf='', selected='blade', busy=false, timer, polling=false;
  let receivedAt=performance.now(), lastGood=-Infinity, pending=null, lastAnimated='';
  const pendingKey='rh.boss.pending';
  // Session storage remembers a click if the connection drops or the tab reloads.
  // Gameplay still works in browsers that disable storage; cookies are required.
  try { pending=JSON.parse(sessionStorage.getItem(pendingKey)); } catch (_) { /* optional */ }
  function remember(value) {
    pending=value;
    try { value ? sessionStorage.setItem(pendingKey,JSON.stringify(value)) : sessionStorage.removeItem(pendingKey); } catch (_) { /* optional */ }
  }
  function error(message='') { const el=$('bossError'); if(el){el.hidden=!message;el.textContent=message;} }
  const now = () => state ? state.server_time+(performance.now()-receivedAt)/1000 : 0;
  function duration(seconds) {
    const s=Math.max(0,Math.ceil(seconds));
    return s>=3600 ? `${Math.floor(s/3600)}h ${Math.floor(s%3600/60)}m` : `${Math.floor(s/60)}:${String(s%60).padStart(2,'0')}`;
  }
  function strikeFeedback(hit, receipt) {
    if (!hit || receipt===lastAnimated) return;
    lastAnimated=receipt;
    text('hitResult',`${hit.burst?'CRIMSON BURST! ':''}${labels[hit.style]} hit for ${number(hit.damage)}${hit.weakness?' · Weakness matched!':' · Nice hit.'}`);
    text('hitFloat','−'+number(hit.damage));
    if(stage){stage.classList.remove('struck'); void stage.offsetWidth; stage.classList.add('struck');}
  }
  function rows(id, values, empty, mapper) {
    const list=$(id); if(!list) return;
    const nodes=values.map(mapper);
    if(!nodes.length){const li=document.createElement('li');li.className='muted';li.textContent=empty;nodes.push(li);}
    list.replaceChildren(...nodes);
  }
  function item(title, detail, score, self=false) {
    const li=document.createElement('li'), left=document.createElement('span'), strong=document.createElement('strong'), small=document.createElement('small'), right=document.createElement('span');
    strong.textContent=title;small.textContent=detail;right.textContent=score;right.className='score';
    left.append(strong,small);li.append(left,right);if(self)li.className='self';return li;
  }
  function apply(value) {
    const next=value.state;
    if(!next || typeof next.raid_id!=='string' || !Number.isFinite(next.server_time) || !next.you) throw new Error('The game returned an incomplete update. Reload in a moment.');
    // A slow poll must not undo an attack or bring back a replaced raid.
    if(state && (next.server_time<state.server_time || (next.raid_id===state.raid_id && next.version<state.version))) return;
    if(value.csrf)csrf=value.csrf;
    state=next;receivedAt=performance.now();lastGood=receivedAt;
    if(pending && (pending.raid_id!==state.raid_id || pending.name!==state.you.name)) remember(null);
    if(pending && state.you.last_request===pending.request_id){strikeFeedback(state.you.last_hit,pending.request_id);remember(null);}
    text('bossConnection','Live · Shared raid connected');
    text('bossHealth',`${number(state.hp)} / ${number(state.max_hp)} HP`);
    text('bossPercent',(state.hp/state.max_hp*100).toFixed(2)+'%');
    const bar=$('bossHealthBar');if(bar){bar.max=state.max_hp;bar.value=state.hp;}
    text('bossPhase',state.status==='victory'?'DEFEATED':state.status==='paused'?'PAUSED':state.phase);
    text('bossDay','Raid day '+state.day);text('bossRaiders',number(state.raiders));
    text('bossAttacks',number(state.total_attacks));text('bossDamage',number(state.total_damage));
    const story=state.status==='victory'?'VICTORY. The Red crew brought the beast down. Every hit made this happen.':state.status==='paused'?'The host has paused attacks. Your progress is safe; the raid-day clock keeps running.':state.status==='waiting'?'The first strike starts the raid. Let’s wake the beast.':state.phase==='Last stand'?'Last stand. The beast is cornered. Rally the crew and finish what you started.':state.phase==='Enraged'?'Enraged. The arena is heating up. Watch the weakness and keep the pressure on.':'Awakening. The beast stirs. Small hits become a massive takedown.';
    text('bossStory',story);if(stage)stage.classList.toggle('victory',state.status==='victory');
    text('bossWeakness',`${state.weakness_label} · 150 damage`);
    root.querySelectorAll('[data-style]').forEach(el=>el.classList.toggle('is-weak',el.dataset.style===state.weakness));
    text('yourName',state.you.name);text('yourDamage',number(state.you.damage));
    text('yourRemaining',`${state.you.remaining} / ${state.rules.daily_attacks}`);
    text('burstLabel',state.you.burst_in===1?'NEXT HIT: +100 damage':`${state.you.burst_in} hits to +100 damage`);
    root.querySelectorAll('#burstMeter span').forEach((el,i)=>el.classList.toggle('filled',i<10-state.you.burst_in));
    rows('bossLeaders',state.leaders,'Land the first hit to lead the charge.',(r,i)=>item(`${String(i+1).padStart(2,'0')}  ${r.name}${r.you?' · You':''}`,`${number(r.attacks)} hits`,number(r.damage),r.you));
    rows('bossRecent',state.recent,'The arena is waiting for your community.',r=>item(r.name,`${labels[r.style]}${r.burst?' · Burst':''}${r.weakness?' · Weakness':''} · ${new Date(r.at*1000).toLocaleTimeString([], {hour:'2-digit',minute:'2-digit'})}`,'−'+number(r.damage)));
    rows('bossHistory',state.history.slice().reverse(),'The first chapter is yours to write.',r=>item(r.outcome,`${number(r.raiders)} raiders · ${number(r.attacks)} hits · ${new Date(r.ended_at*1000).toLocaleDateString()}`,number(r.damage)+' damage'));
    tick();
  }
  function tick() {
    if(!state)return;
    const seconds=now(), stale=performance.now()-lastGood>15000;
    text('wardTimer',seconds>=state.ward_changes_at?'Weakness changing…':`Changes in ${duration(state.ward_changes_at-seconds)}`);
    text('raidReset',state.resets_at?`Next raid day in ${duration(state.resets_at-seconds)}. Allowance refreshes then.`:'The first community hit starts the 24-hour raid-day schedule.');
    if(!button)return;
    const active=['waiting','active'].includes(state.status);
    // An unacknowledged click can be retried even if its first delivery caused
    // a cooldown or victory. The backend returns the original receipt.
    const retry=Boolean(pending && !busy && !stale);
    const ready=active && state.connection_ready && state.you.remaining>0 && seconds>=state.you.ready_at && !stale && !busy;
    button.disabled=!(retry || ready);
    button.textContent=busy?'Landing your hit…':stale?'Reconnecting…':pending?'Retry last strike':state.status==='victory'?'Victory · We did it!':state.status==='paused'?'Raid paused':!state.connection_ready?'Connection setup needed':!state.you.remaining?'Rest up · Return next raid day':seconds<state.you.ready_at?`Next strike in ${duration(state.you.ready_at-seconds)}`:`Attack with ${labels[selected]} →`;
    text('attackHint',pending?'Last strike unconfirmed. Retry safely; it won’t count twice.':state.status==='victory'?'You helped write this chapter. The host can open the next raid.':!state.you.remaining?'Daily allowance used by this browser or shared connection.':`One strike per minute · ${selected===state.weakness?'150':'100'} damage${state.you.burst_in===1?' + 100 burst':''}`);
    if(stale)text('bossConnection','Reconnecting · Showing the last confirmed state');
  }
  async function request(url, options={}) {
    const controller=new AbortController(), timeout=setTimeout(()=>controller.abort(),10000);
    try {
      const response=await fetch(url,{...options,credentials:'same-origin',cache:'no-store',signal:controller.signal,
        headers:{Accept:'application/json',...options.headers}});
      if(!response.headers.get('content-type')?.includes('application/json'))throw new Error('The game server returned an unexpected response. Try again in a moment.');
      return {response,value:await response.json()};
    } finally {clearTimeout(timeout);}
  }
  async function poll() {
    clearTimeout(timer);
    if(document.hidden || polling)return;
    polling=true;
    try {
      const {response,value}=await request('/play/api/state');
      if(!response.ok)throw new Error(value.error || 'The raid is temporarily unavailable.');
      apply(value);error();
    } catch (_) {text('bossConnection','Reconnecting · Your saved damage is safe');tick();}
    finally {polling=false;if(!document.hidden)timer=setTimeout(poll,5000);}
  }
  root.querySelectorAll('[data-style]').forEach(el=>el.addEventListener('click',()=>{
    selected=el.dataset.style;
    root.querySelectorAll('[data-style]').forEach(b=>b.setAttribute('aria-pressed',String(b===el)));
    tick();
  }));
  if(button)button.addEventListener('click',async()=>{
    if(busy || button.disabled)return;
    if(!pending){
      const bytes=new Uint8Array(16);crypto.getRandomValues(bytes);
      remember({request_id:Array.from(bytes,b=>b.toString(16).padStart(2,'0')).join(''),raid_id:state.raid_id,style:selected,name:state.you.name});
    }
    const receipt=pending.request_id;
    busy=true;error();tick();
    try {
      const {response,value}=await request('/play/api/attack',{method:'POST',headers:{'Content-Type':'application/json','X-CSRF-Token':csrf},
        body:JSON.stringify({request_id:pending.request_id,raid_id:pending.raid_id,style:pending.style})});
      if(value.state)apply(value);
      if(!response.ok){
        // A definitive rejection did not land. A 5xx may have happened after
        // commit, so retain its receipt until a state check resolves it.
        if(response.status<500)remember(null);
        throw new Error(value.error || 'The strike could not be confirmed.');
      }
      strikeFeedback(value.hit,receipt);remember(null);
    } catch(e) {error(e.name==='AbortError'?'The connection timed out. Your hit may have landed. Retry the same strike safely.':e.message);}
    finally {busy=false;tick();void poll();}
  });
  document.addEventListener('visibilitychange',()=>{if(document.hidden)clearTimeout(timer);else void poll();});
  window.addEventListener('online',()=>void poll());
  try {apply(JSON.parse(root.dataset.bossBootstrap));} catch (_) {error('Reload to reconnect to the raid.');}
  if(!admin)setInterval(tick,1000);
  void poll();
})();
