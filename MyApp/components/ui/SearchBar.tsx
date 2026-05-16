import React from "react";
import { View, TextInput, TouchableOpacity } from "react-native";
import { Ionicons } from "@expo/vector-icons";
import { useTheme } from "@/hooks/ThemeContext";

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

  return (
    <View>
      <TextInput
        style={{
          borderWidth: 1,
          borderColor: theme.border.default,
          borderRadius: 8,
          paddingVertical: 10,
          paddingHorizontal: 16,
          marginTop: 4,
          width: "100%",
          color: theme.text.primary,
        }}
        value={value}
        onChangeText={onChange}
        autoCapitalize="none"
        returnKeyType="search"
        placeholder="Tìm kiếm theo mã chứng khoán, tên công ty..."
        onBlur={() => {
          if (value.trim() !== "") onSearchPress?.();
          onBlur?.();
        }}
        onFocus={onFocus}
        autoFocus={autoFocus}
      />

      <TouchableOpacity
        onPress={onSearchPress}
        style={{ position: "absolute", right: 16, top: 14 }}
      >
        <Ionicons name="search-outline" size={20} color={theme.text.primary} />
      </TouchableOpacity>
    </View>
  );
};
