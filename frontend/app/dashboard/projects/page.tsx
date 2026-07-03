"use client";
// ================================================
// === frontend/app/dashboard/projects/page.tsx 
// Sprint 9: Next Actions Assistant
//  Sprint 11: Visual Dependency Graph + Portfolio Scale
//  Sprint 17 : Live Event Stream + Readiness Momentum - IS implemented here
// ================================================

import {
  CreateProjectPayload,
  deriveStats,
  Project,
  projectsApi,
  RecentActivityItem,
  STAGE_META,
} from "@/lib/api/projects";
import { warnaProgres } from "@/lib/mock-data";
import {
  ArrowRight,
  Building2,
  Calendar,
  CheckCircle2,
  Circle,
  FolderOpen,
  Home,
  Loader2,
  MapPin,
  Plus,
  SortAsc,
  TrendingUp,
  X
} from "lucide-react";
import Link from "next/link";
import { useEffect, useState } from "react";

// ── Stage pipeline badge ──────────────────────────────────────
function StageBadge({ stage }: { stage: Project["stage"] }) {
  const meta = STAGE_META[stage];
  return (
    <span style={{
      fontSize: 11, fontWeight: 600, padding: "3px 10px",
      borderRadius: 999, color: meta.color, backgroundColor: meta.bg,
      letterSpacing: "0.03em",
    }}>
      {meta.label}
    </span>
  );
}

