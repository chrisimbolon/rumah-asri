"use client";
// ===================================================================================================
// === frontend/app/dashboard/page.tsx ===
// Sprint 1 upgrade:
//   + Alerts ledger (critical/warning/info) from portfolio
//   + Collection efficiency financial snapshot
//   + Parallel stage (5A/5B) indicators on portfolio table + this has to be solved on with REAL DATA
//   All original sections preserved — additive only.
//  Sprint9: next actions assistant dashboard widget - is implemented at this stage
//  Sprint 19: Command Center redesign.
//    - Event Stream + Portfolio Intelligence Hub MOVED here from
//      app/dashboard/projects/page.tsx (unchanged, just relocated —
//      the roadmap wants these on the main dashboard, not the
//      projects list page).
//    - Added: Dependency Graph / Decision Engine / Risk Forecast for
//      the single highest-priority project (top_at_risk[0] from
//      Portfolio Intelligence) — per-project only versions exist,
//      so this is one project's view, not a portfolio-wide aggregate.
//    - Removed: old 6-card "Summary metrics" grid (superseded by
//      Portfolio Intelligence Hub's 6 metrics, which include real
//      week-over-week deltas).
//    - Removed: mock "Log Aktivitas" section (LOG from mock-data) —
//      Event Stream now covers this with real data; having both a
//      real live feed AND a fake static one would be confusing.
//    - AI Assistant panel from the roadmap mockup: intentionally
//      skipped (Sprint 15 is still shelved).
// ==============================================================================================

import {
  DecisionEnginePanel,
  DependencyGraphPanel,
  RiskForecastPanel,
} from "@/components/project/IntelligencePanels";
import { useAuth } from "@/context/AuthContext";
import {
  ACTION_TYPE_META,
  ALERT_META,
  ActionItem,
  MyActionsResponse,
  PortfolioAtRiskProject,
  PortfolioIntelligence,
  PortfolioRow,
  Project,
  RISK_META,
  RecentActivityItem,
  STAGE_META,
  TREND_META,
  projectsApi,
} from "@/lib/api/projects";
import { NOTIFIKASI } from "@/lib/mock-data";
import {
  AlertTriangle,
  ArrowRight,
  Building2,
  CheckCircle2,
  Info,
  Loader2,
} from "lucide-react";
import Link from "next/link";
import { useEffect, useState } from "react";

// ── Readiness bar ─────────────────────────────────────────────
function ReadinessBar({ score }: { score: number }) {
  const color =
    score >= 80 ? "var(--color-success)" :
    score >= 50 ? "var(--color-warning)" :
                  "var(--color-danger)";
  return (
    <div style={{ display: "flex", alignItems: "center", gap: 8 }}>
      <div style={{ flex: 1, height: 6, backgroundColor: "rgba(14,13,11,0.08)", borderRadius: 3, overflow: "hidden" }}>
        <div style={{ width: `${score}%`, height: "100%", backgroundColor: color, borderRadius: 3, transition: "width 0.3s" }} />
      </div>
      <span style={{ fontSize: 11, fontWeight: 700, color, minWidth: 32, textAlign: "right" }}>
        {score}%
      </span>
    </div>
  );
}

// ── Sprint 1: Readiness dimensions mini-bar ───────────────────
function DimensionBar({ label, value }: { label: string; value: number }) {
  const color =
    value >= 80 ? "var(--color-success)" :
    value >= 50 ? "var(--color-warning)" :
                  "var(--color-danger)";
  return (
    <div style={{ marginBottom: 8 }}>
      <div style={{ display: "flex", justifyContent: "space-between", marginBottom: 3 }}>
        <span style={{ fontSize: 11, color: "var(--color-ink-3)" }}>{label}</span>
        <span style={{ fontSize: 11, fontWeight: 700, color }}>{value}%</span>
      </div>
      <div style={{ height: 4, backgroundColor: "rgba(14,13,11,0.08)", borderRadius: 2, overflow: "hidden" }}>
        <div style={{ width: `${value}%`, height: "100%", backgroundColor: color, borderRadius: 2 }} />
      </div>
    </div>
  );
}

// ── Sprint 1: Alerts ledger ───────────────────────────────────
function AlertsLedger({ projects }: { projects: Project[] }) {
  // Collect all alerts across all projects, tag with project name
  const allAlerts = projects.flatMap((p) =>
    (p.alerts ?? []).map((a) => ({ ...a, projectName: p.name, projectId: p.id }))
  );

  // Sort: critical first, then warning, then info
  const order: Record<string, number> = { critical: 0, warning: 1, info: 2 };
  allAlerts.sort((a, b) => (order[a.level] ?? 3) - (order[b.level] ?? 3));

  if (allAlerts.length === 0) {
    return (
      <div style={{ textAlign: "center", padding: "24px 0", color: "var(--color-ink-3)" }}>
        <CheckCircle2 size={28} style={{ margin: "0 auto 8px", display: "block", color: "var(--color-success)", opacity: 0.6 }} />
        <div style={{ fontSize: 12 }}>Tidak ada alert aktif — semua proyek berjalan lancar</div>
      </div>
    );
  }

  return (
    <div style={{ display: "flex", flexDirection: "column", gap: 8 }}>
      {allAlerts.slice(0, 6).map((alert, i) => {
        const meta = ALERT_META[alert.level as keyof typeof ALERT_META] ?? ALERT_META.info;
        return (
          <Link
            key={i}
            href={`/dashboard/projects/${alert.projectId}`}
            style={{ textDecoration: "none" }}
          >
            <div style={{
              padding: "10px 12px",
              backgroundColor: meta.bg,
              border: `1px solid ${meta.border}`,
              borderRadius: 8,
              transition: "opacity 0.15s",
            }}
              onMouseEnter={(e) => ((e.currentTarget as HTMLElement).style.opacity = "0.8")}
              onMouseLeave={(e) => ((e.currentTarget as HTMLElement).style.opacity = "1")}
            >
              <div style={{ display: "flex", alignItems: "flex-start", gap: 8 }}>
                <div style={{
                  width: 6, height: 6, borderRadius: "50%",
                  backgroundColor: meta.color,
                  flexShrink: 0, marginTop: 5,
                }} />
                <div style={{ flex: 1, minWidth: 0 }}>
                  <div style={{ fontSize: 11, fontWeight: 600, color: meta.color, marginBottom: 2 }}>
                    {alert.projectName}
                  </div>
                  <div style={{ fontSize: 12, color: "var(--color-ink)", lineHeight: 1.4, marginBottom: 3 }}>
                    {alert.message}
                  </div>
                  <div style={{ fontSize: 11, color: "var(--color-ink-3)" }}>
                    → {alert.action}
                  </div>
                </div>
                <span style={{
                  fontSize: 10, fontWeight: 700,
                  padding: "2px 7px", borderRadius: 999,
                  color: meta.color, backgroundColor: "white",
                  flexShrink: 0, textTransform: "uppercase",
                  letterSpacing: "0.05em",
                }}>
                  {alert.level}
                </span>
              </div>
            </div>
          </Link>
        );
      })}
      {allAlerts.length > 6 && (
        <div style={{ fontSize: 11, color: "var(--color-ink-3)", textAlign: "center", paddingTop: 4 }}>
          +{allAlerts.length - 6} alert lainnya
        </div>
      )}
    </div>
  );
}

