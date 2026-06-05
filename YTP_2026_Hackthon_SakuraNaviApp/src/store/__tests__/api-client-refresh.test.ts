const mockToastError = jest.fn();
const mockGetAuthToken = jest.fn();
const mockGetRefreshToken = jest.fn();
const mockSetToken = jest.fn();
const mockClearSession = jest.fn();

jest.mock("sonner-native", () => ({
  __esModule: true,
  toast: {
    error: (...args: unknown[]) => mockToastError(...args),
  },
}));

jest.mock("@/lib/auth", () => ({
  __esModule: true,
  getAuthToken: (...args: unknown[]) => mockGetAuthToken(...args),
  getRefreshToken: (...args: unknown[]) => mockGetRefreshToken(...args),
  parseAuthTokens: (data: unknown) => {
    if (!data || typeof data !== "object") {
      return {
        accessToken: null,
        refreshToken: null,
      };
    }

    return {
      accessToken: Reflect.get(data, "access_token") ?? null,
      refreshToken: Reflect.get(data, "refresh_token") ?? null,
    };
  },
}));

jest.mock("@/store/user-store", () => ({
  __esModule: true,
  useUserStore: {
    getState: () => ({
      setToken: (...args: unknown[]) => mockSetToken(...args),
      clearSession: (...args: unknown[]) => mockClearSession(...args),
    }),
  },
}));

import { request } from "@/lib/api/client";

function createJsonResponse(status: number, body: unknown): Response {
  return {
    status,
    ok: status >= 200 && status < 300,
    headers: {
      get: (name: string) =>
        name.toLowerCase() === "content-type" ? "application/json" : null,
    },
    json: async () => body,
    text: async () => JSON.stringify(body),
  } as unknown as Response;
}

describe("api client refresh flow", () => {
  beforeEach(() => {
    jest.clearAllMocks();

    mockGetAuthToken.mockResolvedValue("expired-access-token");
    mockGetRefreshToken.mockResolvedValue("valid-refresh-token");
    mockSetToken.mockResolvedValue(undefined);

    (global as unknown as { fetch: jest.Mock }).fetch = jest.fn();
  });

  it("refreshes token on 401 and retries original request", async () => {
    const fetchMock = (global as unknown as { fetch: jest.Mock }).fetch;
    fetchMock
      .mockResolvedValueOnce(createJsonResponse(401, { detail: "expired" }))
      .mockResolvedValueOnce(
        createJsonResponse(200, {
          access_token: "new-access-token",
          refresh_token: "new-refresh-token",
          token_type: "bearer",
        }),
      )
      .mockResolvedValueOnce(createJsonResponse(200, { ok: true }));

    const result = await request<{ ok: boolean }>("/users/me", {
      withAuth: true,
    });

    expect(result).toEqual({ ok: true });
    expect(fetchMock).toHaveBeenCalledTimes(3);
    expect(mockSetToken).toHaveBeenCalledWith(
      "new-access-token",
      "new-refresh-token",
    );
    expect(mockClearSession).not.toHaveBeenCalled();

    const refreshCall = fetchMock.mock.calls[1];
    expect(String(refreshCall[0])).toContain("/auth/refresh");
    expect((refreshCall[1] as RequestInit).body).toBe(
      JSON.stringify({ refresh_token: "valid-refresh-token" }),
    );
  });

  it("logs out when refresh endpoint returns 401", async () => {
    const fetchMock = (global as unknown as { fetch: jest.Mock }).fetch;
    fetchMock
      .mockResolvedValueOnce(createJsonResponse(401, { detail: "expired" }))
      .mockResolvedValueOnce(
        createJsonResponse(401, { detail: "refresh expired" }),
      );

    await expect(
      request("/users/me", {
        withAuth: true,
      }),
    ).rejects.toMatchObject({
      name: "ApiError",
      status: 401,
    });

    expect(fetchMock).toHaveBeenCalledTimes(2);
    expect(mockClearSession).toHaveBeenCalledTimes(1);
  });

  it("does not log out when refresh fails with non-401", async () => {
    const fetchMock = (global as unknown as { fetch: jest.Mock }).fetch;
    fetchMock
      .mockResolvedValueOnce(createJsonResponse(401, { detail: "expired" }))
      .mockResolvedValueOnce(
        createJsonResponse(500, { detail: "service unavailable" }),
      );

    await expect(
      request("/users/me", {
        withAuth: true,
      }),
    ).rejects.toMatchObject({
      name: "ApiError",
      status: 500,
    });

    expect(fetchMock).toHaveBeenCalledTimes(2);
    expect(mockClearSession).not.toHaveBeenCalled();
  });

  it("logs out when retried request is still 401", async () => {
    const fetchMock = (global as unknown as { fetch: jest.Mock }).fetch;
    fetchMock
      .mockResolvedValueOnce(createJsonResponse(401, { detail: "expired" }))
      .mockResolvedValueOnce(
        createJsonResponse(200, {
          access_token: "new-access-token",
          refresh_token: "new-refresh-token",
          token_type: "bearer",
        }),
      )
      .mockResolvedValueOnce(
        createJsonResponse(401, { detail: "still unauthorized" }),
      );

    await expect(
      request("/users/me", {
        withAuth: true,
      }),
    ).rejects.toMatchObject({
      name: "ApiError",
      status: 401,
    });

    expect(fetchMock).toHaveBeenCalledTimes(3);
    expect(mockClearSession).toHaveBeenCalledTimes(1);
  });

  it("deduplicates concurrent refresh attempts", async () => {
    const fetchMock = (global as unknown as { fetch: jest.Mock }).fetch;

    const callCountByPath = new Map<string, number>();
    let refreshCallCount = 0;

    fetchMock.mockImplementation(async (input: unknown) => {
      const url = String(input);

      if (url.includes("/auth/refresh")) {
        refreshCallCount += 1;
        return createJsonResponse(200, {
          access_token: "new-access-token",
          refresh_token: "new-refresh-token",
          token_type: "bearer",
        });
      }

      const currentCount = (callCountByPath.get(url) ?? 0) + 1;
      callCountByPath.set(url, currentCount);

      if (currentCount === 1) {
        return createJsonResponse(401, { detail: "expired" });
      }

      return createJsonResponse(200, {
        ok: true,
        url,
      });
    });

    const [firstResult, secondResult] = await Promise.all([
      request<{ ok: boolean; url: string }>("/users/me", {
        withAuth: true,
      }),
      request<{ ok: boolean; url: string }>("/users/profile", {
        withAuth: true,
      }),
    ]);

    expect(firstResult.ok).toBe(true);
    expect(secondResult.ok).toBe(true);
    expect(refreshCallCount).toBe(1);
    expect(mockSetToken).toHaveBeenCalledTimes(1);
    expect(mockClearSession).not.toHaveBeenCalled();
  });
});
