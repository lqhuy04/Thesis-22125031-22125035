import { LocalizationProvider } from "@/hooks/LocalizationContext";
import { ThemeProvider } from "@/hooks/ThemeContext";
import { Stack } from "expo-router";
import { StatusBar } from "expo-status-bar";
import { useFonts } from "expo-font";
import React from "react";
import { GestureHandlerRootView } from "react-native-gesture-handler";
import { SafeAreaProvider } from "react-native-safe-area-context";
import { SessionExpiredModal } from "@/components/authentication/SessionExpiredModal";

export default function RootLayout() {
  const [loaded] = useFonts({
    "Roboto-Medium": require("../assets/fonts/Roboto-Medium.ttf"),
    "Roboto-Regular": require("../assets/fonts/Roboto-Regular.ttf"),
    "Roboto-SemiBold": require("../assets/fonts/Roboto-SemiBold.ttf"),
  });

  if (!loaded) return null;

  return (
    <SafeAreaProvider>
      <GestureHandlerRootView style={{ flex: 1 }}>
        <LocalizationProvider>
          <ThemeProvider>
            <Stack screenOptions={{ headerShown: false }}>
              {/* Các màn hình chính sẽ tự động được Stack quản lý qua file-based routing */}
              <Stack.Screen name="index" />
            </Stack>
            <StatusBar style="auto" />
            <SessionExpiredModal />
          </ThemeProvider>
        </LocalizationProvider>
      </GestureHandlerRootView>
    </SafeAreaProvider>
  );
}
