/* Real rendered templates; fake clock/transport exercise shared-state behavior. */
const {test}=require('node:test');
const assert=require('node:assert/strict');
const fs=require('node:fs');
const path=require('node:path');
const {JSDOM}=require('jsdom');
const root=path.resolve(__dirname,'..'), fixtures=process.env.DOM_FIXTURES||path.join(root,'.test-fixtures');
const code=fs.readFileSync(path.join(root,'static/boss.js'),'utf8');
const flush=async()=>{for(let i=0;i<8;i++)await new Promise(r=>setImmediate(r));};
const response=(value,status=200)=>({ok:status<400,status,headers:new Map([['content-type','application/json']]),json:async()=>structuredClone(value)});
function page(name='play') {
 const dom=new JSDOM(fs.readFileSync(path.join(fixtures,name+'.html'),'utf8'),{url:'https://example.test/play',runScripts:'outside-only'});
 const w=dom.window,calls=[],timers=new Map(),intervals=new Map();let clock=0,serial=0;
 let value=JSON.parse(fs.readFileSync(path.join(fixtures,'boss.json'),'utf8'));
 Object.defineProperty(w.performance,'now',{value:()=>clock});
 Object.defineProperty(w.document,'hidden',{value:false,configurable:true});
 w.setTimeout=(fn,delay)=>{const id=++serial;timers.set(id,{fn,at:clock+delay});return id;};w.clearTimeout=id=>timers.delete(id);
 w.setInterval=fn=>{const id=++serial;intervals.set(id,fn);return id;};
 let responder=async()=>response(value);
 w.fetch=async(url,options)=>{calls.push({url,options});return responder(url,options);};
 w.eval(code);
 return {w,dom,calls,value,timers,respond(fn){responder=fn;},
 async advance(ms){clock+=ms;for(const [id,t]of [...timers])if(t.at<=clock){timers.delete(id);t.fn();}for(const fn of intervals.values())fn();await flush();},
 close(){dom.window.close();}};
}
test('game markup has unique IDs, visible instructions and no admin footer',async()=>{
 const p=page();await flush();const doc=p.w.document, ids=[...doc.querySelectorAll('[id]')].map(e=>e.id);
 assert.equal(new Set(ids).size,ids.length);assert.match(doc.querySelector('#howToPlay').textContent,/40 attacks/);
 assert.equal(doc.querySelector('footer a[href="/admin"]'),null);
 assert.equal(doc.querySelector('#attackButton').disabled,false);p.close();
});
test('game polls every five seconds and pauses while hidden',async()=>{
 const p=page();await flush();assert.equal(p.calls.length,1);await p.advance(5000);assert.equal(p.calls.length,2);
 Object.defineProperty(p.w.document,'hidden',{value:true,configurable:true});p.w.document.dispatchEvent(new p.w.Event('visibilitychange'));
 await p.advance(10000);assert.equal(p.calls.length,2);
 Object.defineProperty(p.w.document,'hidden',{value:false,configurable:true});p.w.document.dispatchEvent(new p.w.Event('visibilitychange'));await flush();
 assert.equal(p.calls.length,3);assert.ok(p.calls.every(x=>!x.options.method));p.close();
});
test('attack sends only server-validated inputs and renders countdown',async()=>{
 const p=page();await flush();let sent;
 p.respond(async(url,options)=>{
  if(options.method==='POST'){
   sent=JSON.parse(options.body);const s=p.value.state;s.version++;s.hp-=150;s.total_damage=150;s.total_attacks=1;
   s.you.ready_at=s.server_time+60;s.you.last_request=sent.request_id;s.you.last_hit={damage:150,style:sent.style,weakness:true,burst:false};
   return response({ok:true,state:s,hit:s.you.last_hit});
  }return response(p.value);
 });
 p.w.document.querySelector('[data-style="bow"]').click();p.w.document.querySelector('#attackButton').click();await flush();
 assert.deepEqual(Object.keys(sent).sort(),['raid_id','request_id','style']);assert.equal(sent.style,'bow');
 const post=p.calls.find(c=>c.options.method==='POST');assert.equal(post.options.headers['X-CSRF-Token'],p.value.csrf);
 assert.equal(p.w.document.querySelector('#attackButton').disabled,true);
 assert.match(p.w.document.querySelector('#attackButton').textContent,/1:00/);
 assert.match(p.w.document.querySelector('#hitResult').textContent,/150/);p.close();
});
test('uncertain delivery keeps receipt and retry uses same ID',async()=>{
 const p=page();await flush();const ids=[];
 p.respond(async(url,options)=>{if(options.method==='POST'){ids.push(JSON.parse(options.body).request_id);throw new Error('Network disconnected');}return response(p.value);});
 p.w.document.querySelector('#attackButton').click();await flush();
 assert.match(p.w.document.querySelector('#attackButton').textContent,/Retry last strike/);
 p.w.document.querySelector('#attackButton').click();await flush();assert.equal(ids.length,2);assert.equal(ids[0],ids[1]);p.close();
});
test('older polls cannot reverse boss damage',async()=>{
 const p=page();await flush();const old=structuredClone(p.value);
 p.value.state.hp-=250;p.value.state.version++;p.value.state.server_time++;
 await p.advance(5000);assert.equal(p.w.document.querySelector('#bossHealthBar').value,p.value.state.hp);
 p.respond(async()=>response(old));await p.advance(5000);
 assert.equal(p.w.document.querySelector('#bossHealthBar').value,p.value.state.hp);p.close();
});
test('victory and paused raids stop attacks, hostile names render as text',async()=>{
 const p=page();await flush();p.value.state.status='paused';
 p.value.state.leaders=[{name:'<img src=x onerror=alert(1)>',damage:100,attacks:1,you:false}];await p.advance(5000);
 assert.equal(p.w.document.querySelector('#attackButton').disabled,true);
 assert.equal(p.w.document.querySelector('#bossLeaders img'),null);
 p.value.state.status='victory';p.value.state.hp=0;await p.advance(5000);
 assert.match(p.w.document.querySelector('#attackButton').textContent,/Victory/);
 assert.match(p.w.document.querySelector('#bossStory').textContent,/Red crew/);p.close();
});
test('admin boss updates preserve difficulty draft and restart confirmation',async()=>{
 const p=page('boss');await flush();const input=p.w.document.querySelector('#bossHealthInput');input.value='5000000';
 const confirm=p.w.document.querySelector('[name="confirm_restart"]');confirm.checked=true;
 await p.advance(5000);assert.equal(input.value,'5000000');assert.equal(confirm.checked,true);
 assert.equal(p.w.document.querySelector('footer'),null);p.close();
});

