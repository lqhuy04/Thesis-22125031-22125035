import React, { useState, useCallback, useRef } from "react";
import { useTheme } from "@/hooks/ThemeContext";
import MarketIndicesSection from "@/components/market/MarketIndicesSection";
import { ScrollView, View, RefreshControl } from "react-native";
import HomeAssetSection from "@/components/home/HomeAssetSection";
import HomeNewSection from "@/components/home/HomeNewSection";
import LinearGradient from "react-native-linear-gradient";

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
        }}
        pointerEvents="none"
      >
        {/* Gradient phía trên */}
        <LinearGradient
          colors={[
            "#4B2FC9",
            "#613DE4",
            "#7B5CFF",
            "#9D8CFF",
            "#7B5CFF",
            "#613DE4",
            "#4B2FC9",
          ]}
          locations={[0, 0.1, 0.24, 0.5, 0.76, 0.82, 1]}
          useAngle
          angle={12}
          angleCenter={{ x: 0.5, y: 0.5 }}
          style={{
            height: 280,
          }}
        />

        {/* Gradient nối tiếp xuống dưới */}
        <LinearGradient
          colors={[
            "#4B2FC9",
            "#613DE4",
            "#7B5CFF",
            "#9D8CFF",
            "#7B5CFF",
            "#613DE4",
            "#4B2FC9",
          ]}
          locations={[0, 0.1, 0.24, 0.5, 0.76, 0.82, 1]}
          useAngle
          angle={168}
          angleCenter={{ x: 0.5, y: 0.5 }}
          style={{
            flex: 1,
          }}
        />

        <View style={{ flex: 1, backgroundColor: theme.background.surface }} />
      </View>

      <ScrollView
        style={{ flex: 1 }}
        refreshControl={
          <RefreshControl refreshing={refreshing} onRefresh={onRefresh} />
        }
      >
        <HomeAssetSection registerRefresh={registerRefresh} />

        <View
          style={{
            flex: 1,
            backgroundColor: theme.background.surface,
            borderTopLeftRadius: 12,
            borderTopRightRadius: 12,
            paddingVertical: 12,
            marginTop: -12,
          }}
        >
          <MarketIndicesSection registerRefresh={registerRefresh} />
          <HomeNewSection registerRefresh={registerRefresh} />
          <View style={{ height: 24 }} />
        </View>
      </ScrollView>
    </View>
  );
};

export default Home;
