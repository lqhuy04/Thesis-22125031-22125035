import React from "react";
import { useTheme } from "@/hooks/ThemeContext";
import MarketIndicesSection from "@/components/market/MarketIndicesSection";
import MacroEcomNewsSection from "@/components/market/MacroEcomNewsSection";
import { ScrollView } from "react-native";
import CategoriesNewsSection from "@/components/market/CategoriesNewsSection";

const Home = () => {
  const { theme } = useTheme();

  return (
    <ScrollView
      style={{ padding: 12, backgroundColor: theme.background.bg, flex: 1 }}
    >
      <MarketIndicesSection />

      <MacroEcomNewsSection />

      <CategoriesNewsSection />
    </ScrollView>
  );
};

export default Home;
