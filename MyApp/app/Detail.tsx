import ScreenHeader from "@/components/ui/ScreenHeader";
import { useTheme } from "@/hooks/ThemeContext";
import React from "react";
import { ScrollView, View } from "react-native";
import { router, useLocalSearchParams } from "expo-router";
import PriceChartComponent from "@/components/detail/PriceChartComponent";
import { useLocalization } from "@/hooks/LocalizationContext";
import IntroductionSection from "@/components/detail/IntroductionSection";
import FinancialIndicatorsSection from "@/components/detail/FinancialIndicatorsSection";
import NewsSection from "@/components/detail/NewsSection";
import ScreenFooter from "@/components/ScreenFooter";
import AIFloatingButton from "@/components/AIFloatingButton";

const Detail = () => {
  const { theme } = useTheme();
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

        <View style={{ height: 140 }} />
      </ScrollView>

      <ScreenFooter
        onPressBuy={() =>
          router.push({
            pathname: "/BuyStock",
            params: { data: stockSymbol },
          })
        }
      />

      <AIFloatingButton
        onPress={() =>
          router.push({
            pathname: "/AIAnalysisConfig",
            params: { data: stockSymbol },
          })
        }
      />
    </View>
  );
};

export default Detail;
