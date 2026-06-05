import { useCallback, useMemo, useState } from "react";
import { Alert } from "react-native";
import { router } from "expo-router";
import { toast } from "sonner-native";

import { useUserStore } from "@/store/user-store";
import { useAgeSlider, useForm } from "@/hooks";
import { updateProfile } from "../api/user-profile-api";
import { MAX_BIO_LENGTH } from "../constant/profile-options";

import type { CareerStatus } from "@/types";

type FormValues = {
  name: string;
  bio: string;
  email: string;
  phone: string;
};

interface UseEditProfileReturn {
  values: FormValues;
  handleChange: <K extends keyof FormValues>(key: K, value: FormValues[K]) => void;
  loading: boolean;
  setLoading: (loading: boolean) => void;
  age: number;
  handleValueChange: (value: number) => void;
  career: CareerStatus | null | undefined;
  setCareer: (career: CareerStatus | null | undefined) => void;
  tags: string[];
  setTags: (tags: string[]) => void;
  isDirty: boolean;
  handleBack: () => void;
  handleSave: () => Promise<void>;
}

export function useEditProfile(): UseEditProfileReturn {
  const user = useUserStore((state) => state.user);
  const updateUserProfile = useUserStore((state) => state.updateProfile);

  const { age, handleValueChange } = useAgeSlider(user?.age ?? 22);
  const { values, handleChange, loading, setLoading } = useForm<FormValues>({
    name: user?.name ?? "",
    bio: user?.bio ?? "",
    email: user?.email ?? "",
    phone: user?.phone ?? "",
  });

  const [career, setCareer] = useState<CareerStatus | null | undefined>(
    user?.career,
  );
  const [tags, setTags] = useState<string[]>(user?.tags ?? []);

  const isDirty = useMemo(() => {
    return (
      values.name !== (user?.name ?? "") ||
      values.bio !== (user?.bio ?? "") ||
      values.email !== (user?.email ?? "") ||
      values.phone !== (user?.phone ?? "") ||
      age !== (user?.age ?? 22) ||
      career !== user?.career ||
      JSON.stringify(tags) !== JSON.stringify(user?.tags ?? [])
    );
  }, [values, age, career, tags, user]);

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

    setLoading(true);
    try {
      const payload = {
        name: values.name.trim(),
        bio: values.bio.trim(),
        email: values.email.trim() || null,
        phone: values.phone.trim() || null,
        age,
        career: career ?? undefined,
        tags,
      };

      await updateProfile(user.id, payload);
      updateUserProfile(payload);

      toast.success("已儲存個人資料");
      router.back();
    } catch {
      // API interceptor handles errors
    } finally {
      setLoading(false);
    }
  }, [user, values, age, career, tags, setLoading, updateUserProfile, isDirty]);

  return {
    values,
    handleChange,
    loading,
    setLoading,
    age,
    handleValueChange,
    career,
    setCareer,
    tags,
    setTags,
    isDirty,
    handleBack,
    handleSave,
  };
}