import React, {
  createContext,
  useContext,
  useEffect,
  useMemo,
  useState,
} from "react";
import * as SecureStore from "expo-secure-store";
import en from "../constants/locales/en";
import vi from "../constants/locales/vi";

export type Language = "en" | "vi";

const LANG_KEY = "app_language";
const translations = { en, vi };

type LocalizationContextType = {
  languageOptions: { key: Language; value: string }[];
  language: Language;
  setLanguage: (lang: Language) => void;
  t: (key: string) => string;
};

const LocalizationContext = createContext<LocalizationContextType | null>(null);

export const LocalizationProvider: React.FC<{ children: React.ReactNode }> = ({
  children,
}) => {
  const [language, setLanguageState] = useState<Language>("vi");
  const [loaded, setLoaded] = useState(false);

  // Load saved language on mount
  useEffect(() => {
    SecureStore.getItemAsync(LANG_KEY).then((val) => {
      if (val === "en" || val === "vi") setLanguageState(val);
      setLoaded(true);
    });
  }, []);

  const setLanguage = async (lang: Language) => {
    setLanguageState(lang);
    await SecureStore.setItemAsync(LANG_KEY, lang);
  };

  const languageOptions = [
    { key: "en" as Language, value: "English" },
    { key: "vi" as Language, value: "Tiếng Việt" },
  ];

  const t = useMemo(() => {
    return (key: string) => {
      const keys = key.split(".");
      let value: any = translations[language];
      for (const k of keys) value = value?.[k];
      return value ?? key;
    };
  }, [language]);

  if (!loaded) return null; // tránh flash ngôn ngữ sai

  return (
    <LocalizationContext.Provider
      value={{ language, setLanguage, t, languageOptions }}
    >
      {children}
    </LocalizationContext.Provider>
  );
};

export const useLocalization = () => {
  const context = useContext(LocalizationContext);
  if (!context)
    throw new Error("useLocalization must be used inside LocalizationProvider");
  return context;
};
