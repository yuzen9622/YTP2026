import { View, ActivityIndicator } from "react-native";

export default function Index() {
  return (
    <View className="items-center justify-center flex-1 bg-background">
      <ActivityIndicator color="#FF6B9D" size="large" />
    </View>
  );
}
