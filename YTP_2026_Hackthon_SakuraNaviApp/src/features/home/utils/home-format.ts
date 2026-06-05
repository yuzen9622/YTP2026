const SAFE_TEXT = "--";

const WEEKDAY_LABELS = [
  "週日",
  "週一",
  "週二",
  "週三",
  "週四",
  "週五",
  "週六",
] as const;

export interface HomeDateParts {
  dateText: string;
  monthText: string;
  dayText: string;
  weekText: string;
  isToday: boolean;
}

function toDate(value?: string | null): Date | null {
  if (!value) {
    return null;
  }

  const date = new Date(value);
  return Number.isNaN(date.getTime()) ? null : date;
}

export function formatHomeDate(value?: string | null): string {
  const date = toDate(value);
  if (!date) {
    return SAFE_TEXT;
  }

  return new Intl.DateTimeFormat("zh-TW", {
    year: "numeric",
    month: "2-digit",
    day: "2-digit",
  }).format(date);
}

export function buildHomeDateParts(value?: string | null): HomeDateParts {
  const date = toDate(value);
  if (!date) {
    return {
      dateText: SAFE_TEXT,
      monthText: SAFE_TEXT,
      dayText: SAFE_TEXT,
      weekText: SAFE_TEXT,
      isToday: false,
    };
  }

  const now = new Date();
  const isToday =
    now.getFullYear() === date.getFullYear() &&
    now.getMonth() === date.getMonth() &&
    now.getDate() === date.getDate();

  return {
    dateText: formatHomeDate(value),
    monthText: String(date.getMonth() + 1).padStart(2, "0"),
    dayText: String(date.getDate()).padStart(2, "0"),
    weekText: WEEKDAY_LABELS[date.getDay()],
    isToday,
  };
}
