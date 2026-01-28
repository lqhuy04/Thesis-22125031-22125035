import React, { useEffect, useState } from "react";
import { SafeAreaView } from "react-native-safe-area-context";
import { useTheme } from "@/hooks/ThemeContext";
import { useLocalization } from "@/hooks/LocalizationContext";
import { Text } from "@/components/ui/Text";
import Markdown from "react-native-markdown-display";
import { ScrollView, View } from "react-native";
import AnalysisTab from "@/components/detail/AnalysisTab";
import FundamentalAnalysisMetricsSection from "@/components/detail/FundamentalAnalysisMetricsSection";
import PriceCandleChart from "@/components/ui/PriceCandleChart";
import PriceLineGraph from "@/components/ui/PriceLineChart";
import {
  fetchStockData,
  StockData,
  getAnalysis,
  FundamentalAnalysisIndexes,
  fetchFundamentalAnalysisIndexes,
} from "@/helpers/DetailHelpers";
import ScreenHeader from "@/components/ui/ScreenHeader";

interface Props {
  stockSymbol: string;
}

const Analysis = ({ stockSymbol }: Props) => {
  const { theme } = useTheme();
  const { t } = useLocalization();

  const [tab, setTab] = useState<"fun" | "tech" | "ovr">("fun");

  const [fundamentalAnalysis, setFundamentalAnalysis] = useState<string>("");
  const [technicalAnalysis, setTechnicalAnalysis] = useState<string>("");
  const [summary, setSummary] = useState<string>("");

  const [stockData, setStockData] = useState<StockData[]>([]);

  const [metrics, setMetrics] = useState<FundamentalAnalysisIndexes | null>(
    null,
  );

  useEffect(() => {
    if (!stockSymbol) return;

    const fetchAll = async () => {
      try {
        const [fundamentalRes, stockRes] = await Promise.all([
          fetchFundamentalAnalysisIndexes(stockSymbol),
          fetchStockData(stockSymbol, "1D"),
        ]);

        if (fundamentalRes?.status) {
          setMetrics(fundamentalRes.data);
        }

        if (stockRes?.status) {
          setStockData(stockRes.data);
        }

        const analysisRes = await getAnalysis(stockSymbol, "", "");

        if (analysisRes?.status) {
          setFundamentalAnalysis(analysisRes.data?.fundamental_analysis ?? "");
          setTechnicalAnalysis(analysisRes.data?.technical_analysis ?? "");
          setSummary(analysisRes.data?.final_report ?? "");
        }
      } catch (error) {
        console.error("Error fetching stock analysis:", error);
      }
    };

    fetchAll();
  }, [stockSymbol]);

  return (
    <SafeAreaView style={{ flex: 1, backgroundColor: theme.background.bg }}>
      <ScreenHeader title={t("detail.screenTitle")} />

      <AnalysisTab tab={tab} setTab={setTab} />

      <ScrollView>
        {tab === "fun" && (
          <View>
            <Text typography="titleLarge" style={{ marginTop: 24 }}>
              {"Fundamental Analysis: "}
            </Text>

            <FundamentalAnalysisMetricsSection metrics={metrics} />

            <Markdown>{fundamentalAnalysis}</Markdown>
          </View>
        )}

        {tab === "tech" && (
          <View>
            <Text typography="titleLarge" style={{ marginTop: 24 }}>
              {"Technical Analysis: "}
            </Text>
            <PriceLineGraph data={stockData} />
            <PriceCandleChart data={stockData} />
            <Markdown>{technicalAnalysis}</Markdown>
          </View>
        )}

        {tab === "ovr" && (
          <View>
            <Text typography="titleLarge" style={{ marginTop: 24 }}>
              {"Summary: "}
            </Text>
            <Markdown>{summary}</Markdown>
          </View>
        )}
      </ScrollView>
    </SafeAreaView>
  );
};

export default Analysis;
