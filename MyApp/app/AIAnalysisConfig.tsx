import ScreenHeader from "@/components/ui/ScreenHeader";
import { Text } from "@/components/ui/Text";
import { useLocalization } from "@/hooks/LocalizationContext";
import { useTheme } from "@/hooks/ThemeContext";
import {
  DataSelection,
  FundamentalSelection,
  TechnicalSelection,
} from "@/helpers/AgenticHelpers";
import { useLocalSearchParams, useRouter } from "expo-router";
import * as SecureStore from "expo-secure-store";
import React, { useEffect, useRef, useState } from "react";
import { Pressable, ScrollView, StyleSheet, Switch, View } from "react-native";
import { useSafeAreaInsets } from "react-native-safe-area-context";
import LinearGradient from "react-native-linear-gradient";
import Octicons from "@expo/vector-icons/Octicons";

const PURPLE_GRADIENT = ["#9D8CFF", "#7B5CFF", "#613DE4"] as const;

type Mode = "auto" | "manual";

const DEFAULT_TECHNICAL: TechnicalSelection = {
  ma: true,
  boll: true,
  rsi: true,
  macd: true,
  kdj: true,
};

const DEFAULT_FUNDAMENTAL: FundamentalSelection = {
  valuation: true,
  profitability: true,
  growth: true,
  financial_health: true,
  cash_flow: true,
};

// ─── Sub-components ───────────────────────────────────────────────────────────

const ModeCard = ({
  selected,
  title,
  description,
  onPress,
  theme,
}: {
  selected: boolean;
  title: string;
  description: string;
  onPress: () => void;
  theme: ReturnType<typeof useTheme>["theme"];
}) => (
  <Pressable
    onPress={onPress}
    style={[
      styles.modeCard,
      {
        backgroundColor: theme.background.bg,
        borderColor: selected ? PURPLE_GRADIENT[1] : theme.border.default,
        borderWidth: selected ? 1.5 : 1,
      },
    ]}
  >
    <View style={styles.modeCardInner}>
      <View
        style={[
          styles.radioOuter,
          { borderColor: selected ? PURPLE_GRADIENT[1] : theme.border.default },
        ]}
      >
        {selected && (
          <View
            style={[styles.radioInner, { backgroundColor: PURPLE_GRADIENT[1] }]}
          />
        )}
      </View>
      <View style={{ flex: 1 }}>
        <Text
          typography="titleSmall"
          color={selected ? PURPLE_GRADIENT[0] : theme.text.primary}
        >
          {title}
        </Text>
        <Text
          typography="bodySmall"
          color={theme.text.secondary}
          style={{ marginTop: 2 }}
        >
          {description}
        </Text>
      </View>
    </View>
  </Pressable>
);

const SectionToggle = ({
  label,
  enabled,
  checkedCount,
  totalCount,
  onToggle,
  theme,
}: {
  label: string;
  enabled: boolean;
  checkedCount: number;
  totalCount: number;
  onToggle: (v: boolean) => void;
  theme: ReturnType<typeof useTheme>["theme"];
}) => (
  <View
    style={[
      styles.sectionToggleRow,
      { borderBottomColor: theme.border.default },
    ]}
  >
    <Text typography="titleSmall" color={theme.text.primary}>
      {label}
    </Text>
    <View style={styles.sectionToggleRight}>
      {enabled && (
        <View
          style={[
            styles.countBadge,
            { backgroundColor: PURPLE_GRADIENT[1] + "22" },
          ]}
        >
          <Text typography="labelSmall" color={PURPLE_GRADIENT[0]}>
            {checkedCount}/{totalCount}
          </Text>
        </View>
      )}
      <Switch
        value={enabled}
        onValueChange={onToggle}
        trackColor={{ false: theme.border.default, true: PURPLE_GRADIENT[1] }}
        thumbColor="#FFFFFF"
      />
    </View>
  </View>
);

const SubCheckbox = ({
  label,
  checked,
  onPress,
  theme,
}: {
  label: string;
  checked: boolean;
  onPress: () => void;
  theme: ReturnType<typeof useTheme>["theme"];
}) => (
  <Pressable onPress={onPress} style={styles.subCheckboxRow}>
    <View
      style={[
        styles.checkbox,
        checked
          ? {
              backgroundColor: PURPLE_GRADIENT[1],
              borderColor: PURPLE_GRADIENT[1],
            }
          : { borderColor: theme.border.default },
      ]}
    >
      {checked && <Octicons name="check" size={10} color="#FFFFFF" />}
    </View>
    <Text typography="bodyMedium" color={theme.text.primary}>
      {label}
    </Text>
  </Pressable>
);

// ─── Main screen ──────────────────────────────────────────────────────────────

