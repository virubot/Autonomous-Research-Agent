import { motion } from "framer-motion";
import { ArrowRight, Bot, Database, FileSearch, GitBranch, HardDriveUpload, Network, ShieldCheck, Sparkles, Wrench } from "lucide-react";
import { MermaidRenderer } from "@/components/MermaidRenderer";

type AgentOverviewShowcaseProps = {
  onPromptSelect: (prompt: string) => void;
};

const heroPrompts = [
  "Design a Google Cloud agent workflow for biomedical literature triage with citation-backed summaries.",
  "Generate a technical implementation plan for an autonomous research agent with MCP tools and Vertex AI orchestration.",
  "Analyze a PDF and produce a structured architecture review with tool trace, evaluation criteria, and export steps.",
];

const capabilityCards = [
  {
    label: "Autonomous Loop",
    value: "Goal → Plan → Tool → Memory → Export",
    icon: Bot,
    color: "text-blue-400",
    bg: "bg-blue-400/10",
  },
  {
    label: "Reasoning Stack",
    value: "Gemini on Vertex AI with JSON enforcement",
    icon: GitBranch,
    color: "text-purple-400",
    bg: "bg-purple-400/10",
  },
  {
    label: "Tool Surface",
    value: "Search, Extraction, MCP, Drive export",
    icon: Wrench,
    color: "text-emerald-400",
    bg: "bg-emerald-400/10",
  },
  {
    label: "Artifacts",
    value: "PDF paper, citations, memory trace",
    icon: HardDriveUpload,
    color: "text-amber-400",
    bg: "bg-amber-400/10",
  },
];

const architectureLayers = [
  "User Input Layer: Topic prompt, file context, constraints.",
  "Frontend Layer: React dashboard, real-time agent telemetry.",
  "Backend API Layer: FastAPI, SSE streaming, orchestration.",
  "Reasoning Engine: Vertex AI Gemini reasoning and planning.",
  "Tool Calling Layer: Web search, OCR, external tool routing.",
  "MCP Integration: Model Context Protocol dispatch layer.",
  "Database/Memory: SQLite run continuity and events.",
  "Export Layer: LaTeX compilation and Drive publishing.",
];

const evaluationRows = [
  ["Source-grounded completion", "Evidence-backed response with citations", "0.88 target"],
  ["Multi-step execution", "Planner issues actionable steps", "3-6 steps"],
  ["Document ingestion", "PDF/image extraction yields context", ">95% parse target"],
  ["Artifact export", "Structured markdown or PDF produced", "100% required"],
];

const benchmarkRows = [
  ["Single-step chat", "1", "Low", "No state"],
  ["RAG-only summarizer", "2", "Medium", "Citations only"],
  ["This AI Platform", "4-6", "High", "Full SQLite memory"],
];

const architectureDiagram = `Architecture layers

\`\`\`mermaid
flowchart TD
    U["User Input"] --> F["React Dashboard"]
    F --> B["FastAPI + SSE"]
    B --> G["Gemini Vertex AI"]
    B --> O["Orchestrator"]
    O --> T["Tools (Search/OCR)"]
    T --> M["MCP Layer"]
    O --> D["SQLite Memory"]
    O --> E["LaTeX / Drive Export"]
\`\`\``;

const workflowDiagram = `Execution pipeline

\`\`\`mermaid
flowchart LR
    A["Goal"] --> B["Plan"]
    B --> C["Tools"]
    C --> D["Retrieve"]
    D --> E["Synthesize"]
    E --> F["Export"]
\`\`\``;

// Animation variants
const containerVariants = {
  hidden: { opacity: 0 },
  show: {
    opacity: 1,
    transition: { staggerChildren: 0.1 },
  },
};

const itemVariants = {
  hidden: { opacity: 0, y: 20 },
  show: { opacity: 1, y: 0, transition: { type: "spring", bounce: 0.4 } },
};

