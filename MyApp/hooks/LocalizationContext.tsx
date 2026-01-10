import React, { createContext, useContext, useMemo, useState } from "react";
import en from "../constants/locales/en";
import vi from "../constants/locales/vi";

export type Language = "en" | "vi";

const translations = {
  en,
  vi,
};

type LocalizationContextType = {
  language: Language;
  setLanguage: (lang: Language) => void;
  t: (key: string) => string;
};

const LocalizationContext = createContext<LocalizationContextType | null>(null);

export const LocalizationProvider: React.FC<{
  children: React.ReactNode;
}> = ({ children }) => {
  const [language, setLanguage] = useState<Language>("en");

  const t = useMemo(() => {
    return (key: string) => {
      const keys = key.split(".");
      let value: any = translations[language];

      for (const k of keys) {
        value = value?.[k];
      }

      return value ?? key;
    };
  }, [language]);

  return (
    <LocalizationContext.Provider value={{ language, setLanguage, t }}>
      {children}
    </LocalizationContext.Provider>
  );
};

export const useLocalization = () => {
  const context = useContext(LocalizationContext);

  if (!context) {
    throw new Error("useLocalization must be used inside LocalizationProvider");
  }

  return context;
};
