"use client";
// =============================================================================
// === frontend/components/project/SitePlanPanel.tsx ===
// Sprint 27-follow-up: real interactive site plan.
//
// Extracted as its own component, matching the established
// TaskPanels.tsx pattern — kept out of the 2800+ line project detail
// page rather than buried inline.
//
// Color is NEVER hardcoded per-marker or fetched as a hex value from
// the backend — map_status is a fixed vocabulary string
// ("tersedia" | "belum_ada_pembayaran" | "cicilan_berjalan" | "lunas" |
// "menunggak"), and the color mapping lives entirely here, in the
// frontend. Same separation of concerns as every other status field
// in this codebase.
//
// Annotation UX is deliberately simple, matching the agreed v1 scope:
// this is a rare, one-time-per-unit admin setup task, not a polished
// end-user feature. No drag-to-edit — a wrong shape gets deleted and
// redrawn from scratch.
// =============================================================================

import { useAuth } from "@/context/AuthContext";
import { SitePlan, SitePlanUnitMarker, sitePlanApi } from "@/lib/api/projects";
import { Unit, unitsApi } from "@/lib/api/units";
import {
  CheckCircle2,
  Loader2,
  MapPinned,
  RotateCcw,
  Upload
} from "lucide-react";
import { useEffect, useRef, useState } from "react";

// ── Color mapping — the frontend's job, not the backend's ──────────
const MAP_STATUS_META: Record<
  SitePlanUnitMarker["map_status"],
  { fill: string; stroke: string; label: string }
> = {
  tersedia:          { fill: "var(--color-paper-2)",       stroke: "rgba(14,13,11,0.25)",  label: "Tersedia" },
  // Fix: was var(--color-gold-light) (#F5EDD9), nearly identical in
  // hue/luminosity to tersedia's paper-2 (#EDEAE3) — indistinguishable
  // at 60% opacity in a real screenshot. Confirmed by comparing the
  // actual hex values in globals.css, not guessed. warning-light is a
  // genuine pale yellow (#FEF3C7), clearly distinct from beige.
  // Renamed from booking_baru — status-neutral on purpose, since this
  // state can't distinguish "genuinely just booked" from "marked sold
  // but no payment ever recorded" (real confusion caught on a real
  // Terjual unit during testing — see Unit.map_status's docstring).
  belum_ada_pembayaran: { fill: "var(--color-warning-light)", stroke: "var(--color-warning)", label: "Belum Ada Pembayaran" },
  cicilan_berjalan:  { fill: "var(--color-accent-light)",  stroke: "var(--color-accent)",  label: "Cicilan Berjalan" },
  lunas:             { fill: "var(--color-success-light)", stroke: "var(--color-success)", label: "Lunas" },
  menunggak:         { fill: "var(--color-danger-light)",  stroke: "var(--color-danger)",  label: "Menunggak" },
};

function pointsToSvgString(points: [number, number][]): string {
  return points.map((p) => p.join(",")).join(" ");
}

interface Props {
  projectId: string;
}

