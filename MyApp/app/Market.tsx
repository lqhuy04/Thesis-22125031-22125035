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
import { useSafeAreaInsets } from "react-native-safe-area-context";
import { useLocalization } from "@/hooks/LocalizationContext";

const Market = () => {
  const { t } = useLocalization();
  const { theme } = useTheme();
  const [activeTab, setActiveTab] = useState<"market" | "news">("market");

  const TABS = [
    { key: "market", label: t("market.tabMarket") },
    { key: "news", label: t("market.tabNews") },
  ];

  const insets = useSafeAreaInsets();

  return (
    <View
      style={{
        flex: 1,
        backgroundColor: theme.background.surface,
        paddingTop: insets.top,
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
          marginVertical: 16,
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
                paddingVertical: 6,
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
                typography="bodyLarge"
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
          flex: 1,
        }}
      >
        <MarketIndicesSection />
        <IndustryMovementSection />
        <View style={{ height: 24 }} />
      </ScrollView>

      <ScrollView
        style={{
          display: activeTab === "news" ? "flex" : "none",
          flex: 1,
        }}
      >
        <TodayHighlightSection />
        <BusinessNewsSection />
        <CategoriesNewsSection />
        <MacroEcomNewsSection />
        <AllNewsSection />
        <View style={{ height: 24 }} />
      </ScrollView>
    </View>
  );
};

export default Market;