const AIAnalysisConfig = () => {
  const { theme } = useTheme();
  const { t } = useLocalization();
  const insets = useSafeAreaInsets();
  const router = useRouter();

  const { data } = useLocalSearchParams() || {};
  const stockSymbol = (data as string) ?? "";

  const [mode, setMode] = useState<Mode>("auto");
  const [newsEnabled, setNewsEnabled] = useState(true);
  const [technicalEnabled, setTechnicalEnabled] = useState(true);
  const [fundamentalEnabled, setFundamentalEnabled] = useState(true);
  const [technical, setTechnical] = useState<TechnicalSelection>({ ...DEFAULT_TECHNICAL });
  const [fundamental, setFundamental] = useState<FundamentalSelection>({ ...DEFAULT_FUNDAMENTAL });

  const PRESET_KEY = "ai_analysis_preset";
  const [hydrated, setHydrated] = useState(false);

  // Load preset on mount
  useEffect(() => {
    SecureStore.getItemAsync(PRESET_KEY).then((raw) => {
      if (raw) {
        try {
          const preset = JSON.parse(raw);
          if (preset.mode) setMode(preset.mode);
          if (typeof preset.newsEnabled === "boolean") setNewsEnabled(preset.newsEnabled);
          if (typeof preset.technicalEnabled === "boolean") setTechnicalEnabled(preset.technicalEnabled);
          if (typeof preset.fundamentalEnabled === "boolean") setFundamentalEnabled(preset.fundamentalEnabled);
          if (preset.technical) setTechnical(preset.technical);
          if (preset.fundamental) setFundamental(preset.fundamental);
        } catch {}
      }
      setHydrated(true);
    });
  }, []);

  // Save preset whenever selections change (skip before hydration completes)
  useEffect(() => {
    if (!hydrated) return;
    SecureStore.setItemAsync(
      PRESET_KEY,
      JSON.stringify({ mode, newsEnabled, technicalEnabled, fundamentalEnabled, technical, fundamental }),
    );
  }, [hydrated, mode, newsEnabled, technicalEnabled, fundamentalEnabled, technical, fundamental]);

  const technicalKeys = Object.keys(
    DEFAULT_TECHNICAL,
  ) as (keyof TechnicalSelection)[];
  const fundamentalKeys = Object.keys(
    DEFAULT_FUNDAMENTAL,
  ) as (keyof FundamentalSelection)[];

  const technicalCheckedCount = technicalKeys.filter(
    (k) => technical[k],
  ).length;
  const fundamentalCheckedCount = fundamentalKeys.filter(
    (k) => fundamental[k],
  ).length;

  const isValid =
    mode === "auto" ||
    newsEnabled ||
    (technicalEnabled && technicalCheckedCount > 0) ||
    (fundamentalEnabled && fundamentalCheckedCount > 0);

  const technicalLabels: Record<keyof TechnicalSelection, string> = {
    ma: t("aiAnalysis.ma"),
    boll: t("aiAnalysis.boll"),
    rsi: t("aiAnalysis.rsi"),
    macd: t("aiAnalysis.macd"),
    kdj: t("aiAnalysis.kdj"),
  };

  const fundamentalLabels: Record<keyof FundamentalSelection, string> = {
    valuation: t("aiAnalysis.valuation"),
    profitability: t("aiAnalysis.profitability"),
    growth: t("aiAnalysis.growth"),
    financial_health: t("aiAnalysis.financialHealth"),
    cash_flow: t("aiAnalysis.cashFlow"),
  };

  const handleAnalyze = () => {
    const params: { data: string; mode: string; dataSelection?: string } = {
      data: stockSymbol,
      mode,
    };

    if (mode === "manual") {
      const selection: DataSelection = {};
      if (newsEnabled) selection.news = true;
      if (technicalEnabled && technicalCheckedCount > 0) {
        selection.technical = { ...technical };
      }
      if (fundamentalEnabled && fundamentalCheckedCount > 0) {
        selection.fundamental = { ...fundamental };
      }
      params.dataSelection = JSON.stringify(selection);
    }

    router.push({ pathname: "/AIAnalysis", params });
  };

  return (
    <View style={{ flex: 1, backgroundColor: theme.background.surface }}>
      <ScreenHeader title={t("aiAnalysis.configScreenTitle")} />

      <ScrollView
        style={{ flex: 1 }}
        contentContainerStyle={{
          padding: 12,
          paddingBottom: insets.bottom + 88,
        }}
      >
        {/* ── Mode selection ── */}
        <View style={{ gap: 8, marginBottom: 20 }}>
          <ModeCard
            selected={mode === "auto"}
            title={t("aiAnalysis.modeAuto")}
            description={t("aiAnalysis.modeAutoDesc")}
            onPress={() => setMode("auto")}
            theme={theme}
          />
          <ModeCard
            selected={mode === "manual"}
            title={t("aiAnalysis.modeManual")}
            description={t("aiAnalysis.modeManualDesc")}
            onPress={() => setMode("manual")}
            theme={theme}
          />
        </View>

        {/* ── Manual config ── */}
        {mode === "manual" && (
          <View
            style={[
              styles.configCard,
              { backgroundColor: theme.background.bg },
            ]}
          >
            <Text
              typography="titleSmall"
              color={theme.text.secondary}
              style={{ marginBottom: 12 }}
            >
              {t("aiAnalysis.dataSourceTitle")}
            </Text>

            {/* News */}
            <SectionToggle
              label={t("aiAnalysis.news")}
              enabled={newsEnabled}
              checkedCount={1}
              totalCount={1}
              onToggle={setNewsEnabled}
              theme={theme}
            />

            {/* Technical */}
            <SectionToggle
              label={t("aiAnalysis.technical")}
              enabled={technicalEnabled}
              checkedCount={technicalCheckedCount}
              totalCount={technicalKeys.length}
              onToggle={(v) => {
                setTechnicalEnabled(v);
                if (v) setTechnical({ ...DEFAULT_TECHNICAL });
              }}
              theme={theme}
            />
            {technicalEnabled &&
              technicalKeys.map((key) => (
                <SubCheckbox
                  key={key}
                  label={technicalLabels[key]}
                  checked={!!technical[key]}
                  onPress={() =>
                    setTechnical((prev) => ({ ...prev, [key]: !prev[key] }))
                  }
                  theme={theme}
                />
              ))}

            <View style={{ height: 8 }} />

            {/* Fundamental */}
            <SectionToggle
              label={t("aiAnalysis.fundamental")}
              enabled={fundamentalEnabled}
              checkedCount={fundamentalCheckedCount}
              totalCount={fundamentalKeys.length}
              onToggle={(v) => {
                setFundamentalEnabled(v);
                if (v) setFundamental({ ...DEFAULT_FUNDAMENTAL });
              }}
              theme={theme}
            />
            {fundamentalEnabled &&
              fundamentalKeys.map((key) => (
                <SubCheckbox
                  key={key}
                  label={fundamentalLabels[key]}
                  checked={!!fundamental[key]}
                  onPress={() =>
                    setFundamental((prev) => ({ ...prev, [key]: !prev[key] }))
                  }
                  theme={theme}
                />
              ))}
          </View>
        )}

        {!isValid && (
          <Text
            typography="bodySmall"
            color={theme.base.error}
            style={{ textAlign: "center", marginTop: 12 }}
          >
            {t("aiAnalysis.selectAtLeastOne")}
          </Text>
        )}
      </ScrollView>

      {/* ── Analyze button (fixed bottom) ── */}
      <View
        style={[
          styles.bottomBar,
          {
            paddingBottom: insets.bottom + 12,
            backgroundColor: theme.background.surface,
          },
        ]}
      >
        <Pressable
          onPress={handleAnalyze}
          disabled={!isValid}
          style={{ opacity: isValid ? 1 : 0.4 }}
        >
          <LinearGradient
            colors={PURPLE_GRADIENT as unknown as string[]}
            start={{ x: 0, y: 0 }}
            end={{ x: 1, y: 0 }}
            style={styles.analyzeBtn}
          >
            <Text typography="titleMedium" color="#FFFFFF">
              {t("aiAnalysis.startAnalysis")}
            </Text>
          </LinearGradient>
        </Pressable>
      </View>
    </View>
  );
};

