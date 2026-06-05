import { Icon } from "@/components/ui/icon";
import { TextClassContext } from "@/components/ui/text";
import { cn } from "@/lib/utils";
import * as AccordionPrimitive from "@rn-primitives/accordion";
import { ChevronDown } from "lucide-react-native";
import * as React from "react";
import { Platform, Pressable, View } from "react-native";
import Animated, {
  Extrapolation,
  FadeIn,
  FadeOutUp,
  interpolate,
  LayoutAnimationConfig,
  LinearTransition,
  useAnimatedStyle,
  useDerivedValue,
  withTiming,
} from "react-native-reanimated";

function Accordion({
  children,
  ...props
}: React.ComponentProps<typeof AccordionPrimitive.Root>) {
  return (
    <LayoutAnimationConfig skipEntering>
      <AccordionPrimitive.Root {...(props as any)} asChild={Platform.OS !== "web"}>
        <Animated.View layout={LinearTransition.duration(200)}>
          {children}
        </Animated.View>
      </AccordionPrimitive.Root>
    </LayoutAnimationConfig>
  );
}

function AccordionItem({
  className,
  value,
  ...props
}: React.ComponentProps<typeof AccordionPrimitive.Item>) {
  return (
    <Animated.View layout={LinearTransition.duration(200)} className="overflow-hidden">
      <AccordionPrimitive.Item value={value} className={className} {...props} />
    </Animated.View>
  );
}

const Trigger = Platform.OS === "web" ? View : Pressable;

function AccordionTrigger({
  className,
  children,
  ...props
}: React.ComponentProps<typeof AccordionPrimitive.Trigger>) {
  const { isExpanded } = AccordionPrimitive.useItemContext();

  const progress = useDerivedValue(() =>
    isExpanded ? withTiming(1, { duration: 220 }) : withTiming(0, { duration: 200 }),
  );
  const chevronStyle = useAnimatedStyle(() => ({
    transform: [
      { rotate: `${interpolate(progress.value, [0, 1], [0, 180], Extrapolation.CLAMP)}deg` },
    ],
  }));

  return (
    <TextClassContext.Provider value="text-foreground text-sm font-medium">
      <AccordionPrimitive.Header asChild>
        <Animated.View>
          <AccordionPrimitive.Trigger {...props} asChild>
            <Trigger
              className={cn(
                "flex flex-row items-center justify-between gap-4 py-3",
                Platform.select({
                  web: "group flex-1 hover:underline focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring",
                }),
                className,
              )}
            >
              <>{children}</>
              <Animated.View style={chevronStyle}>
                <Icon
                  as={ChevronDown}
                  size={16}
                  className="text-muted-foreground shrink-0"
                />
              </Animated.View>
            </Trigger>
          </AccordionPrimitive.Trigger>
        </Animated.View>
      </AccordionPrimitive.Header>
    </TextClassContext.Provider>
  );
}

function AccordionContent({
  className,
  children,
  ...props
}: React.ComponentProps<typeof AccordionPrimitive.Content>) {
  const { isExpanded } = AccordionPrimitive.useItemContext();
  return (
    <TextClassContext.Provider value="text-foreground">
      <AccordionPrimitive.Content
        className={cn(
          Platform.select({
            web: cn(
              "overflow-hidden text-sm transition-all",
              isExpanded ? "animate-accordion-down" : "animate-accordion-up",
            ),
          }),
        )}
        {...props}
      >
        <InnerContent className={cn("pb-3", className)}>{children}</InnerContent>
      </AccordionPrimitive.Content>
    </TextClassContext.Provider>
  );
}

function InnerContent({
  children,
  className,
}: {
  children: React.ReactNode;
  className?: string;
}) {
  if (Platform.OS === "web") {
    return <View className={cn("pb-3", className)}>{children}</View>;
  }
  return (
    <Animated.View
      entering={FadeIn.duration(180)}
      exiting={FadeOutUp.duration(150)}
      className={cn("pb-3", className)}
    >
      {children}
    </Animated.View>
  );
}

export { Accordion, AccordionContent, AccordionItem, AccordionTrigger };
