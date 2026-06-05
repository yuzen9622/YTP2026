import { Platform } from "react-native";
import Head from "expo-router/head";
import { buildCanonicalUrl } from "./origin";
import { PUBLIC_ROBOTS } from "./indexability-policy";
import type { SeoMetaConfig } from "./types";

const SITE_NAME = "Sakura Navi";
const DEFAULT_LOCALE = "zh_TW";

export function SeoHead({
  title,
  description,
  path,
  robots = PUBLIC_ROBOTS,
  type = "website",
  imageUrl,
}: SeoMetaConfig) {
  if (Platform.OS !== "web") {
    return null;
  }

  const canonicalUrl = buildCanonicalUrl(path);
  const fullTitle = `${title} | ${SITE_NAME}`;

  return (
    <Head>
      <title>{fullTitle}</title>
      <meta name="description" content={description} />
      <meta name="robots" content={robots} />
      <link rel="canonical" href={canonicalUrl} />

      <meta property="og:site_name" content={SITE_NAME} />
      <meta property="og:locale" content={DEFAULT_LOCALE} />
      <meta property="og:type" content={type} />
      <meta property="og:title" content={fullTitle} />
      <meta property="og:description" content={description} />
      <meta property="og:url" content={canonicalUrl} />
      {imageUrl ? <meta property="og:image" content={imageUrl} /> : null}

      <meta name="twitter:card" content="summary_large_image" />
      <meta name="twitter:title" content={fullTitle} />
      <meta name="twitter:description" content={description} />
      {imageUrl ? <meta name="twitter:image" content={imageUrl} /> : null}
    </Head>
  );
}
