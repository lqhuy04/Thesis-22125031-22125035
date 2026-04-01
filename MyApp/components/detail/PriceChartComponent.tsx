import React, { useState, useEffect, useMemo } from "react";
import {
  fetchPriceData,
  fetchStockData,
  getTechnicalIndicators,
  PriceData,
  StockData,
  TechnicalIndicatorData,
} from "@/helpers/DetailHelpers";
import { ActivityIndicator, TouchableOpacity, View } from "react-native";
import { Text } from "../ui/Text";
import { useTheme } from "@/hooks/ThemeContext";
import PriceLineGraph from "../ui/PriceLineChart";
import PriceCandleChart from "../ui/PriceCandleChart";
import DetailHeader from "../ui/DetailHeader";
import { SearchStockItem } from "@/helpers/SearchHelper";
import VolumeBarChart from "../ui/VolumeChart";
import RSIChart from "../ui/RSIChart";
import KDJChart from "../ui/KDJChart";
import MACDChart from "../ui/MACDChart";
import MaterialIcons from "@expo/vector-icons/MaterialIcons";
import Entypo from "@expo/vector-icons/Entypo";

interface Props {
  stockItem: SearchStockItem;
}

const PriceChartComponent = ({ stockItem }: Props) => {
  const { theme } = useTheme();
  const [chartType, setChartType] = useState<"Line" | "Candlestick">("Line");
  const [loading, setLoading] = useState<boolean>(false);
  const [option, setOption] = useState<"1D" | "1W" | "1M" | "1Y" | "5Y">("1D");
  const [technicalIndicatorMode1, setTechnicalIndicatorMode1] = useState<
    "MA" | "BOLL" | null
  >(null);
  const [technicalIndicatorMode2, setTechnicalIndicatorMode2] =
    useState<boolean>(false);
  const [technicalIndicatorMode3, setTechnicalIndicatorMode3] = useState<
    "MACD" | "RSI" | "KDJ" | null
  >(null);

  const [data, setData] = useState<StockData[]>([]);
  const [priceData, setPriceData] = useState<PriceData | null>(null);
  const [technicalIndicatorData, setTechnicalIndicatorData] = useState<
    TechnicalIndicatorData[]
  >([]);

  const candlestick_line_ratio = useMemo(() => {
    const maxHighValue = Math.max(...data.map((d) => Number(d?.High)));
    const minLowValue = Math.min(...data.map((d) => Number(d?.Low)));
    const minMA20Value = Math.min(
      ...technicalIndicatorData.map((d) => Number(d?.indicators?.sma_20)),
    );
    const minMA50Value = Math.min(
      ...technicalIndicatorData.map((d) => Number(d?.indicators?.sma_50)),
    );

    const candleStickRange = maxHighValue - minLowValue;

    if (technicalIndicatorMode1 === "BOLL") {
      const maxBBUpperValue = Math.max(
        ...technicalIndicatorData.map((d) => Number(d?.indicators?.bb_upper)),
      );
      const minBBLowerValue = Math.min(
        ...technicalIndicatorData.map((d) => Number(d?.indicators?.bb_lower)),
      );

      const maxLineValue = Math.max(maxHighValue, maxBBUpperValue);
      const minLineValue = Math.min(minLowValue, minBBLowerValue);

      const lineRange = maxLineValue - minLineValue;

      return candleStickRange / lineRange;
    }

    const maxLineValue = maxHighValue;
    const minLineValue = Math.min(minLowValue, minMA20Value, minMA50Value);
    const lineRange = maxLineValue - minLineValue;

    return candleStickRange / lineRange;
  }, [data, technicalIndicatorData, technicalIndicatorMode1]);

  const volumeData = useMemo(() => {
    if (Array.isArray(data)) {
      return data.map((item) => ({
        date: item.TradingDate,
        time: item.Time,
        volume: Number(item.Volume),
        positive: Number(item.Close) >= Number(item.Open),
      }));
    }
    return [];
  }, [data]);

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

  useEffect(() => {
    getTechnicalIndicators(stockItem.symbol).then((res) => {
      if (res?.status) {
        setTechnicalIndicatorData(res.data);
      }
    });
  }, [stockItem.symbol]);

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

            <View style={{ marginBottom: -48 }}>
              <PriceLineGraph
                data={data}
                technicalIndicatorData={technicalIndicatorData}
                candleStickMode={chartType === "Candlestick"}
                technicalIndicatorMode1={technicalIndicatorMode1}
                height={
                  technicalIndicatorMode2 && technicalIndicatorMode3
                    ? 160
                    : technicalIndicatorMode2 || technicalIndicatorMode3
                      ? 200
                      : 300
                }
              />

              {chartType === "Candlestick" ? (
                <View style={{ position: "absolute", zIndex: 0 }}>
                  <PriceCandleChart
                    data={data}
                    height={
                      technicalIndicatorMode2 && technicalIndicatorMode3
                        ? (160 - 48) * candlestick_line_ratio
                        : technicalIndicatorMode2 || technicalIndicatorMode3
                          ? (200 - 48) * candlestick_line_ratio
                          : (300 - 48) * candlestick_line_ratio
                    }
                  />
                </View>
              ) : null}
            </View>

            {technicalIndicatorMode2 ? (
              <View
                style={{
                  height: 1,
                  width: "100%",
                  backgroundColor: theme.border.default,
                  marginVertical: 2,
                }}
              />
            ) : null}

            {technicalIndicatorMode2 ? (
              <View>
                <VolumeBarChart data={volumeData} />
              </View>
            ) : null}

            {technicalIndicatorMode3 != null ? (
              <View
                style={{
                  height: 1,
                  width: "100%",
                  backgroundColor: theme.border.default,
                  marginVertical: 2,
                }}
              />
            ) : null}

            {technicalIndicatorMode3 === "MACD" ? (
              <MACDChart data={technicalIndicatorData} />
            ) : null}
            {technicalIndicatorMode3 === "RSI" ? (
              <RSIChart technicalIndicatorData={technicalIndicatorData} />
            ) : null}
            {technicalIndicatorMode3 === "KDJ" ? (
              <KDJChart technicalIndicatorData={technicalIndicatorData} />
            ) : null}
          </View>
        )}
      </View>

      <View
        style={{
          flexDirection: "row",
          alignItems: "center",
          marginHorizontal: 12,
          marginVertical: 12,
        }}
      >
        <TouchableOpacity
          onPress={() => {
            if (chartType === "Line") {
              setChartType("Candlestick");
            } else {
              setChartType("Line");
            }
          }}
          style={{
            backgroundColor: theme.background.surface,
            borderRadius: 2,
            borderWidth: 1,
            borderColor: theme.border.default,
            alignItems: "center",
            padding: 4,
            marginRight: 8,
          }}
        >
          {chartType === "Line" ? (
            <Entypo name="line-graph" size={18} color="black" />
          ) : (
            <MaterialIcons name={"candlestick-chart"} size={18} color="black" />
          )}
        </TouchableOpacity>

        <View
          style={{
            height: 24,
            width: 1,
            backgroundColor: theme.text.primary,
            marginRight: 12,
          }}
        />

        <TouchableOpacity
          onPress={() => {
            if (technicalIndicatorMode1 === "MA") {
              setTechnicalIndicatorMode1(null);
            } else {
              setTechnicalIndicatorMode1("MA");
            }
          }}
          style={{
            height: 24,
            backgroundColor: theme.background.surface,
            borderRadius: 4,
            borderWidth: 1,
            borderColor: theme.border.default,
            alignItems: "center",
            padding: 2,
            marginRight: 8,
          }}
        >
          <Text typography="labelLarge">MA</Text>
        </TouchableOpacity>

        <TouchableOpacity
          onPress={() => {
            if (technicalIndicatorMode1 === "BOLL") {
              setTechnicalIndicatorMode1(null);
            } else {
              setTechnicalIndicatorMode1("BOLL");
            }
          }}
          style={{
            height: 24,
            backgroundColor: theme.background.surface,
            borderRadius: 4,
            borderWidth: 1,
            borderColor: theme.border.default,
            alignItems: "center",
            padding: 2,
            marginRight: 8,
          }}
        >
          <Text typography="labelLarge">BOLL</Text>
        </TouchableOpacity>

        <TouchableOpacity
          onPress={() => {
            setTechnicalIndicatorMode2((prev) => !prev);
          }}
          style={{
            height: 24,
            backgroundColor: theme.background.surface,
            borderRadius: 4,
            borderWidth: 1,
            borderColor: theme.border.default,
            alignItems: "center",
            padding: 2,
            marginRight: 8,
          }}
        >
          <Text typography="labelLarge">VOL</Text>
        </TouchableOpacity>

        <TouchableOpacity
          onPress={() => {
            if (technicalIndicatorMode3 !== "MACD") {
              setTechnicalIndicatorMode3("MACD");
            } else {
              setTechnicalIndicatorMode3(null);
            }
          }}
          style={{
            height: 24,
            backgroundColor: theme.background.surface,
            borderRadius: 4,
            borderWidth: 1,
            borderColor: theme.border.default,
            alignItems: "center",
            padding: 2,
            marginRight: 8,
          }}
        >
          <Text typography="labelLarge">MACD</Text>
        </TouchableOpacity>

        <TouchableOpacity
          onPress={() => {
            if (technicalIndicatorMode3 !== "RSI") {
              setTechnicalIndicatorMode3("RSI");
            } else {
              setTechnicalIndicatorMode3(null);
            }
          }}
          style={{
            height: 24,
            backgroundColor: theme.background.surface,
            borderRadius: 4,
            borderWidth: 1,
            borderColor: theme.border.default,
            alignItems: "center",
            padding: 2,
            marginRight: 8,
          }}
        >
          <Text typography="labelLarge">RSI</Text>
        </TouchableOpacity>

        <TouchableOpacity
          onPress={() => {
            if (technicalIndicatorMode3 !== "KDJ") {
              setTechnicalIndicatorMode3("KDJ");
            } else {
              setTechnicalIndicatorMode3(null);
            }
          }}
          style={{
            height: 24,
            backgroundColor: theme.background.surface,
            borderRadius: 4,
            borderWidth: 1,
            borderColor: theme.border.default,
            alignItems: "center",
            padding: 2,
            marginRight: 8,
          }}
        >
          <Text typography="labelLarge">KDJ</Text>
        </TouchableOpacity>
      </View>

      {/* <View
        style={{
          flexDirection: "row",
          alignItems: "center",
          justifyContent: "space-between",
          marginHorizontal: 8,
          marginBottom: 12,
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
      </View> */}
    </View>
  );
};

export default PriceChartComponent;
