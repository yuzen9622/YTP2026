import { apiClient } from "@/lib/api";
import { parseAuthTokens } from "@/lib/auth";
import { User } from "@/types";
import type { LoginPayload, RegisterPayload, AuthResponse } from "../types";
export type { LoginPayload, RegisterPayload, AuthResponse };

interface UserProfileResponse {
  id: string;
  name: string;
  account: string;
  email?: string | null;
  phone?: string | null;
  bio: string;
  age?: number | null;
  birth_date?: string | null;
  career?: User["career"];
  tags?: string[];
  avatar_url?: string | null;
  language_skills?: User["language_skills"];
  registered_address?: string | null;
  residential_address?: string | null;
  is_residential_same_as_registered?: boolean;
  gender?: User["gender"];
  is_active: boolean;
  created_at: string;
  updated_at: string;
}

function normalizeUserProfile(input: UserProfileResponse): User {
  return {
    id: input.id,
    name: input.name,
    account: input.account,
    email: input.email ?? null,
    phone: input.phone ?? null,
    bio: input.bio,
    age: input.age ?? null,
    birth_date: input.birth_date ?? null,
    career: input.career ?? null,
    tags: Array.isArray(input.tags) ? input.tags : [],
    avatar_url: input.avatar_url ?? null,
    language_skills: Array.isArray(input.language_skills)
      ? input.language_skills
      : [],
    registered_address: input.registered_address ?? null,
    residential_address: input.residential_address ?? null,
    is_residential_same_as_registered:
      input.is_residential_same_as_registered ?? false,
    gender: input.gender ?? null,
    is_active: input.is_active,
    created_at: input.created_at,
    updated_at: input.updated_at,
    // aliases for old consumers
    createdAt: input.created_at,
    updatedAt: input.updated_at,
  };
}

export function getAuthToken(data: AuthResponse): string | null {
  return parseAuthTokens(data).accessToken;
}

export function getAuthTokens(data: unknown): {
  accessToken: string | null;
  refreshToken: string | null;
} {
  return parseAuthTokens(data);
}

export async function login(payload: LoginPayload): Promise<AuthResponse> {
  return apiClient.post<AuthResponse>("/auth/login", payload, {
    withAuth: false,
  });
}

export async function me(): Promise<User> {
  const data = await apiClient.get<UserProfileResponse>("/users/me", {
    withAuth: true,
  });

  return normalizeUserProfile(data);
}

export async function register(
  payload: RegisterPayload,
): Promise<AuthResponse> {
  return apiClient.post<AuthResponse>("/auth/register", payload, {
    withAuth: false,
  });
}

export async function refreshAuthToken(
  refreshToken: string,
): Promise<AuthResponse> {
  return apiClient.post<AuthResponse>(
    "/auth/refresh",
    { refresh_token: refreshToken },
    { withAuth: false },
  );
}

export async function forgotPassword(email: string): Promise<void> {
  await apiClient.post("/auth/forgot-password", { email }, { withAuth: false });
}
