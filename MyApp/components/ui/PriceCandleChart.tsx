import { StockData } from "@/helpers/DetailHelpers";
import React, {  useMemo } from "react";
import { View, Dimensions, StyleSheet } from "react-native";
import { useTheme } from "@/hooks/ThemeContext";
import { CandlestickChart, useCandlestickChart } from "react-native-wagmi-charts";
import { Text } from "./Text";
import Animated, {  useAnimatedReaction, useAnimatedStyle } from "react-native-reanimated";
import { scheduleOnRN } from "react-native-worklets";
import Svg, { Line } from "react-native-svg";


function parseDateTime(
  dateString: string,
  timeString: string
): number {
  // ---- Parse date ----
  const dateParts = dateString.split("/");

  if (dateParts.length !== 3) {
    throw new Error("Invalid date format. Expected dd/mm/yyyy");
  }

  const day = parseInt(dateParts[0], 10);
  const month = parseInt(dateParts[1], 10) - 1;
  const year = parseInt(dateParts[2], 10);

  // ---- Parse time ----
  const timeParts = timeString.split(":");

  if (timeParts.length !== 3) {
    throw new Error("Invalid time format. Expected hh:mm:ss");
  }

  const hours = parseInt(timeParts[0], 10);
  const minutes = parseInt(timeParts[1], 10);
  const seconds = parseInt(timeParts[2], 10);

  const date = new Date(year, month, day, hours, minutes, seconds);

  // ---- Validate date ----
  if (
    date.getFullYear() !== year ||
    date.getMonth() !== month ||
    date.getDate() !== day
  ) {
    throw new Error("Invalid date");
  }

  // ---- Validate time ----
  if (
    hours < 0 || hours > 23 ||
    minutes < 0 || minutes > 59 ||
    seconds < 0 || seconds > 59
  ) {
    throw new Error("Invalid time");
  }

  return date.getTime(); // ✅ return timestamp
}

function formatTimestamp(timestamp: number): string {
  const date = new Date(timestamp);

  const pad = (num: number) => num.toString().padStart(2, "0");

  const day = pad(date.getDate());
  const month = pad(date.getMonth() + 1); // month is 0-based
  const year = date.getFullYear();

  const hours = pad(date.getHours());
  const minutes = pad(date.getMinutes());

  return `${day}/${month}/${year} ${hours}:${minutes}`;
}

function generateIndexTicks<T extends { timestamp: number }>(
  data: T[],
  count = 7,
  startIndex = 3 // 👈 mặc định phần tử thứ 3
) {
  if (!data.length || startIndex >= data.length) return [];

  const lastIndex = data.length - 1;

  // 👇 range mới tính từ startIndex
  const range = lastIndex - startIndex;
  const step = range / (count - 1);

  const pad = (n: number) => n.toString().padStart(2, "0");

  return Array.from({ length: count }).map((_, i) => {
    const index = Math.round(startIndex + step * i);
    const item = data[index];

    const date = new Date(item.timestamp);

    const hours = pad(date.getHours());
    const minutes = pad(date.getMinutes());

    return {
      label: `${hours}:${minutes}`,
      index,
    };
  });
}

const LastOpenLine = () => {
  const { theme } = useTheme();
  const { data, domain, height, width } = useCandlestickChart();

  if (!data?.length) return null;

  const lastCandle = data[data.length - 1];
  const openPrice = lastCandle.open;

  const [ min, max ] = domain;

  if (min === undefined || max === undefined) return null;

  // 👇 Convert price → y coordinate
  const y =
    height - ((openPrice - min) / (max - min)) * height;

  return (
    <Svg
      width={width}
      height={height}
      style={{ position: "absolute" }}
    >
      <Line
        x1="0"
        y1={y}
        x2={width}
        y2={y}
        stroke={theme.border.default}
        strokeWidth="1"
        strokeDasharray="6 4"
      />
    </Svg>
  );
};

const AnimatedView = Animated.createAnimatedComponent(View);

