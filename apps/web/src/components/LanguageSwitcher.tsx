import { useTranslation } from "react-i18next";

const LOCALES = [
  { code: "en", label: "EN" },
  { code: "ru", label: "RU" },
  { code: "bg", label: "BG" },
] as const;

export function LanguageSwitcher() {
  const { i18n, t } = useTranslation();

  return (
    <div className="flex items-center gap-1" role="group" aria-label={t("common.language")}>
      {LOCALES.map((l) => (
        <button
          key={l.code}
          type="button"
          onClick={() => void i18n.changeLanguage(l.code)}
          className={`rounded px-2 py-1 text-xs font-medium transition ${
            i18n.language?.startsWith(l.code)
              ? "bg-brand-600 text-white"
              : "text-slate-400 hover:text-slate-200 hover:bg-slate-800"
          }`}
        >
          {l.label}
        </button>
      ))}
    </div>
  );
}
