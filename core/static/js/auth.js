/* ============================================================
   txtr — auth.js
   Password show/hide toggle, strength meter, submit loading
   ============================================================ */

'use strict';

/* ── Password Show / Hide Toggle ────────────────────────── */
document.querySelectorAll('.form-input-toggle').forEach(btn => {
  btn.addEventListener('click', () => {
    const targetId = btn.dataset.toggle;
    const input    = document.getElementById(targetId);
    const svg      = btn.querySelector('svg');
    if (!input) return;

    if (input.type === 'password') {
      input.type = 'text';
      svg.innerHTML = `
        <path d="M17.94 17.94A10.07 10.07 0 0112 20c-7 0-11-8-11-8a18.45 18.45 0 015.06-5.94"
              stroke="currentColor" stroke-width="2" stroke-linecap="round" fill="none"/>
        <path d="M9.9 4.24A9.12 9.12 0 0112 4c7 0 11 8 11 8a18.5 18.5 0 01-2.16 3.19"
              stroke="currentColor" stroke-width="2" stroke-linecap="round" fill="none"/>
        <line x1="1" y1="1" x2="23" y2="23"
              stroke="currentColor" stroke-width="2" stroke-linecap="round"/>`;
    } else {
      input.type = 'password';
      svg.innerHTML = `
        <path d="M1 12s4-8 11-8 11 8 11 8-4 8-11 8-11-8-11-8z"
              stroke="currentColor" stroke-width="2" stroke-linecap="round" fill="none"/>
        <circle cx="12" cy="12" r="3"
              stroke="currentColor" stroke-width="2" fill="none"/>`;
    }
  });
});

/* ── Password Strength Meter ─────────────────────────────── */
const passwordInput = document.getElementById('id_password1');
const strengthEl    = document.getElementById('password-strength');
const fillEl        = document.getElementById('strength-fill');
const labelEl       = document.getElementById('strength-label');

if (passwordInput && strengthEl) {
  passwordInput.addEventListener('input', () => {
    const val = passwordInput.value;
    if (!val) { strengthEl.classList.remove('visible'); return; }
    strengthEl.classList.add('visible');

    const score = getPasswordScore(val);
    fillEl.className = 'strength-fill';

    if (score < 2) {
      fillEl.classList.add('weak');
      labelEl.textContent = 'Weak password';
      labelEl.style.color = 'var(--danger)';
    } else if (score < 4) {
      fillEl.classList.add('medium');
      labelEl.textContent = 'Could be stronger';
      labelEl.style.color = '#f0a500';
    } else {
      fillEl.classList.add('strong');
      labelEl.textContent = 'Strong password';
      labelEl.style.color = 'var(--success)';
    }
  });
}

function getPasswordScore(pw) {
  let s = 0;
  if (pw.length >= 8)           s++;
  if (pw.length >= 12)          s++;
  if (/[A-Z]/.test(pw))        s++;
  if (/[0-9]/.test(pw))        s++;
  if (/[^A-Za-z0-9]/.test(pw)) s++;
  return s;
}

/* ── Submit Loading State ────────────────────────────────── */
const submitBtn = document.getElementById('submit-btn');
['register-form', 'login-form'].forEach(id => {
  const form = document.getElementById(id);
  if (!form || !submitBtn) return;
  form.addEventListener('submit', () => {
    setTimeout(() => {
      submitBtn.classList.add('loading');
      submitBtn.disabled = true;
    }, 0);
  });
});