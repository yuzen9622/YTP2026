import { Button } from "@/components/ui/button";
import { Text } from "@/components/ui/text";

interface Props {
  text: string;
  onPress: () => void;
}

export function SuggestChip({ text, onPress }: Props) {
  return (
    <Button
      onPress={onPress}
      variant="outline"
      className="h-auto rounded-full border-primary/50 bg-primary/10 px-3.5 py-1.5 active:bg-primary/20"
    >
      <Text className="text-[13px] font-medium text-primary">{text}</Text>
    </Button>
  );
}
