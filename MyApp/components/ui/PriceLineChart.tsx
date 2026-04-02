// import React, { useMemo } from "react";
// import { View, Dimensions } from "react-native";
// import { useTheme } from "@/hooks/ThemeContext";
// import { LineChart, useLineChart } from "react-native-wagmi-charts";
// import { Text } from "./Text";
// import Animated, { useAnimatedReaction } from "react-native-reanimated";
// import { scheduleOnRN } from "react-native-worklets";
// import {
//   parseDateTime,
//   StockData,
//   TechnicalIndicatorData,
// } from "@/helpers/DetailHelpers";

// const AnimatedView = Animated.createAnimatedComponent(View);

// const LineTooltip = () => {
//   const { theme } = useTheme();
//   const { currentIndex, data } = useLineChart();

//   const [point, setPoint] = React.useState<{
//     value: number;
//     time: number;
//   } | null>(null);

//   useAnimatedReaction(
//     () => Math.round(currentIndex.value),
//     (index) => {
//       if (index === -1) {
//         scheduleOnRN(setPoint, null);
//         return;
//       }

//       const item = data?.[index];
//       if (!item) return;

//       scheduleOnRN(setPoint, {
//         value: item.value,
//         time: item.timestamp,
//       });
//     },
//     [data],
//   );

//   if (!point) return null;

//   return (
//     <AnimatedView
//       style={{
//         position: "absolute",
//         top: 0,
//         alignSelf: "center",
//         padding: 8,
//         borderRadius: 8,
//         backgroundColor: theme.background.surface,
//         borderWidth: 1,
//         borderColor: theme.border.default,
//       }}
//     >
//       <Text color={theme.text.primary}>
//         {point.value.toLocaleString("vi-VN")}
//       </Text>
//       <Text color={theme.text.secondary}>
//         {new Date(point.time).toLocaleString("vi-VN")}
//       </Text>
//     </AnimatedView>
//   );
// };

// interface Props {
//   height: number;
//   data: StockData[];
//   technicalIndicatorData: TechnicalIndicatorData[];
//   candleStickMode: boolean;
//   technicalIndicatorMode1: "MA" | "BOLL" | null;
// }

// const PriceLineGraph = ({
//   height,
//   data,
//   technicalIndicatorData,
//   candleStickMode,
//   technicalIndicatorMode1,
// }: Props) => {
//   const { theme } = useTheme();
//   const screenWidth = Dimensions.get("window").width;

//   const HighData = useMemo(() => {
//     return data.map((item) => ({
//       timestamp: parseDateTime(item.TradingDate, item.Time),
//       value: Number(item.High),
//     }));
//   }, [data]);

//   const LowData = useMemo(() => {
//     return data.map((item) => ({
//       timestamp: parseDateTime(item.TradingDate, item.Time),
//       value: Number(item.Low),
//     }));
//   }, [data]);

//   const priceData = useMemo(() => {
//     return data.map((item) => ({
//       timestamp: parseDateTime(item.TradingDate, item.Time),
//       value: Number(item.Close),
//     }));
//   }, [data]);

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

//   const bbMiddleData = useMemo(() => {
//     return data.map((item, index) => ({
//       timestamp: parseDateTime(item.TradingDate, item.Time),
//       value: Number(technicalIndicatorData[index]?.indicators.bb_middle),
//     }));
//   }, [data, technicalIndicatorData]);

//   const bbLowerData = useMemo(() => {
//     return data.map((item, index) => ({
//       timestamp: parseDateTime(item.TradingDate, item.Time),
//       value: Number(technicalIndicatorData[index]?.indicators.bb_lower),
//     }));
//   }, [data, technicalIndicatorData]);

//   const chartMAData = useMemo(() => {
//     return {
//       price: priceData,
//       ma20: ma20Data,
//       ma50: ma50Data,
//       high: HighData,
//       low: LowData,
//     };
//   }, [HighData, LowData, ma20Data, ma50Data, priceData]);

//   const chartBOLLData = useMemo(() => {
//     return {
//       price: priceData,
//       bbUpper: bbUpperData,
//       bbMiddle: bbMiddleData,
//       bbLower: bbLowerData,
//       high: HighData,
//       low: LowData,
//     };
//   }, [priceData, bbUpperData, bbMiddleData, bbLowerData, HighData, LowData]);

