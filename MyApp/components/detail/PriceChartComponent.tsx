import React, { useState, useEffect, useMemo, useRef } from "react";
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
  Text,
  Modal,
  Animated,
  Pressable,
  StyleSheet,
  Dimensions,
  ActivityIndicator,
} from "react-native";
import { useTheme } from "@/hooks/ThemeContext";
import DetailHeader from "../ui/DetailHeader";
import { SearchStockItem } from "@/helpers/SearchHelper";
import TradingViewChart from "../tradingView/TradingViewChart";
import { BollData, MAData, PriceData, VolumeData } from "../tradingView/utils";
import { MaterialCommunityIcons, MaterialIcons } from "@expo/vector-icons";
import { router } from "expo-router";

interface Props {
  stockItem: SearchStockItem;
}

const enum TIMEFRAME {
  ONE_MINUTE = 1,
  FIVE_MINUTES = 2,
  FIFTEEN_MINUTES = 3,
  THIRTY_MINUTES = 4,
  ONE_HOUR = 5,
  ONE_DAY = 6,
  ONE_WEEK = 7,
  ONE_MONTH = 8,
}

const TIMEFRAME_OPTIONS = [
  { label: "1 Phút", value: TIMEFRAME.ONE_MINUTE },
  { label: "5 Phút", value: TIMEFRAME.FIVE_MINUTES },
  { label: "15 Phút", value: TIMEFRAME.FIFTEEN_MINUTES },
  { label: "30 Phút", value: TIMEFRAME.THIRTY_MINUTES },
  { label: "1 Giờ", value: TIMEFRAME.ONE_HOUR },
  { label: "1 Ngày", value: TIMEFRAME.ONE_DAY },
  { label: "1 Tuần", value: TIMEFRAME.ONE_WEEK },
  { label: "1 Tháng", value: TIMEFRAME.ONE_MONTH },
];

const { height: SCREEN_HEIGHT } = Dimensions.get("window");

