import ScreenHeader from "@/components/ui/ScreenHeader";
import { useTheme } from "@/hooks/ThemeContext";
import { useLocalization } from "@/hooks/LocalizationContext";
import React, { useEffect, useMemo, useRef, useState } from "react";
import {
  Animated,
  Dimensions,
  ScrollView,
  StyleSheet,
  View,
} from "react-native";
import { useLocalSearchParams } from "expo-router";
import { useSafeAreaInsets } from "react-native-safe-area-context";
import { Text } from "@/components/ui/Text";
import Octicons from "@expo/vector-icons/Octicons";
import LinearGradient from "react-native-linear-gradient";
import { AnalysisData, getAnalysis } from "@/helpers/AgenticHelpers";
import { RadarChart, RadarAxis } from "@/components/ui/RadarChart";

const screenWidth = Dimensions.get("window").width;

// Brand purple gradient, matching the app theme.
const PURPLE_GRADIENT = ["#9D8CFF", "#7B5CFF", "#613DE4"] as const;

// Small gradient accent bar shown to the left of section titles.
const SectionTitle = ({ children }: { children: React.ReactNode }) => {
  const { theme } = useTheme();
  return (
    <View style={styles.sectionTitleRow}>
      <LinearGradient
        colors={PURPLE_GRADIENT as unknown as string[]}
        start={{ x: 0, y: 0 }}
        end={{ x: 0, y: 1 }}
        style={styles.sectionAccent}
      />
      <Text typography="titleMedium" color={theme.text.primary}>
        {children}
      </Text>
    </View>
  );
};

// ─── Skeleton Primitives ───────────────────────────────────────────────────────

interface SkeletonBoxProps {
  width?: number | `${number}%`;
  height?: number;
  borderRadius?: number;
  style?: object;
  animatedValue: Animated.Value;
  baseColor: string;
  highlightColor: string;
}

const SkeletonBox = ({
  width = "100%",
  height = 16,
  borderRadius = 6,
  style,
  animatedValue,
  baseColor,
  highlightColor,
}: SkeletonBoxProps) => {
  const backgroundColor = animatedValue.interpolate({
    inputRange: [0, 1],
    outputRange: [baseColor, highlightColor],
  });

  return (
    <Animated.View
      style={[{ width, height, borderRadius, backgroundColor }, style]}
    />
  );
};

