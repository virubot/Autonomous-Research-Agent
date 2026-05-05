const API_BASE_URL = (import.meta.env.VITE_API_BASE_URL ?? "http://127.0.0.1:8000").replace(/\/$/, "");

export type AgentSource = {
  ref_id: string;
  title: string;
  url: string;
  snippet: string;
};

export type AgentPlanStep = {
  step?: number;
  action: string;
  tool: string;
  input?: Record<string, unknown>;
};

export type AgentResponse = {
  plan: AgentPlanStep[];
  sources: AgentSource[];
  output: string;
  drive_link: string | null;
  memory_id: string;
  steps: string[];
  uploaded_file?: {
    id: number;
    filename: string;
    stored_path: string;
    file_type: string;
    extracted_characters: number;
  };
};

type HistoryResponse = {
  status: string;
  items: Array<Record<string, unknown>>;
};

async function parseJsonResponse<T>(response: Response): Promise<T> {
  const data = (await response.json()) as T | { detail?: string };
  if (!response.ok) {
    const detail =
      typeof data === "object" && data && "detail" in data && typeof data.detail === "string"
        ? data.detail
        : `Request failed with status ${response.status}`;
    throw new Error(detail);
  }
  return data as T;
}

export async function askAssistant(query: string) {
  const response = await fetch(`${API_BASE_URL}/generate`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify({
      prompt: query,
      output_type: "summary",
    }),
  });

  return parseJsonResponse<AgentResponse>(response);
}

export async function generatePaper(topic: string, uploadToDrive = false) {
  const response = await fetch(`${API_BASE_URL}/generate`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify({
      topic,
      output_type: "research_paper",
      upload_to_drive: uploadToDrive,
    }),
  });

  return parseJsonResponse<AgentResponse>(response);
}

export async function uploadResearchFile(
  file: File,
  prompt: string,
  outputType = "summary",
  uploadToDrive = false
) {
  const form = new FormData();
  form.append("file", file);
  form.append("prompt", prompt);
  form.append("output_type", outputType);
  form.append("upload_to_drive", String(uploadToDrive));

  const response = await fetch(`${API_BASE_URL}/upload`, {
    method: "POST",
    body: form,
  });

  return parseJsonResponse<AgentResponse>(response);
}

export async function getHistory(limit = 20) {
  const response = await fetch(`${API_BASE_URL}/history?limit=${limit}`);
  return parseJsonResponse<HistoryResponse>(response);
}
