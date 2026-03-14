import {
  STATISTIK,
  PROYEK,
  NOTIFIKASI,
  LOG,
  GRAFIK_PENJUALAN,
  badgeStatus,
  labelStatus,
  warnaProgres,
} from "@/lib/mock-data";
import {
  TrendingUp,
  TrendingDown,
  Home,
  Users,
  BarChart2,
  ArrowRight,
  CheckCircle2,
  AlertCircle,
  Info,
  FolderOpen,
  Activity,
} from "lucide-react";
import Link from "next/link";
import SalesChart from "@/components/charts/SalesChart";

// ─────────────────────────────────────────────────────────────
//  Metric Card
// ─────────────────────────────────────────────────────────────
function MetricCard({
  label,
  value,
  sub,
  trend,
  trendUp,
  icon: Icon,
  iconBg,
  iconColor,
}: {
  label: string;
  value: string;
  sub: string;
  trend?: string;
  trendUp?: boolean;
  icon: React.ElementType;
  iconBg: string;
  iconColor: string;
}) {
  return (
    <div className="metric-card">
      <div
        style={{
          display: "flex",
          alignItems: "flex-start",
          justifyContent: "space-between",
          marginBottom: 12,
        }}
      >
        <div className="metric-label">{label}</div>
        <div
          style={{
            width: 32,
            height: 32,
            borderRadius: 6,
            backgroundColor: iconBg,
            display: "flex",
            alignItems: "center",
            justifyContent: "center",
            flexShrink: 0,
          }}
        >
          <Icon size={15} style={{ color: iconColor }} />
        </div>
      </div>

      <div className="metric-value">{value}</div>

      <div
        style={{
          display: "flex",
          alignItems: "center",
          gap: 6,
          marginTop: 8,
        }}
      >
        {trend && (
          <span
            style={{
              display: "inline-flex",
              alignItems: "center",
              gap: 2,
              fontSize: 11,
              fontWeight: 500,
              color: trendUp
                ? "var(--color-success)"
                : "var(--color-danger)",
            }}
          >
            {trendUp ? (
              <TrendingUp size={11} />
            ) : (
              <TrendingDown size={11} />
            )}
            {trend}
          </span>
        )}
        <span className="metric-sub">{sub}</span>
      </div>
    </div>
  );
}

// ─────────────────────────────────────────────────────────────
//  Notification icon + colour helpers
// ─────────────────────────────────────────────────────────────
const NOTIF_ICON = {
  info:       Info,
  sukses:     CheckCircle2,
  peringatan: AlertCircle,
} as const;

const NOTIF_COLOR = {
  info:       "var(--color-info)",
  sukses:     "var(--color-success)",
  peringatan: "var(--color-warning)",
} as const;

const NOTIF_BG = {
  info:       "var(--color-info-light)",
  sukses:     "var(--color-success-light)",
  peringatan: "var(--color-warning-light)",
} as const;

