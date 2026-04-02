// import {
//   parseDateTime,
//   StockData,
//   TechnicalIndicatorData,
// } from "@/helpers/DetailHelpers";
// import React, { useMemo } from "react";
// import { View, Dimensions } from "react-native";
// import { useTheme } from "@/hooks/ThemeContext";
// import {
//   CandlestickChart,
//   useCandlestickChart,
// } from "react-native-wagmi-charts";
// import { Text } from "./Text";
// import Animated, {
//   useAnimatedReaction,
//   useAnimatedStyle,
// } from "react-native-reanimated";
// import { scheduleOnRN } from "react-native-worklets";
// import Svg, { Line } from "react-native-svg";

// function formatTimestamp(timestamp: number): string {
//   const date = new Date(timestamp);

//   const pad = (num: number) => num.toString().padStart(2, "0");

//   const day = pad(date.getDate());
//   const month = pad(date.getMonth() + 1); // month is 0-based
//   const year = date.getFullYear();

//   const hours = pad(date.getHours());
//   const minutes = pad(date.getMinutes());

//   return `${day}/${month}/${year} ${hours}:${minutes}`;
// }

// const LastOpenLine = () => {
//   const { theme } = useTheme();
//   const { data, domain, height, width } = useCandlestickChart();

//   if (!data?.length) return null;

//   const lastCandle = data[data.length - 1];
//   const openPrice = lastCandle.close;

//   const [min, max] = domain;

//   if (min === undefined || max === undefined) return null;

//   // 👇 Convert price → y coordinate
//   const y = height - ((openPrice - min) / (max - min)) * height;

//   return (
//     <Svg width={width} height={height} style={{ position: "absolute" }}>
//       <Line
//         x1="0"
//         y1={y}
//         x2={width}
//         y2={y}
//         stroke={theme.border.default}
//         strokeWidth="1"
//         strokeDasharray="6 4"
//       />
//     </Svg>
//   );
// };

// const AnimatedView = Animated.createAnimatedComponent(View);

// const CandleTooltip = () => {
//   const { theme } = useTheme();
//   const { data, currentIndex, currentX, width } = useCandlestickChart();

//   const [candle, setCandle] = React.useState<{
//     open: number;
//     high: number;
//     low: number;
//     close: number;
//     time: number;
//   } | null>(null);

//   // 👇 Update dữ liệu khi index thay đổi
//   useAnimatedReaction(
//     () => Math.round(currentIndex.value),
//     (index) => {
//       if (index === -1) {
//         scheduleOnRN(setCandle, null);
//         return;
//       }

//       const item = data[index];
//       if (!item) return;

//       const convertTime = item.timestamp;

//       scheduleOnRN(setCandle, {
//         open: item.open,
//         high: item.high,
//         low: item.low,
//         close: item.close,
//         time: convertTime,
//       });
//     },
//     [data],
//   );

//   // 👇 Animated style cho position
//   const animatedStyle = useAnimatedStyle(() => {
//     const tooltipWidth = 160; // ước lượng width tooltip
//     let x = currentX.value - tooltipWidth / 2;

//     // 👇 tránh tràn mép trái
//     if (x < 0) x = 0;

//     // 👇 tránh tràn mép phải
//     if (x > width - tooltipWidth) {
//       x = width - tooltipWidth;
//     }

//     return {
//       left: x,
//     };
//   });

//   if (!candle) return null;

//   const isUp = candle.close >= candle.open;

//   const format = (v: number) =>
//     v.toLocaleString("vi-VN", { maximumFractionDigits: 2 });

//   return (
//     <AnimatedView
//       style={[
//         {
//           position: "absolute",
//           top: 0,
//           width: 160,
//           padding: 10,
//           borderRadius: 8,
//           borderWidth: 1,
//           backgroundColor: theme.background.surface,
//           borderColor: theme.border.default,
//           alignItems: "center",
//           justifyContent: "center",
//         },
//         animatedStyle,
//       ]}
//     >
//       <View style={{ flexDirection: "row", alignItems: "center" }}>
//         <Text typography="titleSmall" color={theme.text.primary}>
//           O{" "}
//           <Text
//             typography="titleSmall"
//             color={isUp ? theme.base.success : theme.base.error}
//           >
//             {format(candle.open)}
//           </Text>
//         </Text>

//         <View style={{ width: 8 }} />

//         <Text typography="titleSmall" color={theme.text.primary}>
//           H{" "}
//           <Text
//             typography="titleSmall"
//             color={isUp ? theme.base.success : theme.base.error}
//           >
//             {format(candle.high)}
//           </Text>
//         </Text>
//       </View>

//       <View style={{ flexDirection: "row", alignItems: "center" }}>
//         <Text typography="titleSmall" color={theme.text.primary}>
//           L{" "}
//           <Text
//             typography="titleSmall"
//             color={isUp ? theme.base.success : theme.base.error}
//           >
//             {format(candle.low)}
//           </Text>
//         </Text>

