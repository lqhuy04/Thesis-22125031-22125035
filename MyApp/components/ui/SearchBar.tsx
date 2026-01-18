import React from "react";
import { View, TextInput, TouchableOpacity } from "react-native";
import { Ionicons } from "@expo/vector-icons";
import { useTheme } from "@/hooks/ThemeContext";
import { useLocalization } from "@/hooks/LocalizationContext";

type SearchBarProps = {
  value: string;
  onChange: (text: string) => void;
  onSearchPress?: () => void;
};

export const SearchBar = ({
  value,
  onChange,
  onSearchPress,
}: SearchBarProps) => {
  const { theme } = useTheme();
  const { t } = useLocalization();

  return (
    <View>
      <TextInput
        style={{
          borderWidth: 1,
          borderColor: theme.border.default,
          borderRadius: 5,
          paddingVertical: 10,
          paddingHorizontal: 16,
          marginTop: 4,
          color: theme.text.primary,
        }}
        value={value}
        onChangeText={onChange}
        autoCapitalize="none"
        returnKeyType="search"
        placeholder={t("home.search")}
      />

      <TouchableOpacity
        onPress={onSearchPress}
        style={{ position: "absolute", right: 12, top: 14 }}
      >
        <Ionicons name="search-outline" size={20} color={theme.text.primary} />
      </TouchableOpacity>
    </View>
  );
};
