import { useState } from "react";
import { Loader2, Search, Columns3, Square } from "lucide-react";
import { useLanguage } from "@/components/LanguageProvider";
import { MODELS } from "@/lib/models";
import { executeSearch } from "@/lib/searchService";
import type { ModelId, MultiAlgorithmSearchResponse } from "@/lib/types";
import { SectionHeading } from "../sections/Pipeline";
import { ResultCard } from "./ResultCard";

type Mode = "single" | "compare";

export const Playground = () => {
  const { t } = useLanguage();
  const [query, setQuery] = useState(t.playground.defaultQuery);
  const [mode, setMode] = useState<Mode>("compare");
  const [activeModel, setActiveModel] = useState<ModelId>("bm25_weighted");
  const [selectedModels, setSelectedModels] = useState<ModelId[]>([
    "bm25",
    "bm25_weighted",
    "bm25_weighted_embeddings",
  ]);
  const [response, setResponse] = useState<MultiAlgorithmSearchResponse | null>(null);
  const [loading, setLoading] = useState(false);

  const runSearch = async (q: string = query) => {
    if (!q.trim()) return;
    setLoading(true);
    const models = mode === "single" ? [activeModel] : selectedModels;
    try {
      const res = await executeSearch({ query_text: q, models, size: 6 });
      setResponse(res);
    } finally {
      setLoading(false);
    }
  };

  const toggleSelected = (id: ModelId) => {
    setSelectedModels((prev) =>
      prev.includes(id) ? prev.filter((x) => x !== id) : [...prev, id],
    );
  };

  const activeIds: ModelId[] = mode === "single" ? [activeModel] : selectedModels;

  return (
    <section id="playground" className="border-b border-border/70 bg-surface">
      <div className="container py-20 md:py-28">
        <SectionHeading
          eyebrow={t.playground.heading.eyebrow}
          title={t.playground.heading.title}
          lede={t.playground.heading.lede}
        />

        <form
          onSubmit={(e) => {
            e.preventDefault();
            void runSearch();
          }}
          className="mt-12 rounded-xl border border-border bg-card p-2 shadow-sm"
        >
          <div className="flex items-center gap-2">
            <Search className="ml-3 h-4 w-4 flex-shrink-0 text-muted-foreground" />
            <input
              value={query}
              onChange={(e) => setQuery(e.target.value)}
              placeholder={t.playground.placeholder}
              className="flex-1 bg-transparent px-1 py-3 font-serif text-lg outline-none placeholder:text-muted-foreground/60"
              aria-label={t.playground.searchLabel}
            />
            <button
              type="submit"
              disabled={loading}
              className="inline-flex items-center gap-2 rounded-lg bg-foreground px-4 py-2.5 text-sm font-medium text-background transition-opacity hover:opacity-90 disabled:opacity-50"
            >
              {loading ? <Loader2 className="h-4 w-4 animate-spin" /> : <Search className="h-4 w-4" />}
              {t.playground.search}
            </button>
          </div>
          <div className="mt-2 flex flex-wrap items-center gap-2 px-3 pb-2">
            <span className="font-mono text-[10px] uppercase tracking-wider text-muted-foreground">
              {t.playground.try}
            </span>
            {t.playground.suggestions.map((suggestion) => (
              <button
                key={suggestion}
                type="button"
                onClick={() => {
                  setQuery(suggestion);
                  void runSearch(suggestion);
                }}
                className="rounded-full border border-border bg-background px-2.5 py-0.5 font-mono text-[11px] text-muted-foreground transition-colors hover:text-foreground"
              >
                {suggestion}
              </button>
            ))}
          </div>
        </form>

        <div className="mt-8 grid gap-4 md:grid-cols-12 md:items-start">
          <div className="md:col-span-3">
            <p className="mb-2 font-mono text-[10px] uppercase tracking-wider text-muted-foreground">
              {t.playground.viewMode}
            </p>
            <div className="inline-flex rounded-lg border border-border bg-card p-1">
              <ModeButton
                active={mode === "single"}
                onClick={() => setMode("single")}
                icon={<Square className="h-3.5 w-3.5" />}
                label={t.playground.single}
              />
              <ModeButton
                active={mode === "compare"}
                onClick={() => setMode("compare")}
                icon={<Columns3 className="h-3.5 w-3.5" />}
                label={t.playground.compare}
              />
            </div>
          </div>

          <div className="md:col-span-9">
            <p className="mb-2 font-mono text-[10px] uppercase tracking-wider text-muted-foreground">
              {mode === "single" ? t.playground.model : t.playground.modelsToCompare}
            </p>
            <div className="flex flex-wrap gap-2">
              {MODELS.map((m) => {
                const isActive =
                  mode === "single" ? activeModel === m.id : selectedModels.includes(m.id);
                return (
                  <button
                    key={m.id}
                    type="button"
                    onClick={() =>
                      mode === "single" ? setActiveModel(m.id) : toggleSelected(m.id)
                    }
                    className={`rounded-full border px-3 py-1.5 text-xs font-medium transition-colors ${
                      isActive
                        ? "border-foreground bg-foreground text-background"
                        : "border-border bg-card text-muted-foreground hover:text-foreground"
                    }`}
                  >
                    {m.shortName}
                  </button>
                );
              })}
            </div>
          </div>
        </div>

        <div className="mt-10">
          {!response && !loading && (
            <EmptyState onRun={() => void runSearch()} />
          )}

          {loading && <LoadingSkeleton count={mode === "single" ? 1 : activeIds.length} />}

          {response && !loading && (
            <div
              className={`grid gap-6 ${
                mode === "single"
                  ? "grid-cols-1"
                  : activeIds.length === 1
                    ? "grid-cols-1"
                    : activeIds.length === 2
                      ? "lg:grid-cols-2"
                      : "lg:grid-cols-2 xl:grid-cols-3"
              }`}
            >
              {activeIds.map((id) => {
                const meta = MODELS.find((m) => m.id === id)!;
                const algo = response[id];
                return (
                  <div
                    key={id}
                    className="flex flex-col rounded-lg border border-border bg-card p-5 animate-fade-up"
                  >
                    <header className="mb-4 flex items-baseline justify-between border-b border-border pb-3">
                      <div>
                        <h3 className="font-serif text-lg font-semibold tracking-tight">
                          {meta.name}
                        </h3>
                        <p className="font-mono text-[10px] uppercase tracking-wider text-muted-foreground">
                          {t.models.families[meta.family]}
                        </p>
                      </div>
                      <div className="flex items-baseline gap-3 font-mono text-[11px] text-muted-foreground">
                        <span>
                          <span className="text-foreground">{algo?.total ?? 0}</span> {t.playground.hits}
                        </span>
                        <span>
                          <span className="text-foreground">{algo?.execution_time_ms ?? 0}</span> {t.playground.milliseconds}
                        </span>
                      </div>
                    </header>

                    {algo && algo.results.length > 0 ? (
                      <div className="space-y-3">
                        {algo.results.map((r) => (
                          <ResultCard key={r.id} result={r} compact={mode === "compare"} />
                        ))}
                      </div>
                    ) : (
                      <p className="py-12 text-center text-sm text-muted-foreground">
                        {t.playground.noResults}
                      </p>
                    )}
                  </div>
                );
              })}
            </div>
          )}
        </div>
      </div>
    </section>
  );
};

