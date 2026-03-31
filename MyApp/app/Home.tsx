import React from "react";
import { useTheme } from "@/hooks/ThemeContext";
import { SafeAreaView } from "react-native-safe-area-context";
import MarketIndicesSection from "@/components/market/MarketIndicesSection";
import MacroEcomNewsSection from "@/components/market/MacroEcomNewsSection";
import { ScrollView } from "react-native";
import CategoriesNewsSection from "@/components/market/CategoriesNewsSection";

const Home = () => {
  const { theme } = useTheme();

  return (
    <SafeAreaView
      style={{
        paddingHorizontal: 12,
        backgroundColor: theme.background.bg,
        flex: 1,
        paddingTop: 12,
      }}
    >
      <ScrollView style={{ flex: 1 }}>
        <MarketIndicesSection />

        <MacroEcomNewsSection />

        <CategoriesNewsSection />
      </ScrollView>
    </SafeAreaView>
  );
};

export default Home;
