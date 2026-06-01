import React, { useRef, useState } from "react";
import {
  Modal,
  Animated,
  Pressable,
  StyleSheet,
  TouchableOpacity,
  View,
  ScrollView,
  Dimensions,
} from "react-native";
import { useTheme } from "@/hooks/ThemeContext";
import Feather from "@expo/vector-icons/Feather";
import { Text } from "../ui/Text";
import ConversationOptionsBottomSheet from "./ConversationOptionsBottomsheet";

const { height: SCREEN_HEIGHT } = Dimensions.get("window");

export interface ChatConversation {
  id: string;
  title: string;
  /** Nhãn thời gian hiển thị, ví dụ: "Hôm nay", "Hôm qua", "27 tháng 05" */
  timeLabel: string;
}

// Mock data — danh sách các cuộc trò chuyện gần đây
export const MOCK_CONVERSATIONS: ChatConversation[] = [
  { id: "1", title: "123", timeLabel: "Hôm nay" },
  { id: "2", title: "hi", timeLabel: "Hôm nay" },
  { id: "3", title: "hello", timeLabel: "Hôm nay" },
  {
    id: "4",
    title: "Bí kíp deal lương cho chiếu mới 🧠",
    timeLabel: "Hôm qua",
  },
  {
    id: "5",
    title: "🔮 Thông điệp hôm nay cho mình",
    timeLabel: "27 tháng 05",
  },
  { id: "6", title: "hello", timeLabel: "07 tháng 01" },
  {
    id: "7",
    title:
      "Moni, lương thực tập của mình đang ở đâu so với những thực tập sinh khác trên thị trường?",
    timeLabel: "25 tháng 11",
  },
];

interface Props {
  visible: boolean;
  conversations?: ChatConversation[];
  onClose: () => void;
  onSelectConversation?: (conversation: ChatConversation) => void;
  onConversationMenu?: (conversation: ChatConversation) => void;
  onNewConversation?: () => void;
  onDeleteConversation?: (conversation: ChatConversation) => void;
  onShareConversation?: (conversation: ChatConversation) => void;
}

const ChatHistoryBottomSheet = ({
  visible,
  conversations = MOCK_CONVERSATIONS,
  onClose,
  onSelectConversation,
  onConversationMenu,
  onNewConversation,
  onDeleteConversation,
  onShareConversation,
}: Props) => {
  const { theme } = useTheme();

  const [optionsTarget, setOptionsTarget] = useState<ChatConversation | null>(
    null,
  );

  const slideAnim = useRef(new Animated.Value(SCREEN_HEIGHT)).current;
  const backdropAnim = useRef(new Animated.Value(0)).current;

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
          { backgroundColor: theme.background.bg },
          { transform: [{ translateY: slideAnim }] },
        ]}
      >
        {/* Handle */}
        <View style={styles.handle} />

        {/* Header: tiêu đề + nút đóng */}
        <View style={styles.header}>
          <View style={{ width: 24 }} />
          <Text typography="titleLarge" color={theme.text.primary}>
            Lịch sử hoạt động
          </Text>
          <TouchableOpacity onPress={closeSheet} hitSlop={8}>
            <Feather name="x" size={24} color={theme.text.primary} />
          </TouchableOpacity>
        </View>

        {/* Danh sách cuộc trò chuyện */}
        <ScrollView
          style={styles.list}
          showsVerticalScrollIndicator={false}
          contentContainerStyle={{ paddingBottom: 12 }}
        >
          <Text
            typography="titleMedium"
            color={theme.text.primary}
            style={{ marginHorizontal: 20, marginBottom: 4 }}
          >
            Trò chuyện
          </Text>

          {conversations.map((item, index) => (
            <TouchableOpacity
              key={item.id}
              activeOpacity={0.7}
              onPress={() => {
                closeSheet();
                onSelectConversation?.(item);
              }}
              style={[
                styles.row,
                {
                  borderBottomColor:
                    index !== conversations.length - 1
                      ? theme.border.default
                      : "transparent",
                },
              ]}
            >
              <View style={{ flex: 1, marginRight: 12 }}>
                <Text
                  typography="bodyLarge"
                  color={theme.text.primary}
                  numberOfLines={2}
                >
                  {item.title}
                </Text>
                <Text
                  typography="bodySmall"
                  color={theme.text.secondary}
                  style={{ marginTop: 4 }}
                >
                  {item.timeLabel}
                </Text>
              </View>

              <TouchableOpacity
                onPress={() => {
                  onConversationMenu?.(item);
                  setOptionsTarget(item);
                }}
                hitSlop={8}
                style={styles.rowMenu}
              >
                <Feather
                  name="more-horizontal"
                  size={22}
                  color={theme.text.primary}
                />
              </TouchableOpacity>
            </TouchableOpacity>
          ))}
        </ScrollView>

        {/* Nút tạo trò chuyện mới */}
        <TouchableOpacity
          activeOpacity={0.8}
          onPress={() => {
            onNewConversation?.();
            closeSheet();
          }}
          style={[styles.newButton, { backgroundColor: theme.base.primary }]}
        >
          <Feather name="plus" size={20} color={theme.text.onPrimary} />
          <Text
            typography="titleMedium"
            color={theme.text.onPrimary}
            style={{ marginLeft: 8 }}
          >
            Trò chuyện mới
          </Text>
        </TouchableOpacity>
      </Animated.View>

      {/* Bottom sheet tuỳ chọn cho từng cuộc trò chuyện */}
      <ConversationOptionsBottomSheet
        visible={optionsTarget !== null}
        conversation={optionsTarget}
        onClose={() => setOptionsTarget(null)}
        onShare={onShareConversation}
        onDelete={onDeleteConversation}
      />
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
    borderTopLeftRadius: 24,
    borderTopRightRadius: 24,
    paddingBottom: 36,
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
    marginBottom: 16,
  },
  header: {
    flexDirection: "row",
    alignItems: "center",
    justifyContent: "space-between",
    paddingHorizontal: 20,
    marginBottom: 24,
  },
  list: {
    flex: 1,
    marginTop: 12,
  },
  row: {
    flexDirection: "row",
    alignItems: "center",
    paddingVertical: 16,
    paddingHorizontal: 20,
    borderBottomWidth: 1,
  },
  rowMenu: {
    width: 32,
    height: 32,
    alignItems: "center",
    justifyContent: "center",
  },
  newButton: {
    flexDirection: "row",
    alignItems: "center",
    justifyContent: "center",
    marginHorizontal: 20,
    marginTop: 16,
    paddingVertical: 16,
    borderRadius: 12,
  },
});

export default ChatHistoryBottomSheet;
