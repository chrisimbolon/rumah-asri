/**
 * DevelopIndo — Next.js 16 Proxy (Route Protection)
 * Renamed from middleware.ts → proxy.ts in Next.js 16
 * Protected routes:
 *   /dashboard/super-admin  → requires super_admin role
 *   /dashboard/*            → requires login (any role)
 *   /buyer                  → requires login (buyer role expected)
 *
 * Public routes:
 *   /             → landing page (always accessible)
 *   /login        → login page
 *   /register     → register page
 */

import { NextRequest, NextResponse } from "next/server";

// ── Route config ──────────────────────────────────────────────
const PROTECTED_ROUTES  = ["/dashboard", "/buyer"];
const AUTH_ROUTES       = ["/login", "/register"];
// Routes that require a specific role — checked AFTER the login gate
const SUPER_ADMIN_ROUTES = ["/dashboard/super-admin"];

export function proxy(request: NextRequest) {
  const { pathname } = request.nextUrl;

  const token    = request.cookies.get("access_token")?.value;
  const userRole = request.cookies.get("user_role")?.value;

  const isProtectedRoute  = PROTECTED_ROUTES.some((r) => pathname.startsWith(r));
  const isAuthRoute       = AUTH_ROUTES.some((r) => pathname.startsWith(r));
  const isSuperAdminRoute = SUPER_ADMIN_ROUTES.some((r) => pathname.startsWith(r));

  // ── 1. No token → redirect to login
  if (isProtectedRoute && !token) {
    const loginUrl = new URL("/login", request.url);
    loginUrl.searchParams.set("next", pathname);
    return NextResponse.redirect(loginUrl);
  }

  // ── 2. Logged in + hitting /dashboard/super-admin without super_admin role → 403 to dashboard
  if (isSuperAdminRoute && token && userRole !== "super_admin") {
    return NextResponse.redirect(new URL("/dashboard", request.url));
  }

  // ── 3. Already logged in + hitting login/register → redirect to correct home
  if (isAuthRoute && token) {
    // Use role cookie to send to the right landing page
    switch (userRole) {
      case "super_admin": return NextResponse.redirect(new URL("/dashboard/super-admin", request.url));
      case "buyer":       return NextResponse.redirect(new URL("/buyer", request.url));
      default:            return NextResponse.redirect(new URL("/dashboard", request.url));
    }
  }

  return NextResponse.next();
}

// ── Matcher — which routes this proxy applies to 
export const config = {
  matcher: [
    "/dashboard/:path*",
    "/buyer/:path*",
    "/login",
    "/register",
  ],
};
