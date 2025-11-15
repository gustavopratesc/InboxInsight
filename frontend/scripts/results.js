import { analyzeEmail } from "./api.js";

export async function analyzeEmailAndRender() {
  const textarea = document.getElementById("emailText");
  const loading = document.getElementById("loadingState");
  const resultsSection = document.getElementById("resultsSection");
  const historySection = document.getElementById("historySection");

  const badgeCategory = document.getElementById("badgeCategory");
  const badgeSubcategory = document.getElementById("badgeSubcategory");
  const badgeSentiment = document.getElementById("badgeSentiment");

  const replyMain = document.getElementById("replyMain");
  const replyAlt = document.getElementById("replyAlt");

  const emailText = textarea.value.trim();
  if (!emailText) {
    alert("Please paste an email or upload a file first.");
    return;
  }

  loading.classList.remove("hidden");
  resultsSection.classList.add("hidden");

  try {
    const data = await analyzeEmail(emailText);

    // Atualiza badges
    badgeCategory.textContent = data.category || "N/A";
    badgeSubcategory.textContent = data.subcategory || "N/A";
    badgeSentiment.textContent = data.sentiment || "N/A";

    // Respostas
    replyMain.textContent = data.reply_main || "";
    replyAlt.textContent =
      data.reply_short || data.reply_formal || data.reply_technical || "";

    resultsSection.classList.remove("hidden");
    historySection.classList.remove("hidden");
    // depois adicionamos saveHistory(data)
  } catch (err) {
    console.error(err);
    alert("An error occurred while analyzing the email.");
  } finally {
    loading.classList.add("hidden");
  }
}
