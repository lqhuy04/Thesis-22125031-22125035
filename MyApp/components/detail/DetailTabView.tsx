import React, { useState, useEffect, useRef, useCallback } from "react";
import { View, ScrollView, TouchableOpacity, Animated, Platform } from "react-native";
import { useTheme } from "@/hooks/ThemeContext";
import { Text } from "@/components/ui/Text";

export interface TabItem {
  key: string;
  label: string;
  subTabs?: TabItem[];
}

export interface TabViewProps {
  tabs: TabItem[];
  activeTab: string;
  activeSubTab?: string;
  tabScrollRef: React.RefObject<ScrollView | null>;
  tabRefs: React.RefObject<{ [key: string]: number }>;
  handleTabPress: (key: string, subTabKey?: string) => void;
  renderContent: (tabKey: string, subTabKey?: string) => React.ReactNode;
  headerContent: () => React.ReactNode;
}

/**
 * CachedTabContent - renders once and stays mounted, just hidden when inactive.
 * Prevents re-renders when switching tabs.
 */
const CachedTabContent: React.FC<{
  isActive: boolean;
  children: React.ReactNode;
}> = ({ isActive, children }) => {
  const [hasRendered, setHasRendered] = useState(false);
  const fadeAnim = useRef(new Animated.Value(isActive ? 1 : 0)).current;
  const prevIsActive = useRef(isActive);

  // Mark as rendered once it becomes active for the first time
  useEffect(() => {
    if (isActive && !hasRendered) {
      setHasRendered(true);
    }
  }, [isActive]);

  // Animate opacity when active state changes
  useEffect(() => {
    if (prevIsActive.current === isActive) return;
    prevIsActive.current = isActive;

    Animated.timing(fadeAnim, {
      toValue: isActive ? 1 : 0,
      duration: 220,
      useNativeDriver: true,
    }).start();
  }, [isActive]);

  // Don't render until first activation (lazy)
  if (!hasRendered) return null;

  return (
    <Animated.View
      style={{
        opacity: fadeAnim,
        // Keep in layout but hidden — avoids unmount/remount
        display: isActive ? "flex" : "none",
      }}
      pointerEvents={isActive ? "auto" : "none"}
    >
      {children}
    </Animated.View>
  );
};

// ─── Animated underline indicator ───────────────────────────────────────────

const TabIndicator: React.FC<{
  color: string;
  width: number;
  translateX: Animated.Value;
}> = ({ color, width, translateX }) => (
  <Animated.View
    style={{
      position: "absolute",
      bottom: 0,
      left: 0,
      height: 2,
      width,
      borderRadius: 2,
      backgroundColor: color,
      transform: [{ translateX }],
    }}
  />
);

// ─── Main TabView ────────────────────────────────────────────────────────────

