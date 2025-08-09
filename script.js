(function () {
  const sectorEl = document.getElementById('sector');
  const funcEl = document.getElementById('func');
  const roleEl = document.getElementById('role');
  const promptEl = document.getElementById('prompt');
  const outputEl = document.getElementById('output');
  const askBtn = document.getElementById('askBtn');
  const clearBtn = document.getElementById('clearBtn');

  if (!window.ATIS_ROLE_DATA || typeof window.ATIS_ROLE_DATA !== 'object') {
    console.error('roles.js not loaded or exported as ATIS_ROLE_DATA.');
    outputEl.textContent = 'Error: roles.js not loaded or exported as ATIS_ROLE_DATA.';
    return;
  }

  function clearSelect(el, placeholder) {
    el.innerHTML = '';
    const opt = document.createElement('option');
    opt.value = '';
    opt.textContent = placeholder;
    el.appendChild(opt);
  }

  function populateSectors() {
    clearSelect(sectorEl, 'Select Industry Sector');
    Object.keys(window.ATIS_ROLE_DATA).sort().forEach(sector => {
      const opt = document.createElement('option');
      opt.value = sector;
      opt.textContent = sector;
      sectorEl.appendChild(opt);
    });
    funcEl.disabled = true;
    roleEl.disabled = true;
  }

  function populateFunctions(sector) {
    clearSelect(funcEl, 'Select Function');
    clearSelect(roleEl, 'Select Role');
    const functions = window.ATIS_ROLE_DATA[sector] || {};
    Object.keys(functions).sort().forEach(fn => {
      const opt = document.createElement('option');
      opt.value = fn;
      opt.textContent = fn;
      funcEl.appendChild(opt);
    });
    funcEl.disabled = false;
    roleEl.disabled = true;
  }

  function populateRoles(sector, fn) {
    clearSelect(roleEl, 'Select Role');
    (window.ATIS_ROLE_DATA[sector][fn] || []).forEach(role => {
      const opt = document.createElement('option');
      opt.value = role;
      opt.textContent = role;
      roleEl.appendChild(opt);
    });
    roleEl.disabled = false;
  }

  sectorEl.addEventListener('change', () => {
    const sector = sectorEl.value;
    if (sector) {
      populateFunctions(sector);
    } else {
      funcEl.disabled = true;
      roleEl.disabled = true;
    }
  });

  funcEl.addEventListener('change', () => {
    const sector = sectorEl.value;
    const fn = funcEl.value;
    if (fn) {
      populateRoles(sector, fn);
    } else {
      roleEl.disabled = true;
    }
  });

  askBtn.addEventListener('click', async () => {
    const sector = sectorEl.value;
    const fn = funcEl.value;
    const role = roleEl.value;
    const prompt = promptEl.value.trim();

    if (!sector || !fn || !role || !prompt) {
      outputEl.textContent = 'Please select Sector, Function, Role, and enter a prompt.';
      return;
    }

    outputEl.textContent = 'Thinking...';

    try {
      const res = await fetch('/api/ask', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ sector, func: fn, role, prompt })
      });

      if (!res.ok) throw new Error(`HTTP ${res.status}`);

      const data = await res.json();
      const answer = (data.answer || '').replace(/\*\*/g, '').trim();
      outputEl.textContent = answer || 'Nothing found. Please rephrase or rewrite your prompt.';
    } catch (err) {
      console.error(err);
      outputEl.textContent = 'Error retrieving response. Please try again.';
    }
  });

  clearBtn.addEventListener('click', () => {
    promptEl.value = '';
    outputEl.textContent = 'Response will appear here.';
  });

  populateSectors();
})();
