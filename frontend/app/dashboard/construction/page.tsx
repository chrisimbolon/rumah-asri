"use client";
// =============================================================================
// frontend/app/dashboard/construction/page.tsx 
// =============================================================================
/**
 * Construction timeline — wired to real units + construction phases APIs.
 *
 * What changed from the mock version:
 *   - Left panel: unitsApi.list() instead of UNIT mock array
 *   - Right panel: constructionApi.listPhases(unit.id) per selected unit
 *   - generateTimeline() helper removed entirely — real phase data from DB
 *   - Field names updated (nomor→unit_number, progres→progress, tipe→unit_type etc.)
 *  - NEED MORE REVIEW ON THIS page
 */

import { constructionApi, PhaseListResponse } from "@/lib/api/construction";
import { Unit, unitsApi } from "@/lib/api/units";
import { badgeStatus, labelStatus, rupiah, warnaProgres } from "@/lib/mock-data";
import {
  ArrowUpRight,
  Camera,
  CheckCircle2,
  Circle,
  Clock,
  Loader2,
  User,
} from "lucide-react";
import { useEffect, useState } from "react";

// ── Date formatter ────────────────────────────────────────────
function formatDate(iso: string | null): string {
  if (!iso) return "—";
  try {
    return new Date(iso).toLocaleDateString("id-ID", {
      day: "numeric", month: "short", year: "numeric",
    });
  } catch {
    return iso;
  }
}

