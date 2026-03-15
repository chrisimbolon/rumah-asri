/**
 * RumahAsri — Next.js 16 Proxy (Route Protection)
 * Renamed from middleware.ts → proxy.ts in Next.js 16
 *
 * Protected routes:
 *   /dashboard/*  → requires login
 *   /buyer        → requires login
 *
 * Public routes:
 *   /             → landing page (always accessible)
 *   /login        → login page
 *   /register     → register page
 */

import { NextRequest, NextResponse } from "next/server";

// ── Route config ──────────────────────────────────────────────
const PROTECTED_ROUTES = ["/dashboard", "/buyer"];
const AUTH_ROUTES      = ["/login", "/register"];

export function proxy(request: NextRequest) {
  const { pathname } = request.nextUrl;

  // Check for access token in cookies
  // (localStorage not available in server-side proxy)
  const token = request.cookies.get("access_token")?.value;

  const isProtectedRoute = PROTECTED_ROUTES.some((route) =>
    pathname.startsWith(route)
  );
  const isAuthRoute = AUTH_ROUTES.some((route) =>
    pathname.startsWith(route)
  );

  // ── Redirect to login if accessing protected route without token
  if (isProtectedRoute && !token) {
    const loginUrl = new URL("/login", request.url);
    loginUrl.searchParams.set("next", pathname);
    return NextResponse.redirect(loginUrl);
  }

  // ── Redirect to dashboard if already logged in and hitting auth pages
  if (isAuthRoute && token) {
    return NextResponse.redirect(new URL("/dashboard", request.url));
  }

  return NextResponse.next();
}

// ── Matcher — which routes this proxy applies to ──────────────
export const config = {
  matcher: [
    "/dashboard/:path*",
    "/buyer/:path*",
    "/login",
    "/register",
  ],
};