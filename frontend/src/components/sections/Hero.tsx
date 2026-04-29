import { ArrowDown } from "lucide-react";
import { useLanguage } from "@/components/LanguageProvider";

export const Hero = () => {
  const { t } = useLanguage();

  return (
    <section id="top" className="relative overflow-hidden border-b border-border/70 bg-surface grain">
      <div className="container relative z-10 grid gap-10 py-20 md:grid-cols-12 md:py-28 lg:py-36">
        <div className="md:col-span-8">
          <p className="mb-6 flex items-center gap-3 font-mono text-[11px] uppercase tracking-[0.25em] text-muted-foreground">
            <span className="h-px w-8 bg-foreground/40" />
            {t.hero.eyebrow}
          </p>

          <h1 className="font-serif text-5xl font-semibold leading-[0.98] tracking-tight text-balance md:text-7xl lg:text-[5.5rem]">
            {t.hero.titlePrefix} <em className="font-serif italic text-primary">{t.hero.titleEmphasis}</em>,
            <br />
            {t.hero.titleSuffix}
          </h1>

          <p className="mt-8 max-w-2xl text-lg text-muted-foreground text-pretty md:text-xl">
            {t.hero.lede}
          </p>

          <div className="mt-10 flex flex-wrap items-center gap-3">
            <a
              href="#playground"
              className="inline-flex items-center gap-2 rounded-full bg-foreground px-5 py-2.5 text-sm font-medium text-background transition-opacity hover:opacity-90"
            >
              {t.hero.primaryCta}
              <ArrowDown className="h-4 w-4 -rotate-45" />
            </a>
            <a
              href="#pipeline"
              className="inline-flex items-center gap-2 rounded-full border border-border bg-card px-5 py-2.5 text-sm font-medium text-foreground transition-colors hover:bg-muted"
            >
              {t.hero.secondaryCta}
            </a>
          </div>
        </div>

        <aside className="md:col-span-4 md:border-l md:border-border md:pl-8">
          <dl className="space-y-6">
            <div>
              <dt className="font-mono text-[10px] uppercase tracking-[0.2em] text-muted-foreground">
                {t.hero.stats.corpus}
              </dt>
              <dd className="mt-1 font-serif text-3xl">
                12,438 <span className="text-base font-sans text-muted-foreground">{t.hero.stats.games}</span>
              </dd>
            </div>
            <div>
              <dt className="font-mono text-[10px] uppercase tracking-[0.2em] text-muted-foreground">
                {t.hero.stats.indexedFields}
              </dt>
              <dd className="mt-1 font-serif text-3xl">11</dd>
            </div>
            <div>
              <dt className="font-mono text-[10px] uppercase tracking-[0.2em] text-muted-foreground">
                {t.hero.stats.rankingModels}
              </dt>
              <dd className="mt-1 font-serif text-3xl">5</dd>
            </div>
            <div>
              <dt className="font-mono text-[10px] uppercase tracking-[0.2em] text-muted-foreground">
                {t.hero.stats.evaluationMetrics}
              </dt>
              <dd className="mt-1 font-serif text-3xl">9</dd>
            </div>
          </dl>
        </aside>
      </div>
    </section>
  );
};
