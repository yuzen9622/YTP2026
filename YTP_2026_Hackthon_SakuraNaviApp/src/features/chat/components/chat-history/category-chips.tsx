import { ScrollView, Pressable, View, Text } from "react-native";

export type ConversationStatus = "all" | "active" | "awaiting" | "resolved";

interface CategoryChipsProps {
  activeStatus: ConversationStatus;
  onStatusChange: (status: ConversationStatus) => void;
  counts: Record<ConversationStatus, number>;
}

export function CategoryChips({
  activeStatus,
  onStatusChange,
  counts,
}: CategoryChipsProps) {
  const chips: { label: string; status: ConversationStatus }[] = [
    { label: "全部", status: "all" },
    { label: "進行中", status: "active" },
    { label: "等候中", status: "awaiting" },
    { label: "已結案", status: "resolved" },
  ];

  return (
    <View className="pl-4 pr-0 mb-4">
      <ScrollView
        horizontal
        showsHorizontalScrollIndicator={false}
        contentContainerStyle={{ gap: 8, paddingRight: 16 }}
      >
        {chips.map(({ label, status }) => {
          const isActive = activeStatus === status;
          const count = counts[status] || 0;
          return (
            <Pressable
              key={status}
              onPress={() => onStatusChange(status)}
              className={`flex-row items-center px-4 py-2 ${
                isActive ? "bg-primary" : "bg-card"
              } rounded-full`}
            >
              <Text
                className={`text-[13px] font-semibold ${
                  isActive ? "text-primary-foreground" : "text-muted-foreground"
                }`}
              >
                {label}
              </Text>
              {count > 0 && (
                <View
                  className={`ml-2 px-1.5 py-0.5 rounded-full ${
                    isActive ? "bg-primary-foreground/20" : "bg-muted"
                  }`}
                >
                  <Text
                    className={`text-[11px] font-medium ${
                      isActive
                        ? "text-primary-foreground"
                        : "text-muted-foreground"
                    }`}
                  >
                    {count}
                  </Text>
                </View>
              )}
            </Pressable>
          );
        })}
      </ScrollView>
    </View>
  );
}
