"use client";

import {
  UNIT,
  TIMELINE_A01,
  badgeStatus,
  labelStatus,
  warnaProgres,
  rupiah,
} from "@/lib/mock-data";
import {
  Camera,
  CheckCircle2,
  Clock,
  Circle,
  ChevronRight,
  MapPin,
  User,
  Calendar,
  ArrowUpRight,
  Layers,
} from "lucide-react";
import { useState } from "react";

// ─────────────────────────────────────────────────────────────
export default function ConstructionPage() {
  const [selectedUnit, setSelectedUnit] = useState(UNIT[0]);

  const timeline =
    selectedUnit.id === "unt-001" ? TIMELINE_A01 : generateTimeline(selectedUnit.progres);

  const doneCount  = timeline.filter((t) => t.status === "selesai").length;
  const totalPhase = timeline.length;

  return (
    <div style={{ maxWidth: 1100, margin: "0 auto" }}>

      {/* ── Page header ── */}
      <div className="page-header">
        <h1 className="page-title">Progres Konstruksi</h1>
        <p className="page-subtitle">
          Timeline fase per fase — pilih unit untuk melihat detail
        </p>
      </div>

      <div
        style={{
          display: "grid",
          gridTemplateColumns: "300px 1fr",
          gap: 16,
          alignItems: "start",
        }}
      >

        {/* ── LEFT — Unit selector ── */}
        <div style={{ display: "flex", flexDirection: "column", gap: 8 }}>
          <div
            style={{
              fontSize: 11,
              fontWeight: 600,
              color: "var(--color-ink-3)",
              textTransform: "uppercase",
              letterSpacing: "0.07em",
              marginBottom: 4,
              paddingLeft: 4,
            }}
          >
            Pilih Unit
          </div>

          {UNIT.map((u) => {
            const isSelected = selectedUnit.id === u.id;
            return (
              <div
                key={u.id}
                onClick={() => setSelectedUnit(u)}
                style={{
                  padding: "12px 14px",
                  borderRadius: 6,
                  border: isSelected
                    ? "1px solid var(--color-accent)"
                    : "1px solid rgba(14,13,11,0.08)",
                  backgroundColor: isSelected
                    ? "var(--color-accent-light)"
                    : "white",
                  cursor: "pointer",
                  transition: "all 0.15s",
                }}
                onMouseEnter={(e) => {
                  if (!isSelected)
                    (e.currentTarget as HTMLElement).style.borderColor =
                      "var(--color-accent)";
                }}
                onMouseLeave={(e) => {
                  if (!isSelected)
                    (e.currentTarget as HTMLElement).style.borderColor =
                      "rgba(14,13,11,0.08)";
                }}
              >
                {/* Unit header */}
                <div
                  style={{
                    display: "flex",
                    alignItems: "center",
                    justifyContent: "space-between",
                    marginBottom: 8,
                  }}
                >
                  <div
                    style={{
                      fontSize: 14,
                      fontWeight: 700,
                      color: isSelected
                        ? "var(--color-accent)"
                        : "var(--color-ink)",
                    }}
                  >
                    Unit {u.nomor}
                  </div>
                  <span className={`badge ${badgeStatus(u.status)}`}>
                    {labelStatus(u.status)}
                  </span>
                </div>

                {/* Progress bar */}
                <div className="progress-bar" style={{ marginBottom: 6 }}>
                  <div
                    className="progress-fill"
                    style={{
                      width: `${u.progres}%`,
                      backgroundColor: warnaProgres(u.progres),
                    }}
                  />
                </div>

                {/* Meta */}
                <div
                  style={{
                    display: "flex",
                    alignItems: "center",
                    justifyContent: "space-between",
                  }}
                >
                  <span
                    style={{ fontSize: 11, color: "var(--color-ink-3)" }}
                  >
                    {u.tipe} · {u.proyek_nama}
                  </span>
                  <span
                    style={{
                      fontSize: 12,
                      fontWeight: 600,
                      color: warnaProgres(u.progres),
                    }}
                  >
                    {u.progres}%
                  </span>
                </div>
              </div>
            );
          })}
        </div>

        {/* ── RIGHT — Detail panel ── */}
        <div style={{ display: "flex", flexDirection: "column", gap: 16 }}>

          {/* ── Big progress card ── */}
          <div
            className="card"
            style={{
              position: "relative",
              overflow: "hidden",
              padding: 28,
            }}
          >
            {/* Background progress fill */}
            <div
              style={{
                position: "absolute",
                top: 0,
                left: 0,
                height: "100%",
                width: `${selectedUnit.progres}%`,
                backgroundColor: warnaProgres(selectedUnit.progres),
                opacity: 0.04,
                transition: "width 0.8s ease",
                pointerEvents: "none",
              }}
            />

            <div
              style={{
                display: "flex",
                alignItems: "flex-start",
                justifyContent: "space-between",
                position: "relative",
              }}
            >
              {/* Left info */}
              <div>
                <div
                  style={{
                    fontSize: 11,
                    color: "var(--color-ink-3)",
                    textTransform: "uppercase",
                    letterSpacing: "0.08em",
                    marginBottom: 6,
                  }}
                >
                  Unit {selectedUnit.nomor} — {selectedUnit.proyek_nama}
                </div>
                <div
                  style={{
                    fontSize: 20,
                    fontWeight: 600,
                    color: "var(--color-ink)",
                    marginBottom: 8,
                  }}
                >
                  {selectedUnit.fase}
                </div>
                <div
                  style={{
                    display: "flex",
                    alignItems: "center",
                    gap: 6,
                    fontSize: 12,
                    color: "var(--color-ink-3)",
                  }}
                >
                  <Clock size={13} />
                  Target selesai: {selectedUnit.selesai}
                </div>
              </div>

              {/* Big % */}
              <div style={{ textAlign: "right" }}>
                <div
                  style={{
                    fontFamily: "var(--font-serif)",
                    fontSize: 72,
                    fontWeight: 600,
                    color: warnaProgres(selectedUnit.progres),
                    lineHeight: 1,
                  }}
                >
                  {selectedUnit.progres}
                  <span
                    style={{
                      fontSize: 28,
                      color: "var(--color-ink-3)",
                      fontWeight: 300,
                    }}
                  >
                    %
                  </span>
                </div>
                <div
                  style={{
                    fontSize: 11,
                    color: "var(--color-ink-3)",
                    marginTop: 4,
                  }}
                >
                  {doneCount} dari {totalPhase} fase selesai
                </div>
              </div>
            </div>

            {/* Fat progress bar */}
            <div
              className="progress-bar"
              style={{ height: 10, marginTop: 20 }}
            >
              <div
                className="progress-fill"
                style={{
                  width: `${selectedUnit.progres}%`,
                  backgroundColor: warnaProgres(selectedUnit.progres),
                }}
              />
            </div>

            {/* Phase markers */}
            <div
              style={{
                display: "flex",
                justifyContent: "space-between",
                marginTop: 6,
              }}
            >
              {[0, 17, 33, 50, 67, 83, 100].map((pct) => (
                <div
                  key={pct}
                  style={{
                    fontSize: 10,
                    color:
                      selectedUnit.progres >= pct
                        ? warnaProgres(selectedUnit.progres)
                        : "var(--color-ink-3)",
                    opacity: selectedUnit.progres >= pct ? 1 : 0.4,
                    fontWeight: selectedUnit.progres >= pct ? 600 : 400,
                  }}
                >
                  {pct}%
                </div>
              ))}
            </div>
          </div>

          {/* ── Two col — timeline + unit info ── */}
          <div
            style={{
              display: "grid",
              gridTemplateColumns: "1fr 260px",
              gap: 16,
              alignItems: "start",
            }}
          >
            {/* ── Timeline ── */}
            <div className="card">
              <div className="section-title">Timeline Konstruksi</div>

              <div style={{ display: "flex", flexDirection: "column" }}>
                {timeline.map((t, i) => (
                  <div
                    key={i}
                    style={{
                      display: "flex",
                      gap: 14,
                      position: "relative",
                    }}
                  >
                    {/* Vertical connector line */}
                    {i < timeline.length - 1 && (
                      <div
                        style={{
                          position: "absolute",
                          left: 5,
                          top: 16,
                          width: 2,
                          height: "100%",
                          backgroundColor:
                            t.status === "selesai"
                              ? "var(--color-success)"
                              : "rgba(14,13,11,0.08)",
                          zIndex: 0,
                        }}
                      />
                    )}

                    {/* Status dot */}
                    <div
                      style={{
                        position: "relative",
                        zIndex: 1,
                        marginTop: 2,
                        flexShrink: 0,
                      }}
                    >
                      {t.status === "selesai" && (
                        <CheckCircle2
                          size={14}
                          style={{ color: "var(--color-success)" }}
                        />
                      )}
                      {t.status === "proses" && (
                        <div
                          style={{
                            width: 14,
                            height: 14,
                            borderRadius: "50%",
                            backgroundColor: "var(--color-accent)",
                            boxShadow: "0 0 0 4px rgba(26,63,168,0.15)",
                            display: "flex",
                            alignItems: "center",
                            justifyContent: "center",
                          }}
                        >
                          <div
                            style={{
                              width: 5,
                              height: 5,
                              borderRadius: "50%",
                              backgroundColor: "white",
                            }}
                          />
                        </div>
                      )}
                      {t.status === "menunggu" && (
                        <Circle
                          size={14}
                          style={{ color: "rgba(14,13,11,0.2)" }}
                        />
                      )}
                    </div>

                    {/* Content */}
                    <div
                      style={{
                        paddingBottom: i < timeline.length - 1 ? 20 : 0,
                        flex: 1,
                      }}
                    >
                      <div
                        style={{
                          display: "flex",
                          alignItems: "center",
                          justifyContent: "space-between",
                          marginBottom: 4,
                        }}
                      >
                        <div
                          style={{
                            fontSize: 13,
                            fontWeight: t.status === "menunggu" ? 400 : 600,
                            color:
                              t.status === "menunggu"
                                ? "var(--color-ink-3)"
                                : "var(--color-ink)",
                          }}
                        >
                          {t.fase}
                        </div>
                        <div
                          style={{
                            fontSize: 11,
                            color: "var(--color-ink-3)",
                            flexShrink: 0,
                            marginLeft: 12,
                          }}
                        >
                          {t.tgl}
                        </div>
                      </div>

                      {t.catatan && (
                        <div
                          style={{
                            fontSize: 12,
                            color: "var(--color-ink-3)",
                            lineHeight: 1.5,
                          }}
                        >
                          {t.catatan}
                        </div>
                      )}

                      {t.status === "proses" && (
                        <div style={{ marginTop: 6 }}>
                          <span
                            className="badge badge-blue"
                            style={{ fontSize: 10 }}
                          >
                            ⚡ Sedang berjalan
                          </span>
                        </div>
                      )}

                      {t.status === "selesai" && (
                        <div style={{ marginTop: 4 }}>
                          <span
                            className="badge badge-green"
                            style={{ fontSize: 10 }}
                          >
                            ✓ Selesai
                          </span>
                        </div>
                      )}
                    </div>
                  </div>
                ))}
              </div>
            </div>

            {/* ── Right sidebar — unit info + actions ── */}
            <div style={{ display: "flex", flexDirection: "column", gap: 12 }}>

              {/* Unit details */}
              <div className="card" style={{ padding: 16 }}>
                <div className="section-title" style={{ fontSize: 13 }}>
                  Info Unit
                </div>
                <div
                  style={{
                    display: "flex",
                    flexDirection: "column",
                    gap: 0,
                  }}
                >
                  {[
                    { label: "No. Unit",        value: selectedUnit.nomor },
                    { label: "Tipe",             value: selectedUnit.tipe },
                    { label: "Luas Tanah",       value: `${selectedUnit.luas_tanah} m²` },
                    { label: "Luas Bangunan",    value: `${selectedUnit.luas_bgn} m²` },
                    { label: "Harga",            value: rupiah(selectedUnit.harga) },
                    { label: "Pembeli",          value: selectedUnit.pembeli_nama ?? "Tersedia" },
                    { label: "Target Selesai",   value: selectedUnit.selesai },
                  ].map(({ label, value }) => (
                    <div
                      key={label}
                      style={{
                        display: "flex",
                        justifyContent: "space-between",
                        alignItems: "flex-start",
                        padding: "8px 0",
                        borderBottom: "1px solid rgba(14,13,11,0.05)",
                        gap: 8,
                      }}
                    >
                      <span
                        style={{
                          fontSize: 11,
                          color: "var(--color-ink-3)",
                          flexShrink: 0,
                        }}
                      >
                        {label}
                      </span>
                      <span
                        style={{
                          fontSize: 12,
                          fontWeight: 500,
                          color: "var(--color-ink)",
                          textAlign: "right",
                        }}
                      >
                        {value}
                      </span>
                    </div>
                  ))}
                </div>
              </div>

              {/* Quick actions */}
              <div className="card" style={{ padding: 16 }}>
                <div className="section-title" style={{ fontSize: 13 }}>
                  Aksi Cepat
                </div>
                <div
                  style={{
                    display: "flex",
                    flexDirection: "column",
                    gap: 8,
                  }}
                >
                  <button
                    className="btn-accent"
                    style={{
                      justifyContent: "center",
                      width: "100%",
                      fontSize: 12,
                    }}
                  >
                    <ArrowUpRight size={13} />
                    Perbarui Progres
                  </button>
                  <button
                    className="btn-ghost"
                    style={{
                      justifyContent: "center",
                      width: "100%",
                      fontSize: 12,
                    }}
                  >
                    <Camera size={13} />
                    Unggah Foto
                  </button>
                  <button
                    className="btn-ghost"
                    style={{
                      justifyContent: "center",
                      width: "100%",
                      fontSize: 12,
                    }}
                  >
                    <User size={13} />
                    Kirim ke Pembeli
                  </button>
                </div>
              </div>

              {/* Phase summary */}
              <div className="card" style={{ padding: 16 }}>
                <div className="section-title" style={{ fontSize: 13 }}>
                  Ringkasan Fase
                </div>
                <div
                  style={{
                    display: "grid",
                    gridTemplateColumns: "1fr 1fr 1fr",
                    gap: 8,
                    textAlign: "center",
                  }}
                >
                  {[
                    {
                      label: "Selesai",
                      value: doneCount,
                      color: "var(--color-success)",
                      bg: "var(--color-success-light)",
                    },
                    {
                      label: "Berjalan",
                      value: timeline.filter((t) => t.status === "proses").length,
                      color: "var(--color-accent)",
                      bg: "var(--color-accent-light)",
                    },
                    {
                      label: "Menunggu",
                      value: timeline.filter((t) => t.status === "menunggu").length,
                      color: "var(--color-ink-3)",
                      bg: "var(--color-paper-2)",
                    },
                  ].map((s) => (
                    <div
                      key={s.label}
                      style={{
                        backgroundColor: s.bg,
                        borderRadius: 6,
                        padding: "10px 4px",
                      }}
                    >
                      <div
                        style={{
                          fontFamily: "var(--font-serif)",
                          fontSize: 22,
                          fontWeight: 600,
                          color: s.color,
                          lineHeight: 1,
                        }}
                      >
                        {s.value}
                      </div>
                      <div
                        style={{
                          fontSize: 10,
                          color: s.color,
                          marginTop: 4,
                          fontWeight: 500,
                        }}
                      >
                        {s.label}
                      </div>
                    </div>
                  ))}
                </div>
              </div>

            </div>
          </div>
        </div>
      </div>
    </div>
  );
}

