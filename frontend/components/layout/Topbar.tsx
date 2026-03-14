"use client";

import { Bell, ChevronDown, Search } from "lucide-react";
import { usePathname } from "next/navigation";

// ── Page title map ─────────────────────────────────────────────
// Rule: keys (URLs) = English, values (titles) = Bahasa Indonesia
const TITLES: Record<string, string> = {
  "/dashboard":                "Dasbor",
  "/dashboard/projects":       "Semua Proyek",
  "/dashboard/units":          "Unit",
  "/dashboard/construction":   "Progres Konstruksi",
  "/dashboard/sales":          "Dasbor Penjualan",
  "/dashboard/agents":         "Agen Penjualan",
  "/dashboard/buyers":         "Data Pembeli",
  "/dashboard/payments":       "Pelacak Pembayaran",
  "/dashboard/costs":          "Akuntansi Biaya",
  "/dashboard/reports":        "Laporan",
  "/dashboard/notifications":  "Notifikasi",
  "/dashboard/settings":       "Pengaturan",
};

// ─────────────────────────────────────────────────────────────
export default function Topbar() {
  const pathname = usePathname();
  const title = TITLES[pathname] ?? "Dashboard";

  return (
    <header
      style={{
        backgroundColor: "white",
        borderBottom: "1px solid rgba(14,13,11,0.08)",
        height: 52,
        display: "flex",
        alignItems: "center",
        justifyContent: "space-between",
        padding: "0 24px",
        flexShrink: 0,
        position: "sticky",
        top: 0,
        zIndex: 20,
      }}
    >
      {/* ── Left — breadcrumb + title ── */}
      <div style={{ display: "flex", alignItems: "center", gap: 8 }}>
        <span style={{ fontSize: 13, color: "var(--color-ink-3)" }}>
          PT Asri Sentosa /
        </span>
        <span
          style={{
            fontSize: 14,
            fontWeight: 600,
            color: "var(--color-ink)",
          }}
        >
          {title}
        </span>
      </div>

      {/* ── Right — actions + avatar ── */}
      <div style={{ display: "flex", alignItems: "center", gap: 4 }}>

        {/* Search */}
        <button
          style={{
            padding: 8,
            borderRadius: 4,
            border: "none",
            backgroundColor: "transparent",
            cursor: "pointer",
            color: "var(--color-ink-3)",
            display: "flex",
            alignItems: "center",
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
          <Search size={15} />
        </button>

        {/* Notifications */}
        <button
          style={{
            position: "relative",
            padding: 8,
            borderRadius: 4,
            border: "none",
            backgroundColor: "transparent",
            cursor: "pointer",
            display: "flex",
            alignItems: "center",
            transition: "all 0.15s",
          }}
          onMouseEnter={(e) =>
            ((e.currentTarget as HTMLElement).style.backgroundColor =
              "var(--color-paper-2)")
          }
          onMouseLeave={(e) =>
            ((e.currentTarget as HTMLElement).style.backgroundColor =
              "transparent")
          }
        >
          <Bell size={15} style={{ color: "var(--color-ink-3)" }} />
          {/* Unread dot */}
          <span
            style={{
              position: "absolute",
              top: 6,
              right: 6,
              width: 6,
              height: 6,
              backgroundColor: "var(--color-danger)",
              borderRadius: "50%",
              border: "1.5px solid white",
            }}
          />
        </button>

        {/* Divider */}
        <div
          style={{
            width: 1,
            height: 20,
            backgroundColor: "rgba(14,13,11,0.08)",
            margin: "0 4px",
          }}
        />

        {/* Avatar + name */}
        <div
          style={{
            display: "flex",
            alignItems: "center",
            gap: 8,
            cursor: "pointer",
            padding: "4px 8px",
            borderRadius: 4,
            transition: "all 0.15s",
          }}
          onMouseEnter={(e) =>
            ((e.currentTarget as HTMLElement).style.backgroundColor =
              "var(--color-paper-2)")
          }
          onMouseLeave={(e) =>
            ((e.currentTarget as HTMLElement).style.backgroundColor =
              "transparent")
          }
        >
          {/* Avatar circle */}
          <div
            style={{
              width: 28,
              height: 28,
              borderRadius: "50%",
              backgroundColor: "var(--color-accent-light)",
              display: "flex",
              alignItems: "center",
              justifyContent: "center",
              fontSize: 11,
              fontWeight: 600,
              color: "var(--color-accent)",
              flexShrink: 0,
            }}
          >
            AS
          </div>
          <span
            style={{
              fontSize: 12,
              fontWeight: 500,
              color: "var(--color-ink)",
            }}
          >
            Admin
          </span>
          <ChevronDown size={13} style={{ color: "var(--color-ink-3)" }} />
        </div>
      </div>
    </header>
  );
}
