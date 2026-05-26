import ScreenHeader from "@/components/ui/ScreenHeader";
import PriceChartComponent from "@/components/detail/PriceChartComponent";
import { useTheme } from "@/hooks/ThemeContext";
import React from "react";
import { ScrollView, View } from "react-native";
import { useLocalSearchParams } from "expo-router";
import { MarketIndex } from "@/helpers/MarketHelpers";

const IndexDetail = () => {
  const { theme } = useTheme();
  const { data } = useLocalSearchParams() || {};
  const indexItem: MarketIndex = data ? JSON.parse(data as string) : null;

  return (
    <View style={{ flex: 1, backgroundColor: theme.background.surface }}>
      <ScreenHeader title={indexItem?.IndexName ?? "Chi tiết chỉ số"} />
      <ScrollView
        style={{
          flex: 1,
          backgroundColor: theme.background.surface,
        }}
      >
        {indexItem && (
          <PriceChartComponent
            symbol={indexItem?.IndexId}
            isMarketIndex={true}
          />
        )}

        <View style={{ height: 84 }} />
      </ScrollView>
    </View>
  );
};

export default IndexDetail;