// ─────────────────────────────────────────────────────────────
//  Helper — generate realistic timeline for non-A01 units
// ─────────────────────────────────────────────────────────────
function generateTimeline(progres: number) {
  const PHASES = [
    { fase: "Pembersihan & persiapan lahan",   tgl: "Jan 2025" },
    { fase: "Pekerjaan pondasi",               tgl: "Feb 2025" },
    { fase: "Rangka struktur",                 tgl: "Apr 2025" },
    { fase: "Dinding struktural",              tgl: "Mei 2025" },
    { fase: "Pemasangan atap & waterproofing", tgl: "Jun 2025" },
    { fase: "Finishing interior",              tgl: "Jul 2025" },
    { fase: "Selesai / serah terima",          tgl: "Sep 2025" },
  ];

  const doneCount = Math.floor((progres / 100) * PHASES.length);

  return PHASES.map((p, i) => ({
    ...p,
    status:
      i < doneCount
        ? ("selesai" as const)
        : i === doneCount && progres > 0 && doneCount < PHASES.length
        ? ("proses" as const)
        : ("menunggu" as const),
    catatan:
      i < doneCount
        ? "Fase ini telah selesai dikerjakan."
        : i === doneCount && progres > 0
        ? "Sedang dalam pengerjaan."
        : "",
  }));
}
