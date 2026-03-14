"use client";

import {
  PROYEK,
  STATISTIK,
  badgeStatus,
  labelStatus,
  warnaProgres,
} from "@/lib/mock-data";
import {
  Plus,
  MapPin,
  Calendar,
  Home,
  TrendingUp,
  ArrowRight,
  FolderOpen,
} from "lucide-react";
import Link from "next/link";

export default function ProjectsPage() {
  const totalTersedia =
    PROYEK.reduce((s, p) => s + p.total_unit, 0) - STATISTIK.unit_terjual;

  return (
    <div style={{ maxWidth: 1100, margin: "0 auto" }}>

      {/* ── Page header ── */}
      <div
        className="page-header"
        style={{
          display: "flex",
          alignItems: "flex-start",
          justifyContent: "space-between",
        }}
      >
        <div>
          <h1 className="page-title">Semua Proyek</h1>
          <p className="page-subtitle">
            {PROYEK.length} proyek terdaftar — PT Asri Sentosa Properti
          </p>
        </div>
        <button className="btn-accent" style={{ flexShrink: 0 }}>
          <Plus size={15} /> Tambah Proyek
        </button>
      </div>

      {/* ── Summary strip ── */}
      <div
        style={{
          display: "grid",
          gridTemplateColumns: "repeat(4, 1fr)",
          gap: 12,
          marginBottom: 24,
        }}
      >
        {[
          {
            label: "Total Proyek",
            value: String(PROYEK.length),
            sub: "proyek aktif",
            icon: FolderOpen,
            color: "var(--color-info)",
            bg: "var(--color-info-light)",
          },
          {
            label: "Total Unit",
            value: String(STATISTIK.total_unit),
            sub: "semua cluster",
            icon: Home,
            color: "var(--color-accent)",
            bg: "var(--color-accent-light)",
          },
          {
            label: "Unit Terjual",
            value: String(STATISTIK.unit_terjual),
            sub: "sudah terjual",
            icon: TrendingUp,
            color: "var(--color-success)",
            bg: "var(--color-success-light)",
          },
          {
            label: "Unit Tersedia",
            value: String(totalTersedia),
            sub: "siap dipasarkan",
            icon: Home,
            color: "var(--color-warning)",
            bg: "var(--color-warning-light)",
          },
        ].map((s) => (
          <div key={s.label} className="metric-card">
            <div
              style={{
                display: "flex",
                alignItems: "flex-start",
                justifyContent: "space-between",
                marginBottom: 10,
              }}
            >
              <div className="metric-label">{s.label}</div>
              <div
                style={{
                  width: 30,
                  height: 30,
                  borderRadius: 6,
                  backgroundColor: s.bg,
                  display: "flex",
                  alignItems: "center",
                  justifyContent: "center",
                  flexShrink: 0,
                }}
              >
                <s.icon size={14} style={{ color: s.color }} />
              </div>
            </div>
            <div className="metric-value">{s.value}</div>
            <div className="metric-sub">{s.sub}</div>
          </div>
        ))}
      </div>

      {/* ── Project cards grid ── */}
      <div
        style={{
          display: "grid",
          gridTemplateColumns: "repeat(2, 1fr)",
          gap: 16,
        }}
      >
        {PROYEK.map((p) => (
          <div
            key={p.id}
            className="card"
            style={{
              transition: "box-shadow 0.2s",
              cursor: "pointer",
              position: "relative",
              overflow: "hidden",
            }}
            onMouseEnter={(e) =>
              ((e.currentTarget as HTMLElement).style.boxShadow =
                "var(--shadow-card-md)")
            }
            onMouseLeave={(e) =>
              ((e.currentTarget as HTMLElement).style.boxShadow = "none")
            }
          >
            {/* Top colour strip */}
            <div
              style={{
                position: "absolute",
                top: 0,
                left: 0,
                right: 0,
                height: 3,
                backgroundColor: warnaProgres(p.progres),
              }}
            />

            {/* ── Card header ── */}
            <div
              style={{
                display: "flex",
                alignItems: "flex-start",
                justifyContent: "space-between",
                marginBottom: 16,
                paddingTop: 4,
              }}
            >
              <div style={{ flex: 1, minWidth: 0, paddingRight: 12 }}>
                <div
                  style={{
                    fontSize: 16,
                    fontWeight: 600,
                    color: "var(--color-ink)",
                    marginBottom: 6,
                    lineHeight: 1.3,
                  }}
                >
                  {p.nama}
                </div>
                <div
                  style={{
                    display: "flex",
                    alignItems: "center",
                    gap: 4,
                    fontSize: 12,
                    color: "var(--color-ink-3)",
                  }}
                >
                  <MapPin size={12} />
                  {p.lokasi}
                </div>
              </div>
              <span
                className={`badge ${badgeStatus(p.status)}`}
                style={{ flexShrink: 0 }}
              >
                {labelStatus(p.status)}
              </span>
            </div>

            {/* ── Description ── */}
            <p
              style={{
                fontSize: 13,
                color: "var(--color-ink-3)",
                lineHeight: 1.6,
                marginBottom: 16,
                fontWeight: 300,
              }}
            >
              {p.deskripsi}
            </p>

            {/* ── Progress ── */}
            <div style={{ marginBottom: 16 }}>
              <div
                style={{
                  display: "flex",
                  alignItems: "center",
                  justifyContent: "space-between",
                  marginBottom: 6,
                }}
              >
                <span
                  style={{
                    fontSize: 11,
                    color: "var(--color-ink-3)",
                    textTransform: "uppercase",
                    letterSpacing: "0.04em",
                    fontWeight: 500,
                  }}
                >
                  Progres keseluruhan
                </span>
                <span
                  style={{
                    fontSize: 13,
                    fontWeight: 700,
                    color: warnaProgres(p.progres),
                  }}
                >
                  {p.progres}%
                </span>
              </div>
              <div className="progress-bar" style={{ height: 8 }}>
                <div
                  className="progress-fill"
                  style={{
                    width: `${p.progres}%`,
                    backgroundColor: warnaProgres(p.progres),
                  }}
                />
              </div>
            </div>

            {/* ── Stats row ── */}
            <div
              style={{
                display: "grid",
                gridTemplateColumns: "repeat(3, 1fr)",
                gap: 8,
                padding: "14px 0",
                borderTop: "1px solid rgba(14,13,11,0.06)",
                borderBottom: "1px solid rgba(14,13,11,0.06)",
                marginBottom: 16,
              }}
            >
              {[
                { label: "Total unit", value: String(p.total_unit) },
                { label: "Terjual",    value: String(p.terjual) },
                { label: "Tersedia",   value: String(p.total_unit - p.terjual) },
              ].map((s) => (
                <div key={s.label} style={{ textAlign: "center" }}>
                  <div
                    style={{
                      fontFamily: "var(--font-serif)",
                      fontSize: 24,
                      fontWeight: 600,
                      color: "var(--color-ink)",
                      lineHeight: 1,
                    }}
                  >
                    {s.value}
                  </div>
                  <div
                    style={{
                      fontSize: 10,
                      color: "var(--color-ink-3)",
                      marginTop: 4,
                      textTransform: "uppercase",
                      letterSpacing: "0.04em",
                    }}
                  >
                    {s.label}
                  </div>
                </div>
              ))}
            </div>

            {/* ── Footer — dates + actions ── */}
            <div
              style={{
                display: "flex",
                alignItems: "center",
                justifyContent: "space-between",
              }}
            >
              <div style={{ display: "flex", flexDirection: "column", gap: 3 }}>
                <div
                  style={{
                    display: "flex",
                    alignItems: "center",
                    gap: 5,
                    fontSize: 11,
                    color: "var(--color-ink-3)",
                  }}
                >
                  <Calendar size={11} /> Mulai: {p.mulai}
                </div>
                <div
                  style={{
                    display: "flex",
                    alignItems: "center",
                    gap: 5,
                    fontSize: 11,
                    color: "var(--color-ink-3)",
                  }}
                >
                  <Calendar size={11} /> Target: {p.selesai}
                </div>
              </div>

              <div style={{ display: "flex", gap: 8 }}>
                <Link
                  href="/dashboard/units"
                  className="btn-ghost btn-sm"
                  style={{
                    display: "inline-flex",
                    alignItems: "center",
                    gap: 4,
                  }}
                >
                  <Home size={12} /> Unit
                </Link>
                <Link
                  href="/dashboard/construction"
                  className="btn-accent btn-sm"
                  style={{
                    display: "inline-flex",
                    alignItems: "center",
                    gap: 4,
                  }}
                >
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
