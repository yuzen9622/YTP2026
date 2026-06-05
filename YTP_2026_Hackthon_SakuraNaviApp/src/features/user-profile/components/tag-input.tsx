import React, { useState } from "react";
import { View, Pressable } from "react-native";
import { X } from "lucide-react-native";
import { Input } from "@/components/ui/input";
import { Text } from "@/components/ui/text";
import {
  DEFAULT_TAG_OPTIONS,
  MAX_TAGS,
  MAX_TAG_LENGTH,
} from "../constant/profile-options";

interface TagInputProps {
  tags: string[];
  onChange: (tags: string[]) => void;
}

export function TagInput({ tags, onChange }: TagInputProps) {
  const [inputValue, setInputValue] = useState("");

  const handleAddTagValue = (value: string) => {
    const trimmed = value.trim();
    if (!trimmed) return;

    if (tags.length >= MAX_TAGS) return;
    if (trimmed.length > MAX_TAG_LENGTH) return;
    if (tags.includes(trimmed)) {
      return;
    }

    onChange([...tags, trimmed]);
  };

  const handleAddTag = () => {
    handleAddTagValue(inputValue);
    setInputValue("");
  };

  const handleRemoveTag = (indexToRemove: number) => {
    onChange(tags.filter((_, index) => index !== indexToRemove));
  };

  return (
    <View className="gap-3">
      <View className="flex-row items-center gap-2">
        <Input
          className="flex-1 bg-muted/30"
          placeholder="輸入標籤並按下新增"
          value={inputValue}
          onChangeText={setInputValue}
          onSubmitEditing={handleAddTag}
          returnKeyType="done"
        />
        <Pressable
          onPress={handleAddTag}
          disabled={!inputValue.trim() || tags.length >= MAX_TAGS}
          className="items-center justify-center p-3 rounded-xl bg-primary disabled:opacity-50"
        >
          <Text className="font-medium text-primary-foreground">新增</Text>
        </Pressable>
      </View>

      <View className="gap-2">
        <Text className="text-[12px] text-muted-foreground">預設標籤</Text>
        <View className="flex-row flex-wrap gap-2">
          {DEFAULT_TAG_OPTIONS.map((presetTag) => {
            const isSelected = tags.includes(presetTag);
            const isDisabled = isSelected || tags.length >= MAX_TAGS;

            return (
              <Pressable
                key={presetTag}
                onPress={() => handleAddTagValue(presetTag)}
                disabled={isDisabled}
                className={`px-3 py-1.5 rounded-full border ${
                  isSelected
                    ? "bg-primary/15 border-primary/30"
                    : "bg-background border-border"
                } ${isDisabled ? "opacity-50" : "active:opacity-80"}`}
              >
                <Text
                  className={`text-[13px] ${
                    isSelected ? "text-primary font-medium" : "text-foreground"
                  }`}
                >
                  {presetTag}
                </Text>
              </Pressable>
            );
          })}
        </View>
      </View>

      <View className="flex-row flex-wrap gap-2">
        {tags.map((tag, index) => (
          <View
            key={`tag-${index}`}
            className="flex-row items-center gap-1 px-3 py-1.5 bg-muted rounded-full"
          >
            <Text className="text-[14px] text-foreground">{tag}</Text>
            <Pressable
              onPress={() => handleRemoveTag(index)}
              hitSlop={8}
              className="ml-1"
            >
              <X size={14} color="#64748B" />
            </Pressable>
          </View>
        ))}
      </View>

      <Text className="text-[12px] text-right text-muted-foreground">
        {tags.length} / {MAX_TAGS}
      </Text>
    </View>
  );
}
