import { apiClient } from "@/lib/api";
import type { CreateResumePayload, Resume, UpdateResumePayload } from "../types";

export async function getMyResumes(): Promise<Resume[]> {
  return apiClient.get<Resume[]>("/resumes");
}

export async function createResume(payload: CreateResumePayload): Promise<Resume> {
  return apiClient.post<Resume>("/resumes", payload);
}

export async function updateResume(
  resumeId: string,
  payload: UpdateResumePayload,
): Promise<Resume> {
  return apiClient.put<Resume>(`/resumes/${resumeId}`, payload);
}

export async function deleteResume(resumeId: string): Promise<void> {
  await apiClient.delete<void>(`/resumes/${resumeId}`);
}

export async function setPrimaryResume(resumeId: string): Promise<Resume> {
  return apiClient.patch<Resume>(`/resumes/${resumeId}/primary`);
}

export async function unsetPrimaryResume(resumeId: string): Promise<void> {
  await apiClient.delete<void>(`/resumes/${resumeId}/primary`);
}
