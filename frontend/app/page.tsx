"use client";
import Link from "next/link";

const PORTALS = [
  {
    num: "01",
    title: "Developer Portal",
    desc: "Dasbor lengkap — proyek, unit, konstruksi, penjualan & keuangan",
    href: "/dashboard",
    cta: "Masuk",
    featured: true,
  },
  {
    num: "02",
    title: "Portal Pembeli",
    desc: "Lacak progres pembangunan rumah Anda secara real-time, fase per fase",
    href: "/buyer",
    cta: "Lihat progres",
    featured: false,
  },
  {
    num: "03",
    title: "Agen Penjualan",
    desc: "Kelola prospek, catat penjualan & pantau komisi Anda",
    href: "/dashboard/agen",
    cta: "Masuk",
    featured: false,
  },
  {
    num: "04",
    title: "Super Admin",
    desc: "Manajemen platform — developer, langganan & fitur",
    href: "/dashboard",
    cta: "Masuk",
    featured: false,
  },
];

const FITUR = [
  {
    no: "01",
    judul: "Lacak Progres Konstruksi",
    desc: "Pantau fase per fase dengan foto langsung dari lapangan. Pembeli bisa lihat real-time kapan saja.",
  },
  {
    no: "02",
    judul: "Multi-developer SaaS",
    desc: "Satu platform untuk banyak developer properti. Data terisolasi, aman & terpisah per tenant.",
  },
  {
    no: "03",
    judul: "KPR-aware Pembayaran",
    desc: "Sistem khusus pasar Indonesia — BCA, BNI, BTN, Mandiri, cash keras, cash bertahap.",
  },
  {
    no: "04",
    judul: "Akuntansi Biaya",
    desc: "RAB vs realisasi per proyek. Alert otomatis jika ada item yang melebihi anggaran.",
  },
  {
    no: "05",
    judul: "Manajemen Agen",
    desc: "Ranking agen, target penjualan, rekam jejak komisi & performa bulanan.",
  },
  {
    no: "06",
    judul: "Laporan PDF & Excel",
    desc: "Satu klik — laporan progres untuk pembeli, laporan keuangan untuk investor.",
  },
];

const MARQUEE_ITEMS = [
  "Lacak Konstruksi",
  "Manajemen Penjualan",
  "Portal Pembeli",
  "Akuntansi KPR",
  "Multi-developer SaaS",
  "Pelacak Pembayaran",
  "Laporan PDF / Excel",
  "Notifikasi Real-time",
];