const styles = StyleSheet.create({
  modeCard: {
    borderRadius: 12,
    padding: 14,
  },
  modeCardInner: {
    flexDirection: "row",
    alignItems: "center",
    gap: 12,
  },
  radioOuter: {
    width: 20,
    height: 20,
    borderRadius: 10,
    borderWidth: 2,
    alignItems: "center",
    justifyContent: "center",
  },
  radioInner: {
    width: 10,
    height: 10,
    borderRadius: 5,
  },
  configCard: {
    borderRadius: 12,
    padding: 14,
  },
  sectionToggleRow: {
    flexDirection: "row",
    alignItems: "center",
    justifyContent: "space-between",
    paddingVertical: 10,
    borderBottomWidth: StyleSheet.hairlineWidth,
  },
  sectionToggleRight: {
    flexDirection: "row",
    alignItems: "center",
    gap: 8,
  },
  countBadge: {
    paddingHorizontal: 8,
    paddingVertical: 2,
    borderRadius: 10,
  },
  subCheckboxRow: {
    flexDirection: "row",
    alignItems: "center",
    paddingVertical: 9,
    paddingLeft: 8,
    gap: 10,
  },
  checkbox: {
    width: 18,
    height: 18,
    borderRadius: 4,
    borderWidth: 1.5,
    alignItems: "center",
    justifyContent: "center",
  },
  bottomBar: {
    position: "absolute",
    bottom: 0,
    left: 0,
    right: 0,
    paddingHorizontal: 16,
    paddingTop: 12,
    borderTopWidth: StyleSheet.hairlineWidth,
    borderTopColor: "rgba(0,0,0,0.08)",
  },
  analyzeBtn: {
    borderRadius: 14,
    paddingVertical: 14,
    alignItems: "center",
  },
});

export default AIAnalysisConfig;