const ModeButton = ({
  active,
  onClick,
  icon,
  label,
}: {
  active: boolean;
  onClick: () => void;
  icon: React.ReactNode;
  label: string;
}) => (
  <button
    type="button"
    onClick={onClick}
    className={`inline-flex items-center gap-1.5 rounded-md px-3 py-1.5 text-xs font-medium transition-colors ${
      active ? "bg-foreground text-background" : "text-muted-foreground hover:text-foreground"
    }`}
  >
    {icon}
    {label}
  </button>
);

const EmptyState = ({ onRun }: { onRun: () => void }) => {
  const { t } = useLanguage();

  return (
    <div className="rounded-lg border border-dashed border-border bg-card p-12 text-center">
      <p className="font-serif text-2xl">{t.playground.emptyTitle}</p>
      <p className="mx-auto mt-2 max-w-md text-sm text-muted-foreground">
        {t.playground.emptyDescription}
      </p>
      <button
        onClick={onRun}
        className="mt-5 inline-flex items-center gap-2 rounded-full bg-foreground px-4 py-2 text-sm text-background"
      >
        <Search className="h-3.5 w-3.5" /> {t.playground.runDefault}
      </button>
    </div>
  );
};

const LoadingSkeleton = ({ count }: { count: number }) => (
  <div className={`grid gap-6 ${count === 1 ? "grid-cols-1" : "lg:grid-cols-2 xl:grid-cols-3"}`}>
    {Array.from({ length: count }).map((_, i) => (
      <div key={i} className="rounded-lg border border-border bg-card p-5">
        <div className="mb-4 h-6 w-32 animate-pulse rounded bg-muted" />
        <div className="space-y-3">
          {Array.from({ length: 4 }).map((_, j) => (
            <div key={j} className="flex gap-4">
              <div className="h-[90px] w-[72px] animate-pulse rounded bg-muted" />
              <div className="flex-1 space-y-2 py-1">
                <div className="h-4 w-2/3 animate-pulse rounded bg-muted" />
                <div className="h-3 w-full animate-pulse rounded bg-muted" />
                <div className="h-3 w-5/6 animate-pulse rounded bg-muted" />
              </div>
            </div>
          ))}
        </div>
      </div>
    ))}
  </div>
);
