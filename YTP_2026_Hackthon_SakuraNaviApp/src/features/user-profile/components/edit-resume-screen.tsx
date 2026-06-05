import { useEffect, useMemo, useState } from "react";
import { Pressable, ScrollView, TextInput, View } from "react-native";
import { Stack, router, useLocalSearchParams } from "expo-router";
import { ChevronLeft } from "lucide-react-native";
import { toast } from "sonner-native";

import { colors } from "@/lib/colors.ios";
import { Label } from "@/components/ui/label";
import { Text } from "@/components/ui/text";
import { Button } from "@/components/ui/button";
import { Section } from "./section";

import {
  useCreateResumeMutation,
  useResumesQuery,
  useUpdateResumeMutation,
} from "../hooks/use-resumes";
import type { WorkTimeType } from "../types";
import {
  buildResumePayload,
  createDefaultResumeFormValue,
  toResumeFormValue,
  validateResumeForm,
  WORK_TIME_TYPE_OPTIONS,
  type ResumeFormValue,
} from "../utils/resume-form";

const PLACEHOLDER_EXPERIENCE = {
  company: "",
  position: "",
  description: "",
  start_date: "",
  end_date: "",
  is_current: false,
};

const PLACEHOLDER_LINK = {
  label: "",
  url: "",
};

