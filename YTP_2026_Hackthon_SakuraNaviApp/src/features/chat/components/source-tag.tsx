import { Linking } from "react-native";
import { Image } from "expo-image";
import type { PolicySource } from "@/types";
import { Button } from "@/components/ui/button";
import { Text } from "@/components/ui/text";

interface Props {
  source: PolicySource;
}

export function SourceTag({ source }: Props) {
  const label = source.name ?? source.title ?? "政策來源";

  return (
    <Button
      onPress={() => {
        if (!source.url) {
          return;
        }

        void Linking.openURL(source.url);
      }}
      variant="secondary"
      size="sm"
      className="h-auto gap-1.5 rounded-full px-2.5 py-1"
    >
      <Image
        source="sf:paperclip"
        style={{ width: 11, height: 11 }}
        tintColor="#666"
      />
      <Text className="text-[11px] font-medium text-muted-foreground">
        {label}
      </Text>
    </Button>
  );
}
