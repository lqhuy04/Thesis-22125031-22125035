import React, { useEffect, useState } from "react";
import { View } from "react-native";
import { Text } from "../ui/Text";
import { useTheme } from "@/hooks/ThemeContext";
import { router } from "expo-router";
import { New } from "@/helpers/DetailHelpers";
import { getAllNews } from "@/helpers/MarketHelpers";
import NewsItem from "../ui/NewsItem";

const AllNewsSection = () => {
  const { theme } = useTheme();
  const [articles, setArticles] = useState<New[]>([]);

  useEffect(() => {
    getAllNews(10).then((result) => {
      if (result.status) {
        setArticles(result.data);
      }
    });
  }, []);

  return (
    <View style={{ marginTop: 16, marginHorizontal: 12 }}>
      <View style={{ marginBottom: 12 }}>
        <View
          style={{
            flexDirection: "row",
            alignItems: "center",
            justifyContent: "space-between",
          }}
        >
          <Text typography="titleMedium">{"Toàn cảnh thị trường"}</Text>
          <Text
            typography="titleMedium"
            color={theme.base.primary}
            onPress={() => {
              router.push({
                pathname: "/AllNews",
                params: {
                  data: JSON.stringify({
                    title: "Toàn cảnh thị trường",
                    type: "all",
                  }),
                },
              });
            }}
          >
            Xem tất cả
          </Text>
        </View>
      </View>

      {articles.map((item, index) => {
        return <NewsItem key={index.toString()} newItem={item} />;
      })}
    </View>
  );
};

export default AllNewsSection;
