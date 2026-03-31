import NewsItem from "@/components/ui/NewsItem";
import ScreenHeader from "@/components/ui/ScreenHeader";
import { New } from "@/helpers/DetailHelpers";
import { getMacroEcomNews, getNewsByCategoryId } from "@/helpers/MarketHelpers";
import { useLocalSearchParams } from "expo-router";
import React, { useEffect, useState } from "react";
import { FlatList } from "react-native-gesture-handler";
import { SafeAreaView } from "react-native-safe-area-context";

const AllNews = () => {
  const { data } = useLocalSearchParams() || {};

  const { title = "", category_id = "" } = data
    ? (JSON.parse(data as string) as any)
    : {};

  const [articles, setArticles] = useState<New[]>([]);

  useEffect(() => {
    if (category_id === "") {
      getMacroEcomNews().then((result) => {
        if (result.status) {
          setArticles(result.data);
        }
      });
    } else {
      getNewsByCategoryId(String(category_id)).then((result) => {
        if (result.status) {
          setArticles(result.data);
        }
      });
    }
  }, [category_id]);

  return (
    <SafeAreaView>
      <ScreenHeader title={title} />

      <FlatList
        style={{ marginHorizontal: 12 }}
        data={articles}
        renderItem={({ item, index }) => {
          return <NewsItem newItem={item} />;
        }}
      />
    </SafeAreaView>
  );
};

export default AllNews;
