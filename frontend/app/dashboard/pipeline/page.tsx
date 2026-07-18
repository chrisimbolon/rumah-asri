"use client";
// =============================================================================
// === frontend/app/dashboard/pipeline/page.tsx ===
// =============================================================================
/**
 * CRM Foundation Sprint 7: Pipeline Kanban.
 *
 * Pure frontend — zero new backend, zero migration, per the roadmap.
 * Reuses prospectsApi.list()/update() from lib/api/crm.ts entirely
 * as-is; drag-and-drop is just a PUT with a new `status`, the same
 * CRUD endpoint Sprint 2.5 already shipped.
 *
 * One real constraint, not a missing feature: the "Won" column does
 * NOT accept drops. Decision 1 (Phase B roadmap) established that
 * WON only means something honest when a real Booking exists behind
 * it — dragging a card straight into Won with nothing but a status
 * change would create exactly the fiction that decision was written
 * to prevent. Winning still only happens through the real "Konversi"
 * flow on the Prospect list page (pick a real unit, a real buyer,
 * hit the real booking endpoint).
 *
 * "Diperbarui X hari lalu" on each card is deliberately NOT labeled
 * "days in this stage" — Prospect only has `updated_at`, which moves
 * on ANY field edit (notes, assigned_to, etc.), not specifically on
 * status changes. Claiming stage-entry precision we don't actually
 * track would be exactly the kind of overclaim this codebase has avoided everywhere else.
 */

import { Prospect, prospectsApi } from "@/lib/api/crm";
import {
  AlertTriangle,
  Building2,
  Clock,
  GripVertical,
  Loader2,
  Lock,
  Phone,
  RefreshCw,
} from "lucide-react";
import { useEffect, useState } from "react";

// ── Pipeline columns, in stage order — same order STATUS_TABS uses
//    on the Prospect list page for consistency. ────────────────
const COLUMNS: { key: Prospect["status"]; label: string; locked?: boolean }[] = [
  { key: "lead",        label: "Lead"        },
  { key: "qualified",   label: "Qualified"   },
  { key: "follow_up",   label: "Follow Up"   },
  { key: "site_visit",  label: "Site Visit"  },
  { key: "negotiation", label: "Negotiation" },
  { key: "won",         label: "Won", locked: true },
  { key: "lost",        label: "Lost"        },
];

const COLUMN_ACCENT: Record<Prospect["status"], string> = {
  lead:         "var(--color-info)",
  qualified:    "var(--color-info)",
  follow_up:    "var(--color-warning)",
  site_visit:   "var(--color-warning)",
  negotiation:  "var(--color-accent)",
  won:          "var(--color-success)",
  lost:         "var(--color-ink-3)",
};

function daysAgo(iso: string): number {
  return Math.floor((Date.now() - new Date(iso).getTime()) / 86_400_000);
}

function ProspectCard({
  prospect,
  onDragStart,
  isDragging,
}: {
  prospect:    Prospect;
  onDragStart: (id: string) => void;
  isDragging:  boolean;
}) {
  const followUpOverdue =
    prospect.next_followup_date != null &&
    new Date(prospect.next_followup_date) < new Date(new Date().toDateString());

  return (
    <div
      draggable
      onDragStart={(e) => {
        onDragStart(prospect.id);
        e.dataTransfer.effectAllowed = "move";
      }}
      style={{
        backgroundColor: "white",
        border: "1px solid rgba(14,13,11,0.08)",
        borderRadius: 8,
        padding: "10px 12px",
        marginBottom: 8,
        cursor: "grab",
        opacity: isDragging ? 0.4 : 1,
        transition: "opacity 0.15s",
      }}
    >
      <div style={{ display: "flex", alignItems: "flex-start", gap: 6, marginBottom: 6 }}>
        <GripVertical size={13} style={{ color: "var(--color-ink-3)", flexShrink: 0, marginTop: 2 }} />
        <div style={{ flex: 1, minWidth: 0 }}>
          <div style={{ fontSize: 13, fontWeight: 600, color: "var(--color-ink)" }}>
            {prospect.name}
          </div>
          <div style={{ display: "flex", alignItems: "center", gap: 4, fontSize: 11, color: "var(--color-ink-3)", marginTop: 2 }}>
            <Phone size={10} /> {prospect.phone}
          </div>
        </div>
      </div>

      {prospect.project_name && (
        <div style={{ display: "flex", alignItems: "center", gap: 4, fontSize: 11, color: "var(--color-ink-3)", marginBottom: 4 }}>
          <Building2 size={10} /> {prospect.project_name}
        </div>
      )}

      <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between", marginTop: 6, paddingTop: 6, borderTop: "1px solid rgba(14,13,11,0.06)" }}>
        <span style={{ fontSize: 10, color: "var(--color-ink-3)" }}>
          Diperbarui {daysAgo(prospect.updated_at)} hari lalu
        </span>
        {prospect.next_followup_date && (
          <span style={{
            display: "flex", alignItems: "center", gap: 3, fontSize: 10, fontWeight: 600,
            color: followUpOverdue ? "var(--color-danger)" : "var(--color-ink-3)",
          }}>
            <Clock size={10} />
            {new Date(prospect.next_followup_date).toLocaleDateString("id-ID", { day: "numeric", month: "short" })}
          </span>
        )}
      </div>
    </div>
  );
}

