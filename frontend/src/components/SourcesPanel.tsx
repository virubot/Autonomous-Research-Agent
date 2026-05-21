import { ExternalLink, Link2, Search } from "lucide-react";
import type { AgentSource } from "@/lib/api";

function domainFromUrl(url: string) {
  try {
    return new URL(url).hostname.replace(/^www\./, "");
  } catch {
    return "";
  }
}

export const SourcesPanel = ({ sources = [] }: { sources?: AgentSource[] }) => {
  return (
    <div className="glass-strong rounded-[1.5rem] border border-white/5 p-4 space-y-3">
      <div className="flex items-center justify-between px-2 pb-2 border-b border-white/5">
        <div className="flex items-center gap-2">
          <div className="flex h-6 w-6 items-center justify-center rounded-md bg-primary/20 text-primary shadow-soft">
            <Search className="h-3.5 w-3.5" strokeWidth={2.5} />
          </div>
          <h3 className="text-[11px] font-bold uppercase tracking-[0.15em] text-muted-foreground">
            Knowledge Base
          </h3>
        </div>
        <span className="flex h-5 items-center justify-center rounded-full bg-white/5 px-2 text-[10px] font-bold text-foreground">
          {sources.length}
        </span>
      </div>
      {sources.length === 0 ? (
        <div className="rounded-xl border border-white/5 bg-black/20 px-4 py-6 text-center text-[12px] font-medium text-muted-foreground/60">
          No grounded sources collected yet.
        </div>
      ) : (
        <ul className="space-y-2">
          {sources.map((source) => (
            <li key={source.ref_id}>
              <a
                href={source.url || "#"}
                target={source.url ? "_blank" : undefined}
                rel={source.url ? "noreferrer" : undefined}
                className="group flex items-start justify-between gap-3 rounded-xl border border-transparent bg-white/[0.02] px-4 py-3 transition-all hover:border-primary/30 hover:bg-primary/5"
              >
                <div className="min-w-0 flex-1">
                  <div className="flex items-start gap-2">
                    <span className="flex h-4 w-4 shrink-0 items-center justify-center rounded bg-primary/20 text-[9px] font-bold text-primary mt-0.5">
                      {source.ref_id}
                    </span>
                    <p className="line-clamp-2 text-[13px] font-semibold leading-snug text-foreground transition-colors group-hover:text-primary-foreground">
                      {source.title}
                    </p>
                  </div>
                  {source.url && (
                    <div className="mt-2 flex items-center gap-1 text-[10px] font-bold uppercase tracking-widest text-muted-foreground/60">
                      <Link2 className="h-3 w-3" />
                      {domainFromUrl(source.url)}
                    </div>
                  )}
                  <p className="mt-2 line-clamp-3 text-[11px] leading-relaxed text-muted-foreground/80">
                    {source.snippet || source.url}
                  </p>
                </div>
                <ExternalLink className="mt-1 h-3.5 w-3.5 shrink-0 text-muted-foreground/40 opacity-0 transition-all group-hover:opacity-100 group-hover:text-primary" />
              </a>
            </li>
          ))}
        </ul>
      )}
    </div>
  );
};
