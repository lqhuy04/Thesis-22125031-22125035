import React, { useState, useEffect, useMemo, useRef } from "react";
import {
  fetchStockDataByTimeFrame,
  parseDateTime,
  StockPriceData,
  CurrentPriceData,
  fetchCurrentPriceData,
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
} from "react-native";
import { useTheme } from "@/hooks/ThemeContext";
import DetailHeader from "../ui/DetailHeader";
import { SearchStockItem } from "@/helpers/SearchHelper";
import TradingViewChart from "../tradingView/TradingViewChart";
import { PriceData, VolumeData } from "../tradingView/utils";
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
  const [chartType, setChartType] = useState<"candle" | "area">("area");
  const [timeFrame, setTimeFrame] = useState<TIMEFRAME>(
    TIMEFRAME.FIFTEEN_MINUTES,
  );
  const [showTimeframeSheet, setShowTimeframeSheet] = useState(false);

  const slideAnim = useRef(new Animated.Value(SCREEN_HEIGHT)).current;
  const backdropAnim = useRef(new Animated.Value(0)).current;

  const [priceTimeframe1mData, setPriceTimeframe1mData] = useState<
    StockPriceData[]
  >([]);

  const [priceTimeframe5mData, setPriceTimeframe5mData] = useState<
    StockPriceData[]
  >([]);

  const [priceTimeframe15mData, setPriceTimeframe15mData] = useState<
    StockPriceData[]
  >([]);

  const [priceTimeframe30mData, setPriceTimeframe30mData] = useState<
    StockPriceData[]
  >([]);

  const [priceTimeframe1hData, setPriceTimeframe1hData] = useState<
    StockPriceData[]
  >([]);

  const [priceTimeframe1dData, setPriceTimeframe1dData] = useState<
    StockPriceData[]
  >([]);

  const [priceTimeframe1wData, setPriceTimeframe1wData] = useState<
    StockPriceData[]
  >([]);

  const [priceTimeframe1MData, setPriceTimeframe1MData] = useState<
    StockPriceData[]
  >([]);

  useEffect(() => {
    const fetchAll = async () => {
      try {
        const [res1m, res5m, res15m, res30m, res1h, res1d, res1w, res1M] =
          await Promise.all([
            fetchStockDataByTimeFrame(stockItem.symbol, "1m"),
            fetchStockDataByTimeFrame(stockItem.symbol, "5m"),
            fetchStockDataByTimeFrame(stockItem.symbol, "15m"),
            fetchStockDataByTimeFrame(stockItem.symbol, "30m"),
            fetchStockDataByTimeFrame(stockItem.symbol, "1h"),
            fetchStockDataByTimeFrame(stockItem.symbol, "1d"),
            fetchStockDataByTimeFrame(stockItem.symbol, "1w"),
            fetchStockDataByTimeFrame(stockItem.symbol, "1M"),
          ]);
        if (res1m?.status) setPriceTimeframe1mData(res1m.data);
        if (res5m?.status) setPriceTimeframe5mData(res5m.data);
        if (res15m?.status) setPriceTimeframe15mData(res15m.data);
        if (res30m?.status) setPriceTimeframe30mData(res30m.data);
        if (res1h?.status) setPriceTimeframe1hData(res1h.data);
        if (res1d?.status) setPriceTimeframe1dData(res1d.data);
        if (res1w?.status) setPriceTimeframe1wData(res1w.data);
        if (res1M?.status) setPriceTimeframe1MData(res1M.data);
      } catch (error) {
        console.error("Fetch error:", error);
      }
    };
    fetchAll();
  }, [stockItem.symbol]);

  const displayData = useMemo(() => {
    return timeFrame === TIMEFRAME.ONE_MINUTE
      ? priceTimeframe1mData
      : timeFrame === TIMEFRAME.FIVE_MINUTES
        ? priceTimeframe5mData
        : timeFrame === TIMEFRAME.FIFTEEN_MINUTES
          ? priceTimeframe15mData
          : timeFrame === TIMEFRAME.THIRTY_MINUTES
            ? priceTimeframe30mData
            : timeFrame === TIMEFRAME.ONE_HOUR
              ? priceTimeframe1hData
              : timeFrame === TIMEFRAME.ONE_DAY
                ? priceTimeframe1dData
                : timeFrame === TIMEFRAME.ONE_WEEK
                  ? priceTimeframe1wData
                  : timeFrame === TIMEFRAME.ONE_MONTH
                    ? priceTimeframe1MData
                    : [];
  }, [
    timeFrame,
    priceTimeframe1mData,
    priceTimeframe5mData,
    priceTimeframe15mData,
    priceTimeframe30mData,
    priceTimeframe1hData,
    priceTimeframe1dData,
    priceTimeframe1wData,
    priceTimeframe1MData,
  ]);

  const chartPriceData: PriceData[] = useMemo(() => {
    console.log("Display data length:", displayData?.length);
    if (
      displayData != null &&
      Array.isArray(displayData) &&
      displayData.length > 0
    ) {
      return displayData.map((item) => ({
        time: parseDateTime(item.TradingDate, item.Time) / 1000,
        open: item.Open,
        high: item.High,
        low: item.Low,
        close: item.Close,
      }));
    } else {
      return [];
    }
  }, [displayData]);

  const chartVolumeData: VolumeData[] = useMemo(() => {
    console.log("Display data length:", displayData?.length);
    if (
      displayData != null &&
      Array.isArray(displayData) &&
      displayData.length > 0
    ) {
      return displayData.map((item) => ({
        time: parseDateTime(item.TradingDate, item.Time) / 1000,
        value: item.Volume,
        color: item.Close >= item.Open ? theme.base.success : theme.base.error,
      }));
    } else {
      return [];
    }
  }, [displayData, theme.base.error, theme.base.success]);

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

      <TradingViewChart
        prices={chartPriceData}
        volumes={chartVolumeData}
        timeframe={timeFrame}
        chartType={chartType}
      />

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
