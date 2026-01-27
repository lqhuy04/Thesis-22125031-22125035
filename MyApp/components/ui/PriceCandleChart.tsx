import { StockData } from "@/helpers/DetailHelpers";
import React, { useMemo } from "react";
import { View, Text, Dimensions, StyleSheet } from "react-native";
import { useTheme } from "@/hooks/ThemeContext";
import { CandlestickChart } from "react-native-wagmi-charts";



function parseDate(dateString: string): Date {
  const parts = dateString.split('/');
  
  if (parts.length !== 3) {
    throw new Error('Invalid date format. Expected dd/mm/yyyy');
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
    throw new Error('Invalid date');
  }

  return date;
}

// Usage example:
const dateStr = "27/01/2026";
const date = parseDate(dateStr);
console.log(date); // Tue Jan 27 2026 00:00:00

interface Props {
  data: StockData[]
}

const PriceCandleChart = ({data}: Props) => {
  const { theme } = useTheme();

  const chartData = useMemo(() => {
    return data.map((item, index) => {
      return {
        timestamp: parseDate(item.TradingDate).getTime(),
        open: Number(item.Open) / 1000,
        close: Number(item.Close) / 1000,
        high: Number(item.High) / 1000,
        low: Number(item.Close) / 1000
      };
    });
  }, [data]);

  const screenWidth = Dimensions.get("window").width;


  return (
    <View style={styles.container}>
      {/* Tên mã chứng khoán */}
      <Text style={styles.symbolText}>{"Stock Chart"}</Text>

      {/* 3. Cấu hình Biểu đồ */}
      <CandlestickChart.Provider data={chartData}>
        <CandlestickChart width={screenWidth - 32} height={300}>
          <CandlestickChart.Candles
            positiveColor="#22c55e" // Xanh (Tăng)
            negativeColor="#ef4444" // Đỏ (Giảm)
          />
          {/* Đường chéo tương tác */}
          <CandlestickChart.Crosshair>
            <CandlestickChart.Tooltip />
          </CandlestickChart.Crosshair>
        </CandlestickChart>

        {/* Hiển thị thông tin chi tiết khi chạm vào nến */}
        <View style={styles.infoContainer}>
          <View style={styles.row}>
            <Text style={styles.label}>Giá đóng cửa: </Text>
            <CandlestickChart.PriceText
              type="close"
              style={styles.priceValue}
            />
          </View>
          <CandlestickChart.DatetimeText style={styles.dateText} />
        </View>
      </CandlestickChart.Provider>
    </View>
  );
}

const styles = StyleSheet.create({
  container: {
    backgroundColor: "#fff",
    paddingHorizontal: 16,
    paddingVertical: 20,
    alignItems: "center",
  },
  symbolText: {
    fontSize: 20,
    fontWeight: "bold",
    marginBottom: 10,
    alignSelf: "flex-start",
  },
  infoContainer: {
    marginTop: 15,
    width: "100%",
    padding: 10,
    backgroundColor: "#f8f9fa",
    borderRadius: 8,
  },
  row: {
    flexDirection: "row",
    alignItems: "center",
  },
  label: {
    fontSize: 14,
    color: "#666",
  },
  priceValue: {
    fontSize: 16,
    fontWeight: "bold",
    color: "#000",
  },
  dateText: {
    fontSize: 12,
    color: "#999",
    marginTop: 4,
  },
});

export default PriceCandleChart