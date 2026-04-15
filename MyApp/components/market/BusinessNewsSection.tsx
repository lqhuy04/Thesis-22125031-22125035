import React, { useEffect, useState } from "react";
import { Text } from "../ui/Text";
import { useTheme } from "@/hooks/ThemeContext";
import { New } from "@/helpers/DetailHelpers";
import { View } from "react-native";
import { router } from "expo-router";
import { getBusinessNews } from "@/helpers/MarketHelpers";
import NewsItem from "../ui/NewsItem";

const BusinessNewsSection = () => {
  const { theme } = useTheme();
  const [articles, setArticles] = useState<New[]>([]);

  useEffect(() => {
    getBusinessNews(3).then((result) => {
      if (result.status) {
        setArticles(result.data);
      }
    });
  }, []);

  return (
    <View>
      <View
        style={{
          flexDirection: "row",
          alignItems: "center",
          justifyContent: "space-between",
          marginVertical: 12,
        }}
      >
        <Text typography="titleLarge">{"Doanh nghiệp"}</Text>
        <Text
          typography="titleMedium"
          color={theme.base.primary}
          onPress={() => {
            router.push({
              pathname: "/AllNews",
              params: {
                data: JSON.stringify({
                  title: "Doanh nghiệp",
                  type: "business",
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

export default BusinessNewsSection;
