// Sprint 21.5: Sentry error monitoring — browser/client side.
// NEXT_PUBLIC_ prefix is required so this value is actually readable
// in the browser bundle. A Sentry DSN is a public identifier (where to send events), not a secret — safe to expose client-side.
// If NEXT_PUBLIC_SENTRY_DSN isn't set yet, Sentry's SDK silently
// no-ops rather than erroring — nothing breaks either way.
import * as Sentry from "@sentry/nextjs";

Sentry.init({
  dsn: process.env.NEXT_PUBLIC_SENTRY_DSN,
  tracesSampleRate: 0.1,
  environment: process.env.NODE_ENV,
});

// Required by the v10 SDK to instrument page-to-page navigations
// (silences the "ACTION REQUIRED" build warning) — tracks navigation
export const onRouterTransitionStart = Sentry.captureRouterTransitionStart;