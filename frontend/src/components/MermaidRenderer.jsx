import { useEffect, useMemo, useRef, useState } from "react";
import mermaid from "mermaid";

mermaid.initialize({
  startOnLoad: true,
  theme: 'dark',
  themeVariables: {
    primaryColor: '#1e1e2d',
    primaryTextColor: '#e2e8f0',
    primaryBorderColor: '#6366f1',
    lineColor: '#818cf8',
    secondaryColor: '#312e81',
    tertiaryColor: '#1e1b4b',
    fontFamily: 'Inter, sans-serif'
  }
});

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
    <div className="space-y-4">
      {parsed.text && <p className="whitespace-pre-wrap">{parsed.text}</p>}

      {parsed.diagram && (
        <div className="overflow-x-auto rounded-2xl border border-white/5 bg-black/40 p-4 shadow-inner">
          {svg ? (
            <div dangerouslySetInnerHTML={{ __html: svg }} className="flex justify-center" />
          ) : (
            <pre className="whitespace-pre-wrap text-[13px] text-muted-foreground/60 p-2">
              {error || parsed.diagram}
            </pre>
          )}
        </div>
      )}
    </div>
  );
};
