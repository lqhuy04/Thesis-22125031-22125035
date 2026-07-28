import ScreenHeader from "@/components/ui/ScreenHeader";
import { Text } from "@/components/ui/Text";
import { useLocalization } from "@/hooks/LocalizationContext";
import { useTheme } from "@/hooks/ThemeContext";
import {
  DataSelection,
  TechnicalSelection,
  WeightSelection,
} from "@/helpers/AgenticHelpers";
import { useLocalSearchParams, useRouter } from "expo-router";
import * as SecureStore from "expo-secure-store";
import React, { useEffect, useRef, useState } from "react";
import {
  Animated,
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
import Feather from "@expo/vector-icons/Feather";

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

const DEFAULT_WEIGHT: WeightSelection = {
  technical: 0.34,
  fundamental: 0.33,
  news: 0.33,
};

const clampPct = (value: number, min: number, max: number) =>
  Math.min(Math.max(value, min), max);

const SOURCE_ORDER: (keyof WeightSelection)[] = [
  "technical",
  "fundamental",
  "news",
];

// Chia đều trọng số cho các nguồn đang bật, các nguồn bị tắt nhận 0.
const equalWeights = (
  activeKeys: (keyof WeightSelection)[],
): WeightSelection => {
  const result: WeightSelection = { technical: 0, fundamental: 0, news: 0 };
  const n = activeKeys.length;
  if (n === 0) return result;
  const basePct = Math.round(100 / n);
  let remaining = 100;
  activeKeys.forEach((k, i) => {
    const value = i === n - 1 ? remaining : basePct;
    result[k] = value / 100;
    remaining -= value;
  });
  return result;
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
  enabled,
}: {
  weight: WeightSelection;
  onChange: (w: WeightSelection) => void;
  theme: ReturnType<typeof useTheme>["theme"];
  labels: { technical: string; fundamental: string; news: string };
  enabled: { technical: boolean; fundamental: boolean; news: boolean };
}) => {
  const [trackWidth, setTrackWidth] = useState(0);

  const activeKeys = SOURCE_ORDER.filter((k) => enabled[k]);

  // Làm tròn % cho từng nguồn đang bật; nguồn cuối cùng nhận phần dư để tổng
  // luôn bằng 100 (tránh lệch do làm tròn). Nguồn bị tắt luôn là 0%.
  const activePcts: Partial<Record<keyof WeightSelection, number>> = {};
  let runningSum = 0;
  activeKeys.forEach((k, i) => {
    if (i === activeKeys.length - 1) {
      activePcts[k] = 100 - runningSum;
    } else {
      const p = Math.round(weight[k] * 100);
      activePcts[k] = p;
      runningSum += p;
    }
  });
  const techPct = activePcts.technical ?? 0;
  const fundPct = activePcts.fundamental ?? 0;
  const newsPct = activePcts.news ?? 0;

  // Vị trí các đường phân chia (boundary) giữa các nguồn đang bật, tính theo %
  // cộng dồn. Với n nguồn bật thì có n-1 đường phân chia có thể kéo.
  const boundaries: number[] = [];
  let cum = 0;
  activeKeys.forEach((k, i) => {
    cum += activePcts[k] ?? 0;
    if (i < activeKeys.length - 1) boundaries.push(cum);
  });

  // PanResponder tracks touch/gesture state internally, so responders must be
  // created ONCE (not on every render) or an in-flight drag loses its
  // starting point the moment `onChange` triggers a re-render. Fresh values
  // needed mid-drag are read from this ref instead of a stale closure.
  const liveRef = useRef({ boundaries, activeKeys, trackWidth, onChange });
  liveRef.current = { boundaries, activeKeys, trackWidth, onChange };

  const grantRef = useRef<{ idx: number; values: number[] }>({
    idx: 0,
    values: [],
  });

  const commitBoundaries = (values: number[]) => {
    const { activeKeys, onChange } = liveRef.current;
    const next: WeightSelection = { technical: 0, fundamental: 0, news: 0 };
    let prev = 0;
    activeKeys.forEach((k, i) => {
      const upper = i < values.length ? Math.round(values[i]) : 100;
      next[k] = Math.max(0, upper - prev) / 100;
      prev = upper;
    });
    onChange(next);
  };

  const respondersRef = useRef<
    Map<number, ReturnType<typeof PanResponder.create>>
  >(new Map());

  const getResponder = (idx: number) => {
    const map = respondersRef.current;
    const existing = map.get(idx);
    if (existing) return existing;
    const responder = PanResponder.create({
      onStartShouldSetPanResponder: () => true,
      onStartShouldSetPanResponderCapture: () => true,
      onMoveShouldSetPanResponder: () => true,
      onMoveShouldSetPanResponderCapture: () => true,
      onPanResponderTerminationRequest: () => false,
      onPanResponderGrant: () => {
        grantRef.current = { idx, values: [...liveRef.current.boundaries] };
      },
      onPanResponderMove: (_evt, gestureState) => {
        const { trackWidth } = liveRef.current;
        if (trackWidth <= 0 || grantRef.current.idx !== idx) return;
        const deltaPct = (gestureState.dx / trackWidth) * 100;
        const values = [...grantRef.current.values];
        const lower = idx > 0 ? values[idx - 1] : MIN_WEIGHT_PCT;
        const upper =
          idx < values.length - 1 ? values[idx + 1] : 100 - MIN_WEIGHT_PCT;
        values[idx] = clampPct(values[idx] + deltaPct, lower, upper);
        commitBoundaries(values);
      },
    });
    map.set(idx, responder);
    return responder;
  };

  return (
    <View>
      <View style={styles.weightLegendRow}>
        {enabled.technical && (
          <WeightLegendItem
            color={WEIGHT_COLORS.technical}
            label={labels.technical}
            pct={techPct}
          />
        )}
        {enabled.fundamental && (
          <WeightLegendItem
            color={WEIGHT_COLORS.fundamental}
            label={labels.fundamental}
            pct={fundPct}
          />
        )}
        {enabled.news && (
          <WeightLegendItem
            color={WEIGHT_COLORS.news}
            label={labels.news}
            pct={newsPct}
          />
        )}
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

        {trackWidth > 0 &&
          boundaries.map((pos, idx) => {
            const responder = getResponder(idx);
            return (
              <View
                key={idx}
                {...responder.panHandlers}
                style={[
                  styles.weightHandle,
                  { left: (pos / 100) * trackWidth - 14 },
                ]}
              >
                <View
                  style={[
                    styles.weightHandleKnob,
                    { borderColor: theme.background.bg },
                  ]}
                />
              </View>
            );
          })}
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
  const [weight, setWeight] = useState<WeightSelection>({
    ...DEFAULT_WEIGHT,
  });

  const PRESET_KEY = "ai_analysis_preset";
  const [hydrated, setHydrated] = useState(false);

  // Toast cảnh báo khi cố tắt data source cuối cùng còn lại.
  const [toastVisible, setToastVisible] = useState(false);
  const toastAnim = useRef(new Animated.Value(0)).current;
  const toastTimer = useRef<ReturnType<typeof setTimeout> | null>(null);

  const showToast = () => {
    if (toastTimer.current) clearTimeout(toastTimer.current);
    setToastVisible(true);
    Animated.timing(toastAnim, {
      toValue: 1,
      duration: 180,
      useNativeDriver: true,
    }).start();

    toastTimer.current = setTimeout(() => {
      Animated.timing(toastAnim, {
        toValue: 0,
        duration: 220,
        useNativeDriver: true,
      }).start(() => setToastVisible(false));
    }, 2200);
  };

  useEffect(() => {
    return () => {
      if (toastTimer.current) clearTimeout(toastTimer.current);
    };
  }, []);

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
    weight,
  ]);

  // Khi bật/tắt một data source, chia đều lại trọng số cho các source còn
  // đang bật (nguồn vừa tắt về 0%). Bỏ qua trước khi hydrate xong và bỏ qua
  // lần chạy đầu sau khi hydrate để không ghi đè trọng số vừa nạp từ preset.
  const prevEnabledKeyRef = useRef<string | null>(null);
  useEffect(() => {
    if (!hydrated) return;
    const key = `${technicalEnabled}-${fundamentalEnabled}-${newsEnabled}`;
    if (prevEnabledKeyRef.current === null) {
      prevEnabledKeyRef.current = key;
      return;
    }
    if (prevEnabledKeyRef.current === key) return;
    prevEnabledKeyRef.current = key;

    const activeKeys = SOURCE_ORDER.filter((k) =>
      k === "technical"
        ? technicalEnabled
        : k === "fundamental"
          ? fundamentalEnabled
          : newsEnabled,
    );
    setWeight(equalWeights(activeKeys));
  }, [hydrated, technicalEnabled, fundamentalEnabled, newsEnabled]);

  const technicalKeys = Object.keys(
    DEFAULT_TECHNICAL,
  ) as (keyof TechnicalSelection)[];

  const technicalCheckedCount = technicalKeys.filter(
    (k) => technical[k],
  ).length;

  // Technical cần ít nhất một chỉ báo; fundamental là toggle toàn nguồn.
  const sourceActive = {
    news: newsEnabled,
    technical: technicalEnabled && technicalCheckedCount > 0,
    fundamental: fundamentalEnabled,
  };

  // Có được phép tắt `source` không: chỉ chặn khi đây là nguồn active duy nhất.
  const canDisableSource = (source: keyof typeof sourceActive) =>
    (["news", "technical", "fundamental"] as const).some(
      (k) => k !== source && sourceActive[k],
    );

  // Bỏ hết checkbox thành phần thì tự động tắt toggle của section đó.
  useEffect(() => {
    if (technicalEnabled && technicalCheckedCount === 0) {
      setTechnicalEnabled(false);
    }
  }, [technicalEnabled, technicalCheckedCount]);

  const isValid =
    mode === "auto" ||
    newsEnabled ||
    (technicalEnabled && technicalCheckedCount > 0) ||
    fundamentalEnabled;

  const technicalLabels: Record<keyof TechnicalSelection, string> = {
    ma: t("aiAnalysis.ma"),
    boll: t("aiAnalysis.boll"),
    rsi: t("aiAnalysis.rsi"),
    macd: t("aiAnalysis.macd"),
    kdj: t("aiAnalysis.kdj"),
  };

  const handleAnalyze = () => {
    const params: { data: string; mode: string; dataSelection?: string } = {
      data: stockSymbol,
      mode,
    };

    if (mode === "manual") {
      const selection: DataSelection = {
        news: newsEnabled,
        technical: technicalEnabled
          ? { ...technical }
          : {
              ma: false,
              boll: false,
              rsi: false,
              macd: false,
              kdj: false,
            },
        fundamental: fundamentalEnabled,
        weight: { ...weight },
      };
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
              enabled={{
                technical: technicalEnabled,
                fundamental: fundamentalEnabled,
                news: newsEnabled,
              }}
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
              onToggle={(v) => {
                if (!v && !canDisableSource("news")) {
                  showToast();
                  return;
                }
                setNewsEnabled(v);
              }}
              theme={theme}
            />

            {/* Technical */}
            <SectionToggle
              label={t("aiAnalysis.technical")}
              enabled={technicalEnabled}
              checkedCount={technicalCheckedCount}
              totalCount={technicalKeys.length}
              onToggle={(v) => {
                if (!v && !canDisableSource("technical")) {
                  showToast();
                  return;
                }
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
                  onPress={() => {
                    const isLastChecked =
                      technical[key] && technicalCheckedCount === 1;
                    if (isLastChecked && !canDisableSource("technical")) {
                      showToast();
                      return;
                    }
                    setTechnical((prev) => ({ ...prev, [key]: !prev[key] }));
                  }}
                  theme={theme}
                />
              ))}

            <View style={{ height: 8 }} />

            {/* Fundamental */}
            <SectionToggle
              label={t("aiAnalysis.fundamental")}
              enabled={fundamentalEnabled}
              checkedCount={fundamentalEnabled ? 1 : 0}
              totalCount={1}
              onToggle={(v) => {
                if (!v && !canDisableSource("fundamental")) {
                  showToast();
                  return;
                }
                setFundamentalEnabled(v);
              }}
              theme={theme}
            />
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
        {toastVisible && (
          <Animated.View
            pointerEvents="none"
            style={{
              alignSelf: "center",
              flexDirection: "row",
              alignItems: "center",
              gap: 6,
              marginBottom: 10,
              paddingHorizontal: 16,
              paddingVertical: 8,
              borderRadius: 20,
              backgroundColor: theme.base.error,
              opacity: toastAnim,
              transform: [
                {
                  translateY: toastAnim.interpolate({
                    inputRange: [0, 1],
                    outputRange: [8, 0],
                  }),
                },
              ],
            }}
          >
            <Feather name="alert-triangle" size={16} color="#FFFFFF" />
            <Text typography="labelLarge" color="#FFFFFF">
              {t("aiAnalysis.selectAtLeastOne")}
            </Text>
          </Animated.View>
        )}

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
