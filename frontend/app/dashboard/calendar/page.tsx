"use client";
// =============================================================================
// === frontend/app/dashboard/calendar/page.tsx ===
// Sprint 19: standalone Calendar page — cross-project view of every
// requirement with a due date, grouped by urgency.
//
// Design note: this renders as a grouped, sorted list rather than a
// traditional month-grid calendar. The rest of the app (Activity
// Timeline, Next Actions, Portfolio Intelligence) all use list/card
// layouts, and there's zero prior art here for a date-grid component
// — so this ships the real, already-tested data in a consistent,
// low-risk shape first. A visual month-grid could be a good follow-up
// if you want one later.
// =============================================================================

import { CalendarEvent, projectsApi } from "@/lib/api/projects";
import {
  AlertTriangle,
  Calendar as CalendarIcon,
  CheckCircle2,
  Clock,
  Loader2,
  User,
} from "lucide-react";
import Link from "next/link";
import { useEffect, useState } from "react";

const STATUS_LABEL: Record<string, string> = {
  pending:             "Belum Dimulai",
  in_progress:         "Sedang Diproses",
  menunggu_verifikasi: "Menunggu Verifikasi",
  completed:           "Selesai",
  not_applicable:      "Tidak Berlaku",
};

function EventRow({ event }: { event: CalendarEvent }) {
  const isDone = event.status === "completed";

  const badgeColor =
    isDone                     ? "var(--color-success)" :
    event.is_overdue           ? "var(--color-danger)"  :
    event.days_until_due <= 3  ? "var(--color-warning)" :
                                  "var(--color-ink-3)";
  const badgeBg =
    isDone                     ? "var(--color-success-light)" :
    event.is_overdue           ? "var(--color-danger-light)"  :
    event.days_until_due <= 3  ? "var(--color-warning-light)" :
                                  "var(--color-paper-2)";

  return (
    <Link
      href={`/dashboard/projects/${event.project_id}`}
      style={{
        display: "flex", alignItems: "center", gap: 12,
        padding: "12px 14px", borderRadius: 8,
        backgroundColor: "var(--color-paper-2)",
        textDecoration: "none", marginBottom: 8,
        opacity: isDone ? 0.6 : 1,
      }}
    >
      <div style={{
        width: 34, height: 34, borderRadius: "50%",
        backgroundColor: badgeBg, display: "flex",
        alignItems: "center", justifyContent: "center", flexShrink: 0,
      }}>
        {isDone ? (
          <CheckCircle2 size={16} style={{ color: badgeColor }} />
        ) : event.is_overdue ? (
          <AlertTriangle size={16} style={{ color: badgeColor }} />
        ) : (
          <Clock size={16} style={{ color: badgeColor }} />
        )}
      </div>

      <div style={{ flex: 1, minWidth: 0 }}>
        <div style={{
          fontSize: 13, fontWeight: 600, color: "var(--color-ink)",
          textDecoration: isDone ? "line-through" : "none",
        }}>
          {event.requirement_name}
        </div>
        <div style={{ fontSize: 11, color: "var(--color-ink-3)", marginTop: 2 }}>
          {event.project_name} · {STATUS_LABEL[event.status] ?? event.status}
        </div>
      </div>

      {event.assigned_to_name && (
        <div style={{
          display: "flex", alignItems: "center", gap: 4,
          fontSize: 11, color: "var(--color-ink-3)", flexShrink: 0,
        }}>
          <User size={12} /> {event.assigned_to_name}
        </div>
      )}

      <div style={{ textAlign: "right", flexShrink: 0, minWidth: 100 }}>
        <div style={{ fontSize: 12, fontWeight: 700, color: badgeColor }}>
          {isDone
            ? "Selesai"
            : event.is_overdue
              ? `${Math.abs(event.days_until_due)} hari terlambat`
              : event.days_until_due === 0
                ? "Hari ini"
                : `${event.days_until_due} hari lagi`}
        </div>
        <div style={{ fontSize: 10, color: "var(--color-ink-3)", marginTop: 1 }}>
          {new Date(event.due_date).toLocaleDateString("id-ID", { day: "numeric", month: "short" })}
        </div>
      </div>
    </Link>
  );
}

