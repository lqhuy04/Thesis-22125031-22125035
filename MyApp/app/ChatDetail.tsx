import React, { useEffect, useRef, useState } from "react";
import {
  Animated,
  ScrollView,
  View,
  Image,
  TouchableOpacity,
  ActivityIndicator,
  TextInput,
  KeyboardAvoidingView,
  Platform,
} from "react-native";
import { useLocalSearchParams } from "expo-router";
import Markdown from "react-native-markdown-display";
import LinearGradient from "react-native-linear-gradient";
import Feather from "@expo/vector-icons/Feather";
import ScreenHeader from "@/components/ui/ScreenHeader";
import { Text } from "@/components/ui/Text";
import { useTheme } from "@/hooks/ThemeContext";
import { useLocalization } from "@/hooks/LocalizationContext";
import { typography } from "@/constants/typography";
import type { ChatConversation } from "@/components/chatbot/ChatHistoryBottomsheet";
import { getChatHistory, sendChatMessage } from "@/helpers/AgenticHelpers";
import Octicons from "@expo/vector-icons/Octicons";

interface ChatMessage {
  id: string;
  role: "user" | "assistant";
  content: string;
  /** URL avatar/hình minh hoạ hiển thị kèm tin nhắn của trợ lý */
  image?: string;
}

const genId = () => `${Date.now()}-${Math.random().toString(36).slice(2)}`;

const TypingIndicator = ({ color }: { color: string }) => {
  const dot1 = useRef(new Animated.Value(0.3)).current;
  const dot2 = useRef(new Animated.Value(0.3)).current;
  const dot3 = useRef(new Animated.Value(0.3)).current;

  useEffect(() => {
    const anim = Animated.loop(
      Animated.sequence([
        Animated.timing(dot1, { toValue: 1, duration: 350, useNativeDriver: true }),
        Animated.timing(dot2, { toValue: 1, duration: 350, useNativeDriver: true }),
        Animated.timing(dot3, { toValue: 1, duration: 350, useNativeDriver: true }),
        Animated.delay(300),
        Animated.parallel([
          Animated.timing(dot1, { toValue: 0.3, duration: 200, useNativeDriver: true }),
          Animated.timing(dot2, { toValue: 0.3, duration: 200, useNativeDriver: true }),
          Animated.timing(dot3, { toValue: 0.3, duration: 200, useNativeDriver: true }),
        ]),
      ]),
    );
    anim.start();
    return () => anim.stop();
  }, [dot1, dot2, dot3]);

  return (
    <View style={{ flexDirection: "row", alignItems: "center", gap: 4 }}>
      {([dot1, dot2, dot3] as Animated.Value[]).map((opacity, i) => (
        <Animated.View
          key={i}
          style={{
            width: 7,
            height: 7,
            borderRadius: 3.5,
            backgroundColor: color,
            opacity,
          }}
        />
      ))}
    </View>
  );
};

