import { LanguageToggle } from "./LanguageToggle";
import { ThemeToggle } from "./ThemeToggle";
import { useLanguage } from "./LanguageProvider";

export const SiteHeader = () => {
  const { t } = useLanguage();

  return (
    <header className="sticky top-0 z-40 border-b border-border/70 bg-background/80 backdrop-blur supports-[backdrop-filter]:bg-background/60">
      <div className="container flex h-14 items-center justify-between">
        <a href="#top" className="flex items-baseline gap-2">
          <span className="font-serif text-lg font-semibold tracking-tight">Indexed</span>
          <span className="font-mono text-[10px] uppercase tracking-[0.2em] text-muted-foreground">
            / IR Lab
          </span>
        </a>

        <nav className="hidden items-center gap-7 md:flex">
          <a href="#pipeline" className="text-sm text-muted-foreground transition-colors hover:text-foreground">
            {t.header.nav.pipeline}
          </a>
          <a href="#models" className="text-sm text-muted-foreground transition-colors hover:text-foreground">
            {t.header.nav.models}
          </a>
          <a href="#metrics" className="text-sm text-muted-foreground transition-colors hover:text-foreground">
            {t.header.nav.metrics}
          </a>
          <a href="#playground" className="text-sm text-muted-foreground transition-colors hover:text-foreground">
            {t.header.nav.playground}
          </a>
        </nav>

        <div className="flex items-center gap-2">
          <a
            href="#playground"
            className="hidden rounded-full border border-border bg-card px-3 py-1.5 text-xs font-medium text-foreground transition-colors hover:bg-muted sm:inline-block"
          >
            {t.header.cta}
          </a>
          <LanguageToggle />
          <ThemeToggle />
        </div>
      </div>
    </header>
  );
};
