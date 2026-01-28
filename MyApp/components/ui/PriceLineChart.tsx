import React, { useEffect, useMemo, useState } from "react";
import { StockData } from "@/helpers/DetailHelpers";
import { CartesianChart, Line, Area, useChartPressState } from "victory-native";
import { View } from "react-native";
import { useTheme } from "@/hooks/ThemeContext";
import { Circle } from "@shopify/react-native-skia";
import { Text } from "./Text";


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
        date: item?.TradingDate,
        time: item?.Time,
      };
    });
  }, [data]);


  return (
    <View style={{ height: 278, marginLeft: -4 }}>
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
        chartPressState={state} // ← Add this prop
      >
        {({ points, chartBounds }) => (
          <>
            {/* Area with gradient fill */}
            <Area 
              points={points.y} 
              y0={chartBounds.bottom}
              color={theme.base.primary + "30"}
            />

            {/* Line on top of gradient */}
            <Line
              points={points.y}
              color={"#4E31B6"}
              strokeWidth={3}
              animate={{ type: "timing", duration: 300 }}
              curveType="natural"
            />

            {/* Interactive circle point */}
            {isActive && (
              <>
                {/* Outer glow circle */}
                <Circle
                  cx={state.x.position}
                  cy={state.y.y.position}
                  r={12}
                  color={theme.base.primary + "30"}
                />
                {/* Center circle */}
                <Circle
                  cx={state.x.position}
                  cy={state.y.y.position}
                  r={4}
                  color={theme.text.onPrimary}
                />
              </>
            )}
          </>
        )}
      </CartesianChart>

      {isActive &&  
        <View style={{
          backgroundColor: theme.base.primary, 
          borderRadius: 4, 
          paddingVertical: 4, 
          paddingHorizontal: 8,       
          alignSelf: 'center', 
          position: 'absolute', 
          top: 29,
        }}>
          <Text 
            typography="titleSmall" 
            color={theme.text.onPrimary}
          >
            VND {(state.y.y.value.value * 1000).toFixed(2)}
          </Text>
        </View>
      }
    </View>
  );
};

export default PriceLineGraph;