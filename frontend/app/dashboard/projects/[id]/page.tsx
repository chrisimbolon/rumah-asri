"use client";
// =============================================================================
// === frontend/app/dashboard/projects/[id]/page.tsx ===
// =============================================================================
/**
 * Project Detail — full lifecycle view with stage pipeline,
 * checklist, permit tracking, and stage advancement.
 */

import {
    Project,
    ProjectStage,
    STAGE_META,
    UpdateProjectPayload,
    projectsApi,
} from "@/lib/api/projects";
import {
    AlertTriangle,
    ArrowRight,
    Building2,
    Calendar,
    CheckCircle2,
    ChevronLeft,
    Circle,
    FileText,
    Home,
    Loader2,
    MapPin,
    Save,
    TrendingUp,
} from "lucide-react";
import Link from "next/link";
import { useParams, useRouter } from "next/navigation";
import { useEffect, useState } from "react";

// ── Stage pipeline component ──────────────────────────────────
function StagePipeline({ stage }: { stage: ProjectStage }) {
  const stages: { key: ProjectStage; label: string }[] = [
    { key: "draft",        label: "Draft" },
    { key: "perencanaan",  label: "Perencanaan" },
    { key: "perizinan",    label: "Perizinan" },
    { key: "konstruksi",   label: "Konstruksi" },
    { key: "penjualan",    label: "Penjualan" },
    { key: "serah_terima", label: "Serah Terima" },
    { key: "selesai",      label: "Selesai" },
  ];
  const currentIdx = stages.findIndex((s) => s.key === stage);

  return (
    <div style={{ marginBottom: 32 }}>
      <div style={{ display: "flex", alignItems: "flex-start", position: "relative" }}>
        {stages.map((s, i) => {
          const meta    = STAGE_META[s.key];
          const done    = i < currentIdx;
          const current = i === currentIdx;
          return (
            <div key={s.key} style={{ flex: 1, display: "flex", flexDirection: "column", alignItems: "center", position: "relative" }}>
              {/* Connector line */}
              {i < stages.length - 1 && (
                <div style={{
                  position: "absolute", top: 14, left: "50%", right: "-50%",
                  height: 2,
                  backgroundColor: done ? "var(--color-success)" : "rgba(14,13,11,0.08)",
                  zIndex: 0,
                }} />
              )}
              {/* Circle */}
              <div style={{
                width: 28, height: 28, borderRadius: "50%",
                backgroundColor: done ? "var(--color-success)" : current ? meta.color : "rgba(14,13,11,0.08)",
                border: current ? `3px solid ${meta.color}` : "none",
                display: "flex", alignItems: "center", justifyContent: "center",
                position: "relative", zIndex: 1,
                boxShadow: current ? `0 0 0 4px ${meta.bg}` : "none",
                transition: "all 0.3s",
              }}>
                {done && <CheckCircle2 size={14} color="white" />}
                {current && <div style={{ width: 8, height: 8, borderRadius: "50%", backgroundColor: "white" }} />}
              </div>
              {/* Label */}
              <div style={{
                marginTop: 8, fontSize: 10, fontWeight: current ? 700 : 500,
                color: current ? meta.color : done ? "var(--color-success)" : "var(--color-ink-3)",
                textAlign: "center", lineHeight: 1.3,
                letterSpacing: "0.02em",
              }}>
                {s.label}
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
}

// ── Permit status badge ───────────────────────────────────────
function PermitBadge({ status }: { status: string }) {
  const map: Record<string, { label: string; color: string; bg: string }> = {
    belum:    { label: "Belum Dimulai", color: "var(--color-ink-3)",   bg: "var(--color-paper-2)"       },
    proses:   { label: "Diproses",      color: "var(--color-warning)", bg: "var(--color-warning-light)" },
    approved: { label: "Disetujui ✓",   color: "var(--color-success)", bg: "var(--color-success-light)" },
    rejected: { label: "Ditolak",       color: "var(--color-danger)",  bg: "var(--color-danger-light)"  },
  };
  const s = map[status] ?? map.belum;
  return (
    <span style={{ fontSize: 11, fontWeight: 600, padding: "3px 10px", borderRadius: 999, color: s.color, backgroundColor: s.bg }}>
      {s.label}
    </span>
  );
}

// ── Main page ─────────────────────────────────────────────────
export default function ProjectDetailPage() {
  const params = useParams();
  const router = useRouter();
  const id     = params.id as string;

  const [project,   setProject]   = useState<Project | null>(null);
  const [loading,   setLoading]   = useState(true);
  const [advancing, setAdvancing] = useState(false);
  const [saving,    setSaving]    = useState(false);
  const [error,     setError]     = useState<string | null>(null);
  const [editMode,  setEditMode]  = useState(false);
  const [form,      setForm]      = useState<UpdateProjectPayload>({});

  useEffect(() => {
    projectsApi.get(id)
      .then((p) => { setProject(p); setForm(buildForm(p)); })
      .catch(() => setError("Gagal memuat proyek"))
      .finally(() => setLoading(false));
  }, [id]);

  function buildForm(p: Project): UpdateProjectPayload {
    return {
      name:         p.name,
      location:     p.location,
      description:  p.description,
      total_units:  p.total_units,
      target_budget: p.target_budget ?? "",
      start_date:   p.start_date ?? "",
      end_date:     p.end_date ?? "",
      ipr_status:   p.ipr_status,
      ipr_date:     p.ipr_date ?? "",
      amdal_status: p.amdal_status,
      amdal_date:   p.amdal_date ?? "",
      pbg_status:   p.pbg_status,
      pbg_date:     p.pbg_date ?? "",
    };
  }

  const handleSave = async () => {
    if (!project) return;
    setSaving(true);
    setError(null);
    try {
      const updated = await projectsApi.update(project.id, form);
      setProject(updated);
      setForm(buildForm(updated));
      setEditMode(false);
    } catch {
      setError("Gagal menyimpan perubahan");
    } finally {
      setSaving(false);
    }
  };

  const handleAdvance = async () => {
    if (!project) return;
    setAdvancing(true);
    setError(null);
    try {
      const updated = await projectsApi.advance(project.id);
      setProject(updated);
      setForm(buildForm(updated));
    } catch (e: unknown) {
      const msg = e instanceof Error ? e.message : "Gagal melanjutkan tahap";
      setError(msg);
    } finally {
      setAdvancing(false);
    }
  };

  if (loading) {
    return (
      <div style={{ display: "flex", alignItems: "center", justifyContent: "center", height: 300, gap: 10, color: "var(--color-ink-3)" }}>
        <Loader2 size={18} style={{ animation: "spin 1s linear infinite" }} />
        <span style={{ fontSize: 13 }}>Memuat proyek…</span>
      </div>
    );
  }

  if (error && !project) {
    return <div style={{ padding: 24, textAlign: "center", color: "var(--color-danger)", fontSize: 13 }}>{error}</div>;
  }

  if (!project) return null;

  const meta        = STAGE_META[project.stage];
  const allChecked  = project.stage_checklist.every((i) => i.done);
  const blockingIncomplete = project.stage_checklist.some((i) => i.blocking && !i.done);

  return (
    <div style={{ maxWidth: 900, margin: "0 auto" }}>

      {/* ── Back + header ── */}
      <div style={{ marginBottom: 24 }}>
        <Link
          href="/dashboard/projects"
          style={{ display: "inline-flex", alignItems: "center", gap: 5, fontSize: 12, color: "var(--color-ink-3)", textDecoration: "none", marginBottom: 16 }}
        >
          <ChevronLeft size={14} /> Kembali ke Semua Proyek
        </Link>

        <div style={{ display: "flex", alignItems: "flex-start", justifyContent: "space-between" }}>
          <div>
            <div style={{ display: "flex", alignItems: "center", gap: 8, marginBottom: 6 }}>
              <span style={{ fontSize: 11, fontWeight: 600, color: meta.color, textTransform: "uppercase", letterSpacing: "0.08em" }}>
                {meta.label}
              </span>
              <span style={{ fontSize: 11, color: "var(--color-ink-3)" }}>—</span>
              <span style={{ fontSize: 11, color: "var(--color-ink-3)" }}>{meta.description}</span>
            </div>
            <h1 style={{ fontSize: 26, fontWeight: 700, color: "var(--color-ink)", margin: 0, marginBottom: 4 }}>
              {project.name}
            </h1>
            <div style={{ display: "flex", alignItems: "center", gap: 4, fontSize: 13, color: "var(--color-ink-3)" }}>
              <MapPin size={13} /> {project.location}
            </div>
          </div>
          <div style={{ display: "flex", gap: 8, flexShrink: 0 }}>
            {editMode ? (
              <>
                <button className="btn-ghost btn-sm" onClick={() => setEditMode(false)}>Batal</button>
                <button
                  className="btn-accent btn-sm"
                  onClick={handleSave}
                  disabled={saving}
                  style={{ display: "flex", alignItems: "center", gap: 4 }}
                >
                  {saving ? <Loader2 size={12} style={{ animation: "spin 1s linear infinite" }} /> : <Save size={12} />}
                  Simpan
                </button>
              </>
            ) : (
              <button className="btn-ghost btn-sm" onClick={() => setEditMode(true)}>
                Edit Proyek
              </button>
            )}
          </div>
        </div>
      </div>

      {/* ── Error banner ── */}
      {error && (
        <div style={{ marginBottom: 16, padding: "12px 16px", backgroundColor: "var(--color-danger-light)", borderRadius: 8, fontSize: 13, color: "var(--color-danger)", display: "flex", alignItems: "center", gap: 8 }}>
          <AlertTriangle size={14} /> {error}
        </div>
      )}

      {/* ── Stage pipeline ── */}
      <div className="card" style={{ marginBottom: 20 }}>
        <div style={{ fontSize: 12, fontWeight: 600, color: "var(--color-ink)", marginBottom: 20 }}>
          Alur Tahap Proyek
        </div>
        <StagePipeline stage={project.stage} />

        {/* Advance button */}
        {project.stage !== "selesai" && project.stage !== "ditunda" && (
          <div style={{
            padding: "16px",
            backgroundColor: allChecked ? "var(--color-success-light)" : blockingIncomplete ? "var(--color-danger-light)" : "var(--color-paper-2)",
            borderRadius: 8,
          }}>
            <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between" }}>
              <div>
                <div style={{ fontSize: 13, fontWeight: 600, color: "var(--color-ink)", marginBottom: 2 }}>
                  Lanjut ke tahap: <span style={{ color: project.next_stage ? STAGE_META[project.next_stage]?.color : "inherit" }}>
                    {project.next_stage ? STAGE_META[project.next_stage]?.label : "—"}
                  </span>
                </div>
                <div style={{ fontSize: 11, color: "var(--color-ink-3)" }}>
                  {blockingIncomplete
                    ? "⚡ Ada item wajib yang belum selesai"
                    : allChecked
                    ? "✓ Semua checklist selesai — siap dilanjutkan"
                    : "Beberapa item checklist belum selesai"
                  }
                </div>
              </div>
              <button
                className="btn-accent"
                onClick={handleAdvance}
                disabled={advancing || !project.can_advance}
                style={{ display: "flex", alignItems: "center", gap: 6, opacity: project.can_advance ? 1 : 0.5 }}
              >
                {advancing
                  ? <Loader2 size={14} style={{ animation: "spin 1s linear infinite" }} />
                  : <ArrowRight size={14} />
                }
                Lanjutkan Tahap
              </button>
            </div>
          </div>
        )}
      </div>

      <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 16 }}>

        {/* ── Checklist card ── */}
        <div className="card">
          <div style={{ fontSize: 12, fontWeight: 600, color: "var(--color-ink)", marginBottom: 16 }}>
            Checklist Tahap {meta.label}
          </div>
          {project.stage_checklist.length === 0 ? (
            <div style={{ fontSize: 12, color: "var(--color-ink-3)", fontStyle: "italic" }}>
              Tidak ada checklist untuk tahap ini
            </div>
          ) : (
            project.stage_checklist.map((item, i) => (
              <div key={i} style={{ display: "flex", alignItems: "flex-start", gap: 10, marginBottom: 10, padding: "8px 10px", backgroundColor: item.done ? "var(--color-success-light)" : "var(--color-paper-2)", borderRadius: 6 }}>
                {item.done
                  ? <CheckCircle2 size={14} style={{ color: "var(--color-success)", marginTop: 1, flexShrink: 0 }} />
                  : <Circle       size={14} style={{ color: item.blocking ? "var(--color-danger)" : "var(--color-ink-3)", marginTop: 1, flexShrink: 0 }} />
                }
                <div>
                  <div style={{ fontSize: 12, fontWeight: 500, color: item.done ? "var(--color-ink-3)" : "var(--color-ink)", textDecoration: item.done ? "line-through" : "none" }}>
                    {item.item}
                  </div>
                  {item.blocking && !item.done && (
                    <div style={{ fontSize: 10, color: "var(--color-danger)", marginTop: 2 }}>
                      ⚡ Item wajib — memblokir ke tahap berikutnya
                    </div>
                  )}
                </div>
              </div>
            ))
          )}
        </div>

        {/* ── Basic info / edit card ── */}
        <div className="card">
          <div style={{ fontSize: 12, fontWeight: 600, color: "var(--color-ink)", marginBottom: 16 }}>
            Informasi Proyek
          </div>

          {editMode ? (
            <div style={{ display: "flex", flexDirection: "column", gap: 12 }}>
              {[
                { label: "Nama Proyek",    key: "name",         type: "text" },
                { label: "Lokasi",         key: "location",     type: "text" },
                { label: "Total Unit",     key: "total_units",  type: "number" },
                { label: "Target Anggaran",key: "target_budget",type: "text" },
                { label: "Tanggal Mulai",  key: "start_date",   type: "date" },
                { label: "Target Selesai", key: "end_date",     type: "date" },
              ].map((field) => (
                <div key={field.key}>
                  <label style={{ display: "block", fontSize: 11, fontWeight: 500, color: "var(--color-ink-3)", marginBottom: 4 }}>
                    {field.label}
                  </label>
                  <input
                    type={field.type}
                    value={(form as Record<string, unknown>)[field.key] as string ?? ""}
                    onChange={(e) => setForm({ ...form, [field.key]: field.type === "number" ? Number(e.target.value) : e.target.value })}
                    style={{ width: "100%", padding: "8px 10px", border: "1px solid rgba(14,13,11,0.15)", borderRadius: 6, fontSize: 12, color: "var(--color-ink)", outline: "none", boxSizing: "border-box" }}
                  />
                </div>
              ))}
              <div>
                <label style={{ display: "block", fontSize: 11, fontWeight: 500, color: "var(--color-ink-3)", marginBottom: 4 }}>
                  Deskripsi
                </label>
                <textarea
                  value={form.description ?? ""}
                  onChange={(e) => setForm({ ...form, description: e.target.value })}
                  rows={3}
                  style={{ width: "100%", padding: "8px 10px", border: "1px solid rgba(14,13,11,0.15)", borderRadius: 6, fontSize: 12, color: "var(--color-ink)", outline: "none", resize: "vertical", boxSizing: "border-box", fontFamily: "inherit" }}
                />
              </div>
            </div>
          ) : (
            <div style={{ display: "flex", flexDirection: "column", gap: 10 }}>
              {[
                { label: "Total Unit",      value: String(project.total_units || "—"),  icon: Home },
                { label: "Unit Terjual",    value: String(project.units_sold),           icon: TrendingUp },
                { label: "Target Anggaran", value: project.target_budget ? `Rp ${Number(project.target_budget).toLocaleString("id-ID")}` : "—", icon: FileText },
                { label: "Tanggal Mulai",   value: project.start_date  ?? "—",           icon: Calendar },
                { label: "Target Selesai",  value: project.end_date    ?? "—",           icon: Calendar },
              ].map((row) => (
                <div key={row.label} style={{ display: "flex", alignItems: "center", justifyContent: "space-between", padding: "8px 0", borderBottom: "1px solid rgba(14,13,11,0.05)" }}>
                  <div style={{ display: "flex", alignItems: "center", gap: 6, fontSize: 12, color: "var(--color-ink-3)" }}>
                    <row.icon size={12} /> {row.label}
                  </div>
                  <div style={{ fontSize: 12, fontWeight: 500, color: "var(--color-ink)" }}>
                    {row.value}
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>
      </div>

      {/* ── Permits section (only show when in perizinan or beyond) ── */}
      {["perizinan", "konstruksi", "penjualan", "serah_terima", "selesai"].includes(project.stage) && (
        <div className="card" style={{ marginTop: 16 }}>
          <div style={{ fontSize: 12, fontWeight: 600, color: "var(--color-ink)", marginBottom: 16 }}>
            Status Perizinan
          </div>
          <div style={{ display: "grid", gridTemplateColumns: "repeat(3, 1fr)", gap: 16 }}>
            {[
              { label: "IPR",          status: project.ipr_status,   date: project.ipr_date,   key_s: "ipr_status",   key_d: "ipr_date",   desc: "Izin Pemanfaatan Ruang" },
              { label: "AMDAL/UKL-UPL",status: project.amdal_status, date: project.amdal_date, key_s: "amdal_status", key_d: "amdal_date", desc: "Kajian Lingkungan" },
              { label: "PBG",          status: project.pbg_status,   date: project.pbg_date,   key_s: "pbg_status",   key_d: "pbg_date",   desc: "Persetujuan Bangunan Gedung ⚡" },
            ].map((permit) => (
              <div key={permit.label} style={{ padding: 14, backgroundColor: "var(--color-paper-2)", borderRadius: 8 }}>
                <div style={{ fontSize: 13, fontWeight: 600, color: "var(--color-ink)", marginBottom: 2 }}>
                  {permit.label}
                </div>
                <div style={{ fontSize: 10, color: "var(--color-ink-3)", marginBottom: 10 }}>
                  {permit.desc}
                </div>
                {editMode ? (
                  <>
                    <select
                      value={(form as Record<string, unknown>)[permit.key_s] as string ?? "belum"}
                      onChange={(e) => setForm({ ...form, [permit.key_s]: e.target.value })}
                      style={{ width: "100%", padding: "6px 8px", border: "1px solid rgba(14,13,11,0.15)", borderRadius: 6, fontSize: 11, marginBottom: 6, backgroundColor: "white" }}
                    >
                      <option value="belum">Belum Dimulai</option>
                      <option value="proses">Sedang Diproses</option>
                      <option value="approved">Disetujui</option>
                      <option value="rejected">Ditolak</option>
                    </select>
                    <input
                      type="date"
                      value={(form as Record<string, unknown>)[permit.key_d] as string ?? ""}
                      onChange={(e) => setForm({ ...form, [permit.key_d]: e.target.value })}
                      style={{ width: "100%", padding: "6px 8px", border: "1px solid rgba(14,13,11,0.15)", borderRadius: 6, fontSize: 11, boxSizing: "border-box" }}
                    />
                  </>
                ) : (
                  <>
                    <PermitBadge status={permit.status} />
                    {permit.date && (
                      <div style={{ fontSize: 10, color: "var(--color-ink-3)", marginTop: 6 }}>
                        Tanggal: {permit.date}
                      </div>
                    )}
                  </>
                )}
              </div>
            ))}
          </div>
        </div>
      )}

      {/* ── Quick links ── */}
      <div style={{ display: "flex", gap: 12, marginTop: 16 }}>
        <Link href={`/dashboard/units?project=${project.id}`} className="btn-ghost" style={{ display: "flex", alignItems: "center", gap: 6 }}>
          <Home size={14} /> Kelola Unit
        </Link>
        <Link href={`/dashboard/construction`} className="btn-ghost" style={{ display: "flex", alignItems: "center", gap: 6 }}>
          <Building2 size={14} /> Progres Konstruksi
        </Link>
      </div>
    </div>
  );
}
