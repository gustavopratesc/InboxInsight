console.log("main.js carregado!");

import { setupThemeToggle } from "./theme.js";
import { setupFileUpload } from "./fileUpload.js";

import {
  analyzeEmail,
  analyzeBatchJSON,
  analyzeBatchTXT,
  analyzePDF
} from "./api.js";

import {
  saveToHistory,
  renderHistory,
  clearHistory
} from "./history.js";



// SPLIT INTELIGENTE


function splitEmailsSmart(text) {
  if (text.length < 2000) {
    return [text.trim()];
  }

  const parts = text.split(/\n\s*\n{2,}/g);

  const valid = parts
    .map(p => p.trim())
    .filter(p => p.length > 50);

  return valid.length > 1 ? valid : [text.trim()];
}

function splitEmails(text) {
  return splitEmailsSmart(text);
}



// DOM READY


document.addEventListener("DOMContentLoaded", () => {

  setupThemeToggle();
  setupFileUpload();

  // ELEMENTOS
  const analyzeBtn = document.getElementById("analyzeBtn");
  const textarea = document.getElementById("emailInput");
  const loading = document.getElementById("loadingState");
  const resultsSection = document.getElementById("results");
  const historySection = document.getElementById("historySection");

  const badgeCategory = document.getElementById("badgeCategory");
  const badgeSubcategory = document.getElementById("badgeSubcategory");
  const badgeSentiment = document.getElementById("badgeSentiment");

  const replyMain = document.getElementById("replyMain");
  const replyAlt = document.getElementById("replyAlt");

  const btnShort = document.getElementById("btnShort");
  const btnFormal = document.getElementById("btnFormal");
  const btnTechnical = document.getElementById("btnTechnical");
  const copyMainBtn = document.getElementById("copyMainReply");
  const clearBtn = document.getElementById("clearHistoryBtn");
  const exportBtn = document.getElementById("exportExcel");

  let lastData = null;


  
  // RENDER 1 EMAIL
  

  function renderSingleResult(data, save = true) {
    badgeCategory.textContent = data.categoria;
    badgeSubcategory.textContent = data.subcategoria;
    badgeSentiment.textContent = data.sentimento;

    badgeCategory.classList.remove("badge-prod", "badge-improd");
    badgeCategory.classList.add(
      data.categoria.toLowerCase() === "produtivo"
        ? "badge-prod"
        : "badge-improd"
    );

    replyMain.textContent = data.reply_main;
    replyAlt.textContent = data.reply_short || "";

    resultsSection.classList.remove("hidden");
    historySection.classList.remove("hidden");

    if (save) {
      saveToHistory({
        categoria: data.categoria,
        subcategoria: data.subcategoria,
        preview: data.explicacao?.slice(0, 60) || "",
        hora: new Date().toLocaleString(),
        full: data
      });

      renderHistory();
    }
  }


  
  // RENDER LISTA (TXT, PDF, JSON)
  

  function renderBatchResults(list) {
    const results = document.getElementById("results");
    results.innerHTML = "";

    list.forEach((item, index) => {
      const isProd = item.categoria?.toLowerCase() === "produtivo";

      results.innerHTML += `
        <div class="card results-card fade-in" style="margin-bottom: 20px;">
          <h3>Email ${index + 1}</h3>

          <span class="badge ${isProd ? "badge-prod" : "badge-improd"}">
            ${item.categoria}
          </span>

          <p><strong>Subcategoria:</strong> ${item.subcategoria}</p>
          <p><strong>Sentimento:</strong> ${item.sentimento}</p>
          <p><strong>Explicação:</strong> ${item.explicacao}</p>

          <h4>Resposta Sugerida</h4>
          <p>${item.reply_main}</p>

          <details>
            <summary style="cursor:pointer;">Ver alternativas</summary>
            <ul>
              <li>${item.reply_short}</li>
              <li>${item.reply_formal}</li>
              <li>${item.reply_technical}</li>
            </ul>
          </details>
        </div>
      `;

      saveToHistory({
        categoria: item.categoria,
        subcategoria: item.subcategoria,
        preview: item.explicacao?.slice(0, 60),
        hora: new Date().toLocaleString(),
        full: item
      });
    });

    resultsSection.classList.remove("hidden");
    historySection.classList.remove("hidden");
    renderHistory();
  }


  
  // HISTÓRICO — clique
  

  document.getElementById("historyList").addEventListener("click", (e) => {
    const item = e.target.closest(".history-item");
    if (!item) return;

    const index = item.dataset.index;
    const history = JSON.parse(localStorage.getItem("history") || "[]");

    renderSingleResult(history[index].full, false);
  });



  
  // BOTÃO ANALISAR
  

  analyzeBtn.addEventListener("click", async () => {

    // Se digitou algo → ignorar arquivos
    if (textarea.value.trim().length > 0) {
      window.lastPdfFile = null;
      window.lastTxtFile = null;
    }

    const raw = textarea.value.trim();


    
    // PROCESSAR TXT
    
    if (window.lastTxtFile) {
      loading.classList.remove("hidden");
      try {
        const result = await analyzeBatchTXT(window.lastTxtFile);
        renderBatchResults(result.resultados);
      } catch {
        alert("Erro ao enviar TXT.");
      }
      window.lastTxtFile = null;
      loading.classList.add("hidden");
      return;
    }


  
    // PROCESSAR PDF
    
    if (window.lastPdfFile) {
      loading.classList.remove("hidden");

      try {
        const data = await analyzePDF(window.lastPdfFile);
        renderBatchResults(data.resultados);
      } catch {
        alert("Erro ao enviar PDF.");
      }

      window.lastPdfFile = null;
      loading.classList.add("hidden");
      return;
    }


    
    // TEXTO DIGITADO
    
    if (!raw) {
      alert("Digite ou cole um e-mail.");
      return;
    }

    const emails = splitEmails(raw);
    loading.classList.remove("hidden");

    try {
      if (emails.length === 1) {
        const r = await analyzeEmail(emails[0]);
        lastData = r;
        renderSingleResult(r);
      } else {
        const batch = await analyzeBatchJSON(emails);
        renderBatchResults(batch.resultados);
      }
    } catch {
      alert("Erro ao conectar com o servidor.");
    }

    loading.classList.add("hidden");
  });



  
  // BOTÕES DE RESPOSTAS ALTERNATIVAS
  

  btnShort.addEventListener("click", () => {
    if (lastData) replyAlt.textContent = lastData.reply_short;
  });

  btnFormal.addEventListener("click", () => {
    if (lastData) replyAlt.textContent = lastData.reply_formal;
  });

  btnTechnical.addEventListener("click", () => {
    if (lastData) replyAlt.textContent = lastData.reply_technical;
  });



  
  // COPIAR RESPOSTA
  

  copyMainBtn.addEventListener("click", async () => {
    const text = replyMain.textContent.trim();
    if (!text) return alert("Nada para copiar.");

    await navigator.clipboard.writeText(text);
    alert("Resposta copiada!");
  });



  
  // LIMPAR HISTÓRICO
  

  clearBtn.addEventListener("click", () => {
    if (confirm("Deseja mesmo limpar todo o histórico?")) {
      clearHistory();
      renderHistory();
    }
  });



  
  // EXPORTAR PARA EXCEL
  

  exportBtn.addEventListener("click", () => {
    const history = JSON.parse(localStorage.getItem("history") || "[]");

    if (history.length === 0) {
      alert("Nenhum email no histórico.");
      return;
    }

    const rows = history.map(item => ({
      Categoria: item.full.categoria,
      Subcategoria: item.full.subcategoria,
      Sentimento: item.full.sentimento,
      Resposta: item.full.reply_main,
      Explicacao: item.full.explicacao,
      EmailOriginal: item.full.email || "(Texto original não disponível)"
    }));

    const wb = XLSX.utils.book_new();
    const ws = XLSX.utils.json_to_sheet(rows);

    XLSX.utils.book_append_sheet(wb, ws, "Emails");
    XLSX.writeFile(wb, "inboxinsight_emails.xlsx");
  });


  // Render inicial do histórico
  renderHistory();
});
