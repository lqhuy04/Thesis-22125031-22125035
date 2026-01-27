import { StockData } from "@/helpers/DetailHelpers";
import React, { useMemo, useState } from "react";
import { CartesianChart, Line, useChartPressState } from "victory-native";
import { View, Text, StyleSheet } from "react-native";
import { useTheme } from "@/hooks/ThemeContext";
import { Circle, useFont } from "@shopify/react-native-skia";

interface Props {
  data: StockData[];
}

const PriceLineGraph = ({ data }: Props) => {
  const { theme } = useTheme();
  const { state, isActive } = useChartPressState({ x: 0, y: { y: 0 } });

  const chartData = useMemo(() => {
    return data.map((item, index) => {
      return {
        x: index,
        y: Number(item?.Value) / 1000,
        high: Number(item?.High) / 1000,
        low: Number(item?.Low) / 1000,
        date: item?.TradingDate,
        time: item?.Time,
      };
    });
  }, [data]);

  // Get the active data point
  const activeDataPoint = useMemo(() => {
    if (!isActive || !state.x.value) return null;
    const index = Math.round(state.x.value.value);
    return chartData[index] || null;
  }, [isActive, state.x.value, chartData]);

  return (
    <View style={{ height: 278 }}>
      <CartesianChart
        data={chartData}
        xKey="x"
        yKeys={["y"]}
        chartPressState={state}
        axisOptions={{
          lineColor: "transparent",
        }}
        frame={{
          lineWidth: 0,
          lineColor: "transparent",
        }}
      >
        {({ points, chartBounds }) => (
          <>
            <Line
              points={points.y}
              color={theme.base.primary}
              strokeWidth={3}
              animate={{ type: "timing", duration: 300 }}
            />
            {/* Tooltip indicator */}
            {isActive && state.x.position.value && state.y.y.position.value && (
              <Circle
                cx={state.x.position.value}
                cy={state.y.y.position.value}
                r={8}
                color={theme.base.primary}
                opacity={0.8}
              />
            )}
          </>
        )}
      </CartesianChart>

      {/* Tooltip */}
      {isActive && activeDataPoint && (
        <View style={styles.tooltipContainer}>
          <View style={[styles.tooltip, { backgroundColor: theme.base.primary }]}>
            <Text style={styles.tooltipText}>
              Price: ${(activeDataPoint.y * 1000).toFixed(2)}
            </Text>
            <Text style={styles.tooltipText}>
              High: ${(activeDataPoint.high * 1000).toFixed(2)}
            </Text>
            <Text style={styles.tooltipText}>
              Low: ${(activeDataPoint.low * 1000).toFixed(2)}
            </Text>
            <Text style={styles.tooltipText}>
              {activeDataPoint.date} {activeDataPoint.time}
            </Text>
          </View>
        </View>
      )}
    </View>
  );
};

const styles = StyleSheet.create({
  tooltipContainer: {
    position: "absolute",
    top: 10,
    left: 10,
    zIndex: 10,
  },
  tooltip: {
    padding: 12,
    borderRadius: 8,
    shadowColor: "#000",
    shadowOffset: { width: 0, height: 2 },
    shadowOpacity: 0.25,
    shadowRadius: 3.84,
    elevation: 5,
  },
  tooltipText: {
    color: "#fff",
    fontSize: 12,
    fontWeight: "600",
    marginBottom: 4,
  },
  statsContainer: {
    flexDirection: "row",
    justifyContent: "space-around",
    marginTop: 12,
    paddingHorizontal: 16,
  },
  statBox: {
    alignItems: "center",
  },
  statLabel: {
    fontSize: 12,
    fontWeight: "500",
    marginBottom: 4,
  },
  statValue: {
    fontSize: 16,
    fontWeight: "700",
  },
});

export default PriceLineGraph;