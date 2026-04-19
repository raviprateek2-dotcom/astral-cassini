import { NextResponse, type NextRequest } from "next/server";

const PUBLIC_PATHS = new Set(["/", "/login"]);

function isPublicPath(pathname: string): boolean {
  if (PUBLIC_PATHS.has(pathname)) return true;
  if (pathname.startsWith("/_next")) return true;
  if (pathname.startsWith("/favicon")) return true;
  if (pathname.startsWith("/assets")) return true;
  if (pathname.startsWith("/api")) return true;
  return false;
}

export function middleware(request: NextRequest) {
  const { pathname } = request.nextUrl;
  if (isPublicPath(pathname)) {
    return NextResponse.next();
  }

  const hasSession = Boolean(request.cookies.get("access_token")?.value);
  if (!hasSession) {
    const dest = new URL("/", request.url);
    if (pathname && pathname !== "/") {
      dest.searchParams.set("next", pathname);
    }
    return NextResponse.redirect(dest);
  }
  return NextResponse.next();
}

/**
 * Run only on app shell routes (no regex backtracking on Edge; avoids static files and `_next`).
 * `:path*` matches the segment and subpaths (including zero extra segments for the base path).
 */
export const config = {
  matcher: [
    "/dashboard/:path*",
    "/analytics/:path*",
    "/kanban/:path*",
    "/jobs/:path*",
    "/insights/:path*",
    "/candidates/:path*",
    "/approvals/:path*",
    "/interviews/:path*",
    "/decisions/:path*",
    "/audit/:path*",
  ],
};
