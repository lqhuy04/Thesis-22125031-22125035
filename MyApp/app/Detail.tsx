import FundamentalAnalysisMetricsSection from "@/components/detail/FundamentalAnalysisMetricsSection";
import IntroductionSection from "@/components/detail/IntroductionSection";
import NewsSection from "@/components/detail/NewsSection";
import PriceChartComponent from "@/components/detail/PriceChartComponent";
import DetailHeader from "@/components/ui/DetailHeader";
import ScreenHeader from "@/components/ui/ScreenHeader";
import { useLocalization } from "@/hooks/LocalizationContext";
import { useTheme } from "@/hooks/ThemeContext";
import React, { useCallback, useEffect, useRef, useState } from "react";
import { ScrollView } from "react-native-gesture-handler";
import { SafeAreaView } from "react-native-safe-area-context";
import { Platform, TouchableOpacity } from "react-native";
import { Text } from "@/components/ui/Text";
import { router, useLocalSearchParams } from "expo-router";
import { fetchPriceData, PriceData } from "@/helpers/DetailHelpers";
import StickyTabView from "@/components/ui/StickyTabView";

const Detail = () => {
  const { t } = useLocalization();
  const { theme } = useTheme();

  const { data } = useLocalSearchParams() || {};
  const stockItem = data ? JSON.parse(data as string) : null;

  const [priceData, setPriceData] = useState<PriceData | null>(null);

  useEffect(() => {
    fetchPriceData(stockItem.symbol).then((res) => {
      if (res.status) {
        setPriceData(res.data);
      }
    });
  }, [stockItem]);

  const TABS = [
    { key: "overview", label: "Hồ sơ" },
    { key: "news", label: "Tin tức" },
  ];

  const [activeTab, setActiveTab] = useState<string>(TABS[0]?.key ?? "");
  const tabScrollRef = useRef<ScrollView>(null);
  const tabRefs = useRef<{ [key: string]: number }>({});

  const scrollTabIntoView = useCallback((key: string) => {
    const x = tabRefs.current[key] ?? 0;
    tabScrollRef.current?.scrollTo({ x: Math.max(0, x - 24), animated: true });
  }, []);

  const handleTabPress = useCallback(
    (key: string) => {
      setActiveTab(key);
      scrollTabIntoView(key);
    },
    [scrollTabIntoView],
  );

  return (
    <SafeAreaView
      style={{
        flex: 1,
        backgroundColor: theme.background.bg,
      }}
    >
      <ScreenHeader title={t("detail.screenTitle")} />

      <ScrollView
        style={{ flex: 1 }}
        showsVerticalScrollIndicator={false}
        stickyHeaderIndices={[2]}
        bounces={Platform.OS === "ios"}
      >
        <DetailHeader item={stockItem} priceData={priceData} />
        {/* 
        <PriceChartComponent
          stockSymbol={stockItem.symbol}
          referencePrice={priceData?.reference_price ?? 0}
        /> */}

        <FundamentalAnalysisMetricsSection stockSymbol={stockItem.symbol} />

        <StickyTabView
          tabs={TABS}
          activeTab={activeTab}
          tabScrollRef={tabScrollRef}
          tabRefs={tabRefs}
          handleTabPress={handleTabPress}
        />

        {activeTab === "overview" ? (
          <IntroductionSection stockSymbol={stockItem.symbol} />
        ) : activeTab === "news" ? (
          <NewsSection stockSymbol={stockItem.symbol} />
        ) : null}
      </ScrollView>

      <TouchableOpacity
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
      </TouchableOpacity>
    </SafeAreaView>
  );
};

export default Detail;