const AIAnalysisSkeleton = ({
  cardBg,
  baseColor,
  highlightColor,
  dividerColor,
  contentPadding,
}: {
  cardBg: string;
  baseColor: string;
  highlightColor: string;
  dividerColor: string;
  contentPadding: number;
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

  const box = { animatedValue, baseColor, highlightColor };

  return (
    <ScrollView
      style={{ flex: 1 }}
      contentContainerStyle={{ padding: 12, paddingBottom: contentPadding }}
      scrollEnabled={false}
    >
      {/* ── Symbol + Recommendation ── */}
      <View style={[styles.card, { backgroundColor: cardBg }]}>
        <View style={styles.rowBetween}>
          <View>
            <SkeletonBox
              {...box}
              width={48}
              height={12}
              style={{ marginBottom: 8 }}
            />
            <SkeletonBox {...box} width={140} height={18} />
          </View>
          <SkeletonBox {...box} width={96} height={32} borderRadius={20} />
        </View>

        {/* Confidence */}
        <View style={{ marginTop: 16 }}>
          <View style={styles.rowBetween}>
            <SkeletonBox {...box} width={88} height={14} />
            <SkeletonBox {...box} width={44} height={16} />
          </View>
          <SkeletonBox
            {...box}
            height={8}
            borderRadius={4}
            style={{ marginTop: 8 }}
          />
        </View>
      </View>

      {/* ── Trading Plan ── */}
      <View style={[styles.card, { backgroundColor: cardBg, marginTop: 12 }]}>
        <SkeletonBox
          {...box}
          width={120}
          height={18}
          style={{ marginBottom: 16 }}
        />
        {[0, 1, 2, 3].map((i, _, arr) => (
          <React.Fragment key={i}>
            <View style={styles.rowBetween}>
              <SkeletonBox {...box} width="35%" height={14} />
              <SkeletonBox {...box} width={56} height={16} />
            </View>
            {i < arr.length - 1 && (
              <View
                style={[styles.divider, { backgroundColor: dividerColor }]}
              />
            )}
          </React.Fragment>
        ))}
      </View>

      {/* ── Score Breakdown (Radar) ── */}
      <View style={[styles.card, { backgroundColor: cardBg, marginTop: 12 }]}>
        <SkeletonBox
          {...box}
          width={140}
          height={18}
          style={{ marginBottom: 16 }}
        />
        <SkeletonBox
          {...box}
          width={200}
          height={200}
          borderRadius={100}
          style={{ alignSelf: "center", marginVertical: 8 }}
        />
      </View>

      {/* ── Detailed Analysis ── */}
      <View style={[styles.card, { backgroundColor: cardBg, marginTop: 12 }]}>
        <SkeletonBox
          {...box}
          width={140}
          height={18}
          style={{ marginBottom: 16 }}
        />
        {["100%", "100%", "92%", "100%", "78%", "100%", "60%"].map((w, i) => (
          <SkeletonBox
            {...box}
            key={i}
            width={w as `${number}%`}
            height={12}
            style={{ marginBottom: 10 }}
          />
        ))}
      </View>
    </ScrollView>
  );
};

const AIAnalysis = () => {
  const { theme } = useTheme();
  const { t } = useLocalization();
  const insets = useSafeAreaInsets();

  const { data } = useLocalSearchParams() || {};
  const stockSymbol = (data as string) ?? "";

  const [analysis, setAnalysis] = useState<AnalysisData | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [selectedAxis, setSelectedAxis] = useState<number | null>(null);

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

  const formatPrice = (value: number | null | undefined) =>
    value == null ? t("aiAnalysis.notAvailable") : value.toFixed(2);

  // Order must match axisAnalysisKeys below (index 0 = news, 1 = fundamental, 2 = technical).
  const scoreData = useMemo<RadarAxis[]>(
    () => [
      { label: t("aiAnalysis.newsScore"), value: analysis?.score?.news ?? 0 },
      {
        label: t("aiAnalysis.fundamentalScore"),
        value: analysis?.score?.fundamental ?? 0,
      },
      {
        label: t("aiAnalysis.technicalScore"),
        value: analysis?.score?.technical ?? 0,
      },
    ],
    // eslint-disable-next-line react-hooks/exhaustive-deps
    [analysis?.score],
  );

  const axisAnalysisKeys: (keyof AnalysisData["analysis"])[] = [
    "news",
    "fundamental",
    "technical",
  ];

  const handleAxisPress = (index: number) => {
    setSelectedAxis((prev) => (prev === index ? null : index));
  };

  return (
    <View style={{ flex: 1, backgroundColor: theme.background.surface }}>
      <ScreenHeader title={t("aiAnalysis.screenTitle")} />

      {isLoading ? (
        <AIAnalysisSkeleton
          cardBg={theme.background.bg}
          baseColor={theme.border.default}
          highlightColor={theme.background.bg}
          dividerColor={theme.border.default}
          contentPadding={insets.bottom + 24}
        />
      ) : analysis == null ? (
        <View style={styles.centered}>
          <Octicons name="alert" size={32} color={theme.text.primary + "55"} />
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
          {/* ── Symbol + Recommendation (hero) ── */}
          <LinearGradient
            colors={PURPLE_GRADIENT as unknown as string[]}
            start={{ x: 0, y: 0 }}
            end={{ x: 1, y: 1 }}
            style={styles.heroCard}
          >
            <View style={[styles.rowBetween, { margin: 12 }]}>
              <View>
                <Text
                  typography="labelMedium"
                  color="#FFFFFFAA"
                  style={{ marginBottom: 4 }}
                >
                  {stockSymbol}
                </Text>
                <Text typography="titleLarge" color="#FFFFFF">
                  {t("aiAnalysis.recommendation")}
                </Text>
              </View>

              <View style={styles.heroBadge}>
                <Octicons
                  name={isBuy ? "arrow-up-right" : "clock"}
                  size={16}
                  color="#FFFFFF"
                  style={{ marginRight: 6 }}
                />
                <Text typography="titleMedium" color="#FFFFFF">
                  {analysis.recommendation}
                </Text>
              </View>
            </View>

            {/* Confidence */}
            <View style={{ marginTop: 20 }}>
              <View style={[styles.rowBetween, { marginHorizontal: 12 }]}>
                <Text typography="bodyMedium" color="#FFFFFFCC">
                  {t("aiAnalysis.confidence")}
                </Text>
                <Text typography="titleMedium" color="#FFFFFF">
                  {`${(analysis.confidence * 100).toFixed(0)}%`}
                </Text>
              </View>
              <View style={[styles.progressTrack, styles.heroTrack]}>
                <View
                  style={[
                    styles.progressFill,
                    {
                      width: `${Math.min(Math.max(analysis.confidence, 0), 1) * 100}%`,
                      backgroundColor: "#FFFFFF",
                    },
                  ]}
                />
              </View>
            </View>
          </LinearGradient>

          {/* ── Trading Plan ── */}
          <View
            style={[
              styles.card,
              { backgroundColor: theme.background.bg, marginTop: 12 },
            ]}
          >
            <SectionTitle>{t("aiAnalysis.tradingPlan")}</SectionTitle>

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

          {/* ── Score Breakdown (Radar) ── */}
          <View
            style={[
              styles.card,
              { backgroundColor: theme.background.bg, marginTop: 12 },
            ]}
          >
            <SectionTitle>{t("aiAnalysis.scoreBreakdown")}</SectionTitle>

            <View style={{ marginTop: 12, marginBottom: -24 }}>
              <RadarChart
                data={scoreData}
                size={280}
                selectedIndex={selectedAxis}
                onAxisPress={handleAxisPress}
              />
            </View>

            <View
              style={{
                marginTop: 4,
                padding: 12,
                borderRadius: 10,
                backgroundColor: `${PURPLE_GRADIENT[2]}22`,
                borderWidth: 1,
                borderColor: `${PURPLE_GRADIENT[1]}55`,
              }}
            >
            {selectedAxis === null ? (
              <Text
                typography="bodyMedium"
                color={theme.text.primary + "55"}
                style={{ textAlign: "center", lineHeight: 22 }}
              >
                {t("aiAnalysis.tapToViewDetail")}
              </Text>
            ) : (
              <>
                <Text
                  typography="labelMedium"
                  color={PURPLE_GRADIENT[0]}
                  style={{ marginBottom: 6 }}
                >
                  {scoreData[selectedAxis].label}
                </Text>
                <Text
                  typography="bodyMedium"
                  color={theme.text.primary}
                  style={{ lineHeight: 22 }}
                >
                  {analysis.analysis[axisAnalysisKeys[selectedAxis]]}
                </Text>
              </>
            )}
            </View>
          </View>

          {/* ── Summary ── */}
          <View
            style={[
              styles.card,
              { backgroundColor: theme.background.bg, marginTop: 12 },
            ]}
          >
            <SectionTitle>{t("aiAnalysis.analysis")}</SectionTitle>
            <Text
              typography="bodyLarge"
              color={theme.text.primary}
              style={{ lineHeight: 24 }}
            >
              {analysis.analysis.summary}
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
  heroCard: {
    borderRadius: 16,
    shadowColor: "#613DE4",
    shadowOffset: { width: 0, height: 6 },
    shadowOpacity: 0.35,
    shadowRadius: 12,
    elevation: 6,
  },
  heroBadge: {
    flexDirection: "row",
    alignItems: "center",
    paddingVertical: 6,
    paddingHorizontal: 12,
    borderRadius: 20,
    backgroundColor: "rgba(255,255,255,0.2)",
  },
  heroTrack: {
    backgroundColor: "rgba(255,255,255,0.25)",
  },
  sectionTitleRow: {
    flexDirection: "row",
    alignItems: "center",
    marginBottom: 12,
  },
  sectionAccent: {
    width: 4,
    height: 18,
    borderRadius: 2,
    marginRight: 8,
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
    width: screenWidth - 48,
    height: 8,
    borderRadius: 4,
    marginTop: 8,
    marginBottom: 12,
    marginHorizontal: 12,
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