export const AgentOverviewShowcase = ({ onPromptSelect }: AgentOverviewShowcaseProps) => {
  return (
    <motion.div
      variants={containerVariants}
      initial="hidden"
      animate="show"
      className="space-y-8"
    >
      {/* HERO SECTION */}
      <motion.section variants={itemVariants} className="glass-strong relative overflow-hidden rounded-[2rem] p-8 md:p-10 border border-primary/20">
        <div className="absolute -top-24 -right-24 h-96 w-96 rounded-full bg-primary/20 blur-[100px]" />
        <div className="relative z-10 flex flex-col gap-6">
          <div className="flex flex-wrap items-center gap-3">
            <span className="flex items-center gap-2 rounded-full border border-primary/40 bg-primary/10 px-4 py-1.5 text-xs font-semibold uppercase tracking-widest text-primary">
              <Sparkles className="h-3.5 w-3.5" />
              Autonomous AI Research
            </span>
            <span className="rounded-full border border-border/40 bg-background/40 px-4 py-1.5 text-xs text-muted-foreground backdrop-blur-md">
              Gemini + MCP + Vertex AI
            </span>
          </div>
          <div className="space-y-4">
            <h1 className="max-w-3xl text-4xl font-bold leading-[1.15] text-foreground md:text-5xl lg:text-6xl tracking-tight">
              Research faster with <span className="text-gradient-primary">intelligent orchestration.</span>
            </h1>
            <p className="max-w-2xl text-base leading-relaxed text-muted-foreground md:text-lg">
              A production-ready agentic workspace that plans execution workflows, retrieves verified evidence via MCP tools, builds persistent memory, and compiles publication-ready PDF artifacts.
            </p>
          </div>
          <div className="mt-4 grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
            {heroPrompts.map((prompt) => (
              <button
                key={prompt}
                type="button"
                onClick={() => onPromptSelect(prompt)}
                className="group relative overflow-hidden rounded-2xl border border-white/10 bg-white/5 p-5 text-left transition-all hover:-translate-y-1 hover:border-primary/50 hover:bg-white/10 hover:shadow-float"
              >
                <div className="absolute inset-0 bg-gradient-to-br from-primary/10 to-transparent opacity-0 transition-opacity group-hover:opacity-100" />
                <p className="relative z-10 text-sm leading-relaxed text-foreground/90">{prompt}</p>
                <span className="relative z-10 mt-4 flex items-center gap-2 text-xs font-semibold text-primary transition-colors group-hover:text-primary-foreground">
                  Launch Agent Workflow
                  <ArrowRight className="h-4 w-4 transition-transform group-hover:translate-x-1" />
                </span>
              </button>
            ))}
          </div>
        </div>
      </motion.section>

      {/* CAPABILITIES GRID */}
      <motion.section variants={itemVariants} className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
        {capabilityCards.map(({ label, value, icon: Icon, color, bg }) => (
          <div key={label} className="glass group rounded-3xl p-6 transition-all hover:bg-white/5">
            <div className={`flex h-12 w-12 items-center justify-center rounded-2xl ${bg} ${color} transition-transform group-hover:scale-110`}>
              <Icon className="h-6 w-6" />
            </div>
            <h3 className="mt-5 text-xs font-bold uppercase tracking-widest text-muted-foreground">{label}</h3>
            <p className="mt-2 text-sm font-medium leading-relaxed text-foreground/90">{value}</p>
          </div>
        ))}
      </motion.section>

      {/* ARCHITECTURE & EXECUTION */}
      <motion.section variants={itemVariants} className="grid gap-6 lg:grid-cols-[1.2fr_0.8fr]">
        <div className="glass rounded-[2rem] p-6 md:p-8">
          <div className="mb-6 flex items-center gap-3">
            <div className="flex h-10 w-10 items-center justify-center rounded-xl bg-primary/20">
              <Network className="h-5 w-5 text-primary" />
            </div>
            <h2 className="text-xl font-bold tracking-tight text-foreground">Architecture Stack</h2>
          </div>
          <div className="grid gap-3">
            {architectureLayers.map((layer, idx) => (
              <div key={idx} className="flex items-start gap-4 rounded-2xl border border-white/5 bg-white/5 px-5 py-3.5 transition-colors hover:bg-white/10">
                <span className="flex h-6 w-6 shrink-0 items-center justify-center rounded-full bg-primary/10 text-xs font-bold text-primary">
                  {idx + 1}
                </span>
                <p className="text-sm leading-relaxed text-muted-foreground">{layer}</p>
              </div>
            ))}
          </div>
        </div>

        <div className="glass flex flex-col rounded-[2rem] p-6 md:p-8">
          <div className="mb-6 flex items-center gap-3">
            <div className="flex h-10 w-10 items-center justify-center rounded-xl bg-emerald-400/20">
              <ShieldCheck className="h-5 w-5 text-emerald-400" />
            </div>
            <h2 className="text-xl font-bold tracking-tight text-foreground">Execution Flow</h2>
          </div>
          <div className="flex-1 space-y-6 overflow-hidden rounded-2xl border border-white/5 bg-black/40 p-4">
            <div className="scale-90 transform opacity-80 mix-blend-screen grayscale transition-all hover:opacity-100 hover:grayscale-0">
              <MermaidRenderer content={workflowDiagram} />
            </div>
          </div>
        </div>
      </motion.section>

      {/* EVALUATION BENCHMARKS */}
      <motion.section variants={itemVariants} className="glass rounded-[2rem] p-6 md:p-8">
        <div className="mb-6 flex items-center gap-3">
          <div className="flex h-10 w-10 items-center justify-center rounded-xl bg-amber-400/20">
            <Database className="h-5 w-5 text-amber-400" />
          </div>
          <h2 className="text-xl font-bold tracking-tight text-foreground">System Benchmarks</h2>
        </div>
        
        <div className="grid gap-6 lg:grid-cols-2">
          <div className="overflow-hidden rounded-2xl border border-white/10 bg-black/20">
            <table className="w-full text-left text-sm">
              <thead className="bg-white/5 text-muted-foreground">
                <tr>
                  <th className="px-4 py-3 font-semibold">Metric</th>
                  <th className="px-4 py-3 font-semibold">Target</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-white/5">
                {evaluationRows.map((row, i) => (
                  <tr key={i} className="transition-colors hover:bg-white/5">
                    <td className="px-4 py-3 text-foreground/90">{row[0]}</td>
                    <td className="px-4 py-3 font-mono text-primary">{row[2]}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>

          <div className="overflow-hidden rounded-2xl border border-white/10 bg-black/20">
            <table className="w-full text-left text-sm">
              <thead className="bg-white/5 text-muted-foreground">
                <tr>
                  <th className="px-4 py-3 font-semibold">System Type</th>
                  <th className="px-4 py-3 font-semibold">Memory</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-white/5">
                {benchmarkRows.map((row, i) => (
                  <tr key={i} className="transition-colors hover:bg-white/5">
                    <td className="px-4 py-3 text-foreground/90">{row[0]}</td>
                    <td className="px-4 py-3 text-muted-foreground">{row[3]}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      </motion.section>
    </motion.div>
  );
};

