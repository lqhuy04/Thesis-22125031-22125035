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
import Octicons from "@expo/vector-icons/Octicons";
import { Text } from "../ui/Text";

const { height: SCREEN_HEIGHT } = Dimensions.get("window");

interface SuggestionTab {
  label: string;
  questions: string[];
}

// Mock data — các nhóm gợi ý cho app chứng khoán
export const SUGGESTION_TABS: SuggestionTab[] = [
  {
    label: "Phân tích cổ phiếu",
    questions: [
      "Phân tích cổ phiếu VNM 📊",
      "Cổ phiếu nào đáng mua tuần này?",
      "So sánh HPG và HSG",
      "Định giá cổ phiếu FPT",
      "Cổ phiếu VHM có tiềm năng không?",
      "Phân tích cơ bản mã MWG",
    ],
  },
  {
    label: "Thị trường hôm nay",
    questions: [
      "Tóm tắt thị trường hôm nay 📈",
      "VN-Index hôm nay thế nào?",
      "Top cổ phiếu tăng mạnh nhất",
      "Khối ngoại mua bán ròng gì?",
      "Nhóm ngành nào đang dẫn dắt thị trường?",
      "Tin tức tác động thị trường hôm nay",
    ],
  },
  {
    label: "Chỉ báo kỹ thuật",
    questions: [
      "RSI là gì và cách sử dụng? 📐",
      "MACD của VNM đang báo hiệu gì?",
      "Đường MA50 và MA200 là gì?",
      "Cổ phiếu nào đang vùng quá bán?",
      "Phân tích kỹ thuật mã HPG",
      "Tín hiệu Bollinger Bands hiện tại",
    ],
  },
  {
    label: "Kiến thức đầu tư",
    questions: [
      "Sinh viên có nên đầu tư chứng khoán? 🎓",
      "Làm sao để bắt đầu đầu tư?",
      "Chỉ số P/E và P/B là gì?",
      "Phân biệt cổ phiếu và trái phiếu",
      "Khi nào nên cắt lỗ, chốt lời?",
      "Đầu tư dài hạn hay lướt sóng?",
    ],
  },
  {
    label: "1 phút học đầu tư",
    questions: [
      "Cổ tức là gì? 💡",
      "Vốn hóa thị trường là gì?",
      "Hiểu về thanh khoản cổ phiếu",
      "Margin là gì và rủi ro ra sao?",
      "ETF khác gì so với cổ phiếu?",
      "Cách đọc báo cáo tài chính",
    ],
  },
  {
    label: "Nói chuyện phiếm",
    questions: [
      "Kể chuyện cười về đầu tư 😄",
      "Làm thơ về chứng khoán cho mình nghe",
      "Warren Buffett dạy gì về đầu tư?",
      "Bài học từ những cú sập thị trường",
      "Giúp mình ra quyết định đầu tư",
      "Tâm lý nhà đầu tư khi thị trường đỏ lửa",
    ],
  },
];

interface Props {
  visible: boolean;
  tabs?: SuggestionTab[];
  onClose: () => void;
  onSelectQuestion?: (question: string) => void;
}

const SuggestionsBottomSheet = ({
  visible,
  tabs = SUGGESTION_TABS,
  onClose,
  onSelectQuestion,
}: Props) => {
  const { theme } = useTheme();

  const [activeTab, setActiveTab] = useState(0);

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

  const handleSelect = (question: string) => {
    onSelectQuestion?.(question);
    closeSheet();
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
            Mở rộng
          </Text>
          <TouchableOpacity onPress={closeSheet} hitSlop={8}>
            <Feather name="x" size={24} color={theme.text.primary} />
          </TouchableOpacity>
        </View>

        {/* Tab bar */}
        <View
          style={{
            borderBottomWidth: 1,
            borderBottomColor: theme.border.default,
          }}
        >
          <ScrollView
            horizontal
            showsHorizontalScrollIndicator={false}
            contentContainerStyle={styles.tabBar}
          >
            {tabs.map((tab, index) => {
              const isActive = index === activeTab;
              return (
                <TouchableOpacity
                  key={tab.label}
                  activeOpacity={0.7}
                  onPress={() => setActiveTab(index)}
                  style={styles.tabItem}
                >
                  <Text
                    typography="titleMedium"
                    color={isActive ? theme.base.primary : theme.text.secondary}
                  >
                    {tab.label}
                  </Text>
                  <View
                    style={[
                      styles.tabIndicator,
                      {
                        backgroundColor: isActive
                          ? theme.base.primary
                          : "transparent",
                      },
                    ]}
                  />
                </TouchableOpacity>
              );
            })}
          </ScrollView>
        </View>

        {/* Danh sách câu hỏi của tab đang chọn */}
        <ScrollView
          style={styles.list}
          showsVerticalScrollIndicator={false}
          contentContainerStyle={{ paddingVertical: 16, paddingHorizontal: 16 }}
        >
          {tabs[activeTab].questions.map((question, index) => (
            <TouchableOpacity
              key={index.toString()}
              activeOpacity={0.7}
              onPress={() => handleSelect(question)}
              style={[
                styles.row,
                { backgroundColor: theme.background.surface },
              ]}
            >
              <Octicons
                name="sparkles-fill"
                size={18}
                color={theme.base.primary}
                style={{ marginRight: 16 }}
              />
              <Text
                typography="bodyLarge"
                color={theme.text.primary}
                numberOfLines={1}
                style={{ flex: 1, marginRight: 12 }}
              >
                {question}
              </Text>
              <Feather
                name="chevron-right"
                size={20}
                color={theme.text.secondary}
              />
            </TouchableOpacity>
          ))}
        </ScrollView>
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
    height: SCREEN_HEIGHT * 0.82,
    borderTopLeftRadius: 24,
    borderTopRightRadius: 24,
    paddingBottom: 24,
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
  tabBar: {
    paddingHorizontal: 20,
    gap: 24,
  },
  tabItem: {
    alignItems: "center",
  },
  tabIndicator: {
    height: 3,
    borderRadius: 2,
    alignSelf: "stretch",
    marginTop: 10,
  },
  list: {
    flex: 1,
  },
  row: {
    flexDirection: "row",
    alignItems: "center",
    paddingVertical: 18,
    paddingHorizontal: 20,
    borderRadius: 16,
    marginBottom: 12,
  },
});

export default SuggestionsBottomSheet;
