"use client";
// =============================================================================
// === frontend/app/dashboard/units/page.tsx ===
// =============================================================================
/**
 * Sprint 6: Tambah Unit modal + Booking modal added.
 * Unit status now includes "dipesan" (booked/pre-sales).
 * Sprint 23 and Sprint 24 are implemented here
 */

import { Project, projectsApi } from "@/lib/api/projects";
import {
  Booking, BookingPayload, CreateUnitPayload,
  UNIT_TYPE_OPTIONS, Unit, unitsApi,
} from "@/lib/api/units";
import { rupiah, warnaProgres } from "@/lib/mock-data";
import {
  CheckCircle2,
  FileText, Home, Loader2, Plus,
  Search, TrendingUp, Users, X
} from "lucide-react";
import { useEffect, useState } from "react";

// ── Sprint 22: legal forward transitions, mirroring Unit.VALID_TRANSITIONS
// on the backend exactly. "tersedia→dipesan" and "dipesan→tersedia" are
// already handled by the existing Booking/Cancel flow below — this map
// only covers the three states that had ZERO UI at all until now:
// dipesan→proses→terjual→serah_terima. Deliberately a fixed map, not a
// free-form status dropdown — the UI should only ever be ABLE to offer
// the one legal next step, not send a request the backend guard would
// reject anyway.
const NEXT_STATUS: Partial<Record<Unit["status"], { next: Unit["status"]; label: string }>> = {
  dipesan: { next: "proses",       label: "Mulai Proses" },
  proses:  { next: "terjual",      label: "Tandai Terjual" },
  terjual: { next: "serah_terima", label: "Serah Terima" },
};

// ── Sprint 23: booking expiry countdown ────────────────────────
// Only meaningful for a still-ACTIVE booking with a real deadline —
// a converted/cancelled/expired booking has nothing left to count down. 
// Color escalates as the deadline gets close, matching the
// same "quiet until it matters" spirit as the risk-score pulses.
function bookingCountdown(booking: Booking): { label: string; color: string } | null {
  if (booking.status !== "active" || !booking.expires_at) return null;

  const msLeft   = new Date(booking.expires_at).getTime() - Date.now();
  const daysLeft = Math.ceil(msLeft / 86_400_000);

  if (daysLeft <= 0) return { label: "⚠️ Kedaluwarsa",        color: "var(--color-danger)"  };
  if (daysLeft <= 1) return { label: "⚠️ Kedaluwarsa besok",  color: "var(--color-danger)"  };
  if (daysLeft <= 3) return { label: `⏳ ${daysLeft} hari lagi`, color: "var(--color-warning)" };
  return                    { label: `⏳ ${daysLeft} hari lagi`, color: "var(--color-ink-3)"   };
}

// ── Sprint 24: KPR status color, read-only display on this page —
// the actual editable control lives on the Data Pembeli page, so
// this table doesn't need duplicate mutation logic.
function kprStatusColor(kprStatus: Booking["kpr_status"]): string {
  switch (kprStatus) {
    case "akad":      return "var(--color-success)";
    case "disetujui": return "var(--color-accent)";
    case "diajukan":  return "var(--color-warning)";
    default:          return "var(--color-ink-3)";
  }
}

// ── Status badge ──────────────────────────────────────────────
function StatusBadge({ status, display }: { status: Unit["status"]; display: string }) {
  const map: Record<Unit["status"], { color: string; bg: string }> = {
    tersedia:    { color: "var(--color-info)",    bg: "var(--color-info-light)"    },
    dipesan:     { color: "var(--color-warning)", bg: "var(--color-warning-light)" },
    proses:      { color: "var(--color-accent)",  bg: "var(--color-accent-light)"  },
    terjual:     { color: "var(--color-success)", bg: "var(--color-success-light)" },
    serah_terima:{ color: "#b8860b",              bg: "#fef9e7"                    },
  };
  const s = map[status] ?? map.tersedia;
  return (
    <span style={{ fontSize: 11, fontWeight: 600, padding: "3px 10px", borderRadius: 999, color: s.color, backgroundColor: s.bg }}>
      {display}
    </span>
  );
}

