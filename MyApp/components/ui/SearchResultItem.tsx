import { useTheme } from "@/hooks/ThemeContext";
import React, { useMemo } from "react";
import { Image, TouchableOpacity, View } from "react-native";
import { Text } from "./Text";
import { SearchStockItem } from "@/helpers/SearchHelper";

interface SearchResultItemProps {
  item: SearchStockItem;
  onPress: () => void;
}

const SearchResultItem = ({ item, onPress }: SearchResultItemProps) => {
  const { theme } = useTheme();

  const currentPrice = useMemo(() => {
    if (!item.current_price) return 0;
    return item.current_price;
  }, [item.current_price]);

  const priceChange = useMemo(() => {
    if (!item.price_change) return 0;
    return item.price_change;
  }, [item.price_change]);

  const perPriceChange = useMemo(() => {
    if (!item.per_price_change) return 0;
    return item.per_price_change;
  }, [item.per_price_change]);

  return (
    <TouchableOpacity
      onPress={onPress}
      style={{
        paddingHorizontal: 16,
        paddingVertical: 12,
        backgroundColor: theme.background.bg,
        borderRadius: 12,
        flexDirection: "row",
        alignItems: "center",
        marginTop: 8,
        borderWidth: 1,
        borderColor: theme.border.default,
        marginHorizontal: 12,
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
        <Text typography="labelLarge" color={theme.text.primary}>
          {item.symbol}
        </Text>
        <Text
          typography="bodySmall"
          color={theme.text.primary}
          numberOfLines={1}
        >
          {item.company_name}
        </Text>
      </View>

      <View style={{ alignItems: "flex-end", marginRight: 4 }}>
        <Text typography="labelLarge" color={theme.text.primary}>
          {currentPrice}
        </Text>
        <Text
          typography="bodySmall"
          color={
            priceChange > 0
              ? theme.base.success
              : priceChange === 0
                ? theme.base.warning
                : theme.base.error
          }
          style={{ textAlign: "right" }}
        >
          {"("}
          {priceChange > 0 ? "+" : ""}
          {priceChange >= 0 ? priceChange : priceChange * -1}
          {")"}
        </Text>
      </View>

      <View
        style={{
          marginLeft: 8,
          borderRadius: 4,
          paddingHorizontal: 8,
          paddingVertical: 4,
          backgroundColor:
            perPriceChange > 0
              ? theme.base.success + "36"
              : perPriceChange === 0
                ? theme.base.warning + "36"
                : theme.base.error + "36",
        }}
      >
        <Text
          typography="labelMedium"
          color={
            perPriceChange > 0
              ? theme.base.success
              : perPriceChange === 0
                ? theme.base.warning
                : theme.base.error
          }
        >
          {perPriceChange > 0 ? "▲" : perPriceChange === 0 ? "" : "▼"}
          {perPriceChange >= 0
            ? perPriceChange?.toFixed(2)
            : (perPriceChange * -1).toFixed(2)}
          %
        </Text>
      </View>
    </TouchableOpacity>
  );
};

export default SearchResultItem;
