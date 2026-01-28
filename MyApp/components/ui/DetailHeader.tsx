import { useTheme } from "@/hooks/ThemeContext";
import React from "react";
import { View, Image } from "react-native";
import { Text } from "./Text";
import { SearchStockItem } from "@/helpers/SearchHelper";

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
        backgroundColor: theme.base.primary,
        borderRadius: 4,
        flexDirection: "row",
        alignItems: "center",
      }}
    >
      <Image
        source={{
          uri: "https://ibrand.vn/wp-content/uploads/2024/08/vinamilk-logo_brandlogos.net_quayf.png",
        }}
        style={{
          marginRight: 8,
          width: 40,
          height: 40,
          borderRadius: 2,
          backgroundColor: theme.text.onPrimary,
        }}
      />

      <View style={{ flex: 1, marginRight: 12 }}>
        <Text typography="titleMedium" color={theme.text.onPrimary}>
          {item.symbol}
        </Text>
        <Text typography="bodyMedium" color={theme.text.onPrimary}>
          {item.name}
        </Text>
      </View>

      <View style={{ alignItems: "flex-end" }}>
        {item.current_price != null ? (
          <View
            style={{
              paddingHorizontal: 4,
              paddingVertical: 2,
              borderRadius: 2,
              backgroundColor: theme.base.info,
              marginBottom: 2,
            }}
          >
            <Text
              typography="labelLarge"
              color={
                item.price_change_percent != null &&
                item.price_change_percent >= 0
                  ? theme.base.success
                  : theme.base.error
              }
            >
              {item.price_change_percent != null &&
              item.price_change_percent >= 0
                ? "+"
                : ""}
              {item.price_change_percent}%
            </Text>
          </View>
        ) : null}
        {item.current_price != null ? (
          <Text typography="titleSmall" color={theme.text.onPrimary}>
            {item.current_price}
          </Text>
        ) : null}
      </View>
    </View>
  );
};

export default SearchResultItem;
