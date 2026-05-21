import { useCallback, useEffect, useRef, useState } from "react";
import { MeshBackground } from "@/components/MeshBackground";
import { ChatSidebar, type ChatSummary } from "@/components/ChatSidebar";
import { ChatInput } from "@/components/ChatInput";
import { MessageBubble, TypingIndicator, type ChatMessage } from "@/components/ChatMessage";
import { SourcesPanel } from "@/components/SourcesPanel";
import { PaperGenerator } from "@/components/PaperGenerator";
import {
  uploadResearchFile,
  streamGenerate,
  type AgentResponse,
  type AgentSource,
  type StreamEventName,
  type OutputType,
} from "@/lib/api";

/* ── helpers ─────────────────────────────────────────────────── */
const uid = () => crypto.randomUUID?.() ?? Math.random().toString(36).slice(2);

function titleFromPrompt(prompt: string) {
  const clean = prompt.replace(/\n/g, " ").trim();
  return clean.length > 50 ? clean.slice(0, 47) + "…" : clean || "New chat";
}

const STAGE_LABELS: Record<string, string> = {
  planning: "Building execution plan…",
  searching: "Searching the web…",
  processing: "Processing files…",
  generating: "Generating final output…",
  uploading: "Uploading to Google Drive…",
};

/* ── component ───────────────────────────────────────────────── */
type ChatRecord = {
  id: string;
  title: string;
  messages: ChatMessage[];
  sources: AgentSource[];
};

