import { cn } from "@/lib/utils";
import { CheckCircle2, ExternalLink, Sparkles, User, FileText, BookOpen, Bot } from "lucide-react";
import ReactMarkdown from "react-markdown";
import remarkGfm from "remark-gfm";
import type { AgentSource } from "@/lib/api";
import { MermaidRenderer } from "@/components/MermaidRenderer";

export type ChatMessage = {
  id: string;
  role: "user" | "assistant";
  content: string;
  sources?: AgentSource[];
  steps?: string[];
  driveLink?: string | null;
};

function AgentSteps({ steps }: { steps: string[] }) {
  if (!steps.length) return null;
  return (
    <div className="mb-4 space-y-1.5">
      {steps.map((step, i) => (
        <div
          key={i}
          className="flex items-center gap-2 text-[12px] text-muted-foreground animate-fade-in"
          style={{ animationDelay: `${i * 60}ms` }}
        >
          <div className="flex h-4 w-4 shrink-0 items-center justify-center rounded-full bg-primary/10">
            <CheckCircle2 className="h-3 w-3 text-primary/80" />
          </div>
          <span className="font-medium">{step}</span>
        </div>
      ))}
    </div>
  );
}

function DriveLink({ link }: { link: string }) {
  return (
    <a
      href={link}
      target="_blank"
      rel="noreferrer"
      className="mt-4 inline-flex items-center gap-2 rounded-xl border border-primary/30 bg-primary/10 px-4 py-2.5 text-[13px] font-bold text-primary shadow-[0_0_15px_rgba(100,70,255,0.1)] transition-all hover:bg-primary/20 hover:shadow-[0_0_20px_rgba(100,70,255,0.2)]"
    >
      <ExternalLink className="h-4 w-4" />
      View Document in Drive
    </a>
  );
}

function containsMermaid(content: string) {
  return /```mermaid\s*[\s\S]*?```/i.test(content);
}

/** Detects if a string is likely a raw research-paper JSON blob */
function tryParseResearchPaper(content: string): Record<string, unknown> | null {
  const trimmed = content.trim();
  if (!trimmed.startsWith("{")) return null;
  try {
    const parsed = JSON.parse(trimmed);
    if (parsed && typeof parsed === "object" && ("title" in parsed || "abstract" in parsed)) {
      return parsed as Record<string, unknown>;
    }
  } catch {
    // not valid JSON
  }
  return null;
}

/** Clean summary card for when the agent returns a research-paper JSON blob */
function ResearchPaperCard({ data }: { data: Record<string, unknown> }) {
  const title = (data.title as string) || "Research Paper";
  const abstract = (data.abstract as string) || "";
  const keywords = (data.keywords as string[]) || [];
  const authors = (data.authors as string[]) || [];
  const sections = (data.sections as { title: string }[]) || [];

  return (
    <div className="w-full rounded-[1.25rem] border border-white/10 bg-black/40 p-5 space-y-4 shadow-inner animate-fade-in">
      <div className="flex items-start gap-4">
        <div className="flex h-10 w-10 shrink-0 items-center justify-center rounded-xl bg-gradient-to-br from-primary/20 to-accent/20 text-primary shadow-soft mt-0.5">
          <FileText className="h-5 w-5" strokeWidth={2.5} />
        </div>
        <div className="min-w-0 flex-1">
          <p className="text-[15px] font-bold text-foreground leading-snug">{title}</p>
          {authors.length > 0 && (
            <p className="mt-1 text-[12px] font-medium text-muted-foreground">{authors.join(", ")}</p>
          )}
        </div>
      </div>

      {abstract && (
        <div className="rounded-xl border border-white/5 bg-white/5 px-4 py-3">
          <p className="text-[10px] font-bold uppercase tracking-[0.15em] text-primary mb-1.5">Abstract</p>
          <p className="text-[13px] text-muted-foreground leading-relaxed line-clamp-4">{abstract}</p>
        </div>
      )}

      {sections.length > 0 && (
        <div className="flex flex-wrap gap-2">
          {sections.map((s, i) => (
            <span key={i} className="rounded-lg bg-primary/10 border border-primary/20 px-3 py-1 text-[11px] font-bold text-primary shadow-soft">
              {s.title}
            </span>
          ))}
        </div>
      )}

      {keywords.length > 0 && (
        <div className="flex flex-wrap gap-1.5 mt-1">
          {keywords.map((kw, i) => (
            <span key={i} className="rounded-full border border-white/10 bg-black/40 px-2.5 py-0.5 text-[10px] font-medium text-muted-foreground">
              {kw}
            </span>
          ))}
        </div>
      )}

      <div className="mt-2 flex items-center gap-2 rounded-lg bg-emerald-500/10 border border-emerald-500/20 px-3 py-2 text-[11px] font-medium text-emerald-400">
        <BookOpen className="h-3.5 w-3.5" />
        Publication-quality PDF generated — download from the Paper Generator panel.
      </div>
    </div>
  );
}

