(() => {
  'use strict';

  const toast = document.querySelector('#adminToast');
  const settingsForm = document.querySelector('#wagerRaceSettingsForm');
  const prizeTotal = document.querySelector('#livePrizeTotal');
  const saveBar = document.querySelector('#settingsSaveBar');
  const saveStateTitle = document.querySelector('#saveStateTitle');
  const saveStateDetail = document.querySelector('#saveStateDetail');
  const startInput = settingsForm?.querySelector('[name="start_et"]');
  const endInput = settingsForm?.querySelector('[name="end_et"]');
  let isDirty = false;
  let isSubmitting = false;
  let initialDurationMs = null;

  function showToast(message) {
    if (!toast) return;
    toast.textContent = message;
    toast.hidden = false;
    window.setTimeout(() => { toast.hidden = true; }, 2200);
  }

  async function copyText(value) {
    try {
      await navigator.clipboard.writeText(value);
    } catch {
      const input = document.createElement('textarea');
      input.value = value;
      document.body.appendChild(input);
      input.select();
      document.execCommand('copy');
      input.remove();
    }
    showToast('Copied to clipboard.');
  }

  function markDirty() {
    if (!settingsForm || isDirty) return;
    isDirty = true;
    saveBar?.classList.add('has-unsaved-changes');
    if (saveStateTitle) saveStateTitle.textContent = 'Unsaved changes';
    if (saveStateDetail) saveStateDetail.textContent = 'Save before leaving this page.';
  }

  function moneyValue(value) {
    const cleaned = String(value ?? '').replace(/[$,\s]/g, '');
    if (!/^\d+(?:\.\d{0,2})?$/.test(cleaned)) return null;
    const number = Number(cleaned);
    return Number.isFinite(number) && number >= 0 ? number : null;
  }

  function updatePrizeTotal() {
    if (!settingsForm || !prizeTotal) return;
    const inputs = [...settingsForm.querySelectorAll('input[name^="prize_"]')];
    let total = 0;
    let valid = true;
    inputs.forEach((input) => {
      const amount = moneyValue(input.value);
      const invalid = amount === null;
      input.classList.toggle('input-invalid', invalid);
      input.setAttribute('aria-invalid', invalid ? 'true' : 'false');
      if (invalid) valid = false;
      else total += amount;
    });
    prizeTotal.textContent = valid
      ? `${total.toLocaleString('en-US', { style: 'currency', currency: 'USD', maximumFractionDigits: 2 })} prize pool`
      : 'Fix invalid prize amounts';
    prizeTotal.classList.toggle('pill-error', !valid);
  }

  function pseudoDateFromInput(value) {
    if (!value) return null;
    const parsed = new Date(`${value}:00Z`);
    return Number.isNaN(parsed.getTime()) ? null : parsed;
  }

  function inputValueFromPseudoDate(date) {
    const pad = (value) => String(value).padStart(2, '0');
    return `${date.getUTCFullYear()}-${pad(date.getUTCMonth() + 1)}-${pad(date.getUTCDate())}T${pad(date.getUTCHours())}:${pad(date.getUTCMinutes())}`;
  }

  function easternNowInputValue() {
    const parts = new Intl.DateTimeFormat('en-US', {
      timeZone: 'America/New_York',
      year: 'numeric', month: '2-digit', day: '2-digit',
      hour: '2-digit', minute: '2-digit', hourCycle: 'h23'
    }).formatToParts(new Date());
    const values = Object.fromEntries(parts.map((part) => [part.type, part.value]));
    return `${values.year}-${values.month}-${values.day}T${values.hour}:${values.minute}`;
  }

  function setEndDaysAfterStart(days) {
    if (!startInput || !endInput) return;
    if (!startInput.value) startInput.value = easternNowInputValue();
    const start = pseudoDateFromInput(startInput.value);
    if (!start) return;
    start.setUTCDate(start.getUTCDate() + days);
    endInput.value = inputValueFromPseudoDate(start);
    markDirty();
  }

  function validatePasswordGroup(form) {
    const primary = form.querySelector('[data-password-primary]');
    const confirmation = form.querySelector('[data-password-confirm]');
    if (!primary || !confirmation) return true;
    const matches = primary.value === confirmation.value;
    confirmation.setCustomValidity(matches ? '' : 'Passwords do not match.');
    return matches;
  }

  document.querySelectorAll('[data-copy]').forEach((button) => {
    button.addEventListener('click', () => copyText(button.dataset.copy || ''));
  });

  document.querySelectorAll('form[data-confirm]').forEach((form) => {
    form.addEventListener('submit', (event) => {
      const message = form.dataset.confirm || 'Continue with this action?';
      if (!window.confirm(message)) event.preventDefault();
    });
  });

  document.querySelectorAll('.password-toggle').forEach((button) => {
    button.addEventListener('click', () => {
      const input = button.parentElement?.querySelector('input');
      if (!input) return;
      const show = input.type === 'password';
      input.type = show ? 'text' : 'password';
      button.textContent = show ? 'Hide' : 'Show';
      button.setAttribute('aria-label', show ? 'Hide password' : 'Show password');
    });
  });

  document.querySelectorAll('[data-password-match-group]').forEach((form) => {
    form.querySelectorAll('[data-password-primary], [data-password-confirm]').forEach((input) => {
      input.addEventListener('input', () => validatePasswordGroup(form));
    });
    form.addEventListener('submit', (event) => {
      if (!validatePasswordGroup(form)) {
        event.preventDefault();
        form.querySelector('[data-password-confirm]')?.reportValidity();
      }
    });
  });

  document.querySelector('#sectionJump')?.addEventListener('change', (event) => {
    const id = event.target.value;
    if (!id) return;
    document.getElementById(id)?.scrollIntoView({ behavior: 'smooth', block: 'start' });
    event.target.value = '';
  });

  document.querySelectorAll('.section-nav-links a').forEach((link) => {
    link.addEventListener('click', (event) => {
      const target = document.querySelector(link.getAttribute('href'));
      if (target) {
        event?.preventDefault?.();
        target.scrollIntoView({ behavior: 'smooth', block: 'start' });
      }
    });
  });

  document.querySelectorAll('[data-schedule-action]').forEach((button) => {
    button.addEventListener('click', () => {
      const action = button.dataset.scheduleAction;
      if (action === 'start-now' && startInput) {
        startInput.value = easternNowInputValue();
        markDirty();
      } else if (action === 'end-7') {
        setEndDaysAfterStart(7);
      } else if (action === 'end-14') {
        setEndDaysAfterStart(14);
      } else if (action === 'copy-duration' && startInput && endInput && initialDurationMs && initialDurationMs > 0) {
        const start = pseudoDateFromInput(startInput.value || easternNowInputValue());
        if (!start) return;
        endInput.value = inputValueFromPseudoDate(new Date(start.getTime() + initialDurationMs));
        markDirty();
      }
    });
  });

  document.querySelector('#restoreStandardPrizes')?.addEventListener('click', () => {
    const message = 'Restore the standard 15-place prize schedule? Current unsaved prize amounts will be replaced.';
    if (!window.confirm(message) || !settingsForm) return;
    settingsForm.querySelectorAll('input[name^="prize_"]').forEach((input) => {
      input.value = input.dataset.standard || '0.00';
    });
    updatePrizeTotal();
    markDirty();
  });

  if (settingsForm) {
    const initialStart = pseudoDateFromInput(startInput?.value || '');
    const initialEnd = pseudoDateFromInput(endInput?.value || '');
    if (initialStart && initialEnd && initialEnd > initialStart) {
      initialDurationMs = initialEnd.getTime() - initialStart.getTime();
    }

    settingsForm.addEventListener('input', (event) => {
      markDirty();
      if (event.target.matches('input[name^="prize_"]')) updatePrizeTotal();
    });
    settingsForm.addEventListener('change', markDirty);
    settingsForm.addEventListener('submit', () => { isSubmitting = true; });
    updatePrizeTotal();
  }

  window.addEventListener('beforeunload', (event) => {
    if (!isDirty || isSubmitting) return;
    event.preventDefault();
    event.returnValue = '';
  });

  document.addEventListener('click', (event) => {
    document.querySelectorAll('details.more-actions[open]').forEach((details) => {
      if (!details.contains(event.target)) details.removeAttribute('open');
    });
  });
})();
