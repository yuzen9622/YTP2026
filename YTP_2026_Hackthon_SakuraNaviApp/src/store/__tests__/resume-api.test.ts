const mockGet = jest.fn();
const mockPost = jest.fn();
const mockPut = jest.fn();
const mockDelete = jest.fn();
const mockPatch = jest.fn();

jest.mock("@/lib/api", () => ({
  __esModule: true,
  apiClient: {
    get: (...args: unknown[]) => mockGet(...args),
    post: (...args: unknown[]) => mockPost(...args),
    put: (...args: unknown[]) => mockPut(...args),
    delete: (...args: unknown[]) => mockDelete(...args),
    patch: (...args: unknown[]) => mockPatch(...args),
  },
}));

import {
  createResume,
  deleteResume,
  getMyResumes,
  setPrimaryResume,
  unsetPrimaryResume,
  updateResume,
} from "@/features/user-profile/api/resume-api";

describe("resume api", () => {
  beforeEach(() => {
    jest.clearAllMocks();
  });

  it("calls GET /resumes", async () => {
    mockGet.mockResolvedValueOnce([]);

    await getMyResumes();

    expect(mockGet).toHaveBeenCalledWith("/resumes");
  });

  it("calls POST /resumes", async () => {
    const payload = { title: "我的履歷" };
    mockPost.mockResolvedValueOnce({ id: "1", title: "我的履歷" });

    await createResume(payload);

    expect(mockPost).toHaveBeenCalledWith("/resumes", payload);
  });

  it("calls PUT /resumes/{id}", async () => {
    const payload = { title: "更新履歷" };
    mockPut.mockResolvedValueOnce({ id: "1", title: "更新履歷" });

    await updateResume("resume-1", payload);

    expect(mockPut).toHaveBeenCalledWith("/resumes/resume-1", payload);
  });

  it("calls DELETE /resumes/{id}", async () => {
    mockDelete.mockResolvedValueOnce(undefined);

    await deleteResume("resume-2");

    expect(mockDelete).toHaveBeenCalledWith("/resumes/resume-2");
  });

  it("calls PATCH /resumes/{id}/primary", async () => {
    mockPatch.mockResolvedValueOnce({ id: "resume-3", is_primary: true });

    await setPrimaryResume("resume-3");

    expect(mockPatch).toHaveBeenCalledWith("/resumes/resume-3/primary");
  });

  it("calls DELETE /resumes/{id}/primary", async () => {
    mockDelete.mockResolvedValueOnce(undefined);

    await unsetPrimaryResume("resume-3");

    expect(mockDelete).toHaveBeenCalledWith("/resumes/resume-3/primary");
  });
});