// ── Sprint 1: Collection efficiency panel 
function CollectionPanel({ projects }: { projects: Project[] }) {
  // Aggregate across all projects
  let totalBilled  = 0;
  let totalSettled = 0;

  for (const p of projects) {
    const ce = p.collection_efficiency;
    if (ce) {
      totalBilled  += ce.total_billed;
      totalSettled += ce.total_settled;
    }
  }

  const totalArrears  = totalBilled - totalSettled;
  const efficiencyPct = totalBilled > 0
    ? Math.round((totalSettled / totalBilled) * 100)
    : 100;

  const status =
    efficiencyPct >= 90 ? { label: "Sehat", color: "var(--color-success)", bg: "var(--color-success-light)" } :
    efficiencyPct >= 70 ? { label: "Perlu Perhatian", color: "var(--color-warning)", bg: "var(--color-warning-light)" } :
                          { label: "Kritis", color: "var(--color-danger)", bg: "var(--color-danger-light)" };

  const rupiah = (n: number) =>
    n >= 1_000_000_000
      ? `Rp ${(n / 1_000_000_000).toFixed(1)}M`
      : n >= 1_000_000
      ? `Rp ${(n / 1_000_000).toFixed(0)}jt`
      : `Rp ${n.toLocaleString("id-ID")}`;

  return (
    <div>
      {/* Efficiency header */}
      <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between", marginBottom: 16 }}>
        <div style={{ fontSize: 28, fontWeight: 800, color: status.color }}>
          {efficiencyPct}%
        </div>
        <span style={{
          fontSize: 11, fontWeight: 700,
          padding: "3px 10px", borderRadius: 999,
          color: status.color, backgroundColor: status.bg,
        }}>
          {status.label}
        </span>
      </div>

      {/* Progress bar */}
      <div style={{ height: 8, backgroundColor: "rgba(14,13,11,0.08)", borderRadius: 4, overflow: "hidden", marginBottom: 16 }}>
        <div style={{ width: `${efficiencyPct}%`, height: "100%", backgroundColor: status.color, borderRadius: 4, transition: "width 0.5s" }} />
      </div>

      {/* Three numbers */}
      <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr 1fr", gap: 8 }}>
        {[
          { label: "Total AR",    value: rupiah(totalBilled),  color: "var(--color-ink)"     },
          { label: "Lunas",       value: rupiah(totalSettled), color: "var(--color-success)" },
          { label: "Menunggak",   value: rupiah(totalArrears), color: totalArrears > 0 ? "var(--color-danger)" : "var(--color-ink-3)" },
        ].map((s) => (
          <div key={s.label} style={{ textAlign: "center", padding: "10px 8px", backgroundColor: "var(--color-paper-2)", borderRadius: 6 }}>
            <div style={{ fontSize: 13, fontWeight: 700, color: s.color, marginBottom: 2 }}>{s.value}</div>
            <div style={{ fontSize: 10, color: "var(--color-ink-3)", textTransform: "uppercase", letterSpacing: "0.04em" }}>{s.label}</div>
          </div>
        ))}
      </div>
    </div>
  );
}

