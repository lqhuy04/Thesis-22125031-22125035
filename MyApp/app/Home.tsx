import React, { useState, useCallback, useRef } from "react";
import { useTheme } from "@/hooks/ThemeContext";
import MarketIndicesSection from "@/components/market/MarketIndicesSection";
import {
  ScrollView,
  View,
  RefreshControl,
  ActivityIndicator,
} from "react-native";
import HomeAssetSection from "@/components/home/HomeAssetSection";
import HomeNewSection from "@/components/home/HomeNewSection";

const Home = () => {
  const { theme } = useTheme();
  const [refreshing, setRefreshing] = useState(false);

  // Mỗi component con đăng ký hàm refresh của mình vào đây
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
    <View style={{ flex: 1 }}>
      <View
        style={{
          position: "absolute",
          top: 0,
          left: 0,
          right: 0,
          bottom: 0,
          flex: 1,
        }}
        pointerEvents="none"
      >
        <View style={{ flex: 1, backgroundColor: theme.base.primary }} />
        <View style={{ flex: 1, backgroundColor: theme.background.bg }} />
      </View>

      <ScrollView
        style={{ flex: 1 }}
        refreshControl={
          <RefreshControl refreshing={refreshing} onRefresh={onRefresh} />
        }
      >
        {refreshing ? (
          <ActivityIndicator
            color={theme.text.onPrimary}
            style={{ alignSelf: "center" }}
          />
        ) : null}

        <HomeAssetSection registerRefresh={registerRefresh} />

        <View
          style={{
            flex: 1,
            backgroundColor: theme.background.bg,
            borderTopLeftRadius: 12,
            borderTopRightRadius: 12,
            paddingVertical: 12,
            marginTop: -12,
          }}
        >
          <MarketIndicesSection registerRefresh={registerRefresh} />
          <HomeNewSection registerRefresh={registerRefresh} />
        </View>
      </ScrollView>
    </View>
  );
};

export default Home;
