import { useLanguage } from "@/components/LanguageProvider";

export const Pipeline = () => {
  const { t } = useLanguage();

  return (
    <section id="pipeline" className="border-b border-border/70">
      <div className="container py-20 md:py-28">
        <SectionHeading
          eyebrow={t.pipeline.heading.eyebrow}
          title={t.pipeline.heading.title}
          lede={t.pipeline.heading.lede}
        />

        <ol className="mt-16 grid gap-px overflow-hidden rounded-lg border border-border bg-border md:grid-cols-2">
          {t.pipeline.steps.map((step, index) => (
            <li key={step.title} className="relative bg-card p-8 transition-colors hover:bg-surface">
              <div className="flex items-baseline justify-between gap-6">
                <span className="step-num text-sm text-primary">
                  {String(index + 1).padStart(2, "0")}
                </span>
                <span className="font-mono text-[10px] uppercase tracking-[0.18em] text-muted-foreground">
                  {step.output}
                </span>
              </div>
              <h3 className="mt-3 font-serif text-2xl font-semibold tracking-tight">
                {step.title}
              </h3>
              <p className="mt-3 text-sm leading-relaxed text-muted-foreground text-pretty">
                {step.desc}
              </p>
            </li>
          ))}
        </ol>
      </div>
    </section>
  );
};

export const SectionHeading = ({
  eyebrow,
  title,
  lede,
}: {
  eyebrow: string;
  title: string;
  lede?: string;
}) => (
  <header className="grid gap-8 md:grid-cols-12">
    <p className="font-mono text-[11px] uppercase tracking-[0.25em] text-muted-foreground md:col-span-3">
      {eyebrow}
    </p>
    <div className="md:col-span-9">
      <h2 className="font-serif text-4xl font-semibold leading-tight tracking-tight text-balance md:text-5xl">
        {title}
      </h2>
      {lede && (
        <p className="mt-5 max-w-3xl text-lg text-muted-foreground text-pretty">{lede}</p>
      )}
    </div>
  </header>
);
