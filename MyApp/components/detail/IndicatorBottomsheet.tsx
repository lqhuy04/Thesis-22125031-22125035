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
import { useSafeAreaInsets } from "react-native-safe-area-context";

const { height: SCREEN_HEIGHT } = Dimensions.get("window");

export type IndicatorMode1 = "MA" | "BOLL" | null;
export type IndicatorMode2 = "RSI" | "KDJ" | "MACD" | null;

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

  // Chip giống style của TimeframeBottomSheet
  const renderChip = (
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
          backgroundColor: isSelected
            ? theme.base.primary
            : theme.background.surface,
        },
      ]}
    >
      <Text
        typography="bodyMedium"
        color={isSelected ? theme.text.onPrimary : theme.text.primary}
      >
        {option.label}
      </Text>
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
          {
            backgroundColor: theme.background.bg,
            paddingBottom: insets.bottom + 16,
          },
          { transform: [{ translateY: slideAnim }] },
        ]}
      >
        {/* Handle */}
        <View style={styles.handle} />

        {/* Title — căn giữa như TimeframeBottomSheet */}
        <Text
          typography="titleMedium"
          color={theme.text.primary}
          style={{ textAlign: "center", marginTop: 8 }}
        >
          {t("indicator.title")}
        </Text>

        {/* Divider */}
        <View
          style={{
            width: "100%",
            height: 1,
            backgroundColor: theme.border.default,
            marginTop: 20,
          }}
        />

        {/* Overlay indicators: MA, BOLL */}
        <View style={styles.sectionLabel}>
          <Text typography="labelLarge" color={theme.text.secondary}>
            {t("indicator.overlayIndicators")}
          </Text>
        </View>
        <View style={styles.optionsContainer}>
          {OVERLAY_INDICATORS.map((opt) =>
            renderChip(opt, indicatorState.mode1 === opt.value, () =>
              toggle(indicatorState.mode1, opt.value as IndicatorMode1, (val) =>
                onChangeIndicator({ ...indicatorState, mode1: val }),
              ),
            ),
          )}
        </View>

        {/* Volume */}
        <View style={styles.sectionLabel}>
          <Text typography="labelLarge" color={theme.text.secondary}>
            {t("indicator.volume")}
          </Text>
        </View>
        <View style={styles.optionsContainer}>
          {renderChip(VOLUME_INDICATOR, indicatorState.volume, () =>
            onChangeIndicator({
              ...indicatorState,
              volume: !indicatorState.volume,
            }),
          )}
        </View>

        {/* Sub indicators: MACD, RSI, KDJ */}
        <View style={styles.sectionLabel}>
          <Text typography="labelLarge" color={theme.text.secondary}>
            {t("indicator.subIndicators")}
          </Text>
        </View>
        <View style={styles.optionsContainer}>
          {SUB_INDICATORS.map((opt) =>
            renderChip(opt, indicatorState.mode2 === opt.value, () =>
              toggle(indicatorState.mode2, opt.value as IndicatorMode2, (val) =>
                onChangeIndicator({ ...indicatorState, mode2: val }),
              ),
            ),
          )}
        </View>

        {/* Divider trước nút */}
        <View
          style={{
            width: "100%",
            height: 1,
            backgroundColor: theme.border.default,
            marginTop: 20,
          }}
        />

        {/* Nút hành động: Xóa tất cả (trái) + Xong (phải) */}
        <View style={styles.footer}>
          <TouchableOpacity
            onPress={() =>
              onChangeIndicator({ mode1: null, mode2: null, volume: false })
            }
            style={[
              styles.footerBtn,
              {
                borderWidth: 1.5,
                borderColor: theme.border.default,
                backgroundColor: theme.background.surface,
              },
            ]}
          >
            <Text typography="titleMedium" color={theme.text.primary}>
              {t("indicator.clearAll")}
            </Text>
          </TouchableOpacity>

          <TouchableOpacity
            onPress={closeSheet}
            style={[styles.footerBtn, { backgroundColor: theme.base.primary }]}
          >
            <Text typography="titleMedium" color="#F2F4F7">
              {t("indicator.done")}
            </Text>
          </TouchableOpacity>
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
  sectionLabel: {
    marginTop: 16,
    marginHorizontal: 12,
  },
  optionsContainer: {
    flexDirection: "row",
    marginTop: 8,
    marginHorizontal: 12,
    gap: 8,
  },
  optionBtn: {
    paddingVertical: 6,
    paddingHorizontal: 12,
    borderRadius: 16,
    alignItems: "center",
    justifyContent: "center",
    minWidth: 56,
  },
  footer: {
    flexDirection: "row",
    gap: 10,
    marginHorizontal: 12,
    marginTop: 16,
  },
  footerBtn: {
    flex: 1,
    paddingVertical: 10,
    borderRadius: 10,
    alignItems: "center",
    justifyContent: "center",
  },
});

export default IndicatorBottomSheet;
