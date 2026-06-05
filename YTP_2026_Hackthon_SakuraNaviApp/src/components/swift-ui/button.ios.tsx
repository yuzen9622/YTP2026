import { colors } from "@/lib/colors.ios";
import { LoaderCircle } from "lucide-react-native";
import { Button, HStack, Text } from "@expo/ui/swift-ui";
import {
  background,
  buttonStyle,
  font,
  disabled,
  cornerRadius,
  foregroundStyle,
  frame,
  padding,
  tint,
} from "@expo/ui/swift-ui/modifiers";
import { spacing } from "@/constant/size";
interface PrimaryButtonProps {
  title: string;
  isLoading: boolean;
  isDisabled: boolean;
  onPress: () => void;
}

export default function PrimaryButton({
  title,
  isLoading,
  isDisabled,
  onPress,
}: PrimaryButtonProps) {
  return (
    <Button
      onPress={onPress}
      role="default"
      modifiers={[
        buttonStyle("bordered"),
        tint(isDisabled ? colors.primaryLight : colors.primary),
        background(isDisabled ? colors.primaryLight : colors.primary),
        cornerRadius(9999),
        padding({ horizontal: spacing.md, vertical: 14 }),

        disabled(isDisabled),
      ]}
    >
      <HStack
        modifiers={[
          padding({ horizontal: spacing.sm, vertical: 14 }),
          frame({ minWidth: 300 }),
        ]}
        spacing={spacing.sm}
        alignment="center"
      >
        {isLoading && <LoaderCircle size={18} color="#FFFFFF" />}
        <Text
          modifiers={[
            foregroundStyle("#FFFFFF"),
            font({ size: 17, weight: "semibold" }),
          ]}
        >
          {isLoading ? "Signing In..." : title}
        </Text>
      </HStack>
    </Button>
  );
}
