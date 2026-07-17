"use client";
// =============================================================================
// === frontend/app/dashboard/commissions/page.tsx ===
// =============================================================================
/**
 * Commission Foundation Sprint 1.
 *
 * Deliberately a standalone page, not folded into the existing
 * Settings page — I didn't have that file's structure, and building
 * a self-contained additive page avoids guessing at conventions in a
 * file I hadn't seen. If Settings is where org-level config is
 * meant to consolidate, moving the policy form there later is a
 * small, safe follow-up, not a rebuild.
 */

import { useAuth } from "@/context/AuthContext";
import {
  Commission, CommissionPolicy,
  commissionPolicyApi, commissionsApi,
  CommissionTier,
  commissionTiersApi,
  CreateCommissionTierPayload,
  UpdateCommissionPolicyPayload,
} from "@/lib/api/commissions";
import { rupiah } from "@/lib/mock-data";
import {
  Banknote, CheckCircle2, Clock, Layers, Loader2, Plus, Settings2, Trash2,
} from "lucide-react";
import { useEffect, useMemo, useState } from "react";

const STATUS_TABS: { key: Commission["status"] | "semua"; label: string }[] = [
  { key: "semua",   label: "Semua"   },
  { key: "pending", label: "Pending" },
  { key: "earned",  label: "Earned"  },
  { key: "paid",    label: "Paid"    },
  // Booking Rebooking Foundation Sprint 1
  { key: "void",    label: "Void"    },
];

function statusColor(s: Commission["status"]): { color: string; bg: string } {
  switch (s) {
    case "paid":   return { color: "var(--color-success)", bg: "var(--color-success-light)" };
    case "earned": return { color: "var(--color-accent)",  bg: "var(--color-accent-light)"  };
    // Same muted treatment "Lost" already gets on the Prospect
    // pipeline — a dead-end state, not an active one.
    case "void":   return { color: "var(--color-ink-3)",   bg: "var(--color-paper-2)"       };
    default:       return { color: "var(--color-warning)", bg: "var(--color-warning-light)" };
  }
}

