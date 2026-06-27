// =============================================================================
// === frontend/lib/api/projects.ts ===
// Sprint 2: adds RequirementEvidence types + evidenceApi calls
// All Sprint 1 types preserved — additive only.
// =============================================================================
import api from "@/lib/api";

// ── Existing types — UNCHANGED ────────────────────────────────

export type ProjectStage =
  | "draft" | "perencanaan" | "perizinan" | "konstruksi"
  | "penjualan" | "serah_terima" | "selesai" | "ditunda";

export type PermitStatus = "belum" | "proses" | "approved" | "rejected";
export type RiskLevel    = "low" | "medium" | "high";
export type Trend        = "improving" | "stable" | "declining";

// Sprint 2: menunggu_verifikasi added
export type ReqStatus =
  | "pending"
  | "in_progress"
  | "menunggu_verifikasi"   // ← Sprint 2
  | "completed"
  | "not_applicable";

export type AlertLevel           = "critical" | "warning" | "info";
export type EvidenceVerifStatus  = "pending" | "approved" | "rejected";  // Sprint 2

// ── Sprint 1 types — UNCHANGED ────────────────────────────────

export interface ReadinessDimensions {
  inventory:   number;
  compliance:  number;
  site_plan:   number;
  sales_setup: number;
  general:     number;
}

export interface Alert {
  level:    AlertLevel;
  category: string;
  message:  string;
  action:   string;
}

export interface ParallelStages {
  is_selling:      boolean;
  is_constructing: boolean;
  label_5a:        string;
  label_5b:        string;
  can_sell_now:    boolean;
}

export interface CollectionEfficiency {
  total_billed:   number;
  total_settled:  number;
  total_arrears:  number;
  efficiency_pct: number;
  status:         "healthy" | "attention" | "critical";
  status_display: string;
}

// ── Sprint 2: NEW types ───────────────────────────────────────

export interface RequirementEvidence {
  id:                   string;
  file_name:            string;
  file_url:             string;
  file_url_display:     string;   // resolved download URL
  notes:                string;
  uploaded_by:          string;
  uploaded_by_name:     string;
  uploaded_at:          string;
  verification_status:  EvidenceVerifStatus;
  verification_display: string;
  verifier:             string | null;
  verifier_name:        string;
  verified_at:          string | null;
  verifier_notes:       string;
}

// ── RequirementItem — Sprint 2: adds evidence fields ─────────

export interface RequirementItem {
  id:             string;
  name:           string;
  description:    string;
  is_mandatory:   boolean;
  order:          number;
  category:       string;
  status:         ReqStatus;
  status_display: string;
  notes:          string;
  completed_at:   string | null;
  status_id:      string | null;
  // Sprint 2: evidence
  evidence_count:         number;
  latest_evidence_status: EvidenceVerifStatus | null;
  has_pending_evidence:   boolean;
}

// ── IntelligenceSummary — UNCHANGED ──────────────────────────

export interface IntelligenceSummary {
  readiness_score:    number;
  blocking_count:     number;
  next_action:        string | null;
  risk_level:         RiskLevel;
  risk_level_display: string;
  trend:              Trend;
  can_advance:        boolean;
  requirements:       RequirementItem[];
  readiness_dimensions:  ReadinessDimensions;
  risk_reasons:          string[];
  alerts:                Alert[];
  parallel_stages:       ParallelStages;
  collection_efficiency: CollectionEfficiency;
}

export interface StageChecklistItem {
  item:      string;
  done:      boolean;
  blocking?: boolean;
}

// ── Project — UNCHANGED ───────────────────────────────────────

export interface Project {
  id:               string;
  name:             string;
  location:         string;
  description:      string;
  stage:            ProjectStage;
  stage_display:    string;
  can_advance:      boolean;
  next_stage:       ProjectStage | null;
  stage_checklist:  StageChecklistItem[];
  readiness_score:    number;
  blocking_count:     number;
  next_action:        string | null;
  risk_level:         RiskLevel;
  risk_level_display: string;
  trend:              Trend;
  readiness_dimensions:  ReadinessDimensions;
  risk_reasons:          string[];
  alerts:                Alert[];
  parallel_stages:       ParallelStages;
  collection_efficiency: CollectionEfficiency;
  is_selling:      boolean;
  is_constructing: boolean;
  total_units:      number;
  units_sold:       number;
  overall_progress: number;
  target_budget:    string | null;
  start_date:       string | null;
  end_date:         string | null;
  master_plan_url:  string;
  site_plan_url:    string;
  ipr_status:    PermitStatus;
  ipr_date:      string | null;
  amdal_status:  PermitStatus;
  amdal_date:    string | null;
  pbg_status:    PermitStatus;
  pbg_date:      string | null;
  organization_name: string;
  created_at:        string;
  updated_at:        string;
}

