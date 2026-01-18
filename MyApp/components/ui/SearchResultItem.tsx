import { useTheme } from "@/hooks/ThemeContext";
import { SearchStockItem } from "@/models";
import React from "react";
import { View } from "react-native";
import { Text } from "./Text";

interface SearchResultItemProps {
  item: SearchStockItem;
}

const SearchResultItem = ({ item }: SearchResultItemProps) => {
  const { theme } = useTheme();

  return (
    <View
      style={{
        paddingHorizontal: 16,
        paddingVertical: 12,
        backgroundColor: theme.background.surface,
        borderRadius: 4,
        flexDirection: "row",
        alignItems: "center",
        marginTop: 16,
      }}
    >
      <View
        style={{
          marginRight: 8,
          width: 40,
          height: 40,
          backgroundColor: "red",
          borderRadius: 2,
        }}
      ></View>

      <View style={{ flex: 1 }}>
        <Text typography="titleMedium" color={theme.text.primary}>
          {item.code}
        </Text>
        <Text typography="bodyMedium" color={theme.text.primary}>
          {item.name}
        </Text>
      </View>

      <View style={{ alignItems: "flex-end" }}>
        <Text
          typography="labelLarge"
          color={item.difference >= 0 ? theme.base.success : theme.base.error}
        >
          {item.difference >= 0 ? "+" : "-"}
          {item.difference.toFixed(2)}%
        </Text>
        <Text typography="titleSmall" color={theme.text.primary}>
          {item.currentPrice.toFixed(1)}
        </Text>
      </View>
    </View>
  );
};

export default SearchResultItem;
