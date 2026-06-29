"use client";
// ================================================
// frontend/app/dashboard/payments/page.tsx 
// ================================================
/**
 * Payments tracker — wired to real payments API. - Payment has data on DB, but not via CRUD
 *
 * Field mapping from mock → real API:
 *   pembeli      → buyer_name
 *   unit         → unit_number
 *   jenis        → payment_type
 *   jatuh_tempo  → due_date (YYYY-MM-DD, formatted for display)
 *   jumlah       → amount
 *   bank         → bank
 *
 * Buyer summary cards at bottom are derived from grouped payment data 
 * since there is no dedicated /api/buyers/ endpoint yet (Sprint 2).
 */

import { Payment, paymentsApi } from "@/lib/api/payments";
import { badgeStatus, labelStatus, rupiah } from "@/lib/mock-data";
import {
  AlertCircle,
  CheckCircle2,
  Clock,
  Download,
  Filter,
  Loader2,
  MessageSquare,
  TrendingUp,
  Wallet,
  XCircle,
} from "lucide-react";
import { useEffect, useState } from "react";

// ── Status filter tabs ────────────────────────────────────────
const TABS = [
  { key: "semua",       label: "Semua" },
  { key: "lunas",       label: "Lunas" },
  { key: "menunggu",    label: "Menunggu" },
  { key: "menunggak",   label: "Menunggak" },
  { key: "akan_datang", label: "Akan Datang" },
];

// ── Date formatter — "2026-03-01" → "1 Mar 2026" ─────────────
function formatDate(iso: string): string {
  if (!iso) return "—";
  try {
    return new Date(iso).toLocaleDateString("id-ID", {
      day: "numeric", month: "short", year: "numeric",
    });
  } catch {
    return iso;
  }
}

// ── Status icon ───────────────────────────────────────────────
function StatusIcon({ status }: { status: string }) {
  if (status === "lunas")     return <CheckCircle2 size={15} style={{ color: "var(--color-success)" }} />;
  if (status === "menunggak") return <XCircle      size={15} style={{ color: "var(--color-danger)"  }} />;
  if (status === "menunggu")  return <Clock        size={15} style={{ color: "var(--color-warning)" }} />;
  return                             <Clock        size={15} style={{ color: "var(--color-info)"    }} />;
}

// ── Buyer summary derived from payments ───────────────────────
function deriveBuyerSummary(payments: Payment[]) {
  const map = new Map<string, { buyer_name: string; unit_number: string; bank: string; total: number; status: string }>();
  for (const p of payments) {
    if (!p.buyer_name) continue;
    const key = p.buyer_name;
    if (!map.has(key)) {
      map.set(key, { buyer_name: p.buyer_name, unit_number: p.unit_number, bank: p.bank, total: 0, status: "lunas" });
    }
    const entry = map.get(key)!;
    entry.total += p.amount;
    // Worst status wins: menunggak > menunggu > akan_datang > lunas
    if (p.status === "menunggak") entry.status = "menunggak";
    else if (p.status === "menunggu"    && entry.status !== "menunggak") entry.status = "menunggu";
    else if (p.status === "akan_datang" && !["menunggak","menunggu"].includes(entry.status)) entry.status = "akan_datang";
  }
  return [...map.values()];
}