export const MessageBubble = ({ message }: { message: ChatMessage }) => {
  const isUser = message.role === "user";

  // For assistant messages, check if raw JSON crept in
  const paperJson = !isUser && message.content ? tryParseResearchPaper(message.content) : null;

  return (
    <div className={cn("flex w-full animate-fade-in gap-4", isUser ? "justify-end" : "justify-start")}>
      {!isUser && (
        <div className="mt-1 flex h-9 w-9 shrink-0 items-center justify-center rounded-xl bg-gradient-to-br from-primary to-accent text-white shadow-[0_0_15px_rgba(100,70,255,0.3)] backdrop-blur-sm">
          <Bot className="h-5 w-5" strokeWidth={2.5} />
        </div>
      )}
      <div
        className={cn(
          "max-w-[85%] px-5 py-3 text-[15px] leading-relaxed",
          isUser
            ? "rounded-2xl rounded-tr-md bg-gradient-to-br from-[#1a1a24] to-[#121218] border border-white/5 text-foreground shadow-lg backdrop-blur-md"
            : "text-foreground"
        )}
      >
        {isUser ? (
          <p className="whitespace-pre-wrap">{message.content}</p>
        ) : (
          <div className="space-y-2">
            {message.steps && message.steps.length > 0 && (
              <AgentSteps steps={message.steps} />
            )}
            {paperJson ? (
              <ResearchPaperCard data={paperJson} />
            ) : containsMermaid(message.content) ? (
              <MermaidRenderer content={message.content} />
            ) : (
              <div className="prose prose-invert prose-p:leading-relaxed max-w-none prose-headings:text-foreground prose-headings:font-bold prose-p:text-muted-foreground prose-a:text-primary prose-a:font-medium prose-strong:text-foreground prose-strong:font-bold prose-code:text-primary prose-code:bg-primary/10 prose-code:px-1.5 prose-code:py-0.5 prose-code:rounded-md prose-code:text-[13px] prose-code:font-semibold prose-pre:bg-black/60 prose-pre:border prose-pre:border-white/10 prose-pre:shadow-inner prose-li:text-muted-foreground">
                <ReactMarkdown remarkPlugins={[remarkGfm]}>
                  {message.content}
                </ReactMarkdown>
              </div>
            )}
            {message.driveLink && <DriveLink link={message.driveLink} />}
          </div>
        )}
      </div>
      {isUser && (
        <div className="mt-1 flex h-9 w-9 shrink-0 items-center justify-center rounded-xl bg-white/10 border border-white/5 text-foreground backdrop-blur-sm shadow-soft">
          <User className="h-5 w-5" strokeWidth={2.5} />
        </div>
      )}
    </div>
  );
};

export const TypingIndicator = ({ stage }: { stage?: string }) => {
  return (
    <div className="flex w-full animate-fade-in gap-4">
      <div className="mt-1 flex h-9 w-9 shrink-0 items-center justify-center rounded-xl bg-gradient-to-br from-primary to-accent text-white shadow-[0_0_15px_rgba(100,70,255,0.4)] backdrop-blur-sm">
        <Sparkles className="h-5 w-5 animate-pulse" strokeWidth={2.5} />
      </div>
      <div className="flex flex-col justify-center gap-1.5 px-2">
        {stage && (
          <span className="text-[12px] font-bold text-primary animate-pulse">{stage}</span>
        )}
        <div className="flex items-center gap-2">
          <span className="h-2 w-2 animate-typing rounded-full bg-primary/60" />
          <span className="h-2 w-2 animate-typing rounded-full bg-primary/60" style={{ animationDelay: "0.15s" }} />
          <span className="h-2 w-2 animate-typing rounded-full bg-primary/60" style={{ animationDelay: "0.3s" }} />
        </div>
      </div>
    </div>
  );
};
