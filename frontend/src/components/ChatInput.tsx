import { ArrowUp, Paperclip } from "lucide-react";
import { cn } from "@/lib/utils";
import { useEffect, useRef } from "react";

interface ChatInputProps {
  value: string;
  onChange: (v: string) => void;
  onSend: () => void;
  disabled?: boolean;
}

export const ChatInput = ({ value, onChange, onSend, disabled }: ChatInputProps) => {
  const ref = useRef<HTMLTextAreaElement>(null);

  useEffect(() => {
    const el = ref.current;
    if (!el) return;
    el.style.height = "auto";
    el.style.height = Math.min(el.scrollHeight, 200) + "px";
  }, [value]);

  return (
    <div className="glass-strong rounded-2xl transition-colors focus-within:border-primary/40">
      <textarea
        ref={ref}
        rows={1}
        value={value}
        onChange={(e) => onChange(e.target.value)}
        onKeyDown={(e) => {
          if (e.key === "Enter" && !e.shiftKey) {
            e.preventDefault();
            if (value.trim() && !disabled) onSend();
          }
        }}
        placeholder="Ask anything about research…"
        className="block w-full resize-none rounded-2xl bg-transparent px-4 pt-3.5 pb-12 text-[14px] text-foreground placeholder:text-muted-foreground focus:outline-none"
      />
      <div className="flex items-center justify-between gap-2 px-2.5 pb-2.5">
        <div className="flex items-center gap-1">
          <button
            type="button"
            className="ring-focus rounded-lg p-1.5 text-muted-foreground transition-colors hover:bg-foreground/[0.06] hover:text-foreground"
            aria-label="Attach file"
          >
            <Paperclip className="h-4 w-4" />
          </button>
          <span className="ml-1 hidden text-[11px] text-muted-foreground sm:inline">
            <kbd className="rounded-md bg-foreground/[0.06] px-1.5 py-0.5 text-[10px] font-medium">
              ↵
            </kbd>{" "}
            to send
          </span>
        </div>
        <button
          onClick={() => value.trim() && !disabled && onSend()}
          disabled={!value.trim() || disabled}
          className={cn(
            "ring-focus flex h-8 w-8 items-center justify-center rounded-lg transition-colors",
            value.trim() && !disabled
              ? "bg-primary text-primary-foreground hover:bg-primary/90"
              : "bg-foreground/[0.06] text-muted-foreground"
          )}
          aria-label="Send message"
        >
          <ArrowUp className="h-4 w-4" strokeWidth={2.4} />
        </button>
      </div>
    </div>
  );
};
