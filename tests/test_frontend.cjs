/* Optional development checks. The deployed app does not use Node or jsdom. */
const {test} = require('node:test');
const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');
const {JSDOM, VirtualConsole} = require('jsdom');
const root = path.resolve(__dirname, '..');
const fixtures = process.env.DOM_FIXTURES || path.join(root, '.test-fixtures');
const code = fs.readFileSync(path.join(root, 'static/app.js'), 'utf8');
const data = name => JSON.parse(fs.readFileSync(path.join(fixtures, name+'.json'), 'utf8'));
const flush = async () => {for (let n=0; n<5; n++) await new Promise(resolve=>setImmediate(resolve));};

function page(name, feed=data(name==='public'?'public':'admin')) {
  const errors=[];
  const console = new VirtualConsole().on('jsdomError', error=>errors.push(error.message));
  const dom = new JSDOM(fs.readFileSync(path.join(fixtures,name+'.html'),'utf8'), {
    url:'https://example.test/'+(name==='public'?'':'admin?tab='+name), runScripts:'outside-only', virtualConsole:console,
  });
  const window=dom.window, calls=[], timers=new Map(), intervals=new Map();
  let now=feed.server_time*1000, serial=0;
  window.Date.now=()=>now;
  Object.defineProperty(window.document,'hidden',{value:false,configurable:true});
  window.setTimeout=(fn,delay)=>{const id=++serial;timers.set(id,{fn,at:now+delay,delay});return id;};
  window.clearTimeout=id=>timers.delete(id);
  window.setInterval=(fn,delay)=>{const id=++serial;intervals.set(id,{fn,delay});return id;};
  window.clearInterval=id=>intervals.delete(id);
  let responder=async()=>({status:200,ok:true,headers:new Map([['content-type','application/json']]),json:async()=>structuredClone(feed)});
  window.fetch=async(url,options)=>{calls.push({url:String(url),options,at:now});return responder(url,options);};
  window.confirm=()=>true;
  window.eval(code);
  return {window, dom, calls, errors, feed, timers, intervals,
    respond(fn){responder=fn;},
    async advance(ms){now+=ms;for(const [id,timer] of [...timers])if(timer.at<=now){timers.delete(id);timer.fn();}await flush();},
    async tick(){for(const timer of intervals.values())timer.fn();await flush();},
    close(){dom.window.close();},
  };
}

for(const name of ['public','login','overview','race','players','settings','error']) {
  test(name+' has unique IDs, connected labels, and no script errors',async()=>{
    const p=page(name);await flush();
    const ids=[...p.window.document.querySelectorAll('[id]')].map(node=>node.id);
    assert.equal(new Set(ids).size,ids.length,'Duplicate element ID');
    for(const label of p.window.document.querySelectorAll('label[for]'))assert.ok(p.window.document.getElementById(label.htmlFor));
    assert.equal(p.window.document.querySelectorAll('main').length,1);
    assert.deepEqual(p.errors,[]);p.close();
  });
}

test('public and admin automatically poll at the 60-second cadence',async()=>{
  for(const name of ['public','overview']) {
    const p=page(name);await flush();assert.equal(p.calls.length,1);
    await p.advance(60000);await p.advance(60000);
    assert.deepEqual(p.calls.map(c=>c.at-p.calls[0].at),[0,60000,120000]);p.close();
  }
});

test('repeated refreshes preserve the dashboard and unsaved race draft',async()=>{
  const p=page('race');await flush();
  const form=p.window.document.getElementById('raceForm'),field=form.querySelector('[name=race_title]');
  field.value='My unsaved race title';field.dispatchEvent(new p.window.Event('input',{bubbles:true}));
  for(let i=0;i<4;i++){p.feed.site.race_title='Saved title '+i;await p.advance(60000);}
  assert.strictEqual(p.window.document.getElementById('raceForm'),form);
  assert.equal(field.value,'My unsaved race title');assert.ok(p.window.document.body.textContent.includes('Race'));
  assert.notEqual(p.window.document.body.textContent.trim().toLowerCase(),'not yet');
  assert.deepEqual(p.errors,[]);p.close();
});

test('Code Red expands, searches, updates, and renders usernames as text',async()=>{
  const p=page('players');await flush();
  const details=p.window.document.getElementById('codeRed');details.open=true;
  details.dispatchEvent(new p.window.Event('toggle'));await flush();
  assert.ok(p.calls.at(-1).url.includes('code_red=1'));
  assert.equal(p.window.document.querySelectorAll('#redBody tr').length,100);
  assert.equal(p.window.document.querySelectorAll('#redBody img,#participantsBody img').length,0);
  const search=p.window.document.getElementById('redSearch');search.value='ExamplePlayer010';
  search.dispatchEvent(new p.window.Event('input'));
  assert.equal(p.window.document.querySelectorAll('#redBody tr:not([hidden])').length,1);
  p.feed.red[0].weighted='$555.00';await p.advance(60000);
  assert.equal(search.value,'ExamplePlayer010');assert.equal(details.open,true);
  assert.equal(p.window.document.querySelectorAll('#redBody tr:not([hidden])').length,1);p.close();
});

