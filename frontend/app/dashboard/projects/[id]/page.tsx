"use client";
// ===========================================================
// === frontend/app/dashboard/projects/[id]/page.tsx ===
// Sprint 4: dependency-aware RequirementRow
// All Sprint 1/2/3 sections preserved — additive only.
//  Sprint7 :requirement ownership and accountability - implemented here
//  Sprint 9 : next actions assistant dashboard widget - is NOT implemented at this stage
//  Spint 10 :Live Intelligence Dashboard - IS implemented here
//  Sprint 14 : Risk Forecast (14-day projection) - IS implemented here
// ============================================================

import {
  ActionChain,
  ActivityFilterType,
  ActivityItem,
  ALERT_META,
  commentApi,
  DecisionEngine,
  DependencyGraph,
  DependencyNode,
  EVIDENCE_META,
  EVIDENCE_VERSION_META,
  evidenceApi,
  getRiskScoreMeta,
  IntelligenceSummary,
  KeyProgress,
  OrgMember,
  Project,
  projectsApi,
  ProjectStage,
  PulseEvent,
  PulseResponse,
  READINESS_LABEL_META,
  ReadinessHistoryPoint,
  RequirementComment,
  RequirementEvidence,
  RequirementItem,
  RISK_FACTOR_IMPACT_META,
  RISK_META,
  RiskForecast,
  STAGE_META,
  TREND_META,
  UpdateProjectPayload
} from "@/lib/api/projects";
import {
  AlertTriangle,
  ArrowRight,
  Building2,
  Calendar,
  CheckCircle2,
  ChevronLeft,
  Circle,
  Clock,
  FileText,
  Home,
  Loader2,
  Lock,
  MapPin,
  Paperclip,
  Save,
  TrendingUp,
  X,
  Zap,
} from "lucide-react";
import Link from "next/link";
import { useParams } from "next/navigation";
import { useCallback, useEffect, useRef, useState, } from "react";
import {
  Line,
  LineChart,
  ReferenceLine,
  ResponsiveContainer,
  Tooltip,
  XAxis, YAxis,
} from "recharts";

// ── Circular readiness gauge ──────────────────────────────────
function ReadinessGauge({ score }: { score: number }) {
  const radius        = 36;
  const circumference = 2 * Math.PI * radius;
  const offset        = circumference - (score / 100) * circumference;
  const color =
    score >= 80 ? "var(--color-success)" :
    score >= 50 ? "var(--color-warning)" :
                  "var(--color-danger)";
  return (
    <div style={{ position: "relative", width: 100, height: 100, flexShrink: 0 }}>
      <svg width="100" height="100" style={{ transform: "rotate(-90deg)" }}>
        <circle cx="50" cy="50" r={radius} fill="none" stroke="rgba(14,13,11,0.08)" strokeWidth="8" />
        <circle cx="50" cy="50" r={radius} fill="none" stroke={color} strokeWidth="8"
          strokeDasharray={circumference} strokeDashoffset={offset}
          strokeLinecap="round" style={{ transition: "stroke-dashoffset 0.5s ease" }} />
      </svg>
      <div style={{ position: "absolute", inset: 0, display: "flex", flexDirection: "column", alignItems: "center", justifyContent: "center" }}>
        <span style={{ fontSize: 20, fontWeight: 800, color, lineHeight: 1 }}>{score}%</span>
        <span style={{ fontSize: 9, color: "var(--color-ink-3)", marginTop: 2 }}>KESIAPAN</span>
      </div>
    </div>
  );
}

// ── Stage pipeline ────────────────────────────────────────────
function StagePipeline({ stage }: { stage: ProjectStage }) {
  const stages: { key: ProjectStage; label: string }[] = [
    { key: "draft",        label: "Draft"        },
    { key: "perencanaan",  label: "Perencanaan"  },
    { key: "perizinan",    label: "Perizinan"    },
    { key: "konstruksi",   label: "Konstruksi"   },
    { key: "penjualan",    label: "Penjualan"    },
    { key: "serah_terima", label: "Serah Terima" },
    { key: "selesai",      label: "Selesai"      },
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
              <div style={{ position: "absolute", top: 14, left: "50%", right: "-50%", height: 2, zIndex: 0, backgroundColor: done ? "var(--color-success)" : "rgba(14,13,11,0.08)" }} />
            )}
            <div style={{ width: 28, height: 28, borderRadius: "50%", position: "relative", zIndex: 1, backgroundColor: done ? "var(--color-success)" : current ? meta.color : "rgba(14,13,11,0.08)", border: current ? `3px solid ${meta.color}` : "none", display: "flex", alignItems: "center", justifyContent: "center", boxShadow: current ? `0 0 0 4px ${meta.bg}` : "none" }}>
              {done    && <CheckCircle2 size={14} color="white" />}
              {current && <div style={{ width: 8, height: 8, borderRadius: "50%", backgroundColor: "white" }} />}
            </div>
            <div style={{ marginTop: 8, fontSize: 10, textAlign: "center", lineHeight: 1.3, fontWeight: current ? 700 : 500, color: current ? meta.color : done ? "var(--color-success)" : "var(--color-ink-3)" }}>
              {s.label}
            </div>
          </div>
        );
      })}
    </div>
  );
}

