import React from "react";
import { useTheme } from "@/hooks/ThemeContext";
import MarketIndicesSection from "@/components/market/MarketIndicesSection";
import { ScrollView, View } from "react-native";
import HomeAssetSection from "@/components/home/HomeAssetSection";
import HomeNewSection from "@/components/home/HomeNewSection";

const Home = () => {
  const { theme } = useTheme();

  return (
    <ScrollView
      style={{
        backgroundColor: theme.base.primary,
        flex: 1,
      }}
    >
      <View style={{ marginTop: 24 }}>
        <HomeAssetSection />
      </View>

      <View
        style={{
          flex: 1,
          backgroundColor: theme.background.bg,
          borderTopLeftRadius: 12,
          borderTopRightRadius: 12,
          paddingVertical: 12,
        }}
      >
        <MarketIndicesSection />

        <HomeNewSection />
      </View>
    </ScrollView>
  );
};

export default Home;
