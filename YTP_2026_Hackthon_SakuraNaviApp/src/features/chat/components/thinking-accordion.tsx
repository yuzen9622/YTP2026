import { useEffect, useState } from "react";
import { View } from "react-native";
import Animated, {
  FadeIn,
  FadeOut,
  useAnimatedStyle,
  useSharedValue,
  withRepeat,
  withSequence,
  withTiming,
} from "react-native-reanimated";
import { Sparkles } from "lucide-react-native";
import {
  Accordion,
  AccordionContent,
  AccordionItem,
  AccordionTrigger,
} from "@/components/ui/accordion";
import { Icon } from "@/components/ui/icon";
import { Text } from "@/components/ui/text";
import { cn } from "@/lib/utils";

interface ThinkingAccordionProps {
  isStreaming?: boolean;
  content?: string;
  label?: string;
}

export function ThinkingAccordion({
  isStreaming,
  content,
  label,
}: ThinkingAccordionProps) {
  const hasContent = Boolean(content?.trim());
  const showLabel = label ?? (isStreaming ? "AI 思考中" : "已完成思考");

  const [value, setValue] = useState<string[]>(isStreaming ? ["thinking"] : []);

  useEffect(() => {
    if (isStreaming) {
      setValue(["thinking"]);
    } else {
      setValue([]);
    }
  }, [isStreaming]);

  if (!isStreaming && !hasContent) {
    return null;
  }

  return (
    <Animated.View
      entering={FadeIn.duration(200)}
      exiting={FadeOut.duration(150)}
      className="w-full max-w-[92%]"
    >
      <Accordion
        type="multiple"
        value={value}
        onValueChange={(next) => setValue(next as string[])}
      >
        <AccordionItem
          value="thinking"
          className="rounded-xl border border-muted-foreground/20 bg-muted/40 px-3"
        >
          <AccordionTrigger className="py-2.5">
            <View className="flex-row items-center gap-2">
              {isStreaming ? (
                <ShimmerDot />
              ) : (
                <Icon as={Sparkles} size={14} className="text-muted-foreground" />
              )}
              <Text
                className={cn(
                  "text-sm font-medium",
                  isStreaming ? "text-foreground" : "text-muted-foreground",
                )}
              >
                {showLabel}
              </Text>
            </View>
          </AccordionTrigger>

          <AccordionContent className="pt-0">
            {hasContent ? (
              <View className="border-l-2 border-muted-foreground/30 pl-3">
                <Text className="text-xs leading-5 text-muted-foreground">
                  {content}
                </Text>
              </View>
            ) : (
              <View className="flex-row items-center gap-1.5 py-1">
                {[0, 160, 320].map((delay) => (
                  <ThinkingDot key={delay} delay={delay} />
                ))}
              </View>
            )}
          </AccordionContent>
        </AccordionItem>
      </Accordion>
    </Animated.View>
  );
}

function ShimmerDot() {
  const opacity = useSharedValue(0.4);

  useEffect(() => {
    opacity.value = withRepeat(
      withSequence(
        withTiming(1, { duration: 600 }),
        withTiming(0.4, { duration: 600 }),
      ),
      -1,
      false,
    );
  }, [opacity]);

  const style = useAnimatedStyle(() => ({ opacity: opacity.value }));

  return (
    <Animated.View
      style={style}
      className="size-2 rounded-full bg-primary"
    />
  );
}

function ThinkingDot({ delay }: { delay: number }) {
  const opacity = useSharedValue(0.3);

  useEffect(() => {
    const timeout = setTimeout(() => {
      opacity.value = withRepeat(
        withSequence(
          withTiming(1, { duration: 380 }),
          withTiming(0.3, { duration: 380 }),
        ),
        -1,
        false,
      );
    }, delay);

    return () => clearTimeout(timeout);
  }, [delay, opacity]);

  const style = useAnimatedStyle(() => ({ opacity: opacity.value }));

  return (
    <Animated.View
      style={style}
      className="size-1.5 rounded-full bg-muted-foreground"
    />
  );
}
