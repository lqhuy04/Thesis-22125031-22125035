import ScreenHeader from "@/components/ui/ScreenHeader";
import { useTheme } from "@/hooks/ThemeContext";
import { useLocalization } from "@/hooks/LocalizationContext";
import React, { useEffect, useMemo, useRef, useState } from "react";
import {
  ActivityIndicator,
  Animated,
  Dimensions,
  Image,
  ScrollView,
  StyleSheet,
  TouchableOpacity,
  View,
} from "react-native";
import Feather from "@expo/vector-icons/Feather";
import { router, useLocalSearchParams } from "expo-router";
import * as Crypto from "expo-crypto";
import { useSafeAreaInsets } from "react-native-safe-area-context";
import { Text } from "@/components/ui/Text";
import Octicons from "@expo/vector-icons/Octicons";
import LinearGradient from "react-native-linear-gradient";
import {
  AnalysisData,
  AnalysisMode,
  DataSelection,
  getAnalysis,
  seedChatSession,
} from "@/helpers/AgenticHelpers";
import type { ChatConversation } from "@/components/chatbot/ChatHistoryBottomsheet";
import { RadarChart, RadarAxis } from "@/components/ui/RadarChart";
import Markdown from "react-native-markdown-display";
import { typography } from "@/constants/typography";

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

// ─── Loading Indicator ───────────────────────────────────────────────────────

const LOADING_GIF = {
  uri: "https://ddazflrupjwuxlxlszbk.supabase.co/storage/v1/object/public/icons/stock-market.gif",
};

const AIAnalysisLoading = () => {
  const { theme } = useTheme();
  const { t } = useLocalization();
  return (
    <View style={styles.centered}>
      <View
        style={{
          width: 200,
          height: 200,
          borderRadius: 100,
          alignItems: "center",
          justifyContent: "center",
          backgroundColor: "#ffffff",
        }}
      >
        <Image source={LOADING_GIF} style={styles.loadingGif} />
      </View>
      <Text
        typography="titleLarge"
        color={theme.text.primary + "88"}
        style={{ marginTop: 16, textAlign: "center" }}
      >
        {t("aiAnalysis.analyzing")}
      </Text>
    </View>
  );
};

