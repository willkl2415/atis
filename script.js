// script.js — ATIS Demo UI wired to Render backend (warm-up, timeout, retry)

(function () {
  // ====== CONFIG ======
  const API_BASE = "https://atis-api.onrender.com"; // <- change if your Render URL differs
  const API_URL = `${API_BASE}/api/ask`;
  const HEALTH_URL = `${API_BASE}/health`;
  const REQUEST_TIMEOUT_MS = 15000; // 15s

  // ====== ELEMENTS (match the Demo HTML ids) ======
  const sectorEl = document.getElementById("sector");
  const funcEl = document.getElementById("func");       // not "function"
  const roleEl = document.getElementById("role");
  const promptEl = document.getElementById("prompt");
  const outputEl = document.getElementById("output") || document.getElementById("response");

  // ====== DATA GUARD ======
  const DATA = window.ATIS_ROLE_DATA;
  if (!DATA || typeof DATA !== "object") {
    if (outputEl) outputEl.textContent = "Error: roles.js not loaded as ATIS_ROLE_DATA.";
    console.error("ATIS_ROLE_DATA missing.");
    return;
  }

  // ====== HELPERS ======
  function clearSelect(el, placeholder) {
    el.innerHTML = "";
    const opt = document.createElement("option");
    opt.value = "";
    opt.textContent = placeholder;
    el.appendChild(opt);
  }

  function populateSectors() {
    clearSelect(sectorEl, "Select Industry Sector");
    Object.keys(DATA).sort().forEach(sector => {
      const opt = document.createElement("option");
      opt.value = sector;
      opt.textContent = sector;
      sectorEl.appendChild(opt);
    });
    funcEl.disabled = true;
    roleEl.disabled = true;
    clearSelect(funcEl, "Select Function");
    clearSelect(roleEl, "Select Role");
  }

  function populateFunctions(sector) {
    clearSelect(funcEl, "Select Function");
    clearSelect(roleEl, "Select Role");
    const fns = DATA[sector] || {};
    Object.keys(fns).sort().forEach(fn => {
      const opt = document.createElement("option");
      opt.value = fn;
      opt.textContent = fn;
      funcEl.appendChild(opt);
    });
    funcEl.disabled = false;
    roleEl.disabled = true;
  }

  function populateRoles(sector, fn) {
    clearSelect(roleEl, "Select Role");
    (DATA[sector]?.[fn] || []).forEach(role => {
      const opt = document.createElement("option");
      opt.value = role;
      opt.textContent = role;
      roleEl.appendChild(opt);
    });
    roleEl.disabled = false;
  }

  function withTimeout(ms, doFetch) {
    const controller = new AbortController();
    const t = setTimeout(() => controller.abort(), ms);
    return doFetch(controller).finally(() => clearTimeout(t));
  }

  async function warmup() {
    try {
      await withTimeout(4000, (ctrl) => fetch(HEALTH_URL, { signal: ctrl.signal }));
    } catch { /* best-effort */ }
  }

  async function askAPI(payload, attempt = 1) {
    try {
      const res = await withTimeout(REQUEST_TIMEOUT_MS, (ctrl) =>
        fetch(API_URL, {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify(payload),
          signal: ctrl.signal
        })
      );
      if (!res.ok) {
        const txt = await res.text().catch(() => "");
        if (attempt === 1 && [408, 429, 502, 503, 504].includes(res.status)) {
          return askAPI(payload, 2);
        }
        throw new Error(`HTTP ${res.status} ${res.statusText}${txt ? ` — ${txt}` : ""}`);
      }
      return res.json();
    } catch (err) {
      if (attempt === 1 && (String(err?.name) === "AbortError" || /network/i.test(String(err)))) {
        return askAPI(payload, 2);
      }
      throw err;
    }
  }

  // ====== EVENTS ======
  sectorEl.addEventListener("change", () => {
    const sector = sectorEl.value;
    if (sector) populateFunctions(sector);
    else {
      funcEl.disabled = true;
      roleEl.disabled = true;
      clearSelect(funcEl, "Select Function");
      clearSelect(roleEl, "Select Role");
    }
  });

  funcEl.addEventListener("change", () => {
    const sector = sectorEl.value;
    const fn = funcEl.value;
    if (fn) populateRoles(sector, fn);
    else {
      roleEl.disabled = true;
      clearSelect(roleEl, "Select Role");
    }
  });

  async function submitPrompt() {
    const sector = sectorEl.value;
    const fn = funcEl.value;
    const role = roleEl.value;
    const prompt = (promptEl.value || "").trim();

    if (!sector || !fn || !role || !prompt) {
      outputEl.textContent = "Please select Sector, Function, Role, and enter a prompt.";
      return;
    }

    outputEl.textContent = "Thinking…";

    try {
      await warmup();
      const data = await askAPI({ sector, func: fn, role, prompt });
      const answer = (data.answer || "").replace(/\*\*/g, "").trim();
      outputEl.textContent = answer || "Nothing found. Please rephrase or rewrite your prompt.";
    } catch (err) {
      console.error(err);
      const msg = String(err || "").trim();
      if (/AbortError/i.test(msg)) outputEl.textContent = "Timed out waiting for the backend. Please try again.";
      else if (/HTTP\s\d+/.test(msg)) outputEl.textContent = `Backend error: ${msg}`;
      else outputEl.textContent = "Error retrieving response. Please try again.";
    }
  }

  // Expose for inline onclick="submitPrompt()"
  window.submitPrompt = submitPrompt;

  // ====== INIT ======
  populateSectors();
})();
