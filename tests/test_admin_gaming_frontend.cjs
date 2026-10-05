/* Private dashboard regression checks using real server-rendered fixture HTML. */
const {test,after}=require('node:test'),assert=require('node:assert/strict'),fs=require('node:fs'),path=require('node:path');
const {JSDOM}=require('jsdom');
const root=path.resolve(__dirname,'..');
let directory=process.env.GAMING_ADMIN_FIXTURES;
if(!directory){
 directory=fs.mkdtempSync(path.join(require('node:os').tmpdir(),'red-gaming-test-'));
 after(()=>fs.rmSync(directory,{recursive:true,force:true}));
 require('node:child_process').execFileSync(process.env.RH_TEST_PYTHON||'python3',
  [path.join(__dirname,'serve_admin_gaming_fixture.py'),'--write-fixtures',directory],{stdio:'pipe'});
}
const code=fs.readFileSync(path.join(root,'static/admin-gaming.js'),'utf8');
const tick=async()=>{for(let n=0;n<8;n++)await new Promise(resolve=>setImmediate(resolve));};
function make(){
 const data=JSON.parse(fs.readFileSync(path.join(directory,'state.json'),'utf8'));
 const dom=new JSDOM(fs.readFileSync(path.join(directory,'admin.html'),'utf8'),{url:'https://example.test/admin/gaming',runScripts:'outside-only'});
 const w=dom.window,timers=new Map();let serial=0;
 Object.defineProperty(w.document,'hidden',{value:false,configurable:true});
 w.setTimeout=(fn,delay)=>{timers.set(++serial,{fn,delay});return serial;};w.clearTimeout=id=>timers.delete(id);
 let response=()=>({ok:true,status:200,headers:new Map([['content-type','application/json'],['etag','saved']]),json:async()=>structuredClone(data)});
 w.fetch=async()=>response();w.eval(code);
 return {w,dom,data,timers,respond(fn){response=fn;}};
}
test('all eight top-five lists, exact full counts, IPs and no duplicate DOM IDs',async()=>{
 const p=make();await tick();
 for(const game of ['dice','keno','plinko','blackjack','limbo','coinflip','poker','baccarat']) {
  assert.equal(p.w.document.querySelectorAll('#gamingLeaders-'+game+' li').length,5);
  assert.match(p.w.document.getElementById('gamingCount-'+game).textContent,/Players: 7.*rounds: 7/);
  assert.match(p.w.document.getElementById('gamingLeaders-'+game).textContent,/192\.0\.2\./);
 }
 const ids=[...p.w.document.querySelectorAll('[id]')].map(n=>n.id);assert.equal(ids.length,new Set(ids).size);
 assert.equal(p.w.document.getElementById('gamingNoRecords').hidden,true);
 assert.ok([...p.timers.values()].some(t=>t.delay===5000));p.dom.window.close();
});
test('expired admin clears private rows and cannot be repopulated by a late response',async()=>{
 const p=make();await tick();p.respond(()=>({ok:false,status:401,headers:new Map()}));
 p.w.document.getElementById('refreshGaming').click();await tick();
 assert.equal(p.w.document.querySelectorAll('[id^=gamingLeaders-] li').length,0);
 assert.equal(p.w.document.getElementById('gamingAdminSession').hidden,false);
 assert.equal(p.w.document.getElementById('gamingAdmin').hasAttribute('data-rankings'),false);
 assert.equal(p.w.document.getElementById('refreshGaming').disabled,true);
 assert.doesNotMatch(p.w.document.getElementById('gamingAdmin').textContent,/TestPlayer|192\.0\.2\./);
 p.w.RedGamingAdmin.render(p.data);
 assert.equal(p.w.document.querySelectorAll('[id^=gamingLeaders-] li').length,0);p.dom.window.close();
});
test('mixed release reports a reload message instead of claiming a fresh update',async()=>{
 const p=make();await tick();p.respond(()=>({ok:true,status:200,headers:new Map([['content-type','application/json']]),json:async()=>({...p.data,release:'different-release'})}));
 p.w.document.getElementById('refreshGaming').click();await tick();
 assert.match(p.w.document.getElementById('gamingAdminChecked').textContent,/release changed.*Reload/);
 assert.equal(p.w.document.querySelectorAll('#gamingLeaders-blackjack li').length,5);p.dom.window.close();
});