test('a successful background poll cannot erase an attack error',async()=>{
 const p=page();await flush();
 p.respond(async(url,options)=>options.method==='POST'?response({error:'Your shared connection is cooling down.'},429):response(p.value));
 p.w.document.querySelector('#attackButton').click();await flush();
 await p.advance(5000);await p.advance(5000);
 const error=p.w.document.querySelector('#bossError');
 assert.equal(error.hidden,false);assert.match(error.textContent,/shared connection/);
 p.w.document.querySelector('#dismissBossError').click();assert.equal(error.hidden,true);p.close();
});

test('unchanged contributor rows survive polls and mobile styles share attack controls',async()=>{
 const p=page();await flush();
 p.value.state.leaders=[{name:'Raider ABCDEF12',damage:150,attacks:1,you:false}];await p.advance(5000);
 const row=p.w.document.querySelector('#bossLeaders li');await p.advance(5000);
 assert.strictEqual(p.w.document.querySelector('#bossLeaders li'),row);
 const style=p.w.document.querySelector('#dockStyle');style.value='magic';style.dispatchEvent(new p.w.Event('change'));
 assert.equal(p.w.document.querySelector('[data-style="magic"]').getAttribute('aria-pressed'),'true');
 let sent;p.respond(async(url,options)=>{if(options.method==='POST'){sent=JSON.parse(options.body);return response({error:'Fixture rejection'},400);}return response(p.value);});
 p.w.document.querySelector('#dockAttack').click();await flush();assert.equal(sent.style,'magic');p.close();
});

test('copy link supplies selectable text if clipboard access is unavailable',async()=>{
 const p=page();await flush();p.w.document.querySelector('#copyRaidLink').click();await flush();
 const field=p.w.document.querySelector('#shareUrl');assert.equal(field.hidden,false);
 assert.equal(field.value,'https://example.test/play');assert.equal(field.selectionEnd,field.value.length);p.close();
});

test('same-raid updates cannot refill health even with a newer version or clock',async()=>{
 const p=page();await flush();
 p.value.state.hp-=150;p.value.state.total_damage=150;p.value.state.total_attacks=1;p.value.state.version++;
 await p.advance(5000);const hp=p.value.state.hp;
 p.value.state.hp+=150;p.value.state.total_damage=0;p.value.state.total_attacks=0;
 for(const versionBump of [0,10]){
  p.value.state.version+=versionBump;p.value.state.server_time+=5;
  await p.advance(5000);assert.equal(p.w.document.querySelector('#bossHealthBar').value,hp);
  assert.equal(p.w.document.querySelector('#bossDamage').textContent,'150');
 }
 p.close();
});

test('victory stays at zero until a different raid starts',async()=>{
 const p=page();await flush();
 p.value.state.hp=0;p.value.state.total_damage=p.value.state.max_hp;p.value.state.status='victory';p.value.state.version++;
 await p.advance(5000);assert.equal(p.w.document.querySelector('#bossHealthBar').value,0);
 p.value.state.hp=p.value.state.max_hp;p.value.state.total_damage=0;p.value.state.status='waiting';p.value.state.version++;
 await p.advance(5000);assert.equal(p.w.document.querySelector('#bossHealthBar').value,0);
 p.value.state.raid_id='new-host-started-raid';p.value.state.server_time+=10;
 await p.advance(5000);assert.equal(p.w.document.querySelector('#bossHealthBar').value,p.value.state.max_hp);
 p.close();
});
