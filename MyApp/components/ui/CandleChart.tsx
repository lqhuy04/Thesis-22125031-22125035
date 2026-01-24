import React, { useMemo } from "react";
import { View, StyleSheet, Dimensions, Text } from "react-native";
import { CandlestickChart } from "react-native-wagmi-charts";

const mockData = [
  {
    TradingDate: "23/01/2026",
    PriceChange: "-3700",
    PerPriceChange: "-5.20",
    CeilingPrice: "75800",
    FloorPrice: "66000",
    RefPrice: "70900",
    OpenPrice: "69400",
    HighestPrice: "70100",
    LowestPrice: "67200",
    ClosePrice: "67200",
    AveragePrice: "70100",
    ClosePriceAdjusted: "67200",
    TotalMatchVol: "16050400",
    TotalMatchVal: "1097314610000",
    TotalDealVal: "0",
    TotalDealVol: "0",
    ForeignBuyVolTotal: "1239630",
    ForeignCurrentRoom: "1036661128",
    ForeignSellVolTotal: "1437647",
    ForeignBuyValTotal: "84271563000",
    ForeignSellValTotal: "98599212600",
    TotalBuyTrade: "0",
    TotalBuyTradeVol: "0",
    TotalSellTrade: "0",
    TotalSellTradeVol: "0",
    NetBuySellVol: "-198017",
    NetBuySellVal: "-14327649600",
    TotalTradedVol: "16050400",
    TotalTradedValue: "1097314610000",
    Symbol: "VNM",
    Time: null,
  },
  {
    TradingDate: "22/01/2026",
    PriceChange: "600",
    PerPriceChange: "0.90",
    CeilingPrice: "75200",
    FloorPrice: "65400",
    RefPrice: "70300",
    OpenPrice: "71100",
    HighestPrice: "72800",
    LowestPrice: "70000",
    ClosePrice: "70900",
    AveragePrice: "72800",
    ClosePriceAdjusted: "70900",
    TotalMatchVol: "8055200",
    TotalMatchVal: "573373780000",
    TotalDealVal: "0",
    TotalDealVol: "0",
    ForeignBuyVolTotal: "506529",
    ForeignCurrentRoom: "1033962753",
    ForeignSellVolTotal: "852157",
    ForeignBuyValTotal: "35845443200",
    ForeignSellValTotal: "60976287100",
    TotalBuyTrade: "0",
    TotalBuyTradeVol: "0",
    TotalSellTrade: "0",
    TotalSellTradeVol: "0",
    NetBuySellVol: "-345628",
    NetBuySellVal: "-25130843900",
    TotalTradedVol: "8055200",
    TotalTradedValue: "573373780000",
    Symbol: "VNM",
    Time: null,
  },
  {
    TradingDate: "21/01/2026",
    PriceChange: "-3100",
    PerPriceChange: "-4.20",
    CeilingPrice: "78500",
    FloorPrice: "68300",
    RefPrice: "73400",
    OpenPrice: "73000",
    HighestPrice: "73000",
    LowestPrice: "70000",
    ClosePrice: "70300",
    AveragePrice: "73000",
    ClosePriceAdjusted: "70300",
    TotalMatchVol: "11234100",
    TotalMatchVal: "800042790000",
    TotalDealVal: "3993300000",
    TotalDealVol: "54000",
    ForeignBuyVolTotal: "498400",
    ForeignCurrentRoom: "1034099813",
    ForeignSellVolTotal: "3196776",
    ForeignBuyValTotal: "35404800000",
    ForeignSellValTotal: "228677017700",
    TotalBuyTrade: "0",
    TotalBuyTradeVol: "0",
    TotalSellTrade: "0",
    TotalSellTradeVol: "0",
    NetBuySellVol: "-2698376",
    NetBuySellVal: "-193272217700",
    TotalTradedVol: "11288100",
    TotalTradedValue: "804036090000",
    Symbol: "VNM",
    Time: null,
  },
  {
    TradingDate: "20/01/2026",
    PriceChange: "2800",
    PerPriceChange: "4",
    CeilingPrice: "75500",
    FloorPrice: "65700",
    RefPrice: "70600",
    OpenPrice: "71500",
    HighestPrice: "75500",
    LowestPrice: "71100",
    ClosePrice: "73400",
    AveragePrice: "75500",
    ClosePriceAdjusted: "73400",
    TotalMatchVol: "21521900",
    TotalMatchVal: "1596348490000",
    TotalDealVal: "4098090420",
    TotalDealVol: "58906",
    ForeignBuyVolTotal: "1361550",
    ForeignCurrentRoom: "1033175819",
    ForeignSellVolTotal: "4698827",
    ForeignBuyValTotal: "100796410420",
    ForeignSellValTotal: "347637552720",
    TotalBuyTrade: "0",
    TotalBuyTradeVol: "0",
    TotalSellTrade: "0",
    TotalSellTradeVol: "0",
    NetBuySellVol: "-3337277",
    NetBuySellVal: "-246841142300",
    TotalTradedVol: "21580806",
    TotalTradedValue: "1600446580420",
    Symbol: "VNM",
    Time: null,
  },
  {
    TradingDate: "19/01/2026",
    PriceChange: "1000",
    PerPriceChange: "1.40",
    CeilingPrice: "74400",
    FloorPrice: "64800",
    RefPrice: "69600",
    OpenPrice: "69800",
    HighestPrice: "71000",
    LowestPrice: "68300",
    ClosePrice: "70600",
    AveragePrice: "71000",
    ClosePriceAdjusted: "70600",
    TotalMatchVol: "10385300",
    TotalMatchVal: "722125070000",
    TotalDealVal: "0",
    TotalDealVol: "0",
    ForeignBuyVolTotal: "1023150",
    ForeignCurrentRoom: "1033127468",
    ForeignSellVolTotal: "416846",
    ForeignBuyValTotal: "71023680000",
    ForeignSellValTotal: "29110939200",
    TotalBuyTrade: "0",
    TotalBuyTradeVol: "0",
    TotalSellTrade: "0",
    TotalSellTradeVol: "0",
    NetBuySellVol: "606304",
    NetBuySellVal: "41912740800",
    TotalTradedVol: "10385300",
    TotalTradedValue: "722125070000",
    Symbol: "VNM",
    Time: null,
  },
];

