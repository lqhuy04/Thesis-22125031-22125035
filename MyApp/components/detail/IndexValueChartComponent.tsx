import React, {
  useCallback,
  useEffect,
  useMemo,
  useRef,
  useState,
} from "react";
import {
  StyleSheet,
  TouchableOpacity,
  View,
} from "react-native";
import Animated, {
  interpolate,
  useAnimatedStyle,
  useSharedValue,
  withRepeat,
  withTiming,
} from "react-native-reanimated";
import { MaterialCommunityIcons } from "@expo/vector-icons";
import Entypo from "@expo/vector-icons/Entypo";
import { router } from "expo-router";

import {
  fetchCurrentIndexData,
  fetchIndexValueDataByTimeFrame,
  MarketIndexValueData,
} from "@/helpers/DetailHelpers";
import { MarketIndex } from "@/helpers/MarketHelpers";
import { useLocalization } from "@/hooks/LocalizationContext";
import { useTheme } from "@/hooks/ThemeContext";
import TradingViewChart from "../tradingView/TradingViewChart";
import { PriceData } from "../tradingView/utils";
import DetailHeader from "../ui/DetailHeader";
import { Text } from "../ui/Text";
import TimeframeBottomSheet, {
  TIMEFRAME,
  TIMEFRAME_OPTIONS,
} from "./TimeframeBottomsheet";

interface Props {
  symbol: string;
  registerRefresh?: (fn: () => Promise<void>) => () => void;
}

type IndexInterval =
  | "1m"
  | "5m"
  | "15m"
  | "30m"
  | "1h"
  | "1d"
  | "1w"
  | "1M";

const TIMEFRAME_TO_INTERVAL: Record<TIMEFRAME, IndexInterval> = {
  [TIMEFRAME.ONE_MINUTE]: "1m",
  [TIMEFRAME.FIVE_MINUTES]: "5m",
  [TIMEFRAME.FIFTEEN_MINUTES]: "15m",
  [TIMEFRAME.THIRTY_MINUTES]: "30m",
  [TIMEFRAME.ONE_HOUR]: "1h",
  [TIMEFRAME.ONE_DAY]: "1d",
  [TIMEFRAME.ONE_WEEK]: "1w",
  [TIMEFRAME.ONE_MONTH]: "1M",
};

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

const IndexValueChartSkeleton = () => {
  const { theme } = useTheme();

  return (
    <View style={styles.skeletonContainer}>
      <View
        style={[
          styles.skeletonCard,
          { backgroundColor: theme.background.bg },
        ]}
      >
        <View style={styles.skeletonHeaderRow}>
          <SkeletonBox width={72} height={24} />
          <View style={styles.skeletonSpacer} />
          <SkeletonBox width={110} height={26} borderRadius={8} />
        </View>
        <View style={styles.skeletonPriceRow}>
          <SkeletonBox width={96} height={28} />
          <SkeletonBox width={52} height={22} borderRadius={4} />
          <SkeletonBox width={46} height={14} />
        </View>
        <SkeletonBox width={230} height={13} style={styles.skeletonCloseTime} />
      </View>

      <View
        style={[
          styles.skeletonCard,
          { backgroundColor: theme.background.bg },
        ]}
      >
        <SkeletonBox width={70} height={18} />
        <SkeletonBox
          height={300}
          borderRadius={8}
          style={styles.skeletonChart}
        />
        <View style={styles.skeletonToolbar}>
          <SkeletonBox width={48} height={14} />
          <SkeletonBox width={88} height={30} borderRadius={8} />
        </View>
      </View>

      <SkeletonBox
        width={180}
        height={22}
        style={styles.skeletonSectionTitle}
      />
      <View
        style={[
          styles.skeletonCard,
          styles.skeletonMovementCard,
          { backgroundColor: theme.background.bg },
        ]}
      >
        <View style={styles.skeletonMetric}>
          <SkeletonBox width={116} height={13} />
          <SkeletonBox width={104} height={18} />
        </View>
        <View
          style={[
            styles.skeletonDivider,
            { backgroundColor: theme.border.default },
          ]}
        />
        <View style={styles.skeletonMetric}>
          <SkeletonBox width={104} height={13} />
          <SkeletonBox width={118} height={18} />
        </View>
      </View>
    </View>
  );
};

