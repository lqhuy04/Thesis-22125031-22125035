import { useTheme } from "@/hooks/ThemeContext";
import React, { useEffect, useState } from "react";
import { View, Image } from "react-native";
import { Text } from "./Text";
import {
  CurrentPriceData,
  fetchCurrentPriceData,
} from "@/helpers/DetailHelpers";

interface SearchResultItemProps {
  symbol: string;
}

const SearchResultItem = ({ symbol }: SearchResultItemProps) => {
  const { theme } = useTheme();

  const [data, setData] = useState<CurrentPriceData | null>(null);

  useEffect(() => {
    fetchCurrentPriceData(symbol).then((res) => {
      if (res?.status) setData(res?.data);
    });
  }, [symbol]);

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
            {data?.symbol}
          </Text>
          <Text typography="bodyMedium" color={theme.text.onPrimary}>
            {data?.company_name}
          </Text>
        </View>

        <View style={{ alignItems: "flex-end" }}>
          {data?.CurrentPrice != null ? (
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
                  data?.PerPriceChange != null && data?.PerPriceChange >= 0
                    ? theme.base.success
                    : theme.base.error
                }
              >
                {data?.PerPriceChange != null && data?.PerPriceChange >= 0
                  ? "+"
                  : ""}
                {data?.PerPriceChange}%
              </Text>
            </View>
          ) : null}
          {data?.CurrentPrice != null ? (
            <Text typography="titleSmall" color={theme.text.onPrimary}>
              {data?.CurrentPrice}
            </Text>
          ) : null}
        </View>
      </View>

      <View
        style={{
          flexDirection: "row",
          alignItems: "center",
          marginHorizontal: 12,
          marginVertical: 12,
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
            {data?.FloorPrice}
          </Text>
        </View>
        <View
          style={{
            flex: 1,
            justifyContent: "center",
            alignItems: "center",
          }}
        >
          <Text typography="bodyMedium">Tham chiếu</Text>
          <Text typography="labelLarge" color={theme.base.warning}>
            {data?.RefPrice}
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
            {data?.CeilingPrice}
          </Text>
        </View>
      </View>
    </View>
  );
};

export default SearchResultItem;
