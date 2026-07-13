// =========================================================================
// === frontend/lib/api/projects.ts ===
// Sprint 2: adds RequirementEvidence types + evidenceApi calls
// All Sprint 1 types preserved — additive only.
//  Sprint 9: Next Actions Assistant
// Sprint 14: Risk Forecast 
//  Sprint 17 : Live Event Stream + Readiness Momentum - IS implemented here
//  Sprint 26 :IS implemented here
// ==========================================================================
import api from "@/lib/api";

// ── Existing types — UNCHANGED ─────────

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
  | "menunggu_verifikasi" 
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

// ── Sprint 8: NEW types ───────────────────────────────────────
export interface RequirementEvidence {
  id:                   string;
  file_name:            string;
  file_url:             string;
  file_url_display:     string;
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
  // Sprint 8: version tracking
  version_number:       number;
  version_label:        string;
  is_latest:            boolean;
  superseded_by_id:     string | null;
  version_chain:        EvidenceVersion[];
  can_verify:           boolean;
  cannot_verify_reason: string;
  eligible_verifiers:   EvidenceVerifier[];
}

export interface RequirementComment {
  id:           string;
  body:         string;
  author:       string;
  author_name:  string;
  author_email: string;
  created_at:   string;
}

export interface OrgMember {
  id:        string;
  full_name: string;
  email:     string;
  role:      string;
}

export interface ReadinessBreakdownItem {
  id:                    string;
  name:                  string;
  category:              string;
  weight:                number;  
  weight_pct:            number;   // % of total weight (e.g. 40)
  status:                ReqStatus;
  is_completed:          boolean;
  is_dependency_blocked: boolean;
  contribution:          number;   // weight_pct if completed, else 0
}

export interface ReadinessBreakdown {
  score:            number;   
  label:            string;
  total_weight:     number;
  completed_weight: number;
  formula:          string;   // human-readable e.g. "Readiness = (40 / 100) × 100 = 40%"
  items:            ReadinessBreakdownItem[];
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
  audit_count: number; // Sprint 3
  // Sprint 4: dependency fields 
  prerequisites:         string[];   // prereq names
  unmet_prerequisites:   string[];   // which prereqs are not done yet
  is_dependency_blocked: boolean;    // true if any prereq is unmet
  can_act_now:           boolean;    // true if developer can work on this now
  weight:                number;   // raw weight value (0 if optional)
  weight_pct:            number;   // % of total mandatory weight
  contribution:          number;   // weight_pct if completed, else 0
  // Sprint 7: ownership
  assigned_to_id:   string | null;
  assigned_to_name: string | null;
  due_date:         string | null;
  is_overdue:       boolean;
  days_until_due:   number | null;
  comment_count:    number;
}

// Sprint 6 risk factor type ───────────────────────────

export interface RiskFactor {
  key:         string;   // "pbg_rejected" | "mandatory_blockers" | etc
  name:        string;   // "PBG ditolak"
  description: string;   // full explanation
  impact:      string;   // "Tinggi" | "Sedang" | "Rendah"
  impact_key:  string;   // "high" | "medium" | "low"
  points:      number;   // points this factor contributes
  max_points:  number;   // max possible for this factor
  action:      string;   // what to do
  triggered:   boolean;  // always true (only triggered factors are returned)
  days?:       number;   // only for timeline_overrun factor
}

export interface RiskTrendPoint {
  date:  string;   // ISO date "2026-06-28" - this should be indonesian format
  score: number;   // 0-100
  level: string;   // "low" | "medium" | "high"
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
  readiness_breakdown: ReadinessBreakdown;
  readiness_label:     string;
  risk_score:       number;           // 0-100 numeric score
  risk_factors:     RiskFactor[];     // structured factors
  risk_since:       string | null;    // ISO date when level started
  risk_trend_data:  RiskTrendPoint[]; // last 30 days
  // Sprint 8: evidence workflow
  pending_evidence_count:  number;
  rejected_evidence_count: number;
  key_progress:        KeyProgress;
  readiness_trend_data: ReadinessHistoryPoint[];
  action_chain: ActionChain | null;   // Sprint 12
}

