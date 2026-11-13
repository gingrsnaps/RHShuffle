/* Text-only operational log viewer. Never render provider messages as HTML.
   This calls the local ADMIN endpoint only; provider APIs are not polled here. */
(() => {
  'use strict';
  const wrap=document.getElementById('adminOperations');
  if (!wrap) return;
  const id=name=>document.getElementById(name);
  const names={
    refresh_ok:'Source data confirmed',refresh_failed:'Source refresh failed',
    refresh_queued:'Manual refresh queued',settings_saved:'Settings saved',
    connection_test:'API connection tested',backup_export:'Backup downloaded',
    storage_warning:'State storage warning',server_error:'Server request failed',
    worker_started:'Automatic worker started',api_rate_limited:'Rate limit reached',
    data_quality:'Source data quality warning',
    empire_rewards_draft:'EmpireDrop prize draft saved',
    empire_rewards_published:'EmpireDrop prizes published',
    empire_rewards_save_failed:'EmpireDrop prize update rejected'
  };
  const advice={
    access:'Check credentials and permitted server IP addresses.',
    rate_limit:'The provider is limiting requests; automatic retries are scheduled.',
    format:'The provider response format did not match the expected schema.',
    scope:'The selected race is unavailable to this affiliate account.',
    selection:'Choose a race slug when more than one race is running.',
    window:'The provider identified a date parameter problem. Review the saved race window.',
    bad_request:'Shuffle rejected a request parameter (HTTP 400). Verify the dates and affiliate endpoint.',
    configuration:'Review the provider connection settings.',
    connection:'Check the server’s outgoing network connection.',
    connect_timeout:'The provider connection timed out.',
    timeout:'The provider did not answer before the timeout.',
    http:'The provider returned a non-success status.',
    upstream:'The provider’s service is temporarily unavailable.',
    response_limit:'The provider response exceeded limits.',
    redirect:'The provider redirected the request; credentials were not forwarded.',
    credentials:'A required server credential is missing.',
    partial:'Some source rows were incomplete.',
    storage:'Saved data could not be written.',
    empire_settings:'EmpireDrop race connection settings updated.',
    empire_rewards:'EmpireDrop prizes updated.',
    empire_schedule:'EmpireDrop dates updated.',
    shuffle_settings:'Shuffle configuration updated.',
    conflict:'Another tab saved a newer payout revision. Reload before retrying.',
    validation:'One or more payout values were rejected before saving.',
  };
  const when=value=>new Intl.DateTimeFormat('en-US',{
    timeZone:'America/New_York',month:'short',day:'numeric',hour:'numeric',minute:'2-digit',second:'2-digit',timeZoneName:'short'
  }).format(new Date(Number(value)*1000));
  let busy=false, lastEvents=[], lastSummary=null;
  const select=()=>new URLSearchParams({service:id('opsSource').value,level:id('opsLevel').value,limit:'300'});
  const query=()=>select().toString();
  const downloads=()=>{
    id('opsExport').href='/admin/operations/export?'+query();
    id('opsExportTxt').href='/admin/operations/export?'+query()+'&format=txt';
  };
  function text(node,value){node.textContent=String(value);return node;}
  function make(tag,className,value) {
    const node=document.createElement(tag);
    if(className) node.className=className;
    if(value!==undefined) text(node,value);
    return node;
  }
  function draw(events,summary){
    lastEvents=events;lastSummary=summary;
    for (const level of ['success','info','warning','error'])
      text(id('opsTotal'+level.charAt(0).toUpperCase()+level.slice(1)),summary?.levels?.[level]??0);
    text(id('opsTotalEvents'),summary?.total??events.length);
    const term=id('opsSearch').value.trim().toLocaleLowerCase();
    const rows=events.filter(entry=>!term||[entry.event,entry.service,entry.level,entry.code||'',
      String(entry.http_status||'')].join(' ').toLocaleLowerCase().includes(term));
    const out=id('opsEvents');out.replaceChildren();
    for(const item of rows){
      const article=make('article','operations-entry');article.role='listitem';article.dataset.severity=item.level;
      const severity=make('span','operations-severity',item.level.toUpperCase());
      const body=make('div','operations-entry-main');
      const heading=make('div','operations-entry-heading');
      heading.append(make('strong','',names[item.event]||'Operational activity'),
        make('time','',when(item.at)));
      const extras=[item.service.charAt(0).toUpperCase()+item.service.slice(1)];
      if(item.http_status!=null) extras.push('HTTP '+item.http_status);
      if(item.duration_ms!=null) extras.push(item.duration_ms+' ms');
      if(item.count!=null) extras.push(item.count+' records');
      if(Number(item.occurrences)>1) extras.push('Repeated '+item.occurrences+' times');
      body.append(heading,make('small','operations-details',extras.join(' · ')));
      if(item.code&&advice[item.code])body.append(make('p','operations-advice',advice[item.code]));
      article.append(severity,body);out.append(article);
    }
    text(id('opsMessage'),rows.length ? `Showing ${rows.length} of ${events.length} matching stored events.` :
      'No matching events. Try another filter.');
  }
  async function load(){
    if(busy||!wrap.open||document.hidden)return;
    busy=true;downloads();text(id('opsMessage'),'Loading recent events…');
    try{
      const response=await fetch('/admin/operations/events?'+query(),{
        credentials:'same-origin',cache:'no-store',headers:{Accept:'application/json'}
      });
      if([401,403].includes(response.status))throw new Error('Session expired. Sign in again.');
      if(!response.ok)throw new Error('Activity could not be loaded. Check the server status.');
      const payload=await response.json();
      draw(Array.isArray(payload.events)?payload.events:[],payload.summary);
    }catch(err){text(id('opsMessage'),err.message||'Logs are unavailable.');}
    finally{busy=false;}
  }
  wrap.addEventListener('toggle',load);
  for(const el of [id('opsSource'),id('opsLevel')])el.addEventListener('change',load);
  id('opsSearch').addEventListener('input',()=>draw(lastEvents,lastSummary));
  id('opsReload').addEventListener('click',load);
  document.addEventListener('visibilitychange',()=>{if(!document.hidden&&wrap.open)load();});
  window.setInterval(()=>{if(wrap.open&&!document.hidden)load();},30000);
  downloads();if(wrap.open)load();
})();
