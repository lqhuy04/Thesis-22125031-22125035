import React, { useRef, useState } from "react";
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

const { width: SCREEN_WIDTH } = Dimensions.get("window");
const TAB_COUNT = 4;
const TAB_WIDTH = SCREEN_WIDTH / TAB_COUNT;
const INDICATOR_WIDTH = 48;

const Tabs = () => {
  const { t } = useLocalization();

  const TABS = [
    {
      name: "Home",
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
      name: "Profile",
      label: t("tabs.profile"),
      icon: "person-outline" as const,
      component: <Profile />,
    },
    {
      name: "Chatbot",
      label: t("tabs.chatbot"),
      icon: "chatbubble-ellipses-outline" as const,
      component: <Chatbot />,
    },
  ];

  const insets = useSafeAreaInsets();

  const { theme } = useTheme();
  const pagerRef = useRef<PagerView>(null);
  const [activeIndex, setActiveIndex] = useState(0);

  // Animated value: 0 → TAB_COUNT-1
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
    animateTo(index);
  };

  const handlePageSelected = (index: number) => {
    setActiveIndex(index);
    animateTo(index);
  };

  // Translate X: center of each tab minus half indicator width
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
        onPageSelected={(e) => handlePageSelected(e.nativeEvent.position)}
        overdrag={false}
      >
        {TABS.map((tab) => (
          <View key={tab.name} style={{ flex: 1 }}>
            {tab.component}
          </View>
        ))}
      </PagerView>

      {/* Tab Bar */}
      <View
        style={[
          styles.tabBar,
          {
            backgroundColor: theme.background.bg,
            borderTopColor: theme.border.default,
            paddingBottom: insets.bottom,
            height: 60 + insets.bottom, // tự động mở rộng
          },
        ]}
      >
        {/* Animated indicator line */}
        <Animated.View
          style={[
            styles.indicator,
            {
              backgroundColor: theme.base.primary,
              transform: [{ translateX }],
            },
          ]}
        />

        {TABS.map((tab, index) => {
          const focused = activeIndex === index;
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
              <Text typography="labelLarge" color={color}>
                {tab.label}
              </Text>
            </TouchableOpacity>
          );
        })}
      </View>
    </View>
  );
};

const styles = StyleSheet.create({
  tabBar: {
    flexDirection: "row",
    paddingTop: 10,
    borderTopWidth: 1,
    position: "relative",
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
  },
});

export default Tabs;
