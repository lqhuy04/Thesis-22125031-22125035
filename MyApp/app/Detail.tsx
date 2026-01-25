import NewsSection from "@/components/detail/NewsSection";
import DetailHeader from "@/components/ui/DetailHeader";
import SeeAllBtn from "@/components/ui/SeeAllBtn";
import { useTheme } from "@/hooks/ThemeContext";
import { useLocalSearchParams } from "expo-router";
import React from "react";
import { SafeAreaView } from "react-native-safe-area-context";

const Detail = () => {
  const { theme } = useTheme();

  const { data } = useLocalSearchParams() || {};
  const item = data ? JSON.parse(data as string) : null;

  return (
    <SafeAreaView
      style={{ flex: 1, padding: 12, backgroundColor: theme.background.bg }}
    >
      <DetailHeader item={item} />

      <NewsSection stockSymbol={item?.symbol || ""} />

      <SeeAllBtn />
    </SafeAreaView>
  );
};

export default Detail;
