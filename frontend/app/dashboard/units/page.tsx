// =============================================================================
// === frontend/app/dashboard/units/page.tsx ===
// =============================================================================
/**
 * Units list — wired to real units API.
 * Currently shows all units for the logged-in developer's organization.
 * Supports filter by status and project.
 */
"use client";

import { Project, projectsApi } from "@/lib/api/projects";
import { Unit, unitsApi } from "@/lib/api/units";
import { badgeStatus, labelStatus, rupiah, warnaProgres } from "@/lib/mock-data";
import {
  Home, Loader2, Plus, Search, TrendingUp, Users
} from "lucide-react";
import Link from "next/link";
import { useEffect, useState } from "react";

const STATUS_TABS = [
  { key: "semua",      label: "Semua"        },
  { key: "tersedia",   label: "Tersedia"     },
  { key: "proses",     label: "Proses"       },
  { key: "terjual",    label: "Terjual"      },
  { key: "serah_terima", label: "Serah Terima" },
];

export default function UnitsPage() {
  const [units,    setUnits]    = useState<Unit[]>([]);
  const [projects, setProjects] = useState<Project[]>([]);
  const [loading,  setLoading]  = useState(true);
  const [error,    setError]    = useState<string | null>(null);
  const [activeTab, setActiveTab] = useState("semua");
  const [projectFilter, setProjectFilter] = useState("semua");
  const [search, setSearch] = useState("");

  useEffect(() => {
    Promise.all([unitsApi.list(), projectsApi.list()])
      .then(([u, p]) => { setUnits(u); setProjects(p); })
      .catch(() => setError("Gagal memuat data unit"))
      .finally(() => setLoading(false));
  }, []);

  if (loading) {
    return (
      <div style={{ display: "flex", alignItems: "center", justifyContent: "center", height: 300, gap: 10, color: "var(--color-ink-3)" }}>
        <Loader2 size={18} style={{ animation: "spin 1s linear infinite" }} />
        <span style={{ fontSize: 13 }}>Memuat unit…</span>
      </div>
    );
  }

  if (error) {
    return <div style={{ padding: 24, textAlign: "center", color: "var(--color-danger)", fontSize: 13 }}>{error}</div>;
  }

  const filtered = units
    .filter((u) => activeTab === "semua" || u.status === activeTab)
    .filter((u) => projectFilter === "semua" || u.project === projectFilter)
    .filter((u) => !search || u.unit_number.toLowerCase().includes(search.toLowerCase()) || (u.buyer_name ?? "").toLowerCase().includes(search.toLowerCase()));

  const stats = {
    total:      units.length,
    tersedia:   units.filter((u) => u.status === "tersedia").length,
    terjual:    units.filter((u) => u.status === "terjual").length,
    proses:     units.filter((u) => u.status === "proses").length,
  };

  return (
    <div style={{ maxWidth: 1100, margin: "0 auto" }}>

      {/* ── Page header ── */}
      <div className="page-header" style={{ display: "flex", alignItems: "flex-start", justifyContent: "space-between" }}>
        <div>
          <h1 className="page-title">Semua Unit</h1>
          <p className="page-subtitle">{units.length} unit terdaftar di semua proyek</p>
        </div>
        <button className="btn-accent" style={{ flexShrink: 0 }}>
          <Plus size={15} /> Tambah Unit
        </button>
      </div>

      {/* ── Summary strip ── */}
      <div style={{ display: "grid", gridTemplateColumns: "repeat(4, 1fr)", gap: 12, marginBottom: 20 }}>
        {[
          { label: "Total Unit",   value: units.length,                                         icon: Home,       color: "var(--color-accent)",  bg: "var(--color-accent-light)"  },
          { label: "Tersedia",     value: units.filter((u) => u.status === "tersedia").length,   icon: Home,       color: "var(--color-info)",    bg: "var(--color-info-light)"    },
          { label: "Proses",       value: units.filter((u) => u.status === "proses").length,     icon: TrendingUp, color: "var(--color-warning)", bg: "var(--color-warning-light)" },
          { label: "Terjual",      value: units.filter((u) => u.status === "terjual").length,    icon: Users,      color: "var(--color-success)", bg: "var(--color-success-light)" },
        ].map((s) => (
          <div key={s.label} className="metric-card">
            <div style={{ display: "flex", alignItems: "flex-start", justifyContent: "space-between", marginBottom: 10 }}>
              <div className="metric-label">{s.label}</div>
              <div style={{ width: 30, height: 30, borderRadius: 6, backgroundColor: s.bg, display: "flex", alignItems: "center", justifyContent: "center" }}>
                <s.icon size={14} style={{ color: s.color }} />
              </div>
            </div>
            <div className="metric-value">{s.value}</div>
          </div>
        ))}
      </div>

      {/* ── Filters ── */}
      <div style={{ display: "flex", alignItems: "center", gap: 10, marginBottom: 16 }}>
        {/* Search */}
        <div style={{ display: "flex", alignItems: "center", gap: 8, padding: "8px 12px", backgroundColor: "white", border: "1px solid rgba(14,13,11,0.10)", borderRadius: 6, flex: 1, maxWidth: 260 }}>
          <Search size={13} style={{ color: "var(--color-ink-3)", flexShrink: 0 }} />
          <input
            type="text" placeholder="Cari unit atau pembeli…"
            value={search} onChange={(e) => setSearch(e.target.value)}
            style={{ border: "none", outline: "none", fontSize: 13, fontFamily: "var(--font-sans)", color: "var(--color-ink)", backgroundColor: "transparent", width: "100%" }}
          />
        </div>
        {/* Project filter */}
        <select
          value={projectFilter} onChange={(e) => setProjectFilter(e.target.value)}
          className="form-select" style={{ maxWidth: 200, fontSize: 13 }}
        >
          <option value="semua">Semua Proyek</option>
          {projects.map((p) => (
            <option key={p.id} value={p.id}>{p.name}</option>
          ))}
        </select>
      </div>

      {/* ── Status tabs ── */}
      <div className="card" style={{ padding: 0, overflow: "hidden" }}>
        <div style={{ display: "flex", borderBottom: "1px solid rgba(14,13,11,0.08)", padding: "0 16px" }}>
          {STATUS_TABS.map((tab) => {
            const count = tab.key === "semua" ? units.length : units.filter((u) => u.status === tab.key).length;
            const isActive = activeTab === tab.key;
            return (
              <button key={tab.key} onClick={() => setActiveTab(tab.key)}
                style={{ padding: "14px 14px", fontSize: 12, fontWeight: isActive ? 600 : 400, color: isActive ? "var(--color-accent)" : "var(--color-ink-3)", backgroundColor: "transparent", border: "none", borderBottom: isActive ? "2px solid var(--color-accent)" : "2px solid transparent", cursor: "pointer", display: "flex", alignItems: "center", gap: 5, marginBottom: -1 }}
              >
                {tab.label}
                <span style={{ fontSize: 10, fontWeight: 600, backgroundColor: isActive ? "var(--color-accent-light)" : "var(--color-paper-2)", color: isActive ? "var(--color-accent)" : "var(--color-ink-3)", padding: "1px 5px", borderRadius: 999 }}>
                  {count}
                </span>
              </button>
            );
          })}
        </div>

        {/* ── Table ── */}
        <table className="data-table">
          <thead>
            <tr>
              <th>No. Unit</th>
              <th>Tipe</th>
              <th>Proyek</th>
              <th>Harga</th>
              <th>Pembeli</th>
              <th>Progres</th>
              <th>Status</th>
              <th>Aksi</th>
            </tr>
          </thead>
          <tbody>
            {filtered.map((u) => (
              <tr key={u.id}>
                <td>
                  <span style={{ fontSize: 13, fontWeight: 600, color: "var(--color-ink)" }}>{u.unit_number}</span>
                </td>
                <td style={{ fontSize: 12, color: "var(--color-ink-3)" }}>{u.unit_type}</td>
                <td style={{ fontSize: 12, color: "var(--color-ink-3)" }}>{u.project_name}</td>
                <td style={{ fontSize: 13, fontWeight: 500 }}>{rupiah(u.price)}</td>
                <td>
                  {u.buyer_name ? (
                    <div style={{ display: "flex", alignItems: "center", gap: 6 }}>
                      <div style={{ width: 24, height: 24, borderRadius: "50%", backgroundColor: "var(--color-accent-light)", display: "flex", alignItems: "center", justifyContent: "center", fontSize: 9, fontWeight: 700, color: "var(--color-accent)", flexShrink: 0 }}>
                        {u.buyer_name.split(" ").map((n) => n[0]).join("").slice(0, 2)}
                      </div>
                      <span style={{ fontSize: 12 }}>{u.buyer_name}</span>
                    </div>
                  ) : (
                    <span style={{ fontSize: 12, color: "var(--color-ink-3)" }}>—</span>
                  )}
                </td>
                <td style={{ minWidth: 100 }}>
                  <div style={{ display: "flex", alignItems: "center", gap: 8 }}>
                    <div className="progress-bar" style={{ flex: 1 }}>
                      <div className="progress-fill" style={{ width: `${u.progress}%`, backgroundColor: warnaProgres(u.progress) }} />
                    </div>
                    <span style={{ fontSize: 11, fontWeight: 600, color: warnaProgres(u.progress), flexShrink: 0 }}>{u.progress}%</span>
                  </div>
                </td>
                <td>
                  <span className={`badge ${badgeStatus(u.status)}`}>{u.status_display || labelStatus(u.status)}</span>
                </td>
                <td>
                  <Link href={`/dashboard/construction`} className="btn-ghost btn-sm" style={{ display: "inline-flex", alignItems: "center", gap: 4, fontSize: 11 }}>
                    Timeline
                  </Link>
                </td>
              </tr>
            ))}
            {filtered.length === 0 && (
              <tr>
                <td colSpan={8} style={{ textAlign: "center", padding: 40, color: "var(--color-ink-3)", fontSize: 13 }}>
                  Tidak ada unit untuk filter ini
                </td>
              </tr>
            )}
          </tbody>
        </table>

        <div style={{ padding: "12px 16px", borderTop: "1px solid rgba(14,13,11,0.06)", backgroundColor: "var(--color-paper)" }}>
          <span style={{ fontSize: 12, color: "var(--color-ink-3)" }}>Menampilkan {filtered.length} dari {units.length} unit</span>
        </div>
      </div>
    </div>
  );
}