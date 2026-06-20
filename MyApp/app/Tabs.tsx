import React, { useEffect, useRef, useState } from "react";
import {
  View,
  TouchableOpacity,
  StyleSheet,
  Animated,
  Dimensions,
} from "react-native";
import PagerView from "react-native-pager-view";
import { Ionicons } from "@expo/vector-icons";
import { useTheme } from "@/hooks/ThemeContext";
import Home from "./Home";
import Profile from "./Profile";
import Market from "./Market";
import Chatbot from "./Chatbot";
import { Text } from "@/components/ui/Text";
import { useSafeAreaInsets } from "react-native-safe-area-context";
import { useLocalization } from "@/hooks/LocalizationContext";
import WatchListStock from "./WatchListStock";
import Octicons from "@expo/vector-icons/Octicons";
import { SWITCH_TAB_EVENT, tabEvents } from "@/helpers/api/tabEvents";

const { width: SCREEN_WIDTH } = Dimensions.get("window");
const FEATURED_SIZE = 48;
const TAB_BAR_HEIGHT = 60;
const TAB_COUNT = 5;
const TAB_WIDTH = SCREEN_WIDTH / TAB_COUNT;
const INDICATOR_WIDTH = 48;

const Tabs = () => {
  const { t } = useLocalization();
  const insets = useSafeAreaInsets();
  const { theme } = useTheme();
  const pagerRef = useRef<PagerView>(null);
  const [activeIndex, setActiveIndex] = useState(0);
  const [visitedTabs, setVisitedTabs] = useState<Set<number>>(new Set([0]));

  const TABS = [
    {
      name: "Overview",
      label: t("tabs.home"),
      icon: "home-outline" as const,
      component: <Home />,
    },
    {
      name: "Market",
      label: t("tabs.market"),
      icon: "storefront-outline" as const,
      component: <Market />,
    },
    {
      name: "Chatbot",
      label: t("tabs.chatbot"),
      icon: "chatbubble-ellipses-outline" as const,
      component: <Chatbot />,
      featured: true,
    },
    {
      name: "Assets",
      label: t("tabs.assets"),
      icon: "wallet-outline" as const,
      component: <WatchListStock />,
    },
    {
      name: "Profile",
      label: t("tabs.profile"),
      icon: "person-outline" as const,
      component: <Profile />,
    },
  ];

  const indicatorAnim = useRef(new Animated.Value(0)).current;

  const animateTo = (index: number) => {
    Animated.spring(indicatorAnim, {
      toValue: index,
      useNativeDriver: true,
      tension: 80,
      friction: 12,
    }).start();
  };

  const handleTabPress = (index: number) => {
    pagerRef.current?.setPage(index);
    setActiveIndex(index);
    setVisitedTabs((prev) => new Set(prev).add(index));
    animateTo(index);
  };

  useEffect(() => {
    const handler = (index: number) => handleTabPress(index);
    tabEvents.on(SWITCH_TAB_EVENT, handler);
    return () => {
      tabEvents.off(SWITCH_TAB_EVENT, handler);
    };
  }, []);

  const translateX = indicatorAnim.interpolate({
    inputRange: TABS.map((_, i) => i),
    outputRange: TABS.map(
      (_, i) => i * TAB_WIDTH + TAB_WIDTH / 2 - INDICATOR_WIDTH / 2,
    ),
  });

  return (
    <View style={{ flex: 1 }}>
      <PagerView
        ref={pagerRef}
        style={{ flex: 1 }}
        initialPage={0}
        onPageSelected={(e) => {
          const idx = e.nativeEvent.position;
          setActiveIndex(idx);
          setVisitedTabs((prev) => new Set(prev).add(idx));
          animateTo(idx);
        }}
        overdrag={false}
      >
        {TABS.map((tab, index) => (
          <View key={tab.name} style={{ flex: 1 }}>
            {visitedTabs.has(index) ? tab.component : null}
          </View>
        ))}
      </PagerView>

      {/* Tab Bar */}
      <View
        style={[
          styles.tabBarWrapper,
          {
            height: TAB_BAR_HEIGHT + insets.bottom,
            paddingBottom: insets.bottom,
            backgroundColor: theme.background.bg,
            zIndex: 1,
          },
        ]}
      >
        {/* Animated indicator — transparent khi ở Chatbot (index 2) */}
        <Animated.View
          style={[
            styles.indicator,
            {
              backgroundColor:
                activeIndex === 2 ? "transparent" : theme.base.primary,
              transform: [{ translateX }],
            },
          ]}
        />

        {TABS.map((tab, index) => {
          const focused = activeIndex === index;
          const isFeatured = !!tab.featured;

          if (isFeatured) {
            return <View key={tab.name} style={{ flex: 1 }} />;
          }

          const color = focused
            ? theme.base.primary
            : theme.text.primary + "80";

          return (
            <TouchableOpacity
              key={tab.name}
              style={styles.tabItem}
              onPress={() => handleTabPress(index)}
              activeOpacity={0.7}
            >
              <Ionicons name={tab.icon} size={24} color={color} />
              <Text typography="bodySmall" color={color}>
                {tab.label}
              </Text>
            </TouchableOpacity>
          );
        })}
      </View>

      {/* Featured button nổi */}
      <View
        style={{
          position: "absolute",
          bottom: insets.bottom,
          zIndex: 2,
          alignSelf: "center",
        }}
      >
        <View
          style={{
            width: 60,
            height: 60,
            borderRadius: 30,
            backgroundColor: theme.background.bg,
            marginBottom: -2,
          }}
        >
          <TouchableOpacity
            style={styles.featuredWrapper}
            onPress={() => handleTabPress(2)}
            activeOpacity={0.85}
          >
            <View
              style={[
                styles.featuredCircle,
                { backgroundColor: theme.base.primary },
              ]}
            >
              <Octicons
                name="dependabot"
                size={32}
                color={theme.text.onPrimary}
              />
            </View>
          </TouchableOpacity>
        </View>

        <View
          style={{
            paddingVertical: 1,
            paddingHorizontal: 4,
            borderRadius: 8,
            backgroundColor: theme.base.primary,
            justifyContent: "center",
            alignItems: "center",
          }}
        >
          <Text typography="bodySmall" color={theme.text.onPrimary}>
            {TABS[2].label}
          </Text>
        </View>
      </View>
    </View>
  );
};

const styles = StyleSheet.create({
  tabBarWrapper: {
    flexDirection: "row",
    alignItems: "center",
    overflow: "visible",
    shadowColor: "#000",
    shadowOffset: { width: 0, height: -2 },
    shadowOpacity: 0.08,
    shadowRadius: 12,
    elevation: 20,
  },
  indicator: {
    position: "absolute",
    top: 0,
    width: INDICATOR_WIDTH,
    height: 2.5,
    borderRadius: 2,
  },
  tabItem: {
    flex: 1,
    alignItems: "center",
    justifyContent: "center",
    gap: 4,
    marginTop: 12,
  },
  featuredWrapper: {
    flex: 1,
    alignItems: "center",
    justifyContent: "center",
    marginBottom: 0,
    marginTop: 2,
  },
  featuredCircle: {
    width: FEATURED_SIZE,
    height: FEATURED_SIZE,
    borderRadius: FEATURED_SIZE / 2,
    alignItems: "center",
    justifyContent: "center",
  },
});

export default Tabs;
