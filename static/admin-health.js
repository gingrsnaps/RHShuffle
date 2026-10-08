/* Health polling reuses the existing admin feed; no additional timer. */
(() => {
  'use strict';
  const root = document.getElementById('systemHealth');
  if (!root) return;
  const date = value => value ? new Date(value*1000).toLocaleString() : 'Not recorded';
  function render(value) {
    if (!value?.components) return;
    for (const item of value.components) {
      const card = [...root.querySelectorAll('[data-health-card]')].find(node => node.dataset.healthCard === item.key);
      if (!card) continue;
      card.dataset.state = item.state;
      card.querySelector('[data-health-status]').textContent = item.status;
      card.querySelector('[data-health-detail]').textContent = item.detail;
      card.querySelector('[data-health-time]').textContent = item.last_success ? 'Confirmed '+date(item.last_success) : 'Waiting for first confirmation';
    }
    const m = value.metrics, s = m.storage;
    const items = [
      ['Request p95', m.latency.samples ? m.latency.p95_ms+' ms' : 'Collecting'],
      ['Save p95', s.write.samples ? s.write.p95_ms+' ms' : 'Collecting'],
      ['Lock wait p95', s.lock_wait.p95_ms+' ms'],
      ['State file', (s.bytes/1048576).toFixed(2)+' MB'],
      ['Server errors', String(m.server_errors)],
      ['Last save', date(s.last_write)],
    ];
    const metrics = document.getElementById('healthMetrics');
    metrics.replaceChildren(...items.map(([label, text]) => {
      const node = document.createElement('div'), name = document.createElement('span'), count = document.createElement('strong');
      name.textContent = label; count.textContent = text; node.append(name, count); return node;
    }));
  }
  globalThis.RedHealth = {render};
  render(JSON.parse(root.dataset.health));
  document.getElementById('copyHealthReport').addEventListener('click', async event => {
    const feedback = document.getElementById('healthReportFeedback'), button = event.currentTarget;
    button.disabled = true;
    try {
      const response = await fetch('/admin/health-report', {headers:{Accept:'application/json'}, credentials:'same-origin', cache:'no-store', signal:AbortSignal.timeout(10000)});
      if (response.status === 401) throw Error('Sign in again to get a current report.');
      if (!response.ok) throw Error('Report unavailable. Check runtime logs.');
      const report = JSON.stringify(await response.json(), null, 2);
      try {
        await navigator.clipboard.writeText(report);
        feedback.textContent = 'Support report copied. No private player data or credentials included.';
      } catch {
        const url = URL.createObjectURL(new Blob([report], {type:'application/json'}));
        const link = document.createElement('a'); link.href = url; link.download = 'redhunllef-support.json'; link.click();
        setTimeout(() => URL.revokeObjectURL(url), 1000);
        feedback.textContent = 'Clipboard unavailable. The support report was downloaded instead.';
      }
    } catch (error) { feedback.textContent = error.message; }
    finally { button.disabled = false; feedback.hidden = false; }
  });
})();
