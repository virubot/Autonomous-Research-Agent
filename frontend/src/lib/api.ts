const API_BASE_URL = (import.meta.env.VITE_API_BASE_URL ?? "http://127.0.0.1:8000").replace(/\/$/, "");
const NODE_API_BASE_URL = (import.meta.env.VITE_NODE_API_BASE_URL ?? "http://127.0.0.1:5001").replace(/\/$/, "");

type AssistantResponse = {
  answer?: string;
  error?: string;
};

type PaperResponse = {
  paper?: string;
  error?: string;
};

export async function askAssistant(query: string) {
  const response = await fetch(`${NODE_API_BASE_URL}/api/chat`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify({ type: "chat", message: query }),
  });

  if (!response.ok) {
    throw new Error(`Assistant request failed with status ${response.status}`);
  }

  const data = (await response.json()) as AssistantResponse;

  if (data.error && !data.answer) {
    throw new Error(data.error);
  }

  return data;
}

export async function generatePaper(topic: string) {
  const response = await fetch(`${NODE_API_BASE_URL}/api/generate-paper`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify({ type: "paper", topic }),
  });

  if (!response.ok) {
    throw new Error(`Paper generation request failed with status ${response.status}`);
  }

  const data = (await response.json()) as PaperResponse;

  if (data?.error) {
    throw new Error(data.error);
  }

  return data;
}

export const generateResearchPaper = generatePaper;

export async function downloadPDF() {
  const response = await fetch(`${API_BASE_URL}/download`);

  if (!response.ok) {
    throw new Error(`PDF download failed with status ${response.status}`);
  }

  const blob = await response.blob();
  const url = window.URL.createObjectURL(blob);

  const a = document.createElement("a");
  a.href = url;
  a.download = "research_paper.pdf";
  document.body.appendChild(a);
  a.click();
  a.remove();

  window.setTimeout(() => window.URL.revokeObjectURL(url), 0);
}
