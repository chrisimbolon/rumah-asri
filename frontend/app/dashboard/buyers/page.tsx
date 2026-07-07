"use client";
// =============================================================================
// === frontend/app/dashboard/buyers/page.tsx ===
// =============================================================================
/**
 * Sprint 24: Data Pembeli — was a dead link (404) sitting in the
 * sidebar until now. Deliberately reuses GET /api/units/ entirely —
 * every field this page needs (buyer_name, buyer_email, the nested
 * booking with kpr_status/is_stalled) already exists there, fully
 * tenant-isolated and tested. No new backend endpoint, no new tests
 * needed — this is presentation on top of proven data.
 */

import { rupiah } from "@/lib/mock-data";
import { Booking, Unit, unitsApi } from "@/lib/api/units";
import {
  AlertTriangle, Loader2, Search, Users,
} from "lucide-react";
import { useEffect, useMemo, useState } from "react";

const KPR_TABS: { key: Booking["kpr_status"] | "semua"; label: string }[] = [
  { key: "semua",          label: "Semua" },
  { key: "belum_diajukan", label: "Belum Diajukan" },
  { key: "diajukan",       label: "Diajukan" },
  { key: "disetujui",      label: "Disetujui" },
  { key: "akad",           label: "Akad" },
];

function kprStatusColor(kprStatus: Booking["kpr_status"]): string {
  switch (kprStatus) {
    case "akad":      return "var(--color-success)";
    case "disetujui": return "var(--color-accent)";
    case "diajukan":  return "var(--color-warning)";
    default:          return "var(--color-ink-3)";
  }
}