const IndexValueChartComponent = ({
  symbol,
  registerRefresh,
}: Props) => {
  const { theme } = useTheme();
  const { t } = useLocalization();
  const isFirstLoad = useRef(true);

  const [initialLoading, setInitialLoading] = useState(true);
  const [refreshLoading, setRefreshLoading] = useState(false);
  const [chartLoading, setChartLoading] = useState(false);
  const [showTimeframeSheet, setShowTimeframeSheet] = useState(false);
  const [timeFrame, setTimeFrame] = useState<TIMEFRAME>(
    TIMEFRAME.FIFTEEN_MINUTES,
  );
  const [data, setData] = useState<MarketIndex | null>(null);
  const [historicalValues, setHistoricalValues] = useState<
    MarketIndexValueData[]
  >([]);

  const fetchHeaderData = useCallback(async () => {
    const response = await fetchCurrentIndexData(symbol);
    setData(response.status ? response.data : null);
  }, [symbol]);

  const fetchHistoricalData = useCallback(async () => {
    if (isFirstLoad.current) {
      setInitialLoading(true);
    } else {
      setChartLoading(true);
    }

    try {
      const response = await fetchIndexValueDataByTimeFrame(
        symbol,
        TIMEFRAME_TO_INTERVAL[timeFrame],
      );
      setHistoricalValues(response.status ? response.data : []);
    } catch (error) {
      console.error(`Error fetching historical values for ${symbol}:`, error);
      setHistoricalValues([]);
    } finally {
      setChartLoading(false);
      if (isFirstLoad.current) {
        setInitialLoading(false);
        isFirstLoad.current = false;
      }
    }
  }, [symbol, timeFrame]);

  useEffect(() => {
    fetchHeaderData();
  }, [fetchHeaderData]);

  useEffect(() => {
    fetchHistoricalData();
  }, [fetchHistoricalData]);

  useEffect(() => {
    const refreshFn = async () => {
      setRefreshLoading(true);
      try {
        await Promise.all([fetchHeaderData(), fetchHistoricalData()]);
      } finally {
        setRefreshLoading(false);
      }
    };

    const unregister = registerRefresh?.(refreshFn);
    return () => unregister?.();
  }, [fetchHeaderData, fetchHistoricalData, registerRefresh]);

  const chartPriceData: PriceData[] = useMemo(() => {
    const valuesByTimestamp = new Map<number, PriceData>();

    for (const item of historicalValues) {
      const timestamp = Math.floor(new Date(item.trading_time).getTime() / 1000);
      const value = Number(item.value);

      if (!Number.isFinite(timestamp) || !Number.isFinite(value)) {
        continue;
      }

      valuesByTimestamp.set(timestamp, {
        time: timestamp,
        open: value,
        high: value,
        low: value,
        close: value,
      });
    }

    return Array.from(valuesByTimestamp.values()).sort(
      (first, second) => first.time - second.time,
    );
  }, [historicalValues]);

  const selectedLabelKey =
    TIMEFRAME_OPTIONS.find((option) => option.value === timeFrame)?.labelKey ??
    "";
  const selectedLabel = selectedLabelKey ? t(selectedLabelKey) : "";

  if (initialLoading || refreshLoading) {
    return <IndexValueChartSkeleton />;
  }

  return (
    <View style={styles.container}>
      <DetailHeader
        data={data}
        isMarketIndex
        chart={
          <View
            style={[
              styles.chartCard,
              { backgroundColor: theme.background.bg },
            ]}
          >
            <Text typography="titleMedium" color={theme.text.primary}>
              {t("priceChart.chart")}
            </Text>

            <Animated.View
              style={[
                styles.chartContainer,
                { opacity: chartLoading ? 0.4 : 1 },
              ]}
            >
              {chartPriceData.length > 0 ? (
                <TradingViewChart
                  prices={chartPriceData}
                  volumes={[]}
                  volumeMAData={[]}
                  maData={[]}
                  bollData={[]}
                  macdData={[]}
                  rsiData={[]}
                  kdjData={[]}
                  timeframe={timeFrame}
                  chartType="area"
                  showVolume={false}
                  technicalIndicatorMode1={null}
                  technicalIndicatorMode2={null}
                  hideTooltip
                />
              ) : (
                <View style={styles.emptyChart}>
                  <Text typography="bodyMedium" color={theme.text.primary}>
                    {t("priceChart.noData")}
                  </Text>
                </View>
              )}

              <TouchableOpacity
                onPress={() =>
                  router.push({
                    pathname: "/TradingViewScreen",
                    params: {
                      data: JSON.stringify({
                        symbol,
                        exchange: "HOSE",
                      }),
                    },
                  })
                }
                style={[
                  styles.expandButton,
                  {
                    backgroundColor: theme.background.surface,
                    borderColor: theme.border.default,
                  },
                ]}
              >
                <MaterialCommunityIcons
                  name="arrow-expand"
                  size={12}
                  color={theme.text.primary}
                />
              </TouchableOpacity>
            </Animated.View>

            <View style={styles.toolbar}>
              <Text typography="bodyMedium" color={theme.text.primary}>
                {t("priceChart.candlePeriod")}
              </Text>

              <TouchableOpacity
                onPress={() => setShowTimeframeSheet(true)}
                style={[
                  styles.timeframeButton,
                  {
                    backgroundColor: theme.background.bg,
                    borderColor: theme.border.default,
                  },
                ]}
              >
                <Text
                  typography="bodyMedium"
                  color={theme.text.primary}
                  style={styles.timeframeLabel}
                >
                  {selectedLabel}
                </Text>
                <Entypo
                  name="chevron-small-down"
                  size={16}
                  color={theme.text.primary}
                />
              </TouchableOpacity>
            </View>
          </View>
        }
      />

      <TimeframeBottomSheet
        visible={showTimeframeSheet}
        selectedTimeframe={timeFrame}
        onSelect={setTimeFrame}
        onClose={() => setShowTimeframeSheet(false)}
        showLearnMore={false}
      />
    </View>
  );
};

