import { useMemo, useState } from "react";
import {
  Bar,
  BarChart,
  CartesianGrid,
  Legend,
  Line,
  LineChart,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";
import { useLanguage } from "@/components/LanguageProvider";
import { ALL_METRIC_KEYS, MODELS, MODEL_METRICS } from "@/lib/models";
import type { MetricKey, ModelId } from "@/lib/types";
import { SectionHeading } from "./Pipeline";

const KEY_METRICS: MetricKey[] = ["NDCG@10", "MAP", "P@5", "F1"];

export const Metrics = () => {
  const { t } = useLanguage();
  const [selected, setSelected] = useState<MetricKey>("NDCG@10");

  const barData = useMemo(
    () =>
      MODELS.map((m) => ({
        model: m.shortName,
        score: MODEL_METRICS[m.id][selected],
      })),
    [selected],
  );

  const lineData = useMemo(
    () =>
      ALL_METRIC_KEYS.map((k) => {
        const row: Record<string, string | number> = { metric: k };
        MODELS.forEach((m) => {
          row[m.shortName] = MODEL_METRICS[m.id][k];
        });
        return row;
      }),
    [],
  );

  return (
    <section id="metrics" className="border-b border-border/70">
      <div className="container py-20 md:py-28">
        <SectionHeading
          eyebrow={t.metrics.heading.eyebrow}
          title={t.metrics.heading.title}
          lede={t.metrics.heading.lede}
        />

        <div className="mt-12 flex flex-wrap items-center gap-2">
          <span className="mr-2 font-mono text-[11px] uppercase tracking-wider text-muted-foreground">
            {t.metrics.compareOn}
          </span>
          {KEY_METRICS.map((m) => (
            <button
              key={m}
              onClick={() => setSelected(m)}
              className={`rounded-full border px-3 py-1 font-mono text-xs transition-colors ${
                selected === m
                  ? "border-foreground bg-foreground text-background"
                  : "border-border bg-card text-muted-foreground hover:text-foreground"
              }`}
            >
              {m}
            </button>
          ))}
        </div>

        <div className="mt-8 grid gap-6 lg:grid-cols-5">
          <div className="rounded-lg border border-border bg-card p-6 lg:col-span-2">
            <header className="mb-2 flex items-baseline justify-between">
              <h3 className="font-serif text-xl font-semibold">{selected}</h3>
              <span className="font-mono text-[10px] uppercase tracking-wider text-muted-foreground">
                {t.metrics.higherIsBetter}
              </span>
            </header>
            <p className="mb-4 text-sm text-muted-foreground">
              {t.metrics.selectedMetricDescription}
            </p>
            <div className="h-[280px]">
              <ResponsiveContainer width="100%" height="100%">
                <BarChart data={barData} margin={{ top: 10, right: 10, left: -20, bottom: 0 }}>
                  <CartesianGrid stroke="hsl(var(--border))" strokeDasharray="3 3" vertical={false} />
                  <XAxis
                    dataKey="model"
                    tick={{ fill: "hsl(var(--muted-foreground))", fontSize: 11, fontFamily: "JetBrains Mono" }}
                    axisLine={{ stroke: "hsl(var(--border))" }}
                    tickLine={false}
                  />
                  <YAxis
                    domain={[0, 1]}
                    tick={{ fill: "hsl(var(--muted-foreground))", fontSize: 11, fontFamily: "JetBrains Mono" }}
                    axisLine={false}
                    tickLine={false}
                  />
                  <Tooltip
                    cursor={{ fill: "hsl(var(--muted))" }}
                    contentStyle={{
                      background: "hsl(var(--popover))",
                      border: "1px solid hsl(var(--border))",
                      borderRadius: 8,
                      fontSize: 12,
                    }}
                  />
                  <Bar dataKey="score" fill="hsl(var(--primary))" radius={[6, 6, 0, 0]} />
                </BarChart>
              </ResponsiveContainer>
            </div>
          </div>

          <div className="rounded-lg border border-border bg-card p-6 lg:col-span-3">
            <header className="mb-2 flex items-baseline justify-between">
              <h3 className="font-serif text-xl font-semibold">{t.metrics.allMetricsTitle}</h3>
              <span className="font-mono text-[10px] uppercase tracking-wider text-muted-foreground">
                {t.metrics.profile}
              </span>
            </header>
            <p className="mb-4 text-sm text-muted-foreground">
              {t.metrics.allMetricsDescription}
            </p>
            <div className="h-[280px]">
              <ResponsiveContainer width="100%" height="100%">
                <LineChart data={lineData} margin={{ top: 10, right: 16, left: -20, bottom: 0 }}>
                  <CartesianGrid stroke="hsl(var(--border))" strokeDasharray="3 3" vertical={false} />
                  <XAxis
                    dataKey="metric"
                    tick={{ fill: "hsl(var(--muted-foreground))", fontSize: 10, fontFamily: "JetBrains Mono" }}
                    axisLine={{ stroke: "hsl(var(--border))" }}
                    tickLine={false}
                  />
                  <YAxis
                    domain={[0, 1]}
                    tick={{ fill: "hsl(var(--muted-foreground))", fontSize: 11, fontFamily: "JetBrains Mono" }}
                    axisLine={false}
                    tickLine={false}
                  />
                  <Tooltip
                    contentStyle={{
                      background: "hsl(var(--popover))",
                      border: "1px solid hsl(var(--border))",
                      borderRadius: 8,
                      fontSize: 12,
                    }}
                  />
                  <Legend wrapperStyle={{ fontSize: 11, fontFamily: "JetBrains Mono" }} />
                  {MODELS.map((m, i) => (
                    <Line
                      key={m.id}
                      type="monotone"
                      dataKey={m.shortName}
                      stroke={`hsl(var(--chart-${(i % 5) + 1}))`}
                      strokeWidth={2}
                      dot={{ r: 3 }}
                      activeDot={{ r: 5 }}
                    />
                  ))}
                </LineChart>
              </ResponsiveContainer>
            </div>
          </div>
        </div>

        <div className="mt-8 overflow-hidden rounded-lg border border-border bg-card">
          <div className="overflow-x-auto">
            <table className="w-full text-sm">
              <thead className="bg-surface">
                <tr>
                  <th className="px-4 py-3 text-left font-mono text-[10px] uppercase tracking-wider text-muted-foreground">
                    {t.metrics.modelColumn}
                  </th>
                  {ALL_METRIC_KEYS.map((k) => (
                    <th
                      key={k}
                      className="px-3 py-3 text-right font-mono text-[10px] uppercase tracking-wider text-muted-foreground"
                    >
                      {k}
                    </th>
                  ))}
                </tr>
              </thead>
              <tbody>
                {MODELS.map((m) => {
                  const scores = MODEL_METRICS[m.id];
                  return (
                    <tr key={m.id} className="border-t border-border transition-colors hover:bg-muted/40">
                      <td className="px-4 py-3 font-medium">
                        <div className="flex items-center gap-2">
                          <span>{m.name}</span>
                          <span className="font-mono text-[10px] uppercase tracking-wider text-muted-foreground">
                            {t.models.families[m.family]}
                          </span>
                        </div>
                      </td>
                      {ALL_METRIC_KEYS.map((k) => {
                        const value = scores[k];
                        const best = Math.max(...MODELS.map((mm) => MODEL_METRICS[mm.id as ModelId][k]));
                        const isBest = value === best;
                        return (
                          <td
                            key={k}
                            className={`px-3 py-3 text-right font-mono tabular-nums ${
                              isBest ? "font-semibold text-primary" : "text-foreground/80"
                            }`}
                          >
                            {value.toFixed(2)}
                          </td>
                        );
                      })}
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>
        </div>

        <p className="mt-4 font-mono text-[11px] text-muted-foreground">
          <span className="text-primary">*</span> {t.metrics.bestNote}
        </p>
      </div>
    </section>
  );
};
