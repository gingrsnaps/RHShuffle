/* Regression tests for the real public EmpireDrop renderer.
 * Runs under Node without a browser, live credentials, or external services.
 * The simulated DOM includes payout elements: the old test omitted these and
 * therefore never exercised the ReferenceError that stopped the public board.
 */
const test = require('node:test');
const assert = require('node:assert/strict');
const fs = require('node:fs');
const vm = require('node:vm');
const path = require('node:path');

const SCRIPT = fs.readFileSync(path.join(__dirname, '..', 'static', 'empiredrop.js'), 'utf8');

function harness(bootstrap) {
  const handlers = {};
  const elements = {};
  const slots = {};
  const metrics = [];
  class Element {
    constructor(id, panel) {
      this.id = id;
      this.tabIndex = 0;
      this.hidden = false;
      this.textContent = '';
      this.attributes = {'aria-controls': panel};
      this.classList = {toggle: (name, active) => { this.active = active; }};
    }
    setAttribute(name, value) { this.attributes[name] = value; }
    getAttribute(name) { return this.attributes[name]; }
    addEventListener(name, fn) { handlers[this.id + ':' + name] = fn; }
    focus() { this.focused = true; }
    querySelector(selector) {
      const match = selector.match(/^\[data-empire-place="(\d+)"\]$/);
      return match ? slots[`${match[1]}:place`] : null;
    }
  }
  for (const [id, panel] of [
    ['shuffleTab', 'shuffleBoard'], ['empireTab', 'empireBoard']
  ]) elements[id] = new Element(id, panel);
  for (const id of [
    'shuffleBoard', 'empireBoard', 'empireMessage', 'empireChecked',
    'empireRankingCoverage', 'empirePoolTotal', 'empireSourceStatus',
    'shuffleSourceStatus', 'empireSourceTime', 'empireNextCheck', 'empireSourceLabel', 'empireRaceMode',
    'empireRaceWindow', 'empireCountdown', 'raceTitle', 'raceDescription'
  ]) elements[id] = elements[id] || new Element(id);
  elements.raceTitle.textContent = 'Shuffle Wager Race';
  elements.raceDescription.textContent = 'Shuffle race';
  for (let n = 1; n <= 15; n++) {
    for (const field of ['name', 'wager', 'prize', 'place']) {
      slots[`${n}:${field}`] = new Element(`slot-${n}-${field}`);
    }
  }
  for (let i=0; i<2; i++) metrics.push(new Element('metric'+i));
  const doc = {
    body: {dataset: {bootstrap: JSON.stringify({empiredrop: bootstrap})}},
    getElementById(id) { return elements[id] || null; },
    querySelector(selector) {
      if (selector.includes('.source-status')) return null;
      const match = selector.match(/^\[data-empire(?:-row)?-(name|wager|prize)="(\d+)"\]$/);
      return match ? slots[`${match[2]}:${match[1]}`] : null;
    },
    querySelectorAll(selector) { return selector === '[data-empire-metric]' ? metrics : []; },
    addEventListener(name, fn) { handlers['document:' + name] = fn; },
  };
  const errors = [];
  const timers=[];
  const context = {document: doc, Date, Intl, console:{error:(...x)=>errors.push(x),warn:(...x)=>errors.push(x)},setInterval:(fn)=>{timers.push(fn);return null;}};
  vm.runInNewContext(SCRIPT, context, {filename:'static/empiredrop.js'});
  return {slots, elements, handlers, metrics, errors,
    tick() { for (const tick of timers) tick(); },
    update(detail) { assert.equal(typeof handlers['document:empiredrop:update'], 'function'); handlers['document:empiredrop:update']({detail}); },
    selectEmpire() { handlers['empireTab:click'](); },
    selectShuffle() { handlers['shuffleTab:click'](); }};
}

function rows(count, opts={}) {
  return Array.from({length:count}, (_,i)=>({
    rank: opts.tied && i===2 ? 2 : i+1,
    username: `P${String(i+1).padStart(2,'0')}******`,
    wager: `€${(i+1)*100}.00`,
    prize: opts.prizes ? `€${(i+1)*10}.00` : '—'
  }));
}

const blankPrizes = {enabled:false,total:'€0.00',formatted:{}};

