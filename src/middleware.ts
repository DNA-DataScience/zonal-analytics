import { NextRequest, NextResponse } from "next/server";

const USERNAME = process.env.BASIC_AUTH_USER || "tester";
const PASSWORD = process.env.BASIC_AUTH_PASS || "";

export function middleware(req: NextRequest) {
  // Skip protection if no password set (so local dev won't lock you out accidentally)
  if (!PASSWORD) return NextResponse.next();

  const authHeader = req.headers.get("authorization");

  if (authHeader) {
    const [scheme, encoded] = authHeader.split(" ");
    if (scheme === "Basic" && encoded) {
      const decoded = atob(encoded);
      const [user, pass] = decoded.split(":");

      if (user === USERNAME && pass === PASSWORD) {
        return NextResponse.next();
      }
    }
  }

  return new NextResponse("Authentication required", {
    status: 401,
    headers: {
      "WWW-Authenticate": 'Basic realm="Protected Area"',
    },
  });
}

// Apply to app routes; avoid static files and Next internals
export const config = {
  matcher: [
    "/((?!_next/static|_next/image|favicon.ico|.*\\.(?:svg|png|jpg|jpeg|gif|webp)$).*)",
  ],
};
