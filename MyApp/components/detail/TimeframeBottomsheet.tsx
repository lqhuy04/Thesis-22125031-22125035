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
import { Text } from "../ui/Text";

const { height: SCREEN_HEIGHT } = Dimensions.get("window");

export const enum TIMEFRAME {
  ONE_MINUTE = 1,
  FIVE_MINUTES = 2,
  FIFTEEN_MINUTES = 3,
  THIRTY_MINUTES = 4,
  ONE_HOUR = 5,
  ONE_DAY = 6,
  ONE_WEEK = 7,
  ONE_MONTH = 8,
}

export const TIMEFRAME_OPTIONS = [
  { labelKey: "timeframe.oneMinute", value: TIMEFRAME.ONE_MINUTE },
  { labelKey: "timeframe.fiveMinutes", value: TIMEFRAME.FIVE_MINUTES },
  { labelKey: "timeframe.fifteenMinutes", value: TIMEFRAME.FIFTEEN_MINUTES },
  { labelKey: "timeframe.thirtyMinutes", value: TIMEFRAME.THIRTY_MINUTES },
  { labelKey: "timeframe.oneHour", value: TIMEFRAME.ONE_HOUR },
  { labelKey: "timeframe.oneDay", value: TIMEFRAME.ONE_DAY },
  { labelKey: "timeframe.oneWeek", value: TIMEFRAME.ONE_WEEK },
  { labelKey: "timeframe.oneMonth", value: TIMEFRAME.ONE_MONTH },
];

interface Props {
  visible: boolean;
  selectedTimeframe: TIMEFRAME;
  onSelect: (value: TIMEFRAME) => void;
  onClose: () => void;
}

const TimeframeBottomSheet = ({
  visible,
  selectedTimeframe,
  onSelect,
  onClose,
}: Props) => {
  const { theme } = useTheme();
  const { t } = useLocalization();

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

  const handleSelect = (value: TIMEFRAME) => {
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
          { backgroundColor: theme.background.bg },
          { transform: [{ translateY: slideAnim }] },
        ]}
      >
        {/* Handle */}
        <View style={styles.handle} />

        <Text
          typography="titleMedium"
          color={theme.text.primary}
          style={{ textAlign: "center", marginTop: 8 }}
        >
          {t("timeframe.title")}
        </Text>

        <View
          style={{
            width: "100%",
            height: 1,
            backgroundColor: theme.border.default,
            marginTop: 20,
          }}
        />

        <View style={styles.optionsContainer}>
          {TIMEFRAME_OPTIONS.slice(0, 4).map((option) => {
            const isSelected = selectedTimeframe === option.value;
            return (
              <TouchableOpacity
                key={option.value}
                onPress={() => handleSelect(option.value)}
                style={[
                  styles.optionBtn,
                  {
                    borderWidth: 2,
                    backgroundColor: isSelected
                      ? theme.base.primary + "20"
                      : theme.background.surface,
                    borderColor: isSelected
                      ? theme.base.primary + "60"
                      : "transparent",
                  },
                ]}
              >
                <Text
                  typography="bodyMedium"
                  color={isSelected ? theme.base.primary : theme.text.primary}
                >
                  {t(option.labelKey)}
                </Text>
              </TouchableOpacity>
            );
          })}
        </View>
        <View style={styles.optionsContainer}>
          {TIMEFRAME_OPTIONS.slice(4).map((option) => {
            const isSelected = selectedTimeframe === option.value;
            return (
              <TouchableOpacity
                key={option.value}
                onPress={() => handleSelect(option.value)}
                style={[
                  styles.optionBtn,
                  {
                    borderWidth: 2,
                    backgroundColor: isSelected
                      ? theme.base.primary + "20"
                      : theme.background.surface,
                    borderColor: isSelected
                      ? theme.base.primary + "60"
                      : "transparent",
                  },
                ]}
              >
                <Text
                  typography="bodyMedium"
                  color={isSelected ? theme.base.primary : theme.text.primary}
                >
                  {t(option.labelKey)}
                </Text>
              </TouchableOpacity>
            );
          })}
        </View>

        <View
          style={{
            borderRadius: 12,
            borderWidth: 1,
            borderColor: theme.base.success,
            backgroundColor: theme.base.success + "24",
            padding: 12,
            margin: 12,
          }}
        >
          <Text typography="bodyMedium" color={theme.text.primary}>
            {t("timeframe.description")}
          </Text>
          <Text
            typography="labelLarge"
            color={theme.base.success}
            style={{ textAlign: "right", marginTop: 8 }}
          >
            {t("timeframe.learnMore")}
          </Text>
        </View>
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
    paddingBottom: 36,
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
  sheetTitle: {
    fontSize: 15,
    fontWeight: "600",
    marginBottom: 16,
  },
  optionsContainer: {
    flexDirection: "row",
    marginTop: 12,
    marginHorizontal: 12,
    gap: 8,
  },
  optionBtn: {
    paddingVertical: 4,
    paddingHorizontal: 6,
    borderRadius: 16,
    flex: 1,
    alignItems: "center",
    justifyContent: "center",
  },
  optionText: {
    fontSize: 14,
    fontWeight: "500",
  },
});

export default TimeframeBottomSheet;
