import FundamentalAnalysisMetricsSection from "@/components/detail/FundamentalAnalysisMetricsSection";
import NewsSection from "@/components/detail/NewsSection";
import DetailHeader from "@/components/ui/DetailHeader";
import PriceCandleChart from "@/components/ui/PriceCandleChart";
import PriceLineGraph from "@/components/ui/PriceLineChart";
import ScreenHeader from "@/components/ui/ScreenHeader";
import { Text } from "@/components/ui/Text";
import { fetchStockData, getAnalysis, StockData } from "@/helpers/DetailHelpers";
import { useLocalization } from "@/hooks/LocalizationContext";
import { useTheme } from "@/hooks/ThemeContext";
import { useLocalSearchParams } from "expo-router";
import React, { useEffect, useState } from "react";
import { ScrollView } from "react-native-gesture-handler";
import { SafeAreaView } from "react-native-safe-area-context";
import Markdown from "react-native-markdown-display";


const Detail = () => {
  const { t } = useLocalization();
  const { theme } = useTheme();

  const { data } = useLocalSearchParams() || {};
  const item = data ? JSON.parse(data as string) : null;

  const [stockData, setStockData] = useState<StockData[]>([]);
  const [fundamentalAnalysis, setFundamentalAnalysis] = useState<string>('')
  const [ technicalAnalysis, setTechnicalAnalysis] = useState<string>('')
  const [summary, setSummary] = useState<string>('')


  useEffect(() => {
    fetchStockData(item?.symbol || "", "1D").then((res) => {
      if (res.status) {
        setStockData(res.data);
      }
    });

    getAnalysis('','','').then((res) => {
      if (res.status) {
          setFundamentalAnalysis(res.data?.fundamental_analysis ?? '');
          setTechnicalAnalysis(res.data?.technical_analysis ?? '')
          setSummary(res.data?.final_report ?? '');
      }
    })
  }, [item?.symbol]);

  return (
    <SafeAreaView
      style={{ flex: 1, backgroundColor: theme.background.bg }}
    >
      <ScreenHeader title={t("detail.screenTitle")} />

      <ScrollView style={{flex: 1}}>
        <DetailHeader item={item} />

        <NewsSection stockSymbol={item?.symbol || ""} />

        <FundamentalAnalysisMetricsSection stock_symbol={item?.symbol || ""} />

        <PriceLineGraph  data={stockData}/>

        <PriceCandleChart data={stockData} />
        

        <Text typography="titleLarge" style={{marginTop: 24}}>
        {"Fundamental Analysis: "}
        </Text>
        <Markdown>
          {fundamentalAnalysis}
        </Markdown>

        <Text typography="titleLarge" style={{marginTop: 24}}>
        {"Technical Analysis: "}
        </Text>
        <Markdown>
          {technicalAnalysis}
        </Markdown>


        <Text typography="titleLarge" style={{marginTop: 24}}>
        {"Summary: "}
        </Text>
        <Markdown>
          {summary}
        </Markdown>

      </ScrollView>


    </SafeAreaView>
  );
};

export default Detail;
