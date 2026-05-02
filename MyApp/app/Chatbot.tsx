import React, { useState, useRef, useCallback } from "react";
import {
  View,
  ScrollView,
  TextInput,
  TouchableOpacity,
  KeyboardAvoidingView,
  Platform,
  ActivityIndicator,
} from "react-native";
import { SafeAreaView } from "react-native-safe-area-context";
import { Ionicons } from "@expo/vector-icons";
import { router } from "expo-router";
import uuid from "react-native-uuid";
import Markdown from "react-native-markdown-display";

import { useTheme } from "@/hooks/ThemeContext";
import { Text } from "@/components/ui/Text";
import { sendChatMessage } from "@/helpers/AgenticHelpers";

// ─── Types ────────────────────────────────────────────────────────────────────

type MessageRole = "user" | "assistant";

interface Message {
  id: string;
  role: MessageRole;
  content: string;
  timestamp: Date;
}

// ─── Sub-components ───────────────────────────────────────────────────────────

const UserBubble = ({ message, theme }: { message: Message; theme: any }) => (
  <View style={{ alignItems: "flex-end", marginBottom: 12 }}>
    <View
      style={{
        backgroundColor: theme.base.primary,
        borderRadius: 16,
        borderBottomRightRadius: 4,
        paddingHorizontal: 14,
        paddingVertical: 10,
        maxWidth: "78%",
      }}
    >
      <Text typography="bodyMedium" color={theme.text.onPrimary}>
        {message.content}
      </Text>
    </View>
    <Text
      typography="labelSmall"
      color={theme.text.secondary}
      style={{ marginTop: 4, marginRight: 4 }}
    >
      {formatTime(message.timestamp)}
    </Text>
  </View>
);

const AssistantBubble = ({
  message,
  theme,
}: {
  message: Message;
  theme: any;
}) => (
  <View style={{ alignItems: "flex-start", marginBottom: 12 }}>
    <View style={{ flexDirection: "row", alignItems: "flex-end", gap: 8 }}>
      {/* Avatar */}
      <View
        style={{
          width: 28,
          height: 28,
          borderRadius: 14,
          backgroundColor: theme.base.primary,
          alignItems: "center",
          justifyContent: "center",
          marginBottom: 18,
        }}
      >
        <Ionicons name="bar-chart-outline" size={14} color="#fff" />
      </View>

      <View style={{ flex: 1 }}>
        <View
          style={{
            backgroundColor: theme.background.surface,
            borderRadius: 16,
            borderBottomLeftRadius: 4,
            paddingHorizontal: 14,
            paddingVertical: 10,
            maxWidth: "100%",
            borderWidth: 1,
            borderColor: theme.border.default,
          }}
        >
          <Markdown
            style={{
              body: {
                color: theme.text.primary,
                fontSize: 14,
                lineHeight: 20,
              },
              strong: {
                fontWeight: "700",
                color: theme.text.primary,
              },
              em: {
                fontStyle: "italic",
                color: theme.text.primary,
              },
              bullet_list: {
                marginVertical: 4,
              },
              ordered_list: {
                marginVertical: 4,
              },
              list_item: {
                marginVertical: 2,
                color: theme.text.primary,
              },
              heading1: {
                fontSize: 18,
                fontWeight: "700",
                color: theme.text.primary,
                marginVertical: 6,
              },
              heading2: {
                fontSize: 16,
                fontWeight: "700",
                color: theme.text.primary,
                marginVertical: 4,
              },
              heading3: {
                fontSize: 14,
                fontWeight: "700",
                color: theme.text.primary,
                marginVertical: 4,
              },
              code_inline: {
                backgroundColor: theme.border.default,
                color: theme.base.primary,
                borderRadius: 4,
                paddingHorizontal: 4,
                fontSize: 13,
              },
              fence: {
                backgroundColor: theme.background.bg,
                borderRadius: 8,
                padding: 10,
                marginVertical: 6,
                borderWidth: 1,
                borderColor: theme.border.default,
              },
              code_block: {
                color: theme.text.primary,
                fontSize: 13,
              },
              blockquote: {
                borderLeftWidth: 3,
                borderLeftColor: theme.base.primary,
                paddingLeft: 10,
                marginLeft: 0,
                opacity: 0.8,
              },
              hr: {
                borderColor: theme.border.default,
                marginVertical: 8,
              },
              link: {
                color: theme.base.primary,
              },
            }}
          >
            {message.content}
          </Markdown>
        </View>
        <Text
          typography="labelSmall"
          color={theme.text.secondary}
          style={{ marginTop: 4, marginLeft: 4 }}
        >
          {formatTime(message.timestamp)}
        </Text>
      </View>
    </View>
  </View>
);

