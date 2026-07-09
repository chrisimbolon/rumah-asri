"use client";
// =============================================================================
// === frontend/app/dashboard/audit/page.tsx ===
// Sprint 27: Financial Audit Trail — the frontend half of FinancialAudit.
// Read-only by design, same as the backend endpoint it consumes — there
// is no create/edit UI here on purpose, matching FinancialAudit.log()'s
// "only ever written by the real actions that trigger it" contract.
//
// Styled to match the Pelacak Pembayaran page's conventions (metric
// cards, filter tabs, data-table), since this is reading the same
// underlying financial reality from a different angle.
// =============================================================================

import { FinancialAuditEntry, financialAuditApi } from "@/lib/api/payments";
import { rupiah } from "@/lib/mock-data";
import {
  Ban,
  Calendar,
  CircleDollarSign,
  Clock,
  FileClock,
  Filter,
  Landmark,
  Loader2,
  PackageCheck,
  ShieldCheck,
  Tag,
  TrendingDown,
  TrendingUp,
} from "lucide-react";
import { useEffect, useMemo, useState } from "react";

// ── Per-action display metadata ─────────────────────────────────
// Mirrors the ACTION_TYPE_META pattern already used for
// NextActionsPanel/ActionCard (components/dashboard/TaskPanels.tsx) —
// same "icon + color + label" shape, applied here to
// FinancialAudit.Action's 9 real values instead.
const ACTION_META: Record<string, { icon: typeof CircleDollarSign; color: string; bg: string }> = {
  payment_recorded:       { icon: CircleDollarSign, color: "var(--color-success)", bg: "var(--color-success-light)" },
  payment_status_changed: { icon: Tag,              color: "var(--color-info)",    bg: "var(--color-accent-light)"  },
  payment_marked_overdue: { icon: TrendingDown,      color: "var(--color-danger)",  bg: "var(--color-danger-light)"  },
  booking_created:        { icon: Calendar,          color: "var(--color-accent)", bg: "var(--color-accent-light)"  },
  booking_cancelled:      { icon: Ban,               color: "var(--color-ink-3)",  bg: "var(--color-paper-2)"       },
  booking_expired:        { icon: Clock,             color: "var(--color-warning)", bg: "var(--color-gold-light)"   },
  booking_converted:      { icon: PackageCheck,      color: "var(--color-success)", bg: "var(--color-success-light)" },
  price_changed:          { icon: TrendingUp,        color: "var(--color-gold)",    bg: "var(--color-gold-light)"   },
  kpr_advanced:           { icon: Landmark,          color: "var(--color-accent)", bg: "var(--color-accent-light)"  },
};
const DEFAULT_META = { icon: FileClock, color: "var(--color-ink-3)", bg: "var(--color-paper-2)" };

// ── Date/time formatter — "2026-07-08T12:30:45Z" → "8 Jul 2026, 19:30" ──
function formatDateTime(iso: string): string {
  if (!iso) return "—";
  try {
    return new Date(iso).toLocaleString("id-ID", {
      day: "numeric", month: "short", year: "numeric",
      hour: "2-digit", minute: "2-digit",
    });
  } catch {
    return iso;
  }
}

function formatAr(value: number | null): string {
  if (value === null) return "—";
  return rupiah(value);
}

