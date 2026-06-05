import { useCallback, useMemo, useState } from "react";
import {
  Alert,
  Platform,
  Pressable,
  ScrollView,
  Switch,
  TextInput,
  View,
} from "react-native";
import DateTimePicker, {
  type DateTimePickerEvent,
} from "@react-native-community/datetimepicker";
import { Stack, router } from "expo-router";
import { toast } from "sonner-native";

import { useUserStore } from "@/store/user-store";
import { useForm } from "@/hooks";
import { updateProfile } from "../api/user-profile-api";

import {
  CAREER_STATUS_OPTIONS,
  MAX_BIO_LENGTH,
} from "../constant/profile-options";
import { TagInput } from "./tag-input";
import { Section } from "./section";
import { RadioGroup } from "./radio-group";

import type {
  CareerStatus,
  Gender,
  LanguageProficiency,
  LanguageSkill,
} from "@/types";

import { Label } from "@/components/ui/label";

import { Text } from "@/components/ui/text";
import { ChevronLeft } from "lucide-react-native";
import { colors } from "@/lib/colors.ios";

const URL_REGEX = /^https?:\/\//i;
const MAX_LANGUAGE_SKILLS = 10;

const LANGUAGE_PROFICIENCY_OPTIONS: {
  label: string;
  value: LanguageProficiency;
}[] = [
  { label: "母語", value: "native" },
  { label: "進階", value: "advanced" },
  { label: "中高", value: "upper_intermediate" },
  { label: "中階", value: "intermediate" },
  { label: "基礎", value: "basic" },
];

const GENDER_OPTIONS: { label: string; value: Gender }[] = [
  { label: "男性", value: "male" },
  { label: "女性", value: "female" },
  { label: "不公開", value: "hidden" },
];

function normalizeLanguageSkills(skills: LanguageSkill[]): LanguageSkill[] {
  return skills
    .map((item) => ({
      language: item.language.trim().toLowerCase(),
      proficiency: item.proficiency,
    }))
    .filter((item) => item.language.length > 0)
    .slice(0, MAX_LANGUAGE_SKILLS);
}

function formatDateToYmd(date: Date): string {
  const year = date.getFullYear();
  const month = String(date.getMonth() + 1).padStart(2, "0");
  const day = String(date.getDate()).padStart(2, "0");
  return `${year}-${month}-${day}`;
}

function parseBirthDate(value: string): Date | null {
  if (!value) return null;

  const [yearString, monthString, dayString] = value.split("-");
  if (!yearString || !monthString || !dayString) return null;

  const year = Number(yearString);
  const month = Number(monthString);
  const day = Number(dayString);

  if (
    !Number.isInteger(year) ||
    !Number.isInteger(month) ||
    !Number.isInteger(day)
  ) {
    return null;
  }

  const date = new Date(year, month - 1, day);
  if (
    date.getFullYear() !== year ||
    date.getMonth() !== month - 1 ||
    date.getDate() !== day
  ) {
    return null;
  }

  return date;
}

function calculateAgeFromBirthDate(value: string): number | null {
  const birthDate = parseBirthDate(value);
  if (!birthDate) {
    return null;
  }

  const today = new Date();
  let age = today.getFullYear() - birthDate.getFullYear();

  const hasHadBirthdayThisYear =
    today.getMonth() > birthDate.getMonth() ||
    (today.getMonth() === birthDate.getMonth() &&
      today.getDate() >= birthDate.getDate());

  if (!hasHadBirthdayThisYear) {
    age -= 1;
  }

  return age >= 0 ? age : null;
}