export interface PortfolioRow {
  id:                  string;
  name:                string;
  location:            string;
  stage:               ProjectStage;
  stage_display:       string;
  readiness_score:     number;
  blocking_count:      number;
  next_action:         string | null;
  risk_level:          RiskLevel;
  risk_level_display:  string;
  trend:               Trend;
  overall_progress:    number;
  total_units:         number;
  units_sold:          number;
}

export interface CreateProjectPayload {
  name:         string;
  location:     string;
  description?: string;
}

export interface UpdateProjectPayload {
  name?:            string;
  location?:        string;
  description?:     string;
  total_units?:     number;
  target_budget?:   string;
  start_date?:      string;
  end_date?:        string;
  master_plan_url?: string;
  site_plan_url?:   string;
  ipr_status?:      PermitStatus;
  ipr_date?:        string;
  amdal_status?:    PermitStatus;
  amdal_date?:      string;
  pbg_status?:      PermitStatus;
  pbg_date?:        string;
  is_selling?:      boolean;
  is_constructing?: boolean;
}

// Sprint 3 types — add to projects.ts

export interface ActivityItem {
  id:        string;
  type:      string;
  action:    string;
  actor:     string;
  actor_id:  string | null;
  subject:   string;
  message:   string;
  notes:     string;
  old_value: string;
  new_value: string;
  timestamp: string;
}

export interface OverdueItem {
  id:           string;
  unit_number:  string;
  buyer_name:   string;
  payment_type: string;
  amount:       number;
  due_date:     string;
  days_overdue: number;
}

export interface UpcomingItem {
  id:           string;
  unit_number:  string;
  buyer_name:   string;
  payment_type: string;
  amount:       number;
  due_date:     string;
  days_until:   number;
}

export interface FinancialSnapshot {
  has_data:        boolean;
  total_billed:    number;
  total_lunas:     number;
  total_menunggak: number;
  total_upcoming:  number;
  efficiency_pct:  number;
  status:          "healthy" | "attention" | "critical";
  status_display:  string;
  overdue_items:   OverdueItem[];
  upcoming_items:  UpcomingItem[];
}

// ── Metadata — UNCHANGED ──────────────────────────────────────

export const STAGE_META: Record<ProjectStage, {
  label: string; color: string; bg: string; description: string; order: number;
}> = {
  draft:        { label: "Draft",        color: "var(--color-ink-3)",    bg: "var(--color-paper-2)",       description: "Ide proyek dibuat",            order: 0  },
  perencanaan:  { label: "Perencanaan",  color: "var(--color-info)",     bg: "var(--color-info-light)",    description: "Master plan & inventori unit", order: 1  },
  perizinan:    { label: "Perizinan",    color: "var(--color-warning)",  bg: "var(--color-warning-light)", description: "IPR, AMDAL, PBG",             order: 2  },
  konstruksi:   { label: "Konstruksi",   color: "var(--color-accent)",   bg: "var(--color-accent-light)",  description: "Pembangunan berlangsung",      order: 3  },
  penjualan:    { label: "Penjualan",    color: "var(--color-success)",  bg: "var(--color-success-light)", description: "Unit dipasarkan & dijual",     order: 4  },
  serah_terima: { label: "Serah Terima", color: "#b8860b",               bg: "#fef9e7",                    description: "Unit diserahkan ke pembeli",   order: 5  },
  selesai:      { label: "Selesai",      color: "var(--color-success)",  bg: "var(--color-success-light)", description: "Proyek selesai",               order: 6  },
  ditunda:      { label: "Ditunda",      color: "var(--color-danger)",   bg: "var(--color-danger-light)",  description: "Proyek ditunda",               order: -1 },
};

export const RISK_META: Record<RiskLevel, { label: string; color: string; bg: string }> = {
  low:    { label: "Rendah", color: "var(--color-success)", bg: "var(--color-success-light)" },
  medium: { label: "Sedang", color: "var(--color-warning)", bg: "var(--color-warning-light)" },
  high:   { label: "Tinggi", color: "var(--color-danger)",  bg: "var(--color-danger-light)"  },
};

export const TREND_META: Record<Trend, { icon: string; color: string }> = {
  improving: { icon: "↗", color: "var(--color-success)" },
  stable:    { icon: "→", color: "var(--color-ink-3)"   },
  declining: { icon: "↘", color: "var(--color-danger)"  },
};

export const ALERT_META: Record<AlertLevel, { color: string; bg: string; border: string }> = {
  critical: { color: "var(--color-danger)",  bg: "var(--color-danger-light)",  border: "rgba(220,38,38,0.2)"  },
  warning:  { color: "var(--color-warning)", bg: "var(--color-warning-light)", border: "rgba(234,179,8,0.2)"  },
  info:     { color: "var(--color-info)",    bg: "var(--color-info-light)",    border: "rgba(59,130,246,0.2)" },
};