const CandleTooltip = () => {
  const { theme } = useTheme();
  const { data, currentIndex, currentX, width } = useCandlestickChart();

  const [candle, setCandle] = React.useState<{
    open: number;
    high: number;
    low: number;
    close: number;
    time: number;
  } | null>(null);

  // 👇 Update dữ liệu khi index thay đổi
  useAnimatedReaction(
    () => Math.round(currentIndex.value),
    (index) => {
      if (index === -1) {
        scheduleOnRN(setCandle, null);
        return;
      }

      const item = data[index];
      if (!item) return;

      const convertTime = item.timestamp;

      scheduleOnRN(setCandle, {
        open: item.open,
        high: item.high,
        low: item.low,
        close: item.close,
        time: convertTime
      });
    },
    [data]
  );

  // 👇 Animated style cho position
  const animatedStyle = useAnimatedStyle(() => {
    const tooltipWidth = 160; // ước lượng width tooltip
    let x = currentX.value - tooltipWidth / 2;

    // 👇 tránh tràn mép trái
    if (x < 0) x = 0;

    // 👇 tránh tràn mép phải
    if (x > width - tooltipWidth) {
      x = width - tooltipWidth;
    }

    return {
      left: x,
    };
  });

  if (!candle) return null;

  const isUp = candle.close >= candle.open;

  const format = (v: number) =>
    v.toLocaleString("vi-VN", { maximumFractionDigits: 2 });

  return (
    <AnimatedView
      style={[
        {
          position: "absolute",
          top: 0,
          width: 160,
          padding: 10,
          borderRadius: 8,
          borderWidth: 1,
          backgroundColor: theme.background.surface,
          borderColor: theme.border.default,
          alignItems: 'center',
          justifyContent: 'center'
        },
        animatedStyle,
      ]}
    >
      <View style={{flexDirection: 'row', alignItems: 'center'}}>
      <Text typography="titleSmall" color={theme.text.primary}>
        O{' '}
        <Text typography="titleSmall" color={isUp? theme.base.success : theme.base.error}>
          {format(candle.open)}
        </Text>
      </Text>

      <View style={{width: 8}}/>

      <Text typography="titleSmall" color={theme.text.primary}>
        H{' '}
        <Text typography="titleSmall" color={isUp? theme.base.success : theme.base.error}>
          {format(candle.high)}
        </Text>
      </Text>
      </View>

      <View style={{flexDirection: 'row', alignItems: 'center'}}>
      <Text typography="titleSmall" color={theme.text.primary}>
        L{' '}
        <Text typography="titleSmall" color={isUp? theme.base.success : theme.base.error}>
          {format(candle.low)}
        </Text>
      </Text>

      <View style={{width: 8}}/>

      <Text typography="titleSmall" color={theme.text.primary}>
        C{' '}
        <Text typography="titleSmall" color={isUp? theme.base.success : theme.base.error}>
          {format(candle.close)}
        </Text>
      </Text>
      </View>

      <Text typography="titleSmall" color={theme.text.primary}>
        {formatTimestamp(candle.time)}
      </Text>

    </AnimatedView>
  );
};

interface Props {
  data: StockData[];
}

const PriceCandleChart = ({ data }: Props) => {
  const { theme } = useTheme();

  const chartData = useMemo(() => {
    return data.map((item, _) => {
      return {
        timestamp: parseDateTime(item.TradingDate, item?.Time),
        open: Number(item.Open),
        close: Number(item.Close),
        high: Number(item.High),
        low: Number(item.Low),
      };
    });
  }, [data]);

  const timeTicks = useMemo(() => {
    return generateIndexTicks(chartData, 7);
  }, [chartData]);

  const screenWidth = Dimensions.get("window").width;

  const [labelWidths, setLabelWidths] = React.useState<number[]>([]);

  return (
    data.length !== 0 && (

        <View >
          <View style={styles.container}>
            {/* 3. Cấu hình Biểu đồ */}
            <CandlestickChart.Provider data={chartData}>
              <CandlestickChart width={screenWidth} height={278}>

              <LastOpenLine />

                <CandlestickChart.Candles
                  positiveColor={theme.base.success} // Xanh (Tăng)
                  negativeColor={theme.base.error} // Đỏ (Giảm)
                />
                {/* Đường chéo tương tác */}
                <CandlestickChart.Crosshair
                color={theme.base.primary}
                  horizontalCrosshairProps={{
                    style: {
                      backgroundColor: "transparent",
                      borderWidth: 0,
                    },
                  }}
                >
                </CandlestickChart.Crosshair>
                <CandleTooltip />
              </CandlestickChart>
            </CandlestickChart.Provider>
          </View>
  

        <View
          style={{
            flexDirection: "row",
            justifyContent: "space-between",
            marginHorizontal: 16,
          }}
        >
          {timeTicks.map((tick, i) => {
    const x =
      (tick.index / (chartData.length - 1)) * screenWidth;

    return (
      <View
        key={i}
        style={{
          position: "absolute",
          left:
            x -
            ((labelWidths[i] ?? 0) ) + 4, // 👈 trừ đúng 1/2 width
        }}
      >
        <Text
          typography="titleSmall"
          onLayout={(e) => {
            const w = e.nativeEvent.layout.width;

            setLabelWidths((prev) => {
              const copy = [...prev];
              copy[i] = w;
              return copy;
            });
          }}
        >
          {tick.label}
        </Text>
      </View>
    );
  })}
        </View>
      </View>
    )
  );
};

const styles = StyleSheet.create({
  container: {},
});

export default PriceCandleChart;
