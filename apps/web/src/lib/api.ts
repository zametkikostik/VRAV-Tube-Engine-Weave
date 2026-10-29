const API_BASE = import.meta.env.VITE_API_URL || "/api/v1";

export type TokenResponse = {
  access_token: string;
  refresh_token: string;
  token_type: string;
  expires_in: number;
};

export type UserPublic = {
  id: string;
  email: string;
  full_name: string | null;
  preferred_locale: string;
  is_active: boolean;
  is_email_verified: boolean;
  created_at: string;
};

export type OrganizationPublic = {
  id: string;
  name: string;
  slug: string;
  owner_user_id: string;
  billing_email: string | null;
  is_active: boolean;
  created_at: string;
};

class ApiError extends Error {
  constructor(
    public status: number,
    message: string,
  ) {
    super(message);
    this.name = "ApiError";
  }
}

function getTokens() {
  return {
    access: localStorage.getItem("access_token"),
    refresh: localStorage.getItem("refresh_token"),
  };
}

export function setTokens(tokens: TokenResponse) {
  localStorage.setItem("access_token", tokens.access_token);
  localStorage.setItem("refresh_token", tokens.refresh_token);
}

export function clearTokens() {
  localStorage.removeItem("access_token");
  localStorage.removeItem("refresh_token");
}

async function request<T>(
  path: string,
  options: RequestInit = {},
  auth = true,
): Promise<T> {
  const headers = new Headers(options.headers);
  if (!headers.has("Content-Type") && options.body) {
    headers.set("Content-Type", "application/json");
  }
  if (auth) {
    const { access } = getTokens();
    if (access) headers.set("Authorization", `Bearer ${access}`);
  }

  const res = await fetch(`${API_BASE}${path}`, { ...options, headers });

  if (res.status === 401 && auth) {
    const { refresh } = getTokens();
    if (refresh) {
      try {
        const refreshed = await request<TokenResponse>(
          "/auth/refresh",
          {
            method: "POST",
            body: JSON.stringify({ refresh_token: refresh }),
          },
          false,
        );
        setTokens(refreshed);
        headers.set("Authorization", `Bearer ${refreshed.access_token}`);
        const retry = await fetch(`${API_BASE}${path}`, { ...options, headers });
        if (!retry.ok) {
          const err = await retry.json().catch(() => ({ detail: retry.statusText }));
          throw new ApiError(retry.status, err.detail || "Request failed");
        }
        return retry.json();
      } catch {
        clearTokens();
        throw new ApiError(401, "Session expired");
      }
    }
  }

  if (!res.ok) {
    const err = await res.json().catch(() => ({ detail: res.statusText }));
    const detail = typeof err.detail === "string" ? err.detail : JSON.stringify(err.detail);
    throw new ApiError(res.status, detail || "Request failed");
  }

  if (res.status === 204) return undefined as T;
  return res.json();
}

export const api = {
  register: (body: {
    email: string;
    password: string;
    full_name?: string;
    preferred_locale?: string;
    organization_name?: string;
  }) =>
    request<TokenResponse>("/auth/register", {
      method: "POST",
      body: JSON.stringify(body),
    }, false),

  login: (email: string, password: string) =>
    request<TokenResponse>("/auth/login", {
      method: "POST",
      body: JSON.stringify({ email, password }),
    }, false),

  me: () => request<UserPublic>("/auth/me"),

  organizations: () => request<OrganizationPublic[]>("/organizations/me"),

  organizationTenants: (orgId: string) =>
    request<{ id: string; name: string; slug: string; organization_id: string }[]>(
      `/organizations/${orgId}/tenants`,
    ),

  createProject: (body: {
    name: string;
    description?: string;
    tenant_id: string;
    organization_id: string;
  }) =>
    request<{ id: string; name: string }>("/projects", {
      method: "POST",
      body: JSON.stringify(body),
    }),

  createVideo: (body: {
    project_id: string;
    source_type: string;
    youtube_url?: string;
    title?: string;
    description?: string;
    transcript_text?: string;
    language_code?: string;
  }) =>
    request<{ id: string; status: string; youtube_video_id?: string }>("/videos", {
      method: "POST",
      body: JSON.stringify(body),
    }),

  createAudit: (video_source_id: string) =>
    request<{ id: string; status: string; progress_percent: number }>("/audits", {
      method: "POST",
      body: JSON.stringify({ video_source_id }),
    }),

  getAudit: (jobId: string) =>
    request<{
      id: string;
      status: string;
      progress_percent: number;
      current_stage?: string;
      error_message?: string;
    }>(`/audits/${jobId}`),

  getAuditResult: (jobId: string) =>
    request<{
      job: { id: string; status: string; progress_percent: number; error_message?: string };
      result: {
        executive_summary?: string;
        confidence_notes?: string;
        model_info?: Record<string, unknown>;
        findings: Array<{
          id: string;
          category: string;
          severity: string;
          title: string;
          explanation?: string;
          recommendation?: string;
          confidence?: string;
          requires_human_review: boolean;
        }>;
        seo_recommendations: Array<{
          id: string;
          field: string;
          original_value?: string;
          proposed_value?: string;
          explanation?: string;
          confidence?: string;
          is_ai_hypothesis: boolean;
          status: string;
        }>;
        action_items: Array<{
          id: string;
          title: string;
          description?: string;
          priority: number;
          status: string;
        }>;
      };
    }>(`/audits/${jobId}/result`),

  getEntitlements: (orgId: string) =>
    request<{ plan_code: string; subscription_status: string; limits: Record<string, unknown> }>(
      `/billing/entitlements/${orgId}`,
    ),

  createCheckout: (body: {
    organization_id: string;
    plan_code: string;
    provider: string;
    currency: string;
    amount_cents: number;
    success_url: string;
    cancel_url: string;
    interval?: string;
  }) =>
    request<{ provider: string; session_id: string; checkout_url: string; note?: string }>(
      "/billing/checkout",
      { method: "POST", body: JSON.stringify(body) },
    ),

  submitContact: (body: {
    full_name: string;
    email: string;
    company?: string;
    message: string;
    locale?: string;
  }) => request<{ status: string; id: string }>("/contact", { method: "POST", body: JSON.stringify(body) }, false),

  adminStats: () =>
    request<{
      users: number;
      organizations: number;
      audit_jobs: number;
      active_subscriptions: number;
      contact_leads_new: number;
      ai_usage_records: number;
    }>("/admin/stats"),

  adminUsers: () =>
    request<
      Array<{
        id: string;
        email: string;
        full_name: string | null;
        is_active: boolean;
        is_superuser: boolean;
        preferred_locale: string;
      }>
    >("/admin/users"),

  adminLeads: () =>
    request<
      Array<{
        id: string;
        full_name: string;
        email: string;
        company: string | null;
        message: string;
        status: string;
      }>
    >("/admin/contact-leads"),

  health: () => request<{ status: string; version: string }>("/health", {}, false),
};

export { ApiError };
