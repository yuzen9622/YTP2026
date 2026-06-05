export type HttpMethod = "GET" | "POST" | "PUT" | "PATCH" | "DELETE";

export type QueryPrimitive = string | number | boolean | null | undefined;

export type QueryParams = Record<
  string,
  QueryPrimitive | QueryPrimitive[]
>;

export interface ApiRequestOptions {
  method?: HttpMethod;
  headers?: HeadersInit;
  params?: QueryParams;
  body?: unknown;
  timeoutMs?: number;
  signal?: AbortSignal;
  withAuth?: boolean;
}

export type RequestOptionsWithoutMethod = Omit<
  ApiRequestOptions,
  "method" | "body"
>;
