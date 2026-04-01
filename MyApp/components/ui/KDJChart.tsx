import React, { useMemo } from "react";
import { View, Dimensions } from "react-native";
import { useTheme } from "@/hooks/ThemeContext";
import { LineChart } from "react-native-wagmi-charts";
import { parseDateTime, TechnicalIndicatorData } from "@/helpers/DetailHelpers";
import { Text } from "./Text";

interface Props {
  technicalIndicatorData: TechnicalIndicatorData[];
}

const KDJChart = ({ technicalIndicatorData }: Props) => {
  const { theme } = useTheme();
  const screenWidth = Dimensions.get("window").width;

  const stochKData = useMemo(() => {
    return technicalIndicatorData.map((item, index) => ({
      timestamp: parseDateTime(item.date, item.time),
      value: Number(technicalIndicatorData[index]?.indicators.stoch_k),
    }));
  }, [technicalIndicatorData]);

  const stochDData = useMemo(() => {
    return technicalIndicatorData.map((item, index) => ({
      timestamp: parseDateTime(item.date, item.time),
      value: Number(technicalIndicatorData[index]?.indicators.stoch_d),
    }));
  }, [technicalIndicatorData]);

  const stochJData = useMemo(() => {
    return technicalIndicatorData.map((item, index) => ({
      timestamp: parseDateTime(item.date, item.time),
      value: Number(technicalIndicatorData[index]?.indicators.stoch_j),
    }));
  }, [technicalIndicatorData]);

  const chartData = useMemo(() => {
    return {
      stochK: stochKData,
      stochD: stochDData,
      stochJ: stochJData,
    };
  }, [stochKData, stochDData, stochJData]);

  return (
    technicalIndicatorData.length !== 0 && (
      <View>
        <LineChart.Provider data={chartData}>
          <LineChart.Group>
            <LineChart id="stochK" width={screenWidth} height={100}>
              <LineChart.Path color={theme.base.warning} width={1} />
            </LineChart>

            <LineChart id="stochD" width={screenWidth} height={100}>
              <LineChart.Path color={theme.base.success} width={1} />
            </LineChart>

            <LineChart id="stochJ" width={screenWidth} height={100}>
              <LineChart.Path color={theme.base.primary} width={1} />
            </LineChart>
          </LineChart.Group>
        </LineChart.Provider>

        <View
          style={{
            flexDirection: "row",
            alignItems: "center",
            position: "absolute",
          }}
        >
          <Text color={theme.base.warning} style={{ marginHorizontal: 12 }}>
            {`K: ${(technicalIndicatorData.at(-1)?.indicators?.stoch_k || 0).toFixed(2)}`}
          </Text>

          <Text color={theme.base.success} style={{ marginHorizontal: 12 }}>
            {`D: ${(technicalIndicatorData.at(-1)?.indicators?.stoch_d || 0).toFixed(2)}`}
          </Text>

          <Text color={theme.base.primary} style={{ marginHorizontal: 12 }}>
            {`J: ${(technicalIndicatorData.at(-1)?.indicators?.stoch_j || 0).toFixed(2)}`}
          </Text>
        </View>
      </View>
    )
  );
};

export default KDJChart;
