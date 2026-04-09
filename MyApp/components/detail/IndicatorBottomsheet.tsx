import React, { useRef } from "react";
import {
  Modal,
  Animated,
  Pressable,
  StyleSheet,
  Text,
  TouchableOpacity,
  View,
  Dimensions,
} from "react-native";
import { useTheme } from "@/hooks/ThemeContext";
import { MaterialCommunityIcons } from "@expo/vector-icons";

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
  description: string;
}

const OVERLAY_INDICATORS: IndicatorOption[] = [
  { label: "MA", value: "MA", description: "Moving Average" },
  { label: "BOLL", value: "BOLL", description: "Bollinger Bands" },
];

const SUB_INDICATORS: IndicatorOption[] = [
  { label: "RSI", value: "RSI", description: "Relative Strength Index" },
  { label: "KDJ", value: "KDJ", description: "Stochastic Oscillator" },
];

const VOLUME_INDICATOR: IndicatorOption = {
  label: "Volume",
  value: "VOLUME",
  description: "Khối lượng giao dịch",
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
    ]).start(() => onClose());
  };

  const handleToggleMode1 = (value: string) => {
    onChangeIndicator({
      ...indicatorState,
      mode1: indicatorState.mode1 === value ? null : (value as IndicatorMode1),
    });
  };

  const handleToggleVolume = () => {
    onChangeIndicator({
      ...indicatorState,
      volume: !indicatorState.volume,
    });
  };

  const handleToggleMode2 = (value: string) => {
    onChangeIndicator({
      ...indicatorState,
      mode2: indicatorState.mode2 === value ? null : (value as IndicatorMode2),
    });
  };

  const activeCount =
    (indicatorState.mode1 ? 1 : 0) + (indicatorState.mode2 ? 1 : 0);

  const renderOption = (
    option: IndicatorOption,
    isSelected: boolean,
    onToggle: (value: string) => void,
  ) => (
    <TouchableOpacity
      key={option.value}
      onPress={() => onToggle(option.value)}
      style={[
        styles.optionBtn,
        {
          borderColor: isSelected
            ? (theme.base?.primary ?? "#1a56db")
            : (theme.border?.default ?? "#e5e7eb"),
          backgroundColor: isSelected
            ? `${theme.base?.primary ?? "#1a56db"}18`
            : (theme.background?.surface ?? "#f9fafb"),
        },
      ]}
    >
      <View style={styles.optionLeft}>
        <Text
          style={[
            styles.optionLabel,
            {
              color: isSelected
                ? (theme.base?.primary ?? "#1a56db")
                : (theme.text?.primary ?? "#111"),
            },
          ]}
        >
          {option.label}
        </Text>
        <Text
          style={[
            styles.optionDesc,
            { color: theme.text?.secondary ?? "#6b7280" },
          ]}
        >
          {option.description}
        </Text>
      </View>

      {isSelected && (
        <MaterialCommunityIcons
          name="check-circle"
          size={20}
          color={theme.base?.primary ?? "#1a56db"}
        />
      )}
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
          { backgroundColor: theme.background?.surface ?? "#fff" },
          { transform: [{ translateY: slideAnim }] },
        ]}
      >
        {/* Handle */}
        <View style={styles.handle} />

        {/* Header */}
        <View style={styles.header}>
          <Text
            style={[
              styles.sheetTitle,
              { color: theme.text?.primary ?? "#111" },
            ]}
          >
            Chỉ báo kỹ thuật
          </Text>
          {activeCount > 0 && (
            <TouchableOpacity
              onPress={() =>
                onChangeIndicator({ mode1: null, mode2: null, volume: false })
              }
            >
              <Text
                style={[
                  styles.clearBtn,
                  { color: theme.base?.primary ?? "#1a56db" },
                ]}
              >
                Xoá tất cả
              </Text>
            </TouchableOpacity>
          )}
        </View>

        {/* Overlay indicators */}
        <Text
          style={[
            styles.sectionLabel,
            { color: theme.text?.secondary ?? "#6b7280" },
          ]}
        >
          TRÊN BIỂU ĐỒ GIÁ
        </Text>
        <View style={styles.optionsContainer}>
          {OVERLAY_INDICATORS.map((opt) =>
            renderOption(
              opt,
              indicatorState.mode1 === opt.value,
              handleToggleMode1,
            ),
          )}
        </View>

        {/* Volume indicators */}
        <Text
          style={[
            styles.sectionLabel,
            { color: theme.text?.secondary ?? "#6b7280", marginTop: 16 },
          ]}
        >
          KHỐI LƯỢNG
        </Text>

        <View style={styles.optionsContainer}>
          {renderOption(
            VOLUME_INDICATOR,
            indicatorState.volume,
            handleToggleVolume,
          )}
        </View>

        {/* Sub-chart indicators */}
        <Text
          style={[
            styles.sectionLabel,
            { color: theme.text?.secondary ?? "#6b7280", marginTop: 16 },
          ]}
        >
          BIỂU ĐỒ PHỤ
        </Text>
        <View style={styles.optionsContainer}>
          {SUB_INDICATORS.map((opt) =>
            renderOption(
              opt,
              indicatorState.mode2 === opt.value,
              handleToggleMode2,
            ),
          )}
        </View>

        {/* Done button */}
        <TouchableOpacity
          onPress={closeSheet}
          style={[
            styles.doneBtn,
            { backgroundColor: theme.base?.primary ?? "#1a56db" },
          ]}
        >
          <Text style={styles.doneBtnText}>Xong</Text>
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
    justifyContent: "space-between",
    alignItems: "center",
    marginBottom: 16,
  },
  sheetTitle: {
    fontSize: 15,
    fontWeight: "600",
  },
  clearBtn: {
    fontSize: 13,
    fontWeight: "500",
  },
  sectionLabel: {
    fontSize: 11,
    fontWeight: "600",
    letterSpacing: 0.5,
    marginBottom: 8,
  },
  optionsContainer: {
    gap: 8,
  },
  optionBtn: {
    flexDirection: "row",
    alignItems: "center",
    justifyContent: "space-between",
    paddingVertical: 12,
    paddingHorizontal: 14,
    borderRadius: 10,
    borderWidth: 1.5,
  },
  optionLeft: {
    gap: 2,
  },
  optionLabel: {
    fontSize: 14,
    fontWeight: "600",
  },
  optionDesc: {
    fontSize: 12,
  },
  doneBtn: {
    marginTop: 20,
    paddingVertical: 14,
    borderRadius: 10,
    alignItems: "center",
  },
  doneBtnText: {
    color: "#fff",
    fontSize: 15,
    fontWeight: "600",
  },
});

export default IndicatorBottomSheet;
