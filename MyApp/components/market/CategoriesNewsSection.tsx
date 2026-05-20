import React, { useEffect, useState } from "react";
import { TouchableOpacity, View } from "react-native";
import { Text } from "../ui/Text";
import { useTheme } from "@/hooks/ThemeContext";
import { router } from "expo-router";
import { New } from "@/helpers/DetailHelpers";
import { getNewsByCategoryId } from "@/helpers/MarketHelpers";
import NewsItem from "../ui/NewsItem";
import { useLocalization } from "@/hooks/LocalizationContext";

const CategoriesNewsSection = () => {
  const realEstateId = "afb4b18d-dc88-4ed0-b17b-28792868b460";
  const bankId = "1fbbad10-a283-47e8-b126-8360ffa225ae";
  const consumerGoodsId = "00341b34-8a12-4642-afd7-ae4664253b96";
  const { theme } = useTheme();
  const { t } = useLocalization();

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
        { id: realEstateId, name: t("market.categoryRealEstate") },
        { id: bankId, name: t("market.categoryBank") },
        { id: consumerGoodsId, name: t("market.categoryConsumerGoods") },
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
  }, [t]);

  return categoryArticles.length === 0 ? null : (
    <View style={{ marginTop: 24, marginHorizontal: 12 }}>
      <View
        style={{
          flexDirection: "row",
          alignItems: "center",
          justifyContent: "space-between",
          marginBottom: 8,
        }}
      >
        <Text typography="titleMedium" color={theme.text.primary}>
          {t("market.newsByIndustry")}
        </Text>
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
                  type: "category",
                }),
              },
            });
          }}
        >
          {t("market.viewAll")}
        </Text>
      </View>

      <View
        style={{
          backgroundColor: theme.background.bg,
          padding: 12,
          borderRadius: 12,
        }}
      >
        <View
          style={{
            flexDirection: "row",
            alignItems: "center",
            flexWrap: "wrap",
            marginBottom: 4,
          }}
        >
          {categoryArticles.map((item, index) => {
            return (
              <TouchableOpacity
                key={index.toString()}
                onPress={() => setChosenIndex(index)}
                style={{
                  backgroundColor:
                    chosenIndex === index
                      ? theme.base.primary
                      : theme.background.primarySurface,
                  paddingVertical: 6,
                  paddingHorizontal: 12,
                  borderRadius: 16,
                  marginRight: 8,
                }}
              >
                <Text
                  typography="labelLarge"
                  color={
                    chosenIndex === index
                      ? theme.text.onPrimary
                      : theme.text.primary
                  }
                >
                  {item.category_name}
                </Text>
              </TouchableOpacity>
            );
          })}
        </View>

        {categoryArticles[chosenIndex].news.map((item, index) => {
          return (
            <View key={index.toString()}>
              {index !== 0 ? (
                <View
                  style={{
                    height: 1,
                    width: "100%",
                    backgroundColor: theme.border.default,
                  }}
                />
              ) : null}
              <NewsItem key={index.toString()} newItem={item} />
            </View>
          );
        })}
      </View>
    </View>
  );
};

export default CategoriesNewsSection;