export interface StageChecklistItem {
  item:      string;
  done:      boolean;
  blocking?: boolean;
}

// Sprint 8 new types

export interface EvidenceVersion {
  id:                  string;
  version_number:      number;
  label:               string;
  verification_status: EvidenceVerifStatus;
  is_latest:           boolean;
  uploaded_at:         string;
  verifier_notes:      string;
}

export interface EvidenceVerifier {
  id:        string;
  full_name: string;
}

// Sprint 9 types ───────────────────────────────────────

export type ActionType =
  | "overdue"
  | "blocked_others"
  | "high_impact"
  | "high_risk"
  | "resubmit_needed"
  | "standard";

export interface ActionItem {
  project_id:             string;
  project_name:           string;
  project_stage:          ProjectStage;
  project_stage_display:  string;
  requirement_id:         string;
  requirement_name:       string;
  status_id:              string;
  status:                 ReqStatus;
  status_display:         string;
  due_date:               string | null;
  is_overdue:             boolean;
  days_until_due:         number | null;
  weight_pct:             number;
  is_assigned_to_me:      boolean;
  priority_score:         number;
  action_type:            ActionType;
  reasons:                string[];
  primary_reason:         string;
}

export interface MyActionsResponse {
  my_tasks:          ActionItem[];
  my_tasks_count:    number;
  unassigned:        ActionItem[];
  unassigned_count:  number;
  total_actionable:  number;
}

// Sprint 10: Readiness trend history ──────────────────────────
export interface ReadinessHistoryPoint {
  date:  string;   // ISO date "2026-06-25"
  score: number;   // 0-100
}

export interface ReadinessHistory {
  project_id:    string;
  project_name:  string;
  current_score: number;
  days:          number;
  results:       ReadinessHistoryPoint[];
}

// Sprint 10: Key progress aggregate ───────────────────────────
export interface KeyProgress {
  requirements_completed: number;
  requirements_total:     number;
  evidence_uploaded:      number;
  evidence_verified:      number;
  evidence_awaiting:      number;
  overdue_count:          number;
}

// Sprint 11: Dependency graph ──────────────────────────────────
export interface DependencyNode {
  id:                    string;
  name:                  string;
  status:                ReqStatus;
  status_display:        string;
  is_mandatory:          boolean;
  is_blocking:           boolean;
  is_dependency_blocked: boolean;
  weight_pct:            number;
  prerequisites:         string[];
  unmet_prerequisites:   string[];
  // Sprint 16: Interactive node detail
  block_reason:      string | null;
  assigned_to_name:  string | null;
  est_minutes:       number;
}

export interface DependencyEdge {
  from: string;   // node id
  to:   string;   // node id
}

export interface DependencyGraph {
  project_id:    string;
  project_name:  string;
  stage:         ProjectStage;
  stage_display: string;
  nodes:         DependencyNode[];
  edges:         DependencyEdge[];
}

// Sprint 12: Action chain ──────────────
export type ActivityFilterType =
  | "all"
  | "evidence"
  | "readiness"
  | "assignments"
  | "comments";

export interface ActionChainStep {
  step:        number;
  action:      string;
  action_type: "assign" | "upload" | "verify" | "complete";
  status_id:   string | null;
  is_done:     boolean;
  est_minutes: number;
}

export interface ActionChain {
  requirement_name:      string;
  requirement_id:        string;
  status_id:             string | null;
  steps:                 ActionChainStep[];
  total_steps:           number;
  completed_steps:       number;
  est_remaining_minutes: number;
}

// Sprint 13: Decision Engine ───────────────────────────────────
export interface DecisionRecommendation {
  requirement_name:      string;
  requirement_id:        string;
  status_id:             string | null;
  action:                string;
  priority:              "high" | "medium" | "low";
  readiness_impact_pct:  number;
  est_minutes:           number;
  reasons:               string[];
  is_assigned:           boolean;
  evidence_count:        number;
}

