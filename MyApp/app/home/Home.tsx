import React from "react";
import { View, Text } from "react-native";
import { useTheme } from "@/hooks/ThemeContext";

const Home = () => {
  const { theme } = useTheme();

  return (
    <View
      style={{
        padding: 12,
        backgroundColor: theme.background.bg,
        flex: 1,
        paddingTop: 80,
      }}
    >
      <Text>Home</Text>
    </View>
  );
};

export default Home;
