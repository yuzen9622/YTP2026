const mockGet = jest.fn();
const mockPost = jest.fn();

jest.mock("@/lib/api", () => ({
  __esModule: true,
  apiClient: {
    get: (...args: unknown[]) => mockGet(...args),
    post: (...args: unknown[]) => mockPost(...args),
  },
}));

import {
  listHomeAnnouncements,
  listHomeNews,
  listYouthSubsidyDocuments,
  recommendSubsidies,
} from "@/features/home/api/home-api";

describe("home api", () => {
  beforeEach(() => {
    jest.clearAllMocks();
  });

  it("calls POST /rag/recommendations/subsidies with normalized payload", async () => {
    mockPost.mockResolvedValueOnce({ items: [] });

    await recommendSubsidies({
      resume_id: " resume-1 ",
      query: " 青年補助 ",
      limit: 7,
    });

    expect(mockPost).toHaveBeenCalledWith("/rag/recommendations/subsidies", {
      resume_id: "resume-1",
      query: "青年補助",
      limit: 7,
    });
  });

  it("calls GET /rag/news with default limit", async () => {
    mockGet.mockResolvedValueOnce({ items: [] });

    await listHomeNews();

    expect(mockGet).toHaveBeenCalledWith("/rag/news", {
      params: {
        query: undefined,
        limit: 5,
      },
    });
  });

  it("calls GET /rag/announcements with normalized query", async () => {
    mockGet.mockResolvedValueOnce({ items: [] });

    await listHomeAnnouncements({
      query: " 最新 ",
      limit: 3,
    });

    expect(mockGet).toHaveBeenCalledWith("/rag/announcements", {
      params: {
        query: "最新",
        limit: 3,
      },
    });
  });

  it("calls GET /rag/documents for youth_subsidy fallback", async () => {
    mockGet.mockResolvedValueOnce({ items: [], total: 0, limit: 5, offset: 0 });

    await listYouthSubsidyDocuments();

    expect(mockGet).toHaveBeenCalledWith("/rag/documents", {
      params: {
        category: "youth_subsidy",
        limit: 5,
        offset: 0,
      },
    });
  });
});