// Sprint 2: evidence verification status colors
export const EVIDENCE_META: Record<EvidenceVerifStatus, { label: string; color: string; bg: string }> = {
  pending:  { label: "Menunggu Review", color: "var(--color-warning)", bg: "var(--color-warning-light)" },
  approved: { label: "Disetujui ✓",    color: "var(--color-success)", bg: "var(--color-success-light)" },
  rejected: { label: "Ditolak",        color: "var(--color-danger)",  bg: "var(--color-danger-light)"  },
};

// ── Derived stats — UNCHANGED ─────────────────────────────────

export function deriveStats(projects: Project[]) {
  return {
    total_units:     projects.reduce((s, p) => s + p.total_units, 0),
    units_sold:      projects.reduce((s, p) => s + p.units_sold, 0),
    units_available: projects.reduce((s, p) => s + (p.total_units - p.units_sold), 0),
  };
}

// ── API calls — Sprint 2: adds evidenceApi ────────────────────

export const projectsApi = {
  async list(stage?: ProjectStage): Promise<Project[]> {
    const params = stage ? `?stage=${stage}` : "";
    const { data } = await api.get(`/api/projects/${params}`);
    return data.results;
  },

  async get(id: string): Promise<Project> {
    const { data } = await api.get(`/api/projects/${id}/`);
    return data.project;
  },

  async create(payload: CreateProjectPayload): Promise<Project> {
    const { data } = await api.post("/api/projects/", payload);
    return data.project;
  },

  async update(id: string, payload: UpdateProjectPayload): Promise<Project> {
    const { data } = await api.put(`/api/projects/${id}/`, payload);
    return data.project;
  },

  async advance(id: string): Promise<Project> {
    const { data } = await api.post(`/api/projects/${id}/advance/`, { confirm: true });
    return data.project;
  },

  async delete(id: string): Promise<void> {
    await api.delete(`/api/projects/${id}/`);
  },

  async getIntelligence(id: string): Promise<IntelligenceSummary> {
    const { data } = await api.get(`/api/projects/${id}/intelligence/`);
    return data.intelligence;
  },

  async updateRequirement(
    projectId: string,
    reqStatusId: string,
    payload: { status: ReqStatus; notes?: string }
  ): Promise<IntelligenceSummary> {
    const { data } = await api.put(
      `/api/projects/${projectId}/requirements/${reqStatusId}/`,
      payload
    );
    return data.intelligence;
  },

  async getPortfolio(): Promise<PortfolioRow[]> {
    const { data } = await api.get("/api/projects/portfolio/");
    return data.results;
  },

  async toggleSelling(id: string, active: boolean): Promise<Project> {
    const { data } = await api.put(`/api/projects/${id}/`, { is_selling: active });
    return data.project;
  },

  async toggleConstructing(id: string, active: boolean): Promise<Project> {
    const { data } = await api.put(`/api/projects/${id}/`, { is_constructing: active });
    return data.project;
  },

  async getActivity(id: string, limit = 20): Promise<ActivityItem[]> {
  const { data } = await api.get(
    `/api/projects/${id}/activity/?limit=${limit}`
  );
  return data.results;
  },

  async getFinancial(id: string): Promise<FinancialSnapshot> {
  const { data } = await api.get(`/api/projects/${id}/financial/`);
  return data.financial;
  },
};

// Sprint 2: evidence API calls
export const evidenceApi = {
  async list(
    projectId: string,
    reqStatusId: string
  ): Promise<{ count: number; results: RequirementEvidence[] }> {
    const { data } = await api.get(
      `/api/projects/${projectId}/requirements/${reqStatusId}/evidence/`
    );
    return { count: data.count, results: data.results };
  },

  async upload(
    projectId: string,
    reqStatusId: string,
    payload: { file?: File; file_url?: string; notes?: string }
  ): Promise<{ evidence: RequirementEvidence; intelligence: IntelligenceSummary }> {
    const formData = new FormData();
    if (payload.file)     formData.append("file",     payload.file);
    if (payload.file_url) formData.append("file_url", payload.file_url);
    if (payload.notes)    formData.append("notes",    payload.notes);

    const { data } = await api.post(
      `/api/projects/${projectId}/requirements/${reqStatusId}/evidence/`,
      formData,
      { headers: { "Content-Type": "multipart/form-data" } }
    );
    return { evidence: data.evidence, intelligence: data.intelligence };
  },

  async verify(
    projectId: string,
    reqStatusId: string,
    evidenceId: string,
    action: "approve" | "reject",
    notes?: string
  ): Promise<{ evidence: RequirementEvidence; intelligence: IntelligenceSummary }> {
    const { data } = await api.put(
      `/api/projects/${projectId}/requirements/${reqStatusId}/evidence/${evidenceId}/verify/`,
      { action, notes: notes ?? "" }
    );
    return { evidence: data.evidence, intelligence: data.intelligence };
  },
};
