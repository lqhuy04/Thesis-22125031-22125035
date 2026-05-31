import React, { useMemo } from "react";
import {
  ScrollView,
  TextInput,
  View,
  Image,
  Dimensions,
  TouchableOpacity,
} from "react-native";
import { useTheme } from "@/hooks/ThemeContext";
import LinearGradient from "react-native-linear-gradient";
import Feather from "@expo/vector-icons/Feather";
import Octicons from "@expo/vector-icons/Octicons";
import { Text } from "@/components/ui/Text";
import { useSafeAreaInsets } from "react-native-safe-area-context";

const Chatbot = () => {
  const { theme } = useTheme();
  const insets = useSafeAreaInsets();

  const exampleMessages = [
    "Sinh viên có nên đầu tư chứng khoán?",
    "Tóm tắt thị trường hôm nay",
    "Cổ phiếu VNM có tiềm năng không?",
    "Làm sao để bắt đầu đầu tư chứng khoán?",
    "RSI là gì và cách sử dụng nó?",
    "Tóm tắt tình hình mã VHM hôm nay",
  ];

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
      colors={["#4B2FC9", "#613DE4", "#7B5CFF", "#9D8CFF", "#7B5CFF"]}
      locations={[0, 0.1, 0.24, 0.5, 0.76]}
      useAngle
      angle={60}
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
            Chào bạn, tôi có thể giúp gì cho bạn?
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
          Gợi ý dành cho bạn
        </Text>

        <Text typography="labelLarge" color={theme.text.primary}>
          Xem thêm
        </Text>
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
          <View
            key={index.toString()}
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
          </View>
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
          onPress={() => {}}
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
            paddingHorizontal: 12,
          }}
        >
          <Octicons
            name="sparkles-fill"
            size={16}
            color={theme.text.primary}
            style={{ marginRight: 8 }}
          />
          <View style={{ pointerEvents: "none", flex: 1 }}>
            <TextInput
              style={{ color: theme.text.primary }}
              value={""}
              onChangeText={() => {}}
              autoCapitalize="none"
              returnKeyType="search"
              placeholder="Hỏi tôi bất cứ điều gì..."
              placeholderTextColor={theme.text.primary + "88"}
            />
          </View>
        </TouchableOpacity>
      </View>
    </LinearGradient>
  );
};

export default Chatbot;