export function EditResumeScreen() {
  const { resumeId } = useLocalSearchParams<{ resumeId?: string }>();
  const isEditMode = Boolean(resumeId);

  const resumesQuery = useResumesQuery();
  const createResumeMutation = useCreateResumeMutation();
  const updateResumeMutation = useUpdateResumeMutation();

  const editingResume = useMemo(
    () => resumesQuery.data?.find((item) => item.id === resumeId),
    [resumeId, resumesQuery.data],
  );
  const isMissingEditingResume =
    isEditMode && !resumesQuery.isLoading && !editingResume;

  const [formValue, setFormValue] = useState<ResumeFormValue>(() =>
    createDefaultResumeFormValue(),
  );

  useEffect(() => {
    if (!isEditMode || !editingResume) {
      return;
    }

    setFormValue(
      toResumeFormValue({
        title: editingResume.title,
        summary: editingResume.summary,
        skills: editingResume.skills,
        work_experiences: editingResume.work_experiences,
        external_links: editingResume.external_links,
        expected_salary: editingResume.expected_salary,
        work_time_range: editingResume.work_time_range,
      }),
    );
  }, [editingResume, isEditMode]);

  const isSubmitting =
    createResumeMutation.isPending ||
    updateResumeMutation.isPending ||
    isMissingEditingResume;

  const handleSave = async () => {
    const errorMessage = validateResumeForm(formValue);
    if (errorMessage) {
      toast.error(errorMessage);
      return;
    }

    const payload = buildResumePayload(formValue);

    try {
      if (isEditMode && resumeId) {
        await updateResumeMutation.mutateAsync({
          resumeId,
          payload,
        });
        toast.success("履歷已更新");
      } else {
        await createResumeMutation.mutateAsync(payload);
        toast.success("履歷已建立");
      }

      router.back();
    } catch {
      // API interceptor handles toasts
    }
  };

  const updateSkill = (index: number, name: string) => {
    setFormValue((prev) => ({
      ...prev,
      skills: prev.skills.map((item, itemIndex) =>
        itemIndex === index ? { ...item, name } : item,
      ),
    }));
  };

  const addSkill = () => {
    setFormValue((prev) => ({
      ...prev,
      skills: [...prev.skills, { name: "" }],
    }));
  };

  const removeSkill = (index: number) => {
    setFormValue((prev) => ({
      ...prev,
      skills:
        prev.skills.length === 1
          ? [{ name: "" }]
          : prev.skills.filter((_, itemIndex) => itemIndex !== index),
    }));
  };

  const updateExperience = (
    index: number,
    key: keyof (typeof PLACEHOLDER_EXPERIENCE),
    value: string | boolean,
  ) => {
    setFormValue((prev) => ({
      ...prev,
      workExperiences: prev.workExperiences.map((item, itemIndex) => {
        if (itemIndex !== index) {
          return item;
        }

        return {
          ...item,
          [key]: value,
        };
      }),
    }));
  };

  const addExperience = () => {
    setFormValue((prev) => ({
      ...prev,
      workExperiences: [...prev.workExperiences, { ...PLACEHOLDER_EXPERIENCE }],
    }));
  };

  const removeExperience = (index: number) => {
    setFormValue((prev) => ({
      ...prev,
      workExperiences:
        prev.workExperiences.length === 1
          ? [{ ...PLACEHOLDER_EXPERIENCE }]
          : prev.workExperiences.filter((_, itemIndex) => itemIndex !== index),
    }));
  };

  const updateLink = (index: number, key: "label" | "url", value: string) => {
    setFormValue((prev) => ({
      ...prev,
      externalLinks: prev.externalLinks.map((item, itemIndex) =>
        itemIndex === index ? { ...item, [key]: value } : item,
      ),
    }));
  };

  const addLink = () => {
    setFormValue((prev) => ({
      ...prev,
      externalLinks: [...prev.externalLinks, { ...PLACEHOLDER_LINK }],
    }));
  };

  const removeLink = (index: number) => {
    setFormValue((prev) => ({
      ...prev,
      externalLinks:
        prev.externalLinks.length === 1
          ? [{ ...PLACEHOLDER_LINK }]
          : prev.externalLinks.filter((_, itemIndex) => itemIndex !== index),
    }));
  };

  return (
    <>
      <Stack.Screen
        options={{
          title: isEditMode ? "編輯履歷" : "新增履歷",
          headerLeft: () => (
            <Pressable
              onPress={() => router.back()}
              className="items-center justify-center rounded-full shadow-sm w-9 h-9 active:opacity-70"
            >
              <ChevronLeft
                size={20}
                className="text-foreground"
                color={colors.foreground}
              />
            </Pressable>
          ),
          headerRight: () => (
            <Pressable
              onPress={handleSave}
              disabled={isSubmitting}
              className="px-4 py-1.5 rounded-full active:opacity-70"
            >
              <Text className="font-semibold text-[15px]">
                {isSubmitting ? "儲存中" : "儲存"}
              </Text>
            </Pressable>
          ),
        }}
      />

      {isMissingEditingResume ? (
        <ScrollView
          contentInsetAdjustmentBehavior="automatic"
          className="flex-1 bg-[#F7F7F8]"
          contentContainerClassName="p-4 pb-12 gap-6"
        >
          <Section title="資料狀態">
            <View className="px-4 py-3 gap-3">
              <Text className="text-destructive">找不到此履歷，可能已被刪除。</Text>
              <Button variant="outline" onPress={() => router.back()}>
                <Text>返回管理履歷</Text>
              </Button>
            </View>
          </Section>
        </ScrollView>
      ) : (
        <ScrollView
          contentInsetAdjustmentBehavior="automatic"
          className="flex-1 bg-[#F7F7F8]"
          contentContainerClassName="p-4 pb-12 gap-6"
        >
        {isEditMode && resumesQuery.isLoading && (
          <Section title="資料狀態">
            <View className="px-4 py-3">
              <Text className="text-muted-foreground">履歷載入中...</Text>
            </View>
          </Section>
        )}

        <Section title="基本資訊">
          <View className="px-4 py-3 border-b border-border">
            <Label className="text-muted-foreground text-[13px] mb-1">履歷標題</Label>
            <TextInput
              value={formValue.title}
              onChangeText={(value) =>
                setFormValue((prev) => ({
                  ...prev,
                  title: value,
                }))
              }
              placeholder="例如：前端工程師履歷"
              className="h-10 px-0 bg-transparent text-[16px] text-foreground"
            />
          </View>

          <View className="px-4 py-3">
            <View className="flex-row items-center justify-between mb-1">
              <Label className="text-muted-foreground text-[13px]">簡述</Label>
              <Text className="text-[12px] text-muted-foreground">
                {formValue.summary.length} / 2000
              </Text>
            </View>
            <TextInput
              value={formValue.summary}
              onChangeText={(value) =>
                setFormValue((prev) => ({
                  ...prev,
                  summary: value,
                }))
              }
              multiline
              numberOfLines={3}
              placeholder="請輸入履歷簡述"
              textAlignVertical="top"
              className="min-h-[76px] px-0 pt-2 bg-transparent text-[16px] text-foreground"
            />
          </View>
        </Section>

        <Section title="技能">
          <View className="px-4 py-3 gap-3">
            {formValue.skills.map((skill, index) => (
              <View key={`skill-${index}`} className="gap-2">
                <Label className="text-muted-foreground text-[13px]">技能 {index + 1}</Label>
                <View className="flex-row items-center gap-2">
                  <TextInput
                    value={skill.name}
                    onChangeText={(value) => updateSkill(index, value)}
                    placeholder="例如：TypeScript"
                    className="flex-1 h-10 rounded-md border border-border bg-background px-3 text-foreground"
                  />
                  <Pressable
                    onPress={() => removeSkill(index)}
                    className="h-10 items-center justify-center rounded-md border border-destructive/30 px-3"
                  >
                    <Text className="text-destructive text-sm">刪除</Text>
                  </Pressable>
                </View>
              </View>
            ))}

            <Button variant="outline" onPress={addSkill}>
              <Text>新增技能</Text>
            </Button>
            <Text className="text-xs text-muted-foreground">
              第一版僅輸入技能名稱，等級將由後端使用預設值。
            </Text>
          </View>
        </Section>

        <Section title="工作經驗">
          <View className="px-4 py-3 gap-4">
            {formValue.workExperiences.map((experience, index) => (
              <View key={`exp-${index}`} className="rounded-xl border border-border p-3 gap-2">
                <Text className="text-sm font-semibold text-foreground">經驗 {index + 1}</Text>

                <TextInput
                  value={experience.company}
                  onChangeText={(value) => updateExperience(index, "company", value)}
                  placeholder="公司名稱"
                  className="h-10 rounded-md border border-border bg-background px-3 text-foreground"
                />

                <TextInput
                  value={experience.position}
                  onChangeText={(value) => updateExperience(index, "position", value)}
                  placeholder="職位"
                  className="h-10 rounded-md border border-border bg-background px-3 text-foreground"
                />

                <TextInput
                  value={experience.description ?? ""}
                  onChangeText={(value) => updateExperience(index, "description", value)}
                  placeholder="工作描述"
                  multiline
                  numberOfLines={2}
                  className="min-h-[56px] rounded-md border border-border bg-background px-3 py-2 text-foreground"
                />

                <View className="flex-row gap-2">
                  <TextInput
                    value={experience.start_date}
                    onChangeText={(value) => updateExperience(index, "start_date", value)}
                    placeholder="開始年月 YYYY-MM"
                    className="flex-1 h-10 rounded-md border border-border bg-background px-3 text-foreground"
                  />
                  <TextInput
                    value={experience.end_date ?? ""}
                    onChangeText={(value) => updateExperience(index, "end_date", value)}
                    placeholder="結束年月 / present"
                    className="flex-1 h-10 rounded-md border border-border bg-background px-3 text-foreground"
                  />
                </View>

                <Pressable
                  onPress={() =>
                    updateExperience(index, "is_current", !(experience.is_current ?? false))
                  }
                  className="flex-row items-center gap-2"
                >
                  <View
                    className={`h-4 w-4 rounded border ${experience.is_current ? "bg-primary border-primary" : "border-border bg-background"}`}
                  />
                  <Text className="text-sm text-foreground">目前仍在職</Text>
                </Pressable>

                <Pressable onPress={() => removeExperience(index)}>
                  <Text className="text-sm text-destructive">刪除此工作經驗</Text>
                </Pressable>
              </View>
            ))}

            <Button variant="outline" onPress={addExperience}>
              <Text>新增工作經驗</Text>
            </Button>
          </View>
        </Section>

        <Section title="外部連結">
          <View className="px-4 py-3 gap-4">
            {formValue.externalLinks.map((link, index) => (
              <View key={`link-${index}`} className="rounded-xl border border-border p-3 gap-2">
                <TextInput
                  value={link.label}
                  onChangeText={(value) => updateLink(index, "label", value)}
                  placeholder="連結名稱（例如 GitHub）"
                  className="h-10 rounded-md border border-border bg-background px-3 text-foreground"
                />
                <TextInput
                  value={link.url}
                  onChangeText={(value) => updateLink(index, "url", value)}
                  placeholder="https://..."
                  autoCapitalize="none"
                  className="h-10 rounded-md border border-border bg-background px-3 text-foreground"
                />
                <Pressable onPress={() => removeLink(index)}>
                  <Text className="text-sm text-destructive">刪除此連結</Text>
                </Pressable>
              </View>
            ))}

            <Button variant="outline" onPress={addLink}>
              <Text>新增外部連結</Text>
            </Button>
          </View>
        </Section>

        <Section title="期望薪資">
          <View className="px-4 py-3 gap-3">
            <Pressable
              onPress={() =>
                setFormValue((prev) => ({
                  ...prev,
                  expectedSalaryEnabled: !prev.expectedSalaryEnabled,
                }))
              }
              className="flex-row items-center gap-2"
            >
              <View
                className={`h-4 w-4 rounded border ${formValue.expectedSalaryEnabled ? "bg-primary border-primary" : "border-border bg-background"}`}
              />
              <Text className="text-sm text-foreground">啟用期望薪資</Text>
            </Pressable>

            {formValue.expectedSalaryEnabled && (
              <>
                <View className="flex-row gap-2">
                  <TextInput
                    value={formValue.expectedSalaryMin}
                    onChangeText={(value) =>
                      setFormValue((prev) => ({
                        ...prev,
                        expectedSalaryMin: value,
                      }))
                    }
                    keyboardType="number-pad"
                    placeholder="最低薪資"
                    className="flex-1 h-10 rounded-md border border-border bg-background px-3 text-foreground"
                  />
                  <TextInput
                    value={formValue.expectedSalaryMax}
                    onChangeText={(value) =>
                      setFormValue((prev) => ({
                        ...prev,
                        expectedSalaryMax: value,
                      }))
                    }
                    keyboardType="number-pad"
                    placeholder="最高薪資"
                    className="flex-1 h-10 rounded-md border border-border bg-background px-3 text-foreground"
                  />
                </View>

                <TextInput
                  value={formValue.expectedSalaryCurrency}
                  onChangeText={(value) =>
                    setFormValue((prev) => ({
                      ...prev,
                      expectedSalaryCurrency: value.toUpperCase(),
                    }))
                  }
                  autoCapitalize="characters"
                  maxLength={3}
                  placeholder="幣別 (TWD)"
                  className="h-10 rounded-md border border-border bg-background px-3 text-foreground"
                />
              </>
            )}
          </View>
        </Section>

        <Section title="工作時間">
          <View className="px-4 py-3 gap-3">
            <Pressable
              onPress={() =>
                setFormValue((prev) => ({
                  ...prev,
                  workTimeRangeEnabled: !prev.workTimeRangeEnabled,
                }))
              }
              className="flex-row items-center gap-2"
            >
              <View
                className={`h-4 w-4 rounded border ${formValue.workTimeRangeEnabled ? "bg-primary border-primary" : "border-border bg-background"}`}
              />
              <Text className="text-sm text-foreground">啟用工作時間設定</Text>
            </Pressable>

            {formValue.workTimeRangeEnabled && (
              <>
                <View className="flex-row gap-2">
                  <TextInput
                    value={formValue.workTimeRange.start_time ?? ""}
                    onChangeText={(value) =>
                      setFormValue((prev) => ({
                        ...prev,
                        workTimeRange: {
                          ...prev.workTimeRange,
                          start_time: value,
                        },
                      }))
                    }
                    placeholder="開始時間 HH:MM"
                    className="flex-1 h-10 rounded-md border border-border bg-background px-3 text-foreground"
                  />
                  <TextInput
                    value={formValue.workTimeRange.end_time ?? ""}
                    onChangeText={(value) =>
                      setFormValue((prev) => ({
                        ...prev,
                        workTimeRange: {
                          ...prev.workTimeRange,
                          end_time: value,
                        },
                      }))
                    }
                    placeholder="結束時間 HH:MM"
                    className="flex-1 h-10 rounded-md border border-border bg-background px-3 text-foreground"
                  />
                </View>

                <View className="flex-row flex-wrap gap-2">
                  {WORK_TIME_TYPE_OPTIONS.map((option) => (
                    <Pressable
                      key={option.value}
                      onPress={() =>
                        setFormValue((prev) => ({
                          ...prev,
                          workTimeRange: {
                            ...prev.workTimeRange,
                            work_time_type: option.value as WorkTimeType,
                          },
                        }))
                      }
                      className={`rounded-full border px-3 py-1.5 ${formValue.workTimeRange.work_time_type === option.value ? "border-primary bg-primary/10" : "border-border bg-background"}`}
                    >
                      <Text
                        className={`text-sm ${formValue.workTimeRange.work_time_type === option.value ? "text-primary" : "text-foreground"}`}
                      >
                        {option.label}
                      </Text>
                    </Pressable>
                  ))}
                </View>
              </>
            )}
          </View>
        </Section>
        </ScrollView>
      )}
    </>
  );
}
