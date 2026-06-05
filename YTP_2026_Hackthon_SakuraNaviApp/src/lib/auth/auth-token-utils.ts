export interface ParsedAuthTokens {
  accessToken: string | null;
  refreshToken: string | null;
}

export function parseAuthTokens(data: unknown): ParsedAuthTokens {
  if (!data || typeof data !== "object") {
    return {
      accessToken: null,
      refreshToken: null,
    };
  }

  const accessToken = normalizeTokenValue(
    Reflect.get(data, "access_token") ?? Reflect.get(data, "token"),
  );
  const refreshToken = normalizeTokenValue(Reflect.get(data, "refresh_token"));

  return {
    accessToken,
    refreshToken,
  };
}

function normalizeTokenValue(value: unknown): string | null {
  if (typeof value !== "string") {
    return null;
  }

  const trimmedValue = value.trim();
  return trimmedValue.length > 0 ? trimmedValue : null;
}
