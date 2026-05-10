import React from "react";
import { View, TouchableOpacity, StyleSheet } from "react-native";
import { useTheme } from "@/hooks/ThemeContext";
import { Text } from "@/components/ui/Text";
import { useLocalization } from "@/hooks/LocalizationContext";

interface AuthenticationTabProps {
  tab: "signIn" | "signUp";
  setTab: (tab: "signIn" | "signUp") => void;
}

const AuthenticationTab = ({ tab, setTab }: AuthenticationTabProps) => {
  const { theme } = useTheme();
  const { t } = useLocalization();

  return (
    <View
      style={[
        styles.container,
        {
          backgroundColor: theme.background.surface,
          borderColor: theme.border.default,
        },
      ]}
    >
      {(["signIn", "signUp"] as const).map((key) => {
        const isActive = tab === key;
        return (
          <TouchableOpacity
            key={key}
            onPress={() => setTab(key)}
            activeOpacity={0.8}
            style={[
              styles.tab,
              isActive && { backgroundColor: theme.base.primary },
            ]}
          >
            <Text
              typography="titleMedium"
              color={isActive ? theme.text.onPrimary : theme.text.primary}
              style={{ opacity: isActive ? 1 : 0.5 }}
            >
              {t(`auth.${key}`)}
            </Text>
          </TouchableOpacity>
        );
      })}
    </View>
  );
};

export default AuthenticationTab;

const styles = StyleSheet.create({
  container: {
    flexDirection: "row",
    borderRadius: 12,
    borderWidth: 0.5,
    padding: 4,
    marginBottom: 24,
  },
  tab: {
    flex: 1,
    paddingVertical: 10,
    borderRadius: 9,
    alignItems: "center",
    justifyContent: "center",
  },
});
