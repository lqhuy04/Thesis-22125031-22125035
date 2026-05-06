import React from "react";
import { createBottomTabNavigator } from "@react-navigation/bottom-tabs";
import { Ionicons } from "@expo/vector-icons";
import { useTheme } from "@/hooks/ThemeContext";
import Home from "./Home";
import Profile from "./Profile";
import Market from "./Market";
import { View } from "react-native";
import Chatbot from "./Chatbot";
import { Text } from "@/components/ui/Text";

const Tab = createBottomTabNavigator();

const Tabs = () => {
  const { theme } = useTheme();

  return (
    <View style={{ flex: 1 }}>
      <Tab.Navigator
        screenOptions={{
          animation: "fade",
          tabBarActiveTintColor: "#6366F1",
          tabBarInactiveTintColor: "#000",
          tabBarStyle: {
            height: 90,
            paddingBottom: 16,
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
            tabBarLabel: ({ focused }) => (
              <Text
                typography="bodySmall"
                color={focused ? theme.base.primary : theme.text.primary + "80"}
              >
                Tổng quan
              </Text>
            ),
            tabBarIcon: ({ color, focused }) => (
              <Ionicons
                name="home-outline"
                size={20}
                color={focused ? theme.base.primary : theme.text.primary + "80"}
              />
            ),
          }}
        />
        <Tab.Screen
          name="Market"
          component={() => <Market />}
          options={{
            tabBarLabel: ({ focused }) => (
              <Text
                typography="bodySmall"
                color={focused ? theme.base.primary : theme.text.primary + "80"}
              >
                Thị trường
              </Text>
            ),
            tabBarIcon: ({ color, focused }) => (
              <Ionicons
                name="storefront-outline"
                size={20}
                color={focused ? theme.base.primary : theme.text.primary + "80"}
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
                color={focused ? theme.base.primary : theme.text.primary + "80"}
              />
            ),
            tabBarLabel: ({ focused }) => (
              <Text
                typography="bodySmall"
                color={focused ? theme.base.primary : theme.text.primary + "80"}
              >
                Hồ sơ
              </Text>
            ),
          }}
        />
        <Tab.Screen
          name="Chatbot"
          component={() => <Chatbot />}
          options={{
            tabBarIcon: ({ color, focused }) => (
              <Ionicons
                name="chatbubble-ellipses-outline"
                size={20}
                color={focused ? theme.base.primary : theme.text.primary + "80"}
              />
            ),
            tabBarLabel: ({ focused }) => (
              <Text
                typography="bodySmall"
                color={focused ? theme.base.primary : theme.text.primary + "80"}
              >
                Chatbot
              </Text>
            ),
          }}
        />
      </Tab.Navigator>
    </View>
  );
};

export default Tabs;