// ─────────────────────────────────────────────────────────────
export default function ConstructionPage() {
  const [units,          setUnits]          = useState<Unit[]>([]);
  const [selectedUnit,   setSelectedUnit]   = useState<Unit | null>(null);
  const [phaseData,      setPhaseData]      = useState<PhaseListResponse | null>(null);
  const [unitsLoading,   setUnitsLoading]   = useState(true);
  const [phasesLoading,  setPhasesLoading]  = useState(false);
  const [error,          setError]          = useState<string | null>(null);

  // ── Fetch units on mount ──────────────────────────────────
  useEffect(() => {
    unitsApi.list()
      .then((data) => {
        setUnits(data);
        if (data.length > 0) setSelectedUnit(data[0]);
      })
      .catch(() => setError("Gagal memuat data unit"))
      .finally(() => setUnitsLoading(false));
  }, []);

  // ── Fetch phases whenever selected unit changes ───────────
  useEffect(() => {
    if (!selectedUnit) return;
    setPhasesLoading(true);
    setPhaseData(null);
    constructionApi.listPhases(selectedUnit.id)
      .then(setPhaseData)
      .catch(() => setPhaseData(null))
      .finally(() => setPhasesLoading(false));
  }, [selectedUnit]);

  if (unitsLoading) {
    return (
      <div style={{ display: "flex", alignItems: "center", justifyContent: "center", height: 300, gap: 10, color: "var(--color-ink-3)" }}>
        <Loader2 size={18} style={{ animation: "spin 1s linear infinite" }} />
        <span style={{ fontSize: 13 }}>Memuat unit…</span>
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

  const progress  = phaseData?.progress  ?? selectedUnit?.progress ?? 0;
  const doneCount = phaseData ? phaseData.phases.filter((p) => p.status === "selesai").length : 0;
  const totalPhase = phaseData?.phases.length ?? 0;

  return (
    <div style={{ maxWidth: 1100, margin: "0 auto" }}>

      {/* ── Page header ── */}
      <div className="page-header">
        <h1 className="page-title">Progres Konstruksi</h1>
        <p className="page-subtitle">Timeline fase per fase — pilih unit untuk melihat detail</p>
      </div>

      <div style={{ display: "grid", gridTemplateColumns: "300px 1fr", gap: 16, alignItems: "start" }}>

        {/* ── LEFT — Unit selector ── */}
        <div style={{ display: "flex", flexDirection: "column", gap: 8 }}>
          <div style={{ fontSize: 11, fontWeight: 600, color: "var(--color-ink-3)", textTransform: "uppercase", letterSpacing: "0.07em", marginBottom: 4, paddingLeft: 4 }}>
            Pilih Unit
          </div>

          {units.map((u) => {
            const isSelected = selectedUnit?.id === u.id;
            return (
              <div
                key={u.id}
                onClick={() => setSelectedUnit(u)}
                style={{ padding: "12px 14px", borderRadius: 6, border: isSelected ? "1px solid var(--color-accent)" : "1px solid rgba(14,13,11,0.08)", backgroundColor: isSelected ? "var(--color-accent-light)" : "white", cursor: "pointer", transition: "all 0.15s" }}
                onMouseEnter={(e) => { if (!isSelected) (e.currentTarget as HTMLElement).style.borderColor = "var(--color-accent)"; }}
                onMouseLeave={(e) => { if (!isSelected) (e.currentTarget as HTMLElement).style.borderColor = "rgba(14,13,11,0.08)"; }}
              >
                <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between", marginBottom: 8 }}>
                  <div style={{ fontSize: 14, fontWeight: 700, color: isSelected ? "var(--color-accent)" : "var(--color-ink)" }}>
                    Unit {u.unit_number}
                  </div>
                  <span className={`badge ${badgeStatus(u.status)}`}>{u.status_display || labelStatus(u.status)}</span>
                </div>
                <div className="progress-bar" style={{ marginBottom: 6 }}>
                  <div className="progress-fill" style={{ width: `${u.progress}%`, backgroundColor: warnaProgres(u.progress) }} />
                </div>
                <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between" }}>
                  <span style={{ fontSize: 11, color: "var(--color-ink-3)" }}>{u.unit_type} · {u.project_name}</span>
                  <span style={{ fontSize: 12, fontWeight: 600, color: warnaProgres(u.progress) }}>{u.progress}%</span>
                </div>
              </div>
            );
          })}
        </div>

        {/* ── RIGHT — Detail panel ── */}
        {selectedUnit && (
          <div style={{ display: "flex", flexDirection: "column", gap: 16 }}>

            {/* ── Big progress card ── */}
            <div className="card" style={{ position: "relative", overflow: "hidden", padding: 28 }}>
              <div style={{ position: "absolute", top: 0, left: 0, height: "100%", width: `${progress}%`, backgroundColor: warnaProgres(progress), opacity: 0.04, transition: "width 0.8s ease", pointerEvents: "none" }} />

              <div style={{ display: "flex", alignItems: "flex-start", justifyContent: "space-between", position: "relative" }}>
                <div>
                  <div style={{ fontSize: 11, color: "var(--color-ink-3)", textTransform: "uppercase", letterSpacing: "0.08em", marginBottom: 6 }}>
                    Unit {selectedUnit.unit_number} — {selectedUnit.project_name}
                  </div>
                  <div style={{ fontSize: 20, fontWeight: 600, color: "var(--color-ink)", marginBottom: 8 }}>
                    {selectedUnit.current_phase || "—"}
                  </div>
                  <div style={{ display: "flex", alignItems: "center", gap: 6, fontSize: 12, color: "var(--color-ink-3)" }}>
                    <Clock size={13} />
                    Target selesai: {formatDate(selectedUnit.target_completion)}
                  </div>
                </div>
                <div style={{ textAlign: "right" }}>
                  <div style={{ fontFamily: "var(--font-serif)", fontSize: 72, fontWeight: 600, color: warnaProgres(progress), lineHeight: 1 }}>
                    {progress}<span style={{ fontSize: 28, color: "var(--color-ink-3)", fontWeight: 300 }}>%</span>
                  </div>
                  <div style={{ fontSize: 11, color: "var(--color-ink-3)", marginTop: 4 }}>
                    {doneCount} dari {totalPhase} fase selesai
                  </div>
                </div>
              </div>

              <div className="progress-bar" style={{ height: 10, marginTop: 20 }}>
                <div className="progress-fill" style={{ width: `${progress}%`, backgroundColor: warnaProgres(progress) }} />
              </div>
              <div style={{ display: "flex", justifyContent: "space-between", marginTop: 6 }}>
                {[0, 17, 33, 50, 67, 83, 100].map((pct) => (
                  <div key={pct} style={{ fontSize: 10, color: progress >= pct ? warnaProgres(progress) : "var(--color-ink-3)", opacity: progress >= pct ? 1 : 0.4, fontWeight: progress >= pct ? 600 : 400 }}>
                    {pct}%
                  </div>
                ))}
              </div>
            </div>

            {/* ── Two col — timeline + unit info ── */}
            <div style={{ display: "grid", gridTemplateColumns: "1fr 260px", gap: 16, alignItems: "start" }}>

              {/* ── Timeline ── */}
              <div className="card">
                <div className="section-title">Timeline Konstruksi</div>

                {phasesLoading ? (
                  <div style={{ display: "flex", alignItems: "center", gap: 8, color: "var(--color-ink-3)", fontSize: 13, padding: "20px 0" }}>
                    <Loader2 size={15} style={{ animation: "spin 1s linear infinite" }} />
                    Memuat timeline…
                  </div>
                ) : phaseData && phaseData.phases.length > 0 ? (
                  <div style={{ display: "flex", flexDirection: "column" }}>
                    {phaseData.phases.map((phase, i) => (
                      <div key={phase.id} style={{ display: "flex", gap: 14, position: "relative" }}>
                        {i < phaseData.phases.length - 1 && (
                          <div style={{ position: "absolute", left: 5, top: 16, width: 2, height: "100%", backgroundColor: phase.status === "selesai" ? "var(--color-success)" : "rgba(14,13,11,0.08)", zIndex: 0 }} />
                        )}
                        <div style={{ position: "relative", zIndex: 1, marginTop: 2, flexShrink: 0 }}>
                          {phase.status === "selesai" && <CheckCircle2 size={14} style={{ color: "var(--color-success)" }} />}
                          {phase.status === "proses" && (
                            <div style={{ width: 14, height: 14, borderRadius: "50%", backgroundColor: "var(--color-accent)", boxShadow: "0 0 0 4px rgba(26,63,168,0.15)", display: "flex", alignItems: "center", justifyContent: "center" }}>
                              <div style={{ width: 5, height: 5, borderRadius: "50%", backgroundColor: "white" }} />
                            </div>
                          )}
                          {phase.status === "menunggu" && <Circle size={14} style={{ color: "rgba(14,13,11,0.2)" }} />}
                        </div>
                        <div style={{ paddingBottom: i < phaseData.phases.length - 1 ? 20 : 0, flex: 1 }}>
                          <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between", marginBottom: 4 }}>
                            <div style={{ fontSize: 13, fontWeight: phase.status === "menunggu" ? 400 : 600, color: phase.status === "menunggu" ? "var(--color-ink-3)" : "var(--color-ink)" }}>
                              {phase.phase_name}
                            </div>
                            <div style={{ fontSize: 11, color: "var(--color-ink-3)", flexShrink: 0, marginLeft: 12 }}>
                              {phase.phase_date}
                            </div>
                          </div>
                          {phase.notes && (
                            <div style={{ fontSize: 12, color: "var(--color-ink-3)", lineHeight: 1.5 }}>
                              {phase.notes}
                            </div>
                          )}
                          {phase.status === "proses" && (
                            <div style={{ marginTop: 6 }}>
                              <span className="badge badge-blue" style={{ fontSize: 10 }}>⚡ Sedang berjalan</span>
                            </div>
                          )}
                          {phase.status === "selesai" && (
                            <div style={{ marginTop: 4 }}>
                              <span className="badge badge-green" style={{ fontSize: 10 }}>✓ Selesai</span>
                            </div>
                          )}
                        </div>
                      </div>
                    ))}
                  </div>
                ) : (
                  <div style={{ fontSize: 13, color: "var(--color-ink-3)", padding: "20px 0" }}>
                    Belum ada data fase untuk unit ini.
                  </div>
                )}
              </div>

              {/* ── Right sidebar ── */}
              <div style={{ display: "flex", flexDirection: "column", gap: 12 }}>

                {/* Unit details */}
                <div className="card" style={{ padding: 16 }}>
                  <div className="section-title" style={{ fontSize: 13 }}>Info Unit</div>
                  <div style={{ display: "flex", flexDirection: "column", gap: 0 }}>
                    {[
                      { label: "No. Unit",      value: selectedUnit.unit_number },
                      { label: "Tipe",          value: selectedUnit.unit_type },
                      { label: "Luas Tanah",    value: `${selectedUnit.land_area} m²` },
                      { label: "Luas Bangunan", value: `${selectedUnit.building_area} m²` },
                      { label: "Harga",         value: rupiah(selectedUnit.price) },
                      { label: "Pembeli",       value: selectedUnit.buyer_name ?? "Tersedia" },
                      { label: "Target Selesai",value: formatDate(selectedUnit.target_completion) },
                    ].map(({ label, value }) => (
                      <div key={label} style={{ display: "flex", justifyContent: "space-between", alignItems: "flex-start", padding: "8px 0", borderBottom: "1px solid rgba(14,13,11,0.05)", gap: 8 }}>
                        <span style={{ fontSize: 11, color: "var(--color-ink-3)", flexShrink: 0 }}>{label}</span>
                        <span style={{ fontSize: 12, fontWeight: 500, color: "var(--color-ink)", textAlign: "right" }}>{value}</span>
                      </div>
                    ))}
                  </div>
                </div>

                {/* Quick actions */}
                <div className="card" style={{ padding: 16 }}>
                  <div className="section-title" style={{ fontSize: 13 }}>Aksi Cepat</div>
                  <div style={{ display: "flex", flexDirection: "column", gap: 8 }}>
                    <button className="btn-accent" style={{ justifyContent: "center", width: "100%", fontSize: 12 }}>
                      <ArrowUpRight size={13} /> Perbarui Progres
                    </button>
                    <button className="btn-ghost" style={{ justifyContent: "center", width: "100%", fontSize: 12 }}>
                      <Camera size={13} /> Unggah Foto
                    </button>
                    <button className="btn-ghost" style={{ justifyContent: "center", width: "100%", fontSize: 12 }}>
                      <User size={13} /> Kirim ke Pembeli
                    </button>
                  </div>
                </div>

                {/* Phase summary */}
                <div className="card" style={{ padding: 16 }}>
                  <div className="section-title" style={{ fontSize: 13 }}>Ringkasan Fase</div>
                  <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr 1fr", gap: 8, textAlign: "center" }}>
                    {[
                      { label: "Selesai",  value: doneCount,                                                              color: "var(--color-success)", bg: "var(--color-success-light)" },
                      { label: "Berjalan", value: phaseData?.phases.filter((p) => p.status === "proses").length   ?? 0,   color: "var(--color-accent)",  bg: "var(--color-accent-light)"  },
                      { label: "Menunggu", value: phaseData?.phases.filter((p) => p.status === "menunggu").length ?? 0,   color: "var(--color-ink-3)",   bg: "var(--color-paper-2)"       },
                    ].map((s) => (
                      <div key={s.label} style={{ backgroundColor: s.bg, borderRadius: 6, padding: "10px 4px" }}>
                        <div style={{ fontFamily: "var(--font-serif)", fontSize: 22, fontWeight: 600, color: s.color, lineHeight: 1 }}>{s.value}</div>
                        <div style={{ fontSize: 10, color: s.color, marginTop: 4, fontWeight: 500 }}>{s.label}</div>
                      </div>
                    ))}
                  </div>
                </div>

              </div>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
