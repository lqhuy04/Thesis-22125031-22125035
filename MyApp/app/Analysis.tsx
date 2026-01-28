import React, { useEffect, useState } from "react";
import { SafeAreaView } from "react-native-safe-area-context";
import { useTheme } from "@/hooks/ThemeContext";
import { useLocalization } from "@/hooks/LocalizationContext";
import { getAnalysis } from "@/helpers/DetailHelpers";
import { Text } from "@/components/ui/Text";
import Markdown from "react-native-markdown-display";
import { ScrollView, View } from "react-native";
import AnalysisTab from "@/components/detail/AnalysisTab";
import FundamentalAnalysisMetricsSection from "@/components/detail/FundamentalAnalysisMetricsSection";
import PriceCandleChart from "@/components/ui/PriceCandleChart";
import PriceLineGraph from "@/components/ui/PriceLineChart";
import { fetchStockData, StockData } from "@/helpers/DetailHelpers";
import ScreenHeader from "@/components/ui/ScreenHeader";

interface Props {
    stockSymbol: string
}

const Analysis = ({stockSymbol}: Props) => {
    const { theme } = useTheme();
    const { t } = useLocalization();

    const [fundamentalAnalysis, setFundamentalAnalysis] = useState<string>('')
    const [ technicalAnalysis, setTechnicalAnalysis] = useState<string>('')
    const [summary, setSummary] = useState<string>('')
  
    const [tab, setTab] = useState<"fun" | "tech" | "ovr">("fun");


  const [stockData, setStockData] = useState<StockData[]>([]);


  useEffect(() => {
    fetchStockData(stockSymbol, "1D").then((res) => {
      if (res.status) {
        setStockData(res.data);
      }
    });
  }, [stockSymbol]);


    useEffect(() => {
        getAnalysis('','','').then((res) => {
            if (res.status) {
                setFundamentalAnalysis(res.data?.fundamental_analysis ?? '');
                setTechnicalAnalysis(res.data?.technical_analysis ?? '')
                setSummary(res.data?.final_report ?? '');
            }
          })
    },[])

   return  <SafeAreaView
   style={{ flex: 1, backgroundColor: theme.background.bg }}
 >  
 <ScreenHeader title={t("detail.screenTitle")} />

    <AnalysisTab tab={tab} setTab={setTab}/>

 <ScrollView>

    {tab === 'fun' && <View>
        <Text typography="titleLarge" style={{marginTop: 24}}>
        {"Fundamental Analysis: "}
        </Text>

        <FundamentalAnalysisMetricsSection stock_symbol={stockSymbol} />

        <Markdown>
        {fundamentalAnalysis}
        </Markdown>
    </View>}

    {tab === 'tech' && <View>
        <Text typography="titleLarge" style={{marginTop: 24}}>
        {"Technical Analysis: "}
        </Text>
        <PriceLineGraph  data={stockData}/>
        <PriceCandleChart data={stockData} />
        <Markdown>
          {technicalAnalysis}
        </Markdown>
    </View>}

    { tab === 'ovr' && <View>
        <Text typography="titleLarge" style={{marginTop: 24}}>
        {"Summary: "}
        </Text>
        <Markdown>
          {summary}
        </Markdown>
    </View>}
 </ScrollView>
 </SafeAreaView>
}

export default Analysis