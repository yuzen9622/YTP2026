export type ApiAccessMode = "private" | "public";

export interface ApiAccessOptions {
  accessMode?: ApiAccessMode;
}

export function resolveWithAuth(options?: ApiAccessOptions): boolean | undefined {
  return options?.accessMode === "public" ? false : undefined;
}
