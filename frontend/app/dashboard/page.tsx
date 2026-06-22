"use client";
// =============================================================================
// === frontend/app/dashboard/page.tsx ===
// =============================================================================
/**
 * Dashboard home — wired to real projects API.
 *
 * STILL MOCK (no backend yet — Sprint 3):
 *   - NOTIFIKASI  (notifications)
 *   - LOG         (activity log)
 *   - GRAFIK_PENJUALAN (sales chart)
 *   - STATISTIK.pendapatan_bulan / pertumbuhan (revenue — needs payments aggregate)
 */

import SalesChart from "@/components/charts/SalesChart";
import { Project, deriveStats, projectsApi } from "@/lib/api/projects";
import {
  GRAFIK_PENJUALAN,
  LOG,
  NOTIFIKASI,
  badgeStatus,
  warnaProgres
} from "@/lib/mock-data";
import {
  Activity,
  AlertCircle,
  ArrowRight,
  BarChart2,
  CheckCircle2,
  FolderOpen,
  Home,
  Info,
  Loader2,
  TrendingDown,
  TrendingUp
} from "lucide-react";
import Link from "next/link";
import { useEffect, useState } from "react";

// ── Metric Card ───────────────────────────────────────────────
function MetricCard({
  label,
  value,
  sub,
  trend,
  trendUp,
  icon: Icon,
  iconBg,
  iconColor,
}: {
  label: string;
  value: string;
  sub: string;
  trend?: string;
  trendUp?: boolean;
  icon: React.ElementType;
  iconBg: string;
  iconColor: string;
}) {
  return (
    <div className="metric-card">
      <div style={{ display: "flex", alignItems: "flex-start", justifyContent: "space-between", marginBottom: 12 }}>
        <div className="metric-label">{label}</div>
        <div style={{ width: 32, height: 32, borderRadius: 6, backgroundColor: iconBg, display: "flex", alignItems: "center", justifyContent: "center", flexShrink: 0 }}>
          <Icon size={15} style={{ color: iconColor }} />
        </div>
      </div>
      <div className="metric-value">{value}</div>
      <div style={{ display: "flex", alignItems: "center", gap: 6, marginTop: 8 }}>
        {trend && (
          <span style={{ display: "inline-flex", alignItems: "center", gap: 2, fontSize: 11, fontWeight: 500, color: trendUp ? "var(--color-success)" : "var(--color-danger)" }}>
            {trendUp ? <TrendingUp size={11} /> : <TrendingDown size={11} />}
            {trend}
          </span>
        )}
        <span className="metric-sub">{sub}</span>
      </div>
    </div>
  );
}

// ── Notification helpers ──────────────────────────────────────
const NOTIF_ICON   = { info: Info, sukses: CheckCircle2, peringatan: AlertCircle } as const;
const NOTIF_COLOR  = { info: "var(--color-info)", sukses: "var(--color-success)", peringatan: "var(--color-warning)" } as const;
const NOTIF_BG     = { info: "var(--color-info-light)", sukses: "var(--color-success-light)", peringatan: "var(--color-warning-light)" } as const;

