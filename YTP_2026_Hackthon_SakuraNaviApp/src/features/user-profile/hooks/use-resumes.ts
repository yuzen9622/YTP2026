import {
  useMutation,
  useQuery,
  useQueryClient,
  type UseMutationResult,
  type UseQueryResult,
} from "@tanstack/react-query";
import {
  createResume,
  deleteResume,
  getMyResumes,
  setPrimaryResume,
  unsetPrimaryResume,
  updateResume,
} from "../api/resume-api";
import type { CreateResumePayload, Resume, UpdateResumePayload } from "../types";
import { invalidateResumes, RESUMES_QUERY_KEY } from "./resumes-query";

export function useResumesQuery(options?: {
  enabled?: boolean;
}): UseQueryResult<Resume[], Error> {
  return useQuery<Resume[], Error>({
    queryKey: RESUMES_QUERY_KEY,
    queryFn: getMyResumes,
    enabled: options?.enabled ?? true,
  });
}

export function useCreateResumeMutation(): UseMutationResult<
  Resume,
  Error,
  CreateResumePayload
> {
  const queryClient = useQueryClient();

  return useMutation<Resume, Error, CreateResumePayload>({
    mutationFn: createResume,
    onSuccess: async () => {
      await invalidateResumes(queryClient);
    },
  });
}

export function useUpdateResumeMutation(): UseMutationResult<
  Resume,
  Error,
  { resumeId: string; payload: UpdateResumePayload }
> {
  const queryClient = useQueryClient();

  return useMutation<Resume, Error, { resumeId: string; payload: UpdateResumePayload }>({
    mutationFn: ({ resumeId, payload }) => updateResume(resumeId, payload),
    onSuccess: async () => {
      await invalidateResumes(queryClient);
    },
  });
}

export function useDeleteResumeMutation(): UseMutationResult<void, Error, string> {
  const queryClient = useQueryClient();

  return useMutation<void, Error, string>({
    mutationFn: deleteResume,
    onSuccess: async () => {
      await invalidateResumes(queryClient);
    },
  });
}

export function useSetPrimaryResumeMutation(): UseMutationResult<Resume, Error, string> {
  const queryClient = useQueryClient();

  return useMutation<Resume, Error, string>({
    mutationFn: setPrimaryResume,
    onSuccess: async () => {
      await invalidateResumes(queryClient);
    },
  });
}

export function useUnsetPrimaryResumeMutation(): UseMutationResult<void, Error, string> {
  const queryClient = useQueryClient();

  return useMutation<void, Error, string>({
    mutationFn: unsetPrimaryResume,
    onSuccess: async () => {
      await invalidateResumes(queryClient);
    },
  });
}
