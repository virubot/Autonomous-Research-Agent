import { ExternalLink } from "lucide-react";

export type Source = {
  id: string;
  title: string;
  year: number;
  authors: string;
};

const defaultSources: Source[] = [
  { id: "1", title: "Attention Is All You Need", year: 2017, authors: "Vaswani et al." },
  { id: "2", title: "Language Models are Few-Shot Learners", year: 2020, authors: "Brown et al." },
  { id: "3", title: "Retrieval-Augmented Generation for Knowledge Tasks", year: 2021, authors: "Lewis et al." },
  { id: "4", title: "Chain-of-Thought Prompting Elicits Reasoning", year: 2022, authors: "Wei et al." },
];

export const SourcesPanel = ({ sources = defaultSources }: { sources?: Source[] }) => {
  return (
    <div className="space-y-2">
      <div className="flex items-center justify-between px-1 pb-1">
        <h3 className="text-[11px] font-medium uppercase tracking-[0.12em] text-muted-foreground">
          Sources
        </h3>
        <span className="text-[11px] text-muted-foreground">{sources.length}</span>
      </div>
      <ul className="divide-y divide-border/30">
        {sources.map((s) => (
          <li key={s.id}>
            <a
              href="#"
              className="group flex items-start justify-between gap-3 rounded-md px-2 py-3 transition-colors hover:bg-foreground/[0.04]"
            >
              <div className="min-w-0 flex-1">
                <p className="line-clamp-2 text-[13px] font-medium leading-snug text-foreground transition-colors group-hover:text-primary">
                  {s.title}
                </p>
                <p className="mt-1 text-[11px] text-muted-foreground">
                  {s.authors} · {s.year}
                </p>
              </div>
              <ExternalLink className="mt-0.5 h-3.5 w-3.5 shrink-0 text-muted-foreground/60 opacity-0 transition-all group-hover:opacity-100 group-hover:text-primary" />
            </a>
          </li>
        ))}
      </ul>
    </div>
  );
};
