import { New } from "@/helpers/DetailHelpers";
import { getMacroEcomNews } from "@/helpers/MarketHelpers";
import React, { useEffect, useState } from "react";
import { View } from "react-native";
import { Text } from "../ui/Text";
import { useTheme } from "@/hooks/ThemeContext";
import { router } from "expo-router";
import NewsItem from "../ui/NewsItem";

const MacroEcomNewsSection = () => {
  const { theme } = useTheme();
  const [articles, setArticles] = useState<New[]>([]);

  useEffect(() => {
    getMacroEcomNews(3).then((result) => {
      if (result.status) {
        setArticles(result.data);
      }
    });
  }, []);

  return (
    <View style={{ marginTop: 16, marginHorizontal: 12 }}>
      <View
        style={{
          flexDirection: "row",
          alignItems: "center",
          justifyContent: "space-between",
          marginBottom: 12,
        }}
      >
        <Text typography="titleMedium">{"Tin tức kinh tế - vĩ mô"}</Text>
        <Text
          typography="titleMedium"
          color={theme.base.primary}
          onPress={() => {
            router.push({
              pathname: "/AllNews",
              params: {
                data: JSON.stringify({
                  title: "Tin tức kinh tế - vĩ mô",
                  type: "macro",
                }),
              },
            });
          }}
        >
          Xem tất cả
        </Text>
      </View>

      {articles.map((item, index) => {
        return <NewsItem key={index.toString()} newItem={item} />;
      })}
    </View>
  );
};

export default MacroEcomNewsSection;
