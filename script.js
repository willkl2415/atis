// script.js

// 1) Point this to your Render backend (already live)
const API_BASE = "https://atis-api.onrender.com";
const ENDPOINT = "/generate";

const industrySel = document.getElementById("industry");
const functionSel = document.getElementById("function");
const roleSel     = document.getElementById("role");
const promptTA    = document.getElementById("prompt");
const submitBtn   = document.getElementById("submitBtn");
const clearBtn    = document.getElementById("clearBtn");
const responseDiv = document.getElementById("response");

// ---- Populate dropdowns from roles.js (roleData = { Sector: { Function: [roles] } }) ----
(function initDropdowns(){
  // Sectors
  Object.keys(roleData).forEach(sector => {
    const opt = document.createElement("option");
    opt.value = sector; opt.textContent = sector;
    industrySel.appendChild(opt);
  });
})();

industrySel.addEventListener("change", () => {
  functionSel.innerHTML = '<option value="">Select Function</option>';
  roleSel.innerHTML     = '<option value="">Select Role</option>';
  const fns = roleData[industrySel.value];
  if(!fns) return;
  Object.keys(fns).forEach(fn => {
    const opt = document.createElement("option");
    opt.value = fn; opt.textContent = fn;
    functionSel.appendChild(opt);
  });
});

functionSel.addEventListener("change", () => {
  roleSel.innerHTML = '<option value="">Select Role</option>';
  const roles = roleData[industrySel.value]?.[functionSel.value] || [];
  roles.forEach(r => {
    const opt = document.createElement("option");
    opt.value = r; opt.textContent = r;
    roleSel.appendChild(opt);
  });
});

// ---- Clear (cosmetic for now; doesn’t call API) ----
clearBtn.addEventListener("click", () => {
  promptTA.value = "";
  responseDiv.textContent = "";
});

// ---- Submit ----
submitBtn.addEventListener("click", async () => {
  const industry = industrySel.value.trim();
  const func     = functionSel.value.trim();
  const role     = roleSel.value.trim();
  const prompt   = promptTA.value.trim();

  if(!industry || !role || !prompt){
    responseDiv.textContent = "Please select industry, function, role, and enter a question.";
    return;
  }

  submitBtn.disabled = true;
  responseDiv.textContent = "Thinking…";

  // Client-side timeout so we never hang forever
  const controller = new AbortController();
  const t = setTimeout(() => controller.abort(), 12000); // 12s hard cap

  const started = performance.now();
  try {
    const res = await fetch(API_BASE + ENDPOINT, {
      method: "POST",
      headers: {"Content-Type": "application/json"},
      body: JSON.stringify({industry, function: func, role, prompt}),
      signal: controller.signal,
      keepalive: true
    });

    const data = await res.json();
    const elapsed = Math.round(performance.now() - started);

    responseDiv.textContent = (data.text || "No response.")
      + `\n\n— Responded in ${elapsed} ms`;
  } catch (err) {
    responseDiv.textContent = "Error: " + (err.name === "AbortError" ? "Request timed out." : err.message);
  } finally {
    clearTimeout(t);
    submitBtn.disabled = false;
  }
});