export default function BuyersPage() {
  const [units,   setUnits]   = useState<Unit[]>([]);
  const [loading, setLoading] = useState(true);
  const [error,   setError]   = useState<string | null>(null);
  const [search,  setSearch]  = useState("");
  const [tab,     setTab]     = useState<Booking["kpr_status"] | "semua">("semua");
  // Sprint 24: tracks which specific row is mid-update, so only that
  // row's dropdown shows a spinner — same per-row pattern as the
  // Units page's advancingId.
  const [updatingId, setUpdatingId] = useState<string | null>(null);

  useEffect(() => {
    unitsApi.list()
      .then(setUnits)
      .catch(() => setError("Gagal memuat data pembeli"))
      .finally(() => setLoading(false));
  }, []);

  // Only units with an active booking + buyer actually belong on a
  // buyer CRM page — a unit that's tersedia has nobody to show here.
  const buyerUnits = useMemo(
    () => units.filter((u) => u.buyer_name && u.booking),
    [units]
  );

  const filtered = useMemo(() => {
    return buyerUnits.filter((u) => {
      if (tab !== "semua" && u.booking?.kpr_status !== tab) return false;
      if (search.trim()) {
        const q = search.toLowerCase();
        const haystack = `${u.buyer_name} ${u.buyer_email} ${u.unit_number} ${u.booking?.spr_number}`.toLowerCase();
        if (!haystack.includes(q)) return false;
      }
      return true;
    });
  }, [buyerUnits, tab, search]);

  const counts = useMemo(() => {
    const c: Record<string, number> = {
      semua: buyerUnits.length,
      belum_diajukan: 0, diajukan: 0, disetujui: 0, akad: 0,
    };
    buyerUnits.forEach((u) => {
      if (u.booking) c[u.booking.kpr_status] = (c[u.booking.kpr_status] ?? 0) + 1;
    });
    return c;
  }, [buyerUnits]);

  const stalledCount = useMemo(
    () => buyerUnits.filter((u) => u.booking?.is_stalled).length,
    [buyerUnits]
  );

  const handleKPRChange = async (unit: Unit, newStatus: Booking["kpr_status"]) => {
    if (!unit.booking) return;
    setUpdatingId(unit.id);
    try {
      const result = await unitsApi.updateKPRStatus(unit.booking.id, newStatus);
      setUnits((prev) => prev.map((u) =>
        u.id === unit.id ? { ...u, booking: result.booking } : u
      ));
    } catch {
      alert("Gagal memperbarui status KPR");
    } finally {
      setUpdatingId(null);
    }
  };

  if (loading) {
    return (
      <div style={{ display: "flex", alignItems: "center", justifyContent: "center", height: 300, gap: 10, color: "var(--color-ink-3)" }}>
        <Loader2 size={18} style={{ animation: "spin 1s linear infinite" }} />
        <span style={{ fontSize: 13 }}>Memuat data pembeli…</span>
      </div>
    );
  }

  if (error) {
    return (
      <div style={{ padding: "20px 24px", color: "var(--color-danger)", fontSize: 13 }}>
        {error}
      </div>
    );
  }

  return (
    <div style={{ maxWidth: 1180, margin: "0 auto", padding: "24px 24px 60px" }}>

      {/* ── Header ── */}
      <div style={{ marginBottom: 24 }}>
        <h1 style={{ fontSize: 24, fontWeight: 700, color: "var(--color-ink)", margin: 0 }}>
          Data Pembeli
        </h1>
        <div style={{ fontSize: 13, color: "var(--color-ink-3)", marginTop: 4 }}>
          {buyerUnits.length} pembeli dengan booking aktif di semua proyek
        </div>
      </div>

      {/* ── Summary cards ── */}
      <div style={{ display: "grid", gridTemplateColumns: "repeat(5, 1fr)", gap: 12, marginBottom: 20 }}>
        {[
          { label: "Total Pembeli",   value: counts.semua,          icon: Users, color: "var(--color-accent)" },
          { label: "Belum Diajukan",  value: counts.belum_diajukan, icon: Users, color: "var(--color-ink-3)" },
          { label: "Diajukan",        value: counts.diajukan,       icon: Users, color: "var(--color-warning)" },
          { label: "Disetujui",       value: counts.disetujui,      icon: Users, color: "var(--color-accent)" },
          { label: "Akad",           value: counts.akad,           icon: Users, color: "var(--color-success)" },
        ].map((card) => (
          <div key={card.label} style={{ backgroundColor: "var(--color-paper-2)", borderRadius: 8, padding: "14px 16px" }}>
            <div style={{ fontSize: 10, fontWeight: 700, color: "var(--color-ink-3)", textTransform: "uppercase", letterSpacing: "0.06em" }}>
              {card.label}
            </div>
            <div style={{ fontSize: 26, fontWeight: 700, color: card.color, marginTop: 4 }}>
              {card.value}
            </div>
          </div>
        ))}
      </div>

      {/* ── Stalled banner — only shown when it matters ── */}
      {stalledCount > 0 && (
        <div style={{
          display: "flex", alignItems: "center", gap: 8,
          padding: "10px 14px", marginBottom: 16,
          backgroundColor: "var(--color-warning-light)", borderRadius: 8,
          fontSize: 12, color: "var(--color-warning)", fontWeight: 600,
        }}>
          <AlertTriangle size={14} />
          {stalledCount} pembeli belum ada progres KPR selama {">"}5 hari — mungkin perlu ditindaklanjuti
        </div>
      )}

      {/* ── Search ── */}
      <div style={{ position: "relative", marginBottom: 16, maxWidth: 360 }}>
        <Search size={14} style={{ position: "absolute", left: 12, top: 11, color: "var(--color-ink-3)" }} />
        <input
          type="text" placeholder="Cari nama, email, atau unit…"
          value={search} onChange={(e) => setSearch(e.target.value)}
          style={{
            width: "100%", padding: "9px 12px 9px 34px",
            border: "1px solid rgba(14,13,11,0.15)", borderRadius: 8,
            fontSize: 13, outline: "none", boxSizing: "border-box",
          }}
        />
      </div>

      {/* ── Tabs ── */}
      <div style={{ display: "flex", gap: 4, marginBottom: 16, borderBottom: "1px solid rgba(14,13,11,0.08)" }}>
        {KPR_TABS.map((t) => (
          <button
            key={t.key}
            onClick={() => setTab(t.key)}
            style={{
              padding: "8px 14px", fontSize: 12, fontWeight: 600,
              background: "none", border: "none", cursor: "pointer",
              color: tab === t.key ? "var(--color-accent)" : "var(--color-ink-3)",
              borderBottom: tab === t.key ? "2px solid var(--color-accent)" : "2px solid transparent",
              display: "flex", alignItems: "center", gap: 6,
            }}
          >
            {t.label}
            <span style={{
              fontSize: 10, fontWeight: 700, padding: "1px 6px", borderRadius: 999,
              backgroundColor: tab === t.key ? "var(--color-accent-light)" : "var(--color-paper-2)",
              color: tab === t.key ? "var(--color-accent)" : "var(--color-ink-3)",
            }}>
              {counts[t.key] ?? 0}
            </span>
          </button>
        ))}
      </div>

      {/* ── Table ── */}
      {filtered.length === 0 ? (
        <div style={{ padding: "40px 0", textAlign: "center", color: "var(--color-ink-3)", fontSize: 13 }}>
          {buyerUnits.length === 0
            ? "Belum ada pembeli — buat booking pertama dari halaman Unit"
            : "Tidak ada pembeli yang cocok dengan pencarian"}
        </div>
      ) : (
        <div style={{ overflowX: "auto", border: "1px solid rgba(14,13,11,0.08)", borderRadius: 10 }}>
          <table style={{ width: "100%", borderCollapse: "collapse", fontSize: 13 }}>
            <thead>
              <tr style={{ backgroundColor: "var(--color-paper-2)", textAlign: "left" }}>
                {["Pembeli", "Unit", "Proyek", "Harga", "SPR", "Status KPR", "Aksi"].map((h) => (
                  <th key={h} style={{ padding: "10px 14px", fontSize: 10, fontWeight: 700, color: "var(--color-ink-3)", textTransform: "uppercase", letterSpacing: "0.05em" }}>
                    {h}
                  </th>
                ))}
              </tr>
            </thead>
            <tbody>
              {filtered.map((u) => (
                <tr key={u.id} style={{ borderTop: "1px solid rgba(14,13,11,0.06)" }}>
                  <td style={{ padding: "12px 14px" }}>
                    <div style={{ display: "flex", alignItems: "center", gap: 8 }}>
                      <div style={{ width: 26, height: 26, borderRadius: "50%", backgroundColor: "var(--color-accent-light)", display: "flex", alignItems: "center", justifyContent: "center", fontSize: 10, fontWeight: 700, color: "var(--color-accent)", flexShrink: 0 }}>
                        {u.buyer_name!.split(" ").map((n) => n[0]).join("").slice(0, 2)}
                      </div>
                      <div>
                        <div style={{ fontWeight: 600 }}>{u.buyer_name}</div>
                        <div style={{ fontSize: 11, color: "var(--color-ink-3)" }}>{u.buyer_email}</div>
                      </div>
                      {u.booking?.is_stalled && (
                        <AlertTriangle size={13} style={{ color: "var(--color-warning)", flexShrink: 0 }} />
                      )}
                    </div>
                  </td>
                  <td style={{ padding: "12px 14px", fontWeight: 600 }}>{u.unit_number}</td>
                  <td style={{ padding: "12px 14px", color: "var(--color-ink-3)" }}>{u.project_name}</td>
                  <td style={{ padding: "12px 14px", whiteSpace: "nowrap" }}>{rupiah(u.price)}</td>
                  <td style={{ padding: "12px 14px", fontSize: 11, color: "var(--color-warning)", fontWeight: 600 }}>
                    {u.booking?.spr_number}
                  </td>
                  <td style={{ padding: "12px 14px" }}>
                    <select
                      value={u.booking?.kpr_status}
                      disabled={updatingId === u.id || u.booking?.status !== "active"}
                      onChange={(e) => handleKPRChange(u, e.target.value as Booking["kpr_status"])}
                      style={{
                        padding: "5px 8px", borderRadius: 6, fontSize: 12, fontWeight: 600,
                        border: `1px solid ${kprStatusColor(u.booking!.kpr_status)}44`,
                        color: kprStatusColor(u.booking!.kpr_status),
                        backgroundColor: "white", cursor: u.booking?.status === "active" ? "pointer" : "not-allowed",
                      }}
                    >
                      <option value="belum_diajukan">Belum Diajukan</option>
                      <option value="diajukan">Diajukan</option>
                      <option value="disetujui">Disetujui</option>
                      <option value="akad">Akad</option>
                    </select>
                  </td>
                  <td style={{ padding: "12px 14px" }}>
                    {updatingId === u.id && (
                      <Loader2 size={14} style={{ animation: "spin 1s linear infinite", color: "var(--color-ink-3)" }} />
                    )}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
}
