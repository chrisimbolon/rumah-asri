"use client";

/**
 * RumahAsri — Buyer Portal Page
 * Wired to real Django API — no more mock data!!
 */

import { useEffect, useState } from "react";
import Link from "next/link";
import {
  CheckCircle2, Circle, Camera, FileText,
  ChevronLeft, MapPin, Calendar, Home,
  Download, MessageCircle, Star, Loader2,
  AlertCircle,
} from "lucide-react";
import { useAuth } from "@/context/AuthContext";
import { buyerApi } from "@/lib/api/buyer";
import type {
  BuyerMeResponse,
  BuyerTimelineResponse,
  BuyerPaymentsResponse,
  BuyerDocumentsResponse,
} from "@/lib/api/buyer";

// ── Helper — format Rupiah ────────────────────────────────────
function rupiah(n: number): string {
  return new Intl.NumberFormat("id-ID", {
    style: "currency", currency: "IDR",
    minimumFractionDigits: 0, maximumFractionDigits: 0,
  }).format(n);
}

// ── Helper — format date ──────────────────────────────────────
function formatDate(dateStr: string | null): string {
  if (!dateStr) return "-";
  try {
    return new Date(dateStr).toLocaleDateString("id-ID", {
      day: "numeric", month: "short", year: "numeric",
    });
  } catch {
    return dateStr;
  }
}

// ── Status badge colour ───────────────────────────────────────
function paymentStatusColor(status: string): string {
  const map: Record<string, string> = {
    lunas:       "#34D399",
    menunggak:   "#F87171",
    menunggu:    "#FBBF24",
    akan_datang: "#60A5FA",
    proses_bank: "#A78BFA",
  };
  return map[status] ?? "#9CA3AF";
}

