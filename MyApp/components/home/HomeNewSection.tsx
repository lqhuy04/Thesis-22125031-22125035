import React, { useCallback, useEffect, useMemo, useState } from "react";
import { FlatList, TouchableOpacity, View } from "react-native";
import { Text } from "../ui/Text";
import { useTheme } from "@/hooks/ThemeContext";
import { New } from "@/helpers/DetailHelpers";
import {
  getBusinessNews,
  getMacroEcomNews,
  getNewsByCategoryId,
} from "@/helpers/MarketHelpers";
import NewsItem from "../ui/NewsItem";
import { router } from "expo-router";

const HomeNewSection = () => {
  const { theme } = useTheme();

  const [articles, setArticles] = useState<New[]>([]);

  const realEstateId = "afb4b18d-dc88-4ed0-b17b-28792868b460";
  const bankId = "1fbbad10-a283-47e8-b126-8360ffa225ae";
  const categories = useMemo(() => {
    return [
      {
        id: "business",
        name: "Doanh nghiệp",
      },
      {
        id: "macro",
        name: "Kinh tế - Vĩ mô",
      },

      {
        id: "bank",
        name: "Ngân hàng",
      },
      {
        id: "real-estate",
        name: "Bất động sản",
      },
    ];
  }, []);

  const [chosenCategory, setChosenCategory] = useState<string>(
    categories[0].id,
  );

  useEffect(() => {
    if (chosenCategory === "business") {
      getBusinessNews(3).then((result) => {
        if (result.status) {
          setArticles(result.data);
        }
      });
    } else if (chosenCategory === "macro") {
      getMacroEcomNews(3).then((result) => {
        if (result.status) {
          setArticles(result.data);
        }
      });
    } else if (chosenCategory === "bank") {
      getNewsByCategoryId(bankId, 3).then((result) => {
        if (result.status) {
          setArticles(result.data);
        }
      });
    } else if (chosenCategory === "real-estate") {
      getNewsByCategoryId(realEstateId, 3).then((result) => {
        if (result.status) {
          setArticles(result.data);
        }
      });
    }
  }, [chosenCategory]);

  const onViewAll = useCallback(() => {
    const params =
      chosenCategory === "business"
        ? {
            data: JSON.stringify({
              title: "Doanh nghiệp",
              type: "business",
            }),
          }
        : chosenCategory === "macro"
          ? {
              data: JSON.stringify({
                title: "Tin tức kinh tế - vĩ mô",
                type: "macro",
              }),
            }
          : chosenCategory === "bank"
            ? {
                data: JSON.stringify({
                  title: "Ngân hàng",
                  category_id: bankId,
                  type: "category",
                }),
              }
            : {
                data: JSON.stringify({
                  title: "Bất động sản",
                  category_id: realEstateId,
                  type: "category",
                }),
              };

    router.push({
      pathname: "/AllNews",
      params: params,
    });
  }, [chosenCategory]);

  return (
    <View style={{ marginHorizontal: 12, marginTop: 24 }}>
      <Text typography="titleMedium" style={{ marginBottom: 8 }}>
        Hôm nay có gì hot?
      </Text>

      <FlatList
        horizontal
        showsHorizontalScrollIndicator={false}
        data={categories}
        style={{ marginBottom: 8 }}
        renderItem={({ item }) => (
          <TouchableOpacity
            onPress={() => setChosenCategory(item.id)}
            style={{
              backgroundColor:
                chosenCategory === item.id
                  ? theme.base.primary + "12"
                  : theme.text.secondary + "80",
              borderWidth: 2,
              borderColor:
                chosenCategory === item.id
                  ? theme.base.primary + "80"
                  : theme.text.secondary + "80",
              paddingVertical: 4,
              paddingHorizontal: 8,
              borderRadius: 16,
              marginRight: 8,
              marginBottom: 8,
            }}
          >
            <Text
              typography="labelMedium"
              color={
                chosenCategory === item.id
                  ? theme.base.primary
                  : theme.text.primary
              }
            >
              {item.name}
            </Text>
          </TouchableOpacity>
        )}
        keyExtractor={(item) => item.id}
      />

      {articles.map((item, index) => {
        return <NewsItem key={index.toString()} newItem={item} />;
      })}

      <TouchableOpacity onPress={onViewAll}>
        <Text
          typography="labelLarge"
          color={theme.base.primary}
          style={{ alignSelf: "center" }}
        >
          Xem tất cả
        </Text>
      </TouchableOpacity>
    </View>
  );
};

export default HomeNewSection;
