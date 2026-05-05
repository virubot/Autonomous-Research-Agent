import { Bar, BarChart, ResponsiveContainer, Tooltip, XAxis, YAxis } from "recharts";
import { Beaker } from "lucide-react";

const data = [
  { name: "Model A", accuracy: 85 },
  { name: "Model B", accuracy: 92 },
  { name: "Model C", accuracy: 88 },
  { name: "Model D", accuracy: 95 },
];

export const LaboratoryPanel = () => {
  return (
    <div className="glass rounded-2xl p-4 shadow-[0_8px_32px_0_rgba(0,0,0,0.36)] border border-white/5">
      <div className="mb-4 flex items-center gap-2 border-b border-white/10 pb-3">
        <div className="flex h-7 w-7 items-center justify-center rounded-lg bg-primary/20 text-primary">
          <Beaker className="h-4 w-4" />
        </div>
        <h3 className="text-sm font-semibold text-foreground">Laboratory</h3>
      </div>
      <div className="h-[180px] w-full">
        <ResponsiveContainer width="100%" height="100%">
          <BarChart data={data} margin={{ top: 10, right: 10, left: -20, bottom: 0 }}>
            <XAxis dataKey="name" fontSize={11} tickLine={false} axisLine={false} tick={{ fill: "hsl(var(--muted-foreground))" }} />
            <YAxis fontSize={11} tickLine={false} axisLine={false} tick={{ fill: "hsl(var(--muted-foreground))" }} />
            <Tooltip
              contentStyle={{ backgroundColor: "rgba(10, 15, 30, 0.8)", border: "1px solid rgba(255,255,255,0.1)", borderRadius: "8px", backdropFilter: "blur(8px)" }}
              itemStyle={{ color: "hsl(var(--primary))", fontSize: "12px" }}
              labelStyle={{ color: "hsl(var(--foreground))", fontSize: "12px", fontWeight: "bold", marginBottom: "4px" }}
              cursor={{ fill: "rgba(255,255,255,0.05)" }}
            />
            <Bar dataKey="accuracy" fill="hsl(var(--primary))" radius={[4, 4, 0, 0]} barSize={24} />
          </BarChart>
        </ResponsiveContainer>
      </div>
      <p className="mt-3 text-center text-[10px] uppercase tracking-wider text-muted-foreground/60">
        Accuracy Comparison
      </p>
    </div>
  );
};
