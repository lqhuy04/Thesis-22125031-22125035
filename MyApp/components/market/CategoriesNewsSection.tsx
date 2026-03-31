import { CategoryNews, getCategoriesNews } from "@/helpers/MarketHelpers";
import React, { useEffect, useState } from "react";
import { View } from "react-native";
import NewsComponent from "../ui/NewsComponent";
import { Text } from "../ui/Text";
import { useTheme } from "@/hooks/ThemeContext";
import { router } from "expo-router";

const CategoriesNewsSection = () => {
  const { theme } = useTheme();

  const [categoryArticles, setCategoryArticles] = useState<CategoryNews[]>([]);
  const [chosenIndex, setChosenIndex] = useState<number>(0);

  useEffect(() => {
    getCategoriesNews().then((result) => {
      if (result.status) {
        setCategoryArticles(result.data);
      }
    });
  }, []);

  return categoryArticles.length === 0 ? null : (
    <View style={{ marginTop: 12 }}>
      <View
        style={{
          flexDirection: "row",
          alignItems: "center",
          justifyContent: "space-between",
        }}
      >
        <Text typography="titleLarge">{"Tin tức theo nhóm ngành"}</Text>
        <Text
          typography="titleLarge"
          color={theme.base.primary}
          onPress={() => {
            router.push({
              pathname: "/AllNews",
              params: {
                data: JSON.stringify({
                  title: categoryArticles[chosenIndex].category_name,
                  category_id: categoryArticles[chosenIndex].category_id,
                }),
              },
            });
          }}
        >
          Xem tất cả
        </Text>
      </View>

      <View
        style={{
          flexDirection: "row",
          alignItems: "center",
          flexWrap: "wrap",
        }}
      >
        {categoryArticles.map((item, index) => {
          return (
            <Text
              key={item.category_id}
              typography="bodyLarge"
              color={
                chosenIndex === index
                  ? theme.text.onPrimary
                  : theme.text.primary
              }
              style={{
                backgroundColor:
                  chosenIndex === index
                    ? theme.base.primary
                    : theme.background.surface,
                paddingVertical: 2,
                paddingHorizontal: 4,
                borderRadius: 4,
                borderWidth: 1,
                borderColor:
                  chosenIndex === index
                    ? theme.base.primary
                    : theme.border.default,
                marginHorizontal: 4,
                alignItems: "center",
                marginTop: 12,
              }}
              onPress={() => {
                setChosenIndex(index);
              }}
            >
              {item.category_name}
            </Text>
          );
        })}
      </View>

      <NewsComponent articles={categoryArticles[chosenIndex].news} />
    </View>
  );
};

export default CategoriesNewsSection;
