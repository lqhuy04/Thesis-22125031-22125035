import { useTheme } from "@/hooks/ThemeContext";
import React, { useCallback, useEffect, useMemo, useState } from "react";
import { View, Image, TouchableOpacity } from "react-native";
import { Text } from "./Text";
import {
  fetchCurrentIndexData,
  fetchCurrentPriceData,
} from "@/helpers/DetailHelpers";
import FontAwesome from "@expo/vector-icons/FontAwesome";
import {
  addStockToFavorite,
  checkStockInFavorite,
  deleteStockFromFavorite,
} from "@/helpers/ProfileHelpers";

interface DetailHeaderProps {
  symbol: string;
  chart: React.JSX.Element;
  isMarketIndex?: boolean;
}

const DetailHeader = ({
  symbol,
  chart,
  isMarketIndex = false,
}: DetailHeaderProps) => {
  const { theme } = useTheme();

  const [data, setData] = useState<any>(null);
  const [isFavorite, setIsFavorite] = useState<boolean>(false);

  const toggleFavorite = useCallback(() => {
    setIsFavorite((prev) => {
      if (prev === false) {
        addStockToFavorite(symbol);
      } else {
        deleteStockFromFavorite(symbol);
      }

      return !prev;
    });
  }, [symbol]);

  useEffect(() => {
    checkStockInFavorite(symbol).then((res) => {
      if (res?.status) {
        setIsFavorite(res?.data);
      }
    });
  }, [symbol]);

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
      logo: isMarketIndex
        ? "https://ddazflrupjwuxlxlszbk.supabase.co/storage/v1/object/public/icons/office.png"
        : data?.logo,
      symbol: isMarketIndex ? data?.IndexId : data?.symbol,
      company_name: isMarketIndex ? data?.IndexName : data?.company_name,
      exchange: isMarketIndex ? "" : data?.exchange,
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
          backgroundColor: theme.background.bg,
          borderRadius: 12,

          marginHorizontal: 12,
        }}
      >
        <View
          style={{
            flexDirection: "row",
            alignItems: "center",
          }}
        >
          <Image
            source={{
              uri:
                displayData?.logo ||
                "https://ddazflrupjwuxlxlszbk.supabase.co/storage/v1/object/public/icons/office.png",
            }}
            style={{
              marginRight: 8,
              width: 48,
              height: 48,
              borderRadius: 4,
              backgroundColor: theme.background.bg,
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
              <Text typography="titleMedium" color={theme.text.primary}>
                {displayData?.symbol}
              </Text>

              {displayData?.company_name?.length > 0 ? (
                <View
                  style={{
                    paddingVertical: 2,
                    paddingHorizontal: 4,
                    borderRadius: 2,
                    backgroundColor: theme.text.primary + "36",
                    marginLeft: 8,
                  }}
                >
                  <Text typography="bodySmall" color={theme.text.primary}>
                    {displayData?.exchange}
                  </Text>
                </View>
              ) : null}
            </View>
            <Text typography="bodyMedium" color={theme.text.primary + "80"}>
              {displayData?.company_name}
            </Text>
          </View>

          <View
            style={{
              alignItems: "center",
              justifyContent: "center",
            }}
          >
            <TouchableOpacity onPress={toggleFavorite}>
              {isFavorite ? (
                <FontAwesome name="star" size={24} color={theme.base.warning} />
              ) : (
                <FontAwesome
                  name="star-o"
                  size={24}
                  color={theme.base.warning}
                />
              )}
            </TouchableOpacity>

            <Text typography="bodySmall" color={theme.text.primary}>
              {"Theo dõi"}
            </Text>
          </View>
        </View>

        <View
          style={{ flexDirection: "row", alignItems: "center", marginTop: 8 }}
        >
          <Text typography="headlineSmall" color={theme.text.primary}>
            {displayData?.CurrentPrice?.toLocaleString("vi-VN", {
              minimumFractionDigits: 1,
              maximumFractionDigits: 1,
            })}
          </Text>

          <View
            style={{
              marginHorizontal: 8,
              borderRadius: 4,
              paddingHorizontal: 4,
              paddingBottom: 2,
              paddingTop: 1,
              backgroundColor:
                displayData?.PriceChange > 0
                  ? theme.base.success + "36"
                  : displayData?.PriceChange === 0
                    ? theme.base.warning + "36"
                    : theme.base.error + "36",
            }}
          >
            <Text
              typography="labelMedium"
              color={
                displayData?.PriceChange > 0
                  ? theme.base.success
                  : displayData?.PriceChange === 0
                    ? theme.base.warning
                    : theme.base.error
              }
            >
              {displayData?.PriceChange > 0
                ? "▲"
                : displayData?.PriceChange === 0
                  ? ""
                  : "▼"}
              {displayData?.PriceChange >= 0
                ? displayData?.PriceChange?.toFixed(1)
                : (displayData?.PriceChange * -1).toFixed(1)}
            </Text>
          </View>

          <Text
            typography="labelSmall"
            color={
              displayData?.PerPriceChange > 0
                ? theme.base.success
                : displayData?.PerPriceChange === 0
                  ? theme.base.warning
                  : theme.base.error
            }
          >
            {displayData?.PerPriceChange > 0
              ? "▲"
              : displayData?.PerPriceChange === 0
                ? ""
                : "▼"}
            {displayData?.PerPriceChange >= 0
              ? displayData?.PerPriceChange?.toFixed(1)
              : (displayData?.PerPriceChange * -1).toFixed(1)}
            %
          </Text>
        </View>
      </View>

      {chart}

      <Text
        typography="titleMedium"
        color={theme.text.primary}
        style={{ marginHorizontal: 12, marginVertical: 12 }}
      >
        {"Biến động trong ngày"}
      </Text>

      <View
        style={{
          marginHorizontal: 12,
          marginBottom: 12,
          backgroundColor: theme.background.bg,
          paddingVertical: 8,
          paddingHorizontal: 12,
          borderRadius: 12,
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
              <Text typography="bodyMedium" color={theme.text.primary}>
                Sàn
              </Text>
              <Text typography="titleMedium" color={theme.base.error}>
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
              <Text typography="bodyMedium" color={theme.text.primary}>
                Tham chiếu
              </Text>
              <Text typography="titleMedium" color={theme.base.warning}>
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
              <Text typography="bodyMedium" color={theme.text.primary}>
                Trần
              </Text>
              <Text typography="titleMedium" color={theme.base.success}>
                {displayData?.CeilingPrice}
              </Text>
            </View>
          </View>
        )}

        <View
          style={{
            padding: 12,
            borderRadius: 8,
            backgroundColor: theme.background.surface,
          }}
        >
          <View
            style={{
              flexDirection: "row",
              justifyContent: "space-between",
            }}
          >
            <Text typography="bodyMedium" color={theme.text.primary}>
              Khối lượng giao dịch
            </Text>
            <Text typography="titleMedium" color={theme.text.primary}>
              {displayData?.TotalMatchVol} cp
            </Text>
          </View>

          <View
            style={{
              borderBottomWidth: 1,
              borderBottomColor: theme.border.default,
              marginVertical: 12,
            }}
          />

          <View
            style={{ flexDirection: "row", justifyContent: "space-between" }}
          >
            <Text typography="bodyMedium" color={theme.text.primary}>
              Giá trị giao dịch
            </Text>
            <Text typography="titleMedium" color={theme.text.primary}>
              {(Number(displayData?.TotalMatchVal) / 1000000000).toFixed(2)} tỷ
              đồng
            </Text>
          </View>
        </View>
      </View>
    </View>
  );
};

export default DetailHeader;
