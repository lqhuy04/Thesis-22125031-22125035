import ScreenHeader from "@/components/ui/ScreenHeader";
import { useTheme } from "@/hooks/ThemeContext";
import React from "react";
import { ScrollView, View } from "react-native";
import { useLocalSearchParams } from "expo-router";
import PriceChartComponent from "@/components/detail/PriceChartComponent";
import LinearGradient from "react-native-linear-gradient";
import { useSafeAreaInsets } from "react-native-safe-area-context";
import { Text } from "@/components/ui/Text";
import Octicons from "@expo/vector-icons/Octicons";
import { useLocalization } from "@/hooks/LocalizationContext";
import IntroductionSection from "@/components/detail/IntroductionSection";
import FinancialIndicatorsSection from "@/components/detail/FinancialIndicatorsSection";
import NewsSection from "@/components/detail/NewsSection";

const Detail = () => {
  const { theme } = useTheme();
  const insets = useSafeAreaInsets();
  const { t } = useLocalization();

  const { data } = useLocalSearchParams() || {};
  const stockSymbol = (data as string) ?? "";

  return (
    <View style={{ flex: 1, backgroundColor: theme.background.surface }}>
      <ScreenHeader title={t("detail.screenTitle")} />
      <ScrollView
        style={{
          flex: 1,
          backgroundColor: theme.background.surface,
        }}
      >
        <PriceChartComponent symbol={stockSymbol} />

        <NewsSection stockSymbol={stockSymbol} />

        <FinancialIndicatorsSection stockSymbol={stockSymbol} />

        <IntroductionSection stockSymbol={stockSymbol} />

        <View style={{ height: 84 }} />
      </ScrollView>

      <LinearGradient
        colors={[
          "#4B2FC9",
          "#613DE4",
          "#7B5CFF",
          "#9D8CFF",
          "#7B5CFF",
          "#613DE4",
          "#4B2FC9",
        ]}
        useAngle
        angle={90}
        angleCenter={{ x: 0.5, y: 0.5 }}
        style={{
          position: "absolute",
          bottom: insets.bottom,
          right: 12,
          borderRadius: 24,
          // Shadow iOS
          shadowColor: "#000",
          shadowOffset: { width: 0, height: 2 },
          shadowOpacity: 0.08,
          shadowRadius: 4,
          // Shadow Android
          elevation: 4,
        }}
      >
        <View
          style={{
            flexDirection: "row",
            alignItems: "center",
            paddingVertical: 10,
            paddingHorizontal: 12,
          }}
        >
          <Octicons
            name="sparkles-fill"
            size={20}
            color={theme.text.onPrimary}
            style={{ marginRight: 8 }}
          />
          <Text typography="titleMedium" color={theme.text.onPrimary}>
            {t("detail.AIAnalyze")}{" "}
          </Text>
        </View>
      </LinearGradient>
    </View>
  );
};

export default Detail;
