// ---------- CONFIG ----------
const API_BASE = "https://atis-api.onrender.com"; // Render base URL
const GENERATE_PATH = "/generate";

// ---------- ELEMENTS ----------
const sectorSelect   = document.getElementById("sector");
const functionSelect = document.getElementById("function");
const roleSelect     = document.getElementById("role");
const promptInput    = document.getElementById("prompt");
const submitBtn      = document.getElementById("submitBtn");
const clearBtn       = document.getElementById("clearBtn");
const responseDiv    = document.getElementById("response");

// ---------- POPULATE DROPDOWNS FROM roles.js ----------
function populateSectors() {
  try {
    const sectors = Object.keys(roleData || {});
    sectors.forEach(sec => {
      const opt = document.createElement("option");
      opt.value = sec;
      opt.textContent = sec;
      sectorSelect.appendChild(opt);
    });
  } catch {
    responseDiv.textContent = "Error: roles.js not loaded or malformed.";
  }
}

function populateFunctions() {
  functionSelect.innerHTML = '<option value="">Select Function</option>';
  roleSelect.innerHTML     = '<option value="">Select Role</option>';
  const sector = sectorSelect.value;
  if (!sector) return;

  const functions = roleData[sector];
  if (functions) {
    Object.keys(functions).forEach(fn => {
      const opt = document.createElement("option");
      opt.value = fn;
      opt.textContent = fn;
      functionSelect.appendChild(opt);
    });
  }
}

function populateRoles() {
  roleSelect.innerHTML = '<option value="">Select Role</option>';
  const sector = sectorSelect.value;
  const fn     = functionSelect.value;
  if (!sector || !fn) return;

  const roles = roleData[sector]?.[fn];
  if (Array.isArray(roles)) {
    roles.forEach(r => {
      const opt = document.createElement("option");
      opt.value = r;
      opt.textContent = r;
      roleSelect.appendChild(opt);
    });
  }
}

// ---------- SUBMIT ----------
async function submitPrompt() {
  const sector = sectorSelect.value;
  const func   = functionSelect.value;
  const role   = roleSelect.value;
  const prompt = (promptInput.value || "").trim();

  if (!sector || !func || !role || !prompt) {
    responseDiv.textContent = "Please select sector, function, role, and enter your question.";
    return;
  }

  submitBtn.disabled = true;
  responseDiv.textContent = "Thinking…";

  try {
    const res = await fetch(`${API_BASE}${GENERATE_PATH}`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ sector, func, role, prompt })
    });

    if (!res.ok) {
      const txt = await res.text();
      throw new Error(`API error (${res.status}): ${txt}`);
    }

    const data = await res.json();
    const out  = data.text || data.response || "No response received.";
    responseDiv.textContent = out;
  } catch (err) {
    responseDiv.textContent = `Error: ${err.message}`;
  } finally {
    submitBtn.disabled = false;
  }
}

// ---------- CLEAR (cosmetic for now, but it works cleanly) ----------
function clearUI() {
  sectorSelect.value = "";
  functionSelect.innerHTML = '<option value="">Select Function</option>';
  roleSelect.innerHTML     = '<option value="">Select Role</option>';
  promptInput.value = "";
  responseDiv.textContent = "Your response will appear here…";
}

// ---------- EVENTS ----------
sectorSelect.addEventListener("change", populateFunctions);
functionSelect.addEventListener("change", populateRoles);
submitBtn.addEventListener("click", submitPrompt);
clearBtn.addEventListener("click", clearUI);

// ---------- INIT ----------
populateSectors();
