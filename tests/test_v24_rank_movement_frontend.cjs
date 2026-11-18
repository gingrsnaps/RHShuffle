const test=require('node:test');
const assert=require('node:assert/strict');
const fs=require('node:fs');
const vm=require('node:vm');

class El {
  constructor(){this.children=[];this.dataset={};this.attrs={};this.textContent='';this.className='';this.parent=null;}
  append(child){child.parent=this;this.children.push(child);}
  querySelector(sel){
    if(sel==='[data-rank-movement]') return this.children.find(x=>Object.hasOwn(x.dataset,'rankMovement'))||null;
    if(sel==='.placement, .rank') return null;
    return null;
  }
  querySelectorAll(sel){
    const out=[];
    const visit=n=>{for(const c of n.children){if(sel==='[data-rank-movement][data-expires-at]'&&Object.hasOwn(c.dataset,'rankMovement')&&c.dataset.expiresAt)out.push(c);visit(c)}};
    visit(this);return out;
  }
  setAttribute(k,v){this.attrs[k]=v;}
  remove(){if(this.parent)this.parent.children=this.parent.children.filter(x=>x!==this);this.parent=null;}
}

function load(){
  const timers=[];
  const document={createElement:()=>new El()};
  const context={document,globalThis:{},Date,setTimeout:(fn,ms)=>{timers.push({fn,ms});return fn;},clearTimeout:()=>{}};
  context.globalThis=context;
  vm.runInNewContext(fs.readFileSync('static/rank-movement.js','utf8'),context);
  return {api:context.RedRankMovement,timers,document};
}

test('up/down/new indicators use exact server expiration and 45 second default',()=>{
  const {api}=load();
  assert.equal(api.DEFAULT_WINDOW_SECONDS,45);
  const upHost=new El();
  let badge=api.render(upHost,{movement:2,movement_at:100,movement_expires_at:145},{nowMs:120000,newAriaLabel:'New Top 15'});
  assert.equal(badge.textContent,'↑2');
  assert.equal(badge.dataset.expiresAt,'145000');
  assert.equal(badge.attrs['aria-label'],'Up 2 positions');
  const downHost=new El();
  badge=api.render(downHost,{movement:-1,movement_at:100,movement_expires_at:145},{nowMs:120000});
  assert.equal(badge.textContent,'↓1');
  const newHost=new El();
  badge=api.render(newHost,{new_entry:true,movement_at:100,movement_expires_at:145},{nowMs:120000,newAriaLabel:'New in the Top 15'});
  assert.equal(badge.textContent,'NEW');
  assert.equal(badge.attrs['aria-label'],'New in the Top 15');
});

test('polling does not restart the server-authored 45 second window',()=>{
  const {api}=load();
  const host=new El();
  const row={movement:1,movement_at:100,movement_expires_at:145};
  let badge=api.render(host,row,{nowMs:130000});
  assert.equal(badge.dataset.expiresAt,'145000');
  badge=api.render(host,row,{nowMs:140000});
  assert.equal(badge.dataset.expiresAt,'145000');
  assert.equal(host.children.length,1);
  assert.equal(api.render(host,row,{nowMs:145001}),null);
  assert.equal(host.children.length,0);
});

test('same rank/no movement creates no badge and wake cleanup removes expired badges',()=>{
  const {api}=load();
  const host=new El();
  assert.equal(api.render(host,{movement:0,new_entry:false,movement_at:0},{nowMs:100000}),null);
  api.render(host,{movement:-2,movement_at:100,movement_expires_at:145},{nowMs:120000});
  assert.equal(host.children.length,1);
  api.expireAll(host,145001);
  assert.equal(host.children.length,0);
});