// ── Policy settings card ────────────────────────────────────────
function PolicyCard({
  policy,
  canEdit,
  onUpdated,
}: {
  policy:   CommissionPolicy;
  canEdit:  boolean;
  onUpdated: (p: CommissionPolicy) => void;
}) {
  const [rateType,  setRateType]  = useState(policy.rate_type);
  const [rateValue, setRateValue] = useState(policy.rate_value);
  const [saving,    setSaving]    = useState(false);
  const [error,     setError]     = useState<string | null>(null);
  const [saved,     setSaved]     = useState(false);

  const handleSave = async () => {
    setSaving(true);
    setError(null);
    setSaved(false);
    try {
      const payload: UpdateCommissionPolicyPayload = { rate_type: rateType, rate_value: rateValue };
      const updated = await commissionPolicyApi.update(payload);
      onUpdated(updated);
      setSaved(true);
      setTimeout(() => setSaved(false), 2000);
    } catch {
      setError("Gagal menyimpan kebijakan komisi");
    } finally {
      setSaving(false);
    }
  };

  return (
    <div className="card" style={{ marginBottom: 20 }}>
      <div style={{ display: "flex", alignItems: "center", gap: 8, marginBottom: 16 }}>
        <Settings2 size={16} style={{ color: "var(--color-accent)" }} />
        <h2 style={{ fontSize: 15, fontWeight: 600, color: "var(--color-ink)", margin: 0 }}>
          Kebijakan Komisi
        </h2>
      </div>

      {error && (
        <div style={{ marginBottom: 12, padding: "10px 14px", backgroundColor: "var(--color-danger-light)", borderRadius: 6, fontSize: 12, color: "var(--color-danger)" }}>
          {error}
        </div>
      )}

      <div style={{ display: "flex", gap: 12, alignItems: "flex-end", flexWrap: "wrap" }}>
        <div style={{ minWidth: 180 }}>
          <label style={{ display: "block", fontSize: 12, fontWeight: 500, color: "var(--color-ink)", marginBottom: 5 }}>
            Jenis Tarif
          </label>
          <select
            value={rateType}
            disabled={!canEdit}
            onChange={(e) => setRateType(e.target.value as CommissionPolicy["rate_type"])}
            style={{ width: "100%", padding: "8px 10px", border: "1px solid rgba(14,13,11,0.15)", borderRadius: 6, fontSize: 13, outline: "none" }}
          >
            <option value="percentage">Persentase</option>
            <option value="flat_amount">Nominal Tetap</option>
            <option value="tiered">Bertingkat</option>
          </select>
        </div>

        {/* Sprint 2: rate_value is meaningless for a tiered policy —
            the tiers below carry the real rates. The whole field
            (label included) is hidden, not shown-but-disabled, to
            avoid implying it still does something. */}
        {rateType !== "tiered" && (
          <div style={{ minWidth: 200 }}>
            <label style={{ display: "block", fontSize: 12, fontWeight: 500, color: "var(--color-ink)", marginBottom: 5 }}>
              {rateType === "percentage" ? "Persentase (%)" : "Nominal (Rupiah)"}
            </label>
            <input
              type="number"
              step="0.01"
              disabled={!canEdit}
              value={rateValue}
              onChange={(e) => setRateValue(e.target.value)}
              placeholder={rateType === "percentage" ? "mis. 2.5" : "mis. 5000000"}
              style={{ width: "100%", padding: "8px 10px", border: "1px solid rgba(14,13,11,0.15)", borderRadius: 6, fontSize: 13, outline: "none", boxSizing: "border-box" }}
            />
          </div>
        )}

        {canEdit && (
          <button
            onClick={handleSave}
            disabled={saving}
            className="btn-accent"
            style={{ display: "flex", alignItems: "center", gap: 6, height: 36 }}
          >
            {saving
              ? <><Loader2 size={14} style={{ animation: "spin 1s linear infinite" }} /> Menyimpan…</>
              : saved
                ? <><CheckCircle2 size={14} /> Tersimpan</>
                : "Simpan"
            }
          </button>
        )}
      </div>

      {!canEdit && (
        <div style={{ fontSize: 11, color: "var(--color-ink-3)", marginTop: 10 }}>
          Hanya developer yang dapat mengubah kebijakan komisi.
        </div>
      )}
    </div>
  );
}

