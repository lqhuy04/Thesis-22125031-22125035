import { useTheme } from "@/hooks/ThemeContext";
import React from "react";
import { TouchableOpacity, View } from "react-native";
import { Text } from "./Text";
import { SearchStockItem } from "@/helpers/SearchHelper";
import { router } from "expo-router";

interface SearchResultItemProps {
  item: SearchStockItem;
}

const SearchResultItem = ({ item }: SearchResultItemProps) => {
  const { theme } = useTheme();

  return (
    <TouchableOpacity
      onPress={() => {
        router.push(
          {
            pathname: '/Detail',
            params: {data: JSON.stringify(item)},
          }
        );
      }}
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
          backgroundColor: theme.background.primarySurface,
          borderRadius: 2,
        }}
      ></View>

      <View style={{ flex: 1, marginRight: 12 }}>
        <Text typography="titleMedium" color={theme.text.primary}>
          {item.symbol}
        </Text>
        <Text typography="bodyMedium" color={theme.text.primary}>
          {item.name}
        </Text>
      </View>

      <View style={{ alignItems: "flex-end" }}>
        {item.current_price != null ? (
          <Text
            typography="labelLarge"
            color={
              item.price_change_percent != null &&
              item.price_change_percent >= 0
                ? theme.base.success
                : theme.base.error
            }
          >
            {item.price_change_percent != null && item.price_change_percent >= 0
              ? "+"
              : ""}
            {item.price_change_percent}%
          </Text>
        ) : null}
        {item.current_price != null ? (
          <Text typography="titleSmall" color={theme.text.primary}>
            {item.current_price}
            <Text
              typography="titleSmall"
              color={
                item.price_change_percent != null &&
                item.price_change_percent >= 0
                  ? theme.base.success
                  : theme.base.error
              }
            >
              {" "}
              {`(${item.price_change != null && item.price_change >= 0 ? "+" : ""}${item.price_change})`}
            </Text>
          </Text>
        ) : null}
      </View>
    </TouchableOpacity>
  );
};

export default SearchResultItem;
