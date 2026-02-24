import IntroductionSection from "@/components/detail/IntroductionSection";
import NewsSection from "@/components/detail/NewsSection";
import DetailHeader from "@/components/ui/DetailHeader";
import PriceCandleChart from "@/components/ui/PriceCandleChart";
import PriceLineGraph from "@/components/ui/PriceLineChart";
import ScreenHeader from "@/components/ui/ScreenHeader";
import { fetchStockData, StockData } from "@/helpers/DetailHelpers";
import { SearchStockItem } from "@/helpers/SearchHelper";
import { useLocalization } from "@/hooks/LocalizationContext";
import { useTheme } from "@/hooks/ThemeContext";
import React, { useEffect, useState } from "react";
import { View } from "react-native";
import { ScrollView } from "react-native-gesture-handler";
import { SafeAreaView } from "react-native-safe-area-context";

interface Props {
  stockItem: SearchStockItem;
}

const Detail = ({ stockItem }: Props) => {
  const { t } = useLocalization();
  const { theme } = useTheme();

  const [stockData, setStockData] = useState<StockData[]>([]);

  useEffect(() => {
    if (!stockItem?.symbol) return;

    const fetchAll = async () => {
      try {
        const stockRes = await fetchStockData(stockItem.symbol, "1D");

        if (stockRes?.status) {
          setStockData(stockRes.data);
        }
      } catch (error) {
        console.error("Error fetching stock analysis:", error);
      }
    };

    fetchAll();
  }, [stockItem?.symbol]);

  return (
    <SafeAreaView
      style={{
        flex: 1,
        backgroundColor: theme.background.bg,
        paddingVertical: 12,
      }}
    >
      <ScreenHeader title={t("detail.screenTitle")} />

      <ScrollView style={{ flex: 1 }}>
        <DetailHeader item={stockItem} />
        
        <View style={{height: 40}}/>
        <PriceLineGraph data={stockData} />
        <PriceCandleChart data={stockData} />

        <IntroductionSection />

        <NewsSection stockSymbol={stockItem.symbol} />
      </ScrollView>
    </SafeAreaView>
  );
};

export default Detail;
