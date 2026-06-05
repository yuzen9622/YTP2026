import type {
  CareerStage,
  EducationLevel,
  SalaryRange,
  CareerStatus,
  Gender,
} from "@/types";

export interface UpdatePersonalInfoPayload {
  displayName: string;
  age: number;
  location: string;
  educationLevel: EducationLevel;
}

export interface UpdatePersonaPayload {
  fieldTags: string[];
  careerStage: CareerStage;
  expectedSalary: SalaryRange;
}

export interface UpdateProfilePayload {
  name?: string;
  bio?: string | null;
  email?: string | null;
  phone?: string | null;
  age?: number | null;
  birth_date?: string | null;
  career?: CareerStatus | null;
  tags?: string[] | null;
  avatar_url?: string | null;
  registered_address?: string | null;
  residential_address?: string | null;
  is_residential_same_as_registered?: boolean | null;
  gender?: Gender | null;
  language_skills?:
    | {
        language: string;
        proficiency:
          | "native"
          | "advanced"
          | "upper_intermediate"
          | "intermediate"
          | "basic";
      }[]
    | null;
}

export interface ChangePasswordPayload {
  current_password: string;
  new_password: string;
}
