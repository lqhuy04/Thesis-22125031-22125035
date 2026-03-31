import React, { useMemo } from "react";
import { View, Dimensions } from "react-native";
import { useTheme } from "@/hooks/ThemeContext";
import { LineChart } from "react-native-wagmi-charts";
import { parseDateTime, TechnicalIndicatorData } from "@/helpers/DetailHelpers";

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
      </View>
    )
  );
};

export default KDJChart;
