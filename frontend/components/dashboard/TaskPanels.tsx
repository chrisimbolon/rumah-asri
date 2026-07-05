"use client";
// =============================================================================
// === frontend/components/dashboard/TaskPanels.tsx ===
// Sprint 19 extraction: NextActionsPanel + ActionCard were previously
// defined locally inside app/dashboard/page.tsx (Sprint 9). Moved here,
// unchanged, so they can be shared between the Command Center AND the
// new standalone Tasks & Actions page without duplicating logic —
// same pattern as the earlier IntelligencePanels.tsx extraction.
// =============================================================================

import {
  ACTION_TYPE_META,
  ActionItem,
  MyActionsResponse,
  projectsApi,
} from "@/lib/api/projects";
import { ArrowRight, Loader2 } from "lucide-react";
import Link from "next/link";
import { useEffect, useState } from "react";

export function NextActionsPanel() {
  const [actions, setActions] = useState<MyActionsResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [showAll, setShowAll] = useState(false);

  useEffect(() => {
    projectsApi.getMyActions()
      .then(setActions)
      .catch(() => setActions(null))
      .finally(() => setLoading(false));
  }, []);

  if (loading) {
    return (
      <div className="card" style={{ marginBottom: 16, padding: 24, textAlign: "center" }}>
        <Loader2 size={18} style={{ animation: "spin 1s linear infinite", color: "var(--color-ink-3)" }} />
      </div>
    );
  }

  if (!actions || actions.total_actionable === 0) {
    return (
      <div className="card" style={{ marginBottom: 16, padding: 20, textAlign: "center" }}>
        <div style={{ fontSize: 13, color: "var(--color-ink-3)" }}>
          ✨ Tidak ada tindakan mendesak — semua proyek dalam kendali
        </div>
      </div>
    );
  }

  const myTasksToShow   = showAll ? actions.my_tasks   : actions.my_tasks.slice(0, 3);
  const unassignedToShow = showAll ? actions.unassigned : actions.unassigned.slice(0, 2);

  return (
    <div className="card" style={{ marginBottom: 16 }}>
      <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between", marginBottom: 16 }}>
        <div>
          <div style={{ fontSize: 14, fontWeight: 700, color: "var(--color-ink)" }}>
            🎯 Tindakan Berikutnya
          </div>
          <div style={{ fontSize: 11, color: "var(--color-ink-3)", marginTop: 2 }}>
            {actions.my_tasks_count} tugas Anda · {actions.unassigned_count} belum ditugaskan
          </div>
        </div>
        {actions.total_actionable > 5 && (
          <button
            onClick={() => setShowAll(!showAll)}
            style={{ fontSize: 11, fontWeight: 600, color: "var(--color-accent)", background: "none", border: "none", cursor: "pointer" }}>
            {showAll ? "Tampilkan lebih sedikit" : `Lihat semua (${actions.total_actionable})`}
          </button>
        )}
      </div>

      {/* ── My tasks section ── */}
      {myTasksToShow.length > 0 && (
        <div style={{ marginBottom: unassignedToShow.length > 0 ? 16 : 0 }}>
          <div style={{ fontSize: 10, fontWeight: 700, color: "var(--color-ink-3)", textTransform: "uppercase", letterSpacing: "0.06em", marginBottom: 8 }}>
            Tugas Anda
          </div>
          <div style={{ display: "flex", flexDirection: "column", gap: 8 }}>
            {myTasksToShow.map((item) => (
              <ActionCard key={`${item.project_id}-${item.requirement_id}`} item={item} />
            ))}
          </div>
        </div>
      )}
      {/* ── Unassigned section ── */}
      {unassignedToShow.length > 0 && (
        <div>
          <div style={{ fontSize: 10, fontWeight: 700, color: "var(--color-ink-3)", textTransform: "uppercase", letterSpacing: "0.06em", marginBottom: 8 }}>
            Belum Ditugaskan — Bisa Anda Ambil
          </div>
          <div style={{ display: "flex", flexDirection: "column", gap: 8 }}>
            {unassignedToShow.map((item) => (
              <ActionCard key={`${item.project_id}-${item.requirement_id}`} item={item} muted />
            ))}
          </div>
        </div>
      )}
    </div>
  );
}

// ── Action card sub-component ───────────────────────────────────
export function ActionCard({ item, muted = false }: { item: ActionItem; muted?: boolean }) {
  const meta = ACTION_TYPE_META[item.action_type];
  return (
    <Link
      href={`/dashboard/projects/${item.project_id}`}
      style={{
        display: "flex", alignItems: "center", gap: 10,
        padding: "10px 12px", borderRadius: 8, textDecoration: "none",
        backgroundColor: muted ? "var(--color-paper-2)" : meta.bg,
        border: `1px solid ${muted ? "rgba(14,13,11,0.06)" : meta.color + "22"}`,
        transition: "transform 0.15s",
      }}>
      <span style={{ fontSize: 16, flexShrink: 0 }}>{meta.icon}</span>
      <div style={{ flex: 1, minWidth: 0 }}>
        <div style={{ display: "flex", alignItems: "center", gap: 6, marginBottom: 2 }}>
          <span style={{ fontSize: 12, fontWeight: 600, color: "var(--color-ink)" }}>
            {item.requirement_name}
          </span>
          <span style={{ fontSize: 9, fontWeight: 700, padding: "1px 6px", borderRadius: 999, color: meta.color, backgroundColor: "white" }}>
            {meta.label}
          </span>
        </div>
        <div style={{ fontSize: 10, color: "var(--color-ink-3)" }}>
          {item.project_name} · {item.primary_reason}
        </div>
      </div>
      <ArrowRight size={14} style={{ color: "var(--color-ink-3)", flexShrink: 0 }} />
    </Link>
  );
}
