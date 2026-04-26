import { useLanguage } from "./LanguageProvider";

export const SiteFooter = () => {
  const { t } = useLanguage();

  return (
    <footer className="bg-background">
      <div className="container py-12">
        <div className="flex flex-col items-start justify-between gap-6 md:flex-row md:items-end">
          <div>
            <p className="font-serif text-2xl font-semibold tracking-tight">Indexed</p>
            <p className="mt-1 max-w-md text-sm text-muted-foreground">
              {t.footer.description}
            </p>
          </div>
          <div className="font-mono text-[11px] uppercase tracking-wider text-muted-foreground">
            <p>{t.footer.backend}</p>
            <p className="mt-1">{t.footer.frontend}</p>
          </div>
        </div>
        <div className="divider-rule mt-8" />
        <p className="mt-6 font-mono text-[11px] text-muted-foreground">
          (c) {new Date().getFullYear()} {t.footer.copyright}
        </p>
      </div>
    </footer>
  );
};
