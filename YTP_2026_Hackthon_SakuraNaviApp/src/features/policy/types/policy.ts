export interface PolicyCategoryCountItem {
  category: string;
  count: number;
}

export interface PolicyCategoryListResponse {
  items: PolicyCategoryCountItem[];
}

export interface PolicyChunkSummary {
  id: string;
  chunk_index: number;
  heading: string | null;
  content: string;
  token_count: number;
}

export interface PolicyDocumentResponse {
  id: string;
  filename: string;
  title: string;
  category: string;
  source_url: string | null;
  doc_metadata: Record<string, unknown> | null;
  content_hash: string;
  chunk_count: number;
  created_at: string;
  updated_at: string;
  raw_content?: string | null;
  chunks?: PolicyChunkSummary[];
}

export interface PolicyDocumentListResponse {
  items: PolicyDocumentResponse[];
  total: number;
  limit: number;
  offset: number;
}

export interface ListPolicyDocumentsParams {
  category?: string | null;
  limit?: number;
  offset?: number;
}