const Index = () => {
  /* sidebar */
  const [sidebarCollapsed, setSidebarCollapsed] = useState(false);

  /* chats */
  const [chats, setChats] = useState<ChatRecord[]>([]);
  const [activeId, setActiveId] = useState<string>("");

  /* input */
  const [input, setInput] = useState("");
  const [selectedFile, setSelectedFile] = useState<File | null>(null);

  /* agent state */
  const [loading, setLoading] = useState(false);
  const [stage, setStage] = useState<string | undefined>(undefined);
  const [liveSteps, setLiveSteps] = useState<string[]>([]);

  const scrollRef = useRef<HTMLDivElement>(null);
  const historyLoaded = useRef(false);
  const streamCloseRef = useRef<(() => void) | null>(null);

  /* active chat helper */
  const active = chats.find((c) => c.id === activeId);
  const messages = active?.messages ?? [];
  const sources = active?.sources ?? [];

  /* scroll to bottom */
  useEffect(() => {
    const el = scrollRef.current;
    if (el) el.scrollTop = el.scrollHeight;
  }, [messages.length, loading, liveSteps]);

  /* ── clean startup: no auto history load ── */
  useEffect(() => {
    if (historyLoaded.current) return;
    historyLoaded.current = true;
    // Start with a single blank chat — history is opt-in only
    const id = uid();
    setChats([{ id, title: "New chat", messages: [], sources: [] }]);
    setActiveId(id);
  }, []);

  /* ── new / select / delete chat ── */
  const handleNewChat = useCallback(() => {
    const id = uid();
    setChats((prev) => [{ id, title: "New chat", messages: [], sources: [] }, ...prev]);
    setActiveId(id);
    setInput("");
    setSelectedFile(null);
    setLiveSteps([]);
    setStage(undefined);
  }, []);

  const handleSelectChat = useCallback((id: string) => {
    setActiveId(id);
    setInput("");
    setSelectedFile(null);
    setLiveSteps([]);
    setStage(undefined);
  }, []);

  const handleDeleteChat = useCallback(
    (id: string) => {
      const fallbackId = uid();
      setChats((prev) => {
        const next = prev.filter((c) => c.id !== id);
        if (next.length === 0) {
          const replacement = { id: fallbackId, title: "New chat", messages: [], sources: [] };
          setActiveId(replacement.id);
          return [replacement];
        }
        if (id === activeId) {
          setActiveId(next[0].id);
        }
        return next;
      });
    },
    [activeId]
  );

  /* ── append message ── */
  const appendMessage = useCallback(
    (msg: ChatMessage, chatSources?: AgentSource[]) => {
      setChats((prev) =>
        prev.map((c) =>
          c.id === activeId
            ? {
                ...c,
                title: c.title === "New chat" && msg.role === "user" ? titleFromPrompt(msg.content) : c.title,
                messages: [...c.messages, msg],
                sources: chatSources ?? c.sources,
              }
            : c
        )
      );
    },
    [activeId]
  );

  /* ── handle send ── */
  const handleSend = useCallback(async () => {
    const prompt = input.trim();
    const file = selectedFile;

    if (!prompt && !file) return;
    if (loading) return;

    const userContent = file ? `${prompt || "Analyze this file"}\n📎 ${file.name}` : prompt;
    appendMessage({ id: uid(), role: "user", content: userContent });
    setInput("");
    setSelectedFile(null);
    setLoading(true);
    setStage(undefined);
    setLiveSteps([]);

    try {
      let result: AgentResponse;

      if (file) {
        // ── file upload path (no SSE yet for upload) ──
        setStage("Uploading and processing file…");
        result = await uploadResearchFile(file, prompt || "Analyze this file");
        setStage(undefined);
      } else {
        // ── streaming path ──
        result = await new Promise<AgentResponse>((resolve, reject) => {
          const close = streamGenerate(
            { prompt, outputType: "summary" as OutputType },
            (event: StreamEventName, data: unknown) => {
              if (event === "error") {
                reject(
                  new Error(
                    (data as { message?: string })?.message ?? "Agent execution failed."
                  )
                );
                return;
              }
              if (event === "completed") {
                resolve(data as AgentResponse);
                return;
              }
              // live step updates
              const label = STAGE_LABELS[event];
              if (label) setStage(label);
              const payload = data as { message?: string };
              if (payload?.message) {
                setLiveSteps((prev) =>
                  prev.includes(payload.message!) ? prev : [...prev, payload.message!]
                );
              }
            }
          );
          streamCloseRef.current = close;
        });
        setStage(undefined);
      }

      appendMessage(
        {
          id: uid(),
          role: "assistant",
          content: result.output,
          sources: result.sources,
          steps: result.steps,
          driveLink: result.drive_link,
        },
        result.sources
      );
    } catch (err) {
      appendMessage({
        id: uid(),
        role: "assistant",
        content: `⚠️ ${err instanceof Error ? err.message : "Something went wrong."}`,
      });
    } finally {
      setLoading(false);
      setStage(undefined);
      setLiveSteps([]);
      streamCloseRef.current = null;
    }
  }, [input, selectedFile, loading, appendMessage]);

  /* ── sidebar summaries ── */
  const sidebarChats: ChatSummary[] = chats.map((c) => {
    const lastMsg = c.messages[c.messages.length - 1];
    return {
      id: c.id,
      title: c.title,
      preview: lastMsg ? lastMsg.content.slice(0, 60) : "",
      updatedAt: "",
    };
  });

  /* ── render ── */
  return (
    <div className="flex h-full overflow-hidden">
      <MeshBackground />

      {/* Sidebar */}
      <ChatSidebar
        chats={sidebarChats}
        activeId={activeId}
        onSelect={handleSelectChat}
        onNewChat={handleNewChat}
        onDeleteChat={handleDeleteChat}
        collapsed={sidebarCollapsed}
        onToggle={() => setSidebarCollapsed((v) => !v)}
      />

      {/* Main chat area */}
      <main className="relative flex min-w-0 flex-1 flex-col">
        {/* Messages */}
        <div ref={scrollRef} className="flex-1 overflow-y-auto px-4 pt-6 pb-4 md:px-8">
          <div className="mx-auto flex max-w-3xl flex-col gap-5">
            {messages.length === 0 && !loading && (
              <div className="flex flex-col items-center justify-center pt-[20vh] pb-10 text-center animate-fade-in">
                <div className="mb-6 flex h-16 w-16 items-center justify-center rounded-2xl bg-gradient-to-br from-primary/20 to-accent/20 text-primary shadow-[0_0_30px_rgba(100,70,255,0.2)] backdrop-blur-md">
                  <span className="text-3xl">✨</span>
                </div>
                <h1 className="text-3xl font-bold tracking-tight text-foreground sm:text-4xl">
                  What are we researching today?
                </h1>
                <p className="mt-4 max-w-lg text-[15px] leading-relaxed text-muted-foreground">
                  Upload a document, ask a technical question, or request a full academic paper generation.
                </p>
                
                <div className="mt-10 flex flex-wrap justify-center gap-3">
                  {["Summarize the latest AI papers", "Generate an IEEE paper structure", "Analyze my uploaded PDF"].map((suggestion) => (
                    <button
                      key={suggestion}
                      onClick={() => setInput(suggestion)}
                      className="rounded-xl border border-white/10 bg-black/40 px-4 py-2.5 text-[13px] font-medium text-muted-foreground transition-all hover:bg-white/10 hover:text-foreground shadow-soft"
                    >
                      {suggestion}
                    </button>
                  ))}
                </div>
              </div>
            )}

            {messages.map((msg) => (
              <MessageBubble key={msg.id} message={msg} />
            ))}

            {loading && <TypingIndicator stage={stage} />}
          </div>
        </div>

        {/* Agent live steps bar */}
        {loading && liveSteps.length > 0 && (
          <div className="mx-auto flex w-full max-w-3xl flex-wrap gap-1.5 px-4 pb-2 md:px-8 animate-fade-in">
            {liveSteps.map((s, i) => (
              <span key={i} className="rounded-full bg-primary/10 px-2.5 py-0.5 text-[10px] font-medium text-primary animate-fade-in">
                ✓ {s}
              </span>
            ))}
          </div>
        )}

        {/* Input Area */}
        <div className="relative px-4 pb-6 pt-4 md:px-8">
          {/* Transparent fade mask at the top of the input container */}
          <div className="absolute inset-x-0 top-0 -mt-8 h-8 bg-gradient-to-t from-[#060608]/90 to-transparent pointer-events-none" />
          
          <div className="mx-auto max-w-3xl">
            <ChatInput
              value={input}
              onChange={setInput}
              onSend={handleSend}
              onFileSelect={setSelectedFile}
              selectedFile={selectedFile}
              onClearFile={() => setSelectedFile(null)}
              disabled={loading}
            />
          </div>
        </div>
      </main>

      {/* Right panel — sources + paper generator */}
      <aside className="hidden w-80 flex-col gap-4 overflow-y-auto border-l border-white/5 bg-[#060608]/40 backdrop-blur-2xl p-4 lg:flex">
        <PaperGenerator />
        <SourcesPanel sources={sources} />
      </aside>
    </div>
  );
};

export default Index;
