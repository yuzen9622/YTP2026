import type { PolicyDocumentResponse } from "../types/policy";

export const POLICY_MARKDOWN_EMPTY_CONTENT = "目前沒有可顯示的內容。";

export function buildPolicyMarkdownContent(
  document: PolicyDocumentResponse,
): string {
  const rawContent = document.raw_content?.trim();
  if (rawContent) {
    return rawContent;
  }

  const chunks = (document.chunks ?? []).slice().sort((a, b) => {
    return a.chunk_index - b.chunk_index;
  });

  if (chunks.length === 0) {
    return POLICY_MARKDOWN_EMPTY_CONTENT;
  }

  const content = chunks
    .map((chunk) => {
      const heading = chunk.heading?.trim();
      const chunkContent = chunk.content.trim();

      if (!heading) {
        return chunkContent;
      }

      if (chunkContent.length === 0) {
        return `## ${heading}`;
      }

      return `## ${heading}\n\n${chunkContent}`;
    })
    .filter((item) => item.length > 0)
    .join("\n\n")
    .trim();

  return content.length > 0 ? content : POLICY_MARKDOWN_EMPTY_CONTENT;
}
