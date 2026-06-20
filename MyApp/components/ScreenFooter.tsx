import React from "react";
import {
  ActivityIndicator,
  TouchableOpacity,
  View,
  StyleSheet,
} from "react-native";
import { useSafeAreaInsets } from "react-native-safe-area-context";
import { useTheme } from "@/hooks/ThemeContext";
import { useLocalization } from "@/hooks/LocalizationContext";
import { Text } from "@/components/ui/Text";

interface Props {
  onPressBuy?: () => void;
  loading?: boolean;
  disabled?: boolean;
}

const ScreenFooter = ({ onPressBuy, loading = false, disabled = false }: Props) => {
  const insets = useSafeAreaInsets();
  const { theme } = useTheme();
  const { t } = useLocalization();

  return (
    <View
      style={[
        styles.container,
        {
          paddingBottom: insets.bottom + 12,
          backgroundColor: theme.background.bg,
          borderTopColor: theme.border.default,
        },
      ]}
    >
      <TouchableOpacity
        activeOpacity={0.85}
        onPress={onPressBuy}
        disabled={loading || disabled}
        style={[
          styles.buyButton,
          {
            backgroundColor: theme.base.primary,
            opacity: loading || disabled ? 0.6 : 1,
          },
        ]}
      >
        {loading ? (
          <ActivityIndicator color={theme.text.onPrimary} />
        ) : (
          <Text typography="titleMedium" color={theme.text.onPrimary}>
            {t("detail.buy")}
          </Text>
        )}
      </TouchableOpacity>
    </View>
  );
};

const styles = StyleSheet.create({
  container: {
    paddingHorizontal: 12,
    paddingTop: 12,
    borderTopWidth: StyleSheet.hairlineWidth,
    // Shadow iOS
    shadowColor: "#000",
    shadowOffset: { width: 0, height: -2 },
    shadowOpacity: 0.08,
    shadowRadius: 4,
    // Shadow Android
    elevation: 8,
  },
  buyButton: {
    flexDirection: "row",
    alignItems: "center",
    justifyContent: "center",
    paddingVertical: 14,
    borderRadius: 12,
  },
});

export default ScreenFooter;
