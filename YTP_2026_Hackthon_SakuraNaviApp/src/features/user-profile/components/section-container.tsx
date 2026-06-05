import { memo } from "react";
import { View } from "react-native";
import { Text } from "@/components/ui/text";
import { Card } from "@/components/ui/card";

interface SectionContainerProps {
  title: string;
  children: React.ReactNode;
  rightAction?: React.ReactNode;
}

export const SectionContainer = memo(function SectionContainer({
  title,
  children,
  rightAction,
}: SectionContainerProps) {
  return (
    <View className="gap-2">
      <View className="flex-row items-center justify-between px-4">
        <Text className="text-[13px] font-semibold tracking-wider text-muted-foreground uppercase">
          {title}
        </Text>
        {rightAction}
      </View>
      <Card className="gap-0 py-0 overflow-hidden rounded-[18px] border-border mx-4">
        {children}
      </Card>
    </View>
  );
});