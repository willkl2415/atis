// script.js — ATIS Optimisation front-end logic
// Assumes roles.js exposes global window.ROLES

(function () {
  const sectorEl = document.getElementById('sector');
  const funcEl = document.getElementById('func');
  const roleEl = document.getElementById('role');
  const promptEl = document.getElementById('prompt');
  const askBtn = document.getElementById('askBtn');
  const outputEl = document.getElementById('output');
  const metaEl = document.getElementById('meta');
  const statusEl = document.getElementById('status');

  if (!window.ROLES || typeof window.ROLES !== 'object') {
    console.error('ROLES not found. Ensure roles.js is loaded before script.js');
  }

  function clearSelect(el, placeholderText) {
    el.innerHTML = '';
    const opt = document.createElement('option');
    opt.value = '';
    opt.textContent = placeholderText;
    el.appendChild(opt);
  }

  function populateSectors() {
    clearSelect(sectorEl, 'Select sector');
    Object.keys(window.ROLES).sort().forEach(sector => {
      const opt = document.createElement('option');
      opt.value = sector;
      opt.textContent = sector;
      sectorEl.appendChild(opt);
    });
    funcEl.disabled = true;
    roleEl.disabled = true;
    clearSelect(funcEl, 'Select function');
    clearSelect(roleEl, 'Select role');
  }

  function populateFunctions(sector) {
    clearSelect(funcEl, 'Select function');
    clearSelect(roleEl, 'Select role');
    roleEl.disabled = true;

    const functions = window.ROLES[sector] || {};
    Object.keys(functions).sort().forEach(fn => {
      const opt = document.createElement('option');
      opt.value = fn;
      opt.textContent = fn;
      funcEl.appendChild(opt);
    });
    funcEl.disabled = false;
  }

  function populateRoles(sector, fn) {
    clearSelect(roleEl, 'Select role');
    const arr = (window.ROLES[sector] && window.ROLES[sector][fn]) || [];
    arr.forEach(r => {
      const opt = document.createElement('option');
      opt.value = r;
      opt.textContent = r;
      roleEl.appendChild(opt);
    });
    roleEl.disabled = false;
  }

  sectorEl.addEventListener('change', () => {
    const sector = sectorEl.value;
    metaEl.textContent = '';
    if (!sector) {
      funcEl.disabled = true;
      roleEl.disabled = true;
      clearSelect(funcEl, 'Select function');
      clearSelect(roleEl, 'Select role');
      return;
    }
    populateFunctions(sector);
  });

  funcEl.addEventListener('change', () => {
    const sector = sectorEl.value;
    const fn = funcEl.value;
    metaEl.textContent = '';
    if (!fn) {
      roleEl.disabled = true;
      clearSelect(roleEl, 'Select role');
      return;
    }
    populateRoles(sector, fn);
  });

  roleEl.addEventListener('change', () => {
    const sector = sectorEl.value;
    const fn = funcEl.value;
    const role = roleEl.value;
    if (sector && fn && role) {
      metaEl.textContent = `Context: ${sector} → ${fn} → ${role}`;
    } else {
      metaEl.textContent = '';
    }
  });

  async function ask() {
    const sector = sectorEl.value;
    const fn = funcEl.value;
    const role = roleEl.value;
    const prompt = (promptEl.value || '').trim();

    if (!sector || !fn || !role) {
      outputEl.textContent = 'Please select Sector, Function, and Role.';
      return;
    }
    if (!prompt) {
      outputEl.textContent = 'Please enter a prompt.';
      return;
    }

    statusEl.textContent = 'Thinking…';
    outputEl.textContent = '';

    try {
      const res = await fetch('/api/ask', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ sector, func: fn, role, prompt })
      });

      if (!res.ok) {
        const t = await res.text();
        throw new Error(`HTTP ${res.status}: ${t}`);
      }
      const data = await res.json();
      // Ensure clean plain text, remove markdown bold markers
      const cleaned = (data.answer || '')
        .replace(/\*\*/g, '')
        .trim();
      outputEl.textContent = cleaned || 'Nothing found. Please rephrase or rewrite your prompt.';
    } catch (err) {
      console.error(err);
      outputEl.textContent = 'Error retrieving response. Please try again.';
    } finally {
      statusEl.textContent = '';
    }
  }

  askBtn.addEventListener('click', ask);
  populateSectors();
})();