const TypingIndicator = ({ theme }: { theme: any }) => (
  <View style={{ alignItems: "flex-start", marginBottom: 12 }}>
    <View style={{ flexDirection: "row", alignItems: "flex-end", gap: 8 }}>
      <View
        style={{
          width: 28,
          height: 28,
          borderRadius: 14,
          backgroundColor: theme.base.primary,
          alignItems: "center",
          justifyContent: "center",
        }}
      >
        <Ionicons name="bar-chart-outline" size={14} color="#fff" />
      </View>
      <View
        style={{
          backgroundColor: theme.background.surface,
          borderRadius: 16,
          borderBottomLeftRadius: 4,
          paddingHorizontal: 16,
          paddingVertical: 14,
          borderWidth: 1,
          borderColor: theme.border.default,
        }}
      >
        <ActivityIndicator size="small" color={theme.base.primary} />
      </View>
    </View>
  </View>
);

// ─── Helpers ──────────────────────────────────────────────────────────────────

const formatTime = (date: Date) =>
  date.toLocaleTimeString("vi-VN", { hour: "2-digit", minute: "2-digit" });

const WELCOME_MESSAGE: Message = {
  id: "welcome",
  role: "assistant",
  content:
    "Xin chào! Mình là trợ lý phân tích chứng khoán. Bạn muốn tìm hiểu về mã cổ phiếu nào, hoặc có câu hỏi gì về thị trường không?",
  timestamp: new Date(),
};

// ─── Main Screen ──────────────────────────────────────────────────────────────

