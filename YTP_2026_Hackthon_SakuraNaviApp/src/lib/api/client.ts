import { toast } from "sonner-native";
import {
  getAuthToken as getStoredAuthToken,
  getRefreshToken as getStoredRefreshToken,
  parseAuthTokens,
} from "@/lib/auth";
import { useUserStore } from "@/store/user-store";
import { ApiError } from "./errors";
import { fetch } from "expo/fetch";
import type {
  ApiRequestOptions,
  QueryParams,
  RequestOptionsWithoutMethod,
} from "./types";

const API_BASE_URL =
  process.env.EXPO_PUBLIC_API_URL ?? "https://api.sakura-navi.app/v1";

const DEFAULT_TIMEOUT_MS = 30000;
const REFRESH_ENDPOINT_PATH = "/auth/refresh";

interface InternalRequestOptions extends ApiRequestOptions {
  _hasRetriedAfterRefresh?: boolean;
}

let refreshPromise: Promise<void> | null = null;

export function getApiBaseUrl(): string {
  return API_BASE_URL;
}

function buildUrl(path: string): string {
  if (/^https?:\/\//i.test(path)) {
    return path;
  }

  if (path.startsWith("/")) {
    return `${API_BASE_URL}${path}`;
  }
  console.log("API_BASE_URL", API_BASE_URL);
  return `${API_BASE_URL}/${path}`;
}

function appendQueryParams(url: string, params?: QueryParams): string {
  if (!params) {
    return url;
  }

  const query = new URLSearchParams();

  for (const [key, value] of Object.entries(params)) {
    if (value === undefined || value === null) {
      continue;
    }

    if (Array.isArray(value)) {
      for (const item of value) {
        if (item === undefined || item === null) {
          continue;
        }

        query.append(key, String(item));
      }
      continue;
    }

    query.append(key, String(value));
  }

  const queryString = query.toString();
  if (!queryString) {
    return url;
  }

  return `${url}${url.includes("?") ? "&" : "?"}${queryString}`;
}

function shouldJsonEncode(body: unknown): boolean {
  if (body === undefined || body === null) {
    return false;
  }

  return !(body instanceof FormData) && !(body instanceof URLSearchParams);
}

function buildRequestBody(body: unknown): BodyInit | undefined {
  if (body === undefined || body === null) {
    return undefined;
  }

  if (shouldJsonEncode(body)) {
    return JSON.stringify(body);
  }

  return body as BodyInit;
}

function resolveErrorMessage(status: number, data: unknown): string {
  if (typeof data === "string" && data.trim().length > 0) {
    return data;
  }

  if (data && typeof data === "object") {
    const detail = Reflect.get(data, "detail");
    if (typeof detail === "string" && detail.trim().length > 0) {
      return detail;
    }

    const message = Reflect.get(data, "message");
    if (typeof message === "string" && message.trim().length > 0) {
      return message;
    }
  }

  if (status >= 500) {
    return "伺服器異常，請稍後重試";
  }

  if (status === 429) {
    return "使用頻率過高，請稍後再試";
  }

  if (status === 401) {
    return "登入狀態已失效，請重新登入";
  }

  return "請求失敗，請稍後再試";
}

function showErrorToast(status: number, data: unknown): void {
  if (status === 422) {
    const detail =
      data && typeof data === "object" ? Reflect.get(data, "detail") : null;
    toast.error(
      typeof detail === "string" && detail.length > 0
        ? detail
        : "資料有誤，請確認後再試",
    );
    return;
  }

  if (status === 429) {
    toast.error("使用頻率過高，請稍後再試");
    return;
  }

  if (status >= 500) {
    toast.error("伺服器異常，請稍後重試");
  }
}

async function parseResponseData(response: Response): Promise<unknown> {
  if (response.status === 204) {
    return null;
  }

  const contentType = response.headers.get("content-type") ?? "";
  if (contentType.includes("application/json")) {
    try {
      return await response.json();
    } catch {
      return null;
    }
  }

  const text = await response.text();
  return text.length > 0 ? text : null;
}

async function buildHeaders(
  options: ApiRequestOptions,
  body: unknown,
): Promise<Headers> {
  const headers = new Headers(options.headers ?? {});
  headers.set("Accept", "application/json");

  if (shouldJsonEncode(body) && !headers.has("Content-Type")) {
    headers.set("Content-Type", "application/json");
  }

  if (options.withAuth !== false) {
    const token = await getStoredAuthToken();
    if (token) {
      headers.set("Authorization", `Bearer ${token}`);
    }
  }

  return headers;
}

function shouldAttemptAuthRefresh(
  options: InternalRequestOptions,
  status: number,
): boolean {
  return (
    status === 401 &&
    options.withAuth !== false &&
    options._hasRetriedAfterRefresh !== true
  );
}

function shouldLogoutForUnauthorized(
  options: InternalRequestOptions,
  status: number,
): boolean {
  return (
    status === 401 &&
    options.withAuth !== false &&
    options._hasRetriedAfterRefresh === true
  );
}

export async function refreshAccessTokenOnce(): Promise<void> {
  if (!refreshPromise) {
    refreshPromise = runRefreshTokenRequest().finally(() => {
      refreshPromise = null;
    });
  }

  return refreshPromise;
}

