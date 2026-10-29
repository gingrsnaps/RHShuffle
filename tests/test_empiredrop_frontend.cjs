/* Node-native test: no browser or live provider is required. */
const test = require('node:test');
const assert = require('node:assert/strict');
const fs = require('node:fs');
const vm = require('node:vm');
const path = require('node:path');

test('independent provider tabs swap panels and render only EmpireDrop slots', () => {
  const handlers = {};
  class Element {
    constructor(id, panel) {
      this.id = id; this.tabIndex = 0; this.hidden = false;
      this.textContent = ''; this.attributes = { 'aria-controls': panel };
      this.classList = { toggle: (name, on) => { this.active = on; } };
    }
    setAttribute(k, v) { this.attributes[k] = v; }
    getAttribute(k) { return this.attributes[k]; }
    addEventListener(name, fn) { handlers[this.id + ':' + name] = fn; }
    focus() { this.focused = true; }
  }
  const elements = {
    shuffleTab: new Element('shuffleTab', 'shuffleBoard'),
    empireTab: new Element('empireTab', 'empireBoard'),
    shuffleBoard: new Element('shuffleBoard'),
    empireBoard: new Element('empireBoard'),
    empireMessage: new Element('empireMessage'),
    empireChecked: new Element('empireChecked'),
  };
  const slots = {};
  for (let n = 1; n <= 15; n++) {
    for (const field of ['name', 'wager']) {
      slots[`${n}:${field}`] = new Element(`slot-${n}-${field}`);
    }
  }
  let update;
  const document = {
    body: { dataset: { bootstrap: JSON.stringify({empiredrop: {rows:[],label:'Not connected'}}) } },
    getElementById(id) { return elements[id] || null; },
    querySelector(selector) {
      if (selector.includes('.source-status')) return null;
      const match = selector.match(/data-empire(?:-row)?-(name|wager)="(\d+)"/);
      return match ? slots[`${match[2]}:${match[1]}`] : null;
    },
    addEventListener(name, fn) { if (name === 'empiredrop:update') update = fn; },
  };
  const file = path.join(__dirname, '..', 'static', 'empiredrop.js');
  vm.runInNewContext(fs.readFileSync(file, 'utf8'), {document, Intl, Date});
  assert.equal(elements.empireBoard.hidden, true);
  assert.equal(elements.shuffleBoard.hidden, false);
  handlers['empireTab:click']();
  assert.equal(elements.empireBoard.hidden, false);
  assert.equal(elements.shuffleBoard.hidden, true);
  update({detail:{rows:[{rank:1,username:'Te******',wager:'€123.00'}],label:'Confirmed',updated_at:1720000000}});
  assert.equal(slots['1:name'].textContent, 'Te******');
  assert.equal(slots['1:wager'].textContent, '€123.00');
  assert.equal(slots['2:name'].textContent, 'Open position');
  assert.equal(elements.empireMessage.textContent, 'Confirmed');
  handlers['shuffleTab:click']();
  assert.equal(elements.shuffleBoard.hidden, false);
});
