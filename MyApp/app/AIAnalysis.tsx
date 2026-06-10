import ScreenHeader from "@/components/ui/ScreenHeader";
import { useTheme } from "@/hooks/ThemeContext";
import { useLocalization } from "@/hooks/LocalizationContext";
import React, { useEffect, useState } from "react";
import { ActivityIndicator, ScrollView, StyleSheet, View } from "react-native";
import { useLocalSearchParams } from "expo-router";
import { useSafeAreaInsets } from "react-native-safe-area-context";
import { Text } from "@/components/ui/Text";
import Octicons from "@expo/vector-icons/Octicons";
import { AnalysisData, getAnalysis } from "@/helpers/AgenticHelpers";

const AIAnalysis = () => {
  const { theme } = useTheme();
  const { t } = useLocalization();
  const insets = useSafeAreaInsets();

  const { data } = useLocalSearchParams() || {};
  const stockSymbol = (data as string) ?? "";

  const [analysis, setAnalysis] = useState<AnalysisData | null>(null);
  const [isLoading, setIsLoading] = useState(true);

  useEffect(() => {
    let mounted = true;
    setIsLoading(true);
    setAnalysis(null);

    getAnalysis(stockSymbol)
      .then((res) => {
        if (mounted && res.status) setAnalysis(res.data);
      })
      .finally(() => {
        if (mounted) setIsLoading(false);
      });

    return () => {
      mounted = false;
    };
  }, [stockSymbol]);

  const isBuy = analysis?.recommendation === t("aiAnalysis.buy");
  const recommendationColor = isBuy ? theme.base.success : theme.base.warning;

  const formatPrice = (value: number | null | undefined) =>
    value == null ? t("aiAnalysis.notAvailable") : value.toFixed(2);

  return (
    <View style={{ flex: 1, backgroundColor: theme.background.surface }}>
      <ScreenHeader title={t("aiAnalysis.screenTitle")} />

      {isLoading ? (
        <View style={styles.centered}>
          <ActivityIndicator size="large" color={theme.base.primary} />
          <Text
            typography="bodyLarge"
            color={theme.text.primary + "88"}
            style={{ marginTop: 16 }}
          >
            {t("aiAnalysis.loading")}
          </Text>
        </View>
      ) : analysis == null ? (
        <View style={styles.centered}>
          <Octicons
            name="alert"
            size={32}
            color={theme.text.primary + "55"}
          />
          <Text
            typography="bodyLarge"
            color={theme.text.primary + "88"}
            style={{ marginTop: 12, textAlign: "center" }}
          >
            {t("aiAnalysis.noData")}
          </Text>
        </View>
      ) : (
        <ScrollView
          style={{ flex: 1 }}
          contentContainerStyle={{
            padding: 12,
            paddingBottom: insets.bottom + 24,
          }}
        >
          {/* ── Symbol + Recommendation ── */}
          <View
            style={[styles.card, { backgroundColor: theme.background.bg }]}
          >
            <View style={styles.rowBetween}>
              <View>
                <Text
                  typography="labelMedium"
                  color={theme.text.primary + "88"}
                  style={{ marginBottom: 4 }}
                >
                  {stockSymbol}
                </Text>
                <Text typography="titleMedium" color={theme.text.primary}>
                  {t("aiAnalysis.recommendation")}
                </Text>
              </View>

              <View
                style={[
                  styles.badge,
                  { backgroundColor: recommendationColor + "22" },
                ]}
              >
                <Octicons
                  name={isBuy ? "arrow-up-right" : "clock"}
                  size={16}
                  color={recommendationColor}
                  style={{ marginRight: 6 }}
                />
                <Text typography="titleMedium" color={recommendationColor}>
                  {analysis.recommendation}
                </Text>
              </View>
            </View>

            {/* Confidence */}
            <View style={{ marginTop: 16 }}>
              <View style={styles.rowBetween}>
                <Text
                  typography="bodyMedium"
                  color={theme.text.primary + "88"}
                >
                  {t("aiAnalysis.confidence")}
                </Text>
                <Text typography="titleMedium" color={theme.text.primary}>
                  {`${(analysis.confidence * 100).toFixed(0)}%`}
                </Text>
              </View>
              <View
                style={[
                  styles.progressTrack,
                  { backgroundColor: theme.border.default },
                ]}
              >
                <View
                  style={[
                    styles.progressFill,
                    {
                      width: `${Math.min(Math.max(analysis.confidence, 0), 1) * 100}%`,
                      backgroundColor: recommendationColor,
                    },
                  ]}
                />
              </View>
            </View>
          </View>

          {/* ── Trading Plan ── */}
          <View
            style={[
              styles.card,
              { backgroundColor: theme.background.bg, marginTop: 12 },
            ]}
          >
            <Text
              typography="titleMedium"
              color={theme.text.primary}
              style={{ marginBottom: 12 }}
            >
              {t("aiAnalysis.tradingPlan")}
            </Text>

            {[
              {
                label: t("aiAnalysis.entryPrice"),
                value: formatPrice(analysis.entry_price),
                color: theme.text.primary,
              },
              {
                label: t("aiAnalysis.takeProfit"),
                value: formatPrice(analysis.take_profit_price),
                color: theme.base.success,
              },
              {
                label: t("aiAnalysis.stopLoss"),
                value: formatPrice(analysis.stop_loss_price),
                color: theme.base.error,
              },
              {
                label: t("aiAnalysis.maxHoldCandles"),
                value: formatPrice(analysis.max_hold_candles),
                color: theme.text.primary,
              },
            ].map(({ label, value, color }, i, arr) => (
              <React.Fragment key={label}>
                <View style={styles.rowBetween}>
                  <Text
                    typography="bodyLarge"
                    color={theme.text.primary + "88"}
                  >
                    {label}
                  </Text>
                  <Text typography="titleMedium" color={color}>
                    {value}
                  </Text>
                </View>
                {i < arr.length - 1 && (
                  <View
                    style={[
                      styles.divider,
                      { backgroundColor: theme.border.default },
                    ]}
                  />
                )}
              </React.Fragment>
            ))}
          </View>

          {/* ── Detailed Analysis ── */}
          <View
            style={[
              styles.card,
              { backgroundColor: theme.background.bg, marginTop: 12 },
            ]}
          >
            <Text
              typography="titleMedium"
              color={theme.text.primary}
              style={{ marginBottom: 12 }}
            >
              {t("aiAnalysis.analysis")}
            </Text>
            <Text
              typography="bodyLarge"
              color={theme.text.primary}
              style={{ lineHeight: 24 }}
            >
              {analysis.analysis}
            </Text>
          </View>
        </ScrollView>
      )}
    </View>
  );
};

const styles = StyleSheet.create({
  centered: {
    flex: 1,
    alignItems: "center",
    justifyContent: "center",
    paddingHorizontal: 32,
  },
  card: {
    borderRadius: 12,
    padding: 12,
  },
  rowBetween: {
    flexDirection: "row",
    alignItems: "center",
    justifyContent: "space-between",
  },
  badge: {
    flexDirection: "row",
    alignItems: "center",
    paddingVertical: 6,
    paddingHorizontal: 12,
    borderRadius: 20,
  },
  progressTrack: {
    width: "100%",
    height: 8,
    borderRadius: 4,
    marginTop: 8,
    overflow: "hidden",
  },
  progressFill: {
    height: "100%",
    borderRadius: 4,
  },
  divider: {
    width: "100%",
    height: 1,
    marginVertical: 12,
  },
});

export default AIAnalysis;
