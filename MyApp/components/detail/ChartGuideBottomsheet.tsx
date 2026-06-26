import React, { useEffect, useRef, useState } from "react";
import {
  Modal,
  Animated,
  Pressable,
  StyleSheet,
  TouchableOpacity,
  View,
  Dimensions,
  ScrollView,
} from "react-native";
import { useTheme } from "@/hooks/ThemeContext";
import { useLocalization } from "@/hooks/LocalizationContext";
import { MaterialCommunityIcons } from "@expo/vector-icons";
import { Text } from "../ui/Text";
import { useSafeAreaInsets } from "react-native-safe-area-context";

const { height: SCREEN_HEIGHT } = Dimensions.get("window");
const TOTAL_STEPS = 6;

interface Props {
  visible: boolean;
  onClose: () => void;
}

// ─────────────────────────────────────────────
// Candle — a single candlestick drawn with Views
// ─────────────────────────────────────────────
interface CandleProps {
  color: string;
  topWick?: number;
  body?: number;
  bottomWick?: number;
  width?: number;
  marginTop?: number;
}

const Candle = ({
  color,
  topWick = 12,
  body = 36,
  bottomWick = 12,
  width = 16,
  marginTop = 0,
}: CandleProps) => (
  <View style={{ alignItems: "center", marginTop }}>
    <View style={{ width: 2, height: topWick, backgroundColor: color }} />
    <View
      style={{ width, height: body, backgroundColor: color, borderRadius: 2 }}
    />
    <View style={{ width: 2, height: bottomWick, backgroundColor: color }} />
  </View>
);

