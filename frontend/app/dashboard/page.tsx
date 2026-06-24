"use client";
// =============================================================================
// === frontend/app/dashboard/page.tsx ===
// =============================================================================
/**
 * DevelopIndo — Dashboard Home
 * Now features the Portfolio Intelligence Overview table
 * designed by the co-founder — the killer feature that
 * makes a developer pay for the platform.
 */

import { useAuth } from "@/context/AuthContext";
import {
  PortfolioRow, RISK_META, STAGE_META,
  TREND_META, projectsApi,
} from "@/lib/api/projects";
import {
  LOG,
  NOTIFIKASI
} from "@/lib/mock-data";
import {
  Activity, AlertTriangle, ArrowRight,
  BarChart2, Building2, CheckCircle2,
  FolderOpen, Home, Info, Loader2, TrendingUp,
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

// ── Portfolio table ───────────────────────────────────────────
function PortfolioTable({ rows }: { rows: PortfolioRow[] }) {
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
            {["Proyek", "Tahap", "Kesiapan", "Blokir", "Risiko", "Tindakan Berikutnya", "Tren"].map((h) => (
              <th key={h} style={{ padding: "10px 12px", textAlign: "left", fontSize: 10, fontWeight: 700, color: "var(--color-ink-3)", textTransform: "uppercase", letterSpacing: "0.06em", whiteSpace: "nowrap" }}>
                {h}
              </th>
            ))}
          </tr>
        </thead>
        <tbody>
          {rows.map((row, i) => {
            const stageMeta = STAGE_META[row.stage];
            const riskMeta  = RISK_META[row.risk_level];
            const trendMeta = TREND_META[row.trend];
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

// ── Main dashboard ────────────────────────────────────────────
export default function DashboardPage() {
  const { user } = useAuth();
  const [portfolio, setPortfolio] = useState<PortfolioRow[]>([]);
  const [loading,   setLoading]   = useState(true);

  useEffect(() => {
    projectsApi.getPortfolio()
      .then(setPortfolio)
      .catch(() => setPortfolio([]))
      .finally(() => setLoading(false));
  }, []);

  // Derive summary stats from portfolio
  const totalProyek    = portfolio.length;
  const unitTerjual    = portfolio.reduce((s, p) => s + p.units_sold, 0);
  const proyekAktif    = portfolio.filter((p) =>
    ["konstruksi", "penjualan"].includes(p.stage)
  ).length;
  const unitTersedia   = portfolio.reduce(
    (s, p) => s + (p.total_units - p.units_sold), 0
  );
  const avgReadiness   = portfolio.length
    ? Math.round(portfolio.reduce((s, p) => s + p.readiness_score, 0) / portfolio.length)
    : 0;
  const highRiskCount  = portfolio.filter((p) => p.risk_level === "high").length;

  const hour = new Date().getHours();
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
            Ringkasan performa platform — {portfolio[0]?.name ? `${portfolio.length} proyek aktif` : "Mulai tambahkan proyek Anda"}
          </p>
        </div>
      </div>

      {/* ── Summary metrics ── */}
      <div style={{ display: "grid", gridTemplateColumns: "repeat(6, 1fr)", gap: 12, marginBottom: 24 }}>
        {[
          { label: "Total Proyek",    value: totalProyek,   sub: "proyek terdaftar",   icon: FolderOpen, color: "var(--color-info)",    bg: "var(--color-info-light)"    },
          { label: "Unit Terjual",    value: unitTerjual,   sub: `dari ${portfolio.reduce((s,p)=>s+p.total_units,0)} unit`, icon: Home, color: "var(--color-accent)", bg: "var(--color-accent-light)" },
          { label: "Proyek Aktif",    value: proyekAktif,   sub: "sedang berjalan",    icon: BarChart2,  color: "var(--color-warning)", bg: "var(--color-warning-light)" },
          { label: "Unit Tersedia",   value: unitTersedia,  sub: "siap dipasarkan",    icon: TrendingUp, color: "var(--color-success)", bg: "var(--color-success-light)" },
          { label: "Rata² Kesiapan",  value: `${avgReadiness}%`, sub: "semua proyek", icon: CheckCircle2,color:"var(--color-success)", bg: "var(--color-success-light)" },
          { label: "Risiko Tinggi",   value: highRiskCount, sub: "butuh perhatian",    icon: AlertTriangle, color: highRiskCount > 0 ? "var(--color-danger)" : "var(--color-success)", bg: highRiskCount > 0 ? "var(--color-danger-light)" : "var(--color-success-light)" },
        ].map((s) => (
          <div key={s.label} className="metric-card">
            <div style={{ display: "flex", alignItems: "flex-start", justifyContent: "space-between", marginBottom: 8 }}>
              <div className="metric-label" style={{ fontSize: 10 }}>{s.label}</div>
              <div style={{ width: 28, height: 28, borderRadius: 6, backgroundColor: s.bg, display: "flex", alignItems: "center", justifyContent: "center", flexShrink: 0 }}>
                <s.icon size={13} style={{ color: s.color }} />
              </div>
            </div>
            <div className="metric-value" style={{ fontSize: 22 }}>{s.value}</div>
            <div className="metric-sub" style={{ fontSize: 10 }}>{s.sub}</div>
          </div>
        ))}
      </div>

      {/* ── Portfolio Intelligence Table ── */}
      <div className="card" style={{ marginBottom: 24 }}>
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
          <PortfolioTable rows={portfolio} />
        )}
      </div>

      {/* ── Bottom row — notifications + activity ── */}
      <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 16 }}>

        {/* Notifications */}
        <div className="card">
          <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between", marginBottom: 16 }}>
            <div style={{ fontSize: 14, fontWeight: 600, color: "var(--color-ink)" }}>Notifikasi</div>
            <span style={{ fontSize: 10, fontWeight: 700, padding: "2px 8px", borderRadius: 999, backgroundColor: "var(--color-danger)", color: "white" }}>
              {NOTIFIKASI.filter((n) => !n.dibaca).length} baru
            </span>
          </div>
          {NOTIFIKASI.slice(0, 4).map((n) => {
            const iconMap = { info: Info, sukses: CheckCircle2, peringatan: AlertTriangle };
            const colorMap = { info: "var(--color-info)", sukses: "var(--color-success)", peringatan: "var(--color-warning)" };
            const Icon = iconMap[n.tipe];
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

        {/* Activity log */}
        <div className="card">
          <div style={{ fontSize: 14, fontWeight: 600, color: "var(--color-ink)", marginBottom: 16, display: "flex", alignItems: "center", gap: 6 }}>
            <Activity size={14} /> Log Aktivitas
          </div>
          {LOG.map((l, i) => (
            <div key={i} style={{ display: "flex", gap: 10, marginBottom: 12 }}>
              <div style={{ width: 6, height: 6, borderRadius: "50%", backgroundColor: "var(--color-accent)", marginTop: 5, flexShrink: 0 }} />
              <div>
                <div style={{ fontSize: 12, color: "var(--color-ink)", lineHeight: 1.4 }}>
                  <span style={{ fontWeight: 500 }}>{l.pengguna}</span> — {l.aksi}
                </div>
                <div style={{ fontSize: 10, color: "var(--color-ink-3)", marginTop: 2 }}>{l.waktu}</div>
              </div>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}
