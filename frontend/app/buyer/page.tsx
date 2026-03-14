"use client";

import { UNIT, TIMELINE_A01, PEMBELI, rupiah } from "@/lib/mock-data";
import {
  CheckCircle2,
  Circle,
  Camera,
  FileText,
  ChevronLeft,
  MapPin,
  Calendar,
  Home,
  Download,
  MessageCircle,
  Star,
} from "lucide-react";
import Link from "next/link";
import { useState } from "react";

// ── Demo data ─────────────────────────────────────────────────
const unit    = UNIT[0];
const pembeli = PEMBELI[0];

// ── Mock foto ─────────────────────────────────────────────────
const FOTO = [
  { label: "Finishing interior — lantai bawah", tanggal: "10 Mar 2026", fase: "Finishing" },
  { label: "Pemasangan keramik kamar mandi",    tanggal: "8 Mar 2026",  fase: "Finishing" },
  { label: "Pengecatan dinding eksterior",      tanggal: "1 Mar 2026",  fase: "Finishing" },
  { label: "Rangka atap selesai",               tanggal: "15 Jun 2025", fase: "Atap" },
  { label: "Pondasi beton dituang",             tanggal: "12 Feb 2025", fase: "Pondasi" },
  { label: "Pembersihan & uji tanah lulus",     tanggal: "5 Jan 2025",  fase: "Persiapan" },
];

// ── Mock dokumen ──────────────────────────────────────────────
const DOKUMEN = [
  { nama: "PPJB — Perjanjian Pengikatan Jual Beli", tanggal: "Jan 2025",   status: "tersedia" },
  { nama: "IMB — Izin Mendirikan Bangunan",          tanggal: "Des 2024",   status: "tersedia" },
  { nama: "Sertifikat Tanah (AJB)",                  tanggal: "Proses KPR", status: "proses"   },
  { nama: "Faktur Pajak PPN",                        tanggal: "Jan 2025",   status: "tersedia" },
  { nama: "Berita Acara Serah Terima",               tanggal: "Sep 2025",   status: "menunggu" },
];

