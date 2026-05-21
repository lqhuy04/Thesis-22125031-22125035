import React from "react";
import { TouchableOpacity, View, StyleSheet } from "react-native";
import MaterialIcons from "@expo/vector-icons/MaterialIcons";
import { Text } from "./Text";
import { router } from "expo-router";
import { useSafeAreaInsets } from "react-native-safe-area-context";
import { useTheme } from "@/hooks/ThemeContext";
interface Props {
  title: string;
  hiddenBack?: boolean;
  onPressBack?: () => void;
}

const ScreenHeader = ({ hiddenBack = false, title, onPressBack }: Props) => {
  const insets = useSafeAreaInsets();
  const { theme } = useTheme();

  return (
    <View
      style={[
        styles.container,
        {
          paddingTop: insets.top + 8,
          backgroundColor: theme.background.bg,
        },
      ]}
    >
      {!hiddenBack && (
        <TouchableOpacity
          style={{
            width: 28,
            height: 28,
            borderRadius: 14,
            backgroundColor: theme.border.default,
            alignItems: "center",
            justifyContent: "center",
            marginRight: 12,
          }}
          onPress={() =>
            onPressBack != null ? onPressBack() : router.dismiss()
          }
        >
          <MaterialIcons
            name="chevron-left"
            size={24}
            color={theme.text.primary}
            style={{ marginRight: 12 }}
          />
        </TouchableOpacity>
      )}

      <Text typography="titleLarge" color={theme.text.primary}>
        {title}
      </Text>
    </View>
  );
};

const styles = StyleSheet.create({
  container: {
    flexDirection: "row",
    alignItems: "center",
    paddingHorizontal: 12,
    paddingBottom: 16,
    // Shadow iOS
    shadowColor: "#000",
    shadowOffset: { width: 0, height: 2 },
    shadowOpacity: 0.08,
    shadowRadius: 4,
    // Shadow Android
    elevation: 4,
  },
  backIcon: {
    marginRight: 16,
  },
});

export default ScreenHeader;
