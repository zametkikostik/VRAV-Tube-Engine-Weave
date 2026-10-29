import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { useTranslation } from "react-i18next";
import { useAuth } from "@/hooks/useAuth";
import { LanguageSwitcher } from "@/components/LanguageSwitcher";
import { api, ApiError, type OrganizationPublic } from "@/lib/api";

const PLANS = [
  { code: "personal", name: "Personal", price: "$19/mo", audits: 20 },
  { code: "professional", name: "Professional", price: "$49/mo", audits: 100 },
  { code: "agency", name: "Agency", price: "$149/mo", audits: 500 },
] as const;

export function Billing() {
  const { t } = useTranslation();
  const { logout } = useAuth();
  const [orgs, setOrgs] = useState<OrganizationPublic[]>([]);
  const [orgId, setOrgId] = useState("");
  const [ents, setEnts] = useState<{
    plan_code: string;
    subscription_status: string;
    limits: Record<string, unknown>;
  } | null>(null);
  const [error, setError] = useState("");
  const [msg, setMsg] = useState("");

  useEffect(() => {
    void api.organizations().then((list) => {
      setOrgs(list);
      if (list[0]) setOrgId(list[0].id);
    });
  }, []);

  useEffect(() => {
    if (!orgId) return;
    void api
      .getEntitlements(orgId)
      .then(setEnts)
      .catch(() => setEnts(null));
  }, [orgId]);

  async function startCheckout(planCode: string, amountCents: number) {
    setError("");
    setMsg("");
    if (!orgId) return;
    try {
      const session = await api.createCheckout({
        organization_id: orgId,
        plan_code: planCode,
        provider: "stripe",
        currency: "usd",
        amount_cents: amountCents,
        success_url: `${window.location.origin}/dashboard?billing=success`,
        cancel_url: `${window.location.origin}/billing?billing=cancel`,
        interval: "month",
      });
      if (session.checkout_url) {
        window.location.href = session.checkout_url;
      } else {
        setMsg(JSON.stringify(session));
      }
    } catch (err) {
      setError(err instanceof ApiError ? err.message : t("common.error"));
    }
  }

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
        <h1 className="text-2xl font-bold text-white">Billing</h1>
        <p className="mt-1 text-sm text-slate-400">
          Entitlements activate only after a verified payment webhook — not after the success URL.
        </p>

        {orgs.length > 1 && (
          <div className="mt-4">
            <label className="label">Organization</label>
            <select className="input max-w-md" value={orgId} onChange={(e) => setOrgId(e.target.value)}>
              {orgs.map((o) => (
                <option key={o.id} value={o.id}>
                  {o.name}
                </option>
              ))}
            </select>
          </div>
        )}

        {ents && (
          <div className="card mt-6">
            <p className="text-slate-300">
              Current plan: <span className="text-brand-400">{ents.plan_code}</span> · Status:{" "}
              {ents.subscription_status}
            </p>
            <p className="mt-1 text-sm text-slate-500">
              Audits / month: {String(ents.limits.audits_per_month ?? "—")}
            </p>
          </div>
        )}

        <div className="mt-8 grid gap-4 md:grid-cols-3">
          {PLANS.map((p) => (
            <div key={p.code} className="card flex flex-col">
              <h2 className="font-semibold text-white">{p.name}</h2>
              <p className="mt-1 text-2xl text-brand-400">{p.price}</p>
              <p className="mt-2 text-sm text-slate-400">{p.audits} audits / month</p>
              <button
                type="button"
                className="btn-primary mt-auto pt-4"
                onClick={() =>
                  startCheckout(
                    p.code,
                    p.code === "personal" ? 1900 : p.code === "professional" ? 4900 : 14900,
                  )
                }
              >
                Checkout (Stripe)
              </button>
            </div>
          ))}
        </div>

        {error && (
          <p className="mt-4 text-sm text-red-400" role="alert">
            {error}
          </p>
        )}
        {msg && <p className="mt-4 text-sm text-slate-400">{msg}</p>}
      </main>
    </div>
  );
}
