import React from "react";
import { View, TextInput, TouchableOpacity } from "react-native";
import { Ionicons } from "@expo/vector-icons";
import { useTheme } from "@/hooks/ThemeContext";

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
        placeholder={"Tìm kiếm theo mã chứng khoán, tên công ty..."}
        onBlur={onSearchPress}
        autoFocus={autoFocus}
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
