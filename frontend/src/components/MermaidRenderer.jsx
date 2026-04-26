import { useEffect, useMemo, useRef, useState } from "react";
import mermaid from "mermaid";

mermaid.initialize({ startOnLoad: true });

const mermaidBlock = /```mermaid\s*([\s\S]*?)```/i;

export const MermaidRenderer = ({ content }) => {
  const idRef = useRef(`mermaid-${Math.random().toString(36).slice(2)}`);
  const [svg, setSvg] = useState("");
  const [error, setError] = useState("");

  const parsed = useMemo(() => {
    const match = content.match(mermaidBlock);

    if (!match) {
      return {
        text: content,
        diagram: "",
      };
    }

    return {
      text: content.replace(mermaidBlock, "").trim(),
      diagram: match[1].trim(),
    };
  }, [content]);

  useEffect(() => {
    let cancelled = false;

    async function renderDiagram() {
      if (!parsed.diagram) {
        setSvg("");
        setError("");
        return;
      }

      try {
        const result = await mermaid.render(idRef.current, parsed.diagram);
        if (!cancelled) {
          setSvg(result.svg);
          setError("");
        }
      } catch (renderError) {
        console.error("Mermaid render failed:", renderError);
        if (!cancelled) {
          setSvg("");
          setError("Unable to render diagram.");
        }
      }
    }

    renderDiagram();

    return () => {
      cancelled = true;
    };
  }, [parsed.diagram]);

  return (
    <div className="space-y-3">
      {parsed.text && <p className="whitespace-pre-wrap">{parsed.text}</p>}

      {parsed.diagram && (
        <div className="overflow-x-auto rounded-xl border border-border/40 bg-background/40 p-3">
          {svg ? (
            <div dangerouslySetInnerHTML={{ __html: svg }} />
          ) : (
            <pre className="whitespace-pre-wrap text-[12px] text-muted-foreground">
              {error || parsed.diagram}
            </pre>
          )}
        </div>
      )}
    </div>
  );
};
