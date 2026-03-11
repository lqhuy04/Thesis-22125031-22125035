import React from "react";
import { View, ScrollView, TouchableOpacity } from "react-native";
import { useTheme } from "@/hooks/ThemeContext";
import { Text } from "@/components/ui/Text";

export interface TabItem {
  key: string;
  label: string;
}

export interface TabViewProps {
  tabs: TabItem[];
  activeTab: string;
  tabScrollRef: React.RefObject<ScrollView | null>;
  tabRefs: React.RefObject<{
    [key: string]: number;
  }>;
  handleTabPress: (key: string) => void;
}

const TabView: React.FC<TabViewProps> = ({
  tabs,
  activeTab,
  tabScrollRef,
  tabRefs,
  handleTabPress,
}) => {
  const { theme } = useTheme();

  return (
    <View
      style={{
        borderTopWidth: 1,
        borderBottomWidth: 1,
        borderTopColor: theme.border.default,
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
              onPress={() => handleTabPress(tab.key)}
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
  );
};

export default TabView;