const PriceChartComponent = ({ stockItem }: Props) => {
  const { theme } = useTheme();
  const [loading, setLoading] = useState<boolean>(false);
  const [chartType, setChartType] = useState<"candle" | "area">("candle");
  const [timeFrame, setTimeFrame] = useState<TIMEFRAME>(
    TIMEFRAME.FIFTEEN_MINUTES,
  );
  const [showVolume, setShowVolume] = useState<boolean>(false);
  const [technicalIndicatorMode1, setTechnicalIndicatorMode1] = useState<
    string | null
  >(null);

  const [showTimeframeSheet, setShowTimeframeSheet] = useState(false);

  const slideAnim = useRef(new Animated.Value(SCREEN_HEIGHT)).current;
  const backdropAnim = useRef(new Animated.Value(0)).current;

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
                        : "1d";

        const [indicatorRes, priceRes] = await Promise.all([
          getTechnicalIndicators(stockItem.symbol, interval),
          fetchStockDataByTimeFrame(stockItem.symbol, interval),
        ]);

        if (indicatorRes?.status) {
          setTechnicalIndicatorsData(indicatorRes.data ?? []);
        } else {
          setTechnicalIndicatorsData([]);
        }

        if (priceRes?.status) {
          setPriceData(priceRes.data ?? []);
        } else {
          setPriceData([]);
        }
      } catch (error) {
        console.error("Fetch error:", error);
        setTechnicalIndicatorsData([]);
        setPriceData([]);
      } finally {
        setLoading(false); // ✅ đảm bảo luôn chạy sau cùng
      }
    };

    fetchData();
  }, [stockItem.symbol, timeFrame]);

  const chartPriceData: PriceData[] = useMemo(() => {
    if (priceData != null && Array.isArray(priceData) && priceData.length > 0) {
      return priceData.map((item) => ({
        time: parseDateTime(item.TradingDate, item.Time) / 1000,
        open: item.Open,
        high: item.High,
        low: item.Low,
        close: item.Close,
      }));
    } else {
      return [];
    }
  }, [priceData]);

  const chartMAData: MAData[] = useMemo(() => {
    if (
      technicalIndicatorsData != null &&
      Array.isArray(technicalIndicatorsData) &&
      technicalIndicatorsData.length > 0
    ) {
      return technicalIndicatorsData.map((item) => ({
        time: parseDateTime(item.TradingDate, item.Time) / 1000,
        ma20: item.sma_20,
        ma50: item.sma_50,
      }));
    } else {
      return [];
    }
  }, [technicalIndicatorsData]);

  const chartBOLLData: BollData[] = useMemo(() => {
    if (
      technicalIndicatorsData != null &&
      Array.isArray(technicalIndicatorsData) &&
      technicalIndicatorsData.length > 0
    ) {
      return technicalIndicatorsData.map((item) => ({
        time: parseDateTime(item.TradingDate, item.Time) / 1000,
        boll: item.bb_middle,
        ub: item.bb_upper,
        lb: item.bb_lower,
      }));
    } else {
      return [];
    }
  }, [technicalIndicatorsData]);

  const chartVolumeData: VolumeData[] = useMemo(() => {
    if (priceData != null && Array.isArray(priceData) && priceData.length > 0) {
      return priceData.map((item) => ({
        time: parseDateTime(item.TradingDate, item.Time) / 1000,
        value: item.Volume,
        color: item.Close >= item.Open ? theme.base.success : theme.base.error,
      }));
    } else {
      return [];
    }
  }, [priceData, theme.base.error, theme.base.success]);

  const openSheet = () => {
    setShowTimeframeSheet(true);
    Animated.parallel([
      Animated.spring(slideAnim, {
        toValue: 0,
        useNativeDriver: true,
        bounciness: 4,
      }),
      Animated.timing(backdropAnim, {
        toValue: 1,
        duration: 250,
        useNativeDriver: true,
      }),
    ]).start();
  };

  const closeSheet = (callback?: () => void) => {
    Animated.parallel([
      Animated.timing(slideAnim, {
        toValue: SCREEN_HEIGHT,
        duration: 220,
        useNativeDriver: true,
      }),
      Animated.timing(backdropAnim, {
        toValue: 0,
        duration: 220,
        useNativeDriver: true,
      }),
    ]).start(() => {
      setShowTimeframeSheet(false);
      callback?.();
    });
  };

  const handleSelectTimeframe = (value: TIMEFRAME) => {
    closeSheet(() => setTimeFrame(value));
  };

  const selectedLabel =
    TIMEFRAME_OPTIONS.find((o) => o.value === timeFrame)?.label ?? "";

  return (
    <View style={{ marginTop: 12 }}>
      <DetailHeader symbol={stockItem.symbol} />

      {loading ? (
        <View
          style={{
            height: 300,
            alignItems: "center",
            justifyContent: "center",
          }}
        >
          <ActivityIndicator size="small" color={theme.base.primary} />
        </View>
      ) : (
        <TradingViewChart
          prices={chartPriceData}
          volumes={chartVolumeData}
          maData={chartMAData}
          bollData={chartBOLLData}
          timeframe={timeFrame}
          chartType={chartType}
          showVolume={showVolume}
          technicalIndicatorMode1={technicalIndicatorMode1}
        />
      )}

      <View
        style={{
          flexDirection: "row",
          alignItems: "center",
          marginVertical: 8,
          marginHorizontal: 12,
        }}
      >
        {/* Chart type toggle */}
        <TouchableOpacity
          onPress={() => setChartType(chartType === "area" ? "candle" : "area")}
          style={[
            styles.iconBtn,
            {
              backgroundColor: theme.background.surface,
              borderColor: theme.border.default,
              marginRight: 8,
            },
          ]}
        >
          {chartType === "area" ? (
            <MaterialCommunityIcons
              name="chart-timeline-variant"
              size={18}
              color="black"
            />
          ) : (
            <MaterialIcons name="candlestick-chart" size={18} color="black" />
          )}
        </TouchableOpacity>

        {/* Timeframe button */}
        <TouchableOpacity
          onPress={openSheet}
          style={[
            styles.iconBtn,
            {
              backgroundColor: theme.background.surface,
              borderColor: theme.border.default,
              marginHorizontal: 8,
              flexDirection: "row",
              alignItems: "center",
              gap: 4,
              paddingHorizontal: 8,
            },
          ]}
        >
          <MaterialIcons name="date-range" size={18} color="black" />
          <Text style={{ fontSize: 12, color: "black", fontWeight: "500" }}>
            {selectedLabel}
          </Text>
        </TouchableOpacity>

        {/* Chart type toggle */}
        <TouchableOpacity
          onPress={() => {
            if (technicalIndicatorMode1 === "MA") {
              setTechnicalIndicatorMode1(null);
            } else {
              setTechnicalIndicatorMode1("MA");
            }
          }}
          style={[
            styles.iconBtn,
            {
              backgroundColor: theme.background.surface,
              borderColor: theme.border.default,
              marginRight: 8,
            },
          ]}
        >
          {chartType === "area" ? (
            <MaterialCommunityIcons
              name="chart-timeline-variant"
              size={18}
              color="black"
            />
          ) : (
            <MaterialIcons name="candlestick-chart" size={18} color="black" />
          )}
        </TouchableOpacity>

        {/* Chart type toggle */}
        <TouchableOpacity
          onPress={() => {
            if (technicalIndicatorMode1 === "BOLL") {
              setTechnicalIndicatorMode1(null);
            } else {
              setTechnicalIndicatorMode1("BOLL");
            }
          }}
          style={[
            styles.iconBtn,
            {
              backgroundColor: theme.background.surface,
              borderColor: theme.border.default,
              marginRight: 8,
            },
          ]}
        >
          {chartType === "area" ? (
            <MaterialCommunityIcons
              name="chart-timeline-variant"
              size={18}
              color="black"
            />
          ) : (
            <MaterialIcons name="candlestick-chart" size={18} color="black" />
          )}
        </TouchableOpacity>

        <View style={{ flex: 1 }} />

        <TouchableOpacity
          onPress={() => {
            router.push({
              pathname: "/TradingViewScreen",
              params: {
                data: JSON.stringify({
                  symbol: stockItem.symbol,
                }),
              },
            });
          }}
          style={[
            styles.iconBtn,
            {
              backgroundColor: theme.background.surface,
              borderColor: theme.border.default,
              marginHorizontal: 8,
              flexDirection: "row",
              alignItems: "center",
              gap: 4,
              paddingHorizontal: 8,
            },
          ]}
        >
          <MaterialCommunityIcons name="arrow-expand" size={18} color="black" />
        </TouchableOpacity>

        {/* Chart type toggle */}
        <TouchableOpacity
          onPress={() => setShowVolume((prev) => !prev)}
          style={[
            styles.iconBtn,
            {
              backgroundColor: theme.background.surface,
              borderColor: theme.border.default,
              marginRight: 8,
            },
          ]}
        >
          {chartType === "area" ? (
            <MaterialCommunityIcons
              name="chart-timeline-variant"
              size={18}
              color="black"
            />
          ) : (
            <MaterialIcons name="candlestick-chart" size={18} color="black" />
          )}
        </TouchableOpacity>
      </View>

      {/* Bottom Sheet */}
      <Modal visible={showTimeframeSheet} transparent animationType="none">
        {/* Backdrop */}
        <Animated.View
          style={[
            StyleSheet.absoluteFill,
            styles.backdrop,
            { opacity: backdropAnim },
          ]}
        >
          <Pressable
            style={StyleSheet.absoluteFill}
            onPress={() => closeSheet()}
          />
        </Animated.View>

        {/* Sheet */}
        <Animated.View
          style={[
            styles.sheet,
            { backgroundColor: theme.background.surface ?? "#fff" },
            { transform: [{ translateY: slideAnim }] },
          ]}
        >
          {/* Handle */}
          <View style={styles.handle} />

          <Text
            style={[
              styles.sheetTitle,
              { color: theme.text?.primary ?? "#111" },
            ]}
          >
            Chọn khung thời gian
          </Text>

          <View style={styles.optionsContainer}>
            {TIMEFRAME_OPTIONS.map((option) => {
              const isSelected = timeFrame === option.value;
              return (
                <TouchableOpacity
                  key={option.value}
                  onPress={() => handleSelectTimeframe(option.value)}
                  style={[
                    styles.optionBtn,
                    {
                      backgroundColor: isSelected
                        ? (theme.base?.primary ?? "#1a56db")
                        : (theme.background?.surface ?? "#f3f4f6"),
                      borderColor: isSelected
                        ? (theme.base?.primary ?? "#1a56db")
                        : (theme.border?.default ?? "#e5e7eb"),
                    },
                  ]}
                >
                  <Text
                    style={[
                      styles.optionText,
                      {
                        color: isSelected
                          ? "#fff"
                          : (theme.text?.primary ?? "#111"),
                      },
                    ]}
                  >
                    {option.label}
                  </Text>
                </TouchableOpacity>
              );
            })}
          </View>
        </Animated.View>
      </Modal>
    </View>
  );
};

