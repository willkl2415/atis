
const sectorSelect = document.getElementById("sector");
const functionSelect = document.getElementById("function");
const roleSelect = document.getElementById("role");
const responseDiv = document.getElementById("response");

Object.keys(roleData).forEach(sector => {
  const opt = document.createElement("option");
  opt.value = sector;
  opt.textContent = sector;
  sectorSelect.appendChild(opt);
});

sectorSelect.addEventListener("change", () => {
  functionSelect.innerHTML = '<option value="">Select a function</option>';
  roleSelect.innerHTML = '<option value="">Select a role</option>';
  const functions = roleData[sectorSelect.value];
  if (functions) {
    Object.keys(functions).forEach(func => {
      const opt = document.createElement("option");
      opt.value = func;
      opt.textContent = func;
      functionSelect.appendChild(opt);
    });
  }
});

functionSelect.addEventListener("change", () => {
  roleSelect.innerHTML = '<option value="">Select a role</option>';
  const roles = roleData[sectorSelect.value]?.[functionSelect.value];
  if (roles) {
    roles.forEach(role => {
      const opt = document.createElement("option");
      opt.value = role;
      opt.textContent = role;
      roleSelect.appendChild(opt);
    });
  }
});

function submitPrompt() {
  const sector = sectorSelect.value;
  const func = functionSelect.value;
  const role = roleSelect.value;
  const prompt = document.getElementById("prompt").value;
  if (!sector || !func || !role || !prompt) return;
  responseDiv.innerHTML = `
    <strong>Sector:</strong> ${sector}<br>
    <strong>Function:</strong> ${func}<br>
    <strong>Role:</strong> ${role}<br>
    <strong>Prompt:</strong> ${prompt}<br><br>
    <em>(This is a static GitHub Pages demo — AI responses not enabled.)</em>
  `;
}
