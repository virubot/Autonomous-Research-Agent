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
        <ul className="divide-y divide-border/30">
          {sources.map((source) => (
            <li key={source.ref_id}>
              <a
                href={source.url || "#"}
                target={source.url ? "_blank" : undefined}
                rel={source.url ? "noreferrer" : undefined}
                className="group flex items-start justify-between gap-3 rounded-md px-2 py-3 transition-colors hover:bg-foreground/[0.04]"
              >
                <div className="min-w-0 flex-1">
                  <p className="line-clamp-2 text-[13px] font-medium leading-snug text-foreground transition-colors group-hover:text-primary">
                    [{source.ref_id}] {source.title}
                  </p>
                  <p className="mt-1 line-clamp-3 text-[11px] text-muted-foreground">
                    {source.snippet || source.url}
                  </p>
                </div>
                <ExternalLink className="mt-0.5 h-3.5 w-3.5 shrink-0 text-muted-foreground/60 opacity-0 transition-all group-hover:opacity-100 group-hover:text-primary" />
              </a>
            </li>
          ))}
        </ul>
      )}
    </div>
  );
};
