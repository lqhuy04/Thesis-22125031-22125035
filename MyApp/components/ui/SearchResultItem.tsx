import { useTheme } from "@/hooks/ThemeContext";
import React from "react";
import { Image, TouchableOpacity, View } from "react-native";
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
        router.push({
          pathname: "/Detail",
          params: { data: item.symbol },
        });
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
      <Image
        source={{
          uri: "https://ibrand.vn/wp-content/uploads/2024/08/vinamilk-logo_brandlogos.net_quayf.png",
        }}
        style={{
          marginRight: 8,
          width: 40,
          height: 40,
          borderRadius: 2,
        }}
      />

      <View style={{ flex: 1, marginRight: 12 }}>
        <Text typography="titleMedium" color={theme.text.primary}>
          {item.symbol}
        </Text>
        <Text typography="bodyMedium" color={theme.text.primary}>
          {item.company_name}
        </Text>
      </View>
    </TouchableOpacity>
  );
};

export default SearchResultItem;