// ─────────────────────────────────────────────────────────────
export default function PaymentsPage() {
  const [payments,   setPayments]   = useState<Payment[]>([]);
  const [loading,    setLoading]    = useState(true);
  const [error,      setError]      = useState<string | null>(null);
  const [activeTab,  setActiveTab]  = useState("semua");

  useEffect(() => {
    paymentsApi.list()
      .then(setPayments)
      .catch(() => setError("Gagal memuat data pembayaran"))
      .finally(() => setLoading(false));
  }, []);

  if (loading) {
    return (
      <div style={{ display: "flex", alignItems: "center", justifyContent: "center", height: 300, gap: 10, color: "var(--color-ink-3)" }}>
        <Loader2 size={18} style={{ animation: "spin 1s linear infinite" }} />
        <span style={{ fontSize: 13 }}>Memuat pembayaran…</span>
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

  const filtered      = activeTab === "semua" ? payments : payments.filter((p) => p.status === activeTab);
  const totalTagihan  = payments.reduce((s, p) => s + p.amount, 0);
  const totalLunas    = payments.filter((p) => p.status === "lunas").reduce((s, p) => s + p.amount, 0);
  const totalMenunggak = payments.filter((p) => p.status === "menunggak").reduce((s, p) => s + p.amount, 0);
  const countMenunggak = payments.filter((p) => p.status === "menunggak").length;
  const buyerSummary   = deriveBuyerSummary(payments);

  return (
    <div style={{ maxWidth: 1100, margin: "0 auto" }}>

      {/* ── Page header ── */}
      <div className="page-header" style={{ display: "flex", alignItems: "flex-start", justifyContent: "space-between" }}>
        <div>
          <h1 className="page-title">Pelacak Pembayaran</h1>
          <p className="page-subtitle">Jadwal & status pembayaran semua unit</p>
        </div>
        <button className="btn-ghost" style={{ flexShrink: 0 }}>
          <Download size={14} /> Ekspor Laporan
        </button>
      </div>

      {/* ── Metric cards ── */}
      <div style={{ display: "grid", gridTemplateColumns: "repeat(4, 1fr)", gap: 12, marginBottom: 20 }}>
        {[
          { label: "Total Tagihan",   value: rupiah(totalTagihan),   sub: `${payments.length} transaksi`,                                                          icon: Wallet,       color: "var(--color-accent)",  bg: "var(--color-accent-light)"  },
          { label: "Total Lunas",     value: rupiah(totalLunas),     sub: `${payments.filter((p) => p.status === "lunas").length} transaksi`,                       icon: CheckCircle2, color: "var(--color-success)", bg: "var(--color-success-light)" },
          { label: "Menunggak",       value: rupiah(totalMenunggak), sub: `${countMenunggak} transaksi`,                                                             icon: AlertCircle,  color: "var(--color-danger)",  bg: "var(--color-danger-light)"  },
          { label: "Tingkat Koleksi", value: totalTagihan > 0 ? `${Math.round((totalLunas / totalTagihan) * 100)}%` : "0%", sub: "pembayaran lancar",               icon: TrendingUp,   color: "var(--color-gold)",    bg: "var(--color-gold-light)"    },
        ].map((s) => (
          <div key={s.label} className="metric-card">
            <div style={{ display: "flex", alignItems: "flex-start", justifyContent: "space-between", marginBottom: 10 }}>
              <div className="metric-label">{s.label}</div>
              <div style={{ width: 30, height: 30, borderRadius: 6, backgroundColor: s.bg, display: "flex", alignItems: "center", justifyContent: "center", flexShrink: 0 }}>
                <s.icon size={14} style={{ color: s.color }} />
              </div>
            </div>
            <div className="metric-value" style={{ fontSize: s.value.length > 10 ? 18 : 28 }}>{s.value}</div>
            <div className="metric-sub">{s.sub}</div>
          </div>
        ))}
      </div>

      {/* ── Alert — menunggak ── */}
      {countMenunggak > 0 && (
        <div style={{ display: "flex", alignItems: "flex-start", gap: 12, padding: "14px 16px", backgroundColor: "var(--color-danger-light)", border: "1px solid rgba(185,28,28,0.15)", borderRadius: 6, marginBottom: 20 }}>
          <AlertCircle size={16} style={{ color: "var(--color-danger)", flexShrink: 0, marginTop: 1 }} />
          <div>
            <div style={{ fontSize: 13, fontWeight: 600, color: "var(--color-danger-text)" }}>
              {countMenunggak} pembayaran menunggak — segera tindak lanjuti!!
            </div>
            <div style={{ fontSize: 12, color: "var(--color-danger-text)", opacity: 0.75, marginTop: 2 }}>
              Kirim pengingat WhatsApp atau hubungi pembeli langsung untuk menghindari denda keterlambatan.
            </div>
          </div>
          <button className="btn-danger btn-sm" style={{ flexShrink: 0, marginLeft: "auto" }}>
            <MessageSquare size={12} /> Kirim Pengingat
          </button>
        </div>
      )}

      {/* ── Filter tabs + table ── */}
      <div className="card" style={{ padding: 0, overflow: "hidden" }}>

        {/* Tabs */}
        <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between", padding: "0 16px", borderBottom: "1px solid rgba(14,13,11,0.08)" }}>
          <div style={{ display: "flex", gap: 0 }}>
            {TABS.map((tab) => {
              const count = tab.key === "semua" ? payments.length : payments.filter((p) => p.status === tab.key).length;
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
          <button className="btn-ghost btn-sm" style={{ display: "flex", alignItems: "center", gap: 6 }}>
            <Filter size={12} /> Filter
          </button>
        </div>

        {/* Table */}
        <table className="data-table">
          <thead>
            <tr>
              <th>Pembeli</th>
              <th>Unit</th>
              <th>Jenis Pembayaran</th>
              <th>Jatuh Tempo</th>
              <th>Jumlah</th>
              <th>Bank / Metode</th>
              <th>Status</th>
              <th>Aksi</th>
            </tr>
          </thead>
          <tbody>
            {filtered.map((p) => (
              <tr key={p.id}>
                <td>
                  <div style={{ display: "flex", alignItems: "center", gap: 8 }}>
                    <div style={{ width: 28, height: 28, borderRadius: "50%", backgroundColor: "var(--color-accent-light)", display: "flex", alignItems: "center", justifyContent: "center", fontSize: 10, fontWeight: 700, color: "var(--color-accent)", flexShrink: 0 }}>
                      {(p.buyer_name ?? "?").split(" ").map((n) => n[0]).join("").slice(0, 2)}
                    </div>
                    <span style={{ fontSize: 13, fontWeight: 500 }}>{p.buyer_name ?? "—"}</span>
                  </div>
                </td>
                <td><span className="badge badge-blue">{p.unit_number}</span></td>
                <td style={{ fontSize: 12, color: "var(--color-ink-3)" }}>{p.payment_type}</td>
                <td>
                  <div style={{ display: "flex", alignItems: "center", gap: 5, fontSize: 12 }}>
                    <Clock size={12} style={{ color: "var(--color-ink-3)" }} />
                    <span style={{ color: p.status === "menunggak" ? "var(--color-danger)" : "var(--color-ink)", fontWeight: p.status === "menunggak" ? 600 : 400 }}>
                      {formatDate(p.due_date)}
                    </span>
                  </div>
                </td>
                <td>
                  <span style={{ fontSize: 13, fontWeight: 600, color: p.status === "menunggak" ? "var(--color-danger)" : "var(--color-ink)" }}>
                    {rupiah(p.amount)}
                  </span>
                </td>
                <td style={{ fontSize: 12, color: "var(--color-ink-3)" }}>{p.bank || "—"}</td>
                <td>
                  <div style={{ display: "flex", alignItems: "center", gap: 6 }}>
                    <StatusIcon status={p.status} />
                    <span className={`badge ${badgeStatus(p.status)}`}>
                      {p.status_display || labelStatus(p.status)}
                    </span>
                  </div>
                </td>
                <td>
                  {p.status === "menunggak"   && <button className="btn-danger btn-sm"  style={{ display: "inline-flex", alignItems: "center", gap: 4 }}><MessageSquare size={11} /> Ingatkan</button>}
                  {p.status === "menunggu"    && <button className="btn-success btn-sm" style={{ display: "inline-flex", alignItems: "center", gap: 4 }}><CheckCircle2  size={11} /> Konfirmasi</button>}
                  {p.status === "lunas"       && <button className="btn-ghost btn-sm"   style={{ display: "inline-flex", alignItems: "center", gap: 4 }}><Download      size={11} /> Kuitansi</button>}
                  {(p.status === "akan_datang" || p.status === "proses_bank") && <span style={{ fontSize: 12, color: "var(--color-ink-3)" }}>—</span>}
                </td>
              </tr>
            ))}
            {filtered.length === 0 && (
              <tr>
                <td colSpan={8} style={{ textAlign: "center", padding: 40, color: "var(--color-ink-3)", fontSize: 13 }}>
                  Tidak ada data pembayaran untuk filter ini
                </td>
              </tr>
            )}
          </tbody>
        </table>

        {/* Table footer */}
        <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between", padding: "12px 16px", borderTop: "1px solid rgba(14,13,11,0.06)", backgroundColor: "var(--color-paper)" }}>
          <span style={{ fontSize: 12, color: "var(--color-ink-3)" }}>
            Menampilkan {filtered.length} dari {payments.length} transaksi
          </span>
          <div style={{ display: "flex", gap: 8 }}>
            {["KPR Summary", "Cash Summary", "Semua Kuitansi"].map((btn) => (
              <button key={btn} className="btn-ghost btn-sm" style={{ display: "inline-flex", alignItems: "center", gap: 4 }}>
                <Download size={11} /> {btn}
              </button>
            ))}
          </div>
        </div>
      </div>

      {/* ── Buyer payment summary cards — derived from real payment data ── */}
      {buyerSummary.length > 0 && (
        <div style={{ marginTop: 20 }}>
          <div className="section-title">Ringkasan per Pembeli</div>
          <div style={{ display: "grid", gridTemplateColumns: "repeat(5, 1fr)", gap: 10 }}>
            {buyerSummary.map((b) => (
              <div key={b.buyer_name} className="card" style={{ padding: 14, textAlign: "center" }}>
                <div style={{ width: 36, height: 36, borderRadius: "50%", backgroundColor: "var(--color-accent-light)", display: "flex", alignItems: "center", justifyContent: "center", fontSize: 12, fontWeight: 700, color: "var(--color-accent)", margin: "0 auto 10px" }}>
                  {b.buyer_name.split(" ").map((n) => n[0]).join("").slice(0, 2)}
                </div>
                <div style={{ fontSize: 12, fontWeight: 600, color: "var(--color-ink)", marginBottom: 2 }}>
                  {b.buyer_name.split(" ")[0]}
                </div>
                <div style={{ fontSize: 10, color: "var(--color-ink-3)", marginBottom: 8 }}>
                  Unit {b.unit_number} · {b.bank || "—"}
                </div>
                <div style={{ fontSize: 13, fontWeight: 700, color: "var(--color-ink)", marginBottom: 6 }}>
                  {rupiah(b.total)}
                </div>
                <span className={`badge ${badgeStatus(b.status)}`}>
                  {labelStatus(b.status)}
                </span>
              </div>
            ))}
          </div>
        </div>
      )}

    </div>
  );
}
