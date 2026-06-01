import React, { useRef } from "react";
import {
  Modal,
  Animated,
  Pressable,
  StyleSheet,
  TouchableOpacity,
  View,
  Dimensions,
} from "react-native";
import { useTheme } from "@/hooks/ThemeContext";
import Feather from "@expo/vector-icons/Feather";
import { Text } from "../ui/Text";
import type { ChatConversation } from "./ChatHistoryBottomsheet";

const { height: SCREEN_HEIGHT } = Dimensions.get("window");

interface Props {
  visible: boolean;
  conversation: ChatConversation | null;
  onClose: () => void;
  onShare?: (conversation: ChatConversation) => void;
  onDelete?: (conversation: ChatConversation) => void;
}

const ConversationOptionsBottomSheet = ({
  visible,
  conversation,
  onClose,
  onShare,
  onDelete,
}: Props) => {
  const { theme } = useTheme();

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
    <Modal visible={visible} transparent animationType="none" onShow={openSheet}>
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
          { backgroundColor: theme.background.surface },
          { transform: [{ translateY: slideAnim }] },
        ]}
      >
        {/* Handle */}
        <View style={styles.handle} />

        {/* Header: tiêu đề + nút đóng */}
        <View style={styles.header}>
          <View style={{ width: 24 }} />
          <Text typography="titleLarge" color={theme.text.primary}>
            Tuỳ chọn
          </Text>
          <TouchableOpacity onPress={closeSheet} hitSlop={8}>
            <Feather name="x" size={24} color={theme.text.primary} />
          </TouchableOpacity>
        </View>

        {/* Card chứa các tuỳ chọn */}
        <View style={[styles.card, { backgroundColor: theme.background.bg }]}>
          {/* Chia sẻ — sắp ra mắt (disabled) */}
          <TouchableOpacity
            disabled
            activeOpacity={0.7}
            style={styles.option}
          >
            <Feather name="share-2" size={22} color={theme.text.secondary} />
            <Text
              typography="bodyLarge"
              color={theme.text.secondary}
              style={{ marginLeft: 16 }}
            >
              Chia sẻ
            </Text>
            <View
              style={[styles.badge, { backgroundColor: theme.base.warning }]}
            >
              <Text typography="labelSmall" color="#FFFFFF">
                Sắp ra mắt
              </Text>
            </View>
          </TouchableOpacity>

          {/* Divider */}
          <View
            style={{
              height: 1,
              backgroundColor: theme.border.default,
              marginHorizontal: 20,
            }}
          />

          {/* Xoá */}
          <TouchableOpacity
            activeOpacity={0.7}
            onPress={() => {
              if (conversation) onDelete?.(conversation);
              closeSheet();
            }}
            style={styles.option}
          >
            <Feather name="trash-2" size={22} color={theme.base.error} />
            <Text
              typography="bodyLarge"
              color={theme.base.error}
              style={{ marginLeft: 16 }}
            >
              Xoá
            </Text>
          </TouchableOpacity>
        </View>
      </Animated.View>
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
    marginBottom: 20,
  },
  card: {
    marginHorizontal: 16,
    borderRadius: 16,
    overflow: "hidden",
  },
  option: {
    flexDirection: "row",
    alignItems: "center",
    paddingVertical: 18,
    paddingHorizontal: 20,
  },
  badge: {
    marginLeft: 12,
    paddingHorizontal: 8,
    paddingVertical: 3,
    borderRadius: 8,
  },
});

export default ConversationOptionsBottomSheet;