const styles = StyleSheet.create({
  iconBtn: {
    borderRadius: 2,
    borderWidth: 1,
    padding: 4,
  },
  backdrop: {
    backgroundColor: "rgba(0,0,0,0.4)",
  },
  sheet: {
    position: "absolute",
    bottom: 0,
    left: 0,
    right: 0,
    borderTopLeftRadius: 16,
    borderTopRightRadius: 16,
    paddingHorizontal: 20,
    paddingBottom: 36,
    paddingTop: 12,
    elevation: 20,
    shadowColor: "#000",
    shadowOffset: { width: 0, height: -3 },
    shadowOpacity: 0.12,
    shadowRadius: 8,
  },
  handle: {
    width: 40,
    height: 4,
    borderRadius: 2,
    backgroundColor: "#d1d5db",
    alignSelf: "center",
    marginBottom: 16,
  },
  sheetTitle: {
    fontSize: 15,
    fontWeight: "600",
    marginBottom: 16,
  },
  optionsContainer: {
    flexDirection: "row",
    gap: 10,
  },
  optionBtn: {
    flex: 1,
    paddingVertical: 12,
    borderRadius: 8,
    borderWidth: 1,
    alignItems: "center",
    justifyContent: "center",
  },
  optionText: {
    fontSize: 14,
    fontWeight: "500",
  },
});

export default PriceChartComponent;
