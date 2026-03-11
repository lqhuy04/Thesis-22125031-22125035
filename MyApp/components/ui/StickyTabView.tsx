import React, { useRef, useState, useCallback } from "react";
import {
  View,
  Text,
  ScrollView,
  TouchableOpacity,
  StyleSheet,
  Animated,
  Dimensions,
  FlatList,
  Platform,
  StatusBar,
} from "react-native";

const { width: SCREEN_WIDTH } = Dimensions.get("window");

// ─── Types ────────────────────────────────────────────────────────────────────

export interface TabItem {
  key: string;
  label: string;
}

export interface StickyTabViewProps {
  /** Tab definitions */
  tabs: TabItem[];
  /** Render content for each tab by key */
  renderTabContent: (tabKey: string) => React.ReactNode;
  /** Active tab indicator color (default: #6C63FF) */
  accentColor?: string;
  /** Background color of the tab bar (default: #fff) */
  tabBarBackground?: string;
}

// ─── Component ────────────────────────────────────────────────────────────────

const StickyTabView: React.FC<StickyTabViewProps> = ({
  tabs,
  renderTabContent,
  accentColor = "#6C63FF",
  tabBarBackground = "#ffffff",
}) => {
  const [activeTab, setActiveTab] = useState<string>(tabs[0]?.key ?? "");
  const tabScrollRef = useRef<ScrollView>(null);
  const tabRefs = useRef<{ [key: string]: number }>({});

  // ── Scroll active tab indicator into view ──
  const scrollTabIntoView = useCallback((key: string) => {
    const x = tabRefs.current[key] ?? 0;
    tabScrollRef.current?.scrollTo({ x: Math.max(0, x - 24), animated: true });
  }, []);

  const handleTabPress = useCallback(
    (key: string) => {
      setActiveTab(key);
      scrollTabIntoView(key);
    },
    [scrollTabIntoView],
  );

  return (
    // stickyHeaderIndices={[1]} makes the element at index 1 (TabBar) stick to the top
    <View style={styles.root}>
      {/* ── 1: Tab Bar (sticks to top) ── */}
      <View
        style={[styles.tabBarWrapper, { backgroundColor: tabBarBackground }]}
      >
        <ScrollView
          ref={tabScrollRef}
          horizontal
          showsHorizontalScrollIndicator={false}
          contentContainerStyle={styles.tabBarContent}
          bounces={false}
        >
          {tabs.map((tab) => {
            const isActive = tab.key === activeTab;
            return (
              <TouchableOpacity
                key={tab.key}
                activeOpacity={0.75}
                onPress={() => handleTabPress(tab.key)}
                onLayout={(e) => {
                  tabRefs.current[tab.key] = e.nativeEvent.layout.x;
                }}
                style={styles.tabItem}
              >
                <Text
                  style={[
                    styles.tabLabel,
                    isActive
                      ? { color: accentColor, fontWeight: "700" }
                      : { color: "#9CA3AF" },
                  ]}
                >
                  {tab.label}
                </Text>
                {/* Active indicator pill */}
                {isActive && (
                  <View
                    style={[styles.indicator, { backgroundColor: accentColor }]}
                  />
                )}
              </TouchableOpacity>
            );
          })}
        </ScrollView>
        {/* Bottom border */}
        <View style={styles.tabBarBorder} />
      </View>

      {/* ── 2: Tab Content ── */}
      <View style={styles.contentArea}>{renderTabContent(activeTab)}</View>
    </View>
  );
};

export default StickyTabView;

// ─── Styles ───────────────────────────────────────────────────────────────────

const styles = StyleSheet.create({
  root: {
    flex: 1,
    backgroundColor: "#F9FAFB",
  },
  tabBarWrapper: {
    // Shadow for iOS
    shadowColor: "#000",
    shadowOffset: { width: 0, height: 2 },
    shadowOpacity: 0.06,
    shadowRadius: 4,
    // Elevation for Android
    elevation: 3,
    zIndex: 10,
  },
  tabBarContent: {
    paddingHorizontal: 12,
  },
  tabItem: {
    alignItems: "center",
    paddingHorizontal: 16,
    paddingVertical: 14,
    marginRight: 4,
  },
  tabLabel: {
    fontSize: 14,
    letterSpacing: 0.2,
  },
  indicator: {
    marginTop: 6,
    height: 3,
    width: "80%",
    borderRadius: 2,
  },
  tabBarBorder: {
    height: 1,
    backgroundColor: "#E5E7EB",
  },
  contentArea: {
    flex: 1,
    minHeight: 600, // ensure enough height so sticky effect is visible
  },
});

// ─── USAGE EXAMPLE ────────────────────────────────────────────────────────────
//
// import StickyTabView from './StickyTabView';
//
// const TABS = [
//   { key: 'posts',    label: 'Bài viết' },
//   { key: 'photos',   label: 'Ảnh' },
//   { key: 'videos',   label: 'Video' },
//   { key: 'likes',    label: 'Yêu thích' },
//   { key: 'mentions', label: 'Đề cập' },
// ];
//
// export default function ProfileScreen() {
//   return (
//     <StickyTabView
//       accentColor="#6C63FF"
//       headerComponent={<ProfileHeader />}   // your own component
//       tabs={TABS}
//       renderTabContent={(key) => {
//         switch (key) {
//           case 'posts':  return <PostsList />;
//           case 'photos': return <PhotosGrid />;
//           default:       return <Text>Tab: {key}</Text>;
//         }
//       }}
//     />
//   );
// }
