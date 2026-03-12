import React, { useEffect, useState } from "react";
import { View } from "react-native";
import { Text } from "../ui/Text";
import { useLocalization } from "@/hooks/LocalizationContext";
import { fetchNews, New } from "@/helpers/DetailHelpers";
import NewsItem from "../ui/NewsItem";

interface NewsSectionProps {
  stockSymbol: string;
}

const NewsSection = ({ stockSymbol }: NewsSectionProps) => {
  const { t } = useLocalization();

  const [newsItems, setNewsItems] = useState<New[]>([]);

  useEffect(() => {
    fetchNews(stockSymbol).then((data) => {
      if (data.status) {
        setNewsItems(data.data);
      }
    });
  }, [stockSymbol]);

  return (
    <View style={{ marginHorizontal: 12, marginTop: 12 }}>
      <Text typography="titleLarge">{t("detail.newsSectionTitle")}</Text>

      {newsItems.map((item) => (
        <NewsItem key={item.id} newItem={item} />
      ))}
    </View>
  );
};
export default NewsSection;