// 1. Định nghĩa kiểu dữ liệu cho Response từ API của bạn
interface StockDataResponse {
  TradingDate: string;
  OpenPrice: string;
  HighestPrice: string;
  LowestPrice: string;
  ClosePrice: string;
  TotalMatchVol: string;
  Symbol: string;
  [key: string]: any; // Cho phép các trường khác không quan trọng
}

interface StockChartProps {
  listResponse?: StockDataResponse[];
}

const screenWidth = Dimensions.get("window").width;

const StockCandleChart: React.FC<StockChartProps> = ({ listResponse }) => {
  // 2. Chuyển đổi và memoize dữ liệu để tối ưu hiệu năng
  const formattedData = useMemo(() => {
    return mockData
      .map((item) => {
        // Chuyển "23/01/2026" thành định dạng "2026-01-23" để Date có thể đọc được
        const dateParts = item.TradingDate.split("/");
        const isoDate = `${dateParts[2]}-${dateParts[1]}-${dateParts[0]}`;

        return {
          timestamp: new Date(isoDate).getTime(),
          open: parseFloat(item.OpenPrice),
          high: parseFloat(item.HighestPrice),
          low: parseFloat(item.LowestPrice),
          close: parseFloat(item.ClosePrice),
        };
      })
      .sort((a, b) => a.timestamp - b.timestamp);
  }, []);

  if (formattedData.length === 0) {
    return (
      <View style={styles.container}>
        <Text>Không có dữ liệu hiển thị</Text>
      </View>
    );
  }

  return (
    <View style={styles.container}>
      {/* Tên mã chứng khoán */}
      <Text style={styles.symbolText}>{"Stock Chart"}</Text>

      {/* 3. Cấu hình Biểu đồ */}
      <CandlestickChart.Provider data={formattedData}>
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
};

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

export default StockCandleChart;
