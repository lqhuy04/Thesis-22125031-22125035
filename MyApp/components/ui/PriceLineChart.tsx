import React, { useMemo } from "react";
import { StockData } from "@/helpers/DetailHelpers";
import { CartesianChart, Line, Area } from "victory-native";
import { View } from "react-native";
import { useTheme } from "@/hooks/ThemeContext";
import { LinearGradient, vec } from "@shopify/react-native-skia";

interface Props {
  data: StockData[];
}

const PriceLineGraph = ({ data }: Props) => {
  const { theme } = useTheme();

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

  return (
    <View style={{ height: 278 }}>
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
      >
        {({ points, chartBounds }) => (
          <>
            {/* Area with gradient fill */}
            <Area points={points.y} y0={chartBounds.bottom}>
              <LinearGradient
                start={vec(0, 0)}
                end={vec(0, chartBounds.bottom)}
                colors={[theme.base.primary + "30"]}
              />
            </Area>

            {/* Line on top of gradient */}
            <Line
              points={points.y}
              color={"#4E31B6"}
              strokeWidth={3}
              animate={{ type: "timing", duration: 300 }}
              curveType="natural"
            />
          </>
        )}
      </CartesianChart>
    </View>
  );
};

export default PriceLineGraph;
