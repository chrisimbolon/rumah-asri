// Sprint 21.5: Sentry error monitoring — Node.js server runtime.
// Same guard as the client config: empty DSN = silent no-op.
import * as Sentry from "@sentry/nextjs";

Sentry.init({
  dsn: process.env.NEXT_PUBLIC_SENTRY_DSN,
  tracesSampleRate: 0.1,
  environment: process.env.NODE_ENV,
});
