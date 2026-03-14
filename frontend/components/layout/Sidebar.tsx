"use client";

import { DEVELOPER } from "@/lib/mock-data";
import { cn } from "@/lib/utils";
import {
  BarChart2,
  Bell,
  Calculator,
  ChevronLeft,
  CreditCard,
  FileText,
  FolderOpen,
  Home,
  LayoutDashboard,
  Settings,
  TrendingUp,
  UserCheck,
  Users,
} from "lucide-react";
import Link from "next/link";
import { usePathname } from "next/navigation";

// ── Nav structure ─────────────────────────────────────────────
// Rule: href (code/URL) = English, label (UI text) = Bahasa Indonesia
const NAV = [
  {
    group: "Ikhtisar",
    items: [
      { href: "/dashboard", icon: LayoutDashboard, label: "Dasbor" },
    ],
  },
  {
    group: "Proyek & Konstruksi",
    items: [
      { href: "/dashboard/projects",     icon: FolderOpen, label: "Semua Proyek" },
      { href: "/dashboard/units",        icon: Home,       label: "Unit" },
      { href: "/dashboard/construction", icon: TrendingUp, label: "Progres Konstruksi" },
    ],
  },
  {
    group: "Penjualan",
    items: [
      { href: "/dashboard/sales",  icon: BarChart2, label: "Dasbor Penjualan" },
      { href: "/dashboard/agents", icon: UserCheck, label: "Agen" },
      { href: "/dashboard/buyers", icon: Users,     label: "Data Pembeli" },
    ],
  },
  {
    group: "Keuangan",
    items: [
      { href: "/dashboard/payments", icon: CreditCard, label: "Pelacak Pembayaran" },
      { href: "/dashboard/costs",    icon: Calculator, label: "Akuntansi Biaya" },
      { href: "/dashboard/reports",  icon: FileText,   label: "Laporan" },
    ],
  },
  {
    group: "Sistem",
    items: [
      { href: "/dashboard/notifications", icon: Bell,     label: "Notifikasi", badge: 4 },
      { href: "/dashboard/settings",      icon: Settings, label: "Pengaturan" },
    ],
  },
];

// ─────────────────────────────────────────────────────────────
export default function Sidebar() {
  const pathname = usePathname();

  return (
    <aside
      style={{
        width: 224,
        minWidth: 224,
        backgroundColor: "white",
        borderRight: "1px solid rgba(14,13,11,0.08)",
        display: "flex",
        flexDirection: "column",
        height: "100vh",
        overflowY: "auto",
      }}
      className="scrollbar-hide"
    >
      {/* ── Logo ── */}
      <div
        style={{
          padding: "20px 16px",
          borderBottom: "1px solid rgba(14,13,11,0.08)",
          flexShrink: 0,
        }}
      >
        <div
          style={{
            fontFamily: "var(--font-serif)",
            fontSize: 20,
            fontWeight: 600,
            color: "var(--color-ink)",
          }}
        >
          Rumah
          <span style={{ color: "var(--color-accent)" }}>Asri</span>
        </div>
        <div
          style={{
            fontSize: 10,
            color: "var(--color-ink-3)",
            marginTop: 2,
            textTransform: "uppercase",
            letterSpacing: "0.08em",
          }}
        >
          Platform Properti
        </div>
      </div>

      {/* ── Developer pill ── */}
      <div
        style={{
          margin: "12px 10px",
          backgroundColor: "var(--color-accent-light)",
          borderRadius: 4,
          padding: "8px 12px",
          flexShrink: 0,
        }}
      >
        <div style={{ fontSize: 10, color: "var(--color-ink-3)" }}>
          Developer aktif
        </div>
        <div
          style={{
            fontSize: 12,
            fontWeight: 500,
            color: "var(--color-accent)",
            lineHeight: 1.3,
            marginTop: 2,
          }}
        >
          {DEVELOPER.nama}
        </div>
      </div>

      {/* ── Nav groups ── */}
      <nav style={{ flex: 1, padding: "4px 8px" }}>
        {NAV.map((group) => (
          <div key={group.group} style={{ marginBottom: 4 }}>
            {/* Group label */}
            <div
              style={{
                fontSize: 10,
                fontWeight: 600,
                color: "var(--color-ink-3)",
                textTransform: "uppercase",
                letterSpacing: "0.07em",
                padding: "10px 12px 4px",
              }}
            >
              {group.group}
            </div>

            {/* Items */}
            {group.items.map((item) => {
              const isActive =
                pathname === item.href ||
                (item.href !== "/dashboard" &&
                  pathname.startsWith(item.href));

              return (
                <Link
                  key={item.href}
                  href={item.href}
                  className={cn("nav-item", isActive && "active")}
                >
                  <item.icon size={15} style={{ flexShrink: 0 }} />
                  <span style={{ flex: 1 }}>{item.label}</span>
                  {"badge" in item && item.badge ? (
                    <span
                      style={{
                        backgroundColor: "var(--color-danger)",
                        color: "white",
                        fontSize: 10,
                        fontWeight: 600,
                        padding: "2px 6px",
                        borderRadius: 999,
                        lineHeight: 1,
                      }}
                    >
                      {item.badge}
                    </span>
                  ) : null}
                </Link>
              );
            })}
          </div>
        ))}
      </nav>

      {/* ── Footer ── */}
      <div
        style={{
          padding: 12,
          borderTop: "1px solid rgba(14,13,11,0.08)",
          flexShrink: 0,
        }}
      >
        <Link
          href="/"
          style={{
            display: "flex",
            alignItems: "center",
            gap: 6,
            fontSize: 12,
            color: "var(--color-ink-3)",
            textDecoration: "none",
            padding: "6px 8px",
            borderRadius: 4,
            transition: "all 0.15s",
          }}
          onMouseEnter={(e) => {
            (e.currentTarget as HTMLElement).style.backgroundColor =
              "var(--color-paper-2)";
            (e.currentTarget as HTMLElement).style.color = "var(--color-ink)";
          }}
          onMouseLeave={(e) => {
            (e.currentTarget as HTMLElement).style.backgroundColor =
              "transparent";
            (e.currentTarget as HTMLElement).style.color =
              "var(--color-ink-3)";
          }}
        >
          <ChevronLeft size={13} />
          Kembali ke beranda
        </Link>
      </div>
    </aside>
  );
}
