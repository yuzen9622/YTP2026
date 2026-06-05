export const POLICY_CATEGORY_LABEL_MAP = {
  international: "國際交流",
  youth_subsidy: "青年補助",
  latest_news: "最新消息",
  policy_news: "政策新聞",
  entrepreneurship: "創業輔導",
} as const;

export type PolicyCategoryLabelKey = keyof typeof POLICY_CATEGORY_LABEL_MAP;

function isPolicyCategoryLabelKey(value: string): value is PolicyCategoryLabelKey {
  return Object.prototype.hasOwnProperty.call(POLICY_CATEGORY_LABEL_MAP, value);
}

export function getPolicyCategoryLabel(category: string): string {
  const normalizedCategory = category.trim().toLowerCase();
  if (isPolicyCategoryLabelKey(normalizedCategory)) {
    return POLICY_CATEGORY_LABEL_MAP[normalizedCategory];
  }

  return category;
}