// ── Tambah Unit Modal ─────────────────────────────────────────
function AddUnitModal({
  projects,
  onClose,
  onCreated,
}: {
  projects:  Project[];
  onClose:   () => void;
  onCreated: (u: Unit) => void;
}) {
  const [form, setForm] = useState<CreateUnitPayload>({
    project:       projects[0]?.id ?? "",
    unit_number:   "",
    unit_type:     "Tipe 45",
    land_area:     72,
    building_area: 45,
    price:         0,
  });
  const [saving, setSaving] = useState(false);
  const [error,  setError]  = useState<string | null>(null);

  const handleSubmit = async () => {
    if (!form.project)     { setError("Pilih proyek"); return; }
    if (!form.unit_number) { setError("Nomor unit wajib diisi"); return; }
    if (!form.price || form.price <= 0) { setError("Harga wajib diisi"); return; }
    setSaving(true);
    setError(null);
    try {
      const unit = await unitsApi.create(form);
      onCreated(unit);
    } catch (e: unknown) {
      const msg = (e as { response?: { data?: { errors?: Record<string, string[]> } } })
        ?.response?.data?.errors;
      setError(msg ? Object.values(msg).flat().join(", ") : "Gagal membuat unit");
    } finally {
      setSaving(false);
    }
  };

  const inputStyle: React.CSSProperties = {
    width: "100%", padding: "8px 10px",
    border: "1px solid rgba(14,13,11,0.15)",
    borderRadius: 6, fontSize: 13,
    color: "var(--color-ink)", outline: "none",
    boxSizing: "border-box",
  };

  return (
    <div style={{ position: "fixed", inset: 0, zIndex: 100, backgroundColor: "rgba(14,13,11,0.4)", display: "flex", alignItems: "center", justifyContent: "center", padding: 16 }}>
      <div style={{ backgroundColor: "white", borderRadius: 12, width: "100%", maxWidth: 520, boxShadow: "0 20px 60px rgba(14,13,11,0.15)", overflow: "hidden", maxHeight: "90vh", overflowY: "auto" }}>

        {/* Header */}
        <div style={{ padding: "20px 24px 16px", borderBottom: "1px solid rgba(14,13,11,0.06)", display: "flex", alignItems: "center", justifyContent: "space-between", position: "sticky", top: 0, backgroundColor: "white", zIndex: 1 }}>
          <div>
            <div style={{ display: "flex", alignItems: "center", gap: 8, marginBottom: 4 }}>
              <Home size={15} style={{ color: "var(--color-accent)" }} />
              <span style={{ fontSize: 11, fontWeight: 700, color: "var(--color-accent)", textTransform: "uppercase", letterSpacing: "0.08em" }}>Unit Baru</span>
            </div>
            <h2 style={{ fontSize: 18, fontWeight: 600, color: "var(--color-ink)", margin: 0 }}>Tambah Unit</h2>
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

          {/* Proyek */}
          <div style={{ marginBottom: 14 }}>
            <label style={{ display: "block", fontSize: 12, fontWeight: 500, color: "var(--color-ink)", marginBottom: 5 }}>
              Proyek <span style={{ color: "var(--color-danger)" }}>*</span>
            </label>
            <select value={form.project} onChange={(e) => setForm({ ...form, project: e.target.value })} style={inputStyle}>
              <option value="">— Pilih Proyek —</option>
              {projects.map((p) => (
                <option key={p.id} value={p.id}>{p.name}</option>
              ))}
            </select>
          </div>

          {/* Nomor Unit + Tipe */}
          <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 12, marginBottom: 14 }}>
            <div>
              <label style={{ display: "block", fontSize: 12, fontWeight: 500, color: "var(--color-ink)", marginBottom: 5 }}>
                Nomor Unit <span style={{ color: "var(--color-danger)" }}>*</span>
              </label>
              <input type="text" placeholder="contoh: A-01" value={form.unit_number}
                onChange={(e) => setForm({ ...form, unit_number: e.target.value })}
                style={inputStyle} />
            </div>
            <div>
              <label style={{ display: "block", fontSize: 12, fontWeight: 500, color: "var(--color-ink)", marginBottom: 5 }}>Tipe Unit</label>
              <select value={form.unit_type} onChange={(e) => setForm({ ...form, unit_type: e.target.value })} style={inputStyle}>
                {UNIT_TYPE_OPTIONS.map((t) => <option key={t} value={t}>{t}</option>)}
              </select>
            </div>
          </div>

          {/* Luas Tanah + Luas Bangunan */}
          <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 12, marginBottom: 14 }}>
            <div>
              <label style={{ display: "block", fontSize: 12, fontWeight: 500, color: "var(--color-ink)", marginBottom: 5 }}>Luas Tanah (m²)</label>
              <input type="number" value={form.land_area}
                onChange={(e) => setForm({ ...form, land_area: Number(e.target.value) })}
                style={inputStyle} />
            </div>
            <div>
              <label style={{ display: "block", fontSize: 12, fontWeight: 500, color: "var(--color-ink)", marginBottom: 5 }}>Luas Bangunan (m²)</label>
              <input type="number" value={form.building_area}
                onChange={(e) => setForm({ ...form, building_area: Number(e.target.value) })}
                style={inputStyle} />
            </div>
          </div>

          {/* Harga */}
          <div style={{ marginBottom: 14 }}>
            <label style={{ display: "block", fontSize: 12, fontWeight: 500, color: "var(--color-ink)", marginBottom: 5 }}>
              Harga (IDR) <span style={{ color: "var(--color-danger)" }}>*</span>
            </label>
            <input type="number" placeholder="contoh: 850000000"
              value={form.price || ""}
              onChange={(e) => setForm({ ...form, price: Number(e.target.value) })}
              style={inputStyle} />
            {form.price > 0 && (
              <div style={{ fontSize: 11, color: "var(--color-ink-3)", marginTop: 4 }}>
                {rupiah(form.price)}
              </div>
            )}
          </div>

          {/* Target Selesai */}
          <div style={{ marginBottom: 20 }}>
            <label style={{ display: "block", fontSize: 12, fontWeight: 500, color: "var(--color-ink)", marginBottom: 5 }}>
              Target Selesai <span style={{ fontSize: 11, color: "var(--color-ink-3)", fontWeight: 400 }}>(opsional)</span>
            </label>
            <input type="date" value={form.target_completion ?? ""}
              onChange={(e) => setForm({ ...form, target_completion: e.target.value })}
              style={inputStyle} />
          </div>

          {/* Actions */}
          <div style={{ display: "flex", gap: 10 }}>
            <button onClick={onClose} className="btn-ghost" style={{ flex: 1 }} disabled={saving}>Batal</button>
            <button onClick={handleSubmit} className="btn-accent" disabled={saving}
              style={{ flex: 2, display: "flex", alignItems: "center", justifyContent: "center", gap: 6 }}>
              {saving
                ? <><Loader2 size={14} style={{ animation: "spin 1s linear infinite" }} /> Membuat…</>
                : <><Home size={14} /> Tambah Unit</>
              }
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}

