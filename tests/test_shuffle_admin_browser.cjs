/* Browser-like regression for the invalid Intl option combination in admin cards. */
const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');
const vm = require('node:vm');
const root = path.join(__dirname,'..');
const nodes = new Map();
const forSelector = s => { if(s==='[data-provider-search]')return []; if(!nodes.has(s)) nodes.set(s, [{textContent: '', dataset: {}}]); return nodes.get(s); };
const sandbox = {
  document: { querySelectorAll: forSelector, querySelector:()=>null },
  globalThis: null,
  Intl, Date, String, Object,
};
sandbox.globalThis=sandbox;
vm.runInNewContext(fs.readFileSync(path.join(root,'static/admin-providers.js'),'utf8'),sandbox);
assert.equal(typeof sandbox.RedProviderCards.render,'function');
sandbox.RedProviderCards.render({providers: {
  shuffle:{state:'warning',status:'Needs attention',last_success:1794375291,last_attempt:1794375510,
           participants:0, quality:'Waiting',metric:'Weighted wager',refresh_seconds:60,issues:[]},
  empiredrop:{state:'good',status:'Connected',last_success:1794375291,last_attempt:1794375291,
           participants:10,quality:'10 verified players',metric:'Wagered',refresh_seconds:300,issues:[]}
}});
assert.match(forSelector('[data-provider-field="shuffle:last_success"]')[0].textContent,/2026/);
assert.match(forSelector('[data-provider-field="empiredrop:last_attempt"]')[0].textContent,/2026/);
assert.equal(forSelector('[data-provider-state="empiredrop"]')[0].textContent,'Connected');
assert.equal(forSelector('[data-provider-field="empiredrop:participants"]')[0].textContent,'10');
// The EmpireDrop controller has its own formatter. Ensure neither uses the
// unsupported dateStyle/timeStyle plus timeZoneName option combination.
for(const f of ['admin-providers.js','admin-empiredrop.js']){
  const source=fs.readFileSync(path.join(root,'static',f),'utf8');
  assert.ok(!source.includes('dateStyle:'));
  assert.ok(source.includes("timeZoneName:'short'"));
}
console.log('PASS Admin timestamps and independent provider cards');
