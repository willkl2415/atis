// --- ATIS Frontend Controller (yellow UI) ---
// Works with roles.js that defines either `window.ATIS_ROLE_DATA` or `window.roleData`.
// Accepts multiple shapes and normalizes to: Map<sectorKey, Map<functionName, string[]>>

(() => {
  const $ = (id) => document.getElementById(id);
  const industrySel = $("industry");
  const functionSel = $("function");
  const roleSel = $("role");
  const promptEl = $("prompt");
  const responseEl = $("response");
  const submitBtn = $("submitBtn");
  const clearBtn = $("clearBtn");

  // Optional: set this globally in index.html via:
  // <script>window.ATIS_API_URL="https://YOUR-BACKEND/generate"</script>
  const API_URL = window.ATIS_API_URL || "/generate";

  // 1) Load roles data from roles.js
  const rawData =
    window.ATIS_ROLE_DATA ||
    window.roleData ||
    window.ROLES ||
    window.data ||
    null;

  if (!rawData) {
    showError(
      "Error: roles.js not loaded or exported as ATIS_ROLE_DATA / roleData."
    );
    disableForm();
    return;
  }

  // 2) Helpers
  const cleanSectorLabel = (txt) =>
    String(txt)
      // remove "Industry Sector X — " or "X — " or leading numbers with dash
      .replace(/^industry\s*sector\s*\d+\s*[—-]\s*/i, "")
      .replace(/^\d+\s*[—-]\s*/i, "")
      .trim();

  function showError(msg) {
    responseEl.textContent = msg;
  }
  function clearMsg() {
    responseEl.textContent = "";
  }
  function disableForm(disabled = true) {
    [industrySel, functionSel, roleSel, promptEl, submitBtn, clearBtn].forEach(
      (el) => (el.disabled = disabled)
    );
  }

  // 3) Normalize roles data to Map<sectorKey, Map<functionName, string[]>>
  function normalizeToMap(data) {
    // Shape A (preferred): { "<Sector>": { "<Function>": [roles...] , ... }, ... }
    // Shape B: [{ sector:"<Sector>", functions: { "<Function>":[...] } }, ...]
    // Shape C: { sectors: { "<Sector>": { "<Function>":[...] } } }
    // We'll map to: sectorsMap: Map<sectorKey, Map<functionName, string[]>>
    const sectorsMap = new Map();

    const material =
      Array.isArray(data)
        ? data
        : data?.sectors && typeof data.sectors === "object"
        ? Object.entries(data.sectors).map(([sector, functions]) => ({
            sector,
            functions,
          }))
        : typeof data === "object"
        ? Object.entries(data).map(([sector, functions]) => {
            // Some people wrap: {sector:"Name", functions:{...}} under a numeric key.
            if (
              functions &&
              typeof functions === "object" &&
              ("functions" in functions || "sector" in functions)
            ) {
              return {
                sector: functions.sector || sector,
                functions: functions.functions || functions,
              };
            }
            return { sector, functions };
          })
        : [];

    for (const item of material) {
      const sectorName = item?.sector ?? "(Unknown Sector)";
      const fnBlock = item?.functions ?? item;

      // If fnBlock accidentally contains sector/functions keys, unwrap.
      const functionsObj =
        fnBlock && typeof fnBlock === "object" && "functions" in fnBlock
          ? fnBlock.functions
          : fnBlock;

      // Expect functionsObj to be: { "<Function>": [roles...] }
      const fnMap = new Map();
      if (functionsObj && typeof functionsObj === "object") {
        for (const [fnName, roles] of Object.entries(functionsObj)) {
          if (Array.isArray(roles)) {
            fnMap.set(fnName, roles.slice());
          }
        }
      }
      if (fnMap.size > 0) {
        sectorsMap.set(sectorName, fnMap);
      }
    }

    return sectorsMap;
  }

  const sectorsMap = normalizeToMap(rawData);
  if (sectorsMap.size === 0) {
    showError("Error: roles.js structure not recognized or empty.");
    disableForm();
    return;
  }

  // 4) Populate sector dropdown (display cleaned labels, keep original keys internally)
  const sectorKeys = Array.from(sectorsMap.keys());
  industrySel.innerHTML = `<option value="">Select Industry Sector</option>`;
  sectorKeys.forEach((sectorKey, idx) => {
    const opt = document.createElement("option");
    opt.value = String(idx); // index as value to avoid collisions
    opt.textContent = cleanSectorLabel(sectorKey);
    industrySel.appendChild(opt);
  });

  // 5) On sector change -> populate functions
  industrySel.addEventListener("change", () => {
    clearMsg();
    functionSel.innerHTML = `<option value="">Select Function</option>`;
    roleSel.innerHTML = `<option value="">Select Role</option>`;

    const idx = parseInt(industrySel.value, 10);
    if (Number.isNaN(idx)) return;

    const sectorKey = sectorKeys[idx];
    const fnMap = sectorsMap.get(sectorKey) || new Map();
    const fnNames = Array.from(fnMap.keys());

    fnNames.forEach((fnName, i) => {
      const opt = document.createElement("option");
      opt.value = String(i);
      opt.textContent = fnName;
      functionSel.appendChild(opt);
    });
  });

  // 6) On function change -> populate roles
  functionSel.addEventListener("change", () => {
    clearMsg();
    roleSel.innerHTML = `<option value="">Select Role</option>`;

    const sIdx = parseInt(industrySel.value, 10);
    const fIdx = parseInt(functionSel.value, 10);
    if (Number.isNaN(sIdx) || Number.isNaN(fIdx)) return;

    const sectorKey = sectorKeys[sIdx];
    const fnMap = sectorsMap.get(sectorKey) || new Map();
    const fnName = Array.from(fnMap.keys())[fIdx];
    const roles = (fnMap.get(fnName) || []).slice();

    roles.forEach((r) => {
      const opt = document.createElement("option");
      opt.value = r;
      opt.textContent = r;
      roleSel.appendChild(opt);
    });
  });

  // 7) Submit -> call backend
  submitBtn.addEventListener("click", async () => {
    clearMsg();

    const sIdx = parseInt(industrySel.value, 10);
    const fIdx = parseInt(functionSel.value, 10);
    const role = roleSel.value?.trim();
    const prompt = promptEl.value?.trim();

    if (
      Number.isNaN(sIdx) ||
      Number.isNaN(fIdx) ||
      !role ||
      !prompt
    ) {
      showError("Please select sector, function, role, and enter a question.");
      return;
    }

    const sectorKey = sectorKeys[sIdx];
    const fnName = Array.from(sectorsMap.get(sectorKey).keys())[fIdx];

    const payload = {
      sector: cleanSectorLabel(sectorKey),
      func: fnName,
      role,
      prompt,
    };

    try {
      submitBtn.disabled = true;
      submitBtn.textContent = "Thinking…";

      const res = await fetch(API_URL, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(payload),
      });

      if (!res.ok) {
        const t = await res.text();
        throw new Error(`HTTP ${res.status}: ${t}`);
      }
      const data = await res.json();
      responseEl.textContent = data.response || "(No content)";
    } catch (err) {
      showError(`Request failed: ${err.message}`);
    } finally {
      submitBtn.disabled = false;
      submitBtn.textContent = "Submit Prompt";
    }
  });

  // 8) Clear
  clearBtn.addEventListener("click", () => {
    clearMsg();
    industrySel.value = "";
    functionSel.innerHTML = `<option value="">Select Function</option>`;
    roleSel.innerHTML = `<option value="">Select Role</option>`;
    promptEl.value = "";
  });
})();
