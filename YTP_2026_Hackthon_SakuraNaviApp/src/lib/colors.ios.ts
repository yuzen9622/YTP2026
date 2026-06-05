// Colors extracted from tailwind/navigation theme for SwiftUI use
export const colors = {
  // Primary brand
  primary: "#FF6B9D", // Pink-500, HSL 341.86 100% 74.71%
  primaryLight: "#FF6B9D22", // 15% opacity for backgrounds

  // Secondary
  secondary: "#6C63FF", // Purple-500

  // Semantic
  destructive: "#FF3B30", // Red-600
  destructiveLight: "#FF3B3022",

  // Text
  foreground: "#1a1a1a",
  mutedForeground: "#0C0505",

  // Background
  background: "#FFFCFA", // HSL 20 100% 98.24%
  card: "#FFFFFF",

  // Border
  border: "#E0E0E0",

  // Misc
  gray: "#999999",
  grayLight: "#E0E0E0",
} as const;

export type ColorKey = keyof typeof colors;
