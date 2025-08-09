(() => {
  const industrySel = document.getElementById("industry");
  const functionSel = document.getElementById("function");
  const roleSel     = document.getElementById("role");
  const promptEl    = document.getElementById("prompt");
  const respEl      = document.getElementById("response");
  const submitBtn   = document.getElementById("submitBtn");
  const clearBtn    = document.getElementById("clearBtn");

  // ====== CONFIG: point this at your FastAPI deployment when not local ======
  const API_URL = (window.ATIS_API_URL || "").trim(); // optional global override
  const FALLBACK_API = "http://localhost:8002/generate"; // local dev
  // ==========================================================================

  // Robustly obtain the roles data from roles.js
  const RAW = (window.ATIS_ROLE_DATA || window.roleData || window.ROLES || null);

  // Utility: show message
  const msg = (text, isError = false) => {
    respEl.textContent = text || "";
    respEl.style.borderColor = isError ? "#e74c3c" : "#e6d884";
  };

  // Normalize sector label (remove leading "Industry Sector 1 — " or "Sector 3 - ")
  const cleanSector = s => (s || "")
    .replace(/^Industry\s+Sector\s+\d+\s*[—-]\s*/i, "")
    .replace(/^Sector\s+\d+\s*[—-]\s*/i, "")
    .trim();

  // Normalize "Function: X" -> "X"
  const cleanFunction = f => (f || "").replace(/^Function:\s*/i, "").trim();

  // Convert arbitrary shapes to: { [sector]: { [function]: string[] } }
  function normalize(data) {
    if (!data) return null;

    const out = {};

    // Case A: already in the desired object shape
    const looksLikeDirect = obj =>
      obj && !Array.isArray(obj) &&
      Object.values(obj).some(v => v && typeof v === "object" && !Array.isArray(v));

    // Case B: wrapped as { sectors: {...} }
    if (!Array.isArray(data) && data.sectors && looksLikeDirect(data.sectors)) {
      data = data.sectors;
    }

    if (Array.isArray(data)) {
      // [{ sector, functions: { fn: [roles] } }, ...]
      for (const item of data) {
        if (!item) continue;
        const sectorName = cleanSector(item.sector || item.name || "");
        const fns = item.functions || {};
        if (!sectorName || typeof fns !== "object") continue;
        out[sectorName] = out[sectorName] || {};
        for (const [fnRaw, list] of Object.entries(fns)) {
          const fn = cleanFunction(fnRaw);
          out[sectorName][fn] = Array.isArray(list) ? list.slice() :
                                (Array.isArray(list?.roles) ? list.roles.slice() : []);
        }
      }
      return Object.keys(out).length ? out : null;
    }

    if (looksLikeDirect(data)) {
      // { "Industry Sector 1 — L&D": { "Function: Leadership": [..] } }
      for (const [sectKey, fnsVal] of Object.entries(data)) {
        const sectorName = cleanSector(sectKey || (fnsVal?.name) || "");
        if (!sectorName) continue;
        const fnObj = (fnsVal && fnsVal.functions && typeof fnsVal.functions === "object")
          ? fnsVal.functions : fnsVal;

        if (typeof fnObj !== "object" || Array.isArray(fnObj)) continue;
        out[sectorName] = out[sectorName] || {};
        for (const [fnRaw, list] of Object.entries(fnObj)) {
          const fn = cleanFunction(fnRaw);
          out[sectorName][fn] = Array.isArray(list) ? list.slice() :
                                (Array.isArray(list?.roles) ? list.roles.slice() : []);
        }
      }
      return Object.keys(out).length ? out : null;
    }

    return null;
  }

  const DATA = normalize(RAW);

  if (!DATA) {
    msg("Error: roles.js not loaded or exported in a usable shape. Expected window.ATIS_ROLE_DATA or window.roleData with { Sector → { Function → [roles] } }.", true);
    console.error("roles.js RAW value:", RAW);
    return;
  }

  // Populate Industry (sector) select
  function populateIndustries() {
    clearSelect(functionSel, "Select Function");
    clearSelect(roleSel, "Select Role");
    clearSelect(industrySel, "Select Industry Sector");

    const sectors = Object.keys(DATA).sort((a,b)=>a.localeCompare(b));
    for (const s of sectors) {
      industrySel.appendChild(new Option(s, s));
    }
  }

  function clearSelect(sel, placeholder) {
    sel.innerHTML = "";
    sel.appendChild(new Option(placeholder, ""));
  }

  function populateFunctions(sector) {
    clearSelect(functionSel, "Select Function");
    clearSelect(roleSel, "Select Role");
    if (!sector || !DATA[sector]) return;
    const functions = Object.keys(DATA[sector]).sort((a,b)=>a.localeCompare(b));
    for (const fn of functions) {
      functionSel.appendChild(new Option(fn, fn));
    }
  }

  function populateRoles(sector, fn) {
    clearSelect(roleSel, "Select Role");
    const roles = DATA[sector]?.[fn] || [];
    for (const r of roles) {
      roleSel.appendChild(new Option(r, r));
    }
  }

  // Event wiring
  industrySel.addEventListener("change", e => {
    populateFunctions(e.target.value);
    msg(""); // clear any previous error
  });

  functionSel.addEventListener("change", () => {
    populateRoles(industrySel.value, functionSel.value);
    msg("");
  });

  clearBtn.addEventListener("click", () => {
    industrySel.value = "";
    clearSelect(functionSel, "Select Function");
    clearSelect(roleSel, "Select Role");
    promptEl.value = "";
    msg("");
  });

  submitBtn.addEventListener("click", async () => {
    const sector = industrySel.value;
    const func   = functionSel.value;
    const role   = roleSel.value;
    const prompt = promptEl.value.trim();

    if (!sector || !func || !role || !prompt) {
      msg("Please select sector, function, role, and enter a question.", true);
      return;
    }

    submitBtn.disabled = true;
    msg("Thinking…");

    try {
      const url = API_URL || FALLBACK_API;
      const res = await fetch(url, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          sector, func, role, prompt
        })
      });

      if (!res.ok) throw new Error(`API ${res.status}`);
      const json = await res.json();
      msg(json.response || "(No content returned)");
    } catch (err) {
      console.error(err);
      msg(`Error calling API: ${err.message}`, true);
    } finally {
      submitBtn.disabled = false;
    }
  });

  // init
  populateIndustries();
})();
