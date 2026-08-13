import { useTheme } from "@/hooks/ThemeContext";
import React, { useCallback, useEffect, useMemo, useState } from "react";
import { View, Image, TouchableOpacity } from "react-native";
import { Text } from "./Text";
import FontAwesome from "@expo/vector-icons/FontAwesome";
import {
  addStockToFavorite,
  checkStockInFavorite,
  deleteStockFromFavorite,
} from "@/helpers/ProfileHelpers";
import { useLocalization } from "@/hooks/LocalizationContext";
import Feather from "@expo/vector-icons/Feather";
import {
  formatNextOpen,
  getMarketState,
  MarketStatus,
} from "@/helpers/MarketHoursHelper";
import {
  formatPercentageChange,
  formatPriceChange,
  getStockChangeColor,
} from "@/helpers/stockChange";

interface DetailHeaderProps {
  data: any;
  chart: React.JSX.Element;
  isMarketIndex?: boolean;
}

const DetailHeader = ({
  data,
  chart,
  isMarketIndex = false,
}: DetailHeaderProps) => {
  const { theme } = useTheme();
  const { t, language } = useLocalization();

  const [isFavorite, setIsFavorite] = useState<boolean>(false);

  // Đồng hồ cập nhật mỗi phút để trạng thái thị trường luôn chính xác.
  const [now, setNow] = useState<Date>(new Date());
  useEffect(() => {
    const timer = setInterval(() => setNow(new Date()), 60 * 1000);
    return () => clearInterval(timer);
  }, []);

  const toggleFavorite = useCallback(() => {
    setIsFavorite((prev) => {
      if (prev === false) {
        addStockToFavorite(data?.symbol);
      } else {
        deleteStockFromFavorite(data?.symbol);
      }

      return !prev;
    });
  }, [data?.symbol]);

  useEffect(() => {
    if (!isMarketIndex) {
      checkStockInFavorite(data?.symbol).then((res) => {
        if (res?.status) {
          setIsFavorite(res?.data);
        }
      });
    }
  }, [data?.symbol, isMarketIndex]);

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

  const marketState = useMemo(
    () => getMarketState(displayData?.symbol, now),
    [displayData?.symbol, now],
  );

  const marketStatusLabel = useMemo(() => {
    const labels: Record<MarketStatus, string> = {
      open: t("detailHeader.marketOpen"),
      lunch: t("detailHeader.marketLunch"),
      closed: t("detailHeader.marketClosed"),
    };
    return labels[marketState.status];
  }, [marketState.status, t]);

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
        {isMarketIndex ? (
          <View>
            <View
              style={{
                flexDirection: "row",
                alignItems: "center",
                justifyContent: "space-between",
              }}
            >
              <Text typography="headlineSmall" color={theme.text.primary}>
                {displayData?.symbol}
              </Text>
              {marketState.status !== "open" ? (
                <View
                  style={{
                    paddingVertical: 4,
                    paddingHorizontal: 8,
                    borderRadius: 8,
                    backgroundColor: theme.background.surface,
                    flexDirection: "row",
                    alignItems: "center",
                  }}
                >
                  <Feather
                    name="clock"
                    size={16}
                    color={theme.text.primary}
                    style={{ marginRight: 8 }}
                  />
                  <Text typography="labelLarge" color={theme.text.primary}>
                    {marketStatusLabel}
                  </Text>
                </View>
              ) : null}
            </View>

            <View
              style={{
                flexDirection: "row",
                alignItems: "center",
                marginTop: 8,
              }}
            >
              <Text typography="headlineSmall" color={theme.text.primary}>
                {displayData?.CurrentPrice?.toLocaleString("vi-VN", {
                  minimumFractionDigits: 2,
                  maximumFractionDigits: 2,
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
                    getStockChangeColor(displayData?.PriceChange, theme.base) +
                    "36",
                }}
              >
                <Text
                  typography="labelMedium"
                  color={getStockChangeColor(
                    displayData?.PriceChange,
                    theme.base,
                  )}
                >
                  {formatPriceChange(displayData?.PriceChange)}
                </Text>
              </View>

              <Text
                typography="labelSmall"
                color={getStockChangeColor(
                  displayData?.PerPriceChange,
                  theme.base,
                )}
              >
                {formatPercentageChange(displayData?.PerPriceChange)}
              </Text>
            </View>

            {marketState.closeAt ? (
              <Text
                typography="labelLarge"
                color={theme.text.primary + "88"}
                style={{ marginTop: 4 }}
              >
                {`${t("detailHeader.closesAt")} ${formatNextOpen(
                  marketState.closeAt,
                  language,
                )}`}
              </Text>
            ) : marketState.nextOpen ? (
              <Text
                typography="labelLarge"
                color={theme.text.primary + "88"}
                style={{ marginTop: 4 }}
              >
                {`${t("detailHeader.opensAt")} ${formatNextOpen(
                  marketState.nextOpen,
                  language,
                )}`}
              </Text>
            ) : null}
          </View>
        ) : (
          <View>
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
                    <FontAwesome
                      name="star"
                      size={24}
                      color={theme.base.warning}
                    />
                  ) : (
                    <FontAwesome
                      name="star-o"
                      size={24}
                      color={theme.base.warning}
                    />
                  )}
                </TouchableOpacity>

                <Text typography="bodySmall" color={theme.text.primary}>
                  {t("detailHeader.follow")}
                </Text>
              </View>
            </View>

            <View
              style={{
                flexDirection: "row",
                alignItems: "center",
                marginTop: 8,
              }}
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
                    getStockChangeColor(displayData?.PriceChange, theme.base) +
                    "36",
                }}
              >
                <Text
                  typography="labelMedium"
                  color={getStockChangeColor(
                    displayData?.PriceChange,
                    theme.base,
                  )}
                >
                  {formatPriceChange(displayData?.PriceChange)}
                </Text>
              </View>

              <Text
                typography="labelSmall"
                color={getStockChangeColor(
                  displayData?.PerPriceChange,
                  theme.base,
                )}
              >
                {formatPercentageChange(displayData?.PerPriceChange)}
              </Text>
            </View>
          </View>
        )}
      </View>

      {chart}

      <Text
        typography="titleLarge"
        color={theme.text.primary}
        style={{ marginHorizontal: 12, marginVertical: 12 }}
      >
        {t("detailHeader.intradayChange")}
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
        {isMarketIndex ? (
          <View
            style={{
              flexDirection: "row",
              alignItems: "center",
              justifyContent: "center",
              marginVertical: 12,
            }}
          >
            <View
              style={{
                alignItems: "center",
                justifyContent: "center",
                flex: 1,
              }}
            >
              <Text
                typography="bodyMedium"
                color={theme.text.primary + "88"}
                style={{ marginBottom: 8 }}
              >
                {t("detailHeader.tradingVolume")}
              </Text>
              <Text typography="titleMedium" color={theme.text.primary}>
                {displayData?.TotalMatchVol.toLocaleString("vi-VN", { minimumFractionDigits: 0, maximumFractionDigits: 0 })}{" "}
                {t("detailHeader.shares")}
              </Text>
            </View>
            <View
              style={{
                width: 1,
                height: "100%",
                backgroundColor: theme.border.default,
              }}
            />
            <View
              style={{
                alignItems: "center",
                justifyContent: "center",
                flex: 1,
              }}
            >
              <Text
                typography="bodyMedium"
                color={theme.text.primary + "88"}
                style={{ marginBottom: 8 }}
              >
                {t("detailHeader.tradingValue")}
              </Text>
              <Text typography="titleMedium" color={theme.text.primary}>
                {(
                  Number(displayData?.TotalMatchVal) / 1000000000
                ).toLocaleString("vi-VN", {
                  minimumFractionDigits: 2,
                  maximumFractionDigits: 2,
                })}{" "}
                {t("detailHeader.billionVND")}
              </Text>
            </View>
          </View>
        ) : (
          <View>
            <View
              style={{
                flexDirection: "row",
                alignItems: "center",
                marginBottom: 8,
              }}
            >
              <View style={{ flex: 1 }}>
                <Text typography="bodyMedium" color={theme.text.primary}>
                  {t("detailHeader.floor")}
                </Text>
                <Text typography="titleMedium" color={theme.base.error}>
                  {displayData?.FloorPrice.toLocaleString("vi-VN", { minimumFractionDigits: 2, maximumFractionDigits: 2 })}
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
                  {t("detailHeader.reference")}
                </Text>
                <Text typography="titleMedium" color={theme.base.warning}>
                  {displayData?.RefPrice.toLocaleString("vi-VN", { minimumFractionDigits: 2, maximumFractionDigits: 2 })}
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
                  {t("detailHeader.ceiling")}
                </Text>
                <Text typography="titleMedium" color={theme.base.success}>
                  {displayData?.CeilingPrice.toLocaleString("vi-VN", { minimumFractionDigits: 2, maximumFractionDigits: 2 })}
                </Text>
              </View>
            </View>

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
                  {t("detailHeader.tradingVolume")}
                </Text>
                <Text typography="titleMedium" color={theme.text.primary}>
                  {displayData?.TotalMatchVol.toLocaleString("vi-VN", { minimumFractionDigits: 0, maximumFractionDigits: 0 })}{" "}
                  {t("detailHeader.shares")}
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
                style={{
                  flexDirection: "row",
                  justifyContent: "space-between",
                }}
              >
                <Text typography="bodyMedium" color={theme.text.primary}>
                  {t("detailHeader.tradingValue")}
                </Text>
                <Text typography="titleMedium" color={theme.text.primary}>
                  {(
                    Number(displayData?.TotalMatchVal) / 1000000000
                  ).toLocaleString("vi-VN", {
                    minimumFractionDigits: 2,
                    maximumFractionDigits: 2,
                  })}{" "}
                  {t("detailHeader.billionVND")}
                </Text>
              </View>
            </View>
          </View>
        )}
      </View>
    </View>
  );
};

export default DetailHeader;
