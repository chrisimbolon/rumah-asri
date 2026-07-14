"use client";
// =============================================================================
// === frontend/app/dashboard/prospects/page.tsx ===
// =============================================================================
/**
 * CRM Foundation Sprint 3: minimal Prospect list.
 *
 * Deliberately small, per the CRM roadmap: a flat list, filterable by
 * status, a "Tandai Follow-up" action, and a "Konversi ke Booking"
 * action that hands off into the existing, already-built booking flow
 * on /dashboard/units. No dashboard, no charts, no analytics, no
 * leaderboard — those are explicitly parked, not this page wearing a
 * smaller name.
 *
 * One addition beyond the roadmap's two named actions: a lightweight
 * "Tandai Hilang" action, since without it a lead can never reach the
 * `hilang` status through the UI at all (only via admin) — trivial to
 * add since it's the same update endpoint, and it completes the status
 * vocabulary Sprint 1's model already defines.
 *
 * One deliberate omission: the "Tambah Prospect" form doesn't include
 * `assigned_to`. There's no existing endpoint on this page's reach that
 * lists developer/agent staff the way /api/organizations/buyers/ lists
 * buyers for the Units page — assignment stays admin/API-only until
 * that data source exists.
 */

import {
  Activity, CreateActivityPayload, CreateProspectPayload,
  Prospect, activitiesApi, prospectsApi,
} from "@/lib/api/crm";
import { Project, projectsApi } from "@/lib/api/projects";
import {
  CheckCircle2,
  Clock,
  Loader2,
  MessageSquareText,
  Phone,
  Plus,
  Search,
  UserCheck,
  UserX,
  Users,
  X,
  XCircle,
} from "lucide-react";
import { useRouter } from "next/navigation";
import { useEffect, useState } from "react";

// ── Date formatter — "2026-03-01" → "1 Mar 2026" ─────────────
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

// ── Status badge ──────────────────────────────────────────────
function StatusBadge({ status, display }: { status: Prospect["status"]; display: string }) {
  // Sprint 5 (CRM Foundation Phase B): expanded from 4 colors to 7.
  // follow_up/won/lost keep their original colors unchanged since
  // those stages carry the same meaning as before; the three new
  // in-between stages (qualified/site_visit/negotiation) get their
  // own shades so the pipeline reads as a visible progression, not
  // just "some are blue, some are grey."
  const map: Record<Prospect["status"], { color: string; bg: string }> = {
    lead:         { color: "var(--color-info)",    bg: "var(--color-info-light)"    },
    qualified:    { color: "var(--color-info)",    bg: "var(--color-info-light)"    },
    follow_up:    { color: "var(--color-warning)", bg: "var(--color-warning-light)" },
    site_visit:   { color: "var(--color-warning)", bg: "var(--color-warning-light)" },
    negotiation:  { color: "var(--color-accent)",  bg: "var(--color-accent-light)"  },
    won:          { color: "var(--color-success)", bg: "var(--color-success-light)" },
    lost:         { color: "var(--color-ink-3)",   bg: "var(--color-paper-2)"       },
  };
  const s = map[status] ?? map.lead;
  return (
    <span style={{ fontSize: 11, fontWeight: 600, padding: "3px 10px", borderRadius: 999, color: s.color, backgroundColor: s.bg }}>
      {display}
    </span>
  );
}

const inputStyle: React.CSSProperties = {
  width: "100%", padding: "8px 10px",
  border: "1px solid rgba(14,13,11,0.15)",
  borderRadius: 6, fontSize: 13,
  color: "var(--color-ink)", outline: "none",
  boxSizing: "border-box",
};

