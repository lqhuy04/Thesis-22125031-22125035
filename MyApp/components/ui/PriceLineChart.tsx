import React, { useMemo } from "react";
import { StockData } from "@/helpers/DetailHelpers";
import { CartesianChart, Line, Area, useChartPressState } from "victory-native";
import { View, Dimensions } from "react-native";
import { useTheme } from "@/hooks/ThemeContext";
import {
  Rect,
  Line as SkiaLine,
  Circle,
  RoundedRect,
  Text as SkiaText,
  useFont,
  vec,
  LinearGradient,
  DashPathEffect,
} from "@shopify/react-native-skia";
import { useDerivedValue } from "react-native-reanimated";

interface Props {
  data: StockData[];
}

const PriceLineGraph = ({ data }: Props) => {
  const screenWidth = Dimensions.get("window").width;
  const chartData = useMemo(() => {
    return data.map((item, index) => {
      return {
        x: index,
        y: Number(item?.Value) / 1000,
        date: item?.TradingDate,
        time: item?.Time,
      };
    });
  }, [data]);
  const { theme } = useTheme();
  const { state, isActive } = useChartPressState({ x: 0, y: { y: 0 } });

  //-----------------------------------------------------------------
  const fontPriceSize = 11;

  const fontPrice = useFont(
    require("@/assets/fonts/Roboto-SemiBold.ttf"),
    fontPriceSize,
  );

  const tooltipText = useDerivedValue(
    () => `${state.y.y.value.value * 1000} VND`,
  );

  const textPrice = tooltipText; // string hoặc SkiaValue
  const textPriceWidth = fontPrice?.measureText(textPrice.value).width ?? 0;

  const fontDateSize = 10;

  //-----------------------------------------------------------------
  const times = useMemo(() => chartData.map((d) => d.time), [chartData]);

  const dates = useMemo(() => chartData.map((d) => d.date), [chartData]);
  const fontDate = useFont(
    require("@/assets/fonts/Roboto-Medium.ttf"),
    fontDateSize,
  );

  const tooltipDateText = useDerivedValue(() => {
    const index = Math.round(state.x.value.value);
    if (index < 0 || index >= dates.length) return "";
    return `${dates[index]} ${times[index]}`;
  });

  const textDate = tooltipDateText;
  const textDateWidth = fontDate?.measureText(textDate.value).width ?? 0;

  //-----------------------------------------------------------------
  const lineP1 = useDerivedValue(() =>
    vec(state.x.position.value, state.y.y.position.value),
  );
  const lineP2 = useDerivedValue(() => vec(state.x.position.value, 360));

  //-----------------------------------------------------------------
  const dashedLineP1 = useDerivedValue(() => vec(0, state.y.y.position.value));
  const dashedLineP2 = useDerivedValue(() =>
    vec(screenWidth, state.y.y.position.value),
  );

  //-----------------------------------------------------------------
  const linearGradientX = useDerivedValue(() => state.x.position.value - 12);
  const linearGradientY = useDerivedValue(() => state.y.y.position.value);

  //-----------------------------------------------------------------
  const horizontalLines = 4;

  const xTicks = 8;

  return (
    data.length !== 0 && (
      <View style={{ height: 360 }}>
        <CartesianChart
          data={chartData}
          xKey="x"
          yKeys={["y"]}
          axisOptions={{
            lineColor: "transparent",
          }}
          frame={{
            lineWidth: 0,
            lineColor: "transparent",
          }}
          chartPressState={state}
          domainPadding={{ top: 60 }}
        >
          {({ points, chartBounds, yScale, xScale }) => {
            return (
              <>
                {/* Area */}
                <Area
                  points={points.y}
                  y0={chartBounds.bottom}
                  color={theme.background.bg}
                  curveType="natural"
                >
                  <LinearGradient
                    start={vec(chartBounds.bottom, chartBounds.top)}
                    end={vec(chartBounds.bottom, chartBounds.bottom)}
                    colors={[theme.background.bg, theme.base.primary + "16"]}
                  />
                </Area>

                {/* Line */}
                <Line
                  points={points.y}
                  color={theme.base.primaryHover}
                  strokeWidth={2}
                  animate={{ type: "timing", duration: 300 }}
                  curveType="natural"
                />

                {/* Interactive circle point */}
                {isActive && (
                  <>
                    <SkiaLine
                      p1={dashedLineP1}
                      p2={dashedLineP2}
                      color={theme.base.primary}
                      strokeWidth={1}
                    >
                      <DashPathEffect intervals={[6, 4]} />
                    </SkiaLine>
                    {/* Linear Gradient*/}
                    <Rect
                      x={linearGradientX}
                      y={linearGradientY}
                      width={24}
                      height={360}
                    >
                      <LinearGradient
                        start={vec(0, chartBounds.top)}
                        end={vec(0, chartBounds.bottom)}
                        colors={[
                          theme.base.primary + "00",
                          theme.base.primary + "39",
                        ]}
                      />
                    </Rect>
                    {/* Vertical Line */}
                    <SkiaLine
                      p1={lineP1}
                      p2={lineP2}
                      color={theme.background.bg}
                      strokeWidth={2}
                    />
                    {/* Outer glow circle */}
                    <Circle
                      cx={state.x.position}
                      cy={state.y.y.position}
                      r={12}
                      color={theme.base.primary + "30"}
                    />
                    {/* Center circle */}
                    <Circle
                      cx={state.x.position}
                      cy={state.y.y.position}
                      r={4}
                      color={theme.text.onPrimary}
                    />

                    {/* Tooltip */}
                    <RoundedRect
                      x={chartBounds.left - 4 + screenWidth / 2 - 127 / 2}
                      y={0}
                      width={127}
                      height={42}
                      r={4}
                      color={theme.base.primary}
                    />
                    <SkiaText
                      x={
                        chartBounds.left -
                        4 +
                        screenWidth / 2 -
                        127 / 2 +
                        (127 - textPriceWidth) / 2
                      }
                      y={0 + 42 / 2 + (fontPrice?.getSize() ?? 0) / 2 - 8}
                      text={textPrice}
                      font={fontPrice}
                      color={theme.text.onPrimary}
                    />
                    <SkiaText
                      x={
                        chartBounds.left -
                        4 +
                        screenWidth / 2 -
                        127 / 2 +
                        (127 - textDateWidth) / 2
                      }
                      y={0 + 42 / 2 + (fontDate?.getSize() ?? 0) / 2 + 6}
                      text={textDate}
                      font={fontDate}
                      color={theme.text.onPrimary}
                    />
                  </>
                )}

                {Array.from({ length: horizontalLines - 1 }).map((_, i) => {
                  const y =
                    chartBounds.top +
                    71 +
                    ((chartBounds.bottom - 71) * i) / (horizontalLines - 1) +
                    4;

                  const domain = yScale.domain(); // [minY, maxY]

                  const value =
                    domain[0] +
                    ((domain[1] - domain[0]) * i) / (horizontalLines - 1);

                  const label = `${value.toFixed(1).toLocaleString()}K`;

                  return (
                    <SkiaText
                      key={i}
                      x={chartBounds.left + 10}
                      y={y}
                      text={label}
                      font={fontPrice}
                      color={theme.text.primary}
                    />
                  );
                })}

                {Array.from({ length: horizontalLines }).map((_, i) => {
                  const y =
                    chartBounds.top +
                    71 +
                    ((chartBounds.bottom - 71) * i) / (horizontalLines - 1);

                  return (
                    <SkiaLine
                      key={i}
                      p1={{
                        x: chartBounds.left + 54,
                        y,
                      }}
                      p2={{
                        x: chartBounds.right,
                        y,
                      }}
                      color={theme.border.default}
                      strokeWidth={1}
                    >
                      <DashPathEffect intervals={[4, 4]} />
                    </SkiaLine>
                  );
                })}

                {Array.from({ length: xTicks - 1 }).map((_, i) => {
                  const domain = xScale.domain(); // [0, data.length - 1]
                  const value =
                    3 + ((domain[1] - domain[0]) * i) / (xTicks - 1);

                  const index = Math.round(value);
                  if (index < 0 || index >= chartData.length) return null;

                  const x = xScale(value);
                  const label = chartData[index].time.substring(0, 5);

                  const textWidth = fontDate?.measureText(label).width ?? 0;
                  return (
                    <SkiaText
                      key={i}
                      x={x - textWidth / 2}
                      y={chartBounds.top + 340}
                      text={label}
                      font={fontPrice}
                      color={theme.text.primary}
                    />
                  );
                })}
              </>
            );
          }}
        </CartesianChart>
      </View>
    )
  );
};

export default PriceLineGraph;
