import {
  buildHomeDateParts,
  formatHomeDate,
} from "@/features/home/utils/home-format";

describe("home date formatting", () => {
  it("returns safe fallback for null and invalid date values", () => {
    expect(formatHomeDate(null)).toBe("--");
    expect(formatHomeDate("not-a-date")).toBe("--");
    expect(buildHomeDateParts(null)).toEqual({
      dateText: "--",
      monthText: "--",
      dayText: "--",
      weekText: "--",
      isToday: false,
    });
  });

  it("builds month/day/week labels for valid dates", () => {
    const parts = buildHomeDateParts("2026-04-20T00:00:00Z");

    expect(parts.monthText).toBe("04");
    expect(parts.dayText).toBe("20");
    expect(parts.weekText.startsWith("週")).toBe(true);
    expect(parts.dateText).not.toBe("--");
  });
});
