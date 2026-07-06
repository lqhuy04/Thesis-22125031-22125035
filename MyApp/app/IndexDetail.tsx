import ScreenHeader from "@/components/ui/ScreenHeader";
import { useTheme } from "@/hooks/ThemeContext";
import React, { useCallback, useRef, useState } from "react";
import { RefreshControl, ScrollView, View } from "react-native";
import { useLocalSearchParams } from "expo-router";
import { MarketIndex } from "@/helpers/MarketHelpers";
import PriceChartComponent from "@/components/detail/PriceChartComponent";

const IndexDetail = () => {
  const { theme } = useTheme();
  const { data } = useLocalSearchParams() || {};
  const indexItem: MarketIndex = data ? JSON.parse(data as string) : null;

  const [refreshing, setRefreshing] = useState(false);

  // Component con đăng ký hàm refresh của mình vào đây
  const refreshFns = useRef<(() => Promise<void>)[]>([]);

  const registerRefresh = useCallback((fn: () => Promise<void>) => {
    refreshFns.current.push(fn);
    return () => {
      refreshFns.current = refreshFns.current.filter((f) => f !== fn);
    };
  }, []);

  const onRefresh = useCallback(async () => {
    setRefreshing(true);
    try {
      await Promise.all(refreshFns.current.map((fn) => fn()));
    } finally {
      setRefreshing(false);
    }
  }, []);

  return (
    <View style={{ flex: 1, backgroundColor: theme.background.surface }}>
      <ScreenHeader title={indexItem?.IndexName ?? "Chi tiết chỉ số"} />
      <ScrollView
        style={{
          flex: 1,
          backgroundColor: theme.background.surface,
        }}
        refreshControl={
          <RefreshControl refreshing={refreshing} onRefresh={onRefresh} />
        }
      >
        {indexItem && (
          <PriceChartComponent
            symbol={indexItem?.IndexId}
            isMarketIndex={true}
            registerRefresh={registerRefresh}
          />
        )}

        <View style={{ height: 84 }} />
      </ScrollView>
    </View>
  );
};

export default IndexDetail;
