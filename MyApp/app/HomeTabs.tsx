import React from "react";
import { createBottomTabNavigator } from "@react-navigation/bottom-tabs";
import Home from "./Home";
import { Ionicons } from "@expo/vector-icons";
import { useTheme } from "@/hooks/ThemeContext";
import Profile from "./Profile";
import Search from "./Search";

const Tab = createBottomTabNavigator();

const HomeTabs = () => {
  const { theme } = useTheme();

  return (
    <Tab.Navigator
      screenOptions={{
        animation: "fade",
        tabBarActiveTintColor: "#6366F1",
        tabBarInactiveTintColor: "#000",
        tabBarStyle: {
          height: 70,
          paddingBottom: 10,
          paddingTop: 10,
          backgroundColor: "#fff",
          borderTopWidth: 1,
          borderTopColor: "#e5e5e5",
        },
        tabBarLabelStyle: {
          fontSize: 12,
          fontWeight: "500",
        },
        headerShown: false,
      }}
    >
      <Tab.Screen
        name="Home"
        component={() => <Home />}
        options={{
          tabBarIcon: ({ color, focused }) => (
            <Ionicons
              name="home-outline"
              size={20}
              color={theme.base.primary}
            />
          ),
        }}
      />
      <Tab.Screen
        name="Search"
        component={() => <Search />}
        options={{
          tabBarIcon: ({ color, focused }) => (
            <Ionicons
              name="search-outline"
              size={20}
              color={theme.base.primary}
            />
          ),
        }}
      />
      <Tab.Screen
        name="Profile"
        component={() => <Profile />}
        options={{
          tabBarIcon: ({ color, focused }) => (
            <Ionicons
              name="person-outline"
              size={20}
              color={theme.base.primary}
            />
          ),
        }}
      />
    </Tab.Navigator>
  );
};

export default HomeTabs;
