/* Protected EmpireDrop-only admin panel. No raw keys are transmitted to the browser. */
(() => {
  'use strict';
  if (!document.getElementById('empireAdminTitle')) return;
  const id = x => document.getElementById(x);
  let pending = false, expired = false;
  const fmt = t => t ? new Intl.DateTimeFormat('en-US', {timeZone:'America/New_York', dateStyle:'medium', timeStyle:'short'}).format(new Date(t*1000)) + ' ET' : 'Not yet verified';
  const render = data => {
    if (expired) return;
    id('empireAdminStatus').textContent = data.label || 'Awaiting verified EmpireDrop data';
    id('empireAdminConfirmed').textContent = fmt(data.updated_at);
    id('empireAdminAttempted').textContent = fmt(data.attempt_at);
    id('empireAdminChecking').textContent = data.checking ? 'Checking provider' : data.queued_at > data.attempt_at ? 'Refresh queued' : 'Idle';
    id('empireError').hidden = !data.error;
    id('empireError').textContent = data.error || '';
    const body = document.createDocumentFragment();
    (Array.isArray(data.rows) ? data.rows.slice(0,15) : []).forEach(r => {
      const tr = document.createElement('tr');
      for (const v of [String(r.rank).padStart(2,'0'), r.username, r.wager]) {
        const td = document.createElement('td'); td.textContent = String(v ?? ''); tr.appendChild(td);
      }
      body.appendChild(tr);
    });
    if (!body.childNodes.length) {
      const tr = document.createElement('tr'); const td = document.createElement('td'); td.colSpan = 3;
      td.textContent = 'No verified EmpireDrop wagers for the selected period.'; tr.appendChild(td); body.appendChild(tr);
    }
    id('empireAdminRows').replaceChildren(body);
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
  document.addEventListener('visibilitychange', () => { if (!document.hidden) poll(); });
  window.setInterval(poll, 15000);
})();
