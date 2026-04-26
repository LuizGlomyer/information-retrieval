import { Star } from "lucide-react";
import { useLanguage } from "@/components/LanguageProvider";
import type { RankedResult } from "@/lib/types";

interface Props {
  result: RankedResult;
  /** Show full summary (single-model view) vs compact (compare view). */
  compact?: boolean;
}

export const ResultCard = ({ result, compact = false }: Props) => {
  const { t } = useLanguage();

  return (
    <article className="group flex gap-4 rounded-lg border border-border bg-card p-3 transition-colors hover:bg-surface">
      <div className="relative flex-shrink-0 overflow-hidden rounded-md">
        <img
          src={result.cover}
          alt={`${t.resultCard.coverAlt} ${result.name}`}
          loading="lazy"
          width={compact ? 72 : 110}
          height={compact ? 90 : 138}
          className={`object-cover ${compact ? "h-[90px] w-[72px]" : "h-[138px] w-[110px]"}`}
        />
        <span className="absolute left-1 top-1 rounded bg-background/85 px-1.5 py-0.5 font-mono text-[10px] font-semibold text-foreground backdrop-blur">
          #{result.rank}
        </span>
      </div>

      <div className="flex min-w-0 flex-1 flex-col">
        <div className="flex items-start justify-between gap-3">
          <h4 className="truncate font-serif text-base font-semibold leading-tight">
            {result.name}
          </h4>
          <div className="flex items-center gap-1 font-mono text-xs text-muted-foreground">
            <Star className="h-3 w-3 fill-primary text-primary" />
            <span className="tabular-nums">{result.rating.toFixed(1)}</span>
          </div>
        </div>

        <p className={`mt-1 text-xs text-muted-foreground ${compact ? "line-clamp-2" : "line-clamp-3"}`}>
          {result.summary}
        </p>

        <div className="mt-2 flex flex-wrap gap-1">
          {result.genres.slice(0, compact ? 2 : 3).map((genre) => (
            <span key={genre} className="badge-soft text-[10px]">
              {genre}
            </span>
          ))}
        </div>

        <div className="mt-auto flex items-center justify-between pt-2">
          <span className="font-mono text-[10px] uppercase tracking-wider text-muted-foreground">
            {new Date(result.release_date).getFullYear()}
          </span>
          <div className="flex items-baseline gap-1.5 font-mono text-xs">
            <span className="text-muted-foreground">{t.resultCard.score}</span>
            <span className="tabular-nums font-semibold text-primary">
              {result.score.toFixed(2)}
            </span>
          </div>
        </div>
      </div>
    </article>
  );
};
