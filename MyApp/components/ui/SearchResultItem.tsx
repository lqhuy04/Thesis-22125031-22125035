import { useTheme } from "@/hooks/ThemeContext";
import React, { useMemo } from "react";
import { Image, TouchableOpacity, View } from "react-native";
import { Text } from "./Text";
import { SearchStockItem } from "@/helpers/SearchHelper";
import {
  formatPercentageChange,
  formatPriceChange,
  getStockChangeColor,
} from "@/helpers/stockChange";

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

  const priceChangeColor = getStockChangeColor(priceChange, theme.base);
  const perPriceChangeColor = getStockChangeColor(perPriceChange, theme.base);

  return (
    <TouchableOpacity
      onPress={onPress}
      style={{
        paddingVertical: 16,
        flexDirection: "row",
        alignItems: "center",
      }}
    >
      <Image
        resizeMode="contain"
        source={{
          uri:
            item.logo ??
            "https://ddazflrupjwuxlxlszbk.supabase.co/storage/v1/object/public/icons/office.png",
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

      <View style={{ alignItems: "flex-start", marginRight: 4 }}>
        <Text typography="labelLarge" color={theme.text.primary}>
          {currentPrice.toLocaleString("vi-VN", {
            minimumFractionDigits: 2,
            maximumFractionDigits: 2,
          })}
        </Text>
        <Text
          typography="bodySmall"
          color={priceChangeColor}
          style={{ textAlign: "right" }}
        >
          {"("}
          {formatPriceChange(priceChange)}
          {")"}
        </Text>
      </View>

      <View
        style={{
          marginLeft: 8,
          borderRadius: 4,
          width: 70,
          paddingVertical: 6,
          alignItems: "center",
          justifyContent: "center",
          backgroundColor: perPriceChangeColor + "36",
        }}
      >
        <Text
          typography="labelMedium"
          color={perPriceChangeColor}
        >
          {formatPercentageChange(perPriceChange)}
        </Text>
      </View>
    </TouchableOpacity>
  );
};

export default SearchResultItem;
