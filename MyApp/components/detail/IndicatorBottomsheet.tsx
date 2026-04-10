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
import { Text } from "../ui/Text";

const { height: SCREEN_HEIGHT } = Dimensions.get("window");

export type IndicatorMode1 = "MA" | "BOLL" | null;
export type IndicatorMode2 = "RSI" | "KDJ" | null;

export interface IndicatorState {
  mode1: IndicatorMode1;
  mode2: IndicatorMode2;
  volume: boolean;
}

interface IndicatorOption {
  label: string;
  value: string;
}

const OVERLAY_INDICATORS: IndicatorOption[] = [
  { label: "MA", value: "MA" },
  { label: "BOLL", value: "BOLL" },
];

const SUB_INDICATORS: IndicatorOption[] = [
  { label: "MACD", value: "MACD" },
  { label: "RSI", value: "RSI" },
  { label: "KDJ", value: "KDJ" },
];

const VOLUME_INDICATOR: IndicatorOption = {
  label: "VOL",
  value: "VOLUME",
};

interface Props {
  visible: boolean;
  indicatorState: IndicatorState;
  onChangeIndicator: (next: IndicatorState) => void;
  onClose: () => void;
}

const IndicatorBottomSheet = ({
  visible,
  indicatorState,
  onChangeIndicator,
  onClose,
}: Props) => {
  const { theme } = useTheme();

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

  const closeSheet = () => {
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
    ]).start(onClose);
  };

  const toggle = <T,>(
    current: T | null,
    value: T,
    updater: (val: T | null) => void,
  ) => {
    updater(current === value ? null : value);
  };

  const renderOption = (
    option: IndicatorOption,
    isSelected: boolean,
    onPress: () => void,
  ) => (
    <TouchableOpacity
      key={option.value}
      onPress={onPress}
      style={[
        styles.optionBtn,
        {
          borderColor: isSelected ? theme.base.primary : theme.border.default,
          backgroundColor: isSelected
            ? `${theme.base.primary}18`
            : theme.background.surface,
        },
      ]}
    >
      <Text typography="bodyLarge">{option.label}</Text>
    </TouchableOpacity>
  );

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
        <Pressable style={StyleSheet.absoluteFill} onPress={closeSheet} />
      </Animated.View>

      {/* Sheet */}
      <Animated.View
        style={[
          styles.sheet,
          { backgroundColor: theme.background.surface },
          { transform: [{ translateY: slideAnim }] },
        ]}
      >
        <View style={styles.handle} />

        {/* Header */}
        <View style={styles.header}>
          <Text typography="titleLarge">Chỉ báo kỹ thuật</Text>
          <TouchableOpacity
            onPress={() =>
              onChangeIndicator({ mode1: null, mode2: null, volume: false })
            }
          >
            <Text typography="titleMedium" color={theme.base.primary}>
              Xoá tất cả
            </Text>
          </TouchableOpacity>
        </View>

        {/* Overlay */}
        <View style={styles.row}>
          {OVERLAY_INDICATORS.map((opt) =>
            renderOption(opt, indicatorState.mode1 === opt.value, () =>
              toggle(indicatorState.mode1, opt.value as IndicatorMode1, (val) =>
                onChangeIndicator({ ...indicatorState, mode1: val }),
              ),
            ),
          )}
        </View>

        <View style={styles.divider} />

        {/* Volume */}
        <View style={styles.row}>
          {renderOption(VOLUME_INDICATOR, indicatorState.volume, () =>
            onChangeIndicator({
              ...indicatorState,
              volume: !indicatorState.volume,
            }),
          )}
        </View>

        <View style={styles.divider} />

        {/* Sub indicators */}
        <View style={styles.row}>
          {SUB_INDICATORS.map((opt) =>
            renderOption(opt, indicatorState.mode2 === opt.value, () =>
              toggle(indicatorState.mode2, opt.value as IndicatorMode2, (val) =>
                onChangeIndicator({ ...indicatorState, mode2: val }),
              ),
            ),
          )}
        </View>

        {/* Done */}
        <TouchableOpacity
          onPress={closeSheet}
          style={[styles.doneBtn, { backgroundColor: theme.base.primary }]}
        >
          <Text typography="titleLarge" color="#F2F4F7">
            Xong
          </Text>
        </TouchableOpacity>
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
    paddingHorizontal: 20,
    paddingBottom: 36,
    paddingTop: 12,
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
    justifyContent: "space-between",
    alignItems: "center",
    marginBottom: 16,
  },
  row: {
    flexDirection: "row",
    gap: 8,
  },
  optionBtn: {
    paddingVertical: 4,
    paddingHorizontal: 6,
    borderRadius: 4,
    borderWidth: 1.5,
  },
  divider: {
    height: 1,
    marginVertical: 12,
    backgroundColor: "#e5e7eb",
  },
  doneBtn: {
    marginTop: 24,
    paddingVertical: 10,
    borderRadius: 6,
    alignItems: "center",
  },
});

export default IndicatorBottomSheet;
