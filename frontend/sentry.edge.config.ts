// Sprint 21.5: Sentry error monitoring — Edge runtime (middleware, etc).
// Same guard as the other configs: empty DSN = silent no-op.
import * as Sentry from "@sentry/nextjs";

Sentry.init({
  dsn: process.env.NEXT_PUBLIC_SENTRY_DSN,
  tracesSampleRate: 0.1,
  environment: process.env.NODE_ENV,
});
