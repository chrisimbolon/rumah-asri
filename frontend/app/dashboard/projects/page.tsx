"use client";
// =============================================================================
// === frontend/app/dashboard/projects/page.tsx ===
// =============================================================================
/**
 * Projects listing — wired to real projects API.
 * Field names updated from Bahasa mock (nama, lokasi, terjual, progres)
 * to real API English (name, location, units_sold, overall_progress).
 */

import { Project, deriveStats, projectsApi } from "@/lib/api/projects";
import { badgeStatus, warnaProgres } from "@/lib/mock-data";
import {
  ArrowRight,
  Calendar,
  FolderOpen,
  Home,
  Loader2,
  MapPin,
  Plus,
  TrendingUp,
} from "lucide-react";
import Link from "next/link";
import { useEffect, useState } from "react";

export default function ProjectsPage() {
  const [projects, setProjects] = useState<Project[]>([]);
  const [loading,  setLoading]  = useState(true);
  const [error,    setError]    = useState<string | null>(null);

  useEffect(() => {
    projectsApi.list()
      .then(setProjects)
      .catch(() => setError("Gagal memuat data proyek"))
      .finally(() => setLoading(false));
  }, []);

  if (loading) {
    return (
      <div style={{ display: "flex", alignItems: "center", justifyContent: "center", height: 300, gap: 10, color: "var(--color-ink-3)" }}>
        <Loader2 size={18} style={{ animation: "spin 1s linear infinite" }} />
        <span style={{ fontSize: 13 }}>Memuat proyek…</span>
      </div>
    );
  }

  if (error) {
    return (
      <div style={{ padding: 24, textAlign: "center", color: "var(--color-danger)", fontSize: 13 }}>
        {error}
      </div>
    );
  }

  const stats         = deriveStats(projects);

  return (
    <div style={{ maxWidth: 1100, margin: "0 auto" }}>

      {/* ── Page header ── */}
      <div className="page-header" style={{ display: "flex", alignItems: "flex-start", justifyContent: "space-between" }}>
        <div>
          <h1 className="page-title">Semua Proyek</h1>
          <p className="page-subtitle">
            {projects.length} proyek terdaftar
            {projects[0]?.organization_name ? ` — ${projects[0].organization_name}` : ""}
          </p>
        </div>
        <button className="btn-accent" style={{ flexShrink: 0 }}>
          <Plus size={15} /> Tambah Proyek
        </button>
      </div>

      {/* ── Summary strip ── */}
      <div style={{ display: "grid", gridTemplateColumns: "repeat(4, 1fr)", gap: 12, marginBottom: 24 }}>
        {[
          { label: "Total Proyek",  value: String(projects.length),         sub: "proyek aktif",     icon: FolderOpen, color: "var(--color-info)",    bg: "var(--color-info-light)"    },
          { label: "Total Unit",    value: String(stats.total_units),        sub: "semua cluster",    icon: Home,       color: "var(--color-accent)",  bg: "var(--color-accent-light)"  },
          { label: "Unit Terjual",  value: String(stats.units_sold),         sub: "sudah terjual",    icon: TrendingUp, color: "var(--color-success)", bg: "var(--color-success-light)" },
          { label: "Unit Tersedia", value: String(stats.units_available),    sub: "siap dipasarkan",  icon: Home,       color: "var(--color-warning)", bg: "var(--color-warning-light)" },
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

      {/* ── Project cards grid ── */}
      <div style={{ display: "grid", gridTemplateColumns: "repeat(2, 1fr)", gap: 16 }}>
        {projects.map((p) => (
          <div
            key={p.id}
            className="card"
            style={{ transition: "box-shadow 0.2s", cursor: "pointer", position: "relative", overflow: "hidden" }}
            onMouseEnter={(e) => ((e.currentTarget as HTMLElement).style.boxShadow = "var(--shadow-card-md)")}
            onMouseLeave={(e) => ((e.currentTarget as HTMLElement).style.boxShadow = "none")}
          >
            {/* Top colour strip */}
            <div style={{ position: "absolute", top: 0, left: 0, right: 0, height: 3, backgroundColor: warnaProgres(p.overall_progress) }} />

            {/* ── Card header ── */}
            <div style={{ display: "flex", alignItems: "flex-start", justifyContent: "space-between", marginBottom: 16, paddingTop: 4 }}>
              <div style={{ flex: 1, minWidth: 0, paddingRight: 12 }}>
                <div style={{ fontSize: 16, fontWeight: 600, color: "var(--color-ink)", marginBottom: 6, lineHeight: 1.3 }}>
                  {p.name}
                </div>
                <div style={{ display: "flex", alignItems: "center", gap: 4, fontSize: 12, color: "var(--color-ink-3)" }}>
                  <MapPin size={12} /> {p.location}
                </div>
              </div>
              <span className={`badge ${badgeStatus(p.status)}`} style={{ flexShrink: 0 }}>
                {p.status_display}
              </span>
            </div>

            {/* ── Description ── */}
            <p style={{ fontSize: 13, color: "var(--color-ink-3)", lineHeight: 1.6, marginBottom: 16, fontWeight: 300 }}>
              {p.description || "—"}
            </p>

            {/* ── Progress ── */}
            <div style={{ marginBottom: 16 }}>
              <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between", marginBottom: 6 }}>
                <span style={{ fontSize: 11, color: "var(--color-ink-3)", textTransform: "uppercase", letterSpacing: "0.04em", fontWeight: 500 }}>
                  Progres keseluruhan
                </span>
                <span style={{ fontSize: 13, fontWeight: 700, color: warnaProgres(p.overall_progress) }}>
                  {p.overall_progress}%
                </span>
              </div>
              <div className="progress-bar" style={{ height: 8 }}>
                <div className="progress-fill" style={{ width: `${p.overall_progress}%`, backgroundColor: warnaProgres(p.overall_progress) }} />
              </div>
            </div>

            {/* ── Stats row ── */}
            <div style={{ display: "grid", gridTemplateColumns: "repeat(3, 1fr)", gap: 8, padding: "14px 0", borderTop: "1px solid rgba(14,13,11,0.06)", borderBottom: "1px solid rgba(14,13,11,0.06)", marginBottom: 16 }}>
              {[
                { label: "Total unit", value: String(p.total_units) },
                { label: "Terjual",    value: String(p.units_sold)  },
                { label: "Tersedia",   value: String(p.total_units - p.units_sold) },
              ].map((s) => (
                <div key={s.label} style={{ textAlign: "center" }}>
                  <div style={{ fontFamily: "var(--font-serif)", fontSize: 24, fontWeight: 600, color: "var(--color-ink)", lineHeight: 1 }}>
                    {s.value}
                  </div>
                  <div style={{ fontSize: 10, color: "var(--color-ink-3)", marginTop: 4, textTransform: "uppercase", letterSpacing: "0.04em" }}>
                    {s.label}
                  </div>
                </div>
              ))}
            </div>

            {/* ── Footer — dates + actions ── */}
            <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between" }}>
              <div style={{ display: "flex", flexDirection: "column", gap: 3 }}>
                <div style={{ display: "flex", alignItems: "center", gap: 5, fontSize: 11, color: "var(--color-ink-3)" }}>
                  <Calendar size={11} /> Mulai: {p.start_date}
                </div>
                <div style={{ display: "flex", alignItems: "center", gap: 5, fontSize: 11, color: "var(--color-ink-3)" }}>
                  <Calendar size={11} /> Target: {p.end_date}
                </div>
              </div>
              <div style={{ display: "flex", gap: 8 }}>
                <Link href={`/dashboard/units?project=${p.id}`} className="btn-ghost btn-sm" style={{ display: "inline-flex", alignItems: "center", gap: 4 }}>
                  <Home size={12} /> Unit
                </Link>
                <Link href={`/dashboard/construction`} className="btn-accent btn-sm" style={{ display: "inline-flex", alignItems: "center", gap: 4 }}>
                  Detail <ArrowRight size={12} />
                </Link>
              </div>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}
