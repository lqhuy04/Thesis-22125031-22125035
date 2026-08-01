import React, {
  useState,
  useEffect,
  useMemo,
  useRef,
  useCallback,
} from "react";
import {
  fetchStockDataByTimeFrame,
  parseDateTime,
  StockPriceData,
  TechnicalIndicatorData,
  getTechnicalIndicators,
  fetchCurrentPriceData,
} from "@/helpers/DetailHelpers";
import { TouchableOpacity, View, StyleSheet } from "react-native";
import Animated, {
  useSharedValue,
  useAnimatedStyle,
  withRepeat,
  withTiming,
  interpolate,
} from "react-native-reanimated";
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
  VolumeMAData,
} from "../tradingView/utils";
import { MaterialCommunityIcons, MaterialIcons } from "@expo/vector-icons";
import { router } from "expo-router";
import TimeframeBottomSheet, {
  TIMEFRAME,
  TIMEFRAME_OPTIONS,
} from "./TimeframeBottomsheet";
import IndicatorBottomSheet, { IndicatorState } from "./IndicatorBottomsheet";
import ChartGuideBottomSheet from "./ChartGuideBottomsheet";
import { Text } from "../ui/Text";
import Entypo from "@expo/vector-icons/Entypo";
import { useLocalization } from "@/hooks/LocalizationContext";

// ─────────────────────────────────────────────
// SkeletonBox — pulsing placeholder block
// ─────────────────────────────────────────────
interface SkeletonBoxProps {
  width?: number | `${number}%`;
  height?: number;
  borderRadius?: number;
  style?: object;
}

const SkeletonBox = ({
  width = "100%",
  height = 14,
  borderRadius = 6,
  style,
}: SkeletonBoxProps) => {
  const { theme } = useTheme();
  const opacity = useSharedValue(0);

  useEffect(() => {
    opacity.value = withRepeat(withTiming(1, { duration: 700 }), -1, true);
  }, [opacity]);

  const animatedStyle = useAnimatedStyle(() => ({
    opacity: interpolate(opacity.value, [0, 1], [0.3, 0.7]),
  }));

  return (
    <Animated.View
      style={[
        {
          width,
          height,
          borderRadius,
          backgroundColor: theme.background.surface,
        },
        animatedStyle,
        style,
      ]}
    />
  );
};

// ─────────────────────────────────────────────
// PriceChartSkeleton — mirrors the real layout
// ─────────────────────────────────────────────
const PriceChartSkeleton = () => {
  const { theme } = useTheme();
  const bg = theme.background.bg;

  return (
    <View style={{ marginTop: 12 }}>
      {/* Stock header */}
      <View style={[skStyles.card, { backgroundColor: bg }]}>
        <View style={skStyles.row}>
          <SkeletonBox width={40} height={40} borderRadius={8} />
          <View style={{ flex: 1, gap: 6 }}>
            <SkeletonBox width={80} height={14} />
            <SkeletonBox width={140} height={11} />
          </View>
          <SkeletonBox width={28} height={28} borderRadius={14} />
        </View>
        <SkeletonBox width={90} height={24} style={{ marginBottom: 6 }} />
        <SkeletonBox width={70} height={12} />
      </View>

      {/* Chart card */}
      <View style={[skStyles.card, { backgroundColor: bg, marginTop: 8 }]}>
        {/* Chart type toggle row */}
        <View style={[skStyles.row, { marginBottom: 12 }]}>
          <SkeletonBox width={38} height={14} />
          <SkeletonBox width={110} height={30} borderRadius={10} />
          <View style={{ flex: 1 }} />
          <SkeletonBox width={20} height={20} borderRadius={10} />
        </View>

        {/* Chart area */}
        <SkeletonBox
          height={220}
          borderRadius={8}
          style={{ marginBottom: 12 }}
        />

        {/* Toolbar */}
        <View style={skStyles.row}>
          <SkeletonBox width={52} height={13} />
          <SkeletonBox width={88} height={28} borderRadius={8} />
          <View style={{ flex: 1 }} />
          <SkeletonBox width={80} height={13} />
          <SkeletonBox width={36} height={28} borderRadius={8} />
        </View>
      </View>

      {/* Intraday Change card */}
      <View style={[skStyles.card, { backgroundColor: bg, marginTop: 8 }]}>
        <SkeletonBox width={110} height={14} style={{ marginBottom: 14 }} />

        {/* Floor / Reference / Ceiling */}
        <View
          style={[
            skStyles.row,
            { justifyContent: "space-between", marginBottom: 0 },
          ]}
        >
          {[36, 44, 36].map((w, i) => (
            <View key={i} style={{ alignItems: "center", gap: 6 }}>
              <SkeletonBox width={w + 8} height={11} />
              <SkeletonBox width={w} height={16} />
            </View>
          ))}
        </View>

        <View style={skStyles.divider} />

        {[130, 150].map((w, i) => (
          <View
            key={i}
            style={[
              skStyles.row,
              {
                justifyContent: "space-between",
                marginBottom: 0,
                marginTop: 12,
              },
            ]}
          >
            <SkeletonBox width={90} height={12} />
            <SkeletonBox width={w} height={12} />
          </View>
        ))}
      </View>
    </View>
  );
};

