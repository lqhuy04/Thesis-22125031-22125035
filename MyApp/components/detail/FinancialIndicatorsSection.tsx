import React, { useEffect, useRef, useState } from "react";
import { Animated, View, StyleSheet } from "react-native";
import { Text } from "../ui/Text";
import {
  CashFlows,
  FinancialIndicators,
  getCashFlows,
  getFinancialIndicators,
} from "@/helpers/FundamentalAnalysisHelpers";
import { useTheme } from "@/hooks/ThemeContext";
import { useLocalization } from "@/hooks/LocalizationContext";

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

// ─── Skeleton Row ──────────────────────────────────────────────────────────────

const SkeletonRow = ({
  animatedValue,
  baseColor,
  highlightColor,
  showDivider,
  dividerColor,
}: {
  animatedValue: Animated.Value;
  baseColor: string;
  highlightColor: string;
  showDivider: boolean;
  dividerColor: string;
}) => (
  <>
    <View style={styles.row}>
      <SkeletonBox
        width="40%"
        height={14}
        animatedValue={animatedValue}
        baseColor={baseColor}
        highlightColor={highlightColor}
      />
      <SkeletonBox
        width="25%"
        height={14}
        animatedValue={animatedValue}
        baseColor={baseColor}
        highlightColor={highlightColor}
      />
    </View>
    {showDivider && (
      <View style={[styles.divider, { backgroundColor: dividerColor }]} />
    )}
  </>
);

// ─── Skeleton Card ─────────────────────────────────────────────────────────────

const SkeletonCard = ({
  title,
  rowCount,
  animatedValue,
  cardBg,
  baseColor,
  highlightColor,
  dividerColor,
  style,
}: {
  title: string;
  rowCount: number;
  animatedValue: Animated.Value;
  cardBg: string;
  baseColor: string;
  highlightColor: string;
  dividerColor: string;
  style?: object;
}) => (
  <View style={[styles.card, { backgroundColor: cardBg }, style]}>
    {/* Section title placeholder */}
    <SkeletonBox
      width="45%"
      height={16}
      animatedValue={animatedValue}
      baseColor={baseColor}
      highlightColor={highlightColor}
      style={{ marginBottom: 16 }}
    />

    {Array.from({ length: rowCount }).map((_, i) => (
      <SkeletonRow
        key={i}
        animatedValue={animatedValue}
        baseColor={baseColor}
        highlightColor={highlightColor}
        showDivider={i < rowCount - 1}
        dividerColor={dividerColor}
      />
    ))}
  </View>
);

// ─── Full Skeleton Layout ──────────────────────────────────────────────────────