async function runRefreshTokenRequest(): Promise<void> {
  const refreshToken = await getStoredRefreshToken();
  if (!refreshToken) {
    throw new ApiError("登入狀態已失效，請重新登入", 401);
  }

  const controller = new AbortController();
  const timeoutId = setTimeout(() => {
    controller.abort();
  }, DEFAULT_TIMEOUT_MS);

  try {
    const response = await fetch(buildUrl(REFRESH_ENDPOINT_PATH), {
      method: "POST",
      headers: {
        Accept: "application/json",
        "Content-Type": "application/json",
      },
      body: JSON.stringify({
        refresh_token: refreshToken,
      }),
      signal: controller.signal,
    });

    const data = await parseResponseData(response);

    if (!response.ok) {
      throw new ApiError(
        resolveErrorMessage(response.status, data),
        response.status,
        data,
      );
    }

    const { accessToken, refreshToken: nextRefreshToken } =
      parseAuthTokens(data);

    if (!accessToken || !nextRefreshToken) {
      throw new ApiError("刷新登入憑證失敗，請重新登入", 500, data);
    }

    await useUserStore.getState().setToken(accessToken, nextRefreshToken);
  } catch (error) {
    if (error instanceof ApiError) {
      throw error;
    }

    if (error instanceof Error && error.name === "AbortError") {
      throw new ApiError("連線逾時，請稍後再試", 408);
    }

    throw new ApiError("網路連線異常，請稍後再試", 0, error);
  } finally {
    clearTimeout(timeoutId);
  }
}

export async function request<T>(
  path: string,
  options: ApiRequestOptions = {},
): Promise<T> {
  const internalOptions = options as InternalRequestOptions;
  const method = internalOptions.method ?? "GET";
  const timeoutMs = internalOptions.timeoutMs ?? DEFAULT_TIMEOUT_MS;

  const controller = new AbortController();
  const timeoutId = setTimeout(() => {
    controller.abort();
  }, timeoutMs);

  if (internalOptions.signal) {
    if (internalOptions.signal.aborted) {
      controller.abort();
    } else {
      internalOptions.signal.addEventListener(
        "abort",
        () => controller.abort(),
        {
          once: true,
        },
      );
    }
  }

  try {
    const requestBody =
      method === "GET" || method === "DELETE"
        ? undefined
        : buildRequestBody(internalOptions.body);

    const response = await fetch(
      appendQueryParams(buildUrl(path), internalOptions.params),
      {
        method,
        headers: await buildHeaders(internalOptions, internalOptions.body),
        body: requestBody,
        signal: controller.signal,
      },
    );

    const data = await parseResponseData(response);

    if (!response.ok) {
      if (shouldAttemptAuthRefresh(internalOptions, response.status)) {
        try {
          await refreshAccessTokenOnce();
        } catch (refreshError) {
          if (refreshError instanceof ApiError && refreshError.status === 401) {
            useUserStore.getState().clearSession();
          }
          throw refreshError;
        }

        return request<T>(path, {
          ...internalOptions,
          _hasRetriedAfterRefresh: true,
        } as ApiRequestOptions);
      }

      if (shouldLogoutForUnauthorized(internalOptions, response.status)) {
        useUserStore.getState().clearSession();
      }

      showErrorToast(response.status, data);
      throw new ApiError(
        resolveErrorMessage(response.status, data),
        response.status,
        data,
      );
    }

    return data as T;
  } catch (error) {
    if (error instanceof ApiError) {
      throw error;
    }

    if (error instanceof Error && error.name === "AbortError") {
      toast.error("連線逾時，請稍後再試");
      throw new ApiError("連線逾時，請稍後再試", 408);
    }

    toast.error("網路連線異常，請稍後再試");
    throw new ApiError("網路連線異常，請稍後再試", 0, error);
  } finally {
    clearTimeout(timeoutId);
  }
}

export const apiClient = {
  get<T>(path: string, options: RequestOptionsWithoutMethod = {}) {
    return request<T>(path, {
      ...options,
      method: "GET",
    });
  },
  stream<T>(
    path: string,
    body: { conversation_id: string | null; message: string },
    options: RequestOptionsWithoutMethod = {},
  ) {
    return request<T>(path, {
      ...options,
      method: "POST",
      headers: {
        Accept: "text/event-stream",
        "Content-Type": "text/event-stream",
      },
      body,
    });
  },

  post<T>(
    path: string,
    body?: unknown,
    options: RequestOptionsWithoutMethod = {},
  ) {
    return request<T>(path, {
      ...options,
      method: "POST",
      body,
    });
  },

  put<T>(
    path: string,
    body?: unknown,
    options: RequestOptionsWithoutMethod = {},
  ) {
    return request<T>(path, {
      ...options,
      method: "PUT",
      body,
    });
  },

  patch<T>(
    path: string,
    body?: unknown,
    options: RequestOptionsWithoutMethod = {},
  ) {
    return request<T>(path, {
      ...options,
      method: "PATCH",
      body,
    });
  },

  delete<T>(path: string, options: RequestOptionsWithoutMethod = {}) {
    return request<T>(path, {
      ...options,
      method: "DELETE",
    });
  },
};