// ── Portfolio table ───────────────────────────────────────────
function PortfolioTable({ rows, projects }: { rows: PortfolioRow[]; projects: Project[] }) {
  // Build a map for parallel stage data from full project objects
  const parallelMap = new Map(
    projects.map((p) => [p.id, p.parallel_stages])
  );

  if (rows.length === 0) {
    return (
      <div style={{ textAlign: "center", padding: "40px 24px", color: "var(--color-ink-3)" }}>
        <Building2 size={32} style={{ margin: "0 auto 12px", opacity: 0.2, display: "block" }} />
        <div style={{ fontSize: 13 }}>Belum ada proyek. Buat proyek pertama Anda.</div>
        <Link href="/dashboard/projects" className="btn-accent" style={{ display: "inline-flex", alignItems: "center", gap: 6, marginTop: 16 }}>
          <Building2 size={13} /> Tambah Proyek
        </Link>
      </div>
    );
  }

  return (
    <div style={{ overflowX: "auto" }}>
      <table style={{ width: "100%", borderCollapse: "collapse", fontSize: 12 }}>
        <thead>
          <tr style={{ borderBottom: "2px solid rgba(14,13,11,0.08)" }}>
            {["Proyek", "Tahap", "Kesiapan", "Blokir", "Risiko", "Tindakan Berikutnya", "5A/5B", "Tren"].map((h) => (
              <th key={h} style={{ padding: "10px 12px", textAlign: "left", fontSize: 10, fontWeight: 700, color: "var(--color-ink-3)", textTransform: "uppercase", letterSpacing: "0.06em", whiteSpace: "nowrap" }}>
                {h}
              </th>
            ))}
          </tr>
        </thead>
        <tbody>
          {rows.map((row) => {
            const stageMeta    = STAGE_META[row.stage];
            const riskMeta     = RISK_META[row.risk_level];
            const trendMeta    = TREND_META[row.trend];
            const parallel     = parallelMap.get(row.id);
            return (
              <tr
                key={row.id}
                style={{ borderBottom: "1px solid rgba(14,13,11,0.05)", transition: "background 0.15s" }}
                onMouseEnter={(e) => ((e.currentTarget as HTMLElement).style.backgroundColor = "var(--color-paper-2)")}
                onMouseLeave={(e) => ((e.currentTarget as HTMLElement).style.backgroundColor = "transparent")}
              >
                {/* Project name */}
                <td style={{ padding: "12px 12px" }}>
                  <Link href={`/dashboard/projects/${row.id}`} style={{ textDecoration: "none" }}>
                    <div style={{ fontWeight: 600, color: "var(--color-ink)", marginBottom: 2 }}>{row.name}</div>
                    <div style={{ fontSize: 10, color: "var(--color-ink-3)" }}>{row.location}</div>
                  </Link>
                </td>

                {/* Stage */}
                <td style={{ padding: "12px 12px" }}>
                  <span style={{ fontSize: 11, fontWeight: 600, padding: "3px 10px", borderRadius: 999, color: stageMeta.color, backgroundColor: stageMeta.bg }}>
                    {stageMeta.label}
                  </span>
                </td>

                {/* Readiness */}
                <td style={{ padding: "12px 12px", minWidth: 130 }}>
                  <ReadinessBar score={row.readiness_score} />
                </td>

                {/* Blocking count */}
                <td style={{ padding: "12px 12px", textAlign: "center" }}>
                  {row.blocking_count > 0 ? (
                    <span style={{ fontSize: 12, fontWeight: 700, color: "var(--color-danger)", display: "flex", alignItems: "center", gap: 4, justifyContent: "center" }}>
                      <AlertTriangle size={12} /> {row.blocking_count}
                    </span>
                  ) : (
                    <CheckCircle2 size={14} style={{ color: "var(--color-success)", display: "block", margin: "0 auto" }} />
                  )}
                </td>

                {/* Risk */}
                <td style={{ padding: "12px 12px" }}>
                  <span style={{ fontSize: 11, fontWeight: 600, padding: "3px 10px", borderRadius: 999, color: riskMeta.color, backgroundColor: riskMeta.bg }}>
                    {riskMeta.label}
                  </span>
                </td>

                {/* Next action */}
                <td style={{ padding: "12px 12px", maxWidth: 200 }}>
                  {row.next_action ? (
                    <span style={{ fontSize: 11, color: "var(--color-warning)", fontWeight: 500 }}>
                      {row.next_action}
                    </span>
                  ) : (
                    <span style={{ fontSize: 11, color: "var(--color-ink-3)", fontStyle: "italic" }}>—</span>
                  )}
                </td>

                {/* Sprint 1: 5A/5B parallel stage indicators */}
                <td style={{ padding: "12px 12px" }}>
                  {parallel ? (
                    <div style={{ display: "flex", gap: 4 }}>
                      <span style={{
                        fontSize: 10, fontWeight: 600, padding: "2px 6px", borderRadius: 4,
                        backgroundColor: parallel.is_selling ? "var(--color-success-light)" : "rgba(14,13,11,0.05)",
                        color: parallel.is_selling ? "var(--color-success)" : "var(--color-ink-3)",
                      }}>
                        5A
                      </span>
                      <span style={{
                        fontSize: 10, fontWeight: 600, padding: "2px 6px", borderRadius: 4,
                        backgroundColor: parallel.is_constructing ? "var(--color-accent-light)" : "rgba(14,13,11,0.05)",
                        color: parallel.is_constructing ? "var(--color-accent)" : "var(--color-ink-3)",
                      }}>
                        5B
                      </span>
                    </div>
                  ) : (
                    <span style={{ color: "var(--color-ink-3)" }}>—</span>
                  )}
                </td>

                {/* Trend */}
                <td style={{ padding: "12px 12px" }}>
                  <span style={{ fontSize: 16, color: trendMeta.color, fontWeight: 700 }}>
                    {trendMeta.icon}
                  </span>
                </td>
              </tr>
            );
          })}
        </tbody>
      </table>
    </div>
  );
}

