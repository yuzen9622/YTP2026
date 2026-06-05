import type {
  CreateResumePayload,
  ExternalLinkInput,
  WorkExperienceInput,
  WorkTimeRangeInput,
} from "../types";

export const WORK_TIME_TYPE_OPTIONS = [
  { label: "全職", value: "full_time" },
  { label: "兼職", value: "part_time" },
  { label: "實習", value: "internship" },
  { label: "接案", value: "freelance" },
] as const;

const YEAR_MONTH_REGEX = /^\d{4}-\d{2}$/;
const HH_MM_REGEX = /^\d{2}:\d{2}$/;

export interface ResumeFormValue {
  title: string;
  summary: string;
  skills: Array<{ name: string }>;
  workExperiences: WorkExperienceInput[];
  externalLinks: ExternalLinkInput[];
  expectedSalaryEnabled: boolean;
  expectedSalaryMin: string;
  expectedSalaryMax: string;
  expectedSalaryCurrency: string;
  workTimeRangeEnabled: boolean;
  workTimeRange: WorkTimeRangeInput;
}

export function createDefaultResumeFormValue(): ResumeFormValue {
  return {
    title: "",
    summary: "",
    skills: [{ name: "" }],
    workExperiences: [
      {
        company: "",
        position: "",
        description: "",
        start_date: "",
        end_date: "",
        is_current: false,
      },
    ],
    externalLinks: [{ label: "", url: "" }],
    expectedSalaryEnabled: false,
    expectedSalaryMin: "",
    expectedSalaryMax: "",
    expectedSalaryCurrency: "TWD",
    workTimeRangeEnabled: false,
    workTimeRange: {
      start_time: "09:00",
      end_time: "18:00",
      work_time_type: "full_time",
    },
  };
}

export function toResumeFormValue(payload: Partial<CreateResumePayload>): ResumeFormValue {
  const form = createDefaultResumeFormValue();

  form.title = payload.title ?? "";
  form.summary = payload.summary ?? "";

  if (payload.skills && payload.skills.length > 0) {
    form.skills = payload.skills.map((item) => ({ name: item.name ?? "" }));
  }

  if (payload.work_experiences && payload.work_experiences.length > 0) {
    form.workExperiences = payload.work_experiences.map((item) => ({
      company: item.company ?? "",
      position: item.position ?? "",
      description: item.description ?? "",
      start_date: item.start_date ?? "",
      end_date: item.end_date ?? "",
      is_current: item.is_current ?? false,
    }));
  }

  if (payload.external_links && payload.external_links.length > 0) {
    form.externalLinks = payload.external_links.map((item) => ({
      label: item.label ?? "",
      url: item.url ?? "",
    }));
  }

  if (payload.expected_salary) {
    form.expectedSalaryEnabled = true;
    form.expectedSalaryMin = String(payload.expected_salary.min ?? "");
    form.expectedSalaryMax = String(payload.expected_salary.max ?? "");
    form.expectedSalaryCurrency = payload.expected_salary.currency ?? "TWD";
  }

  if (payload.work_time_range) {
    form.workTimeRangeEnabled = true;
    form.workTimeRange = {
      start_time: payload.work_time_range.start_time ?? "09:00",
      end_time: payload.work_time_range.end_time ?? "18:00",
      work_time_type: payload.work_time_range.work_time_type,
    };
  }

  return form;
}

export function validateResumeForm(values: ResumeFormValue): string | null {
  const title = values.title.trim();
  if (!title) {
    return "請輸入履歷標題";
  }

  if (title.length > 100) {
    return "履歷標題不得超過 100 字";
  }

  if (values.summary.length > 2000) {
    return "履歷簡述不得超過 2000 字";
  }

  if (values.expectedSalaryEnabled) {
    const min = Number(values.expectedSalaryMin);
    const max = Number(values.expectedSalaryMax);

    if (!Number.isInteger(min) || !Number.isInteger(max) || min < 0 || max < 0) {
      return "期望薪資需為非負整數";
    }

    if (min > max) {
      return "期望薪資最低值不可大於最高值";
    }

    const currency = values.expectedSalaryCurrency.trim();
    if (!currency || currency.length !== 3) {
      return "幣別需為 3 碼，例如 TWD";
    }
  }

  const experiences = values.workExperiences.filter(
    (item) => item.company.trim() || item.position.trim() || item.start_date.trim(),
  );

  for (const experience of experiences) {
    if (!experience.company.trim() || !experience.position.trim() || !experience.start_date.trim()) {
      return "工作經驗需填寫公司、職位與開始年月";
    }

    if (!YEAR_MONTH_REGEX.test(experience.start_date.trim())) {
      return "工作經驗開始年月格式需為 YYYY-MM";
    }

    const endDate = (experience.end_date ?? "").trim();
    if (endDate && endDate !== "present" && !YEAR_MONTH_REGEX.test(endDate)) {
      return "工作經驗結束年月需為 YYYY-MM 或 present";
    }
  }

  const links = values.externalLinks.filter((item) => item.label.trim() || item.url.trim());
  for (const link of links) {
    if (!link.label.trim() || !link.url.trim()) {
      return "外部連結需填寫名稱與網址";
    }

    const url = link.url.trim();
    if (!url.startsWith("http://") && !url.startsWith("https://")) {
      return "外部連結網址需以 http:// 或 https:// 開頭";
    }
  }

  if (values.workTimeRangeEnabled) {
    const startTime = values.workTimeRange.start_time?.trim() ?? "";
    const endTime = values.workTimeRange.end_time?.trim() ?? "";

    if (!HH_MM_REGEX.test(startTime) || !HH_MM_REGEX.test(endTime)) {
      return "工作時間格式需為 HH:MM";
    }
  }

  return null;
}

export function buildResumePayload(values: ResumeFormValue): CreateResumePayload {
  const normalizedSkills = values.skills
    .map((item) => ({ name: item.name.trim() }))
    .filter((item) => item.name.length > 0);

  const normalizedExperiences = values.workExperiences
    .map((item) => ({
      company: item.company.trim(),
      position: item.position.trim(),
      description: (item.description ?? "").trim(),
      start_date: item.start_date.trim(),
      end_date: (item.end_date ?? "").trim() || undefined,
      is_current: item.is_current ?? false,
    }))
    .filter((item) => item.company || item.position || item.start_date);

  const normalizedLinks = values.externalLinks
    .map((item) => ({
      label: item.label.trim(),
      url: item.url.trim(),
    }))
    .filter((item) => item.label || item.url);

  return {
    title: values.title.trim(),
    summary: values.summary.trim() || null,
    skills: normalizedSkills.length > 0 ? normalizedSkills : null,
    work_experiences: normalizedExperiences.length > 0 ? normalizedExperiences : null,
    external_links: normalizedLinks.length > 0 ? normalizedLinks : null,
    expected_salary: values.expectedSalaryEnabled
      ? {
          min: Number(values.expectedSalaryMin),
          max: Number(values.expectedSalaryMax),
          currency: values.expectedSalaryCurrency.trim().toUpperCase(),
        }
      : null,
    work_time_range: values.workTimeRangeEnabled
      ? {
          start_time: values.workTimeRange.start_time?.trim() || "09:00",
          end_time: values.workTimeRange.end_time?.trim() || "18:00",
          work_time_type: values.workTimeRange.work_time_type,
        }
      : null,
  };
}