// ─────────────────────────────────────────────────────────────
export default function BuyerPortalPage() {
  const [activeTab, setActiveTab] = useState<"progress" | "foto" | "dokumen">("progress");
  const doneCount = TIMELINE_A01.filter((t) => t.status === "selesai").length;

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
            fontSize: 12, fontWeight: 700, color: "white",
          }}>BS</div>
          <span style={{ fontSize: 13, color: "rgba(255,255,255,0.8)", fontWeight: 500 }}>
            {pembeli.nama}
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
            Halo, <span style={{ fontStyle: "italic", color: "#B8935A" }}>{pembeli.nama.split(" ")[0]}</span> 👋
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
                Unit {unit.nomor}
              </div>
              <div style={{ fontSize: 13, color: "rgba(255,255,255,0.45)" }}>
                {unit.tipe} · {unit.luas_tanah}m² · {unit.proyek_nama}
              </div>
            </div>
            <div style={{
              background: "rgba(14,123,82,0.2)", border: "1px solid rgba(14,123,82,0.4)",
              borderRadius: 999, padding: "6px 14px",
              fontSize: 12, fontWeight: 600, color: "#34D399",
              display: "flex", alignItems: "center", gap: 6,
            }}>
              <div style={{ width: 6, height: 6, borderRadius: "50%", backgroundColor: "#34D399" }}/>
              Sesuai Jadwal
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
              {unit.progres}
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
              width: `${unit.progres}%`, transition: "width 1s ease",
              boxShadow: "0 0 12px rgba(52,211,153,0.4)",
            }}/>
          </div>

          <div style={{ display: "flex", justifyContent: "space-between", fontSize: 11, color: "rgba(255,255,255,0.3)" }}>
            <span>Dimulai Jan 2025</span>
            <span>{doneCount} dari 7 fase selesai</span>
            <span>Target {unit.selesai}</span>
          </div>
        </div>

        {/* ── Quick info strip ── */}
        <div style={{ display: "grid", gridTemplateColumns: "repeat(3, 1fr)", gap: 10, marginBottom: 24 }}>
          {[
            { icon: Home,     label: "Tipe Unit",    value: unit.tipe },
            { icon: MapPin,   label: "Lokasi",       value: "Telanaipura, Jambi" },
            { icon: Calendar, label: "Serah Terima", value: unit.selesai },
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
            { key: "progress", label: "Timeline Konstruksi", icon: CheckCircle2 },
            { key: "foto",     label: "Foto Lapangan",       icon: Camera },
            { key: "dokumen",  label: "Dokumen",             icon: FileText },
          ].map((tab) => {
            const isActive = activeTab === tab.key;
            return (
              <button key={tab.key} onClick={() => setActiveTab(tab.key as typeof activeTab)}
                style={{
                  display: "flex", alignItems: "center", gap: 7,
                  padding: "12px 20px", fontSize: 13,
                  fontWeight: isActive ? 600 : 400,
                  color: isActive ? "white" : "rgba(255,255,255,0.4)",
                  backgroundColor: "transparent", border: "none",
                  borderBottom: isActive ? "2px solid #B8935A" : "2px solid transparent",
                  cursor: "pointer", transition: "all 0.15s", marginBottom: -1,
                  fontFamily: "var(--font-sans)",
                }}
              >
                <tab.icon size={14}/>{tab.label}
              </button>
            );
          })}
        </div>

        {/* ── TAB: Timeline ── */}
        {activeTab === "progress" && (
          <div style={{
            backgroundColor: "rgba(255,255,255,0.03)",
            border: "1px solid rgba(255,255,255,0.07)",
            borderRadius: 12, padding: 24,
          }}>
            <div style={{ fontSize: 15, fontWeight: 600, color: "white", marginBottom: 24 }}>
              Tahapan Pembangunan
            </div>
            <div style={{ display: "flex", flexDirection: "column" }}>
              {TIMELINE_A01.map((t, i) => (
                <div key={i} style={{ display: "flex", gap: 16, position: "relative" }}>
                  {i < TIMELINE_A01.length - 1 && (
                    <div style={{
                      position: "absolute", left: 7, top: 18, width: 2, height: "100%",
                      backgroundColor: t.status === "selesai" ? "rgba(52,211,153,0.35)" : "rgba(255,255,255,0.06)",
                      zIndex: 0,
                    }}/>
                  )}
                  <div style={{ position: "relative", zIndex: 1, marginTop: 3, flexShrink: 0 }}>
                    {t.status === "selesai"  && <CheckCircle2 size={15} style={{ color: "#34D399" }}/>}
                    {t.status === "proses"   && (
                      <div style={{
                        width: 15, height: 15, borderRadius: "50%", backgroundColor: "#1A3FA8",
                        boxShadow: "0 0 0 4px rgba(26,63,168,0.25)",
                        display: "flex", alignItems: "center", justifyContent: "center",
                      }}>
                        <div style={{ width: 5, height: 5, borderRadius: "50%", backgroundColor: "white" }}/>
                      </div>
                    )}
                    {t.status === "menunggu" && <Circle size={15} style={{ color: "rgba(255,255,255,0.15)" }}/>}
                  </div>
                  <div style={{ paddingBottom: i < TIMELINE_A01.length - 1 ? 24 : 0, flex: 1 }}>
                    <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between", marginBottom: 4 }}>
                      <div style={{
                        fontSize: 14,
                        fontWeight: t.status === "menunggu" ? 400 : 600,
                        color: t.status === "menunggu" ? "rgba(255,255,255,0.3)" : "white",
                      }}>
                        {t.fase}
                      </div>
                      <div style={{ fontSize: 11, color: "rgba(255,255,255,0.3)", flexShrink: 0, marginLeft: 12 }}>
                        {t.tgl}
                      </div>
                    </div>
                    {t.catatan && (
                      <div style={{ fontSize: 12, color: "rgba(255,255,255,0.4)", lineHeight: 1.6, marginBottom: 6 }}>
                        {t.catatan}
                      </div>
                    )}
                    {t.status === "proses" && (
                      <span style={{
                        display: "inline-flex", alignItems: "center", gap: 5,
                        fontSize: 10, fontWeight: 600, color: "#60A5FA",
                        backgroundColor: "rgba(26,63,168,0.2)",
                        padding: "3px 10px", borderRadius: 999,
                        textTransform: "uppercase", letterSpacing: "0.06em",
                      }}>⚡ Sedang berjalan</span>
                    )}
                    {t.status === "selesai" && (
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

        {/* ── TAB: Foto ── */}
        {activeTab === "foto" && (
          <div>
            <div style={{ fontSize: 13, color: "rgba(255,255,255,0.4)", marginBottom: 16 }}>
              {FOTO.length} foto dari lapangan — diperbarui oleh teknisi
            </div>
            <div style={{ display: "grid", gridTemplateColumns: "repeat(3, 1fr)", gap: 10 }}>
              {FOTO.map((f, i) => (
                <div key={i}
                  style={{
                    backgroundColor: "rgba(255,255,255,0.04)",
                    border: "1px solid rgba(255,255,255,0.07)",
                    borderRadius: 10, overflow: "hidden", cursor: "pointer", transition: "all 0.15s",
                  }}
                  onMouseEnter={(e) => ((e.currentTarget as HTMLElement).style.borderColor = "rgba(184,147,90,0.4)")}
                  onMouseLeave={(e) => ((e.currentTarget as HTMLElement).style.borderColor = "rgba(255,255,255,0.07)")}
                >
                  <div style={{
                    height: 100,
                    background: `linear-gradient(135deg, rgba(26,63,168,${0.1 + i * 0.04}) 0%, rgba(184,147,90,${0.05 + i * 0.02}) 100%)`,
                    display: "flex", alignItems: "center", justifyContent: "center",
                  }}>
                    <Camera size={24} style={{ color: "rgba(255,255,255,0.2)" }}/>
                  </div>
                  <div style={{ padding: "10px 12px" }}>
                    <div style={{ fontSize: 11, fontWeight: 500, color: "rgba(255,255,255,0.8)", lineHeight: 1.3, marginBottom: 4 }}>
                      {f.label}
                    </div>
                    <div style={{ fontSize: 10, color: "rgba(255,255,255,0.3)", display: "flex", justifyContent: "space-between" }}>
                      <span>{f.tanggal}</span>
                      <span style={{ color: "#B8935A", fontWeight: 500 }}>{f.fase}</span>
                    </div>
                  </div>
                </div>
              ))}
            </div>
          </div>
        )}

        {/* ── TAB: Dokumen ── */}
        {activeTab === "dokumen" && (
          <div style={{
            backgroundColor: "rgba(255,255,255,0.03)",
            border: "1px solid rgba(255,255,255,0.07)",
            borderRadius: 12, overflow: "hidden",
          }}>
            {DOKUMEN.map((d, i) => (
              <div key={i}
                style={{
                  display: "flex", alignItems: "center", justifyContent: "space-between",
                  padding: "16px 20px",
                  borderBottom: i < DOKUMEN.length - 1 ? "1px solid rgba(255,255,255,0.05)" : "none",
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
                      color: d.status === "menunggu" ? "rgba(255,255,255,0.35)" : "rgba(255,255,255,0.85)",
                    }}>
                      {d.nama}
                    </div>
                    <div style={{ fontSize: 11, color: "rgba(255,255,255,0.3)" }}>{d.tanggal}</div>
                  </div>
                </div>
                {d.status === "tersedia" && (
                  <button style={{
                    display: "flex", alignItems: "center", gap: 6,
                    padding: "6px 14px",
                    backgroundColor: "rgba(14,123,82,0.15)",
                    border: "1px solid rgba(52,211,153,0.25)",
                    borderRadius: 6, fontSize: 11, fontWeight: 600,
                    color: "#34D399", cursor: "pointer", fontFamily: "var(--font-sans)",
                  }}>
                    <Download size={12}/> Unduh
                  </button>
                )}
                {d.status === "proses"   && <span style={{ fontSize: 11, color: "#60A5FA", fontWeight: 500 }}>Sedang diproses</span>}
                {d.status === "menunggu" && <span style={{ fontSize: 11, color: "rgba(255,255,255,0.2)" }}>Belum tersedia</span>}
              </div>
            ))}
          </div>
        )}

        {/* ── Payment details ── */}
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
              ["Harga Unit",         rupiah(unit.harga)],
              ["Metode Pembayaran",  pembeli.metode],
              ["Bank",               pembeli.bank],
              ["Status Pembayaran",  "Lancar ✓"],
              ["Agen Penjualan",     "Rizky Setiawan"],
              ["Lokasi",             "Telanaipura, Kota Jambi"],
            ].map(([label, value], i) => (
              <div key={label} style={{
                padding: "10px 0",
                borderBottom: i < 4 ? "1px solid rgba(255,255,255,0.05)" : "none",
                paddingRight: i % 2 === 0 ? 20 : 0,
              }}>
                <div style={{ fontSize: 11, color: "rgba(255,255,255,0.3)", marginBottom: 3 }}>{label}</div>
                <div style={{ fontSize: 13, fontWeight: 500, color: value.includes("✓") ? "#34D399" : "rgba(255,255,255,0.8)" }}>
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

        {/* ── Back link ── */}
        <div style={{ marginTop: 48, textAlign: "center" }}>
          <Link href="/" style={{
            display: "inline-flex", alignItems: "center", gap: 6,
            fontSize: 12, color: "rgba(255,255,255,0.25)", textDecoration: "none",
          }}>
            <ChevronLeft size={13}/> Kembali ke halaman utama
          </Link>
        </div>

      </div>
    </div>
  );
}
