"use client";
// =============================================================================
// === frontend/app/dashboard/projects/[id]/page.tsx ===
// =============================================================================
/**
 * Project Detail — full intelligence view.
 * Live readiness score, clickable requirements, stage advancement.
 */

import {
  IntelligenceSummary, Project, ProjectStage,
  RISK_META, STAGE_META, TREND_META,
  UpdateProjectPayload, projectsApi,
} from "@/lib/api/projects";
import {
  AlertTriangle, ArrowRight, Building2,
  Calendar, CheckCircle2, ChevronLeft,
  Circle, Clock, FileText, Home,
  Loader2, MapPin, Save, TrendingUp,
} from "lucide-react";
import Link from "next/link";
import { useParams } from "next/navigation";
import { useEffect, useState } from "react";

// ── Circular readiness gauge ──────────────────────────────────
function ReadinessGauge({ score }: { score: number }) {
  const radius      = 36;
  const circumference = 2 * Math.PI * radius;
  const offset      = circumference - (score / 100) * circumference;
  const color =
    score >= 80 ? "var(--color-success)" :
    score >= 50 ? "var(--color-warning)" :
                  "var(--color-danger)";

  return (
    <div style={{ position: "relative", width: 100, height: 100, flexShrink: 0 }}>
      <svg width="100" height="100" style={{ transform: "rotate(-90deg)" }}>
        {/* Background circle */}
        <circle cx="50" cy="50" r={radius}
          fill="none" stroke="rgba(14,13,11,0.08)" strokeWidth="8" />
        {/* Progress arc */}
        <circle cx="50" cy="50" r={radius}
          fill="none" stroke={color} strokeWidth="8"
          strokeDasharray={circumference}
          strokeDashoffset={offset}
          strokeLinecap="round"
          style={{ transition: "stroke-dashoffset 0.5s ease" }}
        />
      </svg>
      <div style={{
        position: "absolute", inset: 0,
        display: "flex", flexDirection: "column",
        alignItems: "center", justifyContent: "center",
      }}>
        <span style={{ fontSize: 20, fontWeight: 800, color, lineHeight: 1 }}>
          {score}%
        </span>
        <span style={{ fontSize: 9, color: "var(--color-ink-3)", marginTop: 2 }}>
          KESIAPAN
        </span>
      </div>
    </div>
  );
}

// ── Stage pipeline ────────────────────────────────────────────
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
    <div style={{ display: "flex", alignItems: "flex-start" }}>
      {stages.map((s, i) => {
        const meta    = STAGE_META[s.key];
        const done    = i < currentIdx;
        const current = i === currentIdx;
        return (
          <div key={s.key} style={{ flex: 1, display: "flex", flexDirection: "column", alignItems: "center", position: "relative" }}>
            {i < stages.length - 1 && (
              <div style={{
                position: "absolute", top: 14, left: "50%", right: "-50%",
                height: 2, zIndex: 0,
                backgroundColor: done ? "var(--color-success)" : "rgba(14,13,11,0.08)",
              }} />
            )}
            <div style={{
              width: 28, height: 28, borderRadius: "50%", position: "relative", zIndex: 1,
              backgroundColor: done ? "var(--color-success)" : current ? meta.color : "rgba(14,13,11,0.08)",
              border: current ? `3px solid ${meta.color}` : "none",
              display: "flex", alignItems: "center", justifyContent: "center",
              boxShadow: current ? `0 0 0 4px ${meta.bg}` : "none",
            }}>
              {done    && <CheckCircle2 size={14} color="white" />}
              {current && <div style={{ width: 8, height: 8, borderRadius: "50%", backgroundColor: "white" }} />}
            </div>
            <div style={{
              marginTop: 8, fontSize: 10, textAlign: "center", lineHeight: 1.3,
              fontWeight: current ? 700 : 500,
              color: current ? meta.color : done ? "var(--color-success)" : "var(--color-ink-3)",
            }}>
              {s.label}
            </div>
          </div>
        );
      })}
    </div>
  );
}

// ── Requirement row ───────────────────────────────────────────
type ReqStatus = "pending" | "in_progress" | "completed" | "not_applicable";

