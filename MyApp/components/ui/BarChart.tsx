import React from "react";
import { View } from "react-native";
import { CartesianChart, Bar } from "victory-native";
import { useFont } from "@shopify/react-native-skia";
import { useTheme } from "@/hooks/ThemeContext";

interface Props {
  data: {
    time: string;
    value: number;
  }[];
}

const BarChart = ({ data }: Props) => {
  const { theme } = useTheme();
  // Nếu bạn có font file, thay đường dẫn tương ứng
  // const font = useFont(require("@/assets/fonts/YourFont.ttf"), 12);
  const fontPriceSize = 11;

  const font = useFont(
    require("@/assets/fonts/Roboto-SemiBold.ttf"),
    fontPriceSize,
  );

  return (
    <View style={{ height: 300 }}>
      <CartesianChart
        data={data}
        xKey="time"
        yKeys={["value"]}
        domainPadding={{ left: 20, right: 20 }}
        axisOptions={{
          font,
          // Label trục X
          formatXLabel: (value) => value,
          // Label trục Y
          formatYLabel: (value) => `${value}`,
          // Tùy chỉnh màu label
          labelColor: theme.text.primary,
          // Tùy chỉnh màu đường kẻ
          lineColor: {
            grid: {
              x: "transparent", // ← ẩn đường grid dọc
              y: theme.border.default, // ← giữ đường grid ngang
            },
            frame: "transparent",
          },
          // Số lượng tick trên trục Y
          tickCount: 5,
        }}
      >
        {({ points, chartBounds }) => (
          <Bar
            points={points.value}
            chartBounds={chartBounds}
            color={theme.base.primary}
            barWidth={40}
          />
        )}
      </CartesianChart>
    </View>
  );
};

export default BarChart;
