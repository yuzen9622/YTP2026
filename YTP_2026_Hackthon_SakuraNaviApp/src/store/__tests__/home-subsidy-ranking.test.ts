const mockRecommendSubsidies = jest.fn();
const mockListYouthSubsidyDocuments = jest.fn();

jest.mock("@/features/home/api/home-api", () => ({
  __esModule: true,
  recommendSubsidies: (...args: unknown[]) => mockRecommendSubsidies(...args),
  listYouthSubsidyDocuments: (...args: unknown[]) =>
    mockListYouthSubsidyDocuments(...args),
  listHomeNews: jest.fn(),
  listHomeAnnouncements: jest.fn(),
}));

import { fetchHomeSubsidyRanking } from "@/features/home/hooks/subsidy-ranking";

describe("fetchHomeSubsidyRanking", () => {
  beforeEach(() => {
    jest.clearAllMocks();
  });

  it("uses subsidy recommendation endpoint when primary resume exists", async () => {
    mockRecommendSubsidies.mockResolvedValueOnce({
      items: [
        {
          title: "青年就業啟航補助",
          amount: "NT$60,000",
          department: "勞工局",
          document_id: "doc-resume-1",
          source_link: "https://example.com/subsidy-1",
        },
      ],
    });

    const result = await fetchHomeSubsidyRanking({
      primaryResumeId: "resume-1",
      limit: 5,
    });

    expect(mockRecommendSubsidies).toHaveBeenCalledWith({
      resume_id: "resume-1",
      query: undefined,
      limit: 5,
    });
    expect(mockListYouthSubsidyDocuments).not.toHaveBeenCalled();
    expect(result.source).toBe("resume");
    expect(result.items[0]).toMatchObject({
      title: "青年就業啟航補助",
      amountText: "NT$60,000",
      departmentText: "勞工局",
      documentId: "doc-resume-1",
      sourceLink: "https://example.com/subsidy-1",
    });
  });

  it("falls back to youth_subsidy documents when no primary resume", async () => {
    mockListYouthSubsidyDocuments.mockResolvedValueOnce({
      items: [
        {
          id: "doc-1",
          filename: "doc-1.md",
          title: "一般熱門補助",
          category: "youth_subsidy",
          source_url: "https://example.com/fallback-doc-1",
          doc_metadata: null,
          content_hash: "hash",
          chunk_count: 0,
          created_at: "2026-01-01T00:00:00Z",
          updated_at: "2026-01-01T00:00:00Z",
        },
      ],
      total: 1,
      limit: 5,
      offset: 0,
    });

    const result = await fetchHomeSubsidyRanking({
      primaryResumeId: null,
      limit: 5,
    });

    expect(mockRecommendSubsidies).not.toHaveBeenCalled();
    expect(mockListYouthSubsidyDocuments).toHaveBeenCalledWith(5);
    expect(result.source).toBe("fallback");
    expect(result.items[0]).toMatchObject({
      id: "doc-1",
      title: "一般熱門補助",
      amountText: "--",
      departmentText: "--",
      documentId: "doc-1",
      sourceLink: "https://example.com/fallback-doc-1",
    });
  });
});
