import { useLanguage } from "@/components/LanguageProvider";
import { MODELS } from "@/lib/models";
import { SectionHeading } from "./Pipeline";

const statusStyle: Record<string, string> = {
  stable: "bg-accent/15 text-accent border-accent/30",
  experimental: "bg-primary/15 text-primary border-primary/30",
  planned: "bg-muted text-muted-foreground border-border",
};

export const ModelsSection = () => {
  const { t } = useLanguage();

  return (
    <section id="models" className="border-b border-border/70 bg-surface">
      <div className="container py-20 md:py-28">
        <SectionHeading
          eyebrow={t.models.heading.eyebrow}
          title={t.models.heading.title}
          lede={t.models.heading.lede}
        />

        <div className="mt-16 grid gap-6 md:grid-cols-2 lg:grid-cols-3">
          {MODELS.map((m, i) => {
            const copy = t.models.copy[m.id];

            return (
              <article
                key={m.id}
                className="group relative flex flex-col rounded-lg border border-border bg-card p-6 transition-all hover:-translate-y-0.5 hover:shadow-sm"
              >
                <div className="flex items-start justify-between gap-3">
                  <span className="step-num text-xs text-muted-foreground">
                    {String(i + 1).padStart(2, "0")}
                  </span>
                  <span
                    className={`rounded-full border px-2 py-0.5 font-mono text-[10px] uppercase tracking-wider ${statusStyle[m.status]}`}
                  >
                    {t.models.statuses[m.status]}
                  </span>
                </div>
                <h3 className="mt-4 font-serif text-2xl font-semibold tracking-tight">
                  {m.name}
                </h3>
                <p className="mt-1 font-mono text-[11px] uppercase tracking-wider text-muted-foreground">
                  {t.models.families[m.family]}
                </p>
                <p className="mt-4 text-sm italic text-foreground/80">{copy.tagline}</p>
                <p className="mt-3 text-sm leading-relaxed text-muted-foreground text-pretty">
                  {copy.description}
                </p>
                <div className="mt-5 flex flex-wrap gap-1.5">
                  {copy.techniques.map((technique) => (
                    <span key={technique} className="badge-soft">
                      {technique}
                    </span>
                  ))}
                </div>
              </article>
            );
          })}
        </div>
      </div>
    </section>
  );
};
