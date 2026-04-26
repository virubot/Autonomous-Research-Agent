import { useEffect, useRef, useState } from "react";
import { FileText, MessageCircle, Microscope, Search, Sparkles } from "lucide-react";
import { MeshBackground } from "@/components/MeshBackground";
import { ChatSidebar, type ChatSummary } from "@/components/ChatSidebar";
import { ChatMessage, MessageBubble, TypingIndicator } from "@/components/ChatMessage";
import { ChatInput } from "@/components/ChatInput";
import { PaperGenerator } from "@/components/PaperGenerator";
import { SourcesPanel } from "@/components/SourcesPanel";
import { askAssistant, generatePaper } from "@/lib/api";

type ChatRecord = ChatSummary & { messages: ChatMessage[] };

const seedChats: ChatRecord[] = [
  {
    id: "c1",
    title: "Transformer architectures overview",
    preview: "Compare encoder-decoder vs decoder-only…",
    updatedAt: "Today",
    messages: [
      {
        id: "m1",
        role: "assistant",
        content:
          "Welcome to AI Research Assistant. Ask me to summarize papers, compare methods, or draft a literature review. I'll cite sources as I go.",
      },
    ],
  },
  {
    id: "c2",
    title: "RAG vs fine-tuning trade-offs",
    preview: "When does retrieval beat fine-tuning?",
    updatedAt: "Yesterday",
    messages: [
      { id: "m1", role: "assistant", content: "Let's analyze RAG versus fine-tuning across cost, latency, and accuracy." },
    ],
  },
  {
    id: "c3",
    title: "Diffusion models in biology",
    preview: "Protein structure generation review",
    updatedAt: "2d ago",
    messages: [
      { id: "m1", role: "assistant", content: "Here's a survey of diffusion approaches for biomolecular design." },
    ],
  },
];

