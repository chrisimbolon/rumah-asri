// =============================================================================
// === frontend/app/dashboard/admin/page.tsx ===
// =============================================================================
/**
 * Super Admin — Platform Management - this is so dense, need to dig dive intensively
 * Lists all organizations on the platform.
 * Only accessible to super_admin role (enforced by proxy.ts + this page's own guard).
 */
"use client";

import { useAuth } from "@/context/AuthContext";
import { Organization, organizationsApi } from "@/lib/api/organizations";
import {
  Building2, CheckCircle2,
  FolderOpen,
  Loader2,
  Shield,
  Users,
} from "lucide-react";
import { useRouter } from "next/navigation";
import { useEffect, useState } from "react";

function formatDate(iso: string): string {
  try {
    return new Date(iso).toLocaleDateString("id-ID", { day: "numeric", month: "short", year: "numeric" });
  } catch { return iso; }
}

export default function AdminPage() {
  const { user } = useAuth();
  const router   = useRouter();

  const [orgs,    setOrgs]    = useState<Organization[]>([]);
  const [loading, setLoading] = useState(true);
  const [error,   setError]   = useState<string | null>(null);

  // ── Guard — redirect non-super-admins ───────────────────
  useEffect(() => {
    if (user && user.role !== "super_admin") {
      router.replace("/dashboard");
    }
  }, [user, router]);

  useEffect(() => {
    if (!user || user.role !== "super_admin") return;
    organizationsApi.list()
      .then(setOrgs)
      .catch(() => setError("Gagal memuat data organisasi"))
      .finally(() => setLoading(false));
  }, [user]);

  if (loading) {
    return (
      <div style={{ display: "flex", alignItems: "center", justifyContent: "center", height: 300, gap: 10, color: "var(--color-ink-3)" }}>
        <Loader2 size={18} style={{ animation: "spin 1s linear infinite" }} />
        <span style={{ fontSize: 13 }}>Memuat organisasi…</span>
      </div>
    );
  }

  if (error) {
    return <div style={{ padding: 24, textAlign: "center", color: "var(--color-danger)", fontSize: 13 }}>{error}</div>;
  }

  const activeOrgs = orgs.filter((o) => o.is_active).length;
  const totalProjects = orgs.reduce((s, o) => s + o.project_count, 0);
  const totalMembers  = orgs.reduce((s, o) => s + o.member_count, 0);

  return (
    <div style={{ maxWidth: 1100, margin: "0 auto" }}>

      {/* ── Page header ── */}
      <div className="page-header" style={{ display: "flex", alignItems: "flex-start", justifyContent: "space-between" }}>
        <div>
          <div style={{ display: "flex", alignItems: "center", gap: 8, marginBottom: 6 }}>
            <Shield size={16} style={{ color: "var(--color-accent)" }} />
            <span style={{ fontSize: 11, fontWeight: 600, color: "var(--color-accent)", textTransform: "uppercase", letterSpacing: "0.08em" }}>Super Admin</span>
          </div>
          <h1 className="page-title">Manajemen Platform</h1>
          <p className="page-subtitle">Semua developer dan organisasi yang terdaftar di DevelopIndo</p>
        </div>
      </div>

      {/* ── Platform stats ── */}
      <div style={{ display: "grid", gridTemplateColumns: "repeat(4, 1fr)", gap: 12, marginBottom: 24 }}>
        {[
          { label: "Total Organisasi", value: orgs.length,    icon: Building2,    color: "var(--color-accent)",  bg: "var(--color-accent-light)"  },
          { label: "Aktif",            value: activeOrgs,     icon: CheckCircle2, color: "var(--color-success)", bg: "var(--color-success-light)" },
          { label: "Total Proyek",     value: totalProjects,  icon: FolderOpen,   color: "var(--color-warning)", bg: "var(--color-warning-light)" },
          { label: "Total Member",     value: totalMembers,   icon: Users,        color: "var(--color-info)",    bg: "var(--color-info-light)"    },
        ].map((s) => (
          <div key={s.label} className="metric-card">
            <div style={{ display: "flex", alignItems: "flex-start", justifyContent: "space-between", marginBottom: 10 }}>
              <div className="metric-label">{s.label}</div>
              <div style={{ width: 30, height: 30, borderRadius: 6, backgroundColor: s.bg, display: "flex", alignItems: "center", justifyContent: "center" }}>
                <s.icon size={14} style={{ color: s.color }} />
              </div>
            </div>
            <div className="metric-value">{s.value}</div>
          </div>
        ))}
      </div>

      {/* ── Org cards ── */}
      <div style={{ display: "grid", gridTemplateColumns: "repeat(2, 1fr)", gap: 16 }}>
        {orgs.map((org) => (
          <div key={org.id} className="card" style={{ position: "relative", overflow: "hidden" }}>
            {/* Status strip */}
            <div style={{ position: "absolute", top: 0, left: 0, right: 0, height: 3, backgroundColor: org.is_active ? "var(--color-success)" : "var(--color-ink-3)" }} />

            <div style={{ paddingTop: 8 }}>
              {/* Header */}
              <div style={{ display: "flex", alignItems: "flex-start", justifyContent: "space-between", marginBottom: 16 }}>
                <div>
                  <div style={{ fontSize: 16, fontWeight: 600, color: "var(--color-ink)", marginBottom: 4 }}>{org.name}</div>
                  <div style={{ display: "flex", alignItems: "center", gap: 8 }}>
                    <span style={{ fontSize: 11, backgroundColor: "var(--color-accent-light)", color: "var(--color-accent)", padding: "2px 8px", borderRadius: 999, fontWeight: 500 }}>
                      {org.plan}
                    </span>
                    <span style={{ fontSize: 11, color: "var(--color-ink-3)" }}>
                      Bergabung {formatDate(org.created_at)}
                    </span>
                  </div>
                </div>
                <span className={`badge ${org.is_active ? "badge-green" : "badge-gray"}`}>
                  {org.is_active ? "Aktif" : "Nonaktif"}
                </span>
              </div>

              {/* Stats */}
              <div style={{ display: "grid", gridTemplateColumns: "repeat(3, 1fr)", gap: 8, padding: "14px 0", borderTop: "1px solid rgba(14,13,11,0.06)", borderBottom: "1px solid rgba(14,13,11,0.06)", marginBottom: 16 }}>
                {[
                  { label: "Proyek", value: org.project_count },
                  { label: "Member", value: org.member_count  },
                  { label: "Paket",  value: org.plan          },
                ].map((s) => (
                  <div key={s.label} style={{ textAlign: "center" }}>
                    <div style={{ fontFamily: "var(--font-serif)", fontSize: 22, fontWeight: 600, color: "var(--color-ink)", lineHeight: 1 }}>{s.value}</div>
                    <div style={{ fontSize: 10, color: "var(--color-ink-3)", marginTop: 4, textTransform: "uppercase", letterSpacing: "0.04em" }}>{s.label}</div>
                  </div>
                ))}
              </div>

              {/* Actions */}
              <div style={{ display: "flex", gap: 8, justifyContent: "flex-end" }}>
                <button className="btn-ghost btn-sm" style={{ display: "inline-flex", alignItems: "center", gap: 4 }}>
                  <Users size={12} /> Anggota
                </button>
                <button className="btn-ghost btn-sm" style={{ display: "inline-flex", alignItems: "center", gap: 4 }}>
                  <FolderOpen size={12} /> Proyek
                </button>
                <button className="btn-accent btn-sm" style={{ display: "inline-flex", alignItems: "center", gap: 4 }}>
                  <Building2 size={12} /> Detail
                </button>
              </div>
            </div>
          </div>
        ))}
      </div>

      {orgs.length === 0 && (
        <div style={{ textAlign: "center", padding: 60, color: "var(--color-ink-3)" }}>
          <Building2 size={32} style={{ margin: "0 auto 12px", opacity: 0.3 }} />
          <div style={{ fontSize: 14 }}>Belum ada organisasi terdaftar</div>
        </div>
      )}
    </div>
  );
}