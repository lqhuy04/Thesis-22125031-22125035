import React, { useEffect, useRef, useState } from "react";
import {
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
import Feather from "@expo/vector-icons/Feather";
import ScreenHeader from "@/components/ui/ScreenHeader";
import { Text } from "@/components/ui/Text";
import { useTheme } from "@/hooks/ThemeContext";
import { typography } from "@/constants/typography";
import type { ChatConversation } from "@/components/chatbot/ChatHistoryBottomsheet";
import { getChatHistory, sendChatMessage } from "@/helpers/AgenticHelpers";

interface ChatMessage {
  id: string;
  role: "user" | "assistant";
  content: string;
  /** URL avatar/hình minh hoạ hiển thị kèm tin nhắn của trợ lý */
  image?: string;
}

const genId = () =>
  `${Date.now()}-${Math.random().toString(36).slice(2)}`;

const ChatDetail = () => {
  const { theme } = useTheme();

  const { data, initialMessage } = useLocalSearchParams() || {};
  const conversation = data
    ? (JSON.parse(data as string) as ChatConversation)
    : null;
  const sessionId = conversation?.id ?? null;
  const firstMessage =
    typeof initialMessage === "string" ? initialMessage : undefined;

  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [loading, setLoading] = useState(true);
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
            : "Xin lỗi, đã có lỗi khi gửi tin nhắn. Vui lòng thử lại.",
      },
    ]);
    setSending(false);
  };

  // Nạp lịch sử khi mở phiên; nếu là phiên mới có initialMessage thì gửi luôn.
  useEffect(() => {
    let active = true;

    const load = async () => {
      if (!sessionId) {
        setLoading(false);
        return;
      }
      const { data: history } = await getChatHistory(sessionId);
      if (!active) return;

      const mapped = history.map((m, index) => ({
        id: String(index),
        role: m.role,
        content: m.content,
      }));
      setMessages(mapped);
      setLoading(false);

      if (firstMessage && !sentInitial.current && mapped.length === 0) {
        sentInitial.current = true;
        send(firstMessage);
      }
    };

    load();
    return () => {
      active = false;
    };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [sessionId]);

  return (
    <KeyboardAvoidingView
      style={{ flex: 1, backgroundColor: theme.background.surface }}
      behavior={Platform.OS === "ios" ? "padding" : undefined}
    >
      <ScreenHeader title={conversation?.title ?? "Chi tiết trò chuyện"} />

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
                Hãy bắt đầu cuộc trò chuyện bằng một câu hỏi.
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
            <View style={{ marginVertical: 8, flexDirection: "row" }}>
              <ActivityIndicator size="small" color={theme.text.secondary} />
              <Text
                typography="bodyMedium"
                color={theme.text.secondary}
                style={{ marginLeft: 8 }}
              >
                Đang trả lời...
              </Text>
            </View>
          ) : null}
        </ScrollView>
      )}

      {/* Composer: nhập + gửi tin nhắn */}
      <View
        style={{
          flexDirection: "row",
          alignItems: "flex-end",
          paddingHorizontal: 12,
          paddingTop: 8,
          paddingBottom: 24,
          borderTopWidth: 1,
          borderTopColor: theme.border.default,
          backgroundColor: theme.background.bg,
        }}
      >
        <View
          style={{
            flex: 1,
            backgroundColor: theme.background.surface,
            borderRadius: 24,
            paddingHorizontal: 16,
            paddingVertical: 8,
            maxHeight: 120,
          }}
        >
          <TextInput
            style={{ color: theme.text.primary, ...typography.bodyLarge }}
            value={input}
            onChangeText={setInput}
            placeholder="Nhập tin nhắn..."
            placeholderTextColor={theme.text.secondary}
            multiline
            editable={!loading}
          />
        </View>

        <TouchableOpacity
          activeOpacity={0.8}
          disabled={!input.trim() || sending}
          onPress={() => send(input)}
          style={{
            width: 48,
            height: 48,
            borderRadius: 24,
            marginLeft: 8,
            alignItems: "center",
            justifyContent: "center",
            backgroundColor:
              !input.trim() || sending
                ? theme.text.secondary
                : theme.base.primary,
          }}
        >
          <Feather name="send" size={20} color={theme.text.onPrimary} />
        </TouchableOpacity>
      </View>
    </KeyboardAvoidingView>
  );
};

export default ChatDetail;
