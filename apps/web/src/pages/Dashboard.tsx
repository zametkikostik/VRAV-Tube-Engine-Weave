import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { useTranslation } from "react-i18next";
import { useAuth } from "@/hooks/useAuth";
import { LanguageSwitcher } from "@/components/LanguageSwitcher";
import { api, type OrganizationPublic } from "@/lib/api";

export function Dashboard() {
  const { t } = useTranslation();
  const { user, logout } = useAuth();
  const [orgs, setOrgs] = useState<OrganizationPublic[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    void api
      .organizations()
      .then(setOrgs)
      .catch(() => setOrgs([]))
      .finally(() => setLoading(false));
  }, []);

  const displayName = user?.full_name || user?.email || "";

  return (
    <div className="min-h-screen">
      <header className="border-b border-slate-800 bg-slate-950/80 backdrop-blur">
        <div className="mx-auto flex max-w-6xl items-center justify-between px-4 py-3">
          <Link to="/dashboard" className="text-lg font-semibold text-white">
            {t("app_name")}
          </Link>
          <nav className="flex items-center gap-4">
            <LanguageSwitcher />
            <span className="hidden text-sm text-slate-400 sm:inline">{user?.email}</span>
            <button type="button" onClick={logout} className="btn-secondary text-sm">
              {t("nav.logout")}
            </button>
          </nav>
        </div>
      </header>

      <main className="mx-auto max-w-6xl px-4 py-10">
        <h1 className="text-2xl font-bold text-white">{t("dashboard.title")}</h1>
        <p className="mt-1 text-slate-400">{t("dashboard.welcome", { name: displayName })}</p>

        <section className="mt-10">
          <h2 className="text-lg font-medium text-slate-200">{t("dashboard.orgs")}</h2>
          {loading ? (
            <p className="mt-4 text-slate-500">{t("common.loading")}</p>
          ) : orgs.length === 0 ? (
            <p className="mt-4 text-slate-500">{t("dashboard.no_orgs")}</p>
          ) : (
            <ul className="mt-4 grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
              {orgs.map((org) => (
                <li key={org.id} className="card">
                  <h3 className="font-medium text-white">{org.name}</h3>
                  <p className="mt-1 text-sm text-slate-400">@{org.slug}</p>
                </li>
              ))}
            </ul>
          )}
        </section>

        <section className="mt-6">
          <Link to="/billing" className="card block border-slate-700 bg-slate-900/40 transition hover:border-brand-600">
            <h2 className="font-medium text-slate-200">Billing & plans</h2>
            <p className="mt-2 text-sm text-slate-500">Personal · Professional · Agency</p>
          </Link>
        </section>

        <section className="mt-12">
          <Link to="/audits/new" className="card block border-brand-800/50 bg-slate-900/40 transition hover:border-brand-600">
            <h2 className="font-medium text-slate-200">{t("dashboard.create_audit")}</h2>
            <p className="mt-2 text-sm text-slate-500">YouTube URL · transcript · SEO & risk analysis</p>
          </Link>
        </section>
      </main>
    </div>
  );
}
