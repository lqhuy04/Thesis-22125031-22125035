import React, { useMemo } from "react";
import { View, StyleSheet } from "react-native";
import { CartesianChart, Bar } from "victory-native";
import { useTheme } from "@/hooks/ThemeContext";

interface DataPoint {
  date: string;
  time: string;
  volume: number;
  positive: boolean;
}

interface Props {
  data: DataPoint[];
}

const VolumeBarChart = ({ data }: Props) => {
  const { theme } = useTheme();

  const maxVolume = useMemo(() => {
    return Math.max(...data.map((d) => d.volume));
  }, [data]);

  const chartDataPositive = useMemo(() => {
    return data.map((item) => ({
      date: item.date,
      time: item.time,
      volume: item.positive ? item.volume : 0,
    }));
  }, [data]);

  const chartDataNegative = useMemo(() => {
    return data.map((item) => ({
      date: item.date,
      time: item.time,
      volume: item.positive ? 0 : item.volume,
    }));
  }, [data]);

  return (
    <View>
      <View style={styles.container}>
        <CartesianChart
          data={chartDataPositive}
          xKey="time"
          yKeys={["volume"]}
          domainPadding={{ left: 12, right: 12 }}
          axisOptions={{
            lineColor: "transparent",
            lineWidth: 0,
          }}
          frame={{
            lineWidth: 0,
            lineColor: "transparent",
          }}
        >
          {({ points, chartBounds }) => (
            <Bar
              points={points.volume}
              chartBounds={chartBounds}
              color={theme.base.success}
              animate={{ type: "spring" }}
            />
          )}
        </CartesianChart>
      </View>
      <View style={{ height: 100, marginTop: -100 }}>
        <CartesianChart
          data={chartDataNegative}
          xKey="time"
          yKeys={["volume"]}
          domain={{ y: [0, maxVolume] }}
          domainPadding={{ left: 12, right: 12 }}
          axisOptions={{
            lineColor: {
              grid: { x: "transparent", y: "transparent" },
              frame: "transparent",
            },
          }}
        >
          {({ points, chartBounds }) => (
            <Bar
              points={points.volume}
              chartBounds={chartBounds}
              color={theme.base.error}
              animate={{ type: "spring" }}
            />
          )}
        </CartesianChart>
      </View>
    </View>
  );
};

const styles = StyleSheet.create({
  container: {
    height: 100,
  },
});

export default VolumeBarChart;
