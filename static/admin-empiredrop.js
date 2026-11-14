/* Protected EmpireDrop-only admin panel. No raw keys are transmitted to the browser. */
(() => {
  'use strict';
  if (!document.getElementById('empireAdminTitle')) return;
  const id = x => document.getElementById(x);
  let pending = false, expired = false;
  const fmt = t => t ? new Intl.DateTimeFormat('en-US', {timeZone:'America/New_York', year:'numeric', month:'short', day:'numeric', hour:'numeric', minute:'2-digit', timeZoneName:'short'}).format(new Date(t*1000)) : 'Not yet verified';
  const render = data => {
    if (expired) return;
    id('empireAdminStatus').textContent = data.label || 'Awaiting verified EmpireDrop data';
    if (id('empireRaceSlug')) id('empireRaceSlug').textContent = data.race_meta?.slug || 'Not discovered';
    if (id('empireRaceMode')) id('empireRaceMode').textContent = (data.source_mode || 'races').toUpperCase();
    id('empireAdminConfirmed').textContent = fmt(data.updated_at);
    id('empireAdminAttempted').textContent = fmt(data.attempt_at);
    id('empireAdminChecking').textContent = data.checking ? 'Checking provider' : data.queued_at > data.attempt_at ? 'Refresh queued' : 'Idle';
    id('empireError').hidden = !data.error;
    id('empireError').textContent = data.error || '';
    // Show the provider's actual active race when automatic recovery occurs.
    const recovery = id('empireSlugRecovery');
    if (recovery) {
      recovery.hidden = !data.selection_warning;
      recovery.textContent = data.selection_warning || '';
    }
    const body = document.createDocumentFragment();
    (Array.isArray(data.rows) ? data.rows.slice(0,10) : []).forEach(r => {
      const tr = document.createElement('tr');
      for (const v of [String(r.rank).padStart(2,'0'), r.username, r.user_id || '—', r.wager, r.prize || '—']) {
        const td = document.createElement('td'); td.textContent = String(v ?? ''); tr.appendChild(td);
      }
      body.appendChild(tr);
    });
    if (!body.childNodes.length) {
      const tr = document.createElement('tr'); const td = document.createElement('td'); td.colSpan = 5;
      td.textContent = 'No ranked players returned for this race. A closed race or a new race may return an empty ranking.'; tr.appendChild(td); body.appendChild(tr);
    }
    id('empireAdminRows').replaceChildren(body);
    filterEmpirePlayers();
  };
  const clear = () => {
    expired = true; id('empireAdminRows').replaceChildren();
    id('empireAdminStatus').textContent = 'Admin session expired. Sign in again.';
    id('empireAdminConfirmed').textContent = 'Private data hidden';
    id('empireAdminAttempted').textContent = 'Private data hidden';
  };
  async function poll() {
    if (pending || document.hidden || expired) return;
    pending = true;
    try {
      const response = await fetch('/admin/empiredrop/status', {credentials:'same-origin', cache:'no-store'});
      if (response.status === 401 || response.status === 403) { clear(); return; }
      if (!response.ok) throw new Error('Status unavailable');
      render(await response.json());
    } catch { if (!expired) id('empireAdminStatus').textContent = 'Status request failed; last known results may be stale.'; }
    finally { pending = false; }
  }
  const test = id('testEmpireConnection');
  if (test) test.addEventListener('click', async () => {
    test.disabled = true;
    id('empireTestResult').textContent = 'Testing official EmpireDrop connection without saving any wagers…';
    try {
      const response = await fetch('/admin/empiredrop/test', {
        method:'POST', credentials:'same-origin', cache:'no-store',
        headers:{'X-CSRF-Token':test.dataset.csrf, 'Accept':'application/json'}
      });
      if (response.status === 401 || response.status === 403) { clear(); return; }
      const value = await response.json();
      id('empireTestResult').textContent = (value.ok ? 'Confirmed: ' : 'Not connected: ') + (value.message || 'No result');
    } catch { id('empireTestResult').textContent = 'Unable to complete the test.'; }
    finally { test.disabled = false; }
  });
  // Diagnostic requests only return race IDs and field *names*, not player values
  // or API credentials. They use the same CSRF/session protections as admin.
  async function inspectRace(buttonId, path, payload = null) {
    const button = id(buttonId), panel = id('empireRaceDiagnostics');
    if (!button || !panel) return;
    button.disabled = true;
    panel.textContent = 'Contacting the EmpireDrop races API…';
    try {
      const response = await fetch(path, {
        method: 'POST', credentials: 'same-origin', cache: 'no-store',
        headers: {'Accept':'application/json', 'Content-Type':'application/json',
                  'X-CSRF-Token': button.dataset.csrf},
        body: JSON.stringify(payload || {})
      });
      if (response.status === 401 || response.status === 403) { clear(); return; }
      const body = await response.json();
      // Never interpolate response data as HTML; textContent prevents injection.
      panel.textContent = JSON.stringify(body, null, 2);
      // Race slugs from the API are offered as a selection helper, never
      // written to settings until the admin clicks Save below.
      const choices = id('empireDiscoveredSlugs');
      if (choices && path.endsWith('/discover')) {
        choices.replaceChildren();
        const races = body.ok && Array.isArray(body.races) ? body.races : [];
        if (races.length) {
          const select = document.createElement('select');
          select.id = 'empireDiscoveredRaceSelect';
          const placeholder = document.createElement('option');
          placeholder.value = ''; placeholder.textContent = 'Choose a race from the verified list';
          select.appendChild(placeholder);
          races.forEach(r => {
            const option = document.createElement('option');
            option.value = r.slug;
            option.textContent = (r.name || r.slug) + ' · ' + r.slug;
            select.appendChild(option);
          });
          const use = document.createElement('button');
          use.type = 'button'; use.className = 'button';
          use.textContent = 'Use selected race (not saved yet)';
          use.addEventListener('click', () => {
            if (!select.value) return;
            id('empireRaceSlugInput').value = select.value;
            id('empireRaceSlugInput').focus();
          });
          choices.append(select, use);
        } else {
          choices.textContent = 'No running races were returned. Finished and scheduled races are intentionally excluded.';
        }
      }
    } catch {
      panel.textContent = 'Race endpoint request failed. See server logs for a safe error classification.';
    } finally { button.disabled = false; }
  }
  id('empireDiscover')?.addEventListener('click', () =>
    inspectRace('empireDiscover', '/admin/empiredrop/discover'));
  id('empireProbe')?.addEventListener('click', () =>
    inspectRace('empireProbe', '/admin/empiredrop/probe',
                {slug: id('empireRaceSlugInput')?.value?.trim() || ''}));
  document.addEventListener('visibilitychange', () => { if (!document.hidden) poll(); });
  window.setInterval(poll, 15000);
})();

