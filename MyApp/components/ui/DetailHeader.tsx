import { useTheme } from "@/hooks/ThemeContext";
import React from "react";
import { View, Image } from "react-native";
import { Text } from "./Text";
import { SearchStockItem } from "@/helpers/SearchHelper";
import { PriceData } from "@/helpers/DetailHelpers";

interface SearchResultItemProps {
  item: SearchStockItem;
  priceData: PriceData | null;
}

const SearchResultItem = ({ item, priceData }: SearchResultItemProps) => {
  const { theme } = useTheme();

  return (
    <View>
      <View
        style={{
          paddingHorizontal: 16,
          paddingVertical: 12,
          backgroundColor: theme.base.primary,
          borderRadius: 4,
          flexDirection: "row",
          alignItems: "center",
          marginTop: 12,
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
          {priceData?.current_price != null ? (
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
                  priceData?.price_change_percent != null &&
                  priceData?.price_change_percent >= 0
                    ? theme.base.success
                    : theme.base.error
                }
              >
                {priceData?.price_change_percent != null &&
                priceData?.price_change_percent >= 0
                  ? "+"
                  : ""}
                {priceData?.price_change_percent}%
              </Text>
            </View>
          ) : null}
          {priceData?.current_price != null ? (
            <Text typography="titleSmall" color={theme.text.onPrimary}>
              {priceData?.current_price}
            </Text>
          ) : null}
        </View>
      </View>

      <View
        style={{
          flexDirection: "row",
          alignItems: "center",
          marginTop: 12,
          marginHorizontal: 12,
          backgroundColor: theme.background.surface,
          paddingVertical: 8,
          paddingHorizontal: 12,
          borderRadius: 4,
          borderWidth: 1,
          borderColor: theme.base.primary,
        }}
      >
        <View style={{ flex: 1 }}>
          <Text typography="bodyMedium">Sàn</Text>
          <Text typography="labelLarge" color={theme.base.error}>
            {priceData?.floor_price}
          </Text>
        </View>
        <View
          style={{ flex: 1, justifyContent: "center", alignItems: "center" }}
        >
          <Text typography="bodyMedium">Tham chiếu</Text>
          <Text typography="labelLarge" color={theme.base.warning}>
            {priceData?.reference_price}
          </Text>
        </View>
        <View
          style={{
            flex: 1,
            justifyContent: "flex-end",
            alignItems: "flex-end",
          }}
        >
          <Text typography="bodyMedium">Trần</Text>
          <Text typography="labelLarge" color={theme.base.success}>
            {priceData?.ceiling_price}
          </Text>
        </View>
      </View>
    </View>
  );
};

export default SearchResultItem;
