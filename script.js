// Config
const API_BASE = "https://atis-api.onrender.com";   // your Render URL
const ENDPOINT_STREAM = "/generate_stream";         // fast streaming endpoint
const ENDPOINT_NONSTREAM = "/generate";             // fallback if needed

const sectorSelect = document.getElementById("sector");
const functionSelect = document.getElementById("function");
const roleSelect = document.getElementById("role");
const promptInput = document.getElementById("prompt");
const submitBtn = document.getElementById("submitBtn") || document.querySelector("button");
const responseDiv = document.getElementById("response");

// roles.js populates window.ATIS_ROLES
function populateSectors() {
  sectorSelect.innerHTML = "<option value=''>Select a sector</option>";
  window.ATIS_ROLES.forEach(sec => {
    const opt = document.createElement("option");
    opt.value = sec.sector; opt.textContent = sec.sector;
    sectorSelect.appendChild(opt);
  });
}
function populateFunctions() {
  functionSelect.innerHTML = "<option value=''>Select a function</option>";
  roleSelect.innerHTML = "<option value=''>Select a role</option>";
  const s = window.ATIS_ROLES.find(x => x.sector === sectorSelect.value);
  if (!s) return;
  s.functions.forEach(f => {
    const opt = document.createElement("option");
    opt.value = f.name; opt.textContent = f.name;
    functionSelect.appendChild(opt);
  });
}
function populateRoles() {
  roleSelect.innerHTML = "<option value=''>Select a role</option>";
  const s = window.ATIS_ROLES.find(x => x.sector === sectorSelect.value);
  if (!s) return;
  const f = s.functions.find(y => y.name === functionSelect.value);
  if (!f) return;
  f.roles.forEach(r => {
    const opt = document.createElement("option");
    opt.value = r; opt.textContent = r;
    roleSelect.appendChild(opt);
  });
}

sectorSelect.addEventListener("change", populateFunctions);
functionSelect.addEventListener("change", populateRoles);

async function submitPrompt() {
  const sector = sectorSelect.value;
  const func = functionSelect.value;
  const role = roleSelect.value;
  const prompt = promptInput.value.trim();
  if (!sector || !func || !role || !prompt) {
    responseDiv.textContent = "Please select sector, function, role, and enter a prompt.";
    return;
  }

  // STREAM for perceived sub‑second
  submitBtn.disabled = true;
  responseDiv.textContent = "";
  const body = JSON.stringify({ sector, func, role, prompt });

  try {
    const res = await fetch(API_BASE + ENDPOINT_STREAM, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body
    });
    if (!res.ok || !res.body) {
      // fallback to non‑stream
      const r2 = await fetch(API_BASE + ENDPOINT_NONSTREAM, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body
      });
      const data = await r2.json();
      responseDiv.textContent = data.text || "No response.";
      submitBtn.disabled = false;
      return;
    }

    // ReadableStream — append tokens as they arrive
    const reader = res.body.getReader();
    const decoder = new TextDecoder();
    let acc = "";
    function pump() {
      return reader.read().then(({ done, value }) => {
        if (done) return;
        acc += decoder.decode(value, { stream: true });
        responseDiv.textContent = acc.replace(/\*\*/g, "");
        return pump();
      });
    }
    await pump();
  } catch (e) {
    responseDiv.textContent = "Error: " + (e?.message || e);
  } finally {
    submitBtn.disabled = false;
  }
}

(document.getElementById("submitBtn") || document.querySelector("button"))
  .addEventListener("click", submitPrompt);

// init
populateSectors();
