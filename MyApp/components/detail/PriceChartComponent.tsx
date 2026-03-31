import React, { useState, useEffect } from "react";
import {
  fetchPriceData,
  fetchStockData,
  PriceData,
  StockData,
} from "@/helpers/DetailHelpers";
import { ActivityIndicator, TouchableOpacity, View, Image } from "react-native";
import { Text } from "../ui/Text";
import { useTheme } from "@/hooks/ThemeContext";
import PriceLineGraph from "../ui/PriceLineChart";
import PriceCandleChart from "../ui/PriceCandleChart";
import { Images } from "@/constants/Images";
import DetailHeader from "../ui/DetailHeader";
import { SearchStockItem } from "@/helpers/SearchHelper";

interface Props {
  stockItem: SearchStockItem;
}

const PriceChartComponent = ({ stockItem }: Props) => {
  const { theme } = useTheme();
  const [chartType, setChartType] = useState<"Line" | "Candlestick">("Line");
  const [loading, setLoading] = useState<boolean>(false);
  const [option, setOption] = useState<"1D" | "1W" | "1M" | "1Y" | "5Y">("1D");
  const [data, setData] = useState<StockData[]>([]);

  const [priceData, setPriceData] = useState<PriceData | null>(null);

  useEffect(() => {
    fetchPriceData(stockItem.symbol).then((res) => {
      if (res?.status) {
        setPriceData(res?.data);
      }
    });
  }, [stockItem.symbol]);

  useEffect(() => {
    setLoading(true);
    fetchStockData(stockItem.symbol, option).then((stockRes) => {
      setLoading(false);
      if (stockRes?.status) {
        setData(stockRes.data);
      }
    });
  }, [stockItem.symbol, option]);

  return (
    <View style={{ marginTop: 12 }}>
      <View>
        {loading ? (
          <View
            style={{
              height: 300,
              justifyContent: "center",
              alignItems: "center",
            }}
          >
            <ActivityIndicator size="large" color={theme.base.primary} />
          </View>
        ) : (
          <View>
            <DetailHeader item={stockItem} priceData={priceData} />

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
                  {priceData?.floor_price}
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

            {chartType === "Line" ? (
              <PriceLineGraph
                data={data}
                option={option}
                referencePrice={priceData?.reference_price ?? 0}
              />
            ) : (
              <PriceCandleChart data={data} />
            )}

            <TouchableOpacity
              onPress={() => {
                if (chartType === "Line") {
                  setChartType("Candlestick");
                } else {
                  setChartType("Line");
                }
              }}
              style={{
                height: 24,
                width: 24,
                backgroundColor: theme.background.surface,
                position: "absolute",
                bottom: 270,
                right: 12,
                borderRadius: 4,
                borderWidth: 1,
                borderColor: theme.border.default,
                alignItems: "center",
                padding: 2,
              }}
            >
              <Image
                source={
                  chartType === "Line"
                    ? Images.ic_candlesticks_chart
                    : Images.ic_line_graph
                }
                style={{ width: 18, height: 18 }}
              />
            </TouchableOpacity>
          </View>
        )}
      </View>

      <View
        style={{
          flexDirection: "row",
          alignItems: "center",
          justifyContent: "space-between",
          marginHorizontal: 8,
        }}
      >
        <View
          style={{
            backgroundColor:
              option === "1D" ? theme.base.primary : theme.background.surface,
            padding: 2,
            borderRadius: 4,
            borderWidth: 1,
            borderColor:
              option === "1D" ? theme.base.primary : theme.border.default,
            marginHorizontal: 4,
            flex: 1,
            alignItems: "center",
          }}
        >
          <Text
            typography="titleSmall"
            color={option === "1D" ? theme.text.onPrimary : theme.text.primary}
            onPress={() => setOption("1D")}
          >
            1D
          </Text>
        </View>
        <View
          style={{
            backgroundColor:
              option === "1W" ? theme.base.primary : theme.background.surface,
            padding: 2,
            borderRadius: 4,
            borderWidth: 1,
            borderColor:
              option === "1W" ? theme.base.primary : theme.border.default,
            marginHorizontal: 4,
            flex: 1,
            alignItems: "center",
          }}
        >
          <Text
            typography="titleSmall"
            color={option === "1W" ? theme.text.onPrimary : theme.text.primary}
            onPress={() => setOption("1W")}
          >
            1W
          </Text>
        </View>
        <View
          style={{
            backgroundColor:
              option === "1M" ? theme.base.primary : theme.background.surface,
            padding: 2,
            borderRadius: 4,
            borderWidth: 1,
            borderColor:
              option === "1M" ? theme.base.primary : theme.border.default,
            marginHorizontal: 4,
            flex: 1,
            alignItems: "center",
          }}
        >
          <Text
            typography="titleSmall"
            color={option === "1M" ? theme.text.onPrimary : theme.text.primary}
            onPress={() => setOption("1M")}
          >
            1M
          </Text>
        </View>
        <View
          style={{
            backgroundColor:
              option === "1Y" ? theme.base.primary : theme.background.surface,
            padding: 2,
            borderRadius: 4,
            borderWidth: 1,
            borderColor:
              option === "1Y" ? theme.base.primary : theme.border.default,
            marginHorizontal: 4,
            flex: 1,
            alignItems: "center",
          }}
        >
          <Text
            typography="titleSmall"
            color={option === "1Y" ? theme.text.onPrimary : theme.text.primary}
            onPress={() => setOption("1Y")}
          >
            1Y
          </Text>
        </View>
        <View
          style={{
            backgroundColor:
              option === "5Y" ? theme.base.primary : theme.background.surface,
            padding: 2,
            borderRadius: 4,
            borderWidth: 1,
            borderColor:
              option === "5Y" ? theme.base.primary : theme.border.default,
            marginHorizontal: 4,
            flex: 1,
            alignItems: "center",
          }}
        >
          <Text
            typography="titleSmall"
            color={option === "5Y" ? theme.text.onPrimary : theme.text.primary}
            onPress={() => setOption("5Y")}
          >
            5Y
          </Text>
        </View>
      </View>
    </View>
  );
};

export default PriceChartComponent;
