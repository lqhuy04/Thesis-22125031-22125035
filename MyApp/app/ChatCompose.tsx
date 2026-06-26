import React, { useEffect, useMemo, useState } from "react";
import {
  View,
  TextInput,
  TouchableOpacity,
  KeyboardAvoidingView,
} from "react-native";
import { useTheme } from "@/hooks/ThemeContext";
import { useLocalization } from "@/hooks/LocalizationContext";
import LinearGradient from "react-native-linear-gradient";
import { router, useLocalSearchParams } from "expo-router";
import * as Crypto from "expo-crypto";
import Feather from "@expo/vector-icons/Feather";
import Octicons from "@expo/vector-icons/Octicons";
import { Text } from "@/components/ui/Text";
import type { ChatConversation } from "@/components/chatbot/ChatHistoryBottomsheet";
import ScreenHeader from "@/components/ui/ScreenHeader";
import useKeyboardVisible from "@/hooks/KeyboardContext";
import { useSafeAreaInsets } from "react-native-safe-area-context";

const ChatCompose = () => {
  const { theme } = useTheme();
  const { t } = useLocalization();
  const [input, setInput] = useState("");
  const isKeyboardOpen = useKeyboardVisible(true);
  const insets = useSafeAreaInsets();
  const fromBts = useLocalSearchParams<{ fromBts?: string }>().fromBts === "1";
  const [firstFromBts, setFirstFromBts] = useState(fromBts);

  const marginBottom = useMemo(() => {
    if (firstFromBts) {
      return insets.bottom + 24;
    } else return isKeyboardOpen ? 24 : 0;
  }, [firstFromBts, insets.bottom, isKeyboardOpen]);

  /** Tạo phiên mới (UUID) và điều hướng sang ChatDetail, gửi luôn tin đầu tiên. */
  const startNewConversation = () => {
    const message = input.trim();
    if (!message) return;

    const sessionId = Crypto.randomUUID();
    const conversation: ChatConversation = {
      id: sessionId,
      title: message.slice(0, 60),
      timeLabel: t("chatbot.today"),
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

  useEffect(() => {
    if (firstFromBts && isKeyboardOpen) setFirstFromBts(false);
  }, [firstFromBts, isKeyboardOpen]);

  return (
    <LinearGradient
      colors={["#5B21B6", "#7C3AED", "#A78BFA", "#E9D5FF"]}
      locations={[0, 0.2, 0.6, 1]}
      useAngle
      angle={135}
      angleCenter={{ x: 0.5, y: 0.5 }}
      style={{ flex: 1 }}
    >
      <KeyboardAvoidingView style={{ flex: 1 }} behavior="padding">
        <ScreenHeader title={t("tabs.chatbot")} />

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
              <Text typography="headlineMedium" color={theme.text.onPrimary}>
                {t("chatbot.greeting")}
              </Text>
            </View>
          </View>
        </View>

        {/* Composer: nhập + gửi tin nhắn đầu tiên */}
        <View
          style={{
            flexDirection: "row",
            alignItems: "center",
            marginBottom: marginBottom,
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
              placeholder={t("chatbot.placeholder")}
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