// ── Evidence upload modal ─────────────────────────────────────
function EvidenceUploadModal({
  req, projectId, onUploaded, onClose,
}: {
  req: RequirementItem; projectId: string;
  onUploaded: (intel: IntelligenceSummary) => void; onClose: () => void;
}) {
  const [mode,   setMode]   = useState<"file" | "url">("url");
  const [fileUrl, setFileUrl] = useState("");
  const [notes,  setNotes]  = useState("");
  const [saving, setSaving] = useState(false);
  const [error,  setError]  = useState<string | null>(null);
  const fileRef = useRef<HTMLInputElement>(null);

  const handleSubmit = async () => {
    if (mode === "url" && !fileUrl.trim()) { setError("Masukkan URL bukti"); return; }
    if (mode === "file" && !fileRef.current?.files?.[0]) { setError("Pilih file untuk diunggah"); return; }
    setSaving(true); setError(null);
    try {
      const result = await evidenceApi.upload(projectId, req.status_id ?? req.id, {
        file:     mode === "file" ? fileRef.current?.files?.[0] : undefined,
        file_url: mode === "url"  ? fileUrl.trim() : undefined,
        notes:    notes.trim(),
      });
      onUploaded(result.intelligence);
    } catch { setError("Gagal mengunggah bukti"); }
    finally { setSaving(false); }
  };

  const inputStyle: React.CSSProperties = { width: "100%", padding: "8px 10px", border: "1px solid rgba(14,13,11,0.15)", borderRadius: 6, fontSize: 13, color: "var(--color-ink)", outline: "none", boxSizing: "border-box" };

  return (
    <div style={{ position: "fixed", inset: 0, zIndex: 200, backgroundColor: "rgba(14,13,11,0.5)", display: "flex", alignItems: "center", justifyContent: "center", padding: 16 }}>
      <div style={{ backgroundColor: "white", borderRadius: 12, width: "100%", maxWidth: 460, boxShadow: "0 20px 60px rgba(14,13,11,0.2)", overflow: "hidden" }}>
        <div style={{ padding: "18px 20px 14px", borderBottom: "1px solid rgba(14,13,11,0.06)", display: "flex", alignItems: "center", justifyContent: "space-between" }}>
          <div>
            <div style={{ display: "flex", alignItems: "center", gap: 6, marginBottom: 3 }}>
              <Paperclip size={13} style={{ color: "var(--color-accent)" }} />
              <span style={{ fontSize: 10, fontWeight: 700, color: "var(--color-accent)", textTransform: "uppercase", letterSpacing: "0.08em" }}>Upload Bukti</span>
            </div>
            <div style={{ fontSize: 15, fontWeight: 600, color: "var(--color-ink)" }}>{req.name}</div>
          </div>
          <button onClick={onClose} style={{ padding: 6, borderRadius: 6, border: "none", backgroundColor: "transparent", cursor: "pointer", color: "var(--color-ink-3)" }}>
            <X size={16} />
          </button>
        </div>
        <div style={{ padding: "16px 20px 20px" }}>
          {error && <div style={{ marginBottom: 12, padding: "8px 12px", backgroundColor: "var(--color-danger-light)", borderRadius: 6, fontSize: 12, color: "var(--color-danger)" }}>{error}</div>}
          <div style={{ display: "flex", gap: 6, marginBottom: 14 }}>
            {(["url", "file"] as const).map((m) => (
              <button key={m} onClick={() => setMode(m)}
                style={{ flex: 1, padding: "7px 10px", borderRadius: 6, border: "1px solid rgba(14,13,11,0.12)", fontSize: 12, fontWeight: 600, cursor: "pointer", backgroundColor: mode === m ? "var(--color-accent)" : "white", color: mode === m ? "white" : "var(--color-ink-3)", transition: "all 0.15s" }}>
                {m === "url" ? "🔗 Link URL" : "📎 Upload File"}
              </button>
            ))}
          </div>
          {mode === "url" && (
            <div style={{ marginBottom: 12 }}>
              <label style={{ display: "block", fontSize: 11, fontWeight: 500, color: "var(--color-ink-3)", marginBottom: 5 }}>URL Bukti <span style={{ color: "var(--color-danger)" }}>*</span></label>
              <input type="url" placeholder="https://drive.google.com/..." value={fileUrl} onChange={(e) => setFileUrl(e.target.value)} style={inputStyle} />
              <div style={{ fontSize: 10, color: "var(--color-ink-3)", marginTop: 3 }}>Google Drive, Dropbox, OneDrive, atau URL dokumen lainnya</div>
            </div>
          )}
          {mode === "file" && (
            <div style={{ marginBottom: 12 }}>
              <label style={{ display: "block", fontSize: 11, fontWeight: 500, color: "var(--color-ink-3)", marginBottom: 5 }}>File Bukti <span style={{ color: "var(--color-danger)" }}>*</span></label>
              <input ref={fileRef} type="file" accept=".pdf,.jpg,.jpeg,.png,.doc,.docx,.xls,.xlsx" style={{ ...inputStyle, padding: "6px 10px" }} />
            </div>
          )}
          <div style={{ marginBottom: 18 }}>
            <label style={{ display: "block", fontSize: 11, fontWeight: 500, color: "var(--color-ink-3)", marginBottom: 5 }}>Deskripsi Bukti <span style={{ fontSize: 10, color: "var(--color-ink-3)", fontWeight: 400 }}>(opsional)</span></label>
            <textarea rows={2} placeholder="Jelaskan bukti yang diunggah..." value={notes} onChange={(e) => setNotes(e.target.value)} style={{ ...inputStyle, resize: "vertical", fontFamily: "inherit" }} />
          </div>
          <div style={{ display: "flex", gap: 8 }}>
            <button onClick={onClose} className="btn-ghost" style={{ flex: 1 }} disabled={saving}>Batal</button>
            <button onClick={handleSubmit} className="btn-accent" disabled={saving} style={{ flex: 2, display: "flex", alignItems: "center", justifyContent: "center", gap: 6 }}>
              {saving ? <><Loader2 size={13} style={{ animation: "spin 1s linear infinite" }} /> Mengunggah…</> : <><Paperclip size={13} /> Upload Bukti</>}
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}

// ── Sprint 8: Evidence item with version tracking ─────────────
function EvidenceItem({ ev, projectId, reqStatusId, onVerified, onResubmit }: {
  ev:           RequirementEvidence;
  projectId:    string;
  reqStatusId:  string;
  onVerified:   (intel: IntelligenceSummary) => void;
  onResubmit:   () => void;   // Sprint 8: triggers re-upload modal
}) {
  const [verifying,    setVerifying]    = useState(false);
  const [showNotes,    setShowNotes]    = useState(false);
  const [notes,        setNotes]        = useState("");
  const [action,       setAction]       = useState<"approve" | "reject" | null>(null);
  const [showHistory,  setShowHistory]  = useState(false);
  const meta = EVIDENCE_META[ev.verification_status];

  const handleVerify = async (act: "approve" | "reject") => {
    setVerifying(true);
    try {
      const result = await evidenceApi.verify(projectId, reqStatusId, ev.id, act, notes);
      onVerified(result.intelligence);
    } catch (e: unknown) {
      console.error("Verify failed", e);
    } finally { setVerifying(false); setShowNotes(false); setAction(null); }
  };

  const hasHistory    = ev.version_chain && ev.version_chain.length > 1;
  const isRejected    = ev.verification_status === "rejected";
  const isApproved    = ev.verification_status === "approved";
  const isPending     = ev.verification_status === "pending";

  return (
    <div style={{
      padding: "10px 12px",
      backgroundColor: meta.bg,
      border: `1px solid rgba(14,13,11,0.06)`,
      borderRadius: 8,
      marginBottom: 8,
    }}>
      {/* ── Header row ── */}
      <div style={{ display: "flex", alignItems: "center", gap: 8 }}>
        <Paperclip size={11} style={{ color: meta.color, flexShrink: 0 }} />
        <div style={{ flex: 1, minWidth: 0 }}>
          <div style={{ display: "flex", alignItems: "center", gap: 6, flexWrap: "wrap" }}>
            <span style={{ fontSize: 11, fontWeight: 500, color: "var(--color-ink)", overflow: "hidden", textOverflow: "ellipsis", whiteSpace: "nowrap" }}>
              {ev.file_name || (ev.file_url ? "Link eksternal" : "Bukti")}
            </span>
            {/* Sprint 8: version badge */}
            <span style={{
              fontSize: 10, fontWeight: 700, padding: "1px 6px", borderRadius: 999,
              backgroundColor: "white", color: meta.color, border: `1px solid ${meta.color}33`,
            }}>
              {ev.version_label}
            </span>
            {!ev.is_latest && (
              <span style={{ fontSize: 10, color: "var(--color-ink-3)", fontStyle: "italic" }}>
                (digantikan)
              </span>
            )}
          </div>
          {ev.file_url_display && (
            <a href={ev.file_url_display} target="_blank" rel="noopener noreferrer"
              style={{ fontSize: 10, color: "var(--color-accent)", textDecoration: "none" }}>
              Lihat bukti →
            </a>
          )}
          {ev.notes && (
            <div style={{ fontSize: 10, color: "var(--color-ink-3)", marginTop: 1 }}>{ev.notes}</div>
          )}
          <div style={{ fontSize: 10, color: "var(--color-ink-3)", marginTop: 1 }}>
            {ev.uploaded_by_name} · {new Date(ev.uploaded_at).toLocaleDateString("id-ID")}
          </div>
        </div>
        <span style={{ fontSize: 10, fontWeight: 600, padding: "2px 7px", borderRadius: 999, color: meta.color, backgroundColor: "white", flexShrink: 0 }}>
          {meta.label}
        </span>
      </div>

      {/* ── Sprint 8: Rejection reason + resubmit ── */}
      {isRejected && ev.is_latest && (
        <div style={{ marginTop: 8, padding: "8px 10px", backgroundColor: "var(--color-danger-light)", borderRadius: 6, border: "1px solid rgba(220,38,38,0.15)" }}>
          <div style={{ fontSize: 10, fontWeight: 700, color: "var(--color-danger)", textTransform: "uppercase", letterSpacing: "0.05em", marginBottom: 4 }}>
            Alasan Penolakan
          </div>
          {ev.verifier_notes && (
            <div style={{ fontSize: 11, color: "var(--color-danger)", marginBottom: 8, lineHeight: 1.4 }}>
              {ev.verifier_notes}
            </div>
          )}
          <div style={{ fontSize: 10, color: "var(--color-ink-3)", marginBottom: 6 }}>
            Diverifikasi oleh: {ev.verifier_name} · {ev.verified_at ? new Date(ev.verified_at).toLocaleDateString("id-ID") : "—"}
          </div>
          {/* Sprint 8: Re-upload button */}
          <button
            onClick={onResubmit}
            style={{
              width: "100%", padding: "6px 10px", borderRadius: 6,
              border: "none", fontSize: 11, fontWeight: 600, cursor: "pointer",
              backgroundColor: "var(--color-danger)", color: "white",
              display: "flex", alignItems: "center", justifyContent: "center", gap: 5,
            }}>
            <Paperclip size={11} /> Upload Ulang Bukti
          </button>
        </div>
      )}

      {/* ── Sprint 8: Approved info ── */}
      {isApproved && (
        <div style={{ marginTop: 6, fontSize: 10, color: "var(--color-success)", display: "flex", alignItems: "center", gap: 4 }}>
          <CheckCircle2 size={10} />
          Diverifikasi oleh {ev.verifier_name} · {ev.verified_at ? new Date(ev.verified_at).toLocaleDateString("id-ID") : ""}
        </div>
      )}

      {/* ── Sprint 8: Eligible verifiers (pending only) ── */}
      {isPending && ev.is_latest && ev.eligible_verifiers && ev.eligible_verifiers.length > 0 && (
        <div style={{ marginTop: 6, fontSize: 10, color: "var(--color-ink-3)" }}>
          Dapat diverifikasi oleh:{" "}
          <span style={{ fontWeight: 600, color: "var(--color-ink)" }}>
            {ev.eligible_verifiers.map(v => v.full_name).join(", ")}
          </span>
        </div>
      )}

      {/* ── Sprint 8: Self-upload warning ── */}
      {isPending && ev.is_latest && !ev.can_verify && ev.cannot_verify_reason && (
        <div style={{ marginTop: 6, fontSize: 10, color: "var(--color-warning)", display: "flex", alignItems: "center", gap: 4 }}>
          <Lock size={10} /> {ev.cannot_verify_reason}
        </div>
      )}

      {/* ── Verify buttons (pending + is_latest + can_verify) ── */}
      {isPending && ev.is_latest && ev.can_verify && (
        <div style={{ marginTop: 8 }}>
          {!showNotes ? (
            <div style={{ display: "flex", gap: 6 }}>
              <button
                onClick={() => { setAction("approve"); setShowNotes(true); }}
                disabled={verifying}
                style={{ flex: 1, padding: "4px 8px", borderRadius: 4, border: "none", fontSize: 10, fontWeight: 600, cursor: "pointer", backgroundColor: "var(--color-success)", color: "white", opacity: verifying ? 0.5 : 1 }}>
                ✓ Setujui
              </button>
              <button
                onClick={() => { setAction("reject"); setShowNotes(true); }}
                disabled={verifying}
                style={{ flex: 1, padding: "4px 8px", borderRadius: 4, border: "1px solid rgba(220,38,38,0.3)", fontSize: 10, fontWeight: 600, cursor: "pointer", backgroundColor: "white", color: "var(--color-danger)", opacity: verifying ? 0.5 : 1 }}>
                ✕ Tolak
              </button>
            </div>
          ) : (
            <div>
              <textarea
                rows={2}
                placeholder={action === "reject" ? "Alasan penolakan (wajib)..." : "Catatan (opsional)..."}
                value={notes}
                onChange={(e) => setNotes(e.target.value)}
                style={{ width: "100%", padding: "6px 8px", border: "1px solid rgba(14,13,11,0.15)", borderRadius: 4, fontSize: 11, resize: "none", boxSizing: "border-box", fontFamily: "inherit", marginBottom: 6 }} />
              <div style={{ display: "flex", gap: 6 }}>
                <button
                  onClick={() => { setShowNotes(false); setNotes(""); setAction(null); }}
                  disabled={verifying}
                  style={{ flex: 1, padding: "4px 8px", borderRadius: 4, border: "1px solid rgba(14,13,11,0.1)", fontSize: 10, cursor: "pointer", backgroundColor: "white", color: "var(--color-ink-3)" }}>
                  Batal
                </button>
                <button
                  onClick={() => handleVerify(action!)}
                  disabled={verifying || (action === "reject" && !notes.trim())}
                  style={{ flex: 2, padding: "4px 8px", borderRadius: 4, border: "none", fontSize: 10, fontWeight: 600, cursor: "pointer", backgroundColor: action === "approve" ? "var(--color-success)" : "var(--color-danger)", color: "white", display: "flex", alignItems: "center", justifyContent: "center", gap: 4, opacity: (verifying || (action === "reject" && !notes.trim())) ? 0.5 : 1 }}>
                  {verifying
                    ? <Loader2 size={11} style={{ animation: "spin 1s linear infinite" }} />
                    : action === "approve" ? "✓ Konfirmasi Setujui" : "✕ Konfirmasi Tolak"
                  }
                </button>
              </div>
              {action === "reject" && !notes.trim() && (
                <div style={{ fontSize: 10, color: "var(--color-danger)", marginTop: 4 }}>
                  Alasan penolakan wajib diisi
                </div>
              )}
            </div>
          )}
        </div>
      )}

      {/* ── Sprint 8: Version history toggle ── */}
      {hasHistory && (
        <div style={{ marginTop: 8, paddingTop: 8, borderTop: "1px solid rgba(14,13,11,0.06)" }}>
          <button
            onClick={() => setShowHistory(!showHistory)}
            style={{ fontSize: 10, color: "var(--color-ink-3)", background: "none", border: "none", cursor: "pointer", display: "flex", alignItems: "center", gap: 4 }}>
            🕐 {showHistory ? "Sembunyikan" : "Lihat"} riwayat versi ({ev.version_chain.length} versi)
          </button>
          {showHistory && (
            <div style={{ marginTop: 6, display: "flex", flexDirection: "column", gap: 4 }}>
              {ev.version_chain.map((v) => {
                const vMeta = EVIDENCE_VERSION_META[v.verification_status] ?? EVIDENCE_VERSION_META["pending"];
                return (
                  <div key={v.id} style={{
                    display: "flex", alignItems: "center", gap: 8,
                    padding: "4px 8px", borderRadius: 4,
                    backgroundColor: v.is_latest ? vMeta.bg : "rgba(14,13,11,0.03)",
                    opacity: v.is_latest ? 1 : 0.6,
                  }}>
                    <span style={{ fontSize: 10, fontWeight: 700, color: vMeta.color, minWidth: 20 }}>{v.label}</span>
                    <span style={{ fontSize: 10 }}>{vMeta.icon}</span>
                    <span style={{ fontSize: 10, color: "var(--color-ink-3)", flex: 1 }}>
                      {new Date(v.uploaded_at).toLocaleDateString("id-ID")}
                    </span>
                    <span style={{ fontSize: 10, fontWeight: 600, color: vMeta.color }}>{vMeta.label}</span>
                    {v.is_latest && (
                      <span style={{ fontSize: 9, color: "var(--color-ink-3)", fontStyle: "italic" }}>aktif</span>
                    )}
                  </div>
                );
              })}
            </div>
          )}
        </div>
      )}
    </div>
  );
}

// ── Requirement row — Sprint 4: dependency-aware ──────────────
type ReqStatus = "pending" | "in_progress" | "menunggu_verifikasi" | "completed" | "not_applicable";

function RequirementRow({
  req, projectId, onUpdated,
}: {
  req:       RequirementItem;
  projectId: string;
  onUpdated: (intel: IntelligenceSummary) => void;
}) {
  const [saving,          setSaving]          = useState(false);
  const [depError,        setDepError]        = useState<string | null>(null);
  const [notes]                               = useState(req.notes);
  const [showEvidence,    setShowEvidence]    = useState(false);
  const [evidenceList,    setEvidenceList]    = useState<RequirementEvidence[]>([]);
  const [loadingEvidence, setLoadingEvidence] = useState(false);
  const [showUploadModal, setShowUploadModal] = useState(false);
  // Sprint 7: ownership + comments state
  const [showOwnership,  setShowOwnership]  = useState(false);
  const [showComments,   setShowComments]   = useState(false);
  const [comments,       setComments]       = useState<RequirementComment[]>([]);
  const [loadingComments,setLoadingComments] = useState(false);
  const [commentBody,    setCommentBody]    = useState("");
  const [postingComment, setPostingComment] = useState(false);
  const [orgMembers,     setOrgMembers]     = useState<OrgMember[]>([]);
  const [savingAssign,   setSavingAssign]   = useState(false);

  const handleStatusChange = async (newStatus: ReqStatus) => {
    if (newStatus === req.status) return;
    setSaving(true);
    setDepError(null);
    try {
      const intel = await projectsApi.updateRequirement(
        projectId, req.status_id ?? req.id, { status: newStatus, notes }
      );
      onUpdated(intel);
    } catch (e: unknown) {
      // Sprint 4: catch dependency_blocked errors from API
      const err = e as { response?: { data?: { message?: string; error_type?: string } } };
      if (err?.response?.data?.error_type === "dependency_blocked") {
        setDepError(err.response.data.message ?? "Prasyarat belum selesai");
      }
    } finally { setSaving(false); }
  };

  const loadEvidence = async () => {
    if (!req.status_id) return;
    setLoadingEvidence(true);
    try {
      const { results } = await evidenceApi.list(projectId, req.status_id);
      setEvidenceList(results);
    } catch { setEvidenceList([]); }
    finally { setLoadingEvidence(false); }
  };

  const toggleEvidence = () => {
    if (!showEvidence && evidenceList.length === 0) loadEvidence();
    setShowEvidence(!showEvidence);
  };

  const handleEvidenceUploaded = (intel: IntelligenceSummary) => {
    setShowUploadModal(false);
    loadEvidence();
    onUpdated(intel);
  };

  const handleEvidenceVerified = (intel: IntelligenceSummary) => {
    loadEvidence();
    onUpdated(intel);
  };

  const loadComments = async () => {
    if (!req.status_id) return;
    setLoadingComments(true);
    try {
      const { results } = await commentApi.list(projectId, req.status_id);
      setComments(results);
    } catch { setComments([]); }
    finally { setLoadingComments(false); }
  };

  const toggleComments = () => {
    if (!showComments && comments.length === 0) loadComments();
    setShowComments(!showComments);
  };

  const handlePostComment = async () => {
    if (!commentBody.trim() || !req.status_id) return;
    setPostingComment(true);
    try {
      await commentApi.post(projectId, req.status_id, commentBody.trim());
      setCommentBody("");
      await loadComments();
    } catch { /* silent */ }
    finally { setPostingComment(false); }
  };

  const loadOrgMembers = async () => {
    if (orgMembers.length > 0) return;
    try {
      const members = await projectsApi.getOrgMembers(projectId);
      setOrgMembers(members);
    } catch { /* silent */ }
  };

  const handleAssign = async (assignedToId: string | null) => {
    if (!req.status_id) return;
    setSavingAssign(true);
    try {
      const intel = await projectsApi.assignRequirement(
        projectId, req.status_id, { assigned_to: assignedToId }
      );
      onUpdated(intel);
    } catch { /* silent */ }
    finally { setSavingAssign(false); }
  };

  const handleSetDueDate = async (dueDate: string | null) => {
    if (!req.status_id) return;
    setSavingAssign(true);
    try {
      const intel = await projectsApi.assignRequirement(
        projectId, req.status_id, { due_date: dueDate }
      );
      onUpdated(intel);
    } catch { /* silent */ }
    finally { setSavingAssign(false); }
  };

  const statusConfig: Record<ReqStatus, { label: string; color: string; bg: string; icon: React.ReactNode }> = {
    pending:             { label: "Belum Dimulai",      color: "var(--color-ink-3)",   bg: "var(--color-paper-2)",       icon: <Circle size={14} />       },
    in_progress:         { label: "Sedang Diproses",    color: "var(--color-warning)", bg: "var(--color-warning-light)", icon: <Clock size={14} />        },
    menunggu_verifikasi: { label: "Menunggu Verifikasi",color: "var(--color-accent)",  bg: "var(--color-accent-light)",  icon: <Paperclip size={14} />    },
    completed:           { label: "Selesai",            color: "var(--color-success)", bg: "var(--color-success-light)", icon: <CheckCircle2 size={14} /> },
    not_applicable:      { label: "Tidak Berlaku",      color: "var(--color-ink-3)",   bg: "var(--color-paper-2)",       icon: <Circle size={14} />       },
  };

  const current    = statusConfig[req.status as ReqStatus] ?? statusConfig.pending;
  const isCompleted = req.status === "completed";

  // Sprint 4: dependency state drives the entire row appearance
  const isDepBlocked = req.is_dependency_blocked === true;
  const isBlocking   = req.is_mandatory && !["completed", "menunggu_verifikasi"].includes(req.status) && !isDepBlocked;

  // Sprint 4: row background logic
  const rowBg =
    isCompleted   ? "var(--color-success-light)" :
    isDepBlocked  ? "rgba(14,13,11,0.03)"        :  
    isBlocking    ? "rgba(220,38,38,0.04)"       :
                    "var(--color-paper-2)";

  const rowBorder =
    isCompleted   ? "1px solid transparent"              :
    isDepBlocked  ? "1px solid rgba(14,13,11,0.08)"     :  
    isBlocking    ? "1px solid rgba(220,38,38,0.15)"    :
                    "1px solid transparent";

  return (
    <>
      {showUploadModal && req.status_id && (
        <EvidenceUploadModal req={req} projectId={projectId} onUploaded={handleEvidenceUploaded} onClose={() => setShowUploadModal(false)} />
      )}

      <div style={{ padding: "12px 14px", borderRadius: 8, marginBottom: 8, backgroundColor: rowBg, border: rowBorder, transition: "all 0.2s", opacity: isDepBlocked ? 0.7 : 1 }}>
        <div style={{ display: "flex", alignItems: "center", gap: 10 }}>

          {/* Status icon — Sprint 4: lock icon for dep-blocked */}
          <div style={{ color: isDepBlocked ? "var(--color-ink-3)" : current.color, flexShrink: 0 }}>
            {saving
              ? <Loader2 size={14} style={{ animation: "spin 1s linear infinite" }} />
              : isDepBlocked
              ? <Lock size={14} />
              : current.icon
            }
          </div>

          {/* Name + badges */}
          <div style={{ flex: 1, minWidth: 0 }}>
            <div style={{ display: "flex", alignItems: "center", gap: 6, flexWrap: "wrap" }}>
              <span style={{
                fontSize: 13, fontWeight: 500,
                color: isCompleted ? "var(--color-ink-3)" : isDepBlocked ? "var(--color-ink-3)" : "var(--color-ink)",
                textDecoration: isCompleted ? "line-through" : "none",
              }}>
                {req.name}
              </span>

              {/* Sprint 4: dependency blocked badge */}
              {isDepBlocked && (
                <span style={{ fontSize: 10, fontWeight: 600, padding: "1px 6px", borderRadius: 4, backgroundColor: "rgba(14,13,11,0.08)", color: "var(--color-ink-3)", display: "flex", alignItems: "center", gap: 3 }}>
                  <Lock size={9} /> Menunggu prasyarat
                </span>
              )}

              {/* Mandatory badge — only if blocking AND not dep-blocked */}
              {req.is_mandatory && !isCompleted && !isDepBlocked && req.status !== "menunggu_verifikasi" && (
                <span style={{ fontSize: 10, color: "var(--color-danger)", fontWeight: 600 }}>⚡ Wajib</span>
              )}
              {!req.is_mandatory && (
                <span style={{ fontSize: 10, color: "var(--color-ink-3)" }}>opsional</span>
              )}

              {/* Evidence count badge */}
              {req.evidence_count > 0 && (
                <button onClick={toggleEvidence} style={{ fontSize: 10, fontWeight: 600, padding: "1px 6px", borderRadius: 999, backgroundColor: "var(--color-accent-light)", color: "var(--color-accent)", border: "none", cursor: "pointer" }}>
                  📎 {req.evidence_count} bukti
                </button>
              )}
              {req.has_pending_evidence && (
                <span style={{ fontSize: 10, fontWeight: 600, color: "var(--color-warning)" }}>⏳ Menunggu review</span>
              )}

              {/* Sprint 7: assigned_to badge */}
              {req.assigned_to_name && (
                <span style={{ fontSize: 10, fontWeight: 600, padding: "1px 6px", borderRadius: 999, backgroundColor: "var(--color-info-light)", color: "var(--color-info)", display: "flex", alignItems: "center", gap: 3 }}>
                  👤 {req.assigned_to_name}
                </span>
              )}

              {/* Sprint 7: due_date badge */}
              {req.due_date && !isCompleted && (
                <span style={{
                  fontSize: 10, fontWeight: 600, padding: "1px 6px", borderRadius: 999,
                  backgroundColor: req.is_overdue ? "var(--color-danger-light)" : "var(--color-paper-2)",
                  color: req.is_overdue ? "var(--color-danger)" : "var(--color-ink-3)",
                  display: "flex", alignItems: "center", gap: 3,
                }}>
                  📅 {req.is_overdue ? `Terlambat ${Math.abs(req.days_until_due ?? 0)} hari` : `${req.days_until_due} hari lagi`}
                </span>
              )}

              {/* Sprint 7: comment count badge */}
              {req.comment_count > 0 && (
                <button onClick={toggleComments} style={{ fontSize: 10, fontWeight: 600, padding: "1px 6px", borderRadius: 999, backgroundColor: "rgba(14,13,11,0.06)", color: "var(--color-ink-3)", border: "none", cursor: "pointer" }}>
                  💬 {req.comment_count}
                </button>
              )}
            </div>

            {req.description && !isDepBlocked && (
              <div style={{ fontSize: 11, color: "var(--color-ink-3)", marginTop: 2 }}>{req.description}</div>
            )}

            {/* Sprint 4: show prerequisite chain for blocked rows */}
            {isDepBlocked && req.unmet_prerequisites && req.unmet_prerequisites.length > 0 && (
              <div style={{ fontSize: 11, color: "var(--color-ink-3)", marginTop: 4, display: "flex", alignItems: "center", gap: 4 }}>
                <Lock size={10} />
                Selesaikan dulu:{" "}
                <span style={{ fontWeight: 600, color: "var(--color-ink)" }}>
                  {req.unmet_prerequisites.join(" → ")}
                </span>
              </div>
            )}

            {req.completed_at && (
              <div style={{ fontSize: 10, color: "var(--color-success)", marginTop: 2 }}>
                ✓ Selesai {new Date(req.completed_at).toLocaleDateString("id-ID")}
              </div>
            )}
          </div>

          {/* Action buttons — Sprint 4: hidden when dep-blocked */}
          <div style={{ display: "flex", gap: 4, flexShrink: 0, flexWrap: "wrap", justifyContent: "flex-end" }}>
            {isCompleted ? (
              <button onClick={() => handleStatusChange("pending")} disabled={saving}
                style={{ padding: "4px 8px", borderRadius: 4, border: "1px solid rgba(14,13,11,0.1)", fontSize: 10, cursor: "pointer", backgroundColor: "white", color: "var(--color-ink-3)", opacity: saving ? 0.5 : 1 }}>
                Batalkan
              </button>
            ) : req.status === "menunggu_verifikasi" ? (
              <button onClick={toggleEvidence} style={{ padding: "4px 8px", borderRadius: 4, border: "1px solid rgba(14,13,11,0.1)", fontSize: 10, fontWeight: 600, cursor: "pointer", backgroundColor: "var(--color-accent-light)", color: "var(--color-accent)" }}>
                {showEvidence ? "Tutup" : "Lihat Bukti"}
              </button>
            ) : isDepBlocked ? (
              // Sprint 4: dep-blocked rows show ONLY the prerequisite info, no action buttons
              <span style={{ fontSize: 10, color: "var(--color-ink-3)", fontStyle: "italic", padding: "4px 8px" }}>
                🔒 Terkunci
              </span>
            ) : (
              <>
                {req.status !== "in_progress" && (
                  <button onClick={() => handleStatusChange("in_progress")} disabled={saving}
                    style={{ padding: "4px 8px", borderRadius: 4, fontSize: 10, fontWeight: 600, cursor: "pointer", backgroundColor: "white", color: "var(--color-warning)", border: "1px solid rgba(14,13,11,0.1)", opacity: saving ? 0.5 : 1 }}>
                    Diproses
                  </button>
                )}
                {req.status_id && (
                  <button onClick={() => setShowUploadModal(true)} disabled={saving}
                    style={{ padding: "4px 8px", borderRadius: 4, fontSize: 10, fontWeight: 600, cursor: "pointer", backgroundColor: "var(--color-accent-light)", color: "var(--color-accent)", border: "1px solid rgba(14,13,11,0.08)", display: "flex", alignItems: "center", gap: 3 }}>
                    <Paperclip size={10} /> Bukti
                  </button>
                )}
                <button onClick={() => handleStatusChange("completed")} disabled={saving}
                  style={{ padding: "4px 10px", borderRadius: 4, fontSize: 10, fontWeight: 600, cursor: "pointer", backgroundColor: "var(--color-success)", color: "white", opacity: saving ? 0.5 : 1 }}>
                  Selesai ✓
                </button>
              </>
            )}
          </div>
        </div>

        {/* Sprint 4: dependency error message */}
        {depError && (
          <div style={{ marginTop: 8, padding: "6px 10px", backgroundColor: "var(--color-warning-light)", borderRadius: 6, fontSize: 11, color: "var(--color-warning)", display: "flex", alignItems: "center", gap: 6 }}>
            <Lock size={11} /> {depError}
            <button onClick={() => setDepError(null)} style={{ marginLeft: "auto", background: "none", border: "none", cursor: "pointer", color: "var(--color-warning)", fontSize: 12 }}>✕</button>
          </div>
        )}

        {/* Evidence list panel */}
        {showEvidence && (
          <div style={{ marginTop: 10, paddingTop: 10, borderTop: "1px solid rgba(14,13,11,0.06)" }}>
            <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between", marginBottom: 8 }}>
              <span style={{ fontSize: 10, fontWeight: 700, color: "var(--color-ink-3)", textTransform: "uppercase", letterSpacing: "0.06em" }}>
                Bukti ({evidenceList.length})
              </span>
              {req.status_id && !isCompleted && !isDepBlocked && (
                <button onClick={() => setShowUploadModal(true)} style={{ fontSize: 10, fontWeight: 600, color: "var(--color-accent)", background: "none", border: "none", cursor: "pointer", display: "flex", alignItems: "center", gap: 3 }}>
                  <Paperclip size={10} /> + Tambah Bukti
                </button>
              )}
            </div>
            {loadingEvidence ? (
              <div style={{ display: "flex", justifyContent: "center", padding: 12 }}>
                <Loader2 size={14} style={{ animation: "spin 1s linear infinite", color: "var(--color-ink-3)" }} />
              </div>
            ) : evidenceList.length === 0 ? (
              <div style={{ fontSize: 11, color: "var(--color-ink-3)", fontStyle: "italic", textAlign: "center", padding: "8px 0" }}>
                Belum ada bukti diunggah
              </div>
            ) : (
              evidenceList.map((ev) => (
                <EvidenceItem key={ev.id} ev={ev} projectId={projectId}
                  reqStatusId={req.status_id ?? req.id}
                  onVerified={handleEvidenceVerified}
                  onResubmit={() => setShowUploadModal(true)}
                />
              ))
            )}
          </div>
        )}

        {/* Sprint 7: Ownership panel */}
        {!isDepBlocked && !isCompleted && (
          <div style={{ marginTop: 8, paddingTop: 8, borderTop: "1px solid rgba(14,13,11,0.06)" }}>
            <div style={{ display: "flex", alignItems: "center", gap: 8, flexWrap: "wrap" }}>
              {/* Assign button */}
              <button
                onClick={() => { setShowOwnership(!showOwnership); loadOrgMembers(); }}
                style={{ fontSize: 10, fontWeight: 600, padding: "3px 8px", borderRadius: 4, border: "1px solid rgba(14,13,11,0.1)", backgroundColor: "white", color: "var(--color-ink-3)", cursor: "pointer", display: "flex", alignItems: "center", gap: 3 }}>
                👤 {req.assigned_to_name ? req.assigned_to_name : "Tugaskan"}
              </button>

              {/* Due date button */}
              <button
                onClick={() => setShowOwnership(!showOwnership)}
                style={{ fontSize: 10, fontWeight: 600, padding: "3px 8px", borderRadius: 4, border: "1px solid rgba(14,13,11,0.1)", backgroundColor: "white", color: req.is_overdue ? "var(--color-danger)" : "var(--color-ink-3)", cursor: "pointer", display: "flex", alignItems: "center", gap: 3 }}>
                📅 {req.due_date ? new Date(req.due_date).toLocaleDateString("id-ID", { day: "numeric", month: "short" }) : "Set tenggat"}
              </button>

              {/* Comment toggle */}
              {req.status_id && (
                <button onClick={toggleComments}
                  style={{ fontSize: 10, fontWeight: 600, padding: "3px 8px", borderRadius: 4, border: "1px solid rgba(14,13,11,0.1)", backgroundColor: "white", color: "var(--color-ink-3)", cursor: "pointer", display: "flex", alignItems: "center", gap: 3 }}>
                  💬 {req.comment_count > 0 ? `${req.comment_count} komentar` : "Komentar"}
                </button>
              )}
            </div>

            {/* Ownership edit panel */}
            {showOwnership && (
              <div style={{ marginTop: 8, padding: "10px 12px", backgroundColor: "var(--color-paper-2)", borderRadius: 8, display: "flex", flexDirection: "column", gap: 8 }}>
                {/* Assignee dropdown */}
                <div>
                  <div style={{ fontSize: 10, fontWeight: 700, color: "var(--color-ink-3)", marginBottom: 4, textTransform: "uppercase", letterSpacing: "0.05em" }}>Ditugaskan ke</div>
                  <select
                    value={req.assigned_to_id ?? ""}
                    onChange={(e) => handleAssign(e.target.value || null)}
                    disabled={savingAssign}
                    style={{ width: "100%", padding: "6px 8px", border: "1px solid rgba(14,13,11,0.12)", borderRadius: 6, fontSize: 12, backgroundColor: "white", color: "var(--color-ink)" }}>
                    <option value="">— Belum ditugaskan —</option>
                    {orgMembers.map((m) => (
                      <option key={m.id} value={m.id}>{m.full_name}</option>
                    ))}
                  </select>
                </div>
                {/* Due date picker */}
                <div>
                  <div style={{ fontSize: 10, fontWeight: 700, color: "var(--color-ink-3)", marginBottom: 4, textTransform: "uppercase", letterSpacing: "0.05em" }}>Tenggat Waktu</div>
                  <div style={{ display: "flex", gap: 6 }}>
                    <input
                      type="date"
                      value={req.due_date ?? ""}
                      onChange={(e) => handleSetDueDate(e.target.value || null)}
                      disabled={savingAssign}
                      style={{ flex: 1, padding: "6px 8px", border: "1px solid rgba(14,13,11,0.12)", borderRadius: 6, fontSize: 12, backgroundColor: "white", color: "var(--color-ink)" }} />
                    {req.due_date && (
                      <button onClick={() => handleSetDueDate(null)} disabled={savingAssign}
                        style={{ padding: "4px 8px", borderRadius: 6, border: "1px solid rgba(14,13,11,0.1)", fontSize: 11, cursor: "pointer", backgroundColor: "white", color: "var(--color-danger)" }}>
                        ✕
                      </button>
                    )}
                  </div>
                </div>
                {savingAssign && <div style={{ fontSize: 10, color: "var(--color-ink-3)", textAlign: "center" }}>Menyimpan...</div>}
              </div>
            )}
          </div>
        )}

        {/* Sprint 7: Comments panel */}
        {showComments && req.status_id && (
          <div style={{ marginTop: 10, paddingTop: 10, borderTop: "1px solid rgba(14,13,11,0.06)" }}>
            <div style={{ fontSize: 10, fontWeight: 700, color: "var(--color-ink-3)", textTransform: "uppercase", letterSpacing: "0.06em", marginBottom: 8 }}>
              Komentar ({comments.length})
            </div>
            {loadingComments ? (
              <div style={{ textAlign: "center", padding: 8 }}>
                <Loader2 size={13} style={{ animation: "spin 1s linear infinite", color: "var(--color-ink-3)" }} />
              </div>
            ) : (
              <>
                {comments.length === 0 && (
                  <div style={{ fontSize: 11, color: "var(--color-ink-3)", fontStyle: "italic", marginBottom: 8 }}>Belum ada komentar</div>
                )}
                {comments.map((c) => (
                  <div key={c.id} style={{ marginBottom: 8, padding: "8px 10px", backgroundColor: "var(--color-paper-2)", borderRadius: 6 }}>
                    <div style={{ display: "flex", alignItems: "center", gap: 6, marginBottom: 3 }}>
                      <span style={{ fontSize: 11, fontWeight: 600, color: "var(--color-ink)" }}>{c.author_name}</span>
                      <span style={{ fontSize: 10, color: "var(--color-ink-3)" }}>
                        {new Date(c.created_at).toLocaleDateString("id-ID", { day: "numeric", month: "short", hour: "2-digit", minute: "2-digit" })}
                      </span>
                    </div>
                    <div style={{ fontSize: 12, color: "var(--color-ink)", lineHeight: 1.4 }}>{c.body}</div>
                  </div>
                ))}
                {/* Post comment */}
                <div style={{ display: "flex", gap: 6, marginTop: 6 }}>
                  <input
                    type="text"
                    placeholder="Tulis komentar..."
                    value={commentBody}
                    onChange={(e) => setCommentBody(e.target.value)}
                    onKeyDown={(e) => { if (e.key === "Enter" && !e.shiftKey) { e.preventDefault(); handlePostComment(); }}}
                    disabled={postingComment}
                    style={{ flex: 1, padding: "6px 10px", border: "1px solid rgba(14,13,11,0.12)", borderRadius: 6, fontSize: 12, outline: "none" }} />
                  <button onClick={handlePostComment} disabled={postingComment || !commentBody.trim()}
                    style={{ padding: "6px 12px", borderRadius: 6, border: "none", fontSize: 11, fontWeight: 600, cursor: "pointer", backgroundColor: "var(--color-accent)", color: "white", opacity: (!commentBody.trim() || postingComment) ? 0.5 : 1 }}>
                    {postingComment ? "..." : "Kirim"}
                  </button>
                </div>
              </>
            )}
          </div>
        )}

      </div>
    </>
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
  return <span style={{ fontSize: 11, fontWeight: 600, padding: "3px 10px", borderRadius: 999, color: s.color, backgroundColor: s.bg }}>{s.label}</span>;
}

// ── Sprint 1: Alerts panel ────────────────────────────────────
function AlertsPanel({ alerts }: { alerts: IntelligenceSummary["alerts"] }) {
  if (!alerts || alerts.length === 0) {
    return (
      <div style={{ textAlign: "center", padding: "16px 0", color: "var(--color-ink-3)" }}>
        <CheckCircle2 size={22} style={{ margin: "0 auto 6px", display: "block", color: "var(--color-success)", opacity: 0.6 }} />
        <div style={{ fontSize: 12 }}>Tidak ada alert aktif</div>
      </div>
    );
  }
  return (
    <div style={{ display: "flex", flexDirection: "column", gap: 8 }}>
      {alerts.map((alert, i) => {
        const meta = ALERT_META[alert.level as keyof typeof ALERT_META] ?? ALERT_META.info;
        return (
          <div key={i} style={{ padding: "10px 12px", backgroundColor: meta.bg, border: `1px solid ${meta.border}`, borderRadius: 8 }}>
            <div style={{ display: "flex", alignItems: "center", gap: 6, marginBottom: 4 }}>
              <div style={{ width: 6, height: 6, borderRadius: "50%", backgroundColor: meta.color, flexShrink: 0 }} />
              <span style={{ fontSize: 10, fontWeight: 700, color: meta.color, textTransform: "uppercase", letterSpacing: "0.05em" }}>{alert.level}</span>
            </div>
            <div style={{ fontSize: 12, color: "var(--color-ink)", lineHeight: 1.4, marginBottom: 4 }}>{alert.message}</div>
            <div style={{ fontSize: 11, color: "var(--color-ink-3)" }}>→ {alert.action}</div>
          </div>
        );
      })}
    </div>
  );
}

// ── Sprint 1: Readiness dimensions ───────────────────────────
function ReadinessDimensions({ dims }: { dims: IntelligenceSummary["readiness_dimensions"] }) {
  if (!dims) return null;
  const items = [
    { key: "inventory",   label: "Inventori Unit"  },
    { key: "compliance",  label: "Perizinan"        },
    { key: "site_plan",   label: "Site Plan"        },
    { key: "sales_setup", label: "Setup Penjualan"  },
  ] as const;
  return (
    <div style={{ display: "flex", flexDirection: "column", gap: 8 }}>
      {items.map(({ key, label }) => {
        const value = dims[key] ?? 100;
        const color = value >= 80 ? "var(--color-success)" : value >= 50 ? "var(--color-warning)" : "var(--color-danger)";
        return (
          <div key={key}>
            <div style={{ display: "flex", justifyContent: "space-between", marginBottom: 3 }}>
              <span style={{ fontSize: 11, color: "var(--color-ink-3)" }}>{label}</span>
              <span style={{ fontSize: 11, fontWeight: 700, color }}>{value}%</span>
            </div>
            <div style={{ height: 5, backgroundColor: "rgba(14,13,11,0.08)", borderRadius: 3, overflow: "hidden" }}>
              <div style={{ width: `${value}%`, height: "100%", backgroundColor: color, borderRadius: 3, transition: "width 0.4s" }} />
            </div>
          </div>
        );
      })}
    </div>
  );
}

// ── Sprint 5: Readiness breakdown panel ──────────────────────
function ReadinessBreakdownPanel({
  breakdown,
}: {
  breakdown: IntelligenceSummary["readiness_breakdown"];
}) {
  const [expanded, setExpanded] = useState(false);
  if (!breakdown) return null;

  const labelMeta = READINESS_LABEL_META[breakdown.label] ?? {
    color: "var(--color-ink-3)",
    bg:    "var(--color-paper-2)",
  };

  return (
    <div style={{ marginTop: 14, paddingTop: 14, borderTop: "1px solid rgba(14,13,11,0.06)" }}>
      {/* Header row */}
      <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between", marginBottom: 10 }}>
        <div style={{ display: "flex", alignItems: "center", gap: 8 }}>
          <span style={{ fontSize: 11, fontWeight: 700, color: "var(--color-ink-3)", textTransform: "uppercase", letterSpacing: "0.06em" }}>
            Bagaimana kalkulasinya?
          </span>
          <span style={{ fontSize: 11, fontWeight: 600, padding: "2px 8px", borderRadius: 999, color: labelMeta.color, backgroundColor: labelMeta.bg }}>
            {breakdown.label}
          </span>
        </div>
        <button
          onClick={() => setExpanded(!expanded)}
          style={{ fontSize: 11, color: "var(--color-accent)", background: "none", border: "none", cursor: "pointer", fontWeight: 600 }}>
          {expanded ? "Sembunyikan ↑" : "Lihat detail ↓"}
        </button>
      </div>

      {/* Formula bar — always visible */}
      <div style={{ padding: "8px 12px", backgroundColor: "var(--color-paper-2)", borderRadius: 8, marginBottom: expanded ? 10 : 0 }}>
        <div style={{ fontSize: 11, color: "var(--color-ink-3)", marginBottom: 4 }}>Formula</div>
        <div style={{ fontSize: 12, fontWeight: 600, color: "var(--color-ink)", fontFamily: "monospace" }}>
          {breakdown.formula}
        </div>
        {/* Mini progress bar */}
        <div style={{ marginTop: 8, height: 6, backgroundColor: "rgba(14,13,11,0.08)", borderRadius: 3, overflow: "hidden" }}>
          <div style={{
            width: `${breakdown.score}%`, height: "100%", borderRadius: 3,
            backgroundColor: breakdown.score >= 80 ? "var(--color-success)" : breakdown.score >= 60 ? "var(--color-info)" : breakdown.score >= 30 ? "var(--color-warning)" : "var(--color-danger)",
            transition: "width 0.5s",
          }} />
        </div>
        <div style={{ display: "flex", justifyContent: "space-between", marginTop: 4 }}>
          <span style={{ fontSize: 10, color: "var(--color-ink-3)" }}>
            Bobot selesai: {breakdown.completed_weight} / {breakdown.total_weight}
          </span>
          <span style={{ fontSize: 10, fontWeight: 700, color: labelMeta.color }}>
            {breakdown.score}%
          </span>
        </div>
      </div>

      {/* Expanded: per-requirement breakdown */}
      {expanded && (
        <div style={{ display: "flex", flexDirection: "column", gap: 6 }}>
          {breakdown.items.map((item) => {
            const isDone    = item.is_completed;
            const isBlocked = item.is_dependency_blocked;
            const barColor  = isDone ? "var(--color-success)" : isBlocked ? "rgba(14,13,11,0.12)" : "var(--color-danger)";
            const icon      = isDone ? "✅" : isBlocked ? "🔒" : "○";
            return (
              <div key={item.id} style={{
                padding: "8px 10px", borderRadius: 6,
                backgroundColor: isDone ? "var(--color-success-light)" : isBlocked ? "rgba(14,13,11,0.03)" : "rgba(220,38,38,0.04)",
                border: `1px solid ${isDone ? "rgba(34,197,94,0.15)" : isBlocked ? "rgba(14,13,11,0.06)" : "rgba(220,38,38,0.1)"}`,
              }}>
                <div style={{ display: "flex", alignItems: "center", gap: 8, marginBottom: 5 }}>
                  <span style={{ fontSize: 12 }}>{icon}</span>
                  <span style={{ fontSize: 12, fontWeight: 500, color: isDone ? "var(--color-ink-3)" : "var(--color-ink)", flex: 1, textDecoration: isDone ? "line-through" : "none" }}>
                    {item.name}
                  </span>
                  <span style={{ fontSize: 11, fontWeight: 700, color: isDone ? "var(--color-success)" : "var(--color-ink-3)" }}>
                    +{item.contribution}%
                  </span>
                </div>
                {/* Weight bar */}
                <div style={{ display: "flex", alignItems: "center", gap: 8 }}>
                  <div style={{ flex: 1, height: 4, backgroundColor: "rgba(14,13,11,0.08)", borderRadius: 2, overflow: "hidden" }}>
                    <div style={{ width: `${item.weight_pct}%`, height: "100%", borderRadius: 2, backgroundColor: barColor }} />
                  </div>
                  <span style={{ fontSize: 10, color: "var(--color-ink-3)", minWidth: 60, textAlign: "right" }}>
                    bobot {item.weight_pct}%
                  </span>
                </div>
              </div>
            );
          })}
          <div style={{ fontSize: 10, color: "var(--color-ink-3)", textAlign: "center", marginTop: 4, fontStyle: "italic" }}>
            Bobot dapat dikonfigurasi oleh admin
          </div>
        </div>
      )}
    </div>
  );
}

// ── Sprint 6: Risk explanation panel ─────────────────────────
function RiskExplanationPanel({
  intel,
}: {
  intel: IntelligenceSummary;
}) {
  const [expanded, setExpanded] = useState(false);
  if (!intel.risk_factors || intel.risk_factors.length === 0) return null;

  const scoreMeta = getRiskScoreMeta(intel.risk_score);

  return (
    <div style={{ marginTop: 14, paddingTop: 14, borderTop: "1px solid rgba(14,13,11,0.06)" }}>
      {/* Header */}
      <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between", marginBottom: 10 }}>
        <div style={{ display: "flex", alignItems: "center", gap: 8 }}>
          <span style={{ fontSize: 11, fontWeight: 700, color: "var(--color-ink-3)", textTransform: "uppercase", letterSpacing: "0.06em" }}>
            Mengapa risiko ini?
          </span>
          <span style={{ fontSize: 12, fontWeight: 800, padding: "2px 10px", borderRadius: 999, color: scoreMeta.color, backgroundColor: scoreMeta.bg }}>
            {intel.risk_score} / 100
          </span>
          {intel.risk_since && (
            <span style={{ fontSize: 10, color: "var(--color-ink-3)" }}>
              sejak {new Date(intel.risk_since).toLocaleDateString("id-ID", { day: "numeric", month: "short", year: "numeric" })}
            </span>
          )}
        </div>
        <button
          onClick={() => setExpanded(!expanded)}
          style={{ fontSize: 11, color: "var(--color-accent)", background: "none", border: "none", cursor: "pointer", fontWeight: 600 }}>
          {expanded ? "Sembunyikan ↑" : "Lihat detail ↓"}
        </button>
      </div>

      {/* Score bar — always visible */}
      <div style={{ padding: "8px 12px", backgroundColor: "var(--color-paper-2)", borderRadius: 8, marginBottom: expanded ? 10 : 0 }}>
        <div style={{ display: "flex", justifyContent: "space-between", marginBottom: 4 }}>
          <span style={{ fontSize: 11, color: "var(--color-ink-3)" }}>Risk Score</span>
          <span style={{ fontSize: 11, fontWeight: 700, color: scoreMeta.color }}>{scoreMeta.label}</span>
        </div>
        <div style={{ height: 6, backgroundColor: "rgba(14,13,11,0.08)", borderRadius: 3, overflow: "hidden" }}>
          <div style={{
            width: `${intel.risk_score}%`, height: "100%", borderRadius: 3,
            backgroundColor: scoreMeta.color, transition: "width 0.5s",
          }} />
        </div>
        <div style={{ display: "flex", justifyContent: "space-between", marginTop: 4 }}>
          <span style={{ fontSize: 10, color: "var(--color-ink-3)" }}>
            {intel.risk_factors.length} faktor aktif
          </span>
          <span style={{ fontSize: 10, fontWeight: 700, color: scoreMeta.color }}>
            {intel.risk_score} pts
          </span>
        </div>
      </div>

      {/* Expanded: per-factor breakdown */}
      {expanded && (
        <div style={{ display: "flex", flexDirection: "column", gap: 8 }}>
          {intel.risk_factors.map((factor) => {
            const impactMeta = RISK_FACTOR_IMPACT_META[factor.impact] ?? RISK_FACTOR_IMPACT_META["Sedang"];
            return (
              <div key={factor.key} style={{
                padding: "10px 12px", borderRadius: 8,
                backgroundColor: impactMeta.bg,
                border: `1px solid ${impactMeta.color}22`,
              }}>
                <div style={{ display: "flex", alignItems: "center", gap: 8, marginBottom: 5 }}>
                  <span style={{ fontSize: 10, fontWeight: 700, padding: "1px 7px", borderRadius: 999, color: impactMeta.color, backgroundColor: "white", flexShrink: 0 }}>
                    {factor.impact}
                  </span>
                  <span style={{ fontSize: 12, fontWeight: 600, color: "var(--color-ink)", flex: 1 }}>
                    {factor.name}
                  </span>
                  <span style={{ fontSize: 11, fontWeight: 700, color: impactMeta.color, flexShrink: 0 }}>
                    +{factor.points}pts
                  </span>
                </div>
                <div style={{ fontSize: 11, color: "var(--color-ink-3)", marginBottom: 5, lineHeight: 1.4 }}>
                  {factor.description}
                </div>
                {/* Points bar */}
                <div style={{ display: "flex", alignItems: "center", gap: 8, marginBottom: 6 }}>
                  <div style={{ flex: 1, height: 4, backgroundColor: "rgba(14,13,11,0.08)", borderRadius: 2, overflow: "hidden" }}>
                    <div style={{ width: `${(factor.points / factor.max_points) * 100}%`, height: "100%", borderRadius: 2, backgroundColor: impactMeta.color }} />
                  </div>
                  <span style={{ fontSize: 10, color: "var(--color-ink-3)", minWidth: 50, textAlign: "right" }}>
                    {factor.points}/{factor.max_points} pts
                  </span>
                </div>
                <div style={{ fontSize: 11, color: impactMeta.color, fontWeight: 500 }}>
                  → {factor.action}
                </div>
              </div>
            );
          })}
          <div style={{ fontSize: 10, color: "var(--color-ink-3)", textAlign: "center", marginTop: 4, fontStyle: "italic" }}>
            Skor risiko dihitung otomatis dari faktor-faktor di atas
          </div>
        </div>
      )}
    </div>
  );
}


// ── Sprint 1: Parallel stage toggles ─────────────────────────
function ParallelStageToggles({ project, onUpdated }: { project: Project; onUpdated: (p: Project) => void }) {
  const [loading5A, setLoading5A] = useState(false);
  const [loading5B, setLoading5B] = useState(false);
  const toggle5A = async () => { setLoading5A(true); try { const u = await projectsApi.toggleSelling(project.id, !project.is_selling); onUpdated(u); } catch (e) { console.error(e); } finally { setLoading5A(false); } };
  const toggle5B = async () => { setLoading5B(true); try { const u = await projectsApi.toggleConstructing(project.id, !project.is_constructing); onUpdated(u); } catch (e) { console.error(e); } finally { setLoading5B(false); } };
  return (
    <div style={{ display: "flex", gap: 8 }}>
      <button onClick={toggle5A} disabled={loading5A || !project.parallel_stages?.can_sell_now}
        style={{ flex: 1, padding: "8px 10px", borderRadius: 6, border: "1px solid rgba(14,13,11,0.12)", fontSize: 11, fontWeight: 600, cursor: "pointer", transition: "all 0.15s", backgroundColor: project.is_selling ? "var(--color-success-light)" : "white", color: project.is_selling ? "var(--color-success)" : "var(--color-ink-3)", opacity: !project.parallel_stages?.can_sell_now ? 0.4 : 1 }}>
        {loading5A ? <Loader2 size={12} style={{ animation: "spin 1s linear infinite", display: "inline" }} /> : project.is_selling ? "✓ 5A Penjualan" : "5A Mulai Jual"}
      </button>
      <button onClick={toggle5B} disabled={loading5B}
        style={{ flex: 1, padding: "8px 10px", borderRadius: 6, border: "1px solid rgba(14,13,11,0.12)", fontSize: 11, fontWeight: 600, cursor: "pointer", transition: "all 0.15s", backgroundColor: project.is_constructing ? "var(--color-accent-light)" : "white", color: project.is_constructing ? "var(--color-accent)" : "var(--color-ink-3)" }}>
        {loading5B ? <Loader2 size={12} style={{ animation: "spin 1s linear infinite", display: "inline" }} /> : project.is_constructing ? "✓ 5B Konstruksi" : "5B Mulai Bangun"}
      </button>
    </div>
  );
}

// ── Sprint 17: Smart polling hook ─────────────────────────────
// Polls /pulse/?since=<timestamp> every 15 seconds.
// Silent on failure — polling is best-effort, never blocks the UI.
// Returns cleanup function to stop polling on unmount.
function useProjectPulse(
  projectId:  string,
  enabled:    boolean,
  onUpdate:   (data: PulseResponse) => void,
) {
  const sinceRef    = useRef<string>(new Date().toISOString());
  const onUpdateRef = useRef(onUpdate);
  onUpdateRef.current = onUpdate;   // always call latest callback

  useEffect(() => {
    if (!enabled || !projectId) return;

    const poll = async () => {
      try {
        const data = await projectsApi.getPulse(projectId, sinceRef.current);
        if (data.has_updates) {
          sinceRef.current = data.checked_at;
          onUpdateRef.current(data);
        }
      } catch {
        // Silent failure — polling continues regardless
      }
    };

    const interval = setInterval(poll, 15_000);   // 15-second cadence
    return () => clearInterval(interval);
  }, [projectId, enabled]);
}

function ReadinessTrendPanel({
  projectId,
  currentScore,
  inlineData,
  liveScore,         // Sprint 17: updated score from pulse
  todayDelta,        // Sprint 17: +X% today badge
}: {
  projectId:    string;
  currentScore: number;
  inlineData:   ReadinessHistoryPoint[];
  liveScore?:   number;
  todayDelta?:  number | null;
}) {
  const [history,      setHistory]      = useState<ReadinessHistoryPoint[]>(inlineData);
  const [loading,      setLoading]      = useState(inlineData.length < 2);
  const [displayScore, setDisplayScore] = useState(liveScore ?? currentScore);
  const [isGlowing,    setIsGlowing]    = useState(false);

  // Sprint 17: animate when liveScore changes
  useEffect(() => {
    const target = liveScore ?? currentScore;
    if (target === displayScore) return;

    const from  = displayScore;
    const diff  = target - from;
    const steps = 20;
    let step    = 0;

    setIsGlowing(true);
    const timer = setInterval(() => {
      step++;
      setDisplayScore(Math.round(from + (diff * step / steps)));
      if (step >= steps) {
        clearInterval(timer);
        setDisplayScore(target);
        setTimeout(() => setIsGlowing(false), 600);
      }
    }, 50);   // 1 second total animation

    return () => clearInterval(timer);
  }, [liveScore, currentScore]);

  useEffect(() => {
    if (inlineData.length >= 2) { setHistory(inlineData); return; }
    projectsApi.getReadinessHistory(projectId, 30)
      .then((d) => setHistory(d.results))
      .catch(() => {})
      .finally(() => setLoading(false));
  }, [projectId, inlineData]);

  const scoreColor =
    displayScore >= 80 ? "var(--color-success)" :
    displayScore >= 50 ? "var(--color-warning)" :
                         "var(--color-danger)";

  const fmt = (iso: string) => {
    const d = new Date(iso);
    return d.toLocaleDateString("id-ID", { day: "numeric", month: "short" });
  };

  return (
    <div className="card" style={{ marginBottom: 16 }}>
      <div style={{
        display: "flex", alignItems: "center",
        justifyContent: "space-between", marginBottom: 16,
      }}>
        <div>
          <div style={{ fontSize: 13, fontWeight: 600, color: "var(--color-ink)" }}>
            Tren Kesiapan
          </div>
          <div style={{ fontSize: 11, color: "var(--color-ink-3)", marginTop: 2 }}>
            30 hari terakhir
          </div>
        </div>
        <div style={{ textAlign: "right" }}>
          {/* Sprint 17: animated score with glow */}
          <div style={{
            fontSize: 24, fontWeight: 800, color: scoreColor,
            transition: "color 0.3s",
            textShadow: isGlowing ? `0 0 12px ${scoreColor}66` : "none",
          }}>
            {displayScore}%
          </div>
          <div style={{ display: "flex", alignItems: "center", gap: 6, justifyContent: "flex-end" }}>
            <div style={{ fontSize: 10, color: "var(--color-ink-3)" }}>saat ini</div>
            {/* Sprint 17: +X% today badge */}
            {todayDelta != null && todayDelta !== 0 && (
              <span style={{
                fontSize: 9, fontWeight: 700,
                padding: "1px 6px", borderRadius: 999,
                backgroundColor: todayDelta > 0
                  ? "var(--color-success-light)"
                  : "var(--color-danger-light)",
                color: todayDelta > 0
                  ? "var(--color-success)"
                  : "var(--color-danger)",
              }}>
                {todayDelta > 0 ? "+" : ""}{todayDelta}% hari ini
              </span>
            )}
          </div>
        </div>
      </div>

      {loading ? (
        <div style={{ height: 120, display: "flex", alignItems: "center", justifyContent: "center", color: "var(--color-ink-3)", fontSize: 12 }}>
          Memuat data tren...
        </div>
      ) : history.length < 2 ? (
        <div style={{ height: 120, display: "flex", alignItems: "center", justifyContent: "center", flexDirection: "column", gap: 4 }}>
          <div style={{ fontSize: 22, opacity: 0.3 }}>📈</div>
          <div style={{ fontSize: 12, color: "var(--color-ink-3)" }}>
            Data tren tersedia setelah beberapa hari aktivitas
          </div>
        </div>
      ) : (
        <ResponsiveContainer width="100%" height={120}>
          <LineChart data={history} margin={{ top: 4, right: 4, bottom: 0, left: -20 }}>
            <XAxis
              dataKey="date"
              tickFormatter={fmt}
              tick={{ fontSize: 10, fill: "var(--color-ink-3)" }}
              axisLine={false} tickLine={false}
              interval="preserveStartEnd"
            />
            <YAxis
              domain={[0, 100]}
              tick={{ fontSize: 10, fill: "var(--color-ink-3)" }}
              axisLine={false} tickLine={false}
            />
            <Tooltip
              formatter={(value) => [`${value ?? 0}%`, "Kesiapan"]}
              labelFormatter={(label) => fmt(String(label ?? ""))}
              contentStyle={{
                fontSize: 11,
                border: "1px solid rgba(14,13,11,0.1)",
                borderRadius: 6,
                boxShadow: "0 4px 12px rgba(14,13,11,0.08)",
              }}
            />
            <ReferenceLine y={80} stroke="var(--color-success)" strokeDasharray="3 3" strokeWidth={1} />
            <Line
              type="monotone" dataKey="score"
              stroke={scoreColor} strokeWidth={2.5}
              dot={false} activeDot={{ r: 4, fill: scoreColor }}
            />
          </LineChart>
        </ResponsiveContainer>
      )}
    </div>
  );
}

// ── Sprint 10: Key Progress Card ──────────────────────────────
function KeyProgressCard({ progress }: { progress: KeyProgress }) {
  const metrics = [
    {
      label:   "Req. Selesai",
      value:   progress.requirements_completed,
      total:   progress.requirements_total,
      color:   progress.requirements_completed === progress.requirements_total
                 ? "var(--color-success)"
                 : "var(--color-warning)",
      icon:    "✅",
    },
    {
      label:   "Bukti Diunggah",
      value:   progress.evidence_uploaded,
      total:   progress.requirements_total,
      color:   "var(--color-accent)",
      icon:    "📎",
    },
    {
      label:   "Diverifikasi",
      value:   progress.evidence_verified,
      total:   progress.requirements_total,
      color:   "var(--color-success)",
      icon:    "✓",
    },
    {
      label:   "Menunggu Review",
      value:   progress.evidence_awaiting,
      total:   null,
      color:   progress.evidence_awaiting > 0 ? "var(--color-warning)" : "var(--color-ink-3)",
      icon:    "⏳",
    },
    {
      label:   "Terlambat",
      value:   progress.overdue_count,
      total:   null,
      color:   progress.overdue_count > 0 ? "var(--color-danger)" : "var(--color-ink-3)",
      icon:    "⚠",
    },
  ];

  return (
    <div className="card" style={{ marginBottom: 16 }}>
      <div style={{ fontSize: 13, fontWeight: 600, color: "var(--color-ink)", marginBottom: 14 }}>
        Progress Utama
      </div>
      <div style={{ display: "grid", gridTemplateColumns: "repeat(5, 1fr)", gap: 8 }}>
        {metrics.map((m) => (
          <div key={m.label} style={{
            textAlign: "center",
            padding: "10px 8px",
            borderRadius: 8,
            backgroundColor: "var(--color-paper-2)",
          }}>
            <div style={{ fontSize: 11, marginBottom: 4 }}>{m.icon}</div>
            <div style={{ fontSize: 18, fontWeight: 800, color: m.color, lineHeight: 1 }}>
              {m.value}
              {m.total !== null && (
                <span style={{ fontSize: 11, fontWeight: 400, color: "var(--color-ink-3)" }}>
                  /{m.total}
                </span>
              )}
            </div>
            <div style={{ fontSize: 10, color: "var(--color-ink-3)", marginTop: 4, lineHeight: 1.2 }}>
              {m.label}
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}

// ── Sprint 10: Workspace Table view ──────────────────────────
// Drop-in alternative to the Checklist view. Toggled by a state variable, in the main page. Shows all requirements as a compact sortable table.

function WorkspaceTable({
  requirements,
  projectId,
  onUpdated,
}: {
  requirements: import("@/lib/api/projects").RequirementItem[];
  projectId:    string;
  onUpdated:    (intel: import("@/lib/api/projects").IntelligenceSummary) => void;
}) {
  const statusColors: Record<string, { color: string; label: string }> = {
    pending:             { color: "var(--color-ink-3)",   label: "Belum"     },
    in_progress:         { color: "var(--color-warning)", label: "Diproses"  },
    menunggu_verifikasi: { color: "var(--color-accent)",  label: "Review"    },
    completed:           { color: "var(--color-success)", label: "Selesai"   },
    not_applicable:      { color: "var(--color-ink-3)",   label: "N/A"       },
  };

  return (
    <div style={{ overflowX: "auto" }}>
      <table style={{ width: "100%", borderCollapse: "collapse", fontSize: 12 }}>
        <thead>
          <tr style={{ borderBottom: "2px solid rgba(14,13,11,0.08)" }}>
            {["Requirement", "Pemilik", "Status", "Tenggat", "Bukti", "Bobot"].map((h) => (
              <th key={h} style={{
                padding: "8px 10px", textAlign: "left",
                fontSize: 10, fontWeight: 700,
                color: "var(--color-ink-3)",
                textTransform: "uppercase", letterSpacing: "0.06em",
                whiteSpace: "nowrap",
              }}>
                {h}
              </th>
            ))}
          </tr>
        </thead>
        <tbody>
          {requirements.map((req) => {
            const sm      = statusColors[req.status] ?? statusColors.pending;
            const isOver  = req.is_overdue;
            const blocked = req.is_dependency_blocked;

            return (
              <tr key={req.id} style={{
                borderBottom: "1px solid rgba(14,13,11,0.05)",
                opacity: blocked ? 0.5 : 1,
                backgroundColor: req.status === "completed"
                  ? "var(--color-success-light)"
                  : "transparent",
              }}>
                {/* Requirement name */}
                <td style={{ padding: "10px 10px" }}>
                  <div style={{ display: "flex", alignItems: "center", gap: 6 }}>
                    {blocked && <Lock size={11} style={{ color: "var(--color-ink-3)", flexShrink: 0 }} />}
                    <span style={{
                      fontWeight: 500,
                      color: req.status === "completed" ? "var(--color-ink-3)" : "var(--color-ink)",
                      textDecoration: req.status === "completed" ? "line-through" : "none",
                    }}>
                      {req.name}
                    </span>
                    {req.is_mandatory && req.status !== "completed" && !blocked && (
                      <span style={{ fontSize: 9, color: "var(--color-danger)", fontWeight: 700 }}>⚡</span>
                    )}
                  </div>
                  {req.description && (
                    <div style={{ fontSize: 10, color: "var(--color-ink-3)", marginTop: 2 }}>
                      {req.description}
                    </div>
                  )}
                </td>

                {/* Owner */}
                <td style={{ padding: "10px 10px", whiteSpace: "nowrap" }}>
                  {req.assigned_to_name
                    ? <span style={{ fontSize: 11, color: "var(--color-ink)" }}>👤 {req.assigned_to_name}</span>
                    : <span style={{ fontSize: 11, color: "var(--color-ink-3)", fontStyle: "italic" }}>—</span>
                  }
                </td>

                {/* Status badge */}
                <td style={{ padding: "10px 10px", whiteSpace: "nowrap" }}>
                  <span style={{
                    fontSize: 10, fontWeight: 600,
                    padding: "2px 8px", borderRadius: 999,
                    color: sm.color,
                    backgroundColor: `${sm.color}18`,
                  }}>
                    {sm.label}
                  </span>
                </td>

                {/* Due date */}
                <td style={{ padding: "10px 10px", whiteSpace: "nowrap" }}>
                  {req.due_date ? (
                    <span style={{
                      fontSize: 11,
                      color: isOver ? "var(--color-danger)" : "var(--color-ink-3)",
                      fontWeight: isOver ? 700 : 400,
                    }}>
                      {isOver
                        ? `⏰ ${Math.abs(req.days_until_due ?? 0)}h terlambat`
                        : new Date(req.due_date).toLocaleDateString("id-ID", { day: "numeric", month: "short" })
                      }
                    </span>
                  ) : (
                    <span style={{ fontSize: 11, color: "var(--color-ink-3)" }}>—</span>
                  )}
                </td>

                {/* Evidence count */}
                <td style={{ padding: "10px 10px", textAlign: "center" }}>
                  {req.evidence_count > 0 ? (
                    <span style={{ fontSize: 11, fontWeight: 600, color: "var(--color-accent)" }}>
                      📎 {req.evidence_count}
                      {req.has_pending_evidence && " ⏳"}
                    </span>
                  ) : (
                    <span style={{ fontSize: 11, color: "var(--color-ink-3)" }}>—</span>
                  )}
                </td>

                {/* Weight */}
                <td style={{ padding: "10px 10px", whiteSpace: "nowrap" }}>
                  {req.is_mandatory ? (
                    <span style={{ fontSize: 11, fontWeight: 700, color: "var(--color-ink-3)" }}>
                      {req.weight_pct}%
                    </span>
                  ) : (
                    <span style={{ fontSize: 11, color: "var(--color-ink-3)" }}>—</span>
                  )}
                </td>
              </tr>
            );
          })}
        </tbody>
      </table>
    </div>
  );
}

function DependencyGraphPanel({ projectId }: { projectId: string }) {
  const [graph,          setGraph]          = useState<DependencyGraph | null>(null);
  const [loading,        setLoading]        = useState(true);
  const [expanded,       setExpanded]       = useState(false);
  const [selectedNodeId, setSelectedNodeId] = useState<string | null>(null);

  useEffect(() => {
    projectsApi.getDependencyGraph(projectId)
      .then(setGraph)
      .catch(() => {})
      .finally(() => setLoading(false));
  }, [projectId]);

  // ── Status colour helpers (unchanged from Sprint 11) ─────
  const nodeColor = (node: DependencyNode): string => {
    if (node.status === "completed")           return "var(--color-success)";
    if (node.status === "menunggu_verifikasi") return "var(--color-accent)";
    if (node.is_blocking)                      return "var(--color-danger)";
    if (node.is_dependency_blocked)            return "var(--color-ink-3)";
    if (node.status === "in_progress")         return "var(--color-warning)";
    return "rgba(14,13,11,0.3)";
  };

  const nodeBg = (node: DependencyNode): string => {
    if (node.status === "completed")           return "var(--color-success-light)";
    if (node.status === "menunggu_verifikasi") return "var(--color-accent-light)";
    if (node.is_blocking)                      return "var(--color-danger-light)";
    if (node.is_dependency_blocked)            return "rgba(14,13,11,0.04)";
    if (node.status === "in_progress")         return "var(--color-warning-light)";
    return "var(--color-paper-2)";
  };

  const nodeIcon = (node: DependencyNode): string => {
    if (node.status === "completed")           return "✅";
    if (node.status === "menunggu_verifikasi") return "⏳";
    if (node.is_blocking)                      return "⚡";
    if (node.is_dependency_blocked)            return "🔒";
    if (node.status === "in_progress")         return "●";
    return "○";
  };

  if (loading) return (
    <div className="card" style={{ marginBottom: 16, textAlign: "center", padding: 16, color: "var(--color-ink-3)", fontSize: 12 }}>
      Memuat dependency graph...
    </div>
  );

  if (!graph || graph.nodes.length === 0) return null;

  // ── Topological sort (unchanged from Sprint 11) ────────────────
  const incomingEdges = new Map<string, string[]>();
  graph.nodes.forEach(n => incomingEdges.set(n.id, []));
  graph.edges.forEach(e => {
    const arr = incomingEdges.get(e.to) ?? [];
    arr.push(e.from);
    incomingEdges.set(e.to, arr);
  });

  const columns = new Map<string, number>();
  const assignCol = (nodeId: string, visited = new Set<string>()): number => {
    if (columns.has(nodeId)) return columns.get(nodeId)!;
    if (visited.has(nodeId)) return 0;
    visited.add(nodeId);
    const prereqs = incomingEdges.get(nodeId) ?? [];
    const col = prereqs.length === 0
      ? 0
      : Math.max(...prereqs.map(p => assignCol(p, new Set(visited)))) + 1;
    columns.set(nodeId, col);
    return col;
  };
  graph.nodes.forEach(n => assignCol(n.id));

  const colGroups = new Map<number, string[]>();
  graph.nodes.forEach(n => {
    const col = columns.get(n.id) ?? 0;
    if (!colGroups.has(col)) colGroups.set(col, []);
    colGroups.get(col)!.push(n.id);
  });
  const numCols = Math.max(...Array.from(columns.values())) + 1;

  const NODE_W  = 152;
  const NODE_H  = 58;
  const COL_GAP = 56;
  const ROW_GAP = 14;

  const nodeMap   = new Map(graph.nodes.map(n => [n.id, n]));
  const positions = new Map<string, { x: number; y: number }>();

  for (let col = 0; col < numCols; col++) {
    const nodesInCol = colGroups.get(col) ?? [];
    nodesInCol.forEach((nodeId, rowIdx) => {
      positions.set(nodeId, {
        x: col * (NODE_W + COL_GAP),
        y: rowIdx * (NODE_H + ROW_GAP),
      });
    });
  }

  const maxRows = Math.max(...Array.from(colGroups.values()).map(g => g.length));
  const svgW    = numCols * (NODE_W + COL_GAP) - COL_GAP + 24;
  const svgH    = maxRows * (NODE_H + ROW_GAP) - ROW_GAP + 16;

  // Sprint 16: selected node for detail panel
  const selectedNode = selectedNodeId ? nodeMap.get(selectedNodeId) : null;

  const handleNodeClick = (nodeId: string) => {
    setSelectedNodeId(prev => prev === nodeId ? null : nodeId);
  };

  return (
    <div className="card" style={{ marginBottom: 16 }}>
      {/* ── Header (unchanged) ── */}
      <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between", marginBottom: 10 }}>
        <div>
          <div style={{ fontSize: 13, fontWeight: 600, color: "var(--color-ink)" }}>
            Dependency Graph
          </div>
          <div style={{ fontSize: 11, color: "var(--color-ink-3)", marginTop: 2 }}>
            Apa yang bergantung pada apa — tahap {graph.stage_display}
            {/* Sprint 16 hint */}
            <span style={{ marginLeft: 8, opacity: 0.6 }}>· Klik node untuk detail</span>
          </div>
        </div>
        <button
          onClick={() => setExpanded(!expanded)}
          style={{ fontSize: 11, color: "var(--color-accent)", background: "none", border: "none", cursor: "pointer", fontWeight: 600 }}>
          {expanded ? "Sembunyikan ↑" : "Lihat graf ↓"}
        </button>
      </div>

      {/* ── Legend (unchanged) ── */}
      <div style={{ display: "flex", gap: 14, flexWrap: "wrap", marginBottom: 12 }}>
        {[
          { color: "var(--color-success)", label: "Selesai"   },
          { color: "var(--color-warning)", label: "Diproses"  },
          { color: "var(--color-accent)",  label: "Review"    },
          { color: "var(--color-danger)",  label: "Memblokir" },
          { color: "var(--color-ink-3)",   label: "Terkunci"  },
        ].map(({ color, label }) => (
          <div key={label} style={{ display: "flex", alignItems: "center", gap: 5 }}>
            <div style={{ width: 9, height: 9, borderRadius: 2, backgroundColor: color }} />
            <span style={{ fontSize: 10, color: "var(--color-ink-3)" }}>{label}</span>
          </div>
        ))}
      </div>

      {/* ── Collapsed: pill chain — NOW CLICKABLE ── */}
      {!expanded && (
        <div style={{ display: "flex", alignItems: "center", gap: 6, flexWrap: "wrap" }}>
          {graph.nodes.map((node) => {
            const color    = nodeColor(node);
            const bg       = nodeBg(node);
            const icon     = nodeIcon(node);
            const isSelected = selectedNodeId === node.id;
            return (
              <div key={node.id} style={{ display: "flex", alignItems: "center", gap: 6 }}>
                {/* Sprint 16: clickable pill */}
                <div
                  onClick={() => handleNodeClick(node.id)}
                  style={{
                    padding: "5px 11px", borderRadius: 999,
                    backgroundColor: bg,
                    border: isSelected
                      ? `2px solid ${color}`
                      : `1.5px solid ${color}44`,
                    fontSize: 11, fontWeight: 600, color,
                    display: "flex", alignItems: "center", gap: 5,
                    cursor: "pointer",
                    transform: isSelected ? "scale(1.04)" : "scale(1)",
                    transition: "all 0.15s",
                    boxShadow: isSelected ? `0 0 0 3px ${color}22` : "none",
                  }}>
                  <span style={{ fontSize: 12 }}>{icon}</span>
                  {node.name}
                  {node.is_mandatory && (
                    <span style={{ fontSize: 9, opacity: 0.7 }}>{node.weight_pct}%</span>
                  )}
                </div>
                {graph.edges.some(e => e.from === node.id) && (
                  <span style={{ color: "var(--color-ink-3)", fontSize: 14, lineHeight: 1 }}>→</span>
                )}
              </div>
            );
          })}
        </div>
      )}

      {/* ── Expanded: SVG graph — nodes NOW CLICKABLE ── */}
      {expanded && (
        <div style={{ overflowX: "auto", paddingBottom: 4 }}>
          <svg width={svgW} height={svgH + 8} style={{ display: "block", minWidth: svgW }}>
            {/* Edges (unchanged) */}
            {graph.edges.map((edge, i) => {
              const from = positions.get(edge.from);
              const to   = positions.get(edge.to);
              if (!from || !to) return null;
              const x1 = from.x + NODE_W + 10;
              const y1 = from.y + NODE_H / 2 + 5;
              const x2 = to.x + 10;
              const y2 = to.y + NODE_H / 2 + 5;
              const cx  = x1 + (x2 - x1) * 0.55;
              const toNode   = nodeMap.get(edge.to);
              const fromNode = nodeMap.get(edge.from);
              const edgeColor =
                toNode?.is_dependency_blocked  ? "rgba(14,13,11,0.12)" :
                toNode?.is_blocking            ? "var(--color-danger)"  :
                fromNode?.status === "completed" ? "var(--color-success)" :
                                                  "rgba(14,13,11,0.18)";
              const isDashed = !!toNode?.is_dependency_blocked;
              return (
                <g key={`edge-${i}`}>
                  <path
                    d={`M${x1},${y1} C${cx},${y1} ${cx},${y2} ${x2},${y2}`}
                    fill="none" stroke={edgeColor} strokeWidth={1.5}
                    strokeDasharray={isDashed ? "4 3" : undefined}
                  />
                  <polygon
                    points={`${x2},${y2} ${x2 - 7},${y2 - 4} ${x2 - 7},${y2 + 4}`}
                    fill={edgeColor}
                  />
                </g>
              );
            })}

            {/* Nodes — Sprint 16: clickable via onClick on <g> */}
            {graph.nodes.map((node) => {
              const pos  = positions.get(node.id);
              if (!pos) return null;
              const color      = nodeColor(node);
              const bg         = nodeBg(node);
              const icon       = nodeIcon(node);
              const isSelected = selectedNodeId === node.id;
              const px         = pos.x + 10;
              const py         = pos.y + 5;
              const displayName = node.name.length > 17
                ? node.name.slice(0, 15) + "…" : node.name;

              return (
                <g
                  key={`node-${node.id}`}
                  transform={`translate(${px}, ${py})`}
                  onClick={() => handleNodeClick(node.id)}
                  style={{ cursor: "pointer" }}
                >
                  <rect
                    width={NODE_W} height={NODE_H} rx={8}
                    fill={bg}
                    stroke={isSelected ? color : `${color}99`}
                    strokeWidth={isSelected ? 2.5 : 1.5}
                  />
                  {/* Selection glow */}
                  {isSelected && (
                    <rect width={NODE_W} height={NODE_H} rx={8}
                      fill="none" stroke={color} strokeWidth={4} opacity={0.15}
                    />
                  )}
                  <text x={12} y={NODE_H / 2} fontSize={15} dominantBaseline="middle">
                    {icon}
                  </text>
                  <text x={32} y={NODE_H / 2 - (node.is_mandatory ? 7 : 0)}
                    fontSize={11} fontWeight={600} fill={color} dominantBaseline="middle">
                    {displayName}
                  </text>
                  {node.is_mandatory && (
                    <text x={32} y={NODE_H / 2 + 9}
                      fontSize={9} fill={color} dominantBaseline="middle" opacity={0.65}>
                      bobot {node.weight_pct}%
                      {node.is_blocking ? " · ⚡ memblokir" :
                       node.status === "completed" ? " · selesai" : ""}
                    </text>
                  )}
                  {!node.is_mandatory && (
                    <text x={32} y={NODE_H / 2 + 9}
                      fontSize={9} fill="var(--color-ink-3)" dominantBaseline="middle">
                      opsional
                    </text>
                  )}
                </g>
              );
            })}
          </svg>
        </div>
      )}

      {/* ── Sprint 16: Node detail panel ── */}
      {selectedNode && (
        <div style={{
          marginTop: 12, padding: "12px 14px", borderRadius: 10,
          backgroundColor: nodeBg(selectedNode),
          border: `1.5px solid ${nodeColor(selectedNode)}44`,
          position: "relative",
        }}>
          {/* Close button */}
          <button
            onClick={() => setSelectedNodeId(null)}
            style={{
              position: "absolute", top: 8, right: 8,
              background: "none", border: "none", cursor: "pointer",
              fontSize: 14, color: "var(--color-ink-3)", lineHeight: 1,
            }}>
            ✕
          </button>

          {/* Node title */}
          <div style={{
            fontSize: 13, fontWeight: 700,
            color: nodeColor(selectedNode), marginBottom: 8,
          }}>
            {nodeIcon(selectedNode)} {selectedNode.name}
            <span style={{
              marginLeft: 8, fontSize: 9, fontWeight: 600,
              padding: "2px 7px", borderRadius: 999,
              backgroundColor: `${nodeColor(selectedNode)}22`,
              color: nodeColor(selectedNode),
            }}>
              {selectedNode.status_display}
            </span>
          </div>

          {/* Detail rows */}
          <div style={{ display: "flex", flexDirection: "column", gap: 5 }}>
            {/* Block reason */}
            {selectedNode.block_reason && (
              <div style={{ display: "flex", gap: 8, fontSize: 11, color: "var(--color-ink)" }}>
                <span style={{ color: "var(--color-ink-3)", minWidth: 60, flexShrink: 0 }}>Alasan</span>
                <span style={{ fontWeight: 600, color: "var(--color-danger)" }}>
                  {selectedNode.block_reason}
                </span>
              </div>
            )}
            {/* Owner */}
            <div style={{ display: "flex", gap: 8, fontSize: 11, color: "var(--color-ink)" }}>
              <span style={{ color: "var(--color-ink-3)", minWidth: 60, flexShrink: 0 }}>Pemilik</span>
              <span>
                {selectedNode.assigned_to_name
                  ? `👤 ${selectedNode.assigned_to_name}`
                  : <span style={{ color: "var(--color-ink-3)", fontStyle: "italic" }}>Belum ditugaskan</span>
                }
              </span>
            </div>
            {/* ETA */}
            <div style={{ display: "flex", gap: 8, fontSize: 11, color: "var(--color-ink)" }}>
              <span style={{ color: "var(--color-ink-3)", minWidth: 60, flexShrink: 0 }}>ETA</span>
              <span>~{selectedNode.est_minutes} menit</span>
            </div>
            {/* Impact */}
            {selectedNode.is_mandatory && selectedNode.status !== "completed" && (
              <div style={{ display: "flex", gap: 8, fontSize: 11, color: "var(--color-ink)" }}>
                <span style={{ color: "var(--color-ink-3)", minWidth: 60, flexShrink: 0 }}>Dampak</span>
                <span style={{ fontWeight: 700, color: "var(--color-success)" }}>
                  +{selectedNode.weight_pct}% kesiapan jika selesai
                </span>
              </div>
            )}
          </div>

          {/* CTA button */}
          {selectedNode.status !== "completed" && (
            <button
              onClick={() => {
                document
                  .getElementById("requirements-card")
                  ?.scrollIntoView({ behavior: "smooth", block: "start" });
                setSelectedNodeId(null);
              }}
              style={{
                marginTop: 10, width: "100%",
                padding: "8px", borderRadius: 7, border: "none",
                backgroundColor: nodeColor(selectedNode), color: "white",
                fontSize: 11, fontWeight: 700, cursor: "pointer",
                transition: "opacity 0.15s",
              }}
              onMouseEnter={e => (e.currentTarget.style.opacity = "0.88")}
              onMouseLeave={e => (e.currentTarget.style.opacity = "1")}
            >
              Ambil Tindakan →
            </button>
          )}
        </div>
      )}
    </div>
  );
}

// ── Sprint 12: Action Chain Panel ─────────────────────────────
// Slots inside the existing Alerts card, below AlertsPanel. Shows ordered micro-steps to resolve the primary blocker.
// Only renders if intel.action_chain is non-null (i.e. there IS a blocker).
function ActionChainPanel({ chain }: { chain: ActionChain | null }) {
  if (!chain) return null;

  const stepIcon: Record<string, string> = {
    assign:   "👤",
    upload:   "📎",
    verify:   "⏳",
    complete: "✓",
  };

  return (
    <div style={{
      marginTop: 12, paddingTop: 12,
      borderTop: "1px solid rgba(14,13,11,0.06)",
    }}>
      {/* Sub-header */}
      <div style={{
        display: "flex", alignItems: "center",
        justifyContent: "space-between", marginBottom: 10,
      }}>
        <div style={{
          fontSize: 10, fontWeight: 700,
          color: "var(--color-ink-3)",
          textTransform: "uppercase", letterSpacing: "0.06em",
        }}>
          Langkah Berikutnya
        </div>
        <div style={{
          fontSize: 10, fontWeight: 600,
          color: chain.completed_steps > 0 ? "var(--color-success)" : "var(--color-ink-3)",
        }}>
          {chain.completed_steps}/{chain.total_steps} selesai
        </div>
      </div>

      {/* Steps */}
      <div style={{ display: "flex", flexDirection: "column", gap: 7 }}>
        {chain.steps.map((step) => (
          <div key={step.step} style={{
            display: "flex", alignItems: "center", gap: 9,
            opacity: step.is_done ? 0.45 : 1,
          }}>
            {/* Step circle */}
            <div style={{
              width: 22, height: 22, borderRadius: "50%", flexShrink: 0,
              backgroundColor: step.is_done
                ? "var(--color-success)"
                : "rgba(14,13,11,0.07)",
              border: step.is_done
                ? "none"
                : "1.5px solid rgba(14,13,11,0.15)",
              display: "flex", alignItems: "center", justifyContent: "center",
              fontSize: step.is_done ? 11 : 10, fontWeight: 700,
              color: step.is_done ? "white" : "var(--color-ink-3)",
            }}>
              {step.is_done ? "✓" : step.step}
            </div>
            {/* Step label */}
            <div style={{ flex: 1 }}>
              <span style={{
                fontSize: 11,
                fontWeight: step.is_done ? 400 : 600,
                color: step.is_done ? "var(--color-ink-3)" : "var(--color-ink)",
                textDecoration: step.is_done ? "line-through" : "none",
              }}>
                {stepIcon[step.action_type] ?? "•"} {step.action}
              </span>
            </div>
            {/* Time estimate (only for pending steps) */}
            {!step.is_done && (
              <span style={{
                fontSize: 10, color: "var(--color-ink-3)",
                whiteSpace: "nowrap", flexShrink: 0,
              }}>
                ~{step.est_minutes} mnt
              </span>
            )}
          </div>
        ))}
      </div>

      {/* Estimated total remaining */}
      {chain.est_remaining_minutes > 0 && (
        <div style={{
          marginTop: 10, paddingTop: 8,
          borderTop: "1px solid rgba(14,13,11,0.04)",
          fontSize: 10, color: "var(--color-ink-3)", textAlign: "right",
        }}>
          ⏱ Est. sisa: <strong>{chain.est_remaining_minutes} menit</strong> untuk membuka blokir
        </div>
      )}
    </div>
  );
}

// ── Sprint 12: Activity Timeline Panel ────────────────────────
// New card rendered BELOW the main requirements + project info grid.
// Fetches from GET /activity/?limit=20&type={filterType}
// Filter tabs trigger re-fetch — no client-side filtering.

function ActivityTimelinePanel({ projectId }: { projectId: string }) {
  const [activities, setActivities] = useState<ActivityItem[]>([]);
  const [loading,    setLoading]    = useState(true);
  const [filterType, setFilterType] = useState<ActivityFilterType>("all");
  const [count,      setCount]      = useState(0);

  useEffect(() => {
    setLoading(true);
    projectsApi.getActivity(projectId, 20, filterType)
      .then((data) => {
        setActivities(data.results);
        setCount(data.count);
      })
      .catch(() => {})
      .finally(() => setLoading(false));
  }, [projectId, filterType]);

  const filterTabs: { key: ActivityFilterType; label: string; icon: string }[] = [
    { key: "all",         label: "Semua",     icon: "📋" },
    { key: "evidence",    label: "Bukti",      icon: "📎" },
    { key: "readiness",   label: "Kesiapan",  icon: "✅" },
    { key: "assignments", label: "Penugasan", icon: "👤" },
    { key: "comments",    label: "Komentar",  icon: "💬" },
  ];

  // Action type → icon mapping
  const actionIcon: Record<string, string> = {
    created:           "🆕",
    updated:           "✏️",
    evidence_uploaded: "📎",
    evidence_approved: "✅",
    evidence_rejected: "❌",
    completed:         "✓",
    stage_advanced:    "🚀",
    assigned:          "👤",
    due_date_set:      "📅",
    comment_added:     "💬",
  };

  // Action type → colour for the dot
  const actionColor = (action: string): string => {
    if (action === "completed" || action === "evidence_approved") return "var(--color-success)";
    if (action === "evidence_rejected")                           return "var(--color-danger)";
    if (action === "stage_advanced")                              return "var(--color-accent)";
    if (action === "evidence_uploaded")                           return "var(--color-warning)";
    if (action === "assigned" || action === "due_date_set")       return "var(--color-info)";
    return "rgba(14,13,11,0.2)";
  };

  // Human-readable relative timestamps in Bahasa Indonesia
  const relativeTime = (iso: string): string => {
    const diff    = Date.now() - new Date(iso).getTime();
    const minutes = Math.floor(diff / 60_000);
    if (minutes < 1)   return "baru saja";
    if (minutes < 60)  return `${minutes} mnt yang lalu`;
    const hours = Math.floor(minutes / 60);
    if (hours < 24)    return `${hours} jam yang lalu`;
    const days = Math.floor(hours / 24);
    if (days === 1)    return "kemarin";
    if (days < 30)     return `${days} hari yang lalu`;
    return new Date(iso).toLocaleDateString("id-ID", {
      day: "numeric", month: "short", year: "numeric",
    });
  };

  return (
    <div className="card" style={{ marginBottom: 16 }}>
      {/* ── Header ── */}
      <div style={{
        display: "flex", alignItems: "center",
        justifyContent: "space-between", marginBottom: 12,
      }}>
        <div>
          <div style={{ fontSize: 13, fontWeight: 600, color: "var(--color-ink)" }}>
            Activity Timeline
          </div>
          <div style={{ fontSize: 11, color: "var(--color-ink-3)", marginTop: 2 }}>
            {count > 0 ? `${count} aktivitas terakhir` : "Riwayat perubahan proyek"}
          </div>
        </div>
      </div>

      {/* ── Filter tabs ── */}
      <div style={{ display: "flex", gap: 5, flexWrap: "wrap", marginBottom: 14 }}>
        {filterTabs.map((tab) => (
          <button
            key={tab.key}
            onClick={() => setFilterType(tab.key)}
            style={{
              padding: "4px 10px", borderRadius: 999,
              fontSize: 10, fontWeight: 600, cursor: "pointer",
              transition: "all 0.15s",
              border: filterType === tab.key
                ? "none"
                : "1px solid rgba(14,13,11,0.12)",
              backgroundColor: filterType === tab.key
                ? "var(--color-accent)"
                : "white",
              color: filterType === tab.key ? "white" : "var(--color-ink-3)",
            }}>
            {tab.icon} {tab.label}
          </button>
        ))}
      </div>

      {/* ── Timeline content ── */}
      {loading ? (
        <div style={{
          textAlign: "center", padding: "20px 0",
          color: "var(--color-ink-3)", fontSize: 12,
        }}>
          Memuat aktivitas...
        </div>
      ) : activities.length === 0 ? (
        <div style={{ textAlign: "center", padding: "20px 0", color: "var(--color-ink-3)" }}>
          <div style={{ fontSize: 24, marginBottom: 6, opacity: 0.35 }}>📋</div>
          <div style={{ fontSize: 12 }}>
            {filterType === "all"
              ? "Belum ada aktivitas untuk proyek ini"
              : "Belum ada aktivitas untuk filter ini"}
          </div>
        </div>
      ) : (
        <div style={{ position: "relative" }}>
          {/* Vertical timeline line */}
          <div style={{
            position: "absolute", left: 10, top: 12, bottom: 12,
            width: 1, backgroundColor: "rgba(14,13,11,0.07)",
          }} />

          <div style={{ display: "flex", flexDirection: "column", gap: 14 }}>
            {activities.map((item) => (
              <div key={item.id} style={{ display: "flex", gap: 12, position: "relative" }}>
                {/* Coloured dot */}
                <div style={{
                  width: 21, height: 21, borderRadius: "50%", flexShrink: 0,
                  backgroundColor: actionColor(item.action),
                  display: "flex", alignItems: "center", justifyContent: "center",
                  fontSize: 9, color: "white", zIndex: 1,
                }}>
                  {actionIcon[item.action] ?? "•"}
                </div>

                {/* Content */}
                <div style={{ flex: 1, paddingBottom: 2 }}>
                  <div style={{ fontSize: 11, color: "var(--color-ink)", lineHeight: 1.4 }}>
                    {item.message}
                  </div>
                  {item.notes && (
                    <div style={{
                      fontSize: 10, color: "var(--color-ink-3)",
                      marginTop: 2, fontStyle: "italic",
                    }}>
                      "{item.notes}"
                    </div>
                  )}
                  {(item.old_value || item.new_value) && item.old_value !== item.new_value && (
                    <div style={{ fontSize: 10, color: "var(--color-ink-3)", marginTop: 2 }}>
                      <span style={{ textDecoration: "line-through" }}>{item.old_value}</span>
                      {" → "}
                      <span style={{ fontWeight: 600, color: "var(--color-accent)" }}>
                        {item.new_value}
                      </span>
                    </div>
                  )}

                  {/* Sprint 16: Cause & Effect badges */}
                  {(item.readiness_delta != null || item.risk_delta != null) && (
                    <div style={{
                      display: "flex", gap: 6, marginTop: 5,
                      flexWrap: "wrap",
                    }}>
                      {/* Readiness delta badge */}
                      {item.readiness_delta != null && item.readiness_delta !== 0 && (
                        <span style={{
                          fontSize: 9, fontWeight: 700,
                          padding: "2px 8px", borderRadius: 999,
                          backgroundColor: item.readiness_delta > 0
                            ? "var(--color-success-light)"
                            : "var(--color-danger-light)",
                          color: item.readiness_delta > 0
                            ? "var(--color-success)"
                            : "var(--color-danger)",
                        }}>
                          {item.readiness_delta > 0 ? "↑" : "↓"} Kesiapan{" "}
                          {item.readiness_delta > 0 ? "+" : ""}
                          {item.readiness_delta}%
                        </span>
                      )}
                      {/* Risk delta badge — note: risk DECREASING is GOOD (green) */}
                      {item.risk_delta != null && item.risk_delta !== 0 && (
                        <span style={{
                          fontSize: 9, fontWeight: 700,
                          padding: "2px 8px", borderRadius: 999,
                          backgroundColor: item.risk_delta < 0
                            ? "var(--color-success-light)"
                            : "var(--color-danger-light)",
                          color: item.risk_delta < 0
                            ? "var(--color-success)"
                            : "var(--color-danger)",
                        }}>
                          {item.risk_delta < 0 ? "↓" : "↑"} Risiko{" "}
                          {item.risk_delta > 0 ? "+" : ""}
                          {item.risk_delta}
                        </span>
                      )}
                    </div>
                  )}
              
                  <div style={{
                    fontSize: 10, color: "var(--color-ink-3)", marginTop: 3,
                  }}>
                    {relativeTime(item.timestamp)}
                  </div>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}

// ── Sprint 13: Decision Engine Panel ─────────────────────────
// Shows the single best action with quantified readiness impact,
// 3 bullet reasons, and ranked alternatives 2-3.
// Fetches independently from GET /api/projects/<id>/decision/
// so the panel loads without blocking the rest of the page.
function DecisionEnginePanel({ projectId }: { projectId: string }) {
  const [engine,  setEngine]  = useState<DecisionEngine | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    projectsApi.getDecisionEngine(projectId)
      .then(setEngine)
      .catch(() => {})
      .finally(() => setLoading(false));
  }, [projectId]);

  // Priority → colour + label mapping
  const priorityMeta: Record<string, { color: string; bg: string; label: string }> = {
    high:   { color: "var(--color-danger)",  bg: "var(--color-danger-light)",  label: "Prioritas Tinggi"  },
    medium: { color: "var(--color-warning)", bg: "var(--color-warning-light)", label: "Prioritas Sedang"  },
    low:    { color: "var(--color-ink-3)",   bg: "var(--color-paper-2)",       label: "Prioritas Rendah"  },
  };

  if (loading) {
    return (
      <div className="card" style={{ marginBottom: 16 }}>
        <div style={{ fontSize: 13, fontWeight: 600, color: "var(--color-ink)", marginBottom: 8 }}>
          🎯 Decision Engine
        </div>
        <div style={{ fontSize: 11, color: "var(--color-ink-3)", padding: "12px 0" }}>
          Menganalisis data proyek...
        </div>
      </div>
    );
  }

  if (!engine) return null;

  // ── All clear — nothing to do ─────────────────────────────
  if (!engine.has_recommendations) {
    return (
      <div className="card" style={{ marginBottom: 16 }}>
        <div style={{ fontSize: 13, fontWeight: 600, color: "var(--color-ink)", marginBottom: 12 }}>
          🎯 Decision Engine
        </div>
        <div style={{
          padding: "16px",
          backgroundColor: "var(--color-success-light)",
          borderRadius: 10,
          textAlign: "center",
        }}>
          <div style={{ fontSize: 22, marginBottom: 6 }}>🎉</div>
          <div style={{ fontSize: 12, fontWeight: 600, color: "var(--color-success)" }}>
            {engine.message ?? "Semua requirement wajib sudah selesai!"}
          </div>
          {engine.all_clear && (
            <div style={{ fontSize: 11, color: "var(--color-success)", opacity: 0.8, marginTop: 4 }}>
              Proyek siap melanjutkan ke tahap berikutnya
            </div>
          )}
        </div>
      </div>
    );
  }

  const primary = engine.primary!;
  const pm      = priorityMeta[primary.priority] ?? priorityMeta.medium;
  const readinessGain = engine.projected_readiness - engine.current_readiness;

  return (
    <div className="card" style={{ marginBottom: 16 }}>
      {/* ── Header ── */}
      <div style={{
        display: "flex", alignItems: "flex-start",
        justifyContent: "space-between", marginBottom: 14,
      }}>
        <div>
          <div style={{ fontSize: 13, fontWeight: 600, color: "var(--color-ink)" }}>
            🎯 Decision Engine
          </div>
          <div style={{ fontSize: 11, color: "var(--color-ink-3)", marginTop: 2 }}>
            Apa yang harus dilakukan sekarang
          </div>
        </div>
        {/* Readiness projection */}
        <div style={{ textAlign: "right" }}>
          <div style={{ fontSize: 10, color: "var(--color-ink-3)", marginBottom: 2 }}>
            proyeksi kesiapan
          </div>
          <div style={{ display: "flex", alignItems: "center", gap: 5 }}>
            <span style={{ fontSize: 13, fontWeight: 700, color: "var(--color-ink-3)" }}>
              {engine.current_readiness}%
            </span>
            <span style={{ fontSize: 11, color: "var(--color-ink-3)" }}>→</span>
            <span style={{ fontSize: 16, fontWeight: 800, color: "var(--color-success)" }}>
              {engine.projected_readiness}%
            </span>
          </div>
        </div>
      </div>

      {/* ── Primary recommendation card ── */}
      <div style={{
        padding: "14px 16px", borderRadius: 10,
        backgroundColor: "var(--color-paper-2)",
        border: `2px solid ${pm.color}28`,
        marginBottom: engine.alternatives.length > 0 ? 12 : 0,
      }}>
        {/* Priority badge + time estimate */}
        <div style={{ display: "flex", alignItems: "center", gap: 8, marginBottom: 8 }}>
          <span style={{
            fontSize: 9, fontWeight: 700,
            padding: "2px 8px", borderRadius: 999,
            backgroundColor: pm.color, color: "white",
            textTransform: "uppercase", letterSpacing: "0.05em",
          }}>
            {pm.label}
          </span>
          <span style={{ fontSize: 10, color: "var(--color-ink-3)" }}>
            ~{primary.est_minutes} menit
          </span>
        </div>

        {/* Action title + impact badge */}
        <div style={{
          display: "flex", alignItems: "flex-start",
          justifyContent: "space-between", gap: 12, marginBottom: 12,
        }}>
          <div style={{
            fontSize: 15, fontWeight: 700,
            color: "var(--color-ink)", flex: 1, lineHeight: 1.3,
          }}>
            {primary.action}
          </div>
          {/* Readiness impact badge */}
          <div style={{
            padding: "8px 12px", borderRadius: 8, flexShrink: 0,
            backgroundColor: "var(--color-success-light)",
            textAlign: "center",
          }}>
            <div style={{
              fontSize: 20, fontWeight: 800,
              color: "var(--color-success)", lineHeight: 1,
            }}>
              +{readinessGain}%
            </div>
            <div style={{ fontSize: 9, color: "var(--color-success)", marginTop: 2 }}>
              kesiapan
            </div>
          </div>
        </div>

        {/* Reasons */}
        <div style={{
          display: "flex", flexDirection: "column",
          gap: 5, marginBottom: 14,
        }}>
          {primary.reasons.map((reason, i) => (
            <div key={i} style={{ display: "flex", gap: 7, fontSize: 11, color: "var(--color-ink)", lineHeight: 1.4 }}>
              <span style={{ color: pm.color, flexShrink: 0, fontWeight: 700 }}>•</span>
              {reason}
            </div>
          ))}
        </div>

        {/* CTA — scrolls to the requirements card */}
        <button
          onClick={() => {
            document
              .getElementById("requirements-card")
              ?.scrollIntoView({ behavior: "smooth", block: "start" });
          }}
          style={{
            width: "100%", padding: "10px", borderRadius: 8,
            border: "none", cursor: "pointer",
            backgroundColor: pm.color, color: "white",
            fontSize: 12, fontWeight: 700,
            transition: "opacity 0.15s",
          }}
          onMouseEnter={(e) => (e.currentTarget.style.opacity = "0.88")}
          onMouseLeave={(e) => (e.currentTarget.style.opacity = "1")}
        >
          Ambil Tindakan →
        </button>
      </div>

      {/* ── Alternatives ── */}
      {engine.alternatives.length > 0 && (
        <div>
          <div style={{
            fontSize: 10, fontWeight: 700, color: "var(--color-ink-3)",
            textTransform: "uppercase", letterSpacing: "0.06em", marginBottom: 8,
          }}>
            Tindakan Lainnya
          </div>
          <div style={{ display: "flex", flexDirection: "column", gap: 5 }}>
            {engine.alternatives.map((alt) => (
              <div key={alt.rank} style={{
                display: "flex", alignItems: "center", gap: 10,
                padding: "9px 12px", borderRadius: 8,
                backgroundColor: "var(--color-paper-2)",
              }}>
                {/* Rank circle */}
                <div style={{
                  width: 22, height: 22, borderRadius: "50%", flexShrink: 0,
                  backgroundColor: "rgba(14,13,11,0.07)",
                  display: "flex", alignItems: "center", justifyContent: "center",
                  fontSize: 10, fontWeight: 700, color: "var(--color-ink-3)",
                }}>
                  {alt.rank}
                </div>
                {/* Action label */}
                <div style={{ flex: 1, fontSize: 11, fontWeight: 600, color: "var(--color-ink)" }}>
                  {alt.action}
                </div>
                {/* Impact */}
                <div style={{
                  fontSize: 12, fontWeight: 700,
                  color: "var(--color-success)", whiteSpace: "nowrap",
                }}>
                  +{alt.readiness_impact_pct}%
                </div>
                {/* Time estimate */}
                <div style={{
                  fontSize: 10, color: "var(--color-ink-3)",
                  whiteSpace: "nowrap",
                }}>
                  ~{alt.est_minutes} mnt
                </div>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}

// ── Sprint 14: Risk Forecast Panel ───────────────────────────
// Shows current risk vs projected risk in 14 days.
// "What happens if nothing changes?" — honest, deterministic.
// Fetches independently so it doesn't block the rest of the page.

function RiskForecastPanel({ projectId }: { projectId: string }) {
  const [forecast, setForecast] = useState<RiskForecast | null>(null);
  const [loading,  setLoading]  = useState(true);

  useEffect(() => {
    projectsApi.getRiskForecast(projectId)
      .then(setForecast)
      .catch(() => {})
      .finally(() => setLoading(false));
  }, [projectId]);

  // Risk level → colour helper
  const levelColor = (level: string): string => {
    if (level === "high")   return "var(--color-danger)";
    if (level === "medium") return "var(--color-warning)";
    return "var(--color-success)";
  };
  const levelBg = (level: string): string => {
    if (level === "high")   return "var(--color-danger-light)";
    if (level === "medium") return "var(--color-warning-light)";
    return "var(--color-success-light)";
  };

  if (loading) {
    return (
      <div className="card" style={{ marginBottom: 16 }}>
        <div style={{ fontSize: 13, fontWeight: 600, color: "var(--color-ink)", marginBottom: 8 }}>
          📈 Risk Forecast
        </div>
        <div style={{ fontSize: 11, color: "var(--color-ink-3)", padding: "10px 0" }}>
          Menghitung proyeksi risiko...
        </div>
      </div>
    );
  }

  if (!forecast) return null;

  const currentColor  = levelColor(forecast.current.level);
  const forecastColor = levelColor(forecast.forecast.level);
  const isGrowing     = forecast.delta > 0;
  const isStable      = forecast.delta === 0;

  return (
    <div className="card" style={{
      marginBottom: 16,
      // Pulse border if escalating — persistent, calm, not alarming
      border: forecast.will_escalate
        ? "1.5px solid var(--color-danger)"
        : "1.5px solid rgba(14,13,11,0.08)",
    }}>
      {/* ── Header ── */}
      <div style={{
        display: "flex", alignItems: "center",
        justifyContent: "space-between", marginBottom: 14,
      }}>
        <div>
          <div style={{ fontSize: 13, fontWeight: 600, color: "var(--color-ink)" }}>
            📈 Risk Forecast
          </div>
          <div style={{ fontSize: 11, color: "var(--color-ink-3)", marginTop: 2 }}>
            Proyeksi dalam {forecast.days} hari jika tidak ada tindakan
          </div>
        </div>
        {/* Delta badge */}
        {isStable ? (
          <div style={{
            padding: "4px 10px", borderRadius: 6,
            backgroundColor: "var(--color-paper-2)",
            fontSize: 11, fontWeight: 700, color: "var(--color-ink-3)",
          }}>
            = Stabil
          </div>
        ) : (
          <div style={{
            padding: "4px 10px", borderRadius: 6,
            backgroundColor: "var(--color-danger-light)",
            fontSize: 11, fontWeight: 700, color: "var(--color-danger)",
          }}>
            +{forecast.delta} pts
          </div>
        )}
      </div>

      {/* ── Two-column: Current vs Forecast ── */}
      <div style={{
        display: "grid", gridTemplateColumns: "1fr auto 1fr",
        gap: 10, alignItems: "center", marginBottom: 14,
      }}>
        {/* Current */}
        <div style={{
          padding: "14px 16px", borderRadius: 10,
          backgroundColor: levelBg(forecast.current.level),
          textAlign: "center",
        }}>
          <div style={{ fontSize: 10, fontWeight: 700, color: "var(--color-ink-3)", marginBottom: 6, textTransform: "uppercase", letterSpacing: "0.05em" }}>
            Saat Ini
          </div>
          <div style={{ fontSize: 28, fontWeight: 800, color: currentColor, lineHeight: 1 }}>
            {forecast.current.score}
          </div>
          <div style={{ fontSize: 10, color: "var(--color-ink-3)", marginTop: 2 }}>/ 100</div>
          <div style={{
            marginTop: 8, padding: "3px 10px", borderRadius: 999,
            backgroundColor: currentColor, color: "white",
            fontSize: 10, fontWeight: 700, display: "inline-block",
          }}>
            {forecast.current.level_display}
          </div>
        </div>

        {/* Arrow */}
        <div style={{
          fontSize: 20, color: isGrowing ? "var(--color-danger)" : "var(--color-ink-3)",
          textAlign: "center",
        }}>
          {isGrowing ? "→" : "→"}
        </div>

        {/* Forecast */}
        <div style={{
          padding: "14px 16px", borderRadius: 10,
          backgroundColor: levelBg(forecast.forecast.level),
          textAlign: "center",
          border: forecast.will_escalate ? `2px solid ${forecastColor}` : "none",
        }}>
          <div style={{ fontSize: 10, fontWeight: 700, color: "var(--color-ink-3)", marginBottom: 6, textTransform: "uppercase", letterSpacing: "0.05em" }}>
            {forecast.days} Hari Lagi
          </div>
          <div style={{ fontSize: 28, fontWeight: 800, color: forecastColor, lineHeight: 1 }}>
            {forecast.forecast.score}
          </div>
          <div style={{ fontSize: 10, color: "var(--color-ink-3)", marginTop: 2 }}>/ 100</div>
          <div style={{
            marginTop: 8, padding: "3px 10px", borderRadius: 999,
            backgroundColor: forecastColor, color: "white",
            fontSize: 10, fontWeight: 700, display: "inline-block",
          }}>
            {forecast.forecast.level_display}
            {forecast.will_escalate && " ⚠"}
          </div>
        </div>
      </div>

      {/* ── Escalation warning ── */}
      {forecast.will_escalate && (
        <div style={{
          marginBottom: 12, padding: "8px 12px",
          backgroundColor: "var(--color-danger-light)",
          borderRadius: 8, fontSize: 11,
          color: "var(--color-danger)",
          display: "flex", alignItems: "center", gap: 6,
        }}>
          <span style={{ fontSize: 14 }}>⚠</span>
          <span>
            <strong>Tingkat risiko akan naik</strong> dari {forecast.current.level_display} ke {forecast.forecast.level_display} dalam {forecast.days} hari jika tidak ada tindakan.
          </span>
        </div>
      )}

      {/* ── Top drivers ── */}
      {forecast.top_drivers.length > 0 && (
        <div>
          <div style={{
            fontSize: 10, fontWeight: 700, color: "var(--color-ink-3)",
            textTransform: "uppercase", letterSpacing: "0.06em", marginBottom: 8,
          }}>
            Faktor Risiko
          </div>
          <div style={{ display: "flex", flexDirection: "column", gap: 6 }}>
            {forecast.top_drivers.map((driver) => (
              <div key={driver.key} style={{
                display: "flex", alignItems: "flex-start",
                gap: 10, padding: "8px 10px", borderRadius: 8,
                backgroundColor: driver.is_new || driver.delta_points > 0
                  ? "var(--color-warning-light)"
                  : "var(--color-paper-2)",
              }}>
                {/* Points indicator */}
                <div style={{ flexShrink: 0, textAlign: "center", minWidth: 36 }}>
                  <div style={{
                    fontSize: 13, fontWeight: 800,
                    color: driver.delta_points > 0 ? "var(--color-danger)" :
                           driver.is_new          ? "var(--color-warning)" :
                                                    "var(--color-ink-3)",
                  }}>
                    {driver.forecast_points}
                  </div>
                  <div style={{ fontSize: 9, color: "var(--color-ink-3)" }}>pts</div>
                </div>
                {/* Driver info */}
                <div style={{ flex: 1 }}>
                  <div style={{ fontSize: 11, fontWeight: 600, color: "var(--color-ink)", lineHeight: 1.3 }}>
                    {driver.name}
                    {driver.is_new && (
                      <span style={{
                        marginLeft: 6, fontSize: 9, fontWeight: 700,
                        padding: "1px 5px", borderRadius: 3,
                        backgroundColor: "var(--color-warning)",
                        color: "white",
                      }}>
                        Baru
                      </span>
                    )}
                  </div>
                  {driver.delta_points > 0 && (
                    <div style={{ fontSize: 10, color: "var(--color-danger)", marginTop: 2 }}>
                      ↑ +{driver.delta_points} pts dari saat ini
                    </div>
                  )}
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* ── Stable message ── */}
      {isStable && forecast.top_drivers.length === 0 && (
        <div style={{
          textAlign: "center", padding: "12px 0",
          fontSize: 12, color: "var(--color-success)",
        }}>
          ✅ Tidak ada faktor risiko yang diproyeksikan dalam {forecast.days} hari ke depan
        </div>
      )}
    </div>
  );
}

// ── Sprint 17: Event Stream Panel ─────────────────────────────
function EventStreamPanel({
  events,
  lastUpdated,
}: {
  events:      PulseEvent[];
  lastUpdated: string | null;
}) {
  if (events.length === 0) return null;

  const actionIcon: Record<string, string> = {
    completed:           "✅",
    evidence_uploaded:   "📎",
    evidence_approved:   "✓",
    evidence_rejected:   "❌",
    stage_advanced:      "🚀",
    assigned:            "👤",
    due_date_set:        "📅",
    comment_added:       "💬",
    updated:             "✏️",
    created:             "🆕",
  };

  return (
    <div className="card" style={{ marginBottom: 16 }}>
      {/* Header */}
      <div style={{
        display: "flex", alignItems: "center",
        justifyContent: "space-between", marginBottom: 12,
      }}>
        <div style={{ display: "flex", alignItems: "center", gap: 8 }}>
          <div style={{ fontSize: 13, fontWeight: 600, color: "var(--color-ink)" }}>
            Event Stream
          </div>
          {/* Live indicator */}
          <div style={{ display: "flex", alignItems: "center", gap: 4 }}>
            <div style={{
              width: 7, height: 7, borderRadius: "50%",
              backgroundColor: "var(--color-success)",
              boxShadow: "0 0 0 2px var(--color-success-light)",
            }} />
            <span style={{ fontSize: 10, color: "var(--color-success)", fontWeight: 600 }}>
              Live
            </span>
          </div>
        </div>
        {lastUpdated && (
          <span style={{ fontSize: 10, color: "var(--color-ink-3)" }}>
            diperbarui {lastUpdated}
          </span>
        )}
      </div>

      {/* Event list */}
      <div style={{ display: "flex", flexDirection: "column", gap: 0 }}>
        {events.slice(0, 5).map((event, i) => (
          <div key={event.id} style={{
            display: "flex", gap: 10, alignItems: "flex-start",
            padding: "8px 0",
            borderBottom: i < Math.min(events.length, 5) - 1
              ? "1px solid rgba(14,13,11,0.05)"
              : "none",
          }}>
            {/* Action icon */}
            <div style={{
              width: 22, height: 22, borderRadius: "50%",
              backgroundColor: "var(--color-paper-2)",
              display: "flex", alignItems: "center", justifyContent: "center",
              fontSize: 11, flexShrink: 0,
            }}>
              {actionIcon[event.action] ?? "📋"}
            </div>

            {/* Content */}
            <div style={{ flex: 1 }}>
              <div style={{ fontSize: 11, color: "var(--color-ink)", lineHeight: 1.4 }}>
                {event.message}
                {/* Inline cause & effect */}
                {event.readiness_delta != null && event.readiness_delta !== 0 && (
                  <span style={{
                    marginLeft: 8, fontSize: 9, fontWeight: 700,
                    color: event.readiness_delta > 0
                      ? "var(--color-success)"
                      : "var(--color-danger)",
                  }}>
                    {event.readiness_delta > 0 ? "↑" : "↓"} Kesiapan{" "}
                    {event.readiness_delta > 0 ? "+" : ""}
                    {event.readiness_delta}%
                  </span>
                )}
              </div>
            </div>

            {/* Time */}
            <div style={{ fontSize: 10, color: "var(--color-ink-3)", whiteSpace: "nowrap" }}>
              {new Date(event.timestamp).toLocaleTimeString("id-ID", {
                hour: "2-digit", minute: "2-digit",
              })}
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}

// ── Main page ─────────────────────────────────────────────────
export default function ProjectDetailPage() {
  const params = useParams();
  const id     = params.id as string;

  const [project,   setProject]   = useState<Project | null>(null);
  const [intel,     setIntel]     = useState<IntelligenceSummary | null>(null);
  const [loading,   setLoading]   = useState(true);
  const [advancing, setAdvancing] = useState(false);
  const [saving,    setSaving]    = useState(false);
  const [editMode,  setEditMode]  = useState(false);
  const [error,     setError]     = useState<string | null>(null);
  const [form,      setForm]      = useState<UpdateProjectPayload>({});
  const [reqView, setReqView] = useState<"checklist" | "workspace">("checklist");
  const [liveScore,    setLiveScore]    = useState<number>(0);
  const [todayDelta,   setTodayDelta]   = useState<number | null>(null);
  const [liveEvents,   setLiveEvents]   = useState<PulseEvent[]>([]);
  const [lastUpdated,  setLastUpdated]  = useState<string | null>(null);

  // Initialize liveScore from intel when it loads
  useEffect(() => {
    if (intel) setLiveScore(intel.readiness_score);
  }, [intel?.readiness_score]);

  // Pulse handler — called every 15 seconds when updates arrive
  const handlePulseUpdate = useCallback((data: PulseResponse) => {
    setLiveScore(data.readiness_score);
    if (data.readiness_delta_today !== null) {
      setTodayDelta(data.readiness_delta_today);
    }
    if (data.new_events.length > 0) {
      setLiveEvents(prev => [...data.new_events, ...prev].slice(0, 10));
      setLastUpdated(
        new Date().toLocaleTimeString("id-ID", { hour: "2-digit", minute: "2-digit" })
      );
    }
  }, []);

  // Start polling (only when project is loaded)
  useProjectPulse(project?.id ?? "", !!project, handlePulseUpdate);

  const loadProject = async () => {
    try {
      const [p, i] = await Promise.all([projectsApi.get(id), projectsApi.getIntelligence(id)]);
      setProject(p); setIntel(i); setForm(buildForm(p));
    } catch { setError("Gagal memuat proyek"); }
    finally { setLoading(false); }
  };

  useEffect(() => { loadProject(); }, [id]);

  function buildForm(p: Project): UpdateProjectPayload {
    return {
      name: p.name, location: p.location, description: p.description,
      total_units: p.total_units, target_budget: p.target_budget ?? "",
      start_date: p.start_date ?? "", end_date: p.end_date ?? "",
      ipr_status: p.ipr_status, ipr_date: p.ipr_date ?? "",
      amdal_status: p.amdal_status, amdal_date: p.amdal_date ?? "",
      pbg_status: p.pbg_status, pbg_date: p.pbg_date ?? "",
    };
  }

  const handleSave = async () => {
    if (!project) return;
    setSaving(true); setError(null);
    try {
      const updated = await projectsApi.update(project.id, form);
      setProject(updated); setForm(buildForm(updated));
      const i = await projectsApi.getIntelligence(project.id);
      setIntel(i); setEditMode(false);
    } catch { setError("Gagal menyimpan perubahan"); }
    finally { setSaving(false); }
  };

  const handleAdvance = async () => {
    if (!project) return;
    setAdvancing(true); setError(null);
    try {
      const updated = await projectsApi.advance(project.id);
      setProject(updated);
      const i = await projectsApi.getIntelligence(updated.id);
      setIntel(i);
    } catch (e: unknown) {
      setError(e instanceof Error ? e.message : "Gagal melanjutkan tahap");
    } finally { setAdvancing(false); }
  };

  const handleRequirementUpdated = (newIntel: IntelligenceSummary) => {
    setIntel(newIntel);
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

  const meta      = STAGE_META[project.stage];
  const riskMeta  = RISK_META[intel.risk_level];
  const trendMeta = TREND_META[intel.trend];
  const mandatory = intel.requirements.filter((r) => r.is_mandatory);
  const optional  = intel.requirements.filter((r) => !r.is_mandatory);

  // Sprint 4: count dependency-blocked requirements
  const depBlockedCount = intel.requirements.filter((r) => r.is_dependency_blocked).length;

  return (
    <div style={{ maxWidth: 960, margin: "0 auto" }}>

      {/* ── Back ── */}
      <Link href="/dashboard/projects" style={{ display: "inline-flex", alignItems: "center", gap: 5, fontSize: 12, color: "var(--color-ink-3)", textDecoration: "none", marginBottom: 20 }}>
        <ChevronLeft size={14} /> Kembali ke Semua Proyek
      </Link>

      {/* ── Header ── */}
      <div style={{ display: "flex", alignItems: "flex-start", justifyContent: "space-between", marginBottom: 24 }}>
        <div>
          <div style={{ display: "flex", alignItems: "center", gap: 8, marginBottom: 6, flexWrap: "wrap" }}>
            <span style={{ fontSize: 11, fontWeight: 700, color: meta.color, textTransform: "uppercase", letterSpacing: "0.08em" }}>{meta.label}</span>
            <span style={{ fontSize: 11, color: "var(--color-ink-3)" }}>— {meta.description}</span>
            {project.is_selling && (
              <span style={{ fontSize: 10, fontWeight: 600, padding: "2px 7px", borderRadius: 999, backgroundColor: "var(--color-success-light)", color: "var(--color-success)" }}>5A Aktif Jual</span>
            )}
            {project.is_constructing && (
              <span style={{ fontSize: 10, fontWeight: 600, padding: "2px 7px", borderRadius: 999, backgroundColor: "var(--color-accent-light)", color: "var(--color-accent)" }}>5B Aktif Bangun</span>
            )}
            {/* Sprint 4: show dep-blocked count in header */}
            {depBlockedCount > 0 && (
              <span style={{ fontSize: 10, fontWeight: 600, padding: "2px 7px", borderRadius: 999, backgroundColor: "rgba(14,13,11,0.06)", color: "var(--color-ink-3)", display: "flex", alignItems: "center", gap: 3 }}>
                <Lock size={9} /> {depBlockedCount} terkunci
              </span>
            )}
          </div>
          <h1 style={{ fontSize: 26, fontWeight: 700, color: "var(--color-ink)", margin: 0, marginBottom: 4 }}>{project.name}</h1>
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
          <ReadinessGauge score={intel.readiness_score} />
          <div style={{ flex: 1, display: "grid", gridTemplateColumns: "repeat(3, 1fr)", gap: 16 }}>
            <div style={{ textAlign: "center", padding: "12px", backgroundColor: intel.blocking_count > 0 ? "var(--color-danger-light)" : "var(--color-success-light)", borderRadius: 8 }}>
              <div style={{ fontSize: 24, fontWeight: 800, color: intel.blocking_count > 0 ? "var(--color-danger)" : "var(--color-success)" }}>{intel.blocking_count}</div>
              <div style={{ fontSize: 11, color: "var(--color-ink-3)", marginTop: 2 }}>Item Blokir</div>
              {/* Sprint 4: show dep-blocked count */}
              {depBlockedCount > 0 && (
                <div style={{ fontSize: 10, color: "var(--color-ink-3)", marginTop: 2, display: "flex", alignItems: "center", justifyContent: "center", gap: 3 }}>
                  <Lock size={9} /> {depBlockedCount} terkunci
                </div>
              )}
            </div>
            <div style={{ textAlign: "center", padding: "12px", backgroundColor: riskMeta.bg, borderRadius: 8 }}>
              <div style={{ fontSize: 18, fontWeight: 800, color: riskMeta.color }}>{riskMeta.label}</div>
              <div style={{ fontSize: 11, color: "var(--color-ink-3)", marginTop: 2 }}>Tingkat Risiko</div>
              {intel.risk_reasons && intel.risk_reasons.length > 0 && (
                <div style={{ fontSize: 12, fontWeight: 700, color: riskMeta.color, marginTop: 4 }}>
                  {intel.risk_score} / 100
                </div>
              )}
            </div>
            <div style={{ textAlign: "center", padding: "12px", backgroundColor: "var(--color-paper-2)", borderRadius: 8 }}>
              <div style={{ fontSize: 24, fontWeight: 800, color: trendMeta.color }}>{trendMeta.icon}</div>
              <div style={{ fontSize: 11, color: "var(--color-ink-3)", marginTop: 2 }}>
                {intel.trend === "improving" ? "Membaik" : intel.trend === "declining" ? "Menurun" : "Stabil"}
              </div>
            </div>
          </div>
          <div style={{ minWidth: 220 }}>
            {intel.next_action && (
              <div style={{ marginBottom: 12, padding: "10px 12px", backgroundColor: "var(--color-warning-light)", borderRadius: 8 }}>
                <div style={{ fontSize: 10, fontWeight: 700, color: "var(--color-warning)", textTransform: "uppercase", letterSpacing: "0.06em", marginBottom: 4 }}>Tindakan Berikutnya</div>
                <div style={{ fontSize: 13, fontWeight: 600, color: "var(--color-ink)" }}>{intel.next_action}</div>
              </div>
            )}
            <button onClick={handleAdvance} disabled={advancing || !intel.can_advance}
              className={intel.can_advance ? "btn-accent" : "btn-ghost"}
              style={{ width: "100%", display: "flex", alignItems: "center", justifyContent: "center", gap: 6, opacity: intel.can_advance ? 1 : 0.5 }}>
              {advancing ? <Loader2 size={14} style={{ animation: "spin 1s linear infinite" }} /> : <ArrowRight size={14} />}
              {intel.can_advance ? "Lanjutkan Tahap" : "Tahap Diblokir"}
            </button>
          </div>
        </div>
        {/* Sprint 5: Explainable readiness breakdown */}
        {intel.readiness_breakdown && (
          <ReadinessBreakdownPanel breakdown={intel.readiness_breakdown} />
        )}

        {/* Sprint 6: Risk explanation panel */}
        {intel.risk_factors && intel.risk_factors.length > 0 && (
          <RiskExplanationPanel intel={intel} />
        )}
      </div>

      {/* Sprint 17: Event Stream */}
        <EventStreamPanel events={liveEvents} lastUpdated={lastUpdated} />

      {/* Sprint 10: Readiness Trend + Key Progress */}
        <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 16, marginBottom: 16 }}>
        <ReadinessTrendPanel
          projectId={project.id}
          currentScore={intel.readiness_score}
          inlineData={intel.readiness_trend_data ?? []}
          liveScore={liveScore || intel.readiness_score}
          todayDelta={todayDelta}
        />
        {intel.key_progress && (
        <KeyProgressCard progress={intel.key_progress} />
        )}
      </div>

      {/* Sprint 13: Decision Engine */}
      <DecisionEnginePanel projectId={project.id} />

      {/* Sprint 14: Risk Forecast */}
      <RiskForecastPanel projectId={project.id} />

      {/* ── Alerts + Dimensions row ── */}
      {((intel.alerts && intel.alerts.length > 0) || intel.readiness_dimensions) && (
        <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 16, marginBottom: 16 }}>
          <div className="card">
            <div style={{ display: "flex", alignItems: "center", gap: 8, marginBottom: 16 }}>
              <Zap size={14} style={{ color: intel.alerts?.some((a) => a.level === "critical") ? "var(--color-danger)" : "var(--color-warning)" }} />
              <span style={{ fontSize: 13, fontWeight: 600, color: "var(--color-ink)" }}>Alerts Aktif</span>
              {intel.alerts && intel.alerts.length > 0 && (
                <span style={{ marginLeft: "auto", fontSize: 10, fontWeight: 700, padding: "2px 7px", borderRadius: 999, backgroundColor: intel.alerts.some((a) => a.level === "critical") ? "var(--color-danger)" : "var(--color-warning)", color: "white" }}>
                  {intel.alerts.length}
                </span>
              )}
            </div>
            <AlertsPanel alerts={intel.alerts ?? []} />
            <ActionChainPanel chain={intel.action_chain ?? null} />
            {intel.risk_reasons && intel.risk_reasons.length > 0 && (
              <div style={{ marginTop: 12, paddingTop: 12, borderTop: "1px solid rgba(14,13,11,0.06)" }}>
                <div style={{ fontSize: 10, fontWeight: 700, color: "var(--color-ink-3)", textTransform: "uppercase", letterSpacing: "0.06em", marginBottom: 6 }}>Alasan Risiko</div>
                {intel.risk_reasons.map((reason, i) => (
                  <div key={i} style={{ display: "flex", gap: 6, marginBottom: 4, fontSize: 11, color: "var(--color-ink)" }}>
                    <span style={{ color: "var(--color-danger)", flexShrink: 0 }}>⚠</span>{reason}
                  </div>
                ))}
              </div>
            )}
          </div>
          <div className="card">
            <div style={{ fontSize: 13, fontWeight: 600, color: "var(--color-ink)", marginBottom: 4 }}>Kesiapan per Dimensi</div>
            <div style={{ fontSize: 11, color: "var(--color-ink-3)", marginBottom: 16 }}>Breakdown readiness score tahap ini</div>
            <ReadinessDimensions dims={intel.readiness_dimensions} />
            <div style={{ marginTop: 16, paddingTop: 14, borderTop: "1px solid rgba(14,13,11,0.06)" }}>
              <div style={{ fontSize: 10, fontWeight: 700, color: "var(--color-ink-3)", textTransform: "uppercase", letterSpacing: "0.06em", marginBottom: 8 }}>Mode Paralel (5A/5B)</div>
              <ParallelStageToggles project={project} onUpdated={setProject} />
            </div>
          </div>
        </div>
      )}

      {/* ── Stage pipeline ── */}
      <div className="card" style={{ marginBottom: 16 }}>
        <div style={{ fontSize: 12, fontWeight: 600, color: "var(--color-ink)", marginBottom: 20 }}>Alur Tahap Proyek</div>
        <StagePipeline stage={project.stage} />
      </div>

      <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 16 }}>

        {/* Sprint 11: Dependency Graph */}
        <DependencyGraphPanel projectId={project.id} />

        {/* ── Requirements ── */}
        <div className="card" id="requirements-card">
          <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between", marginBottom: 4 }}>
        <div style={{ fontSize: 13, fontWeight: 600, color: "var(--color-ink)" }}>
         Checklist Tahap {meta.label}
          </div>
          {/* Sprint 10: view mode toggle */}
          <div style={{ display: "flex", gap: 4 }}>
            {(["checklist", "workspace"] as const).map((mode) => (
              <button
                key={mode}
                onClick={() => setReqView(mode)}
                style={{
                padding: "3px 10px", borderRadius: 4, border: "1px solid rgba(14,13,11,0.12)",
                fontSize: 10, fontWeight: 600, cursor: "pointer",
                backgroundColor: reqView === mode ? "var(--color-accent)" : "white",
                color:           reqView === mode ? "white" : "var(--color-ink-3)",
                transition: "all 0.15s",
                }}>
                {mode === "checklist" ? "📋 Checklist" : "📊 Workspace"}
              </button>
            ))}
          </div>
        </div>

          {/* Sprint 4: dependency legend */}
          {depBlockedCount > 0 && (
            <div style={{ display: "flex", alignItems: "center", gap: 6, marginBottom: 12, padding: "6px 10px", backgroundColor: "rgba(14,13,11,0.04)", borderRadius: 6 }}>
              <Lock size={11} style={{ color: "var(--color-ink-3)" }} />
              <span style={{ fontSize: 11, color: "var(--color-ink-3)" }}>
                {depBlockedCount} requirement terkunci — selesaikan prasyarat terlebih dahulu
              </span>
            </div>
          )}
          <div style={{ fontSize: 11, color: "var(--color-ink-3)", marginBottom: 12 }}>
            {intel.requirements.filter(r => r.status === "completed").length}/{intel.requirements.length} selesai
          </div>

          {reqView === "workspace" ? (
            <WorkspaceTable
              requirements={intel.requirements}
              projectId={project.id}
              onUpdated={handleRequirementUpdated}
            />
          ) : intel.requirements.length === 0 ? (
            <div style={{ fontSize: 12, color: "var(--color-ink-3)", fontStyle: "italic", textAlign: "center", padding: "24px 0" }}>
              Tidak ada checklist untuk tahap ini
            </div>
          ) : (
            <>
              {mandatory.length > 0 && (
                <>
                  <div style={{ fontSize: 10, fontWeight: 700, color: "var(--color-danger)", textTransform: "uppercase", letterSpacing: "0.06em", marginBottom: 8 }}>
                    ⚡ Wajib ({mandatory.filter(r => r.status === "completed").length}/{mandatory.length})
                  </div>
                  {mandatory.map((req) => (
                    <RequirementRow key={req.id} req={req} projectId={project.id} onUpdated={handleRequirementUpdated} />
                  ))}
                </>
              )}
              {optional.length > 0 && (
                <>
                  <div style={{ fontSize: 10, fontWeight: 600, color: "var(--color-ink-3)", textTransform: "uppercase", letterSpacing: "0.06em", marginTop: 12, marginBottom: 8 }}>
                    Opsional ({optional.filter(r => r.status === "completed").length}/{optional.length})
                  </div>
                  {optional.map((req) => (
                    <RequirementRow key={req.id} req={req} projectId={project.id} onUpdated={handleRequirementUpdated} />
                  ))}
                </>
              )}
            </>
          )}
        </div>

        {/* ── Project info / edit ── */}
        <div style={{ display: "flex", flexDirection: "column", gap: 16 }}>
          <div className="card">
            <div style={{ fontSize: 13, fontWeight: 600, color: "var(--color-ink)", marginBottom: 16 }}>Informasi Proyek</div>
            {editMode ? (
              <div style={{ display: "flex", flexDirection: "column", gap: 10 }}>
                {[
                  { label: "Nama Proyek",     key: "name",          type: "text"   },
                  { label: "Lokasi",          key: "location",      type: "text"   },
                  { label: "Total Unit",      key: "total_units",   type: "number" },
                  { label: "Target Anggaran", key: "target_budget", type: "text"   },
                  { label: "Tanggal Mulai",   key: "start_date",    type: "date"   },
                  { label: "Target Selesai",  key: "end_date",      type: "date"   },
                ].map((field) => (
                  <div key={field.key}>
                    <label style={{ display: "block", fontSize: 11, fontWeight: 500, color: "var(--color-ink-3)", marginBottom: 3 }}>{field.label}</label>
                    <input type={field.type} value={(form as Record<string, unknown>)[field.key] as string ?? ""}
                      onChange={(e) => setForm({ ...form, [field.key]: field.type === "number" ? Number(e.target.value) : e.target.value })}
                      style={{ width: "100%", padding: "7px 10px", border: "1px solid rgba(14,13,11,0.15)", borderRadius: 6, fontSize: 12, color: "var(--color-ink)", outline: "none", boxSizing: "border-box" }} />
                  </div>
                ))}
                <div>
                  <label style={{ display: "block", fontSize: 11, fontWeight: 500, color: "var(--color-ink-3)", marginBottom: 3 }}>Deskripsi</label>
                  <textarea value={form.description ?? ""} onChange={(e) => setForm({ ...form, description: e.target.value })} rows={3}
                    style={{ width: "100%", padding: "7px 10px", border: "1px solid rgba(14,13,11,0.15)", borderRadius: 6, fontSize: 12, color: "var(--color-ink)", outline: "none", resize: "vertical", boxSizing: "border-box", fontFamily: "inherit" }} />
                </div>
              </div>
            ) : (
              <div>
                {[
                  { label: "Total Unit",      value: String(project.total_units || "—"), icon: Home       },
                  { label: "Unit Terjual",    value: String(project.units_sold),          icon: TrendingUp },
                  { label: "Target Anggaran", value: project.target_budget ? `Rp ${Number(project.target_budget).toLocaleString("id-ID")}` : "—", icon: FileText },
                  { label: "Tanggal Mulai",   value: project.start_date ?? "—",           icon: Calendar   },
                  { label: "Target Selesai",  value: project.end_date   ?? "—",           icon: Calendar   },
                ].map((row) => (
                  <div key={row.label} style={{ display: "flex", alignItems: "center", justifyContent: "space-between", padding: "8px 0", borderBottom: "1px solid rgba(14,13,11,0.05)" }}>
                    <div style={{ display: "flex", alignItems: "center", gap: 6, fontSize: 12, color: "var(--color-ink-3)" }}>
                      <row.icon size={12} /> {row.label}
                    </div>
                    <div style={{ fontSize: 12, fontWeight: 500, color: "var(--color-ink)" }}>{row.value}</div>
                  </div>
                ))}
                {project.collection_efficiency && project.collection_efficiency.total_billed > 0 && (
                  <div style={{ marginTop: 10, padding: "10px 12px", backgroundColor: "var(--color-paper-2)", borderRadius: 8 }}>
                    <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: 6 }}>
                      <span style={{ fontSize: 11, color: "var(--color-ink-3)" }}>Efisiensi Penagihan</span>
                      <span style={{ fontSize: 11, fontWeight: 700, padding: "2px 8px", borderRadius: 999, color: project.collection_efficiency.status === "healthy" ? "var(--color-success)" : project.collection_efficiency.status === "attention" ? "var(--color-warning)" : "var(--color-danger)", backgroundColor: project.collection_efficiency.status === "healthy" ? "var(--color-success-light)" : project.collection_efficiency.status === "attention" ? "var(--color-warning-light)" : "var(--color-danger-light)" }}>
                        {project.collection_efficiency.efficiency_pct}% — {project.collection_efficiency.status_display}
                      </span>
                    </div>
                    {project.collection_efficiency.total_arrears > 0 && (
                      <div style={{ fontSize: 11, color: "var(--color-danger)" }}>Menunggak: Rp {project.collection_efficiency.total_arrears.toLocaleString("id-ID")}</div>
                    )}
                  </div>
                )}
              </div>
            )}
          </div>

          {["perizinan", "konstruksi", "penjualan", "serah_terima", "selesai"].includes(project.stage) && (
            <div className="card">
              <div style={{ fontSize: 13, fontWeight: 600, color: "var(--color-ink)", marginBottom: 16 }}>Status Perizinan</div>
              <div style={{ display: "flex", flexDirection: "column", gap: 10 }}>
                {[
                  { label: "IPR",           status: project.ipr_status,   date: project.ipr_date,   key_s: "ipr_status",   desc: "Izin Pemanfaatan Ruang"     },
                  { label: "AMDAL/UKL-UPL", status: project.amdal_status, date: project.amdal_date, key_s: "amdal_status", desc: "Kajian Lingkungan"           },
                  { label: "PBG ⚡",         status: project.pbg_status,   date: project.pbg_date,   key_s: "pbg_status",   desc: "Persetujuan Bangunan Gedung" },
                ].map((permit) => (
                  <div key={permit.label} style={{ display: "flex", alignItems: "center", justifyContent: "space-between", padding: "10px 12px", backgroundColor: "var(--color-paper-2)", borderRadius: 8 }}>
                    <div>
                      <div style={{ fontSize: 12, fontWeight: 600, color: "var(--color-ink)" }}>{permit.label}</div>
                      <div style={{ fontSize: 10, color: "var(--color-ink-3)" }}>{permit.desc}</div>
                      {permit.date && <div style={{ fontSize: 10, color: "var(--color-ink-3)", marginTop: 2 }}>{permit.date}</div>}
                    </div>
                    {editMode ? (
                      <select value={(form as Record<string, unknown>)[permit.key_s] as string ?? "belum"}
                        onChange={(e) => setForm({ ...form, [permit.key_s]: e.target.value })}
                        style={{ padding: "5px 8px", border: "1px solid rgba(14,13,11,0.15)", borderRadius: 6, fontSize: 11, backgroundColor: "white" }}>
                        <option value="belum">Belum Dimulai</option>
                        <option value="proses">Sedang Diproses</option>
                        <option value="approved">Disetujui</option>
                        <option value="rejected">Ditolak</option>
                      </select>
                    ) : <PermitBadge status={permit.status} />}
                  </div>
                ))}
              </div>
            </div>
          )}

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
      <ActivityTimelinePanel projectId={project.id} />
    </div>
  );
}
