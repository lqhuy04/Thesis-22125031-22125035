import { StockData } from "@/helpers/DetailHelpers";
import React, { useMemo } from "react";
import { View, Dimensions, StyleSheet } from "react-native";
import { useTheme } from "@/hooks/ThemeContext";
import { CandlestickChart } from "react-native-wagmi-charts";
import { Text } from "./Text";

function parseDate(dateString: string): Date {
  const parts = dateString.split("/");

  if (parts.length !== 3) {
    throw new Error("Invalid date format. Expected dd/mm/yyyy");
  }

  const day = parseInt(parts[0], 10);
  const month = parseInt(parts[1], 10) - 1; // Month is 0-indexed in JavaScript
  const year = parseInt(parts[2], 10);

  const date = new Date(year, month, day);

  // Validate the date
  if (
    date.getDate() !== day ||
    date.getMonth() !== month ||
    date.getFullYear() !== year
  ) {
    throw new Error("Invalid date");
  }

  return date;
}

interface Props {
  data: StockData[];
}

const PriceCandleChart = ({ data }: Props) => {
  const { theme } = useTheme();

  const chartData = useMemo(() => {
    return data.map((item, _) => {
      return {
        timestamp: parseDate(item.TradingDate).getTime(),
        open: Number(item.Open),
        close: Number(item.Close),
        high: Number(item.High),
        low: Number(item.Low),
      };
    });
  }, [data]);

  const screenWidth = Dimensions.get("window").width;

  return (
    <View>
      <View style={{ borderWidth: 1, borderColor: theme.border.default }}>
        <View
          style={{
            flexDirection: "row",
            position: "absolute",
          }}
        >
          {Array.from({
            length: Math.floor((screenWidth) / 36) + 1,
          }).map((_, index) => {
            return (
              <View
                key={index.toString()}
                style={{
                  width: 1,
                  height: 278,
                  backgroundColor: theme.border.default,
                  marginHorizontal: 18,
                }}
              />
            );
          })}
        </View>

        <View
          style={{
            position: "absolute",
          }}
        >
          {Array.from({
            length: Math.floor(278 / 36) + 1,
          }).map((_, index) => {
            return (
              <View
                key={index.toString()}
                style={{
                  width: screenWidth,
                  height: 1,
                  backgroundColor: theme.border.default,
                  marginVertical: 18,
                }}
              />
            );
          })}
        </View>

        <View style={styles.container}>
          {/* 3. Cấu hình Biểu đồ */}
          <CandlestickChart.Provider data={chartData}>
            <CandlestickChart width={screenWidth} height={278}>
              <CandlestickChart.Candles
                positiveColor={theme.base.success} // Xanh (Tăng)
                negativeColor={theme.base.error} // Đỏ (Giảm)
              />
              {/* Đường chéo tương tác */}
              <CandlestickChart.Crosshair>
                <CandlestickChart.Tooltip />
              </CandlestickChart.Crosshair>
            </CandlestickChart>
          </CandlestickChart.Provider>
        </View>

      </View>

      <View
        style={{
          flexDirection: "row",
          justifyContent: "space-between",
          marginVertical: 4,
          marginHorizontal: 16,
        }}
      >
        <Text typography="titleSmall">09:00</Text>
        <Text typography="titleSmall">10:00</Text>
        <Text typography="titleSmall">11:00</Text>
        <Text typography="titleSmall">12:00</Text>
        <Text typography="titleSmall">13:00</Text>
        <Text typography="titleSmall">14:00</Text>
        <Text typography="titleSmall">15:00</Text>
      </View>
    </View>
  );
};

const styles = StyleSheet.create({
  container: {},
});

export default PriceCandleChart;
