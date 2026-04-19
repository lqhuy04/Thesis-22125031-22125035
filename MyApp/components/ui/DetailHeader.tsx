import { useTheme } from "@/hooks/ThemeContext";
import React, { useEffect, useMemo, useState } from "react";
import { View, Image } from "react-native";
import { Text } from "./Text";
import {
  fetchCurrentIndexData,
  fetchCurrentPriceData,
} from "@/helpers/DetailHelpers";

interface SearchResultItemProps {
  symbol: string;
  isMarketIndex?: boolean;
}

const SearchResultItem = ({
  symbol,
  isMarketIndex = false,
}: SearchResultItemProps) => {
  const { theme } = useTheme();

  const [data, setData] = useState<any>(null);

  useEffect(() => {
    if (isMarketIndex) {
      fetchCurrentIndexData(symbol).then((res) => {
        if (res?.status) setData(res?.data);
      });
    } else {
      fetchCurrentPriceData(symbol).then((res) => {
        if (res?.status) setData(res?.data);
      });
    }
  }, [isMarketIndex, symbol]);

  const displayData = useMemo(() => {
    if (!data) return null;
    return {
      symbol: isMarketIndex ? data?.IndexId : data?.symbol,
      company_name: isMarketIndex ? data?.IndexName : data?.company_name,
      CurrentPrice: isMarketIndex ? data?.IndexValue : data?.CurrentPrice,
      PriceChange: isMarketIndex ? data?.Change : data?.PriceChange,
      PerPriceChange: isMarketIndex ? data?.RatioChange : data?.PerPriceChange,
      FloorPrice: data?.FloorPrice ?? 0,
      RefPrice: data?.RefPrice ?? 0,
      CeilingPrice: data?.CeilingPrice ?? 0,
      TotalMatchVol: data?.TotalMatchVol ?? 0,
      TotalMatchVal: data?.TotalMatchVal ?? 0,
    };
  }, [data, isMarketIndex]);

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
          <View
            style={{
              flexDirection: "row",
              alignItems: "center",
              marginBottom: 2,
            }}
          >
            <Text typography="titleMedium" color={theme.text.onPrimary}>
              {displayData?.symbol}
            </Text>
            <View
              style={{
                padding: 2,
                backgroundColor:
                  displayData?.PriceChange >= 0
                    ? theme.base.success + "18"
                    : theme.base.error + "18",
                borderRadius: 2,
                marginLeft: 8,
              }}
            >
              <Text
                typography="labelLarge"
                color={
                  displayData?.PriceChange >= 0
                    ? theme.base.success
                    : theme.base.error
                }
              >
                {displayData?.PriceChange >= 0 ? "+" : ""}
                {displayData?.PriceChange}
              </Text>
            </View>
          </View>
          <Text typography="bodyMedium" color={theme.text.onPrimary}>
            {displayData?.company_name}
          </Text>
        </View>

        <View style={{ alignItems: "flex-end" }}>
          {displayData?.CurrentPrice != null ? (
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
                  displayData?.PerPriceChange != null &&
                  displayData?.PerPriceChange >= 0
                    ? theme.base.success
                    : theme.base.error
                }
              >
                {displayData?.PerPriceChange != null &&
                displayData?.PerPriceChange >= 0
                  ? "+"
                  : ""}
                {displayData?.PerPriceChange}%
              </Text>
            </View>
          ) : null}
          {displayData?.CurrentPrice != null ? (
            <Text typography="titleSmall" color={theme.text.onPrimary}>
              {displayData?.CurrentPrice}
            </Text>
          ) : null}
        </View>
      </View>

      <View
        style={{
          marginHorizontal: 12,
          marginVertical: 12,
          backgroundColor: theme.base.primary + "16",
          paddingVertical: 8,
          paddingHorizontal: 12,
          borderRadius: 4,
        }}
      >
        {isMarketIndex ? null : (
          <View
            style={{
              flexDirection: "row",
              alignItems: "center",
              marginBottom: 8,
            }}
          >
            <View style={{ flex: 1 }}>
              <Text typography="titleSmall">Sàn</Text>
              <Text typography="labelLarge" color={theme.base.error}>
                {displayData?.FloorPrice}
              </Text>
            </View>
            <View
              style={{
                flex: 1,
                justifyContent: "center",
                alignItems: "center",
              }}
            >
              <Text typography="titleSmall">Tham chiếu</Text>
              <Text typography="labelLarge" color={theme.base.warning}>
                {displayData?.RefPrice}
              </Text>
            </View>
            <View
              style={{
                flex: 1,
                justifyContent: "flex-end",
                alignItems: "flex-end",
              }}
            >
              <Text typography="titleSmall">Trần</Text>
              <Text typography="labelLarge" color={theme.base.success}>
                {displayData?.CeilingPrice}
              </Text>
            </View>
          </View>
        )}

        <View
          style={{
            padding: 8,
            borderRadius: 4,
            backgroundColor: theme.background.surface,
          }}
        >
          <View
            style={{
              flexDirection: "row",
              justifyContent: "space-between",
              marginBottom: 4,
            }}
          >
            <Text typography="titleSmall">Khối lượng giao dịch</Text>
            <Text typography="bodyMedium">{displayData?.TotalMatchVol} cp</Text>
          </View>

          <View
            style={{ flexDirection: "row", justifyContent: "space-between" }}
          >
            <Text typography="titleSmall">Giá trị giao dịch</Text>
            <Text typography="bodyMedium">
              {(Number(displayData?.TotalMatchVal) / 1000000000).toFixed(2)} tỷ
              đồng
            </Text>
          </View>
        </View>
      </View>
    </View>
  );
};

export default SearchResultItem;