export default function PipelinePage() {
  const [prospects, setProspects] = useState<Prospect[]>([]);
  const [loading,   setLoading]   = useState(true);
  const [error,     setError]     = useState<string | null>(null);
  const [draggingId, setDraggingId] = useState<string | null>(null);
  const [dragOverColumn, setDragOverColumn] = useState<Prospect["status"] | null>(null);

  const load = () => {
    setLoading(true);
    prospectsApi.list()
      .then(setProspects)
      .catch(() => setError("Gagal memuat pipeline"))
      .finally(() => setLoading(false));
  };

  useEffect(() => { load(); }, []);

  const handleDrop = async (targetStatus: Prospect["status"]) => {
    setDragOverColumn(null);
    const id = draggingId;
    setDraggingId(null);
    if (!id) return;

    const prospect = prospects.find((p) => p.id === id);
    if (!prospect || prospect.status === targetStatus) return;

    // Won never accepts a drop — see the module docstring for why.
    // This check is redundant with the locked column's onDrop being
    // absent entirely, kept here too as a second guard in case a
    // future edit ever loosens that.
    if (targetStatus === "won") return;

    // Same confirm() the Prospect list page's "Tandai Hilang" action
    // already uses — losing a lead is a real business action, drag
    // convenience shouldn't make it accidental.
    if (targetStatus === "lost" && !confirm(`Tandai ${prospect.name} sebagai hilang?`)) {
      return;
    }

    const previous = prospects;
    // Optimistic update — the board should feel instant; reverted
    // below if the PUT actually fails.
    setProspects((prev) => prev.map((p) => p.id === id ? { ...p, status: targetStatus } : p));

    try {
      await prospectsApi.update(id, { status: targetStatus });
    } catch {
      setProspects(previous);
      setError(`Gagal memindahkan ${prospect.name} — coba lagi.`);
    }
  };

  if (loading) {
    return (
      <div style={{ display: "flex", alignItems: "center", justifyContent: "center", height: 300, gap: 10, color: "var(--color-ink-3)" }}>
        <Loader2 size={18} style={{ animation: "spin 1s linear infinite" }} />
        <span style={{ fontSize: 13 }}>Memuat pipeline…</span>
      </div>
    );
  }

  return (
    <div>
      <div className="page-header" style={{ display: "flex", alignItems: "flex-start", justifyContent: "space-between" }}>
        <div>
          <h1 className="page-title">Pipeline</h1>
          <p className="page-subtitle">{prospects.length} prospect di seluruh tahap</p>
        </div>
        <button
          className="btn-ghost"
          onClick={load}
          style={{ display: "flex", alignItems: "center", gap: 6 }}
        >
          <RefreshCw size={14} /> Muat Ulang
        </button>
      </div>

      {error && (
        <div style={{ display: "flex", alignItems: "center", gap: 8, padding: "10px 14px", backgroundColor: "var(--color-danger-light)", borderRadius: 6, fontSize: 12, color: "var(--color-danger)", marginBottom: 16 }}>
          <AlertTriangle size={14} /> {error}
        </div>
      )}

      <div style={{ display: "flex", gap: 12, overflowX: "auto", paddingBottom: 12 }}>
        {COLUMNS.map((col) => {
          const items = prospects.filter((p) => p.status === col.key);
          const isDragOver = dragOverColumn === col.key;

          return (
            <div
              key={col.key}
              onDragOver={(e) => {
                if (col.locked) return; // no preventDefault = drop stays disallowed
                e.preventDefault();
                if (dragOverColumn !== col.key) setDragOverColumn(col.key);
              }}
              onDragLeave={() => { if (dragOverColumn === col.key) setDragOverColumn(null); }}
              onDrop={(e) => {
                if (col.locked) return;
                e.preventDefault();
                handleDrop(col.key);
              }}
              style={{
                minWidth: 260, maxWidth: 260, flexShrink: 0,
                backgroundColor: isDragOver ? "var(--color-accent-light)" : "var(--color-paper-2)",
                borderRadius: 10, padding: 10,
                border: isDragOver ? "2px dashed var(--color-accent)" : "2px dashed transparent",
                transition: "all 0.1s",
              }}
            >
              <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between", marginBottom: 10, padding: "0 2px" }}>
                <div style={{ display: "flex", alignItems: "center", gap: 6 }}>
                  <span style={{ width: 8, height: 8, borderRadius: "50%", backgroundColor: COLUMN_ACCENT[col.key] }} />
                  <span style={{ fontSize: 12, fontWeight: 700, color: "var(--color-ink)" }}>{col.label}</span>
                  {col.locked && (
                    <span title="Gunakan tombol Konversi di halaman Prospect untuk memenangkan lead — kolom ini tidak menerima drag-and-drop, karena Won hanya berarti jujur ketika ada Booking nyata di baliknya.">
                      <Lock size={11} style={{ color: "var(--color-ink-3)" }} />
                    </span>
                  )}
                </div>
                <span style={{ fontSize: 10, fontWeight: 600, color: "var(--color-ink-3)", backgroundColor: "white", padding: "2px 7px", borderRadius: 999 }}>
                  {items.length}
                </span>
              </div>

              {items.length === 0 ? (
                <div style={{ fontSize: 11, color: "var(--color-ink-3)", textAlign: "center", padding: "16px 8px" }}>
                  Kosong
                </div>
              ) : (
                items.map((p) => (
                  <ProspectCard
                    key={p.id}
                    prospect={p}
                    isDragging={draggingId === p.id}
                    onDragStart={setDraggingId}
                  />
                ))
              )}
            </div>
          );
        })}
      </div>
    </div>
  );
}
