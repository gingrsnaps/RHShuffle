const test=require('node:test');
const assert=require('node:assert/strict');
const fs=require('node:fs');
const vm=require('node:vm');

class Classes{constructor(){this.s=new Set()} add(...v){v.forEach(x=>this.s.add(x))} remove(...v){v.forEach(x=>this.s.delete(x))} toggle(v,on){if(on)this.s.add(v);else this.s.delete(v)} contains(v){return this.s.has(v)}}
class El{
  constructor(text=''){this.textContent=text;this.dataset={};this.classList=new Classes();this.hidden=false;this.children=[];this.lastChild={textContent:text};this.offsetWidth=10}
  querySelector(sel){return this.map?.[sel]||null}
  append(node){this.children.push(node);this.lastChild=node}
}
function slot(rank,name,wager,prize){
  const place=new El(String(rank).padStart(2,'0')); const number=new El(place.textContent); place.map={'[data-place-number]':number};
  const e=new El(); e.map={'.placement, .rank':place,'[data-name]':new El(name),'[data-wager]':new El(wager),'[data-prize]':new El(prize)}; return {e,place,number};
}

function headers(values){return {get(name){return values[name]??values[name.toLowerCase()]??null}}}

function makeHarness(){
  const slots={1:slot(1,'Al******','$100.00','$1,800.00'),2:slot(2,'Br******','$90.00','$1,200.00')};
  const syncShuffle=new El(); syncShuffle.children=[new El()]; syncShuffle.lastChild={textContent:'Live standings · connecting'};
  const syncEmpire=new El(); syncEmpire.children=[new El()]; syncEmpire.lastChild={textContent:'Live standings · connecting'};
  const ids={shuffleLiveSyncStatus:syncShuffle,empireLiveSyncStatus:syncEmpire,empireBoard:new El(),empireRankingCoverage:new El(),empireMessage:new El()};
  ids.empireBoard.querySelector=()=>null;
  const boot={release:'v25',runtime_id:'r1',movement_window_seconds:45,server_time:100,
    shuffle:{},shuffle_revision:'a',shuffle_sequence:1,shuffle_movement_sequence:0,shuffle_movement_count:0,shuffle_changed_at:100,
    provider_timing:{shuffle:{updated_at:100,next_check:190,refresh_interval:90}},freshness:{updated_at:100},
    top15:[{rank:1,username:'Al******',wager:'$100.00'},{rank:2,username:'Br******',wager:'$90.00'},...Array.from({length:13},(_,i)=>({rank:i+3,username:'Open position',wager:'$0.00',open:true}))],
    site:{prizes:{'1':'1800','2':'1200'},total_prize:'$4,000.00'},empiredrop:{rows:[],standings_sequence:0,movement_sequence:0,prizes:{enabled:false}}};
  const document={
    body:{dataset:{page:'public',bootstrap:JSON.stringify(boot)}}, hidden:false,
    getElementById:name=>ids[name]||null,
    querySelectorAll:sel=>{const m=sel.match(/^#shuffleBoard \[data-rank="(\d+)"\]$/);return m&&slots[Number(m[1])]?[slots[Number(m[1])].e]:[]},
    querySelector:()=>null,
    addEventListener(){}, dispatchEvent(){},
  };
  const scheduled=[];
  const timers={
    setTimeout(fn,ms){const id={fn,ms};scheduled.push(id);return id}, clearTimeout(){}, setInterval(){return 1}, clearInterval(){},
  };
  const movement=[];
  const update={release:'v25',runtime_id:'r1',movement_window_seconds:45,server_time:105,
    shuffle:{standings_revision:'b',standings_sequence:2,movement_sequence:1,movement_count:2,updated_at:105,next_check_at:190,refresh_interval:90,prizes:{'1':'1800','2':'1200'},top15:[
      {rank:1,username:'Br******',wager:'$120.00',movement:1,movement_event:{event_id:'e1',direction:'up',kind:'up',places:1,previous_rank:2,current_rank:1,changed_at:105,expires_at:150}},
      {rank:2,username:'Al******',wager:'$110.00',movement:-1,movement_event:{event_id:'e2',direction:'down',kind:'down',places:1,previous_rank:1,current_rank:2,changed_at:105,expires_at:150}},
      ...Array.from({length:13},(_,i)=>({rank:i+3,username:'Open position',wager:'$0.00',open:true}))]},
    empiredrop:{rows:[],standings_sequence:0,movement_sequence:0,prizes:{enabled:false}}};
  const fetch=async()=>({ok:true,status:200,headers:headers({'X-Server-Time':'105','content-type':'application/json','ETag':'"b"'}),json:async()=>update});
  const context={document,window:{addEventListener(){}},globalThis:null,fetch,CustomEvent:function(){},Intl,Date,console,
    RedRankMovement:{render(host,row){movement.push({host,row})},expireAll(){}},...timers};
  context.globalThis=context;
  return {context,scheduled,slots,movement};
}

test('dedicated feed is five seconds and never reloads/navigates',()=>{
  const source=fs.readFileSync('static/live-standings.js','utf8');
  assert.match(source,/const SYNC_MS = 5000/);
  assert.match(source,/fetch\('\/public-standings'/);
  assert.doesNotMatch(source,/location\.reload|location\.href|window\.location/);
});

test('open page applies a newer standings sequence in place and sends movement rows to renderer',async()=>{
  const h=makeHarness();
  vm.runInNewContext(fs.readFileSync('static/live-standings.js','utf8'),h.context);
  const first=h.scheduled.find(x=>x.ms===50); assert.ok(first,'initial live poll scheduled');
  first.fn();
  await new Promise(r=>setImmediate(r)); await new Promise(r=>setImmediate(r));
  assert.equal(h.slots[1].e.map['[data-name]'].textContent,'Br******');
  assert.equal(h.slots[1].e.map['[data-wager]'].textContent,'$120.00');
  assert.equal(h.slots[2].e.map['[data-name]'].textContent,'Al******');
  assert.ok(h.movement.some(x=>x.row?.movement_event?.event_id==='e1'));
  assert.ok(h.movement.some(x=>x.row?.movement_event?.event_id==='e2'));
  assert.ok(h.scheduled.some(x=>x.ms===5000),'next live sync scheduled at five seconds');
});