const ChatDetail = () => {
  const { theme } = useTheme();
  const { t } = useLocalization();

  const { data, initialMessage } = useLocalSearchParams() || {};
  const conversation = data
    ? (JSON.parse(data as string) as ChatConversation)
    : null;
  const sessionId = conversation?.id ?? null;
  const firstMessage =
    typeof initialMessage === "string" ? initialMessage : undefined;

  const [messages, setMessages] = useState<ChatMessage[]>([]);
  // Skip loading spinner for brand-new sessions — history doesn't exist yet
  const [loading, setLoading] = useState(!firstMessage);
  const [input, setInput] = useState("");
  const [sending, setSending] = useState(false);

  const scrollRef = useRef<ScrollView>(null);
  const sentInitial = useRef(false);

  const send = async (text: string) => {
    const trimmed = text.trim();
    if (!trimmed || !sessionId || sending) return;

    setInput("");
    setMessages((prev) => [
      ...prev,
      { id: genId(), role: "user", content: trimmed },
    ]);
    setSending(true);

    const { status, data: reply } = await sendChatMessage(sessionId, trimmed);

    setMessages((prev) => [
      ...prev,
      {
        id: genId(),
        role: "assistant",
        content:
          status && reply
            ? reply.reply
            : t("chatbot.errorMessage"),
      },
    ]);
    setSending(false);
  };

  useEffect(() => {
    let active = true;

    const load = async () => {
      if (!sessionId) {
        setLoading(false);
        return;
      }

      // Brand-new session: skip history fetch (session doesn't exist in DB yet)
      if (firstMessage) {
        if (!sentInitial.current) {
          sentInitial.current = true;
          send(firstMessage);
        }
        return;
      }

      // Existing session: fetch history then reveal UI
      const { data: history } = await getChatHistory(sessionId);
      if (!active) return;

      setMessages(
        history.map((m, index) => ({
          id: String(index),
          role: m.role,
          content: m.content,
        })),
      );
      setLoading(false);
    };

    load();
    return () => {
      active = false;
    };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [sessionId]);

  return (
    <LinearGradient
      colors={["#5B21B6", "#7C3AED", "#A78BFA", "#E9D5FF"]}
      locations={[0, 0.2, 0.6, 1]}
      useAngle
      angle={135}
      angleCenter={{ x: 0.5, y: 0.5 }}
      style={{ flex: 1 }}
    >
      <KeyboardAvoidingView
        style={{ flex: 1 }}
        behavior={Platform.OS === "ios" ? "padding" : undefined}
      >
      <ScreenHeader title={conversation?.title ?? t("chatbot.chatTitle")} />

      {loading ? (
        <View
          style={{ flex: 1, alignItems: "center", justifyContent: "center" }}
        >
          <ActivityIndicator size="large" color={theme.base.primary} />
        </View>
      ) : (
        <ScrollView
          ref={scrollRef}
          style={{ flex: 1 }}
          contentContainerStyle={{ padding: 16, paddingBottom: 24 }}
          showsVerticalScrollIndicator={false}
          onContentSizeChange={() =>
            scrollRef.current?.scrollToEnd({ animated: true })
          }
        >
          {messages.length === 0 ? (
            <View style={{ paddingTop: 48, alignItems: "center" }}>
              <Text
                typography="bodyLarge"
                color={theme.text.secondary}
                style={{ textAlign: "center" }}
              >
                {t("chatbot.emptyMessage")}
              </Text>
            </View>
          ) : (
            messages.map((msg) =>
              msg.role === "user" ? (
                <View
                  key={msg.id}
                  style={{
                    alignSelf: "flex-end",
                    maxWidth: "82%",
                    backgroundColor: theme.base.primary,
                    borderTopLeftRadius: 16,
                    borderTopRightRadius: 16,
                    borderBottomLeftRadius: 16,
                    borderBottomRightRadius: 4,
                    paddingHorizontal: 16,
                    paddingVertical: 12,
                    marginVertical: 8,
                  }}
                >
                  <Text typography="bodyLarge" color={theme.text.onPrimary}>
                    {msg.content}
                  </Text>
                </View>
              ) : (
                <View key={msg.id} style={{ marginVertical: 8 }}>
                  <Markdown
                    style={{
                      body: {
                        ...typography.bodyLarge,
                        color: theme.text.primary,
                      },
                      strong: {
                        fontFamily: typography.titleMedium.fontFamily,
                      },
                      bullet_list: { marginVertical: 4 },
                      list_item: { marginVertical: 2 },
                    }}
                  >
                    {msg.content}
                  </Markdown>

                  {msg.image ? (
                    <Image
                      source={{ uri: msg.image }}
                      style={{
                        width: 160,
                        height: 160,
                        alignSelf: "center",
                        marginTop: 12,
                        opacity: 0.85,
                      }}
                      resizeMode="contain"
                    />
                  ) : null}
                </View>
              ),
            )
          )}

          {sending ? (
            <View
              style={{
                marginVertical: 8,
                flexDirection: "row",
                alignItems: "center",
              }}
            >
              <View
                style={{
                  width: 36,
                  height: 36,
                  backgroundColor: theme.background.bg,
                  borderRadius: 18,
                  alignItems: "center",
                  justifyContent: "center",
                  marginRight: 10,
                }}
              >
                <Octicons
                  name="dependabot"
                  size={22}
                  color={theme.text.primary}
                />
              </View>
              <TypingIndicator color={theme.text.primary} />
            </View>
          ) : null}
        </ScrollView>
      )}

      {/* Composer: nhập + gửi tin nhắn */}
      <View
        style={{
          flexDirection: "row",
          alignItems: "center",
          marginBottom: 24,
          paddingHorizontal: 12,
        }}
      >
        <View
          style={{
            minHeight: 56,
            backgroundColor: theme.background.bg,
            borderRadius: 28,
            flex: 1,
            borderWidth: 4,
            borderColor: theme.background.surface,
            flexDirection: "row",
            alignItems: "center",
            paddingLeft: 12,
            paddingRight: 4,
          }}
        >
          <Octicons
            name="sparkles-fill"
            size={16}
            color={theme.text.primary}
            style={{ marginRight: 8 }}
          />
          <TextInput
            style={{
              paddingVertical: 10,
              flex: 1,
              color: theme.text.primary,
              backgroundColor: theme.background.bg,
            }}
            value={input}
            onChangeText={setInput}
            autoCapitalize="none"
            autoFocus
            multiline
            returnKeyType="send"
            placeholder={t("chatbot.placeholder")}
            placeholderTextColor={theme.text.primary + "88"}
          />
          <TouchableOpacity
            activeOpacity={0.8}
            disabled={!input.trim()}
            onPress={() => send(input)}
            style={{
              width: 40,
              height: 40,
              borderRadius: 20,
              alignItems: "center",
              justifyContent: "center",
              backgroundColor: input.trim()
                ? theme.base.primary
                : theme.background.surface,
            }}
          >
            <Feather name="send" size={18} color={theme.text.onPrimary} />
          </TouchableOpacity>
        </View>
      </View>
      </KeyboardAvoidingView>
    </LinearGradient>
  );
};

export default ChatDetail;