function EventGroup({
  title,
  events,
  emptyLabel,
}: {
  title:      string;
  events:     CalendarEvent[];
  emptyLabel: string;
}) {
  return (
    <div className="card" style={{ marginBottom: 16 }}>
      <div style={{ fontSize: 13, fontWeight: 600, color: "var(--color-ink)", marginBottom: 12 }}>
        {title}{" "}
        <span style={{ fontWeight: 400, color: "var(--color-ink-3)" }}>
          ({events.length})
        </span>
      </div>
      {events.length === 0 ? (
        <div style={{ fontSize: 12, color: "var(--color-ink-3)", padding: "8px 0" }}>
          {emptyLabel}
        </div>
      ) : (
        events.map((e) => <EventRow key={e.id} event={e} />)
      )}
    </div>
  );
}

export default function CalendarPage() {
  const [events,  setEvents]  = useState<CalendarEvent[]>([]);
  const [loading, setLoading] = useState(true);
  const [error,   setError]   = useState<string | null>(null);

  useEffect(() => {
    projectsApi.getCalendar()
      .then((data) => setEvents(data.results))
      .catch(() => setError("Gagal memuat kalender. Coba muat ulang halaman."))
      .finally(() => setLoading(false));
  }, []);

  if (loading) {
    return (
      <div style={{ display: "flex", alignItems: "center", justifyContent: "center", padding: 60 }}>
        <Loader2 size={18} style={{ animation: "spin 1s linear infinite", color: "var(--color-ink-3)" }} />
      </div>
    );
  }

  if (error) {
    return (
      <div style={{ padding: 24 }}>
        <div className="card" style={{ padding: 24, textAlign: "center" }}>
          <AlertTriangle size={24} style={{ color: "var(--color-danger)", marginBottom: 8 }} />
          <div style={{ fontSize: 13, color: "var(--color-ink)" }}>{error}</div>
        </div>
      </div>
    );
  }

  const active   = events.filter((e) => e.status !== "completed");
  const done     = events.filter((e) => e.status === "completed");
  const overdue  = active.filter((e) => e.is_overdue);
  const thisWeek = active.filter((e) => !e.is_overdue && e.days_until_due <= 7);
  const later    = active.filter((e) => !e.is_overdue && e.days_until_due > 7);

  return (
    <div style={{ padding: 24 }}>
      <div style={{ marginBottom: 20 }}>
        <div style={{ display: "flex", alignItems: "center", gap: 8, marginBottom: 4 }}>
          <CalendarIcon size={20} style={{ color: "var(--color-accent)" }} />
          <h1 style={{ fontSize: 20, fontWeight: 700, color: "var(--color-ink)", margin: 0 }}>
            Kalender
          </h1>
        </div>
        <div style={{ fontSize: 13, color: "var(--color-ink-3)" }}>
          Semua tenggat waktu di seluruh proyek — {events.length} total
        </div>
      </div>

      {events.length === 0 ? (
        <div className="card" style={{ padding: 40, textAlign: "center" }}>
          <CalendarIcon size={28} style={{ color: "var(--color-ink-3)", marginBottom: 10 }} />
          <div style={{ fontSize: 13, color: "var(--color-ink-3)" }}>
            Belum ada tenggat waktu yang ditetapkan di proyek manapun.
          </div>
        </div>
      ) : (
        <>
          <EventGroup
            title="Terlambat"
            events={overdue}
            emptyLabel="Tidak ada yang terlambat — kerja bagus! 🎉"
          />
          <EventGroup
            title="Minggu Ini"
            events={thisWeek}
            emptyLabel="Tidak ada tenggat dalam 7 hari ke depan."
          />
          <EventGroup
            title="Akan Datang"
            events={later}
            emptyLabel="Tidak ada tenggat lebih lanjut yang dijadwalkan."
          />
          {done.length > 0 && (
            <EventGroup title="Selesai" events={done} emptyLabel="" />
          )}
        </>
      )}
    </div>
  );
}
