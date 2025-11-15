export const BASE_URL = "https://inboxinsight-x8w5.onrender.com";

export async function analyzeEmail(emailText) {
  const response = await fetch(`${BASE_URL}/analyze`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ email_text: emailText }),
  });
  return await response.json();
}

export async function analyzeBatchJSON(list) {
  const response = await fetch(`${BASE_URL}/analyze-batch-json`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ emails: list }),
  });
  return await response.json();
}

export async function analyzeBatchTXT(file) {
  const formData = new FormData();
  formData.append("file", file);
  const response = await fetch(`${BASE_URL}/analyze-batch-txt`, {
    method: "POST",
    body: formData
  });
  return await response.json();
}

export async function analyzePDF(file) {
  const formData = new FormData();
  formData.append("file", file);
  const response = await fetch(`${BASE_URL}/analyze-pdf`, {
    method: "POST",
    body: formData
  });
  return await response.json();
}