const AIAnalysis = () => {
  const { theme } = useTheme();
  const { t } = useLocalization();
  const insets = useSafeAreaInsets();

  const { data, mode, dataSelection } = useLocalSearchParams() || {};
  const stockSymbol = (data as string) ?? "";
  const analysisMode = ((mode as string) ?? "auto") as AnalysisMode;
  const dataSelectionStr = (dataSelection as string) ?? "";
  const parsedDataSelection = useMemo<DataSelection | undefined>(
    () => (dataSelectionStr ? JSON.parse(dataSelectionStr) : undefined),
    [dataSelectionStr],
  );

  const [analysis, setAnalysis] = useState<AnalysisData | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [selectedAxis, setSelectedAxis] = useState<number | null>(null);
  const [seeding, setSeeding] = useState(false);

  // Toast lỗi hiển thị phía trên nút CTA khi seed phiên chat thất bại.
  const [errorVisible, setErrorVisible] = useState(false);
  const errorAnim = useRef(new Animated.Value(0)).current;
  const errorTimer = useRef<ReturnType<typeof setTimeout> | null>(null);

  const showError = () => {
    if (errorTimer.current) clearTimeout(errorTimer.current);
    setErrorVisible(true);
    Animated.timing(errorAnim, {
      toValue: 1,
      duration: 180,
      useNativeDriver: true,
    }).start();

    errorTimer.current = setTimeout(() => {
      Animated.timing(errorAnim, {
        toValue: 0,
        duration: 220,
        useNativeDriver: true,
      }).start(() => setErrorVisible(false));
    }, 2200);
  };

  useEffect(() => {
    return () => {
      if (errorTimer.current) clearTimeout(errorTimer.current);
    };
  }, []);

  useEffect(() => {
    let mounted = true;
    setIsLoading(true);
    setAnalysis(null);

    getAnalysis(stockSymbol, analysisMode, parsedDataSelection)
      .then((res) => {
        if (mounted && res.status) setAnalysis(res.data);
      })
      .finally(() => {
        if (mounted) setIsLoading(false);
      });

    return () => {
      mounted = false;
    };
  }, [analysisMode, parsedDataSelection, stockSymbol]);

  const isBuy = analysis?.buy ?? false;
  const recommendationLabel = isBuy
    ? t("aiAnalysis.buy")
    : t("aiAnalysis.wait");

  const formatPrice = (value: number | null | undefined) =>
    value == null ? t("aiAnalysis.notAvailable") : value.toFixed(2);

  const formatStockScore = (value: number | null | undefined) =>
    `${Math.round(Math.min(Math.max(value ?? 0, 0), 1) * 100)}/100`;

  const formatPercentDiff = (
    value: number | null | undefined,
    entryPrice: number | null | undefined,
  ) => {
    if (value == null || entryPrice == null || entryPrice === 0) return null;
    const diff = ((value - entryPrice) / entryPrice) * 100;
    return `${diff >= 0 ? "+" : "-"}${Math.abs(diff).toFixed(2)}%`;
  };

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

  const analysisMarkdownStyle = {
    body: {
      ...typography.bodyMedium,
      color: theme.text.primary,
      lineHeight: 22,
    },
    strong: { fontFamily: typography.titleMedium.fontFamily },
    bullet_list: { marginVertical: 4 },
    ordered_list: { marginVertical: 4 },
    list_item: { marginVertical: 2 },
  };

  const summaryMarkdownStyle = {
    ...analysisMarkdownStyle,
    body: {
      ...typography.bodyLarge,
      color: theme.text.primary,
      lineHeight: 24,
    },
  };

  const handleAxisPress = (index: number) => {
    setSelectedAxis((prev) => (prev === index ? null : index));
  };

  // Dựng nội dung câu trả lời của trợ lý từ chính dữ liệu đang hiển thị, để nạp
  // sẵn vào phiên chat (Markdown — khớp cách ChatDetail render tin nhắn bot).
  const buildAssistantMessage = (a: AnalysisData): string => {
    const conf = `${(a.confidence * 100).toFixed(0)}%`;
    const decision = a.buy ? t("aiAnalysis.buy") : t("aiAnalysis.wait");
    return [
      `**${t("aiAnalysis.recommendation")}:** ${decision}`,
      `**${t("aiAnalysis.stockScore")}:** ${formatStockScore(a.score.total)} · ${t("aiAnalysis.confidence")} ${conf}`,
      ...(a.buy
        ? [
            "",
            `**${t("aiAnalysis.tradingPlan")}**`,
            `- ${t("aiAnalysis.entryPrice")}: ${formatPrice(a.entry_price)}`,
            `- ${t("aiAnalysis.takeProfit")}: ${formatPrice(a.take_profit_price)}`,
            `- ${t("aiAnalysis.stopLoss")}: ${formatPrice(a.stop_loss_price)}`,
            `- ${t("aiAnalysis.maxHoldCandles")}: ${formatPrice(a.max_hold_candles)}`,
          ]
        : []),
      "",
      `**${t("aiAnalysis.fundamental")}**`,
      a.analysis.fundamental,
      "",
      `**${t("aiAnalysis.technical")}**`,
      a.analysis.technical,
      "",
      `**${t("aiAnalysis.news")}**`,
      a.analysis.news,
      "",
      `**${t("aiAnalysis.analysis")}**`,
      a.analysis.summary,
    ].join("\n");
  };

  const handleAskMore = async () => {
    if (!analysis || seeding) return;
    setSeeding(true);

    const question = t("aiAnalysis.chatQuestion").replace(
      "{symbol}",
      stockSymbol,
    );
    const answer = buildAssistantMessage(analysis);
    const sessionId = Crypto.randomUUID();

    const { status } = await seedChatSession(sessionId, question, answer);
    setSeeding(false);
    if (!status) {
      showError();
      return;
    }

    const conversation: ChatConversation = {
      id: sessionId,
      title: question.slice(0, 60),
      timeLabel: t("chatbot.today"),
    };
    router.push({
      pathname: "/ChatDetail",
      params: { data: JSON.stringify(conversation) },
    });
  };

  return (
    <View style={{ flex: 1, backgroundColor: theme.background.surface }}>
      <ScreenHeader title={t("aiAnalysis.screenTitle")} />

      {isLoading ? (
        <AIAnalysisLoading />
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
            paddingBottom: insets.bottom + 96,
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
                  {recommendationLabel}
                </Text>
              </View>
            </View>

            {/* Stock score and confidence */}
            <View style={{ marginTop: 20 }}>
              <View style={[styles.rowBetween, { marginHorizontal: 12 }]}>
                <Text typography="bodyMedium" color="#FFFFFFCC">
                  {t("aiAnalysis.stockScore")}
                </Text>
                <Text typography="titleMedium" color="#FFFFFF">
                  {formatStockScore(analysis.score.total)}
                </Text>
              </View>

              <View
                style={[
                  styles.rowBetween,
                  { marginHorizontal: 12, marginTop: 12 },
                ]}
              >
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
          {isBuy && (
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
                  percent: null,
                },
                {
                  label: t("aiAnalysis.takeProfit"),
                  value: formatPrice(analysis.take_profit_price),
                  color: theme.base.success,
                  percent: formatPercentDiff(
                    analysis.take_profit_price,
                    analysis.entry_price,
                  ),
                },
                {
                  label: t("aiAnalysis.stopLoss"),
                  value: formatPrice(analysis.stop_loss_price),
                  color: theme.base.error,
                  percent: formatPercentDiff(
                    analysis.stop_loss_price,
                    analysis.entry_price,
                  ),
                },
                {
                  label: t("aiAnalysis.maxHoldCandles"),
                  value: formatPrice(analysis.max_hold_candles),
                  color: theme.text.primary,
                  percent: null,
                },
              ].map(({ label, value, color, percent }, i, arr) => (
                <React.Fragment key={label}>
                  <View style={styles.rowBetween}>
                    <Text
                      typography="bodyLarge"
                      color={theme.text.primary + "88"}
                    >
                      {label}
                    </Text>
                    <View style={{ flexDirection: "row", alignItems: "center" }}>
                      <Text typography="titleMedium" color={color}>
                        {value}{" "}
                      </Text>
                      {percent != null && (
                        <Text
                          typography="labelMedium"
                          color={color}
                          style={{ marginLeft: 6 }}
                        >
                          ({percent})
                        </Text>
                      )}
                    </View>
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
          )}

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
                  <Markdown style={analysisMarkdownStyle}>
                    {analysis.analysis[axisAnalysisKeys[selectedAxis]]}
                  </Markdown>
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
            <Markdown style={summaryMarkdownStyle}>
              {analysis.analysis.summary}
            </Markdown>
          </View>
        </ScrollView>
      )}

      {/* CTA cố định: mở phiên chat với lượt phân tích đã nạp sẵn */}
      {!isLoading && analysis != null && (
        <View
          style={[
            styles.ctaBar,
            {
              paddingBottom: insets.bottom + 12,
              backgroundColor: theme.background.surface,
              borderTopColor: theme.border.default,
            },
          ]}
        >
          {errorVisible && (
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
                opacity: errorAnim,
                transform: [
                  {
                    translateY: errorAnim.interpolate({
                      inputRange: [0, 1],
                      outputRange: [8, 0],
                    }),
                  },
                ],
              }}
            >
              <Feather name="alert-triangle" size={16} color="#FFFFFF" />
              <Text typography="labelLarge" color="#FFFFFF">
                {t("aiAnalysis.seedError")}
              </Text>
            </Animated.View>
          )}

          <TouchableOpacity
            activeOpacity={0.85}
            onPress={handleAskMore}
            disabled={seeding}
          >
            <LinearGradient
              colors={PURPLE_GRADIENT as unknown as string[]}
              start={{ x: 0, y: 0 }}
              end={{ x: 1, y: 0 }}
              style={styles.ctaButton}
            >
              {seeding ? (
                <ActivityIndicator color="#FFFFFF" />
              ) : (
                <>
                  <Octicons
                    name="dependabot"
                    size={20}
                    color="#FFFFFF"
                    style={{ marginRight: 8 }}
                  />
                  <Text typography="titleMedium" color="#FFFFFF">
                    {t("aiAnalysis.askMore")}
                  </Text>
                </>
              )}
            </LinearGradient>
          </TouchableOpacity>
        </View>
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
  loadingGif: {
    width: 160,
    height: 160,
    borderRadius: 80,
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
  ctaBar: {
    position: "absolute",
    left: 0,
    right: 0,
    bottom: 0,
    paddingHorizontal: 12,
    paddingTop: 12,
    borderTopWidth: 1,
  },
  ctaButton: {
    flexDirection: "row",
    alignItems: "center",
    justifyContent: "center",
    height: 52,
    borderRadius: 26,
  },
});

export default AIAnalysis;
