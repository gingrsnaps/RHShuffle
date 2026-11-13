/* Dependency-free responsive menu regression test. */
const assert = require('node:assert/strict');
const fs = require('node:fs');
const vm = require('node:vm');
class Element {
  constructor() {this.handlers={};this.dataset={};this.attrs={};this.open=false;}
  addEventListener(type,listener){(this.handlers[type] ||= []).push(listener)}
  fire(type,event={}){for (const fn of this.handlers[type]||[])fn(event)}
  setAttribute(key,value){this.attrs[key]=value}
  getAttribute(key){return this.attrs[key]}
  contains(){return false}
  focus(){this.focused=true}
}
const toggle=new Element(),nav=new Element(),more=new Element();
const doc = new Element();
doc.getElementById = id=>({publicMenuToggle:toggle,publicPrimaryNav:nav,publicMore:more})[id];
let narrow = true;
const mq = new Element();
const win = {matchMedia:query=>query.includes('max-width')?{matches:narrow}:mq};
vm.runInNewContext(fs.readFileSync('static/public-control.js','utf8'),{document:doc,window:win});
toggle.fire('click');
assert.equal(nav.dataset.open,'true');
assert.equal(toggle.getAttribute('aria-expanded'),'true');
more.open=true;
doc.fire('keydown',{key:'Escape'});
assert.equal(toggle.getAttribute('aria-expanded'),'false');
assert.equal(nav.dataset.open,'false');
toggle.fire('click');
nav.fire('click',{target:{closest:x=> x==='a'}});
assert.equal(nav.dataset.open,'false');
toggle.fire('click');
more.open=true;
mq.fire('change',{matches:true});
assert.equal(nav.dataset.open,'false');
assert.equal(more.open,false);
console.log('Public navigation: 4 behavior checks passed');
