import IntroductionSection from "@/components/detail/IntroductionSection";
import NewsSection from "@/components/detail/NewsSection";
import BoardSection from "@/components/detail/BoardSection";
import ScreenHeader from "@/components/ui/ScreenHeader";
import { useLocalization } from "@/hooks/LocalizationContext";
import { useTheme } from "@/hooks/ThemeContext";
import React, { useCallback, useRef, useState } from "react";
import { ScrollView } from "react-native-gesture-handler";
import { SafeAreaView } from "react-native-safe-area-context";
import { View } from "react-native";
import { useLocalSearchParams } from "expo-router";
import TabView from "@/components/detail/DetailTabView";
import PriceChartComponent from "@/components/detail/PriceChartComponent";
import FinancialIndicatorsSection from "@/components/detail/FinancialIndicatorsSection";
import FinancialAnalysisSummarySection from "@/components/detail/FinancialAnalysisSummarySection";
import SummarizeAndRecommendSection from "@/components/detail/SummarizeAndRecommendSection";

const Detail = () => {
  const { t } = useLocalization();
  const { theme } = useTheme();

  const { data } = useLocalSearchParams() || {};
  const stockSymbol = (data as string) ?? "";

  const TABS = [
    {
      key: "profile",
      label: "Hồ sơ",
      subTabs: [
        { key: "introduction", label: "Giới thiệu" },
        { key: "board", label: "Lãnh đạo" },
      ],
    },
    {
      key: "fundamental-analysis",
      label: "Phân tích cơ bản",
      subTabs: [
        { key: "fundamental-analysis-info", label: "Thông tin" },
        { key: "fundamental-analysis-summary", label: "Tóm tắt" },
      ],
    },
    { key: "news", label: "Tin tức" },
    { key: "summary", label: "Tổng hợp và Gợi ý" },
  ];

  const [activeTab, setActiveTab] = useState<string>(TABS[0]?.key ?? "");
  const [activeSubTab, setActiveSubTab] = useState<string | undefined>(
    TABS[0]?.subTabs?.[0]?.key ?? undefined,
  );

  const tabScrollRef = useRef<ScrollView>(null);
  const tabRefs = useRef<{ [key: string]: number }>({});

  const scrollTabIntoView = useCallback((key: string) => {
    const x = tabRefs.current[key] ?? 0;
    tabScrollRef.current?.scrollTo({ x: Math.max(0, x - 24), animated: true });
  }, []);

  const handleTabPress = useCallback(
    (key: string, subTabKey?: string) => {
      setActiveTab(key);
      setActiveSubTab(subTabKey);
      scrollTabIntoView(key);
    },
    [scrollTabIntoView],
  );

  /**
   * renderContent is called once per tab/subtab combination.
   * CachedTabContent inside TabView keeps the component mounted after
   * first render — so switching tabs won't trigger re-fetches or re-renders.
   */
  const renderContent = useCallback(
    (tabKey: string, subTabKey?: string): React.ReactNode => {
      if (tabKey === "profile" && subTabKey === "introduction") {
        return <IntroductionSection stockSymbol={stockSymbol} />;
      }
      if (tabKey === "profile" && subTabKey === "board") {
        return <BoardSection stockSymbol={stockSymbol} />;
      }
      if (tabKey === "news") {
        return <NewsSection stockSymbol={stockSymbol} />;
      }
      if (tabKey === "summary") {
        return <SummarizeAndRecommendSection stockSymbol={stockSymbol} />;
      }
      if (
        tabKey === "fundamental-analysis" &&
        subTabKey === "fundamental-analysis-info"
      ) {
        return <FinancialIndicatorsSection stockSymbol={stockSymbol} />;
      }
      if (
        tabKey === "fundamental-analysis" &&
        subTabKey === "fundamental-analysis-summary"
      ) {
        return <FinancialAnalysisSummarySection stockSymbol={stockSymbol} />;
      }
      return null;
    },
    [stockSymbol],
  );

  const renderHeaderContent = useCallback(() => {
    return (
      <View>
        <PriceChartComponent symbol={stockSymbol} />
      </View>
    );
  }, [stockSymbol]);

  return (
    <SafeAreaView
      style={{
        flex: 1,
        backgroundColor: theme.background.bg,
      }}
    >
      <ScreenHeader title={t("detail.screenTitle")} />

      <TabView
        tabs={TABS}
        activeTab={activeTab}
        activeSubTab={activeSubTab}
        tabScrollRef={tabScrollRef}
        tabRefs={tabRefs}
        headerContent={renderHeaderContent}
        handleTabPress={handleTabPress}
        renderContent={renderContent}
      />
    </SafeAreaView>
  );
};

export default Detail;