export interface DecisionAlternative {
  rank:                  number;
  requirement_name:      string;
  requirement_id:        string;
  status_id:             string | null;
  action:                string;
  readiness_impact_pct:  number;
  est_minutes:           number;
  priority_score:        number;
}

export interface DecisionEngine {
  has_recommendations:  boolean;
  all_clear:            boolean;
  primary:              DecisionRecommendation | null;
  alternatives:         DecisionAlternative[];
  current_readiness:    number;
  projected_readiness:  number;
  message?:             string;   // only present when all_clear or no candidates
}

// Sprint 14: Risk Forecast ─────────────────────────────────────
export interface RiskForecastPoint {
  score:         number;
  level:         "low" | "medium" | "high";
  level_display: string;
}

export interface RiskForecastDriver {
  key:             string;
  name:            string;
  description:     string;
  impact:          string;
  current_points:  number;
  forecast_points: number;
  delta_points:    number;
  is_new:          boolean;   // factor didn't exist currently, appears in forecast
}

export interface RiskForecast {
  project_id:    string;
  project_name:  string;
  days:          number;
  current:       RiskForecastPoint;
  forecast:      RiskForecastPoint;
  delta:         number;       // forecast.score - current.score
  will_escalate: boolean;      // level goes up (low→medium or medium→high)
  top_drivers:   RiskForecastDriver[];
}

// Sprint 16: Requirement update impact (returned by PUT /requirements/<id>/)
export interface RequirementUpdateImpact {
  readiness_before:  number;
  readiness_after:   number;
  readiness_delta:   number;
  risk_before:       number;
  risk_after:        number;
  risk_delta:        number;
  stage_can_advance: boolean;
}

export interface RequirementUpdateResponse {
  success:      boolean;
  message:      string;
  impact:       RequirementUpdateImpact;   // Sprint 16
  intelligence: IntelligenceSummary;
}

// Sprint 17: Live pulse ────────────────────────────────────────
export interface PulseEvent {
  id:              string;
  action:          string;
  message:         string;
  actor:           string;
  subject:         string;
  readiness_delta: number | null;
  risk_delta:      number | null;
  timestamp:       string;
}

export interface PulseResponse {
  project_id:            string;
  has_updates:           boolean;
  readiness_score:       number;
  readiness_delta_today: number | null;
  risk_score:            number;
  blocking_count:        number;
  new_events:            PulseEvent[];
  checked_at:            string;
}

// Sprint 17: Cross-project recent activity feed ────────────────
export interface RecentActivityItem {
  id:              string;
  action:          string;
  message:         string;
  actor:           string;
  subject:         string;
  project_id:      string;
  project_name:    string;
  readiness_delta: number | null;
  timestamp:       string;
}

// Sprint 18: Portfolio Intelligence Hub ────────────────────────
export interface PortfolioMetrics {
  total_projects:     number;
  avg_readiness:      number;   // 0-100
  critical_count:     number;   // projects with blockers
  high_risk_count:    number;
  delayed_count:      number;
  revenue_protected:  number;   // Rupiah integer, all-time collected (status="lunas")
  // Sprint 26: genuinely new fields, already live on PortfolioIntelligenceView —
  // this type was just never updated to declare them.
  revenue_this_month: number;   // Rupiah integer, current calendar month (timezone.localtime())
  ar_outstanding:     number;   // Rupiah integer, sum of Payment.amount where is_overdue
}

export interface PortfolioWeekDelta {
  avg_readiness:   number;   // positive = improved (readiness went up)
  critical_count:  number;   // negative = improved (fewer critical)
  high_risk_count: number;   // negative = improved
  delayed_count:   number;   // negative = improved
}

export interface PortfolioAtRiskProject {
  id:           string;
  name:         string;
  readiness:    number;
  risk_level:   "low" | "medium" | "high";
  risk_display: string;
  blocking:     number;
  next_action:  string | null;
}

export interface PortfolioIntelligence {
  current:     PortfolioMetrics;
  week_delta:  PortfolioWeekDelta | null;   // null until first snapshot
  top_at_risk: PortfolioAtRiskProject[];
  has_history: boolean;
}