// ── Tambah Prospect Modal ────────────────────────────────────────
function AddProspectModal({
  projects,
  onClose,
  onCreated,
}: {
  projects:  Project[];
  onClose:   () => void;
  onCreated: (p: Prospect) => void;
}) {
  const [form, setForm] = useState<CreateProspectPayload>({
    name: "", phone: "", source: "", interested_project: null,
  });
  const [saving, setSaving] = useState(false);
  const [error,  setError]  = useState<string | null>(null);

  const handleSubmit = async () => {
    if (!form.name.trim())  { setError("Nama wajib diisi"); return; }
    if (!form.phone.trim()) { setError("Nomor telepon wajib diisi"); return; }
    setSaving(true);
    setError(null);
    try {
      const prospect = await prospectsApi.create({
        ...form,
        interested_project: form.interested_project || null,
      });
      onCreated(prospect);
    } catch (e: unknown) {
      const msg = (e as { response?: { data?: { errors?: Record<string, string[]> } } })
        ?.response?.data?.errors;
      setError(msg ? Object.values(msg).flat().join(", ") : "Gagal membuat prospect");
    } finally {
      setSaving(false);
    }
  };

  return (
    <div style={{ position: "fixed", inset: 0, zIndex: 100, backgroundColor: "rgba(14,13,11,0.4)", display: "flex", alignItems: "center", justifyContent: "center", padding: 16 }}>
      <div style={{ backgroundColor: "white", borderRadius: 12, width: "100%", maxWidth: 480, boxShadow: "0 20px 60px rgba(14,13,11,0.15)", overflow: "hidden" }}>

        <div style={{ padding: "20px 24px 16px", borderBottom: "1px solid rgba(14,13,11,0.06)", display: "flex", alignItems: "center", justifyContent: "space-between" }}>
          <div>
            <div style={{ display: "flex", alignItems: "center", gap: 8, marginBottom: 4 }}>
              <Users size={15} style={{ color: "var(--color-accent)" }} />
              <span style={{ fontSize: 11, fontWeight: 700, color: "var(--color-accent)", textTransform: "uppercase", letterSpacing: "0.08em" }}>Prospect Baru</span>
            </div>
            <h2 style={{ fontSize: 18, fontWeight: 600, color: "var(--color-ink)", margin: 0 }}>Tambah Prospect</h2>
          </div>
          <button onClick={onClose} style={{ padding: 6, borderRadius: 6, border: "none", backgroundColor: "transparent", cursor: "pointer", color: "var(--color-ink-3)" }}>
            <X size={18} />
          </button>
        </div>

        <div style={{ padding: "20px 24px" }}>
          {error && (
            <div style={{ marginBottom: 16, padding: "10px 14px", backgroundColor: "var(--color-danger-light)", borderRadius: 6, fontSize: 12, color: "var(--color-danger)" }}>
              {error}
            </div>
          )}

          <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 12, marginBottom: 14 }}>
            <div>
              <label style={{ display: "block", fontSize: 12, fontWeight: 500, color: "var(--color-ink)", marginBottom: 5 }}>
                Nama <span style={{ color: "var(--color-danger)" }}>*</span>
              </label>
              <input type="text" placeholder="Nama lengkap" value={form.name}
                onChange={(e) => setForm({ ...form, name: e.target.value })}
                style={inputStyle} />
            </div>
            <div>
              <label style={{ display: "block", fontSize: 12, fontWeight: 500, color: "var(--color-ink)", marginBottom: 5 }}>
                Telepon <span style={{ color: "var(--color-danger)" }}>*</span>
              </label>
              <input type="text" placeholder="08xxxxxxxxxx" value={form.phone}
                onChange={(e) => setForm({ ...form, phone: e.target.value })}
                style={inputStyle} />
            </div>
          </div>

          <div style={{ marginBottom: 14 }}>
            <label style={{ display: "block", fontSize: 12, fontWeight: 500, color: "var(--color-ink)", marginBottom: 5 }}>
              Sumber <span style={{ fontSize: 11, color: "var(--color-ink-3)", fontWeight: 400 }}>(opsional)</span>
            </label>
            <input type="text" placeholder="Referral, walk-in, WhatsApp, dst"
              value={form.source ?? ""}
              onChange={(e) => setForm({ ...form, source: e.target.value })}
              style={inputStyle} />
          </div>

          <div style={{ marginBottom: 20 }}>
            <label style={{ display: "block", fontSize: 12, fontWeight: 500, color: "var(--color-ink)", marginBottom: 5 }}>
              Proyek Diminati <span style={{ fontSize: 11, color: "var(--color-ink-3)", fontWeight: 400 }}>(opsional)</span>
            </label>
            <select value={form.interested_project ?? ""}
              onChange={(e) => setForm({ ...form, interested_project: e.target.value || null })}
              style={inputStyle}>
              <option value="">— Belum ditentukan —</option>
              {projects.map((p) => (
                <option key={p.id} value={p.id}>{p.name}</option>
              ))}
            </select>
          </div>

          <div style={{ display: "flex", gap: 10 }}>
            <button onClick={onClose} className="btn-ghost" style={{ flex: 1 }} disabled={saving}>Batal</button>
            <button onClick={handleSubmit} className="btn-accent" disabled={saving}
              style={{ flex: 2, display: "flex", alignItems: "center", justifyContent: "center", gap: 6 }}>
              {saving
                ? <><Loader2 size={14} style={{ animation: "spin 1s linear infinite" }} /> Menyimpan…</>
                : <><Users size={14} /> Tambah Prospect</>
              }
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}

