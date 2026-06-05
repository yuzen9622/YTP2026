import { getRequiredWebOrigin } from "@/lib/seo";

function buildRobotsTxt(origin: string): string {
  return [
    "User-agent: *",
    "Allow: /",
    "Disallow: /chat",
    "Disallow: /profile",
    "Disallow: /search",
    "Disallow: /login-screen",
    "Disallow: /register-screen",
    "Disallow: /forgot-password-screen",
    "",
    `Sitemap: ${origin}/sitemap.xml`,
  ].join("\n");
}

export async function GET() {
  const origin = getRequiredWebOrigin();
  const content = buildRobotsTxt(origin);

  return new Response(content, {
    headers: {
      "Content-Type": "text/plain; charset=utf-8",
      "Cache-Control": "public, max-age=3600, s-maxage=3600",
    },
  });
}