test('all ten API entries appear publicly when payouts are NOT announced (initial bootstrap)',()=>{
  const board = {
    rows:rows(10),label:'Updated · EmpireDrop race',updated_at:1794375291,
    prizes:blankPrizes,race_meta:{ranks_limit:10,metric:'Wagered',type:'WAGER',engine:'RANKING'},
    schedule:{mode:'provider',start_time:1794270000,end_time:1794870000,start_et:'Nov 10',end_et:'Nov 17'}
  };
  const h=harness(board);
  h.selectEmpire();
  assert.equal(h.elements.empireBoard.hidden,false);
  assert.equal(h.elements.shuffleBoard.hidden,true);
  for (let place=1;place<=10;place++) {
    assert.equal(h.slots[`${place}:name`].textContent,board.rows[place-1].username, `Missing player at place ${place}`);
    assert.equal(h.slots[`${place}:wager`].textContent,board.rows[place-1].wager);
    assert.equal(h.slots[`${place}:prize`].textContent,'Not announced');
  }
  assert.equal(h.elements.empireRankingCoverage.textContent,'');
  assert.equal(h.elements.empirePoolTotal.textContent,'Not announced');
  assert.deepEqual(h.errors,[]);
});

test('up to ten players and official tied ranks render with enabled independent payouts',()=>{
  const incoming = rows(15,{tied:true,prizes:true});
  const board={rows:incoming,label:'Confirmed',updated_at:1794375291,
    prizes:{enabled:true,total:'€1,200.00',formatted:{'2':'€50.00'}},
    race_meta:{ranks_limit:15,metric:'Wagered',engine:'RANKING',type:'WAGER'}};
  const h=harness({rows:[],prizes:blankPrizes});
  h.update(board);
  for (let place=1;place<=10;place++) {
    assert.equal(h.slots[`${place}:name`].textContent,incoming[place-1].username);
    assert.equal(h.slots[`${place}:wager`].textContent,incoming[place-1].wager);
    assert.equal(h.slots[`${place}:prize`].textContent,incoming[place-1].prize);
  }
  assert.equal(h.slots['3:place'].textContent,'02','Provider tie ranks must not disappear');
  assert.equal(h.slots['4:place'].textContent,'04');
  assert.equal(h.elements.empirePoolTotal.textContent,'€1,200.00');
  assert.deepEqual(h.errors,[]);
  h.selectEmpire();h.selectShuffle();
  assert.equal(h.elements.shuffleBoard.hidden,false);
  assert.equal(h.elements.empireBoard.hidden,true);
});

test('later API refresh replaces every visible slot, not just first place',()=>{
  const h=harness({rows:rows(10),prizes:blankPrizes,race_meta:{ranks_limit:10}});
  h.update({rows:rows(7),prizes:blankPrizes,race_meta:{ranks_limit:10},label:'New race results'});
  for(let n=1;n<=7;n++) assert.equal(h.slots[`${n}:name`].textContent,rows(7)[n-1].username);
  for(let n=8;n<=10;n++) assert.equal(h.slots[`${n}:name`].textContent,'Open position');
  assert.equal(h.elements.empireMessage.textContent,'');
  assert.equal(h.elements.empireMessage.hidden,true);
});

test('empty results are safe and provider limit is not invented',()=>{
  const h=harness({rows:[],prizes:blankPrizes,label:'Awaiting standings'});
  assert.equal(h.slots['1:name'].textContent,'Open position');
  assert.equal(h.slots['10:name'].textContent,'Open position');
  assert.match(h.elements.empireRankingCoverage.textContent,/Open positions will appear/);
  assert.equal(h.elements.empireMessage.textContent,'Standings are temporarily unavailable.');
});

test('public provider switching stays quiet while countdown continues',()=>{
  const now = Math.floor(Date.now()/1000);
  const h = harness({rows:rows(10),label:'Updated · EmpireDrop race',updated_at:now-10,
    next_check_at:now+240,refresh_interval:300,prizes:blankPrizes,race_meta:{ranks_limit:10},
    schedule:{start_time:now-30,end_time:now+3600,start_et:'Today',end_et:'Later'}});
  h.selectEmpire();
  assert.equal(h.elements.empireBoard.hidden,false);
  assert.equal(h.elements.shuffleBoard.hidden,true);
  assert.equal(h.elements.empireMessage.hidden,true);
  assert.match(h.elements.empireCountdown.textContent,/0d/);
  h.tick();
  h.selectShuffle();
  assert.equal(h.elements.empireBoard.hidden,true);
  assert.equal(h.elements.shuffleBoard.hidden,false);
  assert.deepEqual(h.errors,[]);
});