const Index = () => {
  const [chats, setChats] = useState<ChatRecord[]>(seedChats);
  const [activeId, setActiveId] = useState<string>(seedChats[0].id);
  const [input, setInput] = useState("");
  const [mode, setMode] = useState<"chat" | "paper">("chat");
  const [isThinking, setIsThinking] = useState(false);
  const [collapsed, setCollapsed] = useState(false);
  const scrollRef = useRef<HTMLDivElement>(null);

  const active = chats.find((c) => c.id === activeId)!;

  useEffect(() => {
    // Auto-collapse on small screens
    const onResize = () => setCollapsed(window.innerWidth < 768);
    onResize();
    window.addEventListener("resize", onResize);
    return () => window.removeEventListener("resize", onResize);
  }, []);

  useEffect(() => {
    scrollRef.current?.scrollTo({ top: scrollRef.current.scrollHeight, behavior: "smooth" });
  }, [active.messages.length, isThinking, activeId]);

  const updateActive = (updater: (c: ChatRecord) => ChatRecord) => {
    setChats((prev) => prev.map((c) => (c.id === activeId ? updater(c) : c)));
  };

  const handleSend = async () => {
    const text = input.trim();
    if (!text) return;
    const chatId = activeId;
    const userMsg: ChatMessage = { id: crypto.randomUUID(), role: "user", content: text };
    updateActive((c) => ({
      ...c,
      title: c.messages.length <= 1 ? text.slice(0, 42) : c.title,
      preview: text.slice(0, 60),
      messages: [...c.messages, userMsg],
    }));
    setInput("");
    setIsThinking(true);

    try {
      const content =
        mode === "paper"
          ? (await generatePaper(text)).paper ?? "Paper generation returned no content."
          : (await askAssistant(text)).answer ?? "No useful research data found.";

      const aiMsg: ChatMessage = {
        id: crypto.randomUUID(),
        role: "assistant",
        content,
      };
      setChats((prev) => prev.map((c) => (c.id === chatId ? { ...c, messages: [...c.messages, aiMsg] } : c)));
    } catch (error) {
      console.error("Assistant request failed:", error);
      const aiMsg: ChatMessage = {
        id: crypto.randomUUID(),
        role: "assistant",
        content: error instanceof Error ? error.message : "Assistant request failed.",
      };
      setChats((prev) => prev.map((c) => (c.id === chatId ? { ...c, messages: [...c.messages, aiMsg] } : c)));
    } finally {
      setIsThinking(false);
    }
  };

  const handleNewChat = () => {
    const id = crypto.randomUUID();
    const newChat: ChatRecord = {
      id,
      title: "New research thread",
      preview: "Start a new investigation…",
      updatedAt: "Now",
      messages: [
        {
          id: crypto.randomUUID(),
          role: "assistant",
          content:
            "New session ready. What topic should we investigate? I can search papers, summarize findings, or draft sections.",
        },
      ],
    };
    setChats((prev) => [newChat, ...prev]);
    setActiveId(id);
  };

  const handleDeleteChat = (id: string) => {
    setChats((prev) => {
      const next = prev.filter((c) => c.id !== id);
      if (next.length === 0) {
        const fresh: ChatRecord = {
          id: crypto.randomUUID(),
          title: "New research thread",
          preview: "Start a new investigation…",
          updatedAt: "Now",
          messages: [
            {
              id: crypto.randomUUID(),
              role: "assistant",
              content:
                "New session ready. What topic should we investigate? I can search papers, summarize findings, or draft sections.",
            },
          ],
        };
        setActiveId(fresh.id);
        return [fresh];
      }
      if (id === activeId) setActiveId(next[0].id);
      return next;
    });
  };

  const isEmpty = active.messages.length <= 1;

  return (
    <div className="relative flex h-screen w-full overflow-hidden">
      <MeshBackground />

      <ChatSidebar
        chats={chats}
        activeId={activeId}
        onSelect={setActiveId}
        onNewChat={handleNewChat}
        onDeleteChat={handleDeleteChat}
        collapsed={collapsed}
        onToggle={() => setCollapsed((v) => !v)}
      />

      {/* Main */}
      <main className="flex min-w-0 flex-1 flex-col">
        {/* Header — floats on background, no hard divider */}
        <header className="z-10 flex items-center justify-between gap-3 px-6 py-5 md:px-10">
          <div className="flex items-center gap-3">
            <div className="flex h-9 w-9 items-center justify-center rounded-xl bg-primary/15 text-primary backdrop-blur-sm">
              <Microscope className="h-4 w-4" strokeWidth={2.2} />
            </div>
            <div>
              <h1 className="text-[15px] font-semibold leading-tight text-foreground">
                AI Research Assistant
              </h1>
              <p className="text-[12px] text-muted-foreground">
                Search · Analyze · Generate Research Papers
              </p>
            </div>
          </div>
          <div className="hidden items-center gap-2 rounded-full bg-foreground/[0.05] px-3 py-1 backdrop-blur-sm md:flex">
            <span className="h-1.5 w-1.5 rounded-full bg-primary" />
            <span className="text-[11px] font-medium text-muted-foreground">Online</span>
          </div>
        </header>

        {/* Body: messages + right rail */}
        <div className="flex min-h-0 flex-1">
          {/* Messages column */}
          <section className="relative flex min-w-0 flex-1 flex-col">
            <div ref={scrollRef} className="flex-1 overflow-y-auto px-4 pt-6 pb-4 md:px-10">
              <div className="mx-auto w-full max-w-3xl space-y-7">
                {isEmpty && (
                  <div className="animate-fade-in py-10 text-center">
                    <div className="mx-auto mb-5 flex h-12 w-12 items-center justify-center rounded-2xl bg-primary/15 text-primary backdrop-blur-sm">
                      <Sparkles className="h-5 w-5" strokeWidth={2.2} />
                    </div>
                    <h2 className="text-[24px] font-semibold tracking-tight text-foreground md:text-[28px]">
                      What would you like to research?
                    </h2>
                    <p className="mx-auto mt-2 max-w-md text-[13px] text-muted-foreground">
                      Ask a question, request a literature review, or generate a draft paper.
                    </p>
                    <div className="mx-auto mt-8 grid max-w-2xl grid-cols-1 gap-2.5 sm:grid-cols-2">
                      {[
                        "Summarize recent work on retrieval-augmented generation",
                        "Compare LoRA vs full fine-tuning on small models",
                        "Find papers on diffusion models in protein design",
                        "Draft an abstract on multimodal reasoning benchmarks",
                      ].map((q) => (
                        <button
                          key={q}
                          onClick={() => setInput(q)}
                          className="ring-focus group flex items-start gap-2 rounded-xl bg-foreground/[0.04] px-3.5 py-3 text-left text-[13px] text-muted-foreground backdrop-blur-sm transition-all hover:bg-foreground/[0.07] hover:text-foreground"
                        >
                          <Search className="mt-0.5 h-3.5 w-3.5 shrink-0 text-muted-foreground transition-colors group-hover:text-primary" />
                          <span>{q}</span>
                        </button>
                      ))}
                    </div>
                  </div>
                )}

                {active.messages.map((m) => (
                  <MessageBubble key={m.id} message={m} />
                ))}
                {isThinking && <TypingIndicator />}
                <div className="h-4" />
              </div>
            </div>

            {/* Input — floating, no top border, soft fade */}
            <div className="relative px-4 pb-5 pt-2 md:px-10">
              {/* Subtle fade from background to input area */}
              <div
                className="pointer-events-none absolute inset-x-0 -top-12 h-12"
                style={{
                  background:
                    "linear-gradient(to bottom, transparent, hsl(var(--background) / 0.4))",
                }}
              />
              <div className="mx-auto w-full max-w-3xl">
                <div className="mb-3 flex justify-center">
                  <div className="glass-subtle flex rounded-xl p-1">
                    <button
                      type="button"
                      onClick={() => setMode("paper")}
                      className={`ring-focus flex items-center gap-1.5 rounded-lg px-3 py-1.5 text-[12px] font-medium transition-colors ${
                        mode === "paper"
                          ? "bg-primary text-primary-foreground"
                          : "text-muted-foreground hover:bg-foreground/[0.06] hover:text-foreground"
                      }`}
                    >
                      <FileText className="h-3.5 w-3.5" />
                      Paper Mode
                    </button>
                    <button
                      type="button"
                      onClick={() => setMode("chat")}
                      className={`ring-focus flex items-center gap-1.5 rounded-lg px-3 py-1.5 text-[12px] font-medium transition-colors ${
                        mode === "chat"
                          ? "bg-primary text-primary-foreground"
                          : "text-muted-foreground hover:bg-foreground/[0.06] hover:text-foreground"
                      }`}
                    >
                      <MessageCircle className="h-3.5 w-3.5" />
                      Chat Mode
                    </button>
                  </div>
                </div>
                <ChatInput value={input} onChange={setInput} onSend={handleSend} disabled={isThinking} />
                <p className="mt-2 text-center text-[11px] text-muted-foreground">
                  Responses are AI-generated. Verify citations before publishing.
                </p>
              </div>
            </div>
          </section>

          {/* Right rail — floating panels, no hard divider */}
          <aside className="hidden w-80 shrink-0 flex-col gap-5 overflow-y-auto px-5 py-6 lg:flex">
            <PaperGenerator />
            <div className="glass rounded-2xl px-3 py-3">
              <SourcesPanel />
            </div>
          </aside>
        </div>
      </main>
    </div>
  );
};

export default Index;