const ChartGuideBottomSheet = ({ visible, onClose }: Props) => {
  const { theme } = useTheme();
  const { t } = useLocalization();

  const success = theme.base.success;
  const error = theme.base.error;

  const [step, setStep] = useState(0);
  const slideAnim = useRef(new Animated.Value(SCREEN_HEIGHT)).current;
  const backdropAnim = useRef(new Animated.Value(0)).current;
  const scrollRef = useRef<ScrollView>(null);

  // Step transition (content slides + fades in) and progress fill
  const contentAnim = useRef(new Animated.Value(0)).current; // 0 = settled
  const contentOpacity = useRef(new Animated.Value(1)).current;
  const direction = useRef<1 | -1>(1); // 1 = forward, -1 = backward
  const progressAnim = useRef(new Animated.Value(0)).current;

  // Reset to first step whenever the sheet is reopened
  useEffect(() => {
    if (visible) {
      setStep(0);
      direction.current = 1;
      contentAnim.setValue(0);
      contentOpacity.setValue(1);
      progressAnim.setValue(0);
    }
  }, [visible, contentAnim, contentOpacity, progressAnim]);

  // Animate the content in whenever the step changes
  useEffect(() => {
    contentAnim.setValue(direction.current * 36);
    contentOpacity.setValue(0);
    Animated.parallel([
      Animated.spring(contentAnim, {
        toValue: 0,
        useNativeDriver: true,
        bounciness: 2,
        speed: 14,
      }),
      Animated.timing(contentOpacity, {
        toValue: 1,
        duration: 220,
        useNativeDriver: true,
      }),
    ]).start();
  }, [step, contentAnim, contentOpacity]);

  // Animate the progress bar fill toward the current step
  useEffect(() => {
    Animated.timing(progressAnim, {
      toValue: step,
      duration: 320,
      useNativeDriver: false,
    }).start();
  }, [step, progressAnim]);

  const openSheet = () => {
    Animated.parallel([
      Animated.spring(slideAnim, {
        toValue: 0,
        useNativeDriver: true,
        bounciness: 4,
      }),
      Animated.timing(backdropAnim, {
        toValue: 1,
        duration: 250,
        useNativeDriver: true,
      }),
    ]).start();
  };

  const closeSheet = () => {
    Animated.parallel([
      Animated.timing(slideAnim, {
        toValue: SCREEN_HEIGHT,
        duration: 220,
        useNativeDriver: true,
      }),
      Animated.timing(backdropAnim, {
        toValue: 0,
        duration: 220,
        useNativeDriver: true,
      }),
    ]).start(onClose);
  };

  const goNext = () => {
    if (step >= TOTAL_STEPS - 1) {
      closeSheet();
      return;
    }
    direction.current = 1;
    setStep((s) => s + 1);
    scrollRef.current?.scrollTo({ y: 0, animated: false });
  };

  const goBack = () => {
    if (step <= 0) return;
    direction.current = -1;
    setStep((s) => s - 1);
    scrollRef.current?.scrollTo({ y: 0, animated: false });
  };

  // ── Small reusable text blocks ─────────────────────────────────────────
  const Para = ({ children }: { children: React.ReactNode }) => (
    <Text
      typography="bodyMedium"
      color={theme.text.primary}
      style={{ marginTop: 8, lineHeight: 21 }}
    >
      {children}
    </Text>
  );

  const Bullet = ({ children }: { children: React.ReactNode }) => (
    <View style={styles.bulletRow}>
      <Text
        typography="bodyMedium"
        color={theme.text.primary + "88"}
        style={{ marginRight: 6 }}
      >
        •
      </Text>
      <Text
        typography="bodyMedium"
        color={theme.text.primary}
        style={{ flex: 1, lineHeight: 21 }}
      >
        {children}
      </Text>
    </View>
  );

  const SectionLabel = ({ children }: { children: React.ReactNode }) => (
    <Text
      typography="titleSmall"
      color={theme.text.primary}
      style={{ marginTop: 14 }}
    >
      {children}
    </Text>
  );

  const Bold = ({ children }: { children: React.ReactNode }) => (
    <Text typography="labelLarge" color={theme.text.primary}>
      {children}
    </Text>
  );

  // ── Pattern card (used in steps 5 & 6) ─────────────────────────────────
  const PatternCard = ({
    name,
    illustration,
    children,
  }: {
    name: string;
    illustration: React.ReactNode;
    children: React.ReactNode;
  }) => (
    <View
      style={[
        styles.patternCard,
        {
          backgroundColor: theme.background.surface,
          borderColor: theme.border.default,
        },
      ]}
    >
      <Text typography="titleSmall" color={theme.text.primary}>
        {name}
      </Text>
      {children}
      <View style={styles.illustration}>{illustration}</View>
    </View>
  );

  const CaptionedGroup = ({
    caption,
    children,
  }: {
    caption: string;
    children: React.ReactNode;
  }) => (
    <View style={{ alignItems: "center", flex: 1 }}>
      <View
        style={{
          flexDirection: "row",
          alignItems: "flex-end",
          gap: 6,
          height: 84,
        }}
      >
        {children}
      </View>
      <Text
        typography="bodySmall"
        color={theme.text.primary + "88"}
        style={{ marginTop: 8, textAlign: "center" }}
      >
        {caption}
      </Text>
    </View>
  );

  const DisclaimerBox = () => (
    <View
      style={[
        styles.disclaimer,
        {
          backgroundColor: theme.base.primary + "12",
          borderColor: theme.base.primary + "40",
        },
      ]}
    >
      <MaterialCommunityIcons
        name="information-outline"
        size={18}
        color={theme.base.primary}
        style={{ marginRight: 8, marginTop: 1 }}
      />
      <Text
        typography="bodyMedium"
        color={theme.text.primary}
        style={{ flex: 1, lineHeight: 21 }}
      >
        {t("chartGuide.disclaimer")}
      </Text>
    </View>
  );

  // ── Step renderers ─────────────────────────────────────────────────────
  const renderStep1 = () => {
    // labelled candle + price-level labels stacked beside it
    const LabeledCandle = ({
      color,
      title,
      subtitle,
      topLabel,
      midLabel,
      bottomLabel,
    }: {
      color: string;
      title: string;
      subtitle: string;
      topLabel: string;
      midLabel: string;
      bottomLabel: string;
    }) => (
      <View
        style={[
          styles.candleCard,
          {
            backgroundColor: theme.background.surface,
            borderColor: theme.border.default,
          },
        ]}
      >
        <Text typography="labelLarge" color={theme.text.primary}>
          {title}
        </Text>
        <Text
          typography="bodySmall"
          color={theme.text.primary + "88"}
          style={{ marginTop: 2, marginBottom: 10 }}
        >
          {subtitle}
        </Text>
        <View style={{ flexDirection: "row", alignItems: "center", gap: 10 }}>
          <Candle color={color} topWick={22} body={48} bottomWick={22} />
          <View
            style={{ flex: 1, justifyContent: "space-between", height: 92 }}
          >
            <Text typography="bodySmall" color={theme.text.primary + "88"}>
              — {topLabel}
            </Text>
            <Text typography="bodySmall" color={theme.text.primary + "88"}>
              — {midLabel}
            </Text>
            <Text typography="bodySmall" color={theme.text.primary + "88"}>
              — {bottomLabel}
            </Text>
          </View>
        </View>
      </View>
    );

    return (
      <>
        <Text typography="titleMedium" color={theme.text.primary}>
          {t("chartGuide.structureTitle")}
        </Text>
        <View style={{ flexDirection: "row", gap: 10, marginTop: 14 }}>
          <View style={{ flex: 1 }}>
            <LabeledCandle
              color={success}
              title={t("chartGuide.bullTitle")}
              subtitle={t("chartGuide.bullSubtitle")}
              topLabel={t("chartGuide.high")}
              midLabel={t("chartGuide.close")}
              bottomLabel={t("chartGuide.low")}
            />
          </View>
          <View style={{ flex: 1 }}>
            <LabeledCandle
              color={error}
              title={t("chartGuide.bearTitle")}
              subtitle={t("chartGuide.bearSubtitle")}
              topLabel={t("chartGuide.high")}
              midLabel={t("chartGuide.open")}
              bottomLabel={t("chartGuide.low")}
            />
          </View>
        </View>

        <Text
          typography="labelLarge"
          color={theme.text.primary}
          style={{ marginTop: 18 }}
        >
          {t("chartGuide.structureIntro")}
        </Text>

        <Bullet>
          <Bold>{t("chartGuide.bodyLabel")} </Bold>
          {t("chartGuide.bodyDesc")}
        </Bullet>
        <Bullet>
          <Bold>{t("chartGuide.shadowLabel")} </Bold>
          {t("chartGuide.shadowDesc")}
        </Bullet>
        <Bullet>
          <Bold>{t("chartGuide.paramsLabel")}</Bold>
        </Bullet>
        <View style={{ marginLeft: 16 }}>
          <Bullet>{t("chartGuide.param1")}</Bullet>
          <Bullet>{t("chartGuide.param2")}</Bullet>
        </View>
      </>
    );
  };

  const renderStep2 = () => (
    <>
      <Text typography="titleMedium" color={theme.text.primary}>
        {t("chartGuide.candleChartTitle")}
      </Text>
      <Para>{t("chartGuide.candleChartDesc")}</Para>

      {/* Mini candlestick illustration */}
      <View
        style={[
          styles.illustration,
          {
            backgroundColor: theme.background.surface,
            borderRadius: 10,
            paddingVertical: 16,
            marginTop: 14,
          },
        ]}
      >
        <View style={{ flexDirection: "row", alignItems: "flex-end", gap: 5 }}>
          <Candle color={success} topWick={8} body={20} bottomWick={10} />
          <Candle color={error} topWick={6} body={26} bottomWick={6} />
          <Candle color={success} topWick={10} body={30} bottomWick={8} />
          <Candle color={success} topWick={14} body={44} bottomWick={6} />
          <Candle color={error} topWick={8} body={18} bottomWick={14} />
          <Candle color={success} topWick={12} body={34} bottomWick={8} />
          <Candle color={success} topWick={16} body={50} bottomWick={6} />
        </View>
      </View>

      <Bullet>{t("chartGuide.axisXItem")}</Bullet>
      <Bullet>{t("chartGuide.axisYItem")}</Bullet>
      <Bullet>{t("chartGuide.periodItem")}</Bullet>
    </>
  );

  const renderStep3 = () => {
    const bars = [
      { h: 30, up: true },
      { h: 18, up: false },
      { h: 12, up: true },
      { h: 22, up: false },
      { h: 40, up: true },
      { h: 28, up: true },
      { h: 16, up: false },
      { h: 48, up: false },
      { h: 34, up: true },
      { h: 20, up: false },
    ];
    return (
      <>
        <Text typography="titleMedium" color={theme.text.primary}>
          {t("chartGuide.volumeChartTitle")}
        </Text>
        <Para>{t("chartGuide.volumeChartDesc")}</Para>

        {/* Volume bars illustration */}
        <View
          style={[
            styles.illustration,
            {
              backgroundColor: theme.background.surface,
              borderRadius: 10,
              paddingVertical: 16,
              marginTop: 14,
            },
          ]}
        >
          <View
            style={{ flexDirection: "row", alignItems: "flex-end", gap: 6 }}
          >
            {bars.map((b, i) => (
              <View
                key={i}
                style={{
                  width: 12,
                  height: b.h,
                  borderRadius: 2,
                  backgroundColor: (b.up ? success : error) + "AA",
                }}
              />
            ))}
          </View>
        </View>

        <SectionLabel>{t("chartGuide.volumeWhatTitle")}</SectionLabel>
        <Para>{t("chartGuide.volumeWhatDesc")}</Para>

        <SectionLabel>{t("chartGuide.colorLabel")}</SectionLabel>
        <Bullet>{t("chartGuide.colorGreen")}</Bullet>
        <Bullet>{t("chartGuide.colorRed")}</Bullet>

        <SectionLabel>{t("chartGuide.heightLabel")}</SectionLabel>
        <Bullet>{t("chartGuide.heightDesc")}</Bullet>

        <SectionLabel>{t("chartGuide.trendTitle")}</SectionLabel>
        <Para>{t("chartGuide.trendDesc")}</Para>
        <Bullet>{t("chartGuide.trend1")}</Bullet>
        <Bullet>{t("chartGuide.trend2")}</Bullet>

        <SectionLabel>{t("chartGuide.moneyTitle")}</SectionLabel>
        <Para>{t("chartGuide.moneyDesc")}</Para>
        <Bullet>
          <Bold>{t("chartGuide.breakoutLabel")} </Bold>
          {t("chartGuide.breakoutDesc")}
        </Bullet>
        <Bullet>
          <Bold>{t("chartGuide.absorbLabel")} </Bold>
          {t("chartGuide.absorbDesc")}
        </Bullet>
      </>
    );
  };

  // Control row: icon chip + bold title + description (used in step 4)
  const ControlRow = ({
    icon,
    title,
    desc,
  }: {
    icon: React.ComponentProps<typeof MaterialCommunityIcons>["name"];
    title: string;
    desc: string;
  }) => (
    <View
      style={[
        styles.controlRow,
        {
          backgroundColor: theme.background.surface,
          borderColor: theme.border.default,
        },
      ]}
    >
      <View
        style={[
          styles.controlIcon,
          { backgroundColor: theme.base.primary + "1A" },
        ]}
      >
        <MaterialCommunityIcons
          name={icon}
          size={20}
          color={theme.base.primary}
        />
      </View>
      <View style={{ flex: 1 }}>
        <Text typography="labelLarge" color={theme.text.primary}>
          {title}
        </Text>
        <Text
          typography="bodyMedium"
          color={theme.text.primary + "88"}
          style={{ marginTop: 3, lineHeight: 20 }}
        >
          {desc}
        </Text>
      </View>
    </View>
  );

  const renderStep4 = () => (
    <>
      <Text typography="titleMedium" color={theme.text.primary}>
        {t("chartGuide.advancedTitle")}
      </Text>
      <Para>{t("chartGuide.advancedDesc")}</Para>

      <SectionLabel>{t("chartGuide.controlsTitle")}</SectionLabel>

      <View style={{ marginTop: 4 }}>
        <ControlRow
          icon="chart-line-variant"
          title={t("chartGuide.chartTypeTitle")}
          desc={t("chartGuide.chartTypeDesc")}
        />
        <ControlRow
          icon="clock-outline"
          title={t("chartGuide.intervalCtrlTitle")}
          desc={t("chartGuide.intervalCtrlDesc")}
        />
        <ControlRow
          icon="finance"
          title={t("chartGuide.indicatorCtrlTitle")}
          desc={t("chartGuide.indicatorCtrlDesc")}
        />
        <ControlRow
          icon="arrow-expand"
          title={t("chartGuide.expandCtrlTitle")}
          desc={t("chartGuide.expandCtrlDesc")}
        />
      </View>
    </>
  );

  const renderStep5 = () => (
    <>
      <Text typography="titleMedium" color={theme.text.primary}>
        {t("chartGuide.singleTitle")}
      </Text>
      <Para>{t("chartGuide.patternsSubtitle")}</Para>

      <PatternCard
        name={t("chartGuide.dojiName")}
        illustration={
          <View style={{ flexDirection: "row", gap: 18 }}>
            <Candle color={success} topWick={26} body={3} bottomWick={26} />
            <Candle color={error} topWick={26} body={3} bottomWick={26} />
          </View>
        }
      >
        <Bullet>
          <Bold>{t("chartGuide.feature")} </Bold>
          {t("chartGuide.dojiFeature")}
        </Bullet>
        <Bullet>
          <Bold>{t("chartGuide.meaning")} </Bold>
          {t("chartGuide.dojiMeaning")}
        </Bullet>
      </PatternCard>

      <PatternCard
        name={t("chartGuide.hammerName")}
        illustration={
          <View style={{ flexDirection: "row", gap: 18 }}>
            <Candle color={success} topWick={2} body={16} bottomWick={36} />
            <Candle color={error} topWick={2} body={16} bottomWick={36} />
          </View>
        }
      >
        <Bullet>
          <Bold>{t("chartGuide.feature")} </Bold>
          {t("chartGuide.hammerFeature")}
        </Bullet>
        <Bullet>
          <Bold>{t("chartGuide.meaning")} </Bold>
          {t("chartGuide.hammerMeaning")}
        </Bullet>
      </PatternCard>

      <PatternCard
        name={t("chartGuide.marubozuName")}
        illustration={
          <View style={{ flexDirection: "row", gap: 18 }}>
            <Candle
              color={success}
              topWick={0}
              body={56}
              bottomWick={0}
              width={18}
            />
            <Candle
              color={error}
              topWick={0}
              body={56}
              bottomWick={0}
              width={18}
            />
          </View>
        }
      >
        <Bullet>
          <Bold>{t("chartGuide.feature")} </Bold>
          {t("chartGuide.marubozuFeature")}
        </Bullet>
        <Bullet>
          <Bold>{t("chartGuide.meaning")} </Bold>
          {t("chartGuide.marubozuMeaning")}
        </Bullet>
      </PatternCard>

      <DisclaimerBox />
    </>
  );

  const renderStep6 = () => (
    <>
      <Text typography="titleMedium" color={theme.text.primary}>
        {t("chartGuide.clusterTitle")}
      </Text>
      <Para>{t("chartGuide.patternsSubtitle")}</Para>

      {/* Engulfing */}
      <PatternCard
        name={t("chartGuide.engulfingName")}
        illustration={
          <View style={{ flexDirection: "row", gap: 28 }}>
            <CaptionedGroup caption={t("chartGuide.engulfingBearLabel")}>
              <Candle color={success} topWick={8} body={28} bottomWick={8} />
              <Candle color={error} topWick={6} body={52} bottomWick={6} />
            </CaptionedGroup>
            <CaptionedGroup caption={t("chartGuide.engulfingBullLabel")}>
              <Candle color={error} topWick={8} body={28} bottomWick={8} />
              <Candle color={success} topWick={6} body={52} bottomWick={6} />
            </CaptionedGroup>
          </View>
        }
      >
        <Bullet>
          <Bold>{t("chartGuide.feature")} </Bold>
          {t("chartGuide.engulfingFeature")}
        </Bullet>
        <Bullet>
          <Bold>{t("chartGuide.meaning")} </Bold>
          {t("chartGuide.engulfingMeaning")}
        </Bullet>
      </PatternCard>

      {/* Morning / Evening Star */}
      <PatternCard
        name={t("chartGuide.starName")}
        illustration={
          <View style={{ flexDirection: "row", gap: 28 }}>
            <CaptionedGroup caption={t("chartGuide.morningStarLabel")}>
              <Candle color={error} topWick={6} body={40} bottomWick={6} />
              <Candle color={success} topWick={4} body={8} bottomWick={4} />
              <Candle color={success} topWick={6} body={40} bottomWick={6} />
            </CaptionedGroup>
            <CaptionedGroup caption={t("chartGuide.eveningStarLabel")}>
              <Candle color={success} topWick={6} body={40} bottomWick={6} />
              <Candle color={error} topWick={4} body={8} bottomWick={4} />
              <Candle color={error} topWick={6} body={40} bottomWick={6} />
            </CaptionedGroup>
          </View>
        }
      >
        <Bullet>
          <Bold>{t("chartGuide.starFeatureTitle")}</Bold>
        </Bullet>
        <View style={{ marginLeft: 16 }}>
          <Bullet>{t("chartGuide.star1")}</Bullet>
          <Bullet>{t("chartGuide.star2")}</Bullet>
          <Bullet>{t("chartGuide.star3")}</Bullet>
        </View>
        <Bullet>
          <Bold>{t("chartGuide.meaning")} </Bold>
          {t("chartGuide.starMeaning")}
        </Bullet>
      </PatternCard>

      {/* Three White Soldiers / Three Black Crows */}
      <PatternCard
        name={t("chartGuide.soldiersName")}
        illustration={
          <View style={{ flexDirection: "row", gap: 28 }}>
            <CaptionedGroup caption={t("chartGuide.soldiersLabel")}>
              <Candle
                color={success}
                topWick={4}
                body={26}
                bottomWick={4}
                marginTop={0}
              />
              <Candle
                color={success}
                topWick={4}
                body={26}
                bottomWick={4}
                marginTop={-14}
              />
              <Candle
                color={success}
                topWick={4}
                body={26}
                bottomWick={4}
                marginTop={-28}
              />
            </CaptionedGroup>
            <CaptionedGroup caption={t("chartGuide.crowsLabel")}>
              <Candle
                color={error}
                topWick={4}
                body={26}
                bottomWick={4}
                marginTop={-28}
              />
              <Candle
                color={error}
                topWick={4}
                body={26}
                bottomWick={4}
                marginTop={-14}
              />
              <Candle
                color={error}
                topWick={4}
                body={26}
                bottomWick={4}
                marginTop={0}
              />
            </CaptionedGroup>
          </View>
        }
      >
        <Bullet>
          <Bold>{t("chartGuide.soldiersFeatureTitle")}</Bold>
        </Bullet>
        <View style={{ marginLeft: 16 }}>
          <Bullet>{t("chartGuide.soldiersContinuity")}</Bullet>
          <Bullet>{t("chartGuide.soldiersOpen")}</Bullet>
          <Bullet>{t("chartGuide.soldiersClose")}</Bullet>
        </View>
        <Bullet>
          <Bold>{t("chartGuide.soldiersMeaningTitle")}</Bold>
        </Bullet>
        <View style={{ marginLeft: 16 }}>
          <Bullet>{t("chartGuide.soldiersDesc")}</Bullet>
          <Bullet>{t("chartGuide.crowsDesc")}</Bullet>
        </View>
      </PatternCard>

      <DisclaimerBox />
    </>
  );

  const stepRenderers = [
    renderStep1,
    renderStep2,
    renderStep3,
    renderStep4,
    renderStep5,
    renderStep6,
  ];

  const isLastStep = step === TOTAL_STEPS - 1;
  const isFirstStep = step === 0;
  const insets = useSafeAreaInsets();

  return (
    <Modal
      visible={visible}
      transparent
      animationType="none"
      onShow={openSheet}
    >
      {/* Backdrop */}
      <Animated.View
        style={[
          StyleSheet.absoluteFill,
          styles.backdrop,
          { opacity: backdropAnim },
        ]}
      >
        <Pressable style={StyleSheet.absoluteFill} onPress={closeSheet} />
      </Animated.View>

      {/* Sheet */}
      <Animated.View
        style={[
          styles.sheet,
          {
            backgroundColor: theme.background.bg,
            paddingBottom: insets.bottom,
          },
          { transform: [{ translateY: slideAnim }] },
        ]}
      >
        {/* Handle */}
        <View style={styles.handle} />

        {/* Header */}
        <View style={styles.header}>
          <View style={{ width: 24 }} />
          <Text typography="titleMedium" color={theme.text.primary}>
            {t("chartGuide.title")}
          </Text>
          <TouchableOpacity onPress={closeSheet} hitSlop={8}>
            <MaterialCommunityIcons
              name="close"
              size={22}
              color={theme.text.primary}
            />
          </TouchableOpacity>
        </View>

        {/* Progress segments */}
        <View style={styles.progressRow}>
          {Array.from({ length: TOTAL_STEPS }).map((_, i) => (
            <View
              key={i}
              style={{
                flex: 1,
                height: 4,
                borderRadius: 2,
                overflow: "hidden",
                backgroundColor: theme.background.surface,
              }}
            >
              <Animated.View
                style={{
                  height: "100%",
                  borderRadius: 2,
                  backgroundColor: theme.base.primary,
                  width: progressAnim.interpolate({
                    inputRange: [i - 1, i],
                    outputRange: ["0%", "100%"],
                    extrapolate: "clamp",
                  }),
                }}
              />
            </View>
          ))}
        </View>

        {/* Content */}
        <ScrollView
          ref={scrollRef}
          style={{ marginTop: 8 }}
          contentContainerStyle={{ paddingHorizontal: 16, paddingBottom: 16 }}
          showsVerticalScrollIndicator={false}
        >
          <Animated.View
            style={{
              opacity: contentOpacity,
              transform: [{ translateX: contentAnim }],
            }}
          >
            {stepRenderers[step]()}
          </Animated.View>
        </ScrollView>

        {/* Footer */}
        <View style={[styles.footer, { borderTopColor: theme.border.default }]}>
          <TouchableOpacity
            onPress={goBack}
            disabled={isFirstStep}
            style={[
              styles.footerBtn,
              {
                backgroundColor: isFirstStep
                  ? theme.text.primary + "88"
                  : theme.base.primary,
                opacity: isFirstStep ? 0.5 : 1,
              },
            ]}
          >
            <MaterialCommunityIcons
              name="chevron-left"
              size={18}
              color={theme.text.onPrimary}
            />
            <Text typography="titleMedium" color={theme.text.onPrimary}>
              {t("chartGuide.back")}
            </Text>
          </TouchableOpacity>

          <TouchableOpacity
            onPress={goNext}
            style={[
              styles.footerBtn,
              {
                backgroundColor: theme.base.primary,
              },
            ]}
          >
            <Text typography="titleMedium" color={theme.text.onPrimary}>
              {isLastStep ? t("chartGuide.done") : t("chartGuide.next")}
            </Text>
            {!isLastStep && (
              <MaterialCommunityIcons
                name="chevron-right"
                size={18}
                color={theme.text.onPrimary}
              />
            )}
          </TouchableOpacity>
        </View>
      </Animated.View>
    </Modal>
  );
};

