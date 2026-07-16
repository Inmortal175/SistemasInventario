import { NextResponse } from "next/server";
import type { NextRequest } from "next/server";

const TOKEN_COOKIE = "pastry_token";
const PUBLIC_PATHS = ["/login"];

export function middleware(request: NextRequest) {
  const { pathname } = request.nextUrl;
  const hasToken = Boolean(request.cookies.get(TOKEN_COOKIE)?.value);
  const isPublic = PUBLIC_PATHS.some((p) => pathname.startsWith(p));

  if (!hasToken && !isPublic) {
    const url = request.nextUrl.clone();
    url.pathname = "/login";
    return NextResponse.redirect(url);
  }

  if (hasToken && isPublic) {
    const url = request.nextUrl.clone();
    url.pathname = "/dashboard";
    return NextResponse.redirect(url);
  }

  return NextResponse.next();
}

export const config = {
  // Excluye assets estáticos y recursos internos de Next.
  matcher: ["/((?!_next/static|_next/image|favicon.ico|.*\\.svg).*)"],
};