//   const chartData = useMemo(() => {
//     return {
//       price: priceData,
//       high: HighData,
//       low: LowData,
//     };
//   }, [HighData, LowData, priceData]);

//   const isDataReady =
//     data.length > 0 && technicalIndicatorData.length === data.length;

//   return isDataReady ? (
//     <View>
//       <LineChart.Provider
//         data={
//           technicalIndicatorMode1 === "MA"
//             ? chartMAData
//             : technicalIndicatorMode1 === "BOLL"
//               ? chartBOLLData
//               : chartData
//         }
//       >
//         <LineChart.Group>
//           {technicalIndicatorMode1 === "MA" ? (
//             <LineChart id="ma20" width={screenWidth} height={height}>
//               <LineChart.Path color={theme.base.warning} width={1} />
//             </LineChart>
//           ) : null}

//           {technicalIndicatorMode1 === "MA" ? (
//             <LineChart id="ma50" width={screenWidth} height={height}>
//               <LineChart.Path color={theme.base.success} width={1} />
//             </LineChart>
//           ) : null}

//           {technicalIndicatorMode1 === "BOLL" ? (
//             <LineChart id="bbUpper" width={screenWidth} height={height}>
//               <LineChart.Path color={theme.base.success} width={1} />
//             </LineChart>
//           ) : null}

//           {technicalIndicatorMode1 === "BOLL" ? (
//             <LineChart id="bbMiddle" width={screenWidth} height={height}>
//               <LineChart.Path color={theme.base.warning} width={1} />
//             </LineChart>
//           ) : null}

//           {technicalIndicatorMode1 === "BOLL" ? (
//             <LineChart id="bbLower" width={screenWidth} height={height}>
//               <LineChart.Path color={theme.base.primary} width={1} />
//             </LineChart>
//           ) : null}

//           {
//             <LineChart id="price" width={screenWidth} height={height}>
//               {/* Line */}
//               {
//                 <LineChart.Path
//                   color={candleStickMode ? "transparent" : theme.base.success}
//                   width={2}
//                 >
//                   {candleStickMode ? null : <LineChart.Gradient />}
//                 </LineChart.Path>
//               }

//               {/* Crosshair */}
//               <LineChart.CursorCrosshair color={theme.base.primary} />

//               {/* Tooltip */}
//               <LineTooltip />
//             </LineChart>
//           }
//         </LineChart.Group>
//       </LineChart.Provider>

//       {technicalIndicatorMode1 === "MA" ? (
//         <View
//           style={{
//             flexDirection: "row",
//             alignItems: "center",
//             position: "absolute",
//           }}
//         >
//           <Text color={theme.base.warning} style={{ marginHorizontal: 12 }}>
//             MA20: {((ma20Data.at(-1)?.value || 0) / 1000).toFixed(2)}
//           </Text>

//           <Text color={theme.base.success} style={{ marginHorizontal: 12 }}>
//             MA50: {((ma50Data.at(-1)?.value || 0) / 1000).toFixed(2)}
//           </Text>
//         </View>
//       ) : null}

//       {technicalIndicatorMode1 === "BOLL" ? (
//         <View
//           style={{
//             flexDirection: "row",
//             alignItems: "center",
//             position: "absolute",
//           }}
//         >
//           <Text color={theme.base.warning} style={{ marginHorizontal: 12 }}>
//             BOLL: {((bbMiddleData.at(-1)?.value || 0) / 1000).toFixed(2)}
//           </Text>

//           <Text color={theme.base.success} style={{ marginHorizontal: 12 }}>
//             UB: {((bbUpperData.at(-1)?.value || 0) / 1000).toFixed(2)}
//           </Text>

//           <Text color={theme.base.primary} style={{ marginHorizontal: 12 }}>
//             LB: {((bbLowerData.at(-1)?.value || 0) / 1000).toFixed(2)}
//           </Text>
//         </View>
//       ) : null}
//     </View>
//   ) : null;
// };

// export default PriceLineGraph;