// Sprint 19: cross-project Calendar — mirrors ProjectCalendarView's
// response exactly. due_date, is_overdue, days_until_due, and
// assigned_to have existed on ProjectRequirementStatus since Sprint 7.
export interface CalendarEvent {
  id:               string;
  requirement_name: string;
  project_id:       string;
  project_name:     string;
  due_date:         string;
  status:           string;
  is_overdue:       boolean;
  days_until_due:   number;
  assigned_to_name: string | null;
}

// Sprint 20: shape returned by the three requirement-changing
// endpoints (status update, evidence upload, evidence verify) — the
// "feedback loop" data. readiness/risk before/after/delta and
// stage_can_advance existed since the Sprint 16 bug hunt; newly_unlocked
// and the dynamic message are new in Sprint 20.
export interface RequirementImpact {
  readiness_before:  number;
  readiness_after:   number;
  readiness_delta:   number;
  risk_before:       number;
  risk_after:        number;
  risk_delta:        number;
  stage_can_advance: boolean;
  newly_unlocked:    string[];
  message:           string;
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
  risk_score:          number;   
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

// Sprint 3 types

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
  readiness_delta?: number | null;
  risk_delta?:      number | null;
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

export const RISK_FACTOR_IMPACT_META: Record<string, { color: string; bg: string }> = {
  "Tinggi": { color: "var(--color-danger)",  bg: "var(--color-danger-light)"  },
  "Sedang": { color: "var(--color-warning)", bg: "var(--color-warning-light)" },
  "Rendah": { color: "var(--color-info)",    bg: "var(--color-info-light)"    },
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

export const EVIDENCE_VERSION_META: Record<EvidenceVerifStatus, {
  label: string; color: string; bg: string; icon: string;
}> = {
  pending:  { label: "Menunggu",  color: "var(--color-warning)", bg: "var(--color-warning-light)", icon: "⏳" },
  approved: { label: "Disetujui", color: "var(--color-success)", bg: "var(--color-success-light)", icon: "✅" },
  rejected: { label: "Ditolak",   color: "var(--color-danger)",  bg: "var(--color-danger-light)",  icon: "❌" },
};

export const READINESS_LABEL_META: Record<string, { color: string; bg: string }> = {
  "Sangat Siap": { color: "var(--color-success)", bg: "var(--color-success-light)" },
  "Cukup Siap":  { color: "var(--color-info)",    bg: "var(--color-info-light)"    },
  "Sedang":      { color: "var(--color-warning)", bg: "var(--color-warning-light)" },
  "Belum Siap":  { color: "var(--color-danger)",  bg: "var(--color-danger-light)"  },
};

export const ACTION_TYPE_META: Record<ActionType, {
  label: string; color: string; bg: string; icon: string;
}> = {
  overdue:         { label: "Terlambat",        color: "var(--color-danger)",  bg: "var(--color-danger-light)",  icon: "⏰" },
  blocked_others:  { label: "Memblokir Lainnya", color: "var(--color-warning)", bg: "var(--color-warning-light)", icon: "🔓" },
  high_impact:     { label: "Dampak Besar",      color: "var(--color-accent)",  bg: "var(--color-accent-light)",  icon: "⭐" },
  high_risk:       { label: "Risiko Tinggi",     color: "var(--color-danger)",  bg: "var(--color-danger-light)",  icon: "⚠️" },
  resubmit_needed: { label: "Perlu Diunggah Ulang", color: "var(--color-warning)", bg: "var(--color-warning-light)", icon: "🔁" },
  standard:        { label: "Tindakan Diperlukan", color: "var(--color-ink-3)", bg: "var(--color-paper-2)",       icon: "📋" },
};


// ── Derived stats — UNCHANGED ─────────────────────────────────

export function deriveStats(projects: Project[]) {
  return {
    total_units:     projects.reduce((s, p) => s + p.total_units, 0),
    units_sold:      projects.reduce((s, p) => s + p.units_sold, 0),
    units_available: projects.reduce((s, p) => s + (p.total_units - p.units_sold), 0),
  };
}

// ── RISK SCORE META ───────────────────────────────────────────

export function getRiskScoreMeta(score: number): { color: string; bg: string; label: string } {
  if (score >= 60) return { color: "var(--color-danger)",  bg: "var(--color-danger-light)",  label: "Tinggi"  };
  if (score >= 30) return { color: "var(--color-warning)", bg: "var(--color-warning-light)", label: "Sedang"  };
  return              { color: "var(--color-success)", bg: "var(--color-success-light)", label: "Rendah"  };
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
  ): Promise<{ intelligence: IntelligenceSummary; impact: RequirementImpact }> {
    const { data } = await api.put(
      `/api/projects/${projectId}/requirements/${reqStatusId}/`,
      payload
    );
    return { intelligence: data.intelligence, impact: data.impact };
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

  async getActivity(
    id:    string,
    limit: number = 20,
    type:  ActivityFilterType = "all"
  ): Promise<{ count: number; filter_type: string; results: ActivityItem[] }> {
    const { data } = await api.get(
      `/api/projects/${id}/activity/?limit=${limit}&type=${type}`
    );
    return { count: data.count, filter_type: data.filter_type, results: data.results };
  },

  async getFinancial(id: string): Promise<FinancialSnapshot> {
  const { data } = await api.get(`/api/projects/${id}/financial/`);
  return data.financial;
  },

  async assignRequirement(
    projectId:   string,
    reqStatusId: string,
    payload: { assigned_to?: string | null; due_date?: string | null }
  ): Promise<IntelligenceSummary> {
    const { data } = await api.put(
      `/api/projects/${projectId}/requirements/${reqStatusId}/assign/`,
      payload
    );
    return data.intelligence;
  },

  async getOrgMembers(projectId: string): Promise<OrgMember[]> {
    const { data } = await api.get(`/api/projects/${projectId}/members/`);
    return data.results;
  },

  async getMyActions(): Promise<MyActionsResponse> {
    const { data } = await api.get("/api/projects/my-actions/");
    return data;
  },

  async getReadinessHistory(id: string, days = 30): Promise<ReadinessHistory> {
    const { data } = await api.get(
      `/api/projects/${id}/readiness-history/?days=${days}`
    );
    return data;
  },

  async getDependencyGraph(id: string): Promise<DependencyGraph> {
    const { data } = await api.get(`/api/projects/${id}/dependency-graph/`);
    return data;
  },

  async getDecisionEngine(id: string): Promise<DecisionEngine> {
    const { data } = await api.get(`/api/projects/${id}/decision/`);
    return data;
  },

  async getRiskForecast(id: string, days = 14): Promise<RiskForecast> {
    const { data } = await api.get(
      `/api/projects/${id}/risk-forecast/?days=${days}`
    );
    return data;
  },

    async getPulse(id: string, since?: string): Promise<PulseResponse> {
    const params = since ? `?since=${encodeURIComponent(since)}` : "";
    const { data } = await api.get(`/api/projects/${id}/pulse/${params}`);
    return data;
  },

  async getRecentActivity(limit = 10): Promise<{ count: number; results: RecentActivityItem[] }> {
    const { data } = await api.get(`/api/projects/recent-activity/?limit=${limit}`);
    return { count: data.count, results: data.results };
  },

  async getPortfolioIntelligence(): Promise<PortfolioIntelligence> {
    const { data } = await api.get("/api/projects/portfolio-intelligence/");
    return data;
  },

  // Sprint 19: standalone Calendar page
  async getCalendar(): Promise<{ count: number; results: CalendarEvent[] }> {
    const { data } = await api.get("/api/projects/calendar/");
    return { count: data.count, results: data.results };
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
  ): Promise<{ evidence: RequirementEvidence; intelligence: IntelligenceSummary; impact: RequirementImpact }> {
    const formData = new FormData();
    if (payload.file)     formData.append("file",     payload.file);
    if (payload.file_url) formData.append("file_url", payload.file_url);
    if (payload.notes)    formData.append("notes",    payload.notes);

    const { data } = await api.post(
      `/api/projects/${projectId}/requirements/${reqStatusId}/evidence/`,
      formData,
      { headers: { "Content-Type": "multipart/form-data" } }
    );
    return { evidence: data.evidence, intelligence: data.intelligence, impact: data.impact };
  },

  async verify(
    projectId: string,
    reqStatusId: string,
    evidenceId: string,
    action: "approve" | "reject",
    notes?: string
  ): Promise<{ evidence: RequirementEvidence; intelligence: IntelligenceSummary; impact: RequirementImpact }> {
    const { data } = await api.put(
      `/api/projects/${projectId}/requirements/${reqStatusId}/evidence/${evidenceId}/verify/`,
      { action, notes: notes ?? "" }
    );
    return { evidence: data.evidence, intelligence: data.intelligence, impact: data.impact };
  },

  async getEligibleVerifiers(
    projectId:   string,
    reqStatusId: string,
    evidenceId:  string
  ): Promise<{
    eligible_verifiers:         EvidenceVerifier[];
    eligible_count:             number;
    can_verify_as_current_user: boolean;
    reason:                     string;
  }> {
    const { data } = await api.get(
      `/api/projects/${projectId}/requirements/${reqStatusId}/evidence/${evidenceId}/verifiers/`
    );
    return data;
  },
};

export const commentApi = {
  async list(
    projectId:   string,
    reqStatusId: string
  ): Promise<{ count: number; results: RequirementComment[] }> {
    const { data } = await api.get(
      `/api/projects/${projectId}/requirements/${reqStatusId}/comments/`
    );
    return { count: data.count, results: data.results };
  },

  async post(
    projectId:   string,
    reqStatusId: string,
    body:        string
  ): Promise<RequirementComment> {
    const { data } = await api.post(
      `/api/projects/${projectId}/requirements/${reqStatusId}/comments/`,
      { body }
    );
    return data.comment;
  },
};

// =============================================================================
// Sprint 27-follow-up: Site Plan — real interactive site plan, replacing
// the dead site_plan_url field (existed but was never rendered anywhere,
// confirmed by direct audit before this feature was built).
// =============================================================================

export type MapStatus = "tersedia" | "belum_ada_pembayaran" | "cicilan_berjalan" | "lunas" | "menunggak";

export interface SitePlanUnitMarker {
  id:          string;
  unit_id:     string;
  unit_number: string;
  map_status:  MapStatus;
  points:      [number, number][];
  created_at:  string;
}

export interface SitePlan {
  id:            string;
  label:         string;
  is_active:     boolean;
  image_url:     string;
  image_width:   number;
  image_height:  number;
  markers:       SitePlanUnitMarker[];
  unit_count:    number;
  mapped_count:  number;
  uploaded_at:   string;
}

export const sitePlanApi = {
  async get(projectId: string): Promise<SitePlan | null> {
    const { data } = await api.get(`/api/projects/${projectId}/site-plan/`);
    return data.site_plan;
  },

  async upload(
    projectId: string,
    payload: { image: File; label?: string }
  ): Promise<SitePlan> {
    const formData = new FormData();
    formData.append("image", payload.image);
    if (payload.label) formData.append("label", payload.label);

    const { data } = await api.post(
      `/api/projects/${projectId}/site-plan/`,
      formData,
      { headers: { "Content-Type": "multipart/form-data" } }
    );
    return data.site_plan;
  },

  async listMarkers(projectId: string): Promise<SitePlanUnitMarker[]> {
    const { data } = await api.get(`/api/projects/${projectId}/site-plan/markers/`);
    return data.results;
  },

  async createMarker(
    projectId: string,
    payload: { unit_id: string; points: [number, number][] }
  ): Promise<SitePlanUnitMarker> {
    const { data } = await api.post(
      `/api/projects/${projectId}/site-plan/markers/`,
      payload
    );
    return data.marker;
  },

  async deleteMarker(projectId: string, markerId: string): Promise<void> {
    await api.delete(`/api/projects/${projectId}/site-plan/markers/${markerId}/`);
  },
};
