import { ArrowUp, Paperclip, X, FileText, Image as ImageIcon } from "lucide-react";
import { cn } from "@/lib/utils";
import { useEffect, useRef, useState } from "react";

interface ChatInputProps {
  value: string;
  onChange: (v: string) => void;
  onSend: () => void;
  onFileSelect: (file: File) => void;
  selectedFile?: File | null;
  onClearFile: () => void;
  disabled?: boolean;
}

export const ChatInput = ({
  value,
  onChange,
  onSend,
  onFileSelect,
  selectedFile,
  onClearFile,
  disabled,
}: ChatInputProps) => {
  const ref = useRef<HTMLTextAreaElement>(null);
  const fileRef = useRef<HTMLInputElement>(null);

  useEffect(() => {
    const el = ref.current;
    if (!el) return;
    el.style.height = "auto";
    el.style.height = Math.min(el.scrollHeight, 200) + "px";
  }, [value]);

  const isPdf = selectedFile?.name.toLowerCase().endsWith(".pdf");
  const FileIcon = isPdf ? FileText : ImageIcon;

  return (
    <div className="glass-strong relative overflow-hidden rounded-[1.5rem] transition-all focus-within:border-primary/50 focus-within:shadow-[0_0_30px_rgba(100,70,255,0.15)] group">
      {/* Subtle top inner glow */}
      <div className="absolute top-0 left-0 right-0 h-[1px] bg-gradient-to-r from-transparent via-white/10 to-transparent" />
      
      {selectedFile && (
        <div className="flex items-center gap-2 px-5 pt-4 animate-fade-in">
          <div className="flex items-center gap-2 rounded-xl border border-primary/30 bg-primary/10 px-3 py-2 text-[12px] font-semibold text-primary shadow-[0_0_15px_rgba(100,70,255,0.1)]">
            <FileIcon className="h-4 w-4" />
            <span className="max-w-[200px] truncate">{selectedFile.name}</span>
            <button
              type="button"
              onClick={onClearFile}
              className="ml-2 rounded-full bg-primary/20 p-1 text-primary transition-colors hover:bg-primary/40"
              aria-label="Remove file"
            >
              <X className="h-3 w-3" />
            </button>
          </div>
        </div>
      )}
      
      <textarea
        ref={ref}
        rows={1}
        value={value}
        onChange={(e) => onChange(e.target.value)}
        onKeyDown={(e) => {
          if (e.key === "Enter" && !e.shiftKey) {
            e.preventDefault();
            if ((value.trim() || selectedFile) && !disabled) onSend();
          }
        }}
        placeholder={selectedFile ? "Describe what to do with this file…" : "Ask the agent anything about your research..."}
        className="block w-full resize-none bg-transparent px-5 pt-4 pb-14 text-[15px] leading-relaxed text-foreground placeholder:text-muted-foreground focus:outline-none"
      />
      
      <div className="absolute bottom-3 left-3 right-3 flex items-center justify-between">
        <div className="flex items-center gap-2">
          <input
            ref={fileRef}
            type="file"
            accept=".pdf,.png,.jpg,.jpeg,.bmp,.tiff,.webp,application/pdf,image/*"
            className="hidden"
            onChange={(e) => {
              const file = e.target.files?.[0];
              if (file) onFileSelect(file);
              e.target.value = "";
            }}
          />
          <button
            type="button"
            onClick={() => fileRef.current?.click()}
            className={cn(
              "ring-focus flex h-10 w-10 items-center justify-center rounded-xl transition-all",
              selectedFile
                ? "bg-primary/20 text-primary"
                : "bg-white/5 text-muted-foreground hover:bg-white/10 hover:text-foreground"
            )}
            aria-label="Attach file"
          >
            <Paperclip className="h-5 w-5" />
          </button>
          <span className="hidden text-[11px] font-medium uppercase tracking-widest text-muted-foreground/60 sm:inline ml-2">
            AI Agent Ready
          </span>
        </div>
        
        <button
          onClick={() => (value.trim() || selectedFile) && !disabled && onSend()}
          disabled={(!value.trim() && !selectedFile) || disabled}
          className={cn(
            "ring-focus flex h-10 w-10 items-center justify-center rounded-xl transition-all duration-300",
            (value.trim() || selectedFile) && !disabled
              ? "bg-gradient-to-tr from-primary to-accent text-white shadow-[0_0_20px_rgba(100,70,255,0.4)] hover:scale-105 active:scale-95"
              : "bg-white/5 text-muted-foreground/50"
          )}
          aria-label="Send message"
        >
          <ArrowUp className="h-5 w-5" strokeWidth={2.5} />
        </button>
      </div>
    </div>
  );
};
