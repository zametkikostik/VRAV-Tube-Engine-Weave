import { useCallback, useEffect, useState } from "react";
import { Link, useParams } from "react-router-dom";
import { useTranslation } from "react-i18next";
import { useAuth } from "@/hooks/useAuth";
import { LanguageSwitcher } from "@/components/LanguageSwitcher";
import { api } from "@/lib/api";

type ResultPayload = Awaited<ReturnType<typeof api.getAuditResult>>;

export function AuditReport() {
  const { jobId } = useParams<{ jobId: string }>();
  const { t } = useTranslation();
  const { logout } = useAuth();
  const [data, setData] = useState<ResultPayload | null>(null);
  const [status, setStatus] = useState<string>("loading");
  const [progress, setProgress] = useState(0);
  const [error, setError] = useState("");

  const poll = useCallback(async () => {
    if (!jobId) return;
    try {
      const job = await api.getAudit(jobId);
      setStatus(job.status);
      setProgress(job.progress_percent);
      if (job.status === "SUCCEEDED") {
        const full = await api.getAuditResult(jobId);
        setData(full);
      } else if (job.status === "FAILED") {
        setError(job.error_message || "Audit failed");
      }
    } catch (e) {
      setError(e instanceof Error ? e.message : "Error");
    }
  }, [jobId]);

  useEffect(() => {
    void poll();
    const id = setInterval(() => {
      if (status === "SUCCEEDED" || status === "FAILED") return;
      void poll();
    }, 2000);
    return () => clearInterval(id);
  }, [poll, status]);

  const result = data?.result;

  return (
    <div className="min-h-screen">
      <header className="border-b border-slate-800">
        <div className="mx-auto flex max-w-4xl items-center justify-between px-4 py-3">
          <Link to="/dashboard" className="text-lg font-semibold text-white">
            {t("app_name")}
          </Link>
          <div className="flex items-center gap-3">
            <LanguageSwitcher />
            <button type="button" onClick={logout} className="btn-secondary text-sm">
              {t("nav.logout")}
            </button>
          </div>
        </div>
      </header>

      <main className="mx-auto max-w-4xl px-4 py-10">
        <h1 className="text-2xl font-bold text-white">Audit report</h1>
        <p className="mt-1 text-sm text-slate-400">
          Status: <span className="text-brand-400">{status}</span> · {progress}%
        </p>

        {status !== "SUCCEEDED" && status !== "FAILED" && (
          <div className="card mt-6">
            <p className="text-slate-300">{t("common.loading")}</p>
            <div className="mt-3 h-2 overflow-hidden rounded bg-slate-800">
              <div
                className="h-full bg-brand-500 transition-all"
                style={{ width: `${progress}%` }}
              />
            </div>
          </div>
        )}

        {error && (
          <div className="card mt-6 border-red-900/50">
            <p className="text-red-400">{error}</p>
          </div>
        )}

        {result && (
          <div className="mt-8 space-y-8">
            <section className="card">
              <h2 className="font-semibold text-white">Executive summary</h2>
              <p className="mt-3 whitespace-pre-wrap text-slate-300">
                {result.executive_summary || "—"}
              </p>
              {result.confidence_notes && (
                <p className="mt-4 text-xs text-slate-500">{result.confidence_notes}</p>
              )}
              {result.model_info && (
                <p className="mt-2 text-xs text-slate-600">
                  Mode: {String(result.model_info.mode || result.model_info.provider || "n/a")}
                </p>
              )}
            </section>

            <section>
              <h2 className="text-lg font-medium text-white">Findings</h2>
              <ul className="mt-3 space-y-3">
                {result.findings.map((f) => (
                  <li key={f.id} className="card">
                    <div className="flex items-start justify-between gap-2">
                      <h3 className="font-medium text-slate-100">{f.title}</h3>
                      <span
                        className={`shrink-0 rounded px-2 py-0.5 text-xs font-medium ${
                          f.severity === "CRITICAL" || f.severity === "HIGH"
                            ? "bg-red-900/50 text-red-300"
                            : f.severity === "MEDIUM"
                              ? "bg-amber-900/50 text-amber-300"
                              : "bg-slate-800 text-slate-400"
                        }`}
                      >
                        {f.severity}
                      </span>
                    </div>
                    <p className="mt-2 text-sm text-slate-400">{f.explanation}</p>
                    {f.recommendation && (
                      <p className="mt-2 text-sm text-brand-300">→ {f.recommendation}</p>
                    )}
                  </li>
                ))}
              </ul>
            </section>

            <section>
              <h2 className="text-lg font-medium text-white">SEO recommendations</h2>
              <ul className="mt-3 space-y-3">
                {result.seo_recommendations.map((s) => (
                  <li key={s.id} className="card">
                    <p className="text-xs uppercase tracking-wide text-slate-500">{s.field}</p>
                    {s.proposed_value && (
                      <p className="mt-1 text-slate-200">{s.proposed_value}</p>
                    )}
                    {s.explanation && (
                      <p className="mt-2 text-sm text-slate-400">{s.explanation}</p>
                    )}
                    {s.is_ai_hypothesis && (
                      <p className="mt-2 text-xs text-amber-600/80">AI hypothesis — human review required</p>
                    )}
                  </li>
                ))}
                {result.seo_recommendations.length === 0 && (
                  <p className="text-sm text-slate-500">No SEO items</p>
                )}
              </ul>
            </section>

            <section>
              <h2 className="text-lg font-medium text-white">Action plan</h2>
              <ul className="mt-3 space-y-2">
                {result.action_items.map((a) => (
                  <li key={a.id} className="flex gap-3 rounded-lg border border-slate-800 px-4 py-3">
                    <span className="text-brand-400">P{a.priority}</span>
                    <div>
                      <p className="text-slate-200">{a.title}</p>
                      {a.description && (
                        <p className="text-sm text-slate-500">{a.description}</p>
                      )}
                    </div>
                  </li>
                ))}
              </ul>
            </section>

            <p className="mt-4 flex flex-wrap gap-3">
              <a
                className="btn-secondary text-sm"
                href={`/api/v1/audits/${jobId}/report.html`}
                target="_blank"
                rel="noreferrer"
              >
                Export HTML report
              </a>
              <a
                className="btn-secondary text-sm"
                href={`/api/v1/audits/${jobId}/report.pdf`}
                target="_blank"
                rel="noreferrer"
              >
                Export PDF
              </a>
            </p>

            <p className="text-xs text-slate-600">
              This report is an advisory risk assessment. It does not establish YouTube monetization
              status, guarantee approval, or replace professional legal advice. Not affiliated with
              YouTube or Google.
            </p>
          </div>
        )}
      </main>
    </div>
  );
}