export default function SitePlanPanel({ projectId }: Props) {
  const { user } = useAuth();
  const canEdit  = user?.role === "developer" || user?.role === "super_admin";

  const [siteplan, setSiteplan] = useState<SitePlan | null>(null);
  const [units,    setUnits]    = useState<Unit[]>([]);
  const [loading,  setLoading]  = useState(true);
  const [error,    setError]    = useState<string | null>(null);
  const [uploading, setUploading] = useState(false);

  // ── Annotation state ─────────────────────────────────────────────
  const [annotating,     setAnnotating]     = useState(false);
  const [selectedUnitId, setSelectedUnitId] = useState<string | null>(null);
  const [currentPoints,  setCurrentPoints]  = useState<[number, number][]>([]);
  const [savingMarker,   setSavingMarker]   = useState(false);
  const svgRef = useRef<SVGSVGElement>(null);

  const load = () => {
    setLoading(true);
    Promise.all([
      sitePlanApi.get(projectId),
      unitsApi.list({ project: projectId }),
    ])
      .then(([sp, u]) => { setSiteplan(sp); setUnits(u); })
      .catch(() => setError("Gagal memuat site plan"))
      .finally(() => setLoading(false));
  };

  useEffect(load, [projectId]);

  // ── Upload ────────────────────────────────────────────────────────
  const handleUpload = (file: File) => {
    setUploading(true);
    sitePlanApi.upload(projectId, { image: file })
      .then((sp) => { setSiteplan(sp); })
      .catch(() => setError("Gagal mengunggah site plan"))
      .finally(() => setUploading(false));
  };

  // ── Annotation: click on the image to add a polygon point ────────
  const handleSvgClick = (e: React.MouseEvent<SVGSVGElement>) => {
    if (!annotating || !selectedUnitId || !siteplan || !svgRef.current) return;
    const rect   = svgRef.current.getBoundingClientRect();
    const scaleX = siteplan.image_width  / rect.width;
    const scaleY = siteplan.image_height / rect.height;
    const x = Math.round((e.clientX - rect.left) * scaleX);
    const y = Math.round((e.clientY - rect.top)  * scaleY);
    setCurrentPoints((prev) => [...prev, [x, y]]);
  };

  const handleSaveMarker = () => {
    if (!selectedUnitId || currentPoints.length < 3) return;
    setSavingMarker(true);
    sitePlanApi.createMarker(projectId, { unit_id: selectedUnitId, points: currentPoints })
      .then(() => {
        setCurrentPoints([]);
        setSelectedUnitId(null);
        load();
      })
      .catch(() => setError("Gagal menyimpan marker — coba lagi"))
      .finally(() => setSavingMarker(false));
  };

  const handleDeleteMarker = (marker: SitePlanUnitMarker) => {
    if (!window.confirm(`Hapus marker untuk unit ${marker.unit_number}?`)) return;
    sitePlanApi.deleteMarker(projectId, marker.id)
      .then(load)
      .catch(() => setError("Gagal menghapus marker"));
  };

  // ── Loading / error / empty states ─────────────────────────────────
  if (loading) {
    return (
      <div className="card" style={{ marginBottom: 16, padding: 32, textAlign: "center" }}>
        <Loader2 size={18} style={{ animation: "spin 1s linear infinite", color: "var(--color-ink-3)" }} />
      </div>
    );
  }

  const mappedUnitIds  = new Set((siteplan?.markers ?? []).map((m) => m.unit_id));
  const unmappedUnits  = units.filter((u) => !mappedUnitIds.has(u.id));

  return (
    <div className="card" style={{ marginBottom: 16 }}>
      <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between", marginBottom: 16 }}>
        <div style={{ display: "flex", alignItems: "center", gap: 8 }}>
          <MapPinned size={15} style={{ color: "var(--color-accent)" }} />
          <span style={{ fontSize: 13, fontWeight: 600, color: "var(--color-ink)" }}>Site Plan</span>
          {siteplan && (
            <span style={{ fontSize: 11, color: "var(--color-ink-3)" }}>
              {siteplan.mapped_count}/{siteplan.unit_count} unit dipetakan
            </span>
          )}
        </div>

        {canEdit && siteplan && (
          <div style={{ display: "flex", gap: 8 }}>
            <button
              onClick={() => { setAnnotating(!annotating); setSelectedUnitId(null); setCurrentPoints([]); }}
              style={{
                fontSize: 11, fontWeight: 600, padding: "6px 12px", borderRadius: 6,
                border: `1px solid ${annotating ? "var(--color-accent)" : "rgba(14,13,11,0.12)"}`,
                backgroundColor: annotating ? "var(--color-accent-light)" : "white",
                color: annotating ? "var(--color-accent)" : "var(--color-ink)",
                cursor: "pointer",
              }}
            >
              {annotating ? "Selesai Memetakan" : "Petakan Unit"}
            </button>
            <label style={{
              fontSize: 11, fontWeight: 600, padding: "6px 12px", borderRadius: 6,
              border: "1px solid rgba(14,13,11,0.12)", backgroundColor: "white",
              color: "var(--color-ink)", cursor: "pointer",
            }}>
              Ganti Gambar
              <input
                type="file" accept="image/*" style={{ display: "none" }}
                onChange={(e) => { const f = e.target.files?.[0]; if (f) handleUpload(f); }}
              />
            </label>
          </div>
        )}
      </div>

      {error && (
        <div style={{ fontSize: 12, color: "var(--color-danger)", marginBottom: 12 }}>{error}</div>
      )}

      {/* ── No site plan yet — upload prompt ── */}
      {!siteplan && (
        <div style={{
          border: "2px dashed rgba(14,13,11,0.15)", borderRadius: 8,
          padding: 40, textAlign: "center",
        }}>
          <Upload size={24} style={{ color: "var(--color-ink-3)", marginBottom: 8 }} />
          <div style={{ fontSize: 13, color: "var(--color-ink-3)", marginBottom: 16 }}>
            Belum ada site plan untuk proyek ini
          </div>
          {canEdit ? (
            <label style={{
              display: "inline-block", fontSize: 12, fontWeight: 600,
              padding: "8px 16px", borderRadius: 6, backgroundColor: "var(--color-accent)",
              color: "white", cursor: uploading ? "default" : "pointer",
              opacity: uploading ? 0.6 : 1,
            }}>
              {uploading ? "Mengunggah..." : "Unggah Site Plan"}
              <input
                type="file" accept="image/*" style={{ display: "none" }} disabled={uploading}
                onChange={(e) => { const f = e.target.files?.[0]; if (f) handleUpload(f); }}
              />
            </label>
          ) : (
            <div style={{ fontSize: 11, color: "var(--color-ink-3)", fontStyle: "italic" }}>
              Hubungi developer untuk mengunggah site plan
            </div>
          )}
        </div>
      )}

      {/* ── Site plan exists — image + overlay ── */}
      {siteplan && (
        <div style={{ display: "flex", gap: 16 }}>
          <div style={{ flex: 1, minWidth: 0, position: "relative", borderRadius: 8, overflow: "hidden", border: "1px solid rgba(14,13,11,0.08)" }}>
            <svg
              ref={svgRef}
              viewBox={`0 0 ${siteplan.image_width} ${siteplan.image_height}`}
              width="100%"
              style={{ display: "block", cursor: annotating && selectedUnitId ? "crosshair" : "default", backgroundColor: "#fafafa" }}
              onClick={handleSvgClick}
            >
              <image href={siteplan.image_url} width={siteplan.image_width} height={siteplan.image_height} />

              {siteplan.markers.map((m) => {
                const meta = MAP_STATUS_META[m.map_status];
                return (
                  <polygon
                    key={m.id}
                    points={pointsToSvgString(m.points)}
                    fill={meta.fill}
                    fillOpacity={0.6}
                    stroke={meta.stroke}
                    strokeWidth={Math.max(2, siteplan.image_width / 400)}
                    style={{ cursor: annotating ? "pointer" : "default" }}
                    onClick={(e) => {
                      if (!annotating) return;
                      e.stopPropagation();
                      handleDeleteMarker(m);
                    }}
                  >
                    <title>{m.unit_number} — {MAP_STATUS_META[m.map_status].label}</title>
                  </polygon>
                );
              })}

              {/* ── In-progress shape being traced ── */}
              {currentPoints.length > 0 && (
                <>
                  <polyline
                    points={pointsToSvgString(currentPoints)}
                    fill="none" stroke="var(--color-accent)"
                    strokeWidth={Math.max(2, siteplan.image_width / 400)}
                    strokeDasharray="6 4"
                  />
                  {currentPoints.map(([x, y], i) => (
                    <circle key={i} cx={x} cy={y} r={Math.max(4, siteplan.image_width / 150)} fill="var(--color-accent)" />
                  ))}
                </>
              )}
            </svg>
          </div>

          {/* ── Sidebar: legend + annotation controls ── */}
          <div style={{ width: 220, flexShrink: 0 }}>
            <div style={{ fontSize: 10, fontWeight: 700, color: "var(--color-ink-3)", textTransform: "uppercase", letterSpacing: "0.06em", marginBottom: 8 }}>
              Keterangan
            </div>
            <div style={{ display: "flex", flexDirection: "column", gap: 6, marginBottom: 16 }}>
              {(Object.keys(MAP_STATUS_META) as SitePlanUnitMarker["map_status"][]).map((key) => (
                <div key={key} style={{ display: "flex", alignItems: "center", gap: 8, fontSize: 11, color: "var(--color-ink)" }}>
                  <span style={{
                    width: 12, height: 12, borderRadius: 3, flexShrink: 0,
                    backgroundColor: MAP_STATUS_META[key].fill,
                    border: `1.5px solid ${MAP_STATUS_META[key].stroke}`,
                  }} />
                  {MAP_STATUS_META[key].label}
                </div>
              ))}
            </div>

            {annotating && canEdit && (
              <>
                <div style={{ fontSize: 10, fontWeight: 700, color: "var(--color-ink-3)", textTransform: "uppercase", letterSpacing: "0.06em", marginBottom: 8 }}>
                  {selectedUnitId ? "Klik titik di gambar" : "Pilih unit untuk dipetakan"}
                </div>

                {selectedUnitId ? (
                  <div style={{ marginBottom: 12 }}>
                    <div style={{ fontSize: 11, color: "var(--color-ink-3)", marginBottom: 8 }}>
                      {currentPoints.length} titik — minimal 3 untuk menyimpan
                    </div>
                    <div style={{ display: "flex", gap: 6 }}>
                      <button
                        onClick={handleSaveMarker}
                        disabled={currentPoints.length < 3 || savingMarker}
                        style={{
                          flex: 1, fontSize: 11, fontWeight: 600, padding: "6px 10px", borderRadius: 6,
                          border: "none", backgroundColor: "var(--color-success)", color: "white",
                          cursor: currentPoints.length < 3 ? "not-allowed" : "pointer",
                          opacity: currentPoints.length < 3 ? 0.5 : 1,
                          display: "flex", alignItems: "center", justifyContent: "center", gap: 4,
                        }}
                      >
                        <CheckCircle2 size={12} /> Simpan
                      </button>
                      <button
                        onClick={() => { setCurrentPoints([]); setSelectedUnitId(null); }}
                        style={{
                          fontSize: 11, fontWeight: 600, padding: "6px 10px", borderRadius: 6,
                          border: "1px solid rgba(14,13,11,0.12)", backgroundColor: "white",
                          color: "var(--color-ink-3)", cursor: "pointer",
                        }}
                      >
                        <RotateCcw size={12} />
                      </button>
                    </div>
                  </div>
                ) : (
                  <div style={{ display: "flex", flexDirection: "column", gap: 4, maxHeight: 240, overflowY: "auto" }}>
                    {unmappedUnits.length === 0 ? (
                      <div style={{ fontSize: 11, color: "var(--color-ink-3)", fontStyle: "italic" }}>
                        Semua unit sudah dipetakan
                      </div>
                    ) : (
                      unmappedUnits.map((u) => (
                        <button
                          key={u.id}
                          onClick={() => setSelectedUnitId(u.id)}
                          style={{
                            fontSize: 11, textAlign: "left", padding: "6px 8px", borderRadius: 6,
                            border: "1px solid rgba(14,13,11,0.08)", backgroundColor: "var(--color-paper-2)",
                            color: "var(--color-ink)", cursor: "pointer",
                          }}
                        >
                          {u.unit_number}
                        </button>
                      ))
                    )}
                  </div>
                )}

                <div style={{ fontSize: 10, color: "var(--color-ink-3)", marginTop: 12, lineHeight: 1.5 }}>
                  Klik marker unit yang sudah ada untuk menghapusnya.
                </div>
              </>
            )}
          </div>
        </div>
      )}
    </div>
  );
}
