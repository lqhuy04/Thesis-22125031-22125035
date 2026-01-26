import FundamentalAnalysisMetricsSection from "@/components/detail/FundamentalAnalysisMetricsSection";
import NewsSection from "@/components/detail/NewsSection";
import DetailHeader from "@/components/ui/DetailHeader";
import ScreenHeader from "@/components/ui/ScreenHeader";
import { useLocalization } from "@/hooks/LocalizationContext";
import { useTheme } from "@/hooks/ThemeContext";
import { useLocalSearchParams } from "expo-router";
import React from "react";
import { SafeAreaView } from "react-native-safe-area-context";

const Detail = () => {
  const { t } = useLocalization();
  const { theme } = useTheme();

  const { data } = useLocalSearchParams() || {};
  const item = data ? JSON.parse(data as string) : null;

  return (
    <SafeAreaView
      style={{ flex: 1, padding: 12, backgroundColor: theme.background.bg }}
    >
      <ScreenHeader title= {t("detail.screenTitle")} />

      <DetailHeader item={item} />

      <NewsSection stockSymbol={item?.symbol || ""} />

      <FundamentalAnalysisMetricsSection stock_symbol={item?.symbol || ""}/>
    </SafeAreaView>
  );
};

export default Detail;