const skStyles = StyleSheet.create({
  card: {
    borderRadius: 12,
    margin: 12,
    padding: 12,
  },
  row: {
    flexDirection: "row",
    alignItems: "center",
    gap: 8,
    marginBottom: 8,
  },
  divider: {
    height: StyleSheet.hairlineWidth,
    backgroundColor: "rgba(128,128,128,0.25)",
    marginTop: 14,
  },
});

// ─────────────────────────────────────────────
// Main component
// ─────────────────────────────────────────────
interface Props {
  symbol: string;
  registerRefresh?: (fn: () => Promise<void>) => () => void;
}

const PriceChartComponent = ({
  symbol,
  registerRefresh,
}: Props) => {
  const { theme } = useTheme();
  const { t } = useLocalization();

  // true on first load until we have price data for the first time
  const isFirstLoad = useRef(true);
  const [initialLoading, setInitialLoading] = useState(true);
  const [refreshLoading, setRefreshLoading] = useState(false);
  const [loading, setLoading] = useState(false);

  const [chartType, setChartType] = useState<"candle" | "area">("candle");
  const [timeFrame, setTimeFrame] = useState<TIMEFRAME>(
    TIMEFRAME.FIFTEEN_MINUTES,
  );
  const [showTimeframeSheet, setShowTimeframeSheet] = useState(false);
  const [showIndicatorSheet, setShowIndicatorSheet] = useState(false);
  const [showGuideSheet, setShowGuideSheet] = useState(false);
  const [indicatorState, setIndicatorState] = useState<IndicatorState>({
    mode1: null,
    mode2: null,
    volume: false,
  });

  // ── Current stock-price header data ──────────────────────────────────
  const [data, setData] = useState<any>(null);

  const fetchHeaderData = useCallback(async () => {
    const res = await fetchCurrentPriceData(symbol);
    if (res?.status) setData(res?.data);
  }, [symbol]);

  useEffect(() => {
    fetchHeaderData();
  }, [fetchHeaderData]);

  // ── OHLCV + technical indicator data ─────────────────────────────────
  const [priceData, setPriceData] = useState<StockPriceData[]>([]);
  const [technicalIndicatorsData, setTechnicalIndicatorsData] = useState<
    TechnicalIndicatorData[]
  >([]);

  const fetchChartData = useCallback(async () => {
    // Show full skeleton only on the very first fetch; subsequent
    // timeframe changes / refreshes show a lighter loading indicator.
    if (isFirstLoad.current) {
      setInitialLoading(true);
    } else {
      setLoading(true);
    }

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
      if (isFirstLoad.current) {
        setInitialLoading(false);
        isFirstLoad.current = false;
      }
    }
  }, [symbol, timeFrame]);

  useEffect(() => {
    fetchChartData();
  }, [fetchChartData]);

  // Pull-to-refresh — fetch lại header + dữ liệu chart theo timeframe hiện tại
  useEffect(() => {
    const refreshFn = async () => {
      setRefreshLoading(true);
      try {
        await Promise.all([fetchHeaderData(), fetchChartData()]);
      } finally {
        setRefreshLoading(false);
      }
    };
    const unregister = registerRefresh?.(refreshFn);
    return () => unregister?.();
  }, [registerRefresh, fetchHeaderData, fetchChartData]);

  // ── Derived chart data (memoised) ─────────────────────────────────────
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

  const chartVolumeMAData: VolumeMAData[] = useMemo(() => {
    if (
      !Array.isArray(technicalIndicatorsData) ||
      technicalIndicatorsData.length === 0
    )
      return [];
    return technicalIndicatorsData.map((item) => ({
      time: parseDateTime(item.TradingDate, item.Time) / 1000,
      vma20: item.volume_ma_20 ?? null,
      vma50: item.volume_ma_50 ?? null,
    }));
  }, [technicalIndicatorsData]);

  const selectedLabelKey =
    TIMEFRAME_OPTIONS.find((o) => o.value === timeFrame)?.labelKey ?? "";
  const selectedLabel = selectedLabelKey ? t(selectedLabelKey) : "";

  const activeIndicatorCount =
    (indicatorState.mode1 ? 1 : 0) +
    (indicatorState.mode2 ? 1 : 0) +
    (indicatorState.volume ? 1 : 0);

  // ── Skeleton guard — first load and pull-to-refresh ──────────────────
  if (initialLoading || refreshLoading) return <PriceChartSkeleton />;

  // ── Normal render ─────────────────────────────────────────────────────
  return (
    <View style={{ marginTop: 12 }}>
      <DetailHeader
        data={data}
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
                {t("priceChart.chart")}
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
                    {t("priceChart.line")}
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
                    {t("priceChart.candle")}
                  </Text>
                </TouchableOpacity>
              </View>

              <View style={{ flex: 1 }} />
              <TouchableOpacity
                onPress={() => setShowGuideSheet(true)}
                hitSlop={8}
              >
                <MaterialCommunityIcons
                  name="information-slab-circle-outline"
                  size={20}
                  color={theme.text.primary}
                />
              </TouchableOpacity>
            </View>

            {/* Chart — shows skeleton while reloading on timeframe change */}
            {loading ? (
              <SkeletonBox height={300} borderRadius={8} />
            ) : (
              <View>
                <TradingViewChart
                  prices={chartPriceData}
                  volumes={chartVolumeData}
                  volumeMAData={chartVolumeMAData}
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
                      params: {
                        data: JSON.stringify({
                          symbol: symbol,
                          exchange: data?.exchange,
                        }),
                      },
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
              <Text typography="bodyMedium" color={theme.text.primary}>
                {t("priceChart.candlePeriod")}
              </Text>

              <TouchableOpacity
                onPress={() => setShowTimeframeSheet(true)}
                disabled={loading}
                style={{
                  backgroundColor: theme.background.bg,
                  borderWidth: 1,
                  borderColor: theme.border.default,
                  paddingVertical: 4,
                  paddingHorizontal: 8,
                  borderRadius: 8,
                  flexDirection: "row",
                  alignItems: "center",
                  opacity: loading ? 0.5 : 1,
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

              <Text typography="bodyMedium" color={theme.text.primary}>
                {t("priceChart.technicalIndicator")}
              </Text>

              <TouchableOpacity
                onPress={() => setShowIndicatorSheet(true)}
                disabled={loading}
                style={{
                  backgroundColor: theme.background.bg,
                  borderWidth: 1,
                  borderColor: theme.border.default,
                  paddingVertical: 4.5,
                  paddingHorizontal: 8,
                  borderRadius: 8,
                  flexDirection: "row",
                  alignItems: "center",
                  opacity: loading ? 0.5 : 1,
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
                    <Text
                      typography="bodySmall"
                      color={theme.text.onPrimary}
                    >
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
        onLearnMore={() => {
          setShowGuideSheet(true);
        }}
      />

      <IndicatorBottomSheet
        visible={showIndicatorSheet}
        indicatorState={indicatorState}
        onChangeIndicator={setIndicatorState}
        onClose={() => setShowIndicatorSheet(false)}
      />

      <ChartGuideBottomSheet
        visible={showGuideSheet}
        onClose={() => setShowGuideSheet(false)}
      />
    </View>
  );
};

const styles = StyleSheet.create({
  toolbar: {
    flexDirection: "row",
    alignItems: "center",
    gap: 8,
    marginTop: 12,
  },
});

export default PriceChartComponent;