test('session and proxy errors retain rendered content and retry',async()=>{
  const p=page('players');await flush();const html=p.window.document.getElementById('participantsBody').innerHTML;
  p.respond(async()=>({status:401,ok:false}));await p.advance(60000);
  assert.match(p.window.document.getElementById('networkError').textContent,/session expired/);
  assert.equal(p.window.document.getElementById('participantsBody').innerHTML,html);
  p.respond(async()=>({status:502,ok:false,headers:new Map([['content-type','text/html']])}));await p.advance(60000);
  assert.match(p.window.document.getElementById('networkError').textContent,/HTTP 502/);
  assert.equal(p.window.document.getElementById('participantsBody').innerHTML,html);assert.equal(p.calls.length,3);p.close();
});

test('race state transitions use the server clock without waiting for polling',async()=>{
  const feed=data('public');feed.site.start_time=feed.server_time+10;feed.site.end_time=feed.server_time+20;
  const p=page('public',feed);await flush();assert.equal(p.window.document.getElementById('raceBadge').textContent,'Upcoming');
  await p.advance(11000);await p.tick();assert.equal(p.window.document.getElementById('raceBadge').textContent,'Active');
  await p.advance(10000);await p.tick();assert.equal(p.window.document.getElementById('raceBadge').textContent,'Ended');p.close();
});

test('manual check polls quickly then returns to the minute cadence',async()=>{
  const p=page('overview');await flush();let post=false;
  p.respond(async(url,options)=>{
    const value=options.method==='POST'?(post=true,{message:'Check queued'}):p.feed;
    return {status:200,ok:true,headers:new Map([['content-type','application/json']]),json:async()=>structuredClone(value)};
  });
  p.feed.jobs.shuffle.state='queued';
  p.window.document.querySelector('[data-refresh]').dispatchEvent(new p.window.Event('submit',{cancelable:true,bubbles:true}));await flush();
  assert.equal(post,true);const first=p.calls.length;await p.advance(2000);assert.equal(p.calls.length,first+1);
  p.feed.jobs.shuffle.state='scheduled';p.feed.jobs.kick.state='scheduled';await p.advance(2000);
  await p.advance(56000);assert.equal(p.calls.at(-1).at-p.calls[0].at,60000);p.close();
});

test('a named action control cannot redirect a refresh to the wrong URL',async()=>{
  const p=page('overview');await flush();
  try {
    for(const form of p.window.document.querySelectorAll('[data-refresh]')) {
      // jsdom omits this native-browser named-property behavior. Model the
      // actual input collision explicitly, then verify the request destination.
      const control=form.querySelector('[name="action"]');
      Object.defineProperty(form,'action',{configurable:true,value:control});
      p.respond(async(url,options)=>{
        const valid=options.method!=='POST'||new URL(String(url),p.window.location.href).pathname==='/admin/action';
        return {status:valid?200:404,ok:valid,headers:new Map([['content-type',valid?'application/json':'text/html']]),
          json:async()=>structuredClone(options.method==='POST'?{message:'Check requested'}:p.feed)};
      });
      form.dispatchEvent(new p.window.Event('submit',{cancelable:true,bubbles:true}));await flush();
      const sent=p.calls.filter(call=>call.options.method==='POST').at(-1);
      assert.equal(new URL(sent.url,p.window.location.href).pathname,'/admin/action');
      assert.equal(sent.options.body.get('action'),'refresh');
      assert.equal(sent.options.body.get('csrf'),'fixture-csrf');
      assert.equal(sent.options.headers.Accept,'application/json');
      assert.equal(form.querySelector('button').disabled,false);
      assert.match(p.window.document.getElementById('toast').textContent,/Check requested/);
    }
  } finally {p.close();}
});

test('refresh explains a rejected form and re-enables the button',async()=>{
  const p=page('overview');await flush();
  try {
    p.respond(async()=>({status:400,ok:false,headers:new Map([['content-type','application/json']]),
      json:async()=>({error:'This form expired. Reload the page and try again.'})}));
    const form=p.window.document.querySelector('[data-refresh]');
    form.dispatchEvent(new p.window.Event('submit',{cancelable:true,bubbles:true}));await flush();
    assert.match(p.window.document.getElementById('toast').textContent,/form expired.*HTTP 400/);
    assert.equal(form.querySelector('button').disabled,false);
  } finally {p.close();}
});

