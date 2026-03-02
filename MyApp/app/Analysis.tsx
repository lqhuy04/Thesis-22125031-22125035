import React, { useEffect, useState } from "react";
import { SafeAreaView } from "react-native-safe-area-context";
import { useTheme } from "@/hooks/ThemeContext";
import { useLocalization } from "@/hooks/LocalizationContext";
import Markdown from "react-native-markdown-display";
import { ActivityIndicator, ScrollView, View } from "react-native";
import { getAnalysis } from "@/helpers/DetailHelpers";
import ScreenHeader from "@/components/ui/ScreenHeader";
import { useLocalSearchParams } from "expo-router";
import { Text } from "@/components/ui/Text";

const Analysis = () => {
  const { theme } = useTheme();
  const { t } = useLocalization();

  const [loading, setLoading] = useState<boolean>(false);

  const { data } = useLocalSearchParams() || {};
  const stockSymbol = data
    ? (JSON.parse(data as string) as { stockSymbol: string }).stockSymbol
    : null;

  const [newAnalysis, setNewAnalysis] = useState<string>("");
  const [fundamentalAnalysis, setFundamentalAnalysis] = useState<string>("");
  const [technicalAnalysis, setTechnicalAnalysis] = useState<string>("");
  const [summary, setSummary] = useState<string>("");

  useEffect(() => {
    if (!stockSymbol) return;

    setLoading(true);
    getAnalysis(stockSymbol).then((analysisRes) => {
      setLoading(false);
      if (analysisRes?.status) {
        setFundamentalAnalysis(analysisRes.data?.fundamental_analysis ?? "");
        setTechnicalAnalysis(analysisRes.data?.technical_analysis ?? "");
        setNewAnalysis(analysisRes.data?.news_analysis ?? "");
        setSummary(analysisRes.data?.recommendation ?? "");
      }
    });
  }, [stockSymbol]);

  return loading ? (
    <View
      style={{
        flex: 1,
        justifyContent: "center",
        alignItems: "center",
      }}
    >
      <ActivityIndicator size="large" color={theme.base.primary} />
    </View>
  ) : (
    <SafeAreaView style={{ flex: 1, backgroundColor: theme.background.bg }}>
      <ScreenHeader title={t("detail.screenTitle")} />

      <ScrollView style={{ flex: 1, padding: 12 }}>
        <Markdown>{newAnalysis}</Markdown>
        <Markdown>{fundamentalAnalysis}</Markdown>
        <Markdown>{technicalAnalysis}</Markdown>
        <Markdown>{summary}</Markdown>
      </ScrollView>
    </SafeAreaView>
  );
};

export default Analysis;
