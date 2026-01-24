import { LocalizationProvider } from "@/hooks/LocalizationContext";
import { ThemeProvider } from "@/hooks/ThemeContext";
import { Stack } from "expo-router";
import { StatusBar } from "expo-status-bar";
import { useFonts } from "expo-font";
import React from "react";
import { GestureHandlerRootView } from "react-native-gesture-handler";

export default function RootLayout() {
  const [loaded] = useFonts({
    "Roboto-Medium": require("../assets/fonts/Roboto-Medium.ttf"),
    "Roboto-Regular": require("../assets/fonts/Roboto-Regular.ttf"),
    "Roboto-SemiBold": require("../assets/fonts/Roboto-SemiBold.ttf"),
  });

  if (!loaded) return null;

  return (
    <GestureHandlerRootView>
      <LocalizationProvider>
        <ThemeProvider>
          <Stack>
            <Stack.Screen
              name="authentication/Authentication"
              options={{ headerShown: false }}
            />
          </Stack>
          <StatusBar style="auto" />
        </ThemeProvider>
      </LocalizationProvider>
    </GestureHandlerRootView>
  );
}