// ── NEW: Next Actions Assistant panel ──────────────────────────
function NextActionsPanel() {
  const [actions, setActions] = useState<MyActionsResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [showAll, setShowAll] = useState(false);

  useEffect(() => {
    projectsApi.getMyActions()
      .then(setActions)
      .catch(() => setActions(null))
      .finally(() => setLoading(false));
  }, []);

  if (loading) {
    return (
      <div className="card" style={{ marginBottom: 16, padding: 24, textAlign: "center" }}>
        <Loader2 size={18} style={{ animation: "spin 1s linear infinite", color: "var(--color-ink-3)" }} />
      </div>
    );
  }

  if (!actions || actions.total_actionable === 0) {
    return (
      <div className="card" style={{ marginBottom: 16, padding: 20, textAlign: "center" }}>
        <div style={{ fontSize: 13, color: "var(--color-ink-3)" }}>
          ✨ Tidak ada tindakan mendesak — semua proyek dalam kendali
        </div>
      </div>
    );
  }

  const myTasksToShow   = showAll ? actions.my_tasks   : actions.my_tasks.slice(0, 3);
  const unassignedToShow = showAll ? actions.unassigned : actions.unassigned.slice(0, 2);

  return (
    <div className="card" style={{ marginBottom: 16 }}>
      <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between", marginBottom: 16 }}>
        <div>
          <div style={{ fontSize: 14, fontWeight: 700, color: "var(--color-ink)" }}>
            🎯 Tindakan Berikutnya
          </div>
          <div style={{ fontSize: 11, color: "var(--color-ink-3)", marginTop: 2 }}>
            {actions.my_tasks_count} tugas Anda · {actions.unassigned_count} belum ditugaskan
          </div>
        </div>
        {actions.total_actionable > 5 && (
          <button
            onClick={() => setShowAll(!showAll)}
            style={{ fontSize: 11, fontWeight: 600, color: "var(--color-accent)", background: "none", border: "none", cursor: "pointer" }}>
            {showAll ? "Tampilkan lebih sedikit" : `Lihat semua (${actions.total_actionable})`}
          </button>
        )}
      </div>

      {/* ── My tasks section ── */}
      {myTasksToShow.length > 0 && (
        <div style={{ marginBottom: unassignedToShow.length > 0 ? 16 : 0 }}>
          <div style={{ fontSize: 10, fontWeight: 700, color: "var(--color-ink-3)", textTransform: "uppercase", letterSpacing: "0.06em", marginBottom: 8 }}>
            Tugas Anda
          </div>
          <div style={{ display: "flex", flexDirection: "column", gap: 8 }}>
            {myTasksToShow.map((item) => (
              <ActionCard key={`${item.project_id}-${item.requirement_id}`} item={item} />
            ))}
          </div>
        </div>
      )}
      {/* ── Unassigned section ── */}
      {unassignedToShow.length > 0 && (
        <div>
          <div style={{ fontSize: 10, fontWeight: 700, color: "var(--color-ink-3)", textTransform: "uppercase", letterSpacing: "0.06em", marginBottom: 8 }}>
            Belum Ditugaskan — Bisa Anda Ambil
          </div>
          <div style={{ display: "flex", flexDirection: "column", gap: 8 }}>
            {unassignedToShow.map((item) => (
              <ActionCard key={`${item.project_id}-${item.requirement_id}`} item={item} muted />
            ))}
          </div>
        </div>
      )}
    </div>
  );
}

