import { Eye, EyeOff, type LucideIcon } from "lucide-react-native";

import {
  VStack,
  HStack,
  Button,
  TextField,
  Text,
  SecureField,
} from "@expo/ui/swift-ui";
import {
  padding,
  cornerRadius,
  foregroundStyle,
  background,
  font,
} from "@expo/ui/swift-ui/modifiers";
import { colors } from "@/lib/colors.ios";
import { spacing } from "@/constant/size";
interface InputFieldProps {
  title?: string;
  value: string;
  onChangeText: (text: string) => void;
  placeholder: string;
  icon: LucideIcon;
  isSecure?: boolean;
  isPasswordVisible?: boolean;
  onToggleVisibility?: () => void;
  validationMessage?: string;
  keyboardType?: "default" | "emailAddress";
}

export default function InputField({
  title,
  value,
  onChangeText,
  placeholder,
  icon,
  isSecure = false,
  isPasswordVisible,
  onToggleVisibility,
  validationMessage,
}: InputFieldProps) {
  const Icon = icon;

  return (
    <VStack alignment="leading" spacing={spacing.xs}>
      {title && (
        <Text
          modifiers={[
            foregroundStyle(colors.foreground),
            font({ size: 14, weight: "semibold" }),
            padding({ leading: 4 }),
          ]}
        >
          {title}
        </Text>
      )}

      <VStack
        modifiers={[
          background("#F4F4F6"), // Soft off-white typical of modern iOS inputs
          cornerRadius(16),
        ]}
      >
        <HStack
          spacing={spacing.sm}
          alignment="center"
          modifiers={[padding({ horizontal: spacing.md, vertical: 14 })]}
        >
          <Icon size={14} color={colors.primary} />

          {isSecure ? (
            <SecureField
              defaultValue={value}
              onValueChange={onChangeText}
              placeholder={placeholder}
              modifiers={[padding({ all: 0 }), font({ size: 16 })]}
            />
          ) : (
            <TextField
              defaultValue={value}
              onValueChange={onChangeText}
              placeholder={placeholder}
              modifiers={[
                padding({ all: 0 }),

                font({ size: 14, weight: "bold", design: "rounded" }),
              ]}
            />
          )}

          {isSecure && onToggleVisibility && (
            <Button onPress={onToggleVisibility}>
              {isPasswordVisible ? (
                <Eye size={14} color={colors.mutedForeground} />
              ) : (
                <EyeOff size={14} color={colors.mutedForeground} />
              )}
            </Button>
          )}
        </HStack>
      </VStack>

      {validationMessage && (
        <Text
          modifiers={[
            foregroundStyle(colors.destructive),
            font({ size: 12, weight: "medium" }),
            padding({ leading: 4 }),
          ]}
        >
          {validationMessage}
        </Text>
      )}
    </VStack>
  );
}
