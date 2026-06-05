export type WorkTimeType =
  | "full_time"
  | "part_time"
  | "internship"
  | "freelance";

export interface SkillInput {
  name: string;
  level?: string;
}

export interface WorkExperienceInput {
  company: string;
  position: string;
  description?: string;
  start_date: string;
  end_date?: string;
  is_current?: boolean;
}

export interface ExternalLinkInput {
  label: string;
  url: string;
}

export interface ExpectedSalaryInput {
  min: number;
  max: number;
  currency: string;
}

export interface WorkTimeRangeInput {
  start_time?: string;
  end_time?: string;
  work_time_type: WorkTimeType;
}

export interface Resume {
  id: string;
  user_id: string;
  title: string;
  summary: string | null;
  skills?: SkillInput[] | null;
  work_experiences?: WorkExperienceInput[] | null;
  external_links?: ExternalLinkInput[] | null;
  expected_salary?: ExpectedSalaryInput | null;
  work_time_range?: WorkTimeRangeInput | null;
  is_primary: boolean;
  created_at: string;
  updated_at: string;
}

export interface CreateResumePayload {
  title: string;
  summary?: string | null;
  skills?: SkillInput[] | null;
  work_experiences?: WorkExperienceInput[] | null;
  external_links?: ExternalLinkInput[] | null;
  expected_salary?: ExpectedSalaryInput | null;
  work_time_range?: WorkTimeRangeInput | null;
}

export interface UpdateResumePayload {
  title?: string | null;
  summary?: string | null;
  skills?: SkillInput[] | null;
  work_experiences?: WorkExperienceInput[] | null;
  external_links?: ExternalLinkInput[] | null;
  expected_salary?: ExpectedSalaryInput | null;
  work_time_range?: WorkTimeRangeInput | null;
}