export default function HomePage() {
  return (
    <div
      style={{
        minHeight: "100vh",
        backgroundColor: "var(--color-paper)",
        fontFamily: "var(--font-sans)",
      }}
    >
      {/* ── NAV ── */}
      <nav
        style={{
          position: "sticky",
          top: 0,
          zIndex: 50,
          backgroundColor: "rgba(245,243,238,0.92)",
          backdropFilter: "blur(12px)",
          borderBottom: "1px solid rgba(14,13,11,0.08)",
          padding: "16px 48px",
          display: "flex",
          alignItems: "center",
          justifyContent: "space-between",
        }}
      >
        <div
          style={{
            fontFamily: "var(--font-serif)",
            fontSize: 22,
            fontWeight: 600,
            color: "var(--color-ink)",
          }}
        >
          Rumah<span style={{ color: "var(--color-accent)" }}>Asri</span>
        </div>

        <div style={{ display: "flex", alignItems: "center", gap: 32 }}>
          {["Platform", "Fitur", "Harga", "Kontak"].map((l) => (
            <a
              key={l}
              style={{
                fontSize: 13,
                color: "var(--color-ink-3)",
                textDecoration: "none",
                cursor: "pointer",
                transition: "color 0.2s",
              }}
              onMouseEnter={(e) =>
                ((e.target as HTMLElement).style.color = "var(--color-ink)")
              }
              onMouseLeave={(e) =>
                ((e.target as HTMLElement).style.color = "var(--color-ink-3)")
              }
            >
              {l}
            </a>
          ))}
        </div>

        <div style={{ display: "flex", gap: 12 }}>
          <Link href="/login" className="btn-ghost btn-sm">
            Masuk
          </Link>
          <Link href="/dashboard" className="btn-accent btn-sm">
            Coba Gratis
          </Link>
        </div>
      </nav>

      {/* ── HERO ── */}
      <section
        style={{
          padding: "80px 48px 0",
          display: "grid",
          gridTemplateColumns: "1fr 1fr",
          minHeight: "92vh",
          alignItems: "center",
          gap: 0,
          overflow: "hidden",
          position: "relative",
        }}
      >
        {/* Left */}
        <div style={{ paddingBottom: 64 }}>
          <div className="eyebrow" style={{ marginBottom: 24 }}>
            Platform PropTech — Jambi &amp; Indonesia
          </div>
          <h1
            style={{
              fontFamily: "var(--font-serif)",
              fontSize: "clamp(44px, 6vw, 78px)",
              fontWeight: 300,
              lineHeight: 1.05,
              letterSpacing: "-0.02em",
              color: "var(--color-ink)",
              marginBottom: 24,
            }}
          >
            Kami Ahli dalam{" "}
            <span
              style={{
                fontStyle: "italic",
                color: "var(--color-accent)",
              }}
            >
              Semua Aspek
            </span>
            <br />
            <span style={{ fontWeight: 600 }}>Perumahan.</span>
          </h1>
          <p
            style={{
              fontSize: 15,
              color: "var(--color-ink-3)",
              lineHeight: 1.8,
              maxWidth: 400,
              marginBottom: 40,
              fontWeight: 300,
            }}
          >
            Solusi manajemen properti handal untuk pengembang perumahan
            Indonesia. Desain modern, cerdas, dan terhubung — dari Jambi untuk
            Indonesia.
          </p>
          <div style={{ display: "flex", gap: 12, marginBottom: 56 }}>
            <Link href="/dashboard" className="btn-primary">
              Jelajahi Platform →
            </Link>
            <Link href="/login" className="btn-ghost">
              Masuk
            </Link>
          </div>

          {/* Stats */}
          <div
            style={{
              display: "flex",
              gap: 40,
              paddingTop: 32,
              borderTop: "1px solid rgba(14,13,11,0.08)",
            }}
          >
            {[
              ["1.800+", "Unit dikelola"],
              ["14", "Developer aktif"],
              ["4", "Kota di Jambi"],
            ].map(([v, l]) => (
              <div key={l}>
                <div
                  style={{
                    fontFamily: "var(--font-serif)",
                    fontSize: 34,
                    fontWeight: 600,
                    color: "var(--color-ink)",
                    lineHeight: 1,
                  }}
                >
                  {v}
                </div>
                <div
                  style={{
                    fontSize: 11,
                    color: "var(--color-ink-3)",
                    marginTop: 6,
                    textTransform: "uppercase",
                    letterSpacing: "0.05em",
                  }}
                >
                  {l}
                </div>
              </div>
            ))}
          </div>
        </div>

        {/* Right — Architectural visual */}
        <div
          style={{
            position: "relative",
            height: "100%",
            minHeight: 500,
            display: "flex",
            alignItems: "flex-end",
            justifyContent: "center",
            overflow: "hidden",
            backgroundColor: "var(--color-paper-2)",
            backgroundImage:
              "linear-gradient(rgba(14,13,11,0.04) 1px, transparent 1px), linear-gradient(90deg, rgba(14,13,11,0.04) 1px, transparent 1px)",
            backgroundSize: "56px 56px",
          }}
        >
          {/* Building SVG */}
          <svg
            viewBox="0 0 480 420"
            style={{ width: "90%", height: "auto", position: "relative" }}
            preserveAspectRatio="xMidYMax meet"
          >
            <ellipse
              cx="240"
              cy="416"
              rx="200"
              ry="8"
              fill="rgba(14,13,11,0.07)"
            />
            <rect
              x="55"
              y="180"
              width="370"
              height="235"
              fill="#F2EEE7"
              stroke="rgba(14,13,11,0.10)"
              strokeWidth="1"
            />
            <rect
              x="85"
              y="98"
              width="310"
              height="96"
              fill="#F5F2EC"
              stroke="rgba(14,13,11,0.08)"
              strokeWidth="1"
            />
            <rect
              x="115"
              y="48"
              width="250"
              height="60"
              fill="#EAE5DD"
              stroke="rgba(14,13,11,0.08)"
              strokeWidth="1"
            />
            <rect
              x="155"
              y="16"
              width="170"
              height="40"
              fill="#E2DDD5"
              stroke="rgba(14,13,11,0.07)"
              strokeWidth="1"
            />
            <line
              x1="55"
              y1="180"
              x2="425"
              y2="180"
              stroke="#B8935A"
              strokeWidth="1.5"
              opacity="0.6"
            />
            <line
              x1="85"
              y1="98"
              x2="395"
              y2="98"
              stroke="#B8935A"
              strokeWidth="1"
              opacity="0.4"
            />
            {[75, 140, 210, 285, 350].map((x, i) => (
              <rect
                key={i}
                x={x}
                y={212}
                width={52}
                height={72}
                fill="rgba(26,63,168,0.11)"
                stroke="rgba(26,63,168,0.20)"
                strokeWidth="0.5"
              />
            ))}
            <rect
              x="204"
              y="298"
              width="72"
              height="117"
              fill="rgba(26,63,168,0.07)"
              stroke="rgba(14,13,11,0.15)"
              strokeWidth="0.5"
            />
            <line
              x1="240"
              y1="298"
              x2="240"
              y2="415"
              stroke="rgba(14,13,11,0.10)"
              strokeWidth="0.5"
            />
            {[100, 158, 216, 274, 332].map((x, i) => (
              <rect
                key={i}
                x={x}
                y={113}
                width={44}
                height={56}
                fill="rgba(26,63,168,0.10)"
                stroke="rgba(26,63,168,0.17)"
                strokeWidth="0.5"
              />
            ))}
            {[128, 178, 228, 278, 328].map((x, i) => (
              <rect
                key={i}
                x={x}
                y={60}
                width={36}
                height={28}
                fill="rgba(26,63,168,0.12)"
                stroke="rgba(26,63,168,0.18)"
                strokeWidth="0.5"
              />
            ))}
            <ellipse
              cx="28"
              cy="375"
              rx="22"
              ry="34"
              fill="rgba(14,100,50,0.14)"
              stroke="rgba(14,100,50,0.18)"
              strokeWidth="0.5"
            />
            <ellipse
              cx="452"
              cy="370"
              rx="20"
              ry="30"
              fill="rgba(14,100,50,0.12)"
              stroke="rgba(14,100,50,0.15)"
              strokeWidth="0.5"
            />
          </svg>

          {/* Floating badge — construction % */}
          <div
            style={{
              position: "absolute",
              top: 40,
              right: 32,
              background: "white",
              border: "1px solid rgba(14,13,11,0.08)",
              borderRadius: 8,
              padding: "14px 18px",
              boxShadow: "var(--shadow-float)",
              animation: "float 4s ease-in-out infinite",
            }}
          >
            <div
              style={{
                fontSize: 10,
                color: "var(--color-ink-3)",
                textTransform: "uppercase",
                letterSpacing: "0.08em",
                marginBottom: 4,
              }}
            >
              Konstruksi
            </div>
            <div
              style={{
                fontFamily: "var(--font-serif)",
                fontSize: 30,
                fontWeight: 600,
                color: "var(--color-ink)",
                lineHeight: 1,
              }}
            >
              85%
            </div>
            <div
              style={{
                fontSize: 11,
                color: "var(--color-success)",
                fontWeight: 500,
                marginTop: 4,
              }}
            >
              Unit A-01 · Sesuai jadwal
            </div>
          </div>

          {/* Floating badge — projects */}
          <div
            style={{
              position: "absolute",
              bottom: 100,
              left: 16,
              background: "var(--color-ink)",
              borderRadius: 8,
              padding: "12px 16px",
              animation: "float 4s ease-in-out infinite",
              animationDelay: "2s",
            }}
          >
            <div
              style={{
                fontSize: 10,
                color: "rgba(255,255,255,0.45)",
                textTransform: "uppercase",
                letterSpacing: "0.08em",
                marginBottom: 4,
              }}
            >
              Proyek aktif
            </div>
            <div
              style={{ fontSize: 13, color: "white", fontWeight: 500 }}
            >
              4 cluster · 142 unit
            </div>
          </div>
        </div>

        {/* ── SEARCH BAR ── */}
        <div
          style={{
            gridColumn: "1 / -1",
            marginTop: -1,
          }}
        >
          <div
            style={{
              display: "grid",
              gridTemplateColumns: "1fr 1fr 1fr auto",
              background: "white",
              border: "1px solid rgba(14,13,11,0.08)",
              borderRadius: 4,
              overflow: "hidden",
              boxShadow: "var(--shadow-card-lg)",
            }}
          >
            {[
              {
                label: "Tipe Properti",
                opts: ["Semua tipe", "Tipe 36", "Tipe 45", "Tipe 54", "Tipe 60"],
              },
              {
                label: "Lokasi",
                opts: [
                  "Semua area",
                  "Telanaipura",
                  "Alam Barajo",
                  "Kotabaru",
                  "Jambi Timur",
                ],
              },
              {
                label: "Status",
                opts: [
                  "Unit tersedia",
                  "Sedang proses",
                  "Siap serah terima",
                ],
              },
            ].map((f, i) => (
              <div
                key={i}
                style={{
                  padding: "20px 28px",
                  borderRight: "1px solid rgba(14,13,11,0.08)",
                  cursor: "pointer",
                  transition: "background 0.2s",
                }}
                onMouseEnter={(e) =>
                  ((e.currentTarget as HTMLElement).style.background =
                    "var(--color-paper)")
                }
                onMouseLeave={(e) =>
                  ((e.currentTarget as HTMLElement).style.background =
                    "white")
                }
              >
                <div
                  style={{
                    fontSize: 10,
                    color: "var(--color-ink-3)",
                    textTransform: "uppercase",
                    letterSpacing: "0.12em",
                    fontWeight: 500,
                    marginBottom: 8,
                  }}
                >
                  {f.label}
                </div>
                <select
                  style={{
                    width: "100%",
                    background: "transparent",
                    fontSize: 14,
                    color: "var(--color-ink)",
                    border: "none",
                    outline: "none",
                    cursor: "pointer",
                    appearance: "none",
                    fontFamily: "var(--font-sans)",
                  }}
                >
                  {f.opts.map((o) => (
                    <option key={o}>{o}</option>
                  ))}
                </select>
              </div>
            ))}
            <button
              style={{
                padding: "20px 36px",
                background: "var(--color-accent)",
                color: "white",
                border: "none",
                fontSize: 12,
                fontWeight: 500,
                letterSpacing: "0.1em",
                textTransform: "uppercase",
                cursor: "pointer",
                transition: "background 0.2s",
                fontFamily: "var(--font-sans)",
              }}
              onMouseEnter={(e) =>
                ((e.currentTarget as HTMLElement).style.background =
                  "var(--color-accent-dark)")
              }
              onMouseLeave={(e) =>
                ((e.currentTarget as HTMLElement).style.background =
                  "var(--color-accent)")
              }
            >
              Cari Unit →
            </button>
          </div>
        </div>
      </section>

      {/* ── MARQUEE ── */}
      <div
        style={{
          background: "var(--color-gold)",
          overflow: "hidden",
          padding: "14px 0",
          borderTop: "1px solid rgba(184,147,90,0.3)",
          borderBottom: "1px solid rgba(184,147,90,0.3)",
          display: "flex",
          marginTop: 40,
        }}
      >
        <div
          style={{
            display: "flex",
            animation: "marquee 22s linear infinite",
            flexShrink: 0,
            whiteSpace: "nowrap",
          }}
        >
          {[...MARQUEE_ITEMS, ...MARQUEE_ITEMS].map((t, i) => (
            <span
              key={i}
              style={{
                fontSize: 12,
                fontWeight: 500,
                color: "white",
                textTransform: "uppercase",
                letterSpacing: "0.15em",
                padding: "0 32px",
                display: "inline-flex",
                alignItems: "center",
                gap: 16,
              }}
            >
              {t}
              <span style={{ opacity: 0.4 }}>✦</span>
            </span>
          ))}
        </div>
      </div>

      {/* ── PORTALS ── */}
      <section style={{ padding: "100px 48px" }}>
        <div
          style={{
            display: "flex",
            justifyContent: "space-between",
            alignItems: "flex-end",
            marginBottom: 56,
          }}
        >
          <div>
            <div className="eyebrow" style={{ marginBottom: 16 }}>
              Portal platform
            </div>
            <h2
              style={{
                fontFamily: "var(--font-serif)",
                fontSize: "clamp(30px, 4vw, 52px)",
                fontWeight: 300,
                color: "var(--color-ink)",
                lineHeight: 1.15,
              }}
            >
              Satu platform,
              <br />
              <span
                style={{
                  fontStyle: "italic",
                  color: "var(--color-accent)",
                }}
              >
                empat portal
              </span>
            </h2>
          </div>
          <p
            style={{
              fontSize: 13,
              color: "var(--color-ink-3)",
              maxWidth: 280,
              textAlign: "right",
              lineHeight: 1.7,
            }}
          >
            Setiap portal dirancang khusus untuk penggunanya — developer,
            agen, pembeli & admin platform.
          </p>
        </div>

        <div
          style={{
            display: "grid",
            gridTemplateColumns: "repeat(4, 1fr)",
            gap: "1px",
            background: "rgba(14,13,11,0.08)",
            border: "1px solid rgba(14,13,11,0.08)",
            borderRadius: 4,
            overflow: "hidden",
          }}
        >
          {PORTALS.map((portal) => (
            <Link
              key={portal.title}
              href={portal.href}
              style={{
                background: portal.featured ? "var(--color-ink)" : "white",
                padding: "36px 28px",
                display: "flex",
                flexDirection: "column",
                cursor: "pointer",
                textDecoration: "none",
                transition: "all 0.25s",
                position: "relative",
                borderTop: portal.featured
                  ? "3px solid var(--color-gold)"
                  : "3px solid transparent",
              }}
              onMouseEnter={(e) => {
                if (!portal.featured) {
                  (e.currentTarget as HTMLElement).style.background =
                    "var(--color-paper)";
                  (e.currentTarget as HTMLElement).style.borderTopColor =
                    "var(--color-accent)";
                }
              }}
              onMouseLeave={(e) => {
                if (!portal.featured) {
                  (e.currentTarget as HTMLElement).style.background =
                    "white";
                  (e.currentTarget as HTMLElement).style.borderTopColor =
                    "transparent";
                }
              }}
            >
              <div
                style={{
                  fontSize: 11,
                  letterSpacing: "0.15em",
                  textTransform: "uppercase",
                  color: portal.featured
                    ? "rgba(255,255,255,0.35)"
                    : "var(--color-ink-3)",
                  marginBottom: 10,
                }}
              >
                Portal {portal.num}
              </div>
              <div
                style={{
                  fontSize: 18,
                  fontWeight: 600,
                  color: portal.featured ? "white" : "var(--color-ink)",
                  marginBottom: 12,
                  lineHeight: 1.3,
                }}
              >
                {portal.title}
              </div>
              <div
                style={{
                  fontSize: 13,
                  color: portal.featured
                    ? "rgba(255,255,255,0.45)"
                    : "var(--color-ink-3)",
                  lineHeight: 1.7,
                  flex: 1,
                  marginBottom: 28,
                  fontWeight: 300,
                }}
              >
                {portal.desc}
              </div>
              <div
                style={{
                  fontSize: 11,
                  fontWeight: 500,
                  textTransform: "uppercase",
                  letterSpacing: "0.12em",
                  color: portal.featured
                    ? "var(--color-gold)"
                    : "var(--color-accent)",
                }}
              >
                {portal.cta} →
              </div>
            </Link>
          ))}
        </div>
      </section>

      {/* ── FEATURES ── */}
      <section
        style={{
          background: "var(--color-ink)",
          padding: "100px 48px",
        }}
      >
        <div
          style={{
            display: "flex",
            justifyContent: "space-between",
            alignItems: "flex-end",
            paddingBottom: 48,
            borderBottom: "1px solid rgba(255,255,255,0.08)",
            marginBottom: 64,
          }}
        >
          <div>
            <div
              style={{
                fontSize: 11,
                fontWeight: 500,
                letterSpacing: "0.15em",
                textTransform: "uppercase",
                color: "var(--color-gold)",
                display: "flex",
                alignItems: "center",
                gap: 8,
                marginBottom: 16,
              }}
            >
              <span
                style={{
                  width: 24,
                  height: 1,
                  background: "var(--color-gold)",
                  display: "inline-block",
                }}
              />
              Kemampuan platform
            </div>
            <h2
              style={{
                fontFamily: "var(--font-serif)",
                fontSize: "clamp(30px, 4vw, 52px)",
                fontWeight: 300,
                color: "white",
                lineHeight: 1.15,
              }}
            >
              Dibangun untuk pasar
              <br />
              <span style={{ fontStyle: "italic", color: "var(--color-gold)" }}>
                properti Indonesia
              </span>
            </h2>
          </div>
          <p
            style={{
              fontSize: 13,
              color: "rgba(255,255,255,0.4)",
              maxWidth: 280,
              textAlign: "right",
              lineHeight: 1.7,
            }}
          >
            Setiap fitur dirancang sesuai cara kerja developer properti
            Indonesia — KPR, IDR, BTN, BCA, WhatsApp.
          </p>
        </div>

        <div
          style={{
            display: "grid",
            gridTemplateColumns: "repeat(3, 1fr)",
            gap: 48,
          }}
        >
          {FITUR.map((f) => (
            <div
              key={f.no}
              style={{
                borderTop: "1px solid rgba(255,255,255,0.10)",
                paddingTop: 32,
              }}
            >
              <div
                style={{
                  fontFamily: "var(--font-serif)",
                  fontSize: 52,
                  fontWeight: 300,
                  color: "rgba(255,255,255,0.08)",
                  lineHeight: 1,
                  marginBottom: 16,
                }}
              >
                {f.no}
              </div>
              <div
                style={{
                  fontSize: 16,
                  fontWeight: 600,
                  color: "white",
                  marginBottom: 12,
                }}
              >
                {f.judul}
              </div>
              <div
                style={{
                  fontSize: 13,
                  color: "rgba(255,255,255,0.45)",
                  lineHeight: 1.8,
                  fontWeight: 300,
                }}
              >
                {f.desc}
              </div>
            </div>
          ))}
        </div>
      </section>

      {/* ── CTA ── */}
      <section
        style={{
          padding: "100px 48px",
          display: "grid",
          gridTemplateColumns: "1fr 1fr",
          gap: 80,
          alignItems: "center",
        }}
      >
        <div>
          <div className="eyebrow" style={{ marginBottom: 24 }}>
            Mulai sekarang
          </div>
          <h2
            style={{
              fontFamily: "var(--font-serif)",
              fontSize: "clamp(30px, 4vw, 52px)",
              fontWeight: 300,
              color: "var(--color-ink)",
              lineHeight: 1.15,
              marginBottom: 24,
            }}
          >
            Siap mentransformasi
            <br />
            bisnis{" "}
            <span
              style={{ fontStyle: "italic", color: "var(--color-accent)" }}
            >
              properti
            </span>{" "}
            Anda?
          </h2>
          <p
            style={{
              fontSize: 15,
              color: "var(--color-ink-3)",
              lineHeight: 1.8,
              marginBottom: 32,
              fontWeight: 300,
              maxWidth: 400,
            }}
          >
            Bergabung bersama 14 developer properti yang sudah menggunakan
            RumahAsri untuk mengelola 1.800+ unit di Jambi & Indonesia.
          </p>
          <div style={{ display: "flex", gap: 12 }}>
            <Link href="/dashboard" className="btn-primary">
              Minta Demo →
            </Link>
            <a className="btn-ghost" style={{ cursor: "pointer" }}>
              Lihat Harga
            </a>
          </div>
        </div>

        {/* Form */}
        <div className="card" style={{ padding: 36 }}>
          <div
            style={{
              fontFamily: "var(--font-serif)",
              fontSize: 26,
              fontWeight: 300,
              color: "var(--color-ink)",
              marginBottom: 6,
            }}
          >
            Minta Demo Gratis
          </div>
          <div
            style={{
              fontSize: 13,
              color: "var(--color-ink-3)",
              marginBottom: 24,
            }}
          >
            Kami akan menghubungi Anda dalam 24 jam.
          </div>
          <div style={{ display: "flex", flexDirection: "column", gap: 14 }}>
            <div
              style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 12 }}
            >
              <div>
                <label className="form-label">Nama lengkap</label>
                <input className="form-input" placeholder="Budi Santoso" />
              </div>
              <div>
                <label className="form-label">Perusahaan</label>
                <input className="form-input" placeholder="PT Developer Anda" />
              </div>
            </div>
            <div>
              <label className="form-label">Email</label>
              <input
                className="form-input"
                type="email"
                placeholder="budi@developer.co.id"
              />
            </div>
            <div>
              <label className="form-label">WhatsApp</label>
              <input
                className="form-input"
                placeholder="+62 812 xxxx xxxx"
              />
            </div>
            <div>
              <label className="form-label">Jumlah unit</label>
              <select className="form-select">
                <option>Di bawah 50 unit</option>
                <option>50–200 unit</option>
                <option>200–500 unit</option>
                <option>500+ unit</option>
              </select>
            </div>
            <button className="btn-accent" style={{ justifyContent: "center" }}>
              Kirim Permintaan →
            </button>
            <p
              style={{
                fontSize: 11,
                color: "var(--color-ink-3)",
                textAlign: "center",
              }}
            >
              Tanpa komitmen · Uji coba gratis 14 hari
            </p>
          </div>
        </div>
      </section>

      {/* ── FOOTER ── */}
      <footer
        style={{
          background: "var(--color-ink)",
          padding: "60px 48px 32px",
        }}
      >
        <div
          style={{
            display: "grid",
            gridTemplateColumns: "2fr 1fr 1fr 1fr",
            gap: 48,
            marginBottom: 48,
          }}
        >
          <div>
            <div
              style={{
                fontFamily: "var(--font-serif)",
                fontSize: 22,
                color: "white",
                marginBottom: 12,
              }}
            >
              Rumah<span style={{ color: "var(--color-gold)" }}>Asri</span>
            </div>
            <div
              style={{
                fontSize: 13,
                color: "rgba(255,255,255,0.35)",
                lineHeight: 1.7,
                maxWidth: 220,
                fontWeight: 300,
              }}
            >
              Manajemen properti cerdas untuk developer perumahan Indonesia.
              Dibangun oleh JasaPro, Jambi.
            </div>
          </div>
          {[
            {
              title: "Platform",
              links: [
                "Developer Portal",
                "Portal Pembeli",
                "Agen Penjualan",
                "Super Admin",
              ],
            },
            {
              title: "Fitur",
              links: [
                "Lacak Konstruksi",
                "Pelacak Pembayaran",
                "Akuntansi Biaya",
                "Laporan",
              ],
            },
            {
              title: "Perusahaan",
              links: ["Tentang Kami", "Harga", "Kontak", "Kebijakan Privasi"],
            },
          ].map((col) => (
            <div key={col.title}>
              <div
                style={{
                  fontSize: 11,
                  fontWeight: 600,
                  color: "rgba(255,255,255,0.35)",
                  textTransform: "uppercase",
                  letterSpacing: "0.1em",
                  marginBottom: 16,
                }}
              >
                {col.title}
              </div>
              <div style={{ display: "flex", flexDirection: "column", gap: 10 }}>
                {col.links.map((l) => (
                  <a
                    key={l}
                    style={{
                      fontSize: 13,
                      color: "rgba(255,255,255,0.45)",
                      textDecoration: "none",
                      cursor: "pointer",
                      transition: "color 0.2s",
                    }}
                    onMouseEnter={(e) =>
                      ((e.target as HTMLElement).style.color = "white")
                    }
                    onMouseLeave={(e) =>
                      ((e.target as HTMLElement).style.color =
                        "rgba(255,255,255,0.45)")
                    }
                  >
                    {l}
                  </a>
                ))}
              </div>
            </div>
          ))}
        </div>
        <div
          style={{
            borderTop: "1px solid rgba(255,255,255,0.08)",
            paddingTop: 24,
            display: "flex",
            justifyContent: "space-between",
            alignItems: "center",
          }}
        >
          <div style={{ fontSize: 12, color: "rgba(255,255,255,0.25)" }}>
            © 2026 RumahAsri · Hak cipta dilindungi
          </div>
          <div style={{ fontSize: 12, color: "rgba(255,255,255,0.25)" }}>
            Dibangun dengan ❤️ oleh{" "}
            <span style={{ color: "var(--color-gold)" }}>JasaPro</span> ·
            Jambi, Indonesia
          </div>
        </div>
      </footer>
    </div>
  );
}
