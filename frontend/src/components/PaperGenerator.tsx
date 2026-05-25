import { useState } from "react";
import { ChevronDown, FileText, Loader2, CheckCircle2, ExternalLink, Download, Database, Network, Sigma, Sparkles } from "lucide-react";
import { cn } from "@/lib/utils";
import { generate, AgentResponse, API_BASE_URL } from "@/lib/api";

export const PaperGenerator = () => {
  const [open, setOpen] = useState(true);
  const [topic, setTopic] = useState("");
  const [state, setState] = useState<"idle" | "loading" | "done">("idle");
  const [paper, setPaper] = useState<string>("");
  const [driveLink, setDriveLink] = useState<string | null>(null);
  const [formatType, setFormatType] = useState<"ieee" | "apa" | "acm">("ieee");
  const [pageLength, setPageLength] = useState<"4-5" | "6-8">("6-8");
  const [includeDiagrams, setIncludeDiagrams] = useState(true);
  const [includeFormulas, setIncludeFormulas] = useState(false);
  const [pdfPath, setPdfPath] = useState<string | null>(null);
  const [paperData, setPaperData] = useState<AgentResponse | null>(null);

  const handleGenerate = async () => {
    if (!topic.trim() || state === "loading") return;

    setState("loading");
    setPaper("");
    setDriveLink(null);

    try {
      const data = await generate(
        topic.trim(),
        "research_paper",
        false,
        "mcp",
        formatType,
        pageLength,
        includeFormulas,
        includeDiagrams
      );
      setPaper(data.output || "");
      setDriveLink(data.drive_link);
      setPdfPath(data.pdf_path || null);
      setPaperData(data);
      setState("done");
    } catch (error) {
      console.error("Paper generation failed:", error);
      setState("idle");
      alert(error instanceof Error ? error.message : "Paper generation failed.");
    }
  };

  return (
    <div className="glass-strong overflow-hidden rounded-[1.5rem] border border-white/5">
      <button
        onClick={() => setOpen((v) => !v)}
        className="flex w-full items-center justify-between gap-3 px-5 py-4 text-left transition-colors hover:bg-white/5"
      >
        <div className="flex items-center gap-3">
          <div className="flex h-9 w-9 items-center justify-center rounded-xl bg-gradient-to-br from-primary/20 to-accent/20 text-primary shadow-[0_0_15px_rgba(100,70,255,0.15)]">
            <FileText className="h-4 w-4" strokeWidth={2.5} />
          </div>
          <div>
            <p className="text-[14px] font-bold tracking-wide text-foreground">Paper Generator</p>
            <p className="text-[12px] font-medium text-muted-foreground">Draft structured papers</p>
          </div>
        </div>
        <ChevronDown
          className={cn("h-5 w-5 text-muted-foreground transition-transform duration-300", open && "rotate-180")}
        />
      </button>

      <div
        className={cn(
          "grid transition-[grid-template-rows] duration-300 ease-out",
          open ? "grid-rows-[1fr]" : "grid-rows-[0fr]"
        )}
      >
        <div className="overflow-hidden">
          <div className="space-y-4 px-5 pb-5">
            <input
              value={topic}
              onChange={(e) => {
                setTopic(e.target.value);
                if (state === "done") setState("idle");
              }}
              onKeyDown={(e) => e.key === "Enter" && handleGenerate()}
              placeholder="Enter research topic…"
              className="ring-focus w-full rounded-xl border border-white/10 bg-black/40 px-4 py-3 text-[14px] text-foreground shadow-inner placeholder:text-muted-foreground transition-colors focus-within:border-primary/50"
            />
            <div className="flex gap-2">
              <select
                value={formatType}
                onChange={(e) => setFormatType(e.target.value as "ieee" | "apa" | "acm")}
                className="rounded-xl border border-white/10 bg-black/40 px-3 py-2.5 text-[13px] font-medium text-foreground focus:border-primary/50 focus:outline-none"
              >
                <option value="ieee">IEEE Format</option>
                <option value="apa">APA Format</option>
                <option value="acm">ACM Format</option>
              </select>
              <select
                value={pageLength}
                onChange={(e) => setPageLength(e.target.value as "4-5" | "6-8")}
                className="rounded-xl border border-white/10 bg-black/40 px-3 py-2.5 text-[13px] font-medium text-foreground focus:border-primary/50 focus:outline-none"
              >
                <option value="4-5">4-5 Pages</option>
                <option value="6-8">6-8 Pages</option>
              </select>
            </div>

            <button
              onClick={handleGenerate}
              disabled={!topic.trim() || state === "loading"}
              className={cn(
                "ring-focus flex w-full items-center justify-center gap-2 rounded-xl px-4 py-3 text-[14px] font-bold transition-all duration-300",
                topic.trim() && state !== "loading"
                  ? "bg-gradient-to-r from-primary to-accent text-white shadow-[0_0_20px_rgba(100,70,255,0.3)] hover:scale-[1.02] active:scale-[0.98]"
                  : "bg-white/5 text-muted-foreground/50 cursor-not-allowed"
              )}
            >
              {state === "loading" ? (
                <>
                  <Loader2 className="h-5 w-5 animate-spin" />
                  Orchestrating...
                </>
              ) : (
                <>
                  <Sparkles className="h-4 w-4" />
                  Generate Paper
                </>
              )}
            </button>

            {state === "done" && (
              <div className="mt-4 space-y-4 animate-fade-in border-t border-white/5 pt-4">
                <div className="flex items-start gap-3 rounded-xl bg-emerald-500/10 border border-emerald-500/20 px-4 py-3 text-[13px] shadow-[0_0_15px_rgba(16,185,129,0.05)]">
                  <CheckCircle2 className="mt-0.5 h-4 w-4 shrink-0 text-emerald-400" />
                  <span className="text-foreground/90 leading-snug">
                    Generation complete for <span className="font-bold text-emerald-400">"{topic}"</span>
                  </span>
                </div>
                
                <div className="flex gap-2">
                  {driveLink && (
                    <a
                      href={driveLink}
                      target="_blank"
                      rel="noreferrer"
                      className="flex flex-1 items-center justify-center gap-2 rounded-xl bg-blue-500/10 border border-blue-500/20 px-3 py-2.5 text-[12px] font-bold text-blue-400 transition-colors hover:bg-blue-500/20 hover:text-blue-300"
                    >
                      <ExternalLink className="h-4 w-4" />
                      Drive
                    </a>
                  )}
                  {pdfPath ? (
                    <a
                      href={`${API_BASE_URL}/outputs/${pdfPath.split('/').pop()}`}
                      target="_blank"
                      rel="noreferrer"
                      className="flex flex-1 items-center justify-center gap-2 rounded-xl bg-primary/10 border border-primary/20 px-3 py-2.5 text-[12px] font-bold text-primary transition-colors hover:bg-primary/20 hover:text-primary-foreground"
                      download
                    >
                      <Download className="h-4 w-4" />
                      PDF
                    </a>
                  ) : paper ? (
                    <button
                      onClick={() => {
                        const blob = new Blob([paper], { type: "text/markdown" });
                        const url = URL.createObjectURL(blob);
                        const a = document.createElement("a");
                        a.href = url;
                        a.download = `${topic.replace(/[^a-z0-9]/gi, "_").toLowerCase()}_paper.md`;
                        a.click();
                        URL.revokeObjectURL(url);
                      }}
                      className="flex flex-1 items-center justify-center gap-2 rounded-xl bg-primary/10 border border-primary/20 px-3 py-2.5 text-[12px] font-bold text-primary transition-colors hover:bg-primary/20 hover:text-primary-foreground"
                    >
                      <Download className="h-4 w-4" />
                      MD
                    </button>
                  ) : null}
                </div>

                {paperData && paperData.abstract ? (
                  <div className="rounded-xl border border-white/5 bg-black/40 px-4 py-3 text-[12px] leading-relaxed text-muted-foreground">
                    <span className="font-bold text-foreground">Abstract:</span> {paperData.abstract.slice(0, 150)}...
                    {paperData.citations && paperData.citations.length > 0 && (
                      <div className="mt-3 flex items-center gap-2 font-semibold text-primary">
                        <Database className="h-3.5 w-3.5" />
                        Citations integrated: {paperData.citations.length}
                      </div>
                    )}
                  </div>
                ) : paper ? (
                  <div className="rounded-xl border border-white/5 bg-black/40 px-4 py-3 text-[12px] leading-relaxed text-muted-foreground">
                    {paper.slice(0, 220)}
                    {paper.length > 220 ? "…" : ""}
                  </div>
                ) : null}
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
};
