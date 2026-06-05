export const CAREER_STATUS_OPTIONS = [
  { label: "待業中", value: "unemployed" },
  { label: "在職中", value: "employed" },
  { label: "學生", value: "student" },
] as const;

export const DEFAULT_TAG_OPTIONS = [
  "就業",
  "實習",
  "獎學金",
  "AI/機器學習",
  "產品設計",
  "海外交流",
  "志工",
  "創業",
  "公職",
  "語言學習",
] as const;

export const MAX_TAGS = 20;
export const MAX_TAG_LENGTH = 50;
export const MAX_BIO_LENGTH = 500;
