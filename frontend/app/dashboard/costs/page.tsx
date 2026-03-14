"use client";

import { BIAYA, PROYEK, badgeStatus, labelStatus, rupiah } from "@/lib/mock-data";
import {
  AlertTriangle,
  TrendingDown,
  TrendingUp,
  Download,
  Plus,
  CheckCircle2,
  Loader,
  BarChart3,
} from "lucide-react";
import { useState } from "react";

// ─────────────────────────────────────────────────────────────
export default function CostsPage() {
  const [selectedProject, setSelectedProject] = useState(PROYEK[0].id);

  // ── Totals ──
  const totalAnggaran  = BIAYA.reduce((s, b) => s + b.anggaran, 0);
  const totalRealisasi = BIAYA.reduce((s, b) => s + (b.realisasi ?? 0), 0);
  const totalSelisih   = totalRealisasi - totalAnggaran;
  const pctTerpakai    = Math.round((totalRealisasi / totalAnggaran) * 100);
  const itemMelebihi   = BIAYA.filter((b) => b.status === "melebihi").length;
  const itemSesuai     = BIAYA.filter((b) => b.status === "sesuai").length;
  const itemBerjalan   = BIAYA.filter((b) => b.status === "berjalan").length;

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
          <h1 className="page-title">Akuntansi Biaya</h1>
          <p className="page-subtitle">
            RAB vs realisasi biaya konstruksi — Cluster A
          </p>
        </div>
        <div style={{ display: "flex", gap: 8 }}>
          <button
            className="btn-ghost"
            style={{ display: "inline-flex", alignItems: "center", gap: 6 }}
          >
            <Download size={14} /> Ekspor Excel
          </button>
          <button
            className="btn-accent"
            style={{ display: "inline-flex", alignItems: "center", gap: 6 }}
          >
            <Plus size={14} /> Tambah Item
          </button>
        </div>
      </div>

      {/* ── Project selector ── */}
      <div
        style={{
          display: "flex",
          gap: 8,
          marginBottom: 20,
          flexWrap: "wrap",
        }}
      >
        {PROYEK.map((p) => (
          <button
            key={p.id}
            onClick={() => setSelectedProject(p.id)}
            style={{
              padding: "7px 16px",
              borderRadius: 999,
              border:
                selectedProject === p.id
                  ? "1px solid var(--color-accent)"
                  : "1px solid rgba(14,13,11,0.12)",
              backgroundColor:
                selectedProject === p.id
                  ? "var(--color-accent-light)"
                  : "white",
              color:
                selectedProject === p.id
                  ? "var(--color-accent)"
                  : "var(--color-ink-3)",
              fontSize: 12,
              fontWeight: selectedProject === p.id ? 600 : 400,
              cursor: "pointer",
              transition: "all 0.15s",
            }}
          >
            {p.nama.replace("Perumahan Asri ", "")}
          </button>
        ))}
      </div>

      {/* ── Metric cards ── */}
      <div
        style={{
          display: "grid",
          gridTemplateColumns: "repeat(4, 1fr)",
          gap: 12,
          marginBottom: 20,
        }}
      >
        {[
          {
            label:  "Total Anggaran (RAB)",
            value:  rupiah(totalAnggaran),
            sub:    `${BIAYA.length} item pekerjaan`,
            icon:   BarChart3,
            color:  "var(--color-accent)",
            bg:     "var(--color-accent-light)",
          },
          {
            label:  "Realisasi Saat Ini",
            value:  rupiah(totalRealisasi),
            sub:    `${itemSesuai + itemMelebihi} item selesai`,
            icon:   TrendingUp,
            color:  "var(--color-success)",
            bg:     "var(--color-success-light)",
          },
          {
            label:  "Selisih",
            value:  `${totalSelisih > 0 ? "+" : ""}${rupiah(totalSelisih)}`,
            sub:    totalSelisih > 0 ? "Di atas anggaran" : "Di bawah anggaran",
            icon:   totalSelisih > 0 ? TrendingUp : TrendingDown,
            color:  totalSelisih > 0 ? "var(--color-danger)" : "var(--color-success)",
            bg:     totalSelisih > 0 ? "var(--color-danger-light)" : "var(--color-success-light)",
          },
          {
            label:  "% Anggaran Terpakai",
            value:  `${pctTerpakai}%`,
            sub:    `${itemBerjalan} item masih berjalan`,
            icon:   CheckCircle2,
            color:  "var(--color-gold)",
            bg:     "var(--color-gold-light)",
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
            <div
              className="metric-value"
              style={{
                fontSize: s.value.length > 12 ? 16 : 24,
                color: s.label === "Selisih" ? s.color : "var(--color-ink)",
              }}
            >
              {s.value}
            </div>
            <div
              className="metric-sub"
              style={{
                color:
                  s.label === "Selisih"
                    ? s.color
                    : "var(--color-ink-3)",
              }}
            >
              {s.sub}
            </div>
          </div>
        ))}
      </div>

      {/* ── Alert if over budget ── */}
      {itemMelebihi > 0 && (
        <div
          style={{
            display: "flex",
            alignItems: "flex-start",
            gap: 12,
            padding: "14px 16px",
            backgroundColor: "var(--color-warning-light)",
            border: "1px solid rgba(180,83,9,0.15)",
            borderRadius: 6,
            marginBottom: 20,
          }}
        >
          <AlertTriangle
            size={16}
            style={{
              color: "var(--color-warning)",
              flexShrink: 0,
              marginTop: 1,
            }}
          />
          <div>
            <div
              style={{
                fontSize: 13,
                fontWeight: 600,
                color: "var(--color-warning-text)",
              }}
            >
              {itemMelebihi} item melebihi anggaran RAB
            </div>
            <div
              style={{
                fontSize: 12,
                color: "var(--color-warning-text)",
                opacity: 0.8,
                marginTop: 2,
              }}
            >
              Baja struktural & instalasi listrik melebihi RAB. Pertimbangkan
              revisi anggaran atau negosiasi ulang dengan kontraktor.
            </div>
          </div>
        </div>
      )}

      {/* ── Main content — table + chart ── */}
      <div
        style={{
          display: "grid",
          gridTemplateColumns: "1fr 280px",
          gap: 16,
          alignItems: "start",
        }}
      >
        {/* ── Cost table ── */}
        <div className="card" style={{ padding: 0, overflow: "hidden" }}>
          <div
            style={{
              padding: "16px 20px",
              borderBottom: "1px solid rgba(14,13,11,0.08)",
              display: "flex",
              alignItems: "center",
              justifyContent: "space-between",
            }}
          >
            <div className="section-title" style={{ marginBottom: 0 }}>
              Rincian Biaya Konstruksi
            </div>
            <span className="badge badge-blue">
              Cluster A · 2025
            </span>
          </div>

          <table className="data-table">
            <thead>
              <tr>
                <th>Item Pekerjaan</th>
                <th>Anggaran (RAB)</th>
                <th>Realisasi</th>
                <th>Selisih</th>
                <th>% Terpakai</th>
                <th>Status</th>
              </tr>
            </thead>
            <tbody>
              {BIAYA.map((b, i) => {
                const selisih =
                  b.realisasi !== null ? b.realisasi - b.anggaran : null;
                const pct =
                  b.realisasi !== null
                    ? Math.round((b.realisasi / b.anggaran) * 100)
                    : null;

                return (
                  <tr key={i}>
                    {/* Item */}
                    <td>
                      <div
                        style={{
                          display: "flex",
                          alignItems: "center",
                          gap: 8,
                        }}
                      >
                        <div
                          style={{
                            width: 8,
                            height: 8,
                            borderRadius: "50%",
                            backgroundColor:
                              b.status === "melebihi"
                                ? "var(--color-danger)"
                                : b.status === "berjalan"
                                ? "var(--color-accent)"
                                : "var(--color-success)",
                            flexShrink: 0,
                          }}
                        />
                        <span
                          style={{ fontSize: 13, fontWeight: 500 }}
                        >
                          {b.item}
                        </span>
                      </div>
                    </td>

                    {/* Anggaran */}
                    <td style={{ fontSize: 12 }}>{rupiah(b.anggaran)}</td>

                    {/* Realisasi */}
                    <td>
                      {b.realisasi !== null ? (
                        <span
                          style={{
                            fontSize: 12,
                            fontWeight: 600,
                            color:
                              b.status === "melebihi"
                                ? "var(--color-danger)"
                                : "var(--color-ink)",
                          }}
                        >
                          {rupiah(b.realisasi)}
                        </span>
                      ) : (
                        <span
                          style={{
                            fontSize: 12,
                            color: "var(--color-ink-3)",
                            fontStyle: "italic",
                            display: "flex",
                            alignItems: "center",
                            gap: 4,
                          }}
                        >
                          <Loader size={11} /> Berjalan...
                        </span>
                      )}
                    </td>

                    {/* Selisih */}
                    <td>
                      {selisih !== null ? (
                        <div
                          style={{
                            display: "flex",
                            alignItems: "center",
                            gap: 4,
                            fontSize: 12,
                            fontWeight: 600,
                            color:
                              selisih > 0
                                ? "var(--color-danger)"
                                : "var(--color-success)",
                          }}
                        >
                          {selisih > 0 ? (
                            <TrendingUp size={12} />
                          ) : (
                            <TrendingDown size={12} />
                          )}
                          {selisih > 0 ? "+" : ""}
                          {rupiah(selisih)}
                        </div>
                      ) : (
                        <span style={{ color: "var(--color-ink-3)", fontSize: 12 }}>
                          —
                        </span>
                      )}
                    </td>

                    {/* % Terpakai */}
                    <td>
                      {pct !== null ? (
                        <div
                          style={{
                            display: "flex",
                            alignItems: "center",
                            gap: 8,
                          }}
                        >
                          <div
                            className="progress-bar"
                            style={{ width: 60 }}
                          >
                            <div
                              className="progress-fill"
                              style={{
                                width: `${Math.min(pct, 100)}%`,
                                backgroundColor:
                                  pct > 100
                                    ? "var(--color-danger)"
                                    : pct > 85
                                    ? "var(--color-warning)"
                                    : "var(--color-success)",
                              }}
                            />
                          </div>
                          <span
                            style={{
                              fontSize: 11,
                              fontWeight: 600,
                              color:
                                pct > 100
                                  ? "var(--color-danger)"
                                  : "var(--color-ink-3)",
                              minWidth: 32,
                            }}
                          >
                            {pct}%
                          </span>
                        </div>
                      ) : (
                        <span style={{ color: "var(--color-ink-3)", fontSize: 12 }}>
                          —
                        </span>
                      )}
                    </td>

                    {/* Status */}
                    <td>
                      <div
                        style={{
                          display: "flex",
                          alignItems: "center",
                          gap: 5,
                        }}
                      >
                        {b.status === "melebihi" && (
                          <AlertTriangle
                            size={12}
                            style={{ color: "var(--color-danger)" }}
                          />
                        )}
                        {b.status === "sesuai" && (
                          <CheckCircle2
                            size={12}
                            style={{ color: "var(--color-success)" }}
                          />
                        )}
                        {b.status === "berjalan" && (
                          <Loader
                            size={12}
                            style={{ color: "var(--color-accent)" }}
                          />
                        )}
                        <span className={`badge ${badgeStatus(b.status)}`}>
                          {labelStatus(b.status)}
                        </span>
                      </div>
                    </td>
                  </tr>
                );
              })}
            </tbody>

            {/* Totals row */}
            <tfoot>
              <tr
                style={{
                  backgroundColor: "var(--color-paper)",
                  borderTop: "2px solid rgba(14,13,11,0.10)",
                }}
              >
                <td
                  style={{
                    fontWeight: 700,
                    fontSize: 13,
                    padding: "12px",
                  }}
                >
                  TOTAL
                </td>
                <td style={{ fontWeight: 700, fontSize: 13, padding: "12px" }}>
                  {rupiah(totalAnggaran)}
                </td>
                <td style={{ fontWeight: 700, fontSize: 13, padding: "12px" }}>
                  {rupiah(totalRealisasi)}
                </td>
                <td
                  style={{
                    fontWeight: 700,
                    fontSize: 13,
                    padding: "12px",
                    color:
                      totalSelisih > 0
                        ? "var(--color-danger)"
                        : "var(--color-success)",
                  }}
                >
                  {totalSelisih > 0 ? "+" : ""}
                  {rupiah(totalSelisih)}
                </td>
                <td style={{ padding: "12px" }}>
                  <span
                    style={{
                      fontSize: 12,
                      fontWeight: 700,
                      color:
                        pctTerpakai > 100
                          ? "var(--color-danger)"
                          : "var(--color-ink)",
                    }}
                  >
                    {pctTerpakai}%
                  </span>
                </td>
                <td style={{ padding: "12px" }} />
              </tr>
            </tfoot>
          </table>
        </div>

        {/* ── Right sidebar ── */}
        <div style={{ display: "flex", flexDirection: "column", gap: 12 }}>

          {/* Status breakdown */}
          <div className="card" style={{ padding: 16 }}>
            <div className="section-title" style={{ fontSize: 13 }}>
              Ringkasan Status
            </div>
            <div
              style={{
                display: "flex",
                flexDirection: "column",
                gap: 10,
              }}
            >
              {[
                {
                  label: "Sesuai Anggaran",
                  count: itemSesuai,
                  color: "var(--color-success)",
                  bg: "var(--color-success-light)",
                  icon: CheckCircle2,
                },
                {
                  label: "Melebihi Anggaran",
                  count: itemMelebihi,
                  color: "var(--color-danger)",
                  bg: "var(--color-danger-light)",
                  icon: AlertTriangle,
                },
                {
                  label: "Sedang Berjalan",
                  count: itemBerjalan,
                  color: "var(--color-accent)",
                  bg: "var(--color-accent-light)",
                  icon: Loader,
                },
              ].map((s) => (
                <div
                  key={s.label}
                  style={{
                    display: "flex",
                    alignItems: "center",
                    justifyContent: "space-between",
                    padding: "10px 12px",
                    backgroundColor: s.bg,
                    borderRadius: 6,
                  }}
                >
                  <div
                    style={{
                      display: "flex",
                      alignItems: "center",
                      gap: 8,
                    }}
                  >
                    <s.icon size={13} style={{ color: s.color }} />
                    <span
                      style={{
                        fontSize: 12,
                        fontWeight: 500,
                        color: s.color,
                      }}
                    >
                      {s.label}
                    </span>
                  </div>
                  <span
                    style={{
                      fontFamily: "var(--font-serif)",
                      fontSize: 22,
                      fontWeight: 600,
                      color: s.color,
                    }}
                  >
                    {s.count}
                  </span>
                </div>
              ))}
            </div>
          </div>

          {/* Budget overview visual */}
          <div className="card" style={{ padding: 16 }}>
            <div className="section-title" style={{ fontSize: 13 }}>
              Visualisasi Anggaran
            </div>

            {/* Total budget bar */}
            <div style={{ marginBottom: 16 }}>
              <div
                style={{
                  display: "flex",
                  justifyContent: "space-between",
                  marginBottom: 6,
                }}
              >
                <span style={{ fontSize: 11, color: "var(--color-ink-3)" }}>
                  Total terpakai
                </span>
                <span
                  style={{
                    fontSize: 12,
                    fontWeight: 700,
                    color:
                      pctTerpakai > 100
                        ? "var(--color-danger)"
                        : "var(--color-ink)",
                  }}
                >
                  {pctTerpakai}%
                </span>
              </div>
              <div className="progress-bar" style={{ height: 10 }}>
                <div
                  className="progress-fill"
                  style={{
                    width: `${Math.min(pctTerpakai, 100)}%`,
                    backgroundColor:
                      pctTerpakai > 100
                        ? "var(--color-danger)"
                        : pctTerpakai > 85
                        ? "var(--color-warning)"
                        : "var(--color-success)",
                  }}
                />
              </div>
            </div>

            {/* Per-item mini bars */}
            <div style={{ display: "flex", flexDirection: "column", gap: 8 }}>
              {BIAYA.map((b, i) => {
                const pct =
                  b.realisasi !== null
                    ? Math.round((b.realisasi / b.anggaran) * 100)
                    : null;
                return (
                  <div key={i}>
                    <div
                      style={{
                        display: "flex",
                        justifyContent: "space-between",
                        marginBottom: 3,
                      }}
                    >
                      <span
                        style={{
                          fontSize: 10,
                          color: "var(--color-ink-3)",
                          overflow: "hidden",
                          textOverflow: "ellipsis",
                          whiteSpace: "nowrap",
                          maxWidth: 160,
                        }}
                      >
                        {b.item}
                      </span>
                      <span
                        style={{
                          fontSize: 10,
                          fontWeight: 600,
                          color:
                            pct !== null && pct > 100
                              ? "var(--color-danger)"
                              : "var(--color-ink-3)",
                          flexShrink: 0,
                        }}
                      >
                        {pct !== null ? `${pct}%` : "—"}
                      </span>
                    </div>
                    <div className="progress-bar" style={{ height: 4 }}>
                      {pct !== null && (
                        <div
                          className="progress-fill"
                          style={{
                            width: `${Math.min(pct, 100)}%`,
                            backgroundColor:
                              pct > 100
                                ? "var(--color-danger)"
                                : pct > 85
                                ? "var(--color-warning)"
                                : "var(--color-success)",
                          }}
                        />
                      )}
                    </div>
                  </div>
                );
              })}
            </div>
          </div>

          {/* Quick actions */}
          <div className="card" style={{ padding: 16 }}>
            <div className="section-title" style={{ fontSize: 13 }}>
              Aksi Cepat
            </div>
            <div style={{ display: "flex", flexDirection: "column", gap: 8 }}>
              {[
                { label: "Ekspor RAB ke Excel", icon: Download },
                { label: "Cetak Laporan Biaya", icon: Download },
                { label: "Tambah Item Biaya",   icon: Plus },
              ].map((a) => (
                <button
                  key={a.label}
                  className="btn-ghost"
                  style={{
                    justifyContent: "flex-start",
                    width: "100%",
                    fontSize: 12,
                    display: "inline-flex",
                    alignItems: "center",
                    gap: 8,
                  }}
                >
                  <a.icon size={13} />
                  {a.label}
                </button>
              ))}
            </div>
          </div>

        </div>
      </div>
    </div>
  );
}
