import React, { useCallback, useRef, useState } from "react";
import { RefreshControl, ScrollView, View } from "react-native";
import { useTheme } from "@/hooks/ThemeContext";
import TodayHighlightSection from "@/components/market/TodayHighlightSection";
import BusinessNewsSection from "@/components/market/BusinessNewsSection";
import CategoriesNewsSection from "@/components/market/CategoriesNewsSection";
import MacroEcomNewsSection from "@/components/market/MacroEcomNewsSection";
import AllNewsSection from "@/components/market/AllNewsSection";
import { useSafeAreaInsets } from "react-native-safe-area-context";

const News = () => {
  const { theme } = useTheme();
  const insets = useSafeAreaInsets();
  const [refreshing, setRefreshing] = useState(false);

  // Mỗi section con đăng ký hàm refresh của mình vào đây
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
    <View
      style={{
        flex: 1,
        backgroundColor: theme.background.surface,
        paddingTop: insets.top + 12,
      }}
    >
      <ScrollView
        refreshControl={
          <RefreshControl refreshing={refreshing} onRefresh={onRefresh} />
        }
      >
        <TodayHighlightSection registerRefresh={registerRefresh} />
        <BusinessNewsSection registerRefresh={registerRefresh} />
        <CategoriesNewsSection registerRefresh={registerRefresh} />
        <MacroEcomNewsSection registerRefresh={registerRefresh} />
        <AllNewsSection registerRefresh={registerRefresh} />
        <View style={{ height: 24 }} />
      </ScrollView>
    </View>
  );
};

export default News;
