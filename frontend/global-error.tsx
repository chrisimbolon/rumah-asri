"use client";
// Sprint 21.5: Sentry error monitoring — catches React rendering errors
// that escape every other error boundary. Next.js requires this file to
// render its own <html>/<body> since it replaces the root layout
// entirely when it fires. Styled to match the rest of the app (same
// CSS variable tokens, same tone as other empty/error states already
// built this sprint — no apology, states what happened plainly).

import * as Sentry from "@sentry/nextjs";
import { AlertTriangle } from "lucide-react";
import { useEffect } from "react";

export default function GlobalError({
  error,
  reset,
}: {
  error: Error & { digest?: string };
  reset: () => void;
}) {
  useEffect(() => {
    Sentry.captureException(error);
  }, [error]);

  return (
    <html lang="id">
      <body>
        <div style={{
          minHeight: "100vh", display: "flex", flexDirection: "column",
          alignItems: "center", justifyContent: "center", gap: 16,
          backgroundColor: "var(--color-paper)", padding: 24, textAlign: "center",
        }}>
          <AlertTriangle size={40} style={{ color: "var(--color-danger)" }} />
          <div>
            <h1 style={{ fontSize: 20, fontWeight: 700, color: "var(--color-ink)", margin: 0 }}>
              Ada yang tidak beres
            </h1>
            <p style={{ fontSize: 14, color: "var(--color-ink-3)", marginTop: 8, maxWidth: 420 }}>
              Masalah ini sudah tercatat secara otomatis. Coba muat ulang
              halaman — jika masih terjadi, hubungi tim DevelopIndo.
            </p>
          </div>
          <button
            onClick={() => reset()}
            style={{
              padding: "10px 20px", borderRadius: 8, border: "none",
              backgroundColor: "var(--color-accent)", color: "white",
              fontSize: 13, fontWeight: 600, cursor: "pointer",
            }}
          >
            Muat Ulang
          </button>
        </div>
      </body>
    </html>
  );
}
