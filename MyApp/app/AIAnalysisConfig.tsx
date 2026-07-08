import ScreenHeader from "@/components/ui/ScreenHeader";
import { Text } from "@/components/ui/Text";
import { useLocalization } from "@/hooks/LocalizationContext";
import { useTheme } from "@/hooks/ThemeContext";
import {
  DataSelection,
  FundamentalSelection,
  TechnicalSelection,
  WeightSelection,
} from "@/helpers/AgenticHelpers";
import { useLocalSearchParams, useRouter } from "expo-router";
import * as SecureStore from "expo-secure-store";
import React, { useEffect, useRef, useState } from "react";
import {
  PanResponder,
  Pressable,
  ScrollView,
  StyleSheet,
  Switch,
  View,
} from "react-native";
import { useSafeAreaInsets } from "react-native-safe-area-context";
import LinearGradient from "react-native-linear-gradient";
import Octicons from "@expo/vector-icons/Octicons";

const PURPLE_GRADIENT = ["#9D8CFF", "#7B5CFF", "#613DE4"] as const;

const WEIGHT_COLORS = {
  technical: "#5B8DEF",
  fundamental: "#F5A623",
  news: "#2ECC71",
} as const;

const MIN_WEIGHT_PCT = 0;

type Mode = "auto" | "manual";

const DEFAULT_TECHNICAL: TechnicalSelection = {
  ma: true,
  boll: true,
  rsi: true,
  macd: true,
  kdj: true,
};

const DEFAULT_FUNDAMENTAL: FundamentalSelection = {
  liquidity: true,
  leverage: true,
  efficiency: true,
  profitability: true,
  valuation: true,
};

const DEFAULT_WEIGHT: WeightSelection = {
  technical: 0.34,
  fundamental: 0.33,
  news: 0.33,
};

const clampPct = (value: number, min: number, max: number) =>
  Math.min(Math.max(value, min), max);

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
        borderColor: selected ? theme.base.primary : theme.border.default,
        borderWidth: selected ? 1.5 : 1,
      },
    ]}
  >
    <View style={styles.modeCardInner}>
      <View
        style={[
          styles.radioOuter,
          { borderColor: selected ? theme.base.primary : theme.border.default },
        ]}
      >
        {selected && (
          <View
            style={[styles.radioInner, { backgroundColor: theme.base.primary }]}
          />
        )}
      </View>
      <View style={{ flex: 1 }}>
        <Text
          typography="titleSmall"
          color={selected ? theme.base.primary : theme.text.primary}
        >
          {title}
        </Text>
        <Text
          typography="bodySmall"
          color={theme.text.primary + "88"}
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

const WeightLegendItem = ({
  color,
  label,
  pct,
}: {
  color: string;
  label: string;
  pct: number;
}) => (
  <View style={styles.weightLegendItem}>
    <View style={[styles.weightLegendDot, { backgroundColor: color }]} />
    <Text typography="labelSmall" color={color}>
      {label} {pct}%
    </Text>
  </View>
);

