const API_BASE_URL = (import.meta.env.VITE_API_BASE_URL ?? "http://127.0.0.1:8000").replace(/\/$/, "");

export type OutputType = "research_paper" | "summary" | "speech" | "notes" | "project_plan";
export type ToolMode = "direct" | "mcp";

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
  steps: string[];
  sources: AgentSource[];
  output?: string;
  drive_link: string | null;
  memory_id?: string;
  title?: string;
  abstract?: string;
  keywords?: string[];
  sections?: { title: string; content: string[] }[];
  citations?: string[];
  references?: { text: string }[];
  pdf_path?: string;
  memory_id: string;
  uploaded_file?: {
    id: number;
    filename: string;
    stored_path: string;
    file_type: string;
    extracted_characters: number;
  };
};

export type HistoryItem = {
  output_id: number;
  topic: string;
  input_prompt: string;
  output_type: string;
  content: string;
  content_preview: string;
  drive_link: string | null;
  created_at: string;
  sources: AgentSource[];
  files?: Array<{
    id: number;
    filename: string;
    file_type: string;
    file_path: string;
    created_at: string;
  }>;
};

export type StreamEventName =
  | "planning"
  | "searching"
  | "processing"
  | "generating"
  | "uploading"
  | "completed"
  | "error";

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

export async function generate(
  prompt: string,
  outputType: OutputType = "summary",
  uploadToDrive = false,
  toolMode: ToolMode = "mcp",
  formatType = "ieee",
  pageLength = "4-5",
  includeFormulas = false,
  includeDiagrams = false
) {
  const response = await fetch(`${API_BASE_URL}/generate`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      prompt,
      output_type: outputType,
      upload_to_drive: uploadToDrive,
      tool_mode: toolMode,
      format_type: formatType,
      page_length: pageLength,
      include_formulas: includeFormulas,
      include_diagrams: includeDiagrams,
    }),
  });
  return parseJsonResponse<AgentResponse>(response);
}

export async function uploadResearchFile(
  file: File,
  prompt: string,
  outputType: OutputType = "summary",
  uploadToDrive = false,
  toolMode: ToolMode = "mcp"
) {
  const form = new FormData();
  form.append("file", file);
  form.append("prompt", prompt);
  form.append("output_type", outputType);
  form.append("upload_to_drive", String(uploadToDrive));
  form.append("tool_mode", toolMode);

  const response = await fetch(`${API_BASE_URL}/upload`, {
    method: "POST",
    body: form,
  });
  return parseJsonResponse<AgentResponse>(response);
}

export async function getHistory(limit = 30) {
  const response = await fetch(`${API_BASE_URL}/history?limit=${limit}`);
  return parseJsonResponse<{ status: string; items: HistoryItem[] }>(response);
}

export function streamGenerate(
  params: {
    prompt: string;
    outputType?: OutputType;
    uploadToDrive?: boolean;
    toolMode?: ToolMode;
    formatType?: string;
    pageLength?: string;
    includeFormulas?: boolean;
    includeDiagrams?: boolean;
  },
  onEvent: (event: StreamEventName, data: unknown) => void
) {
  const query = new URLSearchParams({
    prompt: params.prompt,
    output_type: params.outputType ?? "summary",
    upload_to_drive: String(params.uploadToDrive ?? false),
    tool_mode: params.toolMode ?? "mcp",
    format_type: params.formatType ?? "ieee",
    page_length: params.pageLength ?? "4-5",
    include_formulas: String(params.includeFormulas ?? false),
    include_diagrams: String(params.includeDiagrams ?? false),
  });
  const source = new EventSource(`${API_BASE_URL}/generate/stream?${query.toString()}`);

  const names: StreamEventName[] = [
    "planning",
    "searching",
    "processing",
    "generating",
    "uploading",
    "completed",
    "error",
  ];
  names.forEach((name) => {
    source.addEventListener(name, (event) => {
      try {
        const data = JSON.parse((event as MessageEvent).data);
        onEvent(name, data);
      } catch {
        onEvent(name, (event as MessageEvent).data);
      }
    });
  });
  source.onerror = () => {
    onEvent("error", { message: "Streaming connection lost." });
    source.close();
  };

  return () => source.close();
}