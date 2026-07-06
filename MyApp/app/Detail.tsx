import ScreenHeader from "@/components/ui/ScreenHeader";
import { useTheme } from "@/hooks/ThemeContext";
import React, { useCallback, useRef, useState } from "react";
import { RefreshControl, ScrollView, View } from "react-native";
import { router, useLocalSearchParams } from "expo-router";
import PriceChartComponent from "@/components/detail/PriceChartComponent";
import { useLocalization } from "@/hooks/LocalizationContext";
import IntroductionSection from "@/components/detail/IntroductionSection";
import FinancialIndicatorsSection from "@/components/detail/FinancialIndicatorsSection";
import NewsSection from "@/components/detail/NewsSection";
import RelatedStocksSection from "@/components/detail/RelatedStocksSection";
import AIFloatingButton from "@/components/AIFloatingButton";

const Detail = () => {
  const { theme } = useTheme();
  const { t } = useLocalization();

  const { data } = useLocalSearchParams() || {};
  const stockSymbol = (data as string) ?? "";

  const [refreshing, setRefreshing] = useState(false);

  // Mỗi section con đăng ký hàm refresh của mình vào đây
  const refreshFns = useRef<(() => Promise<void>)[]>([]);

  const registerRefresh = useCallback((fn: () => Promise<void>) => {
    refreshFns.current.push(fn);
    return () => {
      refreshFns.current = refreshFns.current.filter((f) => f !== fn);
    };
  }, []);

  const onRefresh = useCallback(async () => {
    setRefreshing(true);
    try {
      await Promise.all(refreshFns.current.map((fn) => fn()));
    } finally {
      setRefreshing(false);
    }
  }, []);

  return (
    <View style={{ flex: 1, backgroundColor: theme.background.surface }}>
      <ScreenHeader title={t("detail.screenTitle")} />
      <ScrollView
        style={{
          flex: 1,
          backgroundColor: theme.background.surface,
        }}
        refreshControl={
          <RefreshControl refreshing={refreshing} onRefresh={onRefresh} />
        }
      >
        <PriceChartComponent
          symbol={stockSymbol}
          registerRefresh={registerRefresh}
        />

        <NewsSection
          stockSymbol={stockSymbol}
          registerRefresh={registerRefresh}
        />

        <FinancialIndicatorsSection
          stockSymbol={stockSymbol}
          registerRefresh={registerRefresh}
        />

        <IntroductionSection
          stockSymbol={stockSymbol}
          registerRefresh={registerRefresh}
        />

        <RelatedStocksSection
          stockSymbol={stockSymbol}
          registerRefresh={registerRefresh}
        />

        <View style={{ height: 100 }} />
      </ScrollView>

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
