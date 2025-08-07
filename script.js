const sectorSelect = document.getElementById("sector");
const functionSelect = document.getElementById("function");
const roleSelect = document.getElementById("role");

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
  const prompt = document.getElementById("prompt").value;
  const role = roleSelect.value;
  const sector = sectorSelect.value;
  const output = `Sector: ${sector}\nFunction: ${functionSelect.value}\nRole: ${role}\nPrompt: ${prompt}`;
  document.getElementById("response").textContent = output;
}