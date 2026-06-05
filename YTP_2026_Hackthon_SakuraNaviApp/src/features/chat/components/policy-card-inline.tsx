import { ScrollView, View } from "react-native";
import { useRouter } from "expo-router";
import type { PolicyCard } from "@/types";
import { useSavedPolicyStore } from "@/store/saved-policy-store";
import { Button } from "@/components/ui/button";
import { Card } from "@/components/ui/card";
import { Text } from "@/components/ui/text";

interface PolicyCardInlineProps {
  policy: PolicyCard;
}

export function PolicyCardInline({ policy }: PolicyCardInlineProps) {
  const router = useRouter();
  const savedPolicyIds = useSavedPolicyStore((state) => state.savedPolicyIds);
  const toggleSavedPolicy = useSavedPolicyStore(
    (state) => state.toggleSavedPolicy,
  );
  const isSaved = savedPolicyIds.includes(policy.policyId);

  return (
    <Card className="mt-2 w-full rounded-2xl border-border px-3.5 py-3">
      <View className="gap-2.5">
        <Text className="text-sm font-bold text-foreground" selectable>
          {policy.title}
        </Text>

        <Text
          className="text-xs leading-5 text-muted-foreground"
          numberOfLines={2}
          selectable
        >
          {policy.summary}
        </Text>

        <ScrollView
          horizontal
          showsHorizontalScrollIndicator={false}
          contentContainerClassName="gap-1.5"
        >
          {policy.tags.map((tag) => (
            <View key={tag} className="rounded-full bg-muted px-2 py-0.5">
              <Text className="text-[11px] text-muted-foreground">{tag}</Text>
            </View>
          ))}
        </ScrollView>

        <View className="rounded-xl bg-primary/10 px-2.5 py-2">
          <Text className="text-[11px] font-medium text-primary">推薦原因</Text>
          <Text className="mt-1 text-[12px] text-foreground/90">
            {policy.reason}
          </Text>
        </View>

        <View className="flex-row gap-2">
          <Button
            testID={`policy-inline-detail-${policy.policyId}`}
            size="sm"
            variant="outline"
            className="flex-1"
            onPress={() => {
              router.push({
                pathname: "/(tabs)/search/policy/[policyId]",
                params: { policyId: policy.policyId },
              });
            }}
          >
            <Text>查看詳情</Text>
          </Button>

          <Button
            testID={`policy-inline-save-${policy.policyId}`}
            size="sm"
            variant={isSaved ? "default" : "secondary"}
            className="flex-1"
            onPress={() => toggleSavedPolicy(policy.policyId)}
          >
            <Text>{isSaved ? "已收藏" : "收藏"}</Text>
          </Button>
        </View>
      </View>
    </Card>
  );
}
