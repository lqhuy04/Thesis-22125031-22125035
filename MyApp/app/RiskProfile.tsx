import { useTheme } from "@/hooks/ThemeContext";
import React from "react";
import { SafeAreaView } from "react-native-safe-area-context";
import { View, Switch } from "react-native";
import { Text } from "@/components/ui/Text";
import ScreenHeader from "@/components/ui/ScreenHeader";
import { Language, useLocalization } from "@/hooks/LocalizationContext";
import DropDown from "@/components/ui/Dropdown";

const RiskProfile = () => {
  const { theme, toggleTheme, isDark } = useTheme();
  const { language, setLanguage, languageOptions, t } = useLocalization();

  return (
    <SafeAreaView
      style={{
        flex: 1,
        backgroundColor: theme.background.bg,
      }}
    >
      <ScreenHeader title={"Khẩu vị rủi ro"} />
    </SafeAreaView>
  );
};

export default RiskProfile;
