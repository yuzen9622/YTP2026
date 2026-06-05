import { useMemo } from "react";
import { Linking, Pressable, ScrollView, View } from "react-native";
import { Stack, router, useLocalSearchParams } from "expo-router";
import { BadgeCheck } from "lucide-react-native";
import { toast } from "sonner-native";

import { Avatar, AvatarFallback, AvatarImage } from "@/components/ui/avatar";
import { Card } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Text } from "@/components/ui/text";
import { useUserStore } from "@/store/user-store";
import type { LanguageProficiency } from "@/types";

import { useResumesQuery } from "../hooks/use-resumes";
import type { Resume, WorkTimeType } from "../types";

const WORK_TIME_TYPE_LABEL: Record<WorkTimeType, string> = {
  full_time: "全職",
  part_time: "兼職",
  internship: "實習",
  freelance: "接案",
};

const CAREER_LABEL: Record<string, string> = {
  employed: "在職中",
  unemployed: "待業中",
  student: "在學中",
};

const EDUCATION_LABEL: Record<string, string> = {
  high_school: "高中職",
  associate: "專科",
  bachelor: "學士",
  master: "碩士",
  phd: "博士",
};

const LANGUAGE_PROFICIENCY_LABEL: Record<LanguageProficiency, string> = {
  native: "母語",
  advanced: "進階",
  upper_intermediate: "中高",
  intermediate: "中階",
  basic: "基礎",
};

function formatDate(dateString: string): string {
  const date = new Date(dateString);
  if (Number.isNaN(date.getTime())) {
    return "--";
  }

  return new Intl.DateTimeFormat("zh-TW", {
    year: "numeric",
    month: "2-digit",
    day: "2-digit",
  }).format(date);
}

function formatExpectedSalary(resume: Resume): string {
  const salary = resume.expected_salary;
  if (!salary) {
    return "未提供";
  }

  const currency = salary.currency || "TWD";
  return `${salary.min.toLocaleString("zh-TW")} - ${salary.max.toLocaleString("zh-TW")} ${currency}`;
}

function formatWorkTime(resume: Resume): string {
  const workTimeRange = resume.work_time_range;
  if (!workTimeRange) {
    return "未設定";
  }

  const typeLabel =
    WORK_TIME_TYPE_LABEL[workTimeRange.work_time_type] ?? "未設定";
  if (workTimeRange.start_time || workTimeRange.end_time) {
    return `${typeLabel} (${workTimeRange.start_time ?? "--"} - ${workTimeRange.end_time ?? "--"})`;
  }

  return typeLabel;
}

function getAgeLabel(age: number | null, birthDate: string | null): string {
  if (typeof age === "number") {
    return `${age}歲`;
  }

  if (!birthDate) {
    return "--";
  }

  const date = new Date(birthDate);
  if (Number.isNaN(date.getTime())) {
    return "--";
  }

  const now = new Date();
  let years = now.getFullYear() - date.getFullYear();
  const hasHadBirthday =
    now.getMonth() > date.getMonth() ||
    (now.getMonth() === date.getMonth() && now.getDate() >= date.getDate());

  if (!hasHadBirthday) {
    years -= 1;
  }

  return years >= 0 ? `${years}歲` : "--";
}

async function openExternalUrl(url: string) {
  try {
    let normalizedUrl = url.trim();
    if (!/^https?:\/\//i.test(normalizedUrl)) {
      normalizedUrl = `https://${normalizedUrl}`;
    }

    const canOpen = await Linking.canOpenURL(normalizedUrl);
    if (!canOpen) {
      toast.error("無法開啟連結");
      return;
    }

    await Linking.openURL(normalizedUrl);
  } catch {
    toast.error("開啟連結失敗");
  }
}

function SectionHeader({
  title,
  rightAction,
}: {
  title: string;
  rightAction?: React.ReactNode;
}) {
  return (
    <View className="border-b border-[#D9D9D9] px-4 py-3 flex-row items-center justify-between">
      <Text className="text-[16px] font-bold text-[#111111]">{title}</Text>
      {rightAction}
    </View>
  );
}

