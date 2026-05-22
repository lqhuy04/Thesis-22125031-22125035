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
};

export const SearchBar = ({
  value,
  onChange,
  onSearchPress,
  autoFocus = false,
}: SearchBarProps) => {
  const { theme } = useTheme();
  const { t } = useLocalization();

  return (
    <View>
      <View>
        <TextInput
          style={{
            borderWidth: 1,
            borderColor: theme.border.default,
            borderRadius: 8,
            paddingVertical: 10,
            paddingLeft: 44,
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
          }}
          autoFocus={autoFocus}
        />

        {/* Kính lúp bên trái */}
        <Ionicons
          name="search-outline"
          size={20}
          color={theme.text.primary}
          style={{ position: "absolute", left: 12, bottom: 10, zIndex: 1 }}
        />

        {/* Nút xoá bên phải — chỉ hiện khi có text */}
        {value ? (
          <TouchableOpacity
            onPress={() => onChange("")}
            style={{
              position: "absolute",
              right: 12,
              bottom: 10,
            }}
          >
            <Ionicons
              name="close-circle"
              size={20}
              color={theme.text.primary + "80"}
            />
          </TouchableOpacity>
        ) : null}
      </View>
    </View>
  );
};
