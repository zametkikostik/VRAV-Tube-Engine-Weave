import { FormEvent, useState } from "react";
import { Link } from "react-router-dom";
import { useTranslation } from "react-i18next";
import { LanguageSwitcher } from "@/components/LanguageSwitcher";
import { api, ApiError } from "@/lib/api";

const PLANS = [
  {
    code: "personal",
    nameKey: "pricing.personal",
    price: "$19",
    features: ["pricing.f_audits_20", "pricing.f_html_pdf", "pricing.f_ai"],
    highlighted: false,
  },
  {
    code: "professional",
    nameKey: "pricing.professional",
    price: "$49",
    features: ["pricing.f_audits_100", "pricing.f_html_pdf", "pricing.f_ai", "pricing.f_priority"],
    highlighted: true,
  },
  {
    code: "agency",
    nameKey: "pricing.agency",
    price: "$149",
    features: [
      "pricing.f_audits_500",
      "pricing.f_white_label",
      "pricing.f_html_pdf",
      "pricing.f_ai",
    ],
    highlighted: false,
  },
] as const;

function EnterpriseContactForm() {
  const { t, i18n } = useTranslation();
  const [fullName, setFullName] = useState("");
  const [email, setEmail] = useState("");
  const [company, setCompany] = useState("");
  const [message, setMessage] = useState("");
  const [error, setError] = useState("");
  const [ok, setOk] = useState(false);
  const [busy, setBusy] = useState(false);

  async function onSubmit(e: FormEvent) {
    e.preventDefault();
    setError("");
    setOk(false);
    setBusy(true);
    try {
      await api.submitContact({
        full_name: fullName,
        email,
        company: company || undefined,
        message,
        locale: i18n.language?.slice(0, 2) || "en",
      });
      setOk(true);
      setFullName("");
      setEmail("");
      setCompany("");
      setMessage("");
    } catch (err) {
      setError(err instanceof ApiError ? err.message : t("common.error"));
    } finally {
      setBusy(false);
    }
  }

  return (
    <form onSubmit={onSubmit} className="mt-8 space-y-4">
      <div>
        <label className="label">{t("contact.name")}</label>
        <input className="input" value={fullName} onChange={(e) => setFullName(e.target.value)} required />
      </div>
      <div>
        <label className="label">{t("auth.email")}</label>
        <input className="input" type="email" value={email} onChange={(e) => setEmail(e.target.value)} required />
      </div>
      <div>
        <label className="label">{t("contact.company")}</label>
        <input className="input" value={company} onChange={(e) => setCompany(e.target.value)} />
      </div>
      <div>
        <label className="label">{t("contact.message")}</label>
        <textarea
          className="input min-h-[120px]"
          value={message}
          onChange={(e) => setMessage(e.target.value)}
          required
          minLength={10}
        />
      </div>
      {error && <p className="text-sm text-red-400">{error}</p>}
      {ok && <p className="text-sm text-emerald-400">{t("contact.success")}</p>}
      <button type="submit" className="btn-primary w-full" disabled={busy}>
        {busy ? t("common.loading") : t("contact.send")}
      </button>
    </form>
  );
}

export function Landing() {
  const { t } = useTranslation();

  return (
    <div className="min-h-screen flex flex-col">
      <header className="border-b border-slate-800">
        <div className="mx-auto flex max-w-6xl items-center justify-between px-4 py-4">
          <span className="text-lg font-semibold tracking-tight text-white">{t("app_name")}</span>
          <div className="flex items-center gap-4">
            <a href="#pricing" className="text-sm text-slate-400 hover:text-white">
              {t("pricing.title")}
            </a>
            <a href="#contact" className="text-sm text-slate-400 hover:text-white">
              {t("contact.title")}
            </a>
            <LanguageSwitcher />
            <Link to="/login" className="btn-secondary text-sm">
              {t("auth.login")}
            </Link>
            <Link to="/register" className="btn-primary text-sm">
              {t("auth.register")}
            </Link>
          </div>
        </div>
      </header>

      <main className="flex flex-1 flex-col">
        <section className="flex flex-col items-center px-4 py-20 text-center">
          <h1 className="max-w-3xl text-4xl font-bold tracking-tight text-white sm:text-5xl">
            {t("landing.hero")}
          </h1>
          <p className="mt-6 max-w-2xl text-lg text-slate-400">{t("landing.sub")}</p>
          <div className="mt-10 flex gap-4">
            <Link to="/register" className="btn-primary px-8 py-3 text-base">
              {t("landing.cta")}
            </Link>
            <Link to="/login" className="btn-secondary px-8 py-3 text-base">
              {t("auth.login")}
            </Link>
          </div>
        </section>

        <section id="pricing" className="border-t border-slate-800 bg-slate-950/50 px-4 py-16">
          <div className="mx-auto max-w-5xl">
            <h2 className="text-center text-2xl font-bold text-white">{t("pricing.title")}</h2>
            <p className="mt-2 text-center text-slate-400">{t("pricing.sub")}</p>
            <div className="mt-10 grid gap-6 md:grid-cols-3">
              {PLANS.map((plan) => (
                <div
                  key={plan.code}
                  className={
                    "card flex flex-col " +
                    (plan.highlighted ? "border-brand-500 ring-1 ring-brand-500/40" : "")
                  }
                >
                  <h3 className="text-lg font-semibold text-white">{t(plan.nameKey)}</h3>
                  <p className="mt-2 text-3xl font-bold text-brand-400">
                    {plan.price}
                    <span className="text-base font-normal text-slate-500">/mo</span>
                  </p>
                  <ul className="mt-4 flex-1 space-y-2 text-sm text-slate-400">
                    {plan.features.map((fk) => (
                      <li key={fk}>• {t(fk)}</li>
                    ))}
                  </ul>
                  <Link to="/register" className="btn-primary mt-6 w-full text-center text-sm">
                    {t("landing.cta")}
                  </Link>
                </div>
              ))}
            </div>
            <p className="mt-8 text-center text-xs text-slate-500">{t("pricing.note")}</p>
          </div>
        </section>

        <section id="contact" className="border-t border-slate-800 px-4 py-16">
          <div className="mx-auto max-w-xl">
            <h2 className="text-center text-2xl font-bold text-white">{t("contact.title")}</h2>
            <p className="mt-2 text-center text-slate-400">{t("contact.sub")}</p>
            <EnterpriseContactForm />
          </div>
        </section>

        <p className="mx-auto max-w-xl px-4 py-12 text-center text-xs text-slate-500">
          {t("landing.disclaimer")}
        </p>
      </main>
    </div>
  );
}
