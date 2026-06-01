import React from "react";
import { ScrollView, View, Image, TouchableOpacity } from "react-native";
import { router, useLocalSearchParams } from "expo-router";
import Markdown from "react-native-markdown-display";
import Feather from "@expo/vector-icons/Feather";
import ScreenHeader from "@/components/ui/ScreenHeader";
import { Text } from "@/components/ui/Text";
import { useTheme } from "@/hooks/ThemeContext";
import { typography } from "@/constants/typography";
import type { ChatConversation } from "@/components/chatbot/ChatHistoryBottomsheet";

interface ChatMessage {
  id: string;
  role: "user" | "assistant";
  content: string;
  /** URL avatar/hình minh hoạ hiển thị kèm tin nhắn của trợ lý */
  image?: string;
}

// Mock data — nội dung một cuộc trò chuyện mẫu với trợ lý Moni
const MOCK_MESSAGES: ChatMessage[] = [
  {
    id: "1",
    role: "user",
    content:
      "Moni ơi, danh mục của mình đang lời lỗ thế nào so với thị trường chung?",
  },
  {
    id: "2",
    role: "assistant",
    content:
      "Chào bạn 👋, mình là **Moni** — trợ lý đầu tư của bạn. Hôm nay mình sẽ giúp bạn soi nhanh hiệu suất danh mục so với VN-Index nhé 😎\n— Moni",
  },
  {
    id: "3",
    role: "assistant",
    content:
      "Đầu tiên, bạn có thể cho Moni biết:\n\n- 📊 **Các mã** bạn đang nắm giữ\n- 💰 **Giá vốn & số lượng** từng mã\n\nMoni chờ thông tin từ bạn nhaa",
    image:
      "https://ddazflrupjwuxlxlszbk.supabase.co/storage/v1/object/public/icons/increase.png",
  },
  {
    id: "4",
    role: "user",
    content: "Mình đang giữ HPG giá vốn 25, VNM giá vốn 62, mỗi mã 1000 cp",
  },
  {
    id: "5",
    role: "assistant",
    content:
      "Tuyệt vời! Moni đã sẵn sàng để biến danh mục của bạn thành một bức tranh rõ ràng và dễ hiểu đây 📈\n\nBạn muốn Moni **phân tích hiệu suất**, **đánh giá rủi ro** hay **gợi ý cơ cấu lại danh mục** trước?",
  },
];

const ChatDetail = () => {
  const { theme } = useTheme();

  const { data } = useLocalSearchParams() || {};
  const conversation = data
    ? (JSON.parse(data as string) as ChatConversation)
    : null;

  return (
    <View style={{ flex: 1, backgroundColor: theme.background.surface }}>
      <ScreenHeader title="Chi tiết trò chuyện" />

      <ScrollView
        style={{ flex: 1 }}
        contentContainerStyle={{ padding: 16, paddingBottom: 24 }}
        showsVerticalScrollIndicator={false}
      >
        {MOCK_MESSAGES.map((msg) =>
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
                  strong: { fontFamily: typography.titleMedium.fontFamily },
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
        )}
      </ScrollView>

      {/* Footer: quay về danh sách + ghi chú tính năng */}
      <View style={{ paddingHorizontal: 16, paddingBottom: 24, paddingTop: 8 }}>
        <TouchableOpacity
          activeOpacity={0.8}
          onPress={() => router.back()}
          style={{
            flexDirection: "row",
            alignItems: "center",
            justifyContent: "center",
            backgroundColor: theme.text.onPrimary,
            borderRadius: 28,
            paddingVertical: 16,
          }}
        >
          <Feather name="arrow-left" size={20} color={theme.base.primary} />
          <Text
            typography="titleMedium"
            color={theme.base.primary}
            style={{ marginLeft: 8 }}
          >
            Về danh sách trò chuyện
          </Text>
        </TouchableOpacity>

        <Text
          typography="bodySmall"
          color={theme.text.secondary}
          style={{ textAlign: "center", marginTop: 12 }}
        >
          (Tính năng{" "}
          <Text typography="labelSmall" color={theme.text.secondary}>
            Tiếp tục cuộc trò chuyện
          </Text>{" "}
          đang được phát triển)
        </Text>
      </View>
    </View>
  );
};

export default ChatDetail;