// ── Tier editor ────────────────────────────────────────────────
// Sprint 2 (Commission Foundation): only rendered when the policy is
// actually tiered — a flat-rate org never sees this section at all.
function TierEditor({
  tiers,
  canEdit,
  onChanged,
}: {
  tiers:     CommissionTier[];
  canEdit:   boolean;
  onChanged: () => void;
}) {
  const [minAmount, setMinAmount] = useState("");
  const [maxAmount, setMaxAmount] = useState("");
  const [rateValue, setRateValue] = useState("");
  const [saving,    setSaving]    = useState(false);
  const [error,     setError]     = useState<string | null>(null);
  const [deletingId, setDeletingId] = useState<string | null>(null);

  const sorted = useMemo(
    () => [...tiers].sort((a, b) => Number(a.min_amount) - Number(b.min_amount)),
    [tiers]
  );

  const handleAdd = async () => {
    setError(null);
    if (!minAmount.trim() || !rateValue.trim()) {
      setError("Batas bawah dan persentase wajib diisi");
      return;
    }
    setSaving(true);
    try {
      const payload: CreateCommissionTierPayload = {
        min_amount: minAmount,
        max_amount: maxAmount.trim() ? maxAmount : null,
        rate_value: rateValue,
      };
      await commissionTiersApi.create(payload);
      setMinAmount(""); setMaxAmount(""); setRateValue("");
      onChanged();
    } catch (e: unknown) {
      const msg = (e as { response?: { data?: { errors?: string[] | Record<string, string[]> } } })
        ?.response?.data?.errors;
      setError(
        Array.isArray(msg) ? msg.join(", ")
        : msg ? Object.values(msg).flat().join(", ")
        : "Gagal menambahkan tingkat komisi"
      );
    } finally {
      setSaving(false);
    }
  };

  const handleDelete = async (tierId: string) => {
    setDeletingId(tierId);
    try {
      await commissionTiersApi.remove(tierId);
      onChanged();
    } catch {
      setError("Gagal menghapus tingkat komisi");
    } finally {
      setDeletingId(null);
    }
  };

  return (
    <div className="card" style={{ marginBottom: 20 }}>
      <div style={{ display: "flex", alignItems: "center", gap: 8, marginBottom: 16 }}>
        <Layers size={16} style={{ color: "var(--color-accent)" }} />
        <h2 style={{ fontSize: 15, fontWeight: 600, color: "var(--color-ink)", margin: 0 }}>
          Tingkat Komisi
        </h2>
      </div>

      {error && (
        <div style={{ marginBottom: 12, padding: "10px 14px", backgroundColor: "var(--color-danger-light)", borderRadius: 6, fontSize: 12, color: "var(--color-danger)" }}>
          {error}
        </div>
      )}

      {sorted.length === 0 ? (
        <div style={{ fontSize: 12, color: "var(--color-ink-3)", marginBottom: 14 }}>
          Belum ada tingkat komisi. Tambahkan minimal satu tingkat dengan batas atas
          kosong (tanpa batas) agar setiap harga jual tercakup.
        </div>
      ) : (
        <div style={{ marginBottom: 16 }}>
          {sorted.map((t) => (
            <div key={t.id} style={{ display: "flex", alignItems: "center", justifyContent: "space-between", padding: "8px 12px", backgroundColor: "var(--color-paper-2)", borderRadius: 6, marginBottom: 6 }}>
              <span style={{ fontSize: 12 }}>
                {rupiah(Number(t.min_amount))} – {t.max_amount ? rupiah(Number(t.max_amount)) : "∞"}
              </span>
              <div style={{ display: "flex", alignItems: "center", gap: 10 }}>
                <span style={{ fontSize: 13, fontWeight: 600, color: "var(--color-accent)" }}>{t.rate_value}%</span>
                {canEdit && (
                  <button
                    disabled={deletingId === t.id}
                    onClick={() => handleDelete(t.id)}
                    style={{ padding: 4, border: "none", backgroundColor: "transparent", cursor: "pointer", color: "var(--color-danger)", display: "flex" }}
                  >
                    {deletingId === t.id
                      ? <Loader2 size={13} style={{ animation: "spin 1s linear infinite" }} />
                      : <Trash2 size={13} />}
                  </button>
                )}
              </div>
            </div>
          ))}
        </div>
      )}

      {canEdit && (
        <div style={{ display: "flex", gap: 8, alignItems: "flex-end", flexWrap: "wrap" }}>
          <div style={{ minWidth: 150 }}>
            <label style={{ display: "block", fontSize: 11, color: "var(--color-ink-3)", marginBottom: 4 }}>Batas Bawah</label>
            <input type="number" value={minAmount} onChange={(e) => setMinAmount(e.target.value)}
              placeholder="0" style={{ width: "100%", padding: "7px 9px", border: "1px solid rgba(14,13,11,0.15)", borderRadius: 6, fontSize: 12, outline: "none", boxSizing: "border-box" }} />
          </div>
          <div style={{ minWidth: 150 }}>
            <label style={{ display: "block", fontSize: 11, color: "var(--color-ink-3)", marginBottom: 4 }}>Batas Atas (kosongkan = ∞)</label>
            <input type="number" value={maxAmount} onChange={(e) => setMaxAmount(e.target.value)}
              placeholder="mis. 500000000" style={{ width: "100%", padding: "7px 9px", border: "1px solid rgba(14,13,11,0.15)", borderRadius: 6, fontSize: 12, outline: "none", boxSizing: "border-box" }} />
          </div>
          <div style={{ minWidth: 100 }}>
            <label style={{ display: "block", fontSize: 11, color: "var(--color-ink-3)", marginBottom: 4 }}>Persentase (%)</label>
            <input type="number" step="0.01" value={rateValue} onChange={(e) => setRateValue(e.target.value)}
              placeholder="2.5" style={{ width: "100%", padding: "7px 9px", border: "1px solid rgba(14,13,11,0.15)", borderRadius: 6, fontSize: 12, outline: "none", boxSizing: "border-box" }} />
          </div>
          <button onClick={handleAdd} disabled={saving} className="btn-accent btn-sm"
            style={{ display: "flex", alignItems: "center", gap: 4, height: 32 }}>
            {saving ? <Loader2 size={12} style={{ animation: "spin 1s linear infinite" }} /> : <Plus size={12} />}
            Tambah
          </button>
        </div>
      )}
    </div>
  );
}