const TabView: React.FC<TabViewProps> = ({
  tabs,
  activeTab,
  activeSubTab,
  tabScrollRef,
  tabRefs,
  handleTabPress,
  renderContent,
  headerContent,
}) => {
  const { theme } = useTheme();

  // Track tab widths for animated indicator
  const tabWidths = useRef<{ [key: string]: number }>({});
  const subTabWidths = useRef<{ [key: string]: number }>({});

  // Animated X position for main tab indicator
  const mainIndicatorX = useRef(new Animated.Value(0)).current;
  const mainIndicatorWidth = useRef(new Animated.Value(0)).current;

  // Animated X position for sub tab indicator
  const subIndicatorX = useRef(new Animated.Value(0)).current;
  const subIndicatorWidth = useRef(new Animated.Value(0)).current;

  // Positions of each tab (left edge relative to scrollview)
  const tabPositions = useRef<{ [key: string]: number }>({});
  const subTabPositions = useRef<{ [key: string]: number }>({});

  const activeTabItem = tabs.find((t) => t.key === activeTab);
  const subTabs = activeTabItem?.subTabs ?? [];

  // Animate main indicator when activeTab changes
  useEffect(() => {
    const x = tabPositions.current[activeTab] ?? 0;
    const w = tabWidths.current[activeTab] ?? 0;

    Animated.parallel([
      Animated.spring(mainIndicatorX, {
        toValue: x,
        useNativeDriver: false,
        tension: 80,
        friction: 12,
      }),
      Animated.spring(mainIndicatorWidth, {
        toValue: w,
        useNativeDriver: false,
        tension: 80,
        friction: 12,
      }),
    ]).start();
  }, [activeTab]);

  // Animate sub indicator when activeSubTab changes
  useEffect(() => {
    if (!activeSubTab) return;
    const x = subTabPositions.current[activeSubTab] ?? 0;
    const w = subTabWidths.current[activeSubTab] ?? 0;

    Animated.parallel([
      Animated.spring(subIndicatorX, {
        toValue: x,
        useNativeDriver: false,
        tension: 80,
        friction: 12,
      }),
      Animated.spring(subIndicatorWidth, {
        toValue: w,
        useNativeDriver: false,
        tension: 80,
        friction: 12,
      }),
    ]).start();
  }, [activeSubTab, activeTab]);

  // When subtabs change (tab switch), reset sub indicator immediately
  const prevTabKey = useRef(activeTab);
  useEffect(() => {
    if (prevTabKey.current !== activeTab) {
      prevTabKey.current = activeTab;
      // Reset sub indicator to first subtab position without animation
      const firstSub = subTabs[0]?.key;
      if (firstSub) {
        subIndicatorX.setValue(subTabPositions.current[firstSub] ?? 0);
        subIndicatorWidth.setValue(subTabWidths.current[firstSub] ?? 0);
      }
    }
  }, [activeTab, subTabs]);

  return (
    <ScrollView
    style={{ flex: 1 }}
    showsVerticalScrollIndicator={false}
    bounces={Platform.OS === "ios"}
    stickyHeaderIndices={[1]}
    >

      {headerContent != null ? headerContent() : null}

      <View>
        {/* ── Main Tabs ── */}
        <View
          style={{
            borderTopWidth: 1,
            borderTopColor: theme.border.default,
            borderBottomWidth: 1,
            borderBottomColor: theme.border.default,
            backgroundColor: theme.background.bg,
            paddingHorizontal: 12,
          }}
        >
          <View style={{ position: "relative" }}>
            <ScrollView
              ref={tabScrollRef}
              horizontal
              showsHorizontalScrollIndicator={false}
              bounces={false}
            >
              {tabs.map((tab) => {
                const isActive = tab.key === activeTab;
                return (
                  <TouchableOpacity
                    key={tab.key}
                    activeOpacity={0.7}
                    onPress={() =>
                      handleTabPress(tab.key, tab.subTabs?.[0]?.key ?? undefined)
                    }
                    style={{
                      alignItems: "center",
                      paddingVertical: 10,
                      marginRight: 12,
                      borderBottomWidth: isActive ? 2 : 0,
                      borderBottomColor: isActive ? theme.base.primary  : undefined,
                    }}
                  >
                    <Text
                     typography="titleMedium"
                     color={theme.text.primary}
                    >
                      {tab.label}
                    </Text>
                  </TouchableOpacity>
                );
              })}
            </ScrollView>

            {/* Animated sliding underline */}
            <TabIndicator
              color={theme.base.primary}
              width={0} // controlled by mainIndicatorWidth
              translateX={mainIndicatorX}
            />
          </View>
        </View>

        {/* ── Sub Tabs ── */}
        {subTabs.length > 0 && (

              <ScrollView
                horizontal
                showsHorizontalScrollIndicator={false}
                bounces={false}
                style={{marginHorizontal: 12, backgroundColor: theme.background.bg}}
              >
                {subTabs.map((sub) => {
                  const isSubActive = sub.key === activeSubTab;
                  return (
                    <TouchableOpacity
                      key={sub.key}
                      activeOpacity={0.7}
                      onPress={() => handleTabPress(activeTab, sub.key)}
                      style={{
                        alignItems: "center",
                        backgroundColor: isSubActive ? theme.base.primary : theme.background.surface,
                        borderRadius: 4,
                        paddingVertical: 2,
                        paddingHorizontal: 4,
                        marginVertical: 8,
                        marginRight: 8,
                      }}
                    >
                      <Text
                        typography="labelLarge"
                        color={
                          isSubActive ? theme.text.onPrimary : theme.text.primary
                        }
                      >
                        {sub.label}
                      </Text>
                    </TouchableOpacity>
                  );
                })}
              </ScrollView>
        )}
      </View>

      {/* ── Cached Tab Content ── */}
      {renderContent &&
        tabs.map((tab: TabItem) => {
          const hasSubTabs = (tab.subTabs?.length ?? 0) > 0;

          if (hasSubTabs) {
            return tab.subTabs!.map((sub: TabItem) => {
              const isActive = activeTab === tab.key && activeSubTab === sub.key;
              return (
                <CachedTabContent key={`${tab.key}-${sub.key}`} isActive={isActive}>
                  {renderContent(tab.key, sub.key)}
                </CachedTabContent>
              );
            });
          }

          const isActive = activeTab === tab.key;
          return (
            <CachedTabContent key={tab.key} isActive={isActive}>
              {renderContent(tab.key)}
            </CachedTabContent>
          );
        })}
    </ScrollView>
  );
};

export default TabView;