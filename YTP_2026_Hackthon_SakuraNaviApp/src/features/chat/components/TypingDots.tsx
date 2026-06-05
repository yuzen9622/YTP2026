import { useEffect, useRef } from "react";
import { Animated, View } from "react-native";

export function TypingDots() {
  const dot1 = useRef(new Animated.Value(0.3)).current;
  const dot2 = useRef(new Animated.Value(0.3)).current;
  const dot3 = useRef(new Animated.Value(0.3)).current;

  useEffect(() => {
    const pulse = (dot: Animated.Value, delay: number) =>
      Animated.loop(
        Animated.sequence([
          Animated.delay(delay),
          Animated.timing(dot, {
            toValue: 1,
            duration: 380,
            useNativeDriver: true,
          }),
          Animated.timing(dot, {
            toValue: 0.3,
            duration: 380,
            useNativeDriver: true,
          }),
        ]),
      );

    const animation = Animated.parallel([
      pulse(dot1, 0),
      pulse(dot2, 180),
      pulse(dot3, 360),
    ]);

    animation.start();

    return () => {
      animation.stop();
    };
  }, [dot1, dot2, dot3]);

  return (
    <View className="flex-row gap-1.5 py-0.5">
      {[dot1, dot2, dot3].map((dot, index) => (
        <Animated.View
          key={index}
          className="rounded-full size-2 bg-muted-foreground"
          style={{ opacity: dot }}
        />
      ))}
    </View>
  );
}
