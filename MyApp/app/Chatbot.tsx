import React, { useCallback, useMemo, useState } from "react";
import {
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
import { Text } from "@/components/ui/Text";
import { useSafeAreaInsets } from "react-native-safe-area-context";
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

const Chatbot = () => {
  const { theme } = useTheme();
  const { t } = useLocalization();
  const insets = useSafeAreaInsets();
  const [historyVisible, setHistoryVisible] = useState(false);
  const [suggestionsVisible, setSuggestionsVisible] = useState(false);
  const [conversations, setConversations] = useState<ChatConversation[]>([]);

  const fetchSessions = useCallback(async () => {
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

  /** Mở trang soạn câu hỏi đầu tiên. */
  const openCompose = () => router.push("/ChatCompose");

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
          marginTop: insets.top + 48,
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
          <Text typography="headlineMedium" color={theme.text.primary}>
            {t("chatbot.greeting")}
          </Text>
        </View>
      </View>

      <View
        style={{
          flex: 1,
          alignItems: "center",
          justifyContent: "center",
          paddingHorizontal: 48,
        }}
      >
        <Image
          source={{
            uri: "https://ddazflrupjwuxlxlszbk.supabase.co/storage/v1/object/public/icons/increase.png",
          }}
          style={{
            width: screenWidth * 0.45,
            height: screenWidth * 0.45, // Giữ tỷ lệ hình ảnh
            alignSelf: "center",
            marginBottom: 24,
            opacity: 0.7,
          }}
        />
        <Text
          typography="bodyMedium"
          color={theme.text.primary}
          style={{ textAlign: "center", opacity: 0.8 }}
        >
          <Text
            typography="bodyMedium"
            color={theme.text.primary}
            style={{ fontStyle: "italic" }}
          >
            {quote}
          </Text>{" "}
          <Text typography="bodyMedium" color={theme.text.primary}>
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
        <Text typography="titleMedium" color={theme.text.primary}>
          {t("chatbot.suggestions")}
        </Text>

        <TouchableOpacity onPress={() => setSuggestionsVisible(true)}>
          <Text typography="labelLarge" color={theme.text.primary}>
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
              padding: 16,
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
          onPress={openCompose}
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
        onClose={() => setHistoryVisible(false)}
        onSelectConversation={(conversation) => {
          setHistoryVisible(false);
          router.push({
            pathname: "/ChatDetail",
            params: { data: JSON.stringify(conversation) },
          });
        }}
        onDeleteConversation={handleDeleteConversation}
        onNewConversation={() => {
          router.push("/ChatCompose");
        }}
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
