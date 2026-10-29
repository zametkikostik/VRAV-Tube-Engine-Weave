import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { useTranslation } from "react-i18next";
import { useAuth } from "@/hooks/useAuth";
import { LanguageSwitcher } from "@/components/LanguageSwitcher";
import { api, ApiError } from "@/lib/api";

export function Admin() {
  const { t } = useTranslation();
  const { logout } = useAuth();
  const [stats, setStats] = useState<Record<string, number> | null>(null);
  const [users, setUsers] = useState<
    Array<{ id: string; email: string; full_name: string | null; is_superuser: boolean }>
  >([]);
  const [leads, setLeads] = useState<
    Array<{ id: string; full_name: string; email: string; company: string | null; message: string; status: string }>
  >([]);
  const [error, setError] = useState("");

  useEffect(() => {
    void (async () => {
      try {
        const [s, u, l] = await Promise.all([
          api.adminStats(),
          api.adminUsers(),
          api.adminLeads(),
        ]);
        setStats(s as unknown as Record<string, number>);
        setUsers(u);
        setLeads(l);
      } catch (err) {
        setError(err instanceof ApiError ? err.message : t("common.error"));
      }
    })();
  }, [t]);

  return (
    <div className="min-h-screen">
      <header className="border-b border-slate-800">
        <div className="mx-auto flex max-w-5xl items-center justify-between px-4 py-3">
          <Link to="/dashboard" className="text-lg font-semibold text-white">
            {t("app_name")} · Admin
          </Link>
          <div className="flex items-center gap-3">
            <LanguageSwitcher />
            <button type="button" onClick={logout} className="btn-secondary text-sm">
              {t("nav.logout")}
            </button>
          </div>
        </div>
      </header>

      <main className="mx-auto max-w-5xl px-4 py-10">
        {error && (
          <p className="mb-4 text-sm text-red-400" role="alert">
            {error}
          </p>
        )}

        {stats && (
          <div className="grid gap-3 sm:grid-cols-3">
            {Object.entries(stats).map(([k, v]) => (
              <div key={k} className="card">
                <p className="text-xs uppercase tracking-wide text-slate-500">{k.replace(/_/g, " ")}</p>
                <p className="mt-1 text-2xl font-semibold text-white">{v}</p>
              </div>
            ))}
          </div>
        )}

        <h2 className="mt-10 text-lg font-semibold text-white">Users</h2>
        <div className="mt-3 overflow-x-auto rounded-lg border border-slate-800">
          <table className="w-full text-left text-sm">
            <thead className="bg-slate-900 text-slate-400">
              <tr>
                <th className="px-3 py-2">Email</th>
                <th className="px-3 py-2">Name</th>
                <th className="px-3 py-2">Superuser</th>
              </tr>
            </thead>
            <tbody>
              {users.map((u) => (
                <tr key={u.id} className="border-t border-slate-800 text-slate-300">
                  <td className="px-3 py-2">{u.email}</td>
                  <td className="px-3 py-2">{u.full_name || "—"}</td>
                  <td className="px-3 py-2">{u.is_superuser ? "yes" : "no"}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>

        <h2 className="mt-10 text-lg font-semibold text-white">Enterprise leads</h2>
        <div className="mt-3 space-y-3">
          {leads.length === 0 && <p className="text-sm text-slate-500">No leads yet</p>}
          {leads.map((l) => (
            <div key={l.id} className="card">
              <p className="font-medium text-white">
                {l.full_name} · {l.email}
                {l.company ? ` · ${l.company}` : ""}
              </p>
              <p className="mt-1 text-sm text-slate-400">{l.message}</p>
              <p className="mt-1 text-xs text-slate-600">{l.status}</p>
            </div>
          ))}
        </div>
      </main>
    </div>
  );
}
