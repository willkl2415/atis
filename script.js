// API configuration for Render backend
const API_BASE = "https://atis-api.onrender.com";
const ENDPOINT = "/generate";

const sectorSelect = document.getElementById("sector");
const functionSelect = document.getElementById("function");
const roleSelect = document.getElementById("role");
const promptInput = document.getElementById("prompt");
const submitBtn = document.getElementById("submitBtn");
const responseDiv = document.getElementById("response");

// Populate dropdowns from roles.js
function populateSectors() {
  sectorSelect.innerHTML = "<option value=''>Select a sector</option>";
  window.ATIS_ROLES.forEach(sec => {
    const opt = document.createElement("option");
    opt.value = sec.sector;
    opt.textContent = sec.sector;
    sectorSelect.appendChild(opt);
  });
  // Reset function/role
  functionSelect.innerHTML = "<option value=''>Select a function</option>";
  roleSelect.innerHTML = "<option value=''>Select a role</option>";
}

function populateFunctions() {
  functionSelect.innerHTML = "<option value=''>Select a function</option>";
  roleSelect.innerHTML = "<option value=''>Select a role</option>";
  const sector = window.ATIS_ROLES.find(s => s.sector === sectorSelect.value);
  if (sector) {
    sector.functions.forEach(func => {
      const opt = document.createElement("option");
      opt.value = func.name;
      opt.textContent = func.name;
      functionSelect.appendChild(opt);
    });
  }
}

function populateRoles() {
  roleSelect.innerHTML = "<option value=''>Select a role</option>";
  const sector = window.ATIS_ROLES.find(s => s.sector === sectorSelect.value);
  if (sector) {
    const func = sector.functions.find(f => f.name === functionSelect.value);
    if (func) {
      func.roles.forEach(role => {
        const opt = document.createElement("option");
        opt.value = role;
        opt.textContent = role;
        roleSelect.appendChild(opt);
      });
    }
  }
}

// Send prompt to API
async function submitPrompt() {
  const sector = sectorSelect.value;
  const func = functionSelect.value;
  const role = roleSelect.value;
  const prompt = promptInput.value.trim();

  if (!sector || !func || !role || !prompt) {
    responseDiv.textContent = "Please select sector, function, role, and enter a prompt.";
    return;
  }

  submitBtn.disabled = true;
  responseDiv.textContent = "Thinking...";

  try {
    const res = await fetch(API_BASE + ENDPOINT, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ sector, function: func, role, prompt })
    });
    const data = await res.json();
    responseDiv.textContent = data.text || "No response received.";
  } catch (err) {
    responseDiv.textContent = "Error: " + err.message;
  } finally {
    submitBtn.disabled = false;
  }
}

// Event listeners
sectorSelect.addEventListener("change", populateFunctions);
functionSelect.addEventListener("change", populateRoles);
submitBtn.addEventListener("click", submitPrompt);

// Initialise
populateSectors();
