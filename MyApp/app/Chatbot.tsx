import React, {
  useCallback,
  useEffect,
  useMemo,
  useRef,
  useState,
} from "react";
import {
  Animated,
  ScrollView,
  View,
  Image,
  Dimensions,
  TouchableOpacity,
} from "react-native";
import { useTheme } from "@/hooks/ThemeContext";
import { useLocalization } from "@/hooks/LocalizationContext";
import LinearGradient from "react-native-linear-gradient";
import { router } from "expo-router";
import * as Crypto from "expo-crypto";
import Feather from "@expo/vector-icons/Feather";
import Octicons from "@expo/vector-icons/Octicons";
import AntDesign from "@expo/vector-icons/AntDesign";
import { Text } from "@/components/ui/Text";
import { useSafeAreaInsets } from "react-native-safe-area-context";
import { getInvestingIdea, SuggestionItem } from "@/helpers/MarketHelpers";
import ChatHistoryBottomSheet, {
  type ChatConversation,
} from "@/components/chatbot/ChatHistoryBottomsheet";
import SuggestionsBottomSheet from "@/components/chatbot/SuggestionsBottomsheet";
import {
  getChatSessions,
  deleteChatSession,
  type ChatSession,
} from "@/helpers/AgenticHelpers";

/** Định dạng nhãn thời gian hiển thị cho lịch sử trò chuyện. */
const formatTimeLabel = (iso: string, t: (key: string) => string): string => {
  const date = new Date(iso);
  if (Number.isNaN(date.getTime())) return "";

  const now = new Date();
  const startOfDay = (d: Date) =>
    new Date(d.getFullYear(), d.getMonth(), d.getDate()).getTime();
  const diffDays = Math.round(
    (startOfDay(now) - startOfDay(date)) / 86_400_000,
  );

  if (diffDays === 0) return t("chatbot.today");
  if (diffDays === 1) return t("chatbot.yesterday");
  return `${String(date.getDate()).padStart(2, "0")} tháng ${String(
    date.getMonth() + 1,
  ).padStart(2, "0")}`;
};

/** Skeleton pill dùng khi chip phân tích nhanh chưa tải xong. */
const QuickChipSkeleton = ({ width, backgroundColor }: { width: number; backgroundColor: string }) => {
  const opacity = useRef(new Animated.Value(0.5)).current;

  useEffect(() => {
    const pulse = Animated.loop(
      Animated.sequence([
        Animated.timing(opacity, {
          toValue: 1,
          duration: 700,
          useNativeDriver: true,
        }),
        Animated.timing(opacity, {
          toValue: 0.5,
          duration: 700,
          useNativeDriver: true,
        }),
      ]),
    );
    pulse.start();
    return () => pulse.stop();
  }, [opacity]);

  return (
    <Animated.View
      style={{
        width,
        height: 32,
        borderRadius: 16,
        backgroundColor,
        opacity,
        marginRight: 12,
      }}
    />
  );
};