// ─────────────────────────────────────────────────────────────
export default function FinancialAuditPage() {
  const [entries,       setEntries]       = useState<FinancialAuditEntry[]>([]);
  const [loading,       setLoading]       = useState(true);
  const [error,         setError]         = useState<string | null>(null);
  const [actionFilter,  setActionFilter]  = useState<string>("semua");
  const [unitFilter,    setUnitFilter]    = useState<string>("semua");

  useEffect(() => {
    financialAuditApi.list()
      .then(setEntries)
      .catch(() => setError("Gagal memuat jejak audit keuangan"))
      .finally(() => setLoading(false));
  }, []);

  // Derived from the loaded entries themselves — no extra API call
  // needed just to populate a unit filter dropdown.
  const availableUnits = useMemo(() => {
    const units = new Set(entries.map((e) => e.unit_number).filter(Boolean) as string[]);
    return [...units].sort();
  }, [entries]);

  const availableActions = useMemo(() => {
    const map = new Map<string, string>();
    for (const e of entries) map.set(e.action, e.action_display);
    return [...map.entries()];
  }, [entries]);

  const filtered = entries.filter((e) => {
    if (actionFilter !== "semua" && e.action !== actionFilter) return false;
    if (unitFilter   !== "semua" && e.unit_number !== unitFilter) return false;
    return true;
  });

  const systemTriggeredCount = entries.filter((e) => e.changed_by_name === "Sistem (Otomatis)").length;

  if (loading) {
    return (
      <div style={{ display: "flex", alignItems: "center", justifyContent: "center", height: 300, gap: 10, color: "var(--color-ink-3)" }}>
        <Loader2 size={18} style={{ animation: "spin 1s linear infinite" }} />
        <span style={{ fontSize: 13 }}>Memuat jejak audit…</span>
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

  return (
    <div style={{ maxWidth: 1100, margin: "0 auto" }}>

      {/* ── Page header ── */}
      <div className="page-header">
        <h1 className="page-title">Audit Keuangan</h1>
        <p className="page-subtitle">
          Jejak setiap tindakan finansial — siapa, kapan, dan dampaknya terhadap AR
        </p>
      </div>

      {/* ── Metric cards ── */}
      <div style={{ display: "grid", gridTemplateColumns: "repeat(3, 1fr)", gap: 12, marginBottom: 20 }}>
        {[
          { label: "Total Entri",           value: String(entries.length),          sub: "tindakan tercatat",       icon: FileClock,   color: "var(--color-accent)",  bg: "var(--color-accent-light)"  },
          { label: "Tindakan Manual",       value: String(entries.length - systemTriggeredCount), sub: "oleh pengguna",  icon: ShieldCheck, color: "var(--color-success)", bg: "var(--color-success-light)" },
          { label: "Otomatis (Sistem)",     value: String(systemTriggeredCount),    sub: "cron — tanpa aktor manusia", icon: Clock,      color: "var(--color-warning)", bg: "var(--color-gold-light)"    },
        ].map((s) => (
          <div key={s.label} className="metric-card">
            <div style={{ display: "flex", alignItems: "flex-start", justifyContent: "space-between", marginBottom: 10 }}>
              <div className="metric-label">{s.label}</div>
              <div style={{ width: 30, height: 30, borderRadius: 6, backgroundColor: s.bg, display: "flex", alignItems: "center", justifyContent: "center", flexShrink: 0 }}>
                <s.icon size={14} style={{ color: s.color }} />
              </div>
            </div>
            <div className="metric-value" style={{ fontSize: 28 }}>{s.value}</div>
            <div className="metric-sub">{s.sub}</div>
          </div>
        ))}
      </div>

      {/* ── Filters + table ── */}
      <div className="card" style={{ padding: 0, overflow: "hidden" }}>

        {/* Filter bar */}
        <div style={{ display: "flex", alignItems: "center", gap: 12, padding: "12px 16px", borderBottom: "1px solid rgba(14,13,11,0.08)", flexWrap: "wrap" }}>
          <div style={{ display: "flex", alignItems: "center", gap: 6, fontSize: 12, color: "var(--color-ink-3)", fontWeight: 600 }}>
            <Filter size={12} /> Filter:
          </div>

          <select
            value={actionFilter}
            onChange={(e) => setActionFilter(e.target.value)}
            style={{ fontSize: 12, padding: "6px 10px", borderRadius: 6, border: "1px solid rgba(14,13,11,0.12)", backgroundColor: "white", color: "var(--color-ink)" }}
          >
            <option value="semua">Semua Tindakan</option>
            {availableActions.map(([value, label]) => (
              <option key={value} value={value}>{label}</option>
            ))}
          </select>

          <select
            value={unitFilter}
            onChange={(e) => setUnitFilter(e.target.value)}
            style={{ fontSize: 12, padding: "6px 10px", borderRadius: 6, border: "1px solid rgba(14,13,11,0.12)", backgroundColor: "white", color: "var(--color-ink)" }}
          >
            <option value="semua">Semua Unit</option>
            {availableUnits.map((u) => (
              <option key={u} value={u}>{u}</option>
            ))}
          </select>

          <span style={{ marginLeft: "auto", fontSize: 12, color: "var(--color-ink-3)" }}>
            Menampilkan {filtered.length} dari {entries.length} entri
          </span>
        </div>

        {/* Table */}
        <table className="data-table">
          <thead>
            <tr>
              <th>Waktu</th>
              <th>Tindakan</th>
              <th>Unit</th>
              <th>Oleh</th>
              <th>Perubahan</th>
              <th>AR Sebelum</th>
              <th>AR Sesudah</th>
            </tr>
          </thead>
          <tbody>
            {filtered.map((e) => {
              const meta = ACTION_META[e.action] ?? DEFAULT_META;
              const arChanged = e.ar_before !== null && e.ar_after !== null && e.ar_before !== e.ar_after;
              const isSystem  = e.changed_by_name === "Sistem (Otomatis)";
              return (
                <tr key={e.id}>
                  <td style={{ fontSize: 12, color: "var(--color-ink-3)", whiteSpace: "nowrap" }}>
                    {formatDateTime(e.changed_at)}
                  </td>
                  <td>
                    <div style={{ display: "flex", alignItems: "center", gap: 8 }}>
                      <div style={{ width: 26, height: 26, borderRadius: 6, backgroundColor: meta.bg, display: "flex", alignItems: "center", justifyContent: "center", flexShrink: 0 }}>
                        <meta.icon size={13} style={{ color: meta.color }} />
                      </div>
                      <span style={{ fontSize: 12, fontWeight: 500 }}>{e.action_display}</span>
                    </div>
                  </td>
                  <td>
                    {e.unit_number
                      ? <span className="badge badge-blue">{e.unit_number}</span>
                      : <span style={{ fontSize: 12, color: "var(--color-ink-3)" }}>—</span>}
                  </td>
                  <td>
                    <span style={{
                      fontSize: 12,
                      color: isSystem ? "var(--color-ink-3)" : "var(--color-ink)",
                      fontStyle: isSystem ? "italic" : "normal",
                    }}>
                      {e.changed_by_name}
                    </span>
                  </td>
                  <td style={{ fontSize: 12, color: "var(--color-ink-3)", maxWidth: 220 }}>
                    {e.old_value || e.new_value
                      ? <span>{e.old_value || "—"} → <strong style={{ color: "var(--color-ink)" }}>{e.new_value || "—"}</strong></span>
                      : "—"}
                    {e.notes && (
                      <div style={{ fontSize: 11, color: "var(--color-ink-3)", opacity: 0.8, marginTop: 2 }}>
                        {e.notes}
                      </div>
                    )}
                  </td>
                  <td style={{ fontSize: 12, color: "var(--color-ink-3)" }}>
                    {formatAr(e.ar_before)}
                  </td>
                  <td>
                    <span style={{
                      fontSize: 12, fontWeight: arChanged ? 600 : 400,
                      color: arChanged
                        ? (e.ar_after! < e.ar_before! ? "var(--color-success)" : "var(--color-danger)")
                        : "var(--color-ink-3)",
                    }}>
                      {formatAr(e.ar_after)}
                    </span>
                  </td>
                </tr>
              );
            })}
            {filtered.length === 0 && (
              <tr>
                <td colSpan={7} style={{ textAlign: "center", padding: 40, color: "var(--color-ink-3)", fontSize: 13 }}>
                  Tidak ada entri audit untuk filter ini
                </td>
              </tr>
            )}
          </tbody>
        </table>
      </div>
    </div>
  );
}
