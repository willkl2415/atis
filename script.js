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
  responseDiv.textContent = "";

  try {
    const res = await fetch(API_BASE + "/generate", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ sector, func, role, prompt })
    });

    const reader = res.body.getReader();
    const decoder = new TextDecoder();
    let output = "";

    while (true) {
      const { done, value } = await reader.read();
      if (done) break;
      output += decoder.decode(value, { stream: true });
      responseDiv.textContent = output;
    }
  } catch (err) {
    responseDiv.textContent = "Error: " + err.message;
  } finally {
    submitBtn.disabled = false;
  }
}
