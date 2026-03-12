import FundamentalAnalysisMetricsSection from "@/components/detail/FundamentalAnalysisMetricsSection";
import IntroductionSection from "@/components/detail/IntroductionSection";
import NewsSection from "@/components/detail/NewsSection";
import BoardSection from "@/components/detail/BoardSection";
import DetailHeader from "@/components/ui/DetailHeader";
import ScreenHeader from "@/components/ui/ScreenHeader";
import { useLocalization } from "@/hooks/LocalizationContext";
import { useTheme } from "@/hooks/ThemeContext";
import React, { useCallback, useRef, useState } from "react";
import { ScrollView } from "react-native-gesture-handler";
import { SafeAreaView } from "react-native-safe-area-context";
import { View } from "react-native";
import {  useLocalSearchParams } from "expo-router";
import TabView from "@/components/detail/DetailTabView";
import PriceChartComponent from "@/components/detail/PriceChartComponent";

const Detail = () => {
  const { t } = useLocalization();
  const { theme } = useTheme();

  const { data } = useLocalSearchParams() || {};
  const stockItem = data ? JSON.parse(data as string) : null;

  const TABS = [
    {
      key: "profile",
      label: "Hồ sơ",
      subTabs: [
        { key: "introduction", label: "Giới thiệu" },
        { key: "board", label: "Lãnh đạo" },
      ],
    },
    { key: "news", label: "Tin tức" },
  ];

  const [activeTab, setActiveTab] = useState<string>(TABS[0]?.key ?? "");
  const [activeSubTab, setActiveSubTab] = useState<string | undefined>(
    TABS[0]?.subTabs?.[0]?.key ?? undefined
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
    [scrollTabIntoView]
  );

  /**
   * renderContent is called once per tab/subtab combination.
   * CachedTabContent inside TabView keeps the component mounted after
   * first render — so switching tabs won't trigger re-fetches or re-renders.
   */
  const renderContent = useCallback(
    (tabKey: string, subTabKey?: string): React.ReactNode => {
      if (tabKey === "profile" && subTabKey === "introduction") {
        return <IntroductionSection stockSymbol={stockItem.symbol} />;
      }
      if (tabKey === "profile" && subTabKey === "board") {
        return <BoardSection stockSymbol={stockItem.symbol} />;
      }
      if (tabKey === "news") {
        return <NewsSection stockSymbol={stockItem.symbol} />;
      }
      return null;
    },
    [stockItem?.symbol]
  );

  const renderHeaderContent = useCallback(()=> {
    return <View>
      <PriceChartComponent stockSymbol={stockItem.symbol}/>
      <FundamentalAnalysisMetricsSection stockSymbol={stockItem.symbol} />
    </View>
  },[])

  return (
    <SafeAreaView
      style={{
        flex: 1,
        backgroundColor: theme.background.bg,
      }}
    >
      <ScreenHeader title={t("detail.screenTitle")} />

      <DetailHeader item={stockItem} />

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

      {/* <TouchableOpacity
        onPress={() => {
          router.push({
            pathname: "/Analysis",
            params: { data: JSON.stringify({ stockSymbol: stockItem.symbol }) },
          });
        }}
        style={{
          position: "absolute",
          bottom: 24,
          right: 12,
          height: 40,
          width: 40,
          borderRadius: 20,
          backgroundColor: theme.base.primary,
          alignItems: "center",
          justifyContent: "center",
        }}
      >
        <Text typography="labelLarge" color={theme.text.onPrimary}>
          AI
        </Text>
      </TouchableOpacity> */}
    </SafeAreaView>
  );
};

export default Detail;