const styles = StyleSheet.create({
  backdrop: {
    backgroundColor: "rgba(0,0,0,0.4)",
  },
  sheet: {
    position: "absolute",
    bottom: 0,
    left: 0,
    right: 0,
    height: SCREEN_HEIGHT * 0.82,
    borderTopLeftRadius: 16,
    borderTopRightRadius: 16,
    paddingTop: 12,
    elevation: 20,
    shadowColor: "#000",
    shadowOffset: { width: 0, height: -3 },
    shadowOpacity: 0.12,
    shadowRadius: 8,
  },
  handle: {
    width: 40,
    height: 4,
    borderRadius: 2,
    backgroundColor: "#d1d5db",
    alignSelf: "center",
    marginBottom: 12,
  },
  header: {
    flexDirection: "row",
    alignItems: "center",
    justifyContent: "space-between",
    paddingHorizontal: 16,
  },
  progressRow: {
    flexDirection: "row",
    gap: 6,
    paddingHorizontal: 16,
    marginTop: 16,
  },
  bulletRow: {
    flexDirection: "row",
    marginTop: 8,
  },
  candleCard: {
    borderRadius: 12,
    borderWidth: 1,
    padding: 12,
  },
  patternCard: {
    borderRadius: 12,
    borderWidth: 1,
    padding: 14,
    marginTop: 14,
  },
  controlRow: {
    flexDirection: "row",
    alignItems: "flex-start",
    gap: 12,
    borderRadius: 12,
    borderWidth: 1,
    padding: 12,
    marginTop: 10,
  },
  controlIcon: {
    width: 36,
    height: 36,
    borderRadius: 10,
    alignItems: "center",
    justifyContent: "center",
  },
  illustration: {
    alignItems: "center",
    justifyContent: "center",
    marginTop: 12,
  },
  disclaimer: {
    flexDirection: "row",
    borderRadius: 12,
    borderWidth: 1,
    padding: 12,
    marginTop: 16,
  },
  footer: {
    flexDirection: "row",
    gap: 10,
    paddingHorizontal: 16,
    paddingVertical: 12,
    borderTopWidth: StyleSheet.hairlineWidth,
  },
  footerBtn: {
    flex: 1,
    flexDirection: "row",
    paddingVertical: 12,
    borderRadius: 12,
    alignItems: "center",
    justifyContent: "center",
  },
});

export default ChartGuideBottomSheet;
