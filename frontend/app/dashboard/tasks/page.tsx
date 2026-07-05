"use client";
// =============================================================================
// === frontend/app/dashboard/tasks/page.tsx ===
// Sprint 19: standalone Tasks & Actions page. Thin wrapper around the
// shared NextActionsPanel (extracted to components/dashboard/TaskPanels.tsx)
// — same component already proven on the Command Center, given its own
// dedicated home so it doesn't have to compete for space with Event
// Stream, Portfolio Intelligence, and everything else on that page.
// =============================================================================

import { NextActionsPanel } from "@/components/dashboard/TaskPanels";
import { Target } from "lucide-react";

export default function TasksPage() {
  return (
    <div style={{ padding: 24 }}>
      <div style={{ marginBottom: 20 }}>
        <div style={{ display: "flex", alignItems: "center", gap: 8, marginBottom: 4 }}>
          <Target size={20} style={{ color: "var(--color-accent)" }} />
          <h1 style={{ fontSize: 20, fontWeight: 700, color: "var(--color-ink)", margin: 0 }}>
            Tugas &amp; Tindakan
          </h1>
        </div>
        <div style={{ fontSize: 13, color: "var(--color-ink-3)" }}>
          Semua tugas Anda dan tugas yang belum ditugaskan, di seluruh proyek
        </div>
      </div>

      <NextActionsPanel />
    </div>
  );
}
