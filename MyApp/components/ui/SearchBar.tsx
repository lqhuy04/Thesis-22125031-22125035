import React from "react";
import { View, TextInput, TouchableOpacity } from "react-native";
import { Ionicons } from "@expo/vector-icons";
import { useTheme } from "@/hooks/ThemeContext";
import { useLocalization } from "@/hooks/LocalizationContext";

type SearchBarProps = {
  value: string;
  onChange: (text: string) => void;
  onSearchPress?: () => void;
  autoFocus?: boolean;
  onFocus?: () => void;
  onBlur?: () => void;
};

export const SearchBar = ({
  value,
  onChange,
  onSearchPress,
  autoFocus = false,
  onFocus,
  onBlur,
}: SearchBarProps) => {
  const { theme } = useTheme();
  const { t } = useLocalization();

  return (
    <View>
      {/* Kính lúp bên trái */}
      <Ionicons
        name="search-outline"
        size={20}
        color={theme.text.primary}
        style={{ position: "absolute", left: 12, top: 12, zIndex: 1 }}
      />

      <TextInput
        style={{
          borderWidth: 1,
          borderColor: theme.border.default,
          borderRadius: 8,
          paddingVertical: 10,
          paddingLeft: 44,
          paddingRight: value ? 44 : 16,
          marginTop: 4,
          width: "100%",
          color: theme.text.primary,
          backgroundColor: theme.background.bg,
        }}
        value={value}
        onChangeText={onChange}
        autoCapitalize="none"
        returnKeyType="search"
        placeholder={t("common.searchPlaceholder")}
        placeholderTextColor={theme.text.primary}
        onBlur={() => {
          if (value.trim() !== "") onSearchPress?.();
          onBlur?.();
        }}
        onFocus={onFocus}
        autoFocus={autoFocus}
      />

      {/* Nút xoá bên phải — chỉ hiện khi có text */}
      {value ? (
        <TouchableOpacity
          onPress={() => onChange("")}
          style={{ position: "absolute", right: 12, top: 12 }}
        >
          <Ionicons
            name="close-circle"
            size={20}
            color={theme.text.primary + "80"}
          />
        </TouchableOpacity>
      ) : null}
    </View>
  );
};