/* Prize preview is purely client-side: saving validates all ten amounts server-side. */
(() => {
  const form = document.querySelector('form[action="/admin/empiredrop/rewards"]');
  if (!form) return;
  const output = document.getElementById('empireRewardTotal');
  function preview() {
    let total = 0;
    for (let i=1;i<=10;i++) {
      const input = form.querySelector(`[name="prize_${i}"]`);
      const n = Number(input?.value);
      if (!Number.isFinite(n) || n<0) { output.textContent = 'Check amount for place '+i;return; }
      total += n;
    }
    const currency = form.querySelector('[name="currency"]').value;
    output.textContent = new Intl.NumberFormat('en-US', {style:'currency',currency}).format(total);
  }
  const status = document.getElementById('empireRewardSaveState');
  const original = new FormData(form);
  const baseline = JSON.stringify([...original].filter(([key]) => !['csrf'].includes(key)));
  function state() {
    const current = JSON.stringify([...new FormData(form)].filter(([key]) => !['csrf'].includes(key)));
    if (status) status.textContent = current === baseline ? 'No unsaved changes' : 'Unsaved prize changes';
  }
  form.addEventListener('input',()=>{preview();state();});
  form.addEventListener('change',()=>{preview();state();});
  let submitting = false;
  form.addEventListener('submit',event=>{
    if (submitting) { event.preventDefault(); return; }
    const submitter = event.submitter;
    const mode = submitter?.value === 'publish' ? 'publish' : 'draft';
    // Disabled submit buttons are omitted from native form serialization.
    // Persist the click intent in a hidden field before locking the buttons so
    // Save & publish cannot silently arrive at the server as Save draft.
    const intent = form.querySelector('[name="save_mode_intent"]');
    if (intent) intent.value = mode;
    submitting = true;
    form.setAttribute('aria-busy','true');
    const publish = mode === 'publish';
    if (status) status.textContent = publish ? 'Saving and verifying public prizes…' : 'Saving draft…';
    for (const button of form.querySelectorAll('[data-payout-submit]')) {
      button.disabled = true;
      if (button === submitter) button.textContent = publish ? 'Publishing…' : 'Saving…';
    }
  });
  preview();state();
})();

/* Local search over the admin-only provider names and stable public IDs. */
function filterEmpirePlayers() {
  const input = document.getElementById('empireAdminSearch');
  const body = document.getElementById('empireAdminRows');
  if (!input || !body) return;
  const q = input.value.trim().toLocaleLowerCase();
  for (const tr of body.querySelectorAll('tr')) {
    tr.hidden = q !== '' && !tr.textContent.toLocaleLowerCase().includes(q);
  }
}
// The common admin-providers.js controller attaches the input event.
// filterEmpirePlayers() is still used after each live table refresh.
