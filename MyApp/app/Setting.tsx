import { useTheme } from "@/hooks/ThemeContext";
import React from "react";
import { SafeAreaView } from "react-native-safe-area-context";
import { View, Switch } from "react-native";
import { Text } from "@/components/ui/Text";
import ScreenHeader from "@/components/ui/ScreenHeader";
import { Language, useLocalization } from "@/hooks/LocalizationContext";
import DropDown from "@/components/ui/Dropdown";

const Setting = () => {
  const { theme, toggleTheme, isDark } = useTheme();
  const { language, setLanguage, languageOptions, t } = useLocalization();

  return (
    <SafeAreaView
      style={{
        flex: 1,
        backgroundColor: theme.background.bg,
      }}
    >
      <ScreenHeader title={t("setting.settingScreenTitle")} />

      <View
        style={{
          flexDirection: "row",
          alignItems: "center",
          justifyContent: "space-between",
          marginHorizontal: 12,
        }}
      >
        <Text typography="titleMedium" color={theme.text.primary}>
          {t("setting.darkMode")}
        </Text>
        <Switch
          trackColor={{ false: "#767577", true: "#81b0ff" }}
          thumbColor={isDark ? "#f5dd4b" : "#f4f3f4"}
          ios_backgroundColor="#3e3e3e"
          onValueChange={toggleTheme}
          value={isDark}
        />
      </View>

      <View
        style={{
          flexDirection: "row",
          alignItems: "flex-start",
          justifyContent: "space-between",
          marginHorizontal: 12,
        }}
      >
        <Text
          typography="titleMedium"
          color={theme.text.primary}
          style={{ marginTop: 12 }}
        >
          {t("setting.language")}
        </Text>
        <DropDown
          data={languageOptions}
          setSelected={(val) => {
            setLanguage(val as Language);
          }}
          value={language}
        />
      </View>
    </SafeAreaView>
  );
};

export default Setting;