// ── Dashboard Page ────────────────────────────────────────────
export default function DashboardPage() {
  const [projects, setProjects]   = useState<Project[]>([]);
  const [loading,  setLoading]    = useState(true);
  const [error,    setError]      = useState<string | null>(null);

  useEffect(() => {
    projectsApi.list()
      .then(setProjects)
      .catch(() => setError("Gagal memuat data proyek"))
      .finally(() => setLoading(false));
  }, []);

  const stats  = deriveStats(projects);
  const unread = NOTIFIKASI.filter((n) => !n.dibaca).length;

  if (loading) {
    return (
      <div style={{ display: "flex", alignItems: "center", justifyContent: "center", height: 300, gap: 10, color: "var(--color-ink-3)" }}>
        <Loader2 size={18} style={{ animation: "spin 1s linear infinite" }} />
        <span style={{ fontSize: 13 }}>Memuat data…</span>
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

  return (
    <div style={{ maxWidth: 1100, margin: "0 auto" }}>

      {/* ── Page header ── */}
      <div className="page-header">
        <h1 className="page-title">Selamat pagi, Admin 👋</h1>
        <p className="page-subtitle">
          Ringkasan performa platform — {projects[0]?.organization_name ?? "DevelopIndo"}
        </p>
      </div>

      {/* ── Metric cards ── */}
      <div style={{ display: "grid", gridTemplateColumns: "repeat(4, 1fr)", gap: 12, marginBottom: 20 }}>
        <MetricCard
          label="Total Proyek"
          value={String(projects.length)}
          sub="proyek terdaftar"
          icon={FolderOpen}
          iconBg="var(--color-info-light)"
          iconColor="var(--color-info)"
        />
        <MetricCard
          label="Unit Terjual"
          value={String(stats.units_sold)}
          sub={`dari ${stats.total_units} unit`}
          icon={Home}
          iconBg="var(--color-success-light)"
          iconColor="var(--color-success)"
        />
        <MetricCard
          label="Proyek Aktif"
          value={String(stats.units_active)}
          sub="sedang berjalan"
          icon={BarChart2}
          iconBg="var(--color-warning-light)"
          iconColor="var(--color-warning)"
        />
        <MetricCard
          label="Unit Tersedia"
          value={String(stats.units_available)}
          sub="siap dipasarkan"
          icon={TrendingUp}
          iconBg="var(--color-gold-light)"
          iconColor="var(--color-gold)"
        />
      </div>

      {/* ── Main grid — projects + notifications ── */}
      <div style={{ display: "grid", gridTemplateColumns: "1fr 340px", gap: 16, marginBottom: 16 }}>

        {/* Projects list */}
        <div className="card">
          <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between", marginBottom: 20 }}>
            <div className="section-title" style={{ marginBottom: 0 }}>Semua Proyek</div>
            <Link href="/dashboard/projects" style={{ display: "inline-flex", alignItems: "center", gap: 4, fontSize: 12, color: "var(--color-accent)", textDecoration: "none" }}>
              Lihat semua <ArrowRight size={12} />
            </Link>
          </div>

          <div style={{ display: "flex", flexDirection: "column", gap: 20 }}>
            {projects.map((p) => (
              <div key={p.id} style={{ display: "flex", alignItems: "center", gap: 14 }}>
                <div style={{ width: 36, height: 36, borderRadius: 6, backgroundColor: "var(--color-paper-2)", display: "flex", alignItems: "center", justifyContent: "center", fontSize: 13, fontWeight: 700, color: "var(--color-ink-3)", flexShrink: 0 }}>
                  {p.name.charAt(0)}
                </div>
                <div style={{ flex: 1, minWidth: 0 }}>
                  <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between", marginBottom: 6 }}>
                    <div style={{ fontSize: 13, fontWeight: 500, color: "var(--color-ink)", overflow: "hidden", textOverflow: "ellipsis", whiteSpace: "nowrap" }}>
                      {p.name}
                    </div>
                    <div style={{ fontSize: 13, fontWeight: 600, color: "var(--color-ink)", marginLeft: 12, flexShrink: 0 }}>
                      {p.overall_progress}%
                    </div>
                  </div>
                  <div className="progress-bar" style={{ marginBottom: 6 }}>
                    <div className="progress-fill" style={{ width: `${p.overall_progress}%`, backgroundColor: warnaProgres(p.overall_progress) }} />
                  </div>
                  <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between" }}>
                    <span style={{ fontSize: 11, color: "var(--color-ink-3)" }}>{p.location}</span>
                    <div style={{ display: "flex", alignItems: "center", gap: 8 }}>
                      <span className={`badge ${badgeStatus(p.status)}`}>{p.status_display}</span>
                      <span style={{ fontSize: 11, color: "var(--color-ink-3)" }}>
                        {p.units_sold}/{p.total_units} unit
                      </span>
                    </div>
                  </div>
                </div>
              </div>
            ))}
          </div>
        </div>

        {/* Notifications — mock until Sprint 3 */}
        <div className="card">
          <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between", marginBottom: 20 }}>
            <div className="section-title" style={{ marginBottom: 0 }}>Notifikasi</div>
            <span className="badge badge-red">{unread} baru</span>
          </div>
          <div style={{ display: "flex", flexDirection: "column", gap: 8 }}>
            {NOTIFIKASI.slice(0, 5).map((n) => {
              const Icon = NOTIF_ICON[n.tipe];
              return (
                <div key={n.id} style={{ display: "flex", gap: 12, padding: "10px 12px", borderRadius: 6, backgroundColor: !n.dibaca ? NOTIF_BG[n.tipe] : "transparent" }}>
                  <Icon size={15} style={{ color: NOTIF_COLOR[n.tipe], flexShrink: 0, marginTop: 1 }} />
                  <div style={{ minWidth: 0 }}>
                    <div style={{ fontSize: 12, fontWeight: 500, color: "var(--color-ink)", lineHeight: 1.3 }}>{n.judul}</div>
                    <div style={{ fontSize: 11, color: "var(--color-ink-3)", marginTop: 2, lineHeight: 1.4 }}>{n.pesan}</div>
                    <div style={{ fontSize: 10, color: "var(--color-ink-3)", marginTop: 4 }}>{n.waktu}</div>
                  </div>
                  {!n.dibaca && <div style={{ width: 6, height: 6, borderRadius: "50%", backgroundColor: NOTIF_COLOR[n.tipe], flexShrink: 0, marginTop: 4 }} />}
                </div>
              );
            })}
          </div>
          <Link href="/dashboard/notifikasi" style={{ display: "inline-flex", alignItems: "center", gap: 4, fontSize: 12, color: "var(--color-accent)", textDecoration: "none", marginTop: 12 }}>
            Semua notifikasi <ArrowRight size={12} />
          </Link>
        </div>
      </div>

      {/* ── Bottom grid — chart + activity log (both still mock — Sprint 3) ── */}
      <div style={{ display: "grid", gridTemplateColumns: "1fr 340px", gap: 16 }}>
        <div className="card">
          <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between", marginBottom: 20 }}>
            <div>
              <div className="section-title" style={{ marginBottom: 2 }}>Grafik Penjualan</div>
              <div style={{ fontSize: 12, color: "var(--color-ink-3)" }}>6 bulan terakhir</div>
            </div>
            <span className="badge badge-green" style={{ display: "inline-flex", alignItems: "center", gap: 4 }}>
              <TrendingUp size={10} /> +14%
            </span>
          </div>
          <SalesChart data={GRAFIK_PENJUALAN} />
          <div style={{ display: "flex", gap: 20, marginTop: 16, paddingTop: 16, borderTop: "1px solid rgba(14,13,11,0.06)" }}>
            {[
              { label: "Total terjual", value: `${stats.units_sold} unit`, color: "var(--color-accent)" },
              { label: "Unit tersedia", value: `${stats.units_available} unit`, color: "var(--color-success)" },
            ].map((item) => (
              <div key={item.label} style={{ display: "flex", alignItems: "center", gap: 8 }}>
                <div style={{ width: 8, height: 8, borderRadius: "50%", backgroundColor: item.color, flexShrink: 0 }} />
                <div>
                  <div style={{ fontSize: 10, color: "var(--color-ink-3)", textTransform: "uppercase", letterSpacing: "0.04em" }}>{item.label}</div>
                  <div style={{ fontSize: 12, fontWeight: 600, color: "var(--color-ink)" }}>{item.value}</div>
                </div>
              </div>
            ))}
          </div>
        </div>

        {/* Activity log — mock until Sprint 3 */}
        <div className="card">
          <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between", marginBottom: 20 }}>
            <div className="section-title" style={{ marginBottom: 0 }}>Log Aktivitas</div>
            <Activity size={14} style={{ color: "var(--color-ink-3)" }} />
          </div>
          <div style={{ display: "flex", flexDirection: "column", gap: 0 }}>
            {LOG.map((l, i) => (
              <div key={i} style={{ display: "flex", gap: 12, paddingBottom: i < LOG.length - 1 ? 16 : 0, position: "relative" }}>
                {i < LOG.length - 1 && (
                  <div style={{ position: "absolute", left: 5, top: 14, width: 1, height: "100%", backgroundColor: "rgba(14,13,11,0.08)" }} />
                )}
                <div style={{ width: 11, height: 11, borderRadius: "50%", backgroundColor: i === 0 ? "var(--color-accent)" : "var(--color-paper-3)", border: i === 0 ? "none" : "1px solid rgba(14,13,11,0.15)", flexShrink: 0, marginTop: 3, position: "relative", zIndex: 1 }} />
                <div style={{ minWidth: 0, paddingBottom: 2 }}>
                  <div style={{ fontSize: 12, fontWeight: 500, color: "var(--color-ink)", lineHeight: 1.3 }}>{l.pengguna}</div>
                  <div style={{ fontSize: 11, color: "var(--color-ink-3)", lineHeight: 1.4, marginTop: 2 }}>{l.aksi}</div>
                  <div style={{ fontSize: 10, color: "var(--color-ink-3)", marginTop: 3, opacity: 0.7 }}>{l.waktu}</div>
                </div>
              </div>
            ))}
          </div>
        </div>
      </div>

    </div>
  );
}
