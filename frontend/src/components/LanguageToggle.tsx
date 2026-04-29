import { Languages } from "lucide-react";
import { Button } from "@/components/ui/button";
import { useLanguage } from "./LanguageProvider";

export const LanguageToggle = () => {
  const { toggleLanguage, t } = useLanguage();

  return (
    <Button
      variant="ghost"
      size="sm"
      onClick={toggleLanguage}
      aria-label={t.languageToggle.label}
      className="gap-1.5 rounded-full px-2.5 font-mono text-[11px] uppercase tracking-wider"
    >
      <Languages className="h-4 w-4" />
      {t.languageToggle.shortLabel}
    </Button>
  );
};
