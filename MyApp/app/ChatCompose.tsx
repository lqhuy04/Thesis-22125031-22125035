import React, { useState } from "react";
import {
  View,
  TextInput,
  TouchableOpacity,
  KeyboardAvoidingView,
  Platform,
} from "react-native";
import { useTheme } from "@/hooks/ThemeContext";
import LinearGradient from "react-native-linear-gradient";
import { router } from "expo-router";
import * as Crypto from "expo-crypto";
import Feather from "@expo/vector-icons/Feather";
import Octicons from "@expo/vector-icons/Octicons";
import { Text } from "@/components/ui/Text";
import type { ChatConversation } from "@/components/chatbot/ChatHistoryBottomsheet";
import ScreenHeader from "@/components/ui/ScreenHeader";

const ChatCompose = () => {
  const { theme } = useTheme();
  const [input, setInput] = useState("");

  /** Tạo phiên mới (UUID) và điều hướng sang ChatDetail, gửi luôn tin đầu tiên. */
  const startNewConversation = () => {
    const message = input.trim();
    if (!message) return;

    const sessionId = Crypto.randomUUID();
    const conversation: ChatConversation = {
      id: sessionId,
      title: message.slice(0, 60),
      timeLabel: "Hôm nay",
    };

    setInput("");
    router.replace({
      pathname: "/ChatDetail",
      params: {
        data: JSON.stringify(conversation),
        initialMessage: message,
      },
    });
  };

  return (
    <LinearGradient
      colors={["#4B2FC9", "#613DE4", "#7B5CFF", "#9D8CFF", "#7B5CFF"]}
      locations={[0, 0.1, 0.24, 0.5, 0.76]}
      useAngle
      angle={60}
      angleCenter={{ x: 0.5, y: 0.5 }}
      style={{ flex: 1 }}
    >
      <KeyboardAvoidingView
        style={{ flex: 1 }}
        behavior={Platform.OS === "ios" ? "padding" : undefined}
      >
        <ScreenHeader title="Chatbot" />

        {/* Tiêu đề */}
        <View
          style={{ flex: 1, alignItems: "center", justifyContent: "center" }}
        >
          <View
            style={{
              flexDirection: "row",
              alignItems: "center",
              marginHorizontal: 12,
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
              <Octicons
                name="dependabot"
                size={32}
                color={theme.text.primary}
              />
            </View>
            <View style={{ flex: 1 }}>
              <Text typography="headlineMedium" color={theme.text.primary}>
                Xin chào, tôi có thể giúp gì cho bạn?
              </Text>
            </View>
          </View>
        </View>

        {/* Composer: nhập + gửi tin nhắn đầu tiên */}
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
              onSubmitEditing={startNewConversation}
              placeholder="Hỏi tôi bất cứ điều gì..."
              placeholderTextColor={theme.text.primary + "88"}
            />
            <TouchableOpacity
              activeOpacity={0.8}
              disabled={!input.trim()}
              onPress={startNewConversation}
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

export default ChatCompose;