// ── Tandai Follow-up Modal ───────────────────────────────────────
function FollowUpModal({
  prospect,
  onClose,
  onUpdated,
}: {
  prospect:  Prospect;
  onClose:   () => void;
  onUpdated: (p: Prospect) => void;
}) {
  const defaultDate = new Date(Date.now() + 3 * 86_400_000).toISOString().split("T")[0];
  const [date,  setDate]  = useState(prospect.next_followup_date ?? defaultDate);
  const [notes, setNotes] = useState(prospect.notes ?? "");
  const [saving, setSaving] = useState(false);
  const [error,  setError]  = useState<string | null>(null);

  const handleSubmit = async () => {
    setSaving(true);
    setError(null);
    try {
      const updated = await prospectsApi.update(prospect.id, {
        status: "follow_up",
        next_followup_date: date,
        notes,
      });
      onUpdated(updated);
    } catch {
      setError("Gagal memperbarui prospect");
    } finally {
      setSaving(false);
    }
  };

  return (
    <div style={{ position: "fixed", inset: 0, zIndex: 100, backgroundColor: "rgba(14,13,11,0.4)", display: "flex", alignItems: "center", justifyContent: "center", padding: 16 }}>
      <div style={{ backgroundColor: "white", borderRadius: 12, width: "100%", maxWidth: 420, boxShadow: "0 20px 60px rgba(14,13,11,0.15)", overflow: "hidden" }}>

        <div style={{ padding: "20px 24px 16px", borderBottom: "1px solid rgba(14,13,11,0.06)", display: "flex", alignItems: "center", justifyContent: "space-between" }}>
          <div>
            <div style={{ display: "flex", alignItems: "center", gap: 8, marginBottom: 4 }}>
              <Clock size={15} style={{ color: "var(--color-warning)" }} />
              <span style={{ fontSize: 11, fontWeight: 700, color: "var(--color-warning)", textTransform: "uppercase", letterSpacing: "0.08em" }}>Follow-up</span>
            </div>
            <h2 style={{ fontSize: 18, fontWeight: 600, color: "var(--color-ink)", margin: 0 }}>{prospect.name}</h2>
          </div>
          <button onClick={onClose} style={{ padding: 6, borderRadius: 6, border: "none", backgroundColor: "transparent", cursor: "pointer", color: "var(--color-ink-3)" }}>
            <X size={18} />
          </button>
        </div>

        <div style={{ padding: "20px 24px" }}>
          {error && (
            <div style={{ marginBottom: 16, padding: "10px 14px", backgroundColor: "var(--color-danger-light)", borderRadius: 6, fontSize: 12, color: "var(--color-danger)" }}>
              {error}
            </div>
          )}

          <div style={{ marginBottom: 14 }}>
            <label style={{ display: "block", fontSize: 12, fontWeight: 500, color: "var(--color-ink)", marginBottom: 5 }}>
              Tanggal Follow-up Berikutnya
            </label>
            <input type="date" value={date}
              onChange={(e) => setDate(e.target.value)}
              style={inputStyle} />
          </div>

          <div style={{ marginBottom: 20 }}>
            <label style={{ display: "block", fontSize: 12, fontWeight: 500, color: "var(--color-ink)", marginBottom: 5 }}>
              Catatan <span style={{ fontSize: 11, color: "var(--color-ink-3)", fontWeight: 400 }}>(opsional)</span>
            </label>
            <textarea rows={3}
              placeholder="Hasil percakapan, minat spesifik, dst..."
              value={notes}
              onChange={(e) => setNotes(e.target.value)}
              style={{ ...inputStyle, resize: "vertical", fontFamily: "inherit" }} />
          </div>

          <div style={{ display: "flex", gap: 10 }}>
            <button onClick={onClose} className="btn-ghost" style={{ flex: 1 }} disabled={saving}>Batal</button>
            <button onClick={handleSubmit} className="btn-accent" disabled={saving}
              style={{ flex: 2, display: "flex", alignItems: "center", justifyContent: "center", gap: 6 }}>
              {saving
                ? <><Loader2 size={14} style={{ animation: "spin 1s linear infinite" }} /> Menyimpan…</>
                : <><Clock size={14} /> Tandai Follow-up</>
              }
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}

// ── Activity type → icon/label, shared between the modal's history
//    list and its own quick-add form ──────────────────────────────
const ACTIVITY_TYPE_META: Record<Activity["activity_type"], { icon: typeof Phone; label: string }> = {
  call:      { icon: Phone,             label: "Telepon"   },
  whatsapp:  { icon: MessageSquareText, label: "WhatsApp"  },
  meeting:   { icon: Users,             label: "Pertemuan" },
  note:      { icon: MessageSquareText, label: "Catatan"   },
};

// ── Activity Timeline Modal ───────────────────────────────────────
// Sprint 4 (CRM Foundation Phase B): follow-up history. Deliberately a
// modal rather than a full detail page — a dedicated Prospect detail
// route isn't justified until Sprint 6 (Site Visit) needs one anyway,
// per the roadmap's own note on this sprint.
function ActivityModal({
  prospect,
  onClose,
}: {
  prospect: Prospect;
  onClose:  () => void;
}) {
  const [activities, setActivities] = useState<Activity[]>([]);
  const [loading,    setLoading]    = useState(true);
  const [error,      setError]      = useState<string | null>(null);

  const [newType,  setNewType]  = useState<Activity["activity_type"]>("call");
  const [newNotes, setNewNotes] = useState("");
  const [saving,   setSaving]   = useState(false);

  useEffect(() => {
    activitiesApi.list(prospect.id)
      .then(setActivities)
      .catch(() => setError("Gagal memuat riwayat aktivitas"))
      .finally(() => setLoading(false));
  }, [prospect.id]);

  const handleAdd = async () => {
    setSaving(true);
    setError(null);
    try {
      const payload: CreateActivityPayload = { activity_type: newType, notes: newNotes };
      const created = await activitiesApi.create(prospect.id, payload);
      setActivities((prev) => [created, ...prev]);
      setNewNotes("");
    } catch {
      setError("Gagal mencatat aktivitas");
    } finally {
      setSaving(false);
    }
  };

  return (
    <div style={{ position: "fixed", inset: 0, zIndex: 100, backgroundColor: "rgba(14,13,11,0.4)", display: "flex", alignItems: "center", justifyContent: "center", padding: 16 }}>
      <div style={{ backgroundColor: "white", borderRadius: 12, width: "100%", maxWidth: 480, maxHeight: "85vh", display: "flex", flexDirection: "column", boxShadow: "0 20px 60px rgba(14,13,11,0.15)", overflow: "hidden" }}>

        <div style={{ padding: "20px 24px 16px", borderBottom: "1px solid rgba(14,13,11,0.06)", display: "flex", alignItems: "center", justifyContent: "space-between", flexShrink: 0 }}>
          <div>
            <div style={{ display: "flex", alignItems: "center", gap: 8, marginBottom: 4 }}>
              <MessageSquareText size={15} style={{ color: "var(--color-accent)" }} />
              <span style={{ fontSize: 11, fontWeight: 700, color: "var(--color-accent)", textTransform: "uppercase", letterSpacing: "0.08em" }}>Riwayat Aktivitas</span>
            </div>
            <h2 style={{ fontSize: 18, fontWeight: 600, color: "var(--color-ink)", margin: 0 }}>{prospect.name}</h2>
          </div>
          <button onClick={onClose} style={{ padding: 6, borderRadius: 6, border: "none", backgroundColor: "transparent", cursor: "pointer", color: "var(--color-ink-3)" }}>
            <X size={18} />
          </button>
        </div>

        {/* ── Quick-add form ── */}
        <div style={{ padding: "16px 24px", borderBottom: "1px solid rgba(14,13,11,0.06)", flexShrink: 0 }}>
          {error && (
            <div style={{ marginBottom: 10, padding: "8px 12px", backgroundColor: "var(--color-danger-light)", borderRadius: 6, fontSize: 12, color: "var(--color-danger)" }}>
              {error}
            </div>
          )}
          <div style={{ display: "flex", gap: 8, marginBottom: 8 }}>
            {(Object.keys(ACTIVITY_TYPE_META) as Activity["activity_type"][]).map((type) => {
              const meta = ACTIVITY_TYPE_META[type];
              const active = newType === type;
              return (
                <button key={type} onClick={() => setNewType(type)}
                  style={{ flex: 1, display: "flex", flexDirection: "column", alignItems: "center", gap: 3, padding: "8px 4px", borderRadius: 6, border: active ? "1px solid var(--color-accent)" : "1px solid rgba(14,13,11,0.1)", backgroundColor: active ? "var(--color-accent-light)" : "transparent", cursor: "pointer" }}
                >
                  <meta.icon size={14} style={{ color: active ? "var(--color-accent)" : "var(--color-ink-3)" }} />
                  <span style={{ fontSize: 10, color: active ? "var(--color-accent)" : "var(--color-ink-3)", fontWeight: active ? 600 : 400 }}>{meta.label}</span>
                </button>
              );
            })}
          </div>
          <div style={{ display: "flex", gap: 8 }}>
            <input
              type="text"
              placeholder="Catatan singkat tentang aktivitas ini..."
              value={newNotes}
              onChange={(e) => setNewNotes(e.target.value)}
              onKeyDown={(e) => { if (e.key === "Enter" && newNotes.trim() && !saving) handleAdd(); }}
              style={{ flex: 1, padding: "8px 10px", border: "1px solid rgba(14,13,11,0.15)", borderRadius: 6, fontSize: 12, outline: "none" }}
            />
            <button
              onClick={handleAdd}
              disabled={saving || !newNotes.trim()}
              className="btn-accent btn-sm"
              style={{ display: "flex", alignItems: "center", gap: 4, opacity: (!newNotes.trim() || saving) ? 0.5 : 1 }}
            >
              {saving ? <Loader2 size={13} style={{ animation: "spin 1s linear infinite" }} /> : <Plus size={13} />}
              Catat
            </button>
          </div>
        </div>

        {/* ── Timeline ── */}
        <div style={{ flex: 1, overflowY: "auto", padding: "16px 24px" }}>
          {loading ? (
            <div style={{ display: "flex", alignItems: "center", justifyContent: "center", padding: 30, gap: 8, color: "var(--color-ink-3)" }}>
              <Loader2 size={16} style={{ animation: "spin 1s linear infinite" }} />
              <span style={{ fontSize: 12 }}>Memuat riwayat…</span>
            </div>
          ) : activities.length === 0 ? (
            <div style={{ textAlign: "center", padding: 30, color: "var(--color-ink-3)", fontSize: 12 }}>
              Belum ada aktivitas tercatat untuk prospect ini.
            </div>
          ) : (
            <div style={{ display: "flex", flexDirection: "column", gap: 14 }}>
              {activities.map((a) => {
                const meta = ACTIVITY_TYPE_META[a.activity_type];
                return (
                  <div key={a.id} style={{ display: "flex", gap: 10 }}>
                    <div style={{ width: 26, height: 26, borderRadius: "50%", backgroundColor: "var(--color-accent-light)", display: "flex", alignItems: "center", justifyContent: "center", flexShrink: 0 }}>
                      <meta.icon size={12} style={{ color: "var(--color-accent)" }} />
                    </div>
                    <div style={{ flex: 1, minWidth: 0 }}>
                      <div style={{ display: "flex", alignItems: "baseline", gap: 6, flexWrap: "wrap" }}>
                        <span style={{ fontSize: 12, fontWeight: 600, color: "var(--color-ink)" }}>{meta.label}</span>
                        <span style={{ fontSize: 11, color: "var(--color-ink-3)" }}>
                          {new Date(a.created_at).toLocaleString("id-ID", { day: "numeric", month: "short", hour: "2-digit", minute: "2-digit" })}
                        </span>
                        {a.created_by_name && (
                          <span style={{ fontSize: 11, color: "var(--color-ink-3)" }}>· {a.created_by_name}</span>
                        )}
                      </div>
                      {a.notes && (
                        <div style={{ fontSize: 12, color: "var(--color-ink)", marginTop: 2 }}>{a.notes}</div>
                      )}
                    </div>
                  </div>
                );
              })}
            </div>
          )}
        </div>
      </div>
    </div>
  );
}

// ── Status tabs ───────────────────────────────────────────────
// Sprint 5 (CRM Foundation Phase B): expanded from 4 to 7, in
// pipeline order — Lead through Won, with Lost last since it's an
// exit from the pipeline rather than a stage within it.
const STATUS_TABS = [
  { key: "semua",       label: "Semua"       },
  { key: "lead",        label: "Lead"        },
  { key: "qualified",   label: "Qualified"   },
  { key: "follow_up",   label: "Follow Up"   },
  { key: "site_visit",  label: "Site Visit"  },
  { key: "negotiation", label: "Negotiation" },
  { key: "won",         label: "Won"         },
  { key: "lost",        label: "Lost"        },
];

// ─────────────────────────────────────────────────────────────
export default function ProspectsPage() {
  const router = useRouter();

  const [prospects, setProspects] = useState<Prospect[]>([]);
  const [projects,  setProjects]  = useState<Project[]>([]);
  const [loading,   setLoading]   = useState(true);
  const [error,     setError]     = useState<string | null>(null);
  const [activeTab, setActiveTab] = useState("semua");
  const [search,    setSearch]    = useState("");
  const [showAdd,   setShowAdd]   = useState(false);
  const [followUpProspect, setFollowUpProspect] = useState<Prospect | null>(null);
  const [activityProspect, setActivityProspect] = useState<Prospect | null>(null);
  const [losingId, setLosingId] = useState<string | null>(null);

  useEffect(() => {
    Promise.all([
      prospectsApi.list(),
      projectsApi.list(),
    ])
      .then(([p, proj]) => { setProspects(p); setProjects(proj); })
      .catch(() => setError("Gagal memuat data prospect"))
      .finally(() => setLoading(false));
  }, []);

  const handleCreated = (prospect: Prospect) => {
    setProspects((prev) => [prospect, ...prev]);
    setShowAdd(false);
  };

  const handleFollowUpUpdated = (updated: Prospect) => {
    setProspects((prev) => prev.map((p) => p.id === updated.id ? updated : p));
    setFollowUpProspect(null);
  };

  const handleMarkLost = async (prospect: Prospect) => {
    if (!confirm(`Tandai ${prospect.name} sebagai hilang?`)) return;
    setLosingId(prospect.id);
    try {
      // Sprint 5 (CRM Foundation Phase B): HILANG renamed LOST.
      const updated = await prospectsApi.update(prospect.id, { status: "lost" });
      setProspects((prev) => prev.map((p) => p.id === updated.id ? updated : p));
    } catch {
      alert("Gagal memperbarui status prospect");
    } finally {
      setLosingId(null);
    }
  };

  // Sprint 3 (CRM Foundation): the actual hand-off. Navigates to the
  // existing Units page with the prospect's identity and (if known)
  // their interested project riding in the query string — Sprint 2's
  // BookingModal on that page reads it and threads prospect_id through
  // to the real booking flow. No booking logic duplicated here.
  const handleConvert = (prospect: Prospect) => {
    const params = new URLSearchParams({
      prospect: prospect.id,
      prospect_name: prospect.name,
    });
    if (prospect.interested_project) params.set("project", prospect.interested_project);
    router.push(`/dashboard/units?${params.toString()}`);
  };

  if (loading) {
    return (
      <div style={{ display: "flex", alignItems: "center", justifyContent: "center", height: 300, gap: 10, color: "var(--color-ink-3)" }}>
        <Loader2 size={18} style={{ animation: "spin 1s linear infinite" }} />
        <span style={{ fontSize: 13 }}>Memuat prospect…</span>
      </div>
    );
  }

  if (error) {
    return <div style={{ padding: 24, textAlign: "center", color: "var(--color-danger)", fontSize: 13 }}>{error}</div>;
  }

  const filtered = prospects
    .filter((p) => activeTab === "semua" || p.status === activeTab)
    .filter((p) =>
      !search ||
      p.name.toLowerCase().includes(search.toLowerCase()) ||
      p.phone.includes(search)
    );

  return (
    <div style={{ maxWidth: 1100, margin: "0 auto" }}>

      {/* ── Modals ── */}
      {showAdd && (
        <AddProspectModal
          projects={projects}
          onClose={() => setShowAdd(false)}
          onCreated={handleCreated}
        />
      )}
      {followUpProspect && (
        <FollowUpModal
          prospect={followUpProspect}
          onClose={() => setFollowUpProspect(null)}
          onUpdated={handleFollowUpUpdated}
        />
      )}
      {activityProspect && (
        <ActivityModal
          prospect={activityProspect}
          onClose={() => setActivityProspect(null)}
        />
      )}

      {/* ── Page header ── */}
      <div className="page-header" style={{ display: "flex", alignItems: "flex-start", justifyContent: "space-between" }}>
        <div>
          <h1 className="page-title">Prospect</h1>
          <p className="page-subtitle">{prospects.length} lead terdaftar</p>
        </div>
        <button
          className="btn-accent"
          style={{ flexShrink: 0, display: "flex", alignItems: "center", gap: 6 }}
          onClick={() => setShowAdd(true)}
        >
          <Plus size={15} /> Tambah Prospect
        </button>
      </div>

      {/* ── Search ── */}
      <div style={{ position: "relative", marginBottom: 16, maxWidth: 320 }}>
        <Search size={14} style={{ position: "absolute", left: 12, top: "50%", transform: "translateY(-50%)", color: "var(--color-ink-3)" }} />
        <input
          type="text"
          placeholder="Cari nama atau telepon..."
          value={search}
          onChange={(e) => setSearch(e.target.value)}
          style={{ ...inputStyle, paddingLeft: 34 }}
        />
      </div>

      {/* ── Filter tabs + table ── */}
      <div className="card" style={{ padding: 0, overflow: "hidden" }}>

        <div style={{ display: "flex", padding: "0 16px", borderBottom: "1px solid rgba(14,13,11,0.08)" }}>
          {STATUS_TABS.map((tab) => {
            const count = tab.key === "semua" ? prospects.length : prospects.filter((p) => p.status === tab.key).length;
            const isActive = activeTab === tab.key;
            return (
              <button key={tab.key} onClick={() => setActiveTab(tab.key)}
                style={{ padding: "14px 16px", fontSize: 13, fontWeight: isActive ? 600 : 400, color: isActive ? "var(--color-accent)" : "var(--color-ink-3)", backgroundColor: "transparent", border: "none", borderBottom: isActive ? "2px solid var(--color-accent)" : "2px solid transparent", cursor: "pointer", display: "flex", alignItems: "center", gap: 6, transition: "all 0.15s", marginBottom: -1 }}
              >
                {tab.label}
                {count > 0 && (
                  <span style={{ fontSize: 10, fontWeight: 600, backgroundColor: isActive ? "var(--color-accent-light)" : "var(--color-paper-2)", color: isActive ? "var(--color-accent)" : "var(--color-ink-3)", padding: "1px 6px", borderRadius: 999 }}>
                    {count}
                  </span>
                )}
              </button>
            );
          })}
        </div>

        <table className="data-table">
          <thead>
            <tr>
              <th>Nama</th>
              <th>Telepon</th>
              <th>Sumber</th>
              <th>Proyek Diminati</th>
              <th>Status</th>
              <th>Follow-up Berikutnya</th>
              <th>Aksi</th>
            </tr>
          </thead>
          <tbody>
            {filtered.map((p) => (
              <tr key={p.id}>
                <td>
                  <div style={{ display: "flex", alignItems: "center", gap: 8 }}>
                    <div style={{ width: 28, height: 28, borderRadius: "50%", backgroundColor: "var(--color-accent-light)", display: "flex", alignItems: "center", justifyContent: "center", fontSize: 10, fontWeight: 700, color: "var(--color-accent)", flexShrink: 0 }}>
                      {p.name.split(" ").map((n) => n[0]).join("").slice(0, 2)}
                    </div>
                    <span style={{ fontSize: 13, fontWeight: 500 }}>{p.name}</span>
                  </div>
                </td>
                <td style={{ fontSize: 12, color: "var(--color-ink-3)" }}>{p.phone}</td>
                <td style={{ fontSize: 12, color: "var(--color-ink-3)" }}>{p.source || "—"}</td>
                <td>{p.project_name
                  ? <span className="badge badge-blue">{p.project_name}</span>
                  : <span style={{ fontSize: 12, color: "var(--color-ink-3)" }}>—</span>}
                </td>
                <td><StatusBadge status={p.status} display={p.status_display} /></td>
                <td>
                  <div style={{ display: "flex", alignItems: "center", gap: 5, fontSize: 12, color: "var(--color-ink-3)" }}>
                    <Clock size={12} />
                    {formatDate(p.next_followup_date)}
                  </div>
                </td>
                <td>
                  <div style={{ display: "flex", gap: 6, flexWrap: "wrap" }}>
                    {/* Sprint 4: history matters regardless of pipeline
                        status — a won or lost lead's activity trail is
                        still worth reading, so this button isn't gated
                        by status like the three below it. */}
                    <button
                      className="btn-ghost btn-sm"
                      onClick={() => setActivityProspect(p)}
                      style={{ display: "inline-flex", alignItems: "center", gap: 4, fontSize: 11 }}
                    >
                      <MessageSquareText size={11} /> Riwayat
                    </button>
                    {/* Sprint 5 (CRM Foundation Phase B): KONVERSI/HILANG renamed WON/LOST. */}
                    {p.status !== "won" && p.status !== "lost" && (
                      <>
                        <button
                          className="btn-ghost btn-sm"
                          onClick={() => setFollowUpProspect(p)}
                          style={{ display: "inline-flex", alignItems: "center", gap: 4, fontSize: 11 }}
                        >
                          <Clock size={11} /> Follow-up
                        </button>
                        <button
                          className="btn-accent btn-sm"
                          onClick={() => handleConvert(p)}
                          style={{ display: "inline-flex", alignItems: "center", gap: 4, fontSize: 11 }}
                        >
                          <UserCheck size={11} /> Konversi
                        </button>
                        <button
                          className="btn-ghost btn-sm"
                          disabled={losingId === p.id}
                          onClick={() => handleMarkLost(p)}
                          style={{ display: "inline-flex", alignItems: "center", gap: 4, fontSize: 11, color: "var(--color-danger)" }}
                        >
                          {losingId === p.id
                            ? <Loader2 size={11} style={{ animation: "spin 1s linear infinite" }} />
                            : <UserX size={11} />}
                          Hilang
                        </button>
                      </>
                    )}
                    {p.status === "won" && (
                      <span style={{ fontSize: 12, color: "var(--color-success)", display: "inline-flex", alignItems: "center", gap: 4 }}>
                        <CheckCircle2 size={12} /> Sudah terkonversi
                      </span>
                    )}
                    {p.status === "lost" && (
                      <span style={{ fontSize: 12, color: "var(--color-ink-3)", display: "inline-flex", alignItems: "center", gap: 4 }}>
                        <XCircle size={12} /> Lead hilang
                      </span>
                    )}
                  </div>
                </td>
              </tr>
            ))}
            {filtered.length === 0 && (
              <tr>
                <td colSpan={7} style={{ textAlign: "center", padding: 40, color: "var(--color-ink-3)", fontSize: 13 }}>
                  Tidak ada prospect untuk filter ini
                </td>
              </tr>
            )}
          </tbody>
        </table>

        <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between", padding: "12px 16px", borderTop: "1px solid rgba(14,13,11,0.06)", backgroundColor: "var(--color-paper)" }}>
          <span style={{ fontSize: 12, color: "var(--color-ink-3)" }}>
            Menampilkan {filtered.length} dari {prospects.length} prospect
          </span>
        </div>
      </div>
    </div>
  );
}
