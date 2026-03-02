import React from "react";
import { createBottomTabNavigator } from "@react-navigation/bottom-tabs";
import { useLocalSearchParams } from "expo-router";
import Detail from "./Detail";
import { View } from "react-native";

const Tab = createBottomTabNavigator();

const StockTabs = () => {
  const { data } = useLocalSearchParams() || {};
  const item = data ? JSON.parse(data as string) : null;

  return (
    <View></View>
    // <Tab.Navigator
    //   screenOptions={{
    //     tabBarActiveTintColor: "#6366F1", // Purple/indigo color
    //     tabBarInactiveTintColor: "#000",
    //     tabBarStyle: {
    //       height: 70,
    //       paddingBottom: 10,
    //       paddingTop: 10,
    //       backgroundColor: "#fff",
    //       borderTopWidth: 1,
    //       borderTopColor: "#e5e5e5",
    //     },
    //     tabBarLabelStyle: {
    //       fontSize: 12,
    //       fontWeight: "500",
    //     },
    //     headerShown: false,
    //   }}
    // >
    //   {/* <Tab.Screen
    //     name="Detail"
    //     component={({}) => <Detail stockItem={item} />}
    //     options={{
    //       tabBarIcon: ({ color, focused }) => <View></View>,
    //     }}
    //   /> */}
    //   {/* <Tab.Screen
    //     name="Services"
    //     component={({}) => <Analysis stockSymbol={item?.symbol || ""} />}
    //     options={{
    //       tabBarIcon: ({ color, focused }) => <View></View>,
    //     }}
    //   /> */}
    // </Tab.Navigator>
  );
};

export default StockTabs;