const FinancialIndicatorsSkeleton = ({
  cardBg,
  baseColor,
  highlightColor,
  dividerColor,
}: {
  cardBg: string;
  baseColor: string;
  highlightColor: string;
  dividerColor: string;
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

  const commonProps = {
    animatedValue,
    baseColor,
    highlightColor,
    dividerColor,
    cardBg,
  };

  return (
    <View style={{ marginHorizontal: 12 }}>
      {/* Section header */}
      <Animated.View
        style={[
          styles.sectionTitle,
          {
            backgroundColor: animatedValue.interpolate({
              inputRange: [0, 1],
              outputRange: [baseColor, highlightColor],
            }),
          },
        ]}
      />

      {/* Định giá – 6 rows */}
      <SkeletonCard {...commonProps} title="Định giá" rowCount={6} />

      {/* Khả năng sinh lời – 5 rows */}
      <SkeletonCard
        {...commonProps}
        title="Khả năng sinh lời"
        rowCount={5}
        style={{ marginTop: 12 }}
      />

      {/* Sức mạnh tài chính – 4 rows */}
      <SkeletonCard
        {...commonProps}
        title="Sức mạnh tài chính"
        rowCount={4}
        style={{ marginTop: 12 }}
      />
    </View>
  );
};

// ─── Helpers ──────────────────────────────────────────────────────────────────

const fmt = (value: number | null | undefined, decimals = 2, suffix = "") =>
  value == null || !isFinite(value) ? "N/A" : `${value.toFixed(decimals)}${suffix}`;

const fmtPct = (value: number | null | undefined) => fmt(value != null ? value * 100 : null, 2, "%");

const fmtBillion = (value: number | null | undefined, unit: string) =>
  value == null ? "N/A" : `${(value / 1_000_000_000).toFixed(2)} ${unit}`;

// ─── Main Component ────────────────────────────────────────────────────────────

interface FinancialIndicatorsSectionProps {
  stockSymbol: string;
}

const FinancialIndicatorsSection = ({
  stockSymbol,
}: FinancialIndicatorsSectionProps) => {
  const { theme } = useTheme();
  const { t } = useLocalization();
  const [financialIndicators, setFinancialIndicators] =
    useState<FinancialIndicators | null>(null);
  const [cashFlows, setCashFlows] = useState<CashFlows | null>(null);
  const [isLoading, setIsLoading] = useState(true);

  useEffect(() => {
    setIsLoading(true);
    setFinancialIndicators(null);
    setCashFlows(null);

    Promise.all([
      getFinancialIndicators(stockSymbol).then((res) => {
        if (res.status) setFinancialIndicators(res.data);
      }),
      getCashFlows(stockSymbol).then((res) => {
        if (res.status) setCashFlows(res.data);
      }),
    ]).finally(() => setIsLoading(false));
  }, [stockSymbol]);

  // Derive skeleton colors from theme
  const baseColor = theme.border.default;
  const highlightColor = theme.background.bg;

  if (isLoading) {
    return (
      <FinancialIndicatorsSkeleton
        cardBg={theme.background.bg}
        baseColor={baseColor}
        highlightColor={highlightColor}
        dividerColor={theme.border.default}
      />
    );
  }

  if (financialIndicators == null || cashFlows == null) return null;

  return (
    <View style={{ marginHorizontal: 12 }}>
      <Text
        typography="titleLarge"
        color={theme.text.primary}
        style={{ marginBottom: 12, marginTop: 24 }}
      >
        {t("financialIndicators.sectionTitle")}
      </Text>

      {/* ── Định giá ── */}
      <View
        style={{
          backgroundColor: theme.background.bg,
          borderRadius: 12,
          padding: 12,
        }}
      >
        <Text
          typography="titleMedium"
          color={theme.text.primary}
          style={{ marginBottom: 12 }}
        >
          {t("financialIndicators.valuation")}
        </Text>

        {[
          {
            label: t("financialIndicators.marketCap"),
            value: fmtBillion(financialIndicators.market_cap, t("financialIndicators.billionVND")),
          },
          {
            label: t("financialIndicators.pe"),
            value: fmt(financialIndicators.pe_ratio),
          },
          {
            label: t("financialIndicators.pb"),
            value: fmt(financialIndicators.pb_ratio),
          },
          {
            label: t("financialIndicators.eps"),
            value: fmt(financialIndicators.eps),
          },
          {
            label: t("financialIndicators.bvps"),
            value: fmt(financialIndicators.bvps),
          },
          {
            label: t("financialIndicators.evEbitda"),
            value: fmt(financialIndicators.ev_ebitda),
          },
        ].map(({ label, value }, i, arr) => (
          <React.Fragment key={label}>
            <View style={styles.row}>
              <Text typography="bodyLarge" color={theme.text.primary + "88"}>
                {label}
              </Text>
              <Text typography="titleMedium" color={theme.text.primary}>
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

      {/* ── Khả năng sinh lời ── */}
      <View
        style={{
          backgroundColor: theme.background.bg,
          borderRadius: 12,
          padding: 12,
          marginTop: 12,
        }}
      >
        <Text
          typography="titleMedium"
          color={theme.text.primary}
          style={{ marginBottom: 12 }}
        >
          {t("financialIndicators.profitability")}
        </Text>

        {[
          {
            label: t("financialIndicators.roe"),
            value: fmtPct(financialIndicators.roe),
          },
          {
            label: t("financialIndicators.roa"),
            value: fmtPct(financialIndicators.roa),
          },
          {
            label: t("financialIndicators.roic"),
            value: fmtPct(financialIndicators.roic),
          },
          {
            label: t("financialIndicators.grossMargin"),
            value: fmtPct(financialIndicators.gross_margin),
          },
          {
            label: t("financialIndicators.netMargin"),
            value: fmtPct(financialIndicators.net_margin),
          },
        ].map(({ label, value }, i, arr) => (
          <React.Fragment key={label}>
            <View style={styles.row}>
              <Text typography="bodyLarge" color={theme.text.primary + "88"}>
                {label}
              </Text>
              <Text typography="titleMedium" color={theme.text.primary}>
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

      {/* ── Sức mạnh tài chính ── */}
      <View
        style={{
          backgroundColor: theme.background.bg,
          borderRadius: 12,
          padding: 12,
          marginTop: 12,
        }}
      >
        <Text
          typography="titleMedium"
          color={theme.text.primary}
          style={{ marginBottom: 12 }}
        >
          {t("financialIndicators.financialStrength")}
        </Text>

        {[
          {
            label: t("financialIndicators.debtToEquity"),
            value: fmt(financialIndicators.debt_to_equity),
          },
          {
            label: t("financialIndicators.debtToAsset"),
            value: fmt(financialIndicators.financial_leverage != null ? 1 - 1 / financialIndicators.financial_leverage : null),
          },
          {
            label: t("financialIndicators.quickRatio"),
            value: fmt(financialIndicators.quick_ratio),
          },
          {
            label: t("financialIndicators.currentRatio"),
            value: fmt(financialIndicators.current_ratio),
          },
        ].map(({ label, value }, i, arr) => (
          <React.Fragment key={label}>
            <View style={styles.row}>
              <Text typography="bodyLarge" color={theme.text.primary + "88"}>
                {label}
              </Text>
              <Text typography="titleMedium" color={theme.text.primary}>
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
    </View>
  );
};

// ─── Shared Styles ─────────────────────────────────────────────────────────────

const styles = StyleSheet.create({
  row: {
    flexDirection: "row",
    alignItems: "center",
    justifyContent: "space-between",
  },
  divider: {
    width: "100%",
    height: 1,
    marginVertical: 12,
  },
  card: {
    borderRadius: 12,
    padding: 12,
  },
  sectionTitle: {
    width: "50%",
    height: 18,
    borderRadius: 6,
    marginVertical: 12,
  },
});

export default FinancialIndicatorsSection;