// ─────────────────────────────────────────────────────────────
export default function BuyerPortalPage() {
  const { user, logout } = useAuth();

  // ── State ─────────────────────────────────────────────────
  const [meData,       setMeData]       = useState<BuyerMeResponse | null>(null);
  const [timeline,     setTimeline]     = useState<BuyerTimelineResponse | null>(null);
  const [payments,     setPayments]     = useState<BuyerPaymentsResponse | null>(null);
  const [documents,    setDocuments]    = useState<BuyerDocumentsResponse | null>(null);
  const [isLoading,    setIsLoading]    = useState(true);
  const [error,        setError]        = useState<string | null>(null);
  const [activeTab,    setActiveTab]    = useState<"progress" | "foto" | "dokumen" | "pembayaran">("progress");

  // ── Fetch all buyer data on mount ─────────────────────────
  useEffect(() => {
    async function fetchAll() {
      setIsLoading(true);
      setError(null);
      try {
        const [me, tl, pay, docs] = await Promise.all([
          buyerApi.getMe(),
          buyerApi.getTimeline(),
          buyerApi.getPayments(),
          buyerApi.getDocuments(),
        ]);
        setMeData(me);
        setTimeline(tl);
        setPayments(pay);
        setDocuments(docs);
      } catch (err: unknown) {
        const axiosErr = err as { response?: { data?: { message?: string } } };
        setError(
          axiosErr.response?.data?.message ??
          "Gagal memuat data. Periksa koneksi Anda."
        );
      } finally {
        setIsLoading(false);
      }
    }
    fetchAll();
  }, []);

  // ── Loading state ─────────────────────────────────────────
  if (isLoading) {
    return (
      <div style={{ minHeight: "100vh", backgroundColor: "#0A0E1A", display: "flex", alignItems: "center", justifyContent: "center", flexDirection: "column", gap: 16 }}>
        <Loader2 size={32} style={{ color: "#B8935A", animation: "spin 1s linear infinite" }}/>
        <div style={{ fontSize: 14, color: "rgba(255,255,255,0.5)" }}>Memuat data properti Anda...</div>
      </div>
    );
  }

  // ── Error state ───────────────────────────────────────────
  if (error || !meData) {
    return (
      <div style={{ minHeight: "100vh", backgroundColor: "#0A0E1A", display: "flex", alignItems: "center", justifyContent: "center", flexDirection: "column", gap: 16, padding: 24 }}>
        <AlertCircle size={32} style={{ color: "#F87171" }}/>
        <div style={{ fontSize: 16, fontWeight: 600, color: "white" }}>Terjadi Kesalahan</div>
        <div style={{ fontSize: 13, color: "rgba(255,255,255,0.5)", textAlign: "center", maxWidth: 320 }}>
          {error ?? "Unit belum ditetapkan. Hubungi developer atau agen penjualan."}
        </div>
        <button onClick={logout} style={{ marginTop: 8, padding: "8px 20px", backgroundColor: "rgba(255,255,255,0.1)", border: "1px solid rgba(255,255,255,0.2)", borderRadius: 6, color: "white", fontSize: 13, cursor: "pointer", fontFamily: "var(--font-sans)" }}>
          Keluar
        </button>
      </div>
    );
  }

  const { buyer, unit, project } = meData;

  return (
    <div style={{ minHeight: "100vh", backgroundColor: "#0A0E1A", fontFamily: "var(--font-sans)", color: "white" }}>

      {/* ── NAV ── */}
      <nav style={{
        borderBottom: "1px solid rgba(255,255,255,0.07)",
        padding: "16px 32px",
        display: "flex", alignItems: "center", justifyContent: "space-between",
        position: "sticky", top: 0, zIndex: 50,
        backgroundColor: "rgba(10,14,26,0.92)",
        backdropFilter: "blur(12px)",
      }}>
        <div style={{ fontFamily: "var(--font-serif)", fontSize: 20, fontWeight: 600, color: "white" }}>
          Rumah<span style={{ color: "#B8935A" }}>Asri</span>
        </div>
        <div style={{ fontSize: 11, color: "rgba(255,255,255,0.35)", textTransform: "uppercase", letterSpacing: "0.12em" }}>
          Portal Pembeli
        </div>
        <div style={{ display: "flex", alignItems: "center", gap: 10 }}>
          <div style={{
            width: 32, height: 32, borderRadius: "50%",
            background: "linear-gradient(135deg, #1A3FA8, #B8935A)",
            display: "flex", alignItems: "center", justifyContent: "center",
            fontSize: 11, fontWeight: 700, color: "white",
          }}>
            {buyer.full_name.split(" ").map(n => n[0]).join("").slice(0, 2).toUpperCase()}
          </div>
          <span style={{ fontSize: 13, color: "rgba(255,255,255,0.8)", fontWeight: 500 }}>
            {buyer.full_name}
          </span>
        </div>
      </nav>

      {/* ── CONTENT ── */}
      <div style={{ maxWidth: 800, margin: "0 auto", padding: "40px 24px 80px" }}>

        {/* ── Welcome ── */}
        <div style={{ marginBottom: 36 }}>
          <div style={{ fontSize: 11, color: "rgba(255,255,255,0.35)", textTransform: "uppercase", letterSpacing: "0.15em", marginBottom: 10 }}>
            Selamat datang kembali
          </div>
          <h1 style={{ fontFamily: "var(--font-serif)", fontSize: "clamp(28px,5vw,44px)", fontWeight: 300, color: "white", lineHeight: 1.15, marginBottom: 8 }}>
            Halo, <span style={{ fontStyle: "italic", color: "#B8935A" }}>
              {buyer.full_name.split(" ")[0]}
            </span> 👋
          </h1>
          <p style={{ fontSize: 14, color: "rgba(255,255,255,0.45)", lineHeight: 1.7, maxWidth: 480 }}>
            Rumah impian Anda sedang dibangun dengan penuh dedikasi.
            Pantau setiap tahap pembangunan secara real-time di sini.
          </p>
        </div>

        {/* ── Property hero card ── */}
        <div style={{
          background: "linear-gradient(135deg, rgba(26,63,168,0.15) 0%, rgba(184,147,90,0.08) 100%)",
          border: "1px solid rgba(255,255,255,0.08)",
          borderRadius: 16, padding: 28, marginBottom: 16,
          position: "relative", overflow: "hidden",
        }}>
          {/* Glow */}
          <div style={{
            position: "absolute", top: -60, right: -60,
            width: 200, height: 200, borderRadius: "50%",
            background: "radial-gradient(circle, rgba(184,147,90,0.12) 0%, transparent 70%)",
            pointerEvents: "none",
          }}/>

          {/* Header */}
          <div style={{ display: "flex", alignItems: "flex-start", justifyContent: "space-between", marginBottom: 28 }}>
            <div>
              <div style={{ fontSize: 11, color: "rgba(255,255,255,0.35)", textTransform: "uppercase", letterSpacing: "0.12em", marginBottom: 6 }}>
                Properti Anda
              </div>
              <div style={{ fontSize: 22, fontWeight: 700, color: "white", marginBottom: 4 }}>
                Unit {unit.unit_number}
              </div>
              <div style={{ fontSize: 13, color: "rgba(255,255,255,0.45)" }}>
                {unit.unit_type} · {unit.land_area}m² · {project.name}
              </div>
            </div>
            <div style={{
              background: "rgba(14,123,82,0.2)", border: "1px solid rgba(14,123,82,0.4)",
              borderRadius: 999, padding: "6px 14px",
              fontSize: 12, fontWeight: 600, color: "#34D399",
              display: "flex", alignItems: "center", gap: 6,
            }}>
              <div style={{ width: 6, height: 6, borderRadius: "50%", backgroundColor: "#34D399" }}/>
              {unit.status_display}
            </div>
          </div>

          {/* BIG % */}
          <div style={{ textAlign: "center", marginBottom: 28 }}>
            <div style={{
              fontFamily: "var(--font-serif)",
              fontSize: "clamp(80px, 16vw, 120px)",
              fontWeight: 600, lineHeight: 1,
              background: "linear-gradient(135deg, #FFFFFF 0%, #B8935A 100%)",
              WebkitBackgroundClip: "text",
              WebkitTextFillColor: "transparent",
              backgroundClip: "text",
            }}>
              {unit.progress}
            </div>
            <div style={{ fontSize: 18, color: "rgba(255,255,255,0.4)", marginTop: -8, fontWeight: 300 }}>
              persen selesai
            </div>
          </div>

          {/* Progress bar */}
          <div style={{ backgroundColor: "rgba(255,255,255,0.08)", borderRadius: 999, height: 12, overflow: "hidden", marginBottom: 10 }}>
            <div style={{
              height: "100%", borderRadius: 999,
              background: "linear-gradient(90deg, #1A3FA8 0%, #34D399 100%)",
              width: `${unit.progress}%`, transition: "width 1s ease",
              boxShadow: "0 0 12px rgba(52,211,153,0.4)",
            }}/>
          </div>

          <div style={{ display: "flex", justifyContent: "space-between", fontSize: 11, color: "rgba(255,255,255,0.3)" }}>
            <span>Lokasi: {project.location}</span>
            {timeline && <span>{timeline.done_count} dari {timeline.total_phases} fase selesai</span>}
            {unit.target_completion && <span>Target: {formatDate(unit.target_completion)}</span>}
          </div>
        </div>

        {/* ── Quick info strip ── */}
        <div style={{ display: "grid", gridTemplateColumns: "repeat(3, 1fr)", gap: 10, marginBottom: 24 }}>
          {[
            { icon: Home,     label: "Tipe Unit",    value: unit.unit_type },
            { icon: MapPin,   label: "Lokasi",       value: project.location },
            { icon: Calendar, label: "Serah Terima", value: unit.target_completion ? formatDate(unit.target_completion) : "-" },
          ].map((item) => (
            <div key={item.label} style={{
              backgroundColor: "rgba(255,255,255,0.04)",
              border: "1px solid rgba(255,255,255,0.06)",
              borderRadius: 10, padding: "14px 16px",
              display: "flex", alignItems: "center", gap: 12,
            }}>
              <item.icon size={16} style={{ color: "#B8935A", flexShrink: 0 }}/>
              <div>
                <div style={{ fontSize: 10, color: "rgba(255,255,255,0.35)", textTransform: "uppercase", letterSpacing: "0.08em", marginBottom: 2 }}>
                  {item.label}
                </div>
                <div style={{ fontSize: 13, fontWeight: 500, color: "white" }}>{item.value}</div>
              </div>
            </div>
          ))}
        </div>

        {/* ── Tabs ── */}
        <div style={{ display: "flex", borderBottom: "1px solid rgba(255,255,255,0.08)", marginBottom: 24 }}>
          {[
            { key: "progress",   label: "Timeline",      icon: CheckCircle2 },
            { key: "pembayaran", label: "Pembayaran",    icon: Calendar },
            { key: "dokumen",    label: "Dokumen",       icon: FileText },
            { key: "foto",       label: "Foto Lapangan", icon: Camera },
          ].map((tab) => {
            const isActive = activeTab === tab.key;
            return (
              <button key={tab.key}
                onClick={() => setActiveTab(tab.key as typeof activeTab)}
                style={{
                  display: "flex", alignItems: "center", gap: 7,
                  padding: "12px 16px", fontSize: 12,
                  fontWeight: isActive ? 600 : 400,
                  color: isActive ? "white" : "rgba(255,255,255,0.4)",
                  backgroundColor: "transparent", border: "none",
                  borderBottom: isActive ? "2px solid #B8935A" : "2px solid transparent",
                  cursor: "pointer", transition: "all 0.15s", marginBottom: -1,
                  fontFamily: "var(--font-sans)",
                }}
              >
                <tab.icon size={13}/>{tab.label}
              </button>
            );
          })}
        </div>

        {/* ── TAB: Timeline ── */}
        {activeTab === "progress" && timeline && (
          <div style={{
            backgroundColor: "rgba(255,255,255,0.03)",
            border: "1px solid rgba(255,255,255,0.07)",
            borderRadius: 12, padding: 24,
          }}>
            <div style={{ fontSize: 15, fontWeight: 600, color: "white", marginBottom: 24 }}>
              Tahapan Pembangunan
            </div>
            <div style={{ display: "flex", flexDirection: "column" }}>
              {timeline.phases.map((phase, i) => (
                <div key={phase.id} style={{ display: "flex", gap: 16, position: "relative" }}>
                  {i < timeline.phases.length - 1 && (
                    <div style={{
                      position: "absolute", left: 7, top: 18, width: 2, height: "100%",
                      backgroundColor: phase.status === "selesai"
                        ? "rgba(52,211,153,0.35)"
                        : "rgba(255,255,255,0.06)",
                      zIndex: 0,
                    }}/>
                  )}
                  <div style={{ position: "relative", zIndex: 1, marginTop: 3, flexShrink: 0 }}>
                    {phase.status === "selesai"  && <CheckCircle2 size={15} style={{ color: "#34D399" }}/>}
                    {phase.status === "proses"   && (
                      <div style={{
                        width: 15, height: 15, borderRadius: "50%", backgroundColor: "#1A3FA8",
                        boxShadow: "0 0 0 4px rgba(26,63,168,0.25)",
                        display: "flex", alignItems: "center", justifyContent: "center",
                      }}>
                        <div style={{ width: 5, height: 5, borderRadius: "50%", backgroundColor: "white" }}/>
                      </div>
                    )}
                    {phase.status === "menunggu" && <Circle size={15} style={{ color: "rgba(255,255,255,0.15)" }}/>}
                  </div>
                  <div style={{ paddingBottom: i < timeline.phases.length - 1 ? 24 : 0, flex: 1 }}>
                    <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between", marginBottom: 4 }}>
                      <div style={{
                        fontSize: 14, fontWeight: phase.status === "menunggu" ? 400 : 600,
                        color: phase.status === "menunggu" ? "rgba(255,255,255,0.3)" : "white",
                      }}>
                        {phase.phase_name}
                      </div>
                      <div style={{ fontSize: 11, color: "rgba(255,255,255,0.3)", flexShrink: 0, marginLeft: 12 }}>
                        {phase.phase_date}
                      </div>
                    </div>
                    {phase.notes && (
                      <div style={{ fontSize: 12, color: "rgba(255,255,255,0.4)", lineHeight: 1.6, marginBottom: 6 }}>
                        {phase.notes}
                      </div>
                    )}
                    {phase.status === "proses" && (
                      <span style={{
                        display: "inline-flex", alignItems: "center", gap: 5,
                        fontSize: 10, fontWeight: 600, color: "#60A5FA",
                        backgroundColor: "rgba(26,63,168,0.2)",
                        padding: "3px 10px", borderRadius: 999,
                        textTransform: "uppercase", letterSpacing: "0.06em",
                      }}>⚡ Sedang berjalan</span>
                    )}
                    {phase.status === "selesai" && (
                      <span style={{
                        display: "inline-flex", alignItems: "center", gap: 5,
                        fontSize: 10, fontWeight: 600, color: "#34D399",
                        backgroundColor: "rgba(14,123,82,0.15)",
                        padding: "3px 10px", borderRadius: 999,
                        textTransform: "uppercase", letterSpacing: "0.06em",
                      }}>✓ Selesai</span>
                    )}
                  </div>
                </div>
              ))}
            </div>
          </div>
        )}

        {/* ── TAB: Pembayaran ── */}
        {activeTab === "pembayaran" && payments && (
          <div>
            {/* Summary */}
            <div style={{
              display: "grid", gridTemplateColumns: "repeat(3,1fr)", gap: 10, marginBottom: 16,
            }}>
              {[
                { label: "Total Tagihan", value: rupiah(payments.total_amount), color: "#60A5FA" },
                { label: "Sudah Dibayar", value: rupiah(payments.paid_amount),  color: "#34D399" },
                { label: "Metode",        value: payments.payment_method,       color: "#B8935A" },
              ].map(s => (
                <div key={s.label} style={{
                  backgroundColor: "rgba(255,255,255,0.04)",
                  border: "1px solid rgba(255,255,255,0.06)",
                  borderRadius: 10, padding: "14px 16px",
                }}>
                  <div style={{ fontSize: 10, color: "rgba(255,255,255,0.35)", textTransform: "uppercase", letterSpacing: "0.08em", marginBottom: 6 }}>
                    {s.label}
                  </div>
                  <div style={{ fontSize: 14, fontWeight: 600, color: s.color }}>{s.value}</div>
                </div>
              ))}
            </div>

            {/* Payment list */}
            <div style={{
              backgroundColor: "rgba(255,255,255,0.03)",
              border: "1px solid rgba(255,255,255,0.07)",
              borderRadius: 12, overflow: "hidden",
            }}>
              {payments.payments.map((p, i) => (
                <div key={p.id} style={{
                  display: "flex", alignItems: "center", justifyContent: "space-between",
                  padding: "16px 20px",
                  borderBottom: i < payments.payments.length - 1
                    ? "1px solid rgba(255,255,255,0.05)" : "none",
                }}>
                  <div>
                    <div style={{ fontSize: 13, fontWeight: 500, color: "white", marginBottom: 3 }}>
                      {p.payment_type}
                    </div>
                    <div style={{ fontSize: 11, color: "rgba(255,255,255,0.35)" }}>
                      Jatuh tempo: {formatDate(p.due_date)} · {p.bank || "—"}
                    </div>
                  </div>
                  <div style={{ textAlign: "right" }}>
                    <div style={{ fontSize: 14, fontWeight: 700, color: "white", marginBottom: 4 }}>
                      {rupiah(p.amount)}
                    </div>
                    <span style={{
                      fontSize: 10, fontWeight: 600,
                      color: paymentStatusColor(p.status),
                      backgroundColor: `${paymentStatusColor(p.status)}20`,
                      padding: "2px 8px", borderRadius: 999,
                      textTransform: "uppercase", letterSpacing: "0.06em",
                    }}>
                      {p.status_display}
                    </span>
                  </div>
                </div>
              ))}
            </div>
          </div>
        )}

        {/* ── TAB: Dokumen ── */}
        {activeTab === "dokumen" && documents && (
          <div style={{
            backgroundColor: "rgba(255,255,255,0.03)",
            border: "1px solid rgba(255,255,255,0.07)",
            borderRadius: 12, overflow: "hidden",
          }}>
            {documents.documents.map((d, i) => (
              <div key={d.id}
                style={{
                  display: "flex", alignItems: "center", justifyContent: "space-between",
                  padding: "16px 20px",
                  borderBottom: i < documents.documents.length - 1
                    ? "1px solid rgba(255,255,255,0.05)" : "none",
                  cursor: "pointer", transition: "background 0.15s",
                }}
                onMouseEnter={(e) => ((e.currentTarget as HTMLElement).style.backgroundColor = "rgba(255,255,255,0.03)")}
                onMouseLeave={(e) => ((e.currentTarget as HTMLElement).style.backgroundColor = "transparent")}
              >
                <div style={{ display: "flex", alignItems: "center", gap: 14 }}>
                  <div style={{
                    width: 36, height: 36, borderRadius: 8, flexShrink: 0,
                    backgroundColor:
                      d.status === "tersedia" ? "rgba(14,123,82,0.15)"
                      : d.status === "proses"  ? "rgba(26,63,168,0.15)"
                      : "rgba(255,255,255,0.05)",
                    display: "flex", alignItems: "center", justifyContent: "center",
                  }}>
                    <FileText size={16} style={{
                      color: d.status === "tersedia" ? "#34D399"
                        : d.status === "proses" ? "#60A5FA"
                        : "rgba(255,255,255,0.2)",
                    }}/>
                  </div>
                  <div>
                    <div style={{
                      fontSize: 13, fontWeight: 500, marginBottom: 3,
                      color: d.status === "menunggu"
                        ? "rgba(255,255,255,0.35)"
                        : "rgba(255,255,255,0.85)",
                    }}>
                      {d.name}
                    </div>
                    <div style={{ fontSize: 11, color: "rgba(255,255,255,0.3)" }}>
                      {d.issued_date}
                    </div>
                  </div>
                </div>
                {d.status === "tersedia" && (
                  d.file_url ? (
                    <a href={d.file_url} target="_blank" rel="noopener noreferrer"
                      style={{
                        display: "flex", alignItems: "center", gap: 6,
                        padding: "6px 14px",
                        backgroundColor: "rgba(14,123,82,0.15)",
                        border: "1px solid rgba(52,211,153,0.25)",
                        borderRadius: 6, fontSize: 11, fontWeight: 600,
                        color: "#34D399", textDecoration: "none",
                      }}
                    >
                      <Download size={12}/> Unduh
                    </a>
                  ) : (
                    <span style={{ fontSize: 11, color: "#34D399", fontWeight: 500 }}>✓ Tersedia</span>
                  )
                )}
                {d.status === "proses"   && <span style={{ fontSize: 11, color: "#60A5FA", fontWeight: 500 }}>Sedang diproses</span>}
                {d.status === "menunggu" && <span style={{ fontSize: 11, color: "rgba(255,255,255,0.2)" }}>Belum tersedia</span>}
              </div>
            ))}
          </div>
        )}

        {/* ── TAB: Foto ── */}
        {activeTab === "foto" && (
          <div>
            <div style={{ fontSize: 13, color: "rgba(255,255,255,0.4)", marginBottom: 16 }}>
              Foto konstruksi dari lapangan
            </div>
            {/* Check if any phases have photos */}
            {timeline && timeline.phases.some(p => p.photos.length > 0) ? (
              <div style={{ display: "grid", gridTemplateColumns: "repeat(3,1fr)", gap: 10 }}>
                {timeline.phases.flatMap(phase =>
                  phase.photos.map((photo) => (
                    <div key={photo.id} style={{
                      backgroundColor: "rgba(255,255,255,0.04)",
                      border: "1px solid rgba(255,255,255,0.07)",
                      borderRadius: 10, overflow: "hidden",
                    }}>
                      <img
                        src={photo.image}
                        alt={photo.caption || phase.phase_name}
                        style={{ width: "100%", height: 100, objectFit: "cover" }}
                      />
                      <div style={{ padding: "10px 12px" }}>
                        <div style={{ fontSize: 11, fontWeight: 500, color: "rgba(255,255,255,0.8)", lineHeight: 1.3, marginBottom: 4 }}>
                          {photo.caption || phase.phase_name}
                        </div>
                        <div style={{ fontSize: 10, color: "rgba(255,255,255,0.3)", display: "flex", justifyContent: "space-between" }}>
                          <span>{new Date(photo.uploaded_at).toLocaleDateString("id-ID")}</span>
                          <span style={{ color: "#B8935A", fontWeight: 500 }}>{phase.phase_name}</span>
                        </div>
                      </div>
                    </div>
                  ))
                )}
              </div>
            ) : (
              <div style={{
                backgroundColor: "rgba(255,255,255,0.03)",
                border: "1px solid rgba(255,255,255,0.07)",
                borderRadius: 12, padding: 40,
                textAlign: "center",
              }}>
                <Camera size={32} style={{ color: "rgba(255,255,255,0.15)", margin: "0 auto 12px" }}/>
                <div style={{ fontSize: 13, color: "rgba(255,255,255,0.4)" }}>
                  Belum ada foto yang diunggah
                </div>
                <div style={{ fontSize: 11, color: "rgba(255,255,255,0.25)", marginTop: 6 }}>
                  Teknisi akan mengunggah foto progress pembangunan secara berkala
                </div>
              </div>
            )}
          </div>
        )}

        {/* ── Purchase details ── */}
        <div style={{
          marginTop: 24,
          backgroundColor: "rgba(255,255,255,0.03)",
          border: "1px solid rgba(255,255,255,0.07)",
          borderRadius: 12, padding: 20,
        }}>
          <div style={{ fontSize: 13, fontWeight: 600, color: "rgba(255,255,255,0.6)", textTransform: "uppercase", letterSpacing: "0.08em", marginBottom: 16 }}>
            Detail Pembelian
          </div>
          <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 0 }}>
            {[
              ["Harga Unit",        rupiah(unit.price)],
              ["Metode Pembayaran", unit.payment_method || "—"],
              ["Bank",              unit.bank || "—"],
              ["Status Pembayaran", payments?.overdue_count === 0 ? "Lancar ✓" : "Ada Tunggakan ⚠️"],
              ["Proyek",            project.name],
              ["Lokasi",            project.location],
            ].map(([label, value], i) => (
              <div key={label} style={{
                padding: "10px 0",
                borderBottom: i < 4 ? "1px solid rgba(255,255,255,0.05)" : "none",
                paddingRight: i % 2 === 0 ? 20 : 0,
              }}>
                <div style={{ fontSize: 11, color: "rgba(255,255,255,0.3)", marginBottom: 3 }}>{label}</div>
                <div style={{
                  fontSize: 13, fontWeight: 500,
                  color: value.includes("✓") ? "#34D399"
                    : value.includes("⚠️") ? "#FBBF24"
                    : "rgba(255,255,255,0.8)",
                }}>
                  {value}
                </div>
              </div>
            ))}
          </div>
        </div>

        {/* ── Contact + rating ── */}
        <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 12, marginTop: 16 }}>
          <div style={{
            backgroundColor: "rgba(26,63,168,0.12)",
            border: "1px solid rgba(26,63,168,0.25)",
            borderRadius: 12, padding: "18px 20px",
            display: "flex", alignItems: "center", gap: 14, cursor: "pointer",
          }}>
            <div style={{
              width: 40, height: 40, borderRadius: "50%",
              backgroundColor: "rgba(26,63,168,0.25)",
              display: "flex", alignItems: "center", justifyContent: "center", flexShrink: 0,
            }}>
              <MessageCircle size={18} style={{ color: "#60A5FA" }}/>
            </div>
            <div>
              <div style={{ fontSize: 13, fontWeight: 600, color: "white", marginBottom: 2 }}>Hubungi Admin</div>
              <div style={{ fontSize: 11, color: "rgba(255,255,255,0.4)" }}>WhatsApp · Senin–Sabtu 08–17</div>
            </div>
          </div>
          <div style={{
            backgroundColor: "rgba(184,147,90,0.08)",
            border: "1px solid rgba(184,147,90,0.2)",
            borderRadius: 12, padding: "18px 20px",
            display: "flex", alignItems: "center", gap: 14, cursor: "pointer",
          }}>
            <div style={{
              width: 40, height: 40, borderRadius: "50%",
              backgroundColor: "rgba(184,147,90,0.15)",
              display: "flex", alignItems: "center", justifyContent: "center", flexShrink: 0,
            }}>
              <Star size={18} style={{ color: "#B8935A" }}/>
            </div>
            <div>
              <div style={{ fontSize: 13, fontWeight: 600, color: "white", marginBottom: 2 }}>Beri Penilaian</div>
              <div style={{ fontSize: 11, color: "rgba(255,255,255,0.4)" }}>Bagikan pengalaman Anda</div>
            </div>
          </div>
        </div>

        {/* ── Back + logout ── */}
        <div style={{ marginTop: 48, display: "flex", justifyContent: "space-between", alignItems: "center" }}>
          <Link href="/" style={{
            display: "inline-flex", alignItems: "center", gap: 6,
            fontSize: 12, color: "rgba(255,255,255,0.25)", textDecoration: "none",
          }}>
            <ChevronLeft size={13}/> Kembali ke halaman utama
          </Link>
          <button onClick={logout} style={{
            fontSize: 12, color: "rgba(255,255,255,0.25)",
            backgroundColor: "transparent", border: "none",
            cursor: "pointer", fontFamily: "var(--font-sans)",
          }}>
            Keluar
          </button>
        </div>

      </div>
    </div>
  );
}
