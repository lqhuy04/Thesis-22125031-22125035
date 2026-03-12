import React, { useState, useEffect } from "react";
import { View, ScrollView, TouchableOpacity } from "react-native";
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
}

const TabView: React.FC<TabViewProps> = ({
  tabs,
  activeTab,
  activeSubTab,
  tabScrollRef,
  tabRefs,
  handleTabPress,
}) => {
  const { theme } = useTheme();

  const activeTabItem = tabs.find((t) => t.key === activeTab);
  const subTabs = activeTabItem?.subTabs ?? [];

  return (
    <View>
      {/* Main tabs */}
      <View
        style={{
          borderTopWidth: 1,
          borderTopColor: theme.border.default,
          borderBottomWidth: subTabs.length === 0 ? 1 : 0,
          borderBottomColor: theme.border.default,
          backgroundColor: theme.background.bg,
        }}
      >
        <ScrollView
          ref={tabScrollRef}
          horizontal
          showsHorizontalScrollIndicator={false}
          contentContainerStyle={{ paddingHorizontal: 12 }}
          bounces={false}
        >
          {tabs.map((tab) => {
            const isActive = tab.key === activeTab;
            return (
              <TouchableOpacity
                key={tab.key}
                onPress={() =>
                  handleTabPress(
                    tab.key,
                    tab.subTabs?.[0]?.key ?? undefined
                  )
                }
                onLayout={(e) => {
                  tabRefs.current[tab.key] = e.nativeEvent.layout.x;
                }}
                style={{
                  alignItems: "center",
                  paddingHorizontal: 12,
                  paddingTop: 8,
                }}
              >
                <Text
                  typography="labelLarge"
                  color={isActive ? theme.text.primary : theme.text.secondary}
                >
                  {tab.label}
                </Text>

                {isActive && (
                  <View
                    style={{
                      backgroundColor: theme.base.primary,
                      marginTop: 8,
                      height: 2,
                      width: "100%",
                      borderRadius: 2,
                    }}
                  />
                )}
              </TouchableOpacity>
            );
          })}
        </ScrollView>
      </View>

      {/* Sub tabs */}
      { subTabs!= null &&  subTabs.length > 0 && (
        <View
          style={{
            borderTopWidth: 1,
            borderBottomWidth: 1,
            borderTopColor: theme.border.default,
            borderBottomColor: theme.border.default,
            backgroundColor: theme.background.surface ?? theme.background.bg,
          }}
        >
          <ScrollView
            horizontal
            showsHorizontalScrollIndicator={false}
            contentContainerStyle={{ paddingHorizontal: 12 }}
            bounces={false}
          >
            {subTabs.map((sub) => {
              const isSubActive = sub.key === activeSubTab;
              return (
                <TouchableOpacity
                  key={sub.key}
                  onPress={() => handleTabPress(activeTab, sub.key)}
                  style={{
                    alignItems: "center",
                    paddingHorizontal: 10,
                    paddingTop: 6,
                  }}
                >
                  <Text
                    typography="labelMedium"
                    color={
                      isSubActive ? theme.text.primary : theme.text.secondary
                    }
                  >
                    {sub.label}
                  </Text>

                  {isSubActive && (
                    <View
                      style={{
                        backgroundColor: theme.base.primary,
                        marginTop: 6,
                        height: 2,
                        width: "100%",
                        borderRadius: 2,
                      }}
                    />
                  )}
                </TouchableOpacity>
              );
            })}
          </ScrollView>
        </View>
      )}
    </View>
  );
};

export default TabView;