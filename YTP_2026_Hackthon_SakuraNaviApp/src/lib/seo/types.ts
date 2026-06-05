export interface SeoMetaConfig {
  title: string;
  description: string;
  path: string;
  robots?: string;
  type?: "website" | "article";
  imageUrl?: string;
}

export interface IndexabilityRule {
  pattern: string;
  robots: string;
  indexable: boolean;
}

export type IndexabilityPolicy = Record<string, IndexabilityRule>;