test('empty-board explanation clears when live rows arrive on either page',async()=>{
  for(const name of ['public','players']) {
    const feed=data(name==='public'?'public':'admin');
    const values=structuredClone(name==='public'?feed.rows:feed.participants);
    feed.rows=[];feed.participants=[];feed.leaderboard_message='Waiting for Shuffle data.';
    const p=page(name,feed);await flush();
    try {
      const message=p.window.document.getElementById('leaderboardMessage');
      assert.equal(message.hidden,false);assert.match(message.textContent,/Waiting for Shuffle/);
      feed.leaderboard_message='';if(name==='public')feed.rows=values;else feed.participants=values;
      await p.advance(60000);
      assert.equal(message.hidden,true);
      if(name==='public')assert.equal(p.window.document.querySelector('[data-rank="1"] [data-name]').textContent,values[0].username);
      else assert.equal(p.window.document.querySelector('#participantsBody strong').textContent,values[0].username);
    } finally {p.close();}
  }
});

test('stylesheet parses and includes responsive and reduced-motion rules',()=>{
  const css=fs.readFileSync(path.join(root,'static/style.css'),'utf8');
  const parsed=require('rrweb-cssom').parse(css);
  assert.ok(parsed.cssRules.length>50);assert.match(css,/prefers-reduced-motion/);assert.match(css,/@media/);
});

test('publishing dates automatically follows queued work and shows the saved window',async()=>{
  const feed=data('admin');
  Object.assign(feed.jobs.shuffle,{state:'queued',pending:true,requested:1,completed:0,next_check:feed.server_time});
  const p=page('race',feed);await flush();
  try {
    assert.match(p.window.document.getElementById('shuffleProgress').textContent,/Refresh queued/);
    const published=p.window.document.getElementById('publishedWindow').textContent;
    const field=p.window.document.querySelector('[name="start_et"]');
    field.value='2030-01-01T18:00';field.dispatchEvent(new p.window.Event('input',{bubbles:true}));
    Object.assign(feed.jobs.shuffle,{state:'checking',pending:false,runs:1});
    await p.advance(2000);
    assert.equal(p.calls.length,2);assert.match(p.window.document.getElementById('shuffleProgress').textContent,/Checking the provider now/);
    Object.assign(feed.jobs.shuffle,{state:'scheduled',completed:1,result:'updated',completed_at:feed.server_time+3,next_check:feed.server_time+60});
    await p.advance(2000);
    assert.match(p.window.document.getElementById('shuffleProgress').textContent,new RegExp('Published '+feed.count+' qualifying players'));
    assert.equal(p.window.document.getElementById('publishedWindow').textContent,published);
    assert.equal(field.value,'2030-01-01T18:00');
    assert.equal(p.calls.filter(c=>c.options.method==='POST').length,0);
  } finally {p.close();}
});

test('a queued provider retry shows both its reason and the scheduled time on every tab',async()=>{
  for(const name of ['overview','race','players','settings']) {
    const feed=data('admin');
    Object.assign(feed.jobs.shuffle,{state:'queued',pending:true,requested:1,completed:0,
      next_check:feed.server_time+120,error:'Shuffle rate limit reached.',http_status:429,retry_after:120});
    const p=page(name,feed);await flush();
    try {
      const message=p.window.document.getElementById('shuffleProgress').textContent;
      assert.match(message,/Retry scheduled/);assert.match(message,/HTTP 429/);assert.match(message,/rate limit/);
      await p.advance(2000);assert.equal(p.calls.length,1,'Respect the provider cooldown without fast browser polling');
    } finally {p.close();}
  }
});

test('a manual refresh during an in-flight status read schedules an immediate follow-up',async()=>{
  const p=page('overview');await flush();
  try {
    let release, held=false;
    p.respond(async(url,options)=>{
      if(options.method!=='POST'&&!held) {held=true;return new Promise(resolve=>{release=resolve;});}
      const value=options.method==='POST'?{message:'Refresh queued',runtime_id:p.feed.runtime_id,requests:{shuffle:1}}:p.feed;
      return {status:200,ok:true,headers:new Map([['content-type','application/json']]),json:async()=>structuredClone(value)};
    });
    await p.advance(60000);assert.equal(held,true);
    p.window.document.querySelector('[data-refresh]').dispatchEvent(new p.window.Event('submit',{cancelable:true,bubbles:true}));await flush();
    release({status:200,ok:true,headers:new Map([['content-type','application/json']]),json:async()=>structuredClone(p.feed)});await flush();
    const before=p.calls.length;await p.advance(50);assert.equal(p.calls.length,before+1);
    Object.assign(p.feed.jobs.shuffle,{completed:1,result:'updated',completed_at:p.feed.server_time+61});
    await p.advance(60000);
    assert.match(p.window.document.getElementById('toast').textContent,/Refresh finished\. See the update result/);
  } finally {p.close();}
});