const Chatbot = () => {
  const { theme } = useTheme();
  const { t } = useLocalization();
  const insets = useSafeAreaInsets();
  const [historyVisible, setHistoryVisible] = useState(false);
  const [suggestionsVisible, setSuggestionsVisible] = useState(false);
  const [conversations, setConversations] = useState<ChatConversation[]>([]);
  const [historyLoading, setHistoryLoading] = useState(false);

  /** Các chip phân tích nhanh: top 3 mã tăng + top 3 mã giảm. */
  const [quickChips, setQuickChips] = useState<
    { symbol: string; isUp: boolean }[]
  >([]);
  const [quickChipsLoading, setQuickChipsLoading] = useState(true);

  useEffect(() => {
    let mounted = true;
    Promise.all([
      getInvestingIdea("top_gainers", 3),
      getInvestingIdea("top_decliners", 3),
    ])
      .then(([gainersRes, declinersRes]) => {
        if (!mounted) return;
        const gainers = (gainersRes?.data ?? []).slice(0, 3);
        const decliners = (declinersRes?.data ?? []).slice(0, 3);
        setQuickChips([
          ...gainers.map((s: SuggestionItem) => ({
            symbol: s.symbol,
            isUp: true,
          })),
          ...decliners.map((s: SuggestionItem) => ({
            symbol: s.symbol,
            isUp: false,
          })),
        ]);
      })
      .finally(() => {
        if (mounted) setQuickChipsLoading(false);
      });
    return () => {
      mounted = false;
    };
  }, []);

  const fetchSessions = useCallback(async () => {
    setHistoryLoading(true);
    try {
      const { status, data } = await getChatSessions();
      if (status) {
        setConversations(
          data.map((s: ChatSession) => ({
            id: s.session_id,
            title: s.title || t("chatbot.newConversation"),
            timeLabel: formatTimeLabel(s.updated_at, t),
          })),
        );
      }
    } finally {
      setHistoryLoading(false);
    }
  }, [t]);

  const openHistory = () => {
    setHistoryVisible(true);
    fetchSessions();
  };

  const handleDeleteConversation = async (conversation: ChatConversation) => {
    const { status } = await deleteChatSession(conversation.id);
    if (status) {
      setConversations((prev) => prev.filter((c) => c.id !== conversation.id));
    }
  };

  /** Tạo phiên mới (UUID) và điều hướng sang ChatDetail, gửi luôn tin đầu tiên. */
  const startNewConversation = (text: string) => {
    const message = text.trim();
    if (!message) return;

    const sessionId = Crypto.randomUUID();
    const conversation: ChatConversation = {
      id: sessionId,
      title: message.slice(0, 60),
      timeLabel: t("chatbot.today"),
    };

    router.push({
      pathname: "/ChatDetail",
      params: {
        data: JSON.stringify(conversation),
        initialMessage: message,
      },
    });
  };

  /** Mở trang soạn câu hỏi đầu tiên. `fromBts`: mở từ bottom sheet lịch sử. */
  const openCompose = (fromBts = false) =>
    router.push({
      pathname: "/ChatCompose",
      params: fromBts ? { fromBts: "1" } : {},
    });

  const exampleMessages = useMemo(
    () => [
      t("chatbot.example1"),
      t("chatbot.example2"),
      t("chatbot.example3"),
      t("chatbot.example4"),
      t("chatbot.example5"),
      t("chatbot.example6"),
    ],
    [t],
  );

  const quotes = useMemo(
    () => [
      `"Don't look for the needle in the haystack. Just buy the haystack!" — John Bogle`,
      `"Given a ten percent chance of a 100 times payoff, you should take that bet every time." — Jeff Bezos`,
      `"The stock market is filled with individuals who know the price of everything, but the value of nothing." — Phillip Fisher`,
      `"In investing, what is comfortable is rarely profitable." — Robert Arnott`,
      `"Courage taught me no matter how bad a crisis gets any sound investment will eventually pay off." — Carlos Slim Helú`,
      `"The individual investor should act consistently as an investor and not as a speculator." — Ben Graham`,
      `"Know what you own, and know why you own it." — Peter Lynch`,
      `“Invest for the long haul. Don’t get too greedy and don’t get too scared.” — Shelby M.C. Davis`,
      `“The stock market is a device to transfer money from the impatient to the patient.” — Warren Buffett`,
      `“The function of economic forecasting is to make astrology look respectable.” — John Kenneth Galbraith`,
    ],
    [],
  );

  const getRandomQuote = (): { quote: string; author: string } => {
    const raw = quotes[Math.floor(Math.random() * quotes.length)];
    const parts = raw.split(" — ");
    return {
      quote: parts[0], // "Don't look for the needle..."
      author: `— ${parts[1]}`, // — John Bogle
    };
  };
  const { quote, author } = getRandomQuote();

  const screenWidth = Dimensions.get("window").width;

  return (
    <LinearGradient
      colors={["#5B21B6", "#7C3AED", "#A78BFA", "#E9D5FF"]}
      locations={[0, 0.2, 0.6, 1]}
      useAngle
      angle={135}
      angleCenter={{ x: 0.5, y: 0.5 }}
      style={{ flex: 1 }}
    >
      {/* Vùng chat chiếm hết không gian còn lại */}

      <View
        style={{
          flexDirection: "row",
          alignItems: "center",
          marginHorizontal: 12,
          marginTop: insets.top + 24,
          marginBottom: 12,
        }}
      >
        <View
          style={{
            width: 48,
            height: 48,
            backgroundColor: theme.background.bg,
            borderRadius: 24,
            alignItems: "center",
            justifyContent: "center",
            marginRight: 12,
          }}
        >
          <Octicons name="dependabot" size={32} color={theme.text.primary} />
        </View>
        <View
          style={{
            flex: 1,
          }}
        >
          <Text typography="headlineMedium" color={theme.text.onPrimary}>
            {t("chatbot.greeting")}
          </Text>
        </View>
      </View>

      {/* ── Phân tích nhanh ── */}
      {(quickChipsLoading || quickChips.length > 0) && (
        <View>
          <View
            style={{
              flexDirection: "row",
              alignItems: "center",
              marginHorizontal: 12,
              justifyContent: "space-between",
              marginVertical: 12,
            }}
          >
            <Text typography="titleMedium" color={theme.text.onPrimary}>
              {t("chatbot.quickAnalysis")}
            </Text>

            <TouchableOpacity onPress={() => router.push("/InvestmentIdeas")}>
              <Text typography="labelLarge" color={theme.text.onPrimary}>
                {t("chatbot.viewMore")}
              </Text>
            </TouchableOpacity>
          </View>

          <ScrollView
            horizontal
            showsHorizontalScrollIndicator={false}
            style={{ marginLeft: 12 }}
          >
            {quickChipsLoading
              ? [88, 96, 84, 100, 92].map((width, index) => (
                  <QuickChipSkeleton
                    key={index}
                    width={width}
                    backgroundColor={theme.background.bg}
                  />
                ))
              : quickChips.map((chip) => (
                  <TouchableOpacity
                    key={`${chip.symbol}-${chip.isUp ? "up" : "down"}`}
                    activeOpacity={0.8}
                    onPress={() =>
                      router.push({
                        pathname: "/AIAnalysis",
                        params: { data: chip.symbol, mode: "auto" },
                      })
                    }
                    style={{
                      flexDirection: "row",
                      alignItems: "center",
                      gap: 6,
                      marginRight: 12,
                      borderRadius: 16,
                      backgroundColor: theme.background.bg,
                      paddingVertical: 4,
                      paddingHorizontal: 16,
                    }}
                  >
                    <Text typography="labelLarge" color={theme.text.primary}>
                      {chip.symbol}
                    </Text>
                    <AntDesign
                      name={chip.isUp ? "rise" : "fall"}
                      size={16}
                      color={chip.isUp ? theme.base.success : theme.base.error}
                    />
                  </TouchableOpacity>
                ))}
          </ScrollView>
        </View>
      )}

      <View
        style={{
          flex: 1,
          alignItems: "center",
          justifyContent: "center",
          paddingHorizontal: 48,
          opacity: 0.8,
        }}
      >
        <Image
          source={{
            uri: "https://ddazflrupjwuxlxlszbk.supabase.co/storage/v1/object/public/icons/increase.png",
          }}
          style={{
            width: screenWidth * 0.38,
            height: screenWidth * 0.38, // Giữ tỷ lệ hình ảnh
            alignSelf: "center",
            marginBottom: 24,
            opacity: 0.7,
          }}
        />
        <Text
          typography="bodyMedium"
          color={theme.text.onPrimary}
          style={{ textAlign: "center", opacity: 0.8 }}
        >
          <Text
            typography="bodyMedium"
            color={theme.text.onPrimary}
            style={{ fontStyle: "italic" }}
          >
            {quote}
          </Text>{" "}
          <Text typography="bodyMedium" color={theme.text.onPrimary}>
            {author}
          </Text>
        </Text>
      </View>

      <View
        style={{
          flexDirection: "row",
          alignItems: "center",
          marginHorizontal: 12,
          justifyContent: "space-between",
          marginBottom: 12,
        }}
      >
        <Text typography="titleMedium" color={theme.text.onPrimary}>
          {t("chatbot.suggestions")}
        </Text>

        <TouchableOpacity onPress={() => setSuggestionsVisible(true)}>
          <Text typography="labelLarge" color={theme.text.onPrimary}>
            {t("chatbot.viewMore")}
          </Text>
        </TouchableOpacity>
      </View>

      <ScrollView
        horizontal
        showsHorizontalScrollIndicator={false}
        style={{
          flexDirection: "row",
          paddingLeft: 12,
          marginBottom: 36,
          maxHeight: 128,
        }}
      >
        {exampleMessages.map((msg, index) => (
          <TouchableOpacity
            key={index.toString()}
            activeOpacity={0.7}
            onPress={() => startNewConversation(msg)}
            style={{
              borderTopLeftRadius: 16,
              borderBottomLeftRadius: 16,
              borderTopRightRadius: 16,
              borderBottomRightRadius: 4,
              backgroundColor: theme.background.bg,
              padding: 12,
              width: 128,
              height: 128,
              marginRight: 12,
            }}
          >
            <Text
              typography="bodyLarge"
              color={theme.text.primary}
              numberOfLines={4}
            >
              {msg}
            </Text>
          </TouchableOpacity>
        ))}
      </ScrollView>

      <View
        style={{
          flexDirection: "row",
          alignItems: "center",
          marginBottom: 24,
          paddingHorizontal: 12,
        }}
      >
        <TouchableOpacity
          onPress={openHistory}
          style={{
            width: 56,
            height: 56,
            backgroundColor: theme.background.bg,
            borderRadius: 28,
            borderWidth: 4,
            borderColor: theme.background.surface,
            alignItems: "center",
            justifyContent: "center",
          }}
        >
          <Feather name="menu" size={24} color={theme.text.primary} />
        </TouchableOpacity>

        <TouchableOpacity
          activeOpacity={0.8}
          onPress={() => openCompose()}
          style={{
            height: 56,
            backgroundColor: theme.background.bg,
            borderRadius: 28,
            marginLeft: 12,
            flex: 1,
            borderWidth: 4,
            borderColor: theme.background.surface,
            flexDirection: "row",
            alignItems: "center",
            paddingLeft: 12,
            paddingRight: 16,
          }}
        >
          <Octicons
            name="sparkles-fill"
            size={16}
            color={theme.text.primary}
            style={{ marginRight: 8 }}
          />
          <Text
            typography="bodyLarge"
            color={theme.text.primary + "88"}
            style={{ flex: 1 }}
          >
            {t("chatbot.placeholder")}
          </Text>
        </TouchableOpacity>
      </View>

      <ChatHistoryBottomSheet
        visible={historyVisible}
        conversations={conversations}
        loading={historyLoading}
        onClose={() => setHistoryVisible(false)}
        onSelectConversation={(conversation) => {
          setHistoryVisible(false);
          router.push({
            pathname: "/ChatDetail",
            params: { data: JSON.stringify(conversation), fromBts: "1" },
          });
        }}
        onDeleteConversation={handleDeleteConversation}
        onNewConversation={() => openCompose(true)}
      />

      <SuggestionsBottomSheet
        visible={suggestionsVisible}
        onClose={() => setSuggestionsVisible(false)}
        onSelectQuestion={(question) => {
          setSuggestionsVisible(false);
          startNewConversation(question);
        }}
      />
    </LinearGradient>
  );
};

export default Chatbot;