function InfoRow({ label, value }: { label: string; value: string }) {
  return (
    <View className="flex-row items-start gap-3 py-1">
      <Text className="w-[86px] text-[13px] font-semibold text-[#2F2F2F]">
        {label}
      </Text>
      <Text className="flex-1 text-[13px] text-[#1F1F1F] leading-5">
        {value}
      </Text>
    </View>
  );
}

function RightAction({
  text,
  onPress,
}: {
  text: string;
  onPress?: () => void;
}) {
  return (
    <Pressable onPress={onPress} className="px-2 py-1 active:opacity-70">
      <Text className="text-[12px] text-[#666666]">{text}</Text>
    </Pressable>
  );
}

export function ResumeDetailScreen() {
  const { resumeId } = useLocalSearchParams<{ resumeId?: string }>();
  const resumesQuery = useResumesQuery();
  const user = useUserStore((state) => state.user);

  const resume = useMemo(
    () => resumesQuery.data?.find((item) => item.id === resumeId),
    [resumeId, resumesQuery.data],
  );

  const isMissingResume =
    Boolean(resumeId) && !resumesQuery.isLoading && !resume;

  const careerLabel = user?.career
    ? (CAREER_LABEL[user.career] ?? user.career)
    : "--";
  const educationLabel = user?.educationLevel
    ? (EDUCATION_LABEL[user.educationLevel] ?? user.educationLevel)
    : "--";

  return (
    <>
      <Stack.Screen
        options={{
          title: resume?.title || "履歷詳情",
          headerLargeTitle: false,
        }}
      />

      <ScrollView
        contentInsetAdjustmentBehavior="automatic"
        className="flex-1 bg-[#EDEDED]"
        contentContainerClassName="pb-10"
      >
        {resumesQuery.isLoading && (
          <Card className="rounded-none border-0 border-b border-[#D9D9D9] p-4">
            <Text className="text-[#666666]">履歷載入中...</Text>
          </Card>
        )}

        {resumesQuery.isError && (
          <Card className="rounded-none border-0 border-b border-[#D9D9D9] p-4 gap-2">
            <Text className="text-destructive">載入履歷失敗，請稍後再試</Text>
            <Button variant="outline" onPress={() => resumesQuery.refetch()}>
              <Text>重新載入</Text>
            </Button>
          </Card>
        )}

        {isMissingResume && (
          <Card className="rounded-none border-0 border-b border-[#D9D9D9] p-4 gap-3">
            <Text className="text-destructive">
              找不到此履歷，可能已被刪除。
            </Text>
            <Button variant="outline" onPress={() => router.back()}>
              <Text>返回管理履歷</Text>
            </Button>
          </Card>
        )}

        {resume && (
          <>
            <View className="bg-white border-b border-[#D9D9D9]">
              <View className="h-[110px] bg-[#E6D8CC] overflow-hidden">
                <View className="absolute left-[-28px] top-[-24px] h-28 w-28 rounded-full bg-[#F0E6DD]" />
                <View className="absolute left-[120px] top-[0px] h-[110px] w-[72px] bg-[#E1D2C4]" />
                <View className="absolute right-[80px] top-[0px] h-[110px] w-[72px] bg-[#E1D2C4]" />
                <View className="absolute right-[-36px] top-[-22px] h-32 w-32 rounded-full bg-[#DCC9BA]" />
                <View className="absolute left-[46px] top-[24px] h-3 w-3 rounded-full bg-[#EAB67E]" />
                <View className="absolute left-[156px] top-[18px] h-2 w-2 rounded-full bg-[#F08C30]" />
                <View className="absolute left-[238px] top-[56px] h-2.5 w-2.5 rounded-full bg-[#E3A777]" />
              </View>

              <View className="px-5 pb-5">
                <View className="mt-[-36px] flex-row items-end justify-between">
                  <View className="flex-row items-end flex-1 gap-3">
                    <Avatar
                      alt={user?.name || "使用者頭像"}
                      className="size-[72px] border-[3px] border-white bg-[#EEE2D9]"
                    >
                      <AvatarImage
                        source={
                          user?.avatar_url
                            ? { uri: user.avatar_url }
                            : undefined
                        }
                      />
                      <AvatarFallback>
                        <Text className="text-[24px] font-semibold text-[#7B5F4B]">
                          {(user?.name?.trim()?.[0] || "履").toUpperCase()}
                        </Text>
                      </AvatarFallback>
                    </Avatar>
                    <View className="flex-1 pb-1">
                      <Text className="text-[28px] font-extrabold text-[#121212]">
                        {user?.name || "未命名使用者"}
                      </Text>
                    </View>
                  </View>

                  <View className="flex-row items-center">
                    <RightAction
                      text="編輯"
                      onPress={() =>
                        router.push({
                          pathname: "/(tabs)/profile/edit-resume-screen",
                          params: { resumeId: resume.id },
                        })
                      }
                    />
                    <RightAction
                      text="回履歷"
                      onPress={() =>
                        router.push("/(tabs)/profile/manage-resumes-screen")
                      }
                    />
                  </View>
                </View>

                <View className="gap-2 mt-3">
                  <Text className="text-[13px] text-[#333333]">
                    {careerLabel}
                  </Text>
                  <Text className="text-[14px] leading-6 text-[#1F1F1F]">
                    {resume.summary?.trim() ||
                      user?.bio?.trim() ||
                      "尚未填寫自我介紹"}
                  </Text>
                </View>
              </View>
            </View>

            <Card className="rounded-none border-0 border-b border-[#D9D9D9] bg-[#F7F7F7]">
              <SectionHeader title="個人資料" />
              <View className="px-5 py-4">
                <InfoRow
                  label="基本資料"
                  value={`性別 ${user.gender === "male" ? "男" : "女"}、 ${getAgeLabel(user?.age ?? null, user?.birth_date ?? null)}`}
                />
                <InfoRow label="就業狀態" value={careerLabel} />
                <InfoRow label="主要手機" value={user?.phone || "--"} />
                <InfoRow label="E-mail" value={user?.email || "--"} />
                <InfoRow
                  label="通訊地址"
                  value={user?.registered_address || "--"}
                />
              </View>
            </Card>

            <Card className="mt-2 rounded-none border-0 border-b border-[#D9D9D9] bg-[#F7F7F7]">
              <SectionHeader
                title="學歷"
                rightAction={
                  <RightAction
                    text="新增"
                    onPress={() =>
                      router.push("/(tabs)/profile/edit-profile-screen")
                    }
                  />
                }
              />
              <View className="gap-2 px-5 py-4">
                <Text className="text-[12px] text-[#666666]">
                  履歷目前未獨立儲存學歷欄位，先展示個人資料中的學歷。
                </Text>
                <Text className="text-[15px] font-bold text-[#1F1F1F]">
                  {educationLabel}
                </Text>
                <Text className="text-[13px] text-[#444444]">
                  {careerLabel}
                </Text>
              </View>
            </Card>

            <Card className="mt-2 rounded-none border-0 border-b border-[#D9D9D9] bg-[#F7F7F7]">
              <SectionHeader title="專長" />
              <View className="gap-3 px-5 py-4">
                <Text className="text-[14px] leading-6 text-[#1F1F1F]">
                  {resume.summary?.trim() || "尚未填寫專長描述"}
                </Text>

                <View className="gap-2">
                  <Text className="text-[13px] font-semibold text-[#2F2F2F]">
                    技能
                  </Text>
                  {resume.skills && resume.skills.length > 0 ? (
                    <View className="flex-row flex-wrap gap-2">
                      {resume.skills.map((skill, index) => (
                        <View
                          key={`${skill.name}-${index}`}
                          className="rounded-sm border border-[#CDCDCD] bg-white px-2.5 py-1"
                        >
                          <Text className="text-[12px] text-[#1F1F1F]">
                            {skill.name}
                          </Text>
                        </View>
                      ))}
                    </View>
                  ) : (
                    <Text className="text-[13px] text-[#666666]">
                      尚未填寫技能
                    </Text>
                  )}
                </View>

                <View className="gap-2">
                  <Text className="text-[13px] font-semibold text-[#2F2F2F]">
                    作品 / 外部連結
                  </Text>
                  {resume.external_links && resume.external_links.length > 0 ? (
                    <View className="gap-1.5">
                      {resume.external_links.map((link, index) => (
                        <Pressable
                          key={`${link.url}-${index}`}
                          onPress={() => openExternalUrl(link.url)}
                          className="active:opacity-70"
                        >
                          <Text className="text-[13px] text-[#005FAD] underline">
                            {link.label || link.url}
                          </Text>
                        </Pressable>
                      ))}
                    </View>
                  ) : (
                    <Text className="text-[13px] text-[#666666]">
                      尚未提供外部連結
                    </Text>
                  )}
                </View>
              </View>
            </Card>

            <Card className="mt-2 rounded-none border-0 border-b border-[#D9D9D9] bg-[#F7F7F7]">
              <SectionHeader title="證照" />
              <View className="gap-2 px-5 py-4">
                {user?.tags && user.tags.length > 0 ? (
                  user.tags.map((tag, index) => (
                    <View
                      key={`${tag}-${index}`}
                      className="flex-row items-center gap-2"
                    >
                      <BadgeCheck size={14} color="#666666" />
                      <Text className="text-[13px] text-[#2A2A2A]">{tag}</Text>
                    </View>
                  ))
                ) : (
                  <Text className="text-[13px] text-[#666666]">
                    尚未填寫證照資料
                  </Text>
                )}
              </View>
            </Card>

            <Card className="mt-2 rounded-none border-0 border-b border-[#D9D9D9] bg-[#F7F7F7]">
              <SectionHeader title="求職條件" />
              <View className="px-5 py-4">
                <InfoRow
                  label="希望待遇"
                  value={formatExpectedSalary(resume)}
                />
                <InfoRow label="上班時段" value={formatWorkTime(resume)} />
                <InfoRow label="希望地點" value={user?.location || "--"} />
                <InfoRow label="希望職務" value={resume.title || "--"} />
              </View>
            </Card>

            <Card className="mt-2 rounded-none border-0 border-b border-[#D9D9D9] bg-[#F7F7F7]">
              <SectionHeader title="工作經驗" />
              <View className="gap-3 px-5 py-4">
                {resume.work_experiences &&
                resume.work_experiences.length > 0 ? (
                  resume.work_experiences.map((experience, index) => (
                    <View
                      key={`${experience.company}-${index}`}
                      className="gap-1 pb-3 border-b border-[#DFDFDF] last:border-b-0 last:pb-0"
                    >
                      <Text className="text-[15px] font-bold text-[#1F1F1F]">
                        {experience.position || "未填寫職位"}
                      </Text>
                      <Text className="text-[13px] text-[#3A3A3A]">
                        {experience.company || "未填寫公司"}
                      </Text>
                      <Text className="text-[12px] text-[#666666]">
                        {experience.start_date || "--"} -{" "}
                        {experience.is_current
                          ? "至今"
                          : experience.end_date || "--"}
                      </Text>
                      {experience.description?.trim() ? (
                        <Text className="text-[13px] leading-6 text-[#222222]">
                          {experience.description}
                        </Text>
                      ) : null}
                    </View>
                  ))
                ) : (
                  <Text className="text-[13px] text-[#666666]">
                    無工作經驗資料
                  </Text>
                )}
              </View>
            </Card>

            <Card className="mt-2 rounded-none border-0 border-b border-[#D9D9D9] bg-[#F7F7F7]">
              <SectionHeader title="語文能力" />
              <View className="gap-2 px-5 py-4">
                {user?.language_skills && user.language_skills.length > 0 ? (
                  user.language_skills.map((item, index) => (
                    <View
                      key={`${item.language}-${index}`}
                      className="flex-row items-center justify-between border-b border-[#DFDFDF] pb-2 last:border-b-0 last:pb-0"
                    >
                      <Text className="text-[14px] font-semibold text-[#1F1F1F]">
                        {item.language || "未命名語言"}
                      </Text>
                      <Text className="text-[13px] text-[#555555]">
                        {LANGUAGE_PROFICIENCY_LABEL[item.proficiency] ||
                          item.proficiency}
                      </Text>
                    </View>
                  ))
                ) : (
                  <Text className="text-[13px] text-[#666666]">
                    尚未填寫語文能力
                  </Text>
                )}
              </View>
            </Card>

            <View className="px-4 mt-3">
              <Text className="text-[12px] text-[#777777] text-right">
                最後更新於 {formatDate(resume.updated_at)}
              </Text>
            </View>
          </>
        )}
      </ScrollView>
    </>
  );
}
