const form = document.getElementById("genForm");
const statusEl = document.getElementById("status");

form.addEventListener("submit", async (e) => {
  e.preventDefault();
  statusEl.textContent = "Generating…";
  const fd = new FormData(form);

  // Ensure speaker_notes field exists
  if (!fd.get("speaker_notes")) fd.set("speaker_notes", "");

  try {
    const res = await fetch("/generate", {
      method: "POST",
      body: fd
    });
    if (!res.ok) {
      const text = await res.text();
      throw new Error(text || "Failed to generate");
    }
    const blob = await res.blob();
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = "generated_presentation.pptx";
    document.body.appendChild(a);
    a.click();
    a.remove();
    URL.revokeObjectURL(url);
    statusEl.textContent = "Done. File downloaded.";
  } catch (err) {
    statusEl.textContent = "Error: " + err.message;
  }
});