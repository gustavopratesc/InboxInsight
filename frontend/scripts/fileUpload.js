export function setupFileUpload() {
  const fileInput = document.getElementById("fileInput");
  const fileNameEl = document.getElementById("fileName");
  const removeBtn = document.getElementById("removeFileBtn");
  const textarea = document.getElementById("emailInput");

  // Mostrar nome e preparar variáveis globais
  fileInput.addEventListener("change", async () => {
    const file = fileInput.files[0];
    if (!file) return;

    fileNameEl.textContent = file.name;
    removeBtn.classList.remove("hidden");

    // Se for TXT
    if (file.type === "text/plain") {
      window.lastTxtFile = file;
      window.lastPdfFile = null;

      const text = await file.text();
      textarea.value = "";       // limpar textarea
      textarea.placeholder = "Arquivo TXT carregado.";
    }

    // Se for PDF
    else if (file.type === "application/pdf") {
      window.lastPdfFile = file;
      window.lastTxtFile = null;

      textarea.value = "";
      textarea.placeholder = "Arquivo PDF carregado.";
    }
  });

  // Botão remover arquivo
  removeBtn.addEventListener("click", () => {
    window.lastTxtFile = null;
    window.lastPdfFile = null;

    fileInput.value = "";     // limpar input real
    fileNameEl.textContent = "";
    removeBtn.classList.add("hidden");

    textarea.placeholder = "Cole o conteúdo do e-mail aqui...";
  });
}