function RequirementRow({
  req,
  projectId,
  onUpdated,
}: {
  req:       IntelligenceSummary["requirements"][0];
  projectId: string;
  onUpdated: (intel: IntelligenceSummary) => void;
}) {
  const [saving, setSaving] = useState(false);
  const [notes,  setNotes]  = useState(req.notes);
  const [showNote, setShowNote] = useState(false);

  const handleStatusChange = async (newStatus: ReqStatus) => {
    if (!req.status_id && newStatus !== "pending") {
      // No status row yet — need to create via the update endpoint
      // status_id is null when no ProjectRequirementStatus row exists
    }
    if (newStatus === req.status) return;
    setSaving(true);
    try {
      const intel = await projectsApi.updateRequirement(
        projectId,
        req.status_id ?? req.id, // fall back to requirement id
        { status: newStatus, notes }
      );
      onUpdated(intel);
    } catch (e) {
      console.error(e);
    } finally {
      setSaving(false);
    }
  };

  const statusConfig: Record<ReqStatus, { label: string; color: string; bg: string; icon: React.ReactNode }> = {
    pending:        { label: "Belum Dimulai", color: "var(--color-ink-3)",   bg: "var(--color-paper-2)",       icon: <Circle size={14} /> },
    in_progress:    { label: "Sedang Diproses",color: "var(--color-warning)", bg: "var(--color-warning-light)", icon: <Clock size={14} /> },
    completed:      { label: "Selesai",       color: "var(--color-success)", bg: "var(--color-success-light)", icon: <CheckCircle2 size={14} /> },
    not_applicable: { label: "Tidak Berlaku", color: "var(--color-ink-3)",   bg: "var(--color-paper-2)",       icon: <Circle size={14} /> },
  };

  const current = statusConfig[req.status as ReqStatus] ?? statusConfig.pending;
  const isBlocking = req.is_mandatory && req.status !== "completed";

  return (
    <div style={{
      padding: "12px 14px",
      borderRadius: 8,
      backgroundColor: req.status === "completed"
        ? "var(--color-success-light)"
        : isBlocking
        ? "rgba(220,38,38,0.04)"
        : "var(--color-paper-2)",
      border: isBlocking ? "1px solid rgba(220,38,38,0.15)" : "1px solid transparent",
      marginBottom: 8,
      transition: "all 0.2s",
    }}>
      <div style={{ display: "flex", alignItems: "center", gap: 10 }}>
        {/* Status icon */}
        <div style={{ color: current.color, flexShrink: 0 }}>
          {saving ? <Loader2 size={14} style={{ animation: "spin 1s linear infinite" }} /> : current.icon}
        </div>

        {/* Name + description */}
        <div style={{ flex: 1, minWidth: 0 }}>
          <div style={{ display: "flex", alignItems: "center", gap: 6 }}>
            <span style={{
              fontSize: 13, fontWeight: 500,
              color: req.status === "completed" ? "var(--color-ink-3)" : "var(--color-ink)",
              textDecoration: req.status === "completed" ? "line-through" : "none",
            }}>
              {req.name}
            </span>
            {req.is_mandatory && req.status !== "completed" && (
              <span style={{ fontSize: 10, color: "var(--color-danger)", fontWeight: 600 }}>
                ⚡ Wajib
              </span>
            )}
            {!req.is_mandatory && (
              <span style={{ fontSize: 10, color: "var(--color-ink-3)" }}>opsional</span>
            )}
          </div>
          {req.description && (
            <div style={{ fontSize: 11, color: "var(--color-ink-3)", marginTop: 2 }}>
              {req.description}
            </div>
          )}
          {req.completed_at && (
            <div style={{ fontSize: 10, color: "var(--color-success)", marginTop: 2 }}>
              ✓ Selesai {new Date(req.completed_at).toLocaleDateString("id-ID")}
            </div>
          )}
        </div>

        {/* Status selector */}
        {req.status !== "completed" ? (
          <div style={{ display: "flex", gap: 4, flexShrink: 0 }}>
            <button
              onClick={() => handleStatusChange("in_progress")}
              disabled={saving || req.status === "in_progress"}
              style={{
                padding: "4px 8px", borderRadius: 4, border: "none",
                fontSize: 10, fontWeight: 600, cursor: "pointer",
                backgroundColor: req.status === "in_progress" ? "var(--color-warning-light)" : "white",
                color: "var(--color-warning)",
                border: "1px solid rgba(14,13,11,0.1)",
                opacity: saving ? 0.5 : 1,
              }}
            >
              Diproses
            </button>
            <button
              onClick={() => handleStatusChange("completed")}
              disabled={saving}
              style={{
                padding: "4px 10px", borderRadius: 4, border: "none",
                fontSize: 10, fontWeight: 600, cursor: "pointer",
                backgroundColor: "var(--color-success)",
                color: "white",
                opacity: saving ? 0.5 : 1,
              }}
            >
              Selesai ✓
            </button>
          </div>
        ) : (
          <button
            onClick={() => handleStatusChange("pending")}
            disabled={saving}
            style={{
              padding: "4px 8px", borderRadius: 4, border: "1px solid rgba(14,13,11,0.1)",
              fontSize: 10, cursor: "pointer", backgroundColor: "white",
              color: "var(--color-ink-3)", opacity: saving ? 0.5 : 1,
            }}
          >
            Batalkan
          </button>
        )}
      </div>
    </div>
  );
}

