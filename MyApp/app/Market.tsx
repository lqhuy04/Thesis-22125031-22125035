import React, { useRef, useState } from "react";
import { useTheme } from "@/hooks/ThemeContext";
import MarketIndicesSection from "@/components/market/MarketIndicesSection";
import MacroEcomNewsSection from "@/components/market/MacroEcomNewsSection";
import {
  Animated,
  Dimensions,
  ScrollView,
  TouchableOpacity,
  View,
} from "react-native";
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
import LinearGradient from "react-native-linear-gradient";
import WatchlistSection from "@/components/market/WatchlistSection";

const TABS = ["market", "favorites", "news"] as const;
type Tab = (typeof TABS)[number];

const { width: SCREEN_WIDTH } = Dimensions.get("window");

const Market = () => {
  const { t } = useLocalization();
  const { theme } = useTheme();
  const [activeTab, setActiveTab] = useState<Tab>("market");
  const [visitedTabs, setVisitedTabs] = useState<Set<Tab>>(
    new Set<Tab>(["market"]),
  );
  const translateX = useRef(new Animated.Value(0)).current;
  const insets = useSafeAreaInsets();

  const TAB_LABELS: Record<Tab, string> = {
    market: t("market.tabMarket"),
    favorites: t("market.tabFavorites"),
    news: t("market.tabNews"),
  };

  const switchTab = (tab: Tab) => {
    const index = TABS.indexOf(tab);
    setActiveTab(tab);
    setVisitedTabs((prev) => new Set(prev).add(tab));
    Animated.spring(translateX, {
      toValue: -index * SCREEN_WIDTH,
      useNativeDriver: true,
      tension: 68,
      friction: 12,
    }).start();
  };

  return (
    <View style={{ flex: 1, backgroundColor: theme.background.surface }}>
      {/* Search Bar */}

      <LinearGradient colors={["#613DE4", "#7B5CFF", "#9D8CFF"]}>
        <View style={{ paddingTop: insets.top + 12, paddingBottom: 12 }}>
          <TouchableOpacity onPress={() => router.push("/Search")}>
            <View style={{ marginHorizontal: 12 }} pointerEvents="none">
              <SearchBar value={""} onChange={() => {}} />
            </View>
          </TouchableOpacity>
        </View>
      </LinearGradient>

      {/* Tab Bar */}
      <View
        style={{
          flexDirection: "row",
          backgroundColor: theme.background.bg,
          marginBottom: 12,
          // Shadow iOS
          shadowColor: "#000",
          shadowOffset: { width: 0, height: 2 },
          shadowOpacity: 0.08,
          shadowRadius: 4,
          // Shadow Android
          elevation: 4,
        }}
      >
        {TABS.map((tab) => {
          const isActive = activeTab === tab;
          return (
            <TouchableOpacity
              key={tab}
              onPress={() => switchTab(tab)}
              style={{
                flex: 1,
                paddingVertical: 8,
                alignItems: "center",
                borderBottomWidth: 2,
                borderBottomColor: isActive
                  ? theme.base.primary
                  : "transparent",
              }}
            >
              <Text
                typography="bodyLarge"
                color={isActive ? theme.base.primary : theme.text.primary}
              >
                {TAB_LABELS[tab]}
              </Text>
            </TouchableOpacity>
          );
        })}
      </View>

      {/* Sliding content */}
      <View style={{ flex: 1, overflow: "hidden" }}>
        <Animated.View
          style={{
            flex: 1,
            flexDirection: "row",
            width: SCREEN_WIDTH * TABS.length,
            transform: [{ translateX }],
          }}
        >
          {/* Tab 0 — Market */}
          <ScrollView style={{ width: SCREEN_WIDTH }}>
            {visitedTabs.has("market") && (
              <>
                <MarketIndicesSection />
                <IndustryMovementSection />
                <View style={{ height: 24 }} />
              </>
            )}
          </ScrollView>

          {/* Tab 1 — Favorites */}
          <ScrollView style={{ width: SCREEN_WIDTH }}>
            {visitedTabs.has("favorites") && (
              <>
                <WatchlistSection />
                <View style={{ height: 24 }} />
              </>
            )}
          </ScrollView>

          {/* Tab 2 — News */}
          <ScrollView style={{ width: SCREEN_WIDTH }}>
            {visitedTabs.has("news") && (
              <>
                <TodayHighlightSection />
                <BusinessNewsSection />
                <CategoriesNewsSection />
                <MacroEcomNewsSection />
                <AllNewsSection />
                <View style={{ height: 24 }} />
              </>
            )}
          </ScrollView>
        </Animated.View>
      </View>
    </View>
  );
};

export default Market;
