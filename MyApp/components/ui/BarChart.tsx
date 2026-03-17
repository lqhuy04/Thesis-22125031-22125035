import React, { useState } from "react";
import { View, Text, StyleSheet, LayoutChangeEvent } from "react-native";
import { CartesianChart, Bar, Line } from "victory-native";
import { Circle, useFont } from "@shopify/react-native-skia";
import { useTheme } from "@/hooks/ThemeContext";

interface DataPoint {
  time: string;
  revenue: number;
  profit: number;
}

interface Props {
  data: DataPoint[];
}

// Padding mặc định của CartesianChart (trục Y label chiếm ~50px bên trái, ~10px bên phải)
const CHART_TOP_INSET = 8;
const CHART_BOTTOM_INSET = 28; // trục X label

function formatShortNumber(value: number): string {
  if (value >= 1_000_000) return `${(value / 1_000_000).toFixed(1)}M`;
  if (value >= 1_000) return `${(value / 1_000).toFixed(0)}K`;
  return `${value}`;
}

const TICK_COUNT = 5;

const RevenueBarChart = ({ data }: Props) => {
  const { theme } = useTheme();
  const font = useFont(require("@/assets/fonts/Roboto-SemiBold.ttf"), 12);

  const [chartHeight, setChartHeight] = useState(300);

  const maxRevenue = Math.max(...data.map((d) => d.revenue));
  const maxProfit = Math.max(...data.map((d) => d.profit));
  const profitScale = maxRevenue / maxProfit;

  const scaledData = data.map((d) => ({
    ...d,
    profitScaled: d.profit * profitScale,
  }));

  // Chiều cao vùng vẽ thực sự (trừ padding trên/dưới của chart)
  const plotHeight = chartHeight - CHART_TOP_INSET - CHART_BOTTOM_INSET;

  // Sinh các tick cho trục Y phải (lợi nhuận)
  const rightTicks = Array.from({ length: TICK_COUNT + 1 }, (_, i) => {
    const ratio = i / TICK_COUNT; // 0 → 1 (bottom → top)
    const value = maxProfit * ratio;
    // pixel tính từ top của View chart
    const y = CHART_TOP_INSET + plotHeight * (1 - ratio);
    return { value, y };
  });

  return (
    <View style={styles.container}>
      {/* Chart container – position relative để overlay trục phải */}
      <View
        style={styles.chartOuter}
        onLayout={(e: LayoutChangeEvent) =>
          setChartHeight(e.nativeEvent.layout.height)
        }
      >
        {/* Victory chart – bớt padding phải để nhường chỗ cho label */}
        <CartesianChart
          data={scaledData}
          xKey="time"
          yKeys={["revenue", "profitScaled"]}
          domain={{ y: [0, maxRevenue * 1.15] }}
          domainPadding={{ left: 20, right: 20 }}
          padding={{ right: 24 }} // ← nhường 48px bên phải cho label lợi nhuận
          axisOptions={{
            font,
            formatXLabel: (v) => v,
            formatYLabel: (v) => formatShortNumber(v),
            labelColor: theme.text.primary,
            lineColor: {
              grid: { x: "transparent", y: theme.border.default },
              frame: "transparent",
            },
            tickCount: { x: data.length, y: TICK_COUNT },
          }}
        >
          {({ points, chartBounds }) => (
            <>
              <Bar
                points={points.revenue}
                chartBounds={chartBounds}
                color={theme.base.primary}
                barWidth={28}
                animate={{ type: "spring" }}
                roundedCorners={{ topLeft: 4, topRight: 4 }}
              />
              <Line
                points={points.profitScaled}
                color={theme.text.primary}
                strokeWidth={2.5}
                animate={{ type: "spring" }}
              >
                {points.profitScaled.map((point, i) =>
                  point.x != null && point.y != null ? (
                    <Circle
                      key={i}
                      cx={point.x}
                      cy={point.y}
                      r={4}
                      color={theme.text.primary}
                      style="fill"
                    />
                  ) : null,
                )}
              </Line>
            </>
          )}
        </CartesianChart>

        {/* Overlay trục Y phải – absolute, căn theo chartHeight */}
        <View style={StyleSheet.absoluteFill} pointerEvents="none">
          {rightTicks.map(({ value, y }, i) => (
            <Text
              key={i}
              style={[
                styles.rightLabel,
                {
                  color: theme.text.primary,
                  top: y - 6, // -6 để căn giữa dòng text với tick
                },
              ]}
            >
              {formatShortNumber(value)}
            </Text>
          ))}
        </View>
      </View>

      {/* Legend */}
      <View style={styles.legend}>
        <View style={styles.legendItem}>
          <View
            style={[styles.legendBox, { backgroundColor: theme.base.primary }]}
          />
          <Text style={[styles.legendText, { color: theme.text.primary }]}>
            Doanh thu
          </Text>
        </View>
        <View style={styles.legendItem}>
          <View
            style={[styles.legendLine, { backgroundColor: theme.text.primary }]}
          />
          <Text style={[styles.legendText, { color: theme.text.primary }]}>
            Lợi nhuận
          </Text>
        </View>
      </View>
    </View>
  );
};

const styles = StyleSheet.create({
  container: {
    paddingVertical: 8,
  },
  legend: {
    flexDirection: "row",
    alignItems: "center",
    justifyContent: "center",
    gap: 16,
    paddingHorizontal: 8,
    marginVertical: 8,
  },
  legendItem: {
    flexDirection: "row",
    alignItems: "center",
    gap: 6,
  },
  legendBox: {
    width: 12,
    height: 12,
    borderRadius: 2,
  },
  legendLine: {
    width: 20,
    height: 3,
    borderRadius: 2,
  },
  legendText: {
    fontSize: 12,
  },
  chartOuter: {
    height: 300,
    position: "relative",
  },
  rightLabel: {
    position: "absolute",
    right: 0,
    width: 44,
    fontSize: 12,
    fontFamily: "Roboto-SemiBold",
    textAlign: "right",
  },
});

export default RevenueBarChart;
