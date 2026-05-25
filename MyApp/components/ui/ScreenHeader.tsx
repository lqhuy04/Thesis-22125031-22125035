import React from "react";
import { TouchableOpacity, View, StyleSheet } from "react-native";
import { Text } from "./Text";
import { router } from "expo-router";
import { useSafeAreaInsets } from "react-native-safe-area-context";
import { useTheme } from "@/hooks/ThemeContext";
import Entypo from "@expo/vector-icons/Entypo";

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
            width: 20,
            height: 20,
            borderRadius: 10,
            backgroundColor: theme.border.default,
            alignItems: "center",
            justifyContent: "center",
            marginRight: 12,
          }}
          onPress={() =>
            onPressBack != null ? onPressBack() : router.dismiss()
          }
        >
          <Entypo
            name="chevron-small-left"
            size={16}
            color={theme.text.primary}
          />
        </TouchableOpacity>
      )}

      <Text typography="titleMedium" color={theme.text.primary}>
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