// ── Action card sub-component ───────────────────────────────────
function ActionCard({ item, muted = false }: { item: ActionItem; muted?: boolean }) {
  const meta = ACTION_TYPE_META[item.action_type];
  return (
    <Link
      href={`/dashboard/projects/${item.project_id}`}
      style={{
        display: "flex", alignItems: "center", gap: 10,
        padding: "10px 12px", borderRadius: 8, textDecoration: "none",
        backgroundColor: muted ? "var(--color-paper-2)" : meta.bg,
        border: `1px solid ${muted ? "rgba(14,13,11,0.06)" : meta.color + "22"}`,
        transition: "transform 0.15s",
      }}>
      <span style={{ fontSize: 16, flexShrink: 0 }}>{meta.icon}</span>
      <div style={{ flex: 1, minWidth: 0 }}>
        <div style={{ display: "flex", alignItems: "center", gap: 6, marginBottom: 2 }}>
          <span style={{ fontSize: 12, fontWeight: 600, color: "var(--color-ink)" }}>
            {item.requirement_name}
          </span>
          <span style={{ fontSize: 9, fontWeight: 700, padding: "1px 6px", borderRadius: 999, color: meta.color, backgroundColor: "white" }}>
            {meta.label}
          </span>
        </div>
        <div style={{ fontSize: 10, color: "var(--color-ink-3)" }}>
          {item.project_name} · {item.primary_reason}
        </div>
      </div>
      <ArrowRight size={14} style={{ color: "var(--color-ink-3)", flexShrink: 0 }} />
    </Link>
  );
}
// ── Sprint 17: Dashboard Cross-Project Event Stream ───────────
// Sprint 19: moved here from app/dashboard/projects/page.tsx — the
// roadmap explicitly wants Event Stream as the FIRST thing on the
// Command Center, not buried on the projects list page.
function DashboardEventStream() {
  const [events,      setEvents]      = useState<RecentActivityItem[]>([]);
  const [loading,     setLoading]     = useState(true);
  const [lastUpdated, setLastUpdated] = useState<string | null>(null);

  const fetchEvents = async () => {
    try {
      const data = await projectsApi.getRecentActivity(8);
      setEvents(data.results);
      setLastUpdated(
        new Date().toLocaleTimeString("id-ID", { hour: "2-digit", minute: "2-digit" })
      );
    } catch {
      // Silent failure
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchEvents();
    const interval = setInterval(fetchEvents, 30_000);   // 30-second cadence
    return () => clearInterval(interval);
  }, []);

  const actionIcon: Record<string, string> = {
    completed:           "✅",
    evidence_uploaded:   "📎",
    evidence_approved:   "✓",
    evidence_rejected:   "❌",
    stage_advanced:      "🚀",
    assigned:            "👤",
    due_date_set:        "📅",
    comment_added:       "💬",
    updated:             "✏️",
    created:             "🆕",
  };

  const relativeTime = (iso: string): string => {
    const diff    = Date.now() - new Date(iso).getTime();
    const minutes = Math.floor(diff / 60_000);
    if (minutes < 1)   return "baru saja";
    if (minutes < 60)  return `${minutes} mnt`;
    const hours = Math.floor(minutes / 60);
    if (hours < 24)    return `${hours} jam`;
    return `${Math.floor(hours / 24)} hari`;
  };

  if (loading) {
    return (
      <div className="card" style={{ marginBottom: 16 }}>
        <div style={{ fontSize: 13, fontWeight: 600, color: "var(--color-ink)", marginBottom: 8 }}>
          Event Stream
        </div>
        <div style={{ fontSize: 11, color: "var(--color-ink-3)", padding: "8px 0" }}>
          Memuat aktivitas terbaru...
        </div>
      </div>
    );
  }

  if (events.length === 0) return null;

  return (
    <div className="card" style={{ marginBottom: 16 }}>
      {/* Header */}
      <div style={{
        display: "flex", alignItems: "center",
        justifyContent: "space-between", marginBottom: 12,
      }}>
        <div style={{ display: "flex", alignItems: "center", gap: 8 }}>
          <div style={{ fontSize: 13, fontWeight: 600, color: "var(--color-ink)" }}>
            Event Stream
          </div>
          {/* Pulsing live dot */}
          <div style={{ display: "flex", alignItems: "center", gap: 4 }}>
            <div style={{
              width: 7, height: 7, borderRadius: "50%",
              backgroundColor: "var(--color-success)",
              boxShadow: "0 0 0 2px var(--color-success-light)",
            }} />
            <span style={{ fontSize: 10, color: "var(--color-success)", fontWeight: 600 }}>
              Live
            </span>
          </div>
          <span style={{ fontSize: 10, color: "var(--color-ink-3)" }}>
            Semua proyek
          </span>
        </div>
        {lastUpdated && (
          <span style={{ fontSize: 10, color: "var(--color-ink-3)" }}>
            diperbarui {lastUpdated}
          </span>
        )}
      </div>

      {/* Events */}
      <div style={{ display: "flex", flexDirection: "column", gap: 0 }}>
        {events.slice(0, 6).map((event, i) => (
          <div key={event.id} style={{
            display: "flex", gap: 10, alignItems: "flex-start",
            padding: "7px 0",
            borderBottom: i < Math.min(events.length, 6) - 1
              ? "1px solid rgba(14,13,11,0.05)"
              : "none",
          }}>
            {/* Icon */}
            <div style={{
              width: 20, height: 20, borderRadius: "50%",
              backgroundColor: "var(--color-paper-2)",
              display: "flex", alignItems: "center", justifyContent: "center",
              fontSize: 10, flexShrink: 0,
            }}>
              {actionIcon[event.action] ?? "📋"}
            </div>

            {/* Message + project name */}
            <div style={{ flex: 1, minWidth: 0 }}>
              <div style={{
                fontSize: 11, color: "var(--color-ink)", lineHeight: 1.3,
                overflow: "hidden", textOverflow: "ellipsis", whiteSpace: "nowrap",
              }}>
                {event.message}
                {event.readiness_delta != null && event.readiness_delta !== 0 && (
                  <span style={{
                    marginLeft: 6, fontSize: 9, fontWeight: 700,
                    color: event.readiness_delta > 0
                      ? "var(--color-success)"
                      : "var(--color-danger)",
                  }}>
                    {event.readiness_delta > 0 ? "+" : ""}{event.readiness_delta}%
                  </span>
                )}
              </div>
              <div style={{ fontSize: 10, color: "var(--color-ink-3)", marginTop: 1 }}>
                {event.project_name}
              </div>
            </div>

            {/* Relative time */}
            <div style={{
              fontSize: 10, color: "var(--color-ink-3)",
              whiteSpace: "nowrap", flexShrink: 0,
            }}>
              {relativeTime(event.timestamp)}
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}

// ── Sprint 18: Portfolio Intelligence Hub ─────────────────────
// Sprint 19: moved here from app/dashboard/projects/page.tsx — this
// IS the "executive overview" panel the Command Center mockup calls for.
// Bloomberg-style executive view of the entire org's project portfolio.
// 6 key metrics with week-over-week deltas (when snapshot history exists).
// Top at-risk projects listed below.
// Polls every 60 seconds — portfolio changes slowly.
function PortfolioIntelligenceHub() {
  const [intel,   setIntel]   = useState<PortfolioIntelligence | null>(null);
  const [loading, setLoading] = useState(true);

  const fetch = async () => {
    try {
      const data = await projectsApi.getPortfolioIntelligence();
      setIntel(data);
    } catch {
      // Silent failure
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetch();
    const interval = setInterval(fetch, 60_000);
    return () => clearInterval(interval);
  }, []);

  // Format Rupiah: 46000000000 → "Rp 46B"
  const formatRupiah = (amount: number): string => {
    if (amount >= 1_000_000_000) return `Rp ${(amount / 1_000_000_000).toFixed(0)}B`;
    if (amount >= 1_000_000)     return `Rp ${(amount / 1_000_000).toFixed(0)}M`;
    return `Rp ${amount.toLocaleString("id-ID")}`;
  };

  // Delta display: positive or negative with arrow + colour
  const DeltaBadge = ({
    value,
    goodWhenPositive = true,
  }: {
    value: number;
    goodWhenPositive?: boolean;
  }) => {
    if (value === 0) {
      return (
        <span style={{ fontSize: 9, color: "var(--color-ink-3)", fontWeight: 600 }}>
          = stabil
        </span>
      );
    }
    const isGood  = goodWhenPositive ? value > 0 : value < 0;
    const color   = isGood ? "var(--color-success)" : "var(--color-danger)";
    const arrow   = value > 0 ? "↑" : "↓";
    const display = `${arrow} ${Math.abs(value)}${goodWhenPositive ? "%" : ""} mnggu ini`;
    return (
      <span style={{ fontSize: 9, fontWeight: 700, color }}>
        {display}
      </span>
    );
  };

  if (loading) {
    return (
      <div className="card" style={{ marginBottom: 16 }}>
        <div style={{ fontSize: 13, fontWeight: 600, color: "var(--color-ink)", marginBottom: 8 }}>
          Portfolio Intelligence
        </div>
        <div style={{ fontSize: 11, color: "var(--color-ink-3)" }}>
          Menganalisis portofolio...
        </div>
      </div>
    );
  }

  if (!intel) return null;

  const { current, week_delta, top_at_risk, has_history } = intel;

  // 6 Bloomberg metrics
  const metrics = [
    {
      label:   "Total Proyek",
      value:   String(current.total_projects),
      delta:   null,
      color:   "var(--color-info)",
      icon:    "📁",
    },
    {
      label:         "Rata² Kesiapan",
      value:         `${current.avg_readiness}%`,
      delta:         week_delta ? (
        <DeltaBadge value={week_delta.avg_readiness} goodWhenPositive={true} />
      ) : null,
      color:
        current.avg_readiness >= 80 ? "var(--color-success)" :
        current.avg_readiness >= 50 ? "var(--color-warning)" :
                                      "var(--color-danger)",
      icon: "📈",
    },
    {
      label:   "Kritis",
      value:   String(current.critical_count),
      delta:   week_delta ? (
        <DeltaBadge value={week_delta.critical_count} goodWhenPositive={false} />
      ) : null,
      color:   current.critical_count > 0 ? "var(--color-danger)" : "var(--color-success)",
      icon:    "⚡",
    },
    {
      label:   "Risiko Tinggi",
      value:   String(current.high_risk_count),
      delta:   week_delta ? (
        <DeltaBadge value={week_delta.high_risk_count} goodWhenPositive={false} />
      ) : null,
      color:   current.high_risk_count > 0 ? "var(--color-warning)" : "var(--color-success)",
      icon:    "🔴",
    },
    {
      label:   "Terlambat",
      value:   String(current.delayed_count),
      delta:   week_delta ? (
        <DeltaBadge value={week_delta.delayed_count} goodWhenPositive={false} />
      ) : null,
      color:   current.delayed_count > 0 ? "var(--color-warning)" : "var(--color-success)",
      icon:    "⏰",
    },
    {
      label:   "Value Terlindungi",
      value:   formatRupiah(current.revenue_protected),
      delta:   null,
      color:   "var(--color-accent)",
      icon:    "💰",
    },
  ];

  return (
    <div className="card" style={{ marginBottom: 16 }}>
      {/* Header */}
      <div style={{
        display: "flex", alignItems: "center",
        justifyContent: "space-between", marginBottom: 14,
      }}>
        <div>
          <div style={{ fontSize: 13, fontWeight: 600, color: "var(--color-ink)" }}>
            Portfolio Intelligence
          </div>
          <div style={{ fontSize: 11, color: "var(--color-ink-3)", marginTop: 2 }}>
            {has_history
              ? "Perbandingan 7 hari terakhir"
              : "Data saat ini · Jalankan snapshot untuk melihat tren minggu ini"}
          </div>
        </div>
      </div>

      {/* 6 Bloomberg metrics */}
      <div style={{
        display: "grid",
        gridTemplateColumns: "repeat(6, 1fr)",
        gap: 8,
        marginBottom: top_at_risk.length > 0 ? 16 : 0,
      }}>
        {metrics.map((m) => (
          <div key={m.label} style={{
            textAlign: "center",
            padding: "10px 6px",
            borderRadius: 8,
            backgroundColor: "var(--color-paper-2)",
          }}>
            <div style={{ fontSize: 13, marginBottom: 4 }}>{m.icon}</div>
            <div style={{
              fontSize: 16, fontWeight: 800,
              color: m.color, lineHeight: 1, marginBottom: 3,
            }}>
              {m.value}
            </div>
            <div style={{
              fontSize: 9, color: "var(--color-ink-3)",
              marginBottom: 3, lineHeight: 1.2,
            }}>
              {m.label}
            </div>
            {m.delta && (
              <div>{m.delta}</div>
            )}
          </div>
        ))}
      </div>

      {/* Top at-risk mini-table */}
      {top_at_risk.length > 0 && (
        <div>
          <div style={{
            fontSize: 10, fontWeight: 700, color: "var(--color-ink-3)",
            textTransform: "uppercase", letterSpacing: "0.06em",
            marginBottom: 8,
          }}>
            Proyek Berisiko Tertinggi
          </div>
          <div style={{ display: "flex", flexDirection: "column", gap: 5 }}>
            {top_at_risk.map((p: PortfolioAtRiskProject) => (
              <div key={p.id} style={{
                display: "flex", alignItems: "center", gap: 10,
                padding: "7px 10px", borderRadius: 7,
                backgroundColor: "var(--color-paper-2)",
                cursor: "pointer",
              }}
              onClick={() => window.location.href = `/dashboard/projects/${p.id}`}
              >
                {/* Readiness bar */}
                <div style={{ minWidth: 32, textAlign: "center" }}>
                  <div style={{
                    fontSize: 12, fontWeight: 800,
                    color: p.readiness >= 80 ? "var(--color-success)" :
                           p.readiness >= 50 ? "var(--color-warning)" :
                                               "var(--color-danger)",
                  }}>
                    {p.readiness}%
                  </div>
                </div>
                {/* Name */}
                <div style={{ flex: 1, fontSize: 11, fontWeight: 600, color: "var(--color-ink)" }}>
                  {p.name}
                </div>
                {/* Risk badge */}
                <span style={{
                  fontSize: 9, fontWeight: 700,
                  padding: "2px 7px", borderRadius: 999,
                  backgroundColor:
                    p.risk_level === "high"   ? "var(--color-danger-light)"  :
                    p.risk_level === "medium" ? "var(--color-warning-light)" :
                                                "var(--color-success-light)",
                  color:
                    p.risk_level === "high"   ? "var(--color-danger)"  :
                    p.risk_level === "medium" ? "var(--color-warning)" :
                                                "var(--color-success)",
                }}>
                  {p.risk_display}
                </span>
                {/* Blocker badge */}
                {p.blocking > 0 && (
                  <span style={{
                    fontSize: 9, fontWeight: 700,
                    color: "var(--color-danger)",
                  }}>
                    ⚡ {p.blocking} blokir
                  </span>
                )}
                {/* Next action */}
                {p.next_action && (
                  <span style={{
                    fontSize: 10, color: "var(--color-ink-3)",
                    whiteSpace: "nowrap", maxWidth: 120,
                    overflow: "hidden", textOverflow: "ellipsis",
                  }}>
                    → {p.next_action}
                  </span>
                )}
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}

// ── Sprint 19: highest-priority-project focus row ─────────────
// Per your call: instead of a portfolio-wide (nonexistent) version
// of Dependency Graph / Decision Engine / Risk Forecast, show these
// three for whichever single project needs attention most — reusing
// intel.top_at_risk[0] that Portfolio Intelligence already computes.
function TopPriorityFocus({
  projectId,
  projectName,
}: {
  projectId:   string;
  projectName: string;
}) {
  return (
    <div style={{ marginBottom: 16 }}>
      <div style={{ display: "flex", alignItems: "center", gap: 8, marginBottom: 10 }}>
        <span style={{
          fontSize: 11, fontWeight: 700, color: "var(--color-ink-3)",
          textTransform: "uppercase", letterSpacing: "0.06em",
        }}>
          Fokus Hari Ini
        </span>
        <Link
          href={`/dashboard/projects/${projectId}`}
          style={{ fontSize: 12, fontWeight: 600, color: "var(--color-accent)", textDecoration: "none" }}
        >
          {projectName} →
        </Link>
      </div>
      <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr 1fr", gap: 16 }}>
        <DependencyGraphPanel projectId={projectId} />
        <DecisionEnginePanel projectId={projectId} />
        <RiskForecastPanel projectId={projectId} />
      </div>
    </div>
  );
}
// ── Main dashboard ────────────────────────────────────────────
export default function DashboardPage() {
  const { user } = useAuth();
  const [portfolio,  setPortfolio]  = useState<PortfolioRow[]>([]);
  const [projects,   setProjects]   = useState<Project[]>([]);
  const [loading,    setLoading]    = useState(true);
  // Sprint 19: highest-priority project for the "Fokus Hari Ini" row.
  // One-time fetch (not polled) — PortfolioIntelligenceHub already
  // polls the same endpoint every 60s for its own display, so this
  // stays independent on purpose rather than modifying that
  // already-proven component's interface.
  const [topProject, setTopProject] = useState<PortfolioAtRiskProject | null>(null);

  useEffect(() => {
    Promise.all([
      projectsApi.getPortfolio(),
      projectsApi.list(),
    ])
      .then(([rows, projs]) => {
        setPortfolio(rows);
        setProjects(projs);
      })
      .catch(() => {
        setPortfolio([]);
        setProjects([]);
      })
      .finally(() => setLoading(false));

    projectsApi.getPortfolioIntelligence()
      .then((intel: PortfolioIntelligence) => setTopProject(intel.top_at_risk?.[0] ?? null))
      .catch(() => setTopProject(null));
  }, []);

  // Derive summary stats
  const totalProyek   = portfolio.length;

  // Sprint 1: count total alerts across all projects
  const totalAlerts   = projects.reduce((s, p) => s + (p.alerts?.length ?? 0), 0);
  const criticalCount = projects.reduce(
    (s, p) => s + (p.alerts?.filter((a) => a.level === "critical").length ?? 0), 0
  );

  const hour     = new Date().getHours();
  const greeting = hour < 12 ? "Selamat pagi" : hour < 17 ? "Selamat siang" : "Selamat malam";

  return (
    <div style={{ maxWidth: 1200, margin: "0 auto" }}>

      {/* ── Hero ── */}
      <div className="page-header">
        <div>
          <h1 className="page-title">
            {greeting}, {user?.full_name?.split(" ")[0] ?? "Admin"} 👋
          </h1>
          <p className="page-subtitle">
            {totalAlerts > 0
              ? `${criticalCount > 0 ? `⚡ ${criticalCount} alert kritis —` : ""} ${totalAlerts} hal perlu perhatian hari ini`
              : `Ringkasan performa platform — ${totalProyek} proyek terdaftar`
            }
          </p>
        </div>
      </div>
      
      <NextActionsPanel />

      {/* ── Sprint 19: Event Stream — the FIRST thing after Next Actions.
          Roadmap: "Event Stream moves to TOP LEFT — the first thing
          you see. Not readiness score. Not risk number. The EVENT
          that caused those numbers." ── */}
      <DashboardEventStream />

      {/* ── Sprint 19: highest-priority project focus row.
          Dependency Graph / Decision Engine / Risk Forecast only
          exist per-project (no portfolio-wide aggregate version),
          so we show these for whichever project needs attention
          most right now, per your call. ── */}
      {topProject && (
        <TopPriorityFocus projectId={topProject.id} projectName={topProject.name} />
      )}

      {/* ── Sprint 19: Portfolio Intelligence Hub — moved from
          /dashboard/projects. This IS the "executive overview"
          the roadmap calls for, and supersedes the old 6-card
          Summary Metrics grid (same numbers, but with real
          week-over-week deltas). ── */}
      <PortfolioIntelligenceHub />

      {/* ── Portfolio Intelligence Table ── */}
      <div className="card" style={{ marginBottom: 20 }}>
        <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between", marginBottom: 16 }}>
          <div>
            <div style={{ display: "flex", alignItems: "center", gap: 8, marginBottom: 4 }}>
              <Building2 size={14} style={{ color: "var(--color-accent)" }} />
              <span style={{ fontSize: 11, fontWeight: 700, color: "var(--color-accent)", textTransform: "uppercase", letterSpacing: "0.08em" }}>
                Intelligence Overview
              </span>
            </div>
            <div style={{ fontSize: 16, fontWeight: 600, color: "var(--color-ink)" }}>
              Project Portfolio
            </div>
          </div>
          <Link href="/dashboard/projects" className="btn-ghost btn-sm" style={{ display: "flex", alignItems: "center", gap: 4 }}>
            Semua Proyek <ArrowRight size={12} />
          </Link>
        </div>

        {loading ? (
          <div style={{ display: "flex", alignItems: "center", justifyContent: "center", height: 120, gap: 8, color: "var(--color-ink-3)" }}>
            <Loader2 size={16} style={{ animation: "spin 1s linear infinite" }} />
            <span style={{ fontSize: 12 }}>Memuat portfolio…</span>
          </div>
        ) : (
          <PortfolioTable rows={portfolio} projects={projects} />
        )}
      </div>

      {/* ── Sprint 1: Three-column intelligence row ── */}
      <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr 1fr", gap: 16, marginBottom: 20 }}>

        {/* Alerts Ledger */}
        <div className="card">
          <div style={{ display: "flex", alignItems: "center", gap: 8, marginBottom: 16 }}>
            <AlertTriangle size={14} style={{ color: criticalCount > 0 ? "var(--color-danger)" : "var(--color-warning)" }} />
            <span style={{ fontSize: 13, fontWeight: 600, color: "var(--color-ink)" }}>
              Alerts Ledger
            </span>
            {totalAlerts > 0 && (
              <span style={{ marginLeft: "auto", fontSize: 10, fontWeight: 700, padding: "2px 7px", borderRadius: 999, backgroundColor: criticalCount > 0 ? "var(--color-danger)" : "var(--color-warning)", color: "white" }}>
                {totalAlerts}
              </span>
            )}
          </div>
          {loading ? (
            <div style={{ display: "flex", justifyContent: "center", padding: 24 }}>
              <Loader2 size={16} style={{ animation: "spin 1s linear infinite", color: "var(--color-ink-3)" }} />
            </div>
          ) : (
            <AlertsLedger projects={projects} />
          )}
        </div>

        {/* Readiness Dimensions */}
        <div className="card">
          <div style={{ fontSize: 13, fontWeight: 600, color: "var(--color-ink)", marginBottom: 4 }}>
            Kesiapan per Dimensi
          </div>
          <div style={{ fontSize: 11, color: "var(--color-ink-3)", marginBottom: 16 }}>
            Rata-rata semua proyek
          </div>
          {loading ? (
            <div style={{ display: "flex", justifyContent: "center", padding: 24 }}>
              <Loader2 size={16} style={{ animation: "spin 1s linear infinite", color: "var(--color-ink-3)" }} />
            </div>
          ) : projects.length === 0 ? (
            <div style={{ fontSize: 12, color: "var(--color-ink-3)", fontStyle: "italic" }}>Belum ada proyek</div>
          ) : (
            (() => {
              // Average each dimension across all projects
              const dims = ["inventory", "compliance", "site_plan", "sales_setup"] as const;
              const dimLabels: Record<string, string> = {
                inventory:   "Inventori Unit",
                compliance:  "Perizinan",
                site_plan:   "Site Plan",
                sales_setup: "Setup Penjualan",
              };
              return dims.map((dim) => {
                const avg = projects.length
                  ? Math.round(
                      projects.reduce((s, p) => s + (p.readiness_dimensions?.[dim] ?? 100), 0)
                      / projects.length
                    )
                  : 100;
                return (
                  <DimensionBar key={dim} label={dimLabels[dim]} value={avg} />
                );
              });
            })()
          )}
        </div>

        {/* Collection Efficiency */}
        <div className="card">
          <div style={{ fontSize: 13, fontWeight: 600, color: "var(--color-ink)", marginBottom: 4 }}>
            Efisiensi Penagihan
          </div>
          <div style={{ fontSize: 11, color: "var(--color-ink-3)", marginBottom: 16 }}>
            AR semua proyek
          </div>
          {loading ? (
            <div style={{ display: "flex", justifyContent: "center", padding: 24 }}>
              <Loader2 size={16} style={{ animation: "spin 1s linear infinite", color: "var(--color-ink-3)" }} />
            </div>
          ) : (
            <CollectionPanel projects={projects} />
          )}
        </div>
      </div>

      {/* ── Notifications ──
          Sprint 19: dropped the mock "Log Aktivitas" card that lived
          alongside this — DashboardEventStream above now covers that
          exact need with real data. Keeping a fake static log next to
          a real live one would just be confusing. ── */}
      <div className="card">
        <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between", marginBottom: 16 }}>
          <div style={{ fontSize: 14, fontWeight: 600, color: "var(--color-ink)" }}>Notifikasi</div>
          <span style={{ fontSize: 10, fontWeight: 700, padding: "2px 8px", borderRadius: 999, backgroundColor: "var(--color-danger)", color: "white" }}>
            {NOTIFIKASI.filter((n) => !n.dibaca).length} baru
          </span>
        </div>
        {NOTIFIKASI.slice(0, 4).map((n) => {
          const iconMap  = { info: Info, sukses: CheckCircle2, peringatan: AlertTriangle };
          const colorMap = { info: "var(--color-info)", sukses: "var(--color-success)", peringatan: "var(--color-warning)" };
          const Icon     = iconMap[n.tipe];
          return (
            <div key={n.id} style={{ display: "flex", gap: 10, marginBottom: 12, padding: "10px 12px", backgroundColor: n.dibaca ? "transparent" : "var(--color-paper-2)", borderRadius: 6 }}>
              <Icon size={14} style={{ color: colorMap[n.tipe], marginTop: 1, flexShrink: 0 }} />
              <div style={{ flex: 1, minWidth: 0 }}>
                <div style={{ fontSize: 12, fontWeight: 500, color: "var(--color-ink)", marginBottom: 2 }}>{n.judul}</div>
                <div style={{ fontSize: 11, color: "var(--color-ink-3)", lineHeight: 1.4 }}>{n.pesan}</div>
                <div style={{ fontSize: 10, color: "var(--color-ink-3)", marginTop: 4 }}>{n.waktu}</div>
              </div>
              {!n.dibaca && <div style={{ width: 6, height: 6, borderRadius: "50%", backgroundColor: "var(--color-accent)", flexShrink: 0, marginTop: 4 }} />}
            </div>
          );
        })}
      </div>
    </div>
  );
}
