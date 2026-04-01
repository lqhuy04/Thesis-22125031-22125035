import React, { useMemo } from "react";
import { View, Dimensions } from "react-native";
import { useTheme } from "@/hooks/ThemeContext";
import { LineChart, useLineChart } from "react-native-wagmi-charts";
import { Text } from "./Text";
import Animated, { useAnimatedReaction } from "react-native-reanimated";
import { scheduleOnRN } from "react-native-worklets";
import {
  parseDateTime,
  StockData,
  TechnicalIndicatorData,
} from "@/helpers/DetailHelpers";

const AnimatedView = Animated.createAnimatedComponent(View);

const LineTooltip = () => {
  const { theme } = useTheme();
  const { currentIndex, data } = useLineChart();

  const [point, setPoint] = React.useState<{
    value: number;
    time: number;
  } | null>(null);

  useAnimatedReaction(
    () => Math.round(currentIndex.value),
    (index) => {
      if (index === -1) {
        scheduleOnRN(setPoint, null);
        return;
      }

      const item = data?.[index];
      if (!item) return;

      scheduleOnRN(setPoint, {
        value: item.value,
        time: item.timestamp,
      });
    },
    [data],
  );

  if (!point) return null;

  return (
    <AnimatedView
      style={{
        position: "absolute",
        top: 0,
        alignSelf: "center",
        padding: 8,
        borderRadius: 8,
        backgroundColor: theme.background.surface,
        borderWidth: 1,
        borderColor: theme.border.default,
      }}
    >
      <Text color={theme.text.primary}>
        {point.value.toLocaleString("vi-VN")}
      </Text>
      <Text color={theme.text.secondary}>
        {new Date(point.time).toLocaleString("vi-VN")}
      </Text>
    </AnimatedView>
  );
};

interface Props {
  data: StockData[];
  technicalIndicatorData: TechnicalIndicatorData[];
  showPriceLine: boolean;
  technicalIndicatorMode1: "MA" | "BOLL" | null;
}

const PriceLineChart = ({
  data,
  technicalIndicatorData,
  showPriceLine,
  technicalIndicatorMode1,
}: Props) => {
  const { theme } = useTheme();
  const screenWidth = Dimensions.get("window").width;

  const priceData = useMemo(() => {
    return data.map((item) => ({
      timestamp: parseDateTime(item.TradingDate, item.Time),
      value: Number(item.Close),
    }));
  }, [data]);

  const ma20Data = useMemo(() => {
    return data.map((item, index) => ({
      timestamp: parseDateTime(item.TradingDate, item.Time),
      value: Number(technicalIndicatorData[index]?.indicators.sma_20),
    }));
  }, [data, technicalIndicatorData]);

  const ma50Data = useMemo(() => {
    return data.map((item, index) => ({
      timestamp: parseDateTime(item.TradingDate, item.Time),
      value: Number(technicalIndicatorData[index]?.indicators.sma_50),
    }));
  }, [data, technicalIndicatorData]);

  const bbUpperData = useMemo(() => {
    return data.map((item, index) => ({
      timestamp: parseDateTime(item.TradingDate, item.Time),
      value: Number(technicalIndicatorData[index]?.indicators.bb_upper),
    }));
  }, [data, technicalIndicatorData]);

  const bbMiddleData = useMemo(() => {
    return data.map((item, index) => ({
      timestamp: parseDateTime(item.TradingDate, item.Time),
      value: Number(technicalIndicatorData[index]?.indicators.bb_middle),
    }));
  }, [data, technicalIndicatorData]);

  const bbLowerData = useMemo(() => {
    return data.map((item, index) => ({
      timestamp: parseDateTime(item.TradingDate, item.Time),
      value: Number(technicalIndicatorData[index]?.indicators.bb_lower),
    }));
  }, [data, technicalIndicatorData]);

  const chartData = useMemo(() => {
    if (technicalIndicatorMode1 === "MA") {
      return {
        price: priceData,
        ma20: ma20Data,
        ma50: ma50Data,
      };
    } else if (technicalIndicatorMode1 === "BOLL") {
      return {
        price: priceData,
        bbUpper: bbUpperData,
        bbMiddle: bbMiddleData,
        bbLower: bbLowerData,
      };
    } else {
      return {
        price: priceData,
      };
    }
  }, [
    technicalIndicatorMode1,
    priceData,
    ma20Data,
    ma50Data,
    bbUpperData,
    bbMiddleData,
    bbLowerData,
  ]);

  return (
    data.length !== 0 && (
      <View>
        <LineChart.Provider data={chartData}>
          <LineChart.Group>
            {showPriceLine ? (
              <LineChart id="price" width={screenWidth} height={300}>
                {/* Line */}
                <LineChart.Path color={theme.base.primary} width={2}>
                  <LineChart.Gradient />
                </LineChart.Path>

                {/* Crosshair */}
                <LineChart.CursorCrosshair color={theme.base.primary} />

                {/* Tooltip */}
                <LineTooltip />
              </LineChart>
            ) : null}

            <LineChart id="ma20" width={screenWidth} height={300}>
              <LineChart.Path color={theme.base.warning} width={1} />
            </LineChart>

            <LineChart id="ma50" width={screenWidth} height={300}>
              <LineChart.Path color={theme.base.success} width={1} />
            </LineChart>

            <LineChart id="bbUpper" width={screenWidth} height={300}>
              <LineChart.Path color={"red"} width={1} />
            </LineChart>

            <LineChart id="bbMiddle" width={screenWidth} height={300}>
              <LineChart.Path color={"red"} width={1} />
            </LineChart>

            <LineChart id="bbLower" width={screenWidth} height={300}>
              <LineChart.Path color={"red"} width={1} />
            </LineChart>
          </LineChart.Group>
        </LineChart.Provider>
      </View>
    )
  );
};

export default PriceLineChart;