// ─────────────────────────────────────────────────────────────
export default function CommissionsPage() {
  const { user } = useAuth();
  const canEdit = user?.role === "developer" || user?.role === "super_admin";

  const [policy,      setPolicy]      = useState<CommissionPolicy | null>(null);
  const [commissions, setCommissions] = useState<Commission[]>([]);
  const [loading,     setLoading]     = useState(true);
  const [error,       setError]       = useState<string | null>(null);
  const [tab,         setTab]         = useState<Commission["status"] | "semua">("semua");
  const [updatingId,  setUpdatingId]  = useState<string | null>(null);

  useEffect(() => {
    Promise.all([commissionPolicyApi.get(), commissionsApi.list()])
      .then(([p, c]) => { setPolicy(p); setCommissions(c); })
      .catch(() => setError("Gagal memuat data komisi"))
      .finally(() => setLoading(false));
  }, []);

  const filtered = useMemo(
    () => tab === "semua" ? commissions : commissions.filter((c) => c.status === tab),
    [commissions, tab]
  );

  const counts = useMemo(() => {
    const c: Record<string, number> = { semua: commissions.length, pending: 0, earned: 0, paid: 0 };
    commissions.forEach((x) => { c[x.status] = (c[x.status] ?? 0) + 1; });
    return c;
  }, [commissions]);

  const handleTransition = async (commission: Commission, newStatus: Commission["status"]) => {
    setUpdatingId(commission.id);
    try {
      const updated = await commissionsApi.updateStatus(commission.id, newStatus);
      setCommissions((prev) => prev.map((c) => c.id === updated.id ? updated : c));
    } catch {
      alert("Gagal memperbarui status komisi");
    } finally {
      setUpdatingId(null);
    }
  };

  if (loading) {
    return (
      <div style={{ display: "flex", alignItems: "center", justifyContent: "center", height: 300, gap: 10, color: "var(--color-ink-3)" }}>
        <Loader2 size={18} style={{ animation: "spin 1s linear infinite" }} />
        <span style={{ fontSize: 13 }}>Memuat data komisi…</span>
      </div>
    );
  }

  if (error || !policy) {
    return <div style={{ padding: 24, textAlign: "center", color: "var(--color-danger)", fontSize: 13 }}>{error}</div>;
  }

  return (
    <div style={{ maxWidth: 1100, margin: "0 auto" }}>

      <div className="page-header">
        <h1 className="page-title">Komisi</h1>
        <p className="page-subtitle">{commissions.length} komisi tercatat</p>
      </div>

      <PolicyCard policy={policy} canEdit={canEdit} onUpdated={setPolicy} />

      {policy.rate_type === "tiered" && (
        <TierEditor
          tiers={policy.tiers}
          canEdit={canEdit}
          onChanged={() => {
            // Tiers are nested read-only on the policy serializer —
            // refetch the whole policy to get the updated list rather
            // than trying to keep local state in sync by hand.
            commissionPolicyApi.get().then(setPolicy).catch(() => {});
          }}
        />
      )}

      <div className="card" style={{ padding: 0, overflow: "hidden" }}>
        <div style={{ display: "flex", padding: "0 16px", borderBottom: "1px solid rgba(14,13,11,0.08)" }}>
          {STATUS_TABS.map((t) => {
            const isActive = tab === t.key;
            return (
              <button key={t.key} onClick={() => setTab(t.key)}
                style={{ padding: "14px 16px", fontSize: 13, fontWeight: isActive ? 600 : 400, color: isActive ? "var(--color-accent)" : "var(--color-ink-3)", backgroundColor: "transparent", border: "none", borderBottom: isActive ? "2px solid var(--color-accent)" : "2px solid transparent", cursor: "pointer", display: "flex", alignItems: "center", gap: 6 }}
              >
                {t.label}
                {counts[t.key] > 0 && (
                  <span style={{ fontSize: 10, fontWeight: 600, backgroundColor: isActive ? "var(--color-accent-light)" : "var(--color-paper-2)", color: isActive ? "var(--color-accent)" : "var(--color-ink-3)", padding: "1px 6px", borderRadius: 999 }}>
                    {counts[t.key]}
                  </span>
                )}
              </button>
            );
          })}
        </div>

        <table className="data-table">
          <thead>
            <tr>
              <th>Agen</th>
              <th>Unit / SPR</th>
              <th>Nominal</th>
              <th>Status</th>
              <th>Tanggal</th>
              {canEdit && <th>Aksi</th>}
            </tr>
          </thead>
          <tbody>
            {filtered.map((c) => {
              const meta = statusColor(c.status);
              return (
                <tr key={c.id}>
                  <td>
                    <div style={{ fontSize: 13, fontWeight: 500 }}>{c.agent_name}</div>
                    <div style={{ fontSize: 11, color: "var(--color-ink-3)" }}>{c.agent_email}</div>
                  </td>
                  <td style={{ fontSize: 12 }}>
                    <div>{c.unit_number ?? "—"}</div>
                    <div style={{ color: "var(--color-warning)", fontSize: 11 }}>{c.booking_spr}</div>
                  </td>
                  <td style={{ fontWeight: 600 }}>
                    <div style={{ display: "flex", alignItems: "center", gap: 4 }}>
                      <Banknote size={13} style={{ color: "var(--color-ink-3)" }} />
                      {rupiah(Number(c.amount))}
                    </div>
                  </td>
                  <td>
                    <span style={{ fontSize: 11, fontWeight: 600, padding: "3px 10px", borderRadius: 999, color: meta.color, backgroundColor: meta.bg }}>
                      {c.status_display}
                    </span>
                  </td>
                  <td style={{ fontSize: 12, color: "var(--color-ink-3)" }}>
                    {new Date(c.computed_at).toLocaleDateString("id-ID", { day: "numeric", month: "short", year: "numeric" })}
                  </td>
                  {canEdit && (
                    <td>
                      <div style={{ display: "flex", gap: 6 }}>
                        {c.status === "pending" && (
                          <button
                            disabled={updatingId === c.id}
                            onClick={() => handleTransition(c, "earned")}
                            className="btn-ghost btn-sm"
                            style={{ display: "inline-flex", alignItems: "center", gap: 4, fontSize: 11 }}
                          >
                            <Clock size={11} /> Tandai Earned
                          </button>
                        )}
                        {c.status === "earned" && (
                          <button
                            disabled={updatingId === c.id}
                            onClick={() => handleTransition(c, "paid")}
                            className="btn-accent btn-sm"
                            style={{ display: "inline-flex", alignItems: "center", gap: 4, fontSize: 11 }}
                          >
                            {updatingId === c.id
                              ? <Loader2 size={11} style={{ animation: "spin 1s linear infinite" }} />
                              : <CheckCircle2 size={11} />}
                            Tandai Paid
                          </button>
                        )}
                      </div>
                    </td>
                  )}
                </tr>
              );
            })}
            {filtered.length === 0 && (
              <tr>
                <td colSpan={canEdit ? 6 : 5} style={{ textAlign: "center", padding: 40, color: "var(--color-ink-3)", fontSize: 13 }}>
                  Belum ada komisi untuk filter ini
                </td>
              </tr>
            )}
          </tbody>
        </table>
      </div>
    </div>
  );
}