const Chatbot = () => {
  const { theme } = useTheme();
  const scrollViewRef = useRef<ScrollView>(null);
  const sessionId = useRef<string>(uuid.v4() as string);

  const [messages, setMessages] = useState<Message[]>([WELCOME_MESSAGE]);
  const [inputText, setInputText] = useState("");
  const [isLoading, setIsLoading] = useState(false);

  const scrollToBottom = useCallback(() => {
    setTimeout(() => {
      scrollViewRef.current?.scrollToEnd({ animated: true });
    }, 100);
  }, []);

  const handleSend = useCallback(async () => {
    const text = inputText.trim();
    if (!text || isLoading) return;

    const userMessage: Message = {
      id: uuid.v4() as string,
      role: "user",
      content: text,
      timestamp: new Date(),
    };

    setMessages((prev) => [...prev, userMessage]);
    setInputText("");
    setIsLoading(true);
    scrollToBottom();

    const result = await sendChatMessage(sessionId.current, text);

    const assistantMessage: Message = {
      id: uuid.v4() as string,
      role: "assistant",
      content: result.status
        ? result.data!.reply
        : "Xin lỗi, mình gặp sự cố khi xử lý yêu cầu. Bạn thử lại sau nhé!",
      timestamp: new Date(),
    };

    setMessages((prev) => [...prev, assistantMessage]);
    setIsLoading(false);
    scrollToBottom();
  }, [inputText, isLoading, scrollToBottom]);

  return (
    <SafeAreaView style={{ flex: 1, backgroundColor: theme.background.bg }}>
      {/* Header */}
      <View
        style={{
          flexDirection: "row",
          alignItems: "center",
          paddingHorizontal: 16,
          paddingVertical: 12,
          borderBottomWidth: 1,
          borderBottomColor: theme.border.default,
          backgroundColor: theme.background.bg,
          gap: 12,
        }}
      >
        <TouchableOpacity onPress={() => router.back()}>
          <Ionicons
            name="arrow-back-outline"
            size={22}
            color={theme.text.primary}
          />
        </TouchableOpacity>

        <View
          style={{
            width: 36,
            height: 36,
            borderRadius: 18,
            backgroundColor: theme.base.primary,
            alignItems: "center",
            justifyContent: "center",
          }}
        >
          <Ionicons name="bar-chart-outline" size={18} color="#fff" />
        </View>

        <View style={{ flex: 1 }}>
          <Text typography="titleSmall" color={theme.text.primary}>
            Trợ lý phân tích
          </Text>
          <Text typography="labelSmall" color={theme.base.success}>
            Đang hoạt động
          </Text>
        </View>
      </View>

      {/* Messages */}
      <KeyboardAvoidingView
        style={{ flex: 1 }}
        behavior={Platform.OS === "ios" ? "padding" : "height"}
        keyboardVerticalOffset={0}
      >
        <ScrollView
          ref={scrollViewRef}
          style={{ flex: 1 }}
          contentContainerStyle={{ padding: 16, paddingBottom: 8 }}
          onContentSizeChange={scrollToBottom}
          showsVerticalScrollIndicator={false}
        >
          {messages.map((message) =>
            message.role === "user" ? (
              <UserBubble key={message.id} message={message} theme={theme} />
            ) : (
              <AssistantBubble
                key={message.id}
                message={message}
                theme={theme}
              />
            ),
          )}

          {isLoading && <TypingIndicator theme={theme} />}
        </ScrollView>

        {/* Input */}
        <View
          style={{
            flexDirection: "row",
            alignItems: "flex-end",
            paddingHorizontal: 12,
            paddingVertical: 10,
            borderTopWidth: 1,
            borderTopColor: theme.border.default,
            backgroundColor: theme.background.bg,
            gap: 8,
          }}
        >
          <View
            style={{
              flex: 1,
              backgroundColor: theme.background.surface,
              borderRadius: 20,
              borderWidth: 1,
              borderColor: theme.border.default,
              paddingHorizontal: 16,
              paddingVertical: 10,
              minHeight: 42,
              maxHeight: 120,
              justifyContent: "center",
            }}
          >
            <TextInput
              value={inputText}
              onChangeText={setInputText}
              placeholder="Nhập câu hỏi..."
              placeholderTextColor={theme.text.secondary}
              multiline
              style={{
                color: theme.text.primary,
                fontSize: 14,
                lineHeight: 20,
                padding: 0,
              }}
              onSubmitEditing={handleSend}
              blurOnSubmit={false}
            />
          </View>

          <TouchableOpacity
            onPress={handleSend}
            disabled={!inputText.trim() || isLoading}
            style={{
              width: 42,
              height: 42,
              borderRadius: 21,
              backgroundColor:
                inputText.trim() && !isLoading
                  ? theme.base.primary
                  : theme.background.surface,
              alignItems: "center",
              justifyContent: "center",
              borderWidth: 1,
              borderColor:
                inputText.trim() && !isLoading
                  ? theme.base.primary
                  : theme.border.default,
            }}
            activeOpacity={0.8}
          >
            <Ionicons
              name="send"
              size={18}
              color={
                inputText.trim() && !isLoading
                  ? "#FFFFFF"
                  : theme.text.secondary
              }
            />
          </TouchableOpacity>
        </View>
      </KeyboardAvoidingView>
    </SafeAreaView>
  );
};

export default Chatbot;