// ── Booking Modal ─────────────────────────────────────────────
function BookingModal({
  unit,
  buyers,
  onClose,
  onBooked,
}: {
  unit:     Unit;
  buyers:   { id: string; full_name: string; email: string }[];
  onClose:  () => void;
  onBooked: (u: Unit) => void;
}) {
  const [form, setForm] = useState<BookingPayload>({
    buyer_id:       buyers[0]?.id ?? "",
    booking_fee:    0,
    booking_date:   new Date().toISOString().split("T")[0],
    expiry_days:    7,
    payment_method: "",
    bank:           "",
    notes:          "",
  });
  const [saving,  setSaving]  = useState(false);
  const [error,   setError]   = useState<string | null>(null);
  const [success, setSuccess] = useState<string | null>(null);

  const handleSubmit = async () => {
    if (!form.buyer_id)    { setError("Pilih pembeli"); return; }
    if (!form.booking_fee || form.booking_fee <= 0) { setError("Booking fee wajib diisi"); return; }
    setSaving(true);
    setError(null);
    try {
      const result = await unitsApi.book(unit.id, form);
      setSuccess(result.message);
      setTimeout(() => { onBooked(result.unit); }, 1500);
    } catch (e: unknown) {
      const msg = (e as { response?: { data?: { message?: string } } })
        ?.response?.data?.message;
      setError(msg ?? "Gagal melakukan booking");
    } finally {
      setSaving(false);
    }
  };

  const inputStyle: React.CSSProperties = {
    width: "100%", padding: "8px 10px",
    border: "1px solid rgba(14,13,11,0.15)",
    borderRadius: 6, fontSize: 13,
    color: "var(--color-ink)", outline: "none",
    boxSizing: "border-box",
  };

  return (
    <div style={{ position: "fixed", inset: 0, zIndex: 100, backgroundColor: "rgba(14,13,11,0.4)", display: "flex", alignItems: "center", justifyContent: "center", padding: 16 }}>
      <div style={{ backgroundColor: "white", borderRadius: 12, width: "100%", maxWidth: 480, boxShadow: "0 20px 60px rgba(14,13,11,0.15)", overflow: "hidden" }}>

        {/* Header */}
        <div style={{ padding: "20px 24px 16px", borderBottom: "1px solid rgba(14,13,11,0.06)", display: "flex", alignItems: "center", justifyContent: "space-between" }}>
          <div>
            <div style={{ display: "flex", alignItems: "center", gap: 8, marginBottom: 4 }}>
              <FileText size={15} style={{ color: "var(--color-warning)" }} />
              <span style={{ fontSize: 11, fontWeight: 700, color: "var(--color-warning)", textTransform: "uppercase", letterSpacing: "0.08em" }}>Booking Unit</span>
            </div>
            <h2 style={{ fontSize: 18, fontWeight: 600, color: "var(--color-ink)", margin: 0 }}>
              Pesan Unit {unit.unit_number}
            </h2>
            <div style={{ fontSize: 12, color: "var(--color-ink-3)", marginTop: 2 }}>
              {unit.project_name} — {unit.unit_type} — {rupiah(unit.price)}
            </div>
          </div>
          <button onClick={onClose} style={{ padding: 6, borderRadius: 6, border: "none", backgroundColor: "transparent", cursor: "pointer", color: "var(--color-ink-3)" }}>
            <X size={18} />
          </button>
        </div>

        <div style={{ padding: "20px 24px" }}>
          {success ? (
            <div style={{ textAlign: "center", padding: "24px 0" }}>
              <CheckCircle2 size={40} style={{ color: "var(--color-success)", margin: "0 auto 12px", display: "block" }} />
              <div style={{ fontSize: 14, fontWeight: 600, color: "var(--color-ink)", marginBottom: 4 }}>Booking Berhasil!</div>
              <div style={{ fontSize: 12, color: "var(--color-ink-3)" }}>{success}</div>
            </div>
          ) : (
            <>
              {error && (
                <div style={{ marginBottom: 16, padding: "10px 14px", backgroundColor: "var(--color-danger-light)", borderRadius: 6, fontSize: 12, color: "var(--color-danger)" }}>
                  {error}
                </div>
              )}

              {/* SPR info banner */}
              <div style={{ marginBottom: 16, padding: "10px 14px", backgroundColor: "var(--color-info-light)", borderRadius: 6, fontSize: 12, color: "var(--color-info)" }}>
                📄 Nomor SPR akan digenerate otomatis setelah booking berhasil
              </div>

              {/* Pembeli */}
              <div style={{ marginBottom: 14 }}>
                <label style={{ display: "block", fontSize: 12, fontWeight: 500, color: "var(--color-ink)", marginBottom: 5 }}>
                  Pembeli <span style={{ color: "var(--color-danger)" }}>*</span>
                </label>
                {buyers.length > 0 ? (
                  <select value={form.buyer_id}
                    onChange={(e) => setForm({ ...form, buyer_id: e.target.value })}
                    style={inputStyle}>
                    <option value="">— Pilih Pembeli —</option>
                    {buyers.map((b) => (
                      <option key={b.id} value={b.id}>{b.full_name} ({b.email})</option>
                    ))}
                  </select>
                ) : (
                  <div style={{ padding: "10px 12px", backgroundColor: "var(--color-warning-light)", borderRadius: 6, fontSize: 12, color: "var(--color-warning)" }}>
                    ⚠️ Belum ada akun pembeli. Minta pembeli untuk registrasi terlebih dahulu.
                  </div>
                )}
              </div>

              {/* Booking Fee */}
              <div style={{ marginBottom: 14 }}>
                <label style={{ display: "block", fontSize: 12, fontWeight: 500, color: "var(--color-ink)", marginBottom: 5 }}>
                  Booking Fee (IDR) <span style={{ color: "var(--color-danger)" }}>*</span>
                </label>
                <input type="number" placeholder="contoh: 5000000"
                  value={form.booking_fee || ""}
                  onChange={(e) => setForm({ ...form, booking_fee: Number(e.target.value) })}
                  style={inputStyle} />
                {(form.booking_fee ?? 0) > 0 && (
                  <div style={{ fontSize: 11, color: "var(--color-ink-3)", marginTop: 4 }}>
                    {rupiah(form.booking_fee ?? 0)}
                  </div>
                )}
              </div>

              {/* Tanggal + Metode Pembayaran */}
              <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 12, marginBottom: 14 }}>
                <div>
                  <label style={{ display: "block", fontSize: 12, fontWeight: 500, color: "var(--color-ink)", marginBottom: 5 }}>Tanggal Booking</label>
                  <input type="date" value={form.booking_date ?? ""}
                    onChange={(e) => setForm({ ...form, booking_date: e.target.value })}
                    style={inputStyle} />
                </div>
                <div>
                  <label style={{ display: "block", fontSize: 12, fontWeight: 500, color: "var(--color-ink)", marginBottom: 5 }}>Metode Pembayaran</label>
                  <input type="text" placeholder="KPR BCA / Cash"
                    value={form.payment_method ?? ""}
                    onChange={(e) => setForm({ ...form, payment_method: e.target.value })}
                    style={inputStyle} />
                </div>
              </div>

              {/* Sprint 23: deposit window — how many days before this
                  booking auto-expires if never converted to a real sale.
                  Defaults to 7, matching Booking.DEFAULT_EXPIRY_DAYS
                  server-side, but adjustable per-booking here. */}
              <div style={{ marginBottom: 14 }}>
                <label style={{ display: "block", fontSize: 12, fontWeight: 500, color: "var(--color-ink)", marginBottom: 5 }}>
                  Jendela Deposit (hari)
                </label>
                <input type="number" min={1} placeholder="7"
                  value={form.expiry_days ?? 7}
                  onChange={(e) => setForm({ ...form, expiry_days: Number(e.target.value) })}
                  style={inputStyle} />
                <div style={{ fontSize: 11, color: "var(--color-ink-3)", marginTop: 4 }}>
                  Booking otomatis kedaluwarsa pada{" "}
                  {new Date(Date.now() + (form.expiry_days ?? 7) * 86_400_000)
                    .toLocaleDateString("id-ID", { day: "numeric", month: "long", year: "numeric" })}
                  {" "}jika belum dikonversi
                </div>
              </div>

              {/* Catatan */}
              <div style={{ marginBottom: 20 }}>
                <label style={{ display: "block", fontSize: 12, fontWeight: 500, color: "var(--color-ink)", marginBottom: 5 }}>
                  Catatan <span style={{ fontSize: 11, color: "var(--color-ink-3)", fontWeight: 400 }}>(opsional)</span>
                </label>
                <textarea rows={2}
                  placeholder="Catatan tambahan..."
                  value={form.notes ?? ""}
                  onChange={(e) => setForm({ ...form, notes: e.target.value })}
                  style={{ ...inputStyle, resize: "vertical", fontFamily: "inherit" }} />
              </div>

              <div style={{ display: "flex", gap: 10 }}>
                <button onClick={onClose} className="btn-ghost" style={{ flex: 1 }} disabled={saving}>Batal</button>
                <button onClick={handleSubmit} className="btn-accent" disabled={saving || buyers.length === 0}
                  style={{ flex: 2, display: "flex", alignItems: "center", justifyContent: "center", gap: 6 }}>
                  {saving
                    ? <><Loader2 size={14} style={{ animation: "spin 1s linear infinite" }} /> Memproses…</>
                    : <><FileText size={14} /> Konfirmasi Booking</>
                  }
                </button>
              </div>
            </>
          )}
        </div>
      </div>
    </div>
  );
}

