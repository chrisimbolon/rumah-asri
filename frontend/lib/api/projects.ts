// =============================================================================
// === frontend/lib/api/projects.ts ===
// Sprint 1: adds ReadinessDimensions, Alert, ParallelStages,
// CollectionEfficiency types + new fields on Project & IntelligenceSummary.
// BACKWARD COMPATIBLE — all original fields preserved.
// =============================================================================
import api from "@/lib/api";

// ── Existing types — UNCHANGED ────────────────────────────────

export type ProjectStage =
  | "draft" | "perencanaan" | "perizinan" | "konstruksi"
  | "penjualan" | "serah_terima" | "selesai" | "ditunda";

export type PermitStatus = "belum" | "proses" | "approved" | "rejected";
export type RiskLevel    = "low" | "medium" | "high";
export type Trend        = "improving" | "stable" | "declining";
export type ReqStatus    = "pending" | "in_progress" | "completed" | "not_applicable";

// ── Sprint 1: new types ───────────────────────────────────────

export type AlertLevel = "critical" | "warning" | "info";

export interface ReadinessDimensions {
  inventory:   number;  // % of inventory requirements completed
  compliance:  number;  // % of compliance requirements completed
  site_plan:   number;  // % of site plan requirements completed
  sales_setup: number;  // % of sales setup requirements completed
  general:     number;  // % of general requirements completed
}

export interface Alert {
  level:    AlertLevel;
  category: string;   // "permit" | "requirement" | "timeline" | "financial" | "inventory" | "sales"
  message:  string;   // human-readable alert message
  action:   string;   // what to do about it
}

export interface ParallelStages {
  is_selling:      boolean;  // 5A — actively selling units
  is_constructing: boolean;  // 5B — construction underway
  label_5a:        string;   // "Aktif Penjualan" | "Belum Dipasarkan"
  label_5b:        string;   // "Aktif Konstruksi" | "Belum Konstruksi"
  can_sell_now:    boolean;  // whether selling is allowed at current stage
}

export interface CollectionEfficiency {
  total_billed:   number;  // total AR (Rp)
  total_settled:  number;  // total lunas (Rp)
  total_arrears:  number;  // total menunggak (Rp)
  efficiency_pct: number;  // collection efficiency %
  status:         "healthy" | "attention" | "critical";
  status_display: string;  // "Sehat" | "Perlu Perhatian" | "Kritis"
}

// ── RequirementItem — Sprint 1: adds category field ──────────

export interface RequirementItem {
  id:             string;
  name:           string;
  description:    string;
  is_mandatory:   boolean;
  order:          number;
  category:       string;  // Sprint 1: "inventory" | "compliance" | etc.
  status:         ReqStatus;
  status_display: string;
  notes:          string;
  completed_at:   string | null;
  status_id:      string | null;
}

// ── IntelligenceSummary — Sprint 1: new fields added ─────────

export interface IntelligenceSummary {
  // Original fields — UNCHANGED
  readiness_score:    number;
  blocking_count:     number;
  next_action:        string | null;
  risk_level:         RiskLevel;
  risk_level_display: string;
  trend:              Trend;
  can_advance:        boolean;
  requirements:       RequirementItem[];

  // Sprint 1: new fields
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

// ── Project — Sprint 1: new fields added ─────────────────────

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
  // Original intelligence
  readiness_score:    number;
  blocking_count:     number;
  next_action:        string | null;
  risk_level:         RiskLevel;
  risk_level_display: string;
  trend:              Trend;
  // Sprint 1 intelligence
  readiness_dimensions:  ReadinessDimensions;
  risk_reasons:          string[];
  alerts:                Alert[];
  parallel_stages:       ParallelStages;
  collection_efficiency: CollectionEfficiency;
  // Sprint 1 parallel flags
  is_selling:      boolean;
  is_constructing: boolean;
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
  // Sprint 1: parallel stage flags
  is_selling?:      boolean;
  is_constructing?: boolean;
}

// ── Stage metadata — UNCHANGED ────────────────────────────────

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

// Sprint 1: alert level metadata
export const ALERT_META: Record<AlertLevel, { color: string; bg: string; border: string }> = {
  critical: { color: "var(--color-danger)",  bg: "var(--color-danger-light)",  border: "rgba(220,38,38,0.2)"  },
  warning:  { color: "var(--color-warning)", bg: "var(--color-warning-light)", border: "rgba(234,179,8,0.2)"  },
  info:     { color: "var(--color-info)",    bg: "var(--color-info-light)",    border: "rgba(59,130,246,0.2)" },
};

// ── Derived stats — UNCHANGED ─────────────────────────────────

export function deriveStats(projects: Project[]) {
  return {
    total_units:     projects.reduce((s, p) => s + p.total_units, 0),
    units_sold:      projects.reduce((s, p) => s + p.units_sold, 0),
    units_available: projects.reduce((s, p) => s + (p.total_units - p.units_sold), 0),
  };
}

// ── API calls — Sprint 1: adds toggleSelling, toggleConstructing ──

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

  // Sprint 1: toggle parallel stage flags
  async toggleSelling(id: string, active: boolean): Promise<Project> {
    const { data } = await api.put(`/api/projects/${id}/`, { is_selling: active });
    return data.project;
  },

  async toggleConstructing(id: string, active: boolean): Promise<Project> {
    const { data } = await api.put(`/api/projects/${id}/`, { is_constructing: active });
    return data.project;
  },
};