// ─────────────────────────────────────────────────────────────
//  Dashboard Page
// ─────────────────────────────────────────────────────────────
export default function DashboardPage() {
  const unread = NOTIFIKASI.filter((n) => !n.dibaca).length;

  return (
    <div style={{ maxWidth: 1100, margin: "0 auto" }}>

      {/* ── Page header ── */}
      <div className="page-header">
        <h1 className="page-title">Selamat pagi, Admin 👋</h1>
        <p className="page-subtitle">
          Ringkasan performa platform — PT Asri Sentosa Properti · Jambi
        </p>
      </div>

      {/* ── Metric cards ── */}
      <div
        style={{
          display: "grid",
          gridTemplateColumns: "repeat(4, 1fr)",
          gap: 12,
          marginBottom: 20,
        }}
      >
        <MetricCard
          label="Total Proyek"
          value={String(STATISTIK.total_proyek)}
          sub="proyek aktif"
          trend="+1 bulan ini"
          trendUp={true}
          icon={FolderOpen}
          iconBg="var(--color-info-light)"
          iconColor="var(--color-info)"
        />
        <MetricCard
          label="Unit Terjual"
          value={String(STATISTIK.unit_terjual)}
          sub={`dari ${STATISTIK.total_unit} unit`}
          trend="+8% vs bulan lalu"
          trendUp={true}
          icon={Home}
          iconBg="var(--color-success-light)"
          iconColor="var(--color-success)"
        />
        <MetricCard
          label="Sedang Konstruksi"
          value={String(STATISTIK.unit_konstruksi)}
          sub="unit aktif dibangun"
          icon={BarChart2}
          iconBg="var(--color-warning-light)"
          iconColor="var(--color-warning)"
        />
        <MetricCard
          label="Pendapatan Bulan Ini"
          value={STATISTIK.pendapatan_bulan}
          sub="bulan Maret 2026"
          trend={STATISTIK.pertumbuhan}
          trendUp={true}
          icon={TrendingUp}
          iconBg="var(--color-gold-light)"
          iconColor="var(--color-gold)"
        />
      </div>

      {/* ── Main grid — projects + notifications ── */}
      <div
        style={{
          display: "grid",
          gridTemplateColumns: "1fr 340px",
          gap: 16,
          marginBottom: 16,
        }}
      >
        {/* Projects list */}
        <div className="card">
          <div
            style={{
              display: "flex",
              alignItems: "center",
              justifyContent: "space-between",
              marginBottom: 20,
            }}
          >
            <div className="section-title" style={{ marginBottom: 0 }}>
              Semua Proyek
            </div>
            <Link
              href="/dashboard/proyek"
              style={{
                display: "inline-flex",
                alignItems: "center",
                gap: 4,
                fontSize: 12,
                color: "var(--color-accent)",
                textDecoration: "none",
              }}
            >
              Lihat semua <ArrowRight size={12} />
            </Link>
          </div>

          <div style={{ display: "flex", flexDirection: "column", gap: 20 }}>
            {PROYEK.map((p) => (
              <div
                key={p.id}
                style={{ display: "flex", alignItems: "center", gap: 14 }}
              >
                {/* Icon */}
                <div
                  style={{
                    width: 36,
                    height: 36,
                    borderRadius: 6,
                    backgroundColor: "var(--color-paper-2)",
                    display: "flex",
                    alignItems: "center",
                    justifyContent: "center",
                    fontSize: 13,
                    fontWeight: 700,
                    color: "var(--color-ink-3)",
                    flexShrink: 0,
                  }}
                >
                  {p.nama.charAt(0)}
                </div>

                {/* Details */}
                <div style={{ flex: 1, minWidth: 0 }}>
                  <div
                    style={{
                      display: "flex",
                      alignItems: "center",
                      justifyContent: "space-between",
                      marginBottom: 6,
                    }}
                  >
                    <div
                      style={{
                        fontSize: 13,
                        fontWeight: 500,
                        color: "var(--color-ink)",
                        overflow: "hidden",
                        textOverflow: "ellipsis",
                        whiteSpace: "nowrap",
                      }}
                    >
                      {p.nama}
                    </div>
                    <div
                      style={{
                        fontSize: 13,
                        fontWeight: 600,
                        color: "var(--color-ink)",
                        marginLeft: 12,
                        flexShrink: 0,
                      }}
                    >
                      {p.progres}%
                    </div>
                  </div>

                  {/* Progress bar */}
                  <div className="progress-bar" style={{ marginBottom: 6 }}>
                    <div
                      className="progress-fill"
                      style={{
                        width: `${p.progres}%`,
                        backgroundColor: warnaProgres(p.progres),
                      }}
                    />
                  </div>

                  {/* Meta row */}
                  <div
                    style={{
                      display: "flex",
                      alignItems: "center",
                      justifyContent: "space-between",
                    }}
                  >
                    <span
                      style={{
                        fontSize: 11,
                        color: "var(--color-ink-3)",
                      }}
                    >
                      {p.lokasi}
                    </span>
                    <div
                      style={{
                        display: "flex",
                        alignItems: "center",
                        gap: 8,
                      }}
                    >
                      <span className={`badge ${badgeStatus(p.status)}`}>
                        {labelStatus(p.status)}
                      </span>
                      <span
                        style={{
                          fontSize: 11,
                          color: "var(--color-ink-3)",
                        }}
                      >
                        {p.terjual}/{p.total_unit} unit
                      </span>
                    </div>
                  </div>
                </div>
              </div>
            ))}
          </div>
        </div>

        {/* Notifications */}
        <div className="card">
          <div
            style={{
              display: "flex",
              alignItems: "center",
              justifyContent: "space-between",
              marginBottom: 20,
            }}
          >
            <div className="section-title" style={{ marginBottom: 0 }}>
              Notifikasi
            </div>
            <span className="badge badge-red">{unread} baru</span>
          </div>

          <div style={{ display: "flex", flexDirection: "column", gap: 8 }}>
            {NOTIFIKASI.slice(0, 5).map((n) => {
              const Icon = NOTIF_ICON[n.tipe];
              return (
                <div
                  key={n.id}
                  style={{
                    display: "flex",
                    gap: 12,
                    padding: "10px 12px",
                    borderRadius: 6,
                    backgroundColor: !n.dibaca
                      ? NOTIF_BG[n.tipe]
                      : "transparent",
                    transition: "background 0.15s",
                  }}
                >
                  <Icon
                    size={15}
                    style={{
                      color: NOTIF_COLOR[n.tipe],
                      flexShrink: 0,
                      marginTop: 1,
                    }}
                  />
                  <div style={{ minWidth: 0 }}>
                    <div
                      style={{
                        fontSize: 12,
                        fontWeight: 500,
                        color: "var(--color-ink)",
                        lineHeight: 1.3,
                      }}
                    >
                      {n.judul}
                    </div>
                    <div
                      style={{
                        fontSize: 11,
                        color: "var(--color-ink-3)",
                        marginTop: 2,
                        lineHeight: 1.4,
                      }}
                    >
                      {n.pesan}
                    </div>
                    <div
                      style={{
                        fontSize: 10,
                        color: "var(--color-ink-3)",
                        marginTop: 4,
                      }}
                    >
                      {n.waktu}
                    </div>
                  </div>
                  {/* Unread dot */}
                  {!n.dibaca && (
                    <div
                      style={{
                        width: 6,
                        height: 6,
                        borderRadius: "50%",
                        backgroundColor: NOTIF_COLOR[n.tipe],
                        flexShrink: 0,
                        marginTop: 4,
                      }}
                    />
                  )}
                </div>
              );
            })}
          </div>

          <Link
            href="/dashboard/notifikasi"
            style={{
              display: "inline-flex",
              alignItems: "center",
              gap: 4,
              fontSize: 12,
              color: "var(--color-accent)",
              textDecoration: "none",
              marginTop: 12,
            }}
          >
            Semua notifikasi <ArrowRight size={12} />
          </Link>
        </div>
      </div>

      {/* ── Bottom grid — chart + activity log ── */}
      <div
        style={{
          display: "grid",
          gridTemplateColumns: "1fr 340px",
          gap: 16,
        }}
      >
        {/* Sales chart */}
        <div className="card">
          <div
            style={{
              display: "flex",
              alignItems: "center",
              justifyContent: "space-between",
              marginBottom: 20,
            }}
          >
            <div>
              <div className="section-title" style={{ marginBottom: 2 }}>
                Grafik Penjualan
              </div>
              <div
                style={{ fontSize: 12, color: "var(--color-ink-3)" }}
              >
                6 bulan terakhir
              </div>
            </div>
            <div
              style={{
                display: "flex",
                alignItems: "center",
                gap: 8,
              }}
            >
              <span className="badge badge-green"
                style={{ display: "inline-flex", alignItems: "center", gap: 4 }}
              >
                <TrendingUp size={10} /> +14%
              </span>
              <Link
                href="/dashboard/penjualan"
                style={{
                  display: "inline-flex",
                  alignItems: "center",
                  gap: 4,
                  fontSize: 12,
                  color: "var(--color-accent)",
                  textDecoration: "none",
                }}
              >
                Detail <ArrowRight size={12} />
              </Link>
            </div>
          </div>
          <SalesChart data={GRAFIK_PENJUALAN} />

          {/* Chart legend */}
          <div
            style={{
              display: "flex",
              gap: 20,
              marginTop: 16,
              paddingTop: 16,
              borderTop: "1px solid rgba(14,13,11,0.06)",
            }}
          >
            {[
              { label: "Total terjual", value: "89 unit", color: "var(--color-accent)" },
              { label: "Bulan terbaik", value: "Mar — 13 unit", color: "var(--color-success)" },
              { label: "Rata-rata", value: "8,2 unit/bulan", color: "var(--color-gold)" },
            ].map((item) => (
              <div key={item.label} style={{ display: "flex", alignItems: "center", gap: 8 }}>
                <div
                  style={{
                    width: 8,
                    height: 8,
                    borderRadius: "50%",
                    backgroundColor: item.color,
                    flexShrink: 0,
                  }}
                />
                <div>
                  <div style={{ fontSize: 10, color: "var(--color-ink-3)", textTransform: "uppercase", letterSpacing: "0.04em" }}>
                    {item.label}
                  </div>
                  <div style={{ fontSize: 12, fontWeight: 600, color: "var(--color-ink)" }}>
                    {item.value}
                  </div>
                </div>
              </div>
            ))}
          </div>
        </div>

        {/* Activity log */}
        <div className="card">
          <div
            style={{
              display: "flex",
              alignItems: "center",
              justifyContent: "space-between",
              marginBottom: 20,
            }}
          >
            <div className="section-title" style={{ marginBottom: 0 }}>
              Log Aktivitas
            </div>
            <Activity size={14} style={{ color: "var(--color-ink-3)" }} />
          </div>

          <div style={{ display: "flex", flexDirection: "column", gap: 0 }}>
            {LOG.map((l, i) => (
              <div
                key={i}
                style={{
                  display: "flex",
                  gap: 12,
                  paddingBottom: i < LOG.length - 1 ? 16 : 0,
                  position: "relative",
                }}
              >
                {/* Timeline connector */}
                {i < LOG.length - 1 && (
                  <div
                    style={{
                      position: "absolute",
                      left: 5,
                      top: 14,
                      width: 1,
                      height: "100%",
                      backgroundColor: "rgba(14,13,11,0.08)",
                    }}
                  />
                )}

                {/* Dot */}
                <div
                  style={{
                    width: 11,
                    height: 11,
                    borderRadius: "50%",
                    backgroundColor:
                      i === 0
                        ? "var(--color-accent)"
                        : "var(--color-paper-3)",
                    border:
                      i === 0
                        ? "none"
                        : "1px solid rgba(14,13,11,0.15)",
                    flexShrink: 0,
                    marginTop: 3,
                    position: "relative",
                    zIndex: 1,
                  }}
                />

                {/* Content */}
                <div style={{ minWidth: 0, paddingBottom: 2 }}>
                  <div
                    style={{
                      fontSize: 12,
                      fontWeight: 500,
                      color: "var(--color-ink)",
                      lineHeight: 1.3,
                    }}
                  >
                    {l.pengguna}
                  </div>
                  <div
                    style={{
                      fontSize: 11,
                      color: "var(--color-ink-3)",
                      lineHeight: 1.4,
                      marginTop: 2,
                    }}
                  >
                    {l.aksi}
                  </div>
                  <div
                    style={{
                      fontSize: 10,
                      color: "var(--color-ink-3)",
                      marginTop: 3,
                      opacity: 0.7,
                    }}
                  >
                    {l.waktu}
                  </div>
                </div>
              </div>
            ))}
          </div>
        </div>
      </div>

    </div>
  );
}
