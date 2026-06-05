import { buildCanonicalUrl, fetchSitemapPolicyDocuments } from "@/lib/seo";

interface SitemapEntry {
  loc: string;
  lastmod?: string;
  changefreq?: "daily" | "weekly" | "monthly";
  priority?: number;
}

function xmlEscape(value: string): string {
  return value
    .replaceAll("&", "&amp;")
    .replaceAll("<", "&lt;")
    .replaceAll(">", "&gt;")
    .replaceAll('"', "&quot;")
    .replaceAll("'", "&apos;");
}

function renderSitemap(entries: SitemapEntry[]): string {
  const lines = entries.map((entry) => {
    const nodes = [
      `<loc>${xmlEscape(entry.loc)}</loc>`,
      entry.lastmod ? `<lastmod>${xmlEscape(entry.lastmod)}</lastmod>` : null,
      entry.changefreq ? `<changefreq>${entry.changefreq}</changefreq>` : null,
      entry.priority !== undefined ? `<priority>${entry.priority.toFixed(1)}</priority>` : null,
    ]
      .filter(Boolean)
      .join("");

    return `<url>${nodes}</url>`;
  });

  return `<?xml version="1.0" encoding="UTF-8"?>\n<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">${lines.join("")}</urlset>`;
}

export async function GET() {
  const baseEntries: SitemapEntry[] = [
    {
      loc: buildCanonicalUrl("/"),
      changefreq: "daily",
      priority: 1.0,
    },
    {
      loc: buildCanonicalUrl("/policy"),
      changefreq: "daily",
      priority: 0.8,
    },
  ];

  const policyDocuments = await fetchSitemapPolicyDocuments();
  const policyEntries = policyDocuments.map((item): SitemapEntry => ({
    loc: buildCanonicalUrl(`/policy/${encodeURIComponent(item.id)}`),
    lastmod: item.updated_at ? new Date(item.updated_at).toISOString() : undefined,
    changefreq: "weekly",
    priority: 0.7,
  }));

  const content = renderSitemap([...baseEntries, ...policyEntries]);

  return new Response(content, {
    headers: {
      "Content-Type": "application/xml; charset=utf-8",
      "Cache-Control": "public, max-age=3600, s-maxage=3600",
    },
  });
}
