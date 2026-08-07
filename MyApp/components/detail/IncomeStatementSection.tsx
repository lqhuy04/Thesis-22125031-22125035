import React, { useCallback, useEffect, useRef, useState } from "react";
import {
  Animated,
  LayoutChangeEvent,
  StyleSheet,
  View,
} from "react-native";
import { CartesianChart, Bar } from "victory-native";
import { useFont } from "@shopify/react-native-skia";
import { Text } from "../ui/Text";
import {
  IncomeStatement,
  getIncomeStatements,
} from "@/helpers/FundamentalAnalysisHelpers";
import { useTheme } from "@/hooks/ThemeContext";
import { useLocalization } from "@/hooks/LocalizationContext";

// ─── Helpers ────────────────────────────────────────────────────────────────

const BILLION = 1_000_000_000;

// Định dạng số tỷ đồng: 64000 -> "64.000" (vi-VN), 1250 -> "1.250"
const fmtBillion = (value: number): string =>
  Math.round(value).toLocaleString("vi-VN");

// ─── Single annual bar chart ──────────────────────────────────────────────────

type ChartPoint = {
  year: string;
  value: number; // đơn vị: tỷ đồng
};

const CHART_HEIGHT = 260;

const AnnualBarChart = ({
  data,
  color,
}: {
  data: ChartPoint[];
  color: string;
}) => {
  const { theme } = useTheme();
  const font = useFont(require("@/assets/fonts/Roboto-SemiBold.ttf"), 12);
  const [chartWidth, setChartWidth] = useState(0);

  const values = data.map((d) => d.value);
  const maxValue = Math.max(...values, 0);
  const minValue = Math.min(...values, 0);

  // Thêm khoảng đệm để cột không chạm mép trên/dưới
  const yTop = maxValue > 0 ? maxValue * 1.15 : 0;
  const yBottom = minValue < 0 ? minValue * 1.15 : 0;

  // Bề rộng cột co giãn theo số năm và bề rộng vùng vẽ
  const barWidth =
    data.length > 0 && chartWidth > 0
      ? Math.min(48, Math.max(20, (chartWidth - 80) / data.length - 16))
      : 28;

  return (
    <View
      style={{ height: CHART_HEIGHT }}
      onLayout={(e: LayoutChangeEvent) =>
        setChartWidth(e.nativeEvent.layout.width)
      }
    >
      <CartesianChart
        data={data}
        xKey="year"
        yKeys={["value"]}
        domain={{ y: [yBottom, yTop] }}
        domainPadding={{ left: 28, right: 28, top: 8 }}
        axisOptions={{
          font,
          formatXLabel: (v) => `${v}`,
          formatYLabel: (v) => fmtBillion(v),
          labelColor: theme.text.primary + "99",
          lineColor: {
            grid: { x: "transparent", y: theme.border.default },
            frame: "transparent",
          },
          tickCount: { x: data.length, y: 5 },
        }}
      >
        {({ points, chartBounds }) => (
          <Bar
            points={points.value}
            chartBounds={chartBounds}
            color={color}
            barWidth={barWidth}
            animate={{ type: "spring" }}
            roundedCorners={{ topLeft: 4, topRight: 4 }}
          />
        )}
      </CartesianChart>
    </View>
  );
};

// ─── Chart card ────────────────────────────────────────────────────────────

const ChartCard = ({
  title,
  data,
  color,
}: {
  title: string;
  data: ChartPoint[];
  color: string;
}) => {
  const { theme } = useTheme();
  const { t } = useLocalization();

  return (
    <View style={[styles.card, { backgroundColor: theme.background.bg }]}>
      <Text typography="titleMedium" color={theme.text.primary}>
        {title}
      </Text>
      <Text
        typography="bodyMedium"
        color={theme.text.primary + "88"}
        style={{ marginTop: 2, marginBottom: 4 }}
      >
        {t("incomeStatement.unit")}
      </Text>
      <AnnualBarChart data={data} color={color} />
    </View>
  );
};

// ─── Skeleton ────────────────────────────────────────────────────────────────

