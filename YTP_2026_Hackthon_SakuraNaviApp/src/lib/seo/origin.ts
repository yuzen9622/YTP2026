const FALLBACK_WEB_ORIGIN = "http://localhost:8081";

export function getWebOrigin(): string | null {
  const value = process.env.EXPO_PUBLIC_WEB_ORIGIN?.trim();
  return value && value.length > 0 ? value.replace(/\/+$/, "") : null;
}

export function getRequiredWebOrigin(): string {
  const origin = getWebOrigin();

  if (origin) {
    return origin;
  }

  if (process.env.CI === "true") {
    throw new Error("Missing EXPO_PUBLIC_WEB_ORIGIN for SEO output in CI.");
  }

  return FALLBACK_WEB_ORIGIN;
}

export function buildCanonicalUrl(path: string): string {
  const normalizedPath = path.startsWith("/") ? path : `/${path}`;
  return `${getRequiredWebOrigin()}${normalizedPath}`;
}
