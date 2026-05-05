import { useState } from "react";
import { ChevronDown, FileText, Loader2, CheckCircle2 } from "lucide-react";
import { cn } from "@/lib/utils";
import { generatePaper } from "@/lib/api";

export const PaperGenerator = () => {
  const [open, setOpen] = useState(true);
  const [topic, setTopic] = useState("");
  const [state, setState] = useState<"idle" | "loading" | "done">("idle");
  const [paper, setPaper] = useState<string>("");
  const [driveLink, setDriveLink] = useState<string | null>(null);

  const handleGenerate = async () => {
    if (!topic.trim()) {
      alert("Please enter a research topic.");
      return;
    }

    if (state === "loading") return;

    setState("loading");
    setPaper("");
    setDriveLink(null);

    try {
      const data = await generatePaper(topic.trim(), true);
      setPaper(data.output);
      setDriveLink(data.drive_link);
      setState("done");
    } catch (error) {
      console.error("Paper generation failed:", error);
      setState("idle");
      alert(error instanceof Error ? error.message : "Paper generation failed.");
    }
  };

  return (
    <div className="glass overflow-hidden rounded-2xl">
      <button
        onClick={() => setOpen((v) => !v)}
        className="flex w-full items-center justify-between gap-3 px-4 py-3.5 text-left transition-colors hover:bg-foreground/[0.03]"
      >
        <div className="flex items-center gap-2.5">
          <div className="flex h-7 w-7 items-center justify-center rounded-lg bg-primary/15 text-primary">
            <FileText className="h-3.5 w-3.5" strokeWidth={2.2} />
          </div>
          <div>
            <p className="text-[13px] font-semibold text-foreground">Paper Generator</p>
            <p className="text-[11px] text-muted-foreground">Draft a structured paper</p>
          </div>
        </div>
        <ChevronDown
          className={cn("h-4 w-4 text-muted-foreground transition-transform duration-200", open && "rotate-180")}
        />
      </button>

      <div
        className={cn(
          "grid transition-[grid-template-rows] duration-300 ease-out",
          open ? "grid-rows-[1fr]" : "grid-rows-[0fr]"
        )}
      >
        <div className="overflow-hidden">
          <div className="space-y-3 px-4 pb-4">
            <input
              value={topic}
              onChange={(e) => {
                setTopic(e.target.value);
                if (state === "done") setState("idle");
              }}
              onKeyDown={(e) => e.key === "Enter" && handleGenerate()}
              placeholder="Enter research topic…"
              className="ring-focus w-full rounded-xl border border-border/40 bg-background/40 px-3.5 py-2 text-[13px] text-foreground placeholder:text-muted-foreground transition-colors focus-within:border-primary/40"
            />
            <button
              onClick={handleGenerate}
              disabled={!topic.trim() || state === "loading"}
              className={cn(
                "ring-focus flex w-full items-center justify-center gap-2 rounded-xl px-3 py-2 text-[13px] font-medium transition-colors",
                topic.trim() && state !== "loading"
                  ? "bg-primary text-primary-foreground hover:bg-primary/90"
                  : "bg-secondary/60 text-muted-foreground"
              )}
            >
              {state === "loading" ? (
                <>
                  <Loader2 className="h-3.5 w-3.5 animate-spin" />
                  Generating…
                </>
              ) : (
                "Generate paper"
              )}
            </button>

            {state === "done" && (
              <>
                <div className="flex animate-fade-in items-start gap-2 rounded-xl bg-primary/10 px-3 py-2.5 text-[12.5px]">
                  <CheckCircle2 className="mt-0.5 h-3.5 w-3.5 shrink-0 text-primary" />
                  <span className="text-foreground">
                    Draft on <span className="font-medium">"{topic}"</span> is ready.
                  </span>
                </div>

                <button
                  type="button"
                  className="ring-focus flex w-full items-center justify-center gap-2 rounded-xl bg-secondary/70 px-3 py-2 text-[13px] font-medium text-foreground transition-colors"
                >
                  {driveLink ? "Drive upload complete" : "Generated in backend"}
                </button>
                {driveLink && (
                  <a
                    href={driveLink}
                    target="_blank"
                    rel="noreferrer"
                    className="block text-center text-[12px] text-primary hover:underline"
                  >
                    Open in Google Drive
                  </a>
                )}
                {paper && (
                  <div className="rounded-xl bg-foreground/[0.04] px-3 py-2 text-[12px] text-muted-foreground">
                    {paper.slice(0, 220)}
                    {paper.length > 220 ? "..." : ""}
                  </div>
                )}
              </>
            )}
          </div>
        </div>
      </div>
    </div>
  );
};