const IncomeStatementSkeleton = ({
  cardBg,
  baseColor,
  highlightColor,
}: {
  cardBg: string;
  baseColor: string;
  highlightColor: string;
}) => {
  const animatedValue = useRef(new Animated.Value(0)).current;

  useEffect(() => {
    const pulse = Animated.loop(
      Animated.sequence([
        Animated.timing(animatedValue, {
          toValue: 1,
          duration: 800,
          useNativeDriver: false,
        }),
        Animated.timing(animatedValue, {
          toValue: 0,
          duration: 800,
          useNativeDriver: false,
        }),
      ]),
    );
    pulse.start();
    return () => pulse.stop();
  }, [animatedValue]);

  const bg = animatedValue.interpolate({
    inputRange: [0, 1],
    outputRange: [baseColor, highlightColor],
  });

  const SkeletonCard = () => (
    <View style={[styles.card, { backgroundColor: cardBg }]}>
      <Animated.View
        style={{
          width: "45%",
          height: 16,
          borderRadius: 6,
          backgroundColor: bg,
          marginBottom: 16,
        }}
      />
      <View style={styles.skeletonBars}>
        {[0.5, 0.7, 0.85, 1].map((h, i) => (
          <Animated.View
            key={i}
            style={{
              width: 28,
              height: CHART_HEIGHT * 0.7 * h,
              borderRadius: 4,
              backgroundColor: bg,
            }}
          />
        ))}
      </View>
    </View>
  );

  return (
    <View style={{ marginHorizontal: 12 }}>
      <Animated.View
        style={{
          width: "50%",
          height: 18,
          borderRadius: 6,
          backgroundColor: bg,
          marginVertical: 12,
          marginTop: 24,
        }}
      />
      <SkeletonCard />
      <View style={{ height: 12 }} />
      <SkeletonCard />
    </View>
  );
};

// ─── Main Component ────────────────────────────────────────────────────────────

interface IncomeStatementSectionProps {
  stockSymbol: string;
  registerRefresh?: (fn: () => Promise<void>) => () => void;
}

const IncomeStatementSection = ({
  stockSymbol,
  registerRefresh,
}: IncomeStatementSectionProps) => {
  const { theme } = useTheme();
  const { t } = useLocalization();
  const [statements, setStatements] = useState<IncomeStatement[] | null>(null);
  const [isLoading, setIsLoading] = useState(true);

  const fetchData = useCallback(async (showLoading = true) => {
    if (showLoading) {
      setIsLoading(true);
    }
    try {
      const result = await getIncomeStatements(stockSymbol);
      if (result.status) {
        setStatements(result.data);
      }
    } finally {
      if (showLoading) {
        setIsLoading(false);
      }
    }
  }, [stockSymbol]);

  useEffect(() => {
    fetchData();
  }, [fetchData]);

  // Pull-to-refresh
  useEffect(() => {
    const unregister = registerRefresh?.(() => fetchData(false));
    return () => unregister?.();
  }, [registerRefresh, fetchData]);

  if (isLoading) {
    return (
      <IncomeStatementSkeleton
        cardBg={theme.background.bg}
        baseColor={theme.border.default}
        highlightColor={theme.background.bg}
      />
    );
  }

  if (statements == null || statements.length === 0) return null;

  // Chỉ giữ những năm có dữ liệu (bỏ qua năm null)
  const revenueData: ChartPoint[] = statements
    .filter((s) => s.net_revenue != null)
    .map((s) => ({ year: `${s.year}`, value: s.net_revenue! / BILLION }));

  const profitData: ChartPoint[] = statements
    .filter((s) => s.net_profit_after_tax != null)
    .map((s) => ({
      year: `${s.year}`,
      value: s.net_profit_after_tax! / BILLION,
    }));

  // Không có cột nào để vẽ
  if (revenueData.length === 0 && profitData.length === 0) return null;

  return (
    <View style={{ marginHorizontal: 12 }}>
      <Text
        typography="titleLarge"
        color={theme.text.primary}
        style={{ marginBottom: 12, marginTop: 24 }}
      >
        {t("incomeStatement.sectionTitle")}
      </Text>

      {revenueData.length > 0 && (
        <ChartCard
          title={t("incomeStatement.revenueTitle")}
          data={revenueData}
          color={theme.base.primary}
        />
      )}

      {profitData.length > 0 && (
        <View style={{ marginTop: 12 }}>
          <ChartCard
            title={t("incomeStatement.profitTitle")}
            data={profitData}
            color={theme.base.success}
          />
        </View>
      )}
    </View>
  );
};

const styles = StyleSheet.create({
  card: {
    borderRadius: 12,
    padding: 12,
  },
  skeletonBars: {
    flexDirection: "row",
    alignItems: "flex-end",
    justifyContent: "space-around",
    height: CHART_HEIGHT,
  },
});

export default IncomeStatementSection;
