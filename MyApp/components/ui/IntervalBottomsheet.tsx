import React, { useRef } from "react";
import {
  Modal,
  Animated,
  Pressable,
  StyleSheet,
  TouchableOpacity,
  View,
  Dimensions,
} from "react-native";
import { useTheme } from "@/hooks/ThemeContext";
import { useLocalization } from "@/hooks/LocalizationContext";
import { Text } from "@/components/ui/Text";
import AntDesign from "@expo/vector-icons/build/AntDesign";
import { SuggestionInterval } from "@/helpers/MarketHelpers";
import { useSafeAreaInsets } from "react-native-safe-area-context";

const { height: SCREEN_HEIGHT } = Dimensions.get("window");

export const INTERVAL_OPTIONS: {
  value: SuggestionInterval;
  labelKey: string;
}[] = [
  { value: "today", labelKey: "suggestion.intervalToday" },
  { value: "1w", labelKey: "suggestion.interval1w" },
  { value: "1mo", labelKey: "suggestion.interval1mo" },
  { value: "3mo", labelKey: "suggestion.interval3mo" },
  { value: "6mo", labelKey: "suggestion.interval6mo" },
];

interface Props {
  visible: boolean;
  selectedInterval: SuggestionInterval;
  onSelect: (value: SuggestionInterval) => void;
  onClose: () => void;
}

const IntervalBottomsheet = ({
  visible,
  selectedInterval,
  onSelect,
  onClose,
}: Props) => {
  const { theme } = useTheme();
  const { t } = useLocalization();
  const insets = useSafeAreaInsets();

  const slideAnim = useRef(new Animated.Value(SCREEN_HEIGHT)).current;
  const backdropAnim = useRef(new Animated.Value(0)).current;

  const openSheet = () => {
    Animated.parallel([
      Animated.spring(slideAnim, {
        toValue: 0,
        useNativeDriver: true,
        bounciness: 4,
      }),
      Animated.timing(backdropAnim, {
        toValue: 1,
        duration: 250,
        useNativeDriver: true,
      }),
    ]).start();
  };

  const closeSheet = (callback?: () => void) => {
    Animated.parallel([
      Animated.timing(slideAnim, {
        toValue: SCREEN_HEIGHT,
        duration: 220,
        useNativeDriver: true,
      }),
      Animated.timing(backdropAnim, {
        toValue: 0,
        duration: 220,
        useNativeDriver: true,
      }),
    ]).start(() => {
      onClose();
      callback?.();
    });
  };

  const handleSelect = (value: SuggestionInterval) => {
    closeSheet(() => onSelect(value));
  };

  return (
    <Modal
      visible={visible}
      transparent
      animationType="none"
      onShow={openSheet}
    >
      {/* Backdrop */}
      <Animated.View
        style={[
          StyleSheet.absoluteFill,
          styles.backdrop,
          { opacity: backdropAnim },
        ]}
      >
        <Pressable
          style={StyleSheet.absoluteFill}
          onPress={() => closeSheet()}
        />
      </Animated.View>

      {/* Sheet */}
      <Animated.View
        style={[
          styles.sheet,
          {
            backgroundColor: theme.background.bg,
            paddingBottom: insets.bottom + 12,
          },
          { transform: [{ translateY: slideAnim }] },
        ]}
      >
        {/* Handle */}
        <View style={styles.handle} />

        {/* Header: title centered + close button on the right */}
        <View style={styles.header}>
          <Text
            typography="titleMedium"
            color={theme.text.primary}
            style={{ flex: 1, textAlign: "center", marginLeft: 32 }}
          >
            {t("suggestion.intervalTitle")}
          </Text>
          <TouchableOpacity
            onPress={() => closeSheet()}
            hitSlop={{ top: 8, bottom: 8, left: 8, right: 8 }}
            style={{ width: 32, alignItems: "flex-end" }}
          >
            <AntDesign name="close" size={20} color={theme.text.primary} />
          </TouchableOpacity>
        </View>

        <View
          style={{
            width: "100%",
            height: 1,
            backgroundColor: theme.border.default,
            marginTop: 12,
          }}
        />

        {/* Options */}
        {INTERVAL_OPTIONS.map((option) => {
          const isSelected = selectedInterval === option.value;
          return (
            <TouchableOpacity
              key={option.value}
              onPress={() => handleSelect(option.value)}
              style={[styles.optionRow]}
            >
              <Text
                typography="titleMedium"
                color={isSelected ? theme.base.primary : theme.text.primary}
              >
                {t(option.labelKey)}
              </Text>
              {isSelected && (
                <AntDesign name="check" size={18} color={theme.base.primary} />
              )}
            </TouchableOpacity>
          );
        })}
      </Animated.View>
    </Modal>
  );
};

const styles = StyleSheet.create({
  backdrop: {
    backgroundColor: "rgba(0,0,0,0.4)",
  },
  sheet: {
    position: "absolute",
    bottom: 0,
    left: 0,
    right: 0,
    borderTopLeftRadius: 16,
    borderTopRightRadius: 16,
    paddingTop: 12,
    elevation: 20,
    shadowColor: "#000",
    shadowOffset: { width: 0, height: -3 },
    shadowOpacity: 0.12,
    shadowRadius: 8,
  },
  handle: {
    width: 40,
    height: 4,
    borderRadius: 2,
    backgroundColor: "#d1d5db",
    alignSelf: "center",
    marginBottom: 16,
  },
  header: {
    flexDirection: "row",
    alignItems: "center",
    paddingHorizontal: 16,
  },
  optionRow: {
    flexDirection: "row",
    alignItems: "center",
    justifyContent: "space-between",
    paddingHorizontal: 20,
    paddingVertical: 16,
  },
});

export default IntervalBottomsheet;
