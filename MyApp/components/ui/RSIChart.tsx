import React, { useMemo } from "react";
import { View, Dimensions } from "react-native";
import { useTheme } from "@/hooks/ThemeContext";
import { LineChart } from "react-native-wagmi-charts";
import { parseDateTime, TechnicalIndicatorData } from "@/helpers/DetailHelpers";
import { Text } from "./Text";

interface Props {
  technicalIndicatorData: TechnicalIndicatorData[];
}

const RSIChart = ({ technicalIndicatorData }: Props) => {
  const { theme } = useTheme();
  const screenWidth = Dimensions.get("window").width;

  const chartData = useMemo(() => {
    return technicalIndicatorData.map((item, index) => ({
      timestamp: parseDateTime(item.date, item.time),
      value: Number(technicalIndicatorData[index]?.indicators.rsi_14),
    }));
  }, [technicalIndicatorData]);

  return (
    technicalIndicatorData.length !== 0 && (
      <View>
        <LineChart.Provider data={chartData}>
          <LineChart width={screenWidth} height={100}>
            {/* Line */}
            <LineChart.Path color={theme.base.warning} width={2} />
          </LineChart>
        </LineChart.Provider>

        <View
          style={{
            flexDirection: "row",
            alignItems: "center",
            position: "absolute",
          }}
        >
          <Text color={theme.base.warning} style={{ marginHorizontal: 12 }}>
            {`RSI(14): ${(technicalIndicatorData.at(-1)?.indicators?.rsi_14 || 0).toFixed(2)}`}
          </Text>
        </View>
      </View>
    )
  );
};

export default RSIChart;
