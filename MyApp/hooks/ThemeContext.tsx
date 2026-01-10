// ThemeContext.tsx
import React, { createContext, useContext, useState } from "react";
import { lightTheme, darkTheme, Theme } from "../constants/theme";

type ThemeContextType = {
  theme: Theme;
  toggleTheme: () => void;
};

const ThemeContext = createContext<ThemeContextType | null>(null);

export const ThemeProvider: React.FC<{ children: React.ReactNode }> = ({
  children,
}) => {
  const [isDark, setIsDark] = useState(false);

  return (
    <ThemeContext.Provider
      value={{
        theme: isDark ? darkTheme : lightTheme,
        toggleTheme: () => setIsDark(!isDark),
      }}
    >
      {children}
    </ThemeContext.Provider>
  );
};

export const useTheme = () => {
  const context = useContext(ThemeContext);
  if (!context) {
    throw new Error("useTheme must be used within ThemeProvider");
  }
  return context;
};