// ── Permit badge ──────────────────────────────────────────────
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
  const params    = useParams();
  const id        = params.id as string;

  const [project,    setProject]    = useState<Project | null>(null);
  const [intel,      setIntel]      = useState<IntelligenceSummary | null>(null);
  const [loading,    setLoading]    = useState(true);
  const [advancing,  setAdvancing]  = useState(false);
  const [saving,     setSaving]     = useState(false);
  const [editMode,   setEditMode]   = useState(false);
  const [error,      setError]      = useState<string | null>(null);
  const [form,       setForm]       = useState<UpdateProjectPayload>({});

  const loadProject = async () => {
    try {
      const [p, i] = await Promise.all([
        projectsApi.get(id),
        projectsApi.getIntelligence(id),
      ]);
      setProject(p);
      setIntel(i);
      setForm(buildForm(p));
    } catch {
      setError("Gagal memuat proyek");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => { loadProject(); }, [id]);

  function buildForm(p: Project): UpdateProjectPayload {
    return {
      name:          p.name,
      location:      p.location,
      description:   p.description,
      total_units:   p.total_units,
      target_budget: p.target_budget ?? "",
      start_date:    p.start_date ?? "",
      end_date:      p.end_date ?? "",
      ipr_status:    p.ipr_status,
      ipr_date:      p.ipr_date ?? "",
      amdal_status:  p.amdal_status,
      amdal_date:    p.amdal_date ?? "",
      pbg_status:    p.pbg_status,
      pbg_date:      p.pbg_date ?? "",
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
      // Refresh intelligence after update
      const i = await projectsApi.getIntelligence(project.id);
      setIntel(i);
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
      const i = await projectsApi.getIntelligence(updated.id);
      setIntel(i);
    } catch (e: unknown) {
      const msg = e instanceof Error ? e.message : "Gagal melanjutkan tahap";
      setError(msg);
    } finally {
      setAdvancing(false);
    }
  };

  const handleRequirementUpdated = (newIntel: IntelligenceSummary) => {
    setIntel(newIntel);
    // Refresh project for updated can_advance
    projectsApi.get(id).then(setProject).catch(() => {});
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

  if (!project || !intel) return null;

  const meta         = STAGE_META[project.stage];
  const riskMeta     = RISK_META[intel.risk_level];
  const trendMeta    = TREND_META[intel.trend];
  const mandatory    = intel.requirements.filter((r) => r.is_mandatory);
  const optional     = intel.requirements.filter((r) => !r.is_mandatory);

  return (
    <div style={{ maxWidth: 960, margin: "0 auto" }}>

      {/* ── Back ── */}
      <Link href="/dashboard/projects" style={{ display: "inline-flex", alignItems: "center", gap: 5, fontSize: 12, color: "var(--color-ink-3)", textDecoration: "none", marginBottom: 20 }}>
        <ChevronLeft size={14} /> Kembali ke Semua Proyek
      </Link>

      {/* ── Header ── */}
      <div style={{ display: "flex", alignItems: "flex-start", justifyContent: "space-between", marginBottom: 24 }}>
        <div>
          <div style={{ display: "flex", alignItems: "center", gap: 8, marginBottom: 6 }}>
            <span style={{ fontSize: 11, fontWeight: 700, color: meta.color, textTransform: "uppercase", letterSpacing: "0.08em" }}>
              {meta.label}
            </span>
            <span style={{ fontSize: 11, color: "var(--color-ink-3)" }}>— {meta.description}</span>
          </div>
          <h1 style={{ fontSize: 26, fontWeight: 700, color: "var(--color-ink)", margin: 0, marginBottom: 4 }}>
            {project.name}
          </h1>
          <div style={{ display: "flex", alignItems: "center", gap: 4, fontSize: 13, color: "var(--color-ink-3)" }}>
            <MapPin size={13} /> {project.location}
          </div>
        </div>
        <div style={{ display: "flex", gap: 8 }}>
          {editMode ? (
            <>
              <button className="btn-ghost btn-sm" onClick={() => setEditMode(false)}>Batal</button>
              <button className="btn-accent btn-sm" onClick={handleSave} disabled={saving} style={{ display: "flex", alignItems: "center", gap: 4 }}>
                {saving ? <Loader2 size={12} style={{ animation: "spin 1s linear infinite" }} /> : <Save size={12} />} Simpan
              </button>
            </>
          ) : (
            <button className="btn-ghost btn-sm" onClick={() => setEditMode(true)}>Edit Proyek</button>
          )}
        </div>
      </div>

      {/* ── Error ── */}
      {error && (
        <div style={{ marginBottom: 16, padding: "12px 16px", backgroundColor: "var(--color-danger-light)", borderRadius: 8, fontSize: 13, color: "var(--color-danger)", display: "flex", alignItems: "center", gap: 8 }}>
          <AlertTriangle size={14} /> {error}
          <button onClick={() => setError(null)} style={{ marginLeft: "auto", background: "none", border: "none", cursor: "pointer", color: "var(--color-danger)" }}>✕</button>
        </div>
      )}

      {/* ── Intelligence summary bar ── */}
      <div className="card" style={{ marginBottom: 16 }}>
        <div style={{ display: "flex", alignItems: "center", gap: 24, flexWrap: "wrap" }}>

          {/* Readiness gauge */}
          <ReadinessGauge score={intel.readiness_score} />

          {/* Stats */}
          <div style={{ flex: 1, display: "grid", gridTemplateColumns: "repeat(3, 1fr)", gap: 16 }}>

            <div style={{ textAlign: "center", padding: "12px", backgroundColor: intel.blocking_count > 0 ? "var(--color-danger-light)" : "var(--color-success-light)", borderRadius: 8 }}>
              <div style={{ fontSize: 24, fontWeight: 800, color: intel.blocking_count > 0 ? "var(--color-danger)" : "var(--color-success)" }}>
                {intel.blocking_count}
              </div>
              <div style={{ fontSize: 11, color: "var(--color-ink-3)", marginTop: 2 }}>Item Blokir</div>
            </div>

            <div style={{ textAlign: "center", padding: "12px", backgroundColor: riskMeta.bg, borderRadius: 8 }}>
              <div style={{ fontSize: 18, fontWeight: 800, color: riskMeta.color }}>{riskMeta.label}</div>
              <div style={{ fontSize: 11, color: "var(--color-ink-3)", marginTop: 2 }}>Tingkat Risiko</div>
            </div>

            <div style={{ textAlign: "center", padding: "12px", backgroundColor: "var(--color-paper-2)", borderRadius: 8 }}>
              <div style={{ fontSize: 24, fontWeight: 800, color: trendMeta.color }}>{trendMeta.icon}</div>
              <div style={{ fontSize: 11, color: "var(--color-ink-3)", marginTop: 2 }}>
                {intel.trend === "improving" ? "Membaik" : intel.trend === "declining" ? "Menurun" : "Stabil"}
              </div>
            </div>
          </div>

          {/* Next action + advance button */}
          <div style={{ minWidth: 220 }}>
            {intel.next_action && (
              <div style={{ marginBottom: 12, padding: "10px 12px", backgroundColor: "var(--color-warning-light)", borderRadius: 8 }}>
                <div style={{ fontSize: 10, fontWeight: 700, color: "var(--color-warning)", textTransform: "uppercase", letterSpacing: "0.06em", marginBottom: 4 }}>
                  Tindakan Berikutnya
                </div>
                <div style={{ fontSize: 13, fontWeight: 600, color: "var(--color-ink)" }}>
                  {intel.next_action}
                </div>
              </div>
            )}
            <button
              onClick={handleAdvance}
              disabled={advancing || !intel.can_advance}
              className={intel.can_advance ? "btn-accent" : "btn-ghost"}
              style={{
                width: "100%", display: "flex", alignItems: "center",
                justifyContent: "center", gap: 6,
                opacity: intel.can_advance ? 1 : 0.5,
              }}
            >
              {advancing
                ? <Loader2 size={14} style={{ animation: "spin 1s linear infinite" }} />
                : <ArrowRight size={14} />
              }
              {intel.can_advance ? "Lanjutkan Tahap" : "Tahap Diblokir"}
            </button>
          </div>
        </div>
      </div>

      {/* ── Stage pipeline ── */}
      <div className="card" style={{ marginBottom: 16 }}>
        <div style={{ fontSize: 12, fontWeight: 600, color: "var(--color-ink)", marginBottom: 20 }}>
          Alur Tahap Proyek
        </div>
        <StagePipeline stage={project.stage} />
      </div>

      <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 16 }}>

        {/* ── Requirements ── */}
        <div className="card">
          <div style={{ fontSize: 13, fontWeight: 600, color: "var(--color-ink)", marginBottom: 16 }}>
            Checklist Tahap {meta.label}
            <span style={{ fontSize: 11, fontWeight: 400, color: "var(--color-ink-3)", marginLeft: 8 }}>
              {intel.requirements.filter(r => r.status === "completed").length}/{intel.requirements.length} selesai
            </span>
          </div>

          {intel.requirements.length === 0 ? (
            <div style={{ fontSize: 12, color: "var(--color-ink-3)", fontStyle: "italic", textAlign: "center", padding: "24px 0" }}>
              Tidak ada checklist untuk tahap ini
            </div>
          ) : (
            <>
              {/* Mandatory first */}
              {mandatory.length > 0 && (
                <>
                  <div style={{ fontSize: 10, fontWeight: 700, color: "var(--color-danger)", textTransform: "uppercase", letterSpacing: "0.06em", marginBottom: 8 }}>
                    ⚡ Wajib ({mandatory.filter(r => r.status === "completed").length}/{mandatory.length})
                  </div>
                  {mandatory.map((req) => (
                    <RequirementRow
                      key={req.id}
                      req={req}
                      projectId={project.id}
                      onUpdated={handleRequirementUpdated}
                    />
                  ))}
                </>
              )}

              {/* Optional */}
              {optional.length > 0 && (
                <>
                  <div style={{ fontSize: 10, fontWeight: 600, color: "var(--color-ink-3)", textTransform: "uppercase", letterSpacing: "0.06em", marginTop: 12, marginBottom: 8 }}>
                    Opsional ({optional.filter(r => r.status === "completed").length}/{optional.length})
                  </div>
                  {optional.map((req) => (
                    <RequirementRow
                      key={req.id}
                      req={req}
                      projectId={project.id}
                      onUpdated={handleRequirementUpdated}
                    />
                  ))}
                </>
              )}
            </>
          )}
        </div>

        {/* ── Project info / edit ── */}
        <div style={{ display: "flex", flexDirection: "column", gap: 16 }}>

          {/* Basic info card */}
          <div className="card">
            <div style={{ fontSize: 13, fontWeight: 600, color: "var(--color-ink)", marginBottom: 16 }}>
              Informasi Proyek
            </div>

            {editMode ? (
              <div style={{ display: "flex", flexDirection: "column", gap: 10 }}>
                {[
                  { label: "Nama Proyek",    key: "name",          type: "text" },
                  { label: "Lokasi",         key: "location",      type: "text" },
                  { label: "Total Unit",     key: "total_units",   type: "number" },
                  { label: "Target Anggaran",key: "target_budget", type: "text" },
                  { label: "Tanggal Mulai",  key: "start_date",    type: "date" },
                  { label: "Target Selesai", key: "end_date",      type: "date" },
                ].map((field) => (
                  <div key={field.key}>
                    <label style={{ display: "block", fontSize: 11, fontWeight: 500, color: "var(--color-ink-3)", marginBottom: 3 }}>
                      {field.label}
                    </label>
                    <input
                      type={field.type}
                      value={(form as Record<string, unknown>)[field.key] as string ?? ""}
                      onChange={(e) => setForm({ ...form, [field.key]: field.type === "number" ? Number(e.target.value) : e.target.value })}
                      style={{ width: "100%", padding: "7px 10px", border: "1px solid rgba(14,13,11,0.15)", borderRadius: 6, fontSize: 12, color: "var(--color-ink)", outline: "none", boxSizing: "border-box" }}
                    />
                  </div>
                ))}
                <div>
                  <label style={{ display: "block", fontSize: 11, fontWeight: 500, color: "var(--color-ink-3)", marginBottom: 3 }}>Deskripsi</label>
                  <textarea
                    value={form.description ?? ""}
                    onChange={(e) => setForm({ ...form, description: e.target.value })}
                    rows={3}
                    style={{ width: "100%", padding: "7px 10px", border: "1px solid rgba(14,13,11,0.15)", borderRadius: 6, fontSize: 12, color: "var(--color-ink)", outline: "none", resize: "vertical", boxSizing: "border-box", fontFamily: "inherit" }}
                  />
                </div>
              </div>
            ) : (
              <div>
                {[
                  { label: "Total Unit",      value: String(project.total_units || "—"),   icon: Home },
                  { label: "Unit Terjual",    value: String(project.units_sold),            icon: TrendingUp },
                  { label: "Target Anggaran", value: project.target_budget ? `Rp ${Number(project.target_budget).toLocaleString("id-ID")}` : "—", icon: FileText },
                  { label: "Tanggal Mulai",   value: project.start_date ?? "—",             icon: Calendar },
                  { label: "Target Selesai",  value: project.end_date   ?? "—",             icon: Calendar },
                ].map((row) => (
                  <div key={row.label} style={{ display: "flex", alignItems: "center", justifyContent: "space-between", padding: "8px 0", borderBottom: "1px solid rgba(14,13,11,0.05)" }}>
                    <div style={{ display: "flex", alignItems: "center", gap: 6, fontSize: 12, color: "var(--color-ink-3)" }}>
                      <row.icon size={12} /> {row.label}
                    </div>
                    <div style={{ fontSize: 12, fontWeight: 500, color: "var(--color-ink)" }}>{row.value}</div>
                  </div>
                ))}
              </div>
            )}
          </div>

          {/* Permits card */}
          {["perizinan", "konstruksi", "penjualan", "serah_terima", "selesai"].includes(project.stage) && (
            <div className="card">
              <div style={{ fontSize: 13, fontWeight: 600, color: "var(--color-ink)", marginBottom: 16 }}>
                Status Perizinan
              </div>
              <div style={{ display: "flex", flexDirection: "column", gap: 10 }}>
                {[
                  { label: "IPR",           status: project.ipr_status,   date: project.ipr_date,   key_s: "ipr_status",   key_d: "ipr_date",   desc: "Izin Pemanfaatan Ruang" },
                  { label: "AMDAL/UKL-UPL", status: project.amdal_status, date: project.amdal_date, key_s: "amdal_status", key_d: "amdal_date", desc: "Kajian Lingkungan" },
                  { label: "PBG ⚡",         status: project.pbg_status,   date: project.pbg_date,   key_s: "pbg_status",   key_d: "pbg_date",   desc: "Persetujuan Bangunan Gedung" },
                ].map((permit) => (
                  <div key={permit.label} style={{ display: "flex", alignItems: "center", justifyContent: "space-between", padding: "10px 12px", backgroundColor: "var(--color-paper-2)", borderRadius: 8 }}>
                    <div>
                      <div style={{ fontSize: 12, fontWeight: 600, color: "var(--color-ink)" }}>{permit.label}</div>
                      <div style={{ fontSize: 10, color: "var(--color-ink-3)" }}>{permit.desc}</div>
                      {permit.date && <div style={{ fontSize: 10, color: "var(--color-ink-3)", marginTop: 2 }}>{permit.date}</div>}
                    </div>
                    {editMode ? (
                      <select
                        value={(form as Record<string, unknown>)[permit.key_s] as string ?? "belum"}
                        onChange={(e) => setForm({ ...form, [permit.key_s]: e.target.value })}
                        style={{ padding: "5px 8px", border: "1px solid rgba(14,13,11,0.15)", borderRadius: 6, fontSize: 11, backgroundColor: "white" }}
                      >
                        <option value="belum">Belum Dimulai</option>
                        <option value="proses">Sedang Diproses</option>
                        <option value="approved">Disetujui</option>
                        <option value="rejected">Ditolak</option>
                      </select>
                    ) : (
                      <PermitBadge status={permit.status} />
                    )}
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* Quick links */}
          <div style={{ display: "flex", gap: 10 }}>
            <Link href={`/dashboard/units?project=${project.id}`} className="btn-ghost" style={{ flex: 1, display: "flex", alignItems: "center", justifyContent: "center", gap: 6, fontSize: 12 }}>
              <Home size={13} /> Kelola Unit
            </Link>
            <Link href="/dashboard/construction" className="btn-ghost" style={{ flex: 1, display: "flex", alignItems: "center", justifyContent: "center", gap: 6, fontSize: 12 }}>
              <Building2 size={13} /> Konstruksi
            </Link>
          </div>
        </div>
      </div>
    </div>
  );
}