const styles = StyleSheet.create({
  container: {
    marginTop: 12,
  },
  chartCard: {
    borderRadius: 12,
    margin: 12,
    padding: 12,
  },
  chartContainer: {
    marginTop: 12,
    position: "relative",
  },
  emptyChart: {
    height: 300,
    alignItems: "center",
    justifyContent: "center",
  },
  expandButton: {
    borderWidth: StyleSheet.hairlineWidth,
    position: "absolute",
    bottom: 12,
    left: 12,
    width: 24,
    height: 24,
    borderRadius: 12,
    alignItems: "center",
    justifyContent: "center",
  },
  toolbar: {
    flexDirection: "row",
    alignItems: "center",
    gap: 8,
    marginTop: 12,
  },
  timeframeButton: {
    borderWidth: 1,
    paddingVertical: 4,
    paddingHorizontal: 8,
    borderRadius: 8,
    flexDirection: "row",
    alignItems: "center",
  },
  timeframeLabel: {
    marginRight: 4,
  },
  skeletonContainer: {
    marginTop: 12,
  },
  skeletonCard: {
    borderRadius: 12,
    marginHorizontal: 12,
    marginBottom: 12,
    padding: 12,
  },
  skeletonHeaderRow: {
    flexDirection: "row",
    alignItems: "center",
  },
  skeletonSpacer: {
    flex: 1,
  },
  skeletonPriceRow: {
    flexDirection: "row",
    alignItems: "center",
    gap: 8,
    marginTop: 12,
  },
  skeletonCloseTime: {
    marginTop: 8,
  },
  skeletonChart: {
    marginTop: 12,
  },
  skeletonToolbar: {
    flexDirection: "row",
    alignItems: "center",
    gap: 8,
    marginTop: 12,
  },
  skeletonSectionTitle: {
    marginHorizontal: 12,
    marginBottom: 12,
  },
  skeletonMovementCard: {
    flexDirection: "row",
    alignItems: "center",
    paddingVertical: 18,
  },
  skeletonMetric: {
    flex: 1,
    alignItems: "center",
    gap: 10,
  },
  skeletonDivider: {
    width: StyleSheet.hairlineWidth,
    height: 48,
  },
});

export default IndexValueChartComponent;
