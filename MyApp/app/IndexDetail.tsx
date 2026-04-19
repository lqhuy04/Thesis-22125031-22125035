import ScreenHeader from "@/components/ui/ScreenHeader";
import PriceChartComponent from "@/components/detail/PriceChartComponent";
import { useTheme } from "@/hooks/ThemeContext";
import React from "react";
import { ScrollView } from "react-native-gesture-handler";
import { SafeAreaView } from "react-native-safe-area-context";
import { useLocalSearchParams } from "expo-router";
import { MarketIndex } from "@/helpers/MarketHelpers";

const IndexDetail = () => {
  const { theme } = useTheme();
  const { data } = useLocalSearchParams() || {};
  const indexItem: MarketIndex = data ? JSON.parse(data as string) : null;

  return (
    <SafeAreaView style={{ flex: 1, backgroundColor: theme.background.bg }}>
      <ScreenHeader title={indexItem?.IndexName ?? "Chi tiết chỉ số"} />
      <ScrollView>
        {indexItem && (
          <PriceChartComponent
            symbol={indexItem?.IndexId}
            isMarketIndex={true}
          />
        )}
      </ScrollView>
    </SafeAreaView>
  );
};

export default IndexDetail;
