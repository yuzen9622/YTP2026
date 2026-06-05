import { Text, View } from "react-native";

export function FooterNote() {
  return (
    <View className="items-center justify-center p-6 mb-12">
      <Text className="mt-3 text-[11px] font-medium text-muted-foreground/60">
        Sakura Navi
      </Text>
      <Text className="text-[11px] font-medium text-muted-foreground/60">
        版本 1.0.0
      </Text>
    </View>
  );
}