export function EditProfileScreen() {
  const user = useUserStore((state) => state.user);
  const updateUserProfile = useUserStore((state) => state.updateProfile);

  const { values, handleChange, loading, setLoading } = useForm({
    name: user?.name ?? "",
    bio: user?.bio ?? "",
    email: user?.email ?? "",
    phone: user?.phone ?? "",
    birthDate: user?.birth_date ?? "",
    avatarUrl: user?.avatar_url ?? "",
    registeredAddress: user?.registered_address ?? "",
    residentialAddress: user?.residential_address ?? "",
  });

  const [showBirthDatePicker, setShowBirthDatePicker] = useState(false);
  const [career, setCareer] = useState<CareerStatus | null | undefined>(
    user?.career,
  );
  const [tags, setTags] = useState<string[]>(user?.tags ?? []);
  const [languageSkills, setLanguageSkills] = useState<LanguageSkill[]>(
    user?.language_skills ?? [],
  );
  const [gender, setGender] = useState<Gender | null | undefined>(user?.gender);
  const [isResidentialSameAsRegistered, setIsResidentialSameAsRegistered] =
    useState<boolean>(user?.is_residential_same_as_registered ?? false);

  const age = useMemo(
    () => calculateAgeFromBirthDate(values.birthDate),
    [values.birthDate],
  );

  const pickerDateValue = useMemo(
    () => parseBirthDate(values.birthDate) ?? new Date(2000, 0, 1),
    [values.birthDate],
  );

  const isDirty = useMemo(() => {
    const normalizedCurrentLanguageSkills =
      normalizeLanguageSkills(languageSkills);
    const normalizedOriginalLanguageSkills = normalizeLanguageSkills(
      user?.language_skills ?? [],
    );

    return (
      values.name !== (user?.name ?? "") ||
      values.bio !== (user?.bio ?? "") ||
      values.email !== (user?.email ?? "") ||
      values.phone !== (user?.phone ?? "") ||
      values.birthDate !== (user?.birth_date ?? "") ||
      values.avatarUrl !== (user?.avatar_url ?? "") ||
      values.registeredAddress !== (user?.registered_address ?? "") ||
      values.residentialAddress !== (user?.residential_address ?? "") ||
      career !== user?.career ||
      gender !== user?.gender ||
      isResidentialSameAsRegistered !==
        (user?.is_residential_same_as_registered ?? false) ||
      JSON.stringify(tags) !== JSON.stringify(user?.tags ?? []) ||
      JSON.stringify(normalizedCurrentLanguageSkills) !==
        JSON.stringify(normalizedOriginalLanguageSkills)
    );
  }, [
    values,
    user,
    career,
    tags,
    languageSkills,
    gender,
    isResidentialSameAsRegistered,
  ]);

  const handleBack = useCallback(() => {
    if (isDirty) {
      Alert.alert("放棄變更？", "有尚未儲存的變更，確定要離開嗎？", [
        { text: "繼續編輯", style: "cancel" },
        {
          text: "放棄變更",
          style: "destructive",
          onPress: () => router.back(),
        },
      ]);
    } else {
      router.back();
    }
  }, [isDirty]);

  const handleBirthDateChange = (
    event: DateTimePickerEvent,
    selectedDate?: Date,
  ) => {
    if (Platform.OS === "android") {
      setShowBirthDatePicker(false);
    }

    if (event.type !== "set" || !selectedDate) {
      return;
    }

    handleChange("birthDate", formatDateToYmd(selectedDate));
  };

  const handleAddLanguageSkill = () => {
    if (languageSkills.length >= MAX_LANGUAGE_SKILLS) {
      toast.error(`語言能力最多 ${MAX_LANGUAGE_SKILLS} 筆`);
      return;
    }

    setLanguageSkills((prev) => [
      ...prev,
      {
        language: "",
        proficiency: "intermediate",
      },
    ]);
  };

  const handleUpdateLanguageSkill = (
    index: number,
    patch: Partial<LanguageSkill>,
  ) => {
    setLanguageSkills((prev) =>
      prev.map((item, itemIndex) =>
        itemIndex === index ? { ...item, ...patch } : item,
      ),
    );
  };

  const handleRemoveLanguageSkill = (index: number) => {
    setLanguageSkills((prev) =>
      prev.filter((_, itemIndex) => itemIndex !== index),
    );
  };

  const handleSave = useCallback(async () => {
    if (!user?.id) return;
    if (!isDirty) {
      toast("目前沒有變更");
      return;
    }
    if (!values.name.trim()) {
      toast.error("請輸入名稱");
      return;
    }
    if (values.bio.length > MAX_BIO_LENGTH) {
      toast.error(`自我介紹不得超過 ${MAX_BIO_LENGTH} 字元`);
      return;
    }

    if (values.birthDate.trim() && !parseBirthDate(values.birthDate.trim())) {
      toast.error("生日格式無效，請重新選擇");
      return;
    }

    if (values.avatarUrl.trim() && !URL_REGEX.test(values.avatarUrl.trim())) {
      toast.error("頭貼網址需以 http:// 或 https:// 開頭");
      return;
    }

    const normalizedLanguageSkills = normalizeLanguageSkills(languageSkills);
    if (normalizedLanguageSkills.length > MAX_LANGUAGE_SKILLS) {
      toast.error(`語言能力最多 ${MAX_LANGUAGE_SKILLS} 筆`);
      return;
    }

    setLoading(true);
    try {
      const registeredAddress = values.registeredAddress.trim() || null;
      const residentialAddress = isResidentialSameAsRegistered
        ? registeredAddress
        : values.residentialAddress.trim() || null;

      const payload = {
        name: values.name.trim(),
        bio: values.bio.trim(),
        email: values.email.trim() || null,
        phone: values.phone.trim() || null,
        birth_date: values.birthDate.trim() || null,
        career: career ?? undefined,
        gender: gender ?? null,
        tags,
        avatar_url: values.avatarUrl.trim() || null,
        registered_address: registeredAddress,
        residential_address: residentialAddress,
        is_residential_same_as_registered: isResidentialSameAsRegistered,
        language_skills: normalizedLanguageSkills,
      };

      await updateProfile(user.id, payload);
      updateUserProfile({
        ...payload,
        age: age ?? null,
      });

      toast.success("已儲存個人資料");
      router.back();
    } catch {
      // API interceptor handles errors
    } finally {
      setLoading(false);
    }
  }, [
    user,
    values,
    career,
    gender,
    isResidentialSameAsRegistered,
    tags,
    languageSkills,
    setLoading,
    updateUserProfile,
    isDirty,
    age,
  ]);

  return (
    <>
      <Stack.Screen
        options={{
          title: "編輯個人資料",
          headerLeft: () => (
            <Pressable
              onPress={handleBack}
              className="items-center justify-center rounded-full shadow-sm w-9 h-9 active:opacity-70"
            >
              <ChevronLeft
                size={20}
                className="text-foreground"
                color={colors.foreground}
              />
            </Pressable>
          ),
          headerRight: () =>
            isDirty ? (
              <Pressable
                onPress={handleSave}
                disabled={loading}
                className="px-4 py-1.5 rounded-full active:opacity-70 flex-row items-center justify-center"
              >
                <Text className="font-semibold text-primary  text-[15px]">
                  {loading ? "儲存中" : "儲存"}
                </Text>
              </Pressable>
            ) : null,
        }}
      />
      <ScrollView
        contentInsetAdjustmentBehavior="automatic"
        className="flex-1 bg-[#F7F7F8]"
        contentContainerClassName="p-4 gap-6 pb-12"
      >
        <Section title="基本資訊">
          <View className="px-4 py-3 border-b border-border">
            <Label className="text-muted-foreground text-[13px] mb-1">
              顯示名稱
            </Label>
            <TextInput
              value={values.name}
              onChangeText={(v) => handleChange("name", v)}
              placeholder="輸入顯示名稱"
              className="h-10 px-0 bg-transparent rounded-none text-[16px] text-foreground"
            />
          </View>

          <View className="px-4 py-3 border-b border-border">
            <View className="flex-row items-center justify-between mb-1">
              <Label className="text-muted-foreground text-[13px]">
                自我介紹
              </Label>
              <Text
                className={`text-[12px] ${values.bio.length >= MAX_BIO_LENGTH ? "text-destructive font-medium" : "text-muted-foreground"}`}
              >
                {values.bio.length} / {MAX_BIO_LENGTH}
              </Text>
            </View>
            <TextInput
              value={values.bio}
              onChangeText={(v) => handleChange("bio", v)}
              placeholder="一句話介紹自己..."
              multiline
              numberOfLines={2}
              textAlignVertical="top"
              className="min-h-[56px] px-0 bg-transparent rounded-none text-[16px] text-foreground pt-2"
            />
          </View>

          <View className="px-4 py-3">
            <View className="flex-row items-center justify-between mb-1">
              <Label className="text-muted-foreground text-[13px]">年齡</Label>
              <Text className="text-muted-foreground text-[14px] font-medium">
                {age !== null ? `${age} 歲` : "請先選擇生日"}
              </Text>
            </View>
            <Text className="text-[12px] text-muted-foreground">
              年齡會由出生年月日自動計算
            </Text>
          </View>
        </Section>

        <Section title="學業與身份">
          <View className="px-4 py-3 border-b border-border">
            <Label className="text-muted-foreground text-[13px] mb-3">
              身份類別
            </Label>
            <RadioGroup
              options={CAREER_STATUS_OPTIONS}
              value={career}
              onChange={(v) => setCareer(v as CareerStatus)}
            />
          </View>

          <View className="px-4 py-3">
            <Label className="text-muted-foreground text-[13px] mb-3">
              性別
            </Label>
            <RadioGroup
              options={GENDER_OPTIONS}
              value={gender}
              onChange={(v) => setGender(v as Gender)}
            />
          </View>
        </Section>

        <Section title="聯絡方式">
          <View className="px-4 py-3 border-b border-border">
            <Label className="text-muted-foreground text-[13px] mb-1">
              Email
            </Label>
            <TextInput
              value={values.email}
              onChangeText={(v) => handleChange("email", v)}
              placeholder="輸入 Email"
              keyboardType="email-address"
              autoCapitalize="none"
              className="h-10 px-0 bg-transparent border-0 rounded-none text-[16px] text-foreground"
            />
          </View>

          <View className="px-4 py-3">
            <Label className="text-muted-foreground text-[13px] mb-1">
              手機號碼
            </Label>
            <TextInput
              value={values.phone}
              onChangeText={(v) => handleChange("phone", v)}
              placeholder="+886 912 345 678"
              keyboardType="phone-pad"
              className="h-10 px-0 bg-transparent border-0 rounded-none text-[16px] text-foreground"
            />
          </View>
        </Section>

        <Section title="附加資料">
          <View className="gap-2 px-4 py-3 border-b border-border">
            <Label className="text-muted-foreground text-[13px] mb-1">
              出生年月日
            </Label>

            <Pressable
              onPress={() => setShowBirthDatePicker(true)}
              className="justify-center h-10 px-3 border rounded-md border-border bg-background"
            >
              <Text className="text-[16px] text-foreground">
                {values.birthDate || "請選擇生日"}
              </Text>
            </Pressable>

            {values.birthDate ? (
              <Pressable onPress={() => handleChange("birthDate", "")}>
                <Text className="text-[12px] text-destructive">清除生日</Text>
              </Pressable>
            ) : null}

            {showBirthDatePicker ? (
              <DateTimePicker
                value={pickerDateValue}
                mode="date"
                display={"spinner"}
                maximumDate={new Date()}
                onChange={handleBirthDateChange}
              />
            ) : null}
          </View>

          <View className="px-4 py-3">
            <Label className="text-muted-foreground text-[13px] mb-1">
              頭貼網址
            </Label>
            <TextInput
              value={values.avatarUrl}
              onChangeText={(v) => handleChange("avatarUrl", v)}
              placeholder="https://example.com/avatar.jpg"
              autoCapitalize="none"
              className="h-10 px-0 bg-transparent border-0 rounded-none text-[16px] text-foreground"
            />
          </View>
        </Section>

        <Section title="地址資訊">
          <View className="px-4 py-3 border-b border-border">
            <Label className="text-muted-foreground text-[13px] mb-1">
              戶籍地址
            </Label>
            <TextInput
              value={values.registeredAddress}
              onChangeText={(v) => handleChange("registeredAddress", v)}
              placeholder="輸入戶籍地址"
              className="h-10 px-0 bg-transparent border-0 rounded-none text-[16px] text-foreground"
            />
          </View>

          <View className="px-4 py-3 border-b border-border">
            <View className="flex-row items-center justify-between">
              <View className="flex-1 pr-3">
                <Label className="text-muted-foreground text-[13px] mb-1">
                  居住地址同戶籍
                </Label>
                <Text className="text-[12px] text-muted-foreground">
                  開啟後，居住地址會與戶籍地址一致
                </Text>
              </View>

              <Switch
                value={isResidentialSameAsRegistered}
                onValueChange={setIsResidentialSameAsRegistered}
                trackColor={{
                  false: "#CBD5E1",
                  true: "#F472B6",
                }}
                thumbColor={Platform.OS === "android" ? "#FFFFFF" : undefined}
              />
            </View>
          </View>

          <View className="px-4 py-3">
            <Label className="text-muted-foreground text-[13px] mb-1">
              居住地址
            </Label>
            <TextInput
              value={
                isResidentialSameAsRegistered
                  ? values.registeredAddress
                  : values.residentialAddress
              }
              onChangeText={(v) => handleChange("residentialAddress", v)}
              placeholder="輸入居住地址"
              editable={!isResidentialSameAsRegistered}
              className="h-10 px-0 bg-transparent border-0 rounded-none text-[16px] text-foreground"
            />
          </View>
        </Section>

        <Section title="語言能力">
          <View className="gap-3 px-4 py-3">
            {languageSkills.map((skill, index) => (
              <View
                key={`language-skill-${index}`}
                className="gap-2 p-3 border border-border rounded-xl"
              >
                <TextInput
                  value={skill.language}
                  onChangeText={(value) =>
                    handleUpdateLanguageSkill(index, { language: value })
                  }
                  placeholder="語言代碼，例如 en / ja / zh"
                  autoCapitalize="none"
                  maxLength={10}
                  className="h-10 px-3 border rounded-md border-border bg-background text-foreground"
                />

                <View className="flex-row flex-wrap gap-2">
                  {LANGUAGE_PROFICIENCY_OPTIONS.map((option) => (
                    <Pressable
                      key={`${option.value}-${index}`}
                      onPress={() =>
                        handleUpdateLanguageSkill(index, {
                          proficiency: option.value,
                        })
                      }
                      className={`rounded-full border px-3 py-1.5 ${skill.proficiency === option.value ? "border-primary bg-primary/10" : "border-border bg-background"}`}
                    >
                      <Text
                        className={`text-[12px] ${skill.proficiency === option.value ? "text-primary" : "text-foreground"}`}
                      >
                        {option.label}
                      </Text>
                    </Pressable>
                  ))}
                </View>

                <Pressable onPress={() => handleRemoveLanguageSkill(index)}>
                  <Text className="text-[13px] text-destructive">
                    刪除此語言
                  </Text>
                </Pressable>
              </View>
            ))}

            <Pressable
              onPress={handleAddLanguageSkill}
              className="items-center justify-center py-2.5 border border-border rounded-xl bg-background"
            >
              <Text className="text-[14px] font-medium text-foreground">
                新增語言能力
              </Text>
            </Pressable>

            <Text className="text-[12px] text-muted-foreground text-right">
              {normalizeLanguageSkills(languageSkills).length} /{" "}
              {MAX_LANGUAGE_SKILLS}
            </Text>
          </View>
        </Section>

        <Section title="個人偏好">
          <View className="px-4 py-3">
            <View className="flex-row items-center justify-between mb-3">
              <Label className="text-muted-foreground text-[13px]">
                興趣標籤
              </Label>
              <Text className="text-[12px] text-muted-foreground">
                {tags.length} 個
              </Text>
            </View>
            <TagInput tags={tags} onChange={setTags} />
          </View>
        </Section>
      </ScrollView>
    </>
  );
}
