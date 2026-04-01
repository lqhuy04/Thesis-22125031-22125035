import React, { useMemo } from "react";
import { View, Dimensions } from "react-native";
import { CartesianChart, Bar } from "victory-native";
import { useTheme } from "@/hooks/ThemeContext";
import { Text } from "./Text";
import { parseDateTime, TechnicalIndicatorData } from "@/helpers/DetailHelpers";
import { LineChart } from "react-native-wagmi-charts";

interface Props {
  data: TechnicalIndicatorData[];
}

const MACDChart = ({ data }: Props) => {
  const { theme } = useTheme();
  const screenWidth = Dimensions.get("window").width;

  const maxVolume = useMemo(() => {
    return Math.max(...data.map((d) => d?.indicators?.macd));
  }, [data]);

  const chartDataPositive = useMemo(() => {
    return data.map((item) => ({
      date: item.date,
      time: item.time,
      macd: item.indicators.macd > 0 ? item.indicators.macd : 0,
    }));
  }, [data]);

  const chartDataNegative = useMemo(() => {
    return data.map((item) => ({
      date: item.date,
      time: item.time,
      macd: item.indicators.macd <= 0 ? -item.indicators.macd : 0,
    }));
  }, [data]);

  const DIFChartData = useMemo(() => {
    return data.map((item, index) => ({
      timestamp: parseDateTime(item.date, item.time),
      value: item?.indicators?.DIF,
    }));
  }, [data]);

  const DEAChartData = useMemo(() => {
    return data.map((item, index) => ({
      timestamp: parseDateTime(item.date, item.time),
      value: item?.indicators?.DEA,
    }));
  }, [data]);

  const DIF_DEA_ChartData = useMemo(() => {
    return {
      DIF: DIFChartData,
      DEA: DEAChartData,
    };
  }, [DEAChartData, DIFChartData]);

  return (
    <View style={{ marginBottom: -48 }}>
      <View
        style={{
          flexDirection: "row",
          alignItems: "center",
        }}
      >
        <Text color={theme.base.primary} style={{ marginHorizontal: 12 }}>
          MACD: {((data.at(-1)?.indicators?.macd || 0) / 1000).toFixed(2)}
        </Text>

        <Text color={theme.base.warning} style={{ marginHorizontal: 12 }}>
          DIF: {((data.at(-1)?.indicators?.DIF || 0) / 1000).toFixed(2)}
        </Text>

        <Text color={theme.base.success} style={{ marginHorizontal: 12 }}>
          DEA: {((data.at(-1)?.indicators?.DEA || 0) / 1000).toFixed(2)}
        </Text>
      </View>

      <View>
        <View style={{ height: 30 }}>
          <CartesianChart
            data={chartDataPositive}
            xKey="time"
            yKeys={["macd"]}
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
                points={points.macd}
                chartBounds={chartBounds}
                color={theme.base.success}
                animate={{ type: "spring" }}
              />
            )}
          </CartesianChart>
        </View>
        <View
          style={{
            height: 30,
            transform: [{ scaleY: -1 }],
            marginTop: -16,
          }}
        >
          <CartesianChart
            data={chartDataNegative}
            xKey="time"
            yKeys={["macd"]}
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
                points={points.macd}
                chartBounds={chartBounds}
                color={theme.base.error}
                animate={{ type: "spring" }}
              />
            )}
          </CartesianChart>
        </View>
        <View style={{ marginTop: -74 }}>
          <LineChart.Provider data={DIF_DEA_ChartData}>
            <LineChart.Group>
              <LineChart id="DIF" width={screenWidth} height={128}>
                <LineChart.Path color={theme.base.warning} width={1} />
              </LineChart>
              <LineChart id="DEA" width={screenWidth} height={128}>
                <LineChart.Path color={theme.base.success} width={1} />
              </LineChart>
            </LineChart.Group>
          </LineChart.Provider>
        </View>
      </View>
    </View>
  );
};

export default MACDChart;
