// =============================================================================
// === frontend/lib/api/projects.ts ===
// =============================================================================
import api from "@/lib/api";

// ── Types ─────────────────────────────────────────────────────

export type ProjectStage =
  | "draft" | "perencanaan" | "perizinan" | "konstruksi"
  | "penjualan" | "serah_terima" | "selesai" | "ditunda";

export type PermitStatus = "belum" | "proses" | "approved" | "rejected";
export type RiskLevel    = "low" | "medium" | "high";
export type Trend        = "improving" | "stable" | "declining";
export type ReqStatus    = "pending" | "in_progress" | "completed" | "not_applicable";

export interface RequirementItem {
  id:             string;
  name:           string;
  description:    string;
  is_mandatory:   boolean;
  order:          number;
  status:         ReqStatus;
  status_display: string;
  notes:          string;
  completed_at:   string | null;
  status_id:      string | null;
}

export interface IntelligenceSummary {
  readiness_score:     number;
  blocking_count:      number;
  next_action:         string | null;
  risk_level:          RiskLevel;
  risk_level_display:  string;
  trend:               Trend;
  can_advance:         boolean;
  requirements:        RequirementItem[];
}

export interface StageChecklistItem {
  item:      string;
  done:      boolean;
  blocking?: boolean;
}

export interface Project {
  id:               string;
  name:             string;
  location:         string;
  description:      string;
  // Lifecycle
  stage:            ProjectStage;
  stage_display:    string;
  can_advance:      boolean;
  next_stage:       ProjectStage | null;
  stage_checklist:  StageChecklistItem[];
  // Intelligence
  readiness_score:     number;
  blocking_count:      number;
  next_action:         string | null;
  risk_level:          RiskLevel;
  risk_level_display:  string;
  trend:               Trend;
  // Planning
  total_units:      number;
  units_sold:       number;
  overall_progress: number;
  target_budget:    string | null;
  start_date:       string | null;
  end_date:         string | null;
  master_plan_url:  string;
  site_plan_url:    string;
  // Permits
  ipr_status:    PermitStatus;
  ipr_date:      string | null;
  amdal_status:  PermitStatus;
  amdal_date:    string | null;
  pbg_status:    PermitStatus;
  pbg_date:      string | null;
  // Meta
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
  name?:           string;
  location?:       string;
  description?:    string;
  total_units?:    number;
  target_budget?:  string;
  start_date?:     string;
  end_date?:       string;
  master_plan_url?: string;
  site_plan_url?:  string;
  ipr_status?:     PermitStatus;
  ipr_date?:       string;
  amdal_status?:   PermitStatus;
  amdal_date?:     string;
  pbg_status?:     PermitStatus;
  pbg_date?:       string;
}

// ── Stage metadata ────────────────────────────────────────────

export const STAGE_META: Record<ProjectStage, {
  label: string; color: string; bg: string; description: string; order: number;
}> = {
  draft:        { label: "Draft",        color: "var(--color-ink-3)",    bg: "var(--color-paper-2)",       description: "Ide proyek dibuat",              order: 0 },
  perencanaan:  { label: "Perencanaan",  color: "var(--color-info)",     bg: "var(--color-info-light)",    description: "Master plan & inventori unit",   order: 1 },
  perizinan:    { label: "Perizinan",    color: "var(--color-warning)",  bg: "var(--color-warning-light)", description: "IPR, AMDAL, PBG",               order: 2 },
  konstruksi:   { label: "Konstruksi",   color: "var(--color-accent)",   bg: "var(--color-accent-light)",  description: "Pembangunan berlangsung",        order: 3 },
  penjualan:    { label: "Penjualan",    color: "var(--color-success)",  bg: "var(--color-success-light)", description: "Unit dipasarkan & dijual",       order: 4 },
  serah_terima: { label: "Serah Terima", color: "#b8860b",               bg: "#fef9e7",                    description: "Unit diserahkan ke pembeli",     order: 5 },
  selesai:      { label: "Selesai",      color: "var(--color-success)",  bg: "var(--color-success-light)", description: "Proyek selesai",                order: 6 },
  ditunda:      { label: "Ditunda",      color: "var(--color-danger)",   bg: "var(--color-danger-light)",  description: "Proyek ditunda",                order: -1 },
};

export const RISK_META: Record<RiskLevel, { label: string; color: string; bg: string }> = {
  low:    { label: "Rendah",  color: "var(--color-success)", bg: "var(--color-success-light)" },
  medium: { label: "Sedang",  color: "var(--color-warning)", bg: "var(--color-warning-light)" },
  high:   { label: "Tinggi",  color: "var(--color-danger)",  bg: "var(--color-danger-light)"  },
};

export const TREND_META: Record<Trend, { icon: string; color: string }> = {
  improving: { icon: "↗", color: "var(--color-success)" },
  stable:    { icon: "→", color: "var(--color-ink-3)"   },
  declining: { icon: "↘", color: "var(--color-danger)"  },
};

// ── Derived stats ─────────────────────────────────────────────

export function deriveStats(projects: Project[]) {
  return {
    total_units:     projects.reduce((s, p) => s + p.total_units, 0),
    units_sold:      projects.reduce((s, p) => s + p.units_sold, 0),
    units_available: projects.reduce((s, p) => s + (p.total_units - p.units_sold), 0),
  };
}

// ── API calls ─────────────────────────────────────────────────

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
};