//         <View style={{ width: 8 }} />

//         <Text typography="titleSmall" color={theme.text.primary}>
//           C{" "}
//           <Text
//             typography="titleSmall"
//             color={isUp ? theme.base.success : theme.base.error}
//           >
//             {format(candle.close)}
//           </Text>
//         </Text>
//       </View>

//       <Text typography="titleSmall" color={theme.text.primary}>
//         {formatTimestamp(candle.time)}
//       </Text>
//     </AnimatedView>
//   );
// };

// interface Props {
//   height: number;
//   data: StockData[];
//   technicalIndicatorData: TechnicalIndicatorData[];
//   technicalIndicatorMode1: "MA" | "BOLL" | null;
// }

// const PriceCandleStickChart = ({
//   height,
//   data,
//   technicalIndicatorData,
//   technicalIndicatorMode1,
// }: Props) => {
//   const { theme } = useTheme();

//   const ma20Data = useMemo(() => {
//     return data.map((item, index) => ({
//       timestamp: parseDateTime(item.TradingDate, item.Time),
//       value: Number(technicalIndicatorData[index]?.indicators.sma_20),
//     }));
//   }, [data, technicalIndicatorData]);

//   const ma50Data = useMemo(() => {
//     return data.map((item, index) => ({
//       timestamp: parseDateTime(item.TradingDate, item.Time),
//       value: Number(technicalIndicatorData[index]?.indicators.sma_50),
//     }));
//   }, [data, technicalIndicatorData]);

//   const bbUpperData = useMemo(() => {
//     return data.map((item, index) => ({
//       timestamp: parseDateTime(item.TradingDate, item.Time),
//       value: Number(technicalIndicatorData[index]?.indicators.bb_upper),
//     }));
//   }, [data, technicalIndicatorData]);

//   const bbLowerData = useMemo(() => {
//     return data.map((item, index) => ({
//       timestamp: parseDateTime(item.TradingDate, item.Time),
//       value: Number(technicalIndicatorData[index]?.indicators.bb_lower),
//     }));
//   }, [data, technicalIndicatorData]);

//   const minValue = useMemo(() => {
//     const minPrice = Math.min(...data.map((item) => Number(item.Low)));
//     const minBBLower = Math.min(...bbLowerData.map((item) => item.value));
//     const minMA20 = Math.min(...ma20Data.map((item) => item.value));
//     const minMA50 = Math.min(...ma50Data.map((item) => item.value));

//     if (technicalIndicatorMode1 === "MA") {
//       return Math.min(minPrice, minMA20, minMA50);
//     } else if (technicalIndicatorMode1 === "BOLL") {
//       return Math.min(minPrice, minBBLower);
//     } else {
//       return minPrice;
//     }
//   }, [bbLowerData, data, ma20Data, ma50Data, technicalIndicatorMode1]);

//   const maxValue = useMemo(() => {
//     const maxPrice = Math.max(...data.map((item) => Number(item.High)));
//     const maxBBUpper = Math.max(...bbUpperData.map((item) => item.value));
//     const maxMA20 = Math.max(...ma20Data.map((item) => item.value));
//     const maxMA50 = Math.max(...ma50Data.map((item) => item.value));

//     if (technicalIndicatorMode1 === "MA") {
//       return Math.max(maxPrice, maxMA20, maxMA50);
//     } else if (technicalIndicatorMode1 === "BOLL") {
//       return Math.max(maxPrice, maxBBUpper);
//     } else {
//       return maxPrice;
//     }
//   }, [bbUpperData, data, ma20Data, ma50Data, technicalIndicatorMode1]);

//   const chartData = useMemo(() => {
//     return data.map((item, _) => {
//       return {
//         timestamp: parseDateTime(item.TradingDate, item?.Time),
//         open: Number(item.Open),
//         close: Number(item.Close),
//         high: Number(item.High),
//         low: Number(item.Low),
//       };
//     });
//   }, [data]);

//   const screenWidth = Dimensions.get("window").width;

//   return (
//     data.length !== 0 && (
//       <View>
//         <CandlestickChart.Provider
//           data={chartData}
//           valueRangeY={[minValue, maxValue]}
//         >
//           <CandlestickChart width={screenWidth} height={height}>
//             <LastOpenLine />

//             <CandlestickChart.Candles
//               positiveColor={theme.base.success} // Xanh (Tăng)
//               negativeColor={theme.base.error} // Đỏ (Giảm)
//             />
//             {/* Đường chéo tương tác */}
//             <CandlestickChart.Crosshair
//               color={theme.base.primary}
//               horizontalCrosshairProps={{
//                 style: {
//                   backgroundColor: "transparent",
//                   borderWidth: 0,
//                 },
//               }}
//             ></CandlestickChart.Crosshair>
//             <CandleTooltip />
//           </CandlestickChart>
//         </CandlestickChart.Provider>
//       </View>
//     )
//   );
// };

// export default PriceCandleStickChart;
