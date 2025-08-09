// ------- DOM -------
const industrySelect = document.getElementById("industry");
const functionSelect = document.getElementById("function");
const roleSelect     = document.getElementById("role");
const promptEl       = document.getElementById("prompt");
const submitBtn      = document.getElementById("submitBtn");
const clearBtn       = document.getElementById("clearBtn");
const responseDiv    = document.getElementById("response");

// ------- Data -------
const DATA = window.ATIS_ROLES;

// hard fail if roles map missing or wrong type
(function init() {
  if (!DATA || typeof DATA !== "object" || Array.isArray(DATA)) {
    responseDiv.textContent = "Error: roles.js not loaded or malformed.";
    [industrySelect,functionSelect,roleSelect,submitBtn,clearBtn].forEach(el=>el.disabled=true);
    return;
  }

  // Populate sectors (object keys, sorted A→Z)
  const sectors = Object.keys(DATA).sort((a,b)=>a.localeCompare(b));
  fillSelect(industrySelect, ["Select Industry Sector", ...sectors]);

  // Events
  industrySelect.addEventListener("change", onSectorChange);
  functionSelect.addEventListener("change", onFunctionChange);
  submitBtn.addEventListener("click", onSubmit);
  clearBtn.addEventListener("click", onClear);
})();

function fillSelect(select, items, keepFirst=false) {
  select.innerHTML = "";
  items.forEach((label, i) => {
    const opt = document.createElement("option");
    opt.value = i===0 ? "" : label;
    opt.textContent = label;
    select.appendChild(opt);
  });
}

function onSectorChange() {
  roleSelect.innerHTML = '<option value="">Select Role</option>';
  const sector = industrySelect.value;
  if (!sector) {
    functionSelect.innerHTML = '<option value="">Select Function</option>';
    return;
  }
  const functions = Object.keys(DATA[sector] || {}).sort((a,b)=>a.localeCompare(b));
  fillSelect(functionSelect, ["Select Function", ...functions]);
}

function onFunctionChange() {
  const sector = industrySelect.value;
  const func = functionSelect.value;
  roleSelect.innerHTML = '<option value="">Select Role</option>';
  if (!sector || !func) return;
  const roles = (DATA[sector] && DATA[sector][func]) ? DATA[sector][func] : [];
  const sorted = [...roles].sort((a,b)=>a.localeCompare(b));
  fillSelect(roleSelect, ["Select Role", ...sorted]);
}

async function onSubmit() {
  const sector = industrySelect.value.trim();
  const func   = functionSelect.value.trim();
  const role   = roleSelect.value.trim();
  const prompt = promptEl.value.trim();

  if (!sector || !func || !role || !prompt) {
    responseDiv.textContent = "Please select sector, function, role, and enter a question.";
    return;
  }

  submitBtn.disabled = true;
  responseDiv.textContent = "Thinking…";

  try {
    const res = await fetch("/generate", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ sector, func, role, prompt })
    });
    const data = await res.json();
    responseDiv.textContent = data.response || "No response.";
  } catch (err) {
    responseDiv.textContent = "Error contacting the API.";
  } finally {
    submitBtn.disabled = false;
  }
}

function onClear() {
  industrySelect.selectedIndex = 0;
  functionSelect.innerHTML = '<option value="">Select Function</option>';
  roleSelect.innerHTML = '<option value="">Select Role</option>';
  promptEl.value = "";
  responseDiv.textContent = "";
}
