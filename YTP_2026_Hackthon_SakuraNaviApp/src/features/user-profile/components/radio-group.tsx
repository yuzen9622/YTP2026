import { memo, useCallback } from "react";
import { View, Pressable } from "react-native";
import { Text } from "@/components/ui/text";

interface RadioOption {
  label: string;
  value: string;
}

interface RadioGroupProps {
  options: readonly RadioOption[];
  value: string | null | undefined;
  onChange: (v: string) => void;
}

export const RadioGroup = memo(function RadioGroup({
  options,
  value,
  onChange,
}: RadioGroupProps) {
  const handlePress = useCallback(
    (optValue: string) => onChange(optValue),
    [onChange],
  );

  return (
    <View className="flex-row flex-wrap gap-2">
      {options.map((opt) => {
        const selected = opt.value === value;
        return (
          <Pressable
            key={opt.value}
            onPress={() => handlePress(opt.value)}
            className={`rounded-full px-3.5 py-2 border ${
              selected
                ? "bg-primary border-primary"
                : "bg-transparent border-input active:bg-muted"
            }`}
          >
            <Text
              className={
                selected
                  ? "text-primary-foreground font-medium"
                  : "text-muted-foreground font-medium"
              }
            >
              {opt.label}
            </Text>
          </Pressable>
        );
      })}
    </View>
  );
});