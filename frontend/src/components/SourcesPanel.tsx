import { ExternalLink } from "lucide-react";
import type { AgentSource } from "@/lib/api";

export const SourcesPanel = ({ sources = [] }: { sources?: AgentSource[] }) => {
  return (
    <div className="space-y-2">
      <div className="flex items-center justify-between px-1 pb-1">
        <h3 className="text-[11px] font-medium uppercase tracking-[0.12em] text-muted-foreground">
          Sources
        </h3>
        <span className="text-[11px] text-muted-foreground">{sources.length}</span>
      </div>
      {sources.length === 0 ? (
        <div className="rounded-md px-2 py-3 text-[12px] text-muted-foreground">
          No sources collected yet.
        </div>
      ) : (
        <ul className="space-y-2">
          {sources.map((source) => (
            <li key={source.ref_id}>
              <a
                href={source.url || "#"}
                target={source.url ? "_blank" : undefined}
                rel={source.url ? "noreferrer" : undefined}
                className="group flex flex-col gap-2 rounded-lg border border-white/5 bg-foreground/[0.02] px-3 py-3 shadow-sm backdrop-blur-md transition-all hover:border-primary/30 hover:bg-foreground/[0.05]"
              >
                <div className="flex items-start justify-between gap-2">
                  <span className="flex h-5 w-5 shrink-0 items-center justify-center rounded bg-primary/20 text-[10px] font-bold text-primary">
                    {source.ref_id}
                  </span>
                  <p className="line-clamp-2 min-w-0 flex-1 text-[13px] font-semibold leading-snug text-foreground transition-colors group-hover:text-primary">
                    {source.title}
                  </p>
                  <ExternalLink className="mt-0.5 h-3.5 w-3.5 shrink-0 text-muted-foreground/40 opacity-0 transition-all group-hover:opacity-100 group-hover:text-primary" />
                </div>
                <p className="line-clamp-2 text-[11px] leading-relaxed text-muted-foreground/80 pl-7">
                  {source.snippet || source.url}
                </p>
              </a>
            </li>
          ))}
        </ul>
      )}
    </div>
  );
};
