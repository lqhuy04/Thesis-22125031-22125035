import React, { createContext, useContext, useEffect, useState } from "react";
import { lightTheme, darkTheme, Theme } from "../constants/theme";
import * as SecureStore from "expo-secure-store";

const THEME_KEY = "app_theme";

type ThemeContextType = {
  theme: Theme;
  toggleTheme: () => void;
  resetTheme: () => void;
  isDark: boolean;
};

const ThemeContext = createContext<ThemeContextType | null>(null);

export const ThemeProvider: React.FC<{ children: React.ReactNode }> = ({
  children,
}) => {
  const [isDark, setIsDark] = useState(false);
  const [loaded, setLoaded] = useState(false);

  // Load saved theme on mount
  useEffect(() => {
    SecureStore.getItemAsync(THEME_KEY).then((val) => {
      if (val === "dark") setIsDark(true);
      setLoaded(true);
    });
  }, []);

  const toggleTheme = async () => {
    const next = !isDark;
    setIsDark(next);
    await SecureStore.setItemAsync(THEME_KEY, next ? "dark" : "light");
  };

  // Đưa theme về mặc định (light)
  const resetTheme = async () => {
    setIsDark(false);
    await SecureStore.setItemAsync(THEME_KEY, "light");
  };

  if (!loaded) return null; // tránh flash theme sai

  return (
    <ThemeContext.Provider
      value={{
        isDark,
        theme: isDark ? darkTheme : lightTheme,
        toggleTheme,
        resetTheme,
      }}
    >
      {children}
    </ThemeContext.Provider>
  );
};

export const useTheme = () => {
  const context = useContext(ThemeContext);
  if (!context) throw new Error("useTheme must be used within ThemeProvider");
  return context;
};
