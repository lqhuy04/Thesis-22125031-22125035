import React from "react";
import { useTheme } from "@/hooks/ThemeContext";
import MarketIndicesSection from "@/components/market/MarketIndicesSection";
import MacroEcomNewsSection from "@/components/market/MacroEcomNewsSection";
import { ScrollView, TouchableOpacity, View } from "react-native";
import CategoriesNewsSection from "@/components/market/CategoriesNewsSection";
import { SearchBar } from "@/components/ui/SearchBar";
import { router } from "expo-router";
import { Ionicons } from "@expo/vector-icons";
import { SafeAreaView } from "react-native-safe-area-context";
import AllNewsSection from "@/components/market/AllNewsSection";
import BusinessNewsSection from "@/components/market/BusinessNewsSection";
import IndustryMovementSection from "@/components/market/IndustryMovementSection";
import TodayHighlightSection from "@/components/market/TodayHighlightSection";

const Home = () => {
  const { theme } = useTheme();

  return (
    <SafeAreaView style={{ flex: 1 }}>
      <TouchableOpacity
        style={{
          flexDirection: "row",
          alignItems: "center",
          paddingHorizontal: 12,
          backgroundColor: theme.background.bg,
        }}
        onPress={() => router.push("/Search")}
        activeOpacity={1}
      >
        <View style={{ flex: 1, marginRight: 8 }} pointerEvents="none">
          <SearchBar value={""} onChange={() => {}} />
        </View>

        <TouchableOpacity
          onPress={() => router.push("/Profile")}
          style={{
            borderWidth: 1,
            borderColor: theme.border.default,
            borderRadius: 5,
            paddingVertical: 9.5,
            paddingHorizontal: 12,
            marginTop: 4,
          }}
        >
          <Ionicons
            name="person-outline"
            size={20}
            color={theme.text.primary}
          />
        </TouchableOpacity>
      </TouchableOpacity>

      <ScrollView
        style={{ padding: 12, backgroundColor: theme.background.bg, flex: 1 }}
      >
        <MarketIndicesSection />

        <IndustryMovementSection />

        <TodayHighlightSection />

        <BusinessNewsSection />

        <CategoriesNewsSection />

        <MacroEcomNewsSection />

        <AllNewsSection />
      </ScrollView>
    </SafeAreaView>
  );
};

export default Home;
