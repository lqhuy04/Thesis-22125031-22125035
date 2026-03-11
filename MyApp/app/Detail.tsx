import FundamentalAnalysisMetricsSection from "@/components/detail/FundamentalAnalysisMetricsSection";
import IntroductionSection from "@/components/detail/IntroductionSection";
import NewsSection from "@/components/detail/NewsSection";
import PriceChartComponent from "@/components/detail/PriceChartComponent";
import DetailHeader from "@/components/ui/DetailHeader";
import ScreenHeader from "@/components/ui/ScreenHeader";
import { useLocalization } from "@/hooks/LocalizationContext";
import { useTheme } from "@/hooks/ThemeContext";
import React, { useEffect, useState } from "react";
import { ScrollView } from "react-native-gesture-handler";
import { SafeAreaView } from "react-native-safe-area-context";
import { Platform, TouchableOpacity, View } from "react-native";
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
    { key: "posts", label: "Bài viết" },
    { key: "photos", label: "Ảnh" },
    { key: "videos", label: "Video" },
    { key: "likes", label: "Yêu thích" },
    { key: "mentions", label: "Đề cập" },
  ];

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
        stickyHeaderIndices={[4]}
        showsVerticalScrollIndicator={false}
        bounces={Platform.OS === "ios"}
      >
        <DetailHeader item={stockItem} priceData={priceData} />

        {/* <PriceChartComponent
          stockSymbol={stockItem.symbol}
          referencePrice={priceData?.reference_price ?? 0}
        /> */}

        <FundamentalAnalysisMetricsSection stockSymbol={stockItem.symbol} />

        <IntroductionSection />

        <NewsSection stockSymbol={stockItem.symbol} />

        <StickyTabView
          accentColor="#6C63FF"
          tabs={TABS}
          renderTabContent={(key) => {
            switch (key) {
              default:
                return (
                  <View
                    style={{
                      height: 1000,
                      alignItems: "center",
                      justifyContent: "center",
                    }}
                  >
                    <Text>Tab: {key}</Text>;
                  </View>
                );
            }
          }}
        />
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
