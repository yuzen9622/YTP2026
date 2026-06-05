export interface KnowledgeArticleItem {
  id: string;
  title: string;
  url: string;
  category: string | null;
  summary: string | null;
  published_at: string | null;
  official_updated_at: string | null;
  crawl_status: string;
}

export interface KnowledgeCategory {
  name: string;
  article_count: number;
  articles: KnowledgeArticleItem[];
}

export interface KnowledgeCategoriesResponse {
  categories: KnowledgeCategory[];
}

export interface KnowledgeChunk {
  id: string;
  article_id: string;
  title: string;
  heading: string | null;
  heading_path: string | null;
  content: string;
  source_url: string;
  document_kind: string;
  official_updated_at: string | null;
  category: string | null;
}

export interface KnowledgeSearchResult {
  chunk_id: string;
  document_id: string;
  filename: string;
  title: string;
  category: string;
  heading: string | null;
  snippet: string;
  source_url: string | null;
  score: number;
}

export interface KnowledgeSearchResponse {
  hits: KnowledgeSearchResult[];
}

export interface SearchKnowledgeParams {
  q: string;
  category?: string | null;
  top_k?: number;
}
