
// SALVAR NO HISTÓRICO
export function saveToHistory(entry) {
  const history = JSON.parse(localStorage.getItem("history") || "[]");

  history.unshift(entry); 

  localStorage.setItem("history", JSON.stringify(history));
}



// CARREGAR HISTÓRICO

export function loadHistory() {
  return JSON.parse(localStorage.getItem("history") || "[]");
}



// RENDERIZAR HISTÓRICO

export function renderHistory() {
  const listEl = document.getElementById("historyList");
  const history = loadHistory();

  listEl.innerHTML = "";

  history.forEach((item, index) => {
    const html = `
      <div class="history-item" data-index="${index}">
        <strong>[${item.categoria}]</strong> ${item.subcategoria}  
        <br>
        <small>${item.hora}</small> — 
        <small>${item.preview}</small>
      </div>
    `;
    listEl.innerHTML += html;
  });
}
export function clearHistory() {
  localStorage.removeItem("history");

  // limpa visualmente
  const list = document.getElementById("historyList");
  if (list) list.innerHTML = "";

  // esconde a seção se quiser
  const section = document.getElementById("historySection");
  if (section) section.classList.add("hidden");
}
