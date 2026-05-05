import { cn } from "@/lib/utils";
import { Sparkles, User } from "lucide-react";
import { MermaidRenderer } from "@/components/MermaidRenderer";
import type { AgentSource } from "@/lib/api";

export type ChatMessage = {
  id: string;
  role: "user" | "assistant";
  content: string;
  sources?: AgentSource[];
  steps?: string[];
  driveLink?: string | null;
};

export const MessageBubble = ({ message }: { message: ChatMessage }) => {
  const isUser = message.role === "user";
  return (
    <div className={cn("flex w-full animate-fade-in gap-3", isUser ? "justify-end" : "justify-start")}>
      {!isUser && (
        <div className="mt-1 flex h-8 w-8 shrink-0 items-center justify-center rounded-full bg-primary/15 text-primary backdrop-blur-sm">
          <Sparkles className="h-3.5 w-3.5" strokeWidth={2.2} />
        </div>
      )}
      <div
        className={cn(
          "max-w-[78%] px-4 py-2.5 text-[14px] leading-relaxed",
          isUser
            ? "rounded-2xl rounded-tr-md bg-[hsl(var(--bubble-user))]/85 text-[hsl(var(--bubble-user-fg))] shadow-soft backdrop-blur-sm"
            : "text-[hsl(var(--bubble-ai-fg))]"
        )}
      >
        {isUser ? <p className="whitespace-pre-wrap">{message.content}</p> : <MermaidRenderer content={message.content} />}
      </div>
      {isUser && (
        <div className="mt-1 flex h-8 w-8 shrink-0 items-center justify-center rounded-full bg-secondary/70 text-muted-foreground backdrop-blur-sm">
          <User className="h-3.5 w-3.5" strokeWidth={2.2} />
        </div>
      )}
    </div>
  );
};

export const TypingIndicator = () => {
  return (
    <div className="flex w-full animate-fade-in gap-3">
      <div className="mt-1 flex h-8 w-8 shrink-0 items-center justify-center rounded-full bg-primary/15 text-primary backdrop-blur-sm">
        <Sparkles className="h-3.5 w-3.5" strokeWidth={2.2} />
      </div>
      <div className="flex items-center gap-1.5 px-2 py-3">
        <span className="h-1.5 w-1.5 animate-typing rounded-full bg-muted-foreground" />
        <span className="h-1.5 w-1.5 animate-typing rounded-full bg-muted-foreground" style={{ animationDelay: "0.15s" }} />
        <span className="h-1.5 w-1.5 animate-typing rounded-full bg-muted-foreground" style={{ animationDelay: "0.3s" }} />
      </div>
    </div>
  );
};
