import { withSentryConfig } from "@sentry/nextjs";
import type { NextConfig } from "next";

const nextConfig: NextConfig = {
  output: "standalone",
};

// Sprint 21.5: Sentry error monitoring.
// authToken/org/project are only needed for source-map upload (readable
// stack traces in Sentry) — if these env vars aren't set yet, the build
// just skips that step silently (silent: true suppresses the notice), nothing breaks either way.
export default withSentryConfig(nextConfig, {
  org: process.env.SENTRY_ORG,
  project: process.env.SENTRY_PROJECT,
  authToken: process.env.SENTRY_AUTH_TOKEN,
  silent: true,
  widenClientFileUpload: true,
});