// ── Status tabs ───────────────────────────────────────────────
const STATUS_TABS = [
  { key: "semua",       label: "Semua"       },
  { key: "tersedia",    label: "Tersedia"    },
  { key: "dipesan",     label: "Dipesan"     },
  { key: "proses",      label: "Proses"      },
  { key: "terjual",     label: "Terjual"     },
  { key: "serah_terima",label: "Serah Terima"},
];

// ── Main page ─────────────────────────────────────────────────
export default function UnitsPage() {
  const [units,      setUnits]      = useState<Unit[]>([]);
  const [projects,   setProjects]   = useState<Project[]>([]);
  const [buyers,     setBuyers]     = useState<{ id: string; full_name: string; email: string }[]>([]);
  const [loading,    setLoading]    = useState(true);
  const [error,      setError]      = useState<string | null>(null);
  const [activeTab,  setActiveTab]  = useState("semua");
  const [projectFilter, setProjectFilter] = useState("semua");
  const [search,     setSearch]     = useState("");
  const [showAdd,    setShowAdd]    = useState(false);
  const [bookingUnit, setBookingUnit] = useState<Unit | null>(null);
  // Sprint 22: tracks which specific row is mid-transition, so only
  // that row's button shows a spinner — not the whole table.
  const [advancingId, setAdvancingId] = useState<string | null>(null);

  useEffect(() => {
    Promise.all([
      unitsApi.list(),
      projectsApi.list(),
    ])
      .then(([u, p]) => { setUnits(u); setProjects(p); })
      .catch(() => setError("Gagal memuat data unit"))
      .finally(() => setLoading(false));
  }, []);

  const loadBuyers = async () => {
    try {
      const { default: api } = await import("@/lib/api");
      // Derive buyers from existing unit assignments first, then
      // supplement with the full org buyer list if that endpoint is
      // available (it is — apps/organizations/views.py:BuyerListView).
      const buyerSet = new Map<string, { id: string; full_name: string; email: string }>();
      units.forEach((u) => {
        if (u.buyer && u.buyer_name && u.buyer_email) {
          buyerSet.set(u.buyer, {
            id:        u.buyer,
            full_name: u.buyer_name,
            email:     u.buyer_email,
          });
        }
      });
      try {
        const { data } = await api.get("/api/organizations/buyers/");
        if (data?.results) {
          data.results.forEach((b: { id: string; full_name: string; email: string }) => {
            buyerSet.set(b.id, b);
          });
        }
      } catch {
        // endpoint may not exist yet — unit-derived buyers still work
      }
      setBuyers(Array.from(buyerSet.values()));
    } catch {
      setBuyers([]);
    }
  };

  useEffect(() => {
    if (units.length > 0) loadBuyers();
  }, [units]);

  const handleUnitCreated = (unit: Unit) => {
    setUnits((prev) => [unit, ...prev]);
    setShowAdd(false);
  };

  const handleUnitBooked = (updatedUnit: Unit) => {
    setUnits((prev) => prev.map((u) => u.id === updatedUnit.id ? updatedUnit : u));
    setBookingUnit(null);
  };

  // Sprint 22: advance a unit to the ONE legal next status. The button
  // that calls this only ever renders for a status that has an entry
  // in NEXT_STATUS, so illegal transitions aren't a UI possibility —
  // but the backend guard (Unit.can_transition_to) is still the real
  // source of truth, and its error message surfaces here if anything
  // ever gets out of sync between the two.
  const handleAdvance = async (u: Unit) => {
    const transition = NEXT_STATUS[u.status];
    if (!transition) return;
    setAdvancingId(u.id);
    try {
      const updated = await unitsApi.update(u.id, { status: transition.next });
      setUnits((prev) => prev.map((x) => x.id === updated.id ? updated : x));
    } catch (e: unknown) {
      const msg = (e as { response?: { data?: { errors?: Record<string, string[]> } } })
        ?.response?.data?.errors;
      alert(msg ? Object.values(msg).flat().join(", ") : "Gagal mengubah status unit");
    } finally {
      setAdvancingId(null);
    }
  };

  if (loading) {
    return (
      <div style={{ display: "flex", alignItems: "center", justifyContent: "center", height: 300, gap: 10, color: "var(--color-ink-3)" }}>
        <Loader2 size={18} style={{ animation: "spin 1s linear infinite" }} />
        <span style={{ fontSize: 13 }}>Memuat unit…</span>
      </div>
    );
  }

  if (error) {
    return <div style={{ padding: 24, textAlign: "center", color: "var(--color-danger)", fontSize: 13 }}>{error}</div>;
  }

  const filtered = units
    .filter((u) => activeTab === "semua" || u.status === activeTab)
    .filter((u) => projectFilter === "semua" || u.project === projectFilter)
    .filter((u) =>
      !search ||
      u.unit_number.toLowerCase().includes(search.toLowerCase()) ||
      (u.buyer_name ?? "").toLowerCase().includes(search.toLowerCase())
    );

  return (
    <div style={{ maxWidth: 1100, margin: "0 auto" }}>

      {/* ── Modals ── */}
      {showAdd && (
        <AddUnitModal
          projects={projects}
          onClose={() => setShowAdd(false)}
          onCreated={handleUnitCreated}
        />
      )}
      {bookingUnit && (
        <BookingModal
          unit={bookingUnit}
          buyers={buyers}
          onClose={() => setBookingUnit(null)}
          onBooked={handleUnitBooked}
        />
      )}

      {/* ── Page header ── */}
      <div className="page-header" style={{ display: "flex", alignItems: "flex-start", justifyContent: "space-between" }}>
        <div>
          <h1 className="page-title">Semua Unit</h1>
          <p className="page-subtitle">{units.length} unit terdaftar di semua proyek</p>
        </div>
        <button
          className="btn-accent"
          style={{ flexShrink: 0, display: "flex", alignItems: "center", gap: 6 }}
          onClick={() => setShowAdd(true)}
        >
          <Plus size={15} /> Tambah Unit
        </button>
      </div>

      {/* ── Summary strip ── */}
      <div style={{ display: "grid", gridTemplateColumns: "repeat(5, 1fr)", gap: 12, marginBottom: 20 }}>
        {[
          { label: "Total",      value: units.length,                                            color: "var(--color-accent)",  bg: "var(--color-accent-light)",  icon: Home       },
          { label: "Tersedia",   value: units.filter((u) => u.status === "tersedia").length,    color: "var(--color-info)",    bg: "var(--color-info-light)",    icon: Home       },
          { label: "Dipesan",    value: units.filter((u) => u.status === "dipesan").length,     color: "var(--color-warning)", bg: "var(--color-warning-light)", icon: FileText   },
          { label: "Proses",     value: units.filter((u) => u.status === "proses").length,      color: "var(--color-accent)",  bg: "var(--color-accent-light)",  icon: TrendingUp },
          { label: "Terjual",    value: units.filter((u) => u.status === "terjual").length,     color: "var(--color-success)", bg: "var(--color-success-light)", icon: Users      },
        ].map((s) => (
          <div key={s.label} className="metric-card">
            <div style={{ display: "flex", alignItems: "flex-start", justifyContent: "space-between", marginBottom: 8 }}>
              <div className="metric-label" style={{ fontSize: 10 }}>{s.label}</div>
              <div style={{ width: 26, height: 26, borderRadius: 6, backgroundColor: s.bg, display: "flex", alignItems: "center", justifyContent: "center" }}>
                <s.icon size={13} style={{ color: s.color }} />
              </div>
            </div>
            <div className="metric-value" style={{ fontSize: 22 }}>{s.value}</div>
          </div>
        ))}
      </div>

      {/* ── Filters ── */}
      <div style={{ display: "flex", alignItems: "center", gap: 10, marginBottom: 16 }}>
        <div style={{ display: "flex", alignItems: "center", gap: 8, padding: "8px 12px", backgroundColor: "white", border: "1px solid rgba(14,13,11,0.10)", borderRadius: 6, flex: 1, maxWidth: 260 }}>
          <Search size={13} style={{ color: "var(--color-ink-3)", flexShrink: 0 }} />
          <input
            type="text" placeholder="Cari unit atau pembeli…"
            value={search} onChange={(e) => setSearch(e.target.value)}
            style={{ border: "none", outline: "none", fontSize: 13, fontFamily: "var(--font-sans)", color: "var(--color-ink)", backgroundColor: "transparent", width: "100%" }}
          />
        </div>
        <select value={projectFilter} onChange={(e) => setProjectFilter(e.target.value)}
          style={{ padding: "8px 12px", border: "1px solid rgba(14,13,11,0.10)", borderRadius: 6, fontSize: 13, color: "var(--color-ink)", backgroundColor: "white", maxWidth: 220 }}>
          <option value="semua">Semua Proyek</option>
          {projects.map((p) => <option key={p.id} value={p.id}>{p.name}</option>)}
        </select>
      </div>

      {/* ── Table ── */}
      <div className="card" style={{ padding: 0, overflow: "hidden" }}>
        {/* Status tabs */}
        <div style={{ display: "flex", borderBottom: "1px solid rgba(14,13,11,0.08)", padding: "0 16px", overflowX: "auto" }}>
          {STATUS_TABS.map((tab) => {
            const count = tab.key === "semua" ? units.length : units.filter((u) => u.status === tab.key).length;
            const isActive = activeTab === tab.key;
            return (
              <button key={tab.key} onClick={() => setActiveTab(tab.key)}
                style={{ padding: "14px 12px", fontSize: 12, fontWeight: isActive ? 600 : 400, color: isActive ? "var(--color-accent)" : "var(--color-ink-3)", backgroundColor: "transparent", border: "none", borderBottom: isActive ? "2px solid var(--color-accent)" : "2px solid transparent", cursor: "pointer", display: "flex", alignItems: "center", gap: 5, marginBottom: -1, whiteSpace: "nowrap" }}>
                {tab.label}
                <span style={{ fontSize: 10, fontWeight: 600, backgroundColor: isActive ? "var(--color-accent-light)" : "var(--color-paper-2)", color: isActive ? "var(--color-accent)" : "var(--color-ink-3)", padding: "1px 5px", borderRadius: 999 }}>
                  {count}
                </span>
              </button>
            );
          })}
        </div>

        <table style={{ width: "100%", borderCollapse: "collapse", fontSize: 12 }}>
          <thead>
            <tr style={{ borderBottom: "1px solid rgba(14,13,11,0.06)" }}>
              {["No. Unit", "Tipe", "Proyek", "Harga", "Pembeli / SPR", "Progres", "Status", "Aksi"].map((h) => (
                <th key={h} style={{ padding: "10px 14px", textAlign: "left", fontSize: 10, fontWeight: 700, color: "var(--color-ink-3)", textTransform: "uppercase", letterSpacing: "0.05em", whiteSpace: "nowrap" }}>
                  {h}
                </th>
              ))}
            </tr>
          </thead>
          <tbody>
            {filtered.map((u) => (
              <tr key={u.id} style={{ borderBottom: "1px solid rgba(14,13,11,0.04)" }}
                onMouseEnter={(e) => ((e.currentTarget as HTMLElement).style.backgroundColor = "var(--color-paper-2)")}
                onMouseLeave={(e) => ((e.currentTarget as HTMLElement).style.backgroundColor = "transparent")}>

                <td style={{ padding: "12px 14px" }}>
                  <span style={{ fontSize: 13, fontWeight: 700, color: "var(--color-ink)" }}>{u.unit_number}</span>
                </td>

                <td style={{ padding: "12px 14px", color: "var(--color-ink-3)" }}>{u.unit_type}</td>

                <td style={{ padding: "12px 14px", color: "var(--color-ink-3)", maxWidth: 160 }}>
                  <div style={{ overflow: "hidden", textOverflow: "ellipsis", whiteSpace: "nowrap" }}>
                    {u.project_name}
                  </div>
                </td>

                <td style={{ padding: "12px 14px", fontWeight: 500, whiteSpace: "nowrap" }}>
                  {rupiah(u.price)}
                </td>

                <td style={{ padding: "12px 14px" }}>
                  {u.buyer_name ? (
                    <div>
                      <div style={{ display: "flex", alignItems: "center", gap: 6 }}>
                        <div style={{ width: 22, height: 22, borderRadius: "50%", backgroundColor: "var(--color-accent-light)", display: "flex", alignItems: "center", justifyContent: "center", fontSize: 9, fontWeight: 700, color: "var(--color-accent)", flexShrink: 0 }}>
                          {u.buyer_name.split(" ").map((n) => n[0]).join("").slice(0, 2)}
                        </div>
                        <span style={{ fontSize: 12 }}>{u.buyer_name}</span>
                      </div>
                      {u.booking && (
                        <div style={{ fontSize: 10, color: "var(--color-warning)", marginTop: 3, fontWeight: 600 }}>
                          📄 {u.booking.spr_number}
                        </div>
                      )}
                      {u.booking && bookingCountdown(u.booking) && (
                        <div style={{ fontSize: 10, fontWeight: 700, marginTop: 2, color: bookingCountdown(u.booking)!.color }}>
                          {bookingCountdown(u.booking)!.label}
                        </div>
                      )}
                      {u.booking && u.booking.status === "active" && (
                        <div style={{ fontSize: 10, fontWeight: 600, marginTop: 2, color: kprStatusColor(u.booking.kpr_status) }}>
                          🏦 KPR: {u.booking.kpr_status_display}
                          {u.booking.is_stalled && " ⚠️"}
                        </div>
                      )}
                    </div>
                  ) : (
                    <span style={{ color: "var(--color-ink-3)" }}>—</span>
                  )}
                </td>

                <td style={{ padding: "12px 14px", minWidth: 100 }}>
                  <div style={{ display: "flex", alignItems: "center", gap: 8 }}>
                    <div style={{ flex: 1, height: 5, backgroundColor: "rgba(14,13,11,0.08)", borderRadius: 3, overflow: "hidden" }}>
                      <div style={{ width: `${u.progress}%`, height: "100%", backgroundColor: warnaProgres(u.progress), borderRadius: 3 }} />
                    </div>
                    <span style={{ fontSize: 11, fontWeight: 600, color: warnaProgres(u.progress), flexShrink: 0 }}>
                      {u.progress}%
                    </span>
                  </div>
                </td>

                <td style={{ padding: "12px 14px" }}>
                  <StatusBadge status={u.status} display={u.status_display} />
                </td>

                <td style={{ padding: "12px 14px" }}>
                  <div style={{ display: "flex", gap: 6, flexWrap: "wrap" }}>
                    {u.status === "tersedia" && (
                      <button
                        className="btn-accent btn-sm"
                        onClick={() => setBookingUnit(u)}
                        style={{ display: "flex", alignItems: "center", gap: 4, fontSize: 11 }}
                      >
                        <FileText size={11} /> Booking
                      </button>
                    )}
                    {u.status === "dipesan" && u.booking && (
                      <button
                        className="btn-ghost btn-sm"
                        onClick={async () => {
                          if (!confirm(`Batalkan booking ${u.booking!.spr_number}?`)) return;
                          try {
                            const updated = await unitsApi.cancelBooking(u.booking!.id);
                            handleUnitBooked(updated);
                          } catch {
                            alert("Gagal membatalkan booking");
                          }
                        }}
                        style={{ fontSize: 11, color: "var(--color-danger)" }}
                      >
                        Batalkan
                      </button>
                    )}
                    {/* Sprint 22: the piece that was completely missing — dipesan→proses, proses→terjual, 
                    terjual→serah_terima all had zero UI before this.Only the ONE legal
                        next step is ever offered, mirroring the backend guard exactly. */}
                    {NEXT_STATUS[u.status] && (
                      <button
                        className="btn-accent btn-sm"
                        disabled={advancingId === u.id}
                        onClick={() => handleAdvance(u)}
                        style={{ display: "flex", alignItems: "center", gap: 4, fontSize: 11 }}
                      >
                        {advancingId === u.id ? (
                          <Loader2 size={11} style={{ animation: "spin 1s linear infinite" }} />
                        ) : (
                          <TrendingUp size={11} />
                        )}
                        {NEXT_STATUS[u.status]!.label}
                      </button>
                    )}
                    {u.status === "serah_terima" && (
                      <span style={{ fontSize: 11, color: "var(--color-success)", fontWeight: 600, display: "flex", alignItems: "center", gap: 4 }}>
                        <CheckCircle2 size={11} /> Selesai
                      </span>
                    )}
                  </div>
                </td>
              </tr>
            ))}
            {filtered.length === 0 && (
              <tr>
                <td colSpan={8} style={{ textAlign: "center", padding: 48, color: "var(--color-ink-3)" }}>
                  <Home size={28} style={{ margin: "0 auto 12px", opacity: 0.2, display: "block" }} />
                  <div style={{ fontSize: 13 }}>Tidak ada unit untuk filter ini</div>
                </td>
              </tr>
            )}
          </tbody>
        </table>

        <div style={{ padding: "12px 16px", borderTop: "1px solid rgba(14,13,11,0.06)", backgroundColor: "var(--color-paper)" }}>
          <span style={{ fontSize: 12, color: "var(--color-ink-3)" }}>
            Menampilkan {filtered.length} dari {units.length} unit
          </span>
        </div>
      </div>
    </div>
  );
}
