import React from "react";
import { StyleSheet, useWindowDimensions } from "react-native";
import { Gesture, GestureDetector } from "react-native-gesture-handler";
import Animated, {
  runOnJS,
  useAnimatedStyle,
  useSharedValue,
  withSpring,
} from "react-native-reanimated";
import LinearGradient from "react-native-linear-gradient";
import { useSafeAreaInsets } from "react-native-safe-area-context";
import Octicons from "@expo/vector-icons/Octicons";
import { useTheme } from "@/hooks/ThemeContext";
import { Text } from "@/components/ui/Text";

const SIZE = 56;
const EDGE_MARGIN = 12;

interface Props {
  onPress?: () => void;
}

const AIFloatingButton = ({ onPress }: Props) => {
  const { theme } = useTheme();
  const insets = useSafeAreaInsets();
  const { width, height } = useWindowDimensions();

  // Bounds the bubble can travel within (top-left origin).
  const minX = EDGE_MARGIN;
  const maxX = width - SIZE - EDGE_MARGIN;
  const minY = insets.top + EDGE_MARGIN;
  const maxY = height - insets.bottom - SIZE - EDGE_MARGIN;

  // Initial position: bottom-right, above the footer.
  const translateX = useSharedValue(maxX);
  const translateY = useSharedValue(maxY - 84);

  // Position captured when a drag begins.
  const startX = useSharedValue(0);
  const startY = useSharedValue(0);

  const clamp = (value: number, lower: number, upper: number) => {
    "worklet";
    return Math.min(Math.max(value, lower), upper);
  };

  const pan = Gesture.Pan()
    .maxPointers(1)
    .onStart(() => {
      startX.value = translateX.value;
      startY.value = translateY.value;
    })
    .onUpdate((e) => {
      translateX.value = clamp(startX.value + e.translationX, minX, maxX);
      translateY.value = clamp(startY.value + e.translationY, minY, maxY);
    })
    .onEnd(() => {
      // Snap to the nearest horizontal edge, like a Messenger chat head.
      const snapToRight = translateX.value + SIZE / 2 > width / 2;
      translateX.value = withSpring(snapToRight ? maxX : minX, {
        damping: 26,
        stiffness: 120,
        mass: 0.9,
        overshootClamping: true,
      });
    });

  const tap = Gesture.Tap().onEnd(() => {
    if (onPress) runOnJS(onPress)();
  });

  const gesture = Gesture.Race(pan, tap);

  const animatedStyle = useAnimatedStyle(() => ({
    transform: [
      { translateX: translateX.value },
      { translateY: translateY.value },
    ],
  }));

  return (
    <GestureDetector gesture={gesture}>
      <Animated.View style={[styles.container, animatedStyle]}>
        <LinearGradient
          colors={[
            "#4B2FC9",
            "#613DE4",
            "#7B5CFF",
            "#9D8CFF",
            "#7B5CFF",
            "#613DE4",
            "#4B2FC9",
          ]}
          useAngle
          angle={90}
          angleCenter={{ x: 0.5, y: 0.5 }}
          style={styles.bubble}
        >
          <Octicons
            name="sparkles-fill"
            size={20}
            color={theme.text.onPrimary}
          />
          <Text typography="labelLarge" color={theme.text.onPrimary}>
            AI
          </Text>
        </LinearGradient>
      </Animated.View>
    </GestureDetector>
  );
};

const styles = StyleSheet.create({
  container: {
    position: "absolute",
    top: 0,
    left: 0,
    width: SIZE,
    height: SIZE,
  },
  bubble: {
    flex: 1,
    borderRadius: SIZE / 2,
    alignItems: "center",
    justifyContent: "center",
    // Shadow iOS
    shadowColor: "#000",
    shadowOffset: { width: 0, height: 2 },
    shadowOpacity: 0.2,
    shadowRadius: 6,
    // Shadow Android
    elevation: 6,
  },
});

export default AIFloatingButton;