const WeightSlider = ({
  weight,
  onChange,
  theme,
  labels,
}: {
  weight: WeightSelection;
  onChange: (w: WeightSelection) => void;
  theme: ReturnType<typeof useTheme>["theme"];
  labels: { technical: string; fundamental: string; news: string };
}) => {
  const [trackWidth, setTrackWidth] = useState(0);
  const grantRef = useRef({ d1: 0, d2: 0 });

  const techPct = Math.round(weight.technical * 100);
  const fundPct = Math.round(weight.fundamental * 100);
  const newsPct = 100 - techPct - fundPct;

  // PanResponder tracks touch/gesture state internally, so it must be created
  // ONCE (not on every render) or an in-flight drag loses its starting point
  // the moment `onChange` triggers a re-render. Fresh values it needs mid-drag
  // are read from this ref instead of being captured in a stale closure.
  const liveRef = useRef({ techPct, fundPct, trackWidth, onChange });
  liveRef.current = { techPct, fundPct, trackWidth, onChange };

  const commit = (d1: number, d2: number) => {
    const t1 = Math.round(d1);
    const t2 = Math.round(d2);
    liveRef.current.onChange({
      technical: t1 / 100,
      fundamental: (t2 - t1) / 100,
      news: (100 - t2) / 100,
    });
  };

  const createResponder = (handle: 1 | 2) =>
    PanResponder.create({
      onStartShouldSetPanResponder: () => true,
      onStartShouldSetPanResponderCapture: () => true,
      onMoveShouldSetPanResponder: () => true,
      onMoveShouldSetPanResponderCapture: () => true,
      onPanResponderTerminationRequest: () => false,
      onPanResponderGrant: () => {
        const { techPct, fundPct } = liveRef.current;
        grantRef.current = { d1: techPct, d2: techPct + fundPct };
      },
      onPanResponderMove: (_evt, gestureState) => {
        const { trackWidth } = liveRef.current;
        if (trackWidth <= 0) return;
        const deltaPct = (gestureState.dx / trackWidth) * 100;
        const { d1, d2 } = grantRef.current;
        if (handle === 1) {
          const next = clampPct(
            d1 + deltaPct,
            MIN_WEIGHT_PCT,
            d2 - MIN_WEIGHT_PCT,
          );
          commit(next, d2);
        } else {
          const next = clampPct(
            d2 + deltaPct,
            d1 + MIN_WEIGHT_PCT,
            100 - MIN_WEIGHT_PCT,
          );
          commit(d1, next);
        }
      },
    });

  const handle1Ref = useRef<ReturnType<typeof createResponder> | null>(null);
  const handle2Ref = useRef<ReturnType<typeof createResponder> | null>(null);
  if (!handle1Ref.current) handle1Ref.current = createResponder(1);
  if (!handle2Ref.current) handle2Ref.current = createResponder(2);
  const handle1 = handle1Ref.current;
  const handle2 = handle2Ref.current;

  return (
    <View>
      <View style={styles.weightLegendRow}>
        <WeightLegendItem
          color={WEIGHT_COLORS.technical}
          label={labels.technical}
          pct={techPct}
        />
        <WeightLegendItem
          color={WEIGHT_COLORS.fundamental}
          label={labels.fundamental}
          pct={fundPct}
        />
        <WeightLegendItem
          color={WEIGHT_COLORS.news}
          label={labels.news}
          pct={newsPct}
        />
      </View>

      <View
        style={styles.weightTrack}
        onLayout={(e) => setTrackWidth(e.nativeEvent.layout.width)}
      >
        <View style={styles.weightFillRow}>
          <View
            style={{
              width: `${techPct}%`,
              backgroundColor: WEIGHT_COLORS.technical,
            }}
          />
          <View
            style={{
              width: `${fundPct}%`,
              backgroundColor: WEIGHT_COLORS.fundamental,
            }}
          />
          <View
            style={{
              width: `${newsPct}%`,
              backgroundColor: WEIGHT_COLORS.news,
            }}
          />
        </View>

        {trackWidth > 0 && (
          <>
            <View
              {...handle1.panHandlers}
              style={[
                styles.weightHandle,
                { left: (techPct / 100) * trackWidth - 14 },
              ]}
            >
              <View
                style={[
                  styles.weightHandleKnob,
                  { borderColor: theme.background.bg },
                ]}
              />
            </View>
            <View
              {...handle2.panHandlers}
              style={[
                styles.weightHandle,
                { left: ((techPct + fundPct) / 100) * trackWidth - 14 },
              ]}
            >
              <View
                style={[
                  styles.weightHandleKnob,
                  { borderColor: theme.background.bg },
                ]}
              />
            </View>
          </>
        )}
      </View>
    </View>
  );
};

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
  const [technical, setTechnical] = useState<TechnicalSelection>({
    ...DEFAULT_TECHNICAL,
  });
  const [fundamental, setFundamental] = useState<FundamentalSelection>({
    ...DEFAULT_FUNDAMENTAL,
  });
  const [weight, setWeight] = useState<WeightSelection>({
    ...DEFAULT_WEIGHT,
  });

  const PRESET_KEY = "ai_analysis_preset";
  const [hydrated, setHydrated] = useState(false);

  // Load preset on mount
  useEffect(() => {
    SecureStore.getItemAsync(PRESET_KEY).then((raw) => {
      if (raw) {
        try {
          const preset = JSON.parse(raw);
          if (preset.mode) setMode(preset.mode);
          if (typeof preset.newsEnabled === "boolean")
            setNewsEnabled(preset.newsEnabled);
          if (typeof preset.technicalEnabled === "boolean")
            setTechnicalEnabled(preset.technicalEnabled);
          if (typeof preset.fundamentalEnabled === "boolean")
            setFundamentalEnabled(preset.fundamentalEnabled);
          if (preset.technical) setTechnical(preset.technical);
          if (preset.fundamental) setFundamental(preset.fundamental);
          if (preset.weight) setWeight(preset.weight);
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
      JSON.stringify({
        mode,
        newsEnabled,
        technicalEnabled,
        fundamentalEnabled,
        technical,
        fundamental,
        weight,
      }),
    );
  }, [
    hydrated,
    mode,
    newsEnabled,
    technicalEnabled,
    fundamentalEnabled,
    technical,
    fundamental,
    weight,
  ]);

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
    liquidity: t("aiAnalysis.liquidity"),
    leverage: t("aiAnalysis.leverage"),
    efficiency: t("aiAnalysis.efficiency"),
    profitability: t("aiAnalysis.profitability"),
    valuation: t("aiAnalysis.valuation"),
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
      selection.weight = { ...weight };
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

        {/* ── Weight allocation ── */}
        {mode === "manual" && (
          <View
            style={[
              styles.configCard,
              { backgroundColor: theme.background.bg },
            ]}
          >
            <Text
              typography="titleSmall"
              color={theme.text.primary + "88"}
              style={{ marginBottom: 4 }}
            >
              {t("aiAnalysis.weightTitle")}
            </Text>
            <Text
              typography="bodySmall"
              color={theme.text.primary + "66"}
              style={{ marginBottom: 16 }}
            >
              {t("aiAnalysis.weightHint")}
            </Text>
            <WeightSlider
              weight={weight}
              onChange={setWeight}
              theme={theme}
              labels={{
                technical: t("aiAnalysis.technical"),
                fundamental: t("aiAnalysis.fundamental"),
                news: t("aiAnalysis.news"),
              }}
            />
          </View>
        )}

        {/* ── Manual config ── */}
        {mode === "manual" && (
          <View
            style={[
              styles.configCard,
              { backgroundColor: theme.background.bg, marginTop: 12 },
            ]}
          >
            <Text
              typography="titleSmall"
              color={theme.text.primary + "88"}
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
            backgroundColor: theme.background.bg,
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
  weightLegendRow: {
    flexDirection: "row",
    justifyContent: "space-between",
    marginBottom: 14,
  },
  weightLegendItem: {
    flexDirection: "row",
    alignItems: "center",
    gap: 5,
  },
  weightLegendDot: {
    width: 8,
    height: 8,
    borderRadius: 4,
  },
  weightTrack: {
    height: 28,
    justifyContent: "center",
  },
  weightFillRow: {
    flexDirection: "row",
    width: "100%",
    height: 16,
    borderRadius: 8,
    overflow: "hidden",
  },
  weightHandle: {
    position: "absolute",
    top: -6,
    width: 28,
    height: 40,
    alignItems: "center",
    justifyContent: "center",
  },
  weightHandleKnob: {
    width: 16,
    height: 16,
    borderRadius: 8,
    backgroundColor: "#FFFFFF",
    borderWidth: 3,
    shadowColor: "#000",
    shadowOffset: { width: 0, height: 1 },
    shadowOpacity: 0.25,
    shadowRadius: 2,
    elevation: 3,
  },
});

export default AIAnalysisConfig;
