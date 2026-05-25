import React, { useState, useEffect, useMemo } from "react";
import {
  fetchStockDataByTimeFrame,
  parseDateTime,
  StockPriceData,
  TechnicalIndicatorData,
  getTechnicalIndicators,
} from "@/helpers/DetailHelpers";
import {
  TouchableOpacity,
  View,
  StyleSheet,
  ActivityIndicator,
} from "react-native";
import { useTheme } from "@/hooks/ThemeContext";
import DetailHeader from "../ui/DetailHeader";
import TradingViewChart from "../tradingView/TradingViewChart";
import {
  BollData,
  KDJData,
  MACDData,
  MAData,
  PriceData,
  RSIData,
  VolumeData,
} from "../tradingView/utils";
import { MaterialCommunityIcons, MaterialIcons } from "@expo/vector-icons";
import { router } from "expo-router";
import TimeframeBottomSheet, {
  TIMEFRAME,
  TIMEFRAME_OPTIONS,
} from "./TimeframeBottomsheet";
import IndicatorBottomSheet, { IndicatorState } from "./IndicatorBottomsheet";
import { Text } from "../ui/Text";
import Entypo from "@expo/vector-icons/Entypo";

interface Props {
  symbol: string;
  isMarketIndex?: boolean;
}

const PriceChartComponent = ({ symbol, isMarketIndex = false }: Props) => {
  const { theme } = useTheme();
  const [loading, setLoading] = useState<boolean>(false);
  const [chartType, setChartType] = useState<"candle" | "area">("candle");
  const [timeFrame, setTimeFrame] = useState<TIMEFRAME>(
    TIMEFRAME.FIFTEEN_MINUTES,
  );
  const [showTimeframeSheet, setShowTimeframeSheet] = useState(false);
  const [showIndicatorSheet, setShowIndicatorSheet] = useState(false);
  const [indicatorState, setIndicatorState] = useState<IndicatorState>({
    mode1: null,
    mode2: null,
    volume: false,
  });

  //------------------------------------------------------------------------
  const [priceData, setPriceData] = useState<StockPriceData[]>([]);
  const [technicalIndicatorsData, setTechnicalIndicatorsData] = useState<
    TechnicalIndicatorData[]
  >([]);

  useEffect(() => {
    const fetchData = async () => {
      setLoading(true);
      try {
        const interval =
          timeFrame === TIMEFRAME.ONE_MINUTE
            ? "1m"
            : timeFrame === TIMEFRAME.FIVE_MINUTES
              ? "5m"
              : timeFrame === TIMEFRAME.FIFTEEN_MINUTES
                ? "15m"
                : timeFrame === TIMEFRAME.THIRTY_MINUTES
                  ? "30m"
                  : timeFrame === TIMEFRAME.ONE_HOUR
                    ? "1h"
                    : timeFrame === TIMEFRAME.ONE_DAY
                      ? "1d"
                      : timeFrame === TIMEFRAME.ONE_WEEK
                        ? "1w"
                        : timeFrame === TIMEFRAME.ONE_MONTH
                          ? "1M"
                          : "15m";

        const [indicatorRes, priceRes] = await Promise.all([
          getTechnicalIndicators(symbol, interval),
          fetchStockDataByTimeFrame(symbol, interval),
        ]);

        setTechnicalIndicatorsData(
          indicatorRes?.status ? (indicatorRes.data ?? []) : [],
        );
        setPriceData(priceRes?.status ? (priceRes.data ?? []) : []);
      } catch (error) {
        console.error("Fetch error:", error);
        setTechnicalIndicatorsData([]);
        setPriceData([]);
      } finally {
        setLoading(false);
      }
    };

    fetchData();
  }, [symbol, timeFrame]);

  const chartPriceData: PriceData[] = useMemo(() => {
    if (!Array.isArray(priceData) || priceData.length === 0) return [];
    return priceData.map((item) => ({
      time: parseDateTime(item.TradingDate, item.Time) / 1000,
      open: item.Open,
      high: item.High,
      low: item.Low,
      close: item.Close,
    }));
  }, [priceData]);

  const chartMAData: MAData[] = useMemo(() => {
    if (
      !Array.isArray(technicalIndicatorsData) ||
      technicalIndicatorsData.length === 0
    )
      return [];
    return technicalIndicatorsData.map((item) => ({
      time: parseDateTime(item.TradingDate, item.Time) / 1000,
      ma20: item.sma_20,
      ma50: item.sma_50,
    }));
  }, [technicalIndicatorsData]);

  const chartBOLLData: BollData[] = useMemo(() => {
    if (
      !Array.isArray(technicalIndicatorsData) ||
      technicalIndicatorsData.length === 0
    )
      return [];
    return technicalIndicatorsData.map((item) => ({
      time: parseDateTime(item.TradingDate, item.Time) / 1000,
      boll: item.bb_middle,
      ub: item.bb_upper,
      lb: item.bb_lower,
    }));
  }, [technicalIndicatorsData]);

  const chartMACDData: MACDData[] = useMemo(() => {
    if (
      !Array.isArray(technicalIndicatorsData) ||
      technicalIndicatorsData.length === 0
    )
      return [];
    return technicalIndicatorsData.map((item) => ({
      time: parseDateTime(item.TradingDate, item.Time) / 1000,
      macd: item.macd_histogram,
      dif: item.macd,
      dea: item.macd_signal,
    }));
  }, [technicalIndicatorsData]);

  const chartRSIData: RSIData[] = useMemo(() => {
    if (
      !Array.isArray(technicalIndicatorsData) ||
      technicalIndicatorsData.length === 0
    )
      return [];
    return technicalIndicatorsData.map((item) => ({
      time: parseDateTime(item.TradingDate, item.Time) / 1000,
      value: item.rsi_14,
    }));
  }, [technicalIndicatorsData]);

  const chartKDJData: KDJData[] = useMemo(() => {
    if (
      !Array.isArray(technicalIndicatorsData) ||
      technicalIndicatorsData.length === 0
    )
      return [];
    return technicalIndicatorsData.map((item) => ({
      time: parseDateTime(item.TradingDate, item.Time) / 1000,
      k: item.kdj_k,
      d: item.kdj_d,
      j: item.kdj_j,
    }));
  }, [technicalIndicatorsData]);

  const chartVolumeData: VolumeData[] = useMemo(() => {
    if (!Array.isArray(priceData) || priceData.length === 0) return [];
    return priceData.map((item) => ({
      time: parseDateTime(item.TradingDate, item.Time) / 1000,
      value: item.Volume,
      color: item.Close >= item.Open ? theme.base.success : theme.base.error,
    }));
  }, [priceData, theme.base.error, theme.base.success]);

  const selectedLabel =
    TIMEFRAME_OPTIONS.find((o) => o.value === timeFrame)?.label ?? "";

  const activeIndicatorCount =
    (indicatorState.mode1 ? 1 : 0) +
    (indicatorState.mode2 ? 1 : 0) +
    (indicatorState.volume ? 1 : 0);

  return (
    <View style={{ marginTop: 12 }}>
      <DetailHeader
        symbol={symbol}
        isMarketIndex={isMarketIndex}
        chart={
          <View
            style={{
              backgroundColor: theme.background.bg,
              borderRadius: 12,
              margin: 12,
              padding: 12,
            }}
          >
            <View
              style={{
                flexDirection: "row",
                alignItems: "center",
                marginBottom: 12,
              }}
            >
              <Text typography="titleMedium" color={theme.text.primary}>
                Biểu đồ:
              </Text>

              <View
                style={{
                  flexDirection: "row",
                  alignItems: "center",
                  marginLeft: 8,
                  padding: 4,
                  borderRadius: 10,
                  backgroundColor: theme.background.surface,
                }}
              >
                <TouchableOpacity
                  onPress={() => setChartType("area")}
                  style={{
                    flexDirection: "row",
                    alignItems: "center",
                    paddingVertical: 4,
                    paddingHorizontal: 12,
                    borderRadius: 6,
                    backgroundColor:
                      chartType === "area"
                        ? theme.background.bg
                        : "transparent",
                  }}
                >
                  <MaterialCommunityIcons
                    name="chart-timeline-variant"
                    size={18}
                    color={theme.text.primary}
                    style={{ marginRight: 8 }}
                  />
                  <Text typography="bodyMedium" color={theme.text.primary}>
                    Đường
                  </Text>
                </TouchableOpacity>
                <TouchableOpacity
                  onPress={() => setChartType("candle")}
                  style={{
                    flexDirection: "row",
                    alignItems: "center",
                    paddingVertical: 4,
                    paddingHorizontal: 12,
                    borderRadius: 6,
                    backgroundColor:
                      chartType === "candle"
                        ? theme.background.bg
                        : "transparent",
                  }}
                >
                  <MaterialIcons
                    name="candlestick-chart"
                    size={18}
                    color={theme.text.primary}
                    style={{ marginRight: 8 }}
                  />
                  <Text typography="bodyMedium" color={theme.text.primary}>
                    Nến
                  </Text>
                </TouchableOpacity>
              </View>

              <View style={{ flex: 1 }} />
              <MaterialCommunityIcons
                name="information-slab-circle-outline"
                size={20}
                color={theme.text.primary}
              />
            </View>

            {loading ? (
              <View style={styles.loadingContainer}>
                <ActivityIndicator size="small" color={theme.base.primary} />
              </View>
            ) : (
              <View>
                <TradingViewChart
                  prices={chartPriceData}
                  volumes={chartVolumeData}
                  maData={chartMAData}
                  bollData={chartBOLLData}
                  macdData={chartMACDData}
                  rsiData={chartRSIData}
                  kdjData={chartKDJData}
                  timeframe={timeFrame}
                  chartType={chartType}
                  showVolume={indicatorState.volume}
                  technicalIndicatorMode1={indicatorState.mode1}
                  technicalIndicatorMode2={indicatorState.mode2}
                />

                <TouchableOpacity
                  onPress={() =>
                    router.push({
                      pathname: "/TradingViewScreen",
                      params: { data: JSON.stringify({ symbol: symbol }) },
                    })
                  }
                  style={{
                    backgroundColor: theme.background.surface,
                    borderColor: theme.border.default,
                    position: "absolute",
                    bottom: 64,
                    left: 12,
                    width: 24,
                    height: 24,
                    borderRadius: 12,
                    alignItems: "center",
                    justifyContent: "center",
                  }}
                >
                  <MaterialCommunityIcons
                    name="arrow-expand"
                    size={12}
                    color={theme.text.primary}
                  />
                </TouchableOpacity>
              </View>
            )}

            <View style={styles.toolbar}>
              {/* Timeframe button */}
              <Text typography="bodyMedium" color={theme.text.primary}>
                Chu kỳ nến:
              </Text>

              <TouchableOpacity
                onPress={() => setShowTimeframeSheet(true)}
                style={{
                  backgroundColor: theme.background.bg,
                  borderWidth: 1,
                  borderColor: theme.border.default,
                  paddingVertical: 4,
                  paddingHorizontal: 8,
                  borderRadius: 8,
                  flexDirection: "row",
                  alignItems: "center",
                }}
              >
                <Text
                  typography="bodyMedium"
                  color={theme.text.primary}
                  style={{ marginRight: 4 }}
                >
                  {selectedLabel}
                </Text>
                <Entypo
                  name="chevron-small-down"
                  size={16}
                  color={theme.text.primary}
                />
              </TouchableOpacity>

              <View style={{ flex: 1 }} />

              {/* Indicator button */}
              <Text typography="bodyMedium" color={theme.text.primary}>
                Chỉ báo kỹ thuật:
              </Text>

              <TouchableOpacity
                onPress={() => setShowIndicatorSheet(true)}
                style={{
                  backgroundColor: theme.background.bg,
                  borderWidth: 1,
                  borderColor: theme.border.default,
                  paddingVertical: 4.5,
                  paddingHorizontal: 8,
                  borderRadius: 8,
                  flexDirection: "row",
                  alignItems: "center",
                }}
              >
                <MaterialCommunityIcons
                  name="finance"
                  size={18}
                  color={theme.text.primary}
                />
                {activeIndicatorCount > 0 && (
                  <View
                    style={{
                      width: 16,
                      height: 16,
                      borderRadius: 8,
                      alignItems: "center",
                      justifyContent: "center",
                      backgroundColor: theme.base.primary,
                      marginLeft: 4,
                    }}
                  >
                    <Text typography="bodySmall" color={theme.text.primary}>
                      {activeIndicatorCount}
                    </Text>
                  </View>
                )}
              </TouchableOpacity>
            </View>
          </View>
        }
      />

      <TimeframeBottomSheet
        visible={showTimeframeSheet}
        selectedTimeframe={timeFrame}
        onSelect={(value) => setTimeFrame(value)}
        onClose={() => setShowTimeframeSheet(false)}
      />

      <IndicatorBottomSheet
        visible={showIndicatorSheet}
        indicatorState={indicatorState}
        onChangeIndicator={setIndicatorState}
        onClose={() => setShowIndicatorSheet(false)}
      />
    </View>
  );
};

const styles = StyleSheet.create({
  loadingContainer: {
    height: 300,
    alignItems: "center",
    justifyContent: "center",
  },
  toolbar: {
    flexDirection: "row",
    alignItems: "center",
    gap: 8,
    marginTop: 12,
  },
  iconBtn: {
    borderRadius: 2,
    borderWidth: 1,
    padding: 4,
  },
  rowBtn: {
    flexDirection: "row",
    alignItems: "center",
    gap: 4,
    paddingHorizontal: 8,
  },
  btnLabel: {
    fontSize: 12,
    color: "black",
    fontWeight: "500",
  },
  badge: {
    width: 16,
    height: 16,
    borderRadius: 8,
    alignItems: "center",
    justifyContent: "center",
  },
});

export default PriceChartComponent;
