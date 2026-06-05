import { memo } from "react";
import { View } from "react-native";
import { Text } from "@/components/ui/text";
import { Card } from "@/components/ui/card";

interface SectionProps {
  title: string;
  children: React.ReactNode;
}

export const Section = memo(function Section({ title, children }: SectionProps) {
  return (
    <View className="w-full gap-2">
      <Text className="text-[11px] font-semibold text-muted-foreground tracking-[0.8px] uppercase ml-4">
        {title}
      </Text>
      <Card className="rounded-[18px] overflow-hidden bg-card border-border shadow-sm">
        {children}
      </Card>
    </View>
  );
});