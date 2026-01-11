import React from "react";
import { View, TouchableOpacity } from "react-native";
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
      style={{
        marginBottom: 24,
        backgroundColor: theme.background.surface,
        padding: 4,
        borderRadius: 4,
        alignItems: "center",
        flexDirection: "row",
      }}
    >
      <TouchableOpacity
        onPress={() => setTab("signIn")}
        style={{
          flex: 1,
          justifyContent: "center",
          paddingVertical: 8,
          borderTopLeftRadius: 4,
          borderBottomLeftRadius: 4,
          backgroundColor: tab === "signIn" ? theme.base.primary : undefined,
          borderWidth: 1,
          borderColor:
            tab === "signIn" ? theme.base.primary : theme.border.default,
        }}
      >
        <Text
          typography="titleMedium"
          color={tab === "signIn" ? theme.text.onPrimary : theme.text.primary}
          style={{ textAlign: "center" }}
        >
          {t("auth.signIn")}
        </Text>
      </TouchableOpacity>

      <TouchableOpacity
        onPress={() => setTab("signUp")}
        style={{
          flex: 1,
          justifyContent: "center",
          paddingVertical: 8,
          borderTopRightRadius: 4,
          borderBottomRightRadius: 4,
          backgroundColor: tab === "signUp" ? theme.base.primary : undefined,
          borderWidth: 1,
          borderColor:
            tab === "signUp" ? theme.base.primary : theme.border.default,
        }}
      >
        <Text
          typography="titleMedium"
          color={tab === "signUp" ? theme.text.onPrimary : theme.text.primary}
          style={{ textAlign: "center" }}
        >
          {t("auth.signUp")}
        </Text>
      </TouchableOpacity>
    </View>
  );
};

export default AuthenticationTab;
