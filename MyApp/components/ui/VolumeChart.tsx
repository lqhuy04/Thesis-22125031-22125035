import React, { useMemo } from "react";
import { View, StyleSheet } from "react-native";
import { CartesianChart, Bar } from "victory-native";
import { useTheme } from "@/hooks/ThemeContext";
import { Text } from "./Text";

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
      <View
        style={{
          flexDirection: "row",
          alignItems: "center",
        }}
      >
        <Text color={theme.text.primary} style={{ marginHorizontal: 12 }}>
          VOL: {((data.at(-1)?.volume || 0) / 1000).toFixed(2)}K
        </Text>
      </View>
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
        <View style={{ height: 60, marginTop: -60 }}>
          <CartesianChart
            data={chartDataNegative}
            xKey="time"
            yKeys={["volume"]}
            domain={{ y: [0, maxVolume] }}
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
                color={theme.base.error}
                animate={{ type: "spring" }}
              />
            )}
          </CartesianChart>
        </View>
      </View>
    </View>
  );
};

const styles = StyleSheet.create({
  container: {
    height: 60,
  },
});

export default VolumeBarChart;
