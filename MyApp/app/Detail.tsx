import FundamentalAnalysisMetricsSection from "@/components/detail/FundamentalAnalysisMetricsSection";
import NewsSection from "@/components/detail/NewsSection";
import DetailHeader from "@/components/ui/DetailHeader";
import PriceLineGraph from "@/components/ui/PriceLineChart";
import ScreenHeader from "@/components/ui/ScreenHeader";
import { fetchStockData, StockData } from "@/helpers/DetailHelpers";
import { useLocalization } from "@/hooks/LocalizationContext";
import { useTheme } from "@/hooks/ThemeContext";
import { useLocalSearchParams } from "expo-router";
import React, { useEffect, useState } from "react";
import { ScrollView } from "react-native-gesture-handler";
import { SafeAreaView } from "react-native-safe-area-context";

const Detail = () => {
  const { t } = useLocalization();
  const { theme } = useTheme();

  const { data } = useLocalSearchParams() || {};
  const item = data ? JSON.parse(data as string) : null;

  const [stockData, setStockData] = useState<StockData[]>([]);

  useEffect(() => {
    fetchStockData(item?.symbol || "", "1D").then((res) => {
      if (res.status) {
        setStockData(res.data);
      }
    });
  }, [item?.symbol]);

  return (
    <SafeAreaView
      style={{ flex: 1, padding: 12, backgroundColor: theme.background.bg }}
    >
      <ScreenHeader title={t("detail.screenTitle")} />

      <ScrollView style={{flex: 1}}>
        <DetailHeader item={item} />

        <NewsSection stockSymbol={item?.symbol || ""} />

        <FundamentalAnalysisMetricsSection stock_symbol={item?.symbol || ""} />

        <PriceLineGraph  data={stockData}/>

      </ScrollView>


    </SafeAreaView>
  );
};

export default Detail;
