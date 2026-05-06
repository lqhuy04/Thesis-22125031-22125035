import React, { useState } from "react";
import { useTheme } from "@/hooks/ThemeContext";
import MarketIndicesSection from "@/components/market/MarketIndicesSection";
import MacroEcomNewsSection from "@/components/market/MacroEcomNewsSection";
import { ScrollView, TouchableOpacity, View } from "react-native";
import CategoriesNewsSection from "@/components/market/CategoriesNewsSection";
import { SearchBar } from "@/components/ui/SearchBar";
import AllNewsSection from "@/components/market/AllNewsSection";
import BusinessNewsSection from "@/components/market/BusinessNewsSection";
import IndustryMovementSection from "@/components/market/IndustryMovementSection";
import TodayHighlightSection from "@/components/market/TodayHighlightSection";
import { router } from "expo-router";
import { Text } from "@/components/ui/Text";

const TABS = [
  { key: "market", label: "Thị trường" },
  { key: "news", label: "Tin tức" },
];

const Market = () => {
  const { theme } = useTheme();
  const [activeTab, setActiveTab] = useState<"market" | "news">("market");

  return (
    <View
      style={{
        flex: 1,
        backgroundColor: theme.background.bg,
        paddingTop: 24,
      }}
    >
      {/* Search Bar */}
      <TouchableOpacity onPress={() => router.push("/Search")}>
        <View
          style={{ marginRight: 8, marginHorizontal: 12 }}
          pointerEvents="none"
        >
          <SearchBar value={""} onChange={() => {}} />
        </View>
      </TouchableOpacity>

      {/* Tab Bar */}
      <View
        style={{
          flexDirection: "row",
          marginVertical: 12,
          marginHorizontal: 12,
          gap: 8,
        }}
      >
        {TABS.map((tab) => {
          const isActive = activeTab === tab.key;
          return (
            <TouchableOpacity
              key={tab.key}
              onPress={() => setActiveTab(tab.key as "market" | "news")}
              style={{
                flex: 1,
                paddingVertical: 8,
                alignItems: "center",
                borderRadius: 8,
                backgroundColor: isActive ? theme.base.primary : "transparent",
                borderWidth: 1,
                borderColor: isActive
                  ? theme.base.primary
                  : theme.border.default,
              }}
            >
              <Text
                typography="labelLarge"
                color={isActive ? theme.text.onPrimary : theme.text.primary}
              >
                {tab.label}
              </Text>
            </TouchableOpacity>
          );
        })}
      </View>

      {/* Tab Content - dùng display thay vì unmount để tránh gọi API lại */}
      <ScrollView
        style={{
          display: activeTab === "market" ? "flex" : "none",
          backgroundColor: theme.background.bg,
          flex: 1,
        }}
      >
        <MarketIndicesSection />
        <IndustryMovementSection />
      </ScrollView>

      <ScrollView
        style={{
          display: activeTab === "news" ? "flex" : "none",
          backgroundColor: theme.background.bg,
          flex: 1,
        }}
      >
        <TodayHighlightSection />
        <BusinessNewsSection />
        <CategoriesNewsSection />
        <MacroEcomNewsSection />
        <AllNewsSection />
      </ScrollView>
    </View>
  );
};

export default Market;
