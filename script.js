(() => {
  const byId = (id) => document.getElementById(id);

  const industryEl = byId("industry");
  const functionEl = byId("function");
  const roleEl = byId("role");
  const promptEl = byId("prompt");
  const responseEl = byId("response");
  const submitBtn = byId("submitBtn");
  const clearBtn = byId("clearBtn");

  // Robust check: roles map must exist and be an object
  const ROLES = (typeof window !== "undefined" && window.ATIS_ROLES && typeof window.ATIS_ROLES === "object")
    ? window.ATIS_ROLES
    : null;

  function setError(msg) {
    responseEl.textContent = msg;
    submitBtn.disabled = true;
    industryEl.disabled = true;
    functionEl.disabled = true;
    roleEl.disabled = true;
  }

  function populateIndustries() {
    const sectors = Object.keys(ROLES).sort();
    sectors.forEach(sec => {
      const opt = document.createElement("option");
      opt.value = sec;
      opt.textContent = sec;
      industryEl.appendChild(opt);
    });
  }

  function populateFunctions(sector) {
    functionEl.innerHTML = '<option value="">Select Function</option>';
    roleEl.innerHTML = '<option value="">Select Role</option>';
    if (!sector || !ROLES[sector]) return;
    Object.keys(ROLES[sector]).sort().forEach(fn => {
      const opt = document.createElement("option");
      opt.value = fn;
      opt.textContent = fn;
      functionEl.appendChild(opt);
    });
  }

  function populateRoles(sector, fn) {
    roleEl.innerHTML = '<option value="">Select Role</option>';
    const roles = ROLES[sector]?.[fn];
    if (!roles || !Array.isArray(roles)) return;
    roles.slice().sort().forEach(r => {
      const opt = document.createElement("option");
      opt.value = r;
      opt.textContent = r;
      roleEl.appendChild(opt);
    });
  }

  async function postJSON(url, data, timeoutMs = 20000) {
    const ctrl = new AbortController();
    const t = setTimeout(() => ctrl.abort(), timeoutMs);
    try {
      const res = await fetch(url, {
        method: "POST",
        headers: {"Content-Type": "application/json"},
        body: JSON.stringify(data),
        signal: ctrl.signal,
      });
      clearTimeout(t);
      if (!res.ok) throw new Error(`HTTP ${res.status}`);
      return await res.json();
    } finally {
      clearTimeout(t);
    }
  }

  function wireEvents() {
    industryEl.addEventListener("change", () => {
      populateFunctions(industryEl.value);
    });

    functionEl.addEventListener("change", () => {
      populateRoles(industryEl.value, functionEl.value);
    });

    submitBtn.addEventListener("click", async () => {
      const sector = industryEl.value;
      const fn = functionEl.value;
      const role = roleEl.value;
      const prompt = promptEl.value.trim();

      if (!sector || !fn || !role || !prompt) {
        responseEl.textContent = "Please select sector, function, role, and enter a question.";
        return;
      }

      submitBtn.disabled = true;
      responseEl.textContent = "Thinking…";

      try {
        // Relative path so it works locally or when proxied (e.g., Render, Vercel, etc.)
        const data = await postJSON("/generate", {
          sector,
          function: fn,
          role,
          prompt,
        }, 30000); // 30s guard

        responseEl.textContent = (data && data.response) ? data.response.trim() : "No response.";
      } catch (err) {
        responseEl.textContent = `Error calling backend: ${err.message || err}`;
      } finally {
        submitBtn.disabled = false;
      }
    });

    clearBtn.addEventListener("click", () => {
      promptEl.value = "";
      responseEl.textContent = "";
      industryEl.value = "";
      functionEl.innerHTML = '<option value="">Select Function</option>';
      roleEl.innerHTML = '<option value="">Select Role</option>';
    });
  }

  // Boot
  document.addEventListener("DOMContentLoaded", () => {
    if (!ROLES) {
      setError("Error: roles.js not loaded or malformed.");
      return;
    }
    populateIndustries();
    wireEvents();
  });
})();