// ── Create Project Modal ──────────────────────────────────────
function CreateProjectModal({
  onClose,
  onCreated,
}: {
  onClose:   () => void;
  onCreated: (p: Project) => void;
}) {
  const [form, setForm]       = useState<CreateProjectPayload>({ name: "", location: "", description: "" });
  const [saving, setSaving]   = useState(false);
  const [error,  setError]    = useState<string | null>(null);

  const handleSubmit = async () => {
    if (!form.name.trim())     { setError("Nama proyek wajib diisi"); return; }
    if (!form.location.trim()) { setError("Lokasi wajib diisi");      return; }
    setSaving(true);
    setError(null);
    try {
      const project = await projectsApi.create(form);
      onCreated(project);
    } catch {
      setError("Gagal membuat proyek. Coba lagi.");
    } finally {
      setSaving(false);
    }
  };

  return (
    <div style={{
      position: "fixed", inset: 0, zIndex: 100,
      backgroundColor: "rgba(14,13,11,0.4)",
      display: "flex", alignItems: "center", justifyContent: "center",
      padding: 16,
    }}>
      <div style={{
        backgroundColor: "white", borderRadius: 12,
        width: "100%", maxWidth: 480,
        boxShadow: "0 20px 60px rgba(14,13,11,0.15)",
        overflow: "hidden",
      }}>
        {/* Header */}
        <div style={{
          padding: "20px 24px 16px",
          borderBottom: "1px solid rgba(14,13,11,0.06)",
          display: "flex", alignItems: "center", justifyContent: "space-between",
        }}>
          <div>
            <div style={{ display: "flex", alignItems: "center", gap: 8, marginBottom: 4 }}>
              <Building2 size={16} style={{ color: "var(--color-accent)" }} />
              <span style={{ fontSize: 11, fontWeight: 600, color: "var(--color-accent)", textTransform: "uppercase", letterSpacing: "0.08em" }}>
                Proyek Baru
              </span>
            </div>
            <h2 style={{ fontSize: 18, fontWeight: 600, color: "var(--color-ink)", margin: 0 }}>
              Tambah Proyek
            </h2>
          </div>
          <button
            onClick={onClose}
            style={{ padding: 6, borderRadius: 6, border: "none", backgroundColor: "transparent", cursor: "pointer", color: "var(--color-ink-3)" }}
          >
            <X size={18} />
          </button>
        </div>

        {/* Info banner */}
        <div style={{
          margin: "16px 24px 0",
          padding: "10px 14px",
          backgroundColor: "var(--color-info-light)",
          borderRadius: 6, fontSize: 12,
          color: "var(--color-info)", lineHeight: 1.5,
        }}>
          Proyek akan dibuat dalam tahap <strong>Draft</strong>. Anda dapat melengkapi detail perencanaan, perizinan, dan unit setelah proyek dibuat.
        </div>

        {/* Form */}
        <div style={{ padding: "20px 24px" }}>
          {error && (
            <div style={{ marginBottom: 16, padding: "10px 14px", backgroundColor: "var(--color-danger-light)", borderRadius: 6, fontSize: 12, color: "var(--color-danger)" }}>
              {error}
            </div>
          )}

          <div style={{ marginBottom: 16 }}>
            <label style={{ display: "block", fontSize: 12, fontWeight: 500, color: "var(--color-ink)", marginBottom: 6 }}>
              Nama Proyek <span style={{ color: "var(--color-danger)" }}>*</span>
            </label>
            <input
              type="text"
              placeholder="contoh: Perumahan Asri Cluster D"
              value={form.name}
              onChange={(e) => setForm({ ...form, name: e.target.value })}
              style={{
                width: "100%", padding: "10px 12px",
                border: "1px solid rgba(14,13,11,0.15)",
                borderRadius: 6, fontSize: 13,
                color: "var(--color-ink)",
                outline: "none", boxSizing: "border-box",
              }}
            />
          </div>

          <div style={{ marginBottom: 16 }}>
            <label style={{ display: "block", fontSize: 12, fontWeight: 500, color: "var(--color-ink)", marginBottom: 6 }}>
              Lokasi <span style={{ color: "var(--color-danger)" }}>*</span>
            </label>
            <input
              type="text"
              placeholder="contoh: Telanaipura, Jambi"
              value={form.location}
              onChange={(e) => setForm({ ...form, location: e.target.value })}
              style={{
                width: "100%", padding: "10px 12px",
                border: "1px solid rgba(14,13,11,0.15)",
                borderRadius: 6, fontSize: 13,
                color: "var(--color-ink)",
                outline: "none", boxSizing: "border-box",
              }}
            />
          </div>

          <div style={{ marginBottom: 24 }}>
            <label style={{ display: "block", fontSize: 12, fontWeight: 500, color: "var(--color-ink)", marginBottom: 6 }}>
              Deskripsi <span style={{ fontSize: 11, color: "var(--color-ink-3)", fontWeight: 400 }}>(opsional)</span>
            </label>
            <textarea
              placeholder="Konsep dan gambaran umum proyek..."
              value={form.description}
              onChange={(e) => setForm({ ...form, description: e.target.value })}
              rows={3}
              style={{
                width: "100%", padding: "10px 12px",
                border: "1px solid rgba(14,13,11,0.15)",
                borderRadius: 6, fontSize: 13,
                color: "var(--color-ink)", resize: "vertical",
                outline: "none", boxSizing: "border-box",
                fontFamily: "inherit",
              }}
            />
          </div>

          <div style={{ display: "flex", gap: 10 }}>
            <button
              onClick={onClose}
              className="btn-ghost"
              style={{ flex: 1 }}
              disabled={saving}
            >
              Batal
            </button>
            <button
              onClick={handleSubmit}
              className="btn-accent"
              style={{ flex: 2, display: "flex", alignItems: "center", justifyContent: "center", gap: 6 }}
              disabled={saving}
            >
              {saving ? (
                <><Loader2 size={14} style={{ animation: "spin 1s linear infinite" }} /> Membuat…</>
              ) : (
                <><Building2 size={14} /> Buat Proyek</>
              )}
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}

// ── Mini stage pipeline on each card ─────────────────────────
function CardStagePipeline({ stage }: { stage: Project["stage"] }) {
  const stages: Project["stage"][] = [
    "draft", "perencanaan", "perizinan",
    "konstruksi", "penjualan", "serah_terima", "selesai",
  ];
  const currentIdx = stages.indexOf(stage);

  return (
    <div style={{ display: "flex", alignItems: "center", gap: 0, marginBottom: 14 }}>
      {stages.map((s, i) => {
        const meta    = STAGE_META[s];
        const done    = i < currentIdx;
        const current = i === currentIdx;
        return (
          <div key={s} style={{ display: "flex", alignItems: "center", flex: 1 }}>
            <div
              title={meta.label}
              style={{
                width: 8, height: 8, borderRadius: "50%",
                backgroundColor: done || current ? meta.color : "rgba(14,13,11,0.1)",
                border: current ? `2px solid ${meta.color}` : "none",
                boxShadow: current ? `0 0 0 3px ${meta.bg}` : "none",
                flexShrink: 0,
                transition: "all 0.2s",
              }}
            />
            {i < stages.length - 1 && (
              <div style={{
                flex: 1, height: 2,
                backgroundColor: done ? "var(--color-success)" : "rgba(14,13,11,0.08)",
              }} />
            )}
          </div>
        );
      })}
    </div>
  );
}

// ── Sprint 17: Dashboard Cross-Project Event Stream ───────────
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

// ── Main page ─────────────────────────────────────────────────
export default function ProjectsPage() {
  const [projects,    setProjects]    = useState<Project[]>([]);
  const [loading,     setLoading]     = useState(true);
  const [error,       setError]       = useState<string | null>(null);
  const [showCreate,  setShowCreate]  = useState(false);
    type FilterKey = "all" | "blocking" | "high_risk" | "delayed";
  const [activeFilter, setActiveFilter] = useState<FilterKey>("all");
  const [sortByReadiness, setSortByReadiness] = useState(false);

  // Derived: filtered + sorted projects — computed from existing `projects` state
  // No new API call needed — all fields already in Project[]
  const today = new Date();
  const displayProjects = projects
    .filter((p) => {
      if (activeFilter === "blocking")  return p.blocking_count > 0;
      if (activeFilter === "high_risk") return p.risk_level === "high";
      if (activeFilter === "delayed")   return (
        !!p.end_date &&
        new Date(p.end_date) < today &&
        !["selesai", "serah_terima"].includes(p.stage)
      );
      return true;
    })
    .sort((a, b) => sortByReadiness
      ? a.readiness_score - b.readiness_score   // worst first
      : 0                                        // default API order
    );

  // Filter tabs config — counts computed live from all projects
  const filterTabs: { key: FilterKey; label: string; count: number; color: string }[] = [
    {
      key:   "all",
      label: "Semua",
      count: projects.length,
      color: "var(--color-ink)",
    },
    {
      key:   "blocking",
      label: "Ada Blokir",
      count: projects.filter(p => p.blocking_count > 0).length,
      color: "var(--color-danger)",
    },
    {
      key:   "high_risk",
      label: "Risiko Tinggi",
      count: projects.filter(p => p.risk_level === "high").length,
      color: "var(--color-warning)",
    },
    {
      key:   "delayed",
      label: "Terlambat",
      count: projects.filter(p =>
        !!p.end_date &&
        new Date(p.end_date) < today &&
        !["selesai", "serah_terima"].includes(p.stage)
      ).length,
      color: "var(--color-accent)",
    },
  ];

  useEffect(() => {
    projectsApi.list()
      .then(setProjects)
      .catch(() => setError("Gagal memuat data proyek"))
      .finally(() => setLoading(false));
  }, []);

  const handleCreated = (project: Project) => {
    setProjects((prev) => [project, ...prev]);
    setShowCreate(false);
  };

  if (loading) {
    return (
      <div style={{ display: "flex", alignItems: "center", justifyContent: "center", height: 300, gap: 10, color: "var(--color-ink-3)" }}>
        <Loader2 size={18} style={{ animation: "spin 1s linear infinite" }} />
        <span style={{ fontSize: 13 }}>Memuat proyek…</span>
      </div>
    );
  }

  if (error) {
    return <div style={{ padding: 24, textAlign: "center", color: "var(--color-danger)", fontSize: 13 }}>{error}</div>;
  }

  const stats = deriveStats(projects);

  return (
    <div style={{ maxWidth: 1100, margin: "0 auto" }}>

      {/* ── Modal ── */}
      {showCreate && (
        <CreateProjectModal
          onClose={() => setShowCreate(false)}
          onCreated={handleCreated}
        />
      )}

      {/* ── Page header ── */}
      <div className="page-header" style={{ display: "flex", alignItems: "flex-start", justifyContent: "space-between" }}>
        <div>
          <h1 className="page-title">Semua Proyek</h1>
          <p className="page-subtitle">
            {projects.length} proyek terdaftar
            {projects[0]?.organization_name ? ` — ${projects[0].organization_name}` : ""}
          </p>
        </div>
        <button
          className="btn-accent"
          style={{ flexShrink: 0, display: "flex", alignItems: "center", gap: 6 }}
          onClick={() => setShowCreate(true)}
        >
          <Plus size={15} /> Tambah Proyek
        </button>
      </div>

      {/* ── Summary strip ── */}
      <div style={{ display: "grid", gridTemplateColumns: "repeat(4, 1fr)", gap: 12, marginBottom: 24 }}>
        {[
          { label: "Total Proyek",  value: String(projects.length),      sub: "semua tahap",       icon: FolderOpen, color: "var(--color-info)",    bg: "var(--color-info-light)"    },
          { label: "Total Unit",    value: String(stats.total_units),    sub: "semua cluster",     icon: Home,       color: "var(--color-accent)",  bg: "var(--color-accent-light)"  },
          { label: "Unit Terjual",  value: String(stats.units_sold),     sub: "sudah terjual",     icon: TrendingUp, color: "var(--color-success)", bg: "var(--color-success-light)" },
          { label: "Unit Tersedia", value: String(stats.units_available),sub: "siap dipasarkan",   icon: Home,       color: "var(--color-warning)", bg: "var(--color-warning-light)" },
        ].map((s) => (
          <div key={s.label} className="metric-card">
            <div style={{ display: "flex", alignItems: "flex-start", justifyContent: "space-between", marginBottom: 10 }}>
              <div className="metric-label">{s.label}</div>
              <div style={{ width: 30, height: 30, borderRadius: 6, backgroundColor: s.bg, display: "flex", alignItems: "center", justifyContent: "center", flexShrink: 0 }}>
                <s.icon size={14} style={{ color: s.color }} />
              </div>
            </div>
            <div className="metric-value">{s.value}</div>
            <div className="metric-sub">{s.sub}</div>
          </div>
        ))}
      </div>

      {/* Sprint 17: Cross-project Event Stream */}
        <DashboardEventStream />

          {/* ── Sprint 11: Filter bar ── */}
  <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between", marginBottom: 16, flexWrap: "wrap", gap: 10 }}>
    <div style={{ display: "flex", gap: 6, flexWrap: "wrap" }}>
      {filterTabs.map((tab) => (
        <button
          key={tab.key}
          onClick={() => setActiveFilter(tab.key)}
          style={{
            padding: "5px 12px", borderRadius: 999, fontSize: 11, fontWeight: 600,
            cursor: "pointer", transition: "all 0.15s",
            border: activeFilter === tab.key ? "none" : "1px solid rgba(14,13,11,0.12)",
            backgroundColor: activeFilter === tab.key ? tab.color : "white",
            color: activeFilter === tab.key ? "white" : "var(--color-ink-3)",
          }}>
          {tab.label}
          {tab.count > 0 && (
            <span style={{
              marginLeft: 6, fontSize: 10, fontWeight: 700,
              padding: "1px 6px", borderRadius: 999,
              backgroundColor: activeFilter === tab.key ? "rgba(255,255,255,0.25)" : "rgba(14,13,11,0.06)",
              color: activeFilter === tab.key ? "white" : "var(--color-ink-3)",
            }}>
              {tab.count}
            </span>
          )}
        </button>
      ))}
    </div>
    {/* Sort toggle */}
    <button
      onClick={() => setSortByReadiness(!sortByReadiness)}
      style={{
        padding: "5px 12px", borderRadius: 999, fontSize: 11, fontWeight: 600,
        cursor: "pointer", transition: "all 0.15s",
        border: sortByReadiness ? "none" : "1px solid rgba(14,13,11,0.12)",
        backgroundColor: sortByReadiness ? "var(--color-info)" : "white",
        color: sortByReadiness ? "white" : "var(--color-ink-3)",
        display: "flex", alignItems: "center", gap: 5,
      }}>
      <SortAsc size={12} />
      {sortByReadiness ? "Kesiapan ↑ (aktif)" : "Urutkan: Kesiapan ↑"}
    </button>
  </div>

  {/* Empty filter state */}
  {displayProjects.length === 0 && projects.length > 0 && (
    <div style={{ textAlign: "center", padding: "40px 24px", color: "var(--color-ink-3)" }}>
      <div style={{ fontSize: 28, marginBottom: 8 }}>🔍</div>
      <div style={{ fontSize: 14, fontWeight: 500, marginBottom: 4 }}>
        Tidak ada proyek yang cocok
      </div>
      <div style={{ fontSize: 12 }}>
        Coba filter lain atau{" "}
        <button
          onClick={() => setActiveFilter("all")}
          style={{ color: "var(--color-accent)", background: "none", border: "none", cursor: "pointer", fontSize: 12, fontWeight: 600 }}>
          tampilkan semua
        </button>
      </div>
    </div>
  )}

      {/* ── Empty state ── */}
      {projects.length === 0 && (
        <div style={{ textAlign: "center", padding: "60px 24px" }}>
          <Building2 size={40} style={{ margin: "0 auto 16px", opacity: 0.2, display: "block" }} />
          <div style={{ fontSize: 16, fontWeight: 500, color: "var(--color-ink)", marginBottom: 8 }}>
            Belum ada proyek
          </div>
          <div style={{ fontSize: 13, color: "var(--color-ink-3)", marginBottom: 24 }}>
            Mulai dengan membuat proyek pertama Anda
          </div>
          <button
            className="btn-accent"
            style={{ display: "inline-flex", alignItems: "center", gap: 6 }}
            onClick={() => setShowCreate(true)}
          >
            <Plus size={15} /> Tambah Proyek Pertama
          </button>
        </div>
      )}

      {/* ── Project cards grid ── */}
      <div style={{ display: "grid", gridTemplateColumns: "repeat(2, 1fr)", gap: 16 }}>
        {displayProjects.map((p) => (
          <div
            key={p.id}
            className="card"
            style={{ position: "relative", overflow: "hidden", transition: "box-shadow 0.2s" }}
            onMouseEnter={(e) => ((e.currentTarget as HTMLElement).style.boxShadow = "var(--shadow-card-md)")}
            onMouseLeave={(e) => ((e.currentTarget as HTMLElement).style.boxShadow = "none")}
          >
            {/* Top colour strip by stage */}
            <div style={{
              position: "absolute", top: 0, left: 0, right: 0, height: 3,
              backgroundColor: STAGE_META[p.stage]?.color ?? "var(--color-ink-3)",
            }} />

            <div style={{ paddingTop: 8 }}>
              {/* ── Header ── */}
              <div style={{ display: "flex", alignItems: "flex-start", justifyContent: "space-between", marginBottom: 12 }}>
                <div style={{ flex: 1, minWidth: 0, paddingRight: 12 }}>
                  <div style={{ fontSize: 16, fontWeight: 600, color: "var(--color-ink)", marginBottom: 6, lineHeight: 1.3 }}>
                    {p.name}
                  </div>
                  <div style={{ display: "flex", alignItems: "center", gap: 4, fontSize: 12, color: "var(--color-ink-3)" }}>
                    <MapPin size={12} /> {p.location}
                  </div>
                </div>
                <StageBadge stage={p.stage} />
              </div>

              {/* ── Stage pipeline ── */}
              <CardStagePipeline stage={p.stage} />

              {/* ── Description ── */}
              {p.description && (
                <p style={{ fontSize: 13, color: "var(--color-ink-3)", lineHeight: 1.6, marginBottom: 14, fontWeight: 300 }}>
                  {p.description}
                </p>
              )}

              {/* ── Progress (only show if in konstruksi or later) ── */}
              {["konstruksi", "penjualan", "serah_terima", "selesai"].includes(p.stage) && (
                <div style={{ marginBottom: 14 }}>
                  <div style={{ display: "flex", justifyContent: "space-between", marginBottom: 5 }}>
                    <span style={{ fontSize: 11, color: "var(--color-ink-3)", textTransform: "uppercase", letterSpacing: "0.04em" }}>
                      Progres konstruksi
                    </span>
                    <span style={{ fontSize: 12, fontWeight: 700, color: warnaProgres(p.overall_progress) }}>
                      {p.overall_progress}%
                    </span>
                  </div>
                  <div className="progress-bar" style={{ height: 6 }}>
                    <div className="progress-fill" style={{ width: `${p.overall_progress}%`, backgroundColor: warnaProgres(p.overall_progress) }} />
                  </div>
                </div>
              )}

              {/* ── Stats row ── */}
              <div style={{
                display: "grid", gridTemplateColumns: "repeat(3, 1fr)", gap: 8,
                padding: "12px 0", marginBottom: 14,
                borderTop: "1px solid rgba(14,13,11,0.06)",
                borderBottom: "1px solid rgba(14,13,11,0.06)",
              }}>
                {[
                  { label: "Total unit", value: String(p.total_units || "—") },
                  { label: "Terjual",    value: String(p.units_sold) },
                  { label: "Tersedia",   value: String(p.total_units ? p.total_units - p.units_sold : "—") },
                ].map((s) => (
                  <div key={s.label} style={{ textAlign: "center" }}>
                    <div style={{ fontFamily: "var(--font-serif)", fontSize: 22, fontWeight: 600, color: "var(--color-ink)", lineHeight: 1 }}>
                      {s.value}
                    </div>
                    <div style={{ fontSize: 10, color: "var(--color-ink-3)", marginTop: 4, textTransform: "uppercase", letterSpacing: "0.04em" }}>
                      {s.label}
                    </div>
                  </div>
                ))}
              </div>

              {/* ── Checklist preview (show next 2 incomplete items) ── */}
              {p.stage_checklist.length > 0 && (
                <div style={{ marginBottom: 14 }}>
                  <div style={{ fontSize: 10, fontWeight: 600, color: "var(--color-ink-3)", textTransform: "uppercase", letterSpacing: "0.06em", marginBottom: 6 }}>
                    Checklist tahap ini
                  </div>
                  {p.stage_checklist.slice(0, 3).map((item, i) => (
                    <div key={i} style={{ display: "flex", alignItems: "center", gap: 6, marginBottom: 4 }}>
                      {item.done
                        ? <CheckCircle2 size={12} style={{ color: "var(--color-success)", flexShrink: 0 }} />
                        : <Circle       size={12} style={{ color: item.blocking ? "var(--color-danger)" : "var(--color-ink-3)", flexShrink: 0 }} />
                      }
                      <span style={{ fontSize: 11, color: item.done ? "var(--color-ink-3)" : "var(--color-ink)", textDecoration: item.done ? "line-through" : "none" }}>
                        {item.item}
                        {item.blocking && !item.done && (
                          <span style={{ color: "var(--color-danger)", marginLeft: 4 }}>⚡ Wajib</span>
                        )}
                      </span>
                    </div>
                  ))}
                </div>
              )}

              {/* ── Footer ── */}
              <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between" }}>
                <div style={{ fontSize: 11, color: "var(--color-ink-3)" }}>
                  {p.start_date
                    ? <span style={{ display: "flex", alignItems: "center", gap: 4 }}><Calendar size={11} /> {p.start_date} → {p.end_date ?? "?"}</span>
                    : <span style={{ fontStyle: "italic" }}>Tanggal belum ditetapkan</span>
                  }
                </div>
                <div style={{ display: "flex", gap: 8 }}>
                  <Link
                    href={`/dashboard/units?project=${p.id}`}
                    className="btn-ghost btn-sm"
                    style={{ display: "inline-flex", alignItems: "center", gap: 4 }}
                  >
                    <Home size={12} /> Unit
                  </Link>
                  <Link
                    href={`/dashboard/projects/${p.id}`}
                    className="btn-accent btn-sm"
                    style={{ display: "inline-flex", alignItems: "center", gap: 4 }}
                  >
                    Detail <ArrowRight size={12} />
                  </Link>
                </div>
              </div>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}
