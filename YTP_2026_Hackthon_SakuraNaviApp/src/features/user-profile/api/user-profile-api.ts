import { apiClient } from "@/lib/api";
import type {
  ChangePasswordPayload,
  UpdatePersonalInfoPayload,
  UpdatePersonaPayload,
  UpdateProfilePayload,
} from "../types";

export async function updateProfile(
  userId: string,
  payload: UpdateProfilePayload,
): Promise<void> {
  await apiClient.patch(`/users/me`, payload);
}

export async function updatePersonalInfo(
  userId: string,
  payload: UpdatePersonalInfoPayload,
): Promise<void> {
  await apiClient.patch(`/users/${userId}/personal-info`, payload);
}

export async function updatePersona(
  userId: string,
  payload: UpdatePersonaPayload,
): Promise<void> {
  await apiClient.patch(`/users/${userId}/persona`, payload);
}

export async function changePassword(
  payload: ChangePasswordPayload,
): Promise<void> {
  await apiClient.put(`/users/me/password`, payload);
}
