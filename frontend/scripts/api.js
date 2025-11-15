export async function analyzeEmail(emailText) {
  // Depois vamos trocar esse URL pelo do seu backend (Render, etc.)
  const url = "http://localhost:8000/analyze";

  const response = await fetch(url, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ email_text: emailText })
  });

  if (!response.ok) {
    throw new Error("Backend error");
  }

  return await response.json();
}

export async function analyzeBatchJSON(emailList) {
  // Depois vamos trocar esse URL pelo do seu backend (Render, etc.)
  const url = "http://localhost:8000/analyze-batch-json";

  const response = await fetch(url, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ emails: emailList })
  });

  if (!response.ok) {
    throw new Error("Erro noBackend (batch)");
  }

  return await response.json();
}

export async function analyzeBatchTXT(file) {
  const url = "http://localhost:8000/analyze-batch-txt";

  const formData = new FormData();
  formData.append("file", file);

  const response = await fetch(url, {
    method: "POST",
    body: formData
  });

  if (!response.ok) {
    throw new Error("Erro ao enviar TXT para o backend.");
  }

  return await response.json();
}
