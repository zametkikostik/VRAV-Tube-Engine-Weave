import { FormEvent, useEffect, useState } from "react";
import { Link, useNavigate } from "react-router-dom";
import { useTranslation } from "react-i18next";
import { useAuth } from "@/hooks/useAuth";
import { LanguageSwitcher } from "@/components/LanguageSwitcher";
import { api, ApiError, type OrganizationPublic } from "@/lib/api";

export function NewAudit() {
  const { t } = useTranslation();
  const { user, logout } = useAuth();
  const navigate = useNavigate();

  const [orgs, setOrgs] = useState<OrganizationPublic[]>([]);
  const [orgId, setOrgId] = useState("");
  const [tenantId, setTenantId] = useState("");
  const [youtubeUrl, setYoutubeUrl] = useState("");
  const [title, setTitle] = useState("");
  const [description, setDescription] = useState("");
  const [transcript, setTranscript] = useState("");
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    void api.organizations().then((list) => {
      setOrgs(list);
      if (list[0]) setOrgId(list[0].id);
    });
  }, []);

  useEffect(() => {
    if (!orgId) return;
    void api.organizationTenants(orgId).then((tenants) => {
      if (tenants[0]) setTenantId(tenants[0].id);
    });
  }, [orgId]);

  async function onSubmit(e: FormEvent) {
    e.preventDefault();
    setError("");
    if (!orgId || !tenantId) {
      setError("Organization / tenant required");
      return;
    }
    setLoading(true);
    try {
      const project = await api.createProject({
        name: title || youtubeUrl || "Untitled audit",
        organization_id: orgId,
        tenant_id: tenantId,
      });

      const sourceType = youtubeUrl
        ? "youtube_url"
        : transcript
          ? "transcript_upload"
          : "manual_metadata";

      const video = await api.createVideo({
        project_id: project.id,
        source_type: sourceType,
        youtube_url: youtubeUrl || undefined,
        title: title || undefined,
        description: description || undefined,
        transcript_text: transcript || undefined,
        language_code: user?.preferred_locale,
      });

      const job = await api.createAudit(video.id);
      navigate(`/audits/${job.id}`);
    } catch (err) {
      setError(err instanceof ApiError ? err.message : t("common.error"));
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="min-h-screen">
      <header className="border-b border-slate-800">
        <div className="mx-auto flex max-w-3xl items-center justify-between px-4 py-3">
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

      <main className="mx-auto max-w-3xl px-4 py-10">
        <h1 className="text-2xl font-bold text-white">{t("dashboard.create_audit")}</h1>
        <p className="mt-1 text-sm text-slate-400">
          YouTube URL, optional title/description/transcript. SEO & risk analysis.
        </p>

        <form onSubmit={onSubmit} className="mt-8 space-y-4">
          {orgs.length > 1 && (
            <div>
              <label className="label">Organization</label>
              <select
                className="input"
                value={orgId}
                onChange={(e) => setOrgId(e.target.value)}
              >
                {orgs.map((o) => (
                  <option key={o.id} value={o.id}>
                    {o.name}
                  </option>
                ))}
              </select>
            </div>
          )}

          <div>
            <label className="label" htmlFor="yt">
              YouTube URL
            </label>
            <input
              id="yt"
              className="input"
              placeholder="https://www.youtube.com/watch?v=..."
              value={youtubeUrl}
              onChange={(e) => setYoutubeUrl(e.target.value)}
            />
          </div>

          <div>
            <label className="label" htmlFor="title">
              Title (optional)
            </label>
            <input
              id="title"
              className="input"
              value={title}
              onChange={(e) => setTitle(e.target.value)}
            />
          </div>

          <div>
            <label className="label" htmlFor="desc">
              Description (optional)
            </label>
            <textarea
              id="desc"
              className="input min-h-[80px]"
              value={description}
              onChange={(e) => setDescription(e.target.value)}
            />
          </div>

          <div>
            <label className="label" htmlFor="tr">
              Transcript (optional)
            </label>
            <textarea
              id="tr"
              className="input min-h-[120px]"
              placeholder="Paste transcript for deeper content analysis"
              value={transcript}
              onChange={(e) => setTranscript(e.target.value)}
            />
          </div>

          {error && (
            <p className="text-sm text-red-400" role="alert">
              {error}
            </p>
          )}

          <div className="flex gap-3">
            <button type="submit" className="btn-primary" disabled={loading}>
              {loading ? t("common.loading") : t("dashboard.create_audit")}
            </button>
            <Link to="/dashboard" className="btn-secondary">
              {t("common.cancel")}
            </Link>
          </div>
        </form>
      </main>
    </div>
  );
}
