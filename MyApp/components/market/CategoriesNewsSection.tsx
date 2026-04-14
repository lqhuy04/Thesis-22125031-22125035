import React, { useEffect, useState } from "react";
import { View } from "react-native";
import NewsComponent from "../ui/NewsComponent";
import { Text } from "../ui/Text";
import { useTheme } from "@/hooks/ThemeContext";
import { router } from "expo-router";
import { New } from "@/helpers/DetailHelpers";
import { getNewsByCategoryId } from "@/helpers/MarketHelpers";

const CategoriesNewsSection = () => {
  const realEstateId = "afb4b18d-dc88-4ed0-b17b-28792868b460";
  const bankId = "1fbbad10-a283-47e8-b126-8360ffa225ae";
  const consumerGoodsId = "00341b34-8a12-4642-afd7-ae4664253b96";
  const { theme } = useTheme();

  const [categoryArticles, setCategoryArticles] = useState<
    {
      category_id: string;
      category_name: string;
      news: New[];
    }[]
  >([]);
  const [chosenIndex, setChosenIndex] = useState<number>(0);

  useEffect(() => {
    const fetchData = async () => {
      const results = await Promise.allSettled([
        getNewsByCategoryId(realEstateId, 3),
        getNewsByCategoryId(bankId, 3),
        getNewsByCategoryId(consumerGoodsId, 3),
      ]);

      const categories = [
        { id: realEstateId, name: "Bất động sản" },
        { id: bankId, name: "Ngân hàng" },
        { id: consumerGoodsId, name: "Hàng tiêu dùng" },
      ];

      const formatted = results.map((res, index) => {
        if (res.status === "fulfilled" && res.value.status) {
          return {
            category_id: categories[index].id,
            category_name: categories[index].name,
            news: res.value.data,
          };
        }

        // nếu fail → vẫn return nhưng rỗng
        return {
          category_id: categories[index].id,
          category_name: categories[index].name,
          news: [],
        };
      });

      setCategoryArticles(formatted);
    };

    fetchData();
  }, []);

  return categoryArticles.length === 0 ? null : (
    <View style={{ marginTop: 16 }}>
      <View
        style={{
          flexDirection: "row",
          alignItems: "center",
          justifyContent: "space-between",
        }}
      >
        <Text typography="titleLarge">{"Tin tức theo nhóm ngành"}</Text>
        <Text
          typography="titleMedium"
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
