// Sprint 21.5: Sentry error monitoring.
// Next.js's native instrumentation hook — runs once when the server
// starts, loads the right Sentry config depending on which runtime
// this particular request is executing in (Node.js vs Edge).
import * as Sentry from "@sentry/nextjs";

export async function register() {
  if (process.env.NEXT_RUNTIME === "nodejs") {
    await import("./sentry.server.config");
  }
  if (process.env.NEXT_RUNTIME === "edge") {
    await import("./sentry.edge.config");
  }
}

export const onRequestError = Sentry.captureRequestError;
