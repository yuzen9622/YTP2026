import {
  buildResumePayload,
  createDefaultResumeFormValue,
  validateResumeForm,
} from "@/features/user-profile/utils/resume-form";

describe("resume form validation", () => {
  it("blocks empty title", () => {
    const form = createDefaultResumeFormValue();
    form.title = "";

    expect(validateResumeForm(form)).toBe("請輸入履歷標題");
  });

  it("blocks invalid salary range", () => {
    const form = createDefaultResumeFormValue();
    form.title = "工程師履歷";
    form.expectedSalaryEnabled = true;
    form.expectedSalaryMin = "90000";
    form.expectedSalaryMax = "50000";
    form.expectedSalaryCurrency = "TWD";

    expect(validateResumeForm(form)).toBe("期望薪資最低值不可大於最高值");
  });

  it("blocks invalid date format", () => {
    const form = createDefaultResumeFormValue();
    form.title = "工程師履歷";
    form.workExperiences = [
      {
        company: "ABC",
        position: "Frontend Engineer",
        start_date: "2026/04",
        end_date: "present",
      },
    ];

    expect(validateResumeForm(form)).toBe("工作經驗開始年月格式需為 YYYY-MM");
  });

  it("blocks non-http external url", () => {
    const form = createDefaultResumeFormValue();
    form.title = "工程師履歷";
    form.externalLinks = [{ label: "GitHub", url: "github.com/user" }];

    expect(validateResumeForm(form)).toBe(
      "外部連結網址需以 http:// 或 https:// 開頭",
    );
  });

  it("builds payload without skill level field", () => {
    const form = createDefaultResumeFormValue();
    form.title = "工程師履歷";
    form.skills = [{ name: "TypeScript" }];

    const payload = buildResumePayload(form);

    expect(payload.skills).toEqual([{ name: "TypeScript" }]);
  });
});
