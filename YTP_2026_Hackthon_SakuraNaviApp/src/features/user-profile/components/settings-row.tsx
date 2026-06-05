import { memo, useCallback } from "react";
import { Pressable, View } from "react-native";
import { ChevronRight, type LucideIcon } from "lucide-react-native";
import { Text } from "@/components/ui/text";

interface SettingsRowProps {
  label: string;
  subtitle?: string;
  icon: LucideIcon;
  iconColor: string;
  iconBgColor?: string;
  valueText?: string;
  valueColor?: string;
  valueBold?: boolean;
  badge?: string;
  onPress: () => void;
  destructive?: boolean;
  hideChevron?: boolean;
}

export const SettingsRow = memo(function SettingsRow({
  label,
  subtitle,
  icon: Icon,
  iconColor,
  iconBgColor,
  valueText,
  valueColor = "text-muted-foreground",
  valueBold = false,
  badge,
  onPress,
  destructive = false,
  hideChevron = false,
}: SettingsRowProps) {
  const handlePress = useCallback(() => onPress(), [onPress]);

  return (
    <Pressable
      onPress={handlePress}
      className="flex-row items-center gap-3.5 py-4 px-4 active:bg-muted/50 bg-card"
    >
      <View
        className="items-center justify-center rounded-[10px] w-8 h-8"
        style={{ backgroundColor: iconBgColor || iconColor + "22" }}
      >
        <Icon size={16} color={iconColor} />
      </View>
      <View className="flex-1 gap-1">
        <Text
          className={`text-[17px] ${destructive ? "text-destructive" : "text-foreground"} font-medium`}
        >
          {label}
        </Text>
        {subtitle && (
          <Text className="text-[13px] text-muted-foreground">{subtitle}</Text>
        )}
      </View>

      <View className="flex-row items-center gap-2">
        {valueText && (
          <Text
            className={`text-[15px] ${valueColor} ${valueBold ? "font-bold" : "font-normal"}`}
          >
            {valueText}
          </Text>
        )}
        {badge && (
          <View className="items-center justify-center px-1.5 h-5 rounded-full bg-destructive mr-1">
            <Text className="text-[12px] font-medium text-destructive-foreground">
              {badge}
            </Text>
          </View>
        )}
        {!destructive && !hideChevron && (
          <ChevronRight size={16} color="#C7C7CC" />
        )}
      </View>
    </Pressable>
  );
});